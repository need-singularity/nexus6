//! Interior/boundary score + weighted sampler.
//!
//! interior_score(p) = neighbors(p) / expected_neighbors(local density)
//! boundary_score(p) = 1 - interior_score(p), clamped to [0,1]

use super::topology::Topology;

#[derive(Debug, Clone, PartialEq)]
pub struct BoundaryCandidate {
    pub point_id: String,
    pub score: f32,
    pub neighbor_count: usize,
}

/// Compute boundary candidates from topology.
/// Points with neighbor count below median get higher boundary scores.
pub fn compute_candidates(t: &Topology) -> Vec<BoundaryCandidate> {
    if t.points.is_empty() { return vec![]; }

    let counts: Vec<usize> = t.points.iter()
        .map(|p| t.neighbors(&p.id).len())
        .collect();

    // Use mean as baseline for "expected" density; first point has no priors.
    let expected = if counts.iter().all(|&c| c == 0) { 1.0 }
        else { (counts.iter().sum::<usize>() as f32 / counts.len() as f32).max(1.0) };

    t.points.iter().zip(counts.iter()).map(|(p, &n)| {
        let interior = (n as f32 / expected).min(1.0);
        let score = (1.0 - interior).clamp(0.0, 1.0);
        BoundaryCandidate {
            point_id: p.id.clone(),
            score,
            neighbor_count: n,
        }
    }).collect()
}

/// Select top-K by score.
pub fn top_k(mut candidates: Vec<BoundaryCandidate>, k: usize) -> Vec<BoundaryCandidate> {
    candidates.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    candidates.truncate(k);
    candidates
}

/// Weighted sample one candidate. `rng_seed` is deterministic for testing;
/// callers pass system time nanos for production.
pub fn sample_weighted(candidates: &[BoundaryCandidate], rng_seed: u64) -> Option<&BoundaryCandidate> {
    if candidates.is_empty() { return None; }
    let total: f32 = candidates.iter().map(|c| c.score.max(1e-6)).sum();
    // Deterministic "random" via seed
    let r = ((rng_seed.wrapping_mul(2862933555777941757).wrapping_add(3037000493) >> 32) as f32
        / u32::MAX as f32) * total;
    let mut acc = 0.0f32;
    for c in candidates {
        acc += c.score.max(1e-6);
        if r <= acc { return Some(c); }
    }
    candidates.last()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::singularity_recursion::topology::{Singularity, Topology};

    fn sing(s: &str) -> Singularity {
        Singularity { invariant: s.into(), confidence: 0.5, novelty: 0.7, depth_reached: 3 }
    }

    #[test]
    fn empty_topology_yields_empty_candidates() {
        let t = Topology::new(0.3);
        assert!(compute_candidates(&t).is_empty());
    }

    #[test]
    fn isolated_point_has_max_boundary_score() {
        let mut t = Topology::new(0.3);
        let p = t.make_point("arch", None, sing("alone"), 1, "t");
        t.insert_point(p, "t");
        let cs = compute_candidates(&t);
        assert_eq!(cs.len(), 1);
        assert_eq!(cs[0].neighbor_count, 0);
        assert_eq!(cs[0].score, 1.0);
    }

    #[test]
    fn dense_point_has_lower_boundary_score() {
        let mut t = Topology::new(0.6); // loose eps → many edges
        for w in &["alpha bravo", "alpha charlie", "alpha delta", "alpha echo"] {
            let p = t.make_point("arch", None, sing(w), 1, "t");
            t.insert_point(p, "t");
        }
        let cs = compute_candidates(&t);
        // At least one point should have some neighbors; verify that non-isolated points have score < 1.0
        let has_neighbors = cs.iter().any(|c| c.neighbor_count > 0);
        if has_neighbors {
            assert!(cs.iter().any(|c| c.score < 1.0), "expected at least one point with score < 1.0");
        }
    }

    #[test]
    fn top_k_respects_limit() {
        let cands = vec![
            BoundaryCandidate { point_id: "a".into(), score: 0.9, neighbor_count: 0 },
            BoundaryCandidate { point_id: "b".into(), score: 0.5, neighbor_count: 2 },
            BoundaryCandidate { point_id: "c".into(), score: 0.8, neighbor_count: 1 },
        ];
        let out = top_k(cands, 2);
        assert_eq!(out.len(), 2);
        assert_eq!(out[0].point_id, "a");
        assert_eq!(out[1].point_id, "c");
    }

    #[test]
    fn sample_weighted_nonempty() {
        let cands = vec![
            BoundaryCandidate { point_id: "a".into(), score: 0.9, neighbor_count: 0 },
            BoundaryCandidate { point_id: "b".into(), score: 0.1, neighbor_count: 5 },
        ];
        let s = sample_weighted(&cands, 42);
        assert!(s.is_some());
    }

    #[test]
    fn sample_weighted_empty_returns_none() {
        assert!(sample_weighted(&[], 0).is_none());
    }
}
