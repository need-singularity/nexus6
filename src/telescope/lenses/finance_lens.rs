use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// n=6 constants relevant to finance
const SIGMA: f64 = 12.0;   // σ(6) months in year
const TAU: f64 = 4.0;      // τ(6) quarters
const PHI: f64 = 2.0;      // φ(6) binary splits
const N: f64 = 6.0;
const SOPFR: f64 = 5.0;    // trading days per week
const SIGMA_MINUS_PHI: f64 = 10.0; // decade cycle

/// FinanceLens: Detect financial time-series patterns in data.
///
/// Metrics: volatility, mean_reversion, momentum, fat_tail_index,
///          sharpe_ratio, n6_finance_score
pub struct FinanceLens;

impl Lens for FinanceLens {
    fn name(&self) -> &str { "FinanceLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. Volatility: average coefficient of variation across features
        let mut volatility = 0.0;
        for col in 0..d {
            let mean_abs = means[col].abs().max(1e-12);
            volatility += vars[col].sqrt() / mean_abs;
        }
        volatility /= d as f64;

        // 2. Mean reversion: autocorrelation of returns (negative = reverting)
        let mut mean_reversion = 0.0;
        let mut mr_count = 0;
        for col_data in &columns {
            if col_data.len() < 4 { continue; }
            let returns: Vec<f64> = col_data.windows(2).map(|w| w[1] - w[0]).collect();
            let r_mean = returns.iter().sum::<f64>() / returns.len() as f64;
            let r_var = returns.iter().map(|r| (r - r_mean).powi(2)).sum::<f64>() / returns.len() as f64;
            if r_var < 1e-12 { continue; }
            let mut autocorr = 0.0;
            for i in 0..(returns.len() - 1) {
                autocorr += (returns[i] - r_mean) * (returns[i + 1] - r_mean);
            }
            autocorr /= (returns.len() - 1) as f64 * r_var;
            mean_reversion += -autocorr; // positive = mean-reverting
            mr_count += 1;
        }
        if mr_count > 0 { mean_reversion /= mr_count as f64; }

        // 3. Momentum: positive serial correlation in absolute returns
        let mut momentum = 0.0;
        let mut mom_count = 0;
        for col_data in &columns {
            if col_data.len() < 4 { continue; }
            let abs_ret: Vec<f64> = col_data.windows(2).map(|w| (w[1] - w[0]).abs()).collect();
            let ar_mean = abs_ret.iter().sum::<f64>() / abs_ret.len() as f64;
            if ar_mean < 1e-12 { continue; }
            let mut serial = 0.0;
            for i in 0..(abs_ret.len() - 1) {
                serial += abs_ret[i] * abs_ret[i + 1];
            }
            serial /= (abs_ret.len() - 1) as f64 * ar_mean.powi(2);
            momentum += serial.min(3.0) / 3.0;
            mom_count += 1;
        }
        if mom_count > 0 { momentum /= mom_count as f64; }

        // 4. Fat tail index: kurtosis excess (>0 = fat tails)
        let mut kurtosis_sum = 0.0;
        for col in 0..d {
            let m = means[col];
            let v = vars[col].max(1e-15);
            let k4: f64 = columns[col].iter()
                .map(|&x| ((x - m) / v.sqrt()).powi(4))
                .sum::<f64>() / n as f64;
            kurtosis_sum += (k4 - 3.0).max(0.0); // excess kurtosis
        }
        let fat_tail_index = kurtosis_sum / d as f64;

        // 5. Sharpe-like ratio: mean return / volatility
        let mut sharpe = 0.0;
        for col_data in &columns {
            if col_data.len() < 2 { continue; }
            let ret: Vec<f64> = col_data.windows(2).map(|w| w[1] - w[0]).collect();
            let r_mean = ret.iter().sum::<f64>() / ret.len() as f64;
            let r_std = (ret.iter().map(|r| (r - r_mean).powi(2)).sum::<f64>() / ret.len() as f64).sqrt();
            if r_std > 1e-12 { sharpe += r_mean / r_std; }
        }
        sharpe /= d as f64;

        // 6. n=6 finance score
        let n6_score = 0.2 * volatility.min(1.0) + 0.2 * mean_reversion.abs().min(1.0)
            + 0.2 * momentum.min(1.0) + 0.2 * (fat_tail_index / 10.0).min(1.0)
            + 0.2 * sharpe.abs().min(1.0);

        let mut result = HashMap::new();
        result.insert("volatility".into(), vec![volatility]);
        result.insert("mean_reversion".into(), vec![mean_reversion]);
        result.insert("momentum".into(), vec![momentum]);
        result.insert("fat_tail_index".into(), vec![fat_tail_index]);
        result.insert("sharpe_ratio".into(), vec![sharpe]);
        result.insert("n6_finance_score".into(), vec![n6_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_finance_basic() {
        // Simulate price-like data with trend + noise
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.1;
            100.0 + t * 2.0 + (t * 3.0).sin() * 5.0
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = FinanceLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("volatility"));
        assert!(result.contains_key("sharpe_ratio"));
        assert!(result.contains_key("n6_finance_score"));
    }
}
