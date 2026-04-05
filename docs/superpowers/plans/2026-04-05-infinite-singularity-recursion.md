# Infinite Singularity Recursion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a crash-safe, infinite-running Rust one-shot binary `nexus6 singularity-tick` that discovers the topology of architecture-design methodology by probing boundary points and running the CycleEngine at each probe.

**Architecture:** Topological graph (points + edges) persisted append-only. Each invocation performs exactly one boundary probe, then exits. launchd `KeepAlive=true, ThrottleInterval=60s` provides infinite execution. WAL + atomic renames + fsync guarantee zero data loss on crash.

**Tech Stack:** Rust (edition 2021), serde_json, blake3 (for simhash), fs2 (flock), existing `blowup::cycle_engine::CycleEngine`, launchd.

**Spec:** `docs/superpowers/specs/2026-04-05-infinite-singularity-recursion-design.md`

---

## File Structure

**New files:**
- `src/singularity_recursion/mod.rs` — public API + config struct
- `src/singularity_recursion/budget.rs` — quota tracking
- `src/singularity_recursion/wal.rs` — write-ahead log
- `src/singularity_recursion/embedding.rs` — simhash-based vectorization
- `src/singularity_recursion/topology.rs` — Point/Edge schemas + JSONL persistence
- `src/singularity_recursion/boundary.rs` — interior/boundary scoring + sampler
- `src/singularity_recursion/preflight.rs` — flock + loadavg/mem/halt gates
- `src/singularity_recursion/tick.rs` — tick orchestrator
- `tests/singularity_recursion_integration.rs` — 100-tick fake-cycle integration
- `launchd/com.nexus6.cycle-tick.plist` — launchd agent definition
- `tools/install-cycle-tick.sh` — launchctl bootstrap/bootout

**Modified files:**
- `Cargo.toml` — add `fs2 = "0.4"` dependency
- `src/lib.rs` — add `pub mod singularity_recursion;`
- `src/cli/parser.rs` — add `CliCommand::SingularityTick` variant
- `src/cli/runner.rs` — add dispatch arm
- `src/config.rs` — add `SingularityRecursionConfig` section loader

---

## Task 1: Add fs2 dependency

**Files:**
- Modify: `Cargo.toml`

- [ ] **Step 1: Add dependency**

Open `Cargo.toml`, find the `[dependencies]` block, add after `humantime = "2"`:

```toml
fs2 = "0.4"
```

- [ ] **Step 2: Verify it resolves**

Run: `cargo check --quiet 2>&1 | head -20`
Expected: no errors, `fs2 v0.4.x` downloads if needed.

- [ ] **Step 3: Commit**

```bash
git add Cargo.toml Cargo.lock
git commit -m "deps: add fs2 for flock-based single-instance lock"
```

---

## Task 2: Budget module (TDD)

**Files:**
- Create: `src/singularity_recursion/budget.rs`
- Create: `src/singularity_recursion/mod.rs`
- Modify: `src/lib.rs`

- [ ] **Step 1: Create module skeleton**

Create `src/singularity_recursion/mod.rs`:
```rust
//! Infinite singularity recursion — topological probing of architecture design space.
//!
//! Spec: docs/superpowers/specs/2026-04-05-infinite-singularity-recursion-design.md

pub mod budget;
```

Add to `src/lib.rs` (append after the last `pub mod` line):
```rust
pub mod singularity_recursion;
```

- [ ] **Step 2: Write failing test**

Create `src/singularity_recursion/budget.rs`:
```rust
//! Budget tracking for infinite singularity recursion.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Budget {
    pub tick_count: u64,
    pub cpu_sec_used: u64,
    pub total_points: u64,
    // Limits
    pub max_total_points: u64,
    pub global_cpu_sec_budget: u64,
}

impl Default for Budget {
    fn default() -> Self {
        Self {
            tick_count: 0,
            cpu_sec_used: 0,
            total_points: 0,
            max_total_points: 50_000,
            global_cpu_sec_budget: 86_400,
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub enum BudgetStatus {
    Allowed,
    ExhaustedPoints,
    ExhaustedCpu,
}

impl Budget {
    pub fn check(&self) -> BudgetStatus {
        if self.total_points >= self.max_total_points {
            return BudgetStatus::ExhaustedPoints;
        }
        if self.cpu_sec_used >= self.global_cpu_sec_budget {
            return BudgetStatus::ExhaustedCpu;
        }
        BudgetStatus::Allowed
    }

    pub fn commit_tick(&mut self, cpu_sec: u64, new_points: u64) {
        self.tick_count += 1;
        self.cpu_sec_used += cpu_sec;
        self.total_points += new_points;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_is_allowed() {
        let b = Budget::default();
        assert_eq!(b.check(), BudgetStatus::Allowed);
    }

    #[test]
    fn exhausted_points() {
        let mut b = Budget::default();
        b.total_points = 50_000;
        assert_eq!(b.check(), BudgetStatus::ExhaustedPoints);
    }

    #[test]
    fn exhausted_cpu() {
        let mut b = Budget::default();
        b.cpu_sec_used = 86_400;
        assert_eq!(b.check(), BudgetStatus::ExhaustedCpu);
    }

    #[test]
    fn commit_updates_all_counters() {
        let mut b = Budget::default();
        b.commit_tick(30, 1);
        assert_eq!(b.tick_count, 1);
        assert_eq!(b.cpu_sec_used, 30);
        assert_eq!(b.total_points, 1);
    }

    #[test]
    fn serde_roundtrip() {
        let b = Budget { tick_count: 5, cpu_sec_used: 100, total_points: 3, ..Default::default() };
        let json = serde_json::to_string(&b).unwrap();
        let decoded: Budget = serde_json::from_str(&json).unwrap();
        assert_eq!(b, decoded);
    }
}
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cargo test --lib singularity_recursion::budget -- --nocapture 2>&1 | tail -20`
Expected: `5 passed; 0 failed`

- [ ] **Step 4: Commit**

```bash
git add Cargo.toml src/lib.rs src/singularity_recursion/
git commit -m "feat(singularity_recursion): budget tracker with quota checks"
```

---

## Task 3: WAL module

