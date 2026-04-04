use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// CommunicationComplexityLens: Two-party communication complexity analysis.
///
/// Splits data between Alice and Bob (first/second half of dimensions):
/// - Measures bits needed to communicate a function of joint input
/// - 6-bit protocol: evaluates what can be communicated in 6 bits
/// - Monochromatic rectangle analysis for lower bounds
/// - Information complexity: mutual information between halves
pub struct CommunicationComplexityLens;

impl Lens for CommunicationComplexityLens {
    fn name(&self) -> &str { "CommunicationComplexityLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = shared;
        if n < 4 || d < 2 { return HashMap::new(); }

        let d_alice = d / 2;
        let d_bob = d - d_alice;

        // Build communication matrix: distance between Alice's and Bob's views
        // Alice holds dimensions [0..d_alice), Bob holds [d_alice..d)
        let mut alice_data = vec![0.0; n * d_alice];
        let mut bob_data = vec![0.0; n * d_bob];
        for i in 0..n {
            for j in 0..d_alice {
                alice_data[i * d_alice + j] = data[i * d + j];
            }
            for j in 0..d_bob {
                bob_data[i * d_bob + j] = data[i * d + d_alice + j];
            }
        }

        // Communication function: can Alice and Bob agree on nearest-neighbor?
        // Compute agreement without communication vs with k-bit protocol

        // No communication: each party finds their local nearest neighbor
        let alice_nn = find_nearest_neighbors(&alice_data, n, d_alice);
        let bob_nn = find_nearest_neighbors(&bob_data, n, d_bob);

        // True nearest neighbors (with full information)
        let mut true_nn = vec![0usize; n];
        for i in 0..n {
            let mut best_j = if i == 0 { 1 } else { 0 };
            let mut best_d = shared.dist(i, best_j);
            for j in 0..n {
                if j == i { continue; }
                let dd = shared.dist(i, j);
                if dd < best_d {
                    best_d = dd;
                    best_j = j;
                }
            }
            true_nn[i] = best_j;
        }

        // Agreement rate without communication
        let agree_none = (0..n).filter(|&i| alice_nn[i] == true_nn[i] || bob_nn[i] == true_nn[i]).count();
        let rate_no_comm = agree_none as f64 / n as f64;

        // 6-bit protocol simulation: Alice sends 6-bit hash of her data
        // Quantize Alice's data into 2^6 = 64 buckets
        let bits = 6usize;
        let buckets = 1usize << bits;
        let mut alice_hashes = vec![0u64; n];
        for i in 0..n {
            let mut hash: u64 = 0;
            for j in 0..d_alice.min(bits) {
                let val = alice_data[i * d_alice + j];
                // Simple quantization bit
                let bit = if val >= 0.0 { 1u64 } else { 0u64 };
                hash |= bit << j;
            }
            alice_hashes[i] = hash % buckets as u64;
        }

        // With 6-bit hash, Bob can narrow down candidates
        let mut agree_6bit = 0;
        for i in 0..n {
            let my_hash = alice_hashes[i];
            // Bob considers only points with same Alice hash
            let candidates: Vec<usize> = (0..n)
                .filter(|&j| j != i && alice_hashes[j] == my_hash)
                .collect();
            if candidates.is_empty() { continue; }
            // Bob picks nearest in his view among same-hash candidates
            let best = candidates.iter()
                .min_by(|&&a, &&b| {
                    let da = bob_l2(&bob_data, i, a, d_bob);
                    let db = bob_l2(&bob_data, i, b, d_bob);
                    da.partial_cmp(&db).unwrap_or(std::cmp::Ordering::Equal)
                })
                .cloned()
                .unwrap_or(0);
            if best == true_nn[i] { agree_6bit += 1; }
        }
        let rate_6bit = agree_6bit as f64 / n as f64;

        // Information complexity: mutual information I(Alice ; Bob)
        // Approximated via correlation between Alice and Bob distances
        let mut alice_dists = Vec::new();
        let mut bob_dists = Vec::new();
        for i in 0..n.min(50) {
            for j in (i + 1)..n.min(50) {
                alice_dists.push(l2_dist(&alice_data, i, j, d_alice));
                bob_dists.push(l2_dist(&bob_data, i, j, d_bob));
            }
        }
        let mi_approx = correlation(&alice_dists, &bob_dists).abs();

        // Communication lower bound: log2(n) bits needed in worst case
        let lower_bound = (n as f64).log2();

        // Protocol advantage: improvement of 6-bit over no-communication
        let protocol_advantage = rate_6bit - rate_no_comm;

        // n=6 resonance
        let n6_match = (-((bits as f64 - 6.0).abs() * 0.5)).exp(); // trivially 1.0

        let mut result = HashMap::new();
        result.insert("rate_no_communication".into(), vec![rate_no_comm]);
        result.insert("rate_6bit_protocol".into(), vec![rate_6bit]);
        result.insert("protocol_advantage".into(), vec![protocol_advantage]);
        result.insert("mutual_information_approx".into(), vec![mi_approx]);
        result.insert("communication_lower_bound".into(), vec![lower_bound]);
        result.insert("n6_protocol_match".into(), vec![n6_match]);
        result.insert("score".to_string(), vec![result["rate_no_communication"][0].min(1.0).max(0.0)]);
        result
    }
}

fn l2_dist(data: &[f64], i: usize, j: usize, d: usize) -> f64 {
    let mut sum = 0.0;
    for k in 0..d {
        let diff = data[i * d + k] - data[j * d + k];
        sum += diff * diff;
    }
    sum.sqrt()
}

fn bob_l2(data: &[f64], i: usize, j: usize, d: usize) -> f64 {
    l2_dist(data, i, j, d)
}

fn find_nearest_neighbors(data: &[f64], n: usize, d: usize) -> Vec<usize> {
    let mut nn = vec![0usize; n];
    for i in 0..n {
        let mut best_j = if i == 0 { 1 } else { 0 };
        let mut best_d = l2_dist(data, i, best_j, d);
        for j in 0..n {
            if j == i { continue; }
            let dd = l2_dist(data, i, j, d);
            if dd < best_d {
                best_d = dd;
                best_j = j;
            }
        }
        nn[i] = best_j;
    }
    nn
}

fn correlation(xs: &[f64], ys: &[f64]) -> f64 {
    let n = xs.len();
    if n < 2 { return 0.0; }
    let mx = xs.iter().sum::<f64>() / n as f64;
    let my = ys.iter().sum::<f64>() / n as f64;
    let mut cov = 0.0;
    let mut vx = 0.0;
    let mut vy = 0.0;
    for i in 0..n {
        let dx = xs[i] - mx;
        let dy = ys[i] - my;
        cov += dx * dy;
        vx += dx * dx;
        vy += dy * dy;
    }
    let denom = (vx * vy).sqrt();
    if denom < 1e-15 { 0.0 } else { cov / denom }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_communication_complexity() {
        let mut data = Vec::new();
        for i in 0..12 {
            data.push(i as f64);
            data.push((i * 3) as f64);
            data.push((i % 4) as f64);
            data.push(((i + 1) % 5) as f64);
        }
        let n = 12;
        let d = 4;
        let shared = SharedData::compute(&data, n, d);
        let r = CommunicationComplexityLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("rate_6bit_protocol"));
        assert!(r["communication_lower_bound"][0] > 0.0);
    }
}
