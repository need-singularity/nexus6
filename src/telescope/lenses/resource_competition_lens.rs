use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ResourceCompetitionLens: Tilman's R* resource competition theory.
///
/// Models 6 essential resources competed for by species:
///   - R* = minimum resource level for persistence (break-even concentration)
///   - Species with lowest R* wins competition for that resource
///   - Niche overlap from resource utilization spectra
///   - Competitive exclusion vs coexistence analysis
///   - Limiting similarity threshold
pub struct ResourceCompetitionLens;

impl Lens for ResourceCompetitionLens {
    fn name(&self) -> &str {
        "ResourceCompetitionLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_resources = d.min(6);

        // Treat each data point as a species, each dimension as resource requirement
        // R*_ij = minimum resource j needed by species i (from data values)
        // Lower R* = better competitor for that resource

        // Normalize to positive values (resource concentrations must be >= 0)
        let mut col_min = vec![f64::INFINITY; n_resources];
        for i in 0..n {
            for j in 0..n_resources {
                let v = data[i * d + j];
                if v < col_min[j] { col_min[j] = v; }
            }
        }

        // R* matrix: shifted so minimum is near 0
        let r_star: Vec<Vec<f64>> = (0..n)
            .map(|i| {
                (0..n_resources)
                    .map(|j| (data[i * d + j] - col_min[j]).max(0.0) + 1e-6)
                    .collect()
            })
            .collect();

        // For each resource, find the winner (lowest R*)
        let mut winners = vec![0usize; n_resources];
        for j in 0..n_resources {
            let mut best_i = 0;
            let mut best_r = f64::INFINITY;
            for i in 0..n {
                if r_star[i][j] < best_r {
                    best_r = r_star[i][j];
                    best_i = i;
                }
            }
            winners[j] = best_i;
        }

        // Number of distinct winners (potential coexisting species)
        let mut unique_winners: Vec<usize> = winners.clone();
        unique_winners.sort();
        unique_winners.dedup();
        let coexistence_count = unique_winners.len();

        // Niche overlap: cosine similarity of resource utilization vectors
        let mut overlap_sum = 0.0f64;
        let mut overlap_count = 0usize;
        let max_pairs = 500;
        for i in 0..n {
            for k in (i + 1)..n {
                if overlap_count >= max_pairs { break; }
                let dot: f64 = (0..n_resources).map(|j| r_star[i][j] * r_star[k][j]).sum();
                let norm_i: f64 = (0..n_resources).map(|j| r_star[i][j].powi(2)).sum::<f64>().sqrt();
                let norm_k: f64 = (0..n_resources).map(|j| r_star[k][j].powi(2)).sum::<f64>().sqrt();
                if norm_i > 1e-10 && norm_k > 1e-10 {
                    overlap_sum += dot / (norm_i * norm_k);
                    overlap_count += 1;
                }
            }
            if overlap_count >= max_pairs { break; }
        }
        let mean_niche_overlap = if overlap_count > 0 {
            overlap_sum / overlap_count as f64
        } else {
            0.0
        };

        // Competitive exclusion ratio: how many species are excluded
        // A species is excluded if it doesn't win any resource
        let winner_set: std::collections::HashSet<usize> = winners.iter().cloned().collect();
        let excluded_count = (0..n).filter(|i| !winner_set.contains(i)).count();
        let exclusion_ratio = excluded_count as f64 / n as f64;

        // Limiting similarity: minimum niche distance between winners
        let mut min_winner_dist = f64::INFINITY;
        for (idx_a, &a) in unique_winners.iter().enumerate() {
            for &b in &unique_winners[(idx_a + 1)..] {
                let dist: f64 = (0..n_resources)
                    .map(|j| (r_star[a][j] - r_star[b][j]).powi(2))
                    .sum::<f64>()
                    .sqrt();
                if dist < min_winner_dist {
                    min_winner_dist = dist;
                }
            }
        }
        if min_winner_dist == f64::INFINITY {
            min_winner_dist = 0.0;
        }

        // Mean R* across all species and resources
        let mean_r_star: f64 = r_star.iter()
            .flat_map(|row| row.iter())
            .sum::<f64>() / (n * n_resources) as f64;

        let mut result = HashMap::new();
        result.insert("coexistence_count".into(), vec![coexistence_count as f64]);
        result.insert("mean_niche_overlap".into(), vec![mean_niche_overlap]);
        result.insert("exclusion_ratio".into(), vec![exclusion_ratio]);
        result.insert("limiting_similarity".into(), vec![min_winner_dist]);
        result.insert("mean_r_star".into(), vec![mean_r_star]);
        result.insert("n_resources".into(), vec![n_resources as f64]);
        result
    }
}