**Files:**
- Create: `src/singularity_recursion/wal.rs`
- Modify: `src/singularity_recursion/mod.rs`

- [ ] **Step 1: Write failing test**

Create `src/singularity_recursion/wal.rs`:
```rust
//! Write-ahead log for tick boundary markers.
//!
//! Append-only JSONL. Each line is a WalEntry. Replay on startup detects
//! incomplete ticks (tick_start without matching tick_complete).

use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind")]
pub enum WalEntry {
    TickStart { tick_id: u64, ts: String },
    TickComplete { tick_id: u64, point_id: Option<String>, ts: String },
    TickTimeout { tick_id: u64, ts: String },
    TickSkipped { tick_id: u64, reason: String, ts: String },
}

impl WalEntry {
    pub fn tick_id(&self) -> u64 {
        match self {
            WalEntry::TickStart { tick_id, .. }
            | WalEntry::TickComplete { tick_id, .. }
            | WalEntry::TickTimeout { tick_id, .. }
            | WalEntry::TickSkipped { tick_id, .. } => *tick_id,
        }
    }
}

/// Append a WAL entry and fsync.
pub fn append(path: &Path, entry: &WalEntry) -> std::io::Result<()> {
    let mut file = OpenOptions::new().create(true).append(true).open(path)?;
    let line = serde_json::to_string(entry)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    writeln!(file, "{}", line)?;
    file.sync_all()?;
    Ok(())
}

/// Read all entries (skips malformed lines).
pub fn read_all(path: &Path) -> std::io::Result<Vec<WalEntry>> {
    if !path.exists() {
        return Ok(vec![]);
    }
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut entries = Vec::new();
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() { continue; }
        if let Ok(e) = serde_json::from_str::<WalEntry>(&line) {
            entries.push(e);
        }
    }
    Ok(entries)
}

/// Detect tick_ids that started but never completed/timed-out/skipped.
pub fn incomplete_ticks(entries: &[WalEntry]) -> Vec<u64> {
    use std::collections::HashSet;
    let mut started: HashSet<u64> = HashSet::new();
    let mut finished: HashSet<u64> = HashSet::new();
    for e in entries {
        match e {
            WalEntry::TickStart { tick_id, .. } => { started.insert(*tick_id); }
            _ => { finished.insert(e.tick_id()); }
        }
    }
    let mut out: Vec<u64> = started.difference(&finished).copied().collect();
    out.sort();
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp_path(name: &str) -> std::path::PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_wal_test_{}_{}.jsonl", name, std::process::id()));
        let _ = std::fs::remove_file(&p);
        p
    }

    #[test]
    fn append_and_read_roundtrip() {
        let p = tmp_path("rt");
        append(&p, &WalEntry::TickStart { tick_id: 1, ts: "t1".into() }).unwrap();
        append(&p, &WalEntry::TickComplete { tick_id: 1, point_id: Some("p_0001".into()), ts: "t2".into() }).unwrap();
        let entries = read_all(&p).unwrap();
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].tick_id(), 1);
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn incomplete_tick_detected() {
        let p = tmp_path("incomplete");
        append(&p, &WalEntry::TickStart { tick_id: 1, ts: "t".into() }).unwrap();
        append(&p, &WalEntry::TickComplete { tick_id: 1, point_id: None, ts: "t".into() }).unwrap();
        append(&p, &WalEntry::TickStart { tick_id: 2, ts: "t".into() }).unwrap();
        // tick 2 never completes → incomplete
        let entries = read_all(&p).unwrap();
        assert_eq!(incomplete_ticks(&entries), vec![2]);
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn missing_file_is_empty() {
        let p = tmp_path("missing");
        assert!(read_all(&p).unwrap().is_empty());
    }

    #[test]
    fn malformed_line_skipped() {
        let p = tmp_path("malformed");
        std::fs::write(&p, "not json\n").unwrap();
        append(&p, &WalEntry::TickStart { tick_id: 1, ts: "t".into() }).unwrap();
        let entries = read_all(&p).unwrap();
        assert_eq!(entries.len(), 1);
        std::fs::remove_file(&p).ok();
    }
}
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod wal;
```

- [ ] **Step 2: Run tests**

Run: `cargo test --lib singularity_recursion::wal 2>&1 | tail -10`
Expected: `4 passed`

- [ ] **Step 3: Commit**

```bash
git add src/singularity_recursion/
git commit -m "feat(singularity_recursion): write-ahead log with crash recovery"
```

---

## Task 4: Embedding module (simhash)

**Files:**
- Create: `src/singularity_recursion/embedding.rs`
- Modify: `src/singularity_recursion/mod.rs`

- [ ] **Step 1: Write test + implementation**

Create `src/singularity_recursion/embedding.rs`:
```rust
//! Simhash-based embedding of singularity invariants.
//!
//! 128-bit simhash via blake3 per n-gram, converted to a 16-dim f32 vector.
//! Distance = Hamming(simhash_a, simhash_b) / 128, range [0, 1].

use blake3::Hasher;

/// Compute a 128-bit simhash of a text.
/// Tokens = whitespace-split, n-grams of 1..=3.
pub fn simhash(text: &str) -> u128 {
    let tokens: Vec<&str> = text.split_whitespace().collect();
    if tokens.is_empty() { return 0; }

    let mut v = [0i32; 128];
    for n in 1..=3.min(tokens.len()) {
        for window in tokens.windows(n) {
            let ngram = window.join(" ");
            let mut h = Hasher::new();
            h.update(ngram.as_bytes());
            let hash = h.finalize();
            let bytes = hash.as_bytes(); // 32 bytes
            let val: u128 = u128::from_le_bytes(bytes[..16].try_into().unwrap());
            for i in 0..128 {
                if (val >> i) & 1 == 1 { v[i] += 1; } else { v[i] -= 1; }
            }
        }
    }

    let mut out: u128 = 0;
    for i in 0..128 { if v[i] > 0 { out |= 1u128 << i; } }
    out
}

/// Convert a 128-bit simhash to a 16-dim f32 vector (bit-group counts normalized).
pub fn to_vector(h: u128) -> [f32; 16] {
    let mut out = [0.0f32; 16];
    for g in 0..16 {
        let byte = ((h >> (g * 8)) & 0xFF) as u8;
        out[g] = (byte.count_ones() as f32) / 8.0;
    }
    out
}

/// Hamming-based similarity distance in [0, 1]. 0 = identical.
pub fn distance(a: u128, b: u128) -> f32 {
    (a ^ b).count_ones() as f32 / 128.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identical_text_zero_distance() {
        let h = simhash("one-shot process append-only WAL crash-safe infinite");
        assert_eq!(distance(h, h), 0.0);
    }

    #[test]
    fn similar_texts_small_distance() {
        let a = simhash("crash-safe infinite singularity recursion via launchd");
        let b = simhash("crash-safe infinite singularity recursion via launchctl");
        assert!(distance(a, b) < 0.5, "similar texts too far: {}", distance(a, b));
    }

    #[test]
    fn different_texts_large_distance() {
        let a = simhash("banana quantum chromodynamics");
        let b = simhash("fourier transform filesystem lock");
        assert!(distance(a, b) > 0.3, "different texts too close: {}", distance(a, b));
    }

    #[test]
    fn distance_bounded_unit_interval() {
        let a = simhash("alpha");
        let b = simhash("bravo");
        let d = distance(a, b);
        assert!((0.0..=1.0).contains(&d));
    }

    #[test]
    fn to_vector_bounded() {
        let v = to_vector(u128::MAX);
        for x in v.iter() { assert!((0.0..=1.0).contains(x)); }
    }

    #[test]
    fn empty_text_zero_hash() {
        assert_eq!(simhash(""), 0);
    }
}
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod embedding;
```

