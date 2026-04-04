use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// ErgodicityBreakingLens: Dynamical systems analysis in 6-dim phase space.
///
/// Detects ergodicity breaking by analyzing:
/// - Time average vs ensemble average discrepancy
/// - Correlation decay rate (mixing time)
/// - Recurrence time statistics
/// - Phase space partitioning (6-dim)
pub struct ErgodicityBreakingLens;

impl Lens for ErgodicityBreakingLens {
    fn name(&self) -> &str { "ErgodicityBreakingLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 16 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let dim = d.min(6);

        // Time average vs ensemble average for each feature
        let mut ergodic_gaps = Vec::new();
        let mut correlation_decays = Vec::new();
        let mut recurrence_times = Vec::new();

        for col in columns.iter().take(dim) {
            // Ergodicity gap: difference between cumulative time average
            // and ensemble (overall) average
            let gap = ergodicity_gap(col);
            ergodic_gaps.push(gap);

            // Correlation decay: exponential fit to autocorrelation function
            let decay = correlation_decay_rate(col);
            correlation_decays.push(decay);

            // Mean recurrence time to initial region
            let recurrence = mean_recurrence_time(col);
            recurrence_times.push(recurrence);
        }

        // Phase space analysis (multi-dimensional)
        let phase_partition = phase_space_entropy(data, n, d, dim);

        // Birkhoff average convergence rate
        let birkhoff_rate = birkhoff_convergence(data, n, d, dim);

        // Weak ergodicity breaking parameter (WEB)
        let web_param = weak_ergodicity_breaking(data, n, d, dim);

        let mean_gap = ergodic_gaps.iter().sum::<f64>() / ergodic_gaps.len().max(1) as f64;
        let mean_decay = correlation_decays.iter().sum::<f64>() / correlation_decays.len().max(1) as f64;

        let mut result = HashMap::new();
        result.insert("ergodic_gap".to_string(), ergodic_gaps);
        result.insert("ergodic_correlation_decay".to_string(), correlation_decays);
        result.insert("ergodic_recurrence_time".to_string(), recurrence_times);
        result.insert("ergodic_phase_entropy".to_string(), vec![phase_partition]);
        result.insert("ergodic_birkhoff_rate".to_string(), vec![birkhoff_rate]);
        result.insert("ergodic_web_param".to_string(), vec![web_param]);
        result.insert("ergodic_mean_gap".to_string(), vec![mean_gap]);
        result.insert("ergodic_mean_decay".to_string(), vec![mean_decay]);
        result.insert("score".to_string(), vec![result["ergodic_gap"][0].min(1.0).max(0.0)]);
        result
    }
}

/// Ergodicity gap: max |time_avg(t) - ensemble_avg| over time.
fn ergodicity_gap(col: &[f64]) -> f64 {
    let n = col.len();
    if n == 0 { return 0.0; }

    let ensemble_avg = col.iter().sum::<f64>() / n as f64;
    let ensemble_var = col.iter().map(|x| (x - ensemble_avg).powi(2)).sum::<f64>() / n as f64;
    let scale = ensemble_var.sqrt().max(1e-10);

    let mut running_sum = 0.0;
    let mut max_gap: f64 = 0.0;

    for (i, &x) in col.iter().enumerate() {
        running_sum += x;
        let time_avg = running_sum / (i + 1) as f64;
        let gap = (time_avg - ensemble_avg).abs() / scale;
        max_gap = max_gap.max(gap);
    }

    max_gap
}

/// Estimate correlation decay rate by fitting exponential to ACF.
fn correlation_decay_rate(col: &[f64]) -> f64 {
    let n = col.len();
    if n < 8 { return 0.0; }

    let mean = col.iter().sum::<f64>() / n as f64;
    let var: f64 = col.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n as f64;
    if var < 1e-15 { return 0.0; }

    let max_lag = (n / 4).min(20);
    let mut log_acf = Vec::new();
    let mut lags = Vec::new();

    for lag in 1..=max_lag {
        let mut acf = 0.0;
        for i in lag..n {
            acf += (col[i] - mean) * (col[i - lag] - mean);
        }
        acf /= (n - lag) as f64 * var;

        if acf > 0.01 { // Only positive ACF values for log fit
            log_acf.push(acf.ln());
            lags.push(lag as f64);
        }
    }

    if log_acf.len() < 2 { return 0.0; }

    // Linear regression: log(ACF) ~ -lambda * lag
    let n_pts = log_acf.len() as f64;
    let mean_lag = lags.iter().sum::<f64>() / n_pts;
    let mean_log = log_acf.iter().sum::<f64>() / n_pts;

    let mut num = 0.0;
    let mut den = 0.0;
    for i in 0..log_acf.len() {
        num += (lags[i] - mean_lag) * (log_acf[i] - mean_log);
        den += (lags[i] - mean_lag).powi(2);
    }

    if den < 1e-15 { 0.0 } else { -(num / den) } // positive decay rate
}

/// Mean recurrence time: average time to return to neighborhood of initial value.
fn mean_recurrence_time(col: &[f64]) -> f64 {
    let n = col.len();
    if n < 4 { return 0.0; }

    let initial = col[0];
    let range = col.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
        - col.iter().cloned().fold(f64::INFINITY, f64::min);
    let epsilon = range * 0.1; // 10% neighborhood

    let mut total_recurrence = 0.0;
    let mut recurrence_count = 0;
    let mut last_visit = 0;

    for i in 1..n {
        if (col[i] - initial).abs() < epsilon {
            total_recurrence += (i - last_visit) as f64;
            recurrence_count += 1;
            last_visit = i;
        }
    }

    if recurrence_count == 0 { n as f64 } // never returned
    else { total_recurrence / recurrence_count as f64 }
}

