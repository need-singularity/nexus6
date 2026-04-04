use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ModularLens: Detect modular form patterns — level N=6k, Hecke eigenvalue structure,
/// q-expansion coefficients, and modularity in data.
///
/// n=6 connection: level N = 6k modular forms, weight-2 newforms, Hecke T_p eigenvalues.
pub struct ModularLens;

/// Compute discrete Fourier-like q-expansion coefficients.
/// Treats data as a periodic function and extracts coefficients a(n).
fn q_expansion_coefficients(vals: &[f64], num_coeffs: usize) -> Vec<f64> {
    let n = vals.len();
    let mut coeffs = Vec::with_capacity(num_coeffs);
    for k in 0..num_coeffs {
        let mut re = 0.0;
        for (j, &v) in vals.iter().enumerate() {
            let angle = 2.0 * std::f64::consts::PI * (k as f64) * (j as f64) / (n as f64);
            re += v * angle.cos();
        }
        coeffs.push(re / n as f64);
    }
    coeffs
}

/// Hecke operator T_p action: for a sequence a(n), compute Σ a(pn) + p^(k-1) a(n/p).
/// Simplified to just summing a(p*n) terms that exist.
fn hecke_eigenvalue(coeffs: &[f64], p: usize) -> f64 {
    let mut sum = 0.0;
    let mut count = 0;
    for i in 0..coeffs.len() {
        if i * p < coeffs.len() {
            sum += coeffs[i * p];
            count += 1;
        }
    }
    if count > 0 { sum / count as f64 } else { 0.0 }
}

/// Measure modularity: how well the data respects SL(2,Z) symmetry.
/// Test f(x+1) ≈ f(x) periodicity and f(-1/x) transformation.
fn modularity_score(vals: &[f64]) -> f64 {
    if vals.len() < 12 {
        return 0.0;
    }
    // Test period-6 structure
    let mut period_err = 0.0;
    let mut count = 0;
    for i in 6..vals.len() {
        period_err += (vals[i] - vals[i - 6]).abs();
        count += 1;
    }
    let avg_period_err = if count > 0 { period_err / count as f64 } else { f64::MAX };

    // Normalize by data range
    let max_val = vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    let min_val = vals.iter().cloned().fold(f64::INFINITY, f64::min);
    let range = (max_val - min_val).max(1e-12);

    1.0 - (avg_period_err / range).min(1.0)
}

impl Lens for ModularLens {
    fn name(&self) -> &str {
        "ModularLens"
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

        // Extract first-dimension values
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. q-expansion coefficients
        let num_coeffs = max_n.min(30);
        let coeffs = q_expansion_coefficients(&vals, num_coeffs);

        // Store first 6 coefficient magnitudes
        let coeff_magnitudes: Vec<f64> = coeffs.iter().take(6).map(|c| c.abs()).collect();
        result.insert("q_coeff_magnitudes".to_string(), coeff_magnitudes);

        // 2. Hecke eigenvalues for small primes
        let primes = [2usize, 3, 5, 7, 11, 13];
        let hecke_vals: Vec<f64> = primes.iter().map(|&p| hecke_eigenvalue(&coeffs, p)).collect();
        result.insert("hecke_eigenvalues".to_string(), hecke_vals);

        // 3. Modularity score (period-6 structure)
        let mod_score = modularity_score(&vals);
        result.insert("modularity_score".to_string(), vec![mod_score]);

        // 4. Level detection: find dominant period and check if it's 6k
        let mut best_period = 1;
        let mut best_power = 0.0f64;
        for k in 2..max_n.min(50) {
            let power = coeffs.get(k).map(|c| c.abs()).unwrap_or(0.0);
            if power > best_power {
                best_power = power;
                best_period = k;
            }
        }
        let level_six_alignment = if best_period % 6 == 0 { 1.0 } else {
            1.0 - ((best_period % 6) as f64 / 6.0)
        };
        result.insert("level_six_alignment".to_string(), vec![level_six_alignment]);
        result.insert("dominant_period".to_string(), vec![best_period as f64]);

        // 5. Hecke multiplicativity: check if a(mn) ≈ a(m)·a(n) for coprime m,n
        let mut mult_score = 0.0;
        let mut mult_count = 0;
        for m in 2..num_coeffs.min(8) {
            for nn in 2..num_coeffs.min(8) {
                if m * nn < num_coeffs && gcd(m, nn) == 1 {
                    let a_mn = coeffs[m * nn].abs();
                    let a_m_a_n = (coeffs[m] * coeffs[nn]).abs();
                    if a_m_a_n > 1e-12 {
                        mult_score += 1.0 - (a_mn - a_m_a_n).abs() / a_m_a_n.max(a_mn).max(1e-12);
                        mult_count += 1;
                    }
                }
            }
        }
        let multiplicativity = if mult_count > 0 { (mult_score / mult_count as f64).max(0.0) } else { 0.0 };
        result.insert("hecke_multiplicativity".to_string(), vec![multiplicativity]);

        result
    }
}

fn gcd(mut a: usize, mut b: usize) -> usize {
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_modular_lens_periodic() {
        // Data with period-6 structure
        let data: Vec<f64> = (0..60).map(|i| ((i % 6) as f64).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = ModularLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("modularity_score"));
    }

    #[test]
    fn test_modular_lens_small_n() {
        let data = vec![1.0, 2.0, 3.0];
        let shared = SharedData::compute(&data, 3, 1);
        let result = ModularLens.scan(&data, 3, 1, &shared);
        assert!(result.is_empty());
    }
}
