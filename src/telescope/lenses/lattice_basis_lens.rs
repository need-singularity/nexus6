use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// LatticeBasisLens: Lattice cryptography analysis.
///
/// Treats data points as lattice vectors in 6-dimensional space:
/// - Computes Gram-Schmidt orthogonalization quality
/// - Hermite factor: ratio of shortest vector to det^(1/dim)
/// - Lattice gap: ratio between successive minima
/// - LLL-reduction quality metric
pub struct LatticeBasisLens;

impl Lens for LatticeBasisLens {
    fn name(&self) -> &str { "LatticeBasisLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = shared;
        if n < 6 || d == 0 { return HashMap::new(); }

        // Use first min(n, 6) points as basis vectors in d-dim space
        let basis_count = n.min(6);
        let dim = d;

        // Extract basis vectors
        let mut basis: Vec<Vec<f64>> = Vec::new();
        for i in 0..basis_count {
            let row: Vec<f64> = (0..dim).map(|j| data[i * d + j]).collect();
            basis.push(row);
        }

        // Gram-Schmidt orthogonalization
        let mut gs_basis: Vec<Vec<f64>> = Vec::new();
        let mut gs_norms: Vec<f64> = Vec::new();

        for i in 0..basis_count {
            let mut v = basis[i].clone();
            for j in 0..i {
                if gs_norms[j] < 1e-15 { continue; }
                let mu = dot(&basis[i], &gs_basis[j]) / gs_norms[j];
                for k in 0..dim {
                    v[k] -= mu * gs_basis[j][k];
                }
            }
            let norm_sq = dot(&v, &v);
            gs_norms.push(norm_sq);
            gs_basis.push(v);
        }

        // Orthogonality defect: product of ||b*_i|| vs det(L)^(1/n)
        let log_product: f64 = gs_norms.iter()
            .filter(|&&n| n > 1e-30)
            .map(|n| n.ln() * 0.5) // ln(||b*_i||)
            .sum();

        // Original basis norms
        let orig_norms: Vec<f64> = basis.iter().map(|b| dot(b, b).sqrt()).collect();
        let log_orig_product: f64 = orig_norms.iter()
            .filter(|&&n| n > 1e-30)
            .map(|n| n.ln())
            .sum();

        let orthogonality_defect = if log_product.abs() > 1e-30 {
            (log_orig_product - log_product).exp()
        } else {
            1.0
        };

        // Shortest vector approximation
        let shortest = orig_norms.iter().cloned().fold(f64::MAX, f64::min);

        // Determinant approximation: product of GS norms
        let log_det = gs_norms.iter()
            .filter(|&&n| n > 1e-30)
            .map(|n| n.ln() * 0.5)
            .sum::<f64>();
        let det_root = (log_det / basis_count as f64).exp();

        // Hermite factor: ||shortest|| / det^(1/dim)
        let hermite_factor = if det_root > 1e-15 { shortest / det_root } else { 0.0 };

        // Hermite constant bound for dim 6: gamma_6^(1/2) ~ 1.414 (known)
        let hermite_6_bound = std::f64::consts::SQRT_2;
        let hermite_quality = if hermite_factor > 1e-15 {
            (hermite_6_bound / hermite_factor).min(1.0)
        } else { 0.0 };

        // Successive minima ratios: sort norms and compute gaps
        let mut sorted_norms = orig_norms.clone();
        sorted_norms.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let mut gap_ratios = Vec::new();
        for i in 0..sorted_norms.len().saturating_sub(1) {
            if sorted_norms[i] > 1e-15 {
                gap_ratios.push(sorted_norms[i + 1] / sorted_norms[i]);
            }
        }
        let mean_gap = if gap_ratios.is_empty() { 1.0 }
            else { gap_ratios.iter().sum::<f64>() / gap_ratios.len() as f64 };

        // LLL reduction quality: check Lovász condition
        // For each pair, mu_{i,i-1}^2 <= 3/4 - delta (delta = 3/4)
        let mut lll_violations = 0;
        for i in 1..basis_count {
            if gs_norms[i - 1] < 1e-30 { continue; }
            let mu = dot(&basis[i], &gs_basis[i - 1]) / gs_norms[i - 1];
            // Lovász condition: ||b*_i||^2 >= (3/4 - mu^2) * ||b*_{i-1}||^2
            let lhs = gs_norms[i];
            let rhs = (0.75 - mu * mu) * gs_norms[i - 1];
            if lhs < rhs { lll_violations += 1; }
        }
        let lll_quality = 1.0 - lll_violations as f64 / (basis_count.max(1) - 1).max(1) as f64;

        // n=6 dimension resonance
        let n6_dim_match = if basis_count == 6 { 1.0 } else {
            (-((basis_count as f64 - 6.0).abs() * 0.3)).exp()
        };

        let mut result = HashMap::new();
        result.insert("basis_dimension".into(), vec![basis_count as f64]);
        result.insert("orthogonality_defect".into(), vec![orthogonality_defect]);
        result.insert("hermite_factor".into(), vec![hermite_factor]);
        result.insert("hermite_quality".into(), vec![hermite_quality]);
        result.insert("successive_minima_gap".into(), vec![mean_gap]);
        result.insert("lll_quality".into(), vec![lll_quality]);
        result.insert("n6_dim_match".into(), vec![n6_dim_match]);
        result.insert("gs_norms".into(), gs_norms.iter().map(|n| n.sqrt()).collect());
        result
    }
}

fn dot(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lattice_basis() {
        // 6 basis vectors in 3D (standard + scaled)
        let data = vec![
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0,
            1.0, 1.0, 0.0,
            1.0, 0.0, 1.0,
            0.0, 1.0, 1.0,
        ];
        let n = 6;
        let d = 3;
        let shared = SharedData::compute(&data, n, d);
        let r = LatticeBasisLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("hermite_factor"));
        assert!(r["lll_quality"][0] >= 0.0);
        assert_eq!(r["n6_dim_match"][0], 1.0);
    }
}
