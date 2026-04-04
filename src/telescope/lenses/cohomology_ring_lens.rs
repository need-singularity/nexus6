use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// CohomologyRingLens: Detect cohomological structure — Betti numbers,
/// cup product patterns, Poincare duality.
///
/// n=6 connection: 6-dimensional manifolds, Poincare duality pairs (H^k, H^{6-k}),
/// Euler characteristic via alternating Betti sum.
pub struct CohomologyRingLens;

/// Estimate Betti numbers from data using persistent homology proxy.
/// Uses distance thresholds to count connected components, loops, and voids.
fn estimate_betti_numbers(data: &[f64], n: usize, d: usize, shared: &SharedData) -> Vec<f64> {
    if n < 3 {
        return vec![0.0; 7];
    }

    // Collect all pairwise distances
    let mut all_dists = Vec::new();
    for i in 0..n.min(100) {
        for j in (i + 1)..n.min(100) {
            all_dists.push(shared.dist(i, j));
        }
    }
    if all_dists.is_empty() {
        return vec![0.0; 7];
    }
    all_dists.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

    let median_dist = all_dists[all_dists.len() / 2];
    let mut betti = vec![0.0f64; 7]; // β_0 through β_6

    // β_0: connected components at threshold ε = median_dist
    // Use union-find proxy
    let eps = median_dist;
    let nn = n.min(100);
    let mut parent: Vec<usize> = (0..nn).collect();
    for i in 0..nn {
        for j in (i + 1)..nn {
            if shared.dist(i, j) < eps {
                let pi = find(&mut parent, i);
                let pj = find(&mut parent, j);
                if pi != pj {
                    parent[pi] = pj;
                }
            }
        }
    }
    let components = (0..nn).filter(|&i| find(&mut parent, i) == i).count();
    betti[0] = components as f64;

    // β_1: count "triangles with missing edge" as proxy for 1-cycles
    let mut cycle_count = 0;
    for i in 0..nn.min(30) {
        for j in (i + 1)..nn.min(30) {
            for k in (j + 1)..nn.min(30) {
                let d_ij = shared.dist(i, j) < eps * 1.5;
                let d_jk = shared.dist(j, k) < eps * 1.5;
                let d_ik = shared.dist(i, k) < eps * 1.5;
                let edges = d_ij as usize + d_jk as usize + d_ik as usize;
                if edges == 2 {
                    cycle_count += 1; // incomplete triangle = 1-cycle
                }
            }
        }
    }
    betti[1] = cycle_count as f64;

    // Higher Betti numbers: estimate from dimensional analysis
    // β_k decays exponentially for random point clouds
    for k in 2..=6 {
        betti[k] = (betti[1] * (0.3_f64).powi(k as i32 - 1)).max(0.0);
    }

    betti
}

fn find(parent: &mut [usize], i: usize) -> usize {
    if parent[i] != i {
        parent[i] = find(parent, parent[i]);
    }
    parent[i]
}

impl Lens for CohomologyRingLens {
    fn name(&self) -> &str {
        "CohomologyRingLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);

        // 1. Estimate Betti numbers β_0 through β_6
        let betti = estimate_betti_numbers(data, max_n, d, shared);
        result.insert("betti_numbers".to_string(), betti.clone());

        // 2. Euler characteristic: χ = Σ (-1)^k β_k
        let euler: f64 = betti.iter().enumerate()
            .map(|(k, &b)| if k % 2 == 0 { b } else { -b })
            .sum();
        result.insert("euler_characteristic".to_string(), vec![euler]);

        // 3. Poincare duality check: β_k ≈ β_{6-k} for a closed 6-manifold
        let mut duality_score = 0.0;
        let mut duality_count = 0;
        for k in 0..=3 {
            let bk = betti[k];
            let b6mk = betti[6 - k];
            if bk + b6mk > 1e-12 {
                duality_score += 1.0 - (bk - b6mk).abs() / (bk + b6mk);
                duality_count += 1;
            }
        }
        let poincare_duality = if duality_count > 0 { duality_score / duality_count as f64 } else { 0.0 };
        result.insert("poincare_duality_score".to_string(), vec![poincare_duality]);

        // 4. Cup product structure: measure pairwise interactions between features
        //    as proxy for H^p ∪ H^q → H^{p+q}
        if d >= 2 {
            let max_dim = d.min(6);
            let mut cup_products = Vec::new();
            for p in 0..max_dim {
                for q in (p + 1)..max_dim {
                    // "Cup product" = correlation between dimensions p and q
                    let mut sum_pq = 0.0;
                    let mut sum_p = 0.0;
                    let mut sum_q = 0.0;
                    let mut sum_pp = 0.0;
                    let mut sum_qq = 0.0;
                    for i in 0..max_n {
                        let vp = data[i * d + p];
                        let vq = data[i * d + q];
                        sum_pq += vp * vq;
                        sum_p += vp;
                        sum_q += vq;
                        sum_pp += vp * vp;
                        sum_qq += vq * vq;
                    }
                    let nf = max_n as f64;
                    let cov = sum_pq / nf - (sum_p / nf) * (sum_q / nf);
                    let std_p = (sum_pp / nf - (sum_p / nf).powi(2)).max(0.0).sqrt();
                    let std_q = (sum_qq / nf - (sum_q / nf).powi(2)).max(0.0).sqrt();
                    let corr = if std_p > 1e-12 && std_q > 1e-12 {
                        cov / (std_p * std_q)
                    } else {
                        0.0
                    };
                    cup_products.push(corr.abs());
                }
            }
            if !cup_products.is_empty() {
                let avg_cup = cup_products.iter().sum::<f64>() / cup_products.len() as f64;
                result.insert("cup_product_strength".to_string(), vec![avg_cup]);
            }
        }

        // 5. Cohomological dimension: effective dimension where Betti numbers vanish
        let cohom_dim = betti.iter().rposition(|&b| b > 0.5).unwrap_or(0);
        result.insert("cohomological_dimension".to_string(), vec![cohom_dim as f64]);
        // Score: 1.0 if dimension is 6
        let dim_six_score = 1.0 - ((cohom_dim as f64 - 6.0).abs() / 6.0).min(1.0);
        result.insert("dim_six_score".to_string(), vec![dim_six_score]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_cohomology_ring_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.5).sin()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = CohomologyRingLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("betti_numbers"));
        assert!(result.contains_key("euler_characteristic"));
        assert!(result.contains_key("poincare_duality_score"));
    }

    #[test]
    fn test_cohomology_ring_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = CohomologyRingLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
