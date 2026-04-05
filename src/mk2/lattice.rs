//! Multi-n divisibility lattice.
//!
//! # Topology structure
//!
//! Points have two relations:
//! - **Horizontal** (same prime_set): intra-layer similarity (simhash-like)
//! - **Vertical** (divisibility): cross-layer inheritance (n | m)
//!
//! Layer index = |prime_set| (cardinality = number of distinct primes).
//!
//! # Example
//! ```text
//! Layer 3: n=30={2,3,5}  n=42={2,3,7}  n=105={3,5,7}
//!           ↑              ↑              ↑
//! Layer 2: n=6={2,3}  n=15={3,5}  n=35={5,7}  n=21={3,7}
//!           ↑          ↑           ↑           ↑
//! Layer 1: n=2  n=3  n=5  n=7
//! ```

use std::collections::HashMap;

use crate::mk2::primes::{prime_set_of, PrimeSet};

/// A node in the divisibility lattice.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LatticeNode {
    pub n: u64,
    pub prime_set: PrimeSet,
    pub layer: usize, // = |prime_set|
}

impl LatticeNode {
    pub fn new(n: u64) -> Self {
        let prime_set = prime_set_of(n);
        let layer = prime_set.len();
        Self { n, prime_set, layer }
    }
}

/// Lazy divisibility lattice with LRU-capped cache.
pub struct Lattice {
    cache: HashMap<u64, LatticeNode>,
    capacity: usize,
}

impl Default for Lattice {
    fn default() -> Self {
        Self::new(1000)
    }
}

impl Lattice {
    pub fn new(capacity: usize) -> Self {
        Self {
            cache: HashMap::with_capacity(capacity),
            capacity,
        }
    }

    pub fn node(&mut self, n: u64) -> &LatticeNode {
        if !self.cache.contains_key(&n) {
            // Simple eviction: if full, drop a random entry
            if self.cache.len() >= self.capacity {
                if let Some(k) = self.cache.keys().next().copied() {
                    self.cache.remove(&k);
                }
            }
            self.cache.insert(n, LatticeNode::new(n));
        }
        &self.cache[&n]
    }

    /// Is n divisor of m? (n | m)
    pub fn divides(n: u64, m: u64) -> bool {
        n != 0 && m % n == 0
    }

    /// Cross-layer edge: n → m if n | m and |prime_set(m)| = |prime_set(n)| + 1.
    /// (Adding one more prime to go up a layer.)
    pub fn is_layer_up_edge(&mut self, n: u64, m: u64) -> bool {
        if !Self::divides(n, m) {
            return false;
        }
        let a = self.node(n).layer;
        let b = self.node(m).layer;
        b == a + 1
    }

    /// All n ≤ max with a given prime_set.
    pub fn enumerate_layer(&self, prime_set: &PrimeSet, max: u64) -> Vec<u64> {
        let primes: Vec<u64> = prime_set.iter().collect();
        if primes.is_empty() {
            return vec![];
        }
        let mut out = Vec::new();
        // Generate all products p1^a1 * p2^a2 * ... ≤ max
        fn enumerate(
            primes: &[u64],
            idx: usize,
            acc: u64,
            max: u64,
            out: &mut Vec<u64>,
        ) {
            if idx == primes.len() {
                if acc > 1 {
                    out.push(acc);
                }
                return;
            }
            let p = primes[idx];
            let mut x = acc;
            loop {
                enumerate(primes, idx + 1, x, max, out);
                x = match x.checked_mul(p) {
                    Some(v) if v <= max => v,
                    _ => break,
                };
            }
        }
        enumerate(&primes, 0, 1, max, &mut out);
        // Filter: only those with EXACTLY this prime_set (not less)
        out.retain(|&n| prime_set_of(n) == *prime_set);
        out.sort();
        out
    }

    /// Smallest n whose prime_set matches exactly.
    pub fn smallest_in_layer(prime_set: &PrimeSet) -> u64 {
        let primes: Vec<u64> = prime_set.iter().collect();
        if primes.is_empty() {
            1
        } else {
            primes.iter().product()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lattice_node_basic() {
        let node = LatticeNode::new(6);
        assert_eq!(node.layer, 2); // {2, 3}

        let node = LatticeNode::new(105);
        assert_eq!(node.layer, 3); // {3, 5, 7}

        let node = LatticeNode::new(2310);
        assert_eq!(node.layer, 5); // {2, 3, 5, 7, 11}
    }

    #[test]
    fn divides_basic() {
        assert!(Lattice::divides(6, 12));
        assert!(Lattice::divides(6, 30));
        assert!(!Lattice::divides(6, 10));
        assert!(Lattice::divides(1, 100));
        assert!(!Lattice::divides(0, 10));
    }

    #[test]
    fn layer_up_edge() {
        let mut l = Lattice::default();
        // 6 = {2,3} → 30 = {2,3,5}: layer 2 → 3, divisible
        assert!(l.is_layer_up_edge(6, 30));
        // 6 → 12 = {2,3}: same layer, not up
        assert!(!l.is_layer_up_edge(6, 12));
        // 6 → 10 = {2,5}: not divisible
        assert!(!l.is_layer_up_edge(6, 10));
        // 6 → 210 = {2,3,5,7}: layer 2 → 4, divisible but skip layer
        assert!(!l.is_layer_up_edge(6, 210));
    }

    #[test]
    fn enumerate_layer_small() {
        let l = Lattice::default();
        let ps_23 = prime_set_of(6); // {2,3}
        let entries = l.enumerate_layer(&ps_23, 50);
        // Should contain 6, 12, 18, 24, 36, 48 (all 2^a*3^b with both ≥ 1)
        assert!(entries.contains(&6));
        assert!(entries.contains(&12));
        assert!(entries.contains(&18));
        assert!(entries.contains(&24));
        assert!(entries.contains(&36));
        assert!(entries.contains(&48));
        // Should NOT contain 4 (only {2}), 9 (only {3}), or 8 (only {2})
        assert!(!entries.contains(&4));
        assert!(!entries.contains(&9));
        assert!(!entries.contains(&8));
    }

    #[test]
    fn smallest_in_layer() {
        assert_eq!(Lattice::smallest_in_layer(&prime_set_of(6)), 6);
        assert_eq!(Lattice::smallest_in_layer(&prime_set_of(35)), 35);
        assert_eq!(Lattice::smallest_in_layer(&prime_set_of(105)), 105);
        assert_eq!(Lattice::smallest_in_layer(&prime_set_of(210)), 210);
    }
}
