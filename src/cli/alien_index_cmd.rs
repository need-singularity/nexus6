//! `nexus6 alien-index …` 서브커맨드 실행기.
use crate::alien_index::{
    breakthrough_ratio, combine_signals, histogram, leaderboard, AlienIndex, AlienIndexRecord,
};
use crate::cli::parser::AlienIndexSub;
use crate::verifier::n6_check::n6_match;
use std::path::Path;

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
    if let Ok(value) = target.parse::<f64>() {
        let (name, quality) = n6_match(value);
        let r = combine_signals(Some(quality), None, None);
        let ai = AlienIndex::new(0, r);
        println!(
            "AlienIndex: d={} r={} (source=n6_match: {} quality={:.2})",
            ai.d, ai.r, name, quality
        );
        if scan {
            eprintln!("(hint: --scan integration with lens consensus is a future task)");
        }
        return Ok(());
    }
    let grade = load_grade_for_id(target);
    let r = combine_signals(None, None, grade.as_deref());
    let ai = AlienIndex::new(0, r);
    println!(
        "AlienIndex: d={} r={} (source=grade: {})",
        ai.d,
        ai.r,
        grade.as_deref().unwrap_or("none")
    );
    Ok(())
}

fn load_grade_for_id(id: &str) -> Option<String> {
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
    let out = crate::alien_index::record::distribution_json_path();
    if let Err(e) = write_distribution_json(&records, &out) {
        eprintln!("warn: failed to write {}: {}", out.display(), e);
    } else {
        println!("\nwritten: {}", out.display());
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
    let out = crate::alien_index::record::frontier_md_path();
    if let Err(e) = write_frontier_md(&records, &out, limit) {
        eprintln!("warn: failed to write {}: {}", out.display(), e);
    } else {
        println!("\nwritten: {}", out.display());
    }
    Ok(())
}

fn promote_pending() -> Result<(), String> {
    let records = load_all_records();
    let mut promoted = 0;
    for mut rec in records.into_iter().filter(|r| r.promotion_candidate) {
        let parent_d = rec.current.d;
        if let Some(child) = rec.promote() {
            println!(
                "promote: {} (d={}, r=10) → {} (d={}, r=0)",
                rec.id, parent_d, child.id, child.current.d
            );
            promoted += 1;
        }
    }
    println!(
        "{} record(s) promoted. (Note: writeback to disk is a follow-up task.)",
        promoted
    );
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

pub fn write_distribution_json(
    records: &[AlienIndexRecord],
    out: &Path,
) -> std::io::Result<()> {
    let hist = histogram(records);
    let ratio = breakthrough_ratio(records);
    let buckets: Vec<_> = hist
        .iter()
        .map(|((d, r), n)| serde_json::json!({ "d": d, "r": r, "count": n }))
        .collect();
    let payload = serde_json::json!({
        "total": records.len(),
        "breakthrough_ratio": ratio,
        "meta_fixed_point_target": 0.333_333_333_333_333_3_f64,
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
        md.push_str(&format!(
            "| {} | {} | {} | {} |\n",
            i + 1,
            rec.current.d,
            rec.current.r,
            rec.id
        ));
    }
    std::fs::write(out, md)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alien_index::{AlienIndex, AlienIndexRecord};

    #[test]
    fn write_distribution_json_creates_valid_file() {
        let records = vec![
            AlienIndexRecord::new("a", AlienIndex::new(0, 5)),
            AlienIndexRecord::new("b", AlienIndex::new(0, 7)),
            AlienIndexRecord::new("c", AlienIndex::new(1, 0)),
        ];
        let tmp = std::env::temp_dir().join(format!("ai_dist_{}.json", std::process::id()));
        write_distribution_json(&records, &tmp).unwrap();
        let content = std::fs::read_to_string(&tmp).unwrap();
        let v: serde_json::Value = serde_json::from_str(&content).unwrap();
        assert_eq!(v["total"], 3);
        assert!(v["breakthrough_ratio"].as_f64().unwrap() > 0.3);
        let _ = std::fs::remove_file(&tmp);
    }

    #[test]
    fn write_frontier_md_lists_top_d() {
        let records = vec![
            AlienIndexRecord::new("small", AlienIndex::new(0, 3)),
            AlienIndexRecord::new("BIG", AlienIndex::new(2, 5)),
        ];
        let tmp = std::env::temp_dir().join(format!("ai_frontier_{}.md", std::process::id()));
        write_frontier_md(&records, &tmp, 10).unwrap();
        let md = std::fs::read_to_string(&tmp).unwrap();
        assert!(md.contains("BIG"));
        assert!(md.contains("d=2") || md.contains("| 2 |"));
        let pos_big = md.find("BIG").unwrap();
        let pos_small = md.find("small").unwrap();
        assert!(pos_big < pos_small);
        let _ = std::fs::remove_file(&tmp);
    }
}
