//! Prime utilities: sieve, factorize, PrimeSet bitmask
//!
//! # Design decisions
//!
//! - Prime type: `u64`, max 10^9 (covers all physics constants)
//! - PrimeSet: `u64` bitmask indexing first 64 primes (2..=311)
//! - Factorize: trial division up to √n, sufficient for u64 inputs

use serde::{Deserialize, Serialize};

/// A prime number (u64).
pub type Prime = u64;

/// First 64 primes (2 through 311), indexed 0..64.
/// Used for PrimeSet bitmask representation.
pub const FIRST_64_PRIMES: [u64; 64] = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53,
    59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131,
    137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223,
    227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311,
];

/// Lookup index of prime p in FIRST_64_PRIMES. Returns None if p > 311 or not prime.
pub fn prime_index(p: u64) -> Option<usize> {
    FIRST_64_PRIMES.iter().position(|&q| q == p)
}

/// Check if n is prime (trial division).
pub fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    if n < 4 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }
    let mut d: u64 = 3;
    while d.saturating_mul(d) <= n {
        if n % d == 0 {
            return false;
        }
        d += 2;
    }
    true
}

/// Generate all primes up to `limit` (inclusive) via sieve of Eratosthenes.
pub fn primes_up_to(limit: u64) -> Vec<u64> {
    if limit < 2 {
        return vec![];
    }
    let n = limit as usize;
    let mut is_composite = vec![false; n + 1];
    let mut out = Vec::new();
    for i in 2..=n {
        if !is_composite[i] {
            out.push(i as u64);
            let mut j = i.saturating_mul(i);
            while j <= n {
                is_composite[j] = true;
                j += i;
            }
        }
    }
    out
}

/// Factorize n into (prime, exponent) pairs, sorted by prime ascending.
/// Empty vec for n=0 or n=1.
pub fn factorize(n: u64) -> Vec<(Prime, u32)> {
    if n < 2 {
        return vec![];
    }
    let mut out = Vec::new();
    let mut m = n;
    let mut d: u64 = 2;
    while d.saturating_mul(d) <= m {
        let mut exp = 0u32;
        while m % d == 0 {
            m /= d;
            exp += 1;
        }
        if exp > 0 {
            out.push((d, exp));
        }
        d += if d == 2 { 1 } else { 2 };
    }
    if m > 1 {
        out.push((m, 1));
    }
    out
}

/// Unique prime set of n = {primes dividing n}.
pub fn prime_set_of(n: u64) -> PrimeSet {
    let mut ps = PrimeSet::empty();
    for (p, _) in factorize(n) {
        ps.insert(p);
    }
    ps
}

/// PrimeSet: subset of first 64 primes as u64 bitmask.
///
/// Bit i set ⟺ FIRST_64_PRIMES[i] is in the set.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PrimeSet(u64);

impl PrimeSet {
    pub const fn empty() -> Self {
        Self(0)
    }

    pub const fn from_bits(bits: u64) -> Self {
        Self(bits)
    }

    pub const fn bits(&self) -> u64 {
        self.0
    }

    /// Insert prime p. If p is not in FIRST_64_PRIMES, silently ignored.
    pub fn insert(&mut self, p: Prime) -> bool {
        if let Some(idx) = prime_index(p) {
            self.0 |= 1u64 << idx;
            true
        } else {
            false
        }
    }

    /// Remove prime p.
    pub fn remove(&mut self, p: Prime) {
        if let Some(idx) = prime_index(p) {
            self.0 &= !(1u64 << idx);
        }
    }

    pub fn contains(&self, p: Prime) -> bool {
        prime_index(p).is_some_and(|idx| self.0 & (1u64 << idx) != 0)
    }

    pub fn len(&self) -> usize {
        self.0.count_ones() as usize
    }

    pub fn is_empty(&self) -> bool {
        self.0 == 0
    }

    pub fn union(&self, other: &Self) -> Self {
        Self(self.0 | other.0)
    }

    pub fn intersection(&self, other: &Self) -> Self {
        Self(self.0 & other.0)
    }

    /// Is `self` a subset of `other`?
    pub fn is_subset(&self, other: &Self) -> bool {
        (self.0 & !other.0) == 0
    }

    /// Iterate primes in the set, ascending.
    pub fn iter(&self) -> impl Iterator<Item = Prime> + '_ {
        (0..64).filter_map(move |i| {
            if self.0 & (1u64 << i) != 0 {
                Some(FIRST_64_PRIMES[i])
            } else {
                None
            }
        })
    }

    pub fn to_vec(&self) -> Vec<Prime> {
        self.iter().collect()
    }
}

impl std::fmt::Display for PrimeSet {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let primes: Vec<String> = self.iter().map(|p| p.to_string()).collect();
        write!(f, "{{{}}}", primes.join(","))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn is_prime_basic() {
        assert!(!is_prime(0));
        assert!(!is_prime(1));
        assert!(is_prime(2));
        assert!(is_prime(3));
        assert!(!is_prime(4));
        assert!(is_prime(127));
        assert!(is_prime(311));
        assert!(!is_prime(1024));
    }

    #[test]
    fn factorize_examples() {
        assert_eq!(factorize(6), vec![(2, 1), (3, 1)]);
        assert_eq!(factorize(12), vec![(2, 2), (3, 1)]);
        assert_eq!(factorize(105), vec![(3, 1), (5, 1), (7, 1)]);
        assert_eq!(factorize(8128), vec![(2, 6), (127, 1)]); // P4
        assert_eq!(factorize(496), vec![(2, 4), (31, 1)]); // P3
        assert_eq!(factorize(1), vec![]);
    }

    #[test]
    fn prime_set_ops() {
        let ps = prime_set_of(6);
        assert_eq!(ps.len(), 2);
        assert!(ps.contains(2));
        assert!(ps.contains(3));
        assert!(!ps.contains(5));

        let ps15 = prime_set_of(15);
        assert_eq!(ps15.len(), 2);
        assert!(ps15.contains(3));
        assert!(ps15.contains(5));

        // subset
        let ps105 = prime_set_of(105); // {3,5,7}
        assert!(ps15.is_subset(&ps105));
        assert!(!ps.is_subset(&ps105)); // {2,3} not subset of {3,5,7}
    }

    #[test]
    fn prime_set_union_intersection() {
        let a = prime_set_of(6); // {2,3}
        let b = prime_set_of(15); // {3,5}
        let u = a.union(&b); // {2,3,5}
        let i = a.intersection(&b); // {3}
        assert_eq!(u.len(), 3);
        assert_eq!(i.len(), 1);
        assert!(i.contains(3));
    }

    #[test]
    fn primes_up_to_1000() {
        let ps = primes_up_to(1000);
        assert_eq!(ps.len(), 168);
        assert_eq!(ps[0], 2);
        assert_eq!(ps[167], 997);
    }

    #[test]
    fn factorize_large() {
        // Mersenne primes
        assert_eq!(factorize(127), vec![(127, 1)]);
        assert_eq!(factorize(31), vec![(31, 1)]);
        // composites
        assert_eq!(factorize(720), vec![(2, 4), (3, 2), (5, 1)]); // 6!
    }
}
