use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// KTheoryLens: Detect K-theoretic patterns — Bott periodicity, Chern classes,
/// vector bundle structure in data.
///
/// n=6 connection: Bott periodicity mod 2 (complex) and mod 8 (real),
/// 6 = 2·3 bridges both periodicities. Chern character in dim 6.
pub struct KTheoryLens;

impl Lens for KTheoryLens {
    fn name(&self) -> &str {
        "KTheoryLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);

        // 1. Bott periodicity detection: check for period-2 and period-8 patterns
        //    in the spectral structure of data
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // Period-2 autocorrelation (complex K-theory)
        let period2 = periodic_correlation(&vals, 2);
        result.insert("bott_period_2".to_string(), vec![period2]);

        // Period-8 autocorrelation (real K-theory)
        let period8 = periodic_correlation(&vals, 8);
        result.insert("bott_period_8".to_string(), vec![period8]);

        // Period-6 = lcm(2,3) bridging periodicity
        let period6 = periodic_correlation(&vals, 6);
        result.insert("bott_period_6_bridge".to_string(), vec![period6]);

        // 2. Chern class proxy: curvature form from data
        //    c_k ~ trace of k-th exterior power of curvature matrix
        if d >= 2 {
            let max_dim = d.min(6);
            // Build approximate "curvature" from feature covariance differences
            let mut curv_matrix = vec![0.0f64; max_dim * max_dim];
            for i in 1..max_n {
                for p in 0..max_dim {
                    for q in 0..max_dim {
                        let dp = data[i * d + p] - data[(i - 1) * d + p];
                        let dq = data[i * d + q] - data[(i - 1) * d + q];
                        curv_matrix[p * max_dim + q] += dp * dq;
                    }
                }
            }
            let inv_n = 1.0 / (max_n - 1).max(1) as f64;
            for v in curv_matrix.iter_mut() {
                *v *= inv_n;
            }

            // Chern class c_1 = trace of curvature / 2π
            let trace: f64 = (0..max_dim).map(|i| curv_matrix[i * max_dim + i]).sum();
            let c1 = trace / (2.0 * std::f64::consts::PI);
            result.insert("chern_c1".to_string(), vec![c1]);

            // c_2 = (tr²-tr(F²)) / (8π²) — second Chern class
            let mut trace_f2 = 0.0;
            for i in 0..max_dim {
                for k in 0..max_dim {
                    trace_f2 += curv_matrix[i * max_dim + k] * curv_matrix[k * max_dim + i];
                }
            }
            let c2 = (trace * trace - trace_f2) / (8.0 * std::f64::consts::PI * std::f64::consts::PI);
            result.insert("chern_c2".to_string(), vec![c2]);

            // c_3 proxy from determinant-like quantity
            let c3 = det_3x3_proxy(&curv_matrix, max_dim) / (48.0 * std::f64::consts::PI.powi(3));
            result.insert("chern_c3".to_string(), vec![c3]);

            // Chern character: ch = rank + c1 + (c1²-2c2)/2 + ...
            let ch = max_dim as f64 + c1 + (c1 * c1 - 2.0 * c2) / 2.0;
            result.insert("chern_character".to_string(), vec![ch]);
        }

        // 3. K-group classification: detect if data lives on periodic orbits
        //    K^0 vs K^1 proxy via even/odd harmonic content
        let mut even_power = 0.0;
        let mut odd_power = 0.0;
        for k in 1..max_n.min(50) {
            let mut re = 0.0;
            for (j, &v) in vals.iter().enumerate() {
                re += v * (2.0 * std::f64::consts::PI * k as f64 * j as f64 / vals.len() as f64).cos();
            }
            let power = re * re / (vals.len() as f64).powi(2);
            if k % 2 == 0 {
                even_power += power;
            } else {
                odd_power += power;
            }
        }
        let total_power = (even_power + odd_power).max(1e-12);
        result.insert("k0_weight".to_string(), vec![even_power / total_power]);
        result.insert("k1_weight".to_string(), vec![odd_power / total_power]);

        // 4. Vector bundle rank: effective dimensionality via variance explained
        if d >= 2 {
            let max_dim = d.min(12);
            let mut variances: Vec<f64> = (0..max_dim).map(|j| {
                let col: Vec<f64> = (0..max_n).map(|i| data[i * d + j]).collect();
                let mean = col.iter().sum::<f64>() / col.len() as f64;
                col.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / col.len() as f64
            }).collect();
            variances.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
            let total_var: f64 = variances.iter().sum();
            let mut cum = 0.0;
            let mut effective_rank = variances.len();
            for (i, &v) in variances.iter().enumerate() {
                cum += v;
                if cum / total_var.max(1e-12) > 0.95 {
                    effective_rank = i + 1;
                    break;
                }
            }
            result.insert("bundle_rank".to_string(), vec![effective_rank as f64]);
            result.insert("score".to_string(), vec![result["bott_period_2"][0].min(1.0).max(0.0)]);
        }

        result
    }
}

/// Compute periodic correlation at given lag.
fn periodic_correlation(vals: &[f64], period: usize) -> f64 {
    if vals.len() <= period {
        return 0.0;
    }
    let mean = vals.iter().sum::<f64>() / vals.len() as f64;
    let var: f64 = vals.iter().map(|x| (x - mean).powi(2)).sum::<f64>();
    if var < 1e-12 {
        return 0.0;
    }
    let cov: f64 = vals.iter().skip(period).zip(vals.iter())
        .map(|(&a, &b)| (a - mean) * (b - mean))
        .sum();
    cov / var
}

/// Determinant-like proxy for 3x3 submatrix of a larger matrix.
fn det_3x3_proxy(m: &[f64], dim: usize) -> f64 {
    if dim < 3 {
        return 0.0;
    }
    // Use first 3x3 block
    let a = |i: usize, j: usize| m[i * dim + j];
    a(0, 0) * (a(1, 1) * a(2, 2) - a(1, 2) * a(2, 1))
        - a(0, 1) * (a(1, 0) * a(2, 2) - a(1, 2) * a(2, 0))
        + a(0, 2) * (a(1, 0) * a(2, 1) - a(1, 1) * a(2, 0))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_k_theory_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.3).cos()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = KTheoryLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("bott_period_2"));
        assert!(result.contains_key("chern_c1"));
        assert!(result.contains_key("chern_character"));
    }

    #[test]
    fn test_k_theory_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = KTheoryLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
