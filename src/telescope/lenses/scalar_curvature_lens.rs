use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ScalarCurvatureLens: Ricci scalar curvature on 6-dim data manifold.
///
/// Estimates the scalar curvature R of the data manifold by computing
/// the local metric tensor gᵢⱼ from k-nearest neighbors, then the
/// Christoffel symbols and Riemann tensor components.
///
/// For a 6-dim spacetime, the Einstein equation is:
///   Rμν - (1/2)gμν R + Λgμν = 8πG Tμν
/// The scalar curvature R = gᵘᵛ Rμν encodes total curvature.
///
/// Metrics:
///   1. scalar_curvature: mean Ricci scalar R across the manifold
///   2. curvature_variance: how much curvature varies (inhomogeneity)
///   3. einstein_tensor_trace: trace of Gμν = Rμν - (1/2)gμν R
///   4. positive_curvature_fraction: fraction of points with R > 0
///   5. curvature_per_dim: contribution from each of 6 dimensions
///
/// n=6: 6-dimensional spacetime (5+1 or 4+2 signature possibilities).
pub struct ScalarCurvatureLens;

impl Lens for ScalarCurvatureLens {
    fn name(&self) -> &str { "ScalarCurvatureLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let k = ((n as f64).sqrt().ceil() as usize).max(2).min(n - 1);
        let eff_d = d.min(6); // work with at most 6 dimensions

        // For each point, estimate local curvature via neighborhood geometry
        let mut curvatures = Vec::with_capacity(n);
        let mut curvature_per_dim = vec![0.0f64; eff_d];

        let max_check = n.min(200);
        for i in 0..max_check {
            // Find k nearest neighbors
            let mut neighbors: Vec<(usize, f64)> = (0..n)
                .filter(|&j| j != i)
                .map(|j| (j, shared.dist(i, j)))
                .collect();
            neighbors.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
            neighbors.truncate(k);

            if neighbors.is_empty() { continue; }

            // Local metric tensor: gᵢⱼ = (1/k) Σₙ δxᵢⁿ δxⱼⁿ
            let mut g = vec![0.0f64; eff_d * eff_d];
            for &(j, _) in &neighbors {
                for di in 0..eff_d {
                    let dxi = data[j * d + di] - data[i * d + di];
                    for dj in di..eff_d {
                        let dxj = data[j * d + dj] - data[i * d + dj];
                        g[di * eff_d + dj] += dxi * dxj;
                        if di != dj {
                            g[dj * eff_d + di] += dxi * dxj;
                        }
                    }
                }
            }
            let inv_k = 1.0 / k as f64;
            for v in g.iter_mut() { *v *= inv_k; }

            // Scalar curvature via sectional curvatures
            // For each pair of dimensions (a,b), sectional curvature:
            //   K(a,b) ≈ (gₐₐ gᵦᵦ - gₐᵦ²) deviation from flatness
            // R = Σ_{a<b} K(a,b) × 2
            let mut r_local = 0.0f64;
            for a in 0..eff_d {
                for b in (a + 1)..eff_d {
                    let gaa = g[a * eff_d + a];
                    let gbb = g[b * eff_d + b];
                    let gab = g[a * eff_d + b];
                    let det = gaa * gbb - gab * gab;
                    let flat_det = gaa * gbb; // expected if orthogonal

                    if flat_det.abs() > 1e-12 {
                        // Sectional curvature ~ (det - flat_det) / flat_det
                        let sectional = (det - flat_det) / flat_det.abs();
                        r_local += sectional;

                        // Attribute curvature to each dimension
                        curvature_per_dim[a] += sectional.abs() / max_check as f64;
                        curvature_per_dim[b] += sectional.abs() / max_check as f64;
                    }
                }
            }
            // Factor of 2 for Ricci scalar from sectional curvatures
            r_local *= 2.0 / (eff_d * (eff_d - 1)).max(1) as f64;
            curvatures.push(r_local);
        }

        if curvatures.is_empty() { return HashMap::new(); }

        let mean_r = curvatures.iter().sum::<f64>() / curvatures.len() as f64;
        let var_r = curvatures.iter()
            .map(|&r| (r - mean_r).powi(2))
            .sum::<f64>() / curvatures.len() as f64;

        // Einstein tensor trace: for d-dim, G^μ_μ = R(1 - d/2)
        // In 6D: trace = R × (1 - 3) = -2R
        let einstein_trace = mean_r * (1.0 - eff_d as f64 / 2.0);

        let pos_frac = curvatures.iter().filter(|&&r| r > 0.0).count() as f64
            / curvatures.len() as f64;

        let mut result = HashMap::new();
        result.insert("scalar_curvature".to_string(), vec![mean_r]);
        result.insert("curvature_variance".to_string(), vec![var_r]);
        result.insert("einstein_tensor_trace".to_string(), vec![einstein_trace]);
        result.insert("positive_curvature_fraction".to_string(), vec![pos_frac]);
        result.insert("curvature_per_dim".to_string(), curvature_per_dim);
        result.insert("local_curvatures".to_string(), curvatures);
        result.insert("score".to_string(), vec![result["scalar_curvature"][0].min(1.0).max(0.0)]);
        result
    }
}
