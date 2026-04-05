//! Analysis commands over the persisted topology:
//! - convergence: find invariants repeating across ≥K projects/domains
//! - query: find points similar to a query string (simhash distance)
//! - frontier: low-density (periphery) points — next breakthrough candidates
//! - bridges: points connecting two domains

use std::collections::HashMap;

use super::embedding::{distance, simhash};
use super::topology::{Point, Topology};

/// A cluster of near-duplicate points across domains.
#[derive(Debug, Clone)]
pub struct ConvergenceCluster {
    pub representative_id: String,
    pub representative_invariant: String,
    pub domains: Vec<String>,
    pub member_ids: Vec<String>,
    pub size: usize,
}

/// Find clusters of points within `eps` whose members span ≥ `min_domains` distinct domains.
pub fn find_convergence(t: &Topology, eps: f32, min_domains: usize) -> Vec<ConvergenceCluster> {
    // Union-find via simhash bucket: group points whose pairwise distance ≤ eps.
    // For large N this is O(N²); we limit by first bucketing on top-8 bits of simhash.
    let n = t.points.len();
    if n == 0 { return vec![]; }

    // Precompute simhashes as u128 for all points.
    let hashes: Vec<u128> = t.points.iter()
        .map(|p| u128::from_str_radix(&p.simhash, 16).unwrap_or(0))
        .collect();

    // Union-find.
    let mut parent: Vec<usize> = (0..n).collect();
    fn find(parent: &mut [usize], x: usize) -> usize {
        let mut x = x;
        while parent[x] != x {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        x
    }
    fn union(parent: &mut [usize], a: usize, b: usize) {
        let ra = find(parent, a);
        let rb = find(parent, b);
        if ra != rb { parent[ra] = rb; }
    }

    // O(N²) all-pairs — for n≤20k this is ~200M comparisons (~2 sec on M-series).
    for i in 0..n {
        for j in (i+1)..n {
            if distance(hashes[i], hashes[j]) <= eps {
                union(&mut parent, i, j);
            }
        }
    }

    // Gather clusters.
    let mut clusters: HashMap<usize, Vec<usize>> = HashMap::new();
    for i in 0..n {
        let r = find(&mut parent, i);
        clusters.entry(r).or_default().push(i);
    }

    // Filter by domain diversity.
    let mut out: Vec<ConvergenceCluster> = Vec::new();
    for (_root, members) in clusters {
        if members.len() < 2 { continue; }
        let mut domains: Vec<String> = members.iter()
            .map(|&i| t.points[i].domain.clone())
            .collect();
        domains.sort();
        domains.dedup();
        if domains.len() < min_domains { continue; }
        let rep = &t.points[members[0]];
        out.push(ConvergenceCluster {
            representative_id: rep.id.clone(),
            representative_invariant: rep.singularity.invariant.chars().take(140).collect(),
            domains,
            member_ids: members.iter().map(|&i| t.points[i].id.clone()).collect(),
            size: members.len(),
        });
    }
    out.sort_by(|a, b| b.size.cmp(&a.size));
    out
}

/// Top-K points similar to a query string (lowest simhash distance).
pub fn query_similar<'a>(t: &'a Topology, query: &str, k: usize) -> Vec<(f32, &'a Point)> {
    let q = simhash(query);
    let mut scored: Vec<(f32, &Point)> = t.points.iter()
        .map(|p| {
            let h = u128::from_str_radix(&p.simhash, 16).unwrap_or(0);
            (distance(q, h), p)
        })
        .collect();
    scored.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(k);
    scored
}

/// Top-K frontier (low neighbor density = boundary candidates).
/// Without precomputed edges, approximates density by counting points within eps.
pub fn frontier_points<'a>(t: &'a Topology, eps: f32, k: usize) -> Vec<(usize, &'a Point)> {
    let hashes: Vec<u128> = t.points.iter()
        .map(|p| u128::from_str_radix(&p.simhash, 16).unwrap_or(0))
        .collect();
    let n = t.points.len();
    let mut densities: Vec<(usize, usize)> = (0..n).map(|i| {
        let mut count = 0;
        for j in 0..n {
            if i == j { continue; }
            if distance(hashes[i], hashes[j]) <= eps { count += 1; }
        }
        (count, i)
    }).collect();
    densities.sort_by_key(|(c, _)| *c); // ascending: lowest density first
    densities.truncate(k);
    densities.into_iter().map(|(c, i)| (c, &t.points[i])).collect()
}

