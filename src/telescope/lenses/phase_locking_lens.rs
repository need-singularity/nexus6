use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// PhaseLockingLens: Phase coherence in a 6-oscillator system.
///
/// Models neural oscillator synchronization (Kuramoto-like):
///   - 6 oscillators with phases extracted from data dimensions
///   - Phase Locking Value (PLV) = |mean(exp(i * delta_phase))|
///   - Kuramoto order parameter R = |1/N * sum(exp(i * theta_k))|
///   - Mean phase coherence across all oscillator pairs
///   - Synchronization index and frequency of dominant mode
pub struct PhaseLockingLens;

impl Lens for PhaseLockingLens {
    fn name(&self) -> &str {
        "PhaseLockingLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_osc = d.min(6);

        // Extract phases: map data values to [0, 2*pi) via atan2 or normalization
        // Use the Hilbert-transform analog: phase = 2*pi * (x - min) / (max - min)
        let pi2 = 2.0 * std::f64::consts::PI;

        let mut col_min = vec![f64::INFINITY; n_osc];
        let mut col_max = vec![f64::NEG_INFINITY; n_osc];
        for i in 0..n {
            for j in 0..n_osc {
                let v = data[i * d + j];
                if v < col_min[j] { col_min[j] = v; }
                if v > col_max[j] { col_max[j] = v; }
            }
        }

        // phases[i][j] = phase of oscillator j at time i
        let phases: Vec<Vec<f64>> = (0..n)
            .map(|i| {
                (0..n_osc)
                    .map(|j| {
                        let range = col_max[j] - col_min[j];
                        if range > 0.0 {
                            pi2 * (data[i * d + j] - col_min[j]) / range
                        } else {
                            0.0
                        }
                    })
                    .collect()
            })
            .collect();

        // Kuramoto order parameter per time step: R(t) = |1/N * sum(exp(i*theta_k))|
        let mut order_params = Vec::with_capacity(n);
        for i in 0..n {
            let mut re = 0.0f64;
            let mut im = 0.0f64;
            for j in 0..n_osc {
                re += phases[i][j].cos();
                im += phases[i][j].sin();
            }
            re /= n_osc as f64;
            im /= n_osc as f64;
            order_params.push((re * re + im * im).sqrt());
        }

        let mean_order = order_params.iter().sum::<f64>() / n as f64;

        // Phase Locking Value (PLV) between all oscillator pairs
        let mut plv_sum = 0.0f64;
        let mut pair_count = 0usize;
        for j1 in 0..n_osc {
            for j2 in (j1 + 1)..n_osc {
                let mut re = 0.0f64;
                let mut im = 0.0f64;
                for i in 0..n {
                    let delta = phases[i][j1] - phases[i][j2];
                    re += delta.cos();
                    im += delta.sin();
                }
                re /= n as f64;
                im /= n as f64;
                plv_sum += (re * re + im * im).sqrt();
                pair_count += 1;
            }
        }
        let mean_plv = if pair_count > 0 { plv_sum / pair_count as f64 } else { 0.0 };

        // Synchronization index: variance of order parameter (low = stable sync)
        let order_var = order_params
            .iter()
            .map(|r| (r - mean_order).powi(2))
            .sum::<f64>()
            / n as f64;
        let sync_stability = if order_var > 0.0 { 1.0 / (1.0 + order_var) } else { 1.0 };

        // Mean phase velocity per oscillator (frequency proxy)
        let mut mean_freq = Vec::with_capacity(n_osc);
        for j in 0..n_osc {
            if n < 2 {
                mean_freq.push(0.0);
                continue;
            }
            let mut freq_sum = 0.0f64;
            for i in 1..n {
                let mut dphi = phases[i][j] - phases[i - 1][j];
                // Wrap to [-pi, pi]
                while dphi > std::f64::consts::PI { dphi -= pi2; }
                while dphi < -std::f64::consts::PI { dphi += pi2; }
                freq_sum += dphi.abs();
            }
            mean_freq.push(freq_sum / (n - 1) as f64);
        }
        let dominant_freq = mean_freq.iter().cloned().fold(0.0f64, f64::max);

        let mut result = HashMap::new();
        result.insert("kuramoto_order_parameter".into(), vec![mean_order]);
        result.insert("mean_plv".into(), vec![mean_plv]);
        result.insert("sync_stability".into(), vec![sync_stability]);
        result.insert("dominant_frequency".into(), vec![dominant_freq]);
        result.insert("n_oscillators".into(), vec![n_osc as f64]);
        result
    }
}
