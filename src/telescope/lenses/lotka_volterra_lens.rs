use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// LotkaVolterraLens: Generalized Lotka-Volterra for a 6-species food web.
///
/// Models ecological dynamics:
///   - 6 species with population sizes from data dimensions
///   - Interaction matrix inferred from pairwise correlations
///   - Community matrix eigenvalue analysis for stability (May's criterion)
///   - Jacobian stability: max real eigenvalue < 0 means stable
///   - Connectance and interaction strength statistics
pub struct LotkaVolterraLens;

impl Lens for LotkaVolterraLens {
    fn name(&self) -> &str {
        "LotkaVolterraLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 {
            return HashMap::new();
        }

        let s = d.min(6); // number of species

        // Extract species abundances (columns)
        let mut means = vec![0.0f64; s];
        let mut vars = vec![0.0f64; s];
        for j in 0..s {
            for i in 0..n {
                means[j] += data[i * d + j];
            }
            means[j] /= n as f64;
        }
        for j in 0..s {
            for i in 0..n {
                vars[j] += (data[i * d + j] - means[j]).powi(2);
            }
            vars[j] /= n as f64;
        }

        // Interaction matrix from temporal correlations (consecutive rows as time series)
        // A[i][j] = correlation between species i growth rate and species j abundance
        let mut interaction = vec![vec![0.0f64; s]; s];
        if n >= 3 {
            // Growth rates: delta_x = x(t+1) - x(t)
            let mut growth_rates: Vec<Vec<f64>> = Vec::with_capacity(n - 1);
            for i in 0..(n - 1) {
                let row: Vec<f64> = (0..s)
                    .map(|j| data[(i + 1) * d + j] - data[i * d + j])
                    .collect();
                growth_rates.push(row);
            }

            // Correlation between growth_rate[species_a] and abundance[species_b]
            let m = growth_rates.len();
            for a in 0..s {
                let gr_mean: f64 = growth_rates.iter().map(|r| r[a]).sum::<f64>() / m as f64;
                let gr_var: f64 = growth_rates.iter().map(|r| (r[a] - gr_mean).powi(2)).sum::<f64>() / m as f64;
                for b in 0..s {
                    let ab_mean: f64 = (0..m).map(|i| data[i * d + b]).sum::<f64>() / m as f64;
                    let ab_var: f64 = (0..m).map(|i| (data[i * d + b] - ab_mean).powi(2)).sum::<f64>() / m as f64;
                    if gr_var > 1e-15 && ab_var > 1e-15 {
                        let cov: f64 = (0..m)
                            .map(|i| (growth_rates[i][a] - gr_mean) * (data[i * d + b] - ab_mean))
                            .sum::<f64>()
                            / m as f64;
                        interaction[a][b] = cov / (gr_var.sqrt() * ab_var.sqrt());
                    }
                }
            }
        }

        // Connectance: fraction of non-negligible interactions
        let threshold = 0.1;
        let mut nonzero = 0;
        let total_off_diag = s * (s - 1);
        for a in 0..s {
            for b in 0..s {
                if a != b && interaction[a][b].abs() > threshold {
                    nonzero += 1;
                }
            }
        }
        let connectance = if total_off_diag > 0 {
            nonzero as f64 / total_off_diag as f64
        } else {
            0.0
        };

        // Mean interaction strength
        let mean_interaction: f64 = if total_off_diag > 0 {
            let mut sum = 0.0f64;
            for a in 0..s {
                for b in 0..s {
                    if a != b {
                        sum += interaction[a][b].abs();
                    }
                }
            }
            sum / total_off_diag as f64
        } else {
            0.0
        };

        // May's stability criterion: sqrt(S * C) * sigma < 1 for stability
        // where S = species count, C = connectance, sigma = std of interaction strengths
        let interaction_var: f64 = if total_off_diag > 0 {
            let mut vals = Vec::with_capacity(total_off_diag);
            for a in 0..s {
                for b in 0..s {
                    if a != b {
                        vals.push(interaction[a][b]);
                    }
                }
            }
            let m = vals.iter().sum::<f64>() / vals.len() as f64;
            vals.iter().map(|v| (v - m).powi(2)).sum::<f64>() / vals.len() as f64
        } else {
            0.0
        };
        let sigma = interaction_var.sqrt();
        let may_criterion = (s as f64 * connectance).sqrt() * sigma;
        let is_stable = may_criterion < 1.0;

        // Approximate max eigenvalue using power iteration on interaction matrix
        let mut v = vec![1.0 / (s as f64).sqrt(); s];
        let mut max_eigen = 0.0f64;
        for _ in 0..50 {
            let mut w = vec![0.0f64; s];
            for a in 0..s {
                for b in 0..s {
                    w[a] += interaction[a][b] * v[b];
                }
            }
            let norm: f64 = w.iter().map(|x| x * x).sum::<f64>().sqrt();
            if norm < 1e-15 { break; }
            max_eigen = w.iter().zip(&v).map(|(wi, vi)| wi * vi).sum(); // Rayleigh quotient
            for x in &mut w { *x /= norm; }
            v = w;
        }

        let mut result = HashMap::new();
        result.insert("connectance".into(), vec![connectance]);
        result.insert("mean_interaction_strength".into(), vec![mean_interaction]);
        result.insert("may_stability_criterion".into(), vec![may_criterion]);
        result.insert("is_stable".into(), vec![if is_stable { 1.0 } else { 0.0 }]);
        result.insert("max_eigenvalue".into(), vec![max_eigen]);
        result.insert("n_species".into(), vec![s as f64]);
        result.insert("score".to_string(), vec![result["connectance"][0].min(1.0).max(0.0)]);
        result
    }
}
