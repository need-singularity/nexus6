use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// SuperconductorLensLens: Detect zero-resistance phase transitions and Meissner-effect signatures.
///
/// Algorithm:
///   1. Resistance proxy: for each point, compute mean distance to neighbors.
///      A sudden drop in local connectivity distance signals a "zero-resistance" phase.
///   2. Critical temperature (Tc) detection: sort points by their "energy" (L2 norm),
///      compute resistance proxy vs energy, and find the steepest drop — the phase transition.
///   3. Meissner effect: in the superconducting phase (below Tc), measure how strongly
///      points expel variation — low variance of inter-point distances indicates
///      flux expulsion (analogous to magnetic field exclusion).
///   4. Cooper pair coherence: detect pairs of points with anomalously small distances
///      relative to the bulk, analogous to Cooper pair formation.
pub struct UsuperconductorUlensLens;

impl Lens for UsuperconductorUlensLens {
    fn name(&self) -> &str {
        "superconductor_lens"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 {
            return HashMap::new();
        }

        // --- 1. Compute "energy" (L2 norm) per point and sort ---
        let mut energies: Vec<(usize, f64)> = (0..n)
            .map(|i| {
                let row = &data[i * d..(i + 1) * d];
                let norm = row.iter().map(|x| x * x).sum::<f64>().sqrt();
                (i, norm)
            })
            .collect();
        energies.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));

        // --- 2. Resistance proxy: mean distance from each point to all others ---
        let mut resistance: Vec<f64> = vec![0.0; n];
        for i in 0..n {
            let mut sum = 0.0;
            for j in 0..n {
                if i != j {
                    sum += shared.dist(i, j);
                }
            }
            resistance[i] = sum / (n - 1) as f64;
        }

        // Resistance ordered by energy
        let ordered_resistance: Vec<f64> = energies.iter().map(|&(idx, _)| resistance[idx]).collect();

        // --- 3. Find critical transition: largest drop in resistance ---
        let mut max_drop = 0.0f64;
        let mut tc_index = 0usize;
        for i in 1..n {
            let drop = ordered_resistance[i - 1] - ordered_resistance[i];
            if drop > max_drop {
                max_drop = drop;
                tc_index = i;
            }
        }

        let tc_energy = energies[tc_index].1;
        let tc_fraction = tc_index as f64 / n as f64; // fraction of points below Tc

        // --- 4. Meissner effect: variance of distances in superconducting phase ---
        let sc_indices: Vec<usize> = energies[..tc_index.max(1)]
            .iter()
            .map(|&(idx, _)| idx)
            .collect();

        let meissner_score = if sc_indices.len() >= 2 {
            let mut sc_dists: Vec<f64> = Vec::new();
            for i in 0..sc_indices.len() {
                for j in (i + 1)..sc_indices.len() {
                    sc_dists.push(shared.dist(sc_indices[i], sc_indices[j]));
                }
            }
            let mean = sc_dists.iter().sum::<f64>() / sc_dists.len() as f64;
            let var = sc_dists
                .iter()
                .map(|x| (x - mean) * (x - mean))
                .sum::<f64>()
                / sc_dists.len() as f64;
            // Low variance = strong Meissner effect; normalize by mean^2
            if mean > 1e-12 {
                1.0 - (var.sqrt() / mean).min(1.0)
            } else {
                1.0
            }
        } else {
            0.0
        };

        // --- 5. Cooper pair detection: find pairs with anomalously small distances ---
        let mut all_dists: Vec<f64> = Vec::with_capacity(n * (n - 1) / 2);
        for i in 0..n {
            for j in (i + 1)..n {
                all_dists.push(shared.dist(i, j));
            }
        }
        all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median_dist = all_dists[all_dists.len() / 2];

        // Cooper pair threshold: distances < 25% of median
        let cooper_threshold = median_dist * 0.25;
        let cooper_pair_count = all_dists
            .iter()
            .filter(|&&d| d < cooper_threshold)
            .count();
        let cooper_pair_fraction = cooper_pair_count as f64 / all_dists.len() as f64;

        // --- 6. Resistance ratio: R(normal) / R(superconducting) ---
        let r_normal = if tc_index < n {
            let normal_r: Vec<f64> = energies[tc_index..]
                .iter()
                .map(|&(idx, _)| resistance[idx])
                .collect();
            if normal_r.is_empty() {
                0.0
            } else {
                normal_r.iter().sum::<f64>() / normal_r.len() as f64
            }
        } else {
            0.0
        };
        let r_super = if !sc_indices.is_empty() {
            sc_indices
                .iter()
                .map(|&idx| resistance[idx])
                .sum::<f64>()
                / sc_indices.len() as f64
        } else {
            1.0
        };
        let resistance_ratio = if r_super > 1e-12 {
            r_normal / r_super
        } else {
            f64::MAX
        };

        let mut result = HashMap::new();
        result.insert("tc_energy".to_string(), vec![tc_energy]);
        result.insert("tc_fraction".to_string(), vec![tc_fraction]);
        result.insert("max_resistance_drop".to_string(), vec![max_drop]);
        result.insert("meissner_score".to_string(), vec![meissner_score]);
        result.insert(
            "cooper_pair_fraction".to_string(),
            vec![cooper_pair_fraction],
        );
        result.insert("resistance_ratio".to_string(), vec![resistance_ratio]);
        result.insert(
            "ordered_resistance".to_string(),
            ordered_resistance,
        );
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_scan_produces_nonempty_output() {
        // Two clusters: tight cluster (superconducting) + spread cluster (normal)
        let data = vec![
            // Tight cluster (low energy, low resistance)
            0.1, 0.1,
            0.2, 0.15,
            0.15, 0.2,
            0.12, 0.18,
            // Spread cluster (high energy, high resistance)
            5.0, 5.0,
            6.0, 7.0,
            7.0, 5.5,
            8.0, 9.0,
        ];
        let n = 8;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let lens = UsuperconductorUlensLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "scan() must return non-empty HashMap");
        assert!(result.contains_key("tc_energy"));
        assert!(result.contains_key("meissner_score"));
        assert!(result.contains_key("cooper_pair_fraction"));
        assert!(result.contains_key("resistance_ratio"));
        assert!(result.contains_key("ordered_resistance"));

        let meissner = result["meissner_score"][0];
        assert!(meissner >= 0.0 && meissner <= 1.0, "meissner_score should be in [0,1], got {meissner}");
    }

    #[test]
    fn test_phase_transition_detected() {
        // Create data with a clear phase transition:
        // points at low energy are tightly packed, high energy are spread out
        let mut data = Vec::new();
        // 6 tightly packed points near origin
        for i in 0..6 {
            data.push(0.01 * i as f64);
            data.push(0.01 * (i as f64 + 0.5));
        }
        // 6 widely spread points far from origin
        for i in 0..6 {
            data.push(10.0 + 3.0 * i as f64);
            data.push(10.0 + 2.5 * i as f64);
        }
        let n = 12;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let lens = UsuperconductorUlensLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        // The resistance drop should be positive (transition detected)
        let max_drop = result["max_resistance_drop"][0];
        assert!(max_drop > 0.0, "should detect a resistance drop at phase transition, got {max_drop}");

        // Resistance ratio should be > 1 (normal state has higher resistance)
        let ratio = result["resistance_ratio"][0];
        assert!(ratio > 1.0, "resistance ratio should be > 1 for clear phase transition, got {ratio}");
    }
}
