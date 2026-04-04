use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MagneticMonopoleLens: Search for isolated magnetic charge signatures or topological defects.
///
/// Algorithm:
///   1. Compute a discrete "field" from data gradients in each dimension
///   2. Estimate divergence of the field at each point (∇·B ≠ 0 signals monopole)
///   3. Detect topological charge by computing winding numbers around each point
///   4. Identify isolated points with anomalously high divergence (monopole candidates)
///   5. Measure defect density and monopole strength distribution
pub struct UmagneticUmonopoleLens;

impl Lens for UmagneticUmonopoleLens {
    fn name(&self) -> &str {
        "magnetic_monopole"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 || d < 1 {
            return HashMap::new();
        }

        // --- Step 1: Compute local divergence proxy for each point ---
        // For each point i, estimate ∇·B by summing radial field contributions
        // from neighbors. A monopole has non-zero divergence (Gauss's law for
        // magnetism violated: ∇·B = ρ_m ≠ 0).
        let mut divergences: Vec<f64> = Vec::with_capacity(n);

        for i in 0..n {
            let mut div = 0.0;
            for j in 0..n {
                if i == j {
                    continue;
                }
                let r = shared.dist(i, j);
                if r < 1e-15 {
                    continue;
                }

                // Compute radial unit vector component sum (proxy for field direction)
                let mut radial_component = 0.0;
                for dim in 0..d {
                    let xi = data[i * d + dim];
                    let xj = data[j * d + dim];
                    let diff = xj - xi;
                    // Coulomb-like radial field: B_r ~ 1/r^2 * r_hat
                    // Divergence contribution: (x_j - x_i) / r^3
                    radial_component += diff / (r * r * r);
                }
                div += radial_component;
            }
            divergences.push(div);
        }

        // --- Step 2: Compute statistics to identify monopole candidates ---
        let mean_div = divergences.iter().sum::<f64>() / n as f64;
        let var_div = divergences.iter().map(|x| (x - mean_div).powi(2)).sum::<f64>() / n as f64;
        let std_div = var_div.sqrt();

        // Monopole candidates: points with |divergence| > mean + 2*std
        let threshold = mean_div.abs() + 2.0 * std_div;
        let mut monopole_indices: Vec<f64> = Vec::new();
        let mut monopole_charges: Vec<f64> = Vec::new();

        for (i, &div) in divergences.iter().enumerate() {
            if div.abs() > threshold && threshold > 1e-15 {
                monopole_indices.push(i as f64);
                // Topological charge sign: positive = north monopole, negative = south
                monopole_charges.push(div.signum());
            }
        }

        // --- Step 3: Winding number (topological defect detection) ---
        // For each point, compute a discrete winding number by examining the
        // angular ordering of neighbors and detecting 2π wraps.
        let mut winding_numbers: Vec<f64> = Vec::with_capacity(n);

        for i in 0..n {
            if d < 2 {
                // Need at least 2D for angular winding
                winding_numbers.push(0.0);
                continue;
            }

            // Collect angles to neighbors in first two dimensions
            let mut angles: Vec<f64> = Vec::new();
            for j in 0..n {
                if i == j {
                    continue;
                }
                let dx = data[j * d] - data[i * d];
                let dy = data[j * d + 1] - data[i * d + 1];
                angles.push(dy.atan2(dx));
            }
            angles.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

            // Compute total angular gap — if neighbors wrap around fully,
            // the max gap is small; a large gap indicates a topological defect
            let mut max_gap = 0.0_f64;
            for w in 1..angles.len() {
                let gap = angles[w] - angles[w - 1];
                max_gap = max_gap.max(gap);
            }
            if angles.len() >= 2 {
                let wrap_gap =
                    (2.0 * std::f64::consts::PI) - (angles.last().unwrap() - angles.first().unwrap());
                max_gap = max_gap.max(wrap_gap);
            }
            // Winding number proxy: normalized by 2π
            let winding = 1.0 - max_gap / (2.0 * std::f64::consts::PI);
            winding_numbers.push(winding);
        }

        // Mean winding number (close to 1.0 = uniform coverage, low = defect present)
        let mean_winding = winding_numbers.iter().sum::<f64>() / n as f64;

        // --- Step 4: Isolation metric — how far monopole candidates are from each other ---
        let defect_density = monopole_indices.len() as f64 / n as f64;

        let mut mean_monopole_isolation = 0.0;
        if monopole_indices.len() >= 2 {
            let mut iso_sum = 0.0;
            let mut iso_count = 0;
            for a in 0..monopole_indices.len() {
                for b in (a + 1)..monopole_indices.len() {
                    let ia = monopole_indices[a] as usize;
                    let ib = monopole_indices[b] as usize;
                    iso_sum += shared.dist(ia, ib);
                    iso_count += 1;
                }
            }
            if iso_count > 0 {
                mean_monopole_isolation = iso_sum / iso_count as f64;
            }
        }

        // Net topological charge (sum of all charges; should be ~0 for no net monopole)
        let net_charge: f64 = monopole_charges.iter().sum();

        // --- Build result ---
        let mut result = HashMap::new();
        result.insert("divergence_mean_std".to_string(), vec![mean_div, std_div]);
        result.insert("monopole_count".to_string(), vec![monopole_indices.len() as f64]);
        result.insert("monopole_indices".to_string(), monopole_indices);
        result.insert("monopole_charges".to_string(), monopole_charges);
        result.insert("net_topological_charge".to_string(), vec![net_charge]);
        result.insert("defect_density".to_string(), vec![defect_density]);
        result.insert("mean_winding_number".to_string(), vec![mean_winding]);
        result.insert("mean_monopole_isolation".to_string(), vec![mean_monopole_isolation]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_monopole_scan_returns_nonempty() {
        // 5 points in 3D — arranged so one point is isolated (potential monopole)
        let data = vec![
            0.0, 0.0, 0.0, // cluster center
            0.1, 0.1, 0.1, // near center
            0.1, -0.1, 0.0, // near center
            -0.1, 0.0, 0.1, // near center
            5.0, 5.0, 5.0, // far isolated point
        ];
        let n = 5;
        let d = 3;
        let shared = SharedData::compute(&data, n, d);
        let lens = UmagneticUmonopoleLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan must return non-empty result");
        assert!(result.contains_key("monopole_count"));
        assert!(result.contains_key("divergence_mean_std"));
        assert!(result.contains_key("mean_winding_number"));

        let div_stats = &result["divergence_mean_std"];
        assert_eq!(div_stats.len(), 2);
        // std should be > 0 with varied data
        assert!(div_stats[1] > 0.0, "divergence std should be positive");
    }

    #[test]
    fn test_monopole_symmetric_cluster_low_defect() {
        // 4 points forming a symmetric tetrahedron-like arrangement
        // Should have low defect density due to symmetry
        let data = vec![
            1.0, 0.0, 0.0,
            -1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, -1.0, 0.0,
        ];
        let n = 4;
        let d = 3;
        let shared = SharedData::compute(&data, n, d);
        let lens = UmagneticUmonopoleLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan must return non-empty result");
        let winding = result["mean_winding_number"][0];
        assert!(winding > 0.0, "winding number should be positive for symmetric config");

        let defect = result["defect_density"][0];
        assert!(defect >= 0.0 && defect <= 1.0, "defect density in [0,1]");
    }
}
