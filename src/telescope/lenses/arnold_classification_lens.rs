use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ArnoldClassificationLens: Detect singularity patterns from Arnold's ADE classification —
/// E_6 singularity, Milnor number, Dynkin diagram structure.
///
/// n=6 connection: E_6 singularity x³+y⁴ has Milnor number μ=6,
/// E_6 Dynkin diagram has 6 nodes, Coxeter number h=12=2·6.
pub struct ArnoldClassificationLens;

/// ADE singularity types and their Milnor numbers.
/// A_k: μ=k, D_k: μ=k, E_6: μ=6, E_7: μ=7, E_8: μ=8
struct SingularityType {
    name: &'static str,
    milnor: usize,
    coxeter: usize,
}

const ADE_TYPES: &[SingularityType] = &[
    SingularityType { name: "A_1", milnor: 1, coxeter: 2 },
    SingularityType { name: "A_2", milnor: 2, coxeter: 3 },
    SingularityType { name: "A_3", milnor: 3, coxeter: 4 },
    SingularityType { name: "A_4", milnor: 4, coxeter: 5 },
    SingularityType { name: "A_5", milnor: 5, coxeter: 6 },
    SingularityType { name: "D_4", milnor: 4, coxeter: 6 },
    SingularityType { name: "D_5", milnor: 5, coxeter: 8 },
    SingularityType { name: "D_6", milnor: 6, coxeter: 10 },
    SingularityType { name: "E_6", milnor: 6, coxeter: 12 },
    SingularityType { name: "E_7", milnor: 7, coxeter: 14 },
    SingularityType { name: "E_8", milnor: 8, coxeter: 30 },
];

impl Lens for ArnoldClassificationLens {
    fn name(&self) -> &str {
        "ArnoldClassificationLens"
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

        // 1. Singularity detection via critical point analysis
        //    Find local extrema and classify by their "order" (flatness)
        let mut critical_points = Vec::new();
        for i in 1..vals.len() - 1 {
            let is_max = vals[i] >= vals[i - 1] && vals[i] >= vals[i + 1];
            let is_min = vals[i] <= vals[i - 1] && vals[i] <= vals[i + 1];
            if is_max || is_min {
                // Estimate flatness: how many consecutive values are "close"
                let mut flatness = 1;
                let eps = (vals[i].abs() * 0.01).max(1e-6);
                let mut k = i + 1;
                while k < vals.len() && (vals[k] - vals[i]).abs() < eps {
                    flatness += 1;
                    k += 1;
                }
                critical_points.push((i, vals[i], flatness));
            }
        }
        result.insert("critical_point_count".to_string(), vec![critical_points.len() as f64]);

        // Milnor number proxy: number of critical points in a "fiber"
        let milnor_proxy = critical_points.len();
        result.insert("milnor_number_proxy".to_string(), vec![milnor_proxy as f64]);

        // 2. E_6 score: how well does data match x³+y⁴ singularity pattern?
        //    Signature: the function has a degenerate critical point with specific Hessian
        if d >= 2 {
            let mut e6_score = 0.0;
            // Check for cubic-quartic interaction between first two dimensions
            for i in 0..max_n {
                let x = data[i * d];
                let y = if d > 1 { data[i * d + 1] } else { 0.0 };
                // E_6 normal form: x³ + y⁴
                let residual = x.powi(3) + y.powi(4);
                e6_score += residual.abs();
            }
            e6_score /= max_n as f64;
            // Normalize by data magnitude
            let data_scale: f64 = vals.iter().map(|x| x.abs()).sum::<f64>() / vals.len() as f64;
            let e6_normalized = if data_scale > 1e-12 {
                e6_score / data_scale.powi(3).max(1e-12)
            } else {
                0.0
            };
            result.insert("e6_singularity_residual".to_string(), vec![e6_normalized]);
        }

        // 3. ADE classification: score each type by matching local geometry
        let mut best_type = "none";
        let mut best_score = f64::MAX;
        for ade in ADE_TYPES {
            let milnor_diff = (milnor_proxy as f64 - ade.milnor as f64).abs();
            // Also check if periodicity matches Coxeter number
            let period_score = periodic_strength(&vals, ade.coxeter);
            let combined = milnor_diff + (1.0 - period_score) * 5.0;
            if combined < best_score {
                best_score = combined;
                best_type = ade.name;
            }
        }
        // Encode best type as its Milnor number
        let best_milnor = ADE_TYPES.iter().find(|t| t.name == best_type)
            .map(|t| t.milnor as f64).unwrap_or(0.0);
        result.insert("ade_classification_milnor".to_string(), vec![best_milnor]);
        result.insert("ade_classification_score".to_string(), vec![best_score]);

        // Is it E_6?
        let is_e6 = if best_type == "E_6" { 1.0 } else { 0.0 };
        result.insert("is_e6_singularity".to_string(), vec![is_e6]);

        // 4. Dynkin diagram connectivity: build local graph, check if tree-like with 6 nodes
        let nn = max_n.min(50);
        let mut adjacency = vec![vec![false; nn]; nn];
        let mut all_dists = Vec::new();
        for i in 0..nn {
            for j in (i + 1)..nn {
                all_dists.push(shared.dist(i, j));
            }
        }
        if !all_dists.is_empty() {
            all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            let threshold = all_dists[all_dists.len() / 4]; // 25th percentile
            let mut edge_count = 0;
            for i in 0..nn {
                for j in (i + 1)..nn {
                    if shared.dist(i, j) < threshold {
                        adjacency[i][j] = true;
                        adjacency[j][i] = true;
                        edge_count += 1;
                    }
                }
            }
            // Tree-likeness: tree has n-1 edges
            let tree_score = if nn > 1 {
                1.0 - ((edge_count as f64 - (nn - 1) as f64).abs() / nn as f64).min(1.0)
            } else {
                0.0
            };
            result.insert("dynkin_tree_score".to_string(), vec![tree_score]);

            // E_6 branching: check for a node with degree 3 (the branch point)
            let degrees: Vec<usize> = (0..nn).map(|i| {
                (0..nn).filter(|&j| adjacency[i][j]).count()
            }).collect();
            let branch_nodes = degrees.iter().filter(|&&d| d >= 3).count();
            result.insert("branch_point_count".to_string(), vec![branch_nodes as f64]);
        }

        // 5. Coxeter number: h(E_6) = 12 = 2·6
        let coxeter_12_score = periodic_strength(&vals, 12);
        result.insert("coxeter_12_periodicity".to_string(), vec![coxeter_12_score]);

        result
    }
}

/// Measure periodic strength at given period.
fn periodic_strength(vals: &[f64], period: usize) -> f64 {
    if vals.len() <= period {
        return 0.0;
    }
    let mut err = 0.0;
    let mut count = 0;
    for i in period..vals.len() {
        err += (vals[i] - vals[i - period]).abs();
        count += 1;
    }
    if count == 0 {
        return 0.0;
    }
    let range = vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
        - vals.iter().cloned().fold(f64::INFINITY, f64::min);
    if range < 1e-12 {
        return 1.0;
    }
    1.0 - (err / count as f64) / range
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_arnold_classification_basic() {
        let data: Vec<f64> = (0..60).map(|i| {
            let x = (i as f64 * 0.1) - 3.0;
            x.powi(3) + x.powi(4) * 0.1
        }).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = ArnoldClassificationLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("milnor_number_proxy"));
        assert!(result.contains_key("ade_classification_milnor"));
    }

    #[test]
    fn test_arnold_classification_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = ArnoldClassificationLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
