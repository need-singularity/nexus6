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
    // Simulate crash: wipe budget cache. topology.jsonl remains as source of truth.
    std::fs::remove_file(&paths.budget).ok();
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