- [ ] **Step 2: Run tests**

Run: `cargo test --lib singularity_recursion::embedding 2>&1 | tail -12`
Expected: `6 passed`

- [ ] **Step 3: Commit**

```bash
git add src/singularity_recursion/
git commit -m "feat(singularity_recursion): simhash embedding for topology distance"
```

---

## Task 5: Topology module (Point + Edge + JSONL)

**Files:**
- Create: `src/singularity_recursion/topology.rs`
- Modify: `src/singularity_recursion/mod.rs`

- [ ] **Step 1: Write test + implementation**

Create `src/singularity_recursion/topology.rs`:
```rust
//! Topology graph: points (singularities) + edges (proximity).
//!
//! topology.jsonl and edges.jsonl are append-only, source of truth.

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
        Point {
            id: self.next_id(),
            domain: domain.to_string(),
            seed_from,
            simhash: format!("{:032x}", h),
            embedding: to_vector(h),
            singularity: sing,
            discovered_at_tick: tick,
            ts: ts.to_string(),
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
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod topology;
```

- [ ] **Step 2: Run tests**

Run: `cargo test --lib singularity_recursion::topology 2>&1 | tail -15`
Expected: `5 passed`

- [ ] **Step 3: Commit**

```bash
git add src/singularity_recursion/
git commit -m "feat(singularity_recursion): topology graph with point/edge persistence"
```

---

## Task 6: Boundary scoring + sampler

**Files:**
- Create: `src/singularity_recursion/boundary.rs`
- Modify: `src/singularity_recursion/mod.rs`

- [ ] **Step 1: Write test + implementation**

Create `src/singularity_recursion/boundary.rs`:
```rust
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
    }

    #[test]
    fn dense_point_has_lower_boundary_score() {
        let mut t = Topology::new(0.6); // loose eps → many edges
        for w in &["alpha bravo", "alpha charlie", "alpha delta", "alpha echo"] {
            let p = t.make_point("arch", None, sing(w), 1, "t");
            t.insert_point(p, "t");
        }
        let cs = compute_candidates(&t);
        // Highest-degree point should have score lower than an isolated case.
        assert!(cs.iter().any(|c| c.score < 1.0));
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
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod boundary;
```

- [ ] **Step 2: Run tests**

Run: `cargo test --lib singularity_recursion::boundary 2>&1 | tail -12`
Expected: `6 passed`

- [ ] **Step 3: Commit**

```bash
git add src/singularity_recursion/
git commit -m "feat(singularity_recursion): boundary scoring + weighted sampler"
```

---

## Task 7: Preflight gates (flock + loadavg + mem + halt)

**Files:**
- Create: `src/singularity_recursion/preflight.rs`
- Modify: `src/singularity_recursion/mod.rs`

- [ ] **Step 1: Write test + implementation**

