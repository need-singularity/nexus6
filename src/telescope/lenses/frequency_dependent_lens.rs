use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// FrequencyDependentLens: Evolutionary game theory with 6 phenotypes.
///
/// Models Rock-Paper-Scissors-like dynamics among 6 phenotype classes:
///   - Classify data points into 6 phenotype clusters
///   - Build a payoff matrix from pairwise interactions (distance-based)
///   - Check for ESS (Evolutionarily Stable Strategy) conditions
///   - Compute replicator dynamics equilibrium frequencies
///   - Detect cyclic dominance patterns (RPS-like)
pub struct FrequencyDependentLens;

impl Lens for FrequencyDependentLens {
    fn name(&self) -> &str {
        "FrequencyDependentLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 {
            return HashMap::new();
        }

        let k = 6usize; // 6 phenotype classes

        // Simple k-means-like assignment: project to first dim, sort into 6 bins
        let mut vals: Vec<(f64, usize)> = (0..n)
            .map(|i| {
                let v: f64 = (0..d.min(6)).map(|j| data[i * d + j]).sum::<f64>();
                (v, i)
            })
            .collect();
        vals.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

        let mut labels = vec![0usize; n];
        let chunk = n / k;
        for (rank, &(_, idx)) in vals.iter().enumerate() {
            labels[idx] = (rank / chunk.max(1)).min(k - 1);
        }

        // Phenotype frequencies
        let mut freq = vec![0.0f64; k];
        for &l in &labels {
            freq[l] += 1.0;
        }
        for f in &mut freq {
            *f /= n as f64;
        }

        // Build payoff matrix A[i][j] = mean fitness of type i against type j
        // Fitness from interaction = inverse distance (closer = stronger interaction)
        let mut payoff = vec![vec![0.0f64; k]; k];
        let mut counts = vec![vec![0usize; k]; k];
        let max_pairs = 2000;
        let mut pair_count = 0;
        for i in 0..n {
            for j in (i + 1)..n {
                if pair_count >= max_pairs { break; }
                let d_ij = shared.dist(i, j);
                let fitness = if d_ij > 0.0 { 1.0 / (1.0 + d_ij) } else { 1.0 };
                let li = labels[i];
                let lj = labels[j];
                // Asymmetric: type with lower label "wins" slightly more (RPS analog)
                let advantage = if (li + 1) % k == lj { 0.2 } else if (lj + 1) % k == li { -0.2 } else { 0.0 };
                payoff[li][lj] += fitness + advantage;
                payoff[lj][li] += fitness - advantage;
                counts[li][lj] += 1;
                counts[lj][li] += 1;
                pair_count += 1;
            }
            if pair_count >= max_pairs { break; }
        }
        for i in 0..k {
            for j in 0..k {
                if counts[i][j] > 0 {
                    payoff[i][j] /= counts[i][j] as f64;
                }
            }
        }

        // Expected fitness of each type: W_i = sum_j A[i][j] * freq[j]
        let w: Vec<f64> = (0..k)
            .map(|i| (0..k).map(|j| payoff[i][j] * freq[j]).sum())
            .collect();
        let mean_w: f64 = w.iter().zip(&freq).map(|(wi, fi)| wi * fi).sum();

        // ESS check: is any pure strategy stable?
        // A strategy i is ESS if A[i][i] > A[j][i] for all j != i,
        // or if A[i][i] = A[j][i] then A[i][j] > A[j][j]
        let mut ess_count = 0;
        for i in 0..k {
            let is_ess = (0..k).all(|j| {
                if j == i { return true; }
                payoff[i][i] > payoff[j][i]
                    || (payoff[i][i] >= payoff[j][i] - 1e-10 && payoff[i][j] > payoff[j][j])
            });
            if is_ess { ess_count += 1; }
        }

        // Cyclic dominance detection: check if payoff has a cycle i > i+1 > ... > i
        let mut cyclic_strength = 0.0;
        for i in 0..k {
            let j = (i + 1) % k;
            if payoff[i][j] > payoff[j][i] {
                cyclic_strength += payoff[i][j] - payoff[j][i];
            }
        }
        cyclic_strength /= k as f64;

        // Frequency variance (evenness)
        let mean_freq = 1.0 / k as f64;
        let freq_variance: f64 = freq.iter().map(|f| (f - mean_freq).powi(2)).sum::<f64>() / k as f64;

        let mut result = HashMap::new();
        result.insert("mean_fitness".into(), vec![mean_w]);
        result.insert("ess_count".into(), vec![ess_count as f64]);
        result.insert("cyclic_dominance_strength".into(), vec![cyclic_strength]);
        result.insert("frequency_variance".into(), vec![freq_variance]);
        result.insert("phenotype_frequencies".into(), freq);
        result.insert("score".to_string(), vec![result["mean_fitness"][0].min(1.0).max(0.0)]);
        result
    }
}
