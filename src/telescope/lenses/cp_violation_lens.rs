use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// CPViolationLens: 6-quark sector CP violation and Jarlskog invariant.
///
/// Detects CP (charge-parity) violation by measuring asymmetries between
/// forward and backward processes in data. In the Standard Model, CP
/// violation arises from the complex phase in the CKM matrix.
///
/// The Jarlskog invariant J = Im(V_us V_cb V*_ub V*_cs) measures the
/// irreducible CP-violating phase. J ≈ 3.18 × 10⁻⁵ experimentally.
///
/// We construct an effective "CKM matrix" from data correlations between
/// 6 dimensions (6 quark flavors: u, d, s, c, b, t) and compute:
///   - Mixing angles θ₁₂, θ₂₃, θ₁₃
///   - CP-violating phase δ
///   - Jarlskog invariant
///   - Unitarity triangle area
///
/// Metrics:
///   1. jarlskog_invariant: J = c₁₂c₂₃c²₁₃s₁₂s₂₃s₁₃ sin δ
///   2. cp_asymmetry: forward-backward asymmetry in data
///   3. mixing_angles: three CKM mixing angles
///   4. unitarity_triangle_area: area = J/2
///   5. cp_phase: the CP-violating phase δ
///
/// n=6: 6 quark flavors, 6×6 CKM-like mixing matrix.
pub struct CPViolationLens;

impl Lens for CPViolationLens {
    fn name(&self) -> &str { "CPViolationLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 3 { return HashMap::new(); }

        let n_flavors = d.min(6);
        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);
        let stds: Vec<f64> = vars.iter().map(|v| v.sqrt().max(1e-12)).collect();

        // Build correlation matrix as "CKM-like" mixing matrix
        let mut corr = vec![0.0f64; n_flavors * n_flavors];
        for fi in 0..n_flavors {
            for fj in 0..n_flavors {
                let mut c = 0.0f64;
                for row in 0..n {
                    c += (columns[fi][row] - means[fi]) * (columns[fj][row] - means[fj]);
                }
                c /= n as f64;
                corr[fi * n_flavors + fj] = c / (stds[fi] * stds[fj]);
            }
        }

        // Extract mixing angles from correlation matrix (Euler decomposition)
        // θ₁₂ from off-diagonal (0,1), θ₂₃ from (1,2), θ₁₃ from (0,2)
        let theta12 = corr[0 * n_flavors + 1].abs().asin().abs();
        let theta23 = if n_flavors > 2 {
            corr[1 * n_flavors + 2].abs().asin().abs()
        } else { 0.0 };
        let theta13 = if n_flavors > 2 {
            corr[0 * n_flavors + 2].abs().asin().abs()
        } else { 0.0 };

        // CP phase δ: imaginary part of the "unitarity quadrangle"
        // Use third-order correlations as proxy for complex phase
        let mut cp_phase = 0.0f64;
        if n_flavors >= 3 {
            // Triple correlation: Im(V_us V_cb V*_ub V*_cs) proxy
            let mut triple_corr = 0.0f64;
            for row in 0..n {
                let z0 = (columns[0][row] - means[0]) / stds[0];
                let z1 = (columns[1][row] - means[1]) / stds[1];
                let z2 = (columns[2][row] - means[2]) / stds[2];
                // Antisymmetric combination (CP-odd)
                triple_corr += z0 * z1 * z2;
            }
            triple_corr /= n as f64;
            // Phase from inverse trig of normalized triple correlation
            cp_phase = triple_corr.atan2(1.0);
        }

        // Jarlskog invariant: J = c₁₂ c₂₃ c²₁₃ s₁₂ s₂₃ s₁₃ sin(δ)
        let j_invariant = theta12.cos() * theta23.cos() * theta13.cos().powi(2)
            * theta12.sin() * theta23.sin() * theta13.sin()
            * cp_phase.sin();

        // CP asymmetry: compare data distribution under time-reversal
        // A_CP = (N_forward - N_backward) / (N_forward + N_backward)
        let mut n_forward = 0u32;
        let mut n_backward = 0u32;
        for row in 0..n {
            // "Forward": dim 0 increasing with dim 1
            // "Backward": dim 0 decreasing with dim 1
            if d >= 2 {
                let x = columns[0][row] - means[0];
                let y = columns[1][row] - means[1];
                if x * y > 0.0 { n_forward += 1; }
                else { n_backward += 1; }
            }
        }
        let total = (n_forward + n_backward).max(1) as f64;
        let cp_asymmetry = (n_forward as f64 - n_backward as f64) / total;

        // Unitarity triangle area = |J| / 2
        let triangle_area = j_invariant.abs() / 2.0;

        let mut result = HashMap::new();
        result.insert("jarlskog_invariant".to_string(), vec![j_invariant]);
        result.insert("cp_asymmetry".to_string(), vec![cp_asymmetry]);
        result.insert("mixing_angles".to_string(), vec![theta12, theta23, theta13]);
        result.insert("unitarity_triangle_area".to_string(), vec![triangle_area]);
        result.insert("cp_phase".to_string(), vec![cp_phase]);
        result.insert("score".to_string(), vec![result["jarlskog_invariant"][0].min(1.0).max(0.0)]);
        result
    }
}
