use crate::alien_index::AlienIndex;
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HistoryEntry {
    pub timestamp_unix: u64,
    pub d: u32,
    pub r: u8,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AlienIndexRecord {
    pub id: String,
    pub current: AlienIndex,
    pub history: Vec<HistoryEntry>,
    pub promotion_candidate: bool,
    pub promoted_from: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RecordError {
    DepthRegression { from: u32, to: u32 },
}

impl std::fmt::Display for RecordError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RecordError::DepthRegression { from, to } => {
                write!(f, "d is monotonic non-decreasing; cannot go from d={from} to d={to}")
            }
        }
    }
}

impl std::error::Error for RecordError {}

fn now_unix() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0)
}

impl AlienIndexRecord {
    pub fn new<S: Into<String>>(id: S, initial: AlienIndex) -> Self {
        let id = id.into();
        let mut rec = Self {
            id,
            current: initial,
            history: Vec::new(),
            promotion_candidate: initial.r == 10,
            promoted_from: None,
        };
        rec.history.push(HistoryEntry {
            timestamp_unix: now_unix(),
            d: initial.d,
            r: initial.r,
            reason: "initial".to_string(),
        });
        rec
    }

    pub fn update(&mut self, next: AlienIndex, reason: &str) -> Result<(), RecordError> {
        if next.d < self.current.d {
            return Err(RecordError::DepthRegression { from: self.current.d, to: next.d });
        }
        self.current = next;
        self.promotion_candidate = next.r == 10;
        self.history.push(HistoryEntry {
            timestamp_unix: now_unix(),
            d: next.d,
            r: next.r,
            reason: reason.to_string(),
        });
        Ok(())
    }

    /// Creates a child record at `(d+1, 0)` linked to this one.
    /// Clears this record's `promotion_candidate`. Returns `None` if `r != 10`.
    pub fn promote(&mut self) -> Option<AlienIndexRecord> {
        let child_ai = self.current.breakthrough()?;
        self.promotion_candidate = false;
        let child_id = format!("{}→d{}", self.id, child_ai.d);
        let mut child = AlienIndexRecord::new(child_id, child_ai);
        child.promoted_from = Some(self.id.clone());
        Some(child)
    }
}

/// shared/ 디렉토리 경로 (환경변수 NEXUS6_SHARED_DIR 오버라이드 가능).
fn shared_dir() -> std::path::PathBuf {
    std::env::var("NEXUS6_SHARED_DIR")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| std::path::PathBuf::from("shared"))
}

pub fn math_atlas_path() -> std::path::PathBuf {
    std::env::var("NEXUS6_MATH_ATLAS")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("math_atlas.json"))
}

pub fn discovery_log_path() -> std::path::PathBuf {
    std::env::var("NEXUS6_DISCOVERY_LOG")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("discovery_log.jsonl"))
}

pub fn distribution_json_path() -> std::path::PathBuf {
    std::env::var("NEXUS6_AI_DISTRIBUTION")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("alien_index_distribution.json"))
}

pub fn frontier_md_path() -> std::path::PathBuf {
    std::env::var("NEXUS6_AI_FRONTIER")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("alien_index_frontier.md"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alien_index::AlienIndex;

    #[test]
    fn new_record_starts_with_initial_history() {
        let rec = AlienIndexRecord::new("H-AF-001", AlienIndex::new(0, 5));
        assert_eq!(rec.id, "H-AF-001");
        assert_eq!(rec.current, AlienIndex::new(0, 5));
        assert_eq!(rec.history.len(), 1);
        assert!(!rec.promotion_candidate);
        assert_eq!(rec.promoted_from, None);
    }

    #[test]
    fn update_appends_history_and_enforces_d_monotonic() {
        let mut rec = AlienIndexRecord::new("X", AlienIndex::new(0, 5));
        rec.update(AlienIndex::new(0, 7), "7-lens consensus").unwrap();
        assert_eq!(rec.current.r, 7);
        assert_eq!(rec.history.len(), 2);
        assert!(rec.update(AlienIndex::new(0, 6), "reason").is_ok());
        assert!(rec.update(AlienIndex { d: 0, r: 0 }, "fine").is_ok());
        rec.update(AlienIndex::new(2, 3), "jump").unwrap();
        let attempt = rec.update(AlienIndex::new(1, 9), "go back");
        assert!(attempt.is_err());
    }

    #[test]
    fn update_sets_promotion_candidate_at_r_ten() {
        let mut rec = AlienIndexRecord::new("Y", AlienIndex::new(0, 9));
        assert!(!rec.promotion_candidate);
        rec.update(AlienIndex::new(0, 10), "closed form").unwrap();
        assert!(rec.promotion_candidate);
    }

    #[test]
    fn promote_creates_child_record_and_clears_flag() {
        let mut rec = AlienIndexRecord::new("Z", AlienIndex::new(0, 10));
        rec.promotion_candidate = true;
        let child = rec.promote().unwrap();
        assert_eq!(child.current, AlienIndex::new(1, 0));
        assert_eq!(child.promoted_from.as_deref(), Some("Z"));
        assert!(!rec.promotion_candidate);
    }

    #[test]
    fn serde_roundtrip() {
        let rec = AlienIndexRecord::new("H-X-001", AlienIndex::new(1, 3));
        let json = serde_json::to_string(&rec).unwrap();
        let back: AlienIndexRecord = serde_json::from_str(&json).unwrap();
        assert_eq!(back.current, rec.current);
    }
}
