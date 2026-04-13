# Alien Index System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** nexus에 통합 등급 체계 `AlienIndex = (d, r)`를 도입 — 닫힌 수학 천장(r=10)을 넘는 돌파 영역을 `d+1` 승격으로 표현.

**Architecture:** 신규 Rust 모듈 `src/alien_index/` 에 `(d, r)` 데이터 모델과 평가기를 두고, 기존 `verifier::n6_check`/`telescope` 합의/`MATH_ATLAS grade`에서 신호를 수집해 `r`을 산정한다. `CliCommand::AlienIndex` 서브커맨드로 단일/배치/승격/분포 리포트를 제공. `discovery_log.jsonl`과 `verified_constants.jsonl`에 `alien_index` 필드를 추가하는 단일 일회성 Python 마이그레이션 도구 동봉.

**Tech Stack:** Rust (edition 2021, serde, serde_json), no-external CLI parser(기존 스타일), Python 3 (마이그레이션 스크립트), PyO3 0.22 (선택 바인딩).

**Spec:** `docs/superpowers/specs/2026-04-05-alien-index-system-design.md`

---

## File Structure

**Create:**
- `src/alien_index/mod.rs` — 모듈 선언, public API re-export
- `src/alien_index/index.rs` — `AlienIndex { d, r }` 구조체, 불변식, 승격 연산
- `src/alien_index/assess.rs` — 신호 수집기 (n6_match → r, 렌즈 합의 수 → r, grade → r)
- `src/alien_index/record.rs` — `AlienIndexRecord`(history, parent_id, promotion_candidate) + serde
- `src/alien_index/distribution.rs` — (d, r) 히스토그램 + leaderboard
- `src/cli/alien_index_cmd.rs` — CLI 서브커맨드 dispatch 구현
- `tools/migrate_grades_to_alien_index.py` — MATH_ATLAS grade 일괄 → (d, r) 주입
- `tests/alien_index_integration.rs` — 엔드투엔드 통합 테스트

**Modify:**
- `src/lib.rs` — `pub mod alien_index;` 추가
- `src/cli/parser.rs` — `CliCommand::AlienIndex` variant + 파싱
- `src/cli/runner.rs` — dispatch 분기
- `src/python.rs` — PyO3: `alien_index_assess`, `alien_index_distribution` 노출 (feature=python)

---

## Task 1: AlienIndex 코어 구조체

**Files:**
- Create: `src/alien_index/mod.rs`
- Create: `src/alien_index/index.rs`
- Modify: `src/lib.rs:16` (pub mod 추가)

- [ ] **Step 1: 실패 테스트 작성**

`src/alien_index/index.rs`:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_clamps_rank_to_ten() {
        let ai = AlienIndex::new(0, 10);
        assert_eq!(ai.d, 0);
        assert_eq!(ai.r, 10);
    }

    #[test]
    fn new_rejects_rank_above_ten() {
        // rank > 10 must saturate to 10 (not panic)
        let ai = AlienIndex::new(0, 42);
        assert_eq!(ai.r, 10);
    }

    #[test]
    fn can_promote_only_when_r_is_ten() {
        assert!(AlienIndex::new(0, 10).can_promote());
        assert!(!AlienIndex::new(0, 9).can_promote());
        assert!(AlienIndex::new(3, 10).can_promote());
    }

    #[test]
    fn breakthrough_increments_depth_and_resets_rank() {
        let ai = AlienIndex::new(1, 10);
        let next = ai.breakthrough().unwrap();
        assert_eq!(next.d, 2);
        assert_eq!(next.r, 0);
    }

    #[test]
    fn breakthrough_none_when_not_at_ten() {
        assert!(AlienIndex::new(0, 9).breakthrough().is_none());
    }

    #[test]
    fn ordering_d_then_r() {
        assert!(AlienIndex::new(0, 10) < AlienIndex::new(1, 0));
        assert!(AlienIndex::new(0, 5) < AlienIndex::new(0, 6));
    }
}
```

`src/alien_index/mod.rs`:
```rust
//! Alien Index (외계인 지수) — unified grading `(d, r)`.
//! See: docs/superpowers/specs/2026-04-05-alien-index-system-design.md
pub mod index;

pub use index::AlienIndex;
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cargo test --lib alien_index::index`
Expected: FAIL — `AlienIndex` not defined.

- [ ] **Step 3: 최소 구현 작성**

`src/alien_index/index.rs` (앞쪽에 추가):
```rust
use serde::{Deserialize, Serialize};

/// Alien Index: `(d, r)` pair.
///
/// - `d`: cycle depth (how many blowup→absorption cycles have closed on this object)
/// - `r`: rank within depth `d`, clamped to `0..=10`
///
/// `r == 10` at depth `d` means the object has reached the "closed-form ceiling"
/// of that depth and is eligible for breakthrough to `(d+1, 0)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct AlienIndex {
    pub d: u32,
    pub r: u8,
}

impl AlienIndex {
    /// Construct an index, clamping `r` to `0..=10`.
    pub const fn new(d: u32, r: u8) -> Self {
        let r = if r > 10 { 10 } else { r };
        Self { d, r }
    }

    /// True iff `r == 10` (promotion eligible).
    pub const fn can_promote(&self) -> bool {
        self.r == 10
    }

    /// Promote `(d, 10) → (d+1, 0)`. Returns `None` if `r != 10`.
    pub fn breakthrough(&self) -> Option<AlienIndex> {
        if self.can_promote() {
            Some(AlienIndex::new(self.d + 1, 0))
        } else {
            None
        }
    }
}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cargo test --lib alien_index::index`
Expected: 6 PASS.

- [ ] **Step 5: lib.rs에 모듈 등록**

`src/lib.rs` (line 16 부근, `pub mod resource_limit;` 다음):
```rust
pub mod alien_index;
```

Run: `cargo build --lib`
Expected: 성공.

- [ ] **Step 6: 커밋**

```bash
git add src/alien_index/mod.rs src/alien_index/index.rs src/lib.rs
git commit -m "feat(alien_index): core AlienIndex (d, r) struct with breakthrough"
```

---

## Task 2: AlienIndexRecord — history/승격 메타데이터

**Files:**
- Create: `src/alien_index/record.rs`
- Modify: `src/alien_index/mod.rs`

- [ ] **Step 1: 실패 테스트 작성**

`src/alien_index/record.rs`:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::alien_index::AlienIndex;

    #[test]
    fn new_record_starts_empty_history() {
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
        // d decrement must be rejected
        let err = rec.update(AlienIndex::new(0, 6), "reason").is_ok();
        assert!(err, "r can decrease at same d");
        let bad = rec.update(AlienIndex { d: 0, r: 0 }, "fine").is_ok();
        assert!(bad);
        // But decreasing d is forbidden
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
        assert!(!rec.promotion_candidate, "parent flag cleared after promote");
    }

    #[test]
    fn serde_roundtrip() {
        let rec = AlienIndexRecord::new("H-X-001", AlienIndex::new(1, 3));
        let json = serde_json::to_string(&rec).unwrap();
        let back: AlienIndexRecord = serde_json::from_str(&json).unwrap();
        assert_eq!(back.current, rec.current);
    }
}
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cargo test --lib alien_index::record`
Expected: FAIL — `AlienIndexRecord` not defined.

