use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// RademacherComplexityLens: Statistical learning theory analysis.
///
/// Computes empirical Rademacher complexity for data:
/// - Generates Rademacher (random +-1) vectors, measures correlation with data
/// - 6-sample bound: generalization gap from 6-fold structure
/// - McDiarmid concentration inequality
/// - Generalization gap estimate
pub struct RademacherComplexityLens;

impl Lens for RademacherComplexityLens {
    fn name(&self) -> &str { "RademacherComplexityLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = shared;
        if n < 6 || d == 0 { return HashMap::new(); }

        // Empirical Rademacher complexity via deterministic Rademacher-like vectors
        // R_n(F) = E_sigma[sup_{f in F} (1/n) sum sigma_i f(x_i)]
        // We use the class of linear functions and systematic sigma patterns

        let num_trials = 2usize.pow(n.min(12) as u32); // exact for small n
        let trial_count = num_trials.min(1024);

        let mut max_correlations = Vec::new();

        for trial in 0..trial_count {
            // Generate deterministic Rademacher vector from trial index
            let sigma: Vec<f64> = (0..n).map(|i| {
                if (trial >> (i % 20)) & 1 == 0 { 1.0 } else { -1.0 }
            }).collect();

            // For each dimension, compute correlation with sigma
            let mut max_corr = 0.0f64;
            for dim in 0..d {
                let corr: f64 = (0..n).map(|i| sigma[i] * data[i * d + dim]).sum::<f64>() / n as f64;
                max_corr = max_corr.max(corr.abs());
            }
            max_correlations.push(max_corr);
        }

        // Empirical Rademacher complexity
        let rademacher = max_correlations.iter().sum::<f64>() / trial_count as f64;

        // 6-fold cross-validation generalization bound
        let k = 6usize;
        let fold_size = n / k;
        let mut fold_variances = Vec::new();
        for fold in 0..k {
            let start = fold * fold_size;
            let end = if fold == k - 1 { n } else { start + fold_size };
            // Compute mean distance within fold
            let mut fold_mean = 0.0;
            let mut count = 0;
            for dim in 0..d {
                let sum: f64 = (start..end).map(|i| data[i * d + dim]).sum();
                fold_mean += sum / (end - start).max(1) as f64;
                count += 1;
            }
            fold_mean /= count.max(1) as f64;

            // Variance within fold
            let var: f64 = (start..end).map(|i| {
                let mean_point: f64 = (0..d).map(|dim| data[i * d + dim]).sum::<f64>() / d as f64;
                (mean_point - fold_mean).powi(2)
            }).sum::<f64>() / (end - start).max(1) as f64;

            fold_variances.push(var);
        }

        let mean_fold_var = fold_variances.iter().sum::<f64>() / k as f64;
        let between_fold_var = {
            let grand_mean = fold_variances.iter().sum::<f64>() / k as f64;
            fold_variances.iter().map(|v| (v - grand_mean).powi(2)).sum::<f64>() / k as f64
        };

        // Generalization gap: 2 * R_n + sqrt(ln(2/delta) / (2n))
        let delta: f64 = 0.05;
        let gen_gap = 2.0 * rademacher + ((2.0_f64 / delta).ln() / (2.0 * n as f64)).sqrt();

        // McDiarmid bound: each point changes output by at most c_i
        // For bounded loss in [0,1]: P(|emp - true| > eps) <= 2*exp(-2*n*eps^2)
        let mcdiarmid_eps = ((2.0_f64 / delta).ln() / (2.0 * n as f64)).sqrt();

        // Massart's lemma: if hypothesis class has finite size |H|
        // R_n <= max||x|| * sqrt(2*ln(|H|)/n)
        let max_norm: f64 = (0..n).map(|i| {
            (0..d).map(|j| data[i * d + j].powi(2)).sum::<f64>().sqrt()
        }).fold(0.0f64, f64::max);
        let massart_bound = max_norm * (2.0 * (n as f64).ln() / n as f64).sqrt();

        // n=6 resonance: Rademacher complexity scaled to 6-sample regime
        let rad_6_sample = rademacher * (n as f64 / 6.0).sqrt();
        let n6_rad_match = (-((rad_6_sample - 1.0).abs() * 0.5)).exp();

        let mut result = HashMap::new();
        result.insert("rademacher_complexity".into(), vec![rademacher]);
        result.insert("generalization_gap".into(), vec![gen_gap]);
        result.insert("mcdiarmid_epsilon".into(), vec![mcdiarmid_eps]);
        result.insert("massart_bound".into(), vec![massart_bound]);
        result.insert("mean_fold_variance_6cv".into(), vec![mean_fold_var]);
        result.insert("between_fold_variance".into(), vec![between_fold_var]);
        result.insert("n6_rademacher_match".into(), vec![n6_rad_match]);
        result.insert("fold_variances".into(), fold_variances);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rademacher_complexity() {
        let mut data = Vec::new();
        for i in 0..18 {
            data.push(i as f64 * 0.1);
            data.push((i as f64 * 0.3).sin());
        }
        let n = 18;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = RademacherComplexityLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("rademacher_complexity"));
        assert!(r["generalization_gap"][0] > 0.0);
        assert_eq!(r["fold_variances"].len(), 6);
    }
}
