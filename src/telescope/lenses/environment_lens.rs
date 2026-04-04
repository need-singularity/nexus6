use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors, shannon_entropy};

/// n=6 environment constants (BT-118~122)
const N: f64 = 6.0;        // Kyoto 6 greenhouse gases, 6 major plastics
const SIGMA: f64 = 12.0;   // troposphere 12km
const TAU: f64 = 4.0;      // 4 seasons
const PHI: f64 = 2.0;
const SOPFR: f64 = 5.0;

/// EnvironmentLens: Detect environmental/ecological patterns in data.
///
/// Metrics: cycle_detection, trend_strength, anomaly_rate,
///          seasonal_decomposition, diversity_index, n6_environment_score
pub struct EnvironmentLens;

impl Lens for EnvironmentLens {
    fn name(&self) -> &str { "EnvironmentLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. Cycle detection: check for periodicity at tau=4 (seasonal) intervals
        let mut cycle_score = 0.0;
        let mut cycle_count = 0;
        for col_data in &columns {
            let col_mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
            let col_var: f64 = col_data.iter().map(|x| (x - col_mean).powi(2)).sum::<f64>();
            if col_var < 1e-12 { continue; }
            // Test lags corresponding to n=6 constants: 4 (seasons), 6, 12
            for &lag in &[4_usize, 6, 12] {
                if lag >= n { continue; }
                let mut acf = 0.0;
                for i in 0..(n - lag) {
                    acf += (col_data[i] - col_mean) * (col_data[i + lag] - col_mean);
                }
                acf /= col_var;
                if acf > cycle_score { cycle_score = acf; }
            }
            cycle_count += 1;
        }
        cycle_score = cycle_score.max(0.0).min(1.0);

        // 2. Trend strength: linear regression R² across features
        let mut trend_strength = 0.0;
        for col_data in &columns {
            let col_n = col_data.len() as f64;
            let x_mean = (col_n - 1.0) / 2.0;
            let y_mean = col_data.iter().sum::<f64>() / col_n;
            let mut ss_xy = 0.0;
            let mut ss_xx = 0.0;
            let mut ss_yy = 0.0;
            for (i, &y) in col_data.iter().enumerate() {
                let x = i as f64 - x_mean;
                let dy = y - y_mean;
                ss_xy += x * dy;
                ss_xx += x * x;
                ss_yy += dy * dy;
            }
            if ss_xx > 1e-12 && ss_yy > 1e-12 {
                let r_sq = (ss_xy * ss_xy) / (ss_xx * ss_yy);
                trend_strength += r_sq;
            }
        }
        trend_strength /= d.max(1) as f64;

        // 3. Anomaly rate: fraction of points beyond 2σ from mean
        let mut anomaly_count = 0;
        let mut total_points = 0;
        for col in 0..d {
            let std = vars[col].sqrt().max(1e-12);
            let threshold = 2.0 * std;
            for &val in &columns[col] {
                total_points += 1;
                if (val - means[col]).abs() > threshold {
                    anomaly_count += 1;
                }
            }
        }
        let anomaly_rate = anomaly_count as f64 / total_points.max(1) as f64;

        // 4. Seasonal decomposition: variance explained by tau=4 grouping
        let mut seasonal_score = 0.0;
        for col_data in &columns {
            let season_len = TAU as usize;
            if season_len == 0 || col_data.len() < season_len * 2 { continue; }
            let col_mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
            let total_ss: f64 = col_data.iter().map(|x| (x - col_mean).powi(2)).sum();
            if total_ss < 1e-12 { continue; }
            // Group means by season
            let mut season_means = vec![0.0; season_len];
            let mut season_counts = vec![0usize; season_len];
            for (i, &v) in col_data.iter().enumerate() {
                let s = i % season_len;
                season_means[s] += v;
                season_counts[s] += 1;
            }
            for s in 0..season_len {
                if season_counts[s] > 0 { season_means[s] /= season_counts[s] as f64; }
            }
            let between_ss: f64 = (0..season_len)
                .map(|s| season_counts[s] as f64 * (season_means[s] - col_mean).powi(2))
                .sum();
            seasonal_score += between_ss / total_ss;
        }
        seasonal_score /= d.max(1) as f64;

        // 5. Diversity index: Shannon entropy of feature distribution
        let n_bins = (n as f64).sqrt().max(2.0) as usize;
        let diversity = shannon_entropy(&columns[0], n_bins);

        // 6. Composite n6 environment score
        let n6_score = 0.2 * cycle_score
            + 0.2 * trend_strength.min(1.0)
            + 0.2 * (1.0 - anomaly_rate).max(0.0) // low anomaly = healthy
            + 0.2 * seasonal_score.min(1.0)
            + 0.2 * (diversity / 5.0).min(1.0);

        let mut result = HashMap::new();
        result.insert("cycle_detection".into(), vec![cycle_score]);
        result.insert("trend_strength".into(), vec![trend_strength]);
        result.insert("anomaly_rate".into(), vec![anomaly_rate]);
        result.insert("seasonal_decomposition".into(), vec![seasonal_score]);
        result.insert("diversity_index".into(), vec![diversity]);
        result.insert("n6_environment_score".into(), vec![n6_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_environment_basic() {
        // Simulate seasonal data: sin with period 4 + trend
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64;
            (t * std::f64::consts::PI / 2.0).sin() * 5.0 + t * 0.05
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = EnvironmentLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("cycle_detection"));
        assert!(result.contains_key("seasonal_decomposition"));
        assert!(result.contains_key("n6_environment_score"));
    }
}
