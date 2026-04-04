use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// Common ionic radii (Shannon radii in Å) for perovskite tolerance factor
/// Format: (element_proxy_value, r_ion)
/// We use feature value ranges to proxy element identity
const R_OXYGEN: f64 = 1.40; // O²⁻ ionic radius

/// Typical A-site radii (large cations: Ba²⁺, Sr²⁺, Ca²⁺, La³⁺, K⁺, Na⁺)
const A_SITE_RADII: &[f64] = &[1.61, 1.44, 1.34, 1.36, 1.64, 1.39];
/// Typical B-site radii (small cations: Ti⁴⁺, Zr⁴⁺, Fe³⁺, Mn³⁺, Co³⁺, Ni²⁺)
const B_SITE_RADII: &[f64] = &[0.605, 0.72, 0.645, 0.645, 0.545, 0.69];

/// Pauling electronegativity reference values
const ELECTRONEG_PAIRS: &[(f64, f64, &str)] = &[
    (0.9, 3.5, "Na-Cl ionic"),
    (1.0, 3.0, "K-O ionic"),
    (1.5, 3.0, "mixed ionic-covalent"),
    (2.1, 3.5, "covalent-polar"),
    (2.5, 2.5, "covalent"),
];

/// Formation energy thresholds (eV/atom)
const FORMATION_ENERGY_STABLE: f64 = 0.0;    // negative = thermodynamically stable
const HULL_DISTANCE_THRESHOLD: f64 = 0.050;  // 50 meV/atom above hull = metastable

/// StabilityFilterLens: Detect material stability patterns in data.
///
/// Algorithm:
///   1. Formation energy proxy: detect negative energy patterns (negative = stable)
///   2. Energy above hull simulation: convex hull distance approximation
///   3. Goldschmidt tolerance factor: τ = (r_A + r_O) / (√2 × (r_B + r_O))
///      → 0.8–1.0 indicates perovskite stability
///   4. Elastic stability via Born criteria: C11 > 0, C11-C12 > 0, C44 > 0
///   5. Pauling electronegativity difference → ionic/covalent character
///
/// Reports: stability_score, formation_energy_proxy, tolerance_factor,
///          born_stable, electronegativity_score, hull_distance
pub struct StabilityFilterLens;

impl Lens for StabilityFilterLens {
    fn name(&self) -> &str {
        "StabilityFilterLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 {
            return HashMap::new();
        }

        let (means, vars) = mean_var(data, n, d);
        let columns = column_vectors(data, n, d);

        // ── 1. Formation energy proxy ──────────────────────────────────
        // Negative feature means suggest exothermic / stable formation
        let neg_frac = means.iter().filter(|&&m| m < FORMATION_ENERGY_STABLE).count() as f64
            / d.max(1) as f64;
        // Weighted by how negative: deeper negative = more stable
        let mean_neg: f64 = means.iter()
            .filter(|&&m| m < 0.0)
            .cloned()
            .sum::<f64>()
            / means.iter().filter(|&&m| m < 0.0).count().max(1) as f64;
        // Map to 0..1 score: -3 eV/atom → 1.0, 0 → 0.0
        let formation_energy_proxy = if mean_neg < 0.0 {
            (mean_neg.abs() / 3.0).min(1.0)
        } else {
            0.0
        };

