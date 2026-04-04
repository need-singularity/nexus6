use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ResolutionTreeLens: Detect singularity resolution patterns —
/// blow-up sequences, resolution trees, exceptional divisors.
///
/// n=6 connection: 6-step resolution of singularities, resolution tree
/// with depth 6, exceptional divisor chains of length 6.
pub struct ResolutionTreeLens;

impl Lens for ResolutionTreeLens {
    fn name(&self) -> &str {
        "ResolutionTreeLens"
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

        // 1. Singularity detection: find points where data has extreme curvature
        let mut singular_points = Vec::new();
        for i in 1..vals.len() - 1 {
            let curvature = (vals[i + 1] - 2.0 * vals[i] + vals[i - 1]).abs();
            singular_points.push((i, curvature));
        }
        singular_points.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        // Top singularities
        let top_k = singular_points.len().min(6);
        let top_curvatures: Vec<f64> = singular_points.iter().take(top_k).map(|&(_, c)| c).collect();
        result.insert("top_singularity_curvatures".to_string(), top_curvatures);
        result.insert("singularity_count".to_string(), vec![top_k as f64]);

        // 2. Resolution steps: iteratively "smooth" the data and count steps to flatness
        let mut current = vals.clone();
        let mut resolution_steps = 0;
        let target_flatness = {
            let range = current.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                - current.iter().cloned().fold(f64::INFINITY, f64::min);
            range * 0.01 // 1% of range
        };

        for step in 0..12 {
            // Compute max curvature
            let max_curv = (1..current.len() - 1).map(|i| {
                (current[i + 1] - 2.0 * current[i] + current[i - 1]).abs()
            }).fold(0.0f64, f64::max);

            if max_curv < target_flatness {
                resolution_steps = step;
                break;
            }

            // Blow-up: replace each singular point by its average neighborhood
            let mut smoothed = current.clone();
            for i in 1..current.len() - 1 {
                smoothed[i] = (current[i - 1] + current[i] + current[i + 1]) / 3.0;
            }
            current = smoothed;
            resolution_steps = step + 1;
        }
        result.insert("resolution_depth".to_string(), vec![resolution_steps as f64]);

        // Score: 1.0 if exactly 6 steps needed
        let depth_six_score = 1.0 - ((resolution_steps as f64 - 6.0).abs() / 6.0).min(1.0);
        result.insert("depth_six_score".to_string(), vec![depth_six_score]);

        // 3. Resolution tree structure: analyze branching pattern
        //    Build tree from hierarchical clustering of singular points
        let nn = max_n.min(50);
        let mut tree_edges = 0;
        let mut tree_depth = 0;

        // Hierarchical merge: start with n clusters, merge nearest pairs
        let mut active: Vec<bool> = vec![true; nn];
        let mut centers: Vec<Vec<f64>> = (0..nn).map(|i| {
            (0..d.min(6)).map(|j| data[i * d + j]).collect()
        }).collect();
        let mut merge_dists = Vec::new();

        for _level in 0..nn - 1 {
            // Find nearest pair
            let mut best_dist = f64::MAX;
            let mut best_i = 0;
            let mut best_j = 0;
            for i in 0..nn {
                if !active[i] { continue; }
                for j in (i + 1)..nn {
                    if !active[j] { continue; }
                    let dist = centers[i].iter().zip(&centers[j])
                        .map(|(a, b)| (a - b).powi(2)).sum::<f64>().sqrt();
                    if dist < best_dist {
                        best_dist = dist;
                        best_i = i;
                        best_j = j;
                    }
                }
            }
            if best_dist == f64::MAX { break; }

            // Merge
            for k in 0..centers[best_i].len() {
                centers[best_i][k] = (centers[best_i][k] + centers[best_j][k]) / 2.0;
            }
            active[best_j] = false;
            merge_dists.push(best_dist);
            tree_edges += 1;
            tree_depth += 1;
        }
        result.insert("tree_depth".to_string(), vec![tree_depth as f64]);
        result.insert("tree_edges".to_string(), vec![tree_edges as f64]);

        // 4. Exceptional divisor chain: count consecutive steps where smoothing
        //    reduces curvature significantly (like blowing up a singularity)
        let mut chain_length = 0;
        let mut prev_max_curv = f64::MAX;
        let mut test = vals.clone();
        for _step in 0..12 {
            let max_curv = if test.len() >= 3 {
                (1..test.len() - 1).map(|i| {
                    (test[i + 1] - 2.0 * test[i] + test[i - 1]).abs()
                }).fold(0.0f64, f64::max)
            } else {
                0.0
            };
            if max_curv < prev_max_curv * 0.8 { // significant reduction
                chain_length += 1;
            } else {
                break;
            }
            prev_max_curv = max_curv;
            // Smooth
            let mut next = test.clone();
            for i in 1..test.len() - 1 {
                next[i] = (test[i - 1] + test[i] + test[i + 1]) / 3.0;
            }
            test = next;
        }
        result.insert("exceptional_chain_length".to_string(), vec![chain_length as f64]);

        // 5. Self-intersection numbers: for each exceptional divisor (smoothing step),
        //    compute how much it "intersects" the previous configuration
        if merge_dists.len() >= 2 {
            let mut self_intersections = Vec::new();
            for i in 1..merge_dists.len().min(7) {
                let ratio = if merge_dists[i - 1] > 1e-12 {
                    merge_dists[i] / merge_dists[i - 1]
                } else {
                    0.0
                };
                self_intersections.push(ratio);
            }
            result.insert("self_intersection_ratios".to_string(), self_intersections);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_resolution_tree_basic() {
        // Data with a sharp singularity
        let data: Vec<f64> = (0..60).map(|i| {
            let x = i as f64 / 10.0 - 3.0;
            if x.abs() < 0.1 { 100.0 } else { 1.0 / x.abs() }
        }).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = ResolutionTreeLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("resolution_depth"));
        assert!(result.contains_key("exceptional_chain_length"));
    }

    #[test]
    fn test_resolution_tree_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = ResolutionTreeLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