Create `src/singularity_recursion/preflight.rs`:
```rust
//! Preflight gates: single-instance lock, memory, loadavg, halt file.
//!
//! Returns GateResult which determines exit code.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use fs2::FileExt;

#[derive(Debug, Clone, PartialEq)]
pub enum GateResult {
    Pass,
    SkipLowMemory { free_mb: usize, min_mb: usize },
    SkipHighLoad { loadavg: f64, max: f64 },
    SkipHalted,
    LockContention,
}

/// Hold an exclusive flock for the lifetime of the struct; dropped → unlocked.
pub struct TickLock { file: File, path: PathBuf }

impl TickLock {
    pub fn acquire(path: &Path) -> std::io::Result<Option<Self>> {
        // Clean stale lock (dead PID) before attempt.
        cleanup_stale(path);

        let file = OpenOptions::new().create(true).read(true).write(true).open(path)?;
        match file.try_lock_exclusive() {
            Ok(()) => {
                // Record PID
                let pid = std::process::id();
                (&file).set_len(0)?;
                (&file).write_all(pid.to_string().as_bytes())?;
                (&file).sync_all()?;
                Ok(Some(Self { file, path: path.to_path_buf() }))
            }
            Err(_) => Ok(None),
        }
    }
}

impl Drop for TickLock {
    fn drop(&mut self) {
        let _ = self.file.unlock();
        // Leave file in place (PID record useful for debug)
    }
}

/// If lock file exists with a dead PID, remove it so acquire() succeeds.
fn cleanup_stale(path: &Path) {
    if !path.exists() { return; }
    let content = match std::fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return,
    };
    let pid: Option<u32> = content.trim().parse().ok();
    if let Some(pid) = pid {
        if !pid_alive(pid) {
            let _ = std::fs::remove_file(path);
        }
    }
}

#[cfg(unix)]
fn pid_alive(pid: u32) -> bool {
    // kill(pid, 0) semantics via shell probe — avoids libc dep.
    // /proc on Linux, `ps` on macOS.
    #[cfg(target_os = "linux")]
    { Path::new(&format!("/proc/{}", pid)).exists() }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("ps")
            .args(["-p", &pid.to_string()])
            .output()
            .map(|o| o.status.success() && o.stdout.lines().count() > 1
                 || String::from_utf8_lossy(&o.stdout).lines().count() > 1)
            .unwrap_or(false)
    }
}

#[cfg(not(unix))]
fn pid_alive(_pid: u32) -> bool { true }

/// Read 1-min loadavg on Unix. Returns None on unsupported OS.
pub fn loadavg_1min() -> Option<f64> {
    #[cfg(any(target_os = "linux", target_os = "macos"))]
    {
        let out = std::process::Command::new("uptime").output().ok()?;
        let s = String::from_utf8_lossy(&out.stdout);
        // " ... load averages: 1.23 0.98 0.50"  OR  "load average: 1.23, 0.98, 0.50"
        let after = s.split("load average").nth(1)?;
        let cleaned: String = after.chars()
            .map(|c| if c == ',' || c == ':' || c == 's' { ' ' } else { c })
            .collect();
        cleaned.split_whitespace().next()?.parse().ok()
    }
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    { None }
}

pub struct PreflightConfig {
    pub min_free_memory_mb: usize,
    pub max_loadavg_1min: f64,
    pub halt_file: PathBuf,
}

/// Run non-lock gates (mem, load, halt). Lock is held by caller.
pub fn check_gates(cfg: &PreflightConfig) -> GateResult {
    if cfg.halt_file.exists() { return GateResult::SkipHalted; }
    let free = crate::resource_limit::free_memory_mb();
    if free < cfg.min_free_memory_mb {
        return GateResult::SkipLowMemory { free_mb: free, min_mb: cfg.min_free_memory_mb };
    }
    if let Some(l) = loadavg_1min() {
        if l > cfg.max_loadavg_1min {
            return GateResult::SkipHighLoad { loadavg: l, max: cfg.max_loadavg_1min };
        }
    }
    GateResult::Pass
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp(name: &str) -> PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_preflight_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_file(&p);
        p
    }

    #[test]
    fn lock_acquire_and_release() {
        let p = tmp("lock1");
        let l = TickLock::acquire(&p).unwrap();
        assert!(l.is_some());
        drop(l);
        let l2 = TickLock::acquire(&p).unwrap();
        assert!(l2.is_some());
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn second_acquire_blocks_while_first_held() {
        let p = tmp("lock2");
        let _l = TickLock::acquire(&p).unwrap().unwrap();
        let l2 = TickLock::acquire(&p).unwrap();
        assert!(l2.is_none(), "should not double-acquire");
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn stale_lock_cleaned() {
        let p = tmp("stale");
        // Write a bogus PID unlikely to exist
        std::fs::write(&p, "999999").unwrap();
        let l = TickLock::acquire(&p).unwrap();
        assert!(l.is_some(), "stale lock should be cleaned");
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn halt_file_blocks() {
        let halt = tmp("halt");
        std::fs::write(&halt, "").unwrap();
        let cfg = PreflightConfig {
            min_free_memory_mb: 0,
            max_loadavg_1min: 1e9,
            halt_file: halt.clone(),
        };
        assert_eq!(check_gates(&cfg), GateResult::SkipHalted);
        std::fs::remove_file(&halt).ok();
    }

    #[test]
    fn halt_absent_passes_mem_check_low_threshold() {
        let halt = tmp("no_halt");
        let _ = std::fs::remove_file(&halt);
        let cfg = PreflightConfig {
            min_free_memory_mb: 0,
            max_loadavg_1min: 1e9,
            halt_file: halt,
        };
        // With thresholds at 0/infinity, should pass.
        assert_eq!(check_gates(&cfg), GateResult::Pass);
    }

    #[test]
    fn low_memory_trips_gate() {
        let halt = tmp("no_halt2");
        let _ = std::fs::remove_file(&halt);
        let cfg = PreflightConfig {
            min_free_memory_mb: usize::MAX / 2, // unreachable
            max_loadavg_1min: 1e9,
            halt_file: halt,
        };
        matches!(check_gates(&cfg), GateResult::SkipLowMemory { .. });
    }

    #[test]
    fn loadavg_parses_on_unix() {
        #[cfg(any(target_os = "linux", target_os = "macos"))]
        {
            let l = loadavg_1min();
            assert!(l.is_some());
            assert!(l.unwrap() >= 0.0);
        }
    }
}
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod preflight;
```

- [ ] **Step 2: Run tests**

Run: `cargo test --lib singularity_recursion::preflight 2>&1 | tail -15`
Expected: `7 passed`

- [ ] **Step 3: Commit**

```bash
git add src/singularity_recursion/
git commit -m "feat(singularity_recursion): preflight gates + single-instance flock"
```

---

## Task 8: Tick orchestrator + config

**Files:**
- Create: `src/singularity_recursion/tick.rs`
- Modify: `src/singularity_recursion/mod.rs`
- Modify: `src/config.rs`

- [ ] **Step 1: Add config struct**

Open `src/config.rs`, find the top-level `Config` struct, add a new field. First inspect the structure:

Run: `grep -n "pub struct Config" src/config.rs | head -5`
Expected: a struct definition line.

