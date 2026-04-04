use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// CharacterInductionLens: Detect representation-theoretic patterns —
/// character polynomials, irreducible decomposition, induction from subgroups.
///
/// n=6 connection: S_6 has 11 irreducible representations, character table
/// encodes deep combinatorial structure. |S_6| = 720.
pub struct CharacterInductionLens;

/// Partitions of 6 (corresponding to irreps of S_6): 11 total
const PARTITIONS_OF_6: &[(usize, &[usize])] = &[
    (1, &[6]),
    (2, &[5, 1]),
    (3, &[4, 2]),
    (4, &[4, 1, 1]),
    (5, &[3, 3]),
    (6, &[3, 2, 1]),
    (7, &[3, 1, 1, 1]),
    (8, &[2, 2, 2]),
    (9, &[2, 2, 1, 1]),
    (10, &[2, 1, 1, 1, 1]),
    (11, &[1, 1, 1, 1, 1, 1]),
];

/// Dimensions of irreps of S_6 (from hook-length formula)
const S6_IRREP_DIMS: &[f64] = &[1.0, 5.0, 9.0, 10.0, 5.0, 16.0, 10.0, 5.0, 9.0, 5.0, 1.0];

/// Compute character polynomial: fit data to polynomial and extract coefficients.
fn character_polynomial(vals: &[f64]) -> Vec<f64> {
    // Fit a degree-5 polynomial (6 coefficients for n=6) using least squares
    let n = vals.len().min(50);
    let degree = 5;

    // Build Vandermonde-like system
    let mut coeffs = vec![0.0; degree + 1];
    if n <= degree {
        return coeffs;
    }

    // Simple power sum method: c_k = (1/n) Σ x_i^k
    for k in 0..=degree {
        let mut sum = 0.0;
        for i in 0..n {
            let x = (i as f64 + 1.0) / n as f64; // normalize to [0,1]
            sum += vals[i] * x.powi(k as i32);
        }
        coeffs[k] = sum / n as f64;
    }
    coeffs
}

/// Measure how well data decomposes into S_6 irrep dimension pattern.
fn irrep_decomposition_score(vals: &[f64]) -> (f64, Vec<f64>) {
    let n = vals.len();
    if n < 6 {
        return (0.0, vec![]);
    }

    // Sort absolute values and compare with S_6 irrep dimensions
    let mut abs_vals: Vec<f64> = vals.iter().map(|x| x.abs()).collect();
    abs_vals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

    // Take 11 quantiles (one per irrep)
    let quantiles: Vec<f64> = (0..11).map(|i| {
        let idx = (i * n / 11).min(n - 1);
        abs_vals[idx]
    }).collect();

    // Normalize both to compare shapes
    let q_max = quantiles.iter().cloned().fold(0.0f64, f64::max).max(1e-12);
    let d_max = S6_IRREP_DIMS.iter().cloned().fold(0.0f64, f64::max);
    let norm_q: Vec<f64> = quantiles.iter().map(|x| x / q_max).collect();
    let norm_d: Vec<f64> = S6_IRREP_DIMS.iter().map(|x| x / d_max).collect();

    // Correlation between quantile shape and irrep dimension shape
    let mut dot = 0.0;
    let mut norm_a = 0.0;
    let mut norm_b = 0.0;
    for i in 0..11 {
        dot += norm_q[i] * norm_d[i];
        norm_a += norm_q[i] * norm_q[i];
        norm_b += norm_d[i] * norm_d[i];
    }
    let correlation = if norm_a > 1e-12 && norm_b > 1e-12 {
        dot / (norm_a.sqrt() * norm_b.sqrt())
    } else {
        0.0
    };

    (correlation, quantiles)
}

