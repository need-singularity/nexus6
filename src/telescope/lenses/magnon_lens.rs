use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// MagnonLens: 6-sublattice spin wave (magnon) analysis.
///
/// Models spin-wave excitations on a lattice with 6 sublattices.
/// Detects magnon softening (precursor to magnetic phase transition)
/// by analyzing oscillatory patterns and their damping.
///
/// Magnon dispersion: ω(k) = J·S·z·√(1 - γₖ²) where γₖ is the
/// structure factor. Softening occurs when ω → 0 at some k-point.
///
/// We decompose data into 6 sublattice components and analyze:
///   - Spin-wave frequency at each sublattice
///   - Damping rate (magnon lifetime)
///   - Sublattice magnetization
///   - Softening proximity (how close ω is to zero)
///
/// Metrics:
///   1. magnon_frequencies: oscillation frequency per sublattice
///   2. damping_rates: decay rate of spin waves
///   3. sublattice_magnetization: order parameter per sublattice
///   4. softening_proximity: min frequency / mean frequency
///   5. spin_stiffness: d²ω/dk² at zone center
///
/// n=6: 6 magnetic sublattices, 6-fold magnon branches.
pub struct MagnonLens;

impl Lens for MagnonLens {
    fn name(&self) -> &str { "MagnonLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 1 { return HashMap::new(); }

        let n_sublattices: usize = d.min(6);
        let columns = column_vectors(data, n, d);

        let mut magnon_freqs = Vec::with_capacity(n_sublattices);
        let mut damping_rates = Vec::with_capacity(n_sublattices);
        let mut magnetizations = Vec::with_capacity(n_sublattices);

        for sub in 0..n_sublattices {
            let col = &columns[sub];

            // Sublattice magnetization: mean value (order parameter)
            let mean_val = col.iter().sum::<f64>() / n as f64;
            magnetizations.push(mean_val.abs());

            // Estimate oscillation frequency via zero-crossing rate
            let mut zero_crossings = 0u32;
            let centered: Vec<f64> = col.iter().map(|&x| x - mean_val).collect();
            for i in 1..n {
                if centered[i] * centered[i - 1] < 0.0 {
                    zero_crossings += 1;
                }
            }
            // Frequency ~ zero_crossings / (2 * n) normalized
            let freq = zero_crossings as f64 / (2.0 * n as f64);
            magnon_freqs.push(freq);

            // Damping rate: exponential decay of autocorrelation
            // C(τ) = ⟨s(t)s(t+τ)⟩, fit C(τ) ~ e^{-γτ}cos(ωτ)
            let max_lag = (n / 4).max(1);
            let var = centered.iter().map(|x| x * x).sum::<f64>() / n as f64;
            if var < 1e-12 {
                damping_rates.push(0.0);
                continue;
            }

            let mut autocorr = Vec::with_capacity(max_lag);
            for tau in 1..=max_lag {
                let mut ac = 0.0f64;
                let count = n - tau;
                for t in 0..count {
                    ac += centered[t] * centered[t + tau];
                }
                ac /= count.max(1) as f64;
                autocorr.push(ac / var); // normalized autocorrelation
            }

            // Damping: find first time |autocorrelation| drops below 1/e
            let e_inv = (-1.0f64).exp(); // 1/e ≈ 0.368
            let mut damping = 0.0f64;
            for (tau, &ac) in autocorr.iter().enumerate() {
                if ac.abs() < e_inv.abs() {
                    damping = 1.0 / (tau as f64 + 1.0);
                    break;
                }
            }
            if damping == 0.0 && !autocorr.is_empty() {
                damping = 1.0 / max_lag as f64; // slow damping
            }
            damping_rates.push(damping);
        }

        // Softening proximity: how close the minimum frequency is to zero
        let min_freq = magnon_freqs.iter().cloned().fold(f64::INFINITY, f64::min);
        let mean_freq = magnon_freqs.iter().sum::<f64>() / n_sublattices as f64;
        let softening = if mean_freq > 1e-12 {
            min_freq / mean_freq
        } else {
            0.0
        };

        // Spin stiffness: second derivative of dispersion
        // Approximate from autocorrelation curvature at zero lag
        let mut stiffness_vals = Vec::with_capacity(n_sublattices);
        for sub in 0..n_sublattices {
            let col = &columns[sub];
            let mean_val = col.iter().sum::<f64>() / n as f64;
            // Second difference as proxy for d²ω/dk²
            let mut d2_sum = 0.0f64;
            let mut d2_count = 0u32;
            for i in 1..(n - 1) {
                let d2 = (col[i + 1] - mean_val) - 2.0 * (col[i] - mean_val) + (col[i - 1] - mean_val);
                d2_sum += d2.abs();
                d2_count += 1;
            }
            let stiffness = if d2_count > 0 { d2_sum / d2_count as f64 } else { 0.0 };
            stiffness_vals.push(stiffness);
        }

        let mut result = HashMap::new();
        result.insert("magnon_frequencies".to_string(), magnon_freqs);
        result.insert("damping_rates".to_string(), damping_rates);
        result.insert("sublattice_magnetization".to_string(), magnetizations);
        result.insert("softening_proximity".to_string(), vec![softening]);
        result.insert("spin_stiffness".to_string(), stiffness_vals);
        result
    }
}
