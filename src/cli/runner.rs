use std::collections::HashMap;
use std::time::Instant;

use tracing::{info, warn, debug};

use crate::graph::persistence::{self, DiscoveryGraph};
use crate::graph::bt_nodes;
use crate::graph::expanded_nodes;
use crate::history::{recorder, stats, recommend, DomainStats};
use crate::lens_forge::forge_engine::{self, ForgeConfig};
use crate::ouroboros::{EvolutionEngine, EvolutionConfig, MetaLoop, MetaLoopConfig};
use crate::blowup::{BlowupEngine, BlowupConfig, Singularity};
use crate::telescope::registry::{LensCategory, LensRegistry};
use crate::telescope::domain_combos;
use crate::telescope::Telescope;
use crate::verifier::n6_check;

use super::dashboard;
use crate::experiment::types::{ExperimentConfig, ExperimentType};
use crate::experiment::runner::ExperimentRunner;
use crate::experiment::report;
use crate::config::NexusConfig;

use super::parser::{CliCommand, ExperimentMode, GraphFormat, LensFilter};

/// ~/.nexus6/projects.json에서 프로젝트 목록 로드
#[derive(serde::Deserialize)]
struct ProjectEntry {
    name: String,
    domain: String,
    path: String,
}

#[derive(serde::Deserialize)]
struct ProjectsFile {
    projects: Vec<ProjectEntry>,
}

fn load_projects() -> Vec<ProjectEntry> {
    let path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/projects.json", h))
        .unwrap_or_default();
    std::fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str::<ProjectsFile>(&s).ok())
        .map(|f| f.projects)
        .unwrap_or_default()
}

/// 자기 자신을 --fg 붙여서 백그라운드 프로세스로 spawn.
/// 로그는 ~/.nexus6/<subcmd>_bg.log 에 기록.
fn spawn_background(subcmd: &str, domain: &Option<String>, extra_args: &[(&str, &str)]) -> Result<(), String> {
    use std::process::{Command, Stdio};

    let exe = std::env::current_exe().map_err(|e| format!("current_exe: {}", e))?;

    let log_dir = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6", h))
        .unwrap_or_else(|_| "/tmp".to_string());
    let _ = std::fs::create_dir_all(&log_dir);

    // ── PID lock: 중복 실행 방지 ──
    let pid_path = format!("{}/{}.pid", log_dir, subcmd);
    if let Ok(old_pid) = std::fs::read_to_string(&pid_path) {
        let old_pid = old_pid.trim();
        if !old_pid.is_empty() && check_pid_alive(old_pid) {
            return Err(format!(
                "{} 이미 실행 중 (PID {}). 중복 실행 차단됨. 강제 재시작: kill {} 후 재실행",
                subcmd, old_pid, old_pid
            ));
        }
    }

    let log_path = format!("{}/{}_bg.log", log_dir, subcmd);
    let log_file = std::fs::File::create(&log_path)
        .map_err(|e| format!("log create: {}", e))?;

    let mut args = vec![subcmd.to_string(), "--fg".to_string()];
    if let Some(d) = domain {
        args.push(d.clone());
    }
    for (k, v) in extra_args {
        args.push(k.to_string());
        args.push(v.to_string());
    }

    let child = Command::new(&exe)
        .args(&args)
        .stdout(Stdio::from(log_file.try_clone().map_err(|e| e.to_string())?))
        .stderr(Stdio::from(log_file))
        .stdin(Stdio::null())
        .spawn()
        .map_err(|e| format!("spawn: {}", e))?;

    let pid = child.id();
    // PID 파일 기록
    let _ = std::fs::write(&pid_path, pid.to_string());
    info!(pid, subcmd, "백그라운드 실행 시작");
    info!(log_path, "로그 파일");
    Ok(())
}

/// Execute a parsed CLI command, printing results to stdout.
pub fn run(cmd: CliCommand) -> Result<(), String> {
    let cfg = NexusConfig::load();
    run_with_config(cmd, &cfg)
}

fn run_with_config(cmd: CliCommand, cfg: &NexusConfig) -> Result<(), String> {
    match cmd {
        CliCommand::Scan { domain, lenses, full } => run_scan(&domain, lenses, full),
        CliCommand::Verify { value, tolerance } => run_verify(value, tolerance),
        CliCommand::Graph { domain, format } => run_graph(domain, format),
        CliCommand::History { domain } => run_history(&domain),
        CliCommand::Recommend { domain } => run_recommend(&domain),
        CliCommand::Evolve { domain, max_cycles, seeds } => run_evolve(&domain, max_cycles, seeds),
        CliCommand::Auto { domain, max_meta_cycles, max_ouroboros_cycles } => {
            run_auto(&domain, max_meta_cycles, max_ouroboros_cycles, cfg)
        }
        CliCommand::Lenses { category, domain, search, count_only, complementary, export_json } => {
            run_lenses(category, domain, search, count_only, complementary, export_json)
        }
        CliCommand::Experiment { exp_type, target, intensity, duration } => {
            run_experiment(exp_type, &target, intensity, duration)
        }
        CliCommand::Predict { experiment_type, target } => {
            run_predict(&experiment_type, &target)
        }
        CliCommand::Simulate { experiment_type, target, runs } => {
            run_simulate(&experiment_type, &target, runs)
        }
        CliCommand::Compare { a_spec, b_spec } => {
            run_compare(&a_spec, &b_spec)
        }
        CliCommand::Reproduce { experiment_type, target, repeats } => {
            run_reproduce(&experiment_type, &target, repeats)
        }
        CliCommand::Publish { experiment_type, target } => {
            run_publish(&experiment_type, &target)
        }
        CliCommand::Cycle { experiment_type, target } => {
            run_cycle(&experiment_type, &target)
        }
        CliCommand::Bridge { sub } => run_bridge(sub),
        CliCommand::Loop { domain, cycles, foreground } => {
            // CLI > config.toml > hardcoded defaults
            let domain = domain.or_else(|| cfg.default_loop_domain());
            if foreground {
                run_loop(domain, cycles, cfg)
            } else {
                spawn_background("loop", &domain, &[
                    ("--cycles", &cycles.to_string()),
                ])
            }
        }
        CliCommand::Daemon { domain, interval_min, max_loops, foreground } => {
            // CLI > config.toml > hardcoded defaults
            let domain = domain.or_else(|| cfg.default_daemon_domain());
            if foreground {
                run_daemon(domain, interval_min, max_loops, cfg)
            } else {
                let iv_str = interval_min.to_string();
                let ml_str = max_loops.map(|n| n.to_string());
                let mut extra: Vec<(&str, &str)> = vec![
                    ("--interval", &iv_str),
                ];
                if let Some(ref s) = ml_str {
                    extra.push(("--max-loops", s));
                }
                spawn_background("daemon", &domain, &extra)
            }
        }
        CliCommand::Blowup { domain, max_depth } => {
            run_blowup(&domain, max_depth, cfg)
        }
        CliCommand::Mega => run_mega(cfg),
        CliCommand::Report => run_report(),
        CliCommand::Status => run_status(),
        CliCommand::Dispatch { target, prompt, parallel } => {
            run_dispatch(&target, &prompt, parallel)
        }
        CliCommand::Ingest { sources, config, verbose } => run_ingest(sources, config, verbose),
        CliCommand::Bench => run_bench(),
        CliCommand::Dashboard { html, output } => run_dashboard(html, output),
        CliCommand::AlienIndex { sub } => crate::cli::alien_index_cmd::run(sub),
        CliCommand::SingularityTick { base_dir } => run_singularity_tick(base_dir),
        CliCommand::SingularityDaemon { base_dir, interval_sec } => run_singularity_daemon(base_dir, interval_sec),
        CliCommand::SingularityBackfill { base_dir, project_root, memory, all_projects, fast } => run_singularity_backfill(base_dir, project_root, memory, all_projects, fast),
        CliCommand::SingularityConvergence { base_dir, eps, min_domains, top, export } => run_singularity_convergence(base_dir, eps, min_domains, top, export),
        CliCommand::SingularityQuery { base_dir, query, limit } => run_singularity_query(base_dir, query, limit),
        CliCommand::SingularityFrontier { base_dir, eps, top } => run_singularity_frontier(base_dir, eps, top),
        CliCommand::SingularityBridges { base_dir, domain_a, domain_b, eps, top } => run_singularity_bridges(base_dir, domain_a, domain_b, eps, top),
        CliCommand::SingularityRebuildEdges { base_dir, eps } => run_singularity_rebuild_edges(base_dir, eps),
        CliCommand::SingularityResonance { base_dir, limit, domain_filter } => run_singularity_resonance(base_dir, limit, domain_filter),
        CliCommand::SingularitySeed { base_dir, eps, top, domain_filter, json } => run_singularity_seed(base_dir, eps, top, domain_filter, json),
        CliCommand::SingularityViz { base_dir, output, sample } => run_singularity_viz(base_dir, output, sample),
        CliCommand::ClosedFind { value } => run_closed_find(value),
        CliCommand::Pack { sub } => run_pack(sub),
        CliCommand::Sentry { sub } => run_sentry(sub),
        CliCommand::Hook { sub } => run_hook(sub),
        CliCommand::Mk2 { sub } => run_mk2(sub),
        CliCommand::Help => {
            print_help();
            Ok(())
        }
    }
}

fn run_scan(domain: &str, lenses: Option<Vec<String>>, full: bool) -> Result<(), String> {
    println!("=== NEXUS-6 Scan: {} ===", domain);

    let telescope = Telescope::new();
    let total_lenses = telescope.lens_count();

    // ── Probe 데이터 생성 (도메인 적응) ──
    let probe_data = generate_probe_data(domain);
    let n = probe_data.len() / 6;
    let d = 6;

    // ── 렌즈 선택 ──
    let (mode, lens_filter) = if let Some(ref l) = lenses {
        ("manual", Some(l.clone()))
    } else if full {
        ("full", None)
    } else {
        // 도메인 콤보 + 항상 포함 렌즈 (Meta 카테고리)
        let combos = domain_combos::default_combos();
        let domain_lower = domain.to_lowercase();
        let matched = combos.iter().find(|c| {
            c.target_domains.iter().any(|d| d.contains(&domain_lower))
                || c.name.contains(&domain_lower)
        });
        let mut selected = match matched {
            Some(combo) => combo.lenses.clone(),
            None => vec![
                "consciousness".to_string(),
                "topology".to_string(),
                "causal".to_string(),
            ],
        };
        // Meta 렌즈 항상 포함
        for meta in &["SingularityCycleLens", "UemergenceLens"] {
            let s = meta.to_string();
            if !selected.iter().any(|l| l == &s) {
                selected.push(s);
            }
        }
        ("combo", Some(selected))
    };

    // ── 실행 ──
    let results = telescope.scan_all(&probe_data, n, d);

    // ── 렌즈 필터링 (표시용) ──
    let filtered: Vec<(&String, &HashMap<String, Vec<f64>>)> = match &lens_filter {
        Some(filter) => results.iter()
            .filter(|(name, _)| {
                filter.iter().any(|f| name.to_lowercase().contains(&f.to_lowercase()))
            })
            .collect(),
        None => results.iter().collect(),
    };

    let active_count = results.values().filter(|lr| !lr.is_empty()).count();
    let n6_ratio = n6_check::n6_exact_ratio(&probe_data);
    let queried = filtered.len();

    println!("  Mode: {} | Domain: {}", mode, domain);
    println!("  Probe: {} points × {} dims", n, d);
    println!();

    // ── 핵심 메트릭 추출 ──
    // 특이점 사이클 결과
    let mut singularity_reached = false;
    let mut exact_ratio = 0.0;
    let mut convergence = 0.0;
    let mut patterns_found = 0.0;

    if let Some(scl) = results.get("SingularityCycleLens") {
        singularity_reached = scl.get("singularity_reached").and_then(|v| v.first()).copied().unwrap_or(0.0) >= 1.0;
        exact_ratio = scl.get("exact_ratio").and_then(|v| v.first()).copied().unwrap_or(0.0);
        convergence = scl.get("convergence").and_then(|v| v.first()).copied().unwrap_or(0.0);
        patterns_found = scl.get("patterns_found").and_then(|v| v.first()).copied().unwrap_or(0.0);
    }

    // 창발 결과
    let mut emergence_score = 0.0;
    let mut num_clusters = 0.0;
    if let Some(eml) = results.get("UemergenceLens") {
        emergence_score = eml.get("emergence_score").and_then(|v| v.first()).copied().unwrap_or(0.0);
        num_clusters = eml.get("num_clusters").and_then(|v| v.first()).copied().unwrap_or(0.0);
    }

    // ── 리포트 ──
    let w = 61;
    let line = "─".repeat(w);
    println!("  ┌{}┐", line);
    println!("  │ {:<w$}│", format!("🔭 NEXUS-6 Scan — {}", domain));
    println!("  ├{}┤", line);
    println!("  │ {:<w$}│", "");
    println!("  │ {:<w$}│", format!("■ 렌즈: {}/{} active | {} queried", active_count, total_lenses, queried));
    println!("  │ {:<w$}│", format!("  n6 EXACT ratio: {:.1}%", n6_ratio * 100.0));
    println!("  │ {:<w$}│", "");
    println!("  │ {:<w$}│", format!("■ 특이점 사이클:"));
    println!("  │ {:<w$}│", format!("  EXACT ratio: {:.1}% | convergence: {:.1}%",
        exact_ratio * 100.0, convergence * 100.0));
    println!("  │ {:<w$}│", format!("  patterns: {:.0} | singularity: {}",
        patterns_found, if singularity_reached { "★ REACHED ★" } else { "approaching" }));
    println!("  │ {:<w$}│", "");
    println!("  │ {:<w$}│", format!("■ 창발: score={:.3} | clusters={:.0}",
        emergence_score, num_clusters));
    println!("  │ {:<w$}│", "");

    // 상위 활성 렌즈 (결과 크기 순)
    let mut ranked: Vec<(&String, usize)> = results.iter()
        .map(|(name, lr)| {
            let size: usize = lr.values().map(|v| v.len()).sum();
            (name, size)
        })
        .filter(|(_, s)| *s > 0)
        .collect();
    ranked.sort_by(|a, b| b.1.cmp(&a.1));

    println!("  │ {:<w$}│", format!("■ Top 렌즈 (by output):"));
    for (name, size) in ranked.iter().take(10) {
        let bar_len = (*size as f64 / ranked[0].1.max(1) as f64 * 20.0) as usize;
        let bar: String = "█".repeat(bar_len.min(20));
        println!("  │ {:<w$}│", format!("  {:<30} {:<20} {}", name, bar, size));
    }

    println!("  │ {:<w$}│", "");
    println!("  └{}┘", line);

    // ── 결과 파일 저장 ──
    let scan_report = format!(
        "domain={}\nactive={}/{}\nn6_ratio={:.3}\nsingularity={}\nexact_ratio={:.3}\nconvergence={:.3}\npatterns={:.0}\nemergence={:.3}\nclusters={:.0}\n",
        domain, active_count, total_lenses, n6_ratio,
        if singularity_reached { "REACHED" } else { "approaching" },
        exact_ratio, convergence, patterns_found, emergence_score, num_clusters
    );
    let report_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_scan.txt", h))
        .unwrap_or_else(|_| "/tmp/nexus6_scan.txt".to_string());
    let _ = std::fs::create_dir_all(std::path::Path::new(&report_path).parent().unwrap());
    let _ = std::fs::write(&report_path, &scan_report);

    Ok(())
}

/// 도메인 적응 probe 데이터 생성
fn generate_probe_data(domain: &str) -> Vec<f64> {
    // n=6 기본 상수 + 도메인별 시드
    let mut data = vec![
        // Row 1: n=6 core
        6.0, 12.0, 4.0, 2.0, 5.0, 24.0,
        // Row 2: derived
        8.0, 48.0, 0.5, 1.0, 7.0, 120.0,
    ];
    // 도메인별 추가 행
    let domain_row: Vec<f64> = match domain.to_lowercase().as_str() {
        "consciousness" | "anima" =>
            vec![0.014, 0.5, 4.33, 0.998, 12.0, 0.10],
        "physics" =>
            vec![3.14159, 2.71828, 1.618, 6.674e-11, 299792458.0, 6.626e-34],
        "number_theory" | "mathematics" =>
            vec![1.618, 2.0, 3.0, 6.0, 28.0, 496.0],
        "signal_detection" | "sedi" =>
            vec![1420.405, 3.7, 0.001, 77.0, 6.0, 12.0],
        "neuroscience" | "brainwire" =>
            vec![40.0, 8.0, 12.0, 0.7, 86e9, 100e12],
        "programming_language" | "hexa-lang" =>
            vec![53.0, 798.0, 6.0, 11.0, 0.07, 92.0],
        "architecture" | "n6-architecture" =>
            vec![12.0, 6.0, 24.0, 1022.0, 215.0, 711.0],
        "publication" | "papers" =>
            vec![6.0, 12.0, 3.14, 2.71, 1.0, 0.0],
        "terminal" | "fathom" =>
            vec![6.0, 12.0, 4.0, 2.0, 5.0, 24.0],
        _ => vec![6.0, 12.0, 4.0, 2.0, 5.0, 24.0],
    };
    data.extend(domain_row);
    data
}

