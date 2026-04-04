use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// DiscreteLogLens: Cryptographic discrete logarithm analysis.
///
/// Interprets data as elements in a cyclic group of order 6k:
/// - Baby-step giant-step style search for discrete log structure
/// - Index calculus inspired factor base analysis
/// - Group order detection via periodicity in distances
/// - 6k order group resonance check
pub struct DiscreteLogLens;

impl Lens for DiscreteLogLens {
    fn name(&self) -> &str { "DiscreteLogLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = d;
        if n < 6 { return HashMap::new(); }

        // Map pairwise distances to "exponents" in a cyclic group
        let mut dists = Vec::with_capacity(n * (n - 1) / 2);
        for i in 0..n {
            for j in (i + 1)..n {
                dists.push(shared.dist(i, j));
            }
        }
        dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let max_dist = dists.last().cloned().unwrap_or(1.0).max(1e-15);

        // Quantize distances into group elements mod 6k
        let group_order = 6 * n; // order = 6k where k=n
        let quantized: Vec<usize> = dists.iter()
            .map(|&d| ((d / max_dist) * (group_order as f64 - 1.0)).round() as usize % group_order)
            .collect();

        // Baby-step giant-step: detect periodicity
        // Check for period p in quantized values
        let baby_step_size = (group_order as f64).sqrt().ceil() as usize;
        let mut period_scores = Vec::new();
        for p in 1..=baby_step_size.min(36) {
            let mut matches = 0;
            let total = quantized.len().saturating_sub(p);
            for i in 0..total {
                if quantized[i] % p == quantized[(i + p) % quantized.len()] % p {
                    matches += 1;
                }
            }
            let score = if total > 0 { matches as f64 / total as f64 } else { 0.0 };
            period_scores.push((p, score));
        }
        period_scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

        let best_period = period_scores.first().map(|&(p, _)| p).unwrap_or(1);
        let best_period_score = period_scores.first().map(|&(_, s)| s).unwrap_or(0.0);

        // Index calculus: factor base = small primes {2, 3, 5}
        // Count how many quantized values factor over this base
        let factor_base = [2usize, 3, 5];
        let mut smooth_count = 0;
        for &q in &quantized {
            if q == 0 { smooth_count += 1; continue; }
            let mut val = q;
            for &p in &factor_base {
                while val > 0 && val % p == 0 { val /= p; }
            }
            if val <= 1 { smooth_count += 1; }
        }
        let smoothness_ratio = smooth_count as f64 / quantized.len().max(1) as f64;

        // Pohlig-Hellman inspired: check if group_order has factor 6
        let pohlig_hellman_6 = if group_order % 6 == 0 { 1.0 } else { 0.0 };

        // Distribution uniformity in Z/6Z
        let mut mod6_hist = [0usize; 6];
        for &q in &quantized {
            mod6_hist[q % 6] += 1;
        }
        let expected = quantized.len() as f64 / 6.0;
        let chi_sq: f64 = mod6_hist.iter()
            .map(|&c| (c as f64 - expected).powi(2) / expected.max(1e-15))
            .sum();
        // Low chi_sq = uniform = random-looking (good cryptographic property)
        let uniformity_6 = (-chi_sq / 12.0).exp();

        // DLP hardness estimate: based on baby-step giant-step complexity
        let dlp_hardness = (group_order as f64).sqrt().log2();

        let mut result = HashMap::new();
        result.insert("group_order".into(), vec![group_order as f64]);
        result.insert("best_period".into(), vec![best_period as f64]);
        result.insert("period_score".into(), vec![best_period_score]);
        result.insert("smoothness_ratio".into(), vec![smoothness_ratio]);
        result.insert("pohlig_hellman_6".into(), vec![pohlig_hellman_6]);
        result.insert("uniformity_mod6".into(), vec![uniformity_6]);
        result.insert("mod6_histogram".into(), mod6_hist.iter().map(|&c| c as f64).collect());
        result.insert("dlp_hardness_bits".into(), vec![dlp_hardness]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_discrete_log() {
        let mut data = Vec::new();
        for i in 0..12 {
            data.push((i as f64 * 2.0).sin());
            data.push((i as f64 * 3.0).cos());
        }
        let n = 12;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = DiscreteLogLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("group_order"));
        assert_eq!(r["group_order"][0], 72.0); // 6 * 12
        assert!(r["pohlig_hellman_6"][0] == 1.0);
    }
}
