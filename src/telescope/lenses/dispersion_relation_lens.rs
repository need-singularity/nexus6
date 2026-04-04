use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// DispersionRelationLens: QFT pole residue and Kramers-Kronig analysis.
///
/// Treats the first dimension as "frequency" (ω) and computes the spectral
/// function ρ(ω) = Im G(ω) from the data. Identifies pole structures
/// (particle masses) and checks Kramers-Kronig consistency:
///   Re G(ω) = P.V. ∫ Im G(ω')/（ω'-ω) dω'/π
///
/// Poles in the spectral function correspond to particle-like excitations.
///
/// Metrics:
///   1. pole_count: number of spectral poles (peaks in ρ(ω))
///   2. pole_residues: residue (strength) at each pole
///   3. kramers_kronig_error: deviation from KK consistency
///   4. spectral_weight: total spectral weight ∫ρ(ω)dω
///   5. dispersion_slope: ω(k) relation slope (group velocity)
///
/// n=6: 6-point correlation function poles, 6-particle threshold.
pub struct DispersionRelationLens;

impl Lens for DispersionRelationLens {
    fn name(&self) -> &str { "DispersionRelationLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // Sort by first column ("frequency" axis)
        let mut freq_idx: Vec<usize> = (0..n).collect();
        freq_idx.sort_by(|&a, &b|
            columns[0][a].partial_cmp(&columns[0][b]).unwrap_or(std::cmp::Ordering::Equal)
        );

        let omega: Vec<f64> = freq_idx.iter().map(|&i| columns[0][i]).collect();
        // "Spectral function" = magnitude of response in remaining dimensions
        let rho: Vec<f64> = freq_idx.iter().map(|&i| {
            let mut mag_sq = 0.0f64;
            for dim in 1..d {
                mag_sq += columns[dim][i] * columns[dim][i];
            }
            mag_sq.sqrt()
        }).collect();

        // Find poles: local maxima in ρ(ω) that exceed mean + σ
        let rho_mean = rho.iter().sum::<f64>() / n as f64;
        let rho_var = rho.iter().map(|&r| (r - rho_mean).powi(2)).sum::<f64>() / n as f64;
        let rho_std = rho_var.sqrt();
        let threshold = rho_mean + rho_std;

        let mut poles: Vec<usize> = Vec::new();
        for i in 1..(n - 1) {
            if rho[i] > rho[i - 1] && rho[i] > rho[i + 1] && rho[i] > threshold {
                poles.push(i);
            }
        }

        // Pole residues: height above background × width estimate
        let mut residues = Vec::with_capacity(poles.len());
        for &p in &poles {
            let height = rho[p] - rho_mean;
            // Half-width: distance to nearest half-max
            let half_max = rho_mean + height / 2.0;
            let mut width = 1.0f64;
            let mut left = p;
            while left > 0 && rho[left] > half_max { left -= 1; }
            let mut right = p;
            while right < n - 1 && rho[right] > half_max { right += 1; }
            if right > left {
                width = omega[right] - omega[left];
            }
            // Residue ≈ π × height × half-width (Breit-Wigner)
            residues.push(std::f64::consts::PI * height * width.max(1e-12));
        }

        // Kramers-Kronig consistency check:
        // Re G(ω) should equal P.V. ∫ Im G(ω')/(ω'-ω) dω'/π
        // Approximate with discrete sum
        let n_check = n.min(50);
        let step = (n + n_check - 1) / n_check;
        let mut kk_error = 0.0f64;
        let mut kk_count = 0u32;

        for idx in (0..n).step_by(step) {
            let w = omega[idx];
            // Hilbert transform: P.V. integral
            let mut hilbert = 0.0f64;
            for j in 0..n {
                if j == idx { continue; }
                let dw = omega[j] - w;
                if dw.abs() > 1e-12 {
                    hilbert += rho[j] / dw;
                }
            }
            let dw_step = if n > 1 {
                (omega[n - 1] - omega[0]) / (n - 1) as f64
            } else { 1.0 };
            hilbert *= dw_step / std::f64::consts::PI;

            // Compare with actual "real part" (use dim=1 as proxy)
            let re_actual = columns[1][freq_idx[idx]];
            kk_error += (hilbert - re_actual).abs();
            kk_count += 1;
        }
        let kk_error_mean = if kk_count > 0 {
            kk_error / kk_count as f64
        } else { 0.0 };

        // Normalize KK error
        let (_, rho_vars) = mean_var(&rho, rho.len(), 1);
        let rho_scale = rho_vars[0].sqrt().max(1e-12);
        let kk_normalized = kk_error_mean / rho_scale;

        // Total spectral weight
        let dw = if n > 1 {
            (omega[n - 1] - omega[0]) / (n - 1) as f64
        } else { 1.0 };
        let spectral_weight: f64 = rho.iter().sum::<f64>() * dw.abs();

        // Dispersion slope: ω vs k (use dim 1 as wavevector)
        // Linear regression ω = v·k + c
        let k_vals: Vec<f64> = freq_idx.iter().map(|&i| columns[1][i]).collect();
        let k_mean = k_vals.iter().sum::<f64>() / n as f64;
        let w_mean = omega.iter().sum::<f64>() / n as f64;
        let mut cov_wk = 0.0f64;
        let mut var_k = 0.0f64;
        for i in 0..n {
            cov_wk += (omega[i] - w_mean) * (k_vals[i] - k_mean);
            var_k += (k_vals[i] - k_mean).powi(2);
        }
        let slope = if var_k > 1e-12 { cov_wk / var_k } else { 0.0 };

        let mut result = HashMap::new();
        result.insert("pole_count".to_string(), vec![poles.len() as f64]);
        result.insert("pole_residues".to_string(), residues);
        result.insert("kramers_kronig_error".to_string(), vec![kk_normalized]);
        result.insert("spectral_weight".to_string(), vec![spectral_weight]);
        result.insert("dispersion_slope".to_string(), vec![slope]);
        result.insert("score".to_string(), vec![result["pole_count"][0].min(1.0).max(0.0)]);
        result
    }
}
