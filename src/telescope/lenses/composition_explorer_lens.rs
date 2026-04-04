use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// Coordination number target for octahedral geometry
const CN_OCTAHEDRAL: f64 = 6.0;

/// Known stable crystal structure templates: (name, A, B, C, O ratios summing to total atoms)
/// Perovskite  ABO3   -> 1+1+3 = 5 atoms/formula unit
/// Spinel      AB2O4  -> 1+2+4 = 7
/// Garnet      A3B2C3O12 -> 3+2+3+12 = 20
const STRUCTURE_TEMPLATES: &[(&str, &[f64])] = &[
    ("perovskite_ABO3",     &[1.0, 1.0, 3.0]),
    ("spinel_AB2O4",        &[1.0, 2.0, 4.0]),
    ("garnet_A3B2C3O12",    &[3.0, 2.0, 3.0, 12.0]),
];

/// CompositionExplorerLens: Explore novel material composition spaces.
///
/// Algorithm:
///   1. Detect coordination number (CN=6, octahedral) patterns in data
///   2. Generate A_xB_y composition candidates where x+y is a multiple of 6
///   3. Compute similarity to known stable structures (perovskite, spinel, garnet)
///   4. Report cn6_pattern_score, composition_candidates, structure_similarity, overall score
pub struct CompositionExplorerLens;

impl Lens for CompositionExplorerLens {
    fn name(&self) -> &str {
        "CompositionExplorerLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let (means, vars) = mean_var(data, n, d);
        let columns = column_vectors(data, n, d);

        // ── 1. Coordination number pattern detection ──
        // For each point, check if its k=6 nearest neighbors are roughly equidistant
        // (signature of octahedral coordination)
        let k = 6.min(n.saturating_sub(1));
        let mut cn6_scores = Vec::with_capacity(n);
        for i in 0..n {
            if k == 0 {
                cn6_scores.push(0.0);
                continue;
            }
            let mut dists: Vec<f64> = (0..n)
                .filter(|&j| j != i)
                .map(|j| shared.dist(i, j))
                .collect();
            dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

            if dists.len() < k {
                cn6_scores.push(0.0);
                continue;
            }

            let knn_dists = &dists[..k];
            let mean_d = knn_dists.iter().sum::<f64>() / k as f64;
            if mean_d < 1e-12 {
                cn6_scores.push(1.0);
                continue;
            }
            let variance = knn_dists.iter()
                .map(|&dd| (dd - mean_d).powi(2))
                .sum::<f64>() / k as f64;
            let cv = variance.sqrt() / mean_d;
            // Low coefficient of variation = uniform neighbor distances = good CN=6
            cn6_scores.push((-cv * 5.0).exp());
        }
        let cn6_pattern_score = cn6_scores.iter().sum::<f64>() / n as f64;

        // ── 2. Composition candidate generation ──
        // Treat positive feature means as stoichiometric proxies.
        // Look for pairs (x, y) where x+y is a multiple of 6.
        let positive_means: Vec<f64> = means.iter()
            .filter(|&&m| m > 0.1)
            .cloned()
            .collect();

        let mut candidate_count: f64 = 0.0;
        let mut ratio_6_scores = Vec::new();
        for i in 0..positive_means.len() {
            for j in (i + 1)..positive_means.len() {
                let x = positive_means[i];
                let y = positive_means[j];
                let sum = x + y;
                if sum < 1e-12 { continue; }
                // How close is sum to a multiple of 6?
                let nearest_mult = (sum / CN_OCTAHEDRAL).round() * CN_OCTAHEDRAL;
                let deviation = ((sum - nearest_mult) / CN_OCTAHEDRAL).abs();
                if deviation < 0.15 {
                    candidate_count += 1.0;
                    ratio_6_scores.push(1.0 - deviation / 0.15);
                }
            }
        }
        let max_pairs = (positive_means.len() * positive_means.len().saturating_sub(1) / 2).max(1);
        let composition_candidate_score = candidate_count / max_pairs as f64;

        // ── 3. Similarity to known stable structures ──
        // Normalize sorted positive means and compare cosine similarity with templates
        let mut sorted_means = positive_means.clone();
        sorted_means.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let mut best_similarity: f64 = 0.0;
        let mut best_structure = String::new();
        let mut structure_scores = Vec::new();

        for &(name, template) in STRUCTURE_TEMPLATES {
            let t_len = template.len();
            if sorted_means.len() < t_len {
                structure_scores.push(0.0);
                continue;
            }
            // Try all contiguous windows of length t_len from sorted means
            let mut best_for_template: f64 = 0.0;
            for window in sorted_means.windows(t_len) {
                let sim = cosine_similarity(window, template);
                if sim > best_for_template {
                    best_for_template = sim;
                }
            }
            structure_scores.push(best_for_template);
            if best_for_template > best_similarity {
                best_similarity = best_for_template;
                best_structure = name.to_string();
            }
        }

        // ── 4. Octahedral regularity: knn_k proximity to 6 ──
        let effective_cn = shared.knn_k as f64;
        let cn_proximity = (-(effective_cn - CN_OCTAHEDRAL).powi(2) / 4.0).exp();

        // ── 5. Feature ratio analysis ──
        // Check if feature ratios match common stoichiometric ratios (1:1, 1:2, 1:3, 2:3)
        let stoich_ratios: &[f64] = &[1.0, 0.5, 1.0 / 3.0, 2.0 / 3.0, 0.25, 0.75];
        let mut ratio_match_count = 0.0;
        let mut total_ratio_checks = 0.0;
        for i in 0..positive_means.len() {
            for j in (i + 1)..positive_means.len() {
                let bigger = positive_means[i].max(positive_means[j]);
                let smaller = positive_means[i].min(positive_means[j]);
                if bigger < 1e-12 { continue; }
                let ratio = smaller / bigger;
                total_ratio_checks += 1.0;
                for &sr in stoich_ratios {
                    if (ratio - sr).abs() < 0.08 {
                        ratio_match_count += 1.0;
                        break;
                    }
                }
            }
        }
        let stoich_ratio_score = if total_ratio_checks > 0.0 {
            ratio_match_count / total_ratio_checks
        } else {
            0.0
        };

        // ── Combined composition exploration score ──
        let composition_score = cn6_pattern_score * 0.25
            + composition_candidate_score * 0.20
            + best_similarity * 0.25
            + cn_proximity * 0.15
            + stoich_ratio_score * 0.15;

        let mut result = HashMap::new();
        result.insert("cn6_pattern_score".to_string(), vec![cn6_pattern_score]);
        result.insert("composition_candidate_score".to_string(), vec![composition_candidate_score]);
        result.insert("composition_candidate_count".to_string(), vec![candidate_count]);
        result.insert("best_structure_similarity".to_string(), vec![best_similarity]);
        result.insert("structure_similarity_scores".to_string(), structure_scores);
        result.insert("cn_proximity".to_string(), vec![cn_proximity]);
        result.insert("stoichiometric_ratio_score".to_string(), vec![stoich_ratio_score]);
        result.insert("composition_score".to_string(), vec![composition_score]);
        result.insert("cn6_per_point".to_string(), cn6_scores);
        result.insert("ratio_6_match_quality".to_string(), ratio_6_scores);
        result
    }
}