        // ── 2. Energy above hull (convex hull approximation) ───────────
        // Use per-point distance to the convex envelope of feature space
        // Approximate: for each point, measure distance to the lower envelope
        let mut hull_distances = Vec::with_capacity(n);
        if d >= 2 {
            // Use first two features as (composition, energy) proxy
            let col_x = &columns[0];
            let col_y = &columns[1];

            // Build lower convex hull envelope (sorted by x)
            let mut pairs: Vec<(f64, f64)> = col_x.iter().zip(col_y.iter())
                .map(|(&x, &y)| (x, y))
                .collect();
            pairs.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

            // Simple lower envelope: for each x-range, find the min y
            let n_bins = 10.min(n);
            let x_min = pairs.first().map(|p| p.0).unwrap_or(0.0);
            let x_max = pairs.last().map(|p| p.0).unwrap_or(1.0);
            let x_range = (x_max - x_min).max(1e-12);

            let mut bin_min_y = vec![f64::INFINITY; n_bins];
            for &(x, y) in &pairs {
                let bin = ((x - x_min) / x_range * (n_bins as f64 - 0.01)) as usize;
                let bin = bin.min(n_bins - 1);
                if y < bin_min_y[bin] {
                    bin_min_y[bin] = y;
                }
            }
            // Fill empty bins with interpolation
            let mut last_valid = 0.0_f64;
            for b in bin_min_y.iter_mut() {
                if b.is_finite() {
                    last_valid = *b;
                } else {
                    *b = last_valid;
                }
            }

            // Compute hull distance per point
            for &(x, y) in &pairs {
                let bin = ((x - x_min) / x_range * (n_bins as f64 - 0.01)) as usize;
                let bin = bin.min(n_bins - 1);
                let dist = (y - bin_min_y[bin]).max(0.0);
                hull_distances.push(dist);
            }
        } else {
            // 1D fallback: distance from minimum
            let col = &columns[0];
            let col_min = col.iter().cloned().fold(f64::INFINITY, f64::min);
            for &v in col {
                hull_distances.push((v - col_min).max(0.0));
            }
        }

        let avg_hull_dist = hull_distances.iter().sum::<f64>() / n.max(1) as f64;
        // Fraction of points within metastable threshold
        let hull_stable_frac = hull_distances.iter()
            .filter(|&&h| h < HULL_DISTANCE_THRESHOLD)
            .count() as f64 / n.max(1) as f64;

        // ── 3. Goldschmidt tolerance factor ────────────────────────────
        // τ = (r_A + r_O) / (√2 × (r_B + r_O))
        // We try all (A-site, B-site) combos and see if feature ratios match
        let sqrt2 = std::f64::consts::SQRT_2;
        let mut best_tau = 0.0_f64;
        let mut best_tau_score = 0.0_f64;

        // Check if feature ratios approximate τ in [0.8, 1.0]
        for &r_a in A_SITE_RADII {
            for &r_b in B_SITE_RADII {
                let tau = (r_a + R_OXYGEN) / (sqrt2 * (r_b + R_OXYGEN));
                // Check if any feature ratio matches this tau
                for i in 0..d {
                    for j in 0..d {
                        if i == j { continue; }
                        let mi = means[i];
                        let mj = means[j];
                        if mj.abs() < 1e-12 { continue; }
                        let ratio = mi / mj;
                        if ratio > 0.0 {
                            let match_score = (-(ratio - tau).powi(2) / 0.02).exp();
                            if match_score > best_tau_score {
                                best_tau_score = match_score;
                                best_tau = tau;
                            }
                        }
                    }
                }
            }
        }

        // Also compute tolerance factor score from how close best_tau is to ideal
        let tau_in_range = if (0.8..=1.0).contains(&best_tau) { 1.0 } else {
            let dist_to_range = if best_tau < 0.8 { 0.8 - best_tau } else { best_tau - 1.0 };
            (-dist_to_range.powi(2) * 25.0).exp()
        };
        let tolerance_factor_score = best_tau_score * tau_in_range;

        // ── 4. Born stability criteria (elastic constants) ─────────────
        // Interpret first 3+ features as proxy elastic constants C11, C12, C44
        // Born criteria for cubic: C11 > 0, C11-C12 > 0, C44 > 0
        let born_stable = if d >= 3 {
            let c11 = means[0];
            let c12 = means[1];
            let c44 = means[2];
            let crit1 = c11 > 0.0;
            let crit2 = (c11 - c12) > 0.0;
            let crit3 = c44 > 0.0;
            let crit4 = (c11 + 2.0 * c12) > 0.0; // bulk modulus > 0

            let passed = [crit1, crit2, crit3, crit4].iter().filter(|&&c| c).count();
            passed as f64 / 4.0
        } else {
            // Fewer dimensions: check positivity as a proxy
            let pos_frac = means.iter().filter(|&&m| m > 0.0).count() as f64 / d.max(1) as f64;
            pos_frac * 0.5
        };