- [ ] **Step 3: 구현**

`src/alien_index/record.rs` (앞쪽):
```rust
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

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum RecordError {
    #[error("d is monotonic non-decreasing; cannot go from d={from} to d={to}")]
    DepthRegression { from: u32, to: u32 },
}

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
```

Add to `Cargo.toml` under `[dependencies]` if missing:
```toml
thiserror = "1"
```

Check first: `grep thiserror Cargo.toml` — if present skip.

- [ ] **Step 4: mod.rs 업데이트**

`src/alien_index/mod.rs`:
```rust
//! Alien Index (외계인 지수) — unified grading `(d, r)`.
//! See: docs/superpowers/specs/2026-04-05-alien-index-system-design.md
pub mod index;
pub mod record;

pub use index::AlienIndex;
pub use record::{AlienIndexRecord, HistoryEntry, RecordError};
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cargo test --lib alien_index::record`
Expected: 5 PASS.

- [ ] **Step 6: 커밋**

```bash
git add src/alien_index/record.rs src/alien_index/mod.rs Cargo.toml Cargo.lock
git commit -m "feat(alien_index): AlienIndexRecord with monotonic-d history + promotion"
```

---

## Task 3: r 산정기 (Assessor) — 신호 → rank

**Files:**
- Create: `src/alien_index/assess.rs`
- Modify: `src/alien_index/mod.rs`

nexus의 기존 3가지 신호를 r로 매핑:
1. `n6_match` quality (1.0=EXACT / 0.8=CLOSE / 0.5=WEAK)
2. 렌즈 합의 수 (lens_consensus_count)
3. MATH_ATLAS grade 문자열 (🟩, 🟧★, … 또는 `-`/`none`)

- [ ] **Step 1: 실패 테스트 작성**

`src/alien_index/assess.rs`:
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rank_from_n6_quality_exact_is_nine() {
        assert_eq!(rank_from_n6_quality(1.0), 9);
    }

    #[test]
    fn rank_from_n6_quality_close_is_seven() {
        assert_eq!(rank_from_n6_quality(0.8), 7);
    }

    #[test]
    fn rank_from_n6_quality_weak_is_five() {
        assert_eq!(rank_from_n6_quality(0.5), 5);
    }

    #[test]
    fn rank_from_n6_quality_none_is_zero() {
        assert_eq!(rank_from_n6_quality(0.0), 0);
    }

    #[test]
    fn rank_from_lens_consensus_thresholds() {
        assert_eq!(rank_from_lens_consensus(0), 0);
        assert_eq!(rank_from_lens_consensus(1), 3);
        assert_eq!(rank_from_lens_consensus(3), 6);
        assert_eq!(rank_from_lens_consensus(7), 7);
        assert_eq!(rank_from_lens_consensus(12), 8);
        assert_eq!(rank_from_lens_consensus(99), 8);
    }

    #[test]
    fn rank_from_grade_string_known_tokens() {
        assert_eq!(rank_from_grade("🟩"), Some(9));
        assert_eq!(rank_from_grade("🟧★★★"), Some(8));
        assert_eq!(rank_from_grade("🟧★★"), Some(8));
        assert_eq!(rank_from_grade("🟧★"), Some(7));
        assert_eq!(rank_from_grade("🟧"), Some(6));
        assert_eq!(rank_from_grade("🟦"), Some(5));
        assert_eq!(rank_from_grade("⚪"), Some(1));
        assert_eq!(rank_from_grade("🟥"), Some(2));
        assert_eq!(rank_from_grade("🟥★"), Some(3));
        assert_eq!(rank_from_grade("🟥★★"), Some(4));
        assert_eq!(rank_from_grade("🟥★★★★"), Some(4));
        assert_eq!(rank_from_grade("⬜ UNTESTED"), Some(0));
        assert_eq!(rank_from_grade("-"), None);
        assert_eq!(rank_from_grade(""), None);
    }

    #[test]
    fn combined_takes_max_of_signals() {
        // n6 EXACT (r=9) dominates lens_consensus=3 (r=6)
        let r = combine_signals(Some(1.0), Some(3), None);
        assert_eq!(r, 9);
        // grade 🟩 (r=9) equals EXACT (r=9)
        let r = combine_signals(None, None, Some("🟩"));
        assert_eq!(r, 9);
        // No signals → 0
        assert_eq!(combine_signals(None, None, None), 0);
    }
}
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cargo test --lib alien_index::assess`
Expected: FAIL — functions not defined.

- [ ] **Step 3: 구현**

`src/alien_index/assess.rs` (앞쪽):
```rust
/// Map `n6_match` quality (1.0 EXACT / 0.8 CLOSE / 0.5 WEAK / 0.0) to `r`.
/// Per spec: EXACT → 9 (closed-form candidate), CLOSE → 7, WEAK → 5, NONE → 0.
pub fn rank_from_n6_quality(quality: f64) -> u8 {
    if quality >= 1.0 { 9 }
    else if quality >= 0.8 { 7 }
    else if quality >= 0.5 { 5 }
    else { 0 }
}

/// Map lens consensus count to `r` per spec §5:
/// 1 lens → 3, 3 lenses → 6, 7 lenses → 7, 12+ lenses → 8.
pub fn rank_from_lens_consensus(count: u32) -> u8 {
    if count >= 12 { 8 }
    else if count >= 7 { 7 }
    else if count >= 3 { 6 }
    else if count >= 1 { 3 }
    else { 0 }
}

/// Parse a MATH_ATLAS grade emoji token to `r`.
/// Returns `None` for unknown / `"-"` / empty.
pub fn rank_from_grade(grade: &str) -> Option<u8> {
    let g = grade.trim();
    if g.is_empty() || g == "-" || g == "none" { return None; }
    if g.starts_with("⬜") { return Some(0); }
    if g == "⚪" { return Some(1); }
    if g == "🟥" { return Some(2); }
    if g == "🟥★" { return Some(3); }
    if g.starts_with("🟥★★") { return Some(4); }   // 🟥★★, 🟥★★★, 🟥★★★★
    if g == "🟦" { return Some(5); }
    if g == "🟧" { return Some(6); }
    if g == "🟧★" { return Some(7); }
    if g.starts_with("🟧★★") { return Some(8); }  // 🟧★★, 🟧★★★
    if g == "🟩" { return Some(9); }
    None
}

