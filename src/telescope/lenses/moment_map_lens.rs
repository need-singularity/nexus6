use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MomentMapLens: Detect symplectic geometry patterns — moment maps,
/// symplectic quotients, Hamiltonian actions.
///
/// n=6 connection: 6-dimensional symplectic manifold (M, ω), dim = 2·3,
/// symplectic quotient M//G, moment map μ: M → g*.
pub struct MomentMapLens;

impl Lens for MomentMapLens {
    fn name(&self) -> &str {
        "MomentMapLens"
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

        // 1. Symplectic form detection: ω is a closed non-degenerate 2-form
        //    In coordinates (q_1,p_1,...,q_k,p_k), ω = Σ dq_i ∧ dp_i
        //    Check if pairs of dimensions have anti-symmetric structure
        if max_dim >= 2 {
            let pairs = max_dim / 2;
            let mut symplectic_scores = Vec::new();

            for p in 0..pairs {
                let qi = p * 2;
                let pi = p * 2 + 1;
                let q_col: Vec<f64> = (0..max_n).map(|i| data[i * d + qi]).collect();
                let p_col: Vec<f64> = (0..max_n).map(|i| data[i * d + pi]).collect();

                // Symplectic pairing: ω(q,p) = Σ (dq_i · dp_{i+1} - dp_i · dq_{i+1})
                let mut omega = 0.0;
                let mut count = 0;
                for i in 0..max_n - 1 {
                    let dq = q_col[i + 1] - q_col[i];
                    let dp = p_col[i + 1] - p_col[i];
                    omega += dq * p_col[i] - dp * q_col[i]; // canonical pairing
                    count += 1;
                }
                let avg_omega = if count > 0 { omega / count as f64 } else { 0.0 };
                symplectic_scores.push(avg_omega);
            }

            let total_omega: f64 = symplectic_scores.iter().map(|x| x.abs()).sum();
            result.insert("symplectic_form_magnitude".to_string(), vec![total_omega / pairs as f64]);
            result.insert("symplectic_pair_values".to_string(), symplectic_scores);

            // Non-degeneracy: ω^n ≠ 0 (volume form)
            // For 3 pairs (6-dim), ω³ = ω∧ω∧ω should be nonzero
            if pairs >= 2 {
                let mut pfaffian = 1.0;
                for p in 0..pairs {
                    let qi = p * 2;
                    let pi = p * 2 + 1;
                    // Compute 2x2 block determinant
                    let mut a00 = 0.0;
                    let mut a01 = 0.0;
                    let mut a11 = 0.0;
                    for i in 0..max_n {
                        let q = data[i * d + qi];
                        let p_val = data[i * d + pi];
                        a00 += q * q;
                        a01 += q * p_val;
                        a11 += p_val * p_val;
                    }
                    let det = (a00 * a11 - a01 * a01) / (max_n as f64).powi(2);
                    pfaffian *= det;
                }
                result.insert("symplectic_nondegeneracy".to_string(),
                    vec![if pfaffian.abs() > 1e-12 { 1.0 } else { 0.0 }]);
            }
        }

        // 2. Moment map: μ: M → R^k for Hamiltonian group action
        //    Check for conserved quantities along data trajectories
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();
        let mut conserved_quantities = Vec::new();
        for j in 0..max_dim {
            let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
            // A conserved quantity has small time derivative
            let mut deriv_norm = 0.0;
            for i in 1..col.len() {
                let dt = col[i] - col[i - 1];
                deriv_norm += dt * dt;
            }
            let rms_deriv = (deriv_norm / (col.len() - 1).max(1) as f64).sqrt();
            let col_range = col.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                - col.iter().cloned().fold(f64::INFINITY, f64::min);
            let conservation = if col_range > 1e-12 {
                1.0 - (rms_deriv / col_range).min(1.0)
            } else {
                1.0
            };
            conserved_quantities.push(conservation);
        }
        let num_conserved = conserved_quantities.iter().filter(|&&c| c > 0.8).count();
        result.insert("conserved_quantity_scores".to_string(), conserved_quantities);
        result.insert("num_conserved_quantities".to_string(), vec![num_conserved as f64]);

        // 3. Hamiltonian flow: check if trajectories follow dq/dt = ∂H/∂p, dp/dt = -∂H/∂q
        if max_dim >= 2 {
            let mut hamilton_score = 0.0;
            let mut ham_count = 0;
            let pairs = max_dim / 2;
            for p in 0..pairs {
                let qi = p * 2;
                let pi = p * 2 + 1;
                for i in 1..max_n - 1 {
                    let dq = data[(i + 1) * d + qi] - data[(i - 1) * d + qi];
                    let dp = data[(i + 1) * d + pi] - data[(i - 1) * d + pi];
                    // Hamilton's equations: dq/dt ∝ ∂H/∂p, dp/dt ∝ -∂H/∂q
                    // If flow is Hamiltonian, dq·dp should have specific sign pattern
                    let cross = dq * dp;
                    // Energy conservation: dH/dt = 0 means dq·dp pattern is constrained
                    hamilton_score += cross.abs();
                    ham_count += 1;
                }
            }
            let avg_ham = if ham_count > 0 { hamilton_score / ham_count as f64 } else { 0.0 };
            result.insert("hamiltonian_flow_indicator".to_string(), vec![avg_ham]);
        }

        // 4. Symplectic quotient dimension: dim(M//G) = dim(M) - 2·dim(G)
        //    If we start with 6-dim, quotient by G gives lower-dim symplectic manifold
        let effective_dim = max_dim as f64;
        let quotient_dim = (effective_dim - 2.0 * num_conserved as f64).max(0.0);
        result.insert("symplectic_quotient_dim".to_string(), vec![quotient_dim]);

        // 5. Phase space volume (Liouville measure)
        //    For 6-dim phase space, volume should be preserved under Hamiltonian flow
        if max_dim >= 2 && max_n >= 6 {
            let mut volumes = Vec::new();
            let window = 6;
            for start in (0..max_n - window).step_by(window) {
                let mut vol = 1.0;
                for j in 0..max_dim {
                    let slice: Vec<f64> = (start..start + window)
                        .map(|i| data[i * d + j]).collect();
                    let range = slice.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                        - slice.iter().cloned().fold(f64::INFINITY, f64::min);
                    vol *= range.max(1e-12);
                }
                volumes.push(vol);
            }
            if volumes.len() >= 2 {
                let mean_vol = volumes.iter().sum::<f64>() / volumes.len() as f64;
                let vol_var = volumes.iter().map(|v| (v - mean_vol).powi(2)).sum::<f64>()
                    / volumes.len() as f64;
                let liouville_conservation = if mean_vol > 1e-12 {
                    1.0 - (vol_var.sqrt() / mean_vol).min(1.0)
                } else {
                    0.0
                };
                result.insert("liouville_conservation".to_string(), vec![liouville_conservation]);
            }
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_moment_map_basic() {
        // Harmonic oscillator-like data in 6 dims
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.1;
            match i % 6 {
                0 => t.cos(),
                1 => t.sin(),
                2 => (2.0 * t).cos(),
                3 => (2.0 * t).sin(),
                4 => (3.0 * t).cos(),
                _ => (3.0 * t).sin(),
            }
        }).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = MomentMapLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("symplectic_form_magnitude"));
        assert!(result.contains_key("num_conserved_quantities"));
    }

    #[test]
    fn test_moment_map_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = MomentMapLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
