use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// Musical interval ratios rooted in n=6 harmonic series.
/// The 6th harmonic (6/5 = minor third) is the characteristic n=6 interval.
const HARMONIC_RATIOS: &[(f64, &str, f64)] = &[
    (1.0,       "unison (1/1)",          0.0),
    (2.0,       "octave (2/1)",          1.0),
    (1.5,       "perfect fifth (3/2)",   0.95),
    (1.333333,  "perfect fourth (4/3)",  0.9),
    (1.25,      "major third (5/4)",     0.85),
    (1.2,       "minor third (6/5)",     1.0),  // n=6 signature interval
];

/// Number of harmonics in the series to check (n=6).
const N_HARMONICS: usize = 6;

/// HarmonicSeriesLens: Detect harmonic-series structure in data.
///
/// Maps music theory's harmonic series (overtone ratios up to the 6th partial)
/// onto numerical data. Measures how well value ratios align with
/// consonant intervals, with special weight on the 6/5 minor third.
///
/// Metrics: consonance_score, harmonic_alignment, series_completeness,
///          dissonance_tension, interval_diversity, n6_harmonic_score
pub struct HarmonicSeriesLens;

impl Lens for HarmonicSeriesLens {
    fn name(&self) -> &str { "HarmonicSeriesLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let (means, vars) = mean_var(data, n, d);
        let columns = column_vectors(data, n, d);

        // 1. Consonance score: how many pairwise feature-mean ratios match harmonic intervals
        let mut consonance_hits = 0.0;
        let mut consonance_total = 0.0;
        for i in 0..d {
            for j in (i + 1)..d {
                if means[j].abs() < 1e-12 || means[i].abs() < 1e-12 { continue; }
                let ratio = (means[i] / means[j]).abs();
                let ratio_inv = 1.0 / ratio;
                consonance_total += 1.0;
                for &(target, _, weight) in HARMONIC_RATIOS {
                    if target < 1e-12 { continue; }
                    if (ratio - target).abs() < 0.05 || (ratio_inv - target).abs() < 0.05 {
                        consonance_hits += weight;
                        break;
                    }
                }
            }
        }
        let consonance_score = if consonance_total > 0.0 {
            (consonance_hits / consonance_total).min(1.0)
        } else { 0.0 };

        // 2. Harmonic alignment: per-column, check if sorted values form harmonic ratios
        let mut alignment_sum = 0.0;
        for col in &columns {
            let mut sorted: Vec<f64> = col.iter().copied().filter(|x| x.abs() > 1e-12).collect();
            sorted.sort_by(|a, b| a.abs().partial_cmp(&b.abs()).unwrap());
            if sorted.len() < 2 { continue; }
            let base = sorted[0].abs();
            if base < 1e-12 { continue; }
            let mut col_alignment = 0.0;
            let count = sorted.len().min(N_HARMONICS);
            for k in 1..count {
                let ratio = sorted[k].abs() / base;
                // Expected harmonic ratio: (k+1)/1
                let expected = (k + 1) as f64;
                let deviation = (ratio - expected).abs() / expected;
                col_alignment += (-deviation).exp();
            }
            alignment_sum += col_alignment / (count.max(1) - 1).max(1) as f64;
        }
        let harmonic_alignment = alignment_sum / d.max(1) as f64;

        // 3. Series completeness: of the 6 harmonic ratios, how many appear in the data?
        let mut found = [false; 6];
        for col in &columns {
            let mut sorted: Vec<f64> = col.iter().copied().filter(|x| x.abs() > 1e-12).collect();
            sorted.sort_by(|a, b| a.abs().partial_cmp(&b.abs()).unwrap());
            for w in sorted.windows(2) {
                let ratio = w[1].abs() / w[0].abs().max(1e-12);
                for (idx, &(target, _, _)) in HARMONIC_RATIOS.iter().enumerate() {
                    if target < 1e-12 { continue; }
                    if (ratio - target).abs() < 0.08 {
                        found[idx] = true;
                    }
                }
            }
        }
        let series_completeness = found.iter().filter(|&&f| f).count() as f64 / N_HARMONICS as f64;

        // 4. Dissonance tension: fraction of adjacent-value ratios that do NOT match any consonance
        let mut dissonant = 0.0;
        let mut total_pairs = 0.0;
        for col in &columns {
            for w in col.windows(2) {
                if w[0].abs() < 1e-12 { continue; }
                let ratio = (w[1] / w[0]).abs();
                total_pairs += 1.0;
                let mut is_consonant = false;
                for &(target, _, _) in HARMONIC_RATIOS {
                    if target < 1e-12 { continue; }
                    if (ratio - target).abs() < 0.1 || (1.0 / ratio - target).abs() < 0.1 {
                        is_consonant = true;
                        break;
                    }
                }
                if !is_consonant { dissonant += 1.0; }
            }
        }
        let dissonance_tension = if total_pairs > 0.0 { dissonant / total_pairs } else { 0.0 };

        // 5. Interval diversity: Shannon entropy over interval classes
        let mut interval_counts = vec![0u32; HARMONIC_RATIOS.len() + 1]; // last = "other"
        for col in &columns {
            for w in col.windows(2) {
                if w[0].abs() < 1e-12 { continue; }
                let ratio = (w[1] / w[0]).abs();
                let mut matched = false;
                for (idx, &(target, _, _)) in HARMONIC_RATIOS.iter().enumerate() {
                    if target < 1e-12 { continue; }
                    if (ratio - target).abs() < 0.1 || (1.0 / ratio - target).abs() < 0.1 {
                        interval_counts[idx] += 1;
                        matched = true;
                        break;
                    }
                }
                if !matched { *interval_counts.last_mut().unwrap() += 1; }
            }
        }
        let total_intervals: u32 = interval_counts.iter().sum();
        let interval_diversity = if total_intervals > 0 {
            let mut ent = 0.0;
            for &c in &interval_counts {
                if c > 0 {
                    let p = c as f64 / total_intervals as f64;
                    ent -= p * p.ln();
                }
            }
            ent / (interval_counts.len() as f64).ln() // normalize to [0,1]
        } else { 0.0 };

        // Composite n6 score weighted toward the 6/5 signature
        let n6_harmonic_score = 0.25 * consonance_score
            + 0.20 * harmonic_alignment.min(1.0)
            + 0.20 * series_completeness
            + 0.15 * (1.0 - dissonance_tension) // lower tension = more harmonic
            + 0.20 * interval_diversity;

        let mut result = HashMap::new();
        result.insert("consonance_score".into(), vec![consonance_score]);
        result.insert("harmonic_alignment".into(), vec![harmonic_alignment]);
        result.insert("series_completeness".into(), vec![series_completeness]);
        result.insert("dissonance_tension".into(), vec![dissonance_tension]);
        result.insert("interval_diversity".into(), vec![interval_diversity]);
        result.insert("n6_harmonic_score".into(), vec![n6_harmonic_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_harmonic_series_basic() {
        // Data with harmonic-series ratios: 1, 2, 3, 4, 5, 6 (fundamental * n)
        let data: Vec<f64> = (0..60).map(|i| {
            let row = i / 6;
            let col = i % 6;
            (col + 1) as f64 * (1.0 + 0.1 * row as f64)
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = HarmonicSeriesLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("consonance_score"));
        assert!(result.contains_key("n6_harmonic_score"));
        assert!(result["n6_harmonic_score"][0] >= 0.0);
    }
}
