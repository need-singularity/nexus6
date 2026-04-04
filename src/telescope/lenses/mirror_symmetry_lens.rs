use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MirrorSymmetryAlgLens: Detect mirror symmetry patterns from algebraic geometry —
/// Hodge diamond symmetry, mirror map, genus-zero Gromov-Witten invariants.
///
/// n=6 connection: mirror symmetry for CY3 (6 real dimensions),
/// exchanges h^{1,1} ↔ h^{2,1} in the Hodge diamond.
pub struct MirrorSymmetryAlgLens;

impl Lens for MirrorSymmetryAlgLens {
    fn name(&self) -> &str {
        "MirrorSymmetryAlgLens"
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
        let max_dim = d.min(6);

        // 1. Hodge diamond symmetry: h^{p,q} = h^{q,p} (complex conjugation)
        //    and h^{p,q} = h^{n-p,n-q} (Serre duality for n=3)
        //    Build "Hodge numbers" from frequency content across dimension pairs
        if max_dim >= 2 {
            let pairs = max_dim / 2;
            let mut hodge_pq = Vec::new(); // (p,q) Hodge-like numbers
            let mut hodge_qp = Vec::new();

            for p in 0..pairs {
                for q in 0..pairs {
                    // h^{p,q} proxy: mixed frequency content between dim 2p and 2q+1
                    let col_a: Vec<f64> = (0..max_n).map(|i| data[i * d + (2 * p).min(max_dim - 1)]).collect();
                    let col_b: Vec<f64> = (0..max_n).map(|i| data[i * d + (2 * q + 1).min(max_dim - 1)]).collect();

                    let mut cross = 0.0;
                    for k in 1..max_n.min(10) {
                        let mut a_re = 0.0;
                        let mut b_re = 0.0;
                        for j in 0..max_n {
                            let angle = 2.0 * std::f64::consts::PI * k as f64 * j as f64 / max_n as f64;
                            a_re += col_a[j] * angle.cos();
                            b_re += col_b[j] * angle.cos();
                        }
                        cross += (a_re * b_re).abs() / (max_n as f64).powi(2);
                    }
                    hodge_pq.push(cross);
                    // Mirror: swap p,q
                    hodge_qp.push(cross); // Will be computed differently for actual asymmetry
                }
            }

            // Hodge symmetry score: h^{p,q} ≈ h^{q,p}
            // Since we used same formula, compute actual asymmetry from different orderings
            let mut mirror_score = 0.0;
            let mut mirror_count = 0;
            for p in 0..pairs {
                for q in (p + 1)..pairs {
                    let hpq = hodge_pq[p * pairs + q];
                    let hqp = hodge_pq[q * pairs + p];
                    if hpq + hqp > 1e-12 {
                        mirror_score += 1.0 - (hpq - hqp).abs() / (hpq + hqp);
                        mirror_count += 1;
                    }
                }
            }
            let avg_mirror = if mirror_count > 0 { mirror_score / mirror_count as f64 } else { 0.0 };
            result.insert("hodge_symmetry_score".to_string(), vec![avg_mirror]);
        }

        // 2. Mirror map: the mirror involution exchanges A-model and B-model
        //    A-model: counts curves (enumerative), B-model: periods (variational)
        //    Proxy: compare "counting" vs "averaging" analysis of data
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // A-model proxy: count threshold crossings (enumerative)
        let mean = vals.iter().sum::<f64>() / vals.len() as f64;
        let crossings = vals.windows(2)
            .filter(|w| (w[0] - mean) * (w[1] - mean) < 0.0)
            .count();
        let a_model = crossings as f64 / vals.len() as f64;

        // B-model proxy: integral/period computation
        let integral: f64 = vals.iter().map(|x| (x - mean).abs()).sum::<f64>() / vals.len() as f64;
        let b_model = integral;

        result.insert("a_model_crossings".to_string(), vec![a_model]);
        result.insert("b_model_period".to_string(), vec![b_model]);

        // Mirror symmetry: A and B models should be "dual"
        if a_model > 1e-12 && b_model > 1e-12 {
            let mirror_duality = 1.0 - (a_model - b_model).abs() / (a_model + b_model);
            result.insert("mirror_duality_score".to_string(), vec![mirror_duality.max(0.0)]);
        }

        // 3. Gromov-Witten invariants proxy: "curve counting" in data
        //    Count monotone subsequences of various lengths
        let mut gw_counts = vec![0usize; 6]; // curves of "degree" 1-6
        for deg in 1..=6 {
            let mut count = 0;
            for i in 0..vals.len().saturating_sub(deg) {
                let mut increasing = true;
                for k in 0..deg {
                    if vals[i + k + 1] <= vals[i + k] {
                        increasing = false;
                        break;
                    }
                }
                if increasing {
                    count += 1;
                }
            }
            gw_counts[deg - 1] = count;
        }
        let gw_f64: Vec<f64> = gw_counts.iter().map(|&c| c as f64).collect();
        result.insert("gromov_witten_proxy".to_string(), gw_f64);

        // 4. Instanton corrections: exponentially suppressed contributions
        //    Check for exponential decay in the GW invariant sequence
        if gw_counts[0] > 0 {
            let mut decay_rate = 0.0;
            let mut decay_count = 0;
            for i in 1..6 {
                if gw_counts[i] > 0 && gw_counts[i - 1] > 0 {
                    let ratio = gw_counts[i] as f64 / gw_counts[i - 1] as f64;
                    if ratio > 0.0 && ratio < 1.0 {
                        decay_rate += ratio.ln().abs();
                        decay_count += 1;
                    }
                }
            }
            if decay_count > 0 {
                result.insert("instanton_decay_rate".to_string(),
                    vec![decay_rate / decay_count as f64]);
            }
        }

        // 5. Dimension 6 signature: CY3 has complex dim 3, real dim 6
        let dim_6_indicator = if d >= 6 {
            // Check if the 6 dimensions split into 3+3 (holomorphic + anti-holomorphic)
            let first_half_var: f64 = (0..3).map(|j| {
                let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
                let m = col.iter().sum::<f64>() / col.len() as f64;
                col.iter().map(|x| (x - m).powi(2)).sum::<f64>() / col.len() as f64
            }).sum();
            let second_half_var: f64 = (3..6.min(d)).map(|j| {
                let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
                let m = col.iter().sum::<f64>() / col.len() as f64;
                col.iter().map(|x| (x - m).powi(2)).sum::<f64>() / col.len() as f64
            }).sum();
            if first_half_var + second_half_var > 1e-12 {
                1.0 - (first_half_var - second_half_var).abs() / (first_half_var + second_half_var)
            } else {
                0.0
            }
        } else {
            0.0
        };
        result.insert("cy3_dimension_score".to_string(), vec![dim_6_indicator]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_mirror_symmetry_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.2).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = MirrorSymmetryAlgLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("hodge_symmetry_score"));
        assert!(result.contains_key("gromov_witten_proxy"));
    }

    #[test]
    fn test_mirror_symmetry_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = MirrorSymmetryAlgLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
