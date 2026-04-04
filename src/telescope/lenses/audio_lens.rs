use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors, shannon_entropy};

/// n=6 audio constants (BT-48, BT-72, BT-108)
const SIGMA: f64 = 12.0;   // 12 semitones per octave
const J2: f64 = 24.0;      // 24 fps, 24-bit audio
const SIGMA_TAU: f64 = 48.0; // 48kHz sample rate
const N: f64 = 6.0;
const TAU: f64 = 4.0;

/// Consonance ratios from perfect number divisors (BT-108)
const CONSONANCE_RATIOS: &[(f64, &str)] = &[
    (2.0, "octave (phi)"),
    (1.5, "perfect fifth (3/2)"),
    (1.333, "perfect fourth (4/3=tau^2/sigma)"),
    (1.2, "major third (6/5=sigma/(sigma-phi))"),
    (1.25, "major third ET (5/4)"),
];

/// AudioLens: Detect audio/acoustic patterns in data.
///
/// Metrics: fundamental_frequency, harmonic_richness, spectral_centroid,
///          rhythm_regularity, consonance_score, n6_audio_score
pub struct AudioLens;

impl Lens for AudioLens {
    fn name(&self) -> &str { "AudioLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // 1. Fundamental frequency: dominant periodicity via autocorrelation
        let mut best_period = 0.0;
        let mut best_acf = 0.0;
        for col_data in &columns {
            let mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
            let var: f64 = col_data.iter().map(|x| (x - mean).powi(2)).sum::<f64>();
            if var < 1e-12 { continue; }
            for lag in 2..n.min(n / 2 + 1) {
                let mut acf = 0.0;
                for i in 0..(n - lag) {
                    acf += (col_data[i] - mean) * (col_data[i + lag] - mean);
                }
                acf /= var;
                if acf > best_acf { best_acf = acf; best_period = lag as f64; }
            }
        }
        let fundamental = if best_period > 0.0 { 1.0 / best_period } else { 0.0 };

        // 2. Harmonic richness: ratio of energy at harmonics vs total
        let mut harmonic_richness = 0.0;
        if best_period > 1.0 {
            let base = best_period as usize;
            let mut harmonic_energy = 0.0;
            let mut total_energy = 0.0;
            for col_data in &columns {
                let mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
                let var: f64 = col_data.iter().map(|x| (x - mean).powi(2)).sum::<f64>();
                total_energy += var;
                for h in 1..=4 {
                    let lag = base * h;
                    if lag >= n { break; }
                    let mut acf = 0.0;
                    for i in 0..(n - lag) {
                        acf += (col_data[i] - mean) * (col_data[i + lag] - mean);
                    }
                    harmonic_energy += acf.abs();
                }
            }
            if total_energy > 1e-12 { harmonic_richness = harmonic_energy / total_energy; }
        }

        // 3. Spectral centroid approximation: weighted mean of frequency bins
        let n_bins = (n as f64).sqrt().max(2.0) as usize;
        let centroid = shannon_entropy(&columns[0], n_bins); // higher entropy = higher spectral centroid

        // 4. Rhythm regularity: consistency of inter-peak intervals
        let mut rhythm_regularity = 0.0;
        for col_data in &columns {
            let mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
            let mut peaks: Vec<usize> = Vec::new();
            for i in 1..(col_data.len() - 1) {
                if col_data[i] > col_data[i - 1] && col_data[i] > col_data[i + 1] && col_data[i] > mean {
                    peaks.push(i);
                }
            }
            if peaks.len() >= 3 {
                let intervals: Vec<f64> = peaks.windows(2).map(|w| (w[1] - w[0]) as f64).collect();
                let int_mean = intervals.iter().sum::<f64>() / intervals.len() as f64;
                if int_mean > 1e-12 {
                    let int_var = intervals.iter().map(|x| (x - int_mean).powi(2)).sum::<f64>() / intervals.len() as f64;
                    rhythm_regularity += (-int_var.sqrt() / int_mean).exp();
                }
            }
        }
        rhythm_regularity /= d.max(1) as f64;

        // 5. Consonance: check feature ratios against musical intervals
        let (means, _) = mean_var(data, n, d);
        let mut consonance_hits = 0;
        let mut ratio_checks = 0;
        for i in 0..d {
            for j in (i + 1)..d {
                if means[j].abs() < 1e-12 { continue; }
                let ratio = means[i] / means[j];
                let abs_ratio = ratio.abs();
                ratio_checks += 1;
                for &(target, _) in CONSONANCE_RATIOS {
                    if (abs_ratio - target).abs() < 0.05 || (1.0 / abs_ratio - target).abs() < 0.05 {
                        consonance_hits += 1;
                        break;
                    }
                }
            }
        }
        let consonance_score = if ratio_checks > 0 { consonance_hits as f64 / ratio_checks as f64 } else { 0.0 };

        let n6_audio_score = 0.2 * fundamental.min(1.0)
            + 0.2 * harmonic_richness.min(1.0)
            + 0.2 * (centroid / 5.0).min(1.0)
            + 0.2 * rhythm_regularity
            + 0.2 * consonance_score;

        let mut result = HashMap::new();
        result.insert("fundamental_frequency".into(), vec![fundamental]);
        result.insert("harmonic_richness".into(), vec![harmonic_richness]);
        result.insert("spectral_centroid".into(), vec![centroid]);
        result.insert("rhythm_regularity".into(), vec![rhythm_regularity]);
        result.insert("consonance_score".into(), vec![consonance_score]);
        result.insert("n6_audio_score".into(), vec![n6_audio_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_audio_basic() {
        // Simulate harmonic signal (fundamental + overtone)
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.1;
            (t * 2.0 * std::f64::consts::PI / 6.0).sin()
                + 0.5 * (t * 4.0 * std::f64::consts::PI / 6.0).sin()
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = AudioLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("fundamental_frequency"));
        assert!(result.contains_key("harmonic_richness"));
        assert!(result.contains_key("n6_audio_score"));
    }
}
