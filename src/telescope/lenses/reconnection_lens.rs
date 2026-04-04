use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// ReconnectionLens: 3D 6-component magnetic reconnection analysis.
///
/// Detects magnetic reconnection events — topological rearrangements of
/// magnetic field lines. In 3D with 6 components (B_x, B_y, B_z, E_x, E_y, E_z),
/// reconnection occurs at X-points where B → 0 and E·B ≠ 0.
///
/// Sweet-Parker reconnection rate: R_SP = 1/√(S) where S = Lundquist number
/// Petschek rate: R_P = π/(8 ln S)
///
/// We identify null points (B ≈ 0), measure reconnection electric field,
/// and compute the reconnection rate from field topology.
///
/// Metrics:
///   1. null_point_count: number of points where |B| → 0
///   2. reconnection_rate: E·B / |B|² at null points
///   3. magnetic_helicity: ∫ A·B dV topological invariant
///   4. current_sheet_thickness: scale of the diffusion region
///   5. lundquist_number: ratio of Alfven to diffusion scales
///
/// n=6: 6 field components (B₃ + E₃), 6-component MHD vector.
pub struct ReconnectionLens;

impl Lens for ReconnectionLens {
    fn name(&self) -> &str { "ReconnectionLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d < 3 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let n_field = d.min(6);

        // Interpret first 3 dims as B-field, next 3 as E-field (or velocity)
        let has_e_field = d >= 6;

        // Compute |B| at each point
        let b_dim = n_field.min(3);
        let mut b_mag: Vec<f64> = Vec::with_capacity(n);
        for i in 0..n {
            let mut b_sq = 0.0f64;
            for c in 0..b_dim {
                b_sq += columns[c][i].powi(2);
            }
            b_mag.push(b_sq.sqrt());
        }

        // Find null points: |B| < threshold
        let b_mean = b_mag.iter().sum::<f64>() / n as f64;
        let b_std = (b_mag.iter().map(|&b| (b - b_mean).powi(2)).sum::<f64>() / n as f64).sqrt();
        let null_threshold = (b_mean - 2.0 * b_std).max(b_mean * 0.1).max(1e-12);

        let null_points: Vec<usize> = (0..n)
            .filter(|&i| b_mag[i] < null_threshold)
            .collect();

        // Reconnection rate: E·B / |B|² near null points
        let mut reconnection_rates = Vec::new();
        if has_e_field {
            for &i in &null_points {
                let mut e_dot_b = 0.0f64;
                for c in 0..3 {
                    e_dot_b += columns[3 + c][i] * columns[c][i];
                }
                let b_sq = b_mag[i].powi(2).max(1e-12);
                reconnection_rates.push(e_dot_b.abs() / b_sq);
            }
        } else {
            // Without E-field, estimate reconnection from B-field gradient
            for &i in &null_points {
                // Gradient of |B| at null point
                let mut grad_b = 0.0f64;
                let mut count = 0u32;
                for j in 0..n.min(50) {
                    if j == i { continue; }
                    let dist = shared.dist(i, j).max(1e-12);
                    let db = (b_mag[j] - b_mag[i]).abs();
                    grad_b += db / dist;
                    count += 1;
                }
                if count > 0 {
                    reconnection_rates.push(grad_b / count as f64);
                }
            }
        }

        let mean_rate = if !reconnection_rates.is_empty() {
            reconnection_rates.iter().sum::<f64>() / reconnection_rates.len() as f64
        } else {
            0.0
        };

        // Magnetic helicity: H = ∫ A·B dV
        // Since we don't have A directly, use proxy: H ∝ Σ B_i · (∇ × B)_i
        // Approximate curl from neighbors
        let mut helicity = 0.0f64;
        if b_dim >= 3 {
            let max_check = n.min(100);
            for i in 0..max_check {
                // Finite-difference curl using nearest neighbor
                let j = if i + 1 < n { i + 1 } else { 0 };
                // curl B ≈ (B_j - B_i) × r_hat
                let mut curl_b = [0.0f64; 3];
                let mut dr = [0.0f64; 3];
                for c in 0..b_dim {
                    dr[c] = columns[c][j] - columns[c][i];
                }
                // Simplified curl component
                if b_dim >= 3 {
                    curl_b[0] = columns[2][j] - columns[2][i]; // ∂Bz/∂y proxy
                    curl_b[1] = columns[0][j] - columns[0][i]; // ∂Bx/∂z proxy
                    curl_b[2] = columns[1][j] - columns[1][i]; // ∂By/∂x proxy
                }
                // A·B proxy: sum of B·(∇×B)
                for c in 0..b_dim {
                    helicity += columns[c][i] * curl_b[c];
                }
            }
            helicity /= max_check.max(1) as f64;
        }

        // Current sheet thickness: characteristic scale near null points
        let mut sheet_thickness = 0.0f64;
        if !null_points.is_empty() {
            let mut min_dist_sum = 0.0f64;
            for &i in null_points.iter().take(20) {
                let mut min_d = f64::INFINITY;
                for &j in null_points.iter().take(20) {
                    if i == j { continue; }
                    let d = shared.dist(i, j);
                    if d < min_d { min_d = d; }
                }
                if min_d < f64::INFINITY {
                    min_dist_sum += min_d;
                }
            }
            sheet_thickness = min_dist_sum / null_points.len().min(20) as f64;
        }

        // Lundquist number estimate: S = L × v_A / η
        // v_A = B / √(ρ), η ~ 1/σ, proxy: ratio of system size to dissipation scale
        let (_, vars) = mean_var(data, n, d);
        let system_size = vars.iter().map(|v| v.sqrt()).sum::<f64>() / d as f64;
        let lundquist = if sheet_thickness > 1e-12 {
            system_size / sheet_thickness
        } else {
            1.0
        };

        let mut result = HashMap::new();
        result.insert("null_point_count".to_string(), vec![null_points.len() as f64]);
        result.insert("reconnection_rate".to_string(), vec![mean_rate]);
        result.insert("magnetic_helicity".to_string(), vec![helicity]);
        result.insert("current_sheet_thickness".to_string(), vec![sheet_thickness]);
        result.insert("lundquist_number".to_string(), vec![lundquist]);
        result
    }
}
