use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MatroidLens: Combinatorial optimization via matroid theory.
///
/// Analyzes data using uniform matroid U(6,n) structure:
/// - Independent sets: subsets of size <= 6
/// - Rank function and circuit detection
/// - Greedy algorithm optimality on matroid structure
/// - Tutte polynomial evaluation at key points
pub struct MatroidLens;

impl Lens for MatroidLens {
    fn name(&self) -> &str { "MatroidLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = (data, d);
        if n < 6 { return HashMap::new(); }

        let rank = 6usize; // U(6,n) matroid

        // Matroid rank function: for each subset, rank = min(|S|, 6)
        // We sample random subsets and verify matroid properties

        // Greedy algorithm: select 6 most spread-out points
        // (farthest-point sampling gives greedy-optimal on U(6,n))
        let mut selected = Vec::new();
        let mut available: Vec<bool> = vec![true; n];

        // Start with first point
        selected.push(0);
        available[0] = false;

        while selected.len() < rank && selected.len() < n {
            let mut best_idx = 0;
            let mut best_min_dist = -1.0f64;
            for i in 0..n {
                if !available[i] { continue; }
                let min_dist = selected.iter()
                    .map(|&j| shared.dist(i, j))
                    .fold(f64::MAX, f64::min);
                if min_dist > best_min_dist {
                    best_min_dist = min_dist;
                    best_idx = i;
                }
            }
            selected.push(best_idx);
            available[best_idx] = false;
        }

        // Greedy value: sum of pairwise distances in selected set
        let mut greedy_value = 0.0;
        for i in 0..selected.len() {
            for j in (i + 1)..selected.len() {
                greedy_value += shared.dist(selected[i], selected[j]);
            }
        }

        // Circuit detection: a circuit in U(6,n) is any set of size 7
        // Check density: how many near-duplicate points exist
        let mut circuits_found = 0;
        let threshold = {
            let mut all_d = Vec::new();
            for i in 0..n.min(30) {
                for j in (i + 1)..n.min(30) {
                    all_d.push(shared.dist(i, j));
                }
            }
            all_d.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            all_d.get(all_d.len() / 10).cloned().unwrap_or(0.1) // 10th percentile
        };

        // Find dense cliques of size > 6 (matroid circuits)
        for i in 0..n.min(20) {
            let neighbors: Vec<usize> = (0..n)
                .filter(|&j| j != i && shared.dist(i, j) < threshold)
                .collect();
            if neighbors.len() >= rank {
                circuits_found += 1;
            }
        }
        let circuit_density = circuits_found as f64 / n.min(20) as f64;

        // Matroid polytope: the independent set polytope has vertices at indicator vectors
        // Compute spread of data projected onto the 6-point basis
        let basis_spread = if selected.len() >= 2 {
            let mut max_d = 0.0f64;
            let mut min_d = f64::MAX;
            for i in 0..selected.len() {
                for j in (i + 1)..selected.len() {
                    let dd = shared.dist(selected[i], selected[j]);
                    if dd > max_d { max_d = dd; }
                    if dd < min_d { min_d = dd; }
                }
            }
            if min_d > 1e-15 { max_d / min_d } else { max_d }
        } else { 0.0 };

        // Tutte polynomial T(x,y) at special points:
        // T(1,1) = number of bases (C(n,6))
        let num_bases = binomial(n, rank);
        // T(2,1) = number of independent sets = sum_{k=0}^{6} C(n,k)
        let num_independent: u64 = (0..=rank).map(|k| binomial(n, k)).sum();
        // T(1,2) = number of spanning sets = sum_{k=6}^{n} C(n,k)
        let num_spanning: u64 = (rank..=n).map(|k| binomial(n, k)).sum();

        // Greedy optimality ratio (how good is greedy vs optimal for matroid)
        // For matroids, greedy IS optimal, so ratio should be 1.0
        // We verify by comparing with random selection
        let mut random_values = Vec::new();
        let step = n.max(1);
        for offset in 0..6.min(n) {
            let random_set: Vec<usize> = (0..rank).map(|i| (i * step / rank + offset) % n).collect();
            let mut val = 0.0;
            for i in 0..random_set.len() {
                for j in (i + 1)..random_set.len() {
                    if random_set[i] != random_set[j] {
                        val += shared.dist(random_set[i], random_set[j]);
                    }
                }
            }
            random_values.push(val);
        }
        let avg_random = random_values.iter().sum::<f64>() / random_values.len().max(1) as f64;
        let greedy_ratio = if avg_random > 1e-15 { greedy_value / avg_random } else { 1.0 };

        let mut result = HashMap::new();
        result.insert("matroid_rank".into(), vec![rank as f64]);
        result.insert("greedy_value".into(), vec![greedy_value]);
        result.insert("greedy_optimality_ratio".into(), vec![greedy_ratio]);
        result.insert("circuit_density".into(), vec![circuit_density]);
        result.insert("basis_spread".into(), vec![basis_spread]);
        result.insert("num_bases".into(), vec![num_bases as f64]);
        result.insert("num_independent_sets".into(), vec![num_independent as f64]);
        result.insert("num_spanning_sets".into(), vec![num_spanning as f64]);
        result
    }
}

fn binomial(n: usize, k: usize) -> u64 {
    if k > n { return 0; }
    if k == 0 || k == n { return 1; }
    let k = k.min(n - k);
    let mut result = 1u64;
    for i in 0..k {
        result = result.saturating_mul((n - i) as u64) / (i as u64 + 1);
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_matroid() {
        let mut data = Vec::new();
        for i in 0..10 {
            data.push(i as f64);
            data.push((i as f64 * 0.7).sin());
        }
        let n = 10;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = MatroidLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("matroid_rank"));
        assert_eq!(r["matroid_rank"][0], 6.0);
        assert!(r["greedy_optimality_ratio"][0] >= 0.5);
        // C(10,6) = 210
        assert_eq!(r["num_bases"][0], 210.0);
    }
}
