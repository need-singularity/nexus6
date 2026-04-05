//! SmoothRing trait: φ, τ, σ, sopfr, ρ(n) over u64.
//!
//! All four arithmetic functions defined for any n ≥ 1.
//! n=6 is NOT special — it's a particular instance.

use crate::mk2::primes::{factorize, prime_set_of, PrimeSet};
use crate::mk2::types::Rational;

/// Trait providing n=6-style arithmetic functions for any u64.
pub trait SmoothRing {
    /// Euler totient φ(n) = |{k ≤ n : gcd(k, n) = 1}|
    fn phi(&self) -> u64;

    /// Divisor count τ(n) = |{d : d | n}|
    fn tau(&self) -> u64;

    /// Divisor sum σ(n) = Σ{d : d | n}
    fn sigma(&self) -> u64;

    /// Sum of prime factors with multiplicity sopfr(n) = Σ p·e_p
    fn sopfr(&self) -> u64;

    /// Meta fixed point ρ(n) = φ(n) / n
    fn meta_fp(&self) -> Rational;

    /// Prime set of n (distinct prime factors)
    fn prime_set(&self) -> PrimeSet;
}

impl SmoothRing for u64 {
    fn phi(&self) -> u64 {
        if *self == 0 {
            return 0;
        }
        let mut result = *self;
        for (p, _) in factorize(*self) {
            result = result / p * (p - 1);
        }
        result
    }

    fn tau(&self) -> u64 {
        if *self == 0 {
            return 0;
        }
        factorize(*self)
            .iter()
            .map(|(_, e)| (*e as u64) + 1)
            .product()
    }

    fn sigma(&self) -> u64 {
        if *self == 0 {
            return 0;
        }
        factorize(*self)
            .iter()
            .map(|(p, e)| {
                let e = *e as u32;
                (p.pow(e + 1) - 1) / (p - 1)
            })
            .product()
    }

    fn sopfr(&self) -> u64 {
        factorize(*self)
            .iter()
            .map(|(p, e)| p * (*e as u64))
            .sum()
    }

    fn meta_fp(&self) -> Rational {
        if *self == 0 {
            return Rational::zero();
        }
        Rational::new(self.phi() as i128, *self as i128)
    }

    fn prime_set(&self) -> PrimeSet {
        prime_set_of(*self)
    }
}

/// Shorthand: ρ(n) = φ(n)/n
pub fn rho(n: u64) -> Rational {
    n.meta_fp()
}

/// Euler ratio over a prime set S: ∏(1 - 1/p) for p ∈ S.
/// Same as ρ(n) for any n whose prime set is exactly S.
pub fn euler_ratio(ps: &PrimeSet) -> Rational {
    let mut result = Rational::one();
    for p in ps.iter() {
        let p_i = p as i128;
        result = result * Rational::new(p_i - 1, p_i);
    }
    result
}

/// Find the smallest n whose prime_set matches the given set.
pub fn smallest_n_with_primes(ps: &PrimeSet) -> u64 {
    ps.iter().product::<u64>().max(1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn arithmetic_n6() {
        assert_eq!(6u64.phi(), 2);
        assert_eq!(6u64.tau(), 4);
        assert_eq!(6u64.sigma(), 12);
        assert_eq!(6u64.sopfr(), 5); // 2+3
    }

    #[test]
    fn arithmetic_n15() {
        assert_eq!(15u64.phi(), 8);
        assert_eq!(15u64.tau(), 4);
        assert_eq!(15u64.sigma(), 24);
        assert_eq!(15u64.sopfr(), 8); // 3+5
    }

    #[test]
    fn arithmetic_n35() {
        assert_eq!(35u64.phi(), 24);
        assert_eq!(35u64.tau(), 4);
        assert_eq!(35u64.sigma(), 48);
        assert_eq!(35u64.sopfr(), 12); // 5+7
    }

    #[test]
    fn perfect_numbers() {
        // σ(P) = 2P for perfect numbers
        for &p in &[6u64, 28, 496, 8128] {
            assert_eq!(p.sigma(), 2 * p, "σ({})={} should be {}", p, p.sigma(), 2 * p);
        }
    }

    #[test]
    fn meta_fp_ladder() {
        assert_eq!(rho(6), Rational::new(1, 3));
        assert_eq!(rho(12), Rational::new(1, 3)); // {2,3}-smooth: same ρ
        assert_eq!(rho(18), Rational::new(1, 3)); // {2,3}-smooth
        assert_eq!(rho(15), Rational::new(4, 15));
        assert_eq!(rho(35), Rational::new(24, 35));
    }

    #[test]
    fn euler_ratio_smooth_classes() {
        // {2,3}-smooth → 1/3
        let r = euler_ratio(&prime_set_of(6));
        assert_eq!(r, Rational::new(1, 3));

        // {5,7}-smooth → 24/35
        let r = euler_ratio(&prime_set_of(35));
        assert_eq!(r, Rational::new(24, 35));

        // {2,3,5,7}-smooth → 8/35
        let r = euler_ratio(&prime_set_of(210));
        assert_eq!(r, Rational::new(8, 35));
    }

    #[test]
    fn smallest_n_ident() {
        assert_eq!(smallest_n_with_primes(&prime_set_of(6)), 6); // 2·3
        assert_eq!(smallest_n_with_primes(&prime_set_of(12)), 6); // {2,3} → 6
        assert_eq!(smallest_n_with_primes(&prime_set_of(105)), 105); // 3·5·7
        assert_eq!(smallest_n_with_primes(&prime_set_of(35)), 35); // 5·7
    }

    #[test]
    fn large_n() {
        assert_eq!(100u64.phi(), 40);
        assert_eq!(1000u64.phi(), 400);
        assert_eq!(720u64.phi(), 192); // 6!
        assert_eq!(720u64.tau(), 30);
    }
}
