//! Retroactive absorption — ingest past discoveries into the topology.
//!
//! Sources:
//! - `shared/discovery_log.jsonl` — every prior discovery line → 1 point
//! - `docs/hypotheses/**/*.md` — every hypothesis file → 1 point
//! - `~/.claude-claude9/projects/*/memory/*.md` — memory entries → 1 point
//!
//! Each absorbed entry becomes an append-only topology point. Idempotent
//! via simhash dedup: if a point with the same simhash already exists,
//! we skip it rather than duplicating.

use std::collections::HashSet;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};

use super::topology::{append_edge, append_point, Singularity, Topology};

/// How many points were absorbed from each source.
#[derive(Debug, Default, Clone, Copy)]
pub struct BackfillStats {
    pub discovery: usize,
    pub hypotheses: usize,
    pub memory: usize,
    pub skipped_duplicates: usize,
}

impl BackfillStats {
    pub fn total_absorbed(&self) -> usize {
        self.discovery + self.hypotheses + self.memory
    }
}

/// Build a set of existing simhashes for dedup.
fn existing_simhashes(t: &Topology) -> HashSet<String> {
    t.points.iter().map(|p| p.simhash.clone()).collect()
}

fn now_iso() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    format!("{}Z", secs)
}

/// Insert a text as a singularity point if not a dup.
/// When `fast` is true, skip edge computation (O(N) append instead of O(N²)).
fn absorb_text(
    t: &mut Topology,
    seen: &mut HashSet<String>,
    domain: &str,
    text: &str,
    tick: u64,
    topology_path: &Path,
    edges_path: &Path,
    fast: bool,
) -> bool {
    let sing = Singularity {
        invariant: text.to_string(),
        confidence: 0.5,
        novelty: 0.5,
        depth_reached: 1,
    };
    let point = t.make_point(domain, None, sing, tick, &now_iso());
    if seen.contains(&point.simhash) {
        return false;
    }
    seen.insert(point.simhash.clone());
    let point_save = point.clone();
    if fast {
        t.points.push(point);
        let _ = append_point(topology_path, &point_save);
    } else {
        let new_edges = t.insert_point(point, &now_iso());
        let _ = append_point(topology_path, &point_save);
        for e in &new_edges { let _ = append_edge(edges_path, e); }
    }
    true
}

/// Read discovery_log.jsonl and absorb each line.
pub fn backfill_discovery_log(
    log_path: &Path,
    t: &mut Topology,
    seen: &mut HashSet<String>,
    topology_path: &Path,
    edges_path: &Path,
    fast: bool,
) -> usize {
    if !log_path.exists() { return 0; }
    let file = match std::fs::File::open(log_path) {
        Ok(f) => f,
        Err(_) => return 0,
    };
    let mut count = 0;
    let mut tick = 10_000_000u64; // backfill points get high tick numbers
    for line in BufReader::new(file).lines().flatten() {
        let trimmed = line.trim();
        if trimmed.is_empty() { continue; }
        // Use up to 400 chars as invariant text
        let text: String = trimmed.chars().take(400).collect();
        if absorb_text(t, seen, "discovery_log", &text, tick, topology_path, edges_path, fast) {
            count += 1;
            tick += 1;
        }
    }
    count
}

/// Scan a directory for .md files, absorb each (filename + first 400 chars).
pub fn backfill_markdown_dir(
    dir: &Path,
    domain: &str,
    skip_files: &[&str],
    t: &mut Topology,
    seen: &mut HashSet<String>,
    topology_path: &Path,
    edges_path: &Path,
    fast: bool,
) -> usize {
    if !dir.exists() { return 0; }
    let mut count = 0;
    let mut tick = 20_000_000u64;
    walk_md(dir, &mut |path| {
        let fname = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
        if skip_files.contains(&fname) { return; }
        let content = match std::fs::read_to_string(path) {
            Ok(c) => c,
            Err(_) => return,
        };
        let stem = path.file_stem().and_then(|s| s.to_str()).unwrap_or("file");
        // First 400 chars of content, stripped of excessive whitespace
        let body: String = content
            .lines()
            .filter(|l| !l.trim().is_empty())
            .collect::<Vec<_>>()
            .join(" ")
            .chars()
            .take(400)
            .collect();
        let text = format!("[{}] {}", stem, body);
        if absorb_text(t, seen, domain, &text, tick, topology_path, edges_path, fast) {
            count += 1;
            tick += 1;
        }
    });
    count
}

