use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// DerivedFunctorLens: Detect homological algebra patterns — spectral sequences,
/// Tor/Ext functors, derived category structure.
///
/// n=6 connection: 6-step spectral sequence, Ext^6 vanishing indicates
/// projective dimension ≤ 5, global dimension of polynomial ring in 6 variables = 6.
pub struct DerivedFunctorLens;

impl Lens for DerivedFunctorLens {
    fn name(&self) -> &str {
        "DerivedFunctorLens"
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
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. Spectral sequence: compute iterated "differentials" d_r
        //    d_1 = first differences, d_2 = second differences, ..., d_6
        let mut current = vals.clone();
        let mut spectral_norms = Vec::with_capacity(6);
        for _r in 0..6 {
            if current.len() < 2 {
                break;
            }
            let next: Vec<f64> = current.windows(2).map(|w| w[1] - w[0]).collect();
            let norm: f64 = next.iter().map(|x| x * x).sum::<f64>().sqrt();
            spectral_norms.push(norm);
            current = next;
        }
        // Pad to length 6
        while spectral_norms.len() < 6 {
            spectral_norms.push(0.0);
        }
        result.insert("spectral_sequence_norms".to_string(), spectral_norms.clone());

        // 2. Convergence: spectral sequence converges if norms decay
        let mut is_converging = true;
        for i in 1..spectral_norms.len() {
            if spectral_norms[i] > spectral_norms[i - 1] * 1.1 && spectral_norms[i] > 1e-6 {
                is_converging = false;
                break;
            }
        }
        result.insert("spectral_convergence".to_string(), vec![if is_converging { 1.0 } else { 0.0 }]);

        // Rate of convergence
        if spectral_norms[0] > 1e-12 {
            let decay_rate = if spectral_norms[5] > 1e-15 {
                (spectral_norms[0] / spectral_norms[5]).ln() / 5.0
            } else {
                10.0 // effectively zero at step 6
            };
            result.insert("spectral_decay_rate".to_string(), vec![decay_rate]);
        }

        // 3. Tor/Ext proxy: compute "derived" interactions between feature pairs
        //    Tor measures failure of flatness, Ext measures failure of projectivity
        if d >= 2 {
            let max_dim = d.min(6);
            let mut tor_values = Vec::new();
            let mut ext_values = Vec::new();

            for p in 0..max_dim {
                for q in (p + 1)..max_dim {
                    let col_p: Vec<f64> = (0..max_n).map(|i| data[i * d + p]).collect();
                    let col_q: Vec<f64> = (0..max_n).map(|i| data[i * d + q]).collect();

                    // Tor proxy: measure non-linearity of tensor relationship
                    let mut tensor_err = 0.0;
                    let mean_p = col_p.iter().sum::<f64>() / max_n as f64;
                    let mean_q = col_q.iter().sum::<f64>() / max_n as f64;
                    for i in 0..max_n {
                        let predicted = mean_p * col_q[i] + mean_q * col_p[i] - mean_p * mean_q;
                        let actual = col_p[i] * col_q[i];
                        tensor_err += (actual - predicted).abs();
                    }
                    tor_values.push(tensor_err / max_n as f64);

                    // Ext proxy: measure obstruction to lifting morphisms
                    // Use difference of differences as obstruction
                    if col_p.len() >= 3 {
                        let dp: Vec<f64> = col_p.windows(2).map(|w| w[1] - w[0]).collect();
                        let dq: Vec<f64> = col_q.windows(2).map(|w| w[1] - w[0]).collect();
                        let mut lift_err = 0.0;
                        for i in 0..dp.len().min(dq.len()) {
                            if dp[i].abs() > 1e-12 {
                                lift_err += (dq[i] / dp[i] - dq.get(0).unwrap_or(&0.0) / dp[0].max(1e-12)).abs();
                            }
                        }
                        ext_values.push(lift_err / dp.len().max(1) as f64);
                    }
                }
            }

            if !tor_values.is_empty() {
                let avg_tor = tor_values.iter().sum::<f64>() / tor_values.len() as f64;
                result.insert("tor_obstruction".to_string(), vec![avg_tor]);
            }
            if !ext_values.is_empty() {
                let avg_ext = ext_values.iter().sum::<f64>() / ext_values.len() as f64;
                result.insert("ext_obstruction".to_string(), vec![avg_ext]);
            }
        }

        // 4. Projective dimension: find k where "Ext^k vanishes"
        //    Use the spectral_norms — the step where norm drops below threshold
        let threshold = spectral_norms[0] * 0.01;
        let mut proj_dim = 6;
        for (k, &norm) in spectral_norms.iter().enumerate() {
            if norm < threshold.max(1e-10) {
                proj_dim = k;
                break;
            }
        }
        result.insert("projective_dimension".to_string(), vec![proj_dim as f64]);

        // 5. Global dimension 6 score: how close is projective dimension to 6?
        let global_dim_score = 1.0 - ((proj_dim as f64 - 6.0).abs() / 6.0).min(1.0);
        result.insert("global_dim_six_score".to_string(), vec![global_dim_score]);

        // 6. Homological regularity: Castelnuovo-Mumford regularity proxy
        //    Max k such that H^k(F) ≠ 0
        let nonzero_steps = spectral_norms.iter().filter(|&&x| x > 1e-8).count();
        result.insert("homological_regularity".to_string(), vec![nonzero_steps as f64]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_derived_functor_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.2).exp().sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = DerivedFunctorLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("spectral_sequence_norms"));
        assert_eq!(result["spectral_sequence_norms"].len(), 6);
    }

    #[test]
    fn test_derived_functor_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = DerivedFunctorLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