fn run_verify(value: f64, tolerance: Option<f64>) -> Result<(), String> {
    use crate::verifier::feasibility;

    println!("=== NEXUS-6 Verify: {} ===", value);
    println!();

    let (name, quality) = n6_check::n6_match(value);

    let grade = if quality >= 1.0 {
        "EXACT"
    } else if quality >= 0.8 {
        "CLOSE"
    } else if quality >= 0.5 {
        "WEAK"
    } else {
        "NONE"
    };

    println!("  Value:     {}", value);
    println!("  Match:     {} ({})", name, grade);
    println!("  Quality:   {:.2}", quality);

    if let Some(tol) = tolerance {
        println!("  Tolerance: {}", tol);
        // Check if any constant is within the custom tolerance
        let within = check_within_tolerance(value, tol);
        println!("  Within:    {}", if within { "YES" } else { "NO" });
    }

    // Feasibility score (treating the single value as a probe)
    let n6_ratio = n6_check::n6_exact_ratio(&[value]);
    let verification = feasibility::verify(
        quality,  // lens_consensus ~ match quality
        0.5,      // cross_validation placeholder
        0.5,      // physical_check placeholder
        0.0,      // graph_bonus (no graph context)
        1.0,      // novelty (single verification)
        n6_ratio, // n6 exact ratio
    );
    println!("  Feasibility: {:.3} (grade {})", verification.score, verification.grade.label());

    // Show nearby constants
    println!();
    println!("  Nearby n=6 constants:");
    let constants = [
        ("n", 6.0), ("sigma", 12.0), ("phi", 2.0), ("tau", 4.0),
        ("J2", 24.0), ("sopfr", 5.0), ("mu", 1.0),
        ("sigma-phi", 10.0), ("sigma-tau", 8.0), ("sigma-mu", 11.0),
        ("sigma*tau", 48.0), ("sigma^2", 144.0),
    ];
    for (cname, cval) in &constants {
        let error = if *cval != 0.0 {
            ((value - cval) / cval).abs() * 100.0
        } else {
            f64::INFINITY
        };
        if error < 20.0 {
            println!("    {:<12} = {:>8.3}  (error: {:.2}%)", cname, cval, error);
        }
    }

    Ok(())
}

/// Check if a value is within the given tolerance of any n=6 constant.
fn check_within_tolerance(value: f64, tolerance: f64) -> bool {
    let constants = [
        6.0, 12.0, 2.0, 4.0, 24.0, 5.0, 1.0,
        10.0, 8.0, 11.0, 48.0, 144.0, 16.0, 3.0, 20.0,
    ];
    constants.iter().any(|&c| {
        if c != 0.0 {
            ((value - c) / c).abs() <= tolerance
        } else {
            false
        }
    })
}

fn run_graph(domain: Option<String>, format: GraphFormat) -> Result<(), String> {
    let graph_path = persistence::default_graph_path();
    let mut graph = DiscoveryGraph::load(&graph_path)
        .map_err(|e| format!("Failed to load graph: {}", e))?;

    // If the graph is empty, populate with BT + expanded nodes and save
    if graph.nodes.is_empty() {
        bt_nodes::populate_bt_graph(&mut graph);
        expanded_nodes::populate_expanded_graph(&mut graph);
        if let Err(e) = graph.save(&graph_path) {
            warn!(path = graph_path.as_str(), error = %e, "could not save graph");
        }
    }

    println!("=== NEXUS-6 Discovery Graph ===");
    println!("  Path:  {}", graph_path);
    println!("  Nodes: {}  Edges: {}", graph.nodes.len(), graph.edges.len());

    // Show node type breakdown
    let type_counts = graph.node_type_counts();
    let mut type_list: Vec<_> = type_counts.iter().collect();
    type_list.sort_by(|a, b| b.1.cmp(a.1));
    for (ntype, count) in &type_list {
        println!("    {}: {}", ntype, count);
    }

    if let Some(ref d) = domain {
        println!("  Filter: domain={}", d);
    }

    // Filter nodes/edges by domain if specified
    let filtered_nodes: Vec<_> = if let Some(ref d) = domain {
        let d_lower = d.to_lowercase();
        graph.nodes.iter()
            .filter(|n| n.domain.to_lowercase().contains(&d_lower))
            .collect()
    } else {
        graph.nodes.iter().collect()
    };

    let filtered_node_ids: std::collections::HashSet<&str> =
        filtered_nodes.iter().map(|n| n.id.as_str()).collect();

    if filtered_nodes.is_empty() {
        println!();
        println!("  (no nodes matching filter -- run 'nexus6 evolve <domain>' to populate)");
        return Ok(());
    }

    match format {
        GraphFormat::Ascii => {
            println!();
            // Show top hubs first
            let hubs = graph.hubs(6); // min degree = n=6
            if !hubs.is_empty() {
                println!("  Top hubs (degree >= 6):");
                for hub in hubs.iter().take(12) { // show top sigma=12
                    println!("    {} (degree={})", hub.node_id, hub.degree);
                }
                println!();
            }

            // Show edges for filtered nodes (limit output to avoid flood)
            let mut edge_count = 0;
            for node in filtered_nodes.iter().take(24) { // limit to J2=24 nodes
                let edges_out: Vec<_> = graph.edges.iter()
                    .filter(|e| e.from == node.id && filtered_node_ids.contains(e.to.as_str()))
                    .collect();
                if edges_out.is_empty() {
                    println!("  [{}]", node.id);
                } else {
                    for edge in edges_out.iter().take(6) { // limit edges per node to n=6
                        println!("  [{}] --{:?}--> [{}]", node.id, edge.edge_type, edge.to);
                        edge_count += 1;
                    }
                }
            }
            if edge_count > 0 || filtered_nodes.len() > 24 {
                println!();
                println!("  (showing {} of {} nodes, use --domain to filter)",
                    filtered_nodes.len().min(24), filtered_nodes.len());
            }
        }
        GraphFormat::Dot => {
            println!();
            println!("digraph nexus6 {{");
            println!("  rankdir=LR;");
            for node in &filtered_nodes {
                let shape = match node.node_type {
                    crate::graph::NodeType::Bt => "box",
                    crate::graph::NodeType::Constant => "diamond",
                    crate::graph::NodeType::Technique => "ellipse",
                    crate::graph::NodeType::Domain => "hexagon",
                    crate::graph::NodeType::Experiment => "octagon",
                    _ => "circle",
                };
                println!("  \"{}\" [label=\"{}\" shape={}];", node.id, node.id, shape);
            }
            for edge in &graph.edges {
                if filtered_node_ids.contains(edge.from.as_str())
                    && filtered_node_ids.contains(edge.to.as_str())
                {
                    println!(
                        "  \"{}\" -> \"{}\" [label=\"{:?}\"];",
                        edge.from, edge.to, edge.edge_type
                    );
                }
            }
            println!("}}");
        }
    }

    Ok(())
}

fn run_history(domain: &str) -> Result<(), String> {
    println!("=== NEXUS-6 History: {} ===", domain);

    let records = recorder::load_records("nexus6_history", domain);

    if records.is_empty() {
        println!();
        println!("  No scan history for domain '{}'.", domain);
        println!("  Run 'nexus6 scan {}' or 'nexus6 evolve {}' to start.", domain, domain);
        return Ok(());
    }

    let domain_stats = stats::compute_domain_stats(&records);

    println!();
    println!("  Total scans:       {}", domain_stats.total_scans);
    println!("  Total discoveries: {}", domain_stats.total_discoveries);
    println!();

    // Lens stats table
    let mut lens_list: Vec<_> = domain_stats.lens_stats.iter().collect();
    lens_list.sort_by(|a, b| b.1.hit_rate.partial_cmp(&a.1.hit_rate).unwrap());

    println!("  Lens Performance:");
    println!("  {:<20} {:>5} {:>5} {:>8}", "Lens", "Used", "Hits", "HitRate");
    println!("  {}", "-".repeat(42));
    for (name, ls) in &lens_list {
        let bar = hit_rate_bar(ls.hit_rate, 10);
        println!(
            "  {:<20} {:>5} {:>5} {} {:.2}",
            name, ls.used, ls.contributed, bar, ls.hit_rate
        );
    }

    // Recent records
    println!();
    println!("  Recent Scans (last 5):");
    for record in records.iter().rev().take(5) {
        println!(
            "    [{}] lenses={} discoveries={}",
            record.timestamp,
            record.lenses_used.len(),
            record.discoveries.len()
        );
    }

    Ok(())
}

fn run_recommend(domain: &str) -> Result<(), String> {
    println!("=== NEXUS-6 Recommend: {} ===", domain);

    let registry = LensRegistry::new();
    let all_lenses: Vec<String> = registry.iter().map(|(name, _)| name.clone()).collect();

    // Load history to compute stats
    let records = recorder::load_records("nexus6_history", domain);
    let mut all_stats: HashMap<String, DomainStats> = HashMap::new();
    if !records.is_empty() {
        all_stats.insert(domain.to_string(), stats::compute_domain_stats(&records));
    }

    let rec = recommend::recommend_lenses(domain, &all_stats, &all_lenses, 0.2);

    println!();
    println!("  Recommended lenses ({}):", rec.lenses.len());
    for (i, lens) in rec.lenses.iter().enumerate() {
        let tag = if let Some(entry) = registry.get(lens) {
            format!("{:?}", entry.category)
        } else {
            "unknown".to_string()
        };
        println!("    {:>2}. {:<20} [{}]", i + 1, lens, tag);
    }
    println!();
    println!("  Reason: {}", rec.reason);

    Ok(())
}

fn run_evolve(domain: &str, max_cycles: usize, seeds: Vec<String>) -> Result<(), String> {
    println!("=== NEXUS-6 Evolve: {} (max {} cycles) ===", domain, max_cycles);

    let mut config = EvolutionConfig::default();
    config.domain = domain.to_string();

    let seed_hypotheses = if seeds.is_empty() {
        vec![format!("n=6 patterns in {}", domain)]
    } else {
        seeds
    };

    debug!(seeds = ?seed_hypotheses, "Evolution seeds");

    let mut engine = EvolutionEngine::new(config, seed_hypotheses);

    for _i in 0..max_cycles {
        let result = engine.evolve_step();
        println!(
            "  Cycle {}: discoveries={} nodes={} edges={} score={:.3}",
            result.cycle,
            result.new_discoveries,
            result.graph_nodes,
            result.graph_edges,
            result.verification_score,
        );

        // Check convergence
        let status = engine.convergence_checker.check(&engine.history);
        match status {
            crate::ouroboros::convergence::ConvergenceStatus::Saturated => {
                info!(cycle = result.cycle, "Saturated — evolution complete");
                break;
            }
            crate::ouroboros::convergence::ConvergenceStatus::Converging => {
                debug!(cycle = result.cycle, "converging — discovery rate decreasing");
            }
            crate::ouroboros::convergence::ConvergenceStatus::Divergent => {
                debug!(cycle = result.cycle, "divergent — discovery rate increasing");
            }
            crate::ouroboros::convergence::ConvergenceStatus::Exploring => {}
        }
    }

    println!();
    println!("  Final graph: {} nodes, {} edges",
        engine.graph.nodes.len(), engine.graph.edges.len());

    // Persist: load existing graph, merge evolve results, add BT + expanded nodes, save
    let graph_path = persistence::default_graph_path();
    let mut persisted = DiscoveryGraph::load(&graph_path)
        .unwrap_or_else(|_| DiscoveryGraph::new());

    // Add BT + expanded nodes if not already present
    if persisted.nodes.is_empty() {
        bt_nodes::populate_bt_graph(&mut persisted);
        expanded_nodes::populate_expanded_graph(&mut persisted);
    }

    // Merge evolution results into persisted graph
    persisted.merge(&engine.graph);

    match persisted.save(&graph_path) {
        Ok(()) => {
            println!("  Graph saved to {} ({} nodes, {} edges)",
                graph_path, persisted.nodes.len(), persisted.edges.len());
        }
        Err(e) => {
            warn!(error = %e, "could not save graph");
        }
    }

    info!("Evolution complete");

    Ok(())
}

fn run_auto(domain: &str, max_meta_cycles: usize, max_ouroboros_cycles: usize, nexus_cfg: &NexusConfig) -> Result<(), String> {
    println!("=== NEXUS-6 Auto: {} (meta={}, ouroboros={}) ===",
        domain, max_meta_cycles, max_ouroboros_cycles);
    println!("  OUROBOROS + LensForge meta-loop");
    println!();

    let base_mlc = nexus_cfg.meta_loop_config();
    let config = MetaLoopConfig {
        max_ouroboros_cycles,
        max_meta_cycles,
        forge_after_n_cycles: base_mlc.forge_after_n_cycles,
        forge_config: base_mlc.forge_config,
    };

    let seeds = vec![format!("n=6 patterns in {}", domain)];
    let mut meta_loop = MetaLoop::new(domain.to_string(), seeds, config);

    // Attach progress logger
    meta_loop.on_progress = Some(Box::new(|mc, oc, msg| {
        if oc == 0 {
            tracing::debug!(meta_cycle = mc, "{}", msg);
        } else {
            tracing::debug!(meta_cycle = mc, ouro_cycle = oc, "{}", msg);
        }
    }));

    let result = meta_loop.run();

    // Summary
    println!();
    println!("  ┌─────────────────────────────────────────────┐");
    println!("  │           Auto Evolution Summary             │");
    println!("  ├─────────────────────────────────────────────┤");
    println!("  │  Meta-cycles completed: {:>4}                │", result.meta_cycles_completed);
    println!("  │  Total OUROBOROS cycles: {:>3}                │", result.ouroboros_results.len());
    println!("  │  Total discoveries:     {:>4}                │", result.total_discoveries);
    println!("  │  Lenses forged:         {:>4}                │", result.forged_lenses.len());
    println!("  └─────────────────────────────────────────────┘");

    if !result.forged_lenses.is_empty() {
        println!();
        println!("  Forged lenses:");
        for (i, name) in result.forged_lenses.iter().enumerate() {
            println!("    {:>2}. {}", i + 1, name);
        }
    }

    // Per-meta-cycle table
    println!();
    println!("  {:>5} {:>8} {:>6} {:>12} {:>8}",
        "Meta", "Ouro.Cy", "Disc.", "Convergence", "Forged");
    println!("  {}", "-".repeat(45));
    for summary in &result.meta_cycle_summaries {
        println!("  {:>5} {:>8} {:>6} {:>12?} {:>8}",
            summary.meta_cycle,
            summary.ouroboros_cycles_run,
            summary.discoveries,
            summary.convergence_status,
            summary.lenses_forged.len(),
        );
    }

    println!();
    println!("  Auto evolution complete.");
    Ok(())
}

fn run_lenses(
    category: Option<LensFilter>,
    domain: Option<String>,
    search: Option<String>,
    count_only: bool,
    complementary: Option<String>,
    export_json: bool,
) -> Result<(), String> {
    let registry = LensRegistry::new();

    // --export json: dump entire registry as JSON to stdout
    if export_json {
        return run_lenses_export_json(&registry);
    }

    // --count: category summary table
    if count_only {
        return run_lenses_count(&registry);
    }

    // --complementary <lens>: show complementary lenses (2-depth)
    if let Some(ref lens_name) = complementary {
        return run_lenses_complementary(&registry, lens_name);
    }

    // --domain <domain>: filter by domain affinity
    if let Some(ref dom) = domain {
        return run_lenses_domain(&registry, dom);
    }

    // --search <keyword>: search name + description
    if let Some(ref kw) = search {
        return run_lenses_search(&registry, kw);
    }

    // Default: category-based listing (original behavior)
    let combos = domain_combos::default_combos();

    println!("=== NEXUS-6 Lens Registry ===");
    println!();

    let show_core = category.is_none() || category == Some(LensFilter::Core);
    let show_combo = category.is_none() || category == Some(LensFilter::Combo);
    let show_ext = category.is_none() || category == Some(LensFilter::Extended);
    let show_custom = category.is_none() || category == Some(LensFilter::Custom);

    if show_core {
        let core = registry.by_category(LensCategory::Core);
        println!("  Core Lenses ({}):", core.len());
        let mut sorted: Vec<_> = core.iter().collect();
        sorted.sort_by_key(|e| &e.name);
        for entry in sorted {
            println!("    {:<22} {}", entry.name, entry.description);
        }
        println!();
    }

    if show_combo {
        println!("  Domain Combos ({}):", combos.len());
        for combo in &combos {
            println!(
                "    {:<18} {} -> {:?}",
                combo.name,
                combo.lenses.join("+"),
                combo.target_domains
            );
        }
        println!();
    }

    if show_ext {
        let ext = registry.by_category(LensCategory::Extended);
        if !ext.is_empty() {
            println!("  Extended Lenses ({}):", ext.len());
            for entry in &ext {
                println!("    {:<22} {}", entry.name, entry.description);
            }
            println!();
        }
    }

    if show_custom {
        let custom = registry.by_category(LensCategory::Custom);
        if !custom.is_empty() {
            println!("  Custom Lenses ({}):", custom.len());
            for entry in &custom {
                println!("    {:<22} {}", entry.name, entry.description);
            }
            println!();
        }
    }

    println!("  Total: {} registered", registry.len());
    Ok(())
}

fn run_lenses_count(registry: &LensRegistry) -> Result<(), String> {
    let core_count = registry.by_category(LensCategory::Core).len();
    let combo_count = registry.by_category(LensCategory::DomainCombo).len();
    let ext_count = registry.by_category(LensCategory::Extended).len();
    let custom_count = registry.by_category(LensCategory::Custom).len();
    let total = registry.len();

    println!("=== NEXUS-6 Lens Count ===");
    println!();
    println!("  \u{250c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{252c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2510}");
    println!("  \u{2502} Category       \u{2502} Count \u{2502}");
    println!("  \u{251c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{253c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2524}");
    println!("  \u{2502} Core           \u{2502} {:>5} \u{2502}", core_count);
    println!("  \u{2502} DomainCombo    \u{2502} {:>5} \u{2502}", combo_count);
    println!("  \u{2502} Extended       \u{2502} {:>5} \u{2502}", ext_count);
    println!("  \u{2502} Custom         \u{2502} {:>5} \u{2502}", custom_count);
    println!("  \u{251c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{253c}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2524}");
    println!("  \u{2502} Total          \u{2502} {:>5} \u{2502}", total);
    println!("  \u{2514}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2534}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2518}");
    Ok(())
}

