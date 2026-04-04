use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var};

/// IsometryGroupLens: 6-dim transitive isometry and Killing vector detection.
///
/// Detects continuous symmetries (isometries) of the data manifold by
/// finding approximate Killing vectors — directions along which the
/// metric (distance structure) is invariant.
///
/// A Killing vector ξ satisfies ∇_μ ξ_ν + ∇_ν ξ_μ = 0.
/// In 6D, the maximal isometry group has dim = 6×7/2 = 21 generators.
///
/// Metrics:
///   1. killing_vector_count: number of approximate Killing directions
///   2. isometry_dimension: effective dimension of isometry group
///   3. transitivity_score: how transitive the symmetry action is
///   4. killing_norms: magnitude of each detected Killing vector
///   5. symmetry_breaking_params: deviation from exact symmetry
///
/// n=6: 6-dim manifold, maximal 21 Killing vectors, SO(6) ~ SU(4).
pub struct IsometryGroupLens;

impl Lens for IsometryGroupLens {
    fn name(&self) -> &str { "IsometryGroupLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let eff_d = d.min(6);
        let (means, vars) = mean_var(data, n, d);

        // Test each axis direction as candidate Killing vector
        // A direction ξ is Killing if translating along ξ preserves distances
        let max_check = n.min(100);
        let mut killing_scores = Vec::with_capacity(eff_d);
        let mut killing_norms = Vec::with_capacity(eff_d);

        for dim in 0..eff_d {
            // Sort points by this dimension
            let mut sorted_idx: Vec<usize> = (0..max_check).collect();
            sorted_idx.sort_by(|&a, &b| {
                let va = data[a * d + dim];
                let vb = data[b * d + dim];
                va.partial_cmp(&vb).unwrap_or(std::cmp::Ordering::Equal)
            });

            // Compare distance matrices of "early" vs "late" points along this direction
            let half = max_check / 2;
            let group_a: Vec<usize> = sorted_idx[..half].to_vec();
            let group_b: Vec<usize> = sorted_idx[half..].to_vec();

            // Average distance within each group
            let mut dist_a = 0.0f64;
            let mut count_a = 0u32;
            for i in 0..group_a.len().min(30) {
                for j in (i + 1)..group_a.len().min(30) {
                    dist_a += shared.dist(group_a[i], group_a[j]);
                    count_a += 1;
                }
            }
            let mut dist_b = 0.0f64;
            let mut count_b = 0u32;
            for i in 0..group_b.len().min(30) {
                for j in (i + 1)..group_b.len().min(30) {
                    dist_b += shared.dist(group_b[i], group_b[j]);
                    count_b += 1;
                }
            }

            let mean_a = if count_a > 0 { dist_a / count_a as f64 } else { 0.0 };
            let mean_b = if count_b > 0 { dist_b / count_b as f64 } else { 0.0 };

            // Killing score: distance structure invariance
            // Perfect Killing: mean_a ≈ mean_b
            let avg = (mean_a + mean_b) / 2.0;
            let killing_score = if avg > 1e-12 {
                1.0 - (mean_a - mean_b).abs() / avg
            } else {
                0.0
            };
            killing_scores.push(killing_score.max(0.0));
            killing_norms.push(vars[dim].sqrt());
        }

        // Count approximate Killing vectors (score > 0.8)
        let killing_threshold = 0.8;
        let killing_count = killing_scores.iter()
            .filter(|&&s| s > killing_threshold)
            .count();

        // Isometry group dimension estimate:
        // Also check rotation-like symmetries (pairs of dimensions)
        let mut rotation_scores = Vec::new();
        for di in 0..eff_d {
            for dj in (di + 1)..eff_d {
                // Check if rotation in (di, dj) plane preserves distances
                // Compare correlation of distances with angle in this plane
                let mut angle_dist_corr = 0.0f64;
                let mut count = 0u32;

                for row in 0..max_check.min(50) {
                    let xi = data[row * d + di] - means[di];
                    let xj = data[row * d + dj] - means[dj];
                    let angle = xj.atan2(xi);
                    let radius = (xi * xi + xj * xj).sqrt();

                    // If isometry: radius independent of angle
                    angle_dist_corr += (angle * radius).abs();
                    count += 1;
                }

                if count > 0 {
                    let mean_corr = angle_dist_corr / count as f64;
                    // Normalize
                    let std_a = vars[di].sqrt().max(1e-12);
                    let std_j = vars[dj].sqrt().max(1e-12);
                    let norm_corr = mean_corr / (std_a * std_j);
                    // Low correlation = good rotational symmetry
                    rotation_scores.push(1.0 / (1.0 + norm_corr));
                }
            }
        }

        let rot_killing = rotation_scores.iter()
            .filter(|&&s| s > killing_threshold)
            .count();

        let isometry_dim = killing_count + rot_killing;

        // Transitivity score: if isometry group acts transitively,
        // all points should be reachable from any other via symmetry
        // Proxy: uniformity of distance distribution
        let mut all_dists: Vec<f64> = Vec::new();
        for i in 0..max_check.min(50) {
            for j in (i + 1)..max_check.min(50) {
                all_dists.push(shared.dist(i, j));
            }
        }
        let transitivity = if !all_dists.is_empty() {
            let d_mean = all_dists.iter().sum::<f64>() / all_dists.len() as f64;
            let d_var = all_dists.iter()
                .map(|&x| (x - d_mean).powi(2))
                .sum::<f64>() / all_dists.len() as f64;
            let cv = d_var.sqrt() / d_mean.max(1e-12);
            1.0 / (1.0 + cv) // Low CV = more transitive
        } else {
            0.0
        };

        // Symmetry breaking parameters
        let breaking: Vec<f64> = killing_scores.iter().map(|&s| 1.0 - s).collect();

        let mut result = HashMap::new();
        result.insert("killing_vector_count".to_string(), vec![killing_count as f64]);
        result.insert("isometry_dimension".to_string(), vec![isometry_dim as f64]);
        result.insert("transitivity_score".to_string(), vec![transitivity]);
        result.insert("killing_norms".to_string(), killing_norms);
        result.insert("killing_scores".to_string(), killing_scores);
        result.insert("symmetry_breaking_params".to_string(), breaking);
        result
    }
}
