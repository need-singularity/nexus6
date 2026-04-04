use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// BernsteinApproximationLens: Polynomial approximation via Bernstein basis of degree 6.
///
/// Analyzes function approximation quality using Bernstein polynomials,
/// condition number of the Bernstein-Bezier representation, and
/// variation diminishing properties.
pub struct BernsteinApproximationLens;

impl Lens for BernsteinApproximationLens {
    fn name(&self) -> &str { "BernsteinApproximationLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 8 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let degree = 6;

        let mut approx_errors = Vec::new();
        let mut condition_numbers = Vec::new();
        let mut variation_ratios = Vec::new();
        let mut control_point_spreads = Vec::new();

        for col in columns.iter().take(d.min(12)) {
            // Compute Bernstein coefficients (control points) for degree 6
            let ctrl = bernstein_control_points(col, degree);

            // Evaluate Bernstein polynomial and compute L2 error
            let err = bernstein_l2_error(col, &ctrl, degree);
            approx_errors.push(err);

            // Condition number: max|B_k(x)| * max|c_k| / max|p(x)|
            let cond = bernstein_condition_number(&ctrl, degree);
            condition_numbers.push(cond);

            // Variation diminishing: ratio of sign changes in control points
            // vs sign changes in sampled data
            let data_sign_changes = count_sign_changes(col);
            let ctrl_sign_changes = count_sign_changes(&ctrl);
            let ratio = if data_sign_changes > 0 {
                ctrl_sign_changes as f64 / data_sign_changes as f64
            } else {
                if ctrl_sign_changes == 0 { 1.0 } else { 0.0 }
            };
            variation_ratios.push(ratio);

            // Spread of control points (std dev)
            let mean_ctrl = ctrl.iter().sum::<f64>() / ctrl.len() as f64;
            let var_ctrl = ctrl.iter().map(|c| (c - mean_ctrl).powi(2)).sum::<f64>() / ctrl.len() as f64;
            control_point_spreads.push(var_ctrl.sqrt());
        }

        if approx_errors.is_empty() { return HashMap::new(); }

        let mean_error = approx_errors.iter().sum::<f64>() / approx_errors.len() as f64;
        let mean_cond = condition_numbers.iter().sum::<f64>() / condition_numbers.len() as f64;

        let mut result = HashMap::new();
        result.insert("bernstein_approx_error".to_string(), approx_errors);
        result.insert("bernstein_condition_number".to_string(), condition_numbers);
        result.insert("bernstein_variation_ratio".to_string(), variation_ratios);
        result.insert("bernstein_control_spread".to_string(), control_point_spreads);
        result.insert("bernstein_mean_error".to_string(), vec![mean_error]);
        result.insert("bernstein_mean_condition".to_string(), vec![mean_cond]);
        result.insert("score".to_string(), vec![result["bernstein_approx_error"][0].min(1.0).max(0.0)]);
        result
    }
}

/// Binomial coefficient C(n, k).
fn binom(n: usize, k: usize) -> f64 {
    if k > n { return 0.0; }
    let k = k.min(n - k);
    let mut result = 1.0;
    for i in 0..k {
        result *= (n - i) as f64;
        result /= (i + 1) as f64;
    }
    result
}

/// Evaluate Bernstein basis polynomial B_{k,n}(t).
fn bernstein_basis(k: usize, n: usize, t: f64) -> f64 {
    binom(n, k) * t.powi(k as i32) * (1.0 - t).powi((n - k) as i32)
}

