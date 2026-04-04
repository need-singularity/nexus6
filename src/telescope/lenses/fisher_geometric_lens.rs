use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// FisherGeometricLens: Fisher's geometric model of adaptation.
///
/// Models mutations in a 6-dimensional phenotype space where fitness
/// depends on distance to an optimum. Key predictions:
///   1. Probability a random mutation is beneficial = P_ben
///   2. Mean selection gradient magnitude across population
///   3. Fraction of mutations that overshoot the optimum
///
/// Algorithm:
///   - Treat each data point as an organism in 6-dim phenotype space
///   - Estimate the phenotypic optimum as the population centroid weighted by fitness
///   - Fitness = exp(-||x - optimum||^2 / (2 * n_dim)) (Gaussian fitness landscape)
///   - For random mutation vectors, compute fraction that are beneficial (Fisher's result)
///   - Selection gradient = -grad(fitness) direction, measure alignment with data variation
pub struct FisherGeometricLens;

impl Lens for FisherGeometricLens {
    fn name(&self) -> &str {
        "FisherGeometricLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_dim = d.min(6);

        // Compute centroid (potential optimum)
        let mut centroid = vec![0.0; n_dim];
        for i in 0..n {
            for j in 0..n_dim {
                centroid[j] += data[i * d + j];
            }
        }
        for j in 0..n_dim {
            centroid[j] /= n as f64;
        }

        // Distance of each point to optimum
        let dist_to_opt: Vec<f64> = (0..n)
            .map(|i| {
                let mut s = 0.0;
                for j in 0..n_dim {
                    let diff = data[i * d + j] - centroid[j];
                    s += diff * diff;
                }
                s.sqrt()
            })
            .collect();

        // Gaussian fitness landscape
        let fitness: Vec<f64> = dist_to_opt
            .iter()
            .map(|&r| (-r * r / (2.0 * n_dim as f64)).exp())
            .collect();

        let mean_fitness = fitness.iter().sum::<f64>() / n as f64;

        // Fisher's result: P(beneficial) ~ integral of tail for random mutation
        // For a mutation of size delta at distance r from optimum in n_dim dimensions,
        // P_ben ≈ 1 - Phi(r / delta * sqrt(n_dim)) where Phi is normal CDF
        // We approximate using mean distance and a unit mutation size
        let mean_r = dist_to_opt.iter().sum::<f64>() / n as f64;
        let z = mean_r * (n_dim as f64).sqrt();
        // Approximate normal CDF: Phi(z) ≈ 1/(1 + exp(-1.7 * z))
        let p_beneficial = 1.0 / (1.0 + (1.7 * z).exp());

        // Selection gradient magnitude per point
        // grad(fitness) = fitness * (-x + optimum) / n_dim
        let mut grad_magnitudes = Vec::with_capacity(n);
        for i in 0..n {
            let mut grad_sq = 0.0;
            for j in 0..n_dim {
                let g = fitness[i] * (centroid[j] - data[i * d + j]) / n_dim as f64;
                grad_sq += g * g;
            }
            grad_magnitudes.push(grad_sq.sqrt());
        }
        let mean_grad = grad_magnitudes.iter().sum::<f64>() / n as f64;

        // Overshoot fraction: points that are farther from optimum than twice the mean
        let overshoot_count = dist_to_opt.iter().filter(|&&r| r > 2.0 * mean_r).count();
        let overshoot_frac = overshoot_count as f64 / n as f64;

        let mut result = HashMap::new();
        result.insert("mean_fitness".into(), vec![mean_fitness]);
        result.insert("p_beneficial_mutation".into(), vec![p_beneficial]);
        result.insert("selection_gradient".into(), vec![mean_grad]);
        result.insert("overshoot_fraction".into(), vec![overshoot_frac]);
        result.insert("n_dim".into(), vec![n_dim as f64]);
        result.insert("score".to_string(), vec![result["mean_fitness"][0].min(1.0).max(0.0)]);
        result
    }
}
