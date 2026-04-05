use std::collections::HashMap;

use serde::{Deserialize, Serialize};

/// Consensus level based on number of agreeing lenses.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConsensusLevel {
    /// 3+ lenses agree
    Candidate,
    /// 7+ lenses agree
    High,
    /// 12+ lenses agree
    Confirmed,
}

/// A consensus result for a detected pattern.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConsensusResult {
    /// Identifier for the pattern (e.g. "void_at_3", "barrier_0_1")
    pub pattern_id: String,
    /// Names of agreeing lenses
    pub agreeing_lenses: Vec<String>,
    /// Weighted score (sum of hit_rate weights for agreeing lenses)
    pub weighted_score: f64,
    /// Consensus level
    pub level: ConsensusLevel,
    /// mk2: physics sector classification
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mk2_sector: Option<String>,
    /// mk2: classification confidence
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mk2_confidence: Option<f64>,
}

use crate::telescope::lens_trait::LensResult;

/// Compute weighted consensus across multiple lens results.
///
/// `results`: lens_name -> LensResult (metric_name -> values)
/// `hit_rates`: lens_name -> historical accuracy weight (0.0..1.0)
///
/// Returns consensus results for patterns that at least 3 lenses agree on.
pub fn weighted_consensus(
    results: &HashMap<String, LensResult>,
    hit_rates: &HashMap<String, f64>,
) -> Vec<ConsensusResult> {
    // Collect all pattern IDs across all lenses
    // A lens "agrees" on a pattern if it has non-empty results for that metric
    let mut pattern_map: HashMap<String, Vec<(String, f64)>> = HashMap::new();

    for (lens_name, lr) in results {
        let weight = hit_rates.get(lens_name).copied().unwrap_or(1.0);
        for (metric_name, values) in lr {
            if !values.is_empty() {
                pattern_map
                    .entry(metric_name.clone())
                    .or_default()
                    .push((lens_name.clone(), weight));
            }
        }
    }

    let mut consensus_results = Vec::new();

    for (pattern_id, agreeing) in pattern_map {
        let count = agreeing.len();
        if count < 3 {
            continue;
        }

        let weighted_score: f64 = agreeing.iter().map(|(_, w)| w).sum();
        let agreeing_lenses: Vec<String> = agreeing.into_iter().map(|(name, _)| name).collect();

        let level = if count >= 12 {
            ConsensusLevel::Confirmed
        } else if count >= 7 {
            ConsensusLevel::High
        } else {
            ConsensusLevel::Candidate
        };

        // mk2: classify the consensus pattern
        let (mk2_sector, mk2_confidence) = classify_consensus(&pattern_id, results);

        consensus_results.push(ConsensusResult {
            pattern_id,
            agreeing_lenses,
            weighted_score,
            level,
            mk2_sector,
            mk2_confidence,
        });
    }

    // Sort by weighted score descending
    consensus_results.sort_by(|a, b| {
        b.weighted_score
            .partial_cmp(&a.weighted_score)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    consensus_results
}

/// mk2: classify a consensus pattern by collecting all values from agreeing lenses.
fn classify_consensus(
    pattern_id: &str,
    results: &HashMap<String, LensResult>,
) -> (Option<String>, Option<f64>) {
    let mut all_values = Vec::new();
    for lr in results.values() {
        if let Some(vals) = lr.get(pattern_id) {
            all_values.extend(vals.iter().copied().filter(|v| v.is_finite()));
        }
    }
    if all_values.is_empty() {
        return (None, None);
    }

    let mut ps = crate::mk2::primes::PrimeSet::empty();
    for &v in &all_values {
        if v.abs() < 1e-10 || v.abs() > 1e6 { continue; }
        for den in &[1u64, 2, 3, 5, 6, 7, 15, 21, 35, 105, 210] {
            let num = (v * *den as f64).round() as i128;
            if num > 0 && ((num as f64 / *den as f64) - v).abs() < 1e-6 {
                for (p, _) in crate::mk2::primes::factorize(num.unsigned_abs() as u64) {
                    ps.insert(p);
                }
                for (p, _) in crate::mk2::primes::factorize(*den) {
                    ps.insert(p);
                }
                break;
            }
        }
    }

    let sectors = crate::mk2::classify_v2::default_sectors();
    let result = crate::mk2::classify_v2::classify_v2(pattern_id, &all_values, &ps, &sectors);
    (Some(result.sector.to_string()), Some(result.confidence))
}