/// Take the strongest signal. `r = max(all available)`.
pub fn combine_signals(
    n6_quality: Option<f64>,
    lens_consensus: Option<u32>,
    grade: Option<&str>,
) -> u8 {
    let r_n6 = n6_quality.map(rank_from_n6_quality).unwrap_or(0);
    let r_lens = lens_consensus.map(rank_from_lens_consensus).unwrap_or(0);
    let r_grade = grade.and_then(rank_from_grade).unwrap_or(0);
    r_n6.max(r_lens).max(r_grade)
}
```

- [ ] **Step 4: mod.rs 업데이트**

`src/alien_index/mod.rs` 에 추가:
```rust
pub mod assess;
pub use assess::{rank_from_n6_quality, rank_from_lens_consensus, rank_from_grade, combine_signals};
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cargo test --lib alien_index::assess`
Expected: 7 PASS.

- [ ] **Step 6: 커밋**

```bash
git add src/alien_index/assess.rs src/alien_index/mod.rs
git commit -m "feat(alien_index): rank assessor from n6/lens/grade signals"
```

---

## Task 4: Distribution & Leaderboard

**Files:**
- Create: `src/alien_index/distribution.rs`
- Modify: `src/alien_index/mod.rs`

- [ ] **Step 1: 실패 테스트 작성**

`src/alien_index/distribution.rs`:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::alien_index::{AlienIndex, AlienIndexRecord};

    fn rec(id: &str, d: u32, r: u8) -> AlienIndexRecord {
        AlienIndexRecord::new(id, AlienIndex::new(d, r))
    }

    #[test]
    fn histogram_counts_pairs() {
        let records = vec![rec("a", 0, 5), rec("b", 0, 5), rec("c", 0, 7), rec("d", 1, 0)];
        let hist = histogram(&records);
        assert_eq!(hist.get(&(0, 5)).copied().unwrap_or(0), 2);
        assert_eq!(hist.get(&(0, 7)).copied().unwrap_or(0), 1);
        assert_eq!(hist.get(&(1, 0)).copied().unwrap_or(0), 1);
    }

    #[test]
    fn leaderboard_sorts_by_ai_descending() {
        let records = vec![rec("low", 0, 3), rec("top", 2, 5), rec("mid", 1, 8)];
        let board = leaderboard(&records, 3);
        assert_eq!(board[0].id, "top");
        assert_eq!(board[1].id, "mid");
        assert_eq!(board[2].id, "low");
    }

    #[test]
    fn leaderboard_respects_limit() {
        let records = vec![rec("a", 0, 1), rec("b", 0, 2), rec("c", 0, 3)];
        let board = leaderboard(&records, 2);
        assert_eq!(board.len(), 2);
        assert_eq!(board[0].id, "c");
    }

    #[test]
    fn breakthrough_ratio_d_ge_one_over_total() {
        let records = vec![rec("a", 0, 5), rec("b", 1, 0), rec("c", 1, 3), rec("d", 2, 0)];
        let ratio = breakthrough_ratio(&records);
        assert!((ratio - 0.75).abs() < 1e-9);
    }

    #[test]
    fn breakthrough_ratio_empty_is_zero() {
        assert_eq!(breakthrough_ratio(&[]), 0.0);
    }
}
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `cargo test --lib alien_index::distribution`
Expected: FAIL.

- [ ] **Step 3: 구현**

`src/alien_index/distribution.rs` (앞쪽):
```rust
use crate::alien_index::AlienIndexRecord;
use std::collections::BTreeMap;

pub type Histogram = BTreeMap<(u32, u8), usize>;

pub fn histogram(records: &[AlienIndexRecord]) -> Histogram {
    let mut h = BTreeMap::new();
    for r in records {
        *h.entry((r.current.d, r.current.r)).or_insert(0) += 1;
    }
    h
}

/// Top-`limit` records sorted by (d, r) descending.
pub fn leaderboard(records: &[AlienIndexRecord], limit: usize) -> Vec<AlienIndexRecord> {
    let mut sorted: Vec<AlienIndexRecord> = records.to_vec();
    sorted.sort_by(|a, b| b.current.cmp(&a.current));
    sorted.truncate(limit);
    sorted
}

/// ρ = |{records with d ≥ 1}| / |total|. Per spec §9: long-run limit predicted = 1/3.
pub fn breakthrough_ratio(records: &[AlienIndexRecord]) -> f64 {
    if records.is_empty() { return 0.0; }
    let breakthrough = records.iter().filter(|r| r.current.d >= 1).count();
    breakthrough as f64 / records.len() as f64
}
```

- [ ] **Step 4: mod.rs 업데이트**

```rust
pub mod distribution;
pub use distribution::{histogram, leaderboard, breakthrough_ratio, Histogram};
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cargo test --lib alien_index::distribution`
Expected: 5 PASS.

- [ ] **Step 6: 커밋**

```bash
git add src/alien_index/distribution.rs src/alien_index/mod.rs
git commit -m "feat(alien_index): histogram, leaderboard, breakthrough ratio"
```

---

## Task 5: CLI 파서에 AlienIndex 서브커맨드 추가

**Files:**
- Modify: `src/cli/parser.rs`

- [ ] **Step 1: 파서 현재 구조 확인**

Run: `grep -n "CliCommand::Detect\|CliCommand::Blowup\|parse(" src/cli/parser.rs | head -20`
이어서 Blowup/Detect 파싱이 어떻게 구현되어 있는지 파일을 읽어 패턴을 파악한다.

Run: `grep -n '"blowup"\|"detect"\|fn parse' src/cli/parser.rs | head -30`

- [ ] **Step 2: 실패 테스트 작성**

`src/cli/parser.rs` 의 `#[cfg(test)] mod tests` 안 (파일 끝 근처) 에 추가:
```rust
#[test]
fn parses_alien_index_single_id() {
    let args = vec!["nexus", "alien-index", "H-AF-006"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex {
        sub: AlienIndexSub::Assess { target: "H-AF-006".to_string(), scan: false },
    });
}

#[test]
fn parses_alien_index_scan_flag() {
    let args = vec!["nexus", "alien-index", "12.0", "--scan"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex {
        sub: AlienIndexSub::Assess { target: "12.0".to_string(), scan: true },
    });
}

#[test]
fn parses_alien_index_distribution() {
    let args = vec!["nexus", "alien-index", "--distribution"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex { sub: AlienIndexSub::Distribution });
}

#[test]
fn parses_alien_index_leaderboard() {
    let args = vec!["nexus", "alien-index", "--leaderboard"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex { sub: AlienIndexSub::Leaderboard { limit: 20 } });
}

#[test]
fn parses_alien_index_promote_pending() {
    let args = vec!["nexus", "alien-index", "--promote-pending"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex { sub: AlienIndexSub::PromotePending });
}

#[test]
fn parses_alien_index_recompute_all() {
    let args = vec!["nexus", "alien-index", "--recompute-all"];
    let cmd = parse(args.iter().map(|s| s.to_string())).unwrap();
    assert_eq!(cmd, CliCommand::AlienIndex { sub: AlienIndexSub::RecomputeAll });
}
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `cargo test --lib cli::parser::tests::parses_alien_index`
Expected: FAIL — `AlienIndexSub` not defined.

- [ ] **Step 4: 파서 구현**

`src/cli/parser.rs` 의 `CliCommand` enum에 variant 추가 (variants 맨 뒤, `Help` 직전):
```rust
    /// 외계인 지수 (alien index) 조회/승격/배치 처리
    AlienIndex {
        sub: AlienIndexSub,
    },
