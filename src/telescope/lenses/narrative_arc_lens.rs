use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// NarrativeArcLens: Detect 6-act narrative structure in data.
///
/// Classical 6-act structure: Exposition, Rising Action, Complication,
/// Climax, Falling Action, Resolution. Maps data columns onto a
/// tension curve and measures conformance to this arc.
///
/// n=6 connection: the 6-act dramatic structure.
///
/// Metrics: arc_conformance, climax_position, tension_gradient,
///          resolution_strength, symmetry_score, n6_narrative_score
pub struct NarrativeArcLens;

/// Ideal 6-act tension curve (normalized 0..1):
/// Exposition(0.2) → Rising(0.4) → Complication(0.6) → Climax(1.0) → Falling(0.5) → Resolution(0.1)
const IDEAL_ARC: [f64; 6] = [0.2, 0.4, 0.6, 1.0, 0.5, 0.1];

impl Lens for NarrativeArcLens {
    fn name(&self) -> &str { "NarrativeArcLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // Divide each column into 6 acts and compute mean "tension" per act
        let act_size = n / 6;
        let remainder = n % 6;

        let compute_acts = |col: &[f64]| -> [f64; 6] {
            let mut acts = [0.0; 6];
            let mut start = 0;
            for act in 0..6 {
                let extra = if act < remainder { 1 } else { 0 };
                let end = start + act_size + extra;
                let end = end.min(col.len());
                if end > start {
                    acts[act] = col[start..end].iter().sum::<f64>() / (end - start) as f64;
                }
                start = end;
            }
            acts
        };

        // Normalize acts to [0,1]
        let normalize = |acts: &mut [f64; 6]| {
            let min = acts.iter().cloned().fold(f64::INFINITY, f64::min);
            let max = acts.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let range = (max - min).max(1e-12);
            for a in acts.iter_mut() {
                *a = (*a - min) / range;
            }
        };

        // 1. Arc conformance: correlation with ideal 6-act curve
        let mut conformance_sum = 0.0;
        let mut climax_pos_sum = 0.0;
        let mut tension_grad_sum = 0.0;
        let mut resolution_sum = 0.0;
        let mut symmetry_sum = 0.0;
        let valid_cols;

        let mut vc = 0;
        for col in &columns {
            let mut acts = compute_acts(col);
            let range_check: f64 = acts.iter().cloned().fold(f64::NEG_INFINITY, f64::max)
                - acts.iter().cloned().fold(f64::INFINITY, f64::min);
            if range_check < 1e-12 { continue; }
            normalize(&mut acts);
            vc += 1;

            // Arc conformance: 1 - normalized RMSE vs ideal arc
            let mse: f64 = acts.iter().zip(IDEAL_ARC.iter())
                .map(|(a, b)| (a - b).powi(2))
                .sum::<f64>() / 6.0;
            conformance_sum += (1.0 - mse.sqrt()).max(0.0);

            // 2. Climax position: where is the maximum? Ideal = act 4 (index 3)
            let max_idx = acts.iter().enumerate()
                .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
                .map(|(i, _)| i).unwrap_or(3);
            // Score: 1.0 at index 3, decreasing with distance
            climax_pos_sum += 1.0 / (1.0 + (max_idx as f64 - 3.0).abs());

            // 3. Tension gradient: is there a clear rise then fall?
            let rise = acts[0..4].windows(2).filter(|w| w[1] > w[0]).count() as f64 / 3.0;
            let fall = acts[3..6].windows(2).filter(|w| w[1] < w[0]).count() as f64 / 2.0;
            tension_grad_sum += (rise + fall) / 2.0;

            // 4. Resolution strength: how much does tension drop from climax to end?
            let drop = (acts[3] - acts[5]).max(0.0); // climax - resolution
            resolution_sum += drop.min(1.0);

            // 5. Symmetry: compare rising (acts 0..3) to mirrored falling (acts 3..6)
            let rising = &acts[0..3];
            let falling_rev = [acts[5], acts[4], acts[3]];
            let sym_mse: f64 = rising.iter().zip(falling_rev.iter())
                .map(|(a, b)| (a - b).powi(2))
                .sum::<f64>() / 3.0;
            symmetry_sum += (1.0 - sym_mse.sqrt()).max(0.0);
        }
        valid_cols = vc.max(1) as f64;

        let arc_conformance = conformance_sum / valid_cols;
        let climax_position = climax_pos_sum / valid_cols;
        let tension_gradient = tension_grad_sum / valid_cols;
        let resolution_strength = resolution_sum / valid_cols;
        let symmetry_score = symmetry_sum / valid_cols;

        let n6_narrative_score = 0.25 * arc_conformance
            + 0.20 * climax_position
            + 0.20 * tension_gradient
            + 0.15 * resolution_strength
            + 0.20 * symmetry_score;

        let mut result = HashMap::new();
        result.insert("arc_conformance".into(), vec![arc_conformance]);
        result.insert("climax_position".into(), vec![climax_position]);
        result.insert("tension_gradient".into(), vec![tension_gradient]);
        result.insert("resolution_strength".into(), vec![resolution_strength]);
        result.insert("symmetry_score".into(), vec![symmetry_score]);
        result.insert("n6_narrative_score".into(), vec![n6_narrative_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_narrative_arc_basic() {
        // Simulate a classic narrative arc: rise to climax then fall
        let mut data = Vec::with_capacity(60);
        for row in 0..10 {
            for col in 0..6 {
                // Tension curve following the 6-act structure
                let t = match col {
                    0 => 0.2,
                    1 => 0.4,
                    2 => 0.6,
                    3 => 1.0,
                    4 => 0.5,
                    5 => 0.1,
                    _ => 0.0,
                };
                data.push(t + 0.05 * row as f64);
            }
        }
        let shared = SharedData::compute(&data, 10, 6);
        let result = NarrativeArcLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("arc_conformance"));
        assert!(result.contains_key("n6_narrative_score"));
        assert!(result["n6_narrative_score"][0] > 0.0);
    }
}