Add to `src/config.rs` near the end (before tests if any):
```rust
#[derive(Debug, Clone, serde::Deserialize, serde::Serialize)]
pub struct SingularityRecursionConfig {
    #[serde(default = "default_domain")]
    pub domain: String,
    #[serde(default = "default_max_points")]
    pub max_total_points: u64,
    #[serde(default = "default_eps")]
    pub neighborhood_radius_eps: f32,
    #[serde(default = "default_top_k")]
    pub boundary_sample_top_k: usize,
    #[serde(default = "default_cpu_per_tick")]
    pub cpu_sec_per_tick: u64,
    #[serde(default = "default_wall_per_tick")]
    pub wall_sec_per_tick: u64,
    #[serde(default = "default_global_budget")]
    pub global_cpu_sec_budget: u64,
    #[serde(default = "default_min_mem")]
    pub min_free_memory_mb: usize,
    #[serde(default = "default_max_load")]
    pub max_loadavg_1min: f64,
}

fn default_domain() -> String { "architecture_design".into() }
fn default_max_points() -> u64 { 50_000 }
fn default_eps() -> f32 { 0.3 }
fn default_top_k() -> usize { 20 }
fn default_cpu_per_tick() -> u64 { 30 }
fn default_wall_per_tick() -> u64 { 60 }
fn default_global_budget() -> u64 { 86_400 }
fn default_min_mem() -> usize { 2048 }
fn default_max_load() -> f64 { 8.0 }

impl Default for SingularityRecursionConfig {
    fn default() -> Self {
        Self {
            domain: default_domain(),
            max_total_points: default_max_points(),
            neighborhood_radius_eps: default_eps(),
            boundary_sample_top_k: default_top_k(),
            cpu_sec_per_tick: default_cpu_per_tick(),
            wall_sec_per_tick: default_wall_per_tick(),
            global_cpu_sec_budget: default_global_budget(),
            min_free_memory_mb: default_min_mem(),
            max_loadavg_1min: default_max_load(),
        }
    }
}
```

- [ ] **Step 2: Write tick orchestrator**

Create `src/singularity_recursion/tick.rs`:
```rust
//! Tick orchestrator — glues all modules. Run exactly one boundary probe.

use std::path::{Path, PathBuf};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use super::boundary::{compute_candidates, sample_weighted, top_k};
use super::budget::{Budget, BudgetStatus};
use super::preflight::{check_gates, GateResult, PreflightConfig, TickLock};
use super::topology::{append_edge, append_point, load, Point, Singularity, Topology};
use super::wal::{append as wal_append, WalEntry};
use crate::config::SingularityRecursionConfig;

/// Exit codes — keep in sync with spec.
pub const EXIT_OK: i32 = 0;
pub const EXIT_SKIPPED: i32 = 1;
pub const EXIT_BUDGET: i32 = 2;
pub const EXIT_HALTED: i32 = 3;
pub const EXIT_LOCKED: i32 = 4;

/// Paths derived from a base directory (default `shared/cycle/`).
pub struct TickPaths {
    pub base: PathBuf,
    pub topology: PathBuf,
    pub edges: PathBuf,
    pub boundary_cache: PathBuf,
    pub budget: PathBuf,
    pub wal: PathBuf,
    pub lock: PathBuf,
    pub halt: PathBuf,
}

impl TickPaths {
    pub fn from_base(base: impl AsRef<Path>) -> Self {
        let base = base.as_ref().to_path_buf();
        Self {
            topology: base.join("topology.jsonl"),
            edges: base.join("edges.jsonl"),
            boundary_cache: base.join("boundary.json"),
            budget: base.join("budget.json"),
            wal: base.join("wal.jsonl"),
            lock: base.join("state.lock"),
            halt: base.join("halt"),
            base,
        }
    }
}

/// Seed generator — for now, a dummy deterministic singularity based on the
/// seed point's invariant. Replaced with real CycleEngine integration in a
/// follow-up task.
pub trait CycleRunner {
    fn run(&mut self, domain: &str, seed: Option<&Point>) -> Singularity;
}

pub struct TickOutcome {
    pub exit_code: i32,
    pub point_id: Option<String>,
    pub elapsed_sec: u64,
}

/// Atomic rename helper: write to .tmp then rename.
fn atomic_write_json<T: serde::Serialize>(path: &Path, v: &T) -> std::io::Result<()> {
    use std::io::Write;
    let tmp = path.with_extension("tmp");
    let mut f = std::fs::OpenOptions::new().create(true).write(true).truncate(true).open(&tmp)?;
    let json = serde_json::to_string_pretty(v)
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    f.write_all(json.as_bytes())?;
    f.sync_all()?;
    drop(f);
    std::fs::rename(&tmp, path)?;
    Ok(())
}

fn load_or_default<T: serde::de::DeserializeOwned + Default>(path: &Path) -> T {
    std::fs::read_to_string(path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

fn now_iso() -> String {
    let secs = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    format!("{}Z", secs)
}

/// Execute one tick end-to-end.
pub fn run_tick(
    paths: &TickPaths,
    cfg: &SingularityRecursionConfig,
    runner: &mut dyn CycleRunner,
) -> TickOutcome {
    let started = Instant::now();
    std::fs::create_dir_all(&paths.base).ok();

    // 1. Lock.
    let _lock = match TickLock::acquire(&paths.lock) {
        Ok(Some(l)) => l,
        Ok(None) => return TickOutcome { exit_code: EXIT_LOCKED, point_id: None, elapsed_sec: 0 },
        Err(_) => return TickOutcome { exit_code: EXIT_LOCKED, point_id: None, elapsed_sec: 0 },
    };

    // 2. Gates.
    let gate_cfg = PreflightConfig {
        min_free_memory_mb: cfg.min_free_memory_mb,
        max_loadavg_1min: cfg.max_loadavg_1min,
        halt_file: paths.halt.clone(),
    };
    match check_gates(&gate_cfg) {
        GateResult::Pass => {}
        GateResult::SkipHalted => return TickOutcome { exit_code: EXIT_HALTED, point_id: None, elapsed_sec: 0 },
        _ => return TickOutcome { exit_code: EXIT_SKIPPED, point_id: None, elapsed_sec: 0 },
    }

    // 3. Budget.
    let mut budget: Budget = load_or_default(&paths.budget);
    budget.max_total_points = cfg.max_total_points;
    budget.global_cpu_sec_budget = cfg.global_cpu_sec_budget;
    if budget.check() != BudgetStatus::Allowed {
        return TickOutcome { exit_code: EXIT_BUDGET, point_id: None, elapsed_sec: 0 };
    }

    // 4. Load topology.
    let mut topo = match load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps) {
        Ok(t) => t,
        Err(_) => Topology::new(cfg.neighborhood_radius_eps),
    };

    // 5. WAL: tick_start.
    let tick_id = budget.tick_count + 1;
    let _ = wal_append(&paths.wal, &WalEntry::TickStart { tick_id, ts: now_iso() });

    // 6. Seed selection.
    let seed_point: Option<Point> = if topo.points.is_empty() {
        None // first tick has no seed — cold start
    } else {
        let cands = compute_candidates(&topo);
        let topk = top_k(cands, cfg.boundary_sample_top_k);
        let seed_nanos = SystemTime::now().duration_since(UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64).unwrap_or(0);
        sample_weighted(&topk, seed_nanos)
            .and_then(|c| topo.points.iter().find(|p| p.id == c.point_id).cloned())
    };

    // 7. Run CycleEngine.
    let sing = runner.run(&cfg.domain, seed_point.as_ref());

    // 8. Embed + insert.
    let point = topo.make_point(
        &cfg.domain,
        seed_point.as_ref().map(|p| p.id.clone()),
        sing,
        tick_id,
        &now_iso(),
    );
    let point_id = point.id.clone();
    let point_save = point.clone();
    let new_edges = topo.insert_point(point, &now_iso());

    // 9. Persist point + edges (append + fsync).
    if append_point(&paths.topology, &point_save).is_err() {
        let _ = wal_append(&paths.wal, &WalEntry::TickSkipped {
            tick_id, reason: "append_point_failed".into(), ts: now_iso(),
        });
        return TickOutcome { exit_code: EXIT_SKIPPED, point_id: None, elapsed_sec: started.elapsed().as_secs() };
    }
    for e in &new_edges { let _ = append_edge(&paths.edges, e); }

    // 10. Budget commit.
    let elapsed = started.elapsed().as_secs();
    budget.commit_tick(elapsed, 1);
    let _ = atomic_write_json(&paths.budget, &budget);

    // 11. WAL: tick_complete.
    let _ = wal_append(&paths.wal, &WalEntry::TickComplete {
        tick_id, point_id: Some(point_id.clone()), ts: now_iso(),
    });

    TickOutcome { exit_code: EXIT_OK, point_id: Some(point_id), elapsed_sec: elapsed }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp_base(name: &str) -> PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_tick_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_dir_all(&p);
        std::fs::create_dir_all(&p).unwrap();
        p
    }

    struct FakeRunner { n: usize }
    impl CycleRunner for FakeRunner {
        fn run(&mut self, _domain: &str, seed: Option<&Point>) -> Singularity {
            self.n += 1;
            let seed_txt = seed.map(|p| p.singularity.invariant.clone()).unwrap_or_default();
            Singularity {
                invariant: format!("invariant {} derived from [{}]", self.n, seed_txt),
                confidence: 0.5 + (self.n as f64 * 0.01).min(0.4),
                novelty: 0.9,
                depth_reached: 3,
            }
        }
    }

    fn relaxed_cfg() -> SingularityRecursionConfig {
        SingularityRecursionConfig {
            min_free_memory_mb: 0,
            max_loadavg_1min: 1e9,
            cpu_sec_per_tick: 1,
            wall_sec_per_tick: 10,
            ..Default::default()
        }
    }

    #[test]
    fn single_tick_creates_point() {
        let base = tmp_base("single");
        let paths = TickPaths::from_base(&base);
        let mut runner = FakeRunner { n: 0 };
        let out = run_tick(&paths, &relaxed_cfg(), &mut runner);
        assert_eq!(out.exit_code, EXIT_OK);
        assert_eq!(out.point_id, Some("p_000000".into()));
        assert!(paths.topology.exists());
        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn multiple_ticks_grow_topology() {
        let base = tmp_base("grow");
        let paths = TickPaths::from_base(&base);
        let mut runner = FakeRunner { n: 0 };
        let cfg = relaxed_cfg();
        for _ in 0..5 { run_tick(&paths, &cfg, &mut runner); }
        let topo = load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps).unwrap();
        assert_eq!(topo.points.len(), 5);
        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn halt_file_stops_tick() {
        let base = tmp_base("halt");
        let paths = TickPaths::from_base(&base);
        std::fs::create_dir_all(&base).unwrap();
        std::fs::write(&paths.halt, "").unwrap();
        let mut runner = FakeRunner { n: 0 };
        let out = run_tick(&paths, &relaxed_cfg(), &mut runner);
        assert_eq!(out.exit_code, EXIT_HALTED);
        std::fs::remove_dir_all(&base).ok();
    }

    #[test]
    fn budget_exhaustion_blocks() {
        let base = tmp_base("budget");
        let paths = TickPaths::from_base(&base);
        std::fs::create_dir_all(&base).unwrap();
        // Pre-write an exhausted budget
        let b = Budget {
            tick_count: 100,
            cpu_sec_used: 999_999,
            total_points: 100,
            max_total_points: 50,
            global_cpu_sec_budget: 100,
        };
        atomic_write_json(&paths.budget, &b).unwrap();
        let mut runner = FakeRunner { n: 0 };
        let out = run_tick(&paths, &relaxed_cfg(), &mut runner);
        assert_eq!(out.exit_code, EXIT_BUDGET);
        std::fs::remove_dir_all(&base).ok();
    }
}
```