        // Also check per-point Born criteria patterns
        let mut born_per_point = Vec::with_capacity(n);
        if d >= 3 {
            for i in 0..n {
                let row_start = i * d;
                let c11 = data[row_start];
                let c12 = data[row_start + 1];
                let c44 = data[row_start + 2];
                let passed = [
                    c11 > 0.0,
                    (c11 - c12) > 0.0,
                    c44 > 0.0,
                    (c11 + 2.0 * c12) > 0.0,
                ].iter().filter(|&&c| c).count();
                born_per_point.push(passed as f64 / 4.0);
            }
        }

        // ── 5. Pauling electronegativity difference ────────────────────
        // Large |ΔEN| → ionic; small → covalent
        // Check if feature spreads match known electronegativity differences
        let mut en_score = 0.0_f64;
        for col in &columns {
            if col.len() < 2 { continue; }
            let col_range = {
                let mut lo = f64::INFINITY;
                let mut hi = f64::NEG_INFINITY;
                for &v in col.iter() {
                    if v < lo { lo = v; }
                    if v > hi { hi = v; }
                }
                hi - lo
            };
            // Check if range matches known EN differences
            for &(en1, en2, _label) in ELECTRONEG_PAIRS {
                let delta_en = (en2 - en1).abs();
                if delta_en > 0.1 {
                    let match_val = (-(col_range - delta_en).powi(2) / 0.5).exp();
                    en_score = en_score.max(match_val);
                }
            }
        }

        // Ionic character estimate: Pauling formula  % ionic = 1 - exp(-ΔEN²/4)
        // Use the best-matching feature spread as ΔEN proxy
        let best_delta_en = columns.iter().map(|col| {
            let mut lo = f64::INFINITY;
            let mut hi = f64::NEG_INFINITY;
            for &v in col.iter() {
                if v < lo { lo = v; }
                if v > hi { hi = v; }
            }
            hi - lo
        }).fold(0.0_f64, f64::max);

        let ionic_character = 1.0 - (-best_delta_en.powi(2) / 4.0).exp();

        // ── 6. Variance-based stability (low variance = ordered/stable) ──
        let avg_cv = {
            let mut cv_sum = 0.0_f64;
            let mut cv_count = 0;
            for j in 0..d {
                if means[j].abs() > 1e-12 {
                    let cv = vars[j].sqrt() / means[j].abs();
                    cv_sum += cv;
                    cv_count += 1;
                }
            }
            if cv_count > 0 { cv_sum / cv_count as f64 } else { 1.0 }
        };
        let ordering_score = (-avg_cv * 2.0).exp(); // low CV = high ordering

        // ── Combined stability score ───────────────────────────────────
        let stability_score = formation_energy_proxy * 0.25
            + hull_stable_frac * 0.20
            + tolerance_factor_score * 0.15
            + born_stable * 0.20
            + en_score * 0.10
            + ordering_score * 0.10;