/// Points that sit between two domains: close to points in both.
pub fn bridges_between<'a>(t: &'a Topology, dom_a: &str, dom_b: &str, eps: f32, k: usize)
    -> Vec<(&'a Point, usize, usize)>
{
    let hashes: Vec<u128> = t.points.iter()
        .map(|p| u128::from_str_radix(&p.simhash, 16).unwrap_or(0))
        .collect();
    let idx_a: Vec<usize> = t.points.iter().enumerate()
        .filter(|(_, p)| p.domain == dom_a).map(|(i, _)| i).collect();
    let idx_b: Vec<usize> = t.points.iter().enumerate()
        .filter(|(_, p)| p.domain == dom_b).map(|(i, _)| i).collect();
    if idx_a.is_empty() || idx_b.is_empty() { return vec![]; }

    let mut scored: Vec<(usize, usize, usize)> = t.points.iter().enumerate().map(|(i, _)| {
        let h = hashes[i];
        let na = idx_a.iter().filter(|&&j| distance(h, hashes[j]) <= eps).count();
        let nb = idx_b.iter().filter(|&&j| distance(h, hashes[j]) <= eps).count();
        (i, na, nb)
    }).collect();
    // Bridge score: min(na, nb) high means connects both
    scored.sort_by(|a, b| (b.1.min(b.2)).cmp(&(a.1.min(a.2))));
    scored.truncate(k);
    scored.into_iter()
        .filter(|(_, na, nb)| *na > 0 && *nb > 0)
        .map(|(i, na, nb)| (&t.points[i], na, nb))
        .collect()
}

/// Top-K highest-density points (interior/core) — candidates for re-blowup seeds.
/// Opposite of frontier: points with many neighbors = validated core concepts.
pub fn core_points<'a>(t: &'a Topology, eps: f32, k: usize) -> Vec<(usize, &'a Point)> {
    let hashes: Vec<u128> = t.points.iter()
        .map(|p| u128::from_str_radix(&p.simhash, 16).unwrap_or(0))
        .collect();
    let n = t.points.len();
    let mut densities: Vec<(usize, usize)> = (0..n).map(|i| {
        let mut count = 0;
        for j in 0..n {
            if i == j { continue; }
            if distance(hashes[i], hashes[j]) <= eps { count += 1; }
        }
        (count, i)
    }).collect();
    densities.sort_by_key(|(c, _)| std::cmp::Reverse(*c)); // highest density first
    densities.truncate(k);
    densities.into_iter().map(|(c, i)| (c, &t.points[i])).collect()
}

/// Rebuild all edges for a topology (O(N²)). Writes batched to disk.
/// Returns (edge_count, elapsed_sec).
pub fn rebuild_edges(
    t: &mut Topology,
    eps: f32,
    edges_path: &std::path::Path,
    progress_every: usize,
) -> std::io::Result<(usize, u64)> {
    use std::io::Write;
    use std::time::Instant;

    let started = Instant::now();
    let n = t.points.len();
    if n < 2 { return Ok((0, 0)); }

    let hashes: Vec<u128> = t.points.iter()
        .map(|p| u128::from_str_radix(&p.simhash, 16).unwrap_or(0))
        .collect();

    // Truncate existing edges file (rebuild replaces)
    let mut f = std::fs::OpenOptions::new()
        .create(true).write(true).truncate(true).open(edges_path)?;

    let mut count = 0;
    let ts = {
        use std::time::{SystemTime, UNIX_EPOCH};
        let secs = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
        format!("{}Z", secs)
    };
    for i in 0..n {
        for j in (i+1)..n {
            let d = distance(hashes[i], hashes[j]);
            if d <= eps {
                let line = format!(
                    "{{\"from\":\"{}\",\"to\":\"{}\",\"distance\":{:.4},\"ts\":\"{}\"}}\n",
                    t.points[i].id, t.points[j].id, d, ts
                );
                f.write_all(line.as_bytes())?;
                count += 1;
            }
        }
        if progress_every > 0 && (i + 1) % progress_every == 0 {
            let elapsed = started.elapsed().as_secs();
            let pct = ((i + 1) as f64 * 100.0) / n as f64;
            eprintln!("  rebuild_edges: {}/{} points ({:.1}%) edges={} elapsed={}s",
                      i + 1, n, pct, count, elapsed);
        }
    }
    f.sync_all()?;
    Ok((count, started.elapsed().as_secs()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::singularity_recursion::topology::{Singularity, Topology};

    fn sing(s: &str) -> Singularity {
        Singularity { invariant: s.into(), confidence: 0.5, novelty: 0.5, depth_reached: 1 }
    }

    fn make_topo() -> Topology {
        let mut t = Topology::new(0.5);
        // 3 domains with identical core phrase
        for (dom, label) in &[("proj_a","n=6 sigma tau alpha"),("proj_b","n=6 sigma tau beta"),("proj_c","n=6 sigma tau gamma"),("proj_d","unrelated banana")] {
            let p = t.make_point(dom, None, sing(label), 1, "t");
            t.insert_point(p, "t");
        }
        t
    }

    #[test]
    fn convergence_finds_cross_domain_cluster() {
        let t = make_topo();
        let clusters = find_convergence(&t, 0.35, 3);
        // 3 "n=6 sigma tau ..." points should cluster across 3 domains
        assert!(!clusters.is_empty(), "expected at least one convergence cluster");
        let c = &clusters[0];
        assert!(c.domains.len() >= 3);
    }

    #[test]
    fn query_returns_closest() {
        let t = make_topo();
        let out = query_similar(&t, "n=6 sigma tau something", 2);
        assert_eq!(out.len(), 2);
        assert!(out[0].0 < out[1].0);
    }

    #[test]
    fn frontier_returns_lowest_density() {
        let t = make_topo();
        let out = frontier_points(&t, 0.35, 1);
        assert_eq!(out.len(), 1);
        // "unrelated banana" should be the loneliest
        assert_eq!(out[0].1.domain, "proj_d");
    }

    #[test]
    fn bridges_span_two_domains() {
        let t = make_topo();
        let out = bridges_between(&t, "proj_a", "proj_b", 0.5, 5);
        // Any proj_c point is near both proj_a and proj_b via the "n=6 sigma tau" core
        assert!(!out.is_empty());
    }
}