impl Lens for CharacterInductionLens {
    fn name(&self) -> &str {
        "CharacterInductionLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. Character polynomial coefficients
        let char_poly = character_polynomial(&vals);
        result.insert("character_polynomial".to_string(), char_poly);

        // 2. Irrep decomposition score against S_6
        let (irrep_score, quantiles) = irrep_decomposition_score(&vals);
        result.insert("s6_irrep_score".to_string(), vec![irrep_score]);
        if !quantiles.is_empty() {
            result.insert("irrep_quantiles".to_string(), quantiles);
        }

        // 3. Dimension formula: |S_6| = 720 = Σ (dim ρ)²
        //    Check if data squared-sums approximate 720
        let sum_sq: f64 = vals.iter().map(|x| x * x).sum();
        let mean_sq = sum_sq / vals.len() as f64;
        let s6_order = 720.0;
        let dim_formula_residual = (mean_sq - s6_order).abs() / s6_order;
        result.insert("s6_dim_formula_residual".to_string(), vec![dim_formula_residual]);

        // 4. Induction pattern: check restriction/induction structure
        //    S_5 ⊂ S_6: |S_5| = 120, [S_6:S_5] = 6
        //    Induced character satisfies Frobenius reciprocity
        let chunk_size = 6;
        if vals.len() >= chunk_size * 2 {
            let mut induction_score = 0.0;
            let num_chunks = vals.len() / chunk_size;
            // Check if chunks have consistent inner structure
            let mut chunk_means: Vec<f64> = Vec::new();
            for c in 0..num_chunks {
                let chunk = &vals[c * chunk_size..(c + 1) * chunk_size];
                chunk_means.push(chunk.iter().sum::<f64>() / chunk_size as f64);
            }
            if chunk_means.len() >= 2 {
                let global_mean = chunk_means.iter().sum::<f64>() / chunk_means.len() as f64;
                let inter_var: f64 = chunk_means.iter().map(|x| (x - global_mean).powi(2)).sum::<f64>()
                    / chunk_means.len() as f64;
                let total_var: f64 = vals.iter().map(|x| {
                    let m = vals.iter().sum::<f64>() / vals.len() as f64;
                    (x - m).powi(2)
                }).sum::<f64>() / vals.len() as f64;
                induction_score = if total_var > 1e-12 {
                    inter_var / total_var // ratio of between-group to total variance
                } else {
                    0.0
                };
            }
            result.insert("induction_ratio".to_string(), vec![induction_score]);
        }

        // 5. Number of partitions: p(6) = 11
        result.insert("partition_count_six".to_string(), vec![PARTITIONS_OF_6.len() as f64]);

        // 6. Orthogonality check: character orthogonality rows
        //    Treat consecutive 6-tuples as "characters" and check orthogonality
        if vals.len() >= 12 {
            let mut orth_score = 0.0;
            let mut orth_count = 0;
            let num_chars = (vals.len() / 6).min(11);
            for i in 0..num_chars {
                for j in (i + 1)..num_chars {
                    let chi_i = &vals[i * 6..(i + 1) * 6];
                    let chi_j = &vals[j * 6..(j + 1) * 6];
                    let dot: f64 = chi_i.iter().zip(chi_j).map(|(a, b)| a * b).sum();
                    let norm_i: f64 = chi_i.iter().map(|x| x * x).sum::<f64>().sqrt();
                    let norm_j: f64 = chi_j.iter().map(|x| x * x).sum::<f64>().sqrt();
                    if norm_i > 1e-12 && norm_j > 1e-12 {
                        orth_score += 1.0 - (dot / (norm_i * norm_j)).abs();
                        orth_count += 1;
                    }
                }
            }
            let avg_orth = if orth_count > 0 { orth_score / orth_count as f64 } else { 0.0 };
            result.insert("character_orthogonality".to_string(), vec![avg_orth]);
        }

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_character_induction_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64).sqrt()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = CharacterInductionLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("s6_irrep_score"));
        assert_eq!(result["partition_count_six"][0], 11.0);
    }

    #[test]
    fn test_character_induction_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = CharacterInductionLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
