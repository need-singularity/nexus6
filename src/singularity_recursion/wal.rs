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
