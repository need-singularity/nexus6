use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// PadeApproximantLens: Rational approximation via Pade [m,n] with m+n=6.
///
/// Fits Pade approximants to each feature column and analyzes:
/// - Pole positions of the rational approximant
/// - Approximation error (L2 norm of residual)
/// - Best [m,n] partition (m+n=6)
pub struct PadeApproximantLens;

impl Lens for PadeApproximantLens {
    fn name(&self) -> &str { "PadeApproximantLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 8 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let mut best_errors = Vec::new();
        let mut best_m_vals = Vec::new();
        let mut pole_counts = Vec::new();
        let mut min_pole_dists = Vec::new();

        for col in columns.iter().take(d.min(12)) {
            // Compute Taylor coefficients from data via finite differences
            let taylor = taylor_from_samples(col, 7); // need 7 coefficients for m+n=6

            let mut best_err = f64::INFINITY;
            let mut best_m = 0usize;
            let mut best_poles: Vec<f64> = Vec::new();

            // Try all [m,n] partitions with m+n=6
            for m in 0..=6 {
                let nn = 6 - m;
                if let Some((num, den)) = pade_coefficients(&taylor, m, nn) {
                    // Evaluate approximation error
                    let err = evaluate_pade_error(col, &num, &den);
                    if err < best_err {
                        best_err = err;
                        best_m = m;
                        best_poles = find_real_poles(&den);
                    }
                }
            }

            best_errors.push(best_err);
            best_m_vals.push(best_m as f64);
            pole_counts.push(best_poles.len() as f64);

            // Minimum distance of poles from the unit interval [0,1]
            let min_dist = best_poles.iter()
                .map(|&p| p.abs().min((p - 1.0).abs()))
                .fold(f64::INFINITY, f64::min);
            min_pole_dists.push(if min_dist.is_finite() { min_dist } else { 0.0 });
        }

        if best_errors.is_empty() { return HashMap::new(); }

        let mean_error = best_errors.iter().sum::<f64>() / best_errors.len() as f64;
        let mean_poles = pole_counts.iter().sum::<f64>() / pole_counts.len() as f64;

        let mut result = HashMap::new();
        result.insert("pade_best_error".to_string(), best_errors);
        result.insert("pade_best_m".to_string(), best_m_vals);
        result.insert("pade_pole_count".to_string(), pole_counts);
        result.insert("pade_min_pole_distance".to_string(), min_pole_dists);
        result.insert("pade_mean_error".to_string(), vec![mean_error]);
        result.insert("pade_mean_pole_count".to_string(), vec![mean_poles]);
        result.insert("score".to_string(), vec![result["pade_best_error"][0].min(1.0).max(0.0)]);
        result
    }
}

/// Estimate Taylor coefficients from uniformly sampled data using finite differences.
fn taylor_from_samples(data: &[f64], num_coeffs: usize) -> Vec<f64> {
    let n = data.len();
    if n == 0 { return vec![0.0; num_coeffs]; }

    let h = 1.0 / (n - 1).max(1) as f64;
    let mut coeffs = Vec::with_capacity(num_coeffs);

    // c_0 = f(0)
    coeffs.push(data[0]);

    // Higher order coefficients via forward finite differences
    // c_k = Delta^k f(0) / (k! * h^k)
    let mut diffs: Vec<f64> = data.to_vec();
    let mut factorial = 1.0;

    for k in 1..num_coeffs {
        factorial *= k as f64;
        let mut new_diffs = Vec::with_capacity(diffs.len().saturating_sub(1));
        for i in 0..diffs.len().saturating_sub(1) {
            new_diffs.push(diffs[i + 1] - diffs[i]);
        }
        if new_diffs.is_empty() {
            coeffs.push(0.0);
        } else {
            coeffs.push(new_diffs[0] / (factorial * h.powi(k as i32)));
        }
        diffs = new_diffs;
    }

    coeffs
}