```

`CliCommand` 바로 아래에 새 enum 정의 (다른 sub-enum들 옆, 예: `ExperimentMode` 근처):
```rust
#[derive(Debug, Clone, PartialEq)]
pub enum AlienIndexSub {
    Assess { target: String, scan: bool },
    RecomputeAll,
    PromotePending,
    Breakthrough { id: String },
    Distribution,
    Leaderboard { limit: usize },
}
```

`parse` 함수의 서브커맨드 분기 (기존 `"blowup" => …` 나 `"detect" => …` 근처) 에 추가:
```rust
        "alien-index" => {
            // Flag forms: --distribution, --leaderboard[=N], --promote-pending, --recompute-all
            let mut iter = args.into_iter().peekable();
            let mut scan = false;
            let mut limit: usize = 20;
            let mut target: Option<String> = None;
            let mut flag_mode: Option<&'static str> = None;
            let mut breakthrough_id: Option<String> = None;
            while let Some(arg) = iter.next() {
                match arg.as_str() {
                    "--scan" => scan = true,
                    "--distribution" => flag_mode = Some("distribution"),
                    "--leaderboard" => flag_mode = Some("leaderboard"),
                    "--promote-pending" => flag_mode = Some("promote-pending"),
                    "--recompute-all" => flag_mode = Some("recompute-all"),
                    "--breakthrough" => {
                        breakthrough_id = iter.next();
                        flag_mode = Some("breakthrough");
                    }
                    "--limit" => {
                        if let Some(v) = iter.next() {
                            limit = v.parse().unwrap_or(20);
                        }
                    }
                    other if !other.starts_with("--") && target.is_none() => {
                        target = Some(other.to_string());
                    }
                    _ => {}
                }
            }
            let sub = match flag_mode {
                Some("distribution") => AlienIndexSub::Distribution,
                Some("leaderboard") => AlienIndexSub::Leaderboard { limit },
                Some("promote-pending") => AlienIndexSub::PromotePending,
                Some("recompute-all") => AlienIndexSub::RecomputeAll,
                Some("breakthrough") => AlienIndexSub::Breakthrough {
                    id: breakthrough_id.ok_or("--breakthrough requires an id")?,
                },
                _ => AlienIndexSub::Assess {
                    target: target.ok_or("alien-index requires a target or flag")?,
                    scan,
                },
            };
            Ok(CliCommand::AlienIndex { sub })
        }
```

> 주의: 위 스니펫의 `args` 변수명/에러 타입은 기존 `parse` 함수의 시그니처에 맞춰 조정할 것. `parse` 내에서 이미 첫 토큰(subcommand 이름)을 `match` 하는 위치에 이 `"alien-index"` arm 을 삽입한다.

- [ ] **Step 5: 테스트 통과 확인**

Run: `cargo test --lib cli::parser::tests::parses_alien_index`
Expected: 6 PASS.

- [ ] **Step 6: 커밋**

```bash
git add src/cli/parser.rs
git commit -m "feat(cli): add alien-index subcommand parser"
```

---

## Task 6: CLI 러너 dispatch — Assess + Distribution + Leaderboard

**Files:**
- Create: `src/cli/alien_index_cmd.rs`
- Modify: `src/cli/mod.rs` (모듈 등록)
- Modify: `src/cli/runner.rs` (dispatch arm 추가)

- [ ] **Step 1: mod.rs 확인 및 모듈 등록**

Run: `cat src/cli/mod.rs`

`src/cli/mod.rs`에 추가 (기존 `pub mod` 라인들 뒤):
```rust
pub mod alien_index_cmd;
```

- [ ] **Step 2: dispatch 모듈 작성 (우선 간단한 plumbing)**

`src/cli/alien_index_cmd.rs`:
```rust
//! `nexus alien-index …` 서브커맨드 실행기.
use crate::alien_index::{
    assess::combine_signals, breakthrough_ratio, histogram, leaderboard, AlienIndex,
    AlienIndexRecord,
};
use crate::cli::parser::AlienIndexSub;
use crate::verifier::n6_check::n6_match;

pub fn run(sub: AlienIndexSub) -> Result<(), String> {
    match sub {
        AlienIndexSub::Assess { target, scan } => assess(&target, scan),
        AlienIndexSub::Distribution => distribution(),
        AlienIndexSub::Leaderboard { limit } => show_leaderboard(limit),
        AlienIndexSub::PromotePending => promote_pending(),
        AlienIndexSub::RecomputeAll => recompute_all(),
        AlienIndexSub::Breakthrough { id } => breakthrough(&id),
    }
}

fn assess(target: &str, scan: bool) -> Result<(), String> {
    // If target parses as f64 → n6_match flow.
    if let Ok(value) = target.parse::<f64>() {
        let (name, quality) = n6_match(value);
        let r = combine_signals(Some(quality), None, None);
        let ai = AlienIndex::new(0, r);
        println!("AlienIndex: d={} r={} (source=n6_match: {} quality={:.2})", ai.d, ai.r, name, quality);
        if scan {
            eprintln!("(hint: --scan integration with lens consensus is a future task)");
        }
        return Ok(());
    }
    // Otherwise treat as hypothesis_id — look up in MATH_ATLAS.
    let grade = load_grade_for_id(target);
    let r = combine_signals(None, None, grade.as_deref());
    let ai = AlienIndex::new(0, r);
    println!("AlienIndex: d={} r={} (source=grade: {})", ai.d, ai.r, grade.as_deref().unwrap_or("none"));
    Ok(())
}

