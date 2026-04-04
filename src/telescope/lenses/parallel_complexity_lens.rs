use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ParallelComplexityLens: Parallel algorithm complexity analysis.
///
/// Models data as a 6-processor parallel computation:
/// - Partitions points into 6 work groups via greedy load balancing
/// - Computes work (total distance sum) and span (critical path)
/// - Work-span ratio measures parallelism efficiency
/// - Brent's theorem bound: T_p >= max(W/p, S) where p=6
pub struct ParallelComplexityLens;

impl Lens for ParallelComplexityLens {
    fn name(&self) -> &str { "ParallelComplexityLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = (data, d);
        if n < 6 { return HashMap::new(); }

        let p = 6usize; // 6 processors

        // Compute total work: sum of all pairwise distances
        let mut total_work = 0.0;
        let mut edge_weights: Vec<f64> = Vec::with_capacity(n * (n - 1) / 2);
        for i in 0..n {
            for j in (i + 1)..n {
                let dist = shared.dist(i, j);
                total_work += dist;
                edge_weights.push(dist);
            }
        }
        edge_weights.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));

        // Greedy load balancing across 6 processors (LPT scheduling)
        let mut processor_load = [0.0f64; 6];
        for &w in &edge_weights {
            // Assign to least loaded processor
            let min_idx = processor_load
                .iter()
                .enumerate()
                .min_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                .map(|(i, _)| i)
                .unwrap_or(0);
            processor_load[min_idx] += w;
        }

        // Span = makespan (max processor load)
        let span = processor_load
            .iter()
            .cloned()
            .fold(0.0f64, f64::max);

        // Ideal parallel time
        let ideal_time = total_work / p as f64;

        // Work-span ratio (parallelism)
        let parallelism = if span > 1e-15 { total_work / span } else { 0.0 };

        // Efficiency: how close to ideal p-way parallelism
        let efficiency = if span > 1e-15 { ideal_time / span } else { 0.0 };

        // Brent bound: T_p >= max(W/p, S)
        let brent_bound = ideal_time.max(span);
        let brent_ratio = if brent_bound > 1e-15 { span / brent_bound } else { 1.0 };

        // Load imbalance: coefficient of variation across 6 processors
        let mean_load = processor_load.iter().sum::<f64>() / p as f64;
        let load_var = processor_load.iter().map(|l| (l - mean_load).powi(2)).sum::<f64>() / p as f64;
        let load_cv = if mean_load > 1e-15 { load_var.sqrt() / mean_load } else { 0.0 };

        // n=6 resonance: parallelism closeness to 6
        let n6_resonance = (-((parallelism - 6.0).abs() * 0.3)).exp();

        let mut result = HashMap::new();
        result.insert("total_work".into(), vec![total_work]);
        result.insert("span".into(), vec![span]);
        result.insert("parallelism".into(), vec![parallelism]);
        result.insert("efficiency".into(), vec![efficiency]);
        result.insert("brent_ratio".into(), vec![brent_ratio]);
        result.insert("load_imbalance_cv".into(), vec![load_cv]);
        result.insert("processor_loads".into(), processor_load.to_vec());
        result.insert("n6_resonance".into(), vec![n6_resonance]);
        result.insert("score".to_string(), vec![result["total_work"][0].min(1.0).max(0.0)]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parallel_complexity() {
        let mut data = Vec::new();
        for i in 0..12 {
            data.push(i as f64);
            data.push((i * 2) as f64);
        }
        let n = 12;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = ParallelComplexityLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("parallelism"));
        assert!(r["efficiency"][0] > 0.0);
        assert!(r["processor_loads"].len() == 6);
    }
}
