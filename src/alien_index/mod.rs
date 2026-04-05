//! Alien Index (외계인 지수) — unified grading `(d, r)`.
//! See: docs/superpowers/specs/2026-04-05-alien-index-system-design.md
pub mod index;
pub mod record;
pub mod assess;
pub mod distribution;

pub use index::AlienIndex;
pub use record::{AlienIndexRecord, HistoryEntry, RecordError};
pub use assess::{combine_signals, rank_from_grade, rank_from_lens_consensus, rank_from_n6_quality};
pub use distribution::{breakthrough_ratio, histogram, leaderboard, Histogram};