fn load_grade_for_id(id: &str) -> Option<String> {
    // Load math_atlas.json and find hypothesis by id. Path resolution: shared/math_atlas.json.
    let path = crate::alien_index::record::math_atlas_path();
    let data = std::fs::read_to_string(&path).ok()?;
    let json: serde_json::Value = serde_json::from_str(&data).ok()?;
    let hyps = json.get("hypotheses")?.as_array()?;
    for h in hyps {
        if h.get("id")?.as_str()? == id {
            return h.get("grade").and_then(|g| g.as_str()).map(|s| s.to_string());
        }
    }
    None
}

fn load_all_records() -> Vec<AlienIndexRecord> {
    let path = crate::alien_index::record::discovery_log_path();
    let Ok(content) = std::fs::read_to_string(&path) else { return Vec::new() };
    let mut out = Vec::new();
    for line in content.lines() {
        if line.trim().is_empty() { continue; }
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
            if let Some(ai) = v.get("alien_index") {
                if let Ok(rec) = serde_json::from_value::<AlienIndexRecord>(ai.clone()) {
                    out.push(rec);
                }
            }
        }
    }
    out
}

fn distribution() -> Result<(), String> {
    let records = load_all_records();
    let hist = histogram(&records);
    let ratio = breakthrough_ratio(&records);
    println!("=== Alien Index Distribution ===");
    println!("Total records: {}", records.len());
    println!("Breakthrough ratio ρ = {:.4} (meta fixed point target: 0.333…)", ratio);
    println!();
    println!("  (d, r)  count");
    for ((d, r), n) in &hist {
        println!("  ({}, {:>2})  {}", d, r, n);
    }
    Ok(())
}

fn show_leaderboard(limit: usize) -> Result<(), String> {
    let records = load_all_records();
    let board = leaderboard(&records, limit);
    println!("=== Alien Index Leaderboard (top {}) ===", limit);
    for (i, rec) in board.iter().enumerate() {
        println!("{:>3}. d={} r={:>2}  {}", i + 1, rec.current.d, rec.current.r, rec.id);
    }
    Ok(())
}

fn promote_pending() -> Result<(), String> {
    let records = load_all_records();
    let mut promoted = 0;
    for mut rec in records.into_iter().filter(|r| r.promotion_candidate) {
        if let Some(child) = rec.promote() {
            println!("promote: {} (d={}, r=10) → {} (d={}, r=0)",
                rec.id, rec.current.d, child.id, child.current.d);
            promoted += 1;
        }
    }
    println!("{} record(s) promoted. (Note: writeback to disk is a follow-up task.)", promoted);
    Ok(())
}

fn recompute_all() -> Result<(), String> {
    eprintln!("recompute-all: not yet implemented (needs atlas → discovery_log writer)");
    Ok(())
}

fn breakthrough(id: &str) -> Result<(), String> {
    eprintln!("breakthrough {}: explicit CycleEngine wrapper — not yet implemented", id);
    Ok(())
}
```

> `promote_pending` / `recompute_all` / `breakthrough` 의 디스크 쓰기는 Task 8에서 구현. 현재는 dry-run 출력만.

- [ ] **Step 3: path helper 추가**

`src/alien_index/record.rs` 끝에 추가:
```rust
/// shared/ 디렉토리의 절대 경로. 레포 루트 기준.
fn shared_dir() -> std::path::PathBuf {
    std::env::var("NEXUS_SHARED_DIR")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| {
            let exe = std::env::current_exe().ok();
            // Fallback: cwd/shared
            exe.and_then(|p| p.parent().map(|d| d.to_path_buf()))
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join("shared")
        })
}

pub fn math_atlas_path() -> std::path::PathBuf {
    std::env::var("NEXUS_MATH_ATLAS")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("math_atlas.json"))
}

pub fn discovery_log_path() -> std::path::PathBuf {
    std::env::var("NEXUS_DISCOVERY_LOG")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("discovery_log.jsonl"))
}
```

> 환경변수 오버라이드를 허용해 테스트 격리 가능.

- [ ] **Step 4: runner.rs에 dispatch arm 추가**

Run: `grep -n "CliCommand::Blowup\|CliCommand::Detect" src/cli/runner.rs` 로 dispatch 함수 위치 확인.

`src/cli/runner.rs` 에 use 추가 (파일 상단, 다른 `use crate::…` 근처):
```rust
use crate::cli::parser::AlienIndexSub;
use crate::cli::alien_index_cmd;
```

기존 dispatch match 문 (예: `CliCommand::Blowup { .. }` arm 옆) 에 추가:
```rust
        CliCommand::AlienIndex { sub } => {
            if let Err(e) = alien_index_cmd::run(sub) {
                eprintln!("error: {}", e);
                std::process::exit(1);
            }
        }
```

- [ ] **Step 5: 빌드 확인**

Run: `cargo build --lib --bin nexus 2>&1 | tail -30`
Expected: 빌드 성공 (경고는 허용).

- [ ] **Step 6: 스모크 테스트**

Run: `cargo run --bin nexus -- alien-index 12.0`
Expected: `AlienIndex: d=0 r=9 (source=n6_match: sigma quality=1.00)`

Run: `cargo run --bin nexus -- alien-index --distribution`
Expected: `Total records: 0` 와 분포 빈 출력 (log가 비어있거나 alien_index 필드 없을 때).

- [ ] **Step 7: 커밋**

```bash
git add src/cli/alien_index_cmd.rs src/cli/mod.rs src/cli/runner.rs src/alien_index/record.rs
git commit -m "feat(cli): alien-index dispatch — assess/distribution/leaderboard"
```

---

## Task 7: 통합 테스트 — 엔드투엔드 평가기

**Files:**
- Create: `tests/alien_index_integration.rs`

- [ ] **Step 1: 테스트 작성**

`tests/alien_index_integration.rs`:
```rust
use nexus::alien_index::{
    assess::combine_signals, AlienIndex, AlienIndexRecord, breakthrough_ratio, histogram,
};

#[test]
fn closed_form_candidate_flow() {
    // Start at r=5 (empirical pattern)
    let mut rec = AlienIndexRecord::new("H-TEST-1", AlienIndex::new(0, 5));
    // Lens consensus climbs
    rec.update(AlienIndex::new(0, 7), "7-lens consensus").unwrap();
    rec.update(AlienIndex::new(0, 9), "n6_check EXACT").unwrap();
    rec.update(AlienIndex::new(0, 10), "proof committed").unwrap();
    assert!(rec.promotion_candidate);
    // Promote → child at (1, 0)
    let child = rec.promote().unwrap();
    assert_eq!(child.current, AlienIndex::new(1, 0));
    assert!(!rec.promotion_candidate);
    assert_eq!(child.promoted_from.as_deref(), Some("H-TEST-1"));
}