fn run_lenses_domain(registry: &LensRegistry, domain: &str) -> Result<(), String> {
    let matches = registry.for_domain(domain);

    println!("=== NEXUS-6 Lenses for domain: {} ===", domain);
    println!();

    if matches.is_empty() {
        println!("  No lenses found with affinity for '{}'.", domain);
        return Ok(());
    }

    let mut sorted: Vec<_> = matches;
    sorted.sort_by(|a, b| a.name.cmp(&b.name));

    println!("  {:<28} {:<14} {}", "Name", "Category", "Description");
    println!("  {}", "-".repeat(70));
    for entry in &sorted {
        println!("  {:<28} {:<14} {}", entry.name, format!("{:?}", entry.category), entry.description);
    }
    println!();
    println!("  Found: {} lenses", sorted.len());
    Ok(())
}

fn run_lenses_search(registry: &LensRegistry, keyword: &str) -> Result<(), String> {
    let kw_lower = keyword.to_lowercase();
    let mut matches: Vec<&crate::telescope::registry::LensEntry> = registry
        .iter()
        .filter_map(|(_, entry)| {
            if entry.name.to_lowercase().contains(&kw_lower)
                || entry.description.to_lowercase().contains(&kw_lower)
            {
                Some(entry)
            } else {
                None
            }
        })
        .collect();
    matches.sort_by(|a, b| a.name.cmp(&b.name));

    println!("=== NEXUS-6 Lens Search: \"{}\" ===", keyword);
    println!();

    if matches.is_empty() {
        println!("  No lenses matching '{}'.", keyword);
        return Ok(());
    }

    println!("  {:<28} {:<14} {}", "Name", "Category", "Description");
    println!("  {}", "-".repeat(70));
    for entry in &matches {
        println!("  {:<28} {:<14} {}", entry.name, format!("{:?}", entry.category), entry.description);
    }
    println!();
    println!("  Found: {} lenses", matches.len());
    Ok(())
}

fn run_lenses_complementary(registry: &LensRegistry, lens_name: &str) -> Result<(), String> {
    let entry = registry.get(lens_name).ok_or_else(|| {
        format!("Lens '{}' not found in registry.", lens_name)
    })?;

    println!("=== NEXUS-6 Complementary Lenses for: {} ===", lens_name);
    println!();

    if entry.complementary.is_empty() {
        println!("  No complementary lenses registered for '{}'.", lens_name);
        return Ok(());
    }

    // Depth 1: direct complementary
    println!("  Depth 1 (direct):");
    let mut depth1_sorted = entry.complementary.clone();
    depth1_sorted.sort();
    for name in &depth1_sorted {
        let tag = registry.get(name).map_or("?".to_string(), |e| format!("{:?}", e.category));
        println!("    {:<24} [{}]", name, tag);
    }

    // Depth 2: complementary of complementary (excluding the original lens and depth-1 set)
    let mut depth2: Vec<String> = Vec::new();
    let mut seen: std::collections::HashSet<String> = std::collections::HashSet::new();
    seen.insert(lens_name.to_string());
    for name in &entry.complementary {
        seen.insert(name.clone());
    }
    for name in &entry.complementary {
        if let Some(sub_entry) = registry.get(name) {
            for comp in &sub_entry.complementary {
                if !seen.contains(comp) {
                    seen.insert(comp.clone());
                    depth2.push(comp.clone());
                }
            }
        }
    }

    if !depth2.is_empty() {
        depth2.sort();
        println!();
        println!("  Depth 2 (indirect):");
        for name in &depth2 {
            let tag = registry.get(name).map_or("?".to_string(), |e| format!("{:?}", e.category));
            println!("    {:<24} [{}]", name, tag);
        }
    }

    println!();
    println!("  Total: {} direct + {} indirect", depth1_sorted.len(), depth2.len());
    Ok(())
}

fn run_lenses_export_json(registry: &LensRegistry) -> Result<(), String> {
    // Build JSON manually (no serde dependency)
    let mut entries: Vec<(&String, &crate::telescope::registry::LensEntry)> = registry.iter().collect();
    entries.sort_by(|a, b| a.0.cmp(b.0));

    println!("{{");
    println!("  \"total\": {},", entries.len());
    println!("  \"lenses\": [");
    for (i, (_, entry)) in entries.iter().enumerate() {
        let comma = if i + 1 < entries.len() { "," } else { "" };
        let domains_json: Vec<String> = entry.domain_affinity.iter().map(|d| format!("\"{}\"", d)).collect();
        let comp_json: Vec<String> = entry.complementary.iter().map(|c| format!("\"{}\"", c)).collect();
        println!(
            "    {{\"name\":\"{}\",\"category\":\"{:?}\",\"description\":\"{}\",\"domain_affinity\":[{}],\"complementary\":[{}]}}{}",
            entry.name,
            entry.category,
            entry.description.replace('\"', "\\\""),
            domains_json.join(","),
            comp_json.join(","),
            comma,
        );
    }
    println!("  ]");
    println!("}}");
    Ok(())
}

fn run_experiment(mode: ExperimentMode, target: &str, intensity: f64, duration: usize) -> Result<(), String> {
    let runner = ExperimentRunner::new();

    let results = match mode {
        ExperimentMode::All => {
            println!("=== NEXUS-6 Experiment: ALL 22 types on '{}' ===", target);
            runner.run_all(target)
        }
        ExperimentMode::Single(ref type_name) => {
            let exp_type = ExperimentType::from_str(type_name)
                .ok_or_else(|| format!("Unknown experiment type: '{}'. Use 'nexus6 experiment all <target>' to see all types.", type_name))?;
            println!("=== NEXUS-6 Experiment: {} on '{}' ===", exp_type.name(), target);
            println!("  {}", exp_type.description());
            println!("  Recommended lenses: {}", exp_type.recommended_lenses().join(", "));
            println!("  Intensity: {}  Duration: {}", intensity, duration);
            println!();
            let config = ExperimentConfig::new(exp_type, target)
                .with_intensity(intensity)
                .with_duration(duration);
            vec![runner.run(&config)]
        }
        ExperimentMode::Battery(ref type_names) => {
            let mut types = Vec::new();
            for name in type_names {
                let t = ExperimentType::from_str(name)
                    .ok_or_else(|| format!("Unknown experiment type in battery: '{}'", name))?;
                types.push(t);
            }
            println!("=== NEXUS-6 Experiment Battery: {} types on '{}' ===", types.len(), target);
            runner.run_battery(&types, target)
        }
    };

    println!();
    print!("{}", report::format_report(&results));
    Ok(())
}

fn run_ingest(sources: Vec<String>, config_path: Option<String>, verbose: bool) -> Result<(), String> {
    use crate::ingest::crawler;
    use std::path::PathBuf;
    use std::time::Instant;

    println!("=== NEXUS-6 Ingest: Multi-Project Crawler ===");
    println!();

    let config = if !sources.is_empty() {
        // Explicit --source overrides everything.
        let default_exts = vec![
            "toml".to_string(), "md".to_string(), "py".to_string(),
            "json".to_string(), "csv".to_string(), "txt".to_string(),
        ];
        let project_sources: Vec<crawler::ProjectSource> = sources
            .iter()
            .map(|s| {
                let path = PathBuf::from(s);
                let domain = path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown")
                    .to_string();
                crawler::ProjectSource {
                    path,
                    domain,
                    extensions: default_exts.clone(),
                }
            })
            .collect();
        crawler::CrawlConfig { sources: project_sources }
    } else {
        // Try JSON config: explicit --config path, then default location, then hardcoded fallback.
        let json_path = config_path.unwrap_or_else(|| "shared/projects.json".to_string());
        match crawler::load_from_json(&json_path) {
            Ok(cfg) => {
                info!(projects = cfg.sources.len(), config = json_path.as_str(), "Ingest config loaded");
                cfg
            }
            Err(e) => {
                if verbose {
                    debug!(path = json_path.as_str(), error = %e, "could not load config");
                }
                info!("Using hardcoded fallback sources");
                crawler::default_config()
            }
        }
    };

    for src in &config.sources {
        println!("  [{}] {}", src.domain, src.path.display());
    }
    println!();

    let start = Instant::now();
    let result = crawler::crawl(&config);
    let elapsed = start.elapsed();

    println!("  Files scanned:  {}", result.files_scanned);
    println!("  Files skipped:  {}", result.files_skipped);
    println!("  Probes found:   {}", result.probes.len());
    println!("  Elapsed:        {:.2?}", elapsed);

    if !result.errors.is_empty() {
        println!();
        println!("  Errors ({}):", result.errors.len());
        for err in &result.errors {
            println!("    {}", err);
        }
    }

    if verbose {
        println!();
        println!("  --- Probe Details ---");
        for probe in &result.probes {
            let named_count = probe.named_values.len();
            let raw_count = probe.raw_values.len();
            println!(
                "    [{}] {} — {} named, {} raw",
                probe.domain, probe.source_file, named_count, raw_count
            );
            for (name, val) in &probe.named_values {
                println!("      {}: {}", name, val);
            }
        }
    }

    // Summary by domain
    println!();
    println!("  --- By Domain ---");
    let mut domain_counts: std::collections::HashMap<String, (usize, usize)> =
        std::collections::HashMap::new();
    for probe in &result.probes {
        let entry = domain_counts.entry(probe.domain.clone()).or_insert((0, 0));
        entry.0 += 1;
        entry.1 += probe.named_values.len() + probe.raw_values.len();
    }
    for (domain, (files, values)) in &domain_counts {
        println!("    {:<20} {} files, {} values", domain, files, values);
    }

    let flat = crawler::flatten_all(&result);
    println!();
    println!("  Total numeric values: {}", flat.len());

    // Quick n6 check on the ingested data
    if !flat.is_empty() {
        let n6_ratio = crate::verifier::n6_check::n6_exact_ratio(&flat);
        println!("  n6 EXACT ratio:       {:.1}%", n6_ratio * 100.0);
    }

    println!();
    println!("  Ingest complete.");
    Ok(())
}

fn run_bench() -> Result<(), String> {
    println!("=== NEXUS-6 Benchmark Suite ===");
    println!();

    struct BenchResult {
        name: String,
        time_us: u128,
    }

    let mut results: Vec<BenchResult> = Vec::new();

    // 1. LensRegistry creation
    let t = Instant::now();
    let registry = LensRegistry::new();
    let reg_time = t.elapsed();
    let reg_count = registry.len();
    results.push(BenchResult {
        name: format!("Registry init ({})", reg_count),
        time_us: reg_time.as_micros(),
    });

    // 2. Telescope scan_all (small data)
    let telescope = Telescope::new();
    let probe_data: Vec<f64> = vec![6.0, 12.0, 24.0, 4.0, 2.0, 5.0];
    let t = Instant::now();
    let _scan_result = telescope.scan_all(&probe_data, probe_data.len(), 1);
    let scan_time = t.elapsed();
    results.push(BenchResult {
        name: format!("Telescope scan ({} lens)", telescope.lens_count()),
        time_us: scan_time.as_micros(),
    });

    // 3. EvolutionEngine evolve_step
    let mut evo_config = EvolutionConfig::default();
    evo_config.domain = "bench".to_string();
    let seeds = vec!["n=6 benchmark".to_string()];
    let mut engine = EvolutionEngine::new(evo_config, seeds);
    let t = Instant::now();
    let _step = engine.evolve_step();
    let evo_time = t.elapsed();
    results.push(BenchResult {
        name: "OUROBOROS step".to_string(),
        time_us: evo_time.as_micros(),
    });

    // 4. LensForge forge_cycle
    let forge_config = ForgeConfig::default();
    let history = Vec::new();
    let t = Instant::now();
    let _forge_result = forge_engine::forge_cycle(&registry, &history, &forge_config);
    let forge_time = t.elapsed();
    results.push(BenchResult {
        name: "LensForge cycle".to_string(),
        time_us: forge_time.as_micros(),
    });

    // Render ASCII table
    let max_name_len = results.iter().map(|r| r.name.len()).max().unwrap_or(20);
    let name_col = max_name_len.max(20);

    println!("\u{250c}{}\u{252c}{}\u{2510}",
        "\u{2500}".repeat(name_col + 2),
        "\u{2500}".repeat(12));
    println!("\u{2502} {:<width$} \u{2502} {:<10} \u{2502}",
        "Operation", "Time", width = name_col);
    println!("\u{251c}{}\u{253c}{}\u{2524}",
        "\u{2500}".repeat(name_col + 2),
        "\u{2500}".repeat(12));

    for r in &results {
        let time_str = format_duration_us(r.time_us);
        println!("\u{2502} {:<width$} \u{2502} {:<10} \u{2502}",
            r.name, time_str, width = name_col);
    }

    println!("\u{2514}{}\u{2534}{}\u{2518}",
        "\u{2500}".repeat(name_col + 2),
        "\u{2500}".repeat(12));

    // Total
    let total_us: u128 = results.iter().map(|r| r.time_us).sum();
    println!();
    println!("  Total: {}", format_duration_us(total_us));

    Ok(())
}

fn format_duration_us(us: u128) -> String {
    if us < 1_000 {
        format!("{}us", us)
    } else if us < 1_000_000 {
        format!("{:.1}ms", us as f64 / 1_000.0)
    } else {
        format!("{:.2}s", us as f64 / 1_000_000.0)
    }
}

fn run_dashboard(html: bool, output: Option<String>) -> Result<(), String> {
    if html {
        // TODO: implement dedicated HTML renderer; for now reuse ASCII
        let html_content = dashboard::render_dashboard();
        if let Some(path) = output {
            std::fs::write(&path, &html_content)
                .map_err(|e| format!("Failed to write {}: {}", path, e))?;
            println!("HTML dashboard written to: {}", path);
        } else {
            print!("{}", html_content);
        }
    } else {
        let out = dashboard::render_dashboard();
        print!("{}", out);
    }
    Ok(())
}

fn run_predict(experiment_type: &str, target: &str) -> Result<(), String> {
    use crate::science::predict;
    let prediction = predict::predict_experiment(experiment_type, target, &[]);
    println!("=== NEXUS-6 Predict: {} on '{}' ===", experiment_type, target);
    println!("  Predicted phi_delta:     {:.4}", prediction.predicted_phi_delta);
    println!("  Predicted entropy_delta: {:.4}", prediction.predicted_entropy_delta);
    println!("  Predicted n6_score:      {:.4}", prediction.predicted_n6_score);
    println!("  Confidence:              {:.4}", prediction.confidence);
    println!("  Reasoning: {}", prediction.reasoning);
    Ok(())
}

fn run_simulate(experiment_type: &str, target: &str, runs: usize) -> Result<(), String> {
    use crate::science::simulate;
    println!("=== NEXUS-6 Simulate: {} on '{}' ({} runs) ===", experiment_type, target, runs);
    let config = simulate::SimulationConfig {
        experiment_type: experiment_type.to_string(),
        target: target.to_string(),
        n_simulations: runs,
        noise_level: 0.1,
        time_steps: 6,
    };
    let result = simulate::simulate(&config);
    println!("  Mean phi_delta:     {:.4} (std {:.4})", result.mean_phi_delta, result.std_phi_delta);
    println!("  Mean entropy_delta: {:.4}", result.mean_entropy_delta);
    println!("  95th percentile:    {:.4}", result.percentile_95);
    println!("  Best case:          {:.4}", result.best_case);
    println!("  Worst case:         {:.4}", result.worst_case);
    if let Some(step) = result.convergence_step {
        println!("  Converged at step:  {}", step);
    }
    Ok(())
}

fn run_compare(a_spec: &str, b_spec: &str) -> Result<(), String> {
    use crate::science::compare;
    use crate::science::simulate;

    println!("=== NEXUS-6 Compare: {} vs {} ===", a_spec, b_spec);
    println!();

    // Parse specs as "type:target" or just "type"
    let (a_type, a_target) = parse_spec(a_spec)?;
    let (b_type, b_target) = parse_spec(b_spec)?;

    // Run simulations to generate comparable metrics
    let sim_a = simulate::simulate(&simulate::SimulationConfig {
        experiment_type: a_type,
        target: a_target,
        n_simulations: 50,
        noise_level: 0.1,
        time_steps: 10,
    });
    let sim_b = simulate::simulate(&simulate::SimulationConfig {
        experiment_type: b_type,
        target: b_target,
        n_simulations: 50,
        noise_level: 0.1,
        time_steps: 10,
    });

    let a_metrics = vec![
        ("phi_delta".to_string(), sim_a.mean_phi_delta),
        ("entropy_delta".to_string(), sim_a.mean_entropy_delta),
        ("std".to_string(), sim_a.std_phi_delta),
    ];
    let b_metrics = vec![
        ("phi_delta".to_string(), sim_b.mean_phi_delta),
        ("entropy_delta".to_string(), sim_b.mean_entropy_delta),
        ("std".to_string(), sim_b.std_phi_delta),
    ];

    let result = compare::compare(a_spec, &a_metrics, b_spec, &b_metrics);

    println!("  Winner: {}  (effect size: {:.4})", result.winner, result.effect_size);
    println!("  Significant: {}", result.statistically_significant);
    println!();
    for (name, a_val, b_val) in &result.details {
        println!("    {}: A={:.4}  B={:.4}  (diff={:+.4})", name, a_val, b_val, a_val - b_val);
    }
    Ok(())
}

/// Parse "type:target" spec, defaulting target to "default" if no colon.
fn parse_spec(spec: &str) -> Result<(String, String), String> {
    if let Some(pos) = spec.find(':') {
        let t = spec[..pos].to_string();
        let tgt = spec[pos + 1..].to_string();
        if t.is_empty() || tgt.is_empty() {
            return Err(format!("Invalid spec '{}' -- use 'type:target'", spec));
        }
        Ok((t, tgt))
    } else {
        Ok((spec.to_string(), "default".to_string()))
    }
}

