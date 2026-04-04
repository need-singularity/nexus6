use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// RunningCouplingLens: 6-loop perturbative running coupling analysis.
///
/// Models the QFT beta function β(g) = -b₀g³ - b₁g⁵ - ... - b₅g¹³
/// by treating data variance at different scales as an effective coupling.
/// Detects asymptotic freedom (coupling decreasing at short distances)
/// and infrared slavery (coupling growing at long distances).
///
/// Metrics:
///   1. beta_function: slope of coupling vs scale (negative = asymptotic freedom)
///   2. coupling_at_six_scales: effective coupling measured at 6 scale bins
///   3. asymptotic_freedom_score: how strongly coupling decreases at UV
///   4. landau_pole_proximity: closeness to divergence (Landau pole)
///   5. loop_coefficients: 6 perturbative beta-function coefficients
///
/// n=6: 6-loop perturbative expansion, 6 flavors in QCD.
pub struct RunningCouplingLens;

impl Lens for RunningCouplingLens {
    fn name(&self) -> &str { "RunningCouplingLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, _data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d < 1 { return HashMap::new(); }

        // Collect all pairwise distances to define scale
        let max_check = n.min(200);
        let mut all_dists: Vec<f64> = Vec::with_capacity(max_check * (max_check - 1) / 2);
        for i in 0..max_check {
            for j in (i + 1)..max_check {
                all_dists.push(shared.dist(i, j));
            }
        }
        all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        if all_dists.is_empty() { return HashMap::new(); }

        // Partition distances into 6 scale bins (UV to IR)
        let n_scales: usize = 6;
        let bin_size = all_dists.len() / n_scales;
        if bin_size == 0 { return HashMap::new(); }

        // Effective coupling at each scale: local variance / mean distance
        // This mimics how coupling strength varies with energy scale
        let mut coupling_at_scales = Vec::with_capacity(n_scales);
        let mut scale_centers = Vec::with_capacity(n_scales);

        for s in 0..n_scales {
            let start = s * bin_size;
            let end = if s == n_scales - 1 { all_dists.len() } else { (s + 1) * bin_size };
            let slice = &all_dists[start..end];

            let mean_dist: f64 = slice.iter().sum::<f64>() / slice.len() as f64;
            let var_dist: f64 = slice.iter()
                .map(|&x| (x - mean_dist) * (x - mean_dist))
                .sum::<f64>() / slice.len() as f64;

            // Effective coupling g²(μ) ~ variance / scale²
            let scale = mean_dist.max(1e-12);
            let g_sq = var_dist / (scale * scale);
            coupling_at_scales.push(g_sq);
            scale_centers.push(scale);
        }

        // Beta function: β(g) = dg/d(ln μ) ≈ Δg² / Δ(ln scale)
        let mut beta_values = Vec::with_capacity(n_scales - 1);
        for s in 0..(n_scales - 1) {
            let d_ln_mu = (scale_centers[s + 1] / scale_centers[s].max(1e-12)).ln();
            if d_ln_mu.abs() > 1e-12 {
                let d_g = coupling_at_scales[s + 1] - coupling_at_scales[s];
                beta_values.push(d_g / d_ln_mu);
            }
        }

        // Beta function average slope
        let beta_mean = if !beta_values.is_empty() {
            beta_values.iter().sum::<f64>() / beta_values.len() as f64
        } else {
            0.0
        };

        // Asymptotic freedom score: fraction of scale transitions where coupling decreases
        // toward UV (smaller scales)
        let af_count = beta_values.iter().filter(|&&b| b > 0.0).count();
        let asymptotic_freedom = if !beta_values.is_empty() {
            af_count as f64 / beta_values.len() as f64
        } else {
            0.0
        };

        // Landau pole proximity: max coupling / mean coupling
        let max_coupling = coupling_at_scales.iter().cloned().fold(0.0f64, f64::max);
        let mean_coupling = coupling_at_scales.iter().sum::<f64>() / n_scales as f64;
        let landau_pole = if mean_coupling > 1e-12 {
            max_coupling / mean_coupling
        } else {
            1.0
        };

        // 6-loop perturbative coefficients via polynomial fit
        // β(g) = Σ bₖ g^(2k+1), fit bₖ from measured beta values
        let mut loop_coefficients = vec![0.0f64; 6];
        for (k, coeff) in loop_coefficients.iter_mut().enumerate() {
            if k < coupling_at_scales.len() {
                let g = coupling_at_scales[k].sqrt();
                let power = 2 * k + 3; // g^3, g^5, ..., g^13
                let g_power = g.powi(power as i32);
                if g_power.abs() > 1e-15 && k < beta_values.len() {
                    *coeff = beta_values.get(k).copied().unwrap_or(0.0) / g_power.max(1e-15);
                }
            }
        }

        let mut result = HashMap::new();
        result.insert("beta_function".to_string(), vec![beta_mean]);
        result.insert("coupling_at_six_scales".to_string(), coupling_at_scales);
        result.insert("asymptotic_freedom_score".to_string(), vec![asymptotic_freedom]);
        result.insert("landau_pole_proximity".to_string(), vec![landau_pole]);
        result.insert("loop_coefficients".to_string(), loop_coefficients);
        result.insert("beta_values".to_string(), beta_values);
        result
    }
}
