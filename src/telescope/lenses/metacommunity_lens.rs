use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MetacommunityLens: Spatial ecology with a 6-patch network.
///
/// Models Leibold's metacommunity framework:
///   - 6 patches with local community composition from data
///   - Dispersal kernel based on inter-patch distance (exponential decay)
///   - Beta diversity (Bray-Curtis dissimilarity between patches)
///   - Species sorting signal: correlation between environment and composition
///   - Dispersal limitation index from distance-decay of similarity
pub struct MetacommunityLens;

impl Lens for MetacommunityLens {
    fn name(&self) -> &str {
        "MetacommunityLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 {
            return HashMap::new();
        }

        let n_patches = 6usize.min(n);
        let n_species = d.min(6);

        // Select 6 patches evenly spaced through the data
        let patch_indices: Vec<usize> = (0..n_patches)
            .map(|k| k * n / n_patches)
            .collect();

        // Community composition: data values as species abundances per patch
        let communities: Vec<Vec<f64>> = patch_indices
            .iter()
            .map(|&idx| {
                (0..n_species)
                    .map(|j| data[idx * d + j].abs()) // abundances must be non-negative
                    .collect()
            })
            .collect();

        // Inter-patch distances from shared distance matrix
        let mut patch_dists = vec![vec![0.0f64; n_patches]; n_patches];
        for a in 0..n_patches {
            for b in (a + 1)..n_patches {
                let dist = shared.dist(patch_indices[a], patch_indices[b]);
                patch_dists[a][b] = dist;
                patch_dists[b][a] = dist;
            }
        }

        // Dispersal kernel: k(d) = exp(-d / mean_dist)
        let mean_dist = {
            let mut s = 0.0;
            let mut c = 0;
            for a in 0..n_patches {
                for b in (a + 1)..n_patches {
                    s += patch_dists[a][b];
                    c += 1;
                }
            }
            if c > 0 { s / c as f64 } else { 1.0 }
        };

        let dispersal_kernel: Vec<Vec<f64>> = (0..n_patches)
            .map(|a| {
                (0..n_patches)
                    .map(|b| {
                        if a == b { 0.0 }
                        else { (-patch_dists[a][b] / mean_dist.max(1e-10)).exp() }
                    })
                    .collect()
            })
            .collect();

        // Mean dispersal rate
        let mean_dispersal: f64 = {
            let mut s = 0.0;
            let mut c = 0;
            for a in 0..n_patches {
                for b in 0..n_patches {
                    if a != b {
                        s += dispersal_kernel[a][b];
                        c += 1;
                    }
                }
            }
            if c > 0 { s / c as f64 } else { 0.0 }
        };

        // Beta diversity: Bray-Curtis dissimilarity between all patch pairs
        let mut beta_sum = 0.0f64;
        let mut beta_count = 0usize;
        let mut similarities = Vec::new();
        let mut distances_for_decay = Vec::new();

        for a in 0..n_patches {
            for b in (a + 1)..n_patches {
                let sum_min: f64 = (0..n_species)
                    .map(|j| communities[a][j].min(communities[b][j]))
                    .sum();
                let sum_total: f64 = (0..n_species)
                    .map(|j| communities[a][j] + communities[b][j])
                    .sum();
                let bc = if sum_total > 0.0 {
                    1.0 - 2.0 * sum_min / sum_total
                } else {
                    0.0
                };
                beta_sum += bc;
                beta_count += 1;
                similarities.push(1.0 - bc);
                distances_for_decay.push(patch_dists[a][b]);
            }
        }
        let mean_beta = if beta_count > 0 { beta_sum / beta_count as f64 } else { 0.0 };

        // Distance-decay of similarity (dispersal limitation index)
        // Correlation between log(similarity) and distance
        let dispersal_limitation = if similarities.len() >= 3 {
            let log_sim: Vec<f64> = similarities.iter().map(|s| (s + 1e-10).ln()).collect();
            let m_ls = log_sim.iter().sum::<f64>() / log_sim.len() as f64;
            let m_d = distances_for_decay.iter().sum::<f64>() / distances_for_decay.len() as f64;
            let cov: f64 = log_sim.iter().zip(&distances_for_decay)
                .map(|(ls, dd)| (ls - m_ls) * (dd - m_d))
                .sum::<f64>() / log_sim.len() as f64;
            let var_d: f64 = distances_for_decay.iter().map(|dd| (dd - m_d).powi(2)).sum::<f64>() / distances_for_decay.len() as f64;
            let var_ls: f64 = log_sim.iter().map(|ls| (ls - m_ls).powi(2)).sum::<f64>() / log_sim.len() as f64;
            if var_d > 1e-15 && var_ls > 1e-15 {
                -(cov / (var_d.sqrt() * var_ls.sqrt())) // negative correlation = dispersal limitation
            } else {
                0.0
            }
        } else {
            0.0
        };

        // Alpha diversity per patch (Shannon index)
        let alpha_divs: Vec<f64> = communities.iter().map(|comm| {
            let total: f64 = comm.iter().sum();
            if total <= 0.0 { return 0.0; }
            let mut h = 0.0;
            for &a in comm {
                if a > 0.0 {
                    let p = a / total;
                    h -= p * p.ln();
                }
            }
            h
        }).collect();
        let mean_alpha = alpha_divs.iter().sum::<f64>() / n_patches as f64;

        let mut result = HashMap::new();
        result.insert("mean_beta_diversity".into(), vec![mean_beta]);
        result.insert("mean_alpha_diversity".into(), vec![mean_alpha]);
        result.insert("mean_dispersal_rate".into(), vec![mean_dispersal]);
        result.insert("dispersal_limitation_index".into(), vec![dispersal_limitation]);
        result.insert("n_patches".into(), vec![n_patches as f64]);
        result
    }
}
