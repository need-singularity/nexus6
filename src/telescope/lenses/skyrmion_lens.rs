use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// SkyrmionLens: Topological soliton with 6-fold anisotropy.
///
/// Detects skyrmion-like topological configurations in data by computing
/// the topological charge (winding number) of the field configuration.
///
/// Skyrmion number: Q = (1/4π) ∫ n · (∂ₓn × ∂ᵧn) dx dy
/// where n is the unit magnetization vector.
///
/// We treat pairs of dimensions as spatial coordinates and remaining
/// dimensions as the order-parameter field, computing the Pontryagin
/// index (topological charge) from the field winding.
///
/// 6-fold anisotropy: the crystal field has C₆ symmetry, stabilizing
/// skyrmion lattices in hexagonal magnets like MnSi.
///
/// Metrics:
///   1. topological_charge: integer winding number Q
///   2. skyrmion_radius: characteristic size of the texture
///   3. anisotropy_strength: 6-fold anisotropy parameter
///   4. helicity: skyrmion helicity angle
///   5. topological_density: local charge density distribution
///
/// n=6: 6-fold crystal anisotropy, 6-component order parameter.
pub struct SkyrmionLens;

impl Lens for SkyrmionLens {
    fn name(&self) -> &str { "SkyrmionLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 3 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // Use first 2 dimensions as spatial (x, y) and next as field components
        // Sort data into a 2D grid-like structure
        let n_field = (d - 2).min(3); // up to 3-component field vector

        // Normalize field vectors to unit sphere
        let mut field: Vec<[f64; 3]> = Vec::with_capacity(n);
        for i in 0..n {
            let mut v = [0.0f64; 3];
            for c in 0..n_field {
                v[c] = columns[2 + c][i];
            }
            let norm = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt().max(1e-12);
            v[0] /= norm;
            v[1] /= norm;
            v[2] /= norm;
            field.push(v);
        }

        // Sort points by spatial coordinates to create approximate grid
        let mut indices: Vec<usize> = (0..n).collect();
        indices.sort_by(|&a, &b| {
            let xa = columns[0][a];
            let xb = columns[0][b];
            xa.partial_cmp(&xb).unwrap_or(std::cmp::Ordering::Equal)
        });

        // Estimate grid size
        let grid_side = (n as f64).sqrt().ceil() as usize;

        // Compute topological charge density at each point
        // Q_i = n · (∂ₓn × ∂ᵧn) / (4π)
        let mut charge_density = Vec::with_capacity(n);
        let mut total_charge = 0.0f64;

        for idx in 0..n.saturating_sub(grid_side + 1) {
            let i = indices[idx];
            // Approximate spatial neighbors
            let i_right = if idx + 1 < n { indices[idx + 1] } else { i };
            let i_up = if idx + grid_side < n { indices[idx + grid_side] } else { i };

            // Partial derivatives: ∂n/∂x, ∂n/∂y
            let mut dnx = [0.0f64; 3];
            let mut dny = [0.0f64; 3];
            for c in 0..3 {
                dnx[c] = field[i_right][c] - field[i][c];
                dny[c] = field[i_up][c] - field[i][c];
            }

            // Cross product: ∂ₓn × ∂ᵧn
            let cross = [
                dnx[1] * dny[2] - dnx[2] * dny[1],
                dnx[2] * dny[0] - dnx[0] * dny[2],
                dnx[0] * dny[1] - dnx[1] * dny[0],
            ];

            // Dot with n: topological charge density
            let q_local = field[i][0] * cross[0]
                + field[i][1] * cross[1]
                + field[i][2] * cross[2];

            charge_density.push(q_local);
            total_charge += q_local;
        }

        // Normalize total charge by 4π
        total_charge /= 4.0 * std::f64::consts::PI;
        // Round to nearest integer (topological invariant)
        let q_integer = total_charge.round();

        // Skyrmion radius: RMS distance of points with significant charge
        let charge_threshold = {
            let max_q = charge_density.iter().map(|q| q.abs()).fold(0.0f64, f64::max);
            max_q * 0.1
        };
        let (means, _vars) = mean_var(data, n, d);
        let mut radius_sum = 0.0f64;
        let mut radius_count = 0u32;
        for (idx, &q) in charge_density.iter().enumerate() {
            if q.abs() > charge_threshold && idx < n {
                let i = indices[idx];
                let dx = columns[0][i] - means[0];
                let dy = columns[1][i] - means[1];
                radius_sum += (dx * dx + dy * dy).sqrt();
                radius_count += 1;
            }
        }
        let skyrmion_radius = if radius_count > 0 {
            radius_sum / radius_count as f64
        } else {
            0.0
        };

        // 6-fold anisotropy: check angular distribution of field in xy-plane
        let n_sectors = 6;
        let mut sector_counts = vec![0u32; n_sectors];
        for i in 0..n {
            let angle = field[i][1].atan2(field[i][0]); // [-π, π]
            let sector = ((angle + std::f64::consts::PI) / (2.0 * std::f64::consts::PI)
                * n_sectors as f64) as usize;
            sector_counts[sector.min(n_sectors - 1)] += 1;
        }
        let mean_count = n as f64 / n_sectors as f64;
        let anisotropy: f64 = sector_counts.iter()
            .map(|&c| (c as f64 - mean_count).powi(2))
            .sum::<f64>() / (mean_count * mean_count * n_sectors as f64);

        // Helicity: average angle of the field relative to radial direction
        let mut helicity_sum = 0.0f64;
        for i in 0..n {
            let rx = columns[0][i] - means[0];
            let ry = columns[1][i] - means[1];
            let r_norm = (rx * rx + ry * ry).sqrt().max(1e-12);
            // Angle between field projection and radial direction
            let cos_h = (field[i][0] * rx + field[i][1] * ry) / r_norm;
            helicity_sum += cos_h.acos();
        }
        let helicity = helicity_sum / n as f64;

        let mut result = HashMap::new();
        result.insert("topological_charge".to_string(), vec![q_integer]);
        result.insert("skyrmion_radius".to_string(), vec![skyrmion_radius]);
        result.insert("anisotropy_strength".to_string(), vec![anisotropy]);
        result.insert("helicity".to_string(), vec![helicity]);
        result.insert("topological_density".to_string(), charge_density);
        result.insert("score".to_string(), vec![result["topological_charge"][0].min(1.0).max(0.0)]);
        result
    }
}
