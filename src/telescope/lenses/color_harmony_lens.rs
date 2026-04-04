use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// ColorHarmonyLens: Detect color-wheel harmony patterns in data.
///
/// A 6-color wheel divides 360 degrees into 60-degree sectors.
/// This lens maps data values to hue angles and measures how well
/// they align with standard color harmonies: complementary (180 deg),
/// triadic (120 deg), split-complementary, and hexadic (6-way).
///
/// n=6 connection: the 6-color wheel and hexadic harmony.
///
/// Metrics: hexadic_score, complementary_score, triadic_score,
///          saturation_variance, hue_distribution, n6_color_score
pub struct ColorHarmonyLens;

/// Map a normalized value [0,1] to a hue angle [0, 360).
fn value_to_hue(val: f64) -> f64 {
    (val.fract().abs() * 360.0) % 360.0
}

/// Angular distance between two hue angles.
fn angular_distance(a: f64, b: f64) -> f64 {
    let d = (a - b).abs() % 360.0;
    d.min(360.0 - d)
}

impl Lens for ColorHarmonyLens {
    fn name(&self) -> &str { "ColorHarmonyLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // Normalize data to [0,1] for hue mapping
        let mut all_hues: Vec<f64> = Vec::with_capacity(n * d);
        for col in &columns {
            let min = col.iter().cloned().fold(f64::INFINITY, f64::min);
            let max = col.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let range = (max - min).max(1e-12);
            for &v in col {
                all_hues.push(value_to_hue((v - min) / range));
            }
        }

        // Per-column mean hues (one "color" per feature dimension)
        let mut feature_hues: Vec<f64> = Vec::with_capacity(d);
        for col in &columns {
            let min = col.iter().cloned().fold(f64::INFINITY, f64::min);
            let max = col.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            let range = (max - min).max(1e-12);
            let mean_norm = col.iter().sum::<f64>() / col.len() as f64;
            feature_hues.push(value_to_hue((mean_norm - min) / range));
        }

        // 1. Hexadic score: do the feature hues evenly divide the wheel into 6 sectors (60 deg each)?
        let mut hexadic_score = 0.0;
        if feature_hues.len() >= 6 {
            let mut sorted_hues = feature_hues.clone();
            sorted_hues.sort_by(|a, b| a.partial_cmp(b).unwrap());
            // Check spacing between consecutive hues
            let mut spacings: Vec<f64> = Vec::new();
            for i in 0..sorted_hues.len() {
                let next = (i + 1) % sorted_hues.len();
                let gap = if next == 0 {
                    360.0 - sorted_hues[sorted_hues.len() - 1] + sorted_hues[0]
                } else {
                    sorted_hues[next] - sorted_hues[i]
                };
                spacings.push(gap);
            }
            // Ideal spacing = 360/d degrees; measure deviation
            let ideal = 360.0 / sorted_hues.len() as f64;
            let mse: f64 = spacings.iter().map(|s| (s - ideal).powi(2)).sum::<f64>()
                / spacings.len() as f64;
            hexadic_score = (-mse.sqrt() / 60.0).exp(); // 60 deg tolerance scale
        } else if feature_hues.len() >= 2 {
            // Fewer features: check if they span the wheel proportionally
            let spread = feature_hues.windows(2)
                .map(|w| angular_distance(w[0], w[1]))
                .sum::<f64>();
            hexadic_score = (spread / 360.0).min(1.0) * 0.5;
        }

        // 2. Complementary score: pairs at ~180 degrees apart
        let mut comp_hits = 0.0;
        let mut comp_total = 0.0;
        for i in 0..feature_hues.len() {
            for j in (i + 1)..feature_hues.len() {
                comp_total += 1.0;
                let dist = angular_distance(feature_hues[i], feature_hues[j]);
                if (dist - 180.0).abs() < 30.0 {
                    comp_hits += 1.0 - (dist - 180.0).abs() / 30.0;
                }
            }
        }
        let complementary_score = if comp_total > 0.0 {
            (comp_hits / comp_total).min(1.0)
        } else { 0.0 };

        // 3. Triadic score: triples at ~120 degrees apart
        let mut tri_hits = 0.0;
        let mut tri_total = 0.0;
        for i in 0..feature_hues.len() {
            for j in (i + 1)..feature_hues.len() {
                for k in (j + 1)..feature_hues.len() {
                    tri_total += 1.0;
                    let d1 = angular_distance(feature_hues[i], feature_hues[j]);
                    let d2 = angular_distance(feature_hues[j], feature_hues[k]);
                    let d3 = angular_distance(feature_hues[i], feature_hues[k]);
                    // Ideal triadic: all three distances ~120 deg
                    let dev = ((d1 - 120.0).abs() + (d2 - 120.0).abs() + (d3 - 120.0).abs()) / 3.0;
                    if dev < 40.0 {
                        tri_hits += 1.0 - dev / 40.0;
                    }
                }
            }
        }
        let triadic_score = if tri_total > 0.0 {
            (tri_hits / tri_total).min(1.0)
        } else { 0.0 };

        // 4. Saturation variance: variance of per-column variance (color "saturation" analogy)
        //    Low variance of variance = uniform saturation across features
        let col_vars: Vec<f64> = vars.iter().copied().collect();
        let mean_var_val = col_vars.iter().sum::<f64>() / col_vars.len() as f64;
        let var_of_var = col_vars.iter().map(|v| (v - mean_var_val).powi(2)).sum::<f64>()
            / col_vars.len() as f64;
        let saturation_variance = (-var_of_var.sqrt() / mean_var_val.abs().max(1e-12)).exp();

        // 5. Hue distribution: Shannon entropy over 6 hue sectors (60 deg each)
        let mut sector_counts = [0u32; 6];
        for &h in &all_hues {
            let sector = ((h / 60.0) as usize).min(5);
            sector_counts[sector] += 1;
        }
        let total = all_hues.len() as f64;
        let mut hue_entropy = 0.0;
        for &c in &sector_counts {
            if c > 0 {
                let p = c as f64 / total;
                hue_entropy -= p * p.ln();
            }
        }
        let hue_distribution = hue_entropy / (6.0_f64).ln(); // normalize to [0,1]

        let n6_color_score = 0.25 * hexadic_score
            + 0.20 * complementary_score
            + 0.15 * triadic_score
            + 0.15 * saturation_variance
            + 0.25 * hue_distribution;

        let mut result = HashMap::new();
        result.insert("hexadic_score".into(), vec![hexadic_score]);
        result.insert("complementary_score".into(), vec![complementary_score]);
        result.insert("triadic_score".into(), vec![triadic_score]);
        result.insert("saturation_variance".into(), vec![saturation_variance]);
        result.insert("hue_distribution".into(), vec![hue_distribution]);
        result.insert("n6_color_score".into(), vec![n6_color_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_color_harmony_basic() {
        // 6 features with means spaced ~60 degrees apart on hue wheel
        let data: Vec<f64> = (0..60).map(|i| {
            let col = i % 6;
            (col as f64 / 6.0) + 0.01 * (i / 6) as f64
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = ColorHarmonyLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("hexadic_score"));
        assert!(result.contains_key("n6_color_score"));
        assert!(result["n6_color_score"][0] >= 0.0);
    }
}
