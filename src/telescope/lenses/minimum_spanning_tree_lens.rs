use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// MinimumSpanningTreeLens: MST-based data structure analysis.
///
/// Builds minimum spanning tree via Kruskal's algorithm:
/// - MST weight and edge distribution
/// - 6-edge cycle property: fundamental cycles in MST + one edge
/// - Bottleneck distances and dendrogram structure
/// - MST degree distribution and Steiner ratio
pub struct MinimumSpanningTreeLens;

impl Lens for MinimumSpanningTreeLens {
    fn name(&self) -> &str { "MinimumSpanningTreeLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, _d: usize, shared: &SharedData) -> LensResult {
        let _ = data;
        if n < 4 { return HashMap::new(); }

        // Build edge list
        let mut edges: Vec<(f64, usize, usize)> = Vec::with_capacity(n * (n - 1) / 2);
        for i in 0..n {
            for j in (i + 1)..n {
                edges.push((shared.dist(i, j), i, j));
            }
        }
        edges.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

        // Kruskal's algorithm with union-find
        let mut parent: Vec<usize> = (0..n).collect();
        let mut rank_uf = vec![0usize; n];
        let mut mst_edges: Vec<(f64, usize, usize)> = Vec::new();
        let mut mst_weight = 0.0;

        for &(w, u, v) in &edges {
            let ru = find(&mut parent, u);
            let rv = find(&mut parent, v);
            if ru != rv {
                union(&mut parent, &mut rank_uf, ru, rv);
                mst_edges.push((w, u, v));
                mst_weight += w;
                if mst_edges.len() == n - 1 { break; }
            }
        }

        // MST edge weights
        let mst_edge_weights: Vec<f64> = mst_edges.iter().map(|&(w, _, _)| w).collect();
        let mean_edge_weight = if mst_edge_weights.is_empty() { 0.0 }
            else { mst_edge_weights.iter().sum::<f64>() / mst_edge_weights.len() as f64 };

        // Bottleneck: maximum MST edge weight
        let bottleneck = mst_edge_weights.iter().cloned().fold(0.0f64, f64::max);

        // MST degree distribution
        let mut mst_degree = vec![0usize; n];
        let mut mst_adj: Vec<Vec<(usize, f64)>> = vec![vec![]; n];
        for &(w, u, v) in &mst_edges {
            mst_degree[u] += 1;
            mst_degree[v] += 1;
            mst_adj[u].push((v, w));
            mst_adj[v].push((u, w));
        }
        let max_degree = *mst_degree.iter().max().unwrap_or(&0);
        let mean_degree = mst_degree.iter().sum::<usize>() as f64 / n as f64;
        let leaves = mst_degree.iter().filter(|&&d| d == 1).count();

        // Fundamental cycles: for each non-MST edge, find cycle length through MST
        let mut cycle_lengths = Vec::new();
        let non_mst_count = edges.len() - mst_edges.len();
        let check_limit = non_mst_count.min(100);
        let mut checked = 0;

        for &(w, u, v) in &edges {
            if checked >= check_limit { break; }
            // Check if this edge is in MST
            let in_mst = mst_edges.iter().any(|&(_, mu, mv)| (mu == u && mv == v) || (mu == v && mv == u));
            if in_mst { continue; }
            checked += 1;

            // BFS in MST from u to v
            let path_len = bfs_path_length(&mst_adj, u, v, n);
            if path_len > 0 {
                cycle_lengths.push(path_len + 1); // +1 for the non-MST edge
            }
        }

        let mean_cycle_length = if cycle_lengths.is_empty() { 0.0 }
            else { cycle_lengths.iter().sum::<usize>() as f64 / cycle_lengths.len() as f64 };

        // 6-edge cycles: count cycles of length exactly 6
        let six_edge_cycles = cycle_lengths.iter().filter(|&&l| l == 6).count();
        let six_edge_fraction = if cycle_lengths.is_empty() { 0.0 }
            else { six_edge_cycles as f64 / cycle_lengths.len() as f64 };

        // Steiner ratio: MST_weight / Steiner_tree_weight (approximated)
        // For Euclidean Steiner, ratio >= sqrt(3)/2 ~ 0.866
        let steiner_lower_bound = 3.0f64.sqrt() / 2.0;

        // Edge weight distribution: variance and skewness
        let weight_var = if mst_edge_weights.len() > 1 {
            mst_edge_weights.iter().map(|w| (w - mean_edge_weight).powi(2)).sum::<f64>()
                / (mst_edge_weights.len() - 1) as f64
        } else { 0.0 };

        // Dendrogram height ratios (successive merge distances)
        let mut merge_ratios = Vec::new();
        for i in 1..mst_edge_weights.len() {
            if mst_edge_weights[i - 1] > 1e-15 {
                merge_ratios.push(mst_edge_weights[i] / mst_edge_weights[i - 1]);
            }
        }
        let mean_merge_ratio = if merge_ratios.is_empty() { 1.0 }
            else { merge_ratios.iter().sum::<f64>() / merge_ratios.len() as f64 };

        // n=6 resonance
        let n6_cycle_match = (-((mean_cycle_length - 6.0).abs() * 0.3)).exp();

        let mut result = HashMap::new();
        result.insert("mst_weight".into(), vec![mst_weight]);
        result.insert("mean_edge_weight".into(), vec![mean_edge_weight]);
        result.insert("bottleneck".into(), vec![bottleneck]);
        result.insert("max_degree".into(), vec![max_degree as f64]);
        result.insert("mean_degree".into(), vec![mean_degree]);
        result.insert("leaf_count".into(), vec![leaves as f64]);
        result.insert("mean_cycle_length".into(), vec![mean_cycle_length]);
        result.insert("six_edge_cycle_fraction".into(), vec![six_edge_fraction]);
        result.insert("edge_weight_variance".into(), vec![weight_var]);
        result.insert("mean_merge_ratio".into(), vec![mean_merge_ratio]);
        result.insert("steiner_lower_bound".into(), vec![steiner_lower_bound]);
        result.insert("n6_cycle_match".into(), vec![n6_cycle_match]);
        result.insert("mst_edge_weights".into(), mst_edge_weights);
        result
    }
}

