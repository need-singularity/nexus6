use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// PopulationVectorLens: Georgopoulos-style population vector decoding.
///
/// Models neural population coding in 6-dimensional motor space:
///   - Each data point = neural ensemble activity for a movement direction
///   - 6 neurons with preferred directions uniformly tiling the space
///   - Population vector = weighted sum of preferred directions by firing rates
///   - Decoding accuracy = cos(angle between true and decoded direction)
///   - Bootstrap estimate of decoding precision
pub struct PopulationVectorLens;

impl Lens for PopulationVectorLens {
    fn name(&self) -> &str {
        "PopulationVectorLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_dim = d.min(6);

        // Define 6 preferred direction vectors (uniformly spaced unit vectors)
        // Use simplex-like directions in n_dim space
        let mut pref_dirs: Vec<Vec<f64>> = Vec::with_capacity(n_dim);
        for k in 0..n_dim {
            let mut dir = vec![0.0f64; n_dim];
            dir[k] = 1.0;
            pref_dirs.push(dir);
        }

        // For each data point (treated as a stimulus direction + noise):
        // 1. True direction = normalized data vector
        // 2. Firing rates = cosine tuning: r_k = max(0, cos(angle(stimulus, pref_k))) + baseline
        // 3. Population vector = sum(r_k * pref_k)
        // 4. Accuracy = cosine similarity between true and decoded

        let mut accuracies = Vec::with_capacity(n);
        let mut decoded_magnitudes = Vec::with_capacity(n);

        for i in 0..n {
            let stimulus: Vec<f64> = (0..n_dim).map(|j| data[i * d + j]).collect();
            let stim_norm: f64 = stimulus.iter().map(|v| v * v).sum::<f64>().sqrt();
            if stim_norm < 1e-15 {
                accuracies.push(0.0);
                decoded_magnitudes.push(0.0);
                continue;
            }

            // Cosine tuning: firing rate for each neuron
            let rates: Vec<f64> = pref_dirs
                .iter()
                .map(|pref| {
                    let dot: f64 = stimulus.iter().zip(pref).map(|(s, p)| s * p).sum();
                    let cos_angle = dot / stim_norm; // pref is unit vector
                    (cos_angle + 0.5).max(0.0) // baseline + cosine tuning, rectified
                })
                .collect();

            // Population vector: weighted sum
            let mut pop_vec = vec![0.0f64; n_dim];
            for (k, rate) in rates.iter().enumerate() {
                for j in 0..n_dim {
                    pop_vec[j] += rate * pref_dirs[k][j];
                }
            }

            let pop_norm: f64 = pop_vec.iter().map(|v| v * v).sum::<f64>().sqrt();
            decoded_magnitudes.push(pop_norm);

            if pop_norm < 1e-15 {
                accuracies.push(0.0);
                continue;
            }

            // Cosine similarity between true stimulus and decoded direction
            let cos_sim: f64 = stimulus
                .iter()
                .zip(&pop_vec)
                .map(|(s, p)| s * p)
                .sum::<f64>()
                / (stim_norm * pop_norm);
            accuracies.push(cos_sim);
        }

        let mean_accuracy = accuracies.iter().sum::<f64>() / n as f64;
        let accuracy_var = accuracies
            .iter()
            .map(|a| (a - mean_accuracy).powi(2))
            .sum::<f64>()
            / n as f64;

        let mean_magnitude = decoded_magnitudes.iter().sum::<f64>() / n as f64;

        // Decoding precision: 1 / variance (higher = more precise)
        let precision = if accuracy_var > 0.0 {
            1.0 / accuracy_var
        } else {
            f64::INFINITY
        };

        let mut result = HashMap::new();
        result.insert("mean_decoding_accuracy".into(), vec![mean_accuracy]);
        result.insert("accuracy_variance".into(), vec![accuracy_var]);
        result.insert("decoding_precision".into(), vec![precision.min(1e10)]);
        result.insert("mean_pop_vector_magnitude".into(), vec![mean_magnitude]);
        result.insert("motor_dimensions".into(), vec![n_dim as f64]);
        result
    }
}
