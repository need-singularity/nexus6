//! File watcher for the daemon loop.
//!
//! Tracks mtimes of hypothesis dirs + memory dir. Each tick the daemon calls
//! `poll_and_absorb` which scans for new/changed files and absorbs them into
//! the topology via the backfill path (fast mode, dedup via simhash).

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::SystemTime;

use super::backfill::backfill_markdown_dir;
use super::topology::Topology;

/// Watch state: file_path → last seen mtime (unix secs).
#[derive(Debug, Default)]
pub struct WatchState {
    pub mtimes: HashMap<PathBuf, u64>,
    pub watch_dirs: Vec<(PathBuf, String)>, // (dir, domain)
}

impl WatchState {
    pub fn new() -> Self { Self::default() }

    /// Load watch state from JSON file.
    pub fn load(path: &Path) -> Self {
        std::fs::read_to_string(path)
            .ok()
            .and_then(|s| {
                // Tiny hand-rolled JSON: {"mtimes":{"path":ts,...}}
                let mut state = WatchState::new();
                for pair in s.split("\"mtimes\":{").nth(1)?.split(",\"") {
                    if let Some((k, v)) = pair.split_once("\":") {
                        let k = k.trim_matches('"').trim_matches('{');
                        let v: u64 = v.trim_matches(|c: char| !c.is_ascii_digit()).parse().ok()?;
                        state.mtimes.insert(PathBuf::from(k), v);
                    }
                }
                Some(state)
            })
            .unwrap_or_default()
    }

    /// Save watch state to JSON file (atomic rename).
    pub fn save(&self, path: &Path) -> std::io::Result<()> {
        use std::io::Write;
        let mut body = String::from("{\"mtimes\":{");
        let mut first = true;
        for (p, ts) in &self.mtimes {
            if !first { body.push(','); }
            first = false;
            body.push_str(&format!("\"{}\":{}", p.display(), ts));
        }
        body.push_str("}}");
        let tmp = path.with_extension("tmp");
        let mut f = std::fs::OpenOptions::new()
            .create(true).write(true).truncate(true).open(&tmp)?;
        f.write_all(body.as_bytes())?;
        f.sync_all()?;
        drop(f);
        std::fs::rename(&tmp, path)?;
        Ok(())
    }
}

fn mtime_unix(path: &Path) -> Option<u64> {
    let meta = std::fs::metadata(path).ok()?;
    let mtime = meta.modified().ok()?;
    mtime.duration_since(SystemTime::UNIX_EPOCH).ok().map(|d| d.as_secs())
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

/// Scan watch_dirs for new/changed files. Absorb them into topology.
/// Returns count of newly absorbed files.
pub fn poll_and_absorb(
    state: &mut WatchState,
    t: &mut Topology,
    topology_path: &Path,
    edges_path: &Path,
) -> usize {
    use std::collections::HashSet;

    // Build seen set from topology (simhash dedup via backfill_markdown_dir).
    let mut seen: HashSet<String> = t.points.iter().map(|p| p.simhash.clone()).collect();

    // Detect changed files across all watch dirs.
    let mut changed_dirs: Vec<(PathBuf, String)> = Vec::new();
    let watch_dirs_snapshot = state.watch_dirs.clone();
    for (dir, domain) in &watch_dirs_snapshot {
        if !dir.exists() { continue; }
        let mut dir_changed = false;
        walk_md(dir, &mut |path| {
            if let Some(new_mt) = mtime_unix(path) {
                let old = state.mtimes.get(path).copied().unwrap_or(0);
                if new_mt > old {
                    dir_changed = true;
                    state.mtimes.insert(path.to_path_buf(), new_mt);
                }
            }
        });
        if dir_changed {
            changed_dirs.push((dir.clone(), domain.clone()));
        }
    }

    // For any changed dir, rescan it (dedup via simhash).
    // Re-scan entire dir is simpler than tracking file-level changes because
    // backfill_markdown_dir already dedups via simhash.
    let mut absorbed = 0;
    for (dir, domain) in &changed_dirs {
        let before = t.points.len();
        backfill_markdown_dir(
            dir, domain, &["MEMORY.md"], t, &mut seen, topology_path, edges_path, true,
        );
        absorbed += t.points.len() - before;
    }
    absorbed
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp_dir(name: &str) -> PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_watch_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_dir_all(&p);
        std::fs::create_dir_all(&p).unwrap();
        p
    }

    #[test]
    fn save_and_load_roundtrip() {
        let d = tmp_dir("rt");
        let state_path = d.join("watch_state.json");
        let mut s = WatchState::new();
        s.mtimes.insert(d.join("a.md"), 1000);
        s.mtimes.insert(d.join("b.md"), 2000);
        s.save(&state_path).unwrap();
        let loaded = WatchState::load(&state_path);
        assert_eq!(loaded.mtimes.len(), 2);
        std::fs::remove_dir_all(&d).ok();
    }

    #[test]
    fn poll_detects_new_file() {
        let d = tmp_dir("poll");
        let hyp_dir = d.join("hypotheses");
        std::fs::create_dir_all(&hyp_dir).unwrap();
        std::fs::write(hyp_dir.join("h1.md"), "first hypothesis").unwrap();

        let mut state = WatchState::new();
        state.watch_dirs.push((hyp_dir.clone(), "hypothesis:test".into()));
        let mut t = Topology::new(0.3);
        let topo_path = d.join("topology.jsonl");
        let edges_path = d.join("edges.jsonl");
        let absorbed = poll_and_absorb(&mut state, &mut t, &topo_path, &edges_path);
        assert_eq!(absorbed, 1);

        // Add new file
        std::fs::write(hyp_dir.join("h2.md"), "second hypothesis").unwrap();
        let absorbed2 = poll_and_absorb(&mut state, &mut t, &topo_path, &edges_path);
        assert_eq!(absorbed2, 1);

        // Re-poll without change
        let absorbed3 = poll_and_absorb(&mut state, &mut t, &topo_path, &edges_path);
        assert_eq!(absorbed3, 0);

        std::fs::remove_dir_all(&d).ok();
    }
}
