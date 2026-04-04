use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MobiusInversionLens: Detect Mobius function patterns and incidence algebra structure.
///
/// n=6 connection: μ(6) = μ(2·3) = μ(2)·μ(3) = 1 (square-free, even # of prime factors),
/// Mobius inversion recovers multiplicative structure from additive.
pub struct MobiusInversionLens;

/// Compute Mobius function μ(n).
fn mobius(n: u64) -> i64 {
    if n == 0 {
        return 0;
    }
    if n == 1 {
        return 1;
    }
    let mut remaining = n;
    let mut num_factors = 0;

    let mut p = 2;
    while p * p <= remaining {
        if remaining % p == 0 {
            remaining /= p;
            if remaining % p == 0 {
                return 0; // p^2 divides n
            }
            num_factors += 1;
        }
        p += 1;
    }
    if remaining > 1 {
        num_factors += 1;
    }
    if num_factors % 2 == 0 { 1 } else { -1 }
}

/// Compute Mobius inversion: if g(n) = Σ_{d|n} f(d), recover f(n) = Σ_{d|n} μ(n/d)·g(d).
fn mobius_inversion(g: &[f64]) -> Vec<f64> {
    let n = g.len();
    let mut f = vec![0.0; n];
    for i in 1..n {
        for d in 1..=i {
            if i % d == 0 {
                let mu = mobius((i / d) as u64);
                if mu != 0 && d < n {
                    f[i] += mu as f64 * g[d];
                }
            }
        }
    }
    f
}

/// Measure how multiplicative a sequence is: check if f(mn) ≈ f(m)·f(n) for coprime m,n.
fn multiplicativity_score(f: &[f64]) -> f64 {
    let mut score = 0.0;
    let mut count = 0;
    for m in 2..f.len().min(20) {
        for n in 2..f.len().min(20) {
            if m * n < f.len() && gcd(m, n) == 1 {
                let product = f[m] * f[n];
                let actual = f[m * n];
                if product.abs() > 1e-12 {
                    score += 1.0 - (actual - product).abs() / product.abs().max(actual.abs()).max(1e-12);
                    count += 1;
                }
            }
        }
    }
    if count > 0 { (score / count as f64).max(0.0) } else { 0.0 }
}

fn gcd(mut a: usize, mut b: usize) -> usize {
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a
}

impl Lens for MobiusInversionLens {
    fn name(&self) -> &str {
        "MobiusInversionLens"
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
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. μ(6) = 1 verification and Mobius value distribution
        result.insert("mobius_six".to_string(), vec![mobius(6) as f64]); // Should be 1.0

        // Distribution of μ values in data-derived integers
        let mut mu_plus = 0usize;
        let mut mu_minus = 0usize;
        let mut mu_zero = 0usize;
        for &v in &vals {
            let int_v = v.abs().round() as u64;
            if int_v >= 1 && int_v <= 10000 {
                match mobius(int_v) {
                    1 => mu_plus += 1,
                    -1 => mu_minus += 1,
                    _ => mu_zero += 1,
                }
            }
        }
        let total = (mu_plus + mu_minus + mu_zero).max(1) as f64;
        result.insert("mobius_distribution".to_string(), vec![
            mu_plus as f64 / total,
            mu_minus as f64 / total,
            mu_zero as f64 / total,
        ]);

        // 2. Mobius inversion: apply inversion and check if result is "simpler"
        let inverted = mobius_inversion(&vals);
        let original_complexity: f64 = vals.windows(2).map(|w| (w[1] - w[0]).abs()).sum::<f64>();
        let inverted_complexity: f64 = inverted.windows(2).map(|w| (w[1] - w[0]).abs()).sum::<f64>();
        let inversion_simplification = if original_complexity > 1e-12 {
            (original_complexity - inverted_complexity) / original_complexity
        } else {
            0.0
        };
        result.insert("inversion_simplification".to_string(), vec![inversion_simplification]);

        // 3. Multiplicativity of inverted sequence
        let mult_score = multiplicativity_score(&inverted);
        result.insert("multiplicativity".to_string(), vec![mult_score]);

        // 4. Square-free density: fraction of data values that are square-free (μ≠0)
        let square_free_count = mu_plus + mu_minus;
        let sqfree_density = square_free_count as f64 / total;
        result.insert("square_free_density".to_string(), vec![sqfree_density]);
        // Theoretical: 6/π² ≈ 0.6079 for random integers
        let sqfree_deviation = (sqfree_density - 6.0 / (std::f64::consts::PI * std::f64::consts::PI)).abs();
        result.insert("sqfree_deviation_from_theory".to_string(), vec![sqfree_deviation]);

        // 5. Symmetry restoration: compare autocorrelation before/after inversion
        let auto_before = autocorrelation_lag1(&vals);
        let auto_after = autocorrelation_lag1(&inverted);
        result.insert("symmetry_restoration".to_string(), vec![auto_before, auto_after]);

        result
    }
}

fn autocorrelation_lag1(vals: &[f64]) -> f64 {
    if vals.len() < 3 {
        return 0.0;
    }
    let mean = vals.iter().sum::<f64>() / vals.len() as f64;
    let var: f64 = vals.iter().map(|x| (x - mean).powi(2)).sum::<f64>();
    if var < 1e-12 {
        return 0.0;
    }
    let cov: f64 = vals.windows(2).map(|w| (w[0] - mean) * (w[1] - mean)).sum();
    cov / var
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_mobius_function() {
        assert_eq!(mobius(1), 1);
        assert_eq!(mobius(2), -1);
        assert_eq!(mobius(3), -1);
        assert_eq!(mobius(4), 0); // 2^2
        assert_eq!(mobius(5), -1);
        assert_eq!(mobius(6), 1); // 2·3, even # of factors
        assert_eq!(mobius(30), -1); // 2·3·5, odd # of factors
    }

    #[test]
    fn test_mobius_inversion_lens() {
        let data: Vec<f64> = (1..=60).map(|i| i as f64).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = MobiusInversionLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert_eq!(result["mobius_six"][0], 1.0);
    }

    #[test]
    fn test_mobius_lens_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = MobiusInversionLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
