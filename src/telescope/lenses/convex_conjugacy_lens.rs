use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// ConvexConjugacyLens: Convex analysis in 6-dimensional geometry.
///
/// Analyzes data through Legendre-Fenchel conjugate (convex dual):
/// - Duality gap between function and biconjugate
/// - Convexity measure of the data
/// - Fenchel-Young inequality violation
/// - 6-dim geometric properties of the convex hull
pub struct ConvexConjugacyLens;

impl Lens for ConvexConjugacyLens {
    fn name(&self) -> &str { "ConvexConjugacyLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 8 || d == 0 { return HashMap::new(); }

        let dim = d.min(6); // work in up to 6 dimensions

        // Extract points as rows
        let points: Vec<Vec<f64>> = (0..n)
            .map(|i| {
                let row = i * d;
                (0..dim).map(|j| data[row + j]).collect()
            })
            .collect();

        // Convexity measure: for each triple of consecutive points,
        // measure how much the midpoint exceeds the linear interpolant
        let convexity = measure_convexity(&points);

        // Compute Legendre-Fenchel conjugate at sampled dual directions
        // and measure the duality gap (f - f**)
        let (duality_gaps, mean_gap) = compute_duality_gap(&points, dim);

        // Fenchel-Young inequality: <x, y> <= f(x) + f*(y)
        let fy_violations = fenchel_young_violations(&points, dim);

        // 6-dim convex hull volume estimate via random simplex sampling
        let hull_volume_ratio = convex_hull_volume_ratio(&points, dim);

        // Mean pairwise inner product (measures spread in dual space)
        let mean_inner_product = mean_pairwise_inner_product(&points);

        let mut result = HashMap::new();
        result.insert("convex_convexity_measure".to_string(), vec![convexity]);
        result.insert("convex_duality_gap".to_string(), duality_gaps);
        result.insert("convex_mean_duality_gap".to_string(), vec![mean_gap]);
        result.insert("convex_fy_violation_rate".to_string(), vec![fy_violations]);
        result.insert("convex_hull_volume_ratio".to_string(), vec![hull_volume_ratio]);
        result.insert("convex_mean_inner_product".to_string(), vec![mean_inner_product]);
        result.insert("score".to_string(), vec![result["convex_convexity_measure"][0].min(1.0).max(0.0)]);
        result
    }
}

/// Measure convexity: fraction of triples where midpoint is below/on line.
fn measure_convexity(points: &[Vec<f64>]) -> f64 {
    let n = points.len();
    if n < 3 { return 1.0; }

    let mut convex_count = 0;
    let mut total = 0;

    let step = (n / 50).max(1);
    for i in (0..n.saturating_sub(2)).step_by(step) {
        let j = i + 1;
        let k = (i + 2).min(n - 1);
        if j >= n || k >= n { break; }

        // Check if midpoint of (p_i, p_k) dominates p_j in L2 norm sense
        let dim = points[i].len();
        let mut mid_norm = 0.0;
        let mut pj_norm = 0.0;
        for d in 0..dim {
            let mid = (points[i][d] + points[k][d]) / 2.0;
            mid_norm += mid * mid;
            pj_norm += points[j][d] * points[j][d];
        }
        if mid_norm >= pj_norm - 1e-10 {
            convex_count += 1;
        }
        total += 1;
    }

    if total == 0 { 1.0 } else { convex_count as f64 / total as f64 }
}

/// Compute duality gap: f(x) - f**(x) where f** is the biconjugate.
/// Uses discrete Legendre-Fenchel transform.
fn compute_duality_gap(points: &[Vec<f64>], _dim: usize) -> (Vec<f64>, f64) {
    let n = points.len();
    if n < 3 { return (vec![0.0], 0.0); }

    // Use L2 norm squared as the function: f(x) = ||x||^2
    let f_vals: Vec<f64> = points.iter()
        .map(|p| p.iter().map(|v| v * v).sum::<f64>())
        .collect();

    // Conjugate f*(y) = sup_x { <x,y> - f(x) }
    // evaluated at each point
    let conjugate_at = |y: &[f64]| -> f64 {
        let mut sup = f64::NEG_INFINITY;
        for (i, p) in points.iter().enumerate() {
            let inner: f64 = p.iter().zip(y.iter()).map(|(a, b)| a * b).sum();
            let val = inner - f_vals[i];
            if val > sup { sup = val; }
        }
        sup
    };

    // Biconjugate f**(x) = sup_y { <x,y> - f*(y) }
    let biconjugate_at = |x: &[f64]| -> f64 {
        let mut sup = f64::NEG_INFINITY;
        for p in points.iter() {
            let inner: f64 = x.iter().zip(p.iter()).map(|(a, b)| a * b).sum();
            let fstar = conjugate_at(p);
            let val = inner - fstar;
            if val > sup { sup = val; }
        }
        sup
    };

    // Sample duality gaps
    let step = (n / 20).max(1);
    let mut gaps = Vec::new();
    for i in (0..n).step_by(step) {
        let f_val = f_vals[i];
        let fss = biconjugate_at(&points[i]);
        let gap = (f_val - fss).max(0.0);
        gaps.push(gap);
    }

    let mean_gap = if gaps.is_empty() { 0.0 } else {
        gaps.iter().sum::<f64>() / gaps.len() as f64
    };

    (gaps, mean_gap)
}

