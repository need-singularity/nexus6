use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// QueryComplexityLens: Decision/query complexity analysis.
///
/// Models data classification as a decision tree with query budget:
/// - Builds a binary split tree using median-of-coordinate queries
/// - Measures depth (query count) needed to separate points
/// - 6-query lower bound: information-theoretic minimum queries
/// - Certificate complexity: minimum evidence to certify classification
pub struct QueryComplexityLens;

impl Lens for QueryComplexityLens {
    fn name(&self) -> &str { "QueryComplexityLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = shared;
        if n < 4 || d == 0 { return HashMap::new(); }

        // Information-theoretic query lower bound: ceil(log2(n))
        let info_lower_bound = (n as f64).log2().ceil();

        // Build a greedy decision tree: at each node pick best coordinate split
        // Return depth needed to isolate each point
        let indices: Vec<usize> = (0..n).collect();
        let depths = build_tree_depths(data, d, &indices, 0);

        let max_depth = depths.iter().cloned().fold(0usize, usize::max);
        let mean_depth = depths.iter().sum::<usize>() as f64 / n as f64;

        // Deterministic query complexity: max depth
        let det_complexity = max_depth as f64;

        // 6-query certificate: how many points are resolved within 6 queries
        let resolved_in_6 = depths.iter().filter(|&&d| d <= 6).count();
        let certificate_fraction = resolved_in_6 as f64 / n as f64;

        // Sensitivity: for each point, count coordinates that change its partition
        let mut sensitivity_sum = 0usize;
        for i in 0..n {
            let mut sens = 0usize;
            for dim in 0..d {
                let val = data[i * d + dim];
                // Count how many other points are separated by this coordinate
                let median = coordinate_median(data, n, d, dim);
                let side = val <= median;
                // Check if flipping this bit would change classification
                let other_side = !side;
                let has_other = (0..n).any(|j| j != i && (data[j * d + dim] <= median) == other_side);
                if has_other { sens += 1; }
            }
            sensitivity_sum += sens;
        }
        let mean_sensitivity = sensitivity_sum as f64 / n as f64;

        // Block sensitivity: max over disjoint sensitive blocks of size up to 6
        let block_sensitivity = (mean_sensitivity / 6.0).ceil().min(d as f64);

        // n=6 ratio: how close is mean_depth to 6
        let n6_query_match = (-((mean_depth - 6.0).abs() * 0.25)).exp();

        let mut result = HashMap::new();
        result.insert("info_lower_bound".into(), vec![info_lower_bound]);
        result.insert("det_complexity".into(), vec![det_complexity]);
        result.insert("mean_query_depth".into(), vec![mean_depth]);
        result.insert("certificate_fraction_6".into(), vec![certificate_fraction]);
        result.insert("mean_sensitivity".into(), vec![mean_sensitivity]);
        result.insert("block_sensitivity".into(), vec![block_sensitivity]);
        result.insert("n6_query_match".into(), vec![n6_query_match]);
        result.insert("depth_distribution".into(), depths.iter().map(|&d| d as f64).collect());
        result
    }
}

fn coordinate_median(data: &[f64], n: usize, d: usize, dim: usize) -> f64 {
    let mut vals: Vec<f64> = (0..n).map(|i| data[i * d + dim]).collect();
    vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    vals[vals.len() / 2]
}

fn build_tree_depths(data: &[f64], d: usize, indices: &[usize], depth: usize) -> Vec<usize> {
    if indices.len() <= 1 || depth >= 20 {
        return vec![depth; indices.len()];
    }

    // Find best split dimension: maximize information gain (most even split)
    let mut best_dim = 0;
    let mut best_score = f64::MAX;
    for dim in 0..d {
        let mut vals: Vec<f64> = indices.iter().map(|&i| data[i * d + dim]).collect();
        vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median = vals[vals.len() / 2];
        let left = vals.iter().filter(|&&v| v <= median).count();
        let right = vals.len() - left;
        // Score: how unbalanced (0 = perfect split)
        let score = ((left as f64) - (right as f64)).abs();
        if score < best_score {
            best_score = score;
            best_dim = dim;
        }
    }

    let mut vals: Vec<f64> = indices.iter().map(|&i| data[i * d + best_dim]).collect();
    vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let median = vals[vals.len() / 2];

    let left_idx: Vec<usize> = indices.iter().filter(|&&i| data[i * d + best_dim] <= median).cloned().collect();
    let right_idx: Vec<usize> = indices.iter().filter(|&&i| data[i * d + best_dim] > median).cloned().collect();

    if left_idx.is_empty() || right_idx.is_empty() {
        return vec![depth; indices.len()];
    }

    let mut result = build_tree_depths(data, d, &left_idx, depth + 1);
    result.extend(build_tree_depths(data, d, &right_idx, depth + 1));
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_query_complexity() {
        let mut data = Vec::new();
        for i in 0..16 {
            data.push((i % 4) as f64);
            data.push((i / 4) as f64);
        }
        let n = 16;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = QueryComplexityLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("det_complexity"));
        assert!(r["info_lower_bound"][0] >= 3.0); // log2(16) = 4
    }
}
