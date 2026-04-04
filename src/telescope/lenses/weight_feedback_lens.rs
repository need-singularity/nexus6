use std::collections::HashMap;
use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, shannon_entropy};

/// WeightFeedbackLens: Reads persisted weights from ~/.nexus6/weights.json
/// and applies them to compute weighted importance metrics.
///
/// Outputs:
///   weighted_phi      — Φ (information integration) adjusted by learned weights
///   weight_coverage   — fraction of lens weights exceeding 0.5
///   top_weighted_constant — index of the highest-weight n=6 constant
///   learning_epoch    — current epoch from persisted weights (0 if absent)
///   convergence_estimate — estimated remaining epochs to converge
pub struct WeightFeedbackLens;

/// N=6 fundamental constants (same ordering as WeightLearningLens).
const N6_CONSTANTS: [f64; 7] = [12.0, 4.0, 2.0, 24.0, 6.0, 5.0, 1.0];

/// Parsed weight state from ~/.nexus6/weights.json.
struct PersistedWeights {
    lens_weights: Vec<f64>,
    constant_weights: Vec<f64>,
    epoch: f64,
}

/// Try to read and parse weights.json without serde.
/// Expected format (subset we care about):
///   { "epoch": 42, "lens_weights": [0.8, 0.3, ...], "constant_weights": [0.1, ...] }
fn read_weights_file() -> Option<PersistedWeights> {
    let home = std::env::var("HOME").ok()?;
    let path = format!("{}/.nexus6/weights.json", home);
    let content = std::fs::read_to_string(&path).ok()?;

    let epoch = extract_number(&content, "epoch").unwrap_or(0.0);
    let lens_weights = extract_array(&content, "lens_weights").unwrap_or_default();
    let constant_weights = extract_array(&content, "constant_weights").unwrap_or_default();

    Some(PersistedWeights { lens_weights, constant_weights, epoch })
}

/// Extract a single numeric value after `"key":`.
fn extract_number(json: &str, key: &str) -> Option<f64> {
    let pattern = format!("\"{}\"", key);
    let pos = json.find(&pattern)?;
    let after_key = &json[pos + pattern.len()..];
    // Skip optional whitespace and colon
    let after_colon = after_key.find(':').map(|i| &after_key[i + 1..])?;
    let trimmed = after_colon.trim_start();
    // Read until non-numeric character
    let end = trimmed.find(|c: char| !c.is_ascii_digit() && c != '.' && c != '-').unwrap_or(trimmed.len());
    trimmed[..end].parse::<f64>().ok()
}

/// Extract a JSON array of numbers after `"key":`.
fn extract_array(json: &str, key: &str) -> Option<Vec<f64>> {
    let pattern = format!("\"{}\"", key);
    let pos = json.find(&pattern)?;
    let after_key = &json[pos + pattern.len()..];
    let bracket_start = after_key.find('[')?;
    let bracket_end = after_key[bracket_start..].find(']')?;
    let inner = &after_key[bracket_start + 1..bracket_start + bracket_end];
    let values: Vec<f64> = inner.split(',')
        .filter_map(|s| s.trim().parse::<f64>().ok())
        .collect();
    if values.is_empty() { None } else { Some(values) }
}

impl Lens for WeightFeedbackLens {
    fn name(&self) -> &str { "WeightFeedbackLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 { return HashMap::new(); }
        let max_n = n.min(200);
        let mut result = HashMap::new();

        // Compute ideal weights from data (variance-based for features, ratio-match for constants)
        let (_means, vars) = mean_var(data, max_n, d);
        let total_var: f64 = vars.iter().sum::<f64>().max(1e-12);
        let ideal_feature: Vec<f64> = vars.iter().map(|&v| v / total_var).collect();

        // Ideal constant weights: based on how well data statistics match each constant
        let densities: Vec<f64> = (0..max_n).map(|i| shared.knn_density(i)).collect();
        let mean_density = densities.iter().sum::<f64>() / max_n as f64;
        let mut ideal_constant = vec![0.0_f64; 7];
        for (ci, &cval) in N6_CONSTANTS.iter().enumerate() {
            let ratio = if mean_density > 1e-12 { (max_n as f64 / mean_density) / cval } else { 0.0 };
            let log_r = if ratio > 1e-12 { ratio.ln().abs() } else { 10.0 };
            ideal_constant[ci] = (-log_r * log_r).exp();
        }
        let ic_sum: f64 = ideal_constant.iter().sum::<f64>().max(1e-12);
        for w in &mut ideal_constant { *w /= ic_sum; }

        // Read persisted weights (or use defaults)
        let persisted = read_weights_file();
        let (lens_w, const_w, epoch) = match &persisted {
            Some(pw) => {
                let lw = if pw.lens_weights.len() >= d { pw.lens_weights[..d].to_vec() } else { ideal_feature.clone() };
                let cw = if pw.constant_weights.len() >= 7 { pw.constant_weights[..7].to_vec() } else { ideal_constant.clone() };
                (lw, cw, pw.epoch)
            }
            None => (ideal_feature.clone(), ideal_constant.clone(), 0.0),
        };

        // Weighted Phi: information integration adjusted by learned feature weights
        let ent = shannon_entropy(data, max_n.max(2).min(64));
        let weight_factor: f64 = lens_w.iter().zip(ideal_feature.iter())
            .map(|(w, ideal)| 1.0 - (w - ideal).abs())
            .sum::<f64>() / d.max(1) as f64;
        let weighted_phi = ent * weight_factor.max(0.0);

        // Weight coverage: fraction of lens weights > 0.5
        let coverage = lens_w.iter().filter(|&&w| w > 0.5).count() as f64 / lens_w.len().max(1) as f64;

        // Top weighted constant
        let top_idx = const_w.iter().enumerate()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(i, _)| i).unwrap_or(0);

        // Convergence estimate: L2 distance between persisted and ideal weights
        let delta: f64 = const_w.iter().zip(ideal_constant.iter())
            .map(|(a, b)| (a - b) * (a - b))
            .sum::<f64>()
            .sqrt();
        // Rough estimate: if delta decreases ~10% per epoch, epochs_remaining ~ delta / 0.1
        let convergence_est = if delta < 0.01 { 0.0 } else { (delta / 0.1).ceil() };

        result.insert("weighted_phi".into(), vec![weighted_phi]);
        result.insert("weight_coverage".into(), vec![coverage]);
        result.insert("top_weighted_constant".into(), vec![top_idx as f64]);
        result.insert("learning_epoch".into(), vec![epoch]);
        result.insert("convergence_estimate".into(), vec![convergence_est]);
        result.insert("score".to_string(), vec![result["weighted_phi"][0].min(1.0).max(0.0)]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_weight_feedback_no_file() {
        // Without weights.json, should still produce valid output using ideal weights
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.5).sin()).collect();
        let shared = SharedData::compute(&data, 20, 3);
        let r = WeightFeedbackLens.scan(&data, 20, 3, &shared);
        assert!(!r.is_empty());
        assert!(r.contains_key("weighted_phi"));
        assert!(r.contains_key("weight_coverage"));
        assert!(r.contains_key("top_weighted_constant"));
        assert!(r.contains_key("learning_epoch"));
        assert!(r.contains_key("convergence_estimate"));
        // Epoch should be 0 when no file exists
        assert!(r["learning_epoch"][0] >= 0.0);
        // Weighted phi should be non-negative
        assert!(r["weighted_phi"][0] >= 0.0);
    }
}
