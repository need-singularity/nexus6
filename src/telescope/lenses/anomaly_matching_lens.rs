use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var};

/// AnomalyMatchingLens: 6-flavor QCD triangle anomaly detection.
///
/// Detects anomalous symmetry breaking by analyzing triangle diagrams
/// in data space. For each triple of dimensions (i,j,k), computes the
/// third-order correlation (analogous to the triangle diagram amplitude).
/// Non-vanishing correlations signal anomalous Ward identities.
///
/// In QCD with 6 flavors, the ABJ anomaly: ∂_μ j^μ₅ = (Nf·g²)/(16π²) F·F̃
/// We check all C(d,3) triangles for anomalous (asymmetric) contributions.
///
/// Metrics:
///   1. triangle_anomaly: max |⟨XᵢXⱼXₖ⟩| across all dimension triples
///   2. anomaly_per_flavor: anomaly strength for each of 6 dimension groups
///   3. anomaly_cancellation: how well anomalies cancel (gauge consistency)
///   4. chiral_asymmetry: left-right asymmetry in data distribution
///
/// n=6: 6-flavor QCD, 6 quarks (u,d,s,c,b,t).
pub struct AnomalyMatchingLens;

impl Lens for AnomalyMatchingLens {
    fn name(&self) -> &str { "AnomalyMatchingLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 3 { return HashMap::new(); }

        let (means, vars) = mean_var(data, n, d);
        let stds: Vec<f64> = vars.iter().map(|v| v.sqrt().max(1e-12)).collect();

        // Triangle anomaly: compute third-order cumulant ⟨XᵢXⱼXₖ⟩_c
        // for all dimension triples (up to a budget)
        let max_dims = d.min(12);
        let mut max_anomaly = 0.0f64;
        let mut anomaly_sum = 0.0f64;
        let mut triangle_count = 0u32;

        for di in 0..max_dims {
            for dj in (di + 1)..max_dims {
                for dk in (dj + 1)..max_dims {
                    // Third cumulant: ⟨(Xᵢ-μᵢ)(Xⱼ-μⱼ)(Xₖ-μₖ)⟩ / (σᵢσⱼσₖ)
                    let mut c3 = 0.0f64;
                    for row in 0..n {
                        let xi = (data[row * d + di] - means[di]) / stds[di];
                        let xj = (data[row * d + dj] - means[dj]) / stds[dj];
                        let xk = (data[row * d + dk] - means[dk]) / stds[dk];
                        c3 += xi * xj * xk;
                    }
                    c3 /= n as f64;
                    let abs_c3 = c3.abs();
                    if abs_c3 > max_anomaly { max_anomaly = abs_c3; }
                    anomaly_sum += abs_c3;
                    triangle_count += 1;
                }
            }
        }

        // Anomaly per flavor: group dimensions into 6 "flavor" bins
        let n_flavors: usize = 6;
        let dims_per_flavor = (d + n_flavors - 1) / n_flavors;
        let mut anomaly_per_flavor = vec![0.0f64; n_flavors];

        for f in 0..n_flavors {
            let start = f * dims_per_flavor;
            let end = ((f + 1) * dims_per_flavor).min(d);
            if start >= d { break; }

            // Skewness of this flavor group as anomaly proxy
            let mut skew_sum = 0.0f64;
            let mut count = 0;
            for di in start..end {
                let mut m3 = 0.0f64;
                for row in 0..n {
                    let z = (data[row * d + di] - means[di]) / stds[di];
                    m3 += z * z * z;
                }
                m3 /= n as f64;
                skew_sum += m3.abs();
                count += 1;
            }
            if count > 0 {
                anomaly_per_flavor[f] = skew_sum / count as f64;
            }
        }

        // Anomaly cancellation: in consistent gauge theory, Σ anomalies = 0
        // Check how well positive and negative third cumulants cancel
        let mean_anomaly = if triangle_count > 0 {
            anomaly_sum / triangle_count as f64
        } else {
            0.0
        };
        let cancellation = if max_anomaly > 1e-12 {
            1.0 - (mean_anomaly / max_anomaly).min(1.0)
        } else {
            1.0
        };

        // Chiral asymmetry: compare left-tail vs right-tail weight
        let mut chiral_scores = Vec::with_capacity(d.min(max_dims));
        for di in 0..d.min(max_dims) {
            let mut left = 0u32;
            let mut right = 0u32;
            for row in 0..n {
                let z = (data[row * d + di] - means[di]) / stds[di];
                if z < -1.0 { left += 1; }
                if z > 1.0 { right += 1; }
            }
            let total = (left + right).max(1) as f64;
            chiral_scores.push((right as f64 - left as f64).abs() / total);
        }
        let chiral_asymmetry = if !chiral_scores.is_empty() {
            chiral_scores.iter().sum::<f64>() / chiral_scores.len() as f64
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert("triangle_anomaly".to_string(), vec![max_anomaly]);
        result.insert("anomaly_per_flavor".to_string(), anomaly_per_flavor);
        result.insert("anomaly_cancellation".to_string(), vec![cancellation]);
        result.insert("chiral_asymmetry".to_string(), vec![chiral_asymmetry]);
        result.insert("triangle_count".to_string(), vec![triangle_count as f64]);
        result
    }
}