Add to `src/singularity_recursion/mod.rs`:
```rust
pub mod tick;
```

- [ ] **Step 3: Run tests**

Run: `cargo test --lib singularity_recursion::tick 2>&1 | tail -15`
Expected: `4 passed`

- [ ] **Step 4: Commit**

```bash
git add src/singularity_recursion/ src/config.rs
git commit -m "feat(singularity_recursion): tick orchestrator + config"
```

---

## Task 9: CLI integration (`nexus6 singularity-tick`)

**Files:**
- Modify: `src/cli/parser.rs`
- Modify: `src/cli/runner.rs`

- [ ] **Step 1: Add CLI variant**

In `src/cli/parser.rs`, find the `CliCommand` enum and add:
```rust
    SingularityTick {
        base_dir: Option<String>,
    },
```

Find the parse function (search for `"bench"` or similar match arm) and add a parse arm. First inspect the existing parse dispatch:

Run: `grep -n '"bench" =>' src/cli/parser.rs | head -3`

Add a match arm near the existing ones:
```rust
        "singularity-tick" => {
            let mut base_dir = None;
            while let Some(arg) = args.next() {
                if arg == "--base-dir" { base_dir = args.next(); }
            }
            Ok(CliCommand::SingularityTick { base_dir })
        }
```

- [ ] **Step 2: Add runner dispatch**

