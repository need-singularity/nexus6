use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MacLaneCoherenceLens: Detect monoidal category coherence patterns —
/// associahedron structure, pentagon/hexagon identities, Mac Lane coherence.
///
/// n=6 connection: associahedron K_6 has 14 vertices (Catalan C_5=42 for K_7),
/// K_6 has Catalan(4)=14 vertices, relating to all bracketings of 6 objects.
/// The Catalan number C_4 = 14 counts binary trees with 5 leaves.
pub struct MacLaneCoherenceLens;

/// Catalan number C_n.
fn catalan(n: usize) -> usize {
    if n <= 1 {
        return 1;
    }
    let mut c = 1u64;
    for i in 0..n {
        c = c * 2 * (2 * i as u64 + 1) / (i as u64 + 2);
    }
    c as usize
}

impl Lens for MacLaneCoherenceLens {
    fn name(&self) -> &str {
        "MacLaneCoherenceLens"
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
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. Associativity coherence: check if (a⊗b)⊗c ≈ a⊗(b⊗c)
        //    for all triples, where ⊗ is some binary operation
        let mut assoc_score = 0.0;
        let mut assoc_count = 0;
        for i in 0..max_n.min(20) {
            for j in (i + 1)..max_n.min(20) {
                for k in (j + 1)..max_n.min(20) {
                    let a = vals[i];
                    let b = vals[j];
                    let c = vals[k];
                    // Test with addition (always associative) as baseline
                    // Test with a custom operation: geometric mean-like
                    let left = ((a.abs() + 1.0) * (b.abs() + 1.0)).sqrt() * (c.abs() + 1.0);
                    let right = (a.abs() + 1.0) * ((b.abs() + 1.0) * (c.abs() + 1.0)).sqrt();
                    if left > 1e-12 {
                        let ratio = (left - right).abs() / left;
                        assoc_score += 1.0 - ratio.min(1.0);
                        assoc_count += 1;
                    }
                }
            }
        }
        let avg_assoc = if assoc_count > 0 { assoc_score / assoc_count as f64 } else { 0.0 };
        result.insert("associativity_coherence".to_string(), vec![avg_assoc]);

        // 2. Pentagon identity: 5 faces of associahedron must commute
        //    For 4 objects a,b,c,d, check 5-step commutativity
        if max_n >= 4 {
            let mut pentagon_score = 0.0;
            let mut pent_count = 0;
            for base in 0..max_n.min(15) {
                if base + 3 >= max_n {
                    break;
                }
                let a = vals[base];
                let b = vals[base + 1];
                let c = vals[base + 2];
                let dd = vals[base + 3];
                // Two paths through pentagon: both should give same result
                let path1 = a + (b + (c + dd));
                let path2 = ((a + b) + c) + dd;
                let diff = (path1 - path2).abs();
                let scale = path1.abs().max(path2.abs()).max(1e-12);
                pentagon_score += 1.0 - (diff / scale).min(1.0);
                pent_count += 1;
            }
            let avg_pentagon = if pent_count > 0 { pentagon_score / pent_count as f64 } else { 0.0 };
            result.insert("pentagon_identity_score".to_string(), vec![avg_pentagon]);
        }

        // 3. Hexagon identity: braiding coherence for 3 objects
        //    Two hexagonal paths through braided monoidal category
        if max_n >= 6 {
            let mut hexagon_score = 0.0;
            let mut hex_count = 0;
            for base in (0..max_n.min(30)).step_by(3) {
                if base + 2 >= max_n {
                    break;
                }
                // Use distance-based "braiding"
                let d01 = shared.dist(base, base + 1);
                let d12 = shared.dist(base + 1, base + 2);
                let d02 = shared.dist(base, base + 2);
                // Hexagon: two paths should give consistent braiding
                let path1 = d01 + d12;
                let path2 = d02;
                if path1 > 1e-12 {
                    let coherence = 1.0 - (path1 - path2).abs() / path1;
                    hexagon_score += coherence.max(0.0);
                    hex_count += 1;
                }
            }
            let avg_hex = if hex_count > 0 { hexagon_score / hex_count as f64 } else { 0.0 };
            result.insert("hexagon_identity_score".to_string(), vec![avg_hex]);
        }

        // 4. Catalan numbers: K_n has C_{n-2} vertices
        //    C_4 = 14 for K_6 (6 objects)
        result.insert("catalan_k6_vertices".to_string(), vec![catalan(4) as f64]); // 14

        // Check if data has structure aligned with Catalan numbers
        let catalan_seq: Vec<f64> = (0..6).map(|i| catalan(i) as f64).collect(); // 1,1,2,5,14,42
        let data_sample: Vec<f64> = vals.iter().take(6).cloned().collect();
        if data_sample.len() >= 6 {
            // Correlation with Catalan sequence
            let mut dot = 0.0;
            let mut na = 0.0;
            let mut nb = 0.0;
            for i in 0..6 {
                dot += data_sample[i] * catalan_seq[i];
                na += data_sample[i] * data_sample[i];
                nb += catalan_seq[i] * catalan_seq[i];
            }
            let corr = if na > 1e-12 && nb > 1e-12 {
                dot / (na.sqrt() * nb.sqrt())
            } else {
                0.0
            };
            result.insert("catalan_correlation".to_string(), vec![corr]);
        }

        // 5. Coherence dimension: effective number of independent coherence constraints
        //    Use rank of difference matrix as proxy
        if d >= 2 {
            let max_dim = d.min(6);
            // Compute rank via number of significant singular value proxies
            let mut col_vars: Vec<f64> = (0..max_dim).map(|j| {
                let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
                let mean = col.iter().sum::<f64>() / col.len() as f64;
                col.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / col.len() as f64
            }).collect();
            col_vars.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
            let total: f64 = col_vars.iter().sum();
            let mut effective_dim = 0;
            let mut cum = 0.0;
            for &v in &col_vars {
                cum += v;
                effective_dim += 1;
                if cum / total.max(1e-12) > 0.95 {
                    break;
                }
            }
            result.insert("coherence_dimension".to_string(), vec![effective_dim as f64]);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_catalan_numbers() {
        assert_eq!(catalan(0), 1);
        assert_eq!(catalan(1), 1);
        assert_eq!(catalan(2), 2);
        assert_eq!(catalan(3), 5);
        assert_eq!(catalan(4), 14);
        assert_eq!(catalan(5), 42);
    }

    #[test]
    fn test_maclane_coherence_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.1).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = MacLaneCoherenceLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert_eq!(result["catalan_k6_vertices"][0], 14.0);
    }

    #[test]
    fn test_maclane_coherence_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = MacLaneCoherenceLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
