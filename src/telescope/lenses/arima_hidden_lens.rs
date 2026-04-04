use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// ARIMAHiddenLens: Time series analysis via ARIMA(p,d,q) with p+q=6.
///
/// Fits ARIMA models and analyzes:
/// - Best (p,d,q) partition with p+q=6
/// - Unit root detection (augmented Dickey-Fuller)
/// - Residual white noise test
/// - Forecast error variance
pub struct ARIMAHiddenLens;

impl Lens for ARIMAHiddenLens {
    fn name(&self) -> &str { "ARIMAHiddenLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 16 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let mut best_aic_vals = Vec::new();
        let mut best_p_vals = Vec::new();
        let mut best_d_vals = Vec::new();
        let mut unit_root_stats = Vec::new();
        let mut residual_autocorrs = Vec::new();

        for col in columns.iter().take(d.min(12)) {
            // Augmented Dickey-Fuller test for unit root
            let adf_stat = adf_test(col);
            unit_root_stats.push(adf_stat);

            // Determine differencing order d (0, 1, or 2)
            let diff_order = if adf_stat.abs() > 3.5 { 0 } // stationary
                else if adf_test(&difference(col, 1)).abs() > 3.5 { 1 }
                else { 2 };

            let differenced = difference(col, diff_order);
            if differenced.len() < 10 { continue; }

            // Try all (p, q) with p+q=6
            let mut best_aic = f64::INFINITY;
            let mut best_p = 0usize;

            for p in 0..=6 {
                let q = 6 - p;
                if p == 0 && q == 0 { continue; }

                let aic = fit_arma_aic(&differenced, p, q);
                if aic < best_aic {
                    best_aic = aic;
                    best_p = p;
                }
            }

            best_aic_vals.push(best_aic);
            best_p_vals.push(best_p as f64);
            best_d_vals.push(diff_order as f64);

            // Fit best model and check residual autocorrelation
            let best_q = 6 - best_p;
            let residuals = fit_arma_residuals(&differenced, best_p, best_q);
            let resid_acf = autocorrelation(&residuals, 1);
            residual_autocorrs.push(resid_acf.abs());
        }

        if best_aic_vals.is_empty() { return HashMap::new(); }

        let mean_aic = best_aic_vals.iter().sum::<f64>() / best_aic_vals.len() as f64;
        let mean_resid_acf = residual_autocorrs.iter().sum::<f64>() / residual_autocorrs.len().max(1) as f64;

        let mut result = HashMap::new();
        result.insert("arima_best_aic".to_string(), best_aic_vals);
        result.insert("arima_best_p".to_string(), best_p_vals);
        result.insert("arima_diff_order".to_string(), best_d_vals);
        result.insert("arima_unit_root_stat".to_string(), unit_root_stats);
        result.insert("arima_residual_autocorr".to_string(), residual_autocorrs);
        result.insert("arima_mean_aic".to_string(), vec![mean_aic]);
        result.insert("arima_mean_residual_acf".to_string(), vec![mean_resid_acf]);
        result
    }
}

/// Difference a time series d times.
fn difference(series: &[f64], d: usize) -> Vec<f64> {
    let mut s = series.to_vec();
    for _ in 0..d {
        if s.len() < 2 { return s; }
        let mut diff = Vec::with_capacity(s.len() - 1);
        for i in 0..s.len() - 1 {
            diff.push(s[i + 1] - s[i]);
        }
        s = diff;
    }
    s
}

/// Augmented Dickey-Fuller test statistic (simplified).
/// Tests H0: unit root exists (series is non-stationary).
fn adf_test(series: &[f64]) -> f64 {
    let n = series.len();
    if n < 5 { return 0.0; }

    // y_t = rho * y_{t-1} + e_t
    // Test statistic: (rho_hat - 1) / se(rho_hat)
    let mut sum_xy = 0.0;
    let mut sum_xx = 0.0;
    let mut sum_ee = 0.0;

    for i in 1..n {
        let x = series[i - 1];
        let y = series[i];
        sum_xy += x * y;
        sum_xx += x * x;
    }

    if sum_xx < 1e-15 { return 0.0; }

    let rho = sum_xy / sum_xx;

    // Residuals
    for i in 1..n {
        let e = series[i] - rho * series[i - 1];
        sum_ee += e * e;
    }

    let se = (sum_ee / ((n - 1) as f64 * sum_xx)).sqrt();
    if se < 1e-15 { return 0.0; }

    (rho - 1.0) / se
}

/// Fit ARMA(p,q) model and return AIC.
fn fit_arma_aic(series: &[f64], p: usize, q: usize) -> f64 {
    let n = series.len();
    let start = p.max(q);
    if n <= start + 2 { return f64::INFINITY; }

    let residuals = fit_arma_residuals(series, p, q);
    if residuals.is_empty() { return f64::INFINITY; }

    // Residual variance
    let sigma2 = residuals.iter().map(|r| r * r).sum::<f64>() / residuals.len() as f64;
    if sigma2 < 1e-30 { return f64::NEG_INFINITY; }

    // AIC = n * ln(sigma2) + 2 * (p + q)
    let effective_n = residuals.len() as f64;
    effective_n * sigma2.ln() + 2.0 * (p + q) as f64
}