#[test]
fn d_monotonic_enforced() {
    let mut rec = AlienIndexRecord::new("H-TEST-2", AlienIndex::new(1, 3));
    // r may decrease at same d
    assert!(rec.update(AlienIndex::new(1, 2), "refutation").is_ok());
    // d cannot decrease
    assert!(rec.update(AlienIndex::new(0, 9), "nope").is_err());
}

#[test]
fn combine_signals_picks_max() {
    // EXACT (r=9) > consensus 3 (r=6) > grade 🟧 (r=6)
    let r = combine_signals(Some(1.0), Some(3), Some("🟧"));
    assert_eq!(r, 9);
}

#[test]
fn breakthrough_ratio_on_synthetic_set() {
    let records: Vec<AlienIndexRecord> = (0..9)
        .map(|i| AlienIndexRecord::new(format!("X{i}"), AlienIndex::new(0, 5)))
        .chain(std::iter::once(AlienIndexRecord::new("B", AlienIndex::new(1, 0))))
        .collect();
    let ratio = breakthrough_ratio(&records);
    assert!((ratio - 0.1).abs() < 1e-9);
    let h = histogram(&records);
    assert_eq!(h.get(&(0, 5)).copied().unwrap_or(0), 9);
    assert_eq!(h.get(&(1, 0)).copied().unwrap_or(0), 1);
}
```

- [ ] **Step 2: 테스트 실행**

Run: `cargo test --test alien_index_integration`
Expected: 4 PASS.

- [ ] **Step 3: 커밋**

```bash
git add tests/alien_index_integration.rs
git commit -m "test(alien_index): end-to-end flow (promotion, monotonic d, ratio)"
```

---

## Task 8: 마이그레이션 스크립트 — MATH_ATLAS grade → (d, r)

**Files:**
- Create: `tools/migrate_grades_to_alien_index.py`

- [ ] **Step 1: 스크립트 작성**

`tools/migrate_grades_to_alien_index.py`:
```python
#!/usr/bin/env python3
"""MATH_ATLAS grade → alien_index (d=0, r) 일회성 마이그레이션.

Input:  shared/discovery/math_atlas.json
Output: shared/discovery/alien/alien_index_records.jsonl  (한 가설당 한 줄)

사용법:
  python3 tools/migrate_grades_to_alien_index.py
  python3 tools/migrate_grades_to_alien_index.py --dry-run
  python3 tools/migrate_grades_to_alien_index.py --atlas path/to.json --out path/out.jsonl
"""
import argparse
import json
import sys
import time
from pathlib import Path

# 스펙 §5 매핑과 동일 (src/alien_index/assess.rs 와 일치해야 함)
def rank_from_grade(g: str):
    if not g or g.strip() in ("-", "none"):
        return None
    g = g.strip()
    if g.startswith("⬜"): return 0
    if g == "⚪": return 1
    if g == "🟥": return 2
    if g == "🟥★": return 3
    if g.startswith("🟥★★"): return 4
    if g == "🟦": return 5
    if g == "🟧": return 6
    if g == "🟧★": return 7
    if g.startswith("🟧★★"): return 8
    if g == "🟩": return 9
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", default="shared/discovery/math_atlas.json")
    ap.add_argument("--out", default="shared/discovery/alien/alien_index_records.jsonl")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    atlas_path = Path(args.atlas)
    if not atlas_path.exists():
        print(f"ERROR: atlas not found at {atlas_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(atlas_path.read_text())
    hyps = data.get("hypotheses", [])

    now = int(time.time())
    records = []
    stats = {"mapped": 0, "skipped": 0, "by_r": {}}

    for h in hyps:
        hid = h.get("id") or h.get("title", "?")
        grade = h.get("grade", "")
        r = rank_from_grade(grade)
        if r is None:
            stats["skipped"] += 1
            continue
        rec = {
            "id": hid,
            "current": {"d": 0, "r": r},
            "history": [{"timestamp_unix": now, "d": 0, "r": r, "reason": f"migration:grade={grade}"}],
            "promotion_candidate": r == 10,
            "promoted_from": None,
        }
        records.append(rec)
        stats["mapped"] += 1
        stats["by_r"][r] = stats["by_r"].get(r, 0) + 1

    print(f"Mapped: {stats['mapped']}  Skipped: {stats['skipped']}")
    print("Distribution by r:")
    for r in sorted(stats["by_r"]):
        print(f"  r={r}: {stats['by_r'][r]}")

    if args.dry_run:
        print("(dry-run; no file written)")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 드라이런 실행**

Run: `cd $NEXUS && python3 tools/migrate_grades_to_alien_index.py --dry-run`
Expected: 매핑 통계 출력 (Mapped ~660+, Skipped ~27, r별 분포).

- [ ] **Step 3: 실제 파일 생성**

Run: `python3 tools/migrate_grades_to_alien_index.py`
Expected: `Wrote N records to shared/discovery/alien/alien_index_records.jsonl`.

- [ ] **Step 4: 생성물 검증**

Run: `head -3 shared/discovery/alien/alien_index_records.jsonl && wc -l shared/discovery/alien/alien_index_records.jsonl`
Expected: JSON 레코드 3개 표시 + 총 라인 수.

- [ ] **Step 5: CLI로 분포 확인**

Run: `NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl cargo run --bin nexus -- alien-index --distribution`
Expected: 분포 출력 (총 레코드 수 일치).

> ⚠️ 현재 loader가 `alien_index` 필드를 가진 discovery_log 형식을 기대하지만, migration 출력은 레코드가 **곧 그 필드 내용**이므로 load 경로를 하나 더 맞춰야 함.

- [ ] **Step 6: loader 보강 — migration 파일 직접 로드 경로**

`src/cli/alien_index_cmd.rs` 의 `load_all_records` 수정:
```rust
fn load_all_records() -> Vec<AlienIndexRecord> {
    let path = crate::alien_index::record::discovery_log_path();
    let Ok(content) = std::fs::read_to_string(&path) else { return Vec::new() };
    let mut out = Vec::new();
    for line in content.lines() {
        if line.trim().is_empty() { continue; }
        // Try two forms: (a) { "alien_index": {...} } wrapper, (b) bare record
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
            if let Some(inner) = v.get("alien_index") {
                if let Ok(rec) = serde_json::from_value::<AlienIndexRecord>(inner.clone()) {
                    out.push(rec);
                    continue;
                }
            }
            if let Ok(rec) = serde_json::from_value::<AlienIndexRecord>(v) {
                out.push(rec);
            }
        }
    }
    out
}
```

Run: `cargo build --bin nexus 2>&1 | tail -10`
Expected: 빌드 성공.

Run: `NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl cargo run --bin nexus -- alien-index --distribution`
Expected: Total records > 0, (0, r) 버킷들.

Run: `NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl cargo run --bin nexus -- alien-index --leaderboard --limit 10`
Expected: r=9 항목들 상위 출력.

- [ ] **Step 7: 커밋**

```bash
git add tools/migrate_grades_to_alien_index.py src/cli/alien_index_cmd.rs shared/discovery/alien/alien_index_records.jsonl
git commit -m "feat(alien_index): migration script (grade→r) + loader supports bare records"
```

---

## Task 9: Observability 산출물 — 분포/리더보드 디스크 저장

**Files:**
- Modify: `src/cli/alien_index_cmd.rs`

- [ ] **Step 1: 테스트 작성**

`src/cli/alien_index_cmd.rs` 끝에 `#[cfg(test)] mod tests` 추가:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::alien_index::{AlienIndex, AlienIndexRecord};
    use std::io::Write;
    use tempfile::NamedTempFile;

    fn write_records(records: &[AlienIndexRecord]) -> NamedTempFile {
        let mut f = NamedTempFile::new().unwrap();
        for r in records {
            writeln!(f, "{}", serde_json::to_string(r).unwrap()).unwrap();
        }
        f
    }

    #[test]
    fn write_distribution_json_creates_valid_file() {
        let records = vec![
            AlienIndexRecord::new("a", AlienIndex::new(0, 5)),
            AlienIndexRecord::new("b", AlienIndex::new(0, 7)),
            AlienIndexRecord::new("c", AlienIndex::new(1, 0)),
        ];
        let out = NamedTempFile::new().unwrap();
        write_distribution_json(&records, out.path()).unwrap();
        let content = std::fs::read_to_string(out.path()).unwrap();
        let v: serde_json::Value = serde_json::from_str(&content).unwrap();
        assert_eq!(v["total"], 3);
        assert!(v["breakthrough_ratio"].as_f64().unwrap() > 0.3);
    }

    #[test]
    fn write_frontier_md_lists_top_d() {
        let records = vec![
            AlienIndexRecord::new("small", AlienIndex::new(0, 3)),
            AlienIndexRecord::new("BIG", AlienIndex::new(2, 5)),
        ];
        let out = NamedTempFile::new().unwrap();
        write_frontier_md(&records, out.path(), 10).unwrap();
        let md = std::fs::read_to_string(out.path()).unwrap();
        assert!(md.contains("BIG"));
        assert!(md.contains("d=2"));
        // BIG must appear before small
        let pos_big = md.find("BIG").unwrap();
        let pos_small = md.find("small").unwrap();
        assert!(pos_big < pos_small);
    }
}
```

- [ ] **Step 2: tempfile 의존성 확인 및 추가**

Run: `grep '^tempfile' Cargo.toml`
If absent, add under `[dev-dependencies]` (새 섹션일 수 있음 — 기존에 있으면 그 밑에 추가):
```toml
[dev-dependencies]
tempfile = "3"
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `cargo test --lib alien_index_cmd::tests`
Expected: FAIL — functions not defined.