        let mut result = HashMap::new();
        result.insert("stability_score".into(), vec![stability_score]);
        result.insert("formation_energy_proxy".into(), vec![formation_energy_proxy]);
        result.insert("neg_feature_fraction".into(), vec![neg_frac]);
        result.insert("hull_distance_avg".into(), vec![avg_hull_dist]);
        result.insert("hull_stable_fraction".into(), vec![hull_stable_frac]);
        result.insert("tolerance_factor".into(), vec![best_tau]);
        result.insert("tolerance_factor_score".into(), vec![tolerance_factor_score]);
        result.insert("born_stable".into(), vec![born_stable]);
        result.insert("electronegativity_score".into(), vec![en_score]);
        result.insert("ionic_character".into(), vec![ionic_character]);
        result.insert("ordering_score".into(), vec![ordering_score]);
        result.insert("hull_distances".into(), hull_distances);
        if !born_per_point.is_empty() {
            result.insert("born_per_point".into(), born_per_point);
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_shared(data: &[f64], n: usize, d: usize) -> SharedData {
        SharedData::compute(data, n, d)
    }

    #[test]
    fn test_negative_formation_energy() {
        // All-negative features → should indicate stability
        let n = 10;
        let d = 3;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let noise = (i as f64 * 0.1).sin() * 0.05;
            data.push(-1.5 + noise);  // C11 proxy
            data.push(-0.8 + noise);  // C12 proxy
            data.push(-2.0 + noise);  // C44 proxy
        }
        let shared = make_shared(&data, n, d);
        let result = StabilityFilterLens.scan(&data, n, d, &shared);

        assert!(result.contains_key("formation_energy_proxy"));
        let fe = result["formation_energy_proxy"][0];
        assert!(fe > 0.3, "Negative features should give positive formation energy proxy, got {fe}");
        assert!(result["neg_feature_fraction"][0] > 0.9);
    }

    #[test]
    fn test_born_criteria_stable() {
        // C11=200, C12=50, C44=80 → all Born criteria satisfied
        let n = 10;
        let d = 3;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let noise = (i as f64 * 0.1).sin() * 2.0;
            data.push(200.0 + noise);  // C11
            data.push(50.0 + noise);   // C12
            data.push(80.0 + noise);   // C44
        }
        let shared = make_shared(&data, n, d);
        let result = StabilityFilterLens.scan(&data, n, d, &shared);

        assert!(result.contains_key("born_stable"));
        let bs = result["born_stable"][0];
        assert!((bs - 1.0).abs() < 1e-6, "All Born criteria should pass, got {bs}");
    }

    #[test]
    fn test_born_criteria_unstable() {
        // C11=100, C12=150 → C11-C12 < 0, fails criterion
        let n = 10;
        let d = 3;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let noise = (i as f64 * 0.1).sin() * 1.0;
            data.push(100.0 + noise);  // C11
            data.push(150.0 + noise);  // C12  (> C11!)
            data.push(50.0 + noise);   // C44
        }
        let shared = make_shared(&data, n, d);
        let result = StabilityFilterLens.scan(&data, n, d, &shared);

        let bs = result["born_stable"][0];
        assert!(bs < 1.0, "Should fail at least one Born criterion, got {bs}");
    }

    #[test]
    fn test_tolerance_factor_range() {
        // tolerance_factor should be computed and be a valid float
        let n = 15;
        let d = 4;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let t = i as f64 / n as f64;
            data.push(0.9 + t * 0.1);   // ratio ~0.9 (perovskite range)
            data.push(1.0);
            data.push(0.5 + t * 0.2);
            data.push(1.2);
        }
        let shared = make_shared(&data, n, d);
        let result = StabilityFilterLens.scan(&data, n, d, &shared);

        assert!(result.contains_key("tolerance_factor"));
        let tau = result["tolerance_factor"][0];
        assert!(tau.is_finite(), "Tolerance factor should be finite, got {tau}");
    }

    #[test]
    fn test_empty_data_guard() {
        let shared = make_shared(&[], 0, 0);
        let result = StabilityFilterLens.scan(&[], 0, 0, &shared);
        assert!(result.is_empty());
    }

    #[test]
    fn test_hull_distance() {
        // Points near a convex hull should have small distances
        let n = 20;
        let d = 2;
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let x = i as f64 / n as f64;
            data.push(x);
            data.push(x * x); // parabola = convex hull is the curve itself
        }
        let shared = make_shared(&data, n, d);
        let result = StabilityFilterLens.scan(&data, n, d, &shared);

        assert!(result.contains_key("hull_distances"));
        assert!(result.contains_key("hull_stable_fraction"));
    }
}