fn walk_md(dir: &Path, visit: &mut dyn FnMut(&Path)) {
    let entries = match std::fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            walk_md(&path, visit);
        } else if path.extension().and_then(|s| s.to_str()) == Some("md") {
            visit(&path);
        }
    }
}

/// Run full backfill against all known sources relative to base_dir.
pub fn run_backfill(
    project_root: &Path,
    memory_root: Option<&Path>,
    t: &mut Topology,
    topology_path: &Path,
    edges_path: &Path,
    fast: bool,
) -> BackfillStats {
    let initial = existing_simhashes(t);
    let mut seen = initial.clone();
    let mut stats = BackfillStats::default();

    // 1. discovery_log.jsonl
    let discovery_log = project_root.join("shared/discovery_log.jsonl");
    stats.discovery = backfill_discovery_log(&discovery_log, t, &mut seen, topology_path, edges_path, fast);

    // 2. docs/hypotheses/**/*.md
    let hypotheses_dir = project_root.join("docs/hypotheses");
    stats.hypotheses = backfill_markdown_dir(
        &hypotheses_dir, "hypothesis", &[], t, &mut seen, topology_path, edges_path, fast,
    );

    // 3. memory (optional path)
    if let Some(memdir) = memory_root {
        stats.memory = backfill_markdown_dir(
            memdir, "memory", &["MEMORY.md"], t, &mut seen, topology_path, edges_path, fast,
        );
    }

    stats.skipped_duplicates = (seen.len() - initial.len()).saturating_sub(stats.total_absorbed());
    stats
}

/// Parse shared/projects.json and return list of (name, root_abs_path, hypothesis_subdirs).
/// Zero-dep JSON parsing — just extracts projects.*.root and projects.*.hypothesis_dirs.
pub fn parse_projects_json(projects_json: &Path) -> Vec<(String, PathBuf, Vec<String>)> {
    let content = match std::fs::read_to_string(projects_json) {
        Ok(c) => c,
        Err(_) => return vec![],
    };
    // Use serde_json since we already depend on it
    let v: serde_json::Value = match serde_json::from_str(&content) {
        Ok(v) => v,
        Err(_) => return vec![],
    };
    let projects = match v.get("projects").and_then(|p| p.as_object()) {
        Some(p) => p,
        None => return vec![],
    };
    // Use parent of projects.json as Dev root (e.g. /Users/ghost/Dev)
    let dev_root = projects_json.parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or_else(|| PathBuf::from("/Users/ghost/Dev"));
    let mut out = Vec::new();
    for (name, cfg) in projects.iter() {
        let root_rel = cfg.get("root").and_then(|r| r.as_str()).unwrap_or(name).to_string();
        let root_abs = dev_root.join(&root_rel);
        let hyp_dirs: Vec<String> = cfg.get("hypothesis_dirs")
            .and_then(|h| h.as_array())
            .map(|arr| arr.iter()
                .filter_map(|s| s.as_str().map(String::from))
                .collect())
            .unwrap_or_default();
        out.push((name.clone(), root_abs, hyp_dirs));
    }
    out
}

