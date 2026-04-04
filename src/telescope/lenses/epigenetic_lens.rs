use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// EpigeneticLens: Epigenetic histone modification states with 6 marks.
///
/// Models chromatin state dynamics:
///   - 6 histone marks (H3K4me3, H3K27me3, H3K36me3, H3K9me3, H3K27ac, H3K4me1)
///   - Each data point = a genomic locus with mark intensities
///   - Chromatin state classification (active/poised/repressed/bivalent)
///   - Epigenetic memory: autocorrelation of states across loci
///   - Entropy of chromatin state distribution
///   - Bivalent domain detection (co-occurrence of activating + repressive marks)
pub struct EpigeneticLens;

impl Lens for EpigeneticLens {
    fn name(&self) -> &str {
        "EpigeneticLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let n_marks = d.min(6);

        // Normalize mark intensities to [0, 1]
        let mut col_min = vec![f64::INFINITY; n_marks];
        let mut col_max = vec![f64::NEG_INFINITY; n_marks];
        for i in 0..n {
            for j in 0..n_marks {
                let v = data[i * d + j];
                if v < col_min[j] { col_min[j] = v; }
                if v > col_max[j] { col_max[j] = v; }
            }
        }

        let normalized: Vec<Vec<f64>> = (0..n)
            .map(|i| {
                (0..n_marks)
                    .map(|j| {
                        let range = col_max[j] - col_min[j];
                        if range > 0.0 {
                            (data[i * d + j] - col_min[j]) / range
                        } else {
                            0.5
                        }
                    })
                    .collect()
            })
            .collect();

        // Classify chromatin states based on mark combinations
        // Mark roles (when >= 6 marks available):
        //   0: H3K4me3 (active promoter)
        //   1: H3K27me3 (Polycomb repression)
        //   2: H3K36me3 (active transcription)
        //   3: H3K9me3 (heterochromatin)
        //   4: H3K27ac (active enhancer)
        //   5: H3K4me1 (poised enhancer)
        let mark_threshold = 0.5;
        let mut state_counts = [0usize; 5]; // active, poised, repressed, bivalent, quiescent
        let mut bivalent_count = 0usize;

        for i in 0..n {
            let marks = &normalized[i];
            let has_active = marks.get(0).map_or(false, |&v| v > mark_threshold)
                || marks.get(4).map_or(false, |&v| v > mark_threshold);
            let has_repressive = marks.get(1).map_or(false, |&v| v > mark_threshold)
                || marks.get(3).map_or(false, |&v| v > mark_threshold);
            let has_enhancer = marks.get(5).map_or(false, |&v| v > mark_threshold);

            if has_active && has_repressive {
                state_counts[3] += 1; // bivalent
                bivalent_count += 1;
            } else if has_active {
                state_counts[0] += 1; // active
            } else if has_enhancer && !has_repressive {
                state_counts[1] += 1; // poised
            } else if has_repressive {
                state_counts[2] += 1; // repressed
            } else {
                state_counts[4] += 1; // quiescent
            }
        }

        // Chromatin state entropy
        let state_probs: Vec<f64> = state_counts.iter().map(|&c| c as f64 / n as f64).collect();
        let state_entropy: f64 = state_probs
            .iter()
            .filter(|&&p| p > 0.0)
            .map(|p| -p * p.ln())
            .sum();

        // Epigenetic memory: autocorrelation of mark values across consecutive loci
        // Higher autocorrelation = stronger epigenetic memory (marks spread along chromatin)
        let mut memory_scores = Vec::with_capacity(n_marks);
        for j in 0..n_marks {
            if n < 3 {
                memory_scores.push(0.0);
                continue;
            }
            let vals: Vec<f64> = (0..n).map(|i| normalized[i][j]).collect();
            let mean: f64 = vals.iter().sum::<f64>() / n as f64;
            let var: f64 = vals.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / n as f64;
            if var < 1e-15 {
                memory_scores.push(0.0);
                continue;
            }
            // Lag-1 autocorrelation
            let autocorr: f64 = (0..(n - 1))
                .map(|i| (vals[i] - mean) * (vals[i + 1] - mean))
                .sum::<f64>()
                / ((n - 1) as f64 * var);
            memory_scores.push(autocorr.max(-1.0).min(1.0));
        }
        let mean_memory = memory_scores.iter().sum::<f64>() / n_marks as f64;

        // Mean mark co-occurrence (correlation between marks)
        let mut mark_corr_sum = 0.0f64;
        let mut mark_pairs = 0usize;
        for a in 0..n_marks {
            for b in (a + 1)..n_marks {
                let mean_a: f64 = (0..n).map(|i| normalized[i][a]).sum::<f64>() / n as f64;
                let mean_b: f64 = (0..n).map(|i| normalized[i][b]).sum::<f64>() / n as f64;
                let var_a: f64 = (0..n).map(|i| (normalized[i][a] - mean_a).powi(2)).sum::<f64>() / n as f64;
                let var_b: f64 = (0..n).map(|i| (normalized[i][b] - mean_b).powi(2)).sum::<f64>() / n as f64;
                if var_a > 1e-15 && var_b > 1e-15 {
                    let cov: f64 = (0..n)
                        .map(|i| (normalized[i][a] - mean_a) * (normalized[i][b] - mean_b))
                        .sum::<f64>() / n as f64;
                    mark_corr_sum += cov / (var_a.sqrt() * var_b.sqrt());
                }
                mark_pairs += 1;
            }
        }
        let mean_mark_correlation = if mark_pairs > 0 {
            mark_corr_sum / mark_pairs as f64
        } else {
            0.0
        };

        let bivalent_fraction = bivalent_count as f64 / n as f64;

        let mut result = HashMap::new();
        result.insert("chromatin_state_entropy".into(), vec![state_entropy]);
        result.insert("bivalent_fraction".into(), vec![bivalent_fraction]);
        result.insert("epigenetic_memory".into(), vec![mean_memory]);
        result.insert("mean_mark_correlation".into(), vec![mean_mark_correlation]);
        result.insert("active_fraction".into(), vec![state_probs[0]]);
        result.insert("repressed_fraction".into(), vec![state_probs[2]]);
        result.insert("n_marks".into(), vec![n_marks as f64]);
        result
    }
}
