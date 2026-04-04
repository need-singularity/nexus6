use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// BirchSwinnertonDyerLens: Detect elliptic curve / L-function patterns in data.
///
/// n=6 connection: conductor = 6k, L-function zero analysis at s=1,
/// rank estimation via sign changes analogous to analytic rank.
pub struct BirchSwinnertonDyerLens;

/// Approximate L-function partial sum: L(s) = Σ a_n / n^s
/// Uses data values as Fourier coefficients a_n.
fn l_function_partial(coeffs: &[f64], s: f64, max_terms: usize) -> f64 {
    let mut sum = 0.0;
    for (i, &a) in coeffs.iter().enumerate().take(max_terms) {
        let n = (i + 1) as f64;
        sum += a / n.powf(s);
    }
    sum
}

/// Estimate analytic rank by counting sign changes of L near s=1.
fn estimate_analytic_rank(coeffs: &[f64], max_terms: usize) -> (f64, usize) {
    let steps = 20;
    let mut sign_changes = 0usize;
    let mut prev_sign = 0i32;
    let mut l_at_one = 0.0;

    for step in 0..=steps {
        let s = 0.5 + (step as f64 / steps as f64) * 1.5; // s in [0.5, 2.0]
        let val = l_function_partial(coeffs, s, max_terms);
        let sign = if val > 1e-10 { 1 } else if val < -1e-10 { -1 } else { 0 };
        if sign != 0 && prev_sign != 0 && sign != prev_sign {
            sign_changes += 1;
        }
        if sign != 0 {
            prev_sign = sign;
        }
        if step == steps / 2 {
            l_at_one = val; // approximate L(1)
        }
    }
    (l_at_one, sign_changes)
}

/// Check conductor divisibility by 6.
fn conductor_six_score(data: &[f64], n: usize, d: usize) -> f64 {
    // Use pairwise distances as proxy for conductor components
    let mut count_div6 = 0usize;
    let mut total = 0usize;
    for i in 0..n.min(50) {
        for j in (i + 1)..n.min(50) {
            let mut dist_sq = 0.0;
            for k in 0..d {
                let diff = data[i * d + k] - data[j * d + k];
                dist_sq += diff * diff;
            }
            let dist_int = dist_sq.sqrt().round() as i64;
            if dist_int > 0 {
                total += 1;
                if dist_int % 6 == 0 {
                    count_div6 += 1;
                }
            }
        }
    }
    if total > 0 { count_div6 as f64 / total as f64 } else { 0.0 }
}

impl Lens for BirchSwinnertonDyerLens {
    fn name(&self) -> &str {
        "BirchSwinnertonDyerLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);

        // 1. Use first-dimension values as L-function coefficients
        let coeffs: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();
        let (l_at_one, sign_changes) = estimate_analytic_rank(&coeffs, max_n);

        result.insert("l_value_at_one".to_string(), vec![l_at_one]);
        result.insert("analytic_rank_estimate".to_string(), vec![sign_changes as f64]);

        // 2. Conductor mod-6 score
        let cond_score = conductor_six_score(data, max_n, d);
        result.insert("conductor_six_score".to_string(), vec![cond_score]);

        // 3. Tate-Shafarevich analogy: measure how far data deviates from
        //    expected rank structure. Compute L''(1) / 2 as curvature.
        let eps = 0.05;
        let l_plus = l_function_partial(&coeffs, 1.0 + eps, max_n);
        let l_minus = l_function_partial(&coeffs, 1.0 - eps, max_n);
        let l_center = l_function_partial(&coeffs, 1.0, max_n);
        let curvature = (l_plus - 2.0 * l_center + l_minus) / (eps * eps);
        result.insert("l_curvature_at_one".to_string(), vec![curvature]);

        // 4. BSD ratio: |L(1)| / (Ω · R) analogy
        //    Use variance as regulator proxy, mean absolute value as period proxy
        let mean_abs = coeffs.iter().map(|x| x.abs()).sum::<f64>() / coeffs.len() as f64;
        let variance = {
            let mean = coeffs.iter().sum::<f64>() / coeffs.len() as f64;
            coeffs.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / coeffs.len() as f64
        };
        let bsd_ratio = if mean_abs > 1e-12 && variance > 1e-12 {
            l_at_one.abs() / (mean_abs * variance.sqrt())
        } else {
            0.0
        };
        result.insert("bsd_ratio".to_string(), vec![bsd_ratio]);

        // 5. n=6 resonance: how well sign_changes aligns with multiples of 6
        let six_resonance = if sign_changes > 0 {
            1.0 - ((sign_changes % 6) as f64 / 6.0)
        } else {
            0.0
        };
        result.insert("six_resonance".to_string(), vec![six_resonance]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_bsd_lens_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.1).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = BirchSwinnertonDyerLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("l_value_at_one"));
        assert!(result.contains_key("bsd_ratio"));
    }

    #[test]
    fn test_bsd_lens_small_n() {
        let data = vec![1.0, 2.0, 3.0];
        let shared = SharedData::compute(&data, 3, 1);
        let result = BirchSwinnertonDyerLens.scan(&data, 3, 1, &shared);
        assert!(result.is_empty());
    }
}
