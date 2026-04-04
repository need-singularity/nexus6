use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ProteinFoldingLens: Simplified protein folding with 6 secondary structure elements.
///
/// Models the HP (hydrophobic-polar) lattice model:
///   - 6 secondary structure elements (helices, sheets, loops)
///   - Energy function: hydrophobic contacts in the core
///   - Contact order: sequence separation of contacting residues
///   - Compactness: radius of gyration
///   - Folding cooperativity from energy landscape roughness
pub struct ProteinFoldingLens;

impl Lens for ProteinFoldingLens {
    fn name(&self) -> &str {
        "ProteinFoldingLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 {
            return HashMap::new();
        }

        let n_elements = d.min(6);

        // Treat data points as residues in a protein structure
        // Each dimension represents a structural property

        // Hydrophobicity score per residue: mean of all dimensions (simplified)
        let hydrophobicity: Vec<f64> = (0..n)
            .map(|i| {
                let sum: f64 = (0..n_elements).map(|j| data[i * d + j]).sum();
                sum / n_elements as f64
            })
            .collect();

        // Classify: H (hydrophobic) if above median, P (polar) otherwise
        let mut sorted_h = hydrophobicity.clone();
        sorted_h.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let median_h = sorted_h[n / 2];
        let is_hydrophobic: Vec<bool> = hydrophobicity.iter().map(|&h| h >= median_h).collect();

        // Hydrophobic core energy: count H-H contacts (nearby in space but distant in sequence)
        let contact_threshold = {
            let mut dists: Vec<f64> = Vec::new();
            for i in 0..n.min(50) {
                for j in (i + 1)..n.min(50) {
                    dists.push(shared.dist(i, j));
                }
            }
            dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            if dists.is_empty() { 1.0 } else { dists[dists.len() / 4] } // 25th percentile
        };

        let mut hh_contacts = 0usize;
        let mut total_contacts = 0usize;
        let mut contact_order_sum = 0.0f64;

        for i in 0..n {
            for j in (i + 2)..n { // skip adjacent in sequence
                if j >= n { break; }
                let dist = shared.dist(i, j);
                if dist < contact_threshold {
                    total_contacts += 1;
                    contact_order_sum += (j - i) as f64;
                    if is_hydrophobic[i] && is_hydrophobic[j] {
                        hh_contacts += 1;
                    }
                }
            }
        }

        // Hydrophobic core energy (negative = favorable)
        let core_energy = -(hh_contacts as f64);

        // Relative contact order: mean sequence separation of contacts / chain length
        let rel_contact_order = if total_contacts > 0 {
            contact_order_sum / (total_contacts as f64 * n as f64)
        } else {
            0.0
        };

        // Radius of gyration (compactness)
        let mut centroid = vec![0.0f64; n_elements];
        for i in 0..n {
            for j in 0..n_elements {
                centroid[j] += data[i * d + j];
            }
        }
        for c in &mut centroid { *c /= n as f64; }

        let rg_sq: f64 = (0..n)
            .map(|i| {
                (0..n_elements)
                    .map(|j| (data[i * d + j] - centroid[j]).powi(2))
                    .sum::<f64>()
            })
            .sum::<f64>() / n as f64;
        let radius_of_gyration = rg_sq.sqrt();

        // Energy landscape roughness: variance of pairwise energies
        // Use distance distribution variance as proxy
        let mut dist_values = Vec::new();
        let max_sample = 500;
        let mut cnt = 0;
        for i in 0..n {
            for j in (i + 1)..n {
                if cnt >= max_sample { break; }
                dist_values.push(shared.dist(i, j));
                cnt += 1;
            }
            if cnt >= max_sample { break; }
        }
        let mean_dist = dist_values.iter().sum::<f64>() / dist_values.len().max(1) as f64;
        let dist_var = dist_values.iter().map(|d| (d - mean_dist).powi(2)).sum::<f64>()
            / dist_values.len().max(1) as f64;

        // Folding cooperativity: ratio of core energy to total contacts
        let cooperativity = if total_contacts > 0 {
            hh_contacts as f64 / total_contacts as f64
        } else {
            0.0
        };

        let mut result = HashMap::new();
        result.insert("hydrophobic_core_energy".into(), vec![core_energy]);
        result.insert("relative_contact_order".into(), vec![rel_contact_order]);
        result.insert("radius_of_gyration".into(), vec![radius_of_gyration]);
        result.insert("landscape_roughness".into(), vec![dist_var]);
        result.insert("folding_cooperativity".into(), vec![cooperativity]);
        result.insert("total_contacts".into(), vec![total_contacts as f64]);
        result
    }
}
