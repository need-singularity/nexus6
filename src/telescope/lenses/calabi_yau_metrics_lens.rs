use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// CalabiYauMetricsLens: Detect Calabi-Yau manifold patterns —
/// Ricci-flat metrics, Kahler structure, Hodge numbers.
///
/// n=6 connection: CY3 is a 6-dimensional (real) manifold,
/// the canonical example for string compactification.
/// Hodge numbers h^{1,1} and h^{2,1} encode geometry.
pub struct CalabiYauMetricsLens;

impl Lens for CalabiYauMetricsLens {
    fn name(&self) -> &str {
        "CalabiYauMetricsLens"
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

        // 1. Ricci-flatness: compute proxy Ricci curvature from data
        //    Ricci = 0 for CY manifolds
        //    Use second differences as curvature proxy
        let max_dim = d.min(6);
        let mut ricci_proxy = vec![0.0f64; max_dim];
        for j in 0..max_dim {
            let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
            // Second derivative approximation
            let mut curv_sum = 0.0;
            let mut count = 0;
            for i in 1..col.len() - 1 {
                let second_diff = col[i + 1] - 2.0 * col[i] + col[i - 1];
                curv_sum += second_diff.abs();
                count += 1;
            }
            ricci_proxy[j] = if count > 0 { curv_sum / count as f64 } else { 0.0 };
        }
        let avg_ricci = ricci_proxy.iter().sum::<f64>() / ricci_proxy.len() as f64;
        result.insert("ricci_curvature_proxy".to_string(), ricci_proxy);
        // Lower = more Ricci-flat
        let ricci_flatness = (-avg_ricci).exp(); // 1.0 when flat, <1 when curved
        result.insert("ricci_flatness_score".to_string(), vec![ricci_flatness.min(1.0)]);

        // 2. Kahler structure: check if there exists a compatible (J, g, ω) triple
        //    Proxy: check if feature covariance has block-diagonal (complex) structure
        if d >= 2 {
            let mut cov = vec![0.0f64; max_dim * max_dim];
            let mut means = vec![0.0f64; max_dim];
            for i in 0..max_n {
                for j in 0..max_dim {
                    means[j] += data[i * d + j];
                }
            }
            for j in 0..max_dim {
                means[j] /= max_n as f64;
            }
            for i in 0..max_n {
                for p in 0..max_dim {
                    for q in 0..max_dim {
                        cov[p * max_dim + q] += (data[i * d + p] - means[p])
                            * (data[i * d + q] - means[q]);
                    }
                }
            }
            for v in cov.iter_mut() {
                *v /= max_n as f64;
            }

            // Kahler: J² = -I implies specific block structure
            // Check 2x2 blocks for rotation-like pattern
            let mut kahler_score = 0.0;
            let mut kahler_count = 0;
            let pairs = max_dim / 2;
            for p in 0..pairs {
                let i = p * 2;
                let j = p * 2 + 1;
                let a = cov[i * max_dim + i]; // σ²_i
                let b = cov[j * max_dim + j]; // σ²_j
                let c = cov[i * max_dim + j]; // σ_ij
                // Kahler requires symmetric variance and antisymmetric cross terms
                if a + b > 1e-12 {
                    kahler_score += 1.0 - (a - b).abs() / (a + b); // variance symmetry
                    kahler_count += 1;
                }
            }
            let avg_kahler = if kahler_count > 0 { kahler_score / kahler_count as f64 } else { 0.0 };
            result.insert("kahler_score".to_string(), vec![avg_kahler]);
        }

        // 3. Hodge diamond: for CY3, the diamond is determined by h^{1,1} and h^{2,1}
        //    Estimate from "harmonic" content of data
        //    h^{0,0} = h^{3,3} = 1, h^{1,1}, h^{2,1} are free
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // Fourier analysis to estimate "harmonic" forms
        let mut harmonic_powers = Vec::new();
        for k in 1..max_n.min(20) {
            let mut re = 0.0;
            let mut im = 0.0;
            for (j, &v) in vals.iter().enumerate() {
                let angle = 2.0 * std::f64::consts::PI * k as f64 * j as f64 / vals.len() as f64;
                re += v * angle.cos();
                im += v * angle.sin();
            }
            harmonic_powers.push((re * re + im * im) / (vals.len() as f64).powi(2));
        }

        // h^{1,1} proxy: number of significant harmonic modes
        let power_threshold = harmonic_powers.iter().cloned().fold(0.0f64, f64::max) * 0.1;
        let h11_proxy = harmonic_powers.iter().filter(|&&p| p > power_threshold).count();
        result.insert("hodge_h11_proxy".to_string(), vec![h11_proxy as f64]);

        // h^{2,1} proxy: from cross-dimensional harmonics
        let h21_proxy = if d >= 2 {
            let mut cross_modes = 0;
            for k in 1..max_n.min(10) {
                for dim_pair in 0..d.min(6) / 2 {
                    let col1: Vec<f64> = (0..max_n).map(|i| data[i * d + dim_pair * 2]).collect();
                    let col2: Vec<f64> = (0..max_n).map(|i| data[i * d + dim_pair * 2 + 1]).collect();
                    let mut cross_power = 0.0;
                    for j in 0..max_n {
                        let angle = 2.0 * std::f64::consts::PI * k as f64 * j as f64 / max_n as f64;
                        cross_power += col1[j] * angle.cos() * col2[j] * angle.sin();
                    }
                    if (cross_power / max_n as f64).abs() > power_threshold {
                        cross_modes += 1;
                    }
                }
            }
            cross_modes
        } else {
            0
        };
        result.insert("hodge_h21_proxy".to_string(), vec![h21_proxy as f64]);

        // 4. Euler characteristic: χ = 2(h^{1,1} - h^{2,1}) for CY3
        let euler_cy3 = 2.0 * (h11_proxy as f64 - h21_proxy as f64);
        result.insert("euler_characteristic_cy3".to_string(), vec![euler_cy3]);

        // 5. SU(3) holonomy check: CY3 has SU(3) holonomy
        //    Measure if data has U(3)-like structure (3 complex dimensions)
        let dim_six_score = if d >= 6 {
            // Check if the 6 dimensions pair naturally into 3 complex dims
            let mut pairing_score = 0.0;
            for p in 0..3 {
                let i = p * 2;
                let j = p * 2 + 1;
                let col_i: Vec<f64> = (0..max_n).map(|r| data[r * d + i]).collect();
                let col_j: Vec<f64> = (0..max_n).map(|r| data[r * d + j]).collect();
                // Check if (col_i, col_j) have similar statistics
                let mi = col_i.iter().sum::<f64>() / max_n as f64;
                let mj = col_j.iter().sum::<f64>() / max_n as f64;
                let vi: f64 = col_i.iter().map(|x| (x - mi).powi(2)).sum::<f64>() / max_n as f64;
                let vj: f64 = col_j.iter().map(|x| (x - mj).powi(2)).sum::<f64>() / max_n as f64;
                if vi + vj > 1e-12 {
                    pairing_score += 1.0 - (vi - vj).abs() / (vi + vj);
                }
            }
            pairing_score / 3.0
        } else {
            0.0
        };
        result.insert("su3_holonomy_score".to_string(), vec![dim_six_score]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_calabi_yau_basic() {
        // Quasi-flat data (small curvature)
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.01).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = CalabiYauMetricsLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("ricci_flatness_score"));
        assert!(result.contains_key("kahler_score"));
    }

    #[test]
    fn test_calabi_yau_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = CalabiYauMetricsLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
