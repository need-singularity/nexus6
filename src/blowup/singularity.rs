//! Singularity detection — finds the "point" where a system is maximally compressed.
//!
//! A singularity occurs when:
//! - Discovery rate → 0 (convergence saturation)
//! - All dimensions collapse to minimal representation
//! - The system is "closed" — no new information from current lens set

use std::collections::HashMap;

/// A detected singularity — the compressed core of a closed system.
#[derive(Debug, Clone)]
pub struct Singularity {
    /// The minimal set of axioms/constants that define the closed system.
    pub axioms: Vec<String>,
    /// Compression ratio: original_dimensions / axiom_count.
    pub compression_ratio: f64,
    /// How "closed" the system is (0.0 = open, 1.0 = fully closed).
    pub closure_degree: f64,
    /// The domain this singularity lives in.
    pub domain: String,
    /// Metric values at the singularity point.
    pub metrics: HashMap<String, f64>,
}

/// Detects singularities from scan history.
#[derive(Debug, Clone)]
pub struct SingularityDetector {
    /// Minimum closure degree to declare a singularity.
    pub min_closure: f64,
    /// Minimum compression ratio.
    pub min_compression: f64,
    /// Window of cycles to analyze.
    pub window: usize,
}

impl Default for SingularityDetector {
    fn default() -> Self {
        Self {
            min_closure: 0.9,
            min_compression: 2.0,
            window: 6, // n=6
        }
    }
}

impl SingularityDetector {
    /// Analyze a sequence of metric snapshots to detect singularity formation.
    ///
    /// Each snapshot is a map of metric_name → value.
    /// A singularity is detected when:
    /// 1. Variance across recent snapshots → 0 (system stopped changing)
    /// 2. Dimensionality collapses (many metrics become correlated)
    /// 3. The remaining independent dimensions form the "axiom set"
    pub fn detect(&self, history: &[HashMap<String, f64>]) -> Option<Singularity> {
        if history.len() < self.window {
            return None;
        }

        let recent = &history[history.len() - self.window..];

        // Collect all metric names
        let mut all_keys: Vec<String> = recent
            .iter()
            .flat_map(|m| m.keys().cloned())
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect();
        all_keys.sort();

        if all_keys.is_empty() {
            return None;
        }

        // Calculate variance for each metric across the window
        let mut variances: HashMap<String, f64> = HashMap::new();
        let mut means: HashMap<String, f64> = HashMap::new();

        for key in &all_keys {
            let values: Vec<f64> = recent
                .iter()
                .filter_map(|m| m.get(key).copied())
                .collect();

            if values.is_empty() {
                continue;
            }

            let mean = values.iter().sum::<f64>() / values.len() as f64;
            let variance = values.iter().map(|v| (v - mean).powi(2)).sum::<f64>()
                / values.len() as f64;

            means.insert(key.clone(), mean);
            variances.insert(key.clone(), variance);
        }

        // Closure degree: fraction of metrics with near-zero variance
        let total_metrics = variances.len() as f64;
        if total_metrics == 0.0 {
            return None;
        }
        let frozen_count = variances.values().filter(|&&v| v < 1e-6).count() as f64;
        let closure_degree = frozen_count / total_metrics;

        if closure_degree < self.min_closure {
            return None;
        }

        // Find axioms: metrics that are non-zero and frozen (stable)
        let axioms: Vec<String> = means
            .iter()
            .filter(|(k, v)| {
                v.abs() > 1e-10
                    && variances.get(k.as_str()).copied().unwrap_or(1.0) < 1e-6
            })
            .map(|(k, _)| k.clone())
            .collect();

        let compression_ratio = if axioms.is_empty() {
            0.0
        } else {
            total_metrics / axioms.len() as f64
        };

        if compression_ratio < self.min_compression {
            return None;
        }

        Some(Singularity {
            axioms,
            compression_ratio,
            closure_degree,
            domain: "auto-detected".to_string(),
            metrics: means,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_singularity_detection() {
        let detector = SingularityDetector {
            min_closure: 0.5,
            min_compression: 0.5,
            window: 3,
        };

        // All metrics frozen → singularity
        let snapshot: HashMap<String, f64> = vec![
            ("phi".into(), 1.618),
            ("sigma".into(), 12.0),
            ("tau".into(), 4.0),
        ]
        .into_iter()
        .collect();

        let history = vec![snapshot.clone(), snapshot.clone(), snapshot.clone()];
        let result = detector.detect(&history);
        assert!(result.is_some());
        let s = result.unwrap();
        assert!(s.closure_degree >= 0.5);
        assert!(s.axioms.len() >= 2);
    }

    #[test]
    fn test_no_singularity_when_changing() {
        let detector = SingularityDetector::default();

        let history: Vec<HashMap<String, f64>> = (0..6)
            .map(|i| {
                vec![("x".into(), i as f64 * 10.0), ("y".into(), i as f64)]
                    .into_iter()
                    .collect()
            })
            .collect();

        assert!(detector.detect(&history).is_none());
    }
}
