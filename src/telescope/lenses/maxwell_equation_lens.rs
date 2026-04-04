use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MaxwellEquationLens: Detect curl/divergence field structure consistent with Maxwell equations.
///
/// Treats data points as positions in space and uses pairwise distances to
/// reconstruct a discrete vector field, then measures:
///   1. Discrete divergence — net flux through each point's neighborhood
///   2. Discrete curl — circulation around each point's neighborhood triangles
///   3. Gauss's law score — how well divergence correlates with local charge density
///   4. Faraday score — ratio of curl magnitude to divergence, indicating wave-like structure
pub struct UmaxwellUequationLens;

impl Lens for UmaxwellUequationLens {
    fn name(&self) -> &str {
        "maxwell_equation"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d < 2 {
            return HashMap::new();
        }

        // Extract point coordinates: point i, dimension j = data[i * d + j]
        let point = |i: usize, dim: usize| -> f64 { data[i * d + dim] };

        // Build k-nearest neighbors (k = min(6, n-1)) using shared distances
        let k = 6.min(n - 1);
        let mut neighbors: Vec<Vec<usize>> = Vec::with_capacity(n);
        for i in 0..n {
            let mut dists: Vec<(f64, usize)> = (0..n)
                .filter(|&j| j != i)
                .map(|j| (shared.dist(i, j), j))
                .collect();
            dists.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
            neighbors.push(dists.iter().take(k).map(|&(_, j)| j).collect());
        }

        // Construct discrete vector field: F(i) = sum of (neighbor - i) / |neighbor - i|^2
        // This mimics an inverse-square field (Coulomb/gravitational)
        let mut field: Vec<Vec<f64>> = Vec::with_capacity(n);
        for i in 0..n {
            let mut f_vec = vec![0.0; d];
            for &j in &neighbors[i] {
                let dist_ij = shared.dist(i, j);
                if dist_ij < 1e-12 {
                    continue;
                }
                let inv_r2 = 1.0 / (dist_ij * dist_ij);
                for dim in 0..d {
                    f_vec[dim] += (point(j, dim) - point(i, dim)) * inv_r2;
                }
            }
            field.push(f_vec);
        }

        // 1. Discrete divergence at each point:
        //    div(F)_i ≈ sum over neighbors j of F(j) · (r_j - r_i) / |r_j - r_i|
        let mut divergences: Vec<f64> = Vec::with_capacity(n);
        for i in 0..n {
            let mut div_val = 0.0;
            for &j in &neighbors[i] {
                let dist_ij = shared.dist(i, j);
                if dist_ij < 1e-12 {
                    continue;
                }
                let mut dot = 0.0;
                for dim in 0..d {
                    let r_diff = point(j, dim) - point(i, dim);
                    dot += field[j][dim] * r_diff;
                }
                div_val += dot / dist_ij;
            }
            div_val /= neighbors[i].len().max(1) as f64;
            divergences.push(div_val);
        }

        // 2. Discrete curl magnitude at each point (using triangles of neighbors):
        //    For each pair of neighbors (j, k), compute circulation F·dl around triangle i-j-k
        let mut curls: Vec<f64> = Vec::with_capacity(n);
        for i in 0..n {
            let nbrs = &neighbors[i];
            let mut curl_sum = 0.0;
            let mut tri_count = 0u32;

            let max_pairs = 15.min(nbrs.len() * (nbrs.len() - 1) / 2);
            let mut pair_idx = 0;

            'outer: for a in 0..nbrs.len() {
                for b in (a + 1)..nbrs.len() {
                    if pair_idx >= max_pairs {
                        break 'outer;
                    }
                    let j = nbrs[a];
                    let kk = nbrs[b];

                    // Circulation: F(i)·(j-i) + F(j)·(k-j) + F(k)·(i-k)
                    let mut circ = 0.0;
                    for dim in 0..d {
                        let ij = point(j, dim) - point(i, dim);
                        let jk = point(kk, dim) - point(j, dim);
                        let ki = point(i, dim) - point(kk, dim);
                        circ += field[i][dim] * ij + field[j][dim] * jk + field[kk][dim] * ki;
                    }

                    // Normalize by triangle perimeter
                    let perimeter = shared.dist(i, j) + shared.dist(j, kk) + shared.dist(kk, i);
                    if perimeter > 1e-12 {
                        curl_sum += (circ / perimeter).abs();
                        tri_count += 1;
                    }
                    pair_idx += 1;
                }
            }

            curls.push(if tri_count > 0 {
                curl_sum / tri_count as f64
            } else {
                0.0
            });
        }

        // Aggregate statistics
        let mean_div = divergences.iter().map(|x| x.abs()).sum::<f64>() / n as f64;
        let mean_curl = curls.iter().sum::<f64>() / n as f64;

