use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// BaryogenesisLens: 6-quark mixing and Sakharov conditions for baryogenesis.
///
/// Checks the three Sakharov conditions required for matter-antimatter
/// asymmetry (baryogenesis):
///   1. Baryon number violation (B-violation)
///   2. C and CP violation
///   3. Departure from thermal equilibrium
///
/// In the Standard Model with 6 quarks, sphaleron processes can violate
/// B+L while conserving B-L. The baryon asymmetry η_B ≈ 6 × 10⁻¹⁰.
///
/// We detect these conditions in data:
///   - B-violation: conservation law breaking (sum of quantities not conserved)
///   - CP violation: asymmetry in conjugate processes
///   - Non-equilibrium: deviation from thermal (Gaussian) distribution
///
/// Metrics:
///   1. baryon_asymmetry: net matter-antimatter imbalance
///   2. b_violation_score: how strongly conservation is violated
///   3. cp_violation_score: asymmetry strength
///   4. thermal_departure: deviation from equilibrium
///   5. sphaleron_rate: rate of topology-changing transitions
///   6. sakharov_score: product of all three conditions
///
/// n=6: 6 quark flavors, 6 × 10⁻¹⁰ baryon asymmetry.
pub struct BaryogenesisLens;

impl Lens for BaryogenesisLens {
    fn name(&self) -> &str { "BaryogenesisLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);
        let stds: Vec<f64> = vars.iter().map(|v| v.sqrt().max(1e-12)).collect();
        let n_quarks = d.min(6);

        // 1. Baryon number violation: check if "conserved charges" drift
        // Assign baryon number B = +1/3 to first half of dims, -1/3 to second half
        // Check if total B is conserved across data points
        let mut baryon_numbers = Vec::with_capacity(n);
        for i in 0..n {
            let mut b = 0.0f64;
            for dim in 0..n_quarks {
                let sign = if dim < n_quarks / 2 { 1.0 / 3.0 } else { -1.0 / 3.0 };
                b += sign * columns[dim][i];
            }
            baryon_numbers.push(b);
        }

        let b_mean = baryon_numbers.iter().sum::<f64>() / n as f64;
        let b_var = baryon_numbers.iter()
            .map(|&b| (b - b_mean).powi(2))
            .sum::<f64>() / n as f64;

        // B-violation: non-zero variance of baryon number means it's not conserved
        let b_violation = b_var.sqrt() / (b_mean.abs().max(1e-12));

        // Baryon asymmetry: net baryon number normalized
        let total_scale: f64 = vars.iter().sum::<f64>().sqrt().max(1e-12);
        let baryon_asymmetry = b_mean / total_scale;

        // 2. CP violation: asymmetry under parity (x → -x) transformation
        // Compare distribution of +x and -x
        let mut cp_violation = 0.0f64;
        for dim in 0..n_quarks {
            let mut pos_count = 0u32;
            let mut neg_count = 0u32;
            let mut pos_sum = 0.0f64;
            let mut neg_sum = 0.0f64;
            for i in 0..n {
                let z = (columns[dim][i] - means[dim]) / stds[dim];
                if z > 0.0 {
                    pos_count += 1;
                    pos_sum += z;
                } else {
                    neg_count += 1;
                    neg_sum += z.abs();
                }
            }
            // CP asymmetry: difference in mean magnitude
            let pos_mean = if pos_count > 0 { pos_sum / pos_count as f64 } else { 0.0 };
            let neg_mean = if neg_count > 0 { neg_sum / neg_count as f64 } else { 0.0 };
            let total_mean = (pos_mean + neg_mean).max(1e-12);
            cp_violation += (pos_mean - neg_mean).abs() / total_mean;
        }
        cp_violation /= n_quarks as f64;

        // 3. Thermal departure: how non-Gaussian the data is
        // Measure kurtosis excess (Gaussian → 0)
        let mut kurtosis_sum = 0.0f64;
        for dim in 0..n_quarks {
            let mut m4 = 0.0f64;
            for i in 0..n {
                let z = (columns[dim][i] - means[dim]) / stds[dim];
                m4 += z.powi(4);
            }
            m4 /= n as f64;
            kurtosis_sum += (m4 - 3.0).abs(); // Excess kurtosis
        }
        let thermal_departure = kurtosis_sum / n_quarks as f64;

        // 4. Sphaleron rate: topology-changing transitions
        // Detect "jumps" in the baryon number time series
        let mut jump_count = 0u32;
        let jump_threshold = b_var.sqrt() * 2.0;
        for i in 1..n {
            if (baryon_numbers[i] - baryon_numbers[i - 1]).abs() > jump_threshold {
                jump_count += 1;
            }
        }
        let sphaleron_rate = jump_count as f64 / (n - 1).max(1) as f64;

        // 5. Sakharov score: all three conditions must be met
        // Score = B_violation × CP_violation × thermal_departure
        let sakharov = b_violation.min(10.0)
            * cp_violation.min(10.0)
            * thermal_departure.min(10.0);

        let mut result = HashMap::new();
        result.insert("baryon_asymmetry".to_string(), vec![baryon_asymmetry]);
        result.insert("b_violation_score".to_string(), vec![b_violation]);
        result.insert("cp_violation_score".to_string(), vec![cp_violation]);
        result.insert("thermal_departure".to_string(), vec![thermal_departure]);
        result.insert("sphaleron_rate".to_string(), vec![sphaleron_rate]);
        result.insert("sakharov_score".to_string(), vec![sakharov]);
        result
    }
}
