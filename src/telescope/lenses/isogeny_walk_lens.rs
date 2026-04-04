use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// IsogenyWalkLens: Elliptic curve isogeny graph analysis.
///
/// Models data as an isogeny graph with degree-6 structure:
/// - Each point is a "curve", edges connect isogenous curves
/// - 6-degree isogeny: each node has up to 6 neighbors (degree-6 graph)
/// - Path length analysis: shortest walks in the isogeny graph
/// - Expander graph properties: spectral gap, mixing time
pub struct IsogenyWalkLens;

impl Lens for IsogenyWalkLens {
    fn name(&self) -> &str { "IsogenyWalkLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, _d: usize, shared: &SharedData) -> LensResult {
        let _ = data;
        if n < 6 { return HashMap::new(); }

        let degree = 6usize; // 6-degree isogeny graph

        // Build degree-6 graph: each node connects to 6 nearest neighbors
        let mut adj = vec![vec![]; n];
        for i in 0..n {
            let mut neighbors: Vec<(usize, f64)> = (0..n)
                .filter(|&j| j != i)
                .map(|j| (j, shared.dist(i, j)))
                .collect();
            neighbors.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
            for k in 0..degree.min(neighbors.len()) {
                adj[i].push(neighbors[k].0);
            }
        }

        // Compute actual degree distribution
        let degrees: Vec<f64> = adj.iter().map(|a| a.len() as f64).collect();
        let mean_degree = degrees.iter().sum::<f64>() / n as f64;

        // BFS shortest paths from all nodes (for small n) or sample
        let sample_size = n.min(30);
        let mut all_path_lengths: Vec<f64> = Vec::new();
        let mut diameter = 0usize;

        for src in 0..sample_size {
            let mut dist_bfs = vec![usize::MAX; n];
            dist_bfs[src] = 0;
            let mut queue = std::collections::VecDeque::new();
            queue.push_back(src);
            while let Some(u) = queue.pop_front() {
                for &v in &adj[u] {
                    if dist_bfs[v] == usize::MAX {
                        dist_bfs[v] = dist_bfs[u] + 1;
                        queue.push_back(v);
                    }
                }
            }
            for t in 0..n {
                if t != src && dist_bfs[t] < usize::MAX {
                    all_path_lengths.push(dist_bfs[t] as f64);
                    if dist_bfs[t] > diameter { diameter = dist_bfs[t]; }
                }
            }
        }

        let mean_path_length = if all_path_lengths.is_empty() { 0.0 }
            else { all_path_lengths.iter().sum::<f64>() / all_path_lengths.len() as f64 };

        // Expander property: adjacency matrix spectral gap approximation
        // Power iteration on adjacency matrix to find second eigenvalue
        let spectral_gap = estimate_spectral_gap(&adj, n, degree);

        // Mixing time estimate: t_mix ~ log(n) / spectral_gap
        let mixing_time = if spectral_gap > 1e-10 {
            (n as f64).ln() / spectral_gap
        } else { f64::INFINITY };

        // Ramanujan bound: lambda_2 <= 2*sqrt(d-1) for optimal expander
        let ramanujan_bound = 2.0 * ((degree as f64 - 1.0).sqrt());
        let lambda2_approx = degree as f64 * (1.0 - spectral_gap);
        let ramanujan_ratio = if ramanujan_bound > 1e-15 {
            lambda2_approx / ramanujan_bound
        } else { 1.0 };

        // Girth: shortest cycle length
        let girth = find_girth(&adj, n);

        // n=6 isogeny match
        let n6_isogeny_match = (-((mean_degree - 6.0).abs() * 0.3)).exp();

        let mut result = HashMap::new();
        result.insert("mean_degree".into(), vec![mean_degree]);
        result.insert("mean_path_length".into(), vec![mean_path_length]);
        result.insert("diameter".into(), vec![diameter as f64]);
        result.insert("spectral_gap".into(), vec![spectral_gap]);
        result.insert("mixing_time".into(), vec![mixing_time]);
        result.insert("ramanujan_ratio".into(), vec![ramanujan_ratio]);
        result.insert("girth".into(), vec![girth as f64]);
        result.insert("n6_isogeny_match".into(), vec![n6_isogeny_match]);
        result.insert("score".to_string(), vec![result["mean_degree"][0].min(1.0).max(0.0)]);
        result
    }
}

fn estimate_spectral_gap(adj: &[Vec<usize>], n: usize, degree: usize) -> f64 {
    if n < 3 { return 0.0; }

    // Power iteration to find dominant eigenvector, then deflate
    let mut v: Vec<f64> = (0..n).map(|i| (i as f64 + 1.0) / n as f64).collect();
    let norm = v.iter().map(|x| x * x).sum::<f64>().sqrt();
    for x in &mut v { *x /= norm; }

    // Subtract uniform component (eigenvalue = degree)
    let mean: f64 = v.iter().sum::<f64>() / n as f64;
    for x in &mut v { *x -= mean; }

    for _ in 0..30 {
        let mut new_v = vec![0.0; n];
        for i in 0..n {
            for &j in &adj[i] {
                new_v[i] += v[j];
            }
        }
        // Subtract projection onto uniform vector
        let new_mean: f64 = new_v.iter().sum::<f64>() / n as f64;
        for x in &mut new_v { *x -= new_mean; }

        let norm = new_v.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm < 1e-15 { return 1.0; } // All eigenvalues equal => perfect gap
        for x in &mut new_v { *x /= norm; }
        v = new_v;
    }

    // Estimate lambda_2 via Rayleigh quotient
    let mut av = vec![0.0; n];
    for i in 0..n {
        for &j in &adj[i] {
            av[i] += v[j];
        }
    }
    let lambda2: f64 = v.iter().zip(av.iter()).map(|(x, y)| x * y).sum();
    let lambda1 = degree as f64;

    if lambda1 > 1e-15 { (lambda1 - lambda2.abs()) / lambda1 } else { 0.0 }
}

fn find_girth(adj: &[Vec<usize>], n: usize) -> usize {
    let mut min_girth = usize::MAX;
    for src in 0..n.min(20) {
        let mut dist = vec![usize::MAX; n];
        let mut parent = vec![usize::MAX; n];
        dist[src] = 0;
        let mut queue = std::collections::VecDeque::new();
        queue.push_back(src);
        while let Some(u) = queue.pop_front() {
            for &v in &adj[u] {
                if dist[v] == usize::MAX {
                    dist[v] = dist[u] + 1;
                    parent[v] = u;
                    queue.push_back(v);
                } else if parent[u] != v && parent[v] != u {
                    let cycle_len = dist[u] + dist[v] + 1;
                    if cycle_len < min_girth { min_girth = cycle_len; }
                }
            }
        }
    }
    if min_girth == usize::MAX { 0 } else { min_girth }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_isogeny_walk() {
        let mut data = Vec::new();
        for i in 0..12 {
            let angle = i as f64 * std::f64::consts::TAU / 12.0;
            data.push(angle.cos());
            data.push(angle.sin());
        }
        let n = 12;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = IsogenyWalkLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("spectral_gap"));
        assert!(r["diameter"][0] >= 1.0);
        assert!(r["mean_degree"][0] <= 6.0 + 0.01);
    }
}
