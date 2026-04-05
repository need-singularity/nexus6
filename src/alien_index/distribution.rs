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

/// ρ = |{records with d ≥ 1}| / |total|. Long-run target per meta fixed point: 1/3.
pub fn breakthrough_ratio(records: &[AlienIndexRecord]) -> f64 {
    if records.is_empty() { return 0.0; }
    let breakthrough = records.iter().filter(|r| r.current.d >= 1).count();
    breakthrough as f64 / records.len() as f64
}

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
