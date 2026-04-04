use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// HeatConductionLens: Analyze Fourier-law heat diffusion and thermal gradient patterns.
///
/// Algorithm:
///   1. Treat data values as "temperatures" at spatial points
///   2. Build thermal conductivity graph from pairwise distances
///   3. Compute discrete Laplacian heat flux: q_ij = -k * (T_i - T_j) / d_ij  (Fourier's law)
///   4. Measure net heat flux per point → thermal gradient magnitude
///   5. Simulate one-step diffusion → compute thermal equilibration rate
///   6. Detect thermal clusters (hot/cold regions) via gradient thresholding
pub struct UheatUconductionLens;

impl Lens for UheatUconductionLens {
    fn name(&self) -> &str {
        "heat_conduction"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 {
            return HashMap::new();
        }

        // Assign "temperature" to each point as mean of its feature values
        let temperatures: Vec<f64> = (0..n)
            .map(|i| {
                let row = i * d;
                let sum: f64 = data[row..row + d].iter().sum();
                sum / d as f64
            })
            .collect();

        // Compute thermal conductivity constant k = 1/median_distance
        let pair_count = n * (n - 1) / 2;
        let mut all_dists: Vec<f64> = Vec::with_capacity(pair_count);
        for i in 0..n {
            for j in (i + 1)..n {
                all_dists.push(shared.dist(i, j));
            }
        }
        all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median_dist = all_dists[pair_count / 2].max(1e-12);
        let conductivity = 1.0 / median_dist;

        // Fourier's law heat flux: q_ij = -k * (T_i - T_j) / d_ij
        // Compute net heat flux and gradient magnitude per point
        let mut net_flux: Vec<f64> = vec![0.0; n];
        let mut gradient_mag: Vec<f64> = vec![0.0; n];
        let mut total_flux = 0.0;
        let mut flux_count = 0;

        for i in 0..n {
            for j in (i + 1)..n {
                let dist_ij = shared.dist(i, j);
                if dist_ij < 1e-12 {
                    continue;
                }
                let delta_t = temperatures[i] - temperatures[j];
                let flux = -conductivity * delta_t / dist_ij;

                net_flux[i] += flux;
                net_flux[j] -= flux;
                gradient_mag[i] += (delta_t / dist_ij).abs();
                gradient_mag[j] += (delta_t / dist_ij).abs();
                total_flux += flux.abs();
                flux_count += 1;
            }
        }

        // Normalize gradient magnitudes
        for i in 0..n {
            let neighbors = if n > 1 { n - 1 } else { 1 };
            gradient_mag[i] /= neighbors as f64;
        }

        let mean_flux = if flux_count > 0 {
            total_flux / flux_count as f64
        } else {
            0.0
        };

        // One-step diffusion simulation: T_new = T_old + dt * Laplacian(T)
        // Discrete Laplacian for point i: sum_j [ (T_j - T_i) / d_ij^2 ]
        let dt = 0.01;
        let mut laplacian: Vec<f64> = vec![0.0; n];
        for i in 0..n {
            for j in 0..n {
                if i == j {
                    continue;
                }
                let dist_ij = shared.dist(i, j);
                let d_sq = dist_ij * dist_ij;
                if d_sq < 1e-24 {
                    continue;
                }
                laplacian[i] += (temperatures[j] - temperatures[i]) / d_sq;
            }
        }

        let t_new: Vec<f64> = (0..n)
            .map(|i| temperatures[i] + dt * conductivity * laplacian[i])
            .collect();

        // Thermal equilibration rate: how much variance decreased after one step
        let mean_t: f64 = temperatures.iter().sum::<f64>() / n as f64;
        let var_before: f64 =
            temperatures.iter().map(|t| (t - mean_t).powi(2)).sum::<f64>() / n as f64;
        let mean_t_new: f64 = t_new.iter().sum::<f64>() / n as f64;
        let var_after: f64 =
            t_new.iter().map(|t| (t - mean_t_new).powi(2)).sum::<f64>() / n as f64;
        let equilibration_rate = if var_before > 1e-12 {
            (var_before - var_after) / var_before
        } else {
            0.0
        };

        // Thermal cluster detection: classify points as hot/cold/neutral
        let t_std = var_before.sqrt().max(1e-12);
        let mut hot_count = 0usize;
        let mut cold_count = 0usize;
        for &t in &temperatures {
            if t > mean_t + t_std {
                hot_count += 1;
            } else if t < mean_t - t_std {
                cold_count += 1;
            }
        }

        // Thermal gradient entropy: how uniformly distributed are gradients?
        let grad_sum: f64 = gradient_mag.iter().sum::<f64>();
        let gradient_entropy = if grad_sum > 1e-12 {
            let mut entropy = 0.0;
            for &g in &gradient_mag {
                let p = g / grad_sum;
                if p > 1e-12 {
                    entropy -= p * p.ln();
                }
            }
            entropy
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert("mean_heat_flux".to_string(), vec![mean_flux]);
        result.insert("conductivity".to_string(), vec![conductivity]);
        result.insert("equilibration_rate".to_string(), vec![equilibration_rate]);
        result.insert(
            "thermal_variance".to_string(),
            vec![var_before, var_after],
        );
        result.insert(
            "thermal_clusters".to_string(),
            vec![hot_count as f64, cold_count as f64],
        );
        result.insert("gradient_entropy".to_string(), vec![gradient_entropy]);
        result.insert("gradient_magnitudes".to_string(), gradient_mag);
        result.insert("net_flux".to_string(), net_flux);
        result.insert("score".to_string(), vec![result["mean_heat_flux"][0].min(1.0).max(0.0)]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_heat_conduction_non_empty() {
        // 4 points in 2D with clear temperature gradient
        let data = vec![
            0.0, 0.0, // cold point
            1.0, 0.0, // warm
            2.0, 0.0, // warmer
            3.0, 3.0, // hot point
        ];
        let sd = SharedData::compute(&data, 4, 2);
        let lens = UheatUconductionLens;
        let result = lens.scan(&data, 4, 2, &sd);

        assert!(!result.is_empty(), "scan result should not be empty");
        assert!(result.contains_key("mean_heat_flux"));
        assert!(result.contains_key("conductivity"));
        assert!(result.contains_key("equilibration_rate"));
        assert!(result.contains_key("gradient_magnitudes"));

        let flux = result["mean_heat_flux"][0];
        assert!(flux > 0.0, "heat flux should be positive for non-uniform data");

        let grad = &result["gradient_magnitudes"];
        assert_eq!(grad.len(), 4);
        assert!(grad.iter().any(|&g| g > 0.0), "should have nonzero gradients");
    }

    #[test]
    fn test_heat_conduction_equilibration() {
        // Points with identical "temperatures" should have near-zero flux
        let data = vec![
            1.0, 1.0,
            1.0, 1.0,
            1.0, 1.0,
        ];
        let sd = SharedData::compute(&data, 3, 2);
        let lens = UheatUconductionLens;
        let result = lens.scan(&data, 3, 2, &sd);

        assert!(!result.is_empty());
        let flux = result["mean_heat_flux"][0];
        assert!(
            flux < 1e-6,
            "uniform temperature should yield near-zero flux, got {flux}"
        );

        let eq_rate = result["equilibration_rate"][0];
        assert!(
            eq_rate.abs() < 1e-6,
            "no variance to equilibrate, got {eq_rate}"
        );
    }
}
