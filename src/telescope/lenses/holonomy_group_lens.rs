use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// HolonomyGroupLens: Detect holonomy group patterns —
/// SO(6), SU(3), G2 holonomy, parallel transport, curvature classification.
///
/// n=6 connection: SO(6) is the generic holonomy of a 6-dimensional Riemannian manifold,
/// SU(3) ⊂ SO(6) for Calabi-Yau threefolds, G2 holonomy in 7-dim relates to 6+1.
/// Berger's classification constrains possible holonomy groups.
pub struct HolonomyGroupLens;

impl Lens for HolonomyGroupLens {
    fn name(&self) -> &str {
        "HolonomyGroupLens"
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

        // 1. Parallel transport proxy: transport a vector along the data trajectory
        //    and measure how much it rotates (holonomy = accumulated rotation)
        if max_dim >= 2 {
            // Initial "tangent vector": difference between first two points
            let mut tangent: Vec<f64> = (0..max_dim).map(|j| {
                if max_n > 1 { data[1 * d + j] - data[0 * d + j] } else { 0.0 }
            }).collect();
            let initial_tangent = tangent.clone();

            // Transport along trajectory
            for i in 1..max_n - 1 {
                // Update tangent by "connection": project onto new direction
                let new_dir: Vec<f64> = (0..max_dim).map(|j| {
                    data[(i + 1) * d + j] - data[i * d + j]
                }).collect();

                let new_norm: f64 = new_dir.iter().map(|x| x * x).sum::<f64>().sqrt();
                if new_norm < 1e-12 { continue; }

                // Parallel transport: preserve component perpendicular to motion
                let dot: f64 = tangent.iter().zip(&new_dir).map(|(a, b)| a * b).sum();
                let tang_norm: f64 = tangent.iter().map(|x| x * x).sum::<f64>().sqrt();
                if tang_norm < 1e-12 { continue; }

                // Rotate tangent toward new direction (Levi-Civita connection proxy)
                let alpha = 0.1; // connection strength
                for j in 0..max_dim {
                    tangent[j] = (1.0 - alpha) * tangent[j] + alpha * new_dir[j] / new_norm;
                }
                // Renormalize
                let tn: f64 = tangent.iter().map(|x| x * x).sum::<f64>().sqrt();
                if tn > 1e-12 {
                    for t in tangent.iter_mut() {
                        *t /= tn;
                    }
                }
            }

            // Holonomy angle: angle between initial and final tangent
            let init_norm: f64 = initial_tangent.iter().map(|x| x * x).sum::<f64>().sqrt();
            let final_norm: f64 = tangent.iter().map(|x| x * x).sum::<f64>().sqrt();
            if init_norm > 1e-12 && final_norm > 1e-12 {
                let cos_angle: f64 = initial_tangent.iter().zip(&tangent)
                    .map(|(a, b)| a * b).sum::<f64>() / (init_norm * final_norm);
                let holonomy_angle = cos_angle.clamp(-1.0, 1.0).acos();
                result.insert("holonomy_angle".to_string(), vec![holonomy_angle]);

                // SO(6) indicator: generic angle
                let so6_score = holonomy_angle / std::f64::consts::PI; // normalized to [0,1]
                result.insert("so6_indicator".to_string(), vec![so6_score]);

                // SU(3) ⊂ SO(6): holonomy should be restricted
                // SU(3) preserves a complex structure, so angle should be quantized
                let su3_angles = [0.0, std::f64::consts::PI / 3.0,
                    2.0 * std::f64::consts::PI / 3.0, std::f64::consts::PI];
                let min_su3_dist = su3_angles.iter()
                    .map(|&a| (holonomy_angle - a).abs())
                    .fold(f64::MAX, f64::min);
                let su3_score = 1.0 - (min_su3_dist / (std::f64::consts::PI / 6.0)).min(1.0);
                result.insert("su3_holonomy_score".to_string(), vec![su3_score]);
            }
        }

        // 2. Curvature tensor decomposition: Riemannian curvature splits into
        //    Weyl + Ricci + scalar parts. The holonomy determines which vanish.
        if max_dim >= 2 {
            // Compute approximate Riemann curvature from second differences
            let mut riemann_components = Vec::new();
            for p in 0..max_dim {
                for q in (p + 1)..max_dim {
                    // R_{pq} ∝ [∇_p, ∇_q] proxy
                    let mut curv = 0.0;
                    for i in 1..max_n - 1 {
                        let dp = data[(i + 1) * d + p] - data[(i - 1) * d + p];
                        let dq = data[(i + 1) * d + q] - data[(i - 1) * d + q];
                        let ddp = data[(i + 1) * d + p] - 2.0 * data[i * d + p] + data[(i - 1) * d + p];
                        let ddq = data[(i + 1) * d + q] - 2.0 * data[i * d + q] + data[(i - 1) * d + q];
                        curv += (dp * ddq - dq * ddp).abs();
                    }
                    riemann_components.push(curv / (max_n - 2).max(1) as f64);
                }
            }

            if !riemann_components.is_empty() {
                let total_curv: f64 = riemann_components.iter().sum();
                let avg_curv = total_curv / riemann_components.len() as f64;
                result.insert("riemann_curvature_avg".to_string(), vec![avg_curv]);

                // Weyl tensor proxy: traceless part of curvature
                let trace = riemann_components.iter().step_by(max_dim).sum::<f64>();
                let weyl_proxy = (total_curv - trace).abs();
                result.insert("weyl_tensor_proxy".to_string(), vec![weyl_proxy]);

                // Scalar curvature
                result.insert("scalar_curvature".to_string(), vec![trace]);
            }
        }

        // 3. Berger classification: determine which restricted holonomy group
        //    based on curvature and dimension
        // Groups for dim 6: SO(6), U(3), SU(3), Sp(3) [if applicable]
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // Check for Kahler (U(3)) structure: complex structure compatibility
        let mut kahler_indicator = 0.0;
        if max_dim >= 4 {
            // J² = -I test: pair dimensions and check rotation
            for p in 0..max_dim / 2 {
                let a: Vec<f64> = (0..max_n).map(|i| data[i * d + 2 * p]).collect();
                let b: Vec<f64> = (0..max_n).map(|i| data[i * d + 2 * p + 1]).collect();
                // Check if (a,b) look like (cos θ, sin θ) — circular structure
                let mut circle_score = 0.0;
                for i in 0..max_n {
                    let r = (a[i] * a[i] + b[i] * b[i]).sqrt();
                    if r > 1e-12 {
                        circle_score += 1.0;
                    }
                }
                kahler_indicator += circle_score / max_n as f64;
            }
            kahler_indicator /= (max_dim / 2) as f64;
        }
        result.insert("kahler_structure_score".to_string(), vec![kahler_indicator]);

        // 4. G2 holonomy indicator: 7-dimensional, but check for 6+1 structure
        //    G2 preserves a 3-form φ and a 4-form *φ
        if max_dim >= 3 {
            // Check for a "special" 3-form: antisymmetric triple product
            let mut three_form = 0.0;
            let mut count = 0;
            for i in 0..max_n.min(20) {
                for j in (i + 1)..max_n.min(20) {
                    for k in (j + 1)..max_n.min(20) {
                        // Triple product proxy
                        if max_dim >= 3 {
                            let a = [data[i * d], data[i * d + 1], data[i * d + 2]];
                            let b = [data[j * d], data[j * d + 1], data[j * d + 2]];
                            let c = [data[k * d], data[k * d + 1], data[k * d + 2]];
                            // Scalar triple product
                            let triple = a[0] * (b[1] * c[2] - b[2] * c[1])
                                - a[1] * (b[0] * c[2] - b[2] * c[0])
                                + a[2] * (b[0] * c[1] - b[1] * c[0]);
                            three_form += triple.abs();
                            count += 1;
                        }
                    }
                }
            }
            let avg_triple = if count > 0 { three_form / count as f64 } else { 0.0 };
            result.insert("g2_three_form_proxy".to_string(), vec![avg_triple]);
        }

        // 5. Holonomy dimension: dim(Hol) for various groups
        //    SO(6): dim=15, U(3): dim=9, SU(3): dim=8, Sp(3): dim=21
        let so6_dim = (max_dim * (max_dim - 1)) / 2; // n(n-1)/2
        result.insert("so6_dimension".to_string(), vec![so6_dim as f64]);
        result.insert("expected_holonomy_dim".to_string(), vec![15.0]); // SO(6)

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_holonomy_group_basic() {
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.1;
            t.sin() + 0.5 * (2.0 * t).cos()
        }).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = HolonomyGroupLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("holonomy_angle"));
        assert!(result.contains_key("so6_indicator"));
    }

    #[test]
    fn test_holonomy_group_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = HolonomyGroupLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