fn find(parent: &mut Vec<usize>, x: usize) -> usize {
    if parent[x] != x {
        parent[x] = find(parent, parent[x]);
    }
    parent[x]
}

fn union(parent: &mut Vec<usize>, rank: &mut Vec<usize>, x: usize, y: usize) {
    if rank[x] < rank[y] {
        parent[x] = y;
    } else if rank[x] > rank[y] {
        parent[y] = x;
    } else {
        parent[y] = x;
        rank[x] += 1;
    }
}

fn bfs_path_length(adj: &[Vec<(usize, f64)>], src: usize, dst: usize, n: usize) -> usize {
    let mut dist = vec![usize::MAX; n];
    dist[src] = 0;
    let mut queue = std::collections::VecDeque::new();
    queue.push_back(src);
    while let Some(u) = queue.pop_front() {
        if u == dst { return dist[u]; }
        for &(v, _) in &adj[u] {
            if dist[v] == usize::MAX {
                dist[v] = dist[u] + 1;
                queue.push_back(v);
            }
        }
    }
    0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_minimum_spanning_tree() {
        let mut data = Vec::new();
        for i in 0..10 {
            data.push(i as f64);
            data.push((i as f64 * 0.5).sin() * 3.0);
        }
        let n = 10;
        let d = 2;
        let shared = SharedData::compute(&data, n, d);
        let r = MinimumSpanningTreeLens.scan(&data, n, d, &shared);
        assert!(r.contains_key("mst_weight"));
        assert!(r["mst_weight"][0] > 0.0);
        assert_eq!(r["mst_edge_weights"].len(), 9); // n-1 edges
        assert!(r["leaf_count"][0] >= 2.0);
    }
}