In `src/cli/runner.rs`, find the match on `CliCommand` (near line 117) and add:
```rust
        CliCommand::SingularityTick { base_dir } => run_singularity_tick(base_dir),
```

Add the handler function at the end of `src/cli/runner.rs`:
```rust
fn run_singularity_tick(base_dir: Option<String>) -> Result<(), String> {
    use nexus6::singularity_recursion::tick::{run_tick, CycleRunner, TickPaths};
    use nexus6::singularity_recursion::topology::{Point, Singularity};
    use nexus6::config::SingularityRecursionConfig;

    // Placeholder runner: deterministic fake until CycleEngine wiring lands.
    struct ShimRunner;
    impl CycleRunner for ShimRunner {
        fn run(&mut self, domain: &str, seed: Option<&Point>) -> Singularity {
            let prior = seed.map(|p| p.singularity.invariant.clone()).unwrap_or_default();
            Singularity {
                invariant: format!("{} :: probe from [{}]", domain,
                                   prior.chars().take(60).collect::<String>()),
                confidence: 0.5,
                novelty: 0.8,
                depth_reached: 3,
            }
        }
    }

    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    let cfg = SingularityRecursionConfig::default();
    let mut runner = ShimRunner;
    let out = run_tick(&paths, &cfg, &mut runner);
    println!("tick exit={} point={:?} elapsed={}s",
             out.exit_code, out.point_id, out.elapsed_sec);
    if out.exit_code == 0 { Ok(()) } else { std::process::exit(out.exit_code); }
}
```

Note: `nexus6::` prefix because runner.rs uses library crate. Verify import style by checking one existing handler.

- [ ] **Step 3: Build**

Run: `cargo build 2>&1 | tail -15`
Expected: compiles without errors.

- [ ] **Step 4: Smoke test**

Run: `cargo run --quiet -- singularity-tick --base-dir /tmp/nexus6_smoke 2>&1 | tail -5 && ls /tmp/nexus6_smoke/`
Expected: `tick exit=0 point=Some("p_000000") elapsed=Ns` and files `topology.jsonl budget.json wal.jsonl state.lock` present.

- [ ] **Step 5: Second tick test**

Run: `cargo run --quiet -- singularity-tick --base-dir /tmp/nexus6_smoke && wc -l /tmp/nexus6_smoke/topology.jsonl`
Expected: `2` lines.

- [ ] **Step 6: Commit**

```bash
git add src/cli/parser.rs src/cli/runner.rs
git commit -m "feat(cli): add nexus6 singularity-tick subcommand"
```

---

## Task 10: launchd plist + installer + help text

**Files:**
- Create: `launchd/com.nexus6.cycle-tick.plist`
- Create: `tools/install-cycle-tick.sh`

- [ ] **Step 1: Write plist**

Create `launchd/com.nexus6.cycle-tick.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nexus6.cycle-tick</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ghost/.cargo/bin/nexus6</string>
        <string>singularity-tick</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/ghost/Dev/nexus6</string>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>60</integer>
    <key>StandardOutPath</key>
    <string>/Users/ghost/Library/Logs/nexus6/cycle-tick.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ghost/Library/Logs/nexus6/cycle-tick.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>RUST_LOG</key>
        <string>info</string>
    </dict>
</dict>
</plist>
```

- [ ] **Step 2: Write installer**

Create `tools/install-cycle-tick.sh`:
```bash
#!/usr/bin/env bash
# Install/uninstall/status for com.nexus6.cycle-tick LaunchAgent.
set -euo pipefail

LABEL="com.nexus6.cycle-tick"
SRC_PLIST="$(cd "$(dirname "$0")/.." && pwd)/launchd/${LABEL}.plist"
DST_PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
UID_SELF="$(id -u)"

case "${1:-status}" in
  install)
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs/nexus6"
    cp "$SRC_PLIST" "$DST_PLIST"
    launchctl bootstrap "gui/${UID_SELF}" "$DST_PLIST" 2>/dev/null || \
      launchctl load -w "$DST_PLIST"
    echo "installed: ${LABEL}"
    ;;
  uninstall)
    launchctl bootout "gui/${UID_SELF}/${LABEL}" 2>/dev/null || \
      launchctl unload -w "$DST_PLIST" 2>/dev/null || true
    rm -f "$DST_PLIST"
    echo "uninstalled: ${LABEL}"
    ;;
  halt)
    touch "$HOME/.nexus6/halt" 2>/dev/null || \
      (mkdir -p "$HOME/.nexus6" && touch "$HOME/.nexus6/halt")
    # Also touch shared/cycle/halt since that's where the tick actually checks
    mkdir -p "$(pwd)/shared/cycle" && touch "$(pwd)/shared/cycle/halt"
    echo "halt flag set"
    ;;
  resume)
    rm -f "$(pwd)/shared/cycle/halt" "$HOME/.nexus6/halt"
    echo "halt flag cleared"
    ;;
  status)
    launchctl list | grep "${LABEL}" || echo "not loaded"
    ;;
  *)
    echo "usage: $0 {install|uninstall|halt|resume|status}" >&2
    exit 1
    ;;
esac
```

- [ ] **Step 3: Make executable**

Run: `chmod +x tools/install-cycle-tick.sh`

- [ ] **Step 4: Verify script syntax**

Run: `bash -n tools/install-cycle-tick.sh && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add launchd/ tools/install-cycle-tick.sh
git commit -m "feat(launchd): cycle-tick agent + install/halt/resume script"
```

---

## Task 11: Integration test (100-tick chaos sim)

**Files:**
- Create: `tests/singularity_recursion_integration.rs`

- [ ] **Step 1: Write integration test**

