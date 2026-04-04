use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// HexameterLens: Detect hexameter-like prosodic structure in data.
///
/// Classical hexameter = 6 metrical feet, each dactyl (long-short-short) or
/// spondee (long-long). This lens treats data sequences as prosodic patterns:
/// values above mean = "long" syllables, below = "short".
///
/// n=6 connection: hexameter literally means "six measures."
///
/// Metrics: foot_count_match, dactyl_ratio, spondee_ratio,
///          scansion_regularity, caesura_strength, n6_hexameter_score
pub struct HexameterLens;

/// Classify a value relative to threshold: true = "long", false = "short"
fn is_long(val: f64, threshold: f64) -> bool {
    val >= threshold
}

impl Lens for HexameterLens {
    fn name(&self) -> &str { "HexameterLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, _) = mean_var(data, n, d);

        // Convert each column to a binary "long/short" sequence
        let binary_cols: Vec<Vec<bool>> = columns.iter().enumerate().map(|(j, col)| {
            col.iter().map(|&v| is_long(v, means[j])).collect()
        }).collect();

        // 1. Foot count match: how well does n align with 6-foot structure?
        //    A perfect hexameter has 6 feet. Check if n divides naturally into 6 groups.
        let ideal_foot_len = n as f64 / 6.0;
        let foot_count_match = if ideal_foot_len >= 1.5 {
            // Good: each foot has 2-3 elements (dactyl=3, spondee=2)
            let frac = ideal_foot_len.fract();
            1.0 - (frac - 0.0).abs().min((frac - 0.5).abs()).min((frac - 1.0).abs()) * 2.0
        } else if ideal_foot_len >= 1.0 {
            0.5
        } else {
            0.2
        }.max(0.0).min(1.0);

        // 2 & 3. Dactyl and spondee detection
        //    Dactyl = long-short-short (1,0,0), Spondee = long-long (1,1)
        let mut total_dactyls = 0.0;
        let mut total_spondees = 0.0;
        let mut total_feet = 0.0;

        for bcol in &binary_cols {
            let mut pos = 0;
            while pos < bcol.len() {
                if pos + 2 < bcol.len() && bcol[pos] && !bcol[pos + 1] && !bcol[pos + 2] {
                    // Dactyl: long-short-short
                    total_dactyls += 1.0;
                    total_feet += 1.0;
                    pos += 3;
                } else if pos + 1 < bcol.len() && bcol[pos] && bcol[pos + 1] {
                    // Spondee: long-long
                    total_spondees += 1.0;
                    total_feet += 1.0;
                    pos += 2;
                } else {
                    pos += 1;
                }
            }
        }
        let dactyl_ratio: f64 = if total_feet > 0.0 { total_dactyls / total_feet } else { 0.0 };
        let spondee_ratio: f64 = if total_feet > 0.0 { total_spondees / total_feet } else { 0.0 };

        // 4. Scansion regularity: consistency of foot lengths across columns
        let mut foot_lengths_all: Vec<f64> = Vec::new();
        for bcol in &binary_cols {
            let mut pos = 0;
            while pos < bcol.len() {
                if pos + 2 < bcol.len() && bcol[pos] && !bcol[pos + 1] && !bcol[pos + 2] {
                    foot_lengths_all.push(3.0);
                    pos += 3;
                } else if pos + 1 < bcol.len() && bcol[pos] && bcol[pos + 1] {
                    foot_lengths_all.push(2.0);
                    pos += 2;
                } else {
                    foot_lengths_all.push(1.0);
                    pos += 1;
                }
            }
        }
        let scansion_regularity = if foot_lengths_all.len() >= 2 {
            let fm = foot_lengths_all.iter().sum::<f64>() / foot_lengths_all.len() as f64;
            let fv = foot_lengths_all.iter().map(|x| (x - fm).powi(2)).sum::<f64>()
                / foot_lengths_all.len() as f64;
            (-fv.sqrt() / fm.max(1e-12)).exp()
        } else { 0.0 };

        // 5. Caesura strength: detect a natural pause/break near the middle of each "line"
        //    In hexameter, the caesura typically falls in the 3rd foot (near position n/2).
        let mut caesura_sum = 0.0;
        for col in &columns {
            if col.len() < 6 { continue; }
            // Look for a local minimum (pause) near the midpoint
            let mid = col.len() / 2;
            let window_start = (mid as i64 - 2).max(1) as usize;
            let window_end = (mid + 3).min(col.len() - 1);
            let mut min_val = f64::INFINITY;
            let mut min_idx = mid;
            for i in window_start..window_end {
                if col[i] < min_val {
                    min_val = col[i];
                    min_idx = i;
                }
            }
            // Caesura strength = how much the minimum dips below neighbors
            let left = if min_idx > 0 { col[min_idx - 1] } else { col[min_idx] };
            let right = if min_idx + 1 < col.len() { col[min_idx + 1] } else { col[min_idx] };
            let avg_neighbor = (left + right) / 2.0;
            let dip = (avg_neighbor - min_val).max(0.0);
            let scale = (left.abs() + right.abs()).max(1e-12) / 2.0;
            caesura_sum += (dip / scale).min(1.0);
        }
        let caesura_strength = (caesura_sum / d as f64).min(1.0).max(0.0);

        // Composite: hexameter is about 6-foot structure with dactyls/spondees
        let n6_hexameter_score = 0.20 * foot_count_match
            + 0.20 * (dactyl_ratio + spondee_ratio).min(1.0)
            + 0.15 * dactyl_ratio.min(1.0)
            + 0.15 * spondee_ratio.min(1.0)
            + 0.15 * scansion_regularity
            + 0.15 * caesura_strength;

        let mut result = HashMap::new();
        result.insert("foot_count_match".into(), vec![foot_count_match]);
        result.insert("dactyl_ratio".into(), vec![dactyl_ratio]);
        result.insert("spondee_ratio".into(), vec![spondee_ratio]);
        result.insert("scansion_regularity".into(), vec![scansion_regularity]);
        result.insert("caesura_strength".into(), vec![caesura_strength]);
        result.insert("n6_hexameter_score".into(), vec![n6_hexameter_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hexameter_basic() {
        // Simulate dactylic pattern: high-low-low repeated 6 times across columns
        let data: Vec<f64> = (0..60).map(|i| {
            let pos = i % 3;
            match pos {
                0 => 1.0,  // long
                1 => 0.3,  // short
                _ => 0.2,  // short
            }
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = HexameterLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("dactyl_ratio"));
        assert!(result.contains_key("n6_hexameter_score"));
        assert!(result["n6_hexameter_score"][0] >= 0.0);
    }
}
