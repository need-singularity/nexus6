use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// LatticeCongruenceLens: Detect lattice and congruence class patterns.
///
/// n=6 connection: 2^6 = 64 elements in the Boolean lattice B_6,
/// congruence classes mod 6, lattice reduction signatures.
pub struct LatticeCongruenceLens;

impl Lens for LatticeCongruenceLens {
    fn name(&self) -> &str {
        "LatticeCongruenceLens"
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

        // 1. Congruence class distribution mod 6
        let mut class_counts = [0usize; 6];
        for &v in &vals {
            let r = ((v.round() as i64 % 6) + 6) % 6;
            class_counts[r as usize] += 1;
        }
        let class_dist: Vec<f64> = class_counts.iter().map(|&c| c as f64 / vals.len() as f64).collect();
        result.insert("congruence_class_distribution".to_string(), class_dist);

        // 2. Congruence class entropy (uniformity measure)
        let mut entropy = 0.0;
        for &c in &class_counts {
            if c > 0 {
                let p = c as f64 / vals.len() as f64;
                entropy -= p * p.ln();
            }
        }
        let max_entropy = 6.0_f64.ln();
        let uniformity = if max_entropy > 0.0 { entropy / max_entropy } else { 0.0 };
        result.insert("congruence_uniformity".to_string(), vec![uniformity]);

        // 3. Boolean lattice dimension: find effective dimension of binary representation
        //    Count distinct bit patterns in the 6 LSBs
        let mut bit_patterns = std::collections::HashSet::new();
        for &v in &vals {
            let bits = (v.abs().round() as u64) & 0x3F; // 6 LSBs = B_6
            bit_patterns.insert(bits);
        }
        let lattice_coverage = bit_patterns.len() as f64 / 64.0; // fraction of 2^6=64
        result.insert("boolean_lattice_coverage".to_string(), vec![lattice_coverage]);

        // 4. Lattice reduction quality: compute Gram-Schmidt-like orthogonality
        //    on data rows (treat as lattice basis vectors)
        if d >= 2 {
            let num_vecs = max_n.min(20);
            let mut orthogonality = 0.0;
            let mut orth_count = 0;
            for i in 0..num_vecs {
                for j in (i + 1)..num_vecs {
                    let mut dot = 0.0;
                    let mut norm_i = 0.0;
                    let mut norm_j = 0.0;
                    for k in 0..d {
                        let vi = data[i * d + k];
                        let vj = data[j * d + k];
                        dot += vi * vj;
                        norm_i += vi * vi;
                        norm_j += vj * vj;
                    }
                    if norm_i > 1e-12 && norm_j > 1e-12 {
                        let cos_angle = dot / (norm_i.sqrt() * norm_j.sqrt());
                        orthogonality += 1.0 - cos_angle.abs();
                        orth_count += 1;
                    }
                }
            }
            let avg_orth = if orth_count > 0 { orthogonality / orth_count as f64 } else { 0.0 };
            result.insert("lattice_orthogonality".to_string(), vec![avg_orth]);
        }

        // 5. Shortest vector proxy: minimum nonzero pairwise distance / expected distance
        let mut min_dist = f64::MAX;
        let mut sum_dist = 0.0;
        let mut dist_count = 0usize;
        for i in 0..max_n.min(50) {
            for j in (i + 1)..max_n.min(50) {
                let mut dsq = 0.0;
                for k in 0..d {
                    let diff = data[i * d + k] - data[j * d + k];
                    dsq += diff * diff;
                }
                let dist = dsq.sqrt();
                if dist > 1e-12 {
                    if dist < min_dist {
                        min_dist = dist;
                    }
                    sum_dist += dist;
                    dist_count += 1;
                }
            }
        }
        if dist_count > 0 && min_dist < f64::MAX {
            let avg_dist = sum_dist / dist_count as f64;
            // Hermite's constant proxy: γ = (shortest / det^(1/d))^2
            // Higher = worse lattice packing, 6-dim Hermite ≈ 1.7
            let svp_ratio = min_dist / avg_dist;
            result.insert("shortest_vector_ratio".to_string(), vec![svp_ratio]);

            // 6-dimensional packing ratio comparison
            let hermite_6 = 1.7; // approximate Hermite constant for dim 6
            let hermite_score = 1.0 - (svp_ratio - 1.0 / hermite_6).abs().min(1.0);
            result.insert("hermite_six_score".to_string(), vec![hermite_score]);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_lattice_congruence_basic() {
        // Data with clear mod-6 structure
        let data: Vec<f64> = (0..60).map(|i| (i * 6) as f64).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = LatticeCongruenceLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("congruence_class_distribution"));
        assert!(result.contains_key("boolean_lattice_coverage"));
    }

    #[test]
    fn test_lattice_congruence_small() {
        let data = vec![1.0; 3];
        let shared = SharedData::compute(&data, 3, 1);
        let result = LatticeCongruenceLens.scan(&data, 3, 1, &shared);
        assert!(result.is_empty());
    }
}