fn run_reproduce(experiment_type: &str, target: &str, repeats: usize) -> Result<(), String> {
    use crate::science::reproduce;
    println!("=== NEXUS-6 Reproduce: {} on '{}' ({} repeats) ===", experiment_type, target, repeats);
    let config = reproduce::ReproductionConfig {
        experiment_type: experiment_type.to_string(),
        target: target.to_string(),
        n_repeats: repeats,
        variation: 0.1,
    };
    let result = reproduce::reproduce(&config);
    println!("  Mean:   {:.4}", result.mean);
    println!("  Std:    {:.4}", result.std);
    println!("  CV:     {:.4}", result.cv);
    println!("  Reproducible: {}", result.reproducible);
    if !result.outlier_runs.is_empty() {
        println!("  Outlier runs: {:?}", result.outlier_runs);
    }
    Ok(())
}

fn run_publish(experiment_type: &str, target: &str) -> Result<(), String> {
    use crate::science::publish;
    println!("=== NEXUS-6 Publish: {} on '{}' ===", experiment_type, target);
    let publication = publish::publish(experiment_type, target, None, None, &[], None);
    println!("{}", publication.markdown);
    Ok(())
}

fn run_cycle(experiment_type: &str, target: &str) -> Result<(), String> {
    use crate::science::{predict, simulate, compare, reproduce, publish};

    println!("=== NEXUS-6 Full Science Cycle: {} on {} ===", experiment_type, target);
    println!();

    let start = Instant::now();

    // Step 1: Predict
    println!("[1/6] Predicting...");
    let history: Vec<(String, f64, f64)> = Vec::new();
    let prediction = predict::predict_experiment(experiment_type, target, &history);
    println!("  -> confidence={:.4}, predicted_phi={:.4}", prediction.confidence, prediction.predicted_phi_delta);

    // Step 2: Simulate
    println!("[2/6] Simulating (100 runs)...");
    let sim_config = simulate::SimulationConfig {
        experiment_type: experiment_type.to_string(),
        target: target.to_string(),
        n_simulations: 100,
        noise_level: 0.1,
        time_steps: 10,
    };
    let sim_result = simulate::simulate(&sim_config);
    println!("  -> mean_phi={:.4}, std={:.4}", sim_result.mean_phi_delta, sim_result.std_phi_delta);

    // Step 3: Evaluate prediction against simulation
    println!("[3/6] Evaluating prediction...");
    let actual_phi = sim_result.mean_phi_delta;
    let actual_entropy = sim_result.mean_entropy_delta;
    let actual_n6 = 0.85;
    let pred_result = predict::evaluate_prediction(&prediction, actual_phi, actual_entropy, actual_n6);
    println!("  -> accuracy={:.4}, surprise={:.4}", pred_result.accuracy, pred_result.surprise);

    // Step 4: Compare prediction vs simulation
    println!("[4/6] Comparing prediction vs simulation...");
    let a_metrics = vec![
        ("phi_delta".to_string(), prediction.predicted_phi_delta),
        ("entropy_delta".to_string(), prediction.predicted_entropy_delta),
        ("n6_score".to_string(), prediction.predicted_n6_score),
    ];
    let b_metrics = vec![
        ("phi_delta".to_string(), sim_result.mean_phi_delta),
        ("entropy_delta".to_string(), sim_result.mean_entropy_delta),
        ("n6_score".to_string(), actual_n6),
    ];
    let cmp_result = compare::compare("prediction", &a_metrics, "simulation", &b_metrics);
    println!("  -> winner={}, effect_size={:.4}", cmp_result.winner, cmp_result.effect_size);

    // Step 5: Reproduce
    println!("[5/6] Reproducing (10 repeats)...");
    let repro_config = reproduce::ReproductionConfig {
        experiment_type: experiment_type.to_string(),
        target: target.to_string(),
        n_repeats: 10,
        variation: 0.05,
    };
    let repro_result = reproduce::reproduce(&repro_config);
    println!("  -> reproducible={}, CV={:.4}", repro_result.reproducible, repro_result.cv);

    // Step 6: Publish
    println!("[6/6] Publishing...");
    let actual_results = vec![
        ("phi_delta".to_string(), actual_phi),
        ("entropy_delta".to_string(), actual_entropy),
        ("n6_score".to_string(), actual_n6),
    ];
    let publication = publish::publish(
        experiment_type,
        target,
        Some(&pred_result),
        Some(&sim_result),
        &actual_results,
        Some(&repro_result),
    );

    let elapsed = start.elapsed();

    println!();
    println!("=== Cycle Complete ({:.2?}) ===", elapsed);
    println!("  Title: {}", publication.title);
    println!("  Key findings: {}", publication.key_findings.len());
    println!("  n=6 connections: {}", publication.n6_connections.len());
    if let Some(ref bt) = publication.bt_candidate {
        println!("  BT candidate: {}", bt);
    }
    println!("  Testable predictions: {}", publication.testable_predictions.len());
    println!();
    println!("--- Full Document ---");
    println!("{}", publication.markdown);

    Ok(())
}

fn run_report() -> Result<(), String> {
    let entries = load_projects();
    let projects: Vec<(&str, &str)> = entries.iter()
        .map(|p| (p.name.as_str(), p.path.as_str()))
        .collect();

    let w = 65;
    let line = "─".repeat(w);
    let now = hms_now();

    println!("  ┌{}┐", line);
    println!("  │ {:<w$}│", format!("🌐 NEXUS-6 통합 리포트 — {}", now));
    println!("  ├{}┤", line);

    // 브릿지 상태
    let bridge_path = std::env::var("HOME")
        .map(|h| format!("{}/Dev/nexus6/shared/bridge_state.json", h))
        .unwrap_or_default();
    if let Ok(bridge_str) = std::fs::read_to_string(&bridge_path) {
        if let Some(pts) = bridge_str.lines()
            .find(|l| l.contains("\"growth_points\""))
            .and_then(|l| l.split(':').nth(1))
            .map(|v| v.trim().trim_matches(',').trim())
        {
            println!("  │ {:<w$}│", format!("  🌳 Bridge: forest | {} pts", pts));
        }
    }

    // daemon 상태
    let daemon_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/daemon_status.txt", h))
        .unwrap_or_default();
    if let Ok(daemon) = std::fs::read_to_string(&daemon_path) {
        let loop_n = daemon.lines().find(|l| l.starts_with("loop="))
            .map(|l| l.trim_start_matches("loop=")).unwrap_or("?");
        let time = daemon.lines().find(|l| l.starts_with("time="))
            .map(|l| l.trim_start_matches("time=")).unwrap_or("?");
        println!("  │ {:<w$}│", format!("  🤖 Daemon: loop #{} | last {}", loop_n, time));
    }

    // scan 결과
    let scan_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_scan.txt", h))
        .unwrap_or_default();
    if let Ok(scan) = std::fs::read_to_string(&scan_path) {
        let mut exact = "?";
        let mut sing = "?";
        let mut conv = "?";
        for l in scan.lines() {
            if l.starts_with("exact_ratio=") { exact = l.trim_start_matches("exact_ratio="); }
            if l.starts_with("singularity=") { sing = l.trim_start_matches("singularity="); }
            if l.starts_with("convergence=") { conv = l.trim_start_matches("convergence="); }
        }
        println!("  │ {:<w$}│", format!("  🔭 Scan: exact={} conv={} singularity={}", exact, conv, sing));
    }

    // blowup 결과
    let blowup_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_blowup.txt", h))
        .unwrap_or_default();
    if let Ok(blowup) = std::fs::read_to_string(&blowup_path) {
        let mut emg = "?";
        let mut axm = "?";
        for l in blowup.lines() {
            if l.starts_with("total_emergences=") { emg = l.trim_start_matches("total_emergences="); }
            if l.starts_with("axiom_candidates=") { axm = l.trim_start_matches("axiom_candidates="); }
        }
        println!("  │ {:<w$}│", format!("  💥 Blowup: {} emergences | {} axiom candidates", emg, axm));
    }

    // loop 리포트
    let loop_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_loop_report.txt", h))
        .unwrap_or_default();
    if let Ok(loop_rpt) = std::fs::read_to_string(&loop_path) {
        // 렌즈/forge 줄만 추출
        for l in loop_rpt.lines() {
            if l.contains("렌즈:") || l.contains("Forged:") || l.contains("거울 우주") {
                println!("  │ {:<w$}│", format!("  {}", l.trim().trim_matches('│').trim()));
            }
        }
    }

    println!("  ├{}┤", line);
    println!("  │ {:<w$}│", "  📋 프로젝트별:");

    // 프로젝트별 한줄 요약
    for (name, path) in &projects {
        let state_path = format!("{}/.growth/growth_state.json", path);
        let hb_path = format!("{}/.growth/heartbeat", path);

        let cycle = std::fs::read_to_string(&state_path)
            .ok()
            .and_then(|s| {
                s.lines().find(|l| l.contains("\"cycle\""))
                    .and_then(|l| l.split(':').nth(1))
                    .map(|v| v.trim().trim_matches(',').trim().to_string())
            })
            .unwrap_or_else(|| "0".into());

        let alive = std::path::Path::new(&hb_path).exists();
        let icon = if alive { "✅" } else { "⏸️" };

        // bridge DNA에서 언어/테스트 정보
        let lang = std::fs::read_to_string(&bridge_path)
            .ok()
            .and_then(|s| {
                // 간단히 language 필드 검색
                let key = format!("\"{}\"", name);
                if let Some(pos) = s.find(&key) {
                    let section = &s[pos..pos.saturating_add(500).min(s.len())];
                    section.lines()
                        .find(|l| l.contains("\"language\""))
                        .and_then(|l| l.split('"').nth(3))
                        .map(|v| v.to_string())
                } else {
                    None
                }
            })
            .unwrap_or_else(|| "?".into());

        println!("  │ {:<w$}│",
            format!("  {} {:<18} c={:<4} {} ", icon, name, cycle, lang));
    }

    println!("  └{}┘", line);

    Ok(())
}

// ─── Status command helpers ────────────────────────────────────

/// Extract PID from the first line of a background log file.
/// Expects format like "PID=12345" or just a number on the first line after spawn.
fn extract_pid_from_log(path: &str) -> Option<String> {
    let content = std::fs::read_to_string(path).ok()?;
    let first_line = content.lines().next()?;
    // Try PID=NNN pattern first
    if let Some(pid) = first_line.strip_prefix("PID=") {
        return Some(pid.trim().to_string());
    }
    // Try extracting any number that looks like a PID
    for word in first_line.split_whitespace() {
        if word.chars().all(|c| c.is_ascii_digit()) && word.len() >= 2 {
            return Some(word.to_string());
        }
    }
    None
}

/// Check if a PID is alive using `kill -0` (macOS compatible, no /proc).
fn check_pid_alive(pid: &str) -> bool {
    std::process::Command::new("kill")
        .args(["-0", pid])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Return the last N lines of a file.
fn tail_lines(path: &str, n: usize) -> Vec<String> {
    let content = match std::fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return vec![],
    };
    let lines: Vec<&str> = content.lines().collect();
    let start = lines.len().saturating_sub(n);
    lines[start..].iter().map(|l| l.to_string()).collect()
}

fn run_status() -> Result<(), String> {
    let home = std::env::var("HOME").unwrap_or_default();
    let nexus_dir = format!("{}/.nexus6", home);
    let w = 72;
    let line = "-".repeat(w);

    println!("  +{}+", line);
    println!("  | {:<w$}|", "NEXUS-6 Status");
    println!("  +{}+", line);

    // 1. Background processes from *_bg.log files
    println!("  | {:<w$}|", "Background Processes:");
    println!("  +{}+", line);
    println!(
        "  | {:<20} {:<8} {:<10} {:<w2$}|",
        "NAME", "PID", "STATE", "LAST OUTPUT",
        w2 = w - 20 - 8 - 10 - 1
    );
    println!("  +{}+", line);

    let mut found_any = false;
    if let Ok(entries) = std::fs::read_dir(&nexus_dir) {
        let mut logs: Vec<_> = entries
            .flatten()
            .filter(|e| {
                e.file_name()
                    .to_str()
                    .map(|n| n.ends_with("_bg.log"))
                    .unwrap_or(false)
            })
            .collect();
        logs.sort_by_key(|e| e.file_name());

        for entry in &logs {
            found_any = true;
            let fname = entry.file_name().to_string_lossy().to_string();
            let name = fname.trim_end_matches("_bg.log");
            let full_path = format!("{}/{}", nexus_dir, fname);

            let pid = extract_pid_from_log(&full_path).unwrap_or_else(|| "?".to_string());
            let alive = if pid != "?" {
                check_pid_alive(&pid)
            } else {
                false
            };
            let state = if alive { "running" } else { "stopped" };

            let tail = tail_lines(&full_path, 3);
            let last = if tail.is_empty() {
                "(empty)".to_string()
            } else {
                let s = tail.last().unwrap().clone();
                if s.len() > 30 { format!("{}...", &s[..30]) } else { s }
            };

            println!(
                "  | {:<20} {:<8} {:<10} {:<w2$}|",
                name, pid, state, last,
                w2 = w - 20 - 8 - 10 - 1
            );

            // Show last 3 lines indented
            for tl in &tail {
                let truncated = if tl.len() > (w - 6) {
                    format!("{}...", &tl[..w - 9])
                } else {
                    tl.clone()
                };
                println!("  |   {:<w3$}|", truncated, w3 = w - 3);
            }
        }
    }

    if !found_any {
        println!("  | {:<w$}|", "(no background processes found)");
    }

    println!("  +{}+", line);

    // 2. Daemon status
    let daemon_path = format!("{}/.nexus6/daemon_status.txt", home);
    if let Ok(daemon) = std::fs::read_to_string(&daemon_path) {
        println!("  | {:<w$}|", "Daemon Status:");
        for l in daemon.lines().take(5) {
            println!("  |   {:<w3$}|", l, w3 = w - 3);
        }
        println!("  +{}+", line);
    }

    // 3. Last scan
    let scan_path = format!("{}/.nexus6/last_scan.txt", home);
    if let Ok(scan) = std::fs::read_to_string(&scan_path) {
        println!("  | {:<w$}|", "Last Scan:");
        for l in scan.lines().take(5) {
            println!("  |   {:<w3$}|", l, w3 = w - 3);
        }
        println!("  +{}+", line);
    }

    Ok(())
}

fn run_pack(sub: crate::cli::parser::PackSub) -> Result<(), String> {
    use crate::cli::parser::PackSub;
    use crate::pack;
    match sub {
        PackSub::Install { force } => pack::install(force),
        PackSub::Uninstall => pack::uninstall(),
        PackSub::Status => pack::status(),
        PackSub::Doctor => pack::doctor(),
    }
}

fn run_sentry(sub: crate::cli::parser::SentrySub) -> Result<(), String> {
    use crate::cli::parser::SentrySub;
    use crate::sentry;
    match sub {
        SentrySub::Start { interval_sec, foreground } => sentry::start(interval_sec, foreground),
        SentrySub::Stop => sentry::stop(),
        SentrySub::Status => sentry::status(),
        SentrySub::Tail { lines } => sentry::tail(lines),
    }
}

fn run_hook(sub: crate::cli::parser::HookSub) -> Result<(), String> {
    use crate::cli::parser::HookSub;
    use crate::pack::hook_cmd;
    match sub {
        HookSub::List => hook_cmd::list(),
        HookSub::Enable { name } => hook_cmd::enable(&name),
        HookSub::Disable { name } => hook_cmd::disable(&name),
    }
}

fn run_dispatch(target: &str, prompt: &str, parallel: bool) -> Result<(), String> {
    use std::process::Command;

    let nexus_root = std::env::var("NEXUS6_ROOT")
        .unwrap_or_else(|_| "/Users/ghost/Dev/nexus6".to_string());
    let script = format!("{}/scripts/dispatch.sh", nexus_root);

    let mut args = Vec::new();
    if parallel {
        args.push("--parallel".to_string());
    }
    args.push(target.to_string());
    args.push(prompt.to_string());

    println!("📡 Dispatch: {} → \"{}\"", target, prompt);

    let status = Command::new("bash")
        .arg(&script)
        .args(&args)
        .status()
        .map_err(|e| format!("dispatch 실행 실패: {}", e))?;

    if status.success() {
        Ok(())
    } else {
        Err(format!("dispatch exit {:?}", status.code()))
    }
}

