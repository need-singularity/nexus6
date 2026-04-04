use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// SubdifferentialLens: Non-smooth optimization analysis in 6 dimensions.
///
/// Analyzes:
/// - Subdifferential cardinality at non-differentiable points
/// - Clarke generalized gradient estimation
/// - Proximity operator residuals
/// - Non-smoothness measure (kink detection)
pub struct SubdifferentialLens;

impl Lens for SubdifferentialLens {
    fn name(&self) -> &str { "SubdifferentialLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 8 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let dim = d.min(6);

        let mut kink_counts = Vec::new();
        let mut subdiff_cardinalities = Vec::new();
        let mut prox_residuals = Vec::new();
        let mut nonsmoothness_scores = Vec::new();

        for col in columns.iter().take(dim) {
            // Detect kinks: points where left and right derivatives differ significantly
            let kinks = detect_kinks(col);
            kink_counts.push(kinks.len() as f64);

            // Estimate subdifferential cardinality at kinks
            let card = estimate_subdifferential_cardinality(col, &kinks);
            subdiff_cardinalities.push(card);

            // Proximity operator residual: ||x - prox_{f}(x)||
            let prox_res = proximity_residual(col);
            prox_residuals.push(prox_res);

            // Non-smoothness score: normalized total variation of gradient
            let ns = nonsmoothness_measure(col);
            nonsmoothness_scores.push(ns);
        }

        if kink_counts.is_empty() { return HashMap::new(); }

        // Multi-dimensional analysis: Clarke generalized gradient norm
        let clarke_norms = clarke_gradient_norms(data, n, d, dim);

        let mean_kinks = kink_counts.iter().sum::<f64>() / kink_counts.len() as f64;
        let mean_ns = nonsmoothness_scores.iter().sum::<f64>() / nonsmoothness_scores.len() as f64;

        let mut result = HashMap::new();
        result.insert("subdiff_kink_count".to_string(), kink_counts);
        result.insert("subdiff_cardinality".to_string(), subdiff_cardinalities);
        result.insert("subdiff_prox_residual".to_string(), prox_residuals);
        result.insert("subdiff_nonsmoothness".to_string(), nonsmoothness_scores);
        result.insert("subdiff_clarke_norm".to_string(), clarke_norms);
        result.insert("subdiff_mean_kinks".to_string(), vec![mean_kinks]);
        result.insert("subdiff_mean_nonsmoothness".to_string(), vec![mean_ns]);
        result
    }
}

/// Detect kinks (non-differentiable points) by comparing left/right derivatives.
fn detect_kinks(col: &[f64]) -> Vec<usize> {
    let n = col.len();
    if n < 3 { return Vec::new(); }

    let h = 1.0 / (n - 1).max(1) as f64;
    let threshold = 0.5; // relative derivative jump threshold

    let mut kinks = Vec::new();
    for i in 1..n - 1 {
        let left_deriv = (col[i] - col[i - 1]) / h;
        let right_deriv = (col[i + 1] - col[i]) / h;
        let jump = (right_deriv - left_deriv).abs();
        let scale = left_deriv.abs().max(right_deriv.abs()).max(1e-10);

        if jump / scale > threshold {
            kinks.push(i);
        }
    }
    kinks
}

/// Estimate subdifferential cardinality at kink points.
/// The subdifferential at a kink is the interval [left_deriv, right_deriv].
/// We discretize this interval to estimate "effective cardinality".
fn estimate_subdifferential_cardinality(col: &[f64], kinks: &[usize]) -> f64 {
    let n = col.len();
    if kinks.is_empty() || n < 3 { return 1.0; } // smooth = singleton subdiff

    let h = 1.0 / (n - 1).max(1) as f64;
    let mut total_card = 0.0;

    for &i in kinks {
        let left = (col[i] - col[i - 1]) / h;
        let right = (col[i + 1] - col[i]) / h;
        // Width of subdifferential interval
        let width = (right - left).abs();
        // Effective cardinality: proportional to width, capped at 6
        let card = (width / (1e-10 + width.abs())).min(6.0).max(1.0);
        total_card += card;
    }

    total_card / kinks.len() as f64
}

/// Compute proximity operator residual.
/// prox_{lambda*f}(x) = argmin_y { f(y) + 1/(2*lambda) ||y - x||^2 }
/// For L1 norm (typical non-smooth function), prox is soft thresholding.
fn proximity_residual(col: &[f64]) -> f64 {
    let n = col.len();
    if n == 0 { return 0.0; }

    let lambda = 0.1;
    let mut residual_sq = 0.0;

    for &x in col {
        // Soft thresholding (prox of L1)
        let prox = if x > lambda {
            x - lambda
        } else if x < -lambda {
            x + lambda
        } else {
            0.0
        };
        residual_sq += (x - prox).powi(2);
    }

    (residual_sq / n as f64).sqrt()
}

/// Non-smoothness measure: total variation of the numerical gradient.
fn nonsmoothness_measure(col: &[f64]) -> f64 {
    let n = col.len();
    if n < 3 { return 0.0; }

    let h = 1.0 / (n - 1).max(1) as f64;

    // Compute gradient
    let mut grads = Vec::with_capacity(n - 1);
    for i in 0..n - 1 {
        grads.push((col[i + 1] - col[i]) / h);
    }

    // Total variation of gradient
    let mut tv = 0.0;
    for i in 0..grads.len() - 1 {
        tv += (grads[i + 1] - grads[i]).abs();
    }

    // Normalize by data range
    let range = col.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
        - col.iter().cloned().fold(f64::INFINITY, f64::min);

    if range < 1e-15 { 0.0 } else { tv / (range * n as f64) }
}

/// Clarke generalized gradient norms in multi-dimensional setting.
fn clarke_gradient_norms(data: &[f64], n: usize, d: usize, dim: usize) -> Vec<f64> {
    if n < 3 || dim == 0 { return Vec::new(); }

    let step = (n / 30).max(1);
    let mut norms = Vec::new();

    for i in (1..n - 1).step_by(step) {
        // Clarke gradient approximation:
        // conv{ lim grad f(x_k) : x_k -> x }
        // We approximate by collecting finite difference gradients from neighbors
        let mut grad_sum = vec![0.0; dim];
        let mut count = 0;

        // Use k nearest neighbors
        let k_start = if i >= 3 { i - 3 } else { 0 };
        let k_end = (i + 3).min(n - 1);

        for k in k_start..k_end {
            if k + 1 >= n { continue; }
            for dd in 0..dim {
                let idx_curr = k * d + dd;
                let idx_next = (k + 1) * d + dd;
                if idx_next < data.len() {
                    grad_sum[dd] += data[idx_next] - data[idx_curr];
                    count += 1;
                }
            }
        }

        if count > 0 {
            let norm: f64 = grad_sum.iter()
                .map(|g| (g / count as f64).powi(2))
                .sum::<f64>()
                .sqrt();
            norms.push(norm);
        }
    }

    norms
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_subdifferential_lens_abs() {
        let n = 32;
        let d = 1;
        // |x - 0.5| has a kink at x = 0.5
        let data: Vec<f64> = (0..n)
            .map(|i| {
                let t = i as f64 / (n - 1) as f64;
                (t - 0.5).abs()
            })
            .collect();
        let shared = SharedData::compute(&data, n, d);
        let result = SubdifferentialLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("subdiff_kink_count"));
        assert!(result["subdiff_kink_count"][0] >= 1.0);
    }
}
