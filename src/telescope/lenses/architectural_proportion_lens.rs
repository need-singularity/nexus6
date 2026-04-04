use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// Golden ratio constant.
const PHI: f64 = 1.6180339887;

/// Classical architectural proportion ratios (all related to n=6).
/// The six classical orders of architecture + golden section connections.
const PROPORTION_TARGETS: &[(f64, &str)] = &[
    (PHI,       "golden ratio (phi)"),
    (1.0 / PHI, "golden ratio inverse"),
    (2.0,       "double square (1:2)"),
    (1.5,       "sesquialtera (2:3)"),
    (1.2,       "minor sixth (5:6)"),
    (1.333333,  "sesquitertia (3:4)"),
    (1.6,       "golden approx (8:5)"),
    (2.4,       "12:5 classical module"),
];

/// ArchitecturalProportionLens: Detect classical proportional systems in data.
///
/// Architecture uses modular proportions: the column module (typically 6 columns
/// in a hexastyle temple), golden section, and integer ratios. This lens
/// measures how well data ratios conform to these classical ideals.
///
/// n=6 connection: hexastyle (6-column) temple facade, 6 classical orders.
///
/// Metrics: golden_section_score, proportion_match, modularity,
///          symmetry_index, column_rhythm, n6_architectural_score
pub struct ArchitecturalProportionLens;

impl Lens for ArchitecturalProportionLens {
    fn name(&self) -> &str { "ArchitecturalProportionLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. Golden section score: how many feature-mean ratios approximate phi?
        let mut phi_hits = 0.0;
        let mut phi_total = 0.0;
        for i in 0..d {
            for j in (i + 1)..d {
                if means[j].abs() < 1e-12 || means[i].abs() < 1e-12 { continue; }
                let ratio = (means[i] / means[j]).abs();
                phi_total += 1.0;
                let dev_phi = (ratio - PHI).abs().min((ratio - 1.0 / PHI).abs());
                if dev_phi < 0.1 {
                    phi_hits += 1.0 - dev_phi / 0.1;
                }
            }
        }
        let golden_section_score = if phi_total > 0.0 {
            (phi_hits / phi_total).min(1.0)
        } else { 0.0 };

        // 2. Proportion match: ratio of pairwise ratios matching any classical proportion
        let mut prop_hits: f64 = 0.0;
        let mut prop_total: f64 = 0.0;
        for i in 0..d {
            for j in (i + 1)..d {
                if means[j].abs() < 1e-12 || means[i].abs() < 1e-12 { continue; }
                let ratio = (means[i] / means[j]).abs();
                let ratio_inv = 1.0 / ratio;
                prop_total += 1.0;
                for &(target, _) in PROPORTION_TARGETS {
                    if (ratio - target).abs() < 0.08 || (ratio_inv - target).abs() < 0.08 {
                        prop_hits += 1.0;
                        break;
                    }
                }
            }
        }
        let proportion_match: f64 = if prop_total > 0.0 {
            (prop_hits / prop_total).min(1.0)
        } else { 0.0 };

        // 3. Modularity: does the data show a repeating module of size 6?
        //    Check if values repeat with period 6 (hexastyle column spacing)
        let mut mod_sum = 0.0;
        for col in &columns {
            if col.len() < 12 { continue; }
            let mean_val = col.iter().sum::<f64>() / col.len() as f64;
            let var: f64 = col.iter().map(|x| (x - mean_val).powi(2)).sum::<f64>();
            if var < 1e-12 { continue; }
            // Autocorrelation at lag 6
            let mut acf6 = 0.0;
            for i in 0..(col.len() - 6) {
                acf6 += (col[i] - mean_val) * (col[i + 6] - mean_val);
            }
            acf6 /= var;
            mod_sum += acf6.max(0.0);
        }
        let modularity = (mod_sum / d.max(1) as f64).min(1.0).max(0.0);

        // 4. Symmetry index: bilateral symmetry (mirror around center)
        let mut sym_sum = 0.0;
        for col in &columns {
            let len = col.len();
            let half = len / 2;
            if half == 0 { continue; }
            let mut diff_sum = 0.0;
            let mut scale = 0.0;
            for i in 0..half {
                let left = col[i];
                let right = col[len - 1 - i];
                diff_sum += (left - right).abs();
                scale += left.abs() + right.abs();
            }
            if scale > 1e-12 {
                sym_sum += 1.0 - (diff_sum / scale).min(1.0);
            }
        }
        let symmetry_index = (sym_sum / d.max(1) as f64).min(1.0).max(0.0);

        // 5. Column rhythm: regularity of inter-column spacing (feature-to-feature steps)
        //    In architecture, column spacing follows a rhythm. Check mean-to-mean steps.
        let column_rhythm = if d >= 3 {
            let steps: Vec<f64> = means.windows(2).map(|w| (w[1] - w[0]).abs()).collect();
            let step_mean = steps.iter().sum::<f64>() / steps.len() as f64;
            if step_mean > 1e-12 {
                let step_var = steps.iter().map(|s| (s - step_mean).powi(2)).sum::<f64>()
                    / steps.len() as f64;
                (-step_var.sqrt() / step_mean).exp()
            } else {
                1.0 // All equal spacing = perfect rhythm
            }
        } else { 0.0 };

        let n6_architectural_score = 0.20 * golden_section_score
            + 0.20 * proportion_match
            + 0.20 * modularity
            + 0.20 * symmetry_index
            + 0.20 * column_rhythm;

        let mut result = HashMap::new();
        result.insert("golden_section_score".into(), vec![golden_section_score]);
        result.insert("proportion_match".into(), vec![proportion_match]);
        result.insert("modularity".into(), vec![modularity]);
        result.insert("symmetry_index".into(), vec![symmetry_index]);
        result.insert("column_rhythm".into(), vec![column_rhythm]);
        result.insert("n6_architectural_score".into(), vec![n6_architectural_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_architectural_proportion_basic() {
        // Data with golden-ratio related means: 1.0, 1.618, 2.618, ...
        let data: Vec<f64> = (0..60).map(|i| {
            let col = i % 6;
            let base = PHI.powi(col as i32);
            base + 0.01 * (i / 6) as f64
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = ArchitecturalProportionLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("golden_section_score"));
        assert!(result.contains_key("n6_architectural_score"));
        assert!(result["n6_architectural_score"][0] >= 0.0);
    }

    #[test]
    fn test_symmetry_detection() {
        // Symmetric data: mirror around center
        let data: Vec<f64> = (0..60).map(|i| {
            let row = i / 6;
            let col = i % 6;
            let mid = 4.5;
            let dist = (row as f64 - mid).abs();
            dist + col as f64 * 0.1
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = ArchitecturalProportionLens.scan(&data, 10, 6, &shared);
        assert!(result["symmetry_index"][0] > 0.5);
    }
}
