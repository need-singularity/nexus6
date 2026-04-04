use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// FaradayInductionLens: Identify time-varying magnetic flux inducing electric response.
///
/// Treats data points as time-ordered samples in d-dimensional space.
/// Models Faraday's law: EMF = -dΦ/dt
///
/// Algorithm:
///   1. Compute "flux" through each consecutive triplet of points (area of triangle
///      formed by points i, i+1, i+2 as proxy for magnetic flux through a loop).
///   2. Compute flux rate of change (dΦ/dt) between consecutive flux values.
///   3. Compute induced EMF magnitude as |dΦ/dt|.
///   4. Detect induction peaks where EMF exceeds mean + 1σ.
///   5. Compute coupling strength: correlation between flux change and distance change.
pub struct UfaradayUinductionLens;

impl Lens for UfaradayUinductionLens {
    fn name(&self) -> &str {
        "faraday_induction"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d < 1 {
            return HashMap::new();
        }

        // Helper: extract point i as a slice
        let point = |i: usize| -> &[f64] {
            &data[i * d..(i + 1) * d]
        };

        // Compute triangle area via cross-product magnitude for 3 points
        // For d dimensions, use the general formula: area = 0.5 * ||(b-a) x (c-a)||
        // In arbitrary dimensions, ||u x v||^2 = ||u||^2 * ||v||^2 - (u·v)^2
        let triangle_area = |a: usize, b: usize, c: usize| -> f64 {
            let pa = point(a);
            let pb = point(b);
            let pc = point(c);

            let mut u_sq = 0.0;
            let mut v_sq = 0.0;
            let mut uv = 0.0;

            for dim in 0..d {
                let u_d = pb[dim] - pa[dim];
                let v_d = pc[dim] - pa[dim];
                u_sq += u_d * u_d;
                v_sq += v_d * v_d;
                uv += u_d * v_d;
            }

            let cross_sq = u_sq * v_sq - uv * uv;
            if cross_sq > 0.0 {
                0.5 * cross_sq.sqrt()
            } else {
                0.0
            }
        };

        // Step 1: Compute flux (triangle area) for each consecutive triplet
        let num_flux = n - 2;
        let mut flux: Vec<f64> = Vec::with_capacity(num_flux);
        for i in 0..num_flux {
            flux.push(triangle_area(i, i + 1, i + 2));
        }

        // Step 2: Compute dΦ/dt (flux rate of change)
        let num_emf = if num_flux > 1 { num_flux - 1 } else { 0 };
        if num_emf == 0 {
            return HashMap::new();
        }

        let mut emf: Vec<f64> = Vec::with_capacity(num_emf);
        for i in 0..num_emf {
            emf.push((flux[i + 1] - flux[i]).abs());
        }

        // Step 3: Statistics on EMF
        let emf_mean = emf.iter().sum::<f64>() / emf.len() as f64;
        let emf_var = emf.iter().map(|e| (e - emf_mean).powi(2)).sum::<f64>() / emf.len() as f64;
        let emf_std = emf_var.sqrt();
        let emf_max = emf.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

        // Step 4: Detect induction peaks (EMF > mean + 1σ)
        let threshold = emf_mean + emf_std;
        let mut peak_indices: Vec<f64> = Vec::new();
        let mut peak_values: Vec<f64> = Vec::new();
        for (i, &e) in emf.iter().enumerate() {
            if e > threshold {
                peak_indices.push(i as f64);
                peak_values.push(e);
            }
        }

        // Step 5: Coupling strength — correlation between |Δflux| and distance change
        // distance change between consecutive points
        let mut dist_changes: Vec<f64> = Vec::with_capacity(num_emf);
        for i in 0..num_emf {
            // Use shared distance matrix for consecutive point pairs
            let d1 = shared.dist(i, i + 1);
            let d2 = shared.dist(i + 1, i + 2);
            dist_changes.push((d2 - d1).abs());
        }

        let dc_mean = dist_changes.iter().sum::<f64>() / dist_changes.len() as f64;

        // Pearson correlation between emf and dist_changes
        let mut cov = 0.0;
        let mut var_emf = 0.0;
        let mut var_dc = 0.0;
        for i in 0..num_emf {
            let de = emf[i] - emf_mean;
            let dd = dist_changes[i] - dc_mean;
            cov += de * dd;
            var_emf += de * de;
            var_dc += dd * dd;
        }
        let denom = (var_emf * var_dc).sqrt();
        let coupling = if denom > 1e-15 { cov / denom } else { 0.0 };

        // Step 6: Total induced energy (sum of EMF^2, analogous to power dissipation)
        let total_energy: f64 = emf.iter().map(|e| e * e).sum();

        let mut result = HashMap::new();
        result.insert("emf_mean".to_string(), vec![emf_mean]);
        result.insert("emf_std".to_string(), vec![emf_std]);
        result.insert("emf_max".to_string(), vec![emf_max]);
        result.insert("peak_count".to_string(), vec![peak_indices.len() as f64]);
        if !peak_indices.is_empty() {
            result.insert("peak_indices".to_string(), peak_indices);
            result.insert("peak_values".to_string(), peak_values);
        }
        result.insert("coupling_strength".to_string(), vec![coupling]);
        result.insert("total_induced_energy".to_string(), vec![total_energy]);
        result.insert("flux_series".to_string(), flux);
        result.insert("emf_series".to_string(), emf);
        result.insert("score".to_string(), vec![result["emf_mean"][0].min(1.0).max(0.0)]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    fn make_shared(data: &[f64], n: usize, d: usize) -> SharedData {
        SharedData::compute(data, n, d)
    }

    #[test]
    fn test_oscillating_signal_produces_induction() {
        // Simulate oscillating 2D trajectory: sine wave produces varying flux
        let n = 20;
        let d = 2;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let t = i as f64 * 0.5;
            data.push(t);
            data.push((t * 1.5).sin() * 3.0);
        }
        let shared = make_shared(&data, n, d);
        let lens = UfaradayUinductionLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan must produce non-empty output");
        assert!(result.contains_key("emf_mean"));
        assert!(result.contains_key("coupling_strength"));
        assert!(result.contains_key("flux_series"));

        let emf_mean = result["emf_mean"][0];
        assert!(emf_mean > 0.0, "oscillating signal should produce nonzero EMF");
    }

    #[test]
    fn test_linear_vs_curved_path() {
        // Linear path: constant flux (zero area triangles along a line) → low EMF
        // Curved path: varying flux → higher EMF
        let n = 10;
        let d = 2;

        // Linear path
        let mut linear_data = Vec::with_capacity(n * d);
        for i in 0..n {
            linear_data.push(i as f64);
            linear_data.push(i as f64 * 2.0);
        }
        let shared_lin = make_shared(&linear_data, n, d);
        let lens = UfaradayUinductionLens;
        let result_lin = lens.scan(&linear_data, n, d, &shared_lin);

        // Curved path (quadratic)
        let mut curved_data = Vec::with_capacity(n * d);
        for i in 0..n {
            let t = i as f64;
            curved_data.push(t);
            curved_data.push(t * t * 0.5);
        }
        let shared_cur = make_shared(&curved_data, n, d);
        let result_cur = lens.scan(&curved_data, n, d, &shared_cur);

        assert!(!result_lin.is_empty());
        assert!(!result_cur.is_empty());

        // Linear path should have near-zero flux (collinear points)
        let lin_energy = result_lin["total_induced_energy"][0];
        let cur_energy = result_cur["total_induced_energy"][0];

        // Linear collinear points produce ~0 triangle area, so near-zero energy
        assert!(
            lin_energy < cur_energy + 1e-6,
            "curved path should have >= induced energy than linear: lin={}, cur={}",
            lin_energy,
            cur_energy
        );
    }
}
