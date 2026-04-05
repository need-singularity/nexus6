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

/// Seed generator interface — lets tests inject fake runners.
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
