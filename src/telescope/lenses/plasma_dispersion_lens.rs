use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// PlasmaDispersionLens: 6-mode coupled plasma dispersion with Landau damping.
///
/// Analyzes plasma-like collective excitations by decomposing data into
/// 6 coupled oscillation modes. Detects Landau damping (collisionless
/// energy transfer from wave to resonant particles) and plasma frequency.
///
/// Plasma dispersion relation: ε(ω,k) = 1 - Σᵢ ωₚᵢ²/(ω² - ωᵢ²) = 0
/// where ωₚᵢ are the plasma frequencies of each mode.
///
/// Landau damping rate: γ = -π ωₚ² / (2k²) · f'(ω/k)
/// where f is the velocity distribution function.
///
/// Metrics:
///   1. plasma_frequencies: ωₚ for each of 6 modes
///   2. landau_damping_rates: damping rate per mode
///   3. debye_length: screening length λ_D
///   4. coupling_matrix: inter-mode coupling strengths
///   5. dielectric_function: ε(ω) evaluated at characteristic frequencies
///
/// n=6: 6 coupled plasma modes (e.g., 3 ion species × 2 polarizations).
pub struct PlasmaDispersionLens;

impl Lens for PlasmaDispersionLens {
    fn name(&self) -> &str { "PlasmaDispersionLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let n_modes: usize = d.min(6);
        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. Plasma frequency per mode: ωₚ² ∝ density × charge² / mass
        // Proxy: variance of each column (kinetic energy ~ kT ~ ω²)
        let plasma_freqs: Vec<f64> = (0..n_modes)
            .map(|m| vars[m].sqrt())
            .collect();

        // 2. Landau damping: analyze velocity distribution slope at resonance
        // f(v) = distribution of values; damping ∝ -df/dv at v = ω/k
        let mut damping_rates = Vec::with_capacity(n_modes);
        for m in 0..n_modes {
            let col = &columns[m];
            let std_dev = vars[m].sqrt().max(1e-12);

            // Sort to get distribution function
            let mut sorted: Vec<f64> = col.clone();
            sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

            // Numerical derivative of CDF at the resonance point (mean)
            // df/dv ≈ Δcount / (n × Δv) near the mean
            let mid = n / 2;
            let window = (n / 10).max(1);
            let v_low = sorted[(mid.saturating_sub(window)).max(0)];
            let v_high = sorted[(mid + window).min(n - 1)];
            let dv = (v_high - v_low).max(1e-12);
            let df_dv = (2 * window) as f64 / (n as f64 * dv);

            // Landau damping: γ ∝ -ωₚ² / k² × f'(v_res)
            // Negative slope at resonance → positive damping
            let damping = std::f64::consts::PI * plasma_freqs[m].powi(2)
                / (2.0 * std_dev * std_dev)
                * df_dv;
            damping_rates.push(damping.abs());
        }

        // 3. Debye length: λ_D = √(ε₀ kT / (n e²)) ∝ std_dev / plasma_freq
        let mean_plasma = plasma_freqs.iter().sum::<f64>() / n_modes as f64;
        let mean_thermal = vars.iter().take(n_modes).sum::<f64>() / n_modes as f64;
        let debye_length = if mean_plasma > 1e-12 {
            mean_thermal.sqrt() / mean_plasma
        } else {
            f64::INFINITY
        };

        // 4. Coupling matrix: cross-correlation between modes
        let mut coupling = Vec::with_capacity(n_modes * n_modes);
        for mi in 0..n_modes {
            for mj in 0..n_modes {
                if mi == mj {
                    coupling.push(1.0);
                    continue;
                }
                let std_i = vars[mi].sqrt().max(1e-12);
                let std_j = vars[mj].sqrt().max(1e-12);
                let mut cov = 0.0f64;
                for row in 0..n {
                    cov += (columns[mi][row] - means[mi]) * (columns[mj][row] - means[mj]);
                }
                cov /= n as f64;
                coupling.push(cov / (std_i * std_j));
            }
        }

        // 5. Dielectric function at 6 characteristic frequencies
        // ε(ω) = 1 - Σ ωₚᵢ² / ω²
        let omega_max = plasma_freqs.iter().cloned().fold(0.0f64, f64::max) * 2.0;
        let mut dielectric = Vec::with_capacity(6);
        for k in 1..=6 {
            let omega = omega_max * k as f64 / 6.0;
            let omega_sq = omega * omega;
            if omega_sq < 1e-12 {
                dielectric.push(f64::NEG_INFINITY);
                continue;
            }
            let mut eps = 1.0f64;
            for &wp in &plasma_freqs {
                eps -= wp * wp / omega_sq;
            }
            dielectric.push(eps);
        }

        let mut result = HashMap::new();
        result.insert("plasma_frequencies".to_string(), plasma_freqs);
        result.insert("landau_damping_rates".to_string(), damping_rates);
        result.insert("debye_length".to_string(), vec![debye_length]);
        result.insert("coupling_matrix".to_string(), coupling);
        result.insert("dielectric_function".to_string(), dielectric);
        result.insert("score".to_string(), vec![result["plasma_frequencies"][0].min(1.0).max(0.0)]);
        result
    }
}