/// Run backfill across ALL projects listed in shared/projects.json.
pub fn run_backfill_all_projects(
    projects_json: &Path,
    memory_root: Option<&Path>,
    t: &mut Topology,
    topology_path: &Path,
    edges_path: &Path,
    fast: bool,
) -> (BackfillStats, Vec<(String, usize)>) {
    let initial = existing_simhashes(t);
    let mut seen = initial.clone();
    let mut total = BackfillStats::default();
    let mut per_project: Vec<(String, usize)> = Vec::new();

    let projects = parse_projects_json(projects_json);
    for (name, root, hyp_dirs) in &projects {
        let mut project_count = 0;
        // discovery log
        let disc = root.join("shared/discovery_log.jsonl");
        project_count += backfill_discovery_log(&disc, t, &mut seen, topology_path, edges_path, fast);
        // hypothesis dirs
        for subdir in hyp_dirs {
            let dir = root.join(subdir);
            let domain = format!("hypothesis:{}", name);
            project_count += backfill_markdown_dir(
                &dir, &domain, &[], t, &mut seen, topology_path, edges_path, fast,
            );
        }
        per_project.push((name.clone(), project_count));
        total.hypotheses += project_count;
    }

    // Memory (shared across projects)
    if let Some(memdir) = memory_root {
        total.memory = backfill_markdown_dir(
            memdir, "memory", &["MEMORY.md"], t, &mut seen, topology_path, edges_path, fast,
        );
    }

    total.skipped_duplicates = (seen.len() - initial.len()).saturating_sub(total.total_absorbed());
    (total, per_project)
}

/// Resolve the default memory root for this project, if it exists.
pub fn default_memory_root() -> Option<PathBuf> {
    let home = std::env::var("HOME").ok()?;
    let p = PathBuf::from(home)
        .join(".claude-claude9/projects/-Users-ghost-Dev-nexus6/memory");
    if p.exists() { Some(p) } else { None }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;
    use std::io::Write;

    fn tmp(name: &str) -> PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_backfill_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_dir_all(&p);
        std::fs::create_dir_all(&p).unwrap();
        p
    }

    #[test]
    fn discovery_log_absorb() {
        let d = tmp("disc");
        let log = d.join("discovery_log.jsonl");
        let mut f = std::fs::File::create(&log).unwrap();
        writeln!(f, r#"{{"type":"constant","value":19,"name":"rule_ceiling_num"}}"#).unwrap();
        writeln!(f, r#"{{"type":"constant","value":30,"name":"rule_ceiling_den"}}"#).unwrap();
        drop(f);
        let mut t = Topology::new(0.3);
        let mut seen = HashSet::new();
        let topo_path = d.join("topology.jsonl");
        let edges_path = d.join("edges.jsonl");
        let count = backfill_discovery_log(&log, &mut t, &mut seen, &topo_path, &edges_path, false);
        assert_eq!(count, 2);
        assert_eq!(t.points.len(), 2);
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn markdown_dir_absorb_with_skip() {
        let d = tmp("md");
        std::fs::write(d.join("MEMORY.md"), "index file").unwrap();
        std::fs::write(d.join("hypothesis_a.md"), "first hypothesis body").unwrap();
        std::fs::write(d.join("hypothesis_b.md"), "second hypothesis body").unwrap();
        let mut t = Topology::new(0.3);
        let mut seen = HashSet::new();
        let topo_path = d.join("topology.jsonl");
        let edges_path = d.join("edges.jsonl");
        let count = backfill_markdown_dir(
            &d, "test", &["MEMORY.md"], &mut t, &mut seen, &topo_path, &edges_path, false,
        );
        assert_eq!(count, 2);
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn dedup_same_text() {
        let d = tmp("dedup");
        let log = d.join("log.jsonl");
        let mut f = std::fs::File::create(&log).unwrap();
        writeln!(f, "same line").unwrap();
        writeln!(f, "same line").unwrap();
        writeln!(f, "different line").unwrap();
        drop(f);
        let mut t = Topology::new(0.3);
        let mut seen = HashSet::new();
        let topo_path = d.join("topology.jsonl");
        let edges_path = d.join("edges.jsonl");
        let count = backfill_discovery_log(&log, &mut t, &mut seen, &topo_path, &edges_path, false);
        assert_eq!(count, 2, "deduped identical lines");
        std::fs::remove_dir_all(&d).ok();
    }
}
