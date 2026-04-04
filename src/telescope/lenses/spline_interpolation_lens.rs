use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// SplineInterpolationLens: Cubic spline interpolation with C^6 smoothness analysis.
///
/// Fits natural cubic splines and measures:
/// - Smoothness up to 6th derivative continuity
/// - Knot multiplicity patterns
/// - Curvature variation (second derivative energy)
pub struct SplineInterpolationLens;

impl Lens for SplineInterpolationLens {
    fn name(&self) -> &str { "SplineInterpolationLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 8 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        let mut smoothness_scores = Vec::new();
        let mut curvature_energies = Vec::new();
        let mut knot_uniformities = Vec::new();
        let mut interp_errors = Vec::new();

        for col in columns.iter().take(d.min(12)) {
            // Build natural cubic spline
            let knots: Vec<f64> = (0..col.len())
                .map(|i| i as f64 / (col.len() - 1).max(1) as f64)
                .collect();
            let spline = CubicSpline::natural(&knots, col);

            // Smoothness score: measure derivative continuity up to 6th order
            // by computing finite difference approximations at interior knots
            let smoothness = measure_smoothness(&spline, &knots, 6);
            smoothness_scores.push(smoothness);

            // Curvature energy: integral of second derivative squared
            let curv_energy = spline.curvature_energy();
            curvature_energies.push(curv_energy);

            // Knot uniformity: ratio of min/max knot spacing
            let uniformity = knot_uniformity(&knots);
            knot_uniformities.push(uniformity);

            // Leave-one-out cross-validation error
            let cv_err = leave_one_out_cv(col);
            interp_errors.push(cv_err);
        }

        if smoothness_scores.is_empty() { return HashMap::new(); }

        let mean_smoothness = smoothness_scores.iter().sum::<f64>() / smoothness_scores.len() as f64;
        let mean_curvature = curvature_energies.iter().sum::<f64>() / curvature_energies.len() as f64;

        let mut result = HashMap::new();
        result.insert("spline_smoothness".to_string(), smoothness_scores);
        result.insert("spline_curvature_energy".to_string(), curvature_energies);
        result.insert("spline_knot_uniformity".to_string(), knot_uniformities);
        result.insert("spline_cv_error".to_string(), interp_errors);
        result.insert("spline_mean_smoothness".to_string(), vec![mean_smoothness]);
        result.insert("spline_mean_curvature".to_string(), vec![mean_curvature]);
        result
    }
}

/// Natural cubic spline representation.
struct CubicSpline {
    /// Knot positions
    knots: Vec<f64>,
    /// Coefficients for each segment: a + b(x-x_i) + c(x-x_i)^2 + d(x-x_i)^3
    a: Vec<f64>,
    b: Vec<f64>,
    c: Vec<f64>,
    d: Vec<f64>,
}

impl CubicSpline {
    /// Construct a natural cubic spline (second derivative = 0 at endpoints).
    fn natural(knots: &[f64], values: &[f64]) -> Self {
        let n = knots.len();
        if n < 2 {
            return Self {
                knots: knots.to_vec(),
                a: values.to_vec(),
                b: vec![0.0],
                c: vec![0.0],
                d: vec![0.0],
            };
        }

        let a: Vec<f64> = values.to_vec();
        let mut h = Vec::with_capacity(n - 1);
        for i in 0..n - 1 {
            h.push(knots[i + 1] - knots[i]);
        }

        // Solve tridiagonal system for c coefficients
        let m = n - 2; // interior points
        if m == 0 {
            let b0 = if h[0].abs() > 1e-15 { (a[1] - a[0]) / h[0] } else { 0.0 };
            return Self {
                knots: knots.to_vec(),
                a,
                b: vec![b0],
                c: vec![0.0; n],
                d: vec![0.0],
            };
        }

        // Build tridiagonal system
        let mut alpha = vec![0.0; m];
        for i in 0..m {
            let ii = i + 1;
            alpha[i] = 3.0 / h[ii] * (a[ii + 1] - a[ii]) - 3.0 / h[ii - 1] * (a[ii] - a[ii - 1]);
        }

        // Thomas algorithm
        let mut l = vec![1.0; m];
        let mut mu = vec![0.0; m];
        let mut z = vec![0.0; m];

        l[0] = 2.0 * (h[0] + h[1]);
        mu[0] = h[1] / l[0];
        z[0] = alpha[0] / l[0];

        for i in 1..m {
            let ii = i + 1;
            l[i] = 2.0 * (h[ii - 1] + h[ii.min(n - 2)]) - h[ii - 1] * mu[i - 1];
            if l[i].abs() < 1e-15 { l[i] = 1e-15; }
            mu[i] = if ii < n - 1 { h[ii] / l[i] } else { 0.0 };
            z[i] = (alpha[i] - h[ii - 1] * z[i - 1]) / l[i];
        }

        let mut c_all = vec![0.0; n]; // natural: c[0] = c[n-1] = 0
        for j in (0..m).rev() {
            c_all[j + 1] = z[j] - mu[j] * c_all[j + 2];
        }

        let mut b_vec = Vec::with_capacity(n - 1);
        let mut d_vec = Vec::with_capacity(n - 1);
        for i in 0..n - 1 {
            if h[i].abs() < 1e-15 {
                b_vec.push(0.0);
                d_vec.push(0.0);
            } else {
                d_vec.push((c_all[i + 1] - c_all[i]) / (3.0 * h[i]));
                b_vec.push((a[i + 1] - a[i]) / h[i] - h[i] * (2.0 * c_all[i] + c_all[i + 1]) / 3.0);
            }
        }

        Self {
            knots: knots.to_vec(),
            a,
            b: b_vec,
            c: c_all,
            d: d_vec,
        }
    }

