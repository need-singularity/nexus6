use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ClassNumberLens: Detect quadratic number field patterns — class numbers,
/// ideal factorization structure, discriminant analysis.
///
/// n=6 connection: h(-24)=2, discriminant -24 = -4·6, the class group of Q(√-6)
/// has order 2, connecting to fundamental n=6 arithmetic.
pub struct ClassNumberLens;

/// Compute Legendre symbol (a/p) for odd prime p.
fn legendre_symbol(a: i64, p: i64) -> i64 {
    if a % p == 0 {
        return 0;
    }
    let exp = (p - 1) / 2;
    let mut result = 1i64;
    let mut base = ((a % p) + p) % p;
    let mut e = exp;
    let modp = p;
    while e > 0 {
        if e % 2 == 1 {
            result = (result * base) % modp;
        }
        base = (base * base) % modp;
        e /= 2;
    }
    if result > p / 2 { result - p } else { result }
}

/// Estimate class number h(D) for negative discriminant D using Dirichlet's formula.
/// h(D) ≈ (√|D| / π) · L(1, χ_D) where L(1, χ_D) = Σ (D/n)/n.
fn estimate_class_number(disc: i64) -> f64 {
    if disc >= 0 {
        return 0.0;
    }
    let abs_d = disc.unsigned_abs() as f64;
    let mut l_value = 0.0;
    for n in 1..=1000i64 {
        let chi = legendre_symbol(disc, if n > 1 && is_odd_prime(n) { n } else { continue });
        l_value += chi as f64 / n as f64;
    }
    (abs_d.sqrt() / std::f64::consts::PI) * l_value.abs()
}

fn is_odd_prime(n: i64) -> bool {
    if n < 3 || n % 2 == 0 {
        return false;
    }
    let mut i = 3;
    while i * i <= n {
        if n % i == 0 {
            return false;
        }
        i += 2;
    }
    true
}

/// Analyze ideal factorization: count how many data values factor as products of small primes.
fn ideal_factorization_score(vals: &[f64]) -> f64 {
    let small_primes = [2, 3, 5, 7, 11, 13];
    let mut smooth_count = 0usize;
    let mut total = 0usize;
    for &v in vals {
        let mut n = v.abs().round() as u64;
        if n < 2 {
            continue;
        }
        total += 1;
        for &p in &small_primes {
            while n % p == 0 {
                n /= p;
            }
        }
        if n == 1 {
            smooth_count += 1; // B-smooth number (factors only into small primes)
        }
    }
    if total > 0 { smooth_count as f64 / total as f64 } else { 0.0 }
}

impl Lens for ClassNumberLens {
    fn name(&self) -> &str {
        "ClassNumberLens"
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

        // 1. Class number h(-24) reference: estimate class numbers for discriminants
        //    derived from data values.
        let h_minus_24 = estimate_class_number(-24);
        result.insert("h_minus_24_estimate".to_string(), vec![h_minus_24]);

        // 2. Discriminant-6 density: what fraction of data yields discriminant ≡ 0 (mod 6)?
        let mut disc_six_count = 0usize;
        let mut disc_total = 0usize;
        for &v in &vals {
            let int_v = v.round() as i64;
            if int_v != 0 {
                let disc = -4 * int_v.abs(); // fundamental discriminant form
                disc_total += 1;
                if disc % 6 == 0 {
                    disc_six_count += 1;
                }
            }
        }
        let disc_six_density = if disc_total > 0 {
            disc_six_count as f64 / disc_total as f64
        } else {
            0.0
        };
        result.insert("discriminant_six_density".to_string(), vec![disc_six_density]);

        // 3. Ideal factorization smoothness
        let smooth_score = ideal_factorization_score(&vals);
        result.insert("ideal_smoothness".to_string(), vec![smooth_score]);

        // 4. Quadratic residue pattern: analyze (v mod p) for primes p
        //    Look for non-random residue distribution
        let primes = [5i64, 7, 11, 13, 17, 19];
        let mut residue_entropy = 0.0;
        for &p in &primes {
            let mut counts = vec![0usize; p as usize];
            for &v in &vals {
                let r = ((v.round() as i64 % p) + p) % p;
                counts[r as usize] += 1;
            }
            let n_f = vals.len() as f64;
            let mut ent = 0.0;
            for &c in &counts {
                if c > 0 {
                    let freq = c as f64 / n_f;
                    ent -= freq * freq.ln();
                }
            }
            residue_entropy += ent;
        }
        residue_entropy /= primes.len() as f64;
        result.insert("quadratic_residue_entropy".to_string(), vec![residue_entropy]);

        // 5. Class group structure: detect order-2 symmetry (like Z/2Z for h(-24)=2)
        //    Measure how symmetric the data distribution is around its mean
        let mean = vals.iter().sum::<f64>() / vals.len() as f64;
        let mut sym_score = 0.0;
        let mut sym_count = 0;
        for &v in &vals {
            let reflected = 2.0 * mean - v;
            // Find nearest value to reflected point
            let nearest_dist = vals.iter().map(|&w| (w - reflected).abs()).fold(f64::INFINITY, f64::min);
            let range = vals.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                - vals.iter().cloned().fold(f64::INFINITY, f64::min);
            if range > 1e-12 {
                sym_score += 1.0 - (nearest_dist / range).min(1.0);
                sym_count += 1;
            }
        }
        let z2_symmetry = if sym_count > 0 { sym_score / sym_count as f64 } else { 0.0 };
        result.insert("z2_symmetry_score".to_string(), vec![z2_symmetry]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_class_number_lens_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64) * 6.0).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = ClassNumberLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("h_minus_24_estimate"));
        assert!(result.contains_key("discriminant_six_density"));
    }

    #[test]
    fn test_class_number_lens_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = ClassNumberLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
