use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// TriangulatedCategoryLens: Detect triangulated category patterns —
/// distinguished triangles, octahedron axiom, shift functor periodicity.
///
/// n=6 connection: octahedron axiom involves 6 objects and 6 morphisms,
/// the shift functor [1] iterated 6 times relates to periodicity.
pub struct TriangulatedCategoryLens;

impl Lens for TriangulatedCategoryLens {
    fn name(&self) -> &str {
        "TriangulatedCategoryLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);

        // 1. Distinguished triangle detection: X → Y → Z → X[1]
        //    Look for cyclic triple relationships in data
        let mut triangle_score = 0.0;
        let mut triangle_count = 0;
        for i in 0..max_n.min(30) {
            for j in (i + 1)..max_n.min(30) {
                for k in (j + 1)..max_n.min(30) {
                    let d_ij = shared.dist(i, j);
                    let d_jk = shared.dist(j, k);
                    let d_ki = shared.dist(k, i);

                    // Distinguished triangle: compositions should be "exact"
                    // Check if d_ij + d_jk ≈ d_ki (up to shift)
                    let sum = d_ij + d_jk;
                    if sum > 1e-12 {
                        let exactness = 1.0 - (sum - d_ki).abs() / sum;
                        triangle_score += exactness.max(0.0);
                        triangle_count += 1;
                    }
                }
            }
        }
        let avg_triangle = if triangle_count > 0 {
            triangle_score / triangle_count as f64
        } else {
            0.0
        };
        result.insert("distinguished_triangle_score".to_string(), vec![avg_triangle]);

        // 2. Octahedron axiom: given two composable morphisms f: X→Y, g: Y→Z,
        //    there exist objects that form an octahedral diagram.
        //    Check 6-tuples for octahedral compatibility.
        if max_n >= 6 {
            let mut octa_score = 0.0;
            let mut octa_count = 0;
            let limit = max_n.min(20);
            for base in (0..limit).step_by(6) {
                if base + 5 >= max_n {
                    break;
                }
                // 6 objects: A, B, C, D, E, F
                let pts: Vec<usize> = (base..base + 6).collect();
                // Octahedron: check all 3 distinguished triangles
                // (A,B,D), (B,C,E), (A,C,F) and compatibility D→E→F→D[1]
                let d_ab = shared.dist(pts[0], pts[1]);
                let d_bc = shared.dist(pts[1], pts[2]);
                let d_de = shared.dist(pts[3], pts[4]);
                let d_ef = shared.dist(pts[4], pts[5]);
                let d_fd = shared.dist(pts[5], pts[3]);

                // Compatibility: compositions should chain
                let chain1 = d_ab + d_bc;
                let chain2 = d_de + d_ef + d_fd;
                if chain1 > 1e-12 && chain2 > 1e-12 {
                    let compat = 1.0 - (chain1 - chain2).abs() / (chain1 + chain2);
                    octa_score += compat.max(0.0);
                    octa_count += 1;
                }
            }
            let avg_octa = if octa_count > 0 { octa_score / octa_count as f64 } else { 0.0 };
            result.insert("octahedron_axiom_score".to_string(), vec![avg_octa]);
        }

        // 3. Shift functor periodicity: T[k] ≅ T for some k
        //    Check if data has periodic structure under k-step shifts
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();
        let mut best_period = 0;
        let mut best_period_score = 0.0;
        for period in 2..=12 {
            if vals.len() <= period {
                continue;
            }
            let mut err = 0.0;
            let mut count = 0;
            for i in period..vals.len() {
                err += (vals[i] - vals[i - period]).abs();
                count += 1;
            }
            if count > 0 {
                let range = vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                    - vals.iter().cloned().fold(f64::INFINITY, f64::min);
                let score = if range > 1e-12 {
                    1.0 - (err / count as f64) / range
                } else {
                    0.0
                };
                if score > best_period_score {
                    best_period_score = score;
                    best_period = period;
                }
            }
        }
        result.insert("shift_functor_period".to_string(), vec![best_period as f64]);
        result.insert("shift_periodicity_score".to_string(), vec![best_period_score]);

        // Score bonus if period divides 6 or is 6
        let six_period_bonus = if best_period > 0 && 6 % best_period == 0 {
            1.0
        } else if best_period > 0 && best_period % 6 == 0 {
            0.8
        } else {
            0.0
        };
        result.insert("six_period_alignment".to_string(), vec![six_period_bonus]);

        // 4. Exact sequence detection: look for "kernel-image" pattern
        //    In sequences A→B→C, check if image(f) ⊂ kernel(g)
        let mut exact_score = 0.0;
        let mut exact_count = 0;
        for i in 0..(max_n.saturating_sub(2)).min(50) {
            // "morphism" from differences
            let mut f_norm = 0.0;
            let mut g_norm = 0.0;
            let mut fg_dot = 0.0;
            for k in 0..d {
                let f = data[(i + 1) * d + k] - data[i * d + k];
                let g = data[(i + 2) * d + k] - data[(i + 1) * d + k];
                f_norm += f * f;
                g_norm += g * g;
                fg_dot += f * g;
            }
            if f_norm > 1e-12 && g_norm > 1e-12 {
                // Exactness: g∘f = 0 means dot product should vanish
                let cos = fg_dot / (f_norm.sqrt() * g_norm.sqrt());
                exact_score += 1.0 - cos.abs();
                exact_count += 1;
            }
        }
        let avg_exact = if exact_count > 0 { exact_score / exact_count as f64 } else { 0.0 };
        result.insert("exact_sequence_score".to_string(), vec![avg_exact]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_triangulated_category_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.5).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = TriangulatedCategoryLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("distinguished_triangle_score"));
        assert!(result.contains_key("octahedron_axiom_score"));
    }

    #[test]
    fn test_triangulated_category_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = TriangulatedCategoryLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