    /// Evaluate the spline at x.
    fn eval(&self, x: f64) -> f64 {
        let n = self.knots.len();
        if n < 2 { return if self.a.is_empty() { 0.0 } else { self.a[0] }; }

        // Find segment
        let mut i = 0;
        for k in 0..n - 1 {
            if x >= self.knots[k] { i = k; }
        }
        i = i.min(self.b.len() - 1);

        let dx = x - self.knots[i];
        self.a[i] + self.b[i] * dx + self.c[i] * dx * dx + self.d[i] * dx * dx * dx
    }

    /// Compute integral of (second derivative)^2 -- curvature energy.
    fn curvature_energy(&self) -> f64 {
        let n = self.knots.len();
        if n < 2 { return 0.0; }

        let mut energy = 0.0;
        for i in 0..n - 1 {
            let h = self.knots[i + 1] - self.knots[i];
            if h.abs() < 1e-15 { continue; }
            // Second derivative: 2c_i + 6d_i*(x - x_i)
            // Integral of (2c + 6d*t)^2 dt from 0 to h
            let ci = self.c[i];
            let di = self.d[i];
            energy += 4.0 * ci * ci * h + 24.0 * ci * di * h * h / 2.0 + 36.0 * di * di * h * h * h / 3.0;
        }
        energy
    }
}

/// Measure derivative continuity up to order k at knots.
/// Returns a score 0..1 where 1 = perfectly smooth.
fn measure_smoothness(spline: &CubicSpline, knots: &[f64], max_order: usize) -> f64 {
    let n = knots.len();
    if n < 3 { return 1.0; }

    let eps = 1e-6;
    let mut total_score = 0.0;
    let mut count = 0;

    for order in 1..=max_order {
        for i in 1..n - 1 {
            let x = knots[i];
            // Finite difference approximation of derivative from left and right
            let left = finite_diff_deriv(spline, x - eps, order, eps);
            let right = finite_diff_deriv(spline, x + eps, order, eps);

            let scale = left.abs().max(right.abs()).max(1e-10);
            let continuity = 1.0 - ((left - right).abs() / scale).min(1.0);
            total_score += continuity;
            count += 1;
        }
    }

    if count == 0 { 1.0 } else { total_score / count as f64 }
}

/// Approximate k-th derivative via centered finite differences.
fn finite_diff_deriv(spline: &CubicSpline, x: f64, order: usize, h: f64) -> f64 {
    if order == 0 { return spline.eval(x); }
    let half = h;
    let left = finite_diff_deriv(spline, x - half, order - 1, h);
    let right = finite_diff_deriv(spline, x + half, order - 1, h);
    (right - left) / (2.0 * half)
}

/// Measure knot spacing uniformity (1.0 = perfectly uniform).
fn knot_uniformity(knots: &[f64]) -> f64 {
    if knots.len() < 2 { return 1.0; }
    let mut min_h = f64::INFINITY;
    let mut max_h = 0.0f64;
    for i in 0..knots.len() - 1 {
        let h = (knots[i + 1] - knots[i]).abs();
        if h > 1e-15 {
            min_h = min_h.min(h);
            max_h = max_h.max(h);
        }
    }
    if max_h < 1e-15 { 1.0 } else { min_h / max_h }
}

/// Leave-one-out cross-validation error for cubic spline.
fn leave_one_out_cv(data: &[f64]) -> f64 {
    let n = data.len();
    if n < 4 { return 0.0; }

    // Sample a few points to keep cost manageable
    let step = (n / 8).max(1);
    let mut err_sq = 0.0;
    let mut count = 0;

    for skip in (1..n - 1).step_by(step) {
        let mut knots = Vec::with_capacity(n - 1);
        let mut vals = Vec::with_capacity(n - 1);
        for i in 0..n {
            if i == skip { continue; }
            knots.push(i as f64 / (n - 1).max(1) as f64);
            vals.push(data[i]);
        }
        let spline = CubicSpline::natural(&knots, &vals);
        let x = skip as f64 / (n - 1).max(1) as f64;
        let pred = spline.eval(x);
        err_sq += (data[skip] - pred).powi(2);
        count += 1;
    }

    if count == 0 { 0.0 } else { (err_sq / count as f64).sqrt() }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_spline_lens_smooth() {
        let n = 32;
        let d = 1;
        let data: Vec<f64> = (0..n)
            .map(|i| {
                let t = i as f64 / (n - 1) as f64;
                (2.0 * std::f64::consts::PI * t).sin()
            })
            .collect();
        let shared = SharedData::compute(&data, n, d);
        let result = SplineInterpolationLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("spline_smoothness"));
        assert!(result["spline_mean_smoothness"][0] > 0.5);
    }
}