/// Measure Fenchel-Young inequality violation rate.
fn fenchel_young_violations(points: &[Vec<f64>], _dim: usize) -> f64 {
    let n = points.len();
    if n < 2 { return 0.0; }

    // f(x) = ||x||^2, f*(y) = ||y||^2/4 (for quadratic)
    let mut violations = 0;
    let mut total = 0;

    let step = (n / 30).max(1);
    for i in (0..n).step_by(step) {
        for j in (0..n).step_by(step) {
            let inner: f64 = points[i].iter().zip(points[j].iter())
                .map(|(a, b)| a * b).sum();
            let f_x: f64 = points[i].iter().map(|v| v * v).sum();
            let f_star_y: f64 = points[j].iter().map(|v| v * v).sum::<f64>() / 4.0;

            // Fenchel-Young: <x,y> <= f(x) + f*(y)
            if inner > f_x + f_star_y + 1e-10 {
                violations += 1;
            }
            total += 1;
        }
    }

    if total == 0 { 0.0 } else { violations as f64 / total as f64 }
}

/// Estimate convex hull volume ratio via random simplex sampling.
fn convex_hull_volume_ratio(points: &[Vec<f64>], dim: usize) -> f64 {
    let n = points.len();
    if n <= dim { return 0.0; }

    // Compute bounding box volume
    let mut mins = vec![f64::INFINITY; dim];
    let mut maxs = vec![f64::NEG_INFINITY; dim];
    for p in points {
        for (j, &v) in p.iter().enumerate().take(dim) {
            mins[j] = mins[j].min(v);
            maxs[j] = maxs[j].max(v);
        }
    }
    let _bbox_vol: f64 = (0..dim).map(|j| (maxs[j] - mins[j]).max(1e-15)).product();

    // Estimate hull volume via random simplices (Monte Carlo)
    let num_tests = 200;
    let mut inside_count = 0;

    // Simple LCG for deterministic pseudo-random
    let mut seed: u64 = 42;
    let next_rand = |s: &mut u64| -> f64 {
        *s = s.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((*s >> 33) as f64) / (u32::MAX as f64)
    };

    for _ in 0..num_tests {
        // Generate random point in bounding box
        let test: Vec<f64> = (0..dim)
            .map(|j| mins[j] + next_rand(&mut seed) * (maxs[j] - mins[j]))
            .collect();

        // Check if test point is "inside" convex hull
        // via checking if it can be expressed as convex combination (approximate)
        if is_approx_inside(points, &test) {
            inside_count += 1;
        }
    }

    inside_count as f64 / num_tests as f64
}

/// Approximate check if point is inside convex hull.
fn is_approx_inside(points: &[Vec<f64>], test: &[f64]) -> bool {
    // Find nearest point, then check if test is "surrounded"
    let dim = test.len();
    let mut min_dist = f64::INFINITY;
    for p in points.iter() {
        let dist: f64 = p.iter().zip(test.iter()).map(|(a, b)| (a - b).powi(2)).sum();
        if dist < min_dist { min_dist = dist; }
    }

    // Check directions: for each dimension, there should be points on both sides
    let mut has_both = true;
    for d in 0..dim {
        let mut has_less = false;
        let mut has_more = false;
        for p in points {
            if p[d] < test[d] - 1e-10 { has_less = true; }
            if p[d] > test[d] + 1e-10 { has_more = true; }
            if has_less && has_more { break; }
        }
        if !has_less || !has_more { has_both = false; break; }
    }
    has_both
}

/// Mean pairwise inner product of data points.
fn mean_pairwise_inner_product(points: &[Vec<f64>]) -> f64 {
    let n = points.len();
    if n < 2 { return 0.0; }

    let step = (n / 30).max(1);
    let mut sum = 0.0;
    let mut count = 0;

    for i in (0..n).step_by(step) {
        for j in (i + 1..n).step_by(step) {
            let inner: f64 = points[i].iter().zip(points[j].iter())
                .map(|(a, b)| a * b).sum();
            sum += inner;
            count += 1;
        }
    }

    if count == 0 { 0.0 } else { sum / count as f64 }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_convex_conjugacy_lens() {
        let n = 32;
        let d = 3;
        // Points on a sphere (convex)
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let theta = 2.0 * std::f64::consts::PI * i as f64 / n as f64;
            data.push(theta.cos());
            data.push(theta.sin());
            data.push(0.5);
        }
        let shared = SharedData::compute(&data, n, d);
        let result = ConvexConjugacyLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("convex_convexity_measure"));
        assert!(result.contains_key("convex_mean_duality_gap"));
    }
}