- [ ] **Step 4: 함수 구현**

`src/cli/alien_index_cmd.rs` 에 추가 (dispatch 함수들 근처):
```rust
use std::path::Path;

pub fn write_distribution_json(
    records: &[AlienIndexRecord],
    out: &Path,
) -> std::io::Result<()> {
    let hist = histogram(records);
    let ratio = breakthrough_ratio(records);
    let buckets: Vec<_> = hist.iter().map(|((d, r), n)| {
        serde_json::json!({ "d": d, "r": r, "count": n })
    }).collect();
    let payload = serde_json::json!({
        "total": records.len(),
        "breakthrough_ratio": ratio,
        "meta_fixed_point_target": 0.333_333_333_333_333,
        "buckets": buckets,
    });
    std::fs::write(out, serde_json::to_string_pretty(&payload).unwrap())
}

pub fn write_frontier_md(
    records: &[AlienIndexRecord],
    out: &Path,
    limit: usize,
) -> std::io::Result<()> {
    let top = leaderboard(records, limit);
    let mut md = String::from("# Alien Index Frontier\n\n");
    md.push_str(&format!("Total: {}\n\n", records.len()));
    md.push_str("| Rank | d | r | ID |\n|---|---|---|---|\n");
    for (i, rec) in top.iter().enumerate() {
        md.push_str(&format!("| {} | {} | {} | {} |\n",
            i + 1, rec.current.d, rec.current.r, rec.id));
    }
    std::fs::write(out, md)
}
```

`distribution()` 과 `show_leaderboard()` 함수 뒤에 side-effect 쓰기 호출 추가 (환경변수로 경로 지정):
```rust
fn distribution() -> Result<(), String> {
    let records = load_all_records();
    let hist = histogram(&records);
    let ratio = breakthrough_ratio(&records);
    println!("=== Alien Index Distribution ===");
    println!("Total records: {}", records.len());
    println!("Breakthrough ratio ρ = {:.4} (meta fixed point target: 0.333…)", ratio);
    println!();
    println!("  (d, r)  count");
    for ((d, r), n) in &hist {
        println!("  ({}, {:>2})  {}", d, r, n);
    }
    // Side-effect: write to shared/discovery/alien/alien_index_distribution.json if env set or path exists
    let out = crate::alien_index::record::distribution_json_path();
    if let Err(e) = write_distribution_json(&records, &out) {
        eprintln!("warn: failed to write {}: {}", out.display(), e);
    } else {
        println!("\nwritten: {}", out.display());
    }
    Ok(())
}
```

그리고 `show_leaderboard` 에도 유사하게:
```rust
fn show_leaderboard(limit: usize) -> Result<(), String> {
    let records = load_all_records();
    let board = leaderboard(&records, limit);
    println!("=== Alien Index Leaderboard (top {}) ===", limit);
    for (i, rec) in board.iter().enumerate() {
        println!("{:>3}. d={} r={:>2}  {}", i + 1, rec.current.d, rec.current.r, rec.id);
    }
    let out = crate::alien_index::record::frontier_md_path();
    if let Err(e) = write_frontier_md(&records, &out, limit) {
        eprintln!("warn: failed to write {}: {}", out.display(), e);
    } else {
        println!("\nwritten: {}", out.display());
    }
    Ok(())
}
```