/// Compute Pade [m/n] coefficients from Taylor series.
/// Returns (numerator_coeffs, denominator_coeffs) or None if singular.
fn pade_coefficients(taylor: &[f64], m: usize, n: usize) -> Option<(Vec<f64>, Vec<f64>)> {
    let total = m + n + 1;
    if taylor.len() < total { return None; }
    if n == 0 {
        // Pure polynomial case
        return Some((taylor[..=m].to_vec(), vec![1.0]));
    }

    // Solve for denominator coefficients b_1..b_n from the linear system:
    // sum_{j=1}^{n} b_j * c_{m+i-j} = -c_{m+i}  for i = 1..n
    // where c_k = taylor[k] (c_k=0 if k<0)

    let c = |k: i64| -> f64 {
        if k < 0 || k >= taylor.len() as i64 { 0.0 } else { taylor[k as usize] }
    };

    // Build n x n system
    let mut mat = vec![0.0; n * n];
    let mut rhs = vec![0.0; n];

    for i in 0..n {
        for j in 0..n {
            mat[i * n + j] = c((m as i64) + (i as i64) + 1 - (j as i64) - 1);
        }
        rhs[i] = -c((m as i64) + (i as i64) + 1);
    }

    // Gaussian elimination with partial pivoting
    let b = solve_linear(n, &mut mat, &mut rhs)?;

    // Denominator: 1 + b_1*x + b_2*x^2 + ...
    let mut den = Vec::with_capacity(n + 1);
    den.push(1.0);
    den.extend_from_slice(&b);

    // Numerator: a_k = sum_{j=0}^{min(k,n)} b_j * c_{k-j}, b_0=1
    let mut num = Vec::with_capacity(m + 1);
    for k in 0..=m {
        let mut a_k = 0.0;
        for j in 0..=k.min(n) {
            let b_j = if j == 0 { 1.0 } else { b[j - 1] };
            a_k += b_j * c((k - j) as i64);
        }
        num.push(a_k);
    }

    Some((num, den))
}

/// Solve Ax = b via Gaussian elimination with partial pivoting.
fn solve_linear(n: usize, mat: &mut [f64], rhs: &mut [f64]) -> Option<Vec<f64>> {
    for col in 0..n {
        // Partial pivoting
        let mut max_val = mat[col * n + col].abs();
        let mut max_row = col;
        for row in (col + 1)..n {
            let v = mat[row * n + col].abs();
            if v > max_val { max_val = v; max_row = row; }
        }
        if max_val < 1e-14 { return None; }

        if max_row != col {
            for j in 0..n {
                mat.swap(col * n + j, max_row * n + j);
            }
            rhs.swap(col, max_row);
        }

        let pivot = mat[col * n + col];
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

    // Back substitution
    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        let mut sum = rhs[i];
        for j in (i + 1)..n {
            sum -= mat[i * n + j] * x[j];
        }
        x[i] = sum / mat[i * n + i];
    }
    Some(x)
}

/// Evaluate Pade approximant at normalized points and compute L2 error.
fn evaluate_pade_error(data: &[f64], num: &[f64], den: &[f64]) -> f64 {
    let n = data.len();
    if n == 0 { return 0.0; }

    let mut err_sq = 0.0;
    for i in 0..n {
        let x = i as f64 / (n - 1).max(1) as f64;
        let mut numer = 0.0;
        let mut xk = 1.0;
        for &c in num {
            numer += c * xk;
            xk *= x;
        }
        let mut denom = 0.0;
        xk = 1.0;
        for &c in den {
            denom += c * xk;
            xk *= x;
        }
        if denom.abs() > 1e-12 {
            let approx = numer / denom;
            let diff = data[i] - approx;
            err_sq += diff * diff;
        } else {
            err_sq += data[i] * data[i]; // pole hit
        }
    }
    (err_sq / n as f64).sqrt()
}

/// Find real roots of polynomial (denominator) using companion matrix eigenvalues
/// approximated by bisection on a grid.
fn find_real_poles(den: &[f64]) -> Vec<f64> {
    if den.len() <= 1 { return Vec::new(); }

    let eval_poly = |x: f64| -> f64 {
        let mut val = 0.0;
        let mut xk = 1.0;
        for &c in den {
            val += c * xk;
            xk *= x;
        }
        val
    };

    let mut poles = Vec::new();
    let steps = 1000;
    let lo = -10.0;
    let hi = 10.0;
    let dx = (hi - lo) / steps as f64;

    let mut prev = eval_poly(lo);
    for i in 1..=steps {
        let x = lo + i as f64 * dx;
        let cur = eval_poly(x);
        if prev.is_finite() && cur.is_finite() && prev * cur < 0.0 {
            // Bisect
            let mut a = x - dx;
            let mut b = x;
            for _ in 0..50 {
                let mid = (a + b) / 2.0;
                if eval_poly(a) * eval_poly(mid) <= 0.0 { b = mid; } else { a = mid; }
            }
            poles.push((a + b) / 2.0);
        }
        prev = cur;
    }

    poles
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pade_lens_basic() {
        let n = 32;
        let d = 2;
        let data: Vec<f64> = (0..n * d)
            .map(|i| ((i as f64) * 0.1).sin() + 0.5)
            .collect();
        let shared = SharedData::compute(&data, n, d);
        let result = PadeApproximantLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("pade_best_error"));
        assert!(result.contains_key("pade_best_m"));
    }
}
