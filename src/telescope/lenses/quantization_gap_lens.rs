use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, column_vectors, mean_var};

/// QuantizationGapLens: Geometric quantization on 6-dim phase space.
///
/// Detects quantized energy levels (gaps) in data by analyzing the
/// spacing distribution of sorted values. In quantum mechanics, the
/// WKB approximation gives quantization: ∮ p dq = (n + 1/2)ℏ.
///
/// We treat pairs of dimensions as (q, p) canonical pairs (3 pairs for
/// 6-dim phase space) and compute the phase-space area enclosed by
/// data trajectories. Quantized systems show discrete area values.
///
/// Metrics:
///   1. energy_gaps: spacing between detected quantized levels
///   2. gap_regularity: how uniform the level spacing is (Wigner vs Poisson)
///   3. wkb_action: semiclassical action ∮ p dq for each canonical pair
///   4. quantization_number: estimated quantum number from action
///   5. phase_space_volume: total 6-dim phase space volume occupied
///
/// n=6: 6-dim phase space (3 position + 3 momentum), 6 quantization conditions.
pub struct QuantizationGapLens;

impl Lens for QuantizationGapLens {
    fn name(&self) -> &str { "QuantizationGapLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d < 2 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);

        // 1. Energy gap analysis: treat first column as "energy" proxy
        let mut energies: Vec<f64> = columns[0].clone();
        energies.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        // Compute gaps between sorted values
        let mut gaps: Vec<f64> = Vec::with_capacity(n - 1);
        for i in 1..n {
            gaps.push(energies[i] - energies[i - 1]);
        }

        // Filter out near-zero gaps to find significant level spacings
        let gap_mean = gaps.iter().sum::<f64>() / gaps.len().max(1) as f64;
        let sig_gaps: Vec<f64> = gaps.iter()
            .filter(|&&g| g > gap_mean * 0.1)
            .cloned()
            .collect();

        // 2. Gap regularity: ratio of variance to mean² of spacings
        // Poisson (random): var/mean² = 1, Wigner (quantum): var/mean² ≈ 0.27
        let sg_mean = sig_gaps.iter().sum::<f64>() / sig_gaps.len().max(1) as f64;
        let sg_var = sig_gaps.iter()
            .map(|&g| (g - sg_mean).powi(2))
            .sum::<f64>() / sig_gaps.len().max(1) as f64;
        let gap_regularity = if sg_mean > 1e-12 {
            sg_var / (sg_mean * sg_mean)
        } else {
            1.0
        };

        // 3. WKB action for canonical pairs (q_i, p_i)
        // Pair dimensions: (0,1), (2,3), (4,5), ...
        let n_pairs = (d / 2).min(6);
        let mut wkb_actions = Vec::with_capacity(n_pairs);
        let mut quant_numbers = Vec::with_capacity(n_pairs);

        for pair in 0..n_pairs {
            let qi = pair * 2;
            let pi = pair * 2 + 1;
            if pi >= d { break; }

            // Sort by q coordinate
            let mut qp: Vec<(f64, f64)> = (0..n)
                .map(|i| (columns[qi][i], columns[pi][i]))
                .collect();
            qp.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

            // Compute action = ∮ p dq via trapezoidal rule (closed loop)
            let mut action = 0.0f64;
            for i in 0..qp.len() {
                let j = (i + 1) % qp.len();
                let dq = qp[j].0 - qp[i].0;
                let p_avg = (qp[i].1 + qp[j].1) / 2.0;
                action += p_avg * dq;
            }
            action = action.abs();

            // Quantization: action / (2π) = n + 1/2
            // (using natural units where ℏ = 1)
            let quant_n = (action / (2.0 * std::f64::consts::PI) - 0.5).max(0.0);

            wkb_actions.push(action);
            quant_numbers.push(quant_n);
        }

        // 4. Phase space volume: product of ranges in each dimension pair
        let (_, vars) = mean_var(data, n, d);
        let mut phase_volume = 1.0f64;
        for pair in 0..n_pairs {
            let qi = pair * 2;
            let pi = pair * 2 + 1;
            if pi >= d { break; }
            // Phase space area ~ 4σ_q × 4σ_p (2σ range each side)
            let area = 4.0 * vars[qi].sqrt() * 4.0 * vars[pi].sqrt();
            phase_volume *= area.max(1e-12);
        }

        // Number of quantum states ~ volume / (2πℏ)^n_pairs
        let h_eff = (2.0 * std::f64::consts::PI).powi(n_pairs as i32);
        let n_states = phase_volume / h_eff;

        let mut result = HashMap::new();
        result.insert("energy_gaps".to_string(), sig_gaps);
        result.insert("gap_regularity".to_string(), vec![gap_regularity]);
        result.insert("wkb_action".to_string(), wkb_actions);
        result.insert("quantization_number".to_string(), quant_numbers);
        result.insert("phase_space_volume".to_string(), vec![phase_volume]);
        result.insert("estimated_states".to_string(), vec![n_states]);
        result.insert("score".to_string(), vec![result["energy_gaps"][0].min(1.0).max(0.0)]);
        result
    }
}