`src/alien_index/record.rs` 끝에 path helper 추가:
```rust
pub fn distribution_json_path() -> std::path::PathBuf {
    std::env::var("NEXUS_AI_DISTRIBUTION")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("alien_index_distribution.json"))
}

pub fn frontier_md_path() -> std::path::PathBuf {
    std::env::var("NEXUS_AI_FRONTIER")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| shared_dir().join("alien_index_frontier.md"))
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cargo test --lib alien_index_cmd::tests`
Expected: 2 PASS.

- [ ] **Step 6: 엔드투엔드 스모크 테스트**

Run:
```bash
NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl \
NEXUS_AI_DISTRIBUTION=/tmp/ai_dist.json \
NEXUS_AI_FRONTIER=/tmp/ai_frontier.md \
cargo run --bin nexus -- alien-index --distribution
```

Expected: 분포 출력 + `/tmp/ai_dist.json` 생성.

Run: `cat /tmp/ai_dist.json | head -30`
Expected: 유효 JSON with `total`, `breakthrough_ratio`, `buckets`.

- [ ] **Step 7: 커밋**

```bash
git add src/cli/alien_index_cmd.rs src/alien_index/record.rs Cargo.toml Cargo.lock
git commit -m "feat(alien_index): persist distribution.json and frontier.md"
```

---

## Task 10: 전체 검증 + 문서 갱신

**Files:**
- Modify: `CLAUDE.md` (프로젝트 루트) — 외계인 지수 섹션 추가

- [ ] **Step 1: 전체 테스트 실행**

Run: `cargo test --lib alien_index`
Expected: All pass.

Run: `cargo test --test alien_index_integration`
Expected: 4 PASS.

Run: `cargo build --release --bin nexus 2>&1 | tail -5`
Expected: 빌드 성공.

- [ ] **Step 2: 실 데이터 리그레션**

Run:
```bash
NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl \
./target/release/nexus alien-index --distribution
```

Expected: Total records == 마이그레이션 수, ρ 출력, 버킷 분포.

Run:
```bash
NEXUS_DISCOVERY_LOG=shared/discovery/alien/alien_index_records.jsonl \
./target/release/nexus alien-index --leaderboard --limit 5
```

Expected: r=9 (🟩 가설들) 상위 5개.

Run:
```bash
./target/release/nexus alien-index 12.0
```

Expected: `AlienIndex: d=0 r=9 (source=n6_match: sigma quality=1.00)`.

- [ ] **Step 3: CLAUDE.md 에 섹션 추가**

`CLAUDE.md` 에 "마이크로사이클" 섹션 뒤에 추가:
```markdown
## 외계인 지수 (Alien Index)

> **통합 등급 체계** — 닫힌 수학의 천장(r=10)과 그 너머 돌파 영역(d≥1)을 표현
> CLI: `nexus alien-index` | 모듈: `src/alien_index/` | 스펙: `docs/superpowers/specs/2026-04-05-alien-index-system-design.md`

### 구조

`AI = (d, r)`
- `d` = 사이클 깊이 (몇 번 블로업→흡수가 완결됐나)
- `r` ∈ {0..10} = 깊이 d 안에서의 검증 등급
- `r=10` 도달 → `(d+1, 0)` 자동 승격 (자기유사)

### 사용법

```bash
nexus alien-index 12.0                    # 값 → (0, r) 즉시 판정
nexus alien-index H-AF-006                # 가설 ID → 등급 조회
nexus alien-index --distribution          # (d, r) 히스토그램 + ρ(돌파율)
nexus alien-index --leaderboard           # 최고 d 대상 리더보드
nexus alien-index --promote-pending       # r=10 대기 항목 승격 (dry-run)
```

### 메타 부동점

돌파율 `ρ = |{d ≥ 1}| / |total|` 의 장기 수렴치 예측: **1/3** (CLAUDE.md TECS-L H-056).
매 분포 리포트에 기록되어 메타 부동점 가설의 회귀 검증치로 사용됨.
```

- [ ] **Step 4: 커밋**

```bash
git add CLAUDE.md
git commit -m "docs: add Alien Index section to CLAUDE.md"
```

- [ ] **Step 5: 최종 확인**

Run: `git log --oneline -15`
Expected: 10개 새 커밋 + 기존 헤드.

Run: `./target/release/nexus alien-index --help 2>&1 || ./target/release/nexus --help 2>&1 | grep -i alien`
Expected: 헬프에 alien-index 표시되거나 최소한 서브커맨드가 인식됨.

---

## Self-Review

**Spec coverage 체크:**
- ✅ §2 `(d, r)` 구조 + 돌파 연산 — Task 1
- ✅ §3 매핑 테이블 (d=0 grade, d≥1 사이클 단계) — Task 3 (grade/n6/consensus), 스펙 정의만 채택
- ✅ §4 하이브리드 판정 — Task 3 (자동 d=0), Task 6 (CLI), d≥1 수동은 추후
- ✅ §5 기존 자원 연결 — Task 3 + Task 6 (math_atlas.json 로드)
- ✅ §6.1 데이터 모델 + §6.2 불변식 (d 단조성, promotion_candidate, parent_id) — Task 2
- ✅ §7.1 CLI subcommands — Task 5, 6 (assess/distribution/leaderboard/promote-pending/recompute-all/breakthrough; 일부는 dry-run)
- ✅ §7.2 Rust API — Task 1, 2 (공개 타입)
- ⚠️ §7.3 Python 바인딩 — **PyO3 exposure 미포함** (후속 작업). 스펙 §10에서 "제외" 항목 아님 → 본 플랜에서는 core + CLI 우선, PyO3는 별도 PR 권장.
- ✅ §8 마이그레이션 — Task 8
- ✅ §9 관측 가능성 (distribution.json, frontier.md, ρ 추적) — Task 9
- ✅ §10 범위 (제외 항목은 제외, 나머지 포함)
- ✅ §11 테스트 — Task 7 통합 테스트 + 단위 테스트 전반

**Placeholder scan:** 모든 스텝에 실제 코드/명령 포함됨. `recompute-all` 과 `breakthrough` 는 의도적으로 dry-run 스텁(Task 6에 명시).

**Type consistency:**
- `AlienIndex { d: u32, r: u8 }` — 전체 일관
- `AlienIndexRecord { id, current, history, promotion_candidate, promoted_from }` — Task 2/4/6/8/9 일관
- `AlienIndexSub` variants — Task 5 정의, Task 6 dispatch 일치
- `promote()` — Task 2에서 `&mut self → Option<AlienIndexRecord>`, Task 6에서 동일 사용
- path helpers (`discovery_log_path`, `math_atlas_path`, `distribution_json_path`, `frontier_md_path`) — Task 6/9에서 일관
