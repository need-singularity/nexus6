use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// n=6 medicine constants
const N: f64 = 6.0;        // CN=6 in drug binding (octahedral coordination)
const SIGMA: f64 = 12.0;   // 12 cranial nerves
const TAU: f64 = 4.0;      // 4 vital signs
const PHI: f64 = 2.0;      // bilateral symmetry
const J2: f64 = 24.0;      // 24-hour circadian cycle

/// MedicineLens: Detect biomedical patterns in data.
///
/// Metrics: vital_regularity, dose_response, threshold_detection,
///          recovery_rate, circadian_alignment, n6_medicine_score
pub struct MedicineLens;

impl Lens for MedicineLens {
    fn name(&self) -> &str { "MedicineLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. Vital regularity: low coefficient of variation = stable vitals
        let mut vital_reg = 0.0;
        for col in 0..d {
            let mean_abs = means[col].abs().max(1e-12);
            let cv = vars[col].sqrt() / mean_abs;
            vital_reg += (-cv).exp(); // low CV = high regularity
        }
        vital_reg /= d as f64;

        // 2. Dose-response: detect sigmoid-like pattern (monotone + saturation)
        let mut dose_response = 0.0;
        for col_data in &columns {
            if col_data.len() < 6 { continue; }
            // Check monotonicity in first half, saturation in second half
            let mid = col_data.len() / 2;
            let first_half = &col_data[..mid];
            let second_half = &col_data[mid..];

            // Monotonicity: fraction of increasing consecutive pairs
            let mut increases = 0;
            for i in 0..(first_half.len() - 1) {
                if first_half[i + 1] >= first_half[i] { increases += 1; }
            }
            let mono = increases as f64 / (first_half.len() - 1).max(1) as f64;

            // Saturation: low variance in second half relative to first
            let fh_var = first_half.iter().map(|x| {
                let m = first_half.iter().sum::<f64>() / first_half.len() as f64;
                (x - m).powi(2)
            }).sum::<f64>() / first_half.len() as f64;
            let sh_var = second_half.iter().map(|x| {
                let m = second_half.iter().sum::<f64>() / second_half.len() as f64;
                (x - m).powi(2)
            }).sum::<f64>() / second_half.len() as f64;

            let saturation = if fh_var > 1e-12 {
                (1.0 - sh_var / fh_var).max(0.0).min(1.0)
            } else { 0.0 };

            dose_response += mono * 0.5 + saturation * 0.5;
        }
        dose_response /= d.max(1) as f64;

        // 3. Threshold detection: find sharp transitions (step-like changes)
        let mut threshold_score = 0.0;
        for col_data in &columns {
            if col_data.len() < 3 { continue; }
            let diffs: Vec<f64> = col_data.windows(2).map(|w| (w[1] - w[0]).abs()).collect();
            let mean_diff = diffs.iter().sum::<f64>() / diffs.len() as f64;
            if mean_diff < 1e-12 { continue; }
            // Count jumps > 3x mean difference
            let jumps = diffs.iter().filter(|&&d| d > 3.0 * mean_diff).count();
            threshold_score += (jumps as f64 / diffs.len() as f64).min(0.3);
        }
        threshold_score /= d.max(1) as f64;
        // Normalize: some threshold is good (drug effect), too many = noise
        threshold_score = (threshold_score * 10.0).min(1.0);

        // 4. Recovery rate: after perturbation, how fast data returns to baseline
        let mut recovery = 0.0;
        for col_data in &columns {
            if col_data.len() < 6 { continue; }
            let baseline = col_data.iter().sum::<f64>() / col_data.len() as f64;
            // Find max deviation point
            let (max_idx, _) = col_data.iter().enumerate()
                .max_by(|(_, a), (_, b)| ((**a - baseline).abs()).partial_cmp(&((**b - baseline).abs())).unwrap_or(std::cmp::Ordering::Equal))
                .unwrap_or((0, &0.0));
            // Measure how quickly subsequent values return to baseline
            if max_idx < col_data.len() - 2 {
                let peak_dev = (col_data[max_idx] - baseline).abs();
                if peak_dev > 1e-12 {
                    let after = &col_data[(max_idx + 1)..];
                    let mut steps_to_half = after.len();
                    for (i, &v) in after.iter().enumerate() {
                        if (v - baseline).abs() < peak_dev * 0.5 {
                            steps_to_half = i + 1;
                            break;
                        }
                    }
                    // Faster recovery = higher score
                    recovery += (1.0 - steps_to_half as f64 / after.len() as f64).max(0.0);
                }
            }
        }
        recovery /= d.max(1) as f64;

        // 5. Circadian alignment: check for J2=24 periodicity
        let mut circadian = 0.0;
        if n >= 24 {
            for col_data in &columns {
                let col_mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
                let col_var: f64 = col_data.iter().map(|x| (x - col_mean).powi(2)).sum();
                if col_var < 1e-12 { continue; }
                let lag = 24.min(n - 1);
                let mut acf = 0.0;
                for i in 0..(n - lag) {
                    acf += (col_data[i] - col_mean) * (col_data[i + lag] - col_mean);
                }
                acf /= col_var;
                circadian += acf.max(0.0);
            }
            circadian /= d.max(1) as f64;
        }

        // 6. Composite
        let n6_score = 0.2 * vital_reg
            + 0.2 * dose_response
            + 0.2 * threshold_score
            + 0.2 * recovery
            + 0.2 * circadian.min(1.0);

        let mut result = HashMap::new();
        result.insert("vital_regularity".into(), vec![vital_reg]);
        result.insert("dose_response".into(), vec![dose_response]);
        result.insert("threshold_detection".into(), vec![threshold_score]);
        result.insert("recovery_rate".into(), vec![recovery]);
        result.insert("circadian_alignment".into(), vec![circadian]);
        result.insert("n6_medicine_score".into(), vec![n6_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_medicine_basic() {
        // Simulate dose-response: sigmoid-like ramp then plateau
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.2 - 3.0;
            1.0 / (1.0 + (-t).exp()) * 10.0
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = MedicineLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("vital_regularity"));
        assert!(result.contains_key("dose_response"));
        assert!(result.contains_key("n6_medicine_score"));
    }
}
