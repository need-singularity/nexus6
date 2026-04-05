//! Topology graph: points (singularities) + edges (proximity).
//!
//! topology.jsonl and edges.jsonl are append-only, source of truth.

use std::collections::{HashMap, HashSet};
use std::fs::OpenOptions;
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

use serde::{Deserialize, Serialize};

use super::embedding::{distance, simhash, to_vector};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Singularity {
    pub invariant: String,
    pub confidence: f64,
    pub novelty: f64,
    pub depth_reached: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Point {
    pub id: String,
    pub domain: String,
    pub seed_from: Option<String>,
    pub simhash: String,         // 32-char hex of u128
    pub embedding: [f32; 16],
    pub singularity: Singularity,
    pub discovered_at_tick: u64,
    pub ts: String,
    /// mk2: physics sector (backward-compat: defaults to None for old points)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mk2_sector: Option<String>,
    /// mk2: prime set as sorted vec (e.g. [2,3,5])
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mk2_primes: Option<Vec<u64>>,
    /// mk2: classifier confidence
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mk2_confidence: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Edge {
    pub from: String,
    pub to: String,
    pub distance: f32,
    pub ts: String,
}

pub struct Topology {
    pub points: Vec<Point>,
    pub edges: Vec<Edge>,
    pub eps: f32,
}

impl Topology {
    pub fn new(eps: f32) -> Self {
        Self { points: Vec::new(), edges: Vec::new(), eps }
    }

    pub fn next_id(&self) -> String {
        format!("p_{:06}", self.points.len())
    }

    /// Create a Point from a Singularity, computing embedding.
    pub fn make_point(
        &self,
        domain: &str,
        seed_from: Option<String>,
        sing: Singularity,
        tick: u64,
        ts: &str,
    ) -> Point {
        let h = simhash(&sing.invariant);
        // mk2: classify the invariant text
        let (mk2_sector, mk2_primes, mk2_confidence) = classify_point_mk2(&sing.invariant);
        Point {
            id: self.next_id(),
            domain: domain.to_string(),
            seed_from,
            simhash: format!("{:032x}", h),
            embedding: to_vector(h),
            singularity: sing,
            discovered_at_tick: tick,
            ts: ts.to_string(),
            mk2_sector,
            mk2_primes,
            mk2_confidence,
        }
    }

    /// Append point to in-memory state and compute edges to existing points.
    pub fn insert_point(&mut self, p: Point, ts: &str) -> Vec<Edge> {
        let h_new = u128::from_str_radix(&p.simhash, 16).unwrap_or(0);
        let mut new_edges = Vec::new();
        for existing in &self.points {
            let h_ex = u128::from_str_radix(&existing.simhash, 16).unwrap_or(0);
            let d = distance(h_new, h_ex);
            if d <= self.eps {
                new_edges.push(Edge {
                    from: p.id.clone(),
                    to: existing.id.clone(),
                    distance: d,
                    ts: ts.to_string(),
                });
            }
        }
        self.edges.extend(new_edges.iter().cloned());
        self.points.push(p);
        new_edges
    }

    /// Neighbors of a point id (symmetric edge lookup).
    pub fn neighbors(&self, id: &str) -> Vec<&str> {
        self.edges.iter()
            .filter_map(|e| {
                if e.from == id { Some(e.to.as_str()) }
                else if e.to == id { Some(e.from.as_str()) }
                else { None }
            })
            .collect()
    }
}

/// Append a point to topology.jsonl with fsync.
pub fn append_point(path: &Path, p: &Point) -> std::io::Result<()> {
    let mut f = OpenOptions::new().create(true).append(true).open(path)?;
    let line = serde_json::to_string(p)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    writeln!(f, "{}", line)?;
    f.sync_all()?;
    Ok(())
}

/// Append an edge with fsync.
pub fn append_edge(path: &Path, e: &Edge) -> std::io::Result<()> {
    let mut f = OpenOptions::new().create(true).append(true).open(path)?;
    let line = serde_json::to_string(e)
        .map_err(|err| std::io::Error::new(std::io::ErrorKind::InvalidData, err))?;
    writeln!(f, "{}", line)?;
    f.sync_all()?;
    Ok(())
}

/// Load topology from jsonl files (source of truth).
pub fn load(points_path: &Path, edges_path: &Path, eps: f32) -> std::io::Result<Topology> {
    let mut t = Topology::new(eps);
    if points_path.exists() {
        let f = std::fs::File::open(points_path)?;
        for line in BufReader::new(f).lines() {
            let line = line?;
            if line.trim().is_empty() { continue; }
            if let Ok(p) = serde_json::from_str::<Point>(&line) {
                t.points.push(p);
            }
        }
    }
    if edges_path.exists() {
        let f = std::fs::File::open(edges_path)?;
        for line in BufReader::new(f).lines() {
            let line = line?;
            if line.trim().is_empty() { continue; }
            if let Ok(e) = serde_json::from_str::<Edge>(&line) {
                t.edges.push(e);
            }
        }
    }
    Ok(t)
}

/// mk2: classify a point's invariant text → (sector, primes, confidence).
/// Extracts numeric values from the text and runs classify_v2.
fn classify_point_mk2(text: &str) -> (Option<String>, Option<Vec<u64>>, Option<f64>) {
    use crate::mk2::classify_v2::{classify_v2, default_sectors};
    use crate::mk2::primes::PrimeSet;

    // Extract numbers from text (quick regex-free scan)
    let values: Vec<f64> = text
        .split(|c: char| !c.is_ascii_digit() && c != '.' && c != '-')
        .filter_map(|s| s.parse::<f64>().ok())
        .filter(|v| v.is_finite() && *v != 0.0)
        .collect();

    let mut ps = PrimeSet::empty();
    for &v in &values {
        if v.abs() < 1e-10 || v.abs() > 1e6 { continue; }
        for den in &[1u64, 2, 3, 5, 6, 7, 15, 21, 35, 105, 210] {
            let num = (v * *den as f64).round() as i128;
            if num > 0 && ((num as f64 / *den as f64) - v).abs() < 1e-6 {
                for (p, _) in crate::mk2::primes::factorize(num.unsigned_abs() as u64) {
                    ps.insert(p);
                }
                for (p, _) in crate::mk2::primes::factorize(*den) {
                    ps.insert(p);
                }
                break;
            }
        }
    }

    let sectors = default_sectors();
    let result = classify_v2(text, &values, &ps, &sectors);

    let sector = Some(result.sector.to_string());
    let primes = if ps.is_empty() { None } else { Some(ps.to_vec()) };
    let confidence = Some(result.confidence);

    (sector, primes, confidence)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp_dir(name: &str) -> std::path::PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_topo_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_dir_all(&p);
        std::fs::create_dir_all(&p).unwrap();
        p
    }

    fn sing(s: &str) -> Singularity {
        Singularity { invariant: s.into(), confidence: 0.5, novelty: 0.7, depth_reached: 3 }
    }

    #[test]
    fn make_point_populates_embedding() {
        let t = Topology::new(0.3);
        let p = t.make_point("arch", None, sing("a b c"), 1, "t");
        assert_eq!(p.id, "p_000000");
        assert_eq!(p.simhash.len(), 32);
    }

    #[test]
    fn insert_creates_edges_for_similar_points() {
        let mut t = Topology::new(0.5);
        let p1 = t.make_point("arch", None, sing("alpha bravo charlie"), 1, "t");
        t.insert_point(p1, "t");
        let p2 = t.make_point("arch", Some("p_000000".into()), sing("alpha bravo delta"), 2, "t");
        let edges = t.insert_point(p2, "t");
        assert!(!edges.is_empty(), "expected edge between similar points");
    }

    #[test]
    fn insert_no_edges_for_different() {
        let mut t = Topology::new(0.1);
        let p1 = t.make_point("arch", None, sing("banana quantum"), 1, "t");
        t.insert_point(p1, "t");
        let p2 = t.make_point("arch", None, sing("fourier transform lock"), 2, "t");
        let edges = t.insert_point(p2, "t");
        assert!(edges.is_empty(), "expected no edges for distant points");
    }

    #[test]
    fn append_and_load_roundtrip() {
        let d = tmp_dir("roundtrip");
        let points_path = d.join("topology.jsonl");
        let edges_path = d.join("edges.jsonl");
        let mut t = Topology::new(0.5);
        let p1 = t.make_point("arch", None, sing("alpha bravo"), 1, "t");
        let p1c = p1.clone();
        t.insert_point(p1, "t");
        append_point(&points_path, &p1c).unwrap();
        let loaded = load(&points_path, &edges_path, 0.5).unwrap();
        assert_eq!(loaded.points.len(), 1);
        assert_eq!(loaded.points[0].id, "p_000000");
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn neighbors_symmetric() {
        let mut t = Topology::new(0.5);
        let p1 = t.make_point("arch", None, sing("alpha bravo charlie"), 1, "t");
        t.insert_point(p1, "t");
        let p2 = t.make_point("arch", None, sing("alpha bravo delta"), 2, "t");
        t.insert_point(p2, "t");
        let n1 = t.neighbors("p_000000");
        let n2 = t.neighbors("p_000001");
        assert!(n1.contains(&"p_000001"));
        assert!(n2.contains(&"p_000000"));
    }
}

// ════════════════════════════════════════════════════════════════
// Knowledge Simplicial Complex — Gap-Guided Blowup Seeds
// ════════════════════════════════════════════════════════════════

use std::collections::BTreeSet;

/// A node in the knowledge complex.
#[derive(Debug, Clone)]
pub struct KnowledgeNode {
    pub id: String,
    pub value: Option<f64>,
    pub expr: Option<String>,
    pub domain: String,
    pub grade: u8,
}

/// The knowledge simplicial complex.
/// 0-simplex=node, 1-simplex=edge, 2-simplex=triangle, ...
#[derive(Debug)]
pub struct KnowledgeComplex {
    pub nodes: HashMap<String, KnowledgeNode>,
    pub edges: HashSet<(String, String)>,     // sorted pairs
    pub triangles: HashSet<(String, String, String)>, // sorted triples
}

/// A gap = missing simplex with high discovery potential.
#[derive(Debug, Clone)]
pub struct Gap {
    pub nodes: Vec<String>,
    pub dimension: usize,
    pub score: f64,
    pub seed_expr: Option<String>,
}

impl KnowledgeComplex {
    /// Build from .n6 parsed JSON (array of entries).
    pub fn from_n6_json(json_str: &str) -> Self {
        let mut complex = KnowledgeComplex {
            nodes: HashMap::new(),
            edges: HashSet::new(),
            triangles: HashSet::new(),
        };

        let entries: Vec<serde_json::Value> = match serde_json::from_str(json_str) {
            Ok(v) => v,
            Err(_) => return complex,
        };

        for entry in &entries {
            let id = entry["name"].as_str().unwrap_or("").to_string();
            if id.is_empty() { continue; }
            let value = entry["value"].as_f64();
            let expr = entry["expr"].as_str().map(|s| s.to_string());
            let domain = entry["domain"].as_str().unwrap_or("").to_string();
            let grade = entry["grade"].as_u64().unwrap_or(0) as u8;

            complex.nodes.insert(id.clone(), KnowledgeNode {
                id: id.clone(), value, expr, domain, grade,
            });

            // edges from depends_on
            if let Some(deps) = entry["depends_on"].as_array() {
                for dep in deps {
                    if let Some(dep_id) = dep.as_str() {
                        let (a, b) = if id < dep_id.to_string() {
                            (id.clone(), dep_id.to_string())
                        } else {
                            (dep_id.to_string(), id.clone())
                        };
                        if a != b {
                            complex.edges.insert((a, b));
                        }
                    }
                }
            }
        }

        // Auto-detect triangles: if A-B, A-C, B-C all exist
        let edge_set: HashSet<(&str, &str)> = complex.edges.iter()
            .map(|(a, b)| (a.as_str(), b.as_str()))
            .collect();
        let ids: Vec<&str> = complex.nodes.keys().map(|s| s.as_str()).collect();
        for i in 0..ids.len() {
            for j in (i+1)..ids.len() {
                for k in (j+1)..ids.len() {
                    let (a, b, c) = (ids[i], ids[j], ids[k]);
                    let has_ab = edge_set.contains(&(a, b)) || edge_set.contains(&(b, a));
                    let has_ac = edge_set.contains(&(a, c)) || edge_set.contains(&(c, a));
                    let has_bc = edge_set.contains(&(b, c)) || edge_set.contains(&(c, b));
                    if has_ab && has_ac && has_bc {
                        complex.triangles.insert((a.to_string(), b.to_string(), c.to_string()));
                    }
                }
            }
        }

        complex
    }

    /// Find gaps sorted by discovery potential (highest first).
    pub fn find_gaps(&self, max_gaps: usize) -> Vec<Gap> {
        let mut gaps = Vec::new();
        let ids: Vec<&str> = self.nodes.keys().map(|s| s.as_str()).collect();
        let n6_targets: &[f64] = &[
            1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 12.0, 16.0, 24.0,
            32.0, 48.0, 64.0, 72.0, 128.0, 144.0, 192.0, 220.0, 256.0,
            720.0, 1536.0, 4096.0, 0.333333,
        ];

        // Binary gaps (missing edges between valued nodes)
        for i in 0..ids.len() {
            for j in (i+1)..ids.len() {
                let (a, b) = (ids[i], ids[j]);
                let sorted = if a < b { (a.to_string(), b.to_string()) } else { (b.to_string(), a.to_string()) };
                if self.edges.contains(&sorted) { continue; }

                let na = &self.nodes[a];
                let nb = &self.nodes[b];
                if na.value.is_none() || nb.value.is_none() { continue; }

                let va = na.value.unwrap();
                let vb = nb.value.unwrap();
                let domain_bonus = if na.domain == nb.domain { 0.3 } else { 0.1 };

                // Check if any operation yields an n=6 value
                let ops = [va + vb, va * vb, va - vb, vb - va,
                           if vb != 0.0 { va / vb } else { f64::NAN },
                           if va != 0.0 { vb / va } else { f64::NAN }];
                let mut best_hit = f64::MAX;
                let mut best_expr = String::new();
                for &result in &ops {
                    if result.is_nan() || result.is_infinite() { continue; }
                    for &target in n6_targets {
                        let dist = (result - target).abs();
                        if dist < best_hit {
                            best_hit = dist;
                            best_expr = format!("{}⊕{} ≈ {}", a, b, target);
                        }
                    }
                }

                let proximity_score = if best_hit < 0.001 { 1.0 }
                    else if best_hit < 0.1 { 0.7 }
                    else if best_hit < 1.0 { 0.3 }
                    else { 0.0 };

                let score = domain_bonus + proximity_score;
                if score >= 0.4 {
                    gaps.push(Gap {
                        nodes: vec![a.to_string(), b.to_string()],
                        dimension: 1,
                        score,
                        seed_expr: if proximity_score > 0.0 { Some(best_expr) } else { None },
                    });
                }
            }
        }

        // Ternary gaps (almost-triangles: 2 of 3 edges present)
        for i in 0..ids.len().min(40) {
            for j in (i+1)..ids.len().min(40) {
                for k in (j+1)..ids.len().min(40) {
                    let (a, b, c) = (ids[i], ids[j], ids[k]);
                    let tri = (a.to_string(), b.to_string(), c.to_string());
                    if self.triangles.contains(&tri) { continue; }

                    let has = |x: &str, y: &str| -> bool {
                        let sorted = if x < y { (x.to_string(), y.to_string()) } else { (y.to_string(), x.to_string()) };
                        self.edges.contains(&sorted)
                    };
                    let face_count = [has(a,b), has(a,c), has(b,c)].iter().filter(|&&x| x).count();
                    if face_count >= 2 {
                        // Generate ternary seed
                        let vals: Vec<f64> = [a, b, c].iter()
                            .filter_map(|id| self.nodes.get(*id).and_then(|n| n.value))
                            .collect();
                        let seed = if vals.len() == 3 {
                            let r = vals[0] * vals[1] + vals[2];
                            let closest = n6_targets.iter().min_by(|&&x, &&y|
                                (x - r).abs().partial_cmp(&(y - r).abs()).unwrap()
                            );
                            closest.map(|t| format!("{}·{}+{} ≈ {}", a, b, c, t))
                        } else { None };

                        gaps.push(Gap {
                            nodes: vec![a.to_string(), b.to_string(), c.to_string()],
                            dimension: 2,
                            score: face_count as f64 / 3.0 + 0.2,
                            seed_expr: seed,
                        });
                    }
                }
            }
        }

        gaps.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
        gaps.truncate(max_gaps);
        gaps
    }

    /// Convert gaps to blowup axiom seeds.
    pub fn gaps_to_axioms(&self, gaps: &[Gap]) -> (Vec<String>, HashMap<String, f64>) {
        let mut axioms = Vec::new();
        let mut metrics = HashMap::new();

        for gap in gaps {
            if let Some(ref expr) = gap.seed_expr {
                axioms.push(expr.clone());
            }
            axioms.push(format!("gap_d{}:{}", gap.dimension, gap.nodes.join("+")));

            for nid in &gap.nodes {
                if let Some(node) = self.nodes.get(nid) {
                    if let Some(v) = node.value {
                        metrics.insert(nid.clone(), v);
                    }
                }
            }
        }

        (axioms, metrics)
    }

    /// Euler characteristic: χ = V - E + T
    pub fn euler_char(&self) -> i64 {
        self.nodes.len() as i64 - self.edges.len() as i64 + self.triangles.len() as i64
    }

    pub fn stats(&self) -> String {
        let v = self.nodes.len();
        let e = self.edges.len();
        let t = self.triangles.len();
        let density = if v > 1 { (2 * e) as f64 / (v * (v-1)) as f64 } else { 0.0 };
        format!("V={} E={} T={} χ={} density={:.4}", v, e, t, self.euler_char(), density)
    }
}