        let div_variance = {
            let mu = divergences.iter().sum::<f64>() / n as f64;
            divergences.iter().map(|x| (x - mu) * (x - mu)).sum::<f64>() / n as f64
        };

        // 3. Gauss's law score: correlation between divergence and local density
        //    In Maxwell's equations, div(E) = ρ/ε₀, so divergence should correlate with charge density
        let densities: Vec<f64> = (0..n)
            .map(|i| {
                let avg_dist: f64 =
                    neighbors[i].iter().map(|&j| shared.dist(i, j)).sum::<f64>()
                        / neighbors[i].len().max(1) as f64;
                if avg_dist > 1e-12 {
                    1.0 / avg_dist
                } else {
                    0.0
                }
            })
            .collect();

        let gauss_score = pearson_correlation(&divergences, &densities).abs();

        // 4. Faraday score: ratio indicating wave-like (curl-dominated) vs source-like (div-dominated)
        //    Maxwell wave regime: curl >> div (radiation), source regime: div >> curl (charges)
        let faraday_score = if mean_div > 1e-12 {
            mean_curl / (mean_curl + mean_div)
        } else if mean_curl > 1e-12 {
            1.0
        } else {
            0.5
        };

        // 5. Maxwell consistency: how well the field satisfies ∇·B = 0 constraint
        //    Use the solenoidal fraction: what fraction of the field is divergence-free
        let solenoidal_fraction = if mean_curl + mean_div > 1e-12 {
            mean_curl / (mean_curl + mean_div)
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert("mean_divergence".to_string(), vec![mean_div]);
        result.insert("mean_curl".to_string(), vec![mean_curl]);
        result.insert("divergence_variance".to_string(), vec![div_variance]);
        result.insert("gauss_law_score".to_string(), vec![gauss_score]);
        result.insert("faraday_score".to_string(), vec![faraday_score]);
        result.insert("solenoidal_fraction".to_string(), vec![solenoidal_fraction]);
        result.insert("divergences".to_string(), divergences);
        result.insert("curls".to_string(), curls);
        result
    }
}

/// Pearson correlation coefficient between two slices.
fn pearson_correlation(a: &[f64], b: &[f64]) -> f64 {
    let n = a.len().min(b.len());
    if n < 2 {
        return 0.0;
    }
    let mean_a = a.iter().sum::<f64>() / n as f64;
    let mean_b = b.iter().sum::<f64>() / n as f64;

    let mut cov = 0.0;
    let mut var_a = 0.0;
    let mut var_b = 0.0;
    for i in 0..n {
        let da = a[i] - mean_a;
        let db = b[i] - mean_b;
        cov += da * db;
        var_a += da * da;
        var_b += db * db;
    }

    let denom = (var_a * var_b).sqrt();
    if denom < 1e-12 {
        0.0
    } else {
        cov / denom
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_maxwell_scan_non_empty() {
        // 6 points in 3D arranged as two clusters — should produce non-trivial field structure
        let data = vec![
            0.0, 0.0, 0.0,
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            2.0, 2.0, 0.0,
            2.0, 0.0, 2.0,
        ];
        let n = 6;
        let d = 3;
        let shared = SharedData::compute(&data, n, d);
        let lens = UmaxwellUequationLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan should return non-empty result");
        assert!(result.contains_key("mean_divergence"));
        assert!(result.contains_key("mean_curl"));
        assert!(result.contains_key("gauss_law_score"));
        assert!(result.contains_key("faraday_score"));

        let mean_div = result["mean_divergence"][0];
        let mean_curl = result["mean_curl"][0];
        assert!(mean_div.is_finite(), "divergence should be finite");
        assert!(mean_curl.is_finite(), "curl should be finite");
        assert!(mean_div > 0.0 || mean_curl > 0.0, "at least one measure should be non-zero");
    }

    #[test]
    fn test_maxwell_curl_on_rotational_field() {
        // Points arranged in a circle in 2D — rotational structure should yield higher curl
        let n = 8;
        let d = 2;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let angle = 2.0 * std::f64::consts::PI * i as f64 / n as f64;
            data.push(angle.cos());
            data.push(angle.sin());
        }
        let shared = SharedData::compute(&data, n, d);
        let lens = UmaxwellUequationLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        let curls = &result["curls"];
        assert_eq!(curls.len(), n);
        // At least some points should have non-zero curl for a circular arrangement
        let nonzero_curls = curls.iter().filter(|&&c| c > 1e-10).count();
        assert!(nonzero_curls > 0, "circular arrangement should produce non-zero curls");

        let divs = &result["divergences"];
        assert_eq!(divs.len(), n);
    }
}
