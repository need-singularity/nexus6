use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors};

/// BandStructureLens: 6-band condensed matter model with band gap analysis.
///
/// Models electronic band structure by treating data dimensions as
/// reciprocal-space coordinates (k-points) and values as energy eigenvalues.
/// Detects band gaps, band crossings (Dirac points), and van Hove
/// singularities in the density of states.
///
/// In a 6-band model (e.g., graphene with spin-orbit coupling), the
/// Hamiltonian H(k) is a 6x6 matrix at each k-point.
///
/// Metrics:
///   1. band_gaps: energy gaps between consecutive bands
///   2. max_band_gap: largest gap (fundamental gap)
///   3. density_of_states: DOS at 6 energy levels
///   4. dirac_point_count: number of band crossing points
///   5. bandwidth: total width of each band
///   6. van_hove_singularities: peaks in DOS (critical points)
///
/// n=6: 6-band model, 6 energy eigenvalues per k-point.
pub struct BandStructureLens;

impl Lens for BandStructureLens {
    fn name(&self) -> &str { "BandStructureLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let n_bands: usize = d.min(6);

        // Treat each row as a k-point, each dimension as an energy band
        // Sort each "band" (column) to get band structure
        let columns = column_vectors(data, n, d);

        // For each k-point, sort the d eigenvalues to get ordered bands
        let mut bands: Vec<Vec<f64>> = vec![Vec::with_capacity(n); n_bands];
        for i in 0..n {
            let mut eigvals: Vec<f64> = (0..n_bands)
                .map(|j| columns[j][i])
                .collect();
            eigvals.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            for (b, &val) in eigvals.iter().enumerate() {
                bands[b].push(val);
            }
        }

        // Band statistics
        let mut band_mins = Vec::with_capacity(n_bands);
        let mut band_maxs = Vec::with_capacity(n_bands);
        let mut bandwidths = Vec::with_capacity(n_bands);

        for b in 0..n_bands {
            let min_val = bands[b].iter().cloned().fold(f64::INFINITY, f64::min);
            let max_val = bands[b].iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            band_mins.push(min_val);
            band_maxs.push(max_val);
            bandwidths.push(max_val - min_val);
        }

        // Band gaps: min of upper band - max of lower band
        let mut band_gaps = Vec::with_capacity(n_bands - 1);
        let mut max_gap = 0.0f64;
        for b in 0..(n_bands - 1) {
            let gap = band_mins[b + 1] - band_maxs[b];
            band_gaps.push(gap);
            if gap > max_gap { max_gap = gap; }
        }

        // Dirac points: k-points where adjacent bands touch or cross
        let mut dirac_count = 0u32;
        for i in 0..n {
            for b in 0..(n_bands - 1) {
                let gap_at_k = bands[b + 1][i] - bands[b][i];
                if gap_at_k.abs() < bandwidths[b].max(bandwidths[b.min(n_bands - 1)]) * 0.01 {
                    dirac_count += 1;
                }
            }
        }

        // Density of states: histogram of all eigenvalues
        let all_energies: Vec<f64> = bands.iter().flat_map(|b| b.iter().cloned()).collect();
        let e_min = all_energies.iter().cloned().fold(f64::INFINITY, f64::min);
        let e_max = all_energies.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let e_range = (e_max - e_min).max(1e-12);

        let n_bins: usize = 6; // 6 energy bins for n=6 connection
        let mut dos = vec![0.0f64; n_bins];
        for &e in &all_energies {
            let bin = ((e - e_min) / e_range * (n_bins - 1) as f64) as usize;
            dos[bin.min(n_bins - 1)] += 1.0;
        }
        // Normalize DOS
        let dos_sum: f64 = dos.iter().sum();
        if dos_sum > 0.0 {
            for d in dos.iter_mut() { *d /= dos_sum; }
        }

        // Van Hove singularities: peaks in DOS
        let mut van_hove = Vec::new();
        for i in 1..(n_bins - 1) {
            if dos[i] > dos[i - 1] && dos[i] > dos[i + 1] {
                let energy = e_min + (i as f64 + 0.5) * e_range / n_bins as f64;
                van_hove.push(energy);
            }
        }

        let mut result = HashMap::new();
        result.insert("band_gaps".to_string(), band_gaps);
        result.insert("max_band_gap".to_string(), vec![max_gap]);
        result.insert("density_of_states".to_string(), dos);
        result.insert("dirac_point_count".to_string(), vec![dirac_count as f64]);
        result.insert("bandwidth".to_string(), bandwidths);
        result.insert("van_hove_singularities".to_string(), van_hove);
        result.insert("score".to_string(), vec![result["band_gaps"][0].min(1.0).max(0.0)]);
        result
    }
}