/// Cosine similarity between two slices.
fn cosine_similarity(a: &[f64], b: &[f64]) -> f64 {
    let dot: f64 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f64 = a.iter().map(|x| x * x).sum::<f64>().sqrt();
    let norm_b: f64 = b.iter().map(|x| x * x).sum::<f64>().sqrt();
    if norm_a < 1e-12 || norm_b < 1e-12 {
        return 0.0;
    }
    (dot / (norm_a * norm_b)).clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_shared(data: &[f64], n: usize, d: usize) -> SharedData {
        SharedData::compute(data, n, d)
    }

    #[test]
    fn test_cn6_octahedral_detection() {
        // 1 center + 6 octahedral vertices => high CN=6 score for center
        let mut data = vec![0.0, 0.0, 0.0];
        let offsets = [
            [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0], [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0], [0.0, 0.0, -1.0],
        ];
        for o in &offsets {
            data.extend_from_slice(o);
        }
        let n = 7;
        let d = 3;
        let shared = make_shared(&data, n, d);
        let result = CompositionExplorerLens.scan(&data, n, d, &shared);

        assert!(result.contains_key("cn6_pattern_score"));
        let cn6 = result["cn6_pattern_score"][0];
        assert!(cn6 > 0.3, "Octahedral structure should yield decent CN=6 score, got {cn6}");
    }

    #[test]
    fn test_perovskite_similarity() {
        // Feature means ~ [1, 1, 3] should match perovskite ABO3
        let n = 20;
        let d = 3;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let noise = (i as f64 * 0.1).sin() * 0.02;
            data.push(1.0 + noise);  // A site
            data.push(1.0 + noise);  // B site
            data.push(3.0 + noise);  // O site
        }
        let shared = make_shared(&data, n, d);
        let result = CompositionExplorerLens.scan(&data, n, d, &shared);

        let sim = result["best_structure_similarity"][0];
        assert!(sim > 0.9, "Should strongly match perovskite template, got {sim}");
    }

    #[test]
    fn test_composition_candidates_mult_of_6() {
        // Features with means 2.0 and 4.0 => sum=6 (multiple of 6)
        let n = 15;
        let d = 2;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let noise = (i as f64 * 0.1).sin() * 0.01;
            data.push(2.0 + noise);
            data.push(4.0 + noise);
        }
        let shared = make_shared(&data, n, d);
        let result = CompositionExplorerLens.scan(&data, n, d, &shared);

        let candidates = result["composition_candidate_count"][0];
        assert!(candidates >= 1.0, "Sum 2+4=6 should be flagged as candidate, got {candidates}");
    }

    #[test]
    fn test_empty_data() {
        let data: Vec<f64> = vec![0.0; 6];
        let shared = make_shared(&data, 2, 3);
        let result = CompositionExplorerLens.scan(&data, 2, 3, &shared);
        // n < 3 guard
        assert!(result.is_empty());
    }
}