/// Phase space entropy: discretize 6-dim space and measure distribution entropy.
fn phase_space_entropy(data: &[f64], n: usize, d: usize, dim: usize) -> f64 {
    let bins_per_dim: usize = 6; // n=6 bins per dimension
    let total_bins = (bins_per_dim as u32).pow(dim.min(3) as u32) as usize; // limit to 3D to keep tractable

    // Find min/max per dimension
    let eff_dim = dim.min(3);
    let mut mins = vec![f64::INFINITY; eff_dim];
    let mut maxs = vec![f64::NEG_INFINITY; eff_dim];

    for i in 0..n {
        for j in 0..eff_dim {
            let v = data[i * d + j];
            mins[j] = mins[j].min(v);
            maxs[j] = maxs[j].max(v);
        }
    }

    // Count bin occupancies
    let mut counts = vec![0usize; total_bins];

    for i in 0..n {
        let mut bin_idx = 0;
        let mut multiplier = 1;
        for j in 0..eff_dim {
            let range = maxs[j] - mins[j];
            let bin = if range < 1e-15 { 0 } else {
                let b = ((data[i * d + j] - mins[j]) / range * bins_per_dim as f64) as usize;
                b.min(bins_per_dim - 1)
            };
            bin_idx += bin * multiplier;
            multiplier *= bins_per_dim;
        }
        if bin_idx < total_bins {
            counts[bin_idx] += 1;
        }
    }

    // Shannon entropy
    let mut entropy = 0.0;
    for &c in &counts {
        if c > 0 {
            let p = c as f64 / n as f64;
            entropy -= p * p.ln();
        }
    }

    // Normalize by max entropy
    let max_entropy = (total_bins as f64).ln();
    if max_entropy > 0.0 { entropy / max_entropy } else { 0.0 }
}

/// Birkhoff average convergence rate: how fast time averages converge.
fn birkhoff_convergence(data: &[f64], n: usize, d: usize, _dim: usize) -> f64 {
    if n < 8 { return 0.0; }

    // Use first feature as observable
    let col: Vec<f64> = (0..n).map(|i| data[i * d]).collect();
    let overall_avg = col.iter().sum::<f64>() / n as f64;

    // Measure convergence: ||time_avg(T) - ensemble_avg|| vs T
    let checkpoints = [n / 4, n / 2, 3 * n / 4, n];
    let mut errors = Vec::new();
    let mut running = 0.0;

    for (i, &x) in col.iter().enumerate() {
        running += x;
        let t = i + 1;
        if checkpoints.contains(&t) {
            let time_avg = running / t as f64;
            errors.push((time_avg - overall_avg).abs());
        }
    }

    if errors.len() < 2 { return 0.0; }

    // Rate: fit power law error ~ T^{-alpha}
    // Compare first and last error
    let ratio = if errors.last().unwrap().abs() > 1e-15 {
        errors[0] / errors.last().unwrap()
    } else {
        1.0
    };

    // For ergodic systems, alpha ~ 0.5 (CLT)
    if ratio > 1.0 {
        ratio.ln() / (*checkpoints.last().unwrap_or(&1usize) as f64 / checkpoints[0] as f64).ln()
    } else {
        0.0
    }
}

/// Weak ergodicity breaking parameter.
/// Measures dispersion of time-averaged observables across different time windows.
fn weak_ergodicity_breaking(data: &[f64], n: usize, d: usize, _dim: usize) -> f64 {
    if n < 16 { return 0.0; }

    let num_windows = 6; // n=6 windows
    let window_size = n / num_windows;
    if window_size < 2 { return 0.0; }

    // Compute time average in each window for first feature
    let mut window_avgs = Vec::with_capacity(num_windows);
    for w in 0..num_windows {
        let start = w * window_size;
        let end = ((w + 1) * window_size).min(n);
        let mut sum = 0.0;
        for i in start..end {
            sum += data[i * d]; // first feature
        }
        window_avgs.push(sum / (end - start) as f64);
    }

    // WEB parameter: variance of window averages / expected variance for ergodic system
    let mean_avg = window_avgs.iter().sum::<f64>() / num_windows as f64;
    let var_avg = window_avgs.iter().map(|a| (a - mean_avg).powi(2)).sum::<f64>()
        / num_windows as f64;

    // For ergodic system, variance of window averages ~ sigma^2 / window_size
    let overall_var = {
        let col: Vec<f64> = (0..n).map(|i| data[i * d]).collect();
        let mean = col.iter().sum::<f64>() / n as f64;
        col.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n as f64
    };

    let expected_var = overall_var / window_size as f64;
    if expected_var < 1e-15 { 0.0 } else { var_avg / expected_var }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ergodicity_breaking_lens() {
        let n = 64;
        let d = 2;
        // Ergodic: uniformly distributed
        let mut data = Vec::with_capacity(n * d);
        let mut seed: u64 = 42;
        for _ in 0..n {
            for _ in 0..d {
                seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1);
                data.push((seed >> 33) as f64 / u32::MAX as f64);
            }
        }
        let shared = SharedData::compute(&data, n, d);
        let result = ErgodicityBreakingLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("ergodic_gap"));
        assert!(result.contains_key("ergodic_web_param"));
    }
}