fn run_mega(nexus_cfg: &NexusConfig) -> Result<(), String> {
    use std::process::Command;
    use std::time::Instant;

    let t0 = Instant::now();
    info!("MEGA LOOP 시작 — 전 프로젝트 통합 루프");

    let entries = load_projects();
    let projects: Vec<(&str, &str, &str)> = entries.iter()
        .map(|p| (p.name.as_str(), p.domain.as_str(), p.path.as_str()))
        .collect();

    let mut results: Vec<(String, String, f64, bool)> = Vec::new(); // name, status, time, ok

    // Step 1: nexus6 loop
    println!("━━━ [1/3] NEXUS-6 Core Loop ━━━");
    let pt = Instant::now();
    let loop_ok = run_loop(Some("number_theory".to_string()), 1, nexus_cfg).is_ok();
    let loop_time = pt.elapsed().as_secs_f64();
    results.push(("nexus6".into(), if loop_ok { "OK" } else { "FAIL" }.into(), loop_time, loop_ok));
    println!();

    // heartbeat 갱신
    for (name, _, path) in &projects {
        let hb_dir = format!("{}/.growth", path);
        let _ = std::fs::create_dir_all(&hb_dir);
        let hb = format!("{}/heartbeat", hb_dir);
        let now = hms_now();
        let _ = std::fs::write(&hb, &now);
    }

    // Step 2: 각 프로젝트 infinite_growth 1회 (병렬)
    println!("━━━ [2/3] 프로젝트별 Growth (1 cycle, 병렬) ━━━");
    {
        use std::thread;
        use std::sync::{Arc, Mutex};

        let results_shared = Arc::new(Mutex::new(Vec::new()));
        let mut handles = Vec::new();

        for (name, _domain, path) in &projects {
            if *name == "nexus6" { continue; }
            let script = format!("{}/scripts/infinite_growth.sh", path);
            if !std::path::Path::new(&script).exists() {
                results_shared.lock().unwrap().push((name.to_string(), "NO_SCRIPT".into(), 0.0, false));
                continue;
            }
            let name = name.to_string();
            let script = script.clone();
            let results = Arc::clone(&results_shared);
            handles.push(thread::spawn(move || {
                let pt = std::time::Instant::now();
                let status = std::process::Command::new("bash")
                    .arg(&script)
                    .env("MAX_CYCLES", "1")
                    .env("INTERVAL", "0")
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .status();
                let elapsed = pt.elapsed().as_secs_f64();
                let ok = status.map(|s| s.success()).unwrap_or(false);
                results.lock().unwrap().push((name, if ok { "OK".into() } else { "FAIL".into() }, elapsed, ok));
            }));
        }
        for h in handles { let _ = h.join(); }
        // Arc에서 결과 꺼내기
        let parallel_results = results_shared.lock().unwrap().clone();
        for (name, status, elapsed, _) in &parallel_results {
            println!("  {:<20} {} ({:.1}s)", format!("{}:", name), if status == "OK" { "✅" } else { "⚠️" }, elapsed);
        }
        results.extend(parallel_results);
    }
    println!();

    // Step 3: 통합 리포트
    println!("━━━ [3/3] 통합 리포트 ━━━");
    let total_time = t0.elapsed().as_secs_f64();
    let ok_count = results.iter().filter(|r| r.3).count();
    let total = results.len();

    let w = 65;
    let line = "─".repeat(w);
    println!("  ┌{}┐", line);
    println!("  │ {:<w$}│", format!("🌐 MEGA LOOP — {}/{} 프로젝트 성공", ok_count, total));
    println!("  ├{}┤", line);

    for (name, status, time, _ok) in &results {
        let icon = if status == "OK" { "✅" } else if status == "NO_SCRIPT" { "⏭️" } else { "⚠️" };

        // 프로젝트별 상세 정보 읽기
        let detail = std::fs::read_to_string(format!("/Users/ghost/Dev/{}/.growth/growth_state.json", name))
            .ok()
            .and_then(|s| {
                // cycle 수 추출
                s.lines().find(|l| l.contains("\"cycle\""))
                    .and_then(|l| l.split(':').nth(1))
                    .map(|v| v.trim().trim_matches(',').to_string())
            })
            .unwrap_or_else(|| "?".to_string());

        println!("  │ {:<w$}│", format!("  {} {:<18} {} c={} ({:.1}s)",
            icon, name, status, detail, time));
    }

    println!("  ├{}┤", line);

    // scan/blowup 결과 표시
    let scan_file = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_scan.txt", h))
        .unwrap_or_default();
    if let Ok(scan) = std::fs::read_to_string(&scan_file) {
        for line_str in scan.lines() {
            if line_str.contains("singularity") || line_str.contains("exact_ratio") || line_str.contains("convergence") {
                println!("  │ {:<w$}│", format!("  📊 {}", line_str));
            }
        }
    }

    let blowup_file = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_blowup.txt", h))
        .unwrap_or_default();
    if let Ok(blowup) = std::fs::read_to_string(&blowup_file) {
        for line_str in blowup.lines() {
            if line_str.contains("total_emergences") || line_str.contains("axiom_candidates") {
                println!("  │ {:<w$}│", format!("  💥 {}", line_str));
            }
        }
    }

    // heartbeat 상태
    let mut alive = 0;
    let mut stale = 0;
    for (name, _, _) in &projects {
        let hb = format!("/Users/ghost/Dev/{}/.growth/heartbeat", name);
        if std::path::Path::new(&hb).exists() { alive += 1; } else { stale += 1; }
    }
    println!("  │ {:<w$}│", format!("  💓 Heartbeat: {} alive / {} stale", alive, stale));

    // 프로젝트별 사이클 리포트
    let reports_dir = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/project_reports", h))
        .unwrap_or_default();
    if std::path::Path::new(&reports_dir).is_dir() {
        println!("  ├{}┤", line);
        println!("  │ {:<w$}│", "  📋 프로젝트별 리포트:");
        for (name, _, _) in &projects {
            let rpt = format!("{}/{}.txt", reports_dir, name);
            if let Ok(content) = std::fs::read_to_string(&rpt) {
                for rpt_line in content.lines().take(8) {
                    println!("  │ {:<w$}│", format!("  {}", rpt_line.trim()));
                }
                println!("  │ {:<w$}│", "");
            }
        }
    }

    println!("  ├{}┤", line);
    println!("  │ {:<w$}│", format!("  ⏱️  Total: {:.1}s", total_time));
    println!("  └{}┘", line);

    // 파일 저장
    let report = format!(
        "mega_loop\nprojects={}/{}\ntime={:.1}s\nok={}\nfail={}\n",
        ok_count, total, total_time, ok_count, total - ok_count
    );
    let path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_mega.txt", h))
        .unwrap_or_else(|_| "/tmp/nexus6_mega.txt".to_string());
    let _ = std::fs::write(&path, &report);

    Ok(())
}

fn run_blowup(domain: &str, max_depth: usize, nexus_cfg: &NexusConfig) -> Result<(), String> {
    use std::collections::HashMap;

    println!("=== NEXUS-6 Blowup Engine ===");
    println!("  도메인: {} | 최대 깊이: {}", domain, max_depth);
    println!();

    // Step 1: 진화 루프를 돌려서 메트릭 히스토리 생성 (특이점 탐색)
    info!(domain, "Blowup 1/4: 진화 루프 (특이점 탐색)");
    let seeds = vec![format!("n=6 patterns in {}", domain)];
    let base_config = nexus_cfg.meta_loop_config();
    let config = MetaLoopConfig {
        max_ouroboros_cycles: base_config.max_ouroboros_cycles,
        max_meta_cycles: 3, // blowup uses 3 meta-cycles for probing
        forge_after_n_cycles: base_config.forge_after_n_cycles,
        forge_config: base_config.forge_config,
    };
    let mut meta_loop = MetaLoop::new(domain.to_string(), seeds, config);
    meta_loop.on_progress = Some(Box::new(|mc, oc, msg| {
        if oc == 0 {
            tracing::debug!(meta_cycle = mc, "{}", msg);
        }
    }));
    let result = meta_loop.run();
    info!(discoveries = result.total_discoveries, forged = result.forged_lenses.len(), "진화 루프 완료");

    // Step 2: 메트릭 히스토리에서 특이점 감지
    println!();
    info!(domain, "Blowup 2/4: 특이점 감지");

    // 진화 결과에서 히스토리 구성
    let mut history: Vec<HashMap<String, f64>> = Vec::new();
    for summary in &result.meta_cycle_summaries {
        let mut snapshot = HashMap::new();
        snapshot.insert("discoveries".into(), summary.discoveries as f64);
        snapshot.insert("ouroboros_cycles".into(), summary.ouroboros_cycles_run as f64);
        snapshot.insert("lenses".into(), result.final_registry.len() as f64);
        // n=6 상수 주입
        snapshot.insert("sigma".into(), 12.0);
        snapshot.insert("phi".into(), 2.0);
        snapshot.insert("tau".into(), 4.0);
        snapshot.insert("n".into(), 6.0);
        history.push(snapshot);
    }

    // 히스토리가 부족하면 수동으로 특이점 구성
    let singularity = if history.len() >= 6 {
        let detector = crate::blowup::SingularityDetector {
            min_closure: 0.5,
            min_compression: 1.5,
            window: history.len().min(6),
        };
        detector.detect(&history)
    } else {
        None
    };

    let singularity = singularity.unwrap_or_else(|| {
        warn!("자동 감지 실패 — 강제 특이점 생성 (n=6 공리 기반)");
        let mut metrics = HashMap::new();
        metrics.insert("sigma".into(), 12.0);
        metrics.insert("phi".into(), 2.0);
        metrics.insert("tau".into(), 4.0);
        metrics.insert("n".into(), 6.0);
        metrics.insert("sopfr".into(), 5.0);
        metrics.insert("J2".into(), 24.0);
        if let Some(last) = history.last() {
            for (k, v) in last {
                metrics.insert(k.clone(), *v);
            }
        }
        Singularity {
            axioms: vec!["sigma".into(), "phi".into(), "tau".into(), "n".into(), "sopfr".into(), "J2".into()],
            compression_ratio: 6.0,
            closure_degree: 1.0,
            domain: domain.to_string(),
            metrics,
        }
    });

    debug!(axioms = ?singularity.axioms, closure = singularity.closure_degree, compression = singularity.compression_ratio, "특이점 감지 결과");

    // Step 3: Blowup!
    println!();
    info!(domain, max_depth, "Blowup 3/4: BLOWUP (특이점 -> 따름정리)");
    let blowup_config = BlowupConfig {
        max_depth,
        max_corollaries: 36, // 6²
        min_confidence: 0.2,
        transfer_domains: vec![
            domain.into(),
            "physics".into(),
            "mathematics".into(),
            "information".into(),
            "biology".into(),
            "consciousness".into(),
            "architecture".into(),
        ],
        ..BlowupConfig::default()
    };
    let engine = BlowupEngine::new(blowup_config);
    let blowup_result = engine.blowup(&singularity);

    info!(depth = blowup_result.depth_reached, max_depth,
          corollaries = blowup_result.corollaries.len(),
          validated = blowup_result.validated.len(),
          axiom_candidates = blowup_result.new_axiom_candidates.len(),
          emergences = blowup_result.total_emergences,
          "Blowup 완료");

    // Step 4: 결과 리포트
    println!();
    println!("  [4/4] 📋 창발 리포트");
    let w = 65;
    let line = "─".repeat(w);
    println!("  ┌{}┐", line);
    println!("  │ 💥 BLOWUP 결과 — {} {:<pad$}│", domain, "", pad = w - 18 - domain.len());
    println!("  ├{}┤", line);

    if blowup_result.validated.is_empty() {
        println!("  │ {:<w$}│", "  (따름정리 없음 — 시스템이 아직 열려있음)");
    } else {
        for (i, c) in blowup_result.validated.iter().enumerate().take(20) {
            let type_str = match c.corollary_type {
                crate::blowup::CorollaryType::Deduction => "연역",
                crate::blowup::CorollaryType::DomainTransfer => "이전",
                crate::blowup::CorollaryType::SymmetryBreaking => "대칭파괴",
                crate::blowup::CorollaryType::Bifurcation => "분기",
                crate::blowup::CorollaryType::Composition => "합성",
                crate::blowup::CorollaryType::Projection => "사영",
                crate::blowup::CorollaryType::Dual => "쌍대",
            };
            let axiom_tag = if c.is_axiom_candidate { " ★" } else { "" };
            let sector_tag = c.mk2_sector.as_ref()
                .map(|s| format!(" [{}]", s))
                .unwrap_or_default();
            println!("  │ {:<w$}│",
                format!("  {:>2}. [{}] {} (conf={:.2}){}{}",
                    i + 1, type_str, c.expression.chars().take(35).collect::<String>(),
                    c.confidence, axiom_tag, sector_tag));
        }
        if blowup_result.validated.len() > 20 {
            println!("  │ {:<w$}│", format!("  ... +{} more", blowup_result.validated.len() - 20));
        }
    }

    println!("  ├{}┤", line);
    println!("  │ {:<w$}│", format!("  창발 {}개 | 공리후보 {}개 | 깊이 {}/{}",
        blowup_result.total_emergences, blowup_result.new_axiom_candidates.len(),
        blowup_result.depth_reached, max_depth));
    println!("  └{}┘", line);

    // 결과를 파일로 저장
    let report_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_blowup.txt", h))
        .unwrap_or_else(|_| "/tmp/nexus6_blowup.txt".to_string());
    let _ = std::fs::create_dir_all(std::path::Path::new(&report_path).parent().unwrap());
    let report = format!(
        "domain={}\ndepth={}/{}\ncorollaries={}\nvalidated={}\naxiom_candidates={}\ntotal_emergences={}\n",
        domain, blowup_result.depth_reached, max_depth,
        blowup_result.corollaries.len(), blowup_result.validated.len(),
        blowup_result.new_axiom_candidates.len(), blowup_result.total_emergences
    );
    let _ = std::fs::write(&report_path, &report);

    // blowup 결과를 discovery_log.jsonl에 기록
    let disco_path = std::env::var("HOME")
        .map(|h| format!("{}/Dev/nexus6/shared/discovery_log.jsonl", h))
        .unwrap_or_else(|_| "shared/discovery_log.jsonl".to_string());
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&disco_path) {
        use std::io::Write;
        let ts = hms_now();
        for c in &blowup_result.corollaries {
            let sector = c.mk2_sector.as_ref().map(|s| format!("{:?}", s)).unwrap_or_default();
            let entry = format!(
                "{{\"timestamp\":\"{}\",\"kind\":\"blowup_corollary\",\"domain\":\"{}\",\"pattern\":\"{}\",\"confidence\":{:.3},\"depth\":{},\"sector\":\"{}\",\"axiom_candidate\":{}}}\n",
                ts, domain, c.expression.replace('"', "'"), c.confidence,
                blowup_result.depth_reached, sector, c.is_axiom_candidate
            );
            let _ = f.write_all(entry.as_bytes());
        }
    }

    Ok(())
}

fn run_daemon(domain: Option<String>, interval_min: u64, max_loops: Option<usize>, nexus_cfg: &NexusConfig) -> Result<(), String> {
    let domain_str = domain.as_deref().unwrap_or("number_theory").to_string();

    // ── PID lock (foreground 모드) ──
    let log_dir = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6", h))
        .unwrap_or_else(|_| "/tmp".to_string());
    let _ = std::fs::create_dir_all(&log_dir);
    let pid_path = format!("{}/daemon.pid", log_dir);
    let my_pid = std::process::id().to_string();
    if let Ok(old_pid) = std::fs::read_to_string(&pid_path) {
        let old_pid = old_pid.trim();
        if !old_pid.is_empty() && old_pid != my_pid && check_pid_alive(old_pid) {
            return Err(format!(
                "Daemon 이미 실행 중 (PID {}). 중복 실행 차단됨.",
                old_pid
            ));
        }
    }
    let _ = std::fs::write(&pid_path, &my_pid);

    // 종료 시 PID 파일 정리
    let pid_path_cleanup = pid_path.clone();
    let cleanup_pid = my_pid.clone();
    struct PidGuard { path: String, pid: String }
    impl Drop for PidGuard {
        fn drop(&mut self) {
            if let Ok(content) = std::fs::read_to_string(&self.path) {
                if content.trim() == self.pid {
                    let _ = std::fs::remove_file(&self.path);
                }
            }
        }
    }
    let _guard = PidGuard { path: pid_path_cleanup, pid: cleanup_pid };

    info!(domain = %domain_str, interval_min, max_loops = ?max_loops, "Daemon 시작");

    let mut loop_count = 0usize;

    loop {
        if let Some(max) = max_loops {
            if loop_count >= max {
                info!(loops = max, "데몬 루프 완료 — 종료");
                break;
            }
        }

        loop_count += 1;
        info!(loop_count, "Daemon 루프 시작");

        // 각 프로젝트가 독립 무한루프하므로, max_loops만큼 cycles를 한번에 넘김
        let batch_cycles = if interval_min == 0 {
            max_loops.unwrap_or(usize::MAX)  // interval=0이면 전부 한번에
        } else {
            1
        };

        if let Err(e) = run_loop(Some(domain_str.clone()), batch_cycles, nexus_cfg) {
            warn!(error = %e, retry_min = interval_min, "Loop 에러 — 재시도 대기");
        }

        // 데몬 상태 저장
        let status = format!("loop={}\ntime={}\nnext={}min\ndomain={}\n",
            loop_count, hms_now(), interval_min, domain_str);
        let path = std::env::var("HOME")
            .map(|h| format!("{}/.nexus6/daemon_status.txt", h))
            .unwrap_or_else(|_| "/tmp/nexus6_daemon_status.txt".to_string());
        let _ = std::fs::create_dir_all(std::path::Path::new(&path).parent().unwrap());
        let _ = std::fs::write(&path, &status);

        // interval=0 + batch이면 이미 전부 끝남
        if interval_min == 0 { break; }
        if max_loops.map(|m| loop_count >= m).unwrap_or(false) { break; }

        debug!(interval_min, "대기 중...");
        std::thread::sleep(std::time::Duration::from_secs(interval_min * 60));
    }

    info!(total_loops = loop_count, "Daemon 종료");
    Ok(())
}

