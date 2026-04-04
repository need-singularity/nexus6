use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// NeutralTheoryLens: Kimura's neutral theory of molecular evolution.
///
/// Models 6-allele equilibrium under drift and mutation:
///   - Population of n points interpreted as allele frequency vectors
///   - Heterozygosity H = 1 - sum(p_i^2) for each locus
///   - Expected H under neutrality: H_exp = 4*N_e*mu / (1 + 4*N_e*mu)
///   - Coalescence time T_c estimated from pairwise genetic distances
///   - Tajima's D-like statistic to detect departure from neutrality
pub struct NeutralTheoryLens;

impl Lens for NeutralTheoryLens {
    fn name(&self) -> &str {
        "NeutralTheoryLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d == 0 {
            return HashMap::new();
        }

        let n_alleles = d.min(6);

        // Treat each dimension as a "locus" and compute allele frequencies
        // Normalize values to [0,1] range per dimension to interpret as frequencies
        let mut col_min = vec![f64::INFINITY; n_alleles];
        let mut col_max = vec![f64::NEG_INFINITY; n_alleles];
        for i in 0..n {
            for j in 0..n_alleles {
                let v = data[i * d + j];
                if v < col_min[j] { col_min[j] = v; }
                if v > col_max[j] { col_max[j] = v; }
            }
        }

        // Bin values into 6 allele classes per locus, compute frequencies
        let n_bins = 6usize;
        let mut heterozygosities = Vec::with_capacity(n_alleles);
        for j in 0..n_alleles {
            let range = col_max[j] - col_min[j];
            if range <= 0.0 {
                heterozygosities.push(0.0);
                continue;
            }
            let mut counts = vec![0usize; n_bins];
            for i in 0..n {
                let v = data[i * d + j];
                let bin = (((v - col_min[j]) / range) * (n_bins as f64 - 1.0)).round() as usize;
                counts[bin.min(n_bins - 1)] += 1;
            }
            let freqs: Vec<f64> = counts.iter().map(|&c| c as f64 / n as f64).collect();
            let homozygosity: f64 = freqs.iter().map(|p| p * p).sum();
            heterozygosities.push(1.0 - homozygosity);
        }

        let mean_heterozygosity = heterozygosities.iter().sum::<f64>() / n_alleles as f64;

        // Pairwise genetic distance (Euclidean) for coalescence time estimate
        let mut total_dist = 0.0;
        let mut pair_count = 0usize;
        let max_pairs = 500; // cap for performance
        for i in 0..n {
            for j in (i + 1)..n {
                if pair_count >= max_pairs { break; }
                total_dist += shared.dist(i, j);
                pair_count += 1;
            }
            if pair_count >= max_pairs { break; }
        }
        let mean_pairwise_dist = if pair_count > 0 { total_dist / pair_count as f64 } else { 0.0 };

        // Coalescence time estimate: T_c ~ mean_pairwise_dist / (2 * mutation_rate)
        // Use H to estimate theta = 4*N_e*mu, then T_c = 2*N_e = theta / (2*mu)
        // theta_hat from H: theta = H / (1 - H)
        let theta = if mean_heterozygosity < 1.0 {
            mean_heterozygosity / (1.0 - mean_heterozygosity)
        } else {
            f64::INFINITY
        };

        // Tajima's D analog: compare mean pairwise distance to number of segregating sites
        // Segregating sites = dimensions with heterozygosity > 0
        let seg_sites = heterozygosities.iter().filter(|&&h| h > 0.1).count();
        let theta_pi = mean_pairwise_dist; // pi estimator
        let theta_w = if seg_sites > 0 {
            // Watterson estimator analog
            let harmonic: f64 = (1..n).map(|k| 1.0 / k as f64).sum();
            seg_sites as f64 / harmonic
        } else {
            0.0
        };
        let tajima_d_analog = theta_pi - theta_w;

        let mut result = HashMap::new();
        result.insert("mean_heterozygosity".into(), vec![mean_heterozygosity]);
        result.insert("theta_diversity".into(), vec![theta]);
        result.insert("mean_pairwise_distance".into(), vec![mean_pairwise_dist]);
        result.insert("segregating_sites".into(), vec![seg_sites as f64]);
        result.insert("tajima_d_analog".into(), vec![tajima_d_analog]);
        result.insert("coalescence_theta".into(), vec![theta]);
        result.insert("score".to_string(), vec![result["mean_heterozygosity"][0].min(1.0).max(0.0)]);
        result
    }
}
