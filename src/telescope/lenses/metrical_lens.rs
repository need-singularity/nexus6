use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// MetricalLens: Detect rhythmic/metrical structure in data.
///
/// Inspired by music theory: 6/8 time signature, hemiola (3-against-2),
/// and polyrhythmic complexity. Treats each data column as a time series
/// and measures periodicity at musically meaningful divisions of 6.
///
/// Metrics: six_eight_strength, hemiola_score, polyrhythm_complexity,
///          beat_regularity, metric_hierarchy, n6_metrical_score
pub struct MetricalLens;

impl Lens for MetricalLens {
    fn name(&self) -> &str { "MetricalLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // Helper: autocorrelation at a given lag
        let acf = |col: &[f64], lag: usize| -> f64 {
            let mean = col.iter().sum::<f64>() / col.len() as f64;
            let var: f64 = col.iter().map(|x| (x - mean).powi(2)).sum::<f64>();
            if var < 1e-12 || lag >= col.len() { return 0.0; }
            let mut sum = 0.0;
            for i in 0..(col.len() - lag) {
                sum += (col[i] - mean) * (col[i + lag] - mean);
            }
            sum / var
        };

        // 1. 6/8 strength: autocorrelation at lag=6 (the bar length in 6/8 time)
        let mut six_eight_sum = 0.0;
        for col in &columns {
            let a6 = acf(col, 6);
            let a3 = acf(col, 3); // strong beat subdivision
            six_eight_sum += (a6.max(0.0) + 0.5 * a3.max(0.0)) / 1.5;
        }
        let six_eight_strength = (six_eight_sum / d as f64).min(1.0).max(0.0);

        // 2. Hemiola score: ratio of period-3 to period-2 strength (3-against-2)
        //    Perfect hemiola = both period-2 and period-3 equally strong
        let mut hemiola_sum = 0.0;
        for col in &columns {
            let a2 = acf(col, 2).max(0.0);
            let a3 = acf(col, 3).max(0.0);
            let total = a2 + a3;
            if total > 1e-12 {
                // Closer to 0.5/0.5 balance = stronger hemiola
                let balance = 1.0 - (a2 / total - 0.5).abs() * 2.0;
                hemiola_sum += balance * total.min(1.0);
            }
        }
        let hemiola_score = (hemiola_sum / d as f64).min(1.0).max(0.0);

        // 3. Polyrhythm complexity: how many distinct periodicities coexist?
        //    Check lags 2,3,4,6 (divisors and musically relevant subdivisions of 6)
        let check_lags = [2, 3, 4, 6];
        let mut poly_sum = 0.0;
        for col in &columns {
            let mut active_periods = 0;
            for &lag in &check_lags {
                if lag < n && acf(col, lag) > 0.2 {
                    active_periods += 1;
                }
            }
            poly_sum += active_periods as f64 / check_lags.len() as f64;
        }
        let polyrhythm_complexity = (poly_sum / d as f64).min(1.0);

        // 4. Beat regularity: consistency of peaks at period-6 intervals
        let mut regularity_sum = 0.0;
        for col in &columns {
            let mean_val = col.iter().sum::<f64>() / col.len() as f64;
            let mut beat_values: Vec<f64> = Vec::new();
            let mut idx = 0;
            while idx < col.len() {
                // Downbeat position every 6 samples
                beat_values.push(col[idx] - mean_val);
                idx += 6;
            }
            if beat_values.len() >= 2 {
                let bm = beat_values.iter().sum::<f64>() / beat_values.len() as f64;
                let bv: f64 = beat_values.iter().map(|x| (x - bm).powi(2)).sum::<f64>()
                    / beat_values.len() as f64;
                let mean_abs = beat_values.iter().map(|x| x.abs()).sum::<f64>()
                    / beat_values.len() as f64;
                if mean_abs > 1e-12 {
                    regularity_sum += (-bv.sqrt() / mean_abs).exp();
                }
            }
        }
        let beat_regularity = (regularity_sum / d as f64).min(1.0).max(0.0);

        // 5. Metric hierarchy: ratio of acf(6) to acf(3) to acf(2) — hierarchical nesting
        //    In a well-formed 6/8 meter: acf(6) >= acf(3) >= acf(2)
        let mut hierarchy_sum = 0.0;
        for col in &columns {
            let a2 = acf(col, 2).max(0.0);
            let a3 = acf(col, 3).max(0.0);
            let a6 = acf(col, 6).max(0.0);
            let total = a2 + a3 + a6;
            if total > 1e-12 {
                // Score: 1.0 if a6 >= a3 >= a2 (proper hierarchy)
                let hier = if a6 >= a3 && a3 >= a2 { 1.0 }
                    else if a6 >= a3 || a3 >= a2 { 0.5 }
                    else { 0.1 };
                hierarchy_sum += hier * (total / 3.0).min(1.0);
            }
        }
        let metric_hierarchy = (hierarchy_sum / d as f64).min(1.0).max(0.0);

        let n6_metrical_score = 0.25 * six_eight_strength
            + 0.20 * hemiola_score
            + 0.15 * polyrhythm_complexity
            + 0.20 * beat_regularity
            + 0.20 * metric_hierarchy;

        let mut result = HashMap::new();
        result.insert("six_eight_strength".into(), vec![six_eight_strength]);
        result.insert("hemiola_score".into(), vec![hemiola_score]);
        result.insert("polyrhythm_complexity".into(), vec![polyrhythm_complexity]);
        result.insert("beat_regularity".into(), vec![beat_regularity]);
        result.insert("metric_hierarchy".into(), vec![metric_hierarchy]);
        result.insert("n6_metrical_score".into(), vec![n6_metrical_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrical_basic() {
        // Simulate 6/8 time: strong beats at positions 0, 3 within each bar of 6
        let data: Vec<f64> = (0..60).map(|i| {
            let pos = i % 6;
            if pos == 0 { 1.0 } else if pos == 3 { 0.7 } else { 0.2 }
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = MetricalLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("six_eight_strength"));
        assert!(result.contains_key("n6_metrical_score"));
    }
}
