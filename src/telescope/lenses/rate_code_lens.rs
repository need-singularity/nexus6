use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// RateCodeLens: Neural rate coding with a 6-neuron ensemble.
///
/// Models a population of 6 neurons encoding stimulus information:
///   - Each dimension maps to a neuron's tuning curve center
///   - Firing rates follow a Gaussian tuning model: r = r_max * exp(-(x-pref)^2 / (2*sigma^2))
///   - Fisher information per spike: I_F = sum of (dr/ds)^2 / r for each neuron
///   - Signal-to-noise ratio of the neural population
///   - Fano factor estimation from variance/mean of responses
pub struct RateCodeLens;

impl Lens for RateCodeLens {
    fn name(&self) -> &str {
        "RateCodeLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_neurons = d.min(6);

        // Treat each data point as a stimulus, each dimension as a neuron response
        // Compute tuning curve parameters from data statistics
        let mut means = vec![0.0f64; n_neurons];
        let mut vars = vec![0.0f64; n_neurons];

        for j in 0..n_neurons {
            let col: Vec<f64> = (0..n).map(|i| data[i * d + j]).collect();
            means[j] = col.iter().sum::<f64>() / n as f64;
            vars[j] = col.iter().map(|&v| (v - means[j]).powi(2)).sum::<f64>() / n as f64;
        }

        // Tuning width sigma per neuron (from data variance)
        let sigmas: Vec<f64> = vars.iter().map(|&v| v.sqrt().max(1e-10)).collect();

        // Fisher information per data point:
        // For Poisson spiking with Gaussian tuning, I_F = (dr/ds)^2 / r
        // dr/ds = r * (s - pref) / sigma^2
        // So I_F = r * (s - pref)^2 / sigma^4
        let mut fisher_info_per_point = Vec::with_capacity(n);
        for i in 0..n {
            let mut fi = 0.0;
            for j in 0..n_neurons {
                let s = data[i * d + j];
                let z = (s - means[j]) / sigmas[j];
                let rate = (-0.5 * z * z).exp().max(1e-10); // normalized rate
                let dr_ds = rate * z / sigmas[j]; // derivative
                fi += dr_ds * dr_ds / rate; // Fisher information contribution
            }
            fisher_info_per_point.push(fi);
        }

        let mean_fisher = fisher_info_per_point.iter().sum::<f64>() / n as f64;

        // Population SNR: mean response / std of response
        let global_mean: f64 = means.iter().sum::<f64>() / n_neurons as f64;
        let global_var: f64 = vars.iter().sum::<f64>() / n_neurons as f64;
        let snr = if global_var > 0.0 {
            global_mean.abs() / global_var.sqrt()
        } else {
            0.0
        };

        // Fano factor per neuron: var / mean (Poisson => Fano = 1)
        let fano_factors: Vec<f64> = (0..n_neurons)
            .map(|j| {
                if means[j].abs() > 1e-10 {
                    vars[j] / means[j].abs()
                } else {
                    1.0
                }
            })
            .collect();
        let mean_fano = fano_factors.iter().sum::<f64>() / n_neurons as f64;

        // Information per spike: total Fisher info / total firing rate
        let total_rate: f64 = means.iter().map(|m| m.abs()).sum();
        let info_per_spike = if total_rate > 0.0 {
            mean_fisher / total_rate
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert("mean_fisher_information".into(), vec![mean_fisher]);
        result.insert("population_snr".into(), vec![snr]);
        result.insert("mean_fano_factor".into(), vec![mean_fano]);
        result.insert("info_per_spike".into(), vec![info_per_spike]);
        result.insert("n_neurons".into(), vec![n_neurons as f64]);
        result.insert("score".to_string(), vec![result["mean_fisher_information"][0].min(1.0).max(0.0)]);
        result
    }
}
