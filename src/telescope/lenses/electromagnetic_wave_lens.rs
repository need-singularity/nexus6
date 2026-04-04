use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ElectromagneticWaveLens: Analyze EM wave propagation, polarization, and interference patterns.
///
/// Algorithm:
///   1. Treat each data point as a source emitter; compute wave amplitude at each point
///      from all other sources using inverse-distance with phase: A_ij = cos(k * d_ij) / d_ij
///   2. Superposition: total field at point i = sum of contributions from all j != i
///   3. Interference pattern: classify constructive (|total| > mean) vs destructive
///   4. Polarization analysis: treat consecutive dimension pairs as (E_x, E_y) components,
///      compute ellipticity and degree of polarization
///   5. Standing wave ratio: max_amplitude / min_amplitude (analogous to VSWR)
pub struct UelectromagneticUwaveLens;

impl Lens for UelectromagneticUwaveLens {
    fn name(&self) -> &str {
        "electromagnetic_wave"
    }

    fn category(&self) -> &str {
        "T0"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 {
            return HashMap::new();
        }

        // ── 1. Wave propagation: superposition of spherical waves ──
        // Choose wavenumber k from median distance so that phase varies meaningfully
        let pair_count = n * (n - 1) / 2;
        let mut all_dists: Vec<f64> = Vec::with_capacity(pair_count);
        for i in 0..n {
            for j in (i + 1)..n {
                all_dists.push(shared.dist(i, j));
            }
        }
        all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median_dist = all_dists[pair_count / 2];
        // k chosen so that one median distance = one full wavelength
        let k = if median_dist > 1e-12 {
            2.0 * std::f64::consts::PI / median_dist
        } else {
            1.0
        };

        // Compute superposed amplitude at each point
        let mut amplitudes: Vec<f64> = Vec::with_capacity(n);
        for i in 0..n {
            let mut field_real = 0.0_f64;
            let mut field_imag = 0.0_f64;
            for j in 0..n {
                if i == j {
                    continue;
                }
                let dist = shared.dist(i, j);
                if dist < 1e-15 {
                    continue;
                }
                let phase = k * dist;
                // Complex phasor: e^{i*k*r} / r
                field_real += phase.cos() / dist;
                field_imag += phase.sin() / dist;
            }
            amplitudes.push((field_real * field_real + field_imag * field_imag).sqrt());
        }

        // ── 2. Interference classification ──
        let mean_amp = amplitudes.iter().sum::<f64>() / n as f64;
        let mut constructive_count = 0usize;
        let mut destructive_count = 0usize;
        for &a in &amplitudes {
            if a > mean_amp {
                constructive_count += 1;
            } else {
                destructive_count += 1;
            }
        }
        let interference_ratio = constructive_count as f64 / n as f64;

        // ── 3. Standing wave ratio (VSWR analogue) ──
        let max_amp = amplitudes.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let min_amp = amplitudes.iter().cloned().fold(f64::INFINITY, f64::min);
        let standing_wave_ratio = if min_amp > 1e-15 {
            max_amp / min_amp
        } else {
            f64::INFINITY
        };

        // ── 4. Polarization analysis ──
        // Treat dimension pairs (0,1), (2,3), ... as E-field components
        let num_polarization_pairs = d / 2;
        let mut total_ellipticity = 0.0_f64;
        let mut total_dop = 0.0_f64; // degree of polarization
        let mut pol_count = 0usize;

        for p in 0..num_polarization_pairs {
            let dx = p * 2;
            let dy = p * 2 + 1;

            // Compute Stokes parameters across all points
            let mut s0 = 0.0_f64; // total intensity
            let mut s1 = 0.0_f64; // horizontal vs vertical
            let mut s2 = 0.0_f64; // diagonal
            let mut s3 = 0.0_f64; // circular (approximate via cross-correlation)

            for i in 0..n {
                let ex = data[i * d + dx];
                let ey = data[i * d + dy];
                s0 += ex * ex + ey * ey;
                s1 += ex * ex - ey * ey;
                s2 += 2.0 * ex * ey;
                // s3 approximated: phase difference proxy from neighboring points
                if i + 1 < n {
                    let ex_next = data[(i + 1) * d + dx];
                    let ey_next = data[(i + 1) * d + dy];
                    s3 += ex * ey_next - ey * ex_next;
                }
            }

            if s0.abs() > 1e-15 {
                let dop = (s1 * s1 + s2 * s2 + s3 * s3).sqrt() / s0;
                total_dop += dop.min(1.0);

                // Ellipticity: sin(2*chi) = S3 / sqrt(S1^2 + S2^2 + S3^2)
                let pol_mag = (s1 * s1 + s2 * s2 + s3 * s3).sqrt();
                if pol_mag > 1e-15 {
                    let sin_2chi = (s3 / pol_mag).clamp(-1.0, 1.0);
                    let chi = sin_2chi.asin() / 2.0;
                    total_ellipticity += chi.abs();
                }
                pol_count += 1;
            }
        }

        let avg_ellipticity = if pol_count > 0 {
            total_ellipticity / pol_count as f64
        } else {
            0.0
        };
        let avg_dop = if pol_count > 0 {
            total_dop / pol_count as f64
        } else {
            0.0
        };

        // ── 5. Amplitude variance (field uniformity) ──
        let amp_variance = {
            let var = amplitudes
                .iter()
                .map(|a| (a - mean_amp) * (a - mean_amp))
                .sum::<f64>()
                / n as f64;
            var.sqrt()
        };

        // ── Build result ──
        let mut result = HashMap::new();
        result.insert("amplitudes".to_string(), amplitudes);
        result.insert(
            "interference".to_string(),
            vec![
                interference_ratio,
                constructive_count as f64,
                destructive_count as f64,
            ],
        );
        result.insert("standing_wave_ratio".to_string(), vec![standing_wave_ratio]);
        result.insert(
            "polarization".to_string(),
            vec![avg_ellipticity, avg_dop],
        );
        result.insert(
            "field_stats".to_string(),
            vec![mean_amp, amp_variance, max_amp, min_amp],
        );
        result.insert("wavenumber".to_string(), vec![k]);
        result.insert("score".to_string(), vec![result["amplitudes"][0].min(1.0).max(0.0)]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    fn make_shared(data: &[f64], n: usize, d: usize) -> SharedData {
        SharedData::compute(data, n, d)
    }

    #[test]
    fn test_em_wave_basic_output() {
        // 5 points in 2D arranged in a line
        let data: Vec<f64> = vec![
            0.0, 0.0,
            1.0, 0.0,
            2.0, 0.0,
            3.0, 0.0,
            4.0, 0.0,
        ];
        let n = 5;
        let d = 2;
        let shared = make_shared(&data, n, d);
        let lens = UelectromagneticUwaveLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "Result should not be empty");
        assert!(result.contains_key("amplitudes"));
        assert!(result.contains_key("interference"));
        assert!(result.contains_key("standing_wave_ratio"));
        assert!(result.contains_key("polarization"));
        assert!(result.contains_key("field_stats"));
        assert!(result.contains_key("wavenumber"));

        let amps = &result["amplitudes"];
        assert_eq!(amps.len(), n);
        // All amplitudes should be positive for a non-degenerate configuration
        for a in amps {
            assert!(*a > 0.0, "Amplitude should be positive, got {}", a);
        }

        let interference = &result["interference"];
        assert_eq!(interference.len(), 3);
        // constructive + destructive = n
        assert_eq!(
            interference[1] as usize + interference[2] as usize,
            n,
            "constructive + destructive should equal n"
        );
    }

    #[test]
    fn test_em_wave_polarization_and_swr() {
        // 4 points in 4D (2 polarization pairs)
        let data: Vec<f64> = vec![
            1.0, 2.0, 0.5, 0.3,
            2.0, 1.0, 1.5, 0.7,
            0.5, 3.0, 1.0, 2.0,
            3.0, 0.5, 2.0, 1.0,
        ];
        let n = 4;
        let d = 4;
        let shared = make_shared(&data, n, d);
        let lens = UelectromagneticUwaveLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty(), "Result should not be empty");

        // Polarization should have 2 values: ellipticity and degree of polarization
        let pol = &result["polarization"];
        assert_eq!(pol.len(), 2);
        assert!(pol[0] >= 0.0, "Ellipticity should be non-negative");
        assert!(pol[1] >= 0.0 && pol[1] <= 1.0 + 1e-9, "DoP should be in [0,1]");

        // Standing wave ratio should be >= 1
        let swr = result["standing_wave_ratio"][0];
        assert!(swr >= 1.0, "SWR should be >= 1, got {}", swr);

        // field_stats: [mean, stddev, max, min]
        let stats = &result["field_stats"];
        assert_eq!(stats.len(), 4);
        assert!(stats[2] >= stats[3], "max >= min");
    }
}