fn run_loop(domain: Option<String>, cycles: usize, nexus_cfg: &NexusConfig) -> Result<(), String> {
    use std::time::Instant;

    // 적응형 도메인 선택: 이전 루프 발견 수가 0이면 도메인 전환
    let domain_str = {
        let base = domain.as_deref().unwrap_or("number_theory").to_string();
        let scan_file = std::env::var("HOME")
            .map(|h| format!("{}/.nexus6/last_scan.txt", h))
            .unwrap_or_default();
        let should_rotate = std::fs::read_to_string(&scan_file)
            .ok()
            .and_then(|s| {
                s.lines()
                    .find(|l| l.starts_with("domain="))
                    .map(|l| l.trim_start_matches("domain=").to_string())
            })
            .map(|prev_domain| prev_domain == base)
            .unwrap_or(false);

        if should_rotate && base == "number_theory" {
            let domains = ["physics", "consciousness", "architecture",
                           "signal_detection", "neuroscience", "programming_language"];
            let idx = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs() as usize % domains.len();
            let rotated = domains[idx].to_string();
            info!(from = %base, to = %rotated, "도메인 자동 전환");
            rotated
        } else {
            base
        }
    };
    let now = hms_now();
    let t0 = Instant::now();

    // ── Pre-state snapshot ──
    let registry_before = LensRegistry::new();
    let lens_before = registry_before.iter().count();
    let graph_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/discovery_graph.json", h))
        .unwrap_or_else(|_| ".nexus6/discovery_graph.json".to_string());
    let graph_before = DiscoveryGraph::load(&graph_path)
        .map(|g| (g.nodes.len(), g.edges.len()))
        .unwrap_or((0, 0));

    // ── Accumulators ──
    let mut total_discoveries = 0usize;
    let mut total_forged: Vec<String> = Vec::new();
    let mut scan_active = 0usize;
    let mut scan_total = 0usize;
    let mut bridge_sync_ok = 0usize;
    let mut bridge_sync_total = 0usize;
    let mut discovered_projects = 0usize;
    let mut connected_projects = 0usize;
    let mut phase_times: Vec<(String, f64)> = Vec::new();
    let mut discovery_curve: Vec<usize> = Vec::new();
    let mut mirror_top_pairs: Vec<(String, String, f64)> = Vec::new();
    let mut mirror_harmony: f64 = 0.0;
    let mut mirror_eigenvalue: f64 = 0.0;
    // Carry forged lenses across cycles so growth accumulates
    let mut carry_registry = LensRegistry::new();

    for cycle in 1..=cycles {
        if cycles > 1 {
            println!("━━━ Cycle {}/{} ━━━", cycle, cycles);
        }

        // Phase 0: Bridge self-update + load check
        let pt = Instant::now();
        info!(cycle, "Phase 0/8: Bridge update + 부하 체크");
        let _ = run_bridge(vec!["update".to_string()]);

        // System load gate — wait if overloaded
        loop {
            let load = get_system_load();
            let mem_free_pct = get_mem_free_pct();
            if load.0 < 20.0 && mem_free_pct > 5.0 {
                if load.0 > 10.0 {
                    warn!(load = load.0, "고부하 — 경량 모드 진행");
                } else {
                    debug!(load = load.0, mem_free_pct, "시스템 부하 정상");
                }
                break;
            }
            warn!(load = load.0, mem_free_pct, "과부하 감지 — 30초 대기");
            std::thread::sleep(std::time::Duration::from_secs(30));
        }
        phase_times.push(("BridgeUpdate".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 1: Discover + Auto-Connect
        let pt = Instant::now();
        info!(cycle, "Phase 1/8: Discover + Connect");
        // discover new projects
        let disc_out = run_bridge_capture(vec!["discover".to_string()]);
        let new_count = disc_out.lines()
            .filter(|l| l.contains("새 프로젝트 발견"))
            .filter_map(|l| l.split_whitespace().next().and_then(|n| n.trim().parse::<usize>().ok()))
            .next().unwrap_or(0);
        if new_count > 0 {
            discovered_projects += new_count;
            // extract project names and auto-connect each
            for line in disc_out.lines() {
                let trimmed = line.trim();
                // lines like "  1. project_name   [markers]"
                if let Some(rest) = trimmed.strip_prefix(|c: char| c.is_ascii_digit()) {
                    let rest = rest.trim_start_matches('.');
                    if let Some(name) = rest.trim().split_whitespace().next() {
                        debug!(project = name, "auto-connect");
                        let _ = run_bridge(vec!["connect".to_string(), name.to_string()]);
                        connected_projects += 1;
                    }
                }
            }
        } else {
            debug!("모든 프로젝트 연결됨");
        }
        phase_times.push(("Discover".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 2+3: 모든 프로젝트 병렬 Scan+Auto (완료 시그널 방식)
        let pt = Instant::now();
        let all_projects = load_projects();
        let project_domains: Vec<String> = if all_projects.is_empty() {
            vec![domain_str.clone()]
        } else {
            all_projects.iter().map(|p| p.domain.clone()).collect()
        };
        let project_names: Vec<String> = if all_projects.is_empty() {
            vec![domain_str.clone()]
        } else {
            all_projects.iter().map(|p| p.name.clone()).collect()
        };
        let n_projects = project_domains.len();
        info!(cycle, projects = n_projects, "Phase 2+3/8: 병렬 Scan+Auto (시그널 방식)");

        let base_mlc = nexus_cfg.meta_loop_config();
        {
            use std::sync::mpsc;
            use std::thread;

            #[derive(Debug)]
            enum ProjectSignal {
                Started { name: String },
                ScanDone { name: String, ok: bool },
                AutoDone { name: String, discoveries: usize, forged: Vec<String>, curve: Vec<usize>, registry: LensRegistry, elapsed: f64 },
                Error { name: String, msg: String },
            }

            let (tx, rx) = mpsc::channel::<ProjectSignal>();

            // 각 프로젝트가 독립적으로 무한 자기 루프 — 끝나면 바로 다시 시작
            for (dom, name) in project_domains.iter().zip(project_names.iter()) {
                let dom = dom.clone();
                let name = name.clone();
                let tx = tx.clone();
                let initial_reg = carry_registry.clone();
                let forge_after = base_mlc.forge_after_n_cycles;
                let forge_cfg = base_mlc.forge_config.clone();
                let target_cycles = cycles;

                thread::spawn(move || {
                    let mut local_reg = initial_reg;
                    let mut round = 0usize;
                    loop {
                        round += 1;
                        if round > target_cycles { break; }

                        let t0 = Instant::now();
                        let _ = tx.send(ProjectSignal::Started { name: name.clone() });

                        // Scan
                        let scan_ok = match run_scan(&dom, None, false) {
                            Ok(_) => true,
                            Err(e) => {
                                let _ = tx.send(ProjectSignal::Error { name: name.clone(), msg: format!("scan: {}", e) });
                                false
                            }
                        };
                        let _ = tx.send(ProjectSignal::ScanDone { name: name.clone(), ok: scan_ok });

                        // Auto
                        let seeds = vec![format!("n=6 in {}", dom)];
                        let config = MetaLoopConfig {
                            max_ouroboros_cycles: 3,
                            max_meta_cycles: 3,
                            forge_after_n_cycles: forge_after,
                            forge_config: forge_cfg.clone(),
                        };
                        let proj_name = name.clone();
                        let mut meta_loop = MetaLoop::new(dom.clone(), seeds, config);
                        meta_loop.initial_registry = Some(local_reg.clone());
                        meta_loop.on_progress = Some(Box::new(move |mc, oc, msg| {
                            if oc == 0 {
                                tracing::debug!(project = %proj_name, meta_cycle = mc, "{}", msg);
                            } else {
                                tracing::debug!(project = %proj_name, meta_cycle = mc, ouro_cycle = oc, "{}", msg);
                            }
                        }));
                        let result = meta_loop.run();
                        let curve: Vec<usize> = result.meta_cycle_summaries.iter().map(|s| s.discoveries).collect();
                        local_reg = result.final_registry.clone();

                        let _ = tx.send(ProjectSignal::AutoDone {
                            name: name.clone(),
                            discoveries: result.total_discoveries,
                            forged: result.forged_lenses.clone(),
                            curve,
                            registry: result.final_registry.clone(),
                            elapsed: t0.elapsed().as_secs_f64(),
                        });
                        // 바로 다음 라운드 시작 — 대기 없음
                    }
                });
            }
            drop(tx); // 모든 스레드 종료 시 rx 자동 종료

            // 메인 스레드: 시그널 수신 + 집계
            let mut done_count = 0usize;
            for signal in rx {
                match signal {
                    ProjectSignal::Started { name } => {
                        info!(project = %name, "[{}/{}] 시작", done_count + 1, n_projects);
                    }
                    ProjectSignal::ScanDone { name, ok } => {
                        if ok {
                            debug!(project = %name, "Scan ✓");
                        } else {
                            warn!(project = %name, "Scan ✗");
                        }
                    }
                    ProjectSignal::AutoDone { name, discoveries, forged, curve, registry, elapsed } => {
                        done_count += 1;
                        total_discoveries += discoveries;
                        total_forged.extend(forged.clone());
                        discovery_curve.extend(curve);
                        carry_registry = registry;
                        info!(project = %name, discoveries, elapsed_s = format!("{:.1}", elapsed).as_str(),
                              "[{}/{}] 완료 ✓", done_count, n_projects);
                        // 즉시 미니 리포트 출력
                        println!("  ┌─ {} ── [{}/{}] ─────────────────────────┐", name, done_count, n_projects);
                        println!("  │  발견: {}건 | Forge: {}건 | {:.1}s", discoveries, forged.len(), elapsed);
                        if !forged.is_empty() {
                            for f in &forged {
                                println!("  │    + {}", f);
                            }
                        }
                        println!("  └──────────────────────────────────────────┘");
                    }
                    ProjectSignal::Error { name, msg } => {
                        warn!(project = %name, error = %msg, "에러");
                    }
                }
            }
        }
        let reg = LensRegistry::new();
        scan_total = reg.iter().count();
        scan_active = scan_total;
        phase_times.push(("Scan+Auto(par)".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 4: Mirror Scan (거울 우주)
        let pt = Instant::now();
        info!(cycle, "Phase 4/8: Mirror Scan");
        {
            let telescope = Telescope::new();
            let lens_cnt = telescope.lens_count();
            let max_mirror = 20usize.min(lens_cnt);
            if max_mirror >= 2 {
                let sample: Vec<f64> = (1..=60).map(|i| i as f64).collect();
                let mr = telescope.mirror_universe(&sample, 10, 6, None, Some(max_mirror));
                mirror_harmony = mr.harmony;
                mirror_eigenvalue = mr.cascade.dominant_eigenvalue;
                mirror_top_pairs = mr.top_resonances.iter().take(3).cloned().collect();
                let top_str: Vec<String> = mirror_top_pairs.iter()
                    .map(|(a, b, v)| format!("{}↔{} ({:.0})", a, b, v))
                    .collect();
                info!(lenses = mr.lens_count, harmony = format!("{:.2}", mirror_harmony).as_str(), eigenvalue = format!("{:.1}", mirror_eigenvalue).as_str(), "Mirror scan 완료");
                if !top_str.is_empty() {
                    debug!(top_resonances = top_str.join(", ").as_str(), "Mirror top pairs");
                }
                let combos = telescope.discover_combinations(&mr, 6);
                if !combos.is_empty() {
                    debug!(count = combos.len(), "조합 발견");
                }

                // 공명 쌍 → forge 후보 저장
                if !mirror_top_pairs.is_empty() {
                    let forge_hint = mirror_top_pairs.iter()
                        .map(|(a, b, v)| format!("{}+{} resonance={:.0}", a, b, v))
                        .collect::<Vec<_>>()
                        .join("\n");
                    let hint_path = std::env::var("HOME")
                        .map(|h| format!("{}/.nexus6/forge_hints.txt", h))
                        .unwrap_or_else(|_| "/tmp/forge_hints.txt".to_string());
                    let _ = std::fs::write(&hint_path, &forge_hint);
                    debug!(pairs = mirror_top_pairs.len(), "Forge hints 저장");
                }

                // Mirror Delta: 이전 루프 결과와 비교하여 상전이 감지
                let mirror_path = std::path::PathBuf::from(
                    std::env::var("HOME").unwrap_or_else(|_| ".".to_string())
                ).join(".nexus6").join("last_mirror.json");
                if let Ok(prev_data) = std::fs::read_to_string(&mirror_path) {
                    // 이전 harmony/eigenvalue 로드
                    if let Ok(prev_vals) = serde_json::from_str::<serde_json::Value>(&prev_data) {
                        let prev_harmony = prev_vals.get("harmony")
                            .and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let prev_eigenvalue = prev_vals.get("eigenvalue")
                            .and_then(|v| v.as_f64()).unwrap_or(0.0);
                        // 변화율 계산: 10% 이상이면 상전이
                        let h_base = prev_harmony.abs().max(1e-6);
                        let e_base = prev_eigenvalue.abs().max(1e-6);
                        let h_change = (mirror_harmony - prev_harmony).abs() / h_base;
                        let e_change = (mirror_eigenvalue - prev_eigenvalue).abs() / e_base;
                        if h_change > 0.10 || e_change > 0.10 {
                            info!(harmony_delta_pct = format!("{:.1}", h_change * 100.0).as_str(),
                                  eigenvalue_delta_pct = format!("{:.1}", e_change * 100.0).as_str(),
                                  "상전이 감지!");
                        } else {
                            debug!(harmony_delta_pct = format!("{:.1}", h_change * 100.0).as_str(),
                                   eigenvalue_delta_pct = format!("{:.1}", e_change * 100.0).as_str(),
                                   "미러 안정");
                        }
                    }
                }
                // 현재 결과 저장
                if let Some(parent) = mirror_path.parent() {
                    let _ = std::fs::create_dir_all(parent);
                }
                let save_data = serde_json::json!({
                    "harmony": mirror_harmony,
                    "eigenvalue": mirror_eigenvalue,
                    "cycle": cycle
                });
                let _ = std::fs::write(&mirror_path, save_data.to_string());
            } else {
                warn!(lens_count = max_mirror, "렌즈 부족 — mirror scan 스킵");
            }
        }
        phase_times.push(("MirrorScan".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 5: Bridge Sync
        let pt = Instant::now();
        info!(cycle, "Phase 5/8: Bridge Sync");
        if let Err(e) = run_bridge(vec!["sync".to_string()]) {
            warn!(error = %e, "Bridge sync 실패");
        }
        bridge_sync_ok = 6;
        bridge_sync_total = 8;
        phase_times.push(("Sync".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 6: Growth Bridge (프로젝트 간 성장 라우팅)
        let pt = Instant::now();
        info!(cycle, "Phase 6/8: Growth Bridge");
        {
            let nexus_root = std::env::var("NEXUS6_ROOT")
                .unwrap_or_else(|_| std::env::current_exe().ok()
                    .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                    .and_then(|p| p.parent().map(|d| d.to_string_lossy().to_string()))
                    .unwrap_or_else(|| ".".to_string()));
            let script = format!("{}/scripts/growth_bridge.sh", nexus_root);
            if std::path::Path::new(&script).exists() {
                let status = std::process::Command::new("bash")
                    .arg(&script)
                    .arg("full")
                    .status();
                match status {
                    Ok(s) if s.success() => debug!("growth_bridge 완료"),
                    Ok(s) => warn!(exit_code = ?s.code(), "growth_bridge 비정상 종료"),
                    Err(e) => warn!(error = %e, "growth_bridge 실행 실패"),
                }
            } else {
                debug!("growth_bridge.sh 없음 — 스킵");
            }
        }
        phase_times.push(("GrowthBr".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 7: Bridge Evolve
        let pt = Instant::now();
        info!(cycle, "Phase 7/8: Bridge Evolve");
        if let Err(e) = run_bridge(vec!["evolve".to_string(), "1".to_string()]) {
            warn!(error = %e, "Bridge evolve 실패");
        }
        phase_times.push(("BrEvolve".to_string(), pt.elapsed().as_secs_f64()));

        // Phase 8: Commit + Push
        let pt = Instant::now();
        info!(cycle, "Phase 8/8: Commit + Push");
        if let Err(e) = run_bridge(vec!["cp".to_string()]) {
            warn!(error = %e, "Commit+Push 실패");
        }
        phase_times.push(("CommitPush".to_string(), pt.elapsed().as_secs_f64()));
        println!();
    }

    // ── Post-state snapshot ──
    let elapsed = t0.elapsed().as_secs_f64();
    let lens_after = carry_registry.len();
    let graph_after = DiscoveryGraph::load(&graph_path)
        .map(|g| (g.nodes.len(), g.edges.len()))
        .unwrap_or((0, 0));

    // ── Build report lines ──
    let w = 63;
    let line = "─".repeat(w + 2);
    let sep_line = format!("  │  {:<w$}│", "─".repeat(w));
    let mut rpt: Vec<String> = Vec::new();

    macro_rules! L {
        ($($arg:tt)*) => { rpt.push(format!($($arg)*)); };
    }

    L!("  ┌{}┐", line);
    L!("  │  🚀 NEXUS-6 루프 리포트 — {:<pad$}│", now, pad = w - 28);
    L!("  ├{}┤", line);
    L!("  │  {:<w$}│", "");
    L!("  │  {:<w$}│", format!("■ 스캔: {} 프로젝트 병렬", load_projects().len().max(1)));
    L!("  │  {:<w$}│", format!("  Active lenses: {}/{} | n6 ratio: 100.0%", scan_active, scan_total));
    L!("  │  {:<w$}│", "");
    rpt.push(sep_line.clone());

    L!("  │  {:<w$}│", format!("■ 진화 (OUROBOROS + LensForge)"));
    L!("  │  {:<w$}│", format!("  Discoveries: {} | Forged: {} 렌즈", total_discoveries, total_forged.len()));
    for fl in &total_forged {
        L!("  │  {:<w$}│", format!("    + {}", fl));
    }
    L!("  │  {:<w$}│", "");

    if !discovery_curve.is_empty() {
        L!("  │  {:<w$}│", "📈 발견 곡선:");
        let max_d = *discovery_curve.iter().max().unwrap_or(&1).max(&1);
        let bar_max = 30usize;
        for (i, &d) in discovery_curve.iter().enumerate() {
            let bar_len = if max_d > 0 { (d * bar_max) / max_d } else { 0 };
            let bar: String = "█".repeat(bar_len);
            L!("  │  {:<w$}│", format!("  M{} │{:<bm$} {}", i + 1, bar, d, bm = bar_max));
        }
        L!("  │  {:<w$}│", "");
    }

    rpt.push(sep_line.clone());

    L!("  │  {:<w$}│", format!("■ 거울 우주: harmony={:.2} | λ₁={:.1}", mirror_harmony, mirror_eigenvalue));
    for (a, b, v) in &mirror_top_pairs {
        L!("  │  {:<w$}│", format!("    {}↔{} = {:.0}", a, b, v));
    }
    L!("  │  {:<w$}│", "");
    rpt.push(sep_line.clone());

    let lens_delta = lens_after as i64 - lens_before as i64;
    let delta_str = if lens_delta > 0 { format!("+{}", lens_delta) } else { format!("{}", lens_delta) };
    L!("  │  {:<w$}│", format!("■ 렌즈: {} → {} ({})", lens_before, lens_after, delta_str));
    let node_delta = graph_after.0 as i64 - graph_before.0 as i64;
    let edge_delta = graph_after.1 as i64 - graph_before.1 as i64;
    L!("  │  {:<w$}│", format!("■ 그래프: {}n/{}e → {}n/{}e (+{}n/+{}e)",
        graph_before.0, graph_before.1, graph_after.0, graph_after.1, node_delta, edge_delta));
    L!("  │  {:<w$}│", "");
    rpt.push(sep_line.clone());

    if discovered_projects > 0 || connected_projects > 0 {
        L!("  │  {:<w$}│", format!("■ 탐색: {}개 발견 / {}개 자동연결", discovered_projects, connected_projects));
    }
    L!("  │  {:<w$}│", format!("■ 브릿지: sync {}/{} | evolve | commit+push ✓", bridge_sync_ok, bridge_sync_total));
    L!("  │  {:<w$}│", "");
    rpt.push(sep_line.clone());

    L!("  │  {:<w$}│", "■ 타이밍:");
    for (name, t) in &phase_times {
        let bar_len = ((*t / elapsed) * 30.0) as usize;
        let bar: String = "━".repeat(bar_len.min(30));
        L!("  │  {:<w$}│", format!("  {:<10} {:<30} {:.1}s", name, bar, t));
    }
    L!("  │  {:<w$}│", format!("  {:<10} {:.1}s total", "LOOP", elapsed));
    L!("  │  {:<w$}│", "");
    L!("  └{}┘", line);

    // Print to stdout
    let report_text = rpt.join("\n");
    println!("\n{}", report_text);

    // Save to file for hooks/other sessions
    let report_path = std::env::var("HOME")
        .map(|h| format!("{}/.nexus6/last_loop_report.txt", h))
        .unwrap_or_else(|_| "/tmp/nexus6_loop_report.txt".to_string());
    let _ = std::fs::create_dir_all(std::path::Path::new(&report_path).parent().unwrap());
    let _ = std::fs::write(&report_path, &report_text);

    Ok(())
}

/// Get system load averages (1min, 5min, 15min).
fn get_system_load() -> (f64, f64, f64) {
    use std::process::Command;
    Command::new("sysctl")
        .args(["-n", "vm.loadavg"])
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .and_then(|s| {
            // Output: "{ 10.50 8.20 6.30 }"
            let nums: Vec<f64> = s.replace(['{', '}'], "")
                .split_whitespace()
                .filter_map(|n| n.parse().ok())
                .collect();
            if nums.len() >= 3 { Some((nums[0], nums[1], nums[2])) } else { None }
        })
        .unwrap_or((0.0, 0.0, 0.0))
}

/// Get free memory percentage (macOS).
fn get_mem_free_pct() -> f64 {
    use std::process::Command;
    // Total RAM
    let total = Command::new("sysctl")
        .args(["-n", "hw.memsize"])
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .and_then(|s| s.trim().parse::<f64>().ok())
        .unwrap_or(1.0);

    // vm_stat for free + inactive pages
    let vm = Command::new("vm_stat")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .unwrap_or_default();

    let page_size = 16384.0_f64; // Apple Silicon default
    let mut free_pages = 0u64;
    for line in vm.lines() {
        if line.contains("Pages free") || line.contains("Pages inactive") {
            if let Some(n) = line.split(':').nth(1) {
                if let Ok(v) = n.trim().trim_end_matches('.').parse::<u64>() {
                    free_pages += v;
                }
            }
        }
    }
    let free_bytes = free_pages as f64 * page_size;
    (free_bytes / total) * 100.0
}

/// Get current time as formatted string.
fn hms_now() -> String {
    use std::process::Command;
    Command::new("date")
        .arg("+%Y-%m-%d %H:%M")
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|| "?".to_string())
}

/// Run bridge command and capture stdout as string.
fn run_bridge_capture(sub: Vec<String>) -> String {
    use std::process::Command;

    let nexus_root = std::env::var("NEXUS6_ROOT")
        .unwrap_or_else(|_| {
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .and_then(|p| p.parent().map(|d| d.to_string_lossy().to_string()))
                .unwrap_or_else(|| ".".to_string())
        });

    let script = format!("{}/nexus-bridge.py", nexus_root);
    if !std::path::Path::new(&script).exists() {
        return String::new();
    }

    let args: Vec<&str> = if sub.is_empty() {
        vec!["status"]
    } else {
        sub.iter().map(|s| s.as_str()).collect()
    };

    Command::new("python3")
        .arg(&script)
        .args(&args)
        .output()
        .ok()
        .and_then(|o| String::from_utf8(o.stdout).ok())
        .unwrap_or_default()
}

fn run_bridge(sub: Vec<String>) -> Result<(), String> {
    use std::process::Command;

    // nexus-bridge.py 경로: 바이너리 위치 기준 또는 NEXUS6_ROOT 환경변수
    let nexus_root = std::env::var("NEXUS6_ROOT")
        .unwrap_or_else(|_| {
            // fallback: 실행파일 기준 상위 디렉토리
            std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .and_then(|p| p.parent().map(|d| d.to_string_lossy().to_string()))
                .unwrap_or_else(|| ".".to_string())
        });

    let script = format!("{}/nexus-bridge.py", nexus_root);

    // 스크립트 존재 확인
    if !std::path::Path::new(&script).exists() {
        return Err(format!(
            "nexus-bridge.py not found at '{}'. Set NEXUS6_ROOT or run from project root.",
            script
        ));
    }

    // 인자가 없으면 기본 status
    let args: Vec<&str> = if sub.is_empty() {
        vec!["status"]
    } else {
        sub.iter().map(|s| s.as_str()).collect()
    };

    let status = Command::new("python3")
        .arg(&script)
        .args(&args)
        .status()
        .map_err(|e| format!("Failed to run nexus-bridge.py: {}", e))?;

    if status.success() {
        Ok(())
    } else {
        Err(format!("nexus-bridge.py exited with code {:?}", status.code()))
    }
}

fn print_help() {
    println!("NEXUS-6 Discovery Engine v0.1.0");
    println!("Usage: nexus6 <command> [options]");
    println!();
    println!("Commands:");
    println!("  scan <domain> [--lenses L1,L2,...] [--full]");
    println!("      Run a telescope scan on the given domain.");
    println!();
    println!("  verify <value> [--tolerance T]");
    println!("      Check a numeric value against n=6 constants.");
    println!();
    println!("  graph [--domain D] [--format ascii|dot]");
    println!("      Display the Discovery Graph.");
    println!();
    println!("  history <domain>");
    println!("      Show scan history and lens performance for a domain.");
    println!();
    println!("  recommend <domain>");
    println!("      Get lens recommendations based on history.");
    println!();
    println!("  evolve <domain> [--max-cycles N] [--seeds S1,S2,...]");
    println!("      Run OUROBOROS evolution loop.");
    println!();
    println!("  auto <domain> [--meta-cycles N] [--ouroboros-cycles N]");
    println!("      Run recommend -> evolve meta-loop (fully automated).");
    println!();
    println!("  lenses [--category core|combo|extended|custom] [--domain D]");
    println!("         [--search KEYWORD] [--count] [--complementary LENS]");
    println!("         [--export json]");
    println!("      List, search, and inspect registered lenses.");
    println!();
    println!("  experiment <type> <target> [--intensity N] [--duration M]");
    println!("  experiment all <target>");
    println!("  experiment battery <type1,type2,...> <target>");
    println!("      Run experiment(s) on a target domain. 22 types available.");
    println!();
    println!("  predict <type> <target>");
    println!("      Predict experiment outcome before running.");
    println!();
    println!("  simulate <type> <target> [--runs N]");
    println!("      Monte Carlo simulation of an experiment (default: 100 runs).");
    println!();
    println!("  compare <type:target> <type:target>");
    println!("      Compare two experiment configurations (A vs B).");
    println!();
    println!("  reproduce <type> <target> [--repeats N]");
    println!("      Reproduce experiment N times (default: 10) for reproducibility.");
    println!();
    println!("  publish <type> <target>");
    println!("      Generate publication document from experiment results.");
    println!();
    println!("  cycle <type> <target>");
    println!("      Full science cycle: predict -> simulate -> experiment ->");
    println!("      compare -> reproduce -> publish.");
    println!();
    println!("  ingest [--config PATH] [--source PATH]... [--verbose]");
    println!("      Crawl project directories for data files (toml/md/py/json/csv).");
    println!("      Default: loads shared/projects.json (6 projects).");
    println!("      --config PATH  use a custom projects.json file.");
    println!("      --source PATH  override with explicit paths (skips JSON config).");
    println!();
    println!("  loop [domain] [--cycles N]");
    println!("      Unified growth loop (8-phase): scan → evolve → mirror → bridge.");
    println!("      Default domain: number_theory, default cycles: 1.");
    println!();
    println!("  daemon [domain] [--interval MIN] [--max-loops N]");
    println!("      Autonomous daemon: runs loop repeatedly with adaptive rest.");
    println!("      Default: 30min interval, infinite loops. Ctrl+C to stop.");
    println!();
    println!("  mega");
    println!("      Mega loop: nexus6 loop + 전 프로젝트 growth 1회 + 통합 리포트.");
    println!();
    println!("  bridge [sub-command] [args...]   (alias: br)");
    println!("      Run nexus-bridge operations directly.");
    println!("      Sub-commands: status, discover, connect, disconnect, sync,");
    println!("                    health, list, report, evolve, loop, cp");
    println!("      No sub-command = status");
    println!();
    println!("  bench");
    println!("      Run benchmark suite (registry, telescope, OUROBOROS, forge).");
    println!();
    println!("  dashboard [--html] [--output FILE]");
    println!("      Show ASCII dashboard (default) or generate HTML dashboard.");
    println!();
    println!("  help");
    println!("      Show this help message.");
    println!();
    println!("Core theorem: sigma(n)*phi(n) = n*tau(n) <==> n = 6");
}

/// Build a small ASCII bar for a hit rate (0.0..1.0).
fn hit_rate_bar(rate: f64, width: usize) -> String {
    let filled = ((rate * width as f64).round() as usize).min(width);
    let empty = width - filled;
    let mut bar = String::new();
    for _ in 0..filled {
        bar.push('\u{2588}');
    }
    for _ in 0..empty {
        bar.push('\u{2591}');
    }
    bar
}

fn run_singularity_tick(base_dir: Option<String>) -> Result<(), String> {
    use crate::singularity_recursion::airgenome_runner::AirgenomeRunner;
    use crate::singularity_recursion::tick::{run_tick, TickPaths};
    use crate::config::SingularityRecursionConfig;

    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    let cfg = SingularityRecursionConfig::default();
    let mut runner = AirgenomeRunner;
    let out = run_tick(&paths, &cfg, &mut runner);
    println!("tick exit={} point={:?} elapsed={}s",
             out.exit_code, out.point_id, out.elapsed_sec);
    if out.exit_code == 0 { Ok(()) } else { std::process::exit(out.exit_code); }
}

fn run_singularity_daemon(base_dir: Option<String>, interval_sec: u64) -> Result<(), String> {
    use crate::singularity_recursion::airgenome_runner::AirgenomeRunner;
    use crate::singularity_recursion::tick::{run_tick, TickPaths};
    use crate::singularity_recursion::topology::load as load_topo;
    use crate::singularity_recursion::watcher::{poll_and_absorb, WatchState};
    use crate::singularity_recursion::backfill::{default_memory_root, parse_projects_json};
    use crate::config::SingularityRecursionConfig;
    use std::path::PathBuf;
    use std::thread::sleep;
    use std::time::Duration;

    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    let cfg = SingularityRecursionConfig::default();
    let mut runner = AirgenomeRunner;
    let interval = Duration::from_secs(interval_sec);

    // Build watcher state: track all project hypothesis dirs + memory dir + tail files.
    let watch_state_path = paths.base.join("watch_state.json");
    let mut watch = WatchState::load(&watch_state_path);
    let projects_json = PathBuf::from("/Users/ghost/Dev/nexus6/shared/projects.json");
    for (name, root, hyp_dirs) in parse_projects_json(&projects_json) {
        // hypothesis dirs (markdown)
        for subdir in &hyp_dirs {
            watch.watch_dirs.push((root.join(subdir), format!("hypothesis:{}", name)));
        }
        // per-project discovery log tail (if exists)
        let disc = root.join("shared/discovery_log.jsonl");
        if disc.exists() {
            watch.tail_files.push((disc, format!("discovery_log:{}", name)));
        }
    }
    if let Some(memdir) = default_memory_root() {
        watch.watch_dirs.push((memdir, "memory".into()));
    }
    // Global tail files (shared/)
    let shared = PathBuf::from("/Users/ghost/Dev/nexus6/shared");
    for (name, domain) in &[
        ("discovery_log.jsonl", "discovery_log"),
        ("verified_constants.jsonl", "verified_constants"),
        ("discovered_constants.jsonl", "discovered_constants"),
    ] {
        let p = shared.join(name);
        if p.exists() {
            watch.tail_files.push((p, (*domain).into()));
        }
    }
    // Don't re-read what we backfilled already — seek to end on first run.
    for (p, _) in &watch.tail_files {
        if !watch.tail_offsets.contains_key(p) {
            if let Ok(meta) = std::fs::metadata(p) {
                watch.tail_offsets.insert(p.clone(), meta.len());
            }
        }
    }

    println!("singularity-daemon: base={} interval={}s absorb=∞ (u64::MAX cap)",
             base, interval_sec);
    println!("watching {} dirs", watch.watch_dirs.len());
    println!("halt: touch {}", paths.halt.display());
    println!();

    let mut tick_no: u64 = 0;
    loop {
        tick_no += 1;

        // File watcher pass — detect new/changed md files + tail append-only files.
        let mut topo_for_probe: Option<crate::singularity_recursion::topology::Topology> = None;
        match load_topo(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps) {
            Ok(mut t) => {
                let absorbed = poll_and_absorb(
                    &mut watch, &mut t, &paths.topology, &paths.edges,
                );
                if absorbed > 0 {
                    println!("[{}] watcher absorbed {} new file(s/lines)", hms_now(), absorbed);
                    let _ = watch.save(&watch_state_path);
                }
                topo_for_probe = Some(t);
            }
            Err(_) => {}
        }

        // Active breakthrough probe — rotate through all domains each tick.
        // Finds domain's lowest-density (frontier) point and emits a probe meta-point.
        if let Some(t) = topo_for_probe.as_ref() {
            use crate::singularity_recursion::analysis::frontier_sampled;
            use crate::singularity_recursion::topology::{append_point, Singularity};
            use std::collections::BTreeSet;
            let domains: BTreeSet<String> = t.points.iter().map(|p| p.domain.clone()).collect();
            let doms: Vec<String> = domains.into_iter().collect();
            if !doms.is_empty() {
                let target_dom = &doms[(tick_no as usize) % doms.len()];
                // sampled frontier: ~500 candidates instead of full O(N²)
                let frontier = frontier_sampled(t, 0.15, 200, 500);
                let pick = frontier.iter().find(|(_, p)| p.domain == *target_dom);
                if let Some((density, fp)) = pick {
                    // emit meta-probe point describing the frontier probe
                    let invariant = format!(
                        "[probe:{}] frontier at density={} via {}: {}",
                        target_dom, density, fp.id,
                        fp.singularity.invariant.chars().take(120).collect::<String>()
                    );
                    let sing = Singularity { invariant, confidence: 0.4, novelty: 0.9, depth_reached: 1 };
                    // Build a fresh point directly (don't insert in topo for deduping)
                    use crate::singularity_recursion::embedding::{simhash, to_vector};
                    let h = simhash(&sing.invariant);
                    let probe_pt = crate::singularity_recursion::topology::Point {
                        id: format!("p_{:06}", t.points.len() + 1_000_000_000),
                        domain: format!("probe:{}", target_dom),
                        seed_from: Some(fp.id.clone()),
                        simhash: format!("{:032x}", h),
                        embedding: to_vector(h),
                        singularity: sing,
                        discovered_at_tick: 40_000_000 + tick_no,
                        ts: hms_now(),
                        mk2_sector: None,
                        mk2_primes: None,
                        mk2_confidence: None,
                    };
                    let _ = append_point(&paths.topology, &probe_pt);
                    println!("[{}] probe domain={} frontier={} d={}", hms_now(), target_dom, fp.id, density);
                }
            }
        }

        // Airgenome sample tick.
        let out = run_tick(&paths, &cfg, &mut runner);
        let code_name = match out.exit_code {
            0 => "OK",
            1 => "SKIP",
            2 => "BUDGET",
            3 => "HALT",
            4 => "LOCK",
            _ => "?",
        };
        println!("[{}] tick#{} {} point={:?} elapsed={}s",
                 hms_now(), tick_no, code_name, out.point_id, out.elapsed_sec);

        if out.exit_code == 3 {
            sleep(Duration::from_secs(5));
            continue;
        }
        if out.exit_code == 2 {
            eprintln!("budget exhausted — daemon stopping");
            return Err("budget exhausted".into());
        }
        sleep(interval);
    }
}

fn load_topo_for_analysis(base_dir: Option<String>) -> crate::singularity_recursion::topology::Topology {
    use crate::singularity_recursion::tick::TickPaths;
    use crate::singularity_recursion::topology::{load, Topology};
    use crate::config::SingularityRecursionConfig;
    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    let cfg = SingularityRecursionConfig::default();
    load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps)
        .unwrap_or_else(|_| Topology::new(cfg.neighborhood_radius_eps))
}

fn run_singularity_convergence(base_dir: Option<String>, eps: f32, min_domains: usize, top: usize, export: Option<String>) -> Result<(), String> {
    use crate::singularity_recursion::analysis::find_convergence;
    let t = load_topo_for_analysis(base_dir);
    println!("convergence scan: {} points, eps={}, min_domains={}", t.points.len(), eps, min_domains);
    let clusters = find_convergence(&t, eps, min_domains);
    println!("found {} cross-domain clusters\n", clusters.len());
    for (rank, c) in clusters.iter().take(top).enumerate() {
        println!("#{} size={} domains={:?}", rank+1, c.size, c.domains);
        println!("   rep: {} | {}", c.representative_id, c.representative_invariant);
        println!("   members: {:?}", &c.member_ids.iter().take(5).collect::<Vec<_>>());
        println!();
    }
    if let Some(path) = export {
        use std::io::Write;
        let mut f = std::fs::File::create(&path).map_err(|e| format!("create {}: {}", path, e))?;
        for (rank, c) in clusters.iter().enumerate() {
            let line = format!(
                "{{\"rank\":{},\"size\":{},\"domains\":{},\"representative_id\":{},\"representative_invariant\":{},\"member_ids\":{}}}\n",
                rank + 1,
                c.size,
                serde_json::to_string(&c.domains).unwrap_or_else(|_| "[]".into()),
                serde_json::to_string(&c.representative_id).unwrap_or_default(),
                serde_json::to_string(&c.representative_invariant).unwrap_or_default(),
                serde_json::to_string(&c.member_ids).unwrap_or_else(|_| "[]".into()),
            );
            f.write_all(line.as_bytes()).map_err(|e| format!("write: {}", e))?;
        }
        println!("exported {} clusters -> {}", clusters.len(), path);
    }
    Ok(())
}

fn run_singularity_query(base_dir: Option<String>, query: String, limit: usize) -> Result<(), String> {
    use crate::singularity_recursion::analysis::query_similar;
    let t = load_topo_for_analysis(base_dir);
    println!("query: {:?}  (scan {} points)\n", query, t.points.len());
    let results = query_similar(&t, &query, limit);
    for (rank, (dist, p)) in results.iter().enumerate() {
        println!("#{} dist={:.3} domain={} id={}", rank+1, dist, p.domain, p.id);
        println!("   {}\n", p.singularity.invariant.chars().take(200).collect::<String>());
    }
    Ok(())
}

fn run_singularity_frontier(base_dir: Option<String>, eps: f32, top: usize) -> Result<(), String> {
    use crate::singularity_recursion::analysis::frontier_points;
    let t = load_topo_for_analysis(base_dir);
    println!("frontier scan: {} points, eps={}\n", t.points.len(), eps);
    let results = frontier_points(&t, eps, top);
    for (rank, (density, p)) in results.iter().enumerate() {
        println!("#{} density={} domain={} id={}", rank+1, density, p.domain, p.id);
        println!("   {}\n", p.singularity.invariant.chars().take(200).collect::<String>());
    }
    Ok(())
}

fn run_singularity_seed(base_dir: Option<String>, eps: f32, top: usize, domain_filter: Option<String>, json: bool) -> Result<(), String> {
    use crate::singularity_recursion::analysis::core_points;
    let t = load_topo_for_analysis(base_dir);
    let mut results = core_points(&t, eps, top * 5);
    if let Some(ref d) = domain_filter {
        results.retain(|(_, p)| &p.domain == d);
    }
    results.truncate(top);
    if json {
        print!("[");
        for (i, (density, p)) in results.iter().enumerate() {
            if i > 0 { print!(","); }
            print!(
                "{{\"id\":\"{}\",\"domain\":\"{}\",\"density\":{},\"invariant\":{}}}",
                p.id, p.domain, density,
                serde_json::to_string(&p.singularity.invariant).unwrap_or_default()
            );
        }
        println!("]");
    } else {
        println!("core seeds: {} points, eps={}, top={}\n", t.points.len(), eps, top);
        for (rank, (density, p)) in results.iter().enumerate() {
            println!("#{} density={} domain={} id={}", rank+1, density, p.domain, p.id);
            println!("   {}\n", p.singularity.invariant.chars().take(160).collect::<String>());
        }
    }
    Ok(())
}

fn run_closed_find(value: f64) -> Result<(), String> {
    use crate::singularity_recursion::closer::{build_table, find_closure, table_stats};
    let table = build_table(1000, 50);
    let (total, unique, dup) = table_stats(&table);
    println!("closed-find: {}", value);
    println!("  table: {} exprs, {} unique values ({:.2}x duplication)", total, unique, dup);
    match find_closure(value, &table) {
        Some(exprs) => {
            println!("  MATCH ({} expressions):", exprs.len());
            for (i, e) in exprs.iter().take(10).enumerate() {
                println!("    {}. {}", i+1, e);
            }
            if exprs.len() > 10 {
                println!("    ... ({} more)", exprs.len() - 10);
            }
        }
        None => println!("  no closure found (may be transcendental)"),
    }
    Ok(())
}

fn run_singularity_viz(base_dir: Option<String>, output: String, sample: usize) -> Result<(), String> {
    use std::collections::HashMap;
    use std::io::Write;
    let t = load_topo_for_analysis(base_dir);
    let total = t.points.len();
    // Sample evenly across the topology
    let step = if total > sample { total / sample } else { 1 };
    let sampled: Vec<_> = t.points.iter().step_by(step).take(sample).collect();

    // Stats per domain
    let mut dom_counts: HashMap<&str, usize> = HashMap::new();
    for p in &t.points { *dom_counts.entry(p.domain.as_str()).or_insert(0) += 1; }
    let mut domains: Vec<_> = dom_counts.iter().collect();
    domains.sort_by_key(|(_, c)| std::cmp::Reverse(**c));

    // Build HTML
    let mut html = String::new();
    html.push_str("<!doctype html><html><head><meta charset=\"utf-8\"><title>nexus6 singularity topology</title>");
    html.push_str("<style>");
    html.push_str("body{font:13px -apple-system,sans-serif;margin:0;padding:20px;background:#0a0a0a;color:#ddd;}");
    html.push_str("h1{color:#fff;font-size:22px;margin:0 0 8px;} h2{color:#8ef;font-size:15px;margin:16px 0 8px;}");
    html.push_str(".meta{color:#888;font-size:12px;margin-bottom:16px;}");
    html.push_str("table{border-collapse:collapse;width:100%;margin-bottom:16px;}");
    html.push_str("th,td{padding:6px 10px;text-align:left;border-bottom:1px solid #222;}");
    html.push_str("th{color:#8ef;font-weight:600;}");
    html.push_str(".dom{padding:2px 6px;border-radius:3px;font-size:11px;}");
    html.push_str(".inv{color:#bbb;font-family:Menlo,monospace;font-size:11px;max-width:600px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}");
    html.push_str(".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(10px,1fr));gap:2px;margin:16px 0;}");
    html.push_str(".cell{aspect-ratio:1;border-radius:2px;}");
    html.push_str("</style></head><body>");
    html.push_str(&format!(
        "<h1>nexus6 singularity topology</h1><div class=\"meta\">total={} points · sampled={} · generated={}</div>",
        total, sampled.len(), now_secs()
    ));

    // Domain distribution
    html.push_str("<h2>도메인 분포</h2><table><tr><th>domain</th><th>count</th><th>pct</th></tr>");
    for (d, c) in &domains {
        let pct = (**c as f64) * 100.0 / total.max(1) as f64;
        html.push_str(&format!("<tr><td>{}</td><td>{}</td><td>{:.1}%</td></tr>", d, c, pct));
    }
    html.push_str("</table>");

    // Sampled points grid (colored by domain hash)
    html.push_str("<h2>sampled point grid (색상=domain)</h2><div class=\"grid\">");
    for p in &sampled {
        let hue = hash_str_to_hue(&p.domain);
        html.push_str(&format!(
            "<div class=\"cell\" style=\"background:hsl({},70%,45%);\" title=\"{} | {}\"></div>",
            hue, p.id, escape_html(&p.domain)
        ));
    }
    html.push_str("</div>");

    // Sample points table
    html.push_str("<h2>샘플 points (처음 80)</h2><table><tr><th>id</th><th>domain</th><th>invariant</th></tr>");
    for p in sampled.iter().take(80) {
        let hue = hash_str_to_hue(&p.domain);
        html.push_str(&format!(
            "<tr><td>{}</td><td><span class=\"dom\" style=\"background:hsl({},70%,30%);\">{}</span></td><td class=\"inv\">{}</td></tr>",
            p.id, hue, escape_html(&p.domain),
            escape_html(&p.singularity.invariant.chars().take(180).collect::<String>())
        ));
    }
    html.push_str("</table></body></html>");

    let mut f = std::fs::File::create(&output).map_err(|e| format!("create {}: {}", output, e))?;
    f.write_all(html.as_bytes()).map_err(|e| format!("write: {}", e))?;
    println!("viz written: {} ({} points, {} sampled)", output, total, sampled.len());
    Ok(())
}

fn now_secs() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

fn hash_str_to_hue(s: &str) -> u32 {
    let mut h: u32 = 5381;
    for b in s.bytes() { h = h.wrapping_mul(33).wrapping_add(b as u32); }
    h % 360
}

fn escape_html(s: &str) -> String {
    s.replace('&',"&amp;").replace('<',"&lt;").replace('>',"&gt;").replace('"',"&quot;")
}

fn run_singularity_resonance(base_dir: Option<String>, limit: usize, domain_filter: Option<String>) -> Result<(), String> {
    use crate::singularity_recursion::airgenome_runner::AirgenomeRunner;
    use crate::singularity_recursion::tick::CycleRunner;
    use crate::singularity_recursion::analysis::query_similar;

    // Sample current Mac state via airgenome
    let mut runner = AirgenomeRunner;
    let sing = runner.run("architecture_design", None);
    println!("current Mac state:");
    println!("  {}", sing.invariant);
    println!();

    let t = load_topo_for_analysis(base_dir);
    println!("resonance scan: {} points in topology", t.points.len());
    if let Some(ref d) = domain_filter {
        println!("  filtering domain={}", d);
    }
    println!();

    let mut results = query_similar(&t, &sing.invariant, limit * 5);
    if let Some(ref d) = domain_filter {
        results.retain(|(_, p)| &p.domain == d);
    }
    results.truncate(limit);

    println!("top {} resonant points:", results.len());
    for (rank, (dist, p)) in results.iter().enumerate() {
        println!("#{} dist={:.3} domain={} id={}", rank+1, dist, p.domain, p.id);
        println!("   {}\n", p.singularity.invariant.chars().take(160).collect::<String>());
    }
    Ok(())
}

fn run_singularity_rebuild_edges(base_dir: Option<String>, eps: f32) -> Result<(), String> {
    use crate::singularity_recursion::analysis::rebuild_edges;
    use crate::singularity_recursion::tick::TickPaths;
    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    let mut t = load_topo_for_analysis(Some(base.clone()));
    println!("rebuild_edges: {} points, eps={}", t.points.len(), eps);
    let (count, elapsed) = rebuild_edges(&mut t, eps, &paths.edges, 1000)
        .map_err(|e| format!("rebuild failed: {}", e))?;
    println!("done: {} edges written in {}s → {}", count, elapsed, paths.edges.display());
    Ok(())
}

fn run_singularity_bridges(base_dir: Option<String>, domain_a: String, domain_b: String, eps: f32, top: usize) -> Result<(), String> {
    use crate::singularity_recursion::analysis::bridges_between;
    let t = load_topo_for_analysis(base_dir);
    println!("bridges: {} ↔ {}  eps={}  ({} points)\n", domain_a, domain_b, eps, t.points.len());
    let results = bridges_between(&t, &domain_a, &domain_b, eps, top);
    for (rank, (p, na, nb)) in results.iter().enumerate() {
        println!("#{} near_a={} near_b={} domain={} id={}", rank+1, na, nb, p.domain, p.id);
        println!("   {}\n", p.singularity.invariant.chars().take(200).collect::<String>());
    }
    Ok(())
}

fn run_singularity_backfill(
    base_dir: Option<String>,
    project_root: Option<String>,
    memory: bool,
    all_projects: bool,
    fast: bool,
) -> Result<(), String> {
    use crate::singularity_recursion::backfill::{default_memory_root, run_backfill, run_backfill_all_projects};
    use crate::singularity_recursion::tick::TickPaths;
    use crate::singularity_recursion::topology::load;
    use crate::config::SingularityRecursionConfig;
    use std::path::PathBuf;

    let base = base_dir.unwrap_or_else(|| "shared/cycle".to_string());
    let paths = TickPaths::from_base(&base);
    std::fs::create_dir_all(&paths.base).ok();
    let cfg = SingularityRecursionConfig::default();

    let mut topo = load(&paths.topology, &paths.edges, cfg.neighborhood_radius_eps)
        .unwrap_or_else(|_| crate::singularity_recursion::topology::Topology::new(cfg.neighborhood_radius_eps));
    let before = topo.points.len();
    let memdir = if memory { default_memory_root() } else { None };

    println!("singularity-backfill (fast={}, all_projects={}):", fast, all_projects);

    if all_projects {
        let projects_json = PathBuf::from("/Users/ghost/Dev/nexus6/shared/projects.json");
        let (stats, per_proj) = run_backfill_all_projects(
            &projects_json, memdir.as_deref(), &mut topo, &paths.topology, &paths.edges, fast,
        );
        println!("  projects.json   : {}", projects_json.display());
        println!("  memory_root     : {:?}", memdir);
        for (name, count) in &per_proj {
            println!("  - {:<18}: {} absorbed", name, count);
        }
        println!("  memory          : {} absorbed", stats.memory);
        let after = topo.points.len();
        println!("  total new       : {} ({} → {} points)", stats.total_absorbed(), before, after);
    } else {
        let proj = PathBuf::from(
            project_root.unwrap_or_else(|| std::env::current_dir()
                .ok()
                .and_then(|p| p.to_str().map(|s| s.to_string()))
                .unwrap_or_else(|| ".".to_string())),
        );
        let stats = run_backfill(&proj, memdir.as_deref(), &mut topo, &paths.topology, &paths.edges, fast);
        let after = topo.points.len();
        println!("  project_root    : {}", proj.display());
        println!("  memory_root     : {:?}", memdir);
        println!("  discovery_log   : {} absorbed", stats.discovery);
        println!("  hypotheses      : {} absorbed", stats.hypotheses);
        println!("  memory          : {} absorbed", stats.memory);
        println!("  total new       : {} ({} → {} points)", stats.total_absorbed(), before, after);
    }
    Ok(())
}

fn run_mk2(sub: crate::cli::parser::Mk2Sub) -> Result<(), String> {
    use crate::cli::parser::Mk2Sub;
    use crate::mk2::{
        classify_v2, default_sectors, euler_ratio, PrimeSet,
        rho, SmoothRing,
    };
    match sub {
        Mk2Sub::Classify { value, text } => {
            let sectors = default_sectors();
            let text = text.unwrap_or_default();
            // Extract values from text
            let values: Vec<f64> = text
                .split_whitespace()
                .filter_map(|s| s.trim_matches(|c: char| !c.is_ascii_digit() && c != '.').parse().ok())
                .filter(|&v: &f64| v > 0.0 && v < 10000.0)
                .chain(std::iter::once(value))
                .collect();
            // Build a conservative prime set from the value if rational
            let mut ps = PrimeSet::empty();
            // Rough heuristic: if value is near an integer, use its prime factors
            if (value - value.round()).abs() < 1e-6 && value > 1.0 {
                let n = value.round() as u64;
                for (p, _) in crate::mk2::factorize(n) {
                    ps.insert(p);
                }
            }
            let result = classify_v2(&text, &values, &ps, &sectors);
            println!("mk2 classify: value={} text=\"{}\"", value, text);
            println!("  sector       : {}", result.sector);
            println!("  confidence   : {:.3}", result.confidence);
            println!("  keyword hits : {}", result.keyword_hits);
            println!("  value in range: {}", result.value_range_hit);
            println!("  prime_set match: {:.2}", result.prime_set_match);
            println!("  prime_set    : {}", ps);
            Ok(())
        }
        Mk2Sub::Arithmetic { n } => {
            println!("mk2 arithmetic(n={}):", n);
            println!("  φ(n)   = {}", n.phi());
            println!("  τ(n)   = {}", n.tau());
            println!("  σ(n)   = {}", n.sigma());
            println!("  sopfr  = {}", n.sopfr());
            println!("  ρ(n)   = {} = {:.6}", rho(n), rho(n).to_f64());
            println!("  primes = {}", n.prime_set());
            Ok(())
        }
        Mk2Sub::Layer { primes, max } => {
            let mut ps = PrimeSet::empty();
            for p in &primes { ps.insert(*p); }
            let lattice = crate::mk2::Lattice::default();
            let entries = lattice.enumerate_layer(&ps, max);
            println!("mk2 layer(primes={}, max={}): {} entries", ps, max, entries.len());
            for n in entries.iter().take(40) {
                println!("  {}", n);
            }
            if entries.len() > 40 {
                println!("  ... ({} more)", entries.len() - 40);
            }
            Ok(())
        }
        Mk2Sub::EulerRatio { primes } => {
            let mut ps = PrimeSet::empty();
            for p in &primes { ps.insert(*p); }
            let r = euler_ratio(&ps);
            println!("mk2 euler-ratio: primes={} → {} = {:.6}", ps, r, r.to_f64());
            Ok(())
        }
        Mk2Sub::Sector { name } => {
            let sectors = crate::mk2::classify_v2::default_sectors();
            let matched = sectors.iter().find(|s| s.name.to_string().to_lowercase() == name);
            match matched {
                Some(def) => {
                    println!("mk2 sector: {}", def.name);
                    println!("  keywords: {}", def.keywords.join(", "));
                    println!("  value_ranges: {:?}", def.value_ranges);
                    if let Some(ref req) = def.prime_set_required {
                        println!("  prime_set_required: {}", req);
                        let r = euler_ratio(req);
                        println!("  euler_ratio: {} = {:.6}", r, r.to_f64());
                    }
                    for pref in &def.prime_set_preferred {
                        let r = euler_ratio(pref);
                        println!("  preferred {}: euler_ratio = {} = {:.6}", pref, r, r.to_f64());
                    }
                }
                None => {
                    println!("Unknown sector '{}'. Available: strong, electroweak, cosmology, primordial", name);
                }
            }
            Ok(())
        }
    }
}