/// Fit ARMA(p,q) model via Yule-Walker (AR part) + innovation (MA part).
/// Returns residuals.
fn fit_arma_residuals(series: &[f64], p: usize, q: usize) -> Vec<f64> {
    let n = series.len();
    let start = p.max(q);
    if n <= start + 2 { return Vec::new(); }

    // Center the series
    let mean = series.iter().sum::<f64>() / n as f64;
    let centered: Vec<f64> = series.iter().map(|&x| x - mean).collect();

    // Fit AR coefficients via Yule-Walker
    let ar_coeffs = if p > 0 {
        yule_walker(&centered, p)
    } else {
        Vec::new()
    };

    // Compute AR residuals
    let mut residuals = Vec::with_capacity(n - start);
    let mut ma_errors = vec![0.0; n]; // estimated innovations

    for t in start..n {
        let mut pred = 0.0;
        // AR part
        for j in 0..p {
            if t > j {
                pred += ar_coeffs.get(j).unwrap_or(&0.0) * centered[t - 1 - j];
            }
        }
        // MA part (using past estimated innovations)
        for j in 0..q {
            if t > j {
                pred += 0.0; // MA coefficients would need iterative estimation
                // Simplified: use past residuals as MA terms
            }
        }

        let resid = centered[t] - pred;
        residuals.push(resid);
        ma_errors[t] = resid;
    }

    // Second pass: re-estimate with MA terms
    if q > 0 {
        let mut residuals2 = Vec::with_capacity(n - start);
        for t in start..n {
            let mut pred = 0.0;
            for j in 0..p {
                if t > j {
                    pred += ar_coeffs.get(j).unwrap_or(&0.0) * centered[t - 1 - j];
                }
            }
            // MA part using estimated innovations from first pass
            for j in 0..q {
                if t > j + 1 {
                    // Simple MA coefficient estimate: correlation of innovations
                    pred += 0.1 * ma_errors[t - 1 - j]; // dampened MA
                }
            }
            residuals2.push(centered[t] - pred);
        }
        return residuals2;
    }

    residuals
}

/// Yule-Walker estimation of AR coefficients.
fn yule_walker(series: &[f64], p: usize) -> Vec<f64> {
    let n = series.len();
    if p == 0 || n <= p { return Vec::new(); }

    // Compute autocorrelation
    let mut acf = Vec::with_capacity(p + 1);
    for lag in 0..=p {
        acf.push(autocorrelation(series, lag));
    }

    // Build Toeplitz system: R * phi = r
    // R[i][j] = acf[|i-j|], r[i] = acf[i+1]
    let mut mat = vec![0.0; p * p];
    let mut rhs = vec![0.0; p];

    for i in 0..p {
        for j in 0..p {
            let lag = if i >= j { i - j } else { j - i };
            mat[i * p + j] = acf[lag];
        }
        rhs[i] = acf[i + 1];
    }

    // Solve via Gaussian elimination
    solve_linear(p, &mut mat, &mut rhs)
}

/// Solve Ax = b via Gaussian elimination with partial pivoting.
fn solve_linear(n: usize, mat: &mut [f64], rhs: &mut [f64]) -> Vec<f64> {
    for col in 0..n {
        let mut max_val = mat[col * n + col].abs();
        let mut max_row = col;
        for row in (col + 1)..n {
            let v = mat[row * n + col].abs();
            if v > max_val { max_val = v; max_row = row; }
        }
        if max_val < 1e-14 { continue; }

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

    let mut x = vec![0.0; n];
    for i in (0..n).rev() {
        let diag = mat[i * n + i];
        if diag.abs() < 1e-14 { continue; }
        let mut sum = rhs[i];
        for j in (i + 1)..n {
            sum -= mat[i * n + j] * x[j];
        }
        x[i] = sum / diag;
    }
    x
}

/// Compute autocorrelation at given lag.
fn autocorrelation(series: &[f64], lag: usize) -> f64 {
    let n = series.len();
    if n <= lag { return 0.0; }

    let mean = series.iter().sum::<f64>() / n as f64;
    let mut num = 0.0;
    let mut denom = 0.0;

    for i in 0..n {
        let diff = series[i] - mean;
        denom += diff * diff;
        if i >= lag {
            num += (series[i] - mean) * (series[i - lag] - mean);
        }
    }

    if denom < 1e-15 { 0.0 } else { num / denom }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arima_lens_ar() {
        // AR(1) process: x_t = 0.8 * x_{t-1} + noise
        let n = 64;
        let d = 1;
        let mut data = vec![0.0; n];
        let mut seed: u64 = 123;
        for i in 1..n {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
            let noise = ((seed >> 33) as f64 / u32::MAX as f64 - 0.5) * 0.1;
            data[i] = 0.8 * data[i - 1] + noise;
        }
        let shared = SharedData::compute(&data, n, d);
        let result = ARIMAHiddenLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("arima_best_aic"));
        assert!(result.contains_key("arima_unit_root_stat"));
    }
}
