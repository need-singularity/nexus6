use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ConvectionPatternLens: Identify Rayleigh-Bénard and natural/forced convection cell structures.
///
/// Algorithm:
///   1. Compute centroid of all points
///   2. For each point, compute radial vector from centroid and local flow direction
///      (estimated from nearest-neighbor displacement)
///   3. Detect convection cells by measuring local curl (rotation tendency) around each point
///   4. Classify cells: rising (away from center) vs sinking (toward center)
///   5. Compute Rayleigh-Bénard score from regularity of cell spacing
///   6. Measure forced vs natural convection ratio from flow alignment coherence
pub struct UconvectionUpatternLens;

impl Lens for UconvectionUpatternLens {
    fn name(&self) -> &str {
        "convection_pattern"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d < 2 {
            return HashMap::new();
        }

        // 1. Compute centroid
        let mut centroid = vec![0.0f64; d];
        for i in 0..n {
            for dim in 0..d {
                centroid[dim] += data[i * d + dim];
            }
        }
        let inv_n = 1.0 / n as f64;
        for dim in 0..d {
            centroid[dim] *= inv_n;
        }

        // 2. For each point find nearest neighbor and compute displacement vector
        let mut nearest = vec![0usize; n];
        for i in 0..n {
            let mut best_dist = f64::INFINITY;
            let mut best_j = if i == 0 { 1 } else { 0 };
            for j in 0..n {
                if j == i {
                    continue;
                }
                let dist = shared.dist(i, j);
                if dist < best_dist {
                    best_dist = dist;
                    best_j = j;
                }
            }
            nearest[i] = best_j;
        }

        // Flow vector for each point: direction toward nearest neighbor
        let mut flow: Vec<Vec<f64>> = Vec::with_capacity(n);
        for i in 0..n {
            let j = nearest[i];
            let mut fv = vec![0.0; d];
            let mut mag = 0.0;
            for dim in 0..d {
                fv[dim] = data[j * d + dim] - data[i * d + dim];
                mag += fv[dim] * fv[dim];
            }
            mag = mag.sqrt().max(1e-12);
            for dim in 0..d {
                fv[dim] /= mag;
            }
            flow.push(fv);
        }

        // Radial vector for each point (from centroid)
        let mut radial: Vec<Vec<f64>> = Vec::with_capacity(n);
        for i in 0..n {
            let mut rv = vec![0.0; d];
            let mut mag = 0.0;
            for dim in 0..d {
                rv[dim] = data[i * d + dim] - centroid[dim];
                mag += rv[dim] * rv[dim];
            }
            mag = mag.sqrt().max(1e-12);
            for dim in 0..d {
                rv[dim] /= mag;
            }
            radial.push(rv);
        }

        // 3. Local curl estimation (2D cross product of flow with radial)
        // For d>=2, use first two components as the primary plane
        let mut curls = Vec::with_capacity(n);
        for i in 0..n {
            // 2D cross product: radial x flow = rx*fy - ry*fx
            let curl = radial[i][0] * flow[i][1] - radial[i][1] * flow[i][0];
            curls.push(curl);
        }

        // Mean absolute curl = rotation strength
        let mean_abs_curl = curls.iter().map(|c| c.abs()).sum::<f64>() * inv_n;

        // 4. Classify rising vs sinking: dot(flow, radial)
        // Positive = rising (away from center), negative = sinking (toward center)
        let mut rising_count = 0usize;
        let mut sinking_count = 0usize;
        let mut radial_flow_dots = Vec::with_capacity(n);
        for i in 0..n {
            let mut dot = 0.0;
            for dim in 0..d {
                dot += flow[i][dim] * radial[i][dim];
            }
            radial_flow_dots.push(dot);
            if dot > 0.0 {
                rising_count += 1;
            } else {
                sinking_count += 1;
            }
        }

        // 5. Rayleigh-Bénard score: measures regularity of alternating rising/sinking cells
        // Sort points by angle from centroid (in first 2 dims), check alternation pattern
        let mut angles: Vec<(f64, f64)> = Vec::with_capacity(n);
        for i in 0..n {
            let dx = data[i * d] - centroid[0];
            let dy = data[i * d + 1] - centroid[1];
            let angle = dy.atan2(dx);
            angles.push((angle, radial_flow_dots[i]));
        }
        angles.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

        // Count sign alternations (higher = more cell-like structure)
        let mut alternations = 0usize;
        for i in 1..angles.len() {
            if angles[i].1 * angles[i - 1].1 < 0.0 {
                alternations += 1;
            }
        }
        // Normalize: perfect alternation would give n-1 alternations
        let rayleigh_benard_score = if n > 1 {
            alternations as f64 / (n - 1) as f64
        } else {
            0.0
        };

        // 6. Convection cell count estimate: alternations / 2 (each cell has one rise + one sink)
        let estimated_cells = ((alternations + 1) / 2).max(1);

        // 7. Forced vs natural convection ratio
        // Natural convection: flow aligns with radial (buoyancy-driven)
        // Forced convection: flow is more uniform/coherent across points
        // Measure flow alignment coherence (mean pairwise flow dot product)
        let mut flow_coherence = 0.0;
        let mut pair_count = 0usize;
        let max_pairs = n.min(50); // cap for performance
        for i in 0..max_pairs {
            for j in (i + 1)..max_pairs.min(n) {
                let mut dot = 0.0;
                for dim in 0..d {
                    dot += flow[i][dim] * flow[j][dim];
                }
                flow_coherence += dot;
                pair_count += 1;
            }
        }
        if pair_count > 0 {
            flow_coherence /= pair_count as f64;
        }

        // High coherence → forced convection; low coherence → natural convection
        let forced_ratio = (flow_coherence + 1.0) / 2.0; // map [-1, 1] → [0, 1]

        // 8. Cell spacing regularity via distance variance between adjacent sign-change points
        let mut cell_boundary_dists = Vec::new();
        for i in 1..angles.len() {
            if angles[i].1 * angles[i - 1].1 < 0.0 {
                let da = angles[i].0 - angles[i - 1].0;
                cell_boundary_dists.push(da.abs());
            }
        }
        let spacing_regularity = if cell_boundary_dists.len() >= 2 {
            let mean_sp = cell_boundary_dists.iter().sum::<f64>()
                / cell_boundary_dists.len() as f64;
            let var_sp = cell_boundary_dists
                .iter()
                .map(|x| (x - mean_sp) * (x - mean_sp))
                .sum::<f64>()
                / cell_boundary_dists.len() as f64;
            // Low variance relative to mean = regular spacing
            1.0 / (1.0 + var_sp / (mean_sp * mean_sp + 1e-12))
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert(
            "rayleigh_benard_score".to_string(),
            vec![rayleigh_benard_score],
        );
        result.insert("mean_abs_curl".to_string(), vec![mean_abs_curl]);
        result.insert(
            "rising_sinking_ratio".to_string(),
            vec![rising_count as f64, sinking_count as f64],
        );
        result.insert("estimated_cells".to_string(), vec![estimated_cells as f64]);
        result.insert("forced_convection_ratio".to_string(), vec![forced_ratio]);
        result.insert("spacing_regularity".to_string(), vec![spacing_regularity]);
        result.insert("flow_coherence".to_string(), vec![flow_coherence]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    /// Test with points arranged to simulate convection cells:
    /// Two clusters at different heights with lateral displacement.
    #[test]
    fn test_convection_circular_cells() {
        let n = 12;
        let d = 2;
        let mut data = Vec::with_capacity(n * d);

        // Create two interleaved groups: one moving outward (high y, spread x)
        // and one moving inward (low y, clustered x) to ensure nearest-neighbor
        // flow creates alternating radial directions.
        for i in 0..n {
            let angle = 2.0 * std::f64::consts::PI * i as f64 / n as f64;
            let r = 2.0 + (i as f64 * 1.1).sin(); // varying radius
            data.push(r * angle.cos());
            data.push(r * angle.sin());
        }

        let shared = SharedData::compute(&data, n, d);
        let lens = UconvectionUpatternLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan() must return non-empty result");
        assert!(
            result.contains_key("rayleigh_benard_score"),
            "must contain rayleigh_benard_score"
        );
        assert!(
            result.contains_key("estimated_cells"),
            "must contain estimated_cells"
        );
        assert!(
            result.contains_key("mean_abs_curl"),
            "must contain mean_abs_curl"
        );
        assert!(
            result.contains_key("flow_coherence"),
            "must contain flow_coherence"
        );
        assert!(
            result.contains_key("rising_sinking_ratio"),
            "must contain rising_sinking_ratio"
        );

        let rb = result["rayleigh_benard_score"][0];
        assert!(rb.is_finite(), "rayleigh_benard_score must be finite, got {rb}");

        let cells = result["estimated_cells"][0];
        assert!(cells >= 1.0, "should detect at least 1 convection cell");

        let curl = result["mean_abs_curl"][0];
        assert!(curl >= 0.0, "mean_abs_curl should be non-negative, got {curl}");
    }

    /// Test with a forced-convection-like pattern: all points flowing in the same direction.
    #[test]
    fn test_forced_convection_coherent_flow() {
        let n = 8;
        let d = 2;
        // Points along a line: flow direction will be highly coherent
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            data.push(i as f64 * 1.0);
            data.push(0.5 * (i as f64 * 0.5).sin()); // slight wave
        }

        let shared = SharedData::compute(&data, n, d);
        let lens = UconvectionUpatternLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan() must return non-empty result");
        assert!(result.contains_key("forced_convection_ratio"));
        assert!(result.contains_key("flow_coherence"));

        let forced = result["forced_convection_ratio"][0];
        assert!(
            forced.is_finite(),
            "forced_convection_ratio must be finite, got {forced}"
        );

        let coherence = result["flow_coherence"][0];
        assert!(
            coherence.is_finite(),
            "flow_coherence must be finite, got {coherence}"
        );
    }
}