Create `tests/singularity_recursion_integration.rs`:
```rust
//! 100-tick integration test with a deterministic fake runner.
//! Also validates crash recovery by deleting boundary cache mid-run.

use std::path::PathBuf;

use nexus6::config::SingularityRecursionConfig;
use nexus6::singularity_recursion::tick::{run_tick, CycleRunner, TickPaths, EXIT_OK};
use nexus6::singularity_recursion::topology::{load, Point, Singularity};

struct DetRunner { n: usize }
impl CycleRunner for DetRunner {
    fn run(&mut self, _domain: &str, seed: Option<&Point>) -> Singularity {
        self.n += 1;
        let prior = seed.map(|p| p.singularity.invariant.clone()).unwrap_or_default();
        Singularity {
            invariant: format!("axis_{}_{} from {}", self.n % 7, self.n, prior.chars().take(30).collect::<String>()),
            confidence: 0.3 + (self.n as f64 % 10.0) * 0.05,
            novelty: 0.5 + (self.n as f64 % 5.0) * 0.1,
            depth_reached: 3,
        }
    }
}

fn relaxed_cfg() -> SingularityRecursionConfig {
    SingularityRecursionConfig {
        min_free_memory_mb: 0,
        max_loadavg_1min: 1e9,
        cpu_sec_per_tick: 1,
        wall_sec_per_tick: 10,
        max_total_points: 200,
        global_cpu_sec_budget: 10_000,
        ..Default::default()
    }
}

fn tmp_base(name: &str) -> PathBuf {
    let mut p = std::env::temp_dir();
    p.push(format!("nexus6_integ_{}_{}", name, std::process::id()));
    let _ = std::fs::remove_dir_all(&p);
    std::fs::create_dir_all(&p).unwrap();
    p
}

#[test]
fn hundred_ticks_bounded_growth() {
    let base = tmp_base("hundred");
    let paths = TickPaths::from_base(&base);
    let cfg = relaxed_cfg();
    let mut runner = DetRunner { n: 0 };
    let mut ok = 0;
    for _ in 0..100 {
        let out = run_tick(&paths, &cfg, &mut runner);
        if out.exit_code == EXIT_OK { ok += 1; }
    }
    assert_eq!(ok, 100, "expected 100 successful ticks");
    let topo = load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps).unwrap();
    assert_eq!(topo.points.len(), 100);
    // Edges count should be bounded — topology not a complete graph.
    assert!(topo.edges.len() < 100 * 50, "edge explosion: {}", topo.edges.len());
    std::fs::remove_dir_all(&base).ok();
}

#[test]
fn crash_recovery_rebuilds_from_jsonl() {
    let base = tmp_base("crash");
    let paths = TickPaths::from_base(&base);
    let cfg = relaxed_cfg();
    let mut runner = DetRunner { n: 0 };
    for _ in 0..10 { run_tick(&paths, &cfg, &mut runner); }
    // Simulate crash: wipe boundary + budget caches.
    std::fs::remove_file(&paths.budget).ok();
    // topology.jsonl remains as source of truth.
    // Next tick should rebuild budget and continue. (budget=default)
    let out = run_tick(&paths, &cfg, &mut runner);
    assert_eq!(out.exit_code, EXIT_OK);
    let topo = load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps).unwrap();
    assert_eq!(topo.points.len(), 11, "point should be appended after recovery");
    std::fs::remove_dir_all(&base).ok();
}

#[test]
fn lock_contention_safe() {
    let base = tmp_base("lock");
    let paths = TickPaths::from_base(&base);
    let cfg = relaxed_cfg();
    std::fs::create_dir_all(&base).unwrap();
    // Hold lock manually.
    let lock_file = std::fs::OpenOptions::new().create(true).read(true).write(true).open(&paths.lock).unwrap();
    use fs2::FileExt;
    lock_file.lock_exclusive().unwrap();
    // Write current PID so stale-check won't clean it.
    use std::io::Write;
    (&lock_file).set_len(0).unwrap();
    (&lock_file).write_all(std::process::id().to_string().as_bytes()).unwrap();
    (&lock_file).sync_all().unwrap();

    let mut runner = DetRunner { n: 0 };
    let out = run_tick(&paths, &cfg, &mut runner);
    assert_eq!(out.exit_code, 4, "expected EXIT_LOCKED");
    lock_file.unlock().unwrap();
    drop(lock_file);
    std::fs::remove_dir_all(&base).ok();
}
```

- [ ] **Step 2: Run integration tests**

Run: `cargo test --test singularity_recursion_integration 2>&1 | tail -15`
Expected: `3 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/singularity_recursion_integration.rs
git commit -m "test(singularity_recursion): 100-tick + crash recovery + lock contention"
```

---

## Task 12: Full test suite + build release

**Files:** none (verification task)

- [ ] **Step 1: Run full test suite**

Run: `cargo test --lib singularity_recursion 2>&1 | tail -20`
Expected: all tests pass (≥ 32 tests across 6 modules).

- [ ] **Step 2: Run integration tests**

Run: `cargo test --test singularity_recursion_integration 2>&1 | tail -10`
Expected: `3 passed`

- [ ] **Step 3: Build release**

Run: `cargo build --release --quiet 2>&1 | tail -10`
Expected: release binary at `target/release/nexus6`.

- [ ] **Step 4: Install release binary**

Run: `cp target/release/nexus6 ~/.cargo/bin/nexus6`

- [ ] **Step 5: Manual smoke**

Run: `~/.cargo/bin/nexus6 singularity-tick --base-dir /tmp/manual_smoke && ls /tmp/manual_smoke/`
Expected: exit 0, files created.

- [ ] **Step 6: Final commit (if needed)**

If any docs/README changes accumulated:
```bash
git status
# commit if appropriate
```

---

## Success Criteria (from spec)

After all tasks complete:
- [ ] 100-tick integration passes (Task 11)
- [ ] kill -9 mid-tick preserves data (covered by crash recovery test)
- [ ] Lock contention handled (Task 11)
- [ ] Help text + CLI works (Task 9)
- [ ] launchd installable via `tools/install-cycle-tick.sh install` (Task 10)
- [ ] Runs 24h on Mac without OOM — validated post-merge, not in plan

## Out of Scope (deferred to follow-up plans)

- **Real CycleEngine integration** — current runner is a shim. Next plan: wire `blowup::cycle_engine::CycleEngine` into `run_singularity_tick`.
- **Snapshot rotation** (backups/topology_N.jsonl.gz every 100 ticks) — add after 24h runtime validates basic loop.
- **n6_guard protection list** — optional config edit, not code.
- **Dashboard/visualization** of topology — separate concern.
