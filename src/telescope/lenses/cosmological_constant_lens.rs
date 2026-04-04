use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var};

/// CosmologicalConstantLens: Dark energy fine-tuning analysis.
///
/// Detects vacuum energy-like contributions in data: a constant offset
/// that subtly shifts all observations. The cosmological constant problem
/// is the ~120 order-of-magnitude discrepancy between QFT vacuum energy
/// and observed Λ.
///
/// We analyze:
///   1. Background "vacuum" level: persistent offset across all dimensions
///   2. Fine-tuning: how precisely contributions cancel to give small Λ
///   3. De Sitter / Anti-de Sitter classification from effective Λ sign
///   4. Dark energy equation of state w = p/ρ near each point
///
/// Metrics:
///   1. effective_lambda: estimated cosmological constant (mean residual)
///   2. fine_tuning_ratio: ratio of individual contributions to net Λ
///   3. equation_of_state_w: effective dark energy w parameter
///   4. vacuum_energy_density: energy density of the "vacuum" component
///   5. de_sitter_score: probability data lives on de Sitter space
///
/// n=6: Λ in 6D has units [length]⁻², 6-dim vacuum has 6!/3!3!=20 components.
pub struct CosmologicalConstantLens;

impl Lens for CosmologicalConstantLens {
    fn name(&self) -> &str { "CosmologicalConstantLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 || d < 1 { return HashMap::new(); }

        let (means, vars) = mean_var(data, n, d);

        // 1. Effective Λ: the "background" that remains after subtracting
        // local structure. Use grand mean as vacuum level.
        let grand_mean = means.iter().sum::<f64>() / d as f64;
        let grand_var = vars.iter().sum::<f64>() / d as f64;

        // Residual from zero: how much the data's center deviates from origin
        let effective_lambda = grand_mean;

        // 2. Fine-tuning ratio: individual dimension contributions vs net
        // Each dimension contributes means[i] to the "vacuum energy"
        // Fine-tuning = max|contribution| / |net result|
        let max_contrib = means.iter().map(|x| x.abs()).fold(0.0f64, f64::max);
        let fine_tuning = if effective_lambda.abs() > 1e-15 {
            max_contrib / effective_lambda.abs()
        } else {
            max_contrib * 1e15 // extreme fine-tuning
        };

        // 3. Equation of state w = pressure/density
        // In data: "density" = mean squared value, "pressure" = variance
        // w = -1 for cosmological constant (Λ), w = 0 for matter, w = 1/3 for radiation
        let density: f64 = (0..n).map(|i| {
            let mut sq = 0.0f64;
            for j in 0..d {
                sq += data[i * d + j].powi(2);
            }
            sq / d as f64
        }).sum::<f64>() / n as f64;

        let pressure = grand_var; // variance acts as pressure
        let w = if density > 1e-12 {
            -pressure / density // negative = dark energy-like
        } else {
            -1.0
        };

        // 4. Vacuum energy density: energy stored in the constant component
        // ρ_vac = Λ / (8πG) ~ grand_mean² in natural units
        let vacuum_energy = grand_mean * grand_mean;

        // 5. De Sitter score: positive Λ → expanding (de Sitter)
        // Check if data shows exponential expansion (distances grow with index)
        let max_check = n.min(100);
        let _expansion_score = 0.0f64;
        let _expansion_count = 0u32;

        // Compare mean distances in first half vs second half
        let half = max_check / 2;
        let mut dist_early = 0.0f64;
        let mut count_early = 0u32;
        let mut dist_late = 0.0f64;
        let mut count_late = 0u32;

        for i in 0..half.min(30) {
            for j in (i + 1)..half.min(30) {
                dist_early += shared.dist(i, j);
                count_early += 1;
            }
        }
        for i in half..max_check.min(half + 30) {
            for j in (i + 1)..max_check.min(half + 30) {
                dist_late += shared.dist(i, j);
                count_late += 1;
            }
        }

        let mean_early = if count_early > 0 { dist_early / count_early as f64 } else { 1.0 };
        let mean_late = if count_late > 0 { dist_late / count_late as f64 } else { 1.0 };

        // De Sitter: distances grow (positive Λ causes expansion)
        // Anti-de Sitter: distances shrink (negative Λ)
        let de_sitter_score = if mean_early > 1e-12 {
            let ratio = mean_late / mean_early;
            if ratio > 1.0 {
                1.0 - 1.0 / ratio // expansion → de Sitter
            } else {
                -(1.0 - ratio) // contraction → anti-de Sitter
            }
        } else {
            0.0
        };

        // 6. Per-dimension vacuum contributions
        let dim_contributions: Vec<f64> = means.iter()
            .take(d.min(6))
            .map(|&m| m * m)
            .collect();

        let mut result = HashMap::new();
        result.insert("effective_lambda".to_string(), vec![effective_lambda]);
        result.insert("fine_tuning_ratio".to_string(), vec![fine_tuning]);
        result.insert("equation_of_state_w".to_string(), vec![w]);
        result.insert("vacuum_energy_density".to_string(), vec![vacuum_energy]);
        result.insert("de_sitter_score".to_string(), vec![de_sitter_score]);
        result.insert("dim_vacuum_contributions".to_string(), dim_contributions);
        result
    }
}
