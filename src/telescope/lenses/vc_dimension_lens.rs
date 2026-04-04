use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// VCDimensionLens: VC dimension and shattering analysis.
///
/// Computes VC dimension of data-induced hypothesis classes:
/// - Checks if subsets of size 6 can be shattered by halfplanes
/// - Growth function: max number of dichotomies on n points
/// - Sauer-Shelah bound: sum C(n,i) for i<=VC-dim
/// - Sample complexity from VC theory
pub struct VCDimensionLens;

impl Lens for VCDimensionLens {
    fn name(&self) -> &str { "VCDimensionLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        let _ = shared;
        if n < 4 || d == 0 { return HashMap::new(); }

        // Estimate VC dimension of linear classifiers: VC-dim = d + 1
        let linear_vc_dim = d + 1;

        // Check shattering: for subsets of size k, can all 2^k labelings be realized?
        // Test with random hyperplanes through data
        let test_size = n.min(6);
        let subset: Vec<usize> = (0..test_size).collect();

        // Generate hyperplane directions from pairs of data points
        let mut shattering_count = 0u64;
        let total_labelings = 1u64 << test_size;
        let mut achieved_labelings: std::collections::HashSet<u64> = std::collections::HashSet::new();

        // Use all pairs of points as hyperplane normals
        for i in 0..n.min(30) {
            for j in (i + 1)..n.min(30) {
                // Normal = data[j] - data[i]
                let mut normal: Vec<f64> = (0..d).map(|k| data[j * d + k] - data[i * d + k]).collect();
                let norm = normal.iter().map(|x| x * x).sum::<f64>().sqrt();
                if norm < 1e-15 { continue; }
                for x in &mut normal { *x /= norm; }

                // Try multiple thresholds
                let midpoint: Vec<f64> = (0..d).map(|k| (data[i * d + k] + data[j * d + k]) / 2.0).collect();
                let offsets = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0];

                for &offset in &offsets {
                    let threshold: f64 = normal.iter().zip(midpoint.iter())
                        .map(|(n, m)| n * m)
                        .sum::<f64>() + offset;

                    let mut labeling = 0u64;
                    for &idx in &subset {
                        let proj: f64 = (0..d).map(|k| normal[k] * data[idx * d + k]).sum();
                        if proj >= threshold {
                            labeling |= 1u64 << idx;
                        }
                    }
                    achieved_labelings.insert(labeling);
                }
            }
        }

        shattering_count = achieved_labelings.len() as u64;

        // Growth function: fraction of achievable dichotomies
        let growth_function = shattering_count as f64 / total_labelings as f64;

        // Empirical VC dimension: largest k where all 2^k labelings achieved
        let mut empirical_vc = 0;
        for k in 1..=test_size {
            let expected = 1u64 << k;
            // Count labelings restricted to first k points
            let mut restricted: std::collections::HashSet<u64> = std::collections::HashSet::new();
            let mask = (1u64 << k) - 1;
            for &lab in &achieved_labelings {
                restricted.insert(lab & mask);
            }
            if restricted.len() as u64 >= expected {
                empirical_vc = k;
            } else {
                break;
            }
        }

        // Sauer-Shelah bound: Pi_d(n) <= sum_{i=0}^{vc} C(n, i)
        let sauer_shelah = sauer_shelah_bound(n, empirical_vc);

        // Sample complexity for PAC learning: m >= (4/eps) * (vc * ln(2/eps) + ln(2/delta))
        let epsilon: f64 = 0.1;
        let delta: f64 = 0.05;
        let sample_complexity = (4.0 / epsilon) *
            (empirical_vc as f64 * (2.0_f64 / epsilon).ln() + (2.0_f64 / delta).ln());

        // n=6 resonance: how close is empirical VC-dim to 6
        let n6_vc_match = (-((empirical_vc as f64 - 6.0).abs() * 0.3)).exp();

        // Rademacher complexity bound from VC-dim: R_n <= sqrt(vc * ln(n) / n)
        let rademacher_from_vc = if n > 0 {
            ((empirical_vc as f64 * (n as f64).ln()) / n as f64).sqrt()
        } else { 0.0 };

        let mut result = HashMap::new();
        result.insert("linear_vc_dimension".into(), vec![linear_vc_dim as f64]);
        result.insert("empirical_vc_dimension".into(), vec![empirical_vc as f64]);
        result.insert("growth_function".into(), vec![growth_function]);
        result.insert("shattering_count".into(), vec![shattering_count as f64]);
        result.insert("sauer_shelah_bound".into(), vec![sauer_shelah as f64]);
        result.insert("sample_complexity".into(), vec![sample_complexity]);
        result.insert("rademacher_from_vc".into(), vec![rademacher_from_vc]);
        result.insert("n6_vc_match".into(), vec![n6_vc_match]);
        result
    }
}

fn sauer_shelah_bound(n: usize, vc: usize) -> u64 {
    let mut sum = 0u64;
    for i in 0..=vc {
        sum = sum.saturating_add(binomial(n, i));
    }
    sum
}

fn binomial(n: usize, k: usize) -> u64 {
    if k > n { return 0; }
    if k == 0 || k == n { return 1; }
    let k = k.min(n - k);
    let mut result = 1u64;
    for i in 0..k {
        result = result.saturating_mul((n - i) as u64) / (i as u64 + 1);
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vc_dimension() {
        // Points in 2D: VC-dim of linear classifiers = 3
        let data = vec![
            0.0, 0.0,
            1.0, 0.0,
            0.0, 1.0,
            1.0, 1.0,
            0.5, 0.5,
            2.0, 2.0,
            -1.0, 0.5,
            0.5, -1.0,
        ];
        let n = 8;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = VCDimensionLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("empirical_vc_dimension"));
        assert!(r["linear_vc_dimension"][0] == 3.0);
        assert!(r["growth_function"][0] > 0.0);
    }
}