/// Compute Bernstein control points by least-squares fitting.
/// For data sampled at t_i = i/(N-1), solve B^T B c = B^T f.
fn bernstein_control_points(data: &[f64], degree: usize) -> Vec<f64> {
    let n = data.len();
    let m = degree + 1; // number of control points

    // Build normal equations: A = B^T B, rhs = B^T f
    let mut ata = vec![0.0; m * m];
    let mut atb = vec![0.0; m];

    for i in 0..n {
        let t = i as f64 / (n - 1).max(1) as f64;
        let mut basis = Vec::with_capacity(m);
        for k in 0..m {
            basis.push(bernstein_basis(k, degree, t));
        }
        for j in 0..m {
            for l in 0..m {
                ata[j * m + l] += basis[j] * basis[l];
            }
            atb[j] += basis[j] * data[i];
        }
    }

    // Regularize for stability
    for j in 0..m {
        ata[j * m + j] += 1e-10;
    }

    // Solve via Cholesky-like approach (symmetric positive definite)
    solve_spd(m, &ata, &atb)
}

/// Solve symmetric positive definite system via Gaussian elimination.
fn solve_spd(n: usize, ata: &[f64], atb: &[f64]) -> Vec<f64> {
    let mut mat = ata.to_vec();
    let mut rhs = atb.to_vec();

    for col in 0..n {
        let pivot = mat[col * n + col];
        if pivot.abs() < 1e-15 { continue; }
        for row in (col + 1)..n {
            let factor = mat[row * n + col] / pivot;
            for j in col..n {
                let v = mat[col * n + j];
                mat[row * n + j] -= factor * v;
            }
            let v = rhs[col];
            rhs[row] -= factor * v;
        }
    }

    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        let diag = mat[i * n + i];
        if diag.abs() < 1e-15 { continue; }
        let mut sum = rhs[i];
        for j in (i + 1)..n {
            sum -= mat[i * n + j] * x[j];
        }
        x[i] = sum / diag;
    }
    x
}

/// Evaluate Bernstein polynomial L2 error against data.
fn bernstein_l2_error(data: &[f64], ctrl: &[f64], degree: usize) -> f64 {
    let n = data.len();
    let mut err_sq = 0.0;
    for i in 0..n {
        let t = i as f64 / (n - 1).max(1) as f64;
        let mut val = 0.0;
        for (k, &c) in ctrl.iter().enumerate() {
            val += c * bernstein_basis(k, degree, t);
        }
        let diff = data[i] - val;
        err_sq += diff * diff;
    }
    (err_sq / n as f64).sqrt()
}

/// Compute condition number of the Bernstein representation.
fn bernstein_condition_number(ctrl: &[f64], degree: usize) -> f64 {
    let max_ctrl = ctrl.iter().map(|c| c.abs()).fold(0.0, f64::max);
    if max_ctrl < 1e-15 { return 1.0; }

    // Evaluate polynomial at dense grid
    let steps = 100;
    let mut max_val = 0.0f64;
    for i in 0..=steps {
        let t = i as f64 / steps as f64;
        let mut val = 0.0;
        for (k, &c) in ctrl.iter().enumerate() {
            val += c * bernstein_basis(k, degree, t);
        }
        max_val = max_val.max(val.abs());
    }

    if max_val < 1e-15 { return 1.0; }

    // Condition ~ (degree+1) * max|c_k| / max|p(x)|
    (degree + 1) as f64 * max_ctrl / max_val
}

/// Count sign changes in a sequence (zeros are skipped).
fn count_sign_changes(data: &[f64]) -> usize {
    let mut count = 0;
    let mut prev_sign = 0i32;
    for &v in data {
        let s = if v > 1e-12 { 1 } else if v < -1e-12 { -1 } else { 0 };
        if s != 0 {
            if prev_sign != 0 && s != prev_sign { count += 1; }
            prev_sign = s;
        }
    }
    count
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bernstein_lens() {
        let n = 32;
        let d = 1;
        let data: Vec<f64> = (0..n)
            .map(|i| {
                let t = i as f64 / (n - 1) as f64;
                t * t * (1.0 - t) // simple polynomial
            })
            .collect();
        let shared = SharedData::compute(&data, n, d);
        let result = BernsteinApproximationLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("bernstein_approx_error"));
        // Degree-6 Bernstein should approximate a degree-3 polynomial well
        assert!(result["bernstein_mean_error"][0] < 0.01);
    }
}
