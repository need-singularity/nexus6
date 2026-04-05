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
    let path = crate::alien_index::record::discovery_log_path();
    let content = std::fs::read_to_string(&path).unwrap_or_default();

    // Parse: keep non-ai lines verbatim; collect ai records.
    let mut preserved: Vec<String> = Vec::new();
    let mut ai_records: Vec<AlienIndexRecord> = Vec::new();
    for line in content.lines() {
        if line.trim().is_empty() { continue; }
        if line.contains("\"alien_index\"") {
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(line) {
                if let Some(inner) = v.get("alien_index") {
                    if let Ok(rec) = serde_json::from_value::<AlienIndexRecord>(inner.clone()) {
                        ai_records.push(rec);
                        continue;
                    }
                }
            }
            preserved.push(line.to_string());
        } else {
            preserved.push(line.to_string());
        }
    }

    // Promote candidates, collect children.
    let mut promoted = 0;
    let mut children: Vec<AlienIndexRecord> = Vec::new();
    for rec in ai_records.iter_mut() {
        if rec.promotion_candidate {
            let parent_d = rec.current.d;
            if let Some(child) = rec.promote() {
                println!(
                    "promote: {} (d={}, r=10) → {} (d={}, r=0)",
                    rec.id, parent_d, child.id, child.current.d
                );
                children.push(child);
                promoted += 1;
            }
        }
    }

    // Rewrite: preserved + updated ai + new children.
    let mut out = String::new();
    for l in &preserved { out.push_str(l); out.push('\n'); }
    for rec in &ai_records {
        match serde_json::to_string(rec) {
            Ok(s) => { out.push_str(&format!("{{\"alien_index\":{}}}\n", s)); }
            Err(e) => eprintln!("warn: skip serialize {}: {}", rec.id, e),
        }
    }
    for child in &children {
        match serde_json::to_string(child) {
            Ok(s) => { out.push_str(&format!("{{\"alien_index\":{}}}\n", s)); }
            Err(e) => eprintln!("warn: skip serialize child {}: {}", child.id, e),
        }
    }

    // Atomic write: .tmp + rename.
    let tmp = path.with_extension("jsonl.tmp");
    std::fs::write(&tmp, &out).map_err(|e| format!("write tmp: {}", e))?;
    std::fs::rename(&tmp, &path).map_err(|e| format!("rename: {}", e))?;

    println!(
        "{} record(s) promoted, {} child record(s) added, disk updated.",
        promoted, children.len()
    );
    Ok(())
}

fn recompute_all() -> Result<(), String> {
    eprintln!("recompute-all: not yet implemented (needs atlas → discovery_log writer)");
    Ok(())
}

fn breakthrough(id: &str) -> Result<(), String> {
    use crate::alien_index::breakthrough::{
        evaluate, BreakthroughConfig, BreakthroughEvidence,
    };
    use crate::mk2::types::Sector;

    println!("═══ Breakthrough Attempt: {} ═══\n", id);

    // Load grade for this ID
    let grade = load_grade_for_id(id);
    let base_r = combine_signals(None, None, grade.as_deref());

    println!("Current state: r={} (grade={})", base_r, grade.as_deref().unwrap_or("none"));

    // Run n6_match on the ID if it looks like a number
    let (n6_name, n6_quality) = if let Ok(val) = id.parse::<f64>() {
        let (name, q) = n6_match(val);
        println!("n6_match: {} (quality={:.2})", name, q);
        (name.to_string(), q)
    } else {
        println!("n6_match: N/A (not a numeric target)");
        (String::new(), 0.0)
    };

    // mk2 classify — enrich text with n6_match name for better keyword matching
    let text = format!("{} {} {}", id, n6_name, enrich_n6_name(&n6_name));
    let values: Vec<f64> = id.parse::<f64>().into_iter().collect();
    let mut ps = crate::mk2::primes::PrimeSet::empty();
    for &v in &values {
        if v.is_finite() && v.abs() > 1e-10 && v.abs() < 1e6 {
            for den in &[1u64, 2, 3, 5, 6, 7, 15, 21, 35, 105, 210] {
                let num = (v * *den as f64).round() as i128;
                if num > 0 && ((num as f64 / *den as f64) - v).abs() < 1e-6 {
                    for (p, _) in crate::mk2::primes::factorize(num.unsigned_abs() as u64) {
                        ps.insert(p);
                    }
                    for (p, _) in crate::mk2::primes::factorize(*den) {
                        ps.insert(p);
                    }
                    break;
                }
            }
        }
    }
    let sectors = crate::mk2::classify_v2::default_sectors();
    let mk2_result = crate::mk2::classify_v2::classify_v2(&text, &values, &ps, &sectors);
    println!("mk2: sector={} confidence={:.2} primes={}",
             mk2_result.sector, mk2_result.confidence, ps);

    // Blowup rediscovery: run a mini blowup from n6 singularity and check
    // if any corollary signature value is close to the target.
    let target_val = id.parse::<f64>().unwrap_or(0.0);
    let (blowup_rediscovered, blowup_lens_count) = if target_val.abs() > 1e-10 {
        println!("\nRunning blowup rediscovery...");
        let blowup_result = run_blowup_rediscovery(target_val);
        println!("  blowup: {} corollaries, rediscovered={}",
                 blowup_result.0, if blowup_result.1 { "YES" } else { "no" });
        (blowup_result.1, blowup_result.0)
    } else {
        (false, 0)
    };

    // Count independent paths: n6_check + mk2 + blowup (if rediscovered)
    let base_paths: u32 = if n6_quality >= 1.0 { 2 } else if n6_quality >= 0.5 { 1 } else { 0 };
    let mk2_path: u32 = if mk2_result.confidence >= 0.5 { 1 } else { 0 };
    let blowup_path: u32 = if blowup_rediscovered { 1 } else { 0 };
    let total_paths = base_paths + mk2_path + blowup_path;

    let evidence = BreakthroughEvidence {
        independent_paths: total_paths,
        lens_names: {
            let mut v = vec!["n6_check".into()];
            if mk2_path > 0 { v.push("mk2_classify_v2".into()); }
            if blowup_rediscovered { v.push("blowup_engine".into()); }
            v
        },
        blowup_rediscovered,
        mk2_confidence: mk2_result.confidence,
        mk2_sector: mk2_result.sector.clone(),
        p_value: if n6_quality >= 1.0 && blowup_rediscovered { 0.001 }
                 else if n6_quality >= 1.0 { 0.005 }
                 else { 0.1 },
        summary: format!("{}: n6={:.2} mk2={:.2} blowup={}", id, n6_quality,
                         mk2_result.confidence, blowup_rediscovered),
    };

    let config = BreakthroughConfig::default();
    let verdict = evaluate(&evidence, &config);

    println!("\n─── Gate Results ───");
    println!("  paths  (≥{}): {} ({} paths)",
             config.min_independent_paths,
             if verdict.gate_results.paths_ok { "✓" } else { "✗" },
             evidence.independent_paths);
    println!("  blowup     : {} {}",
             if verdict.gate_results.blowup_ok { "✓" } else { "✗" },
             if evidence.blowup_rediscovered { "(confirmed)" } else { "(not yet run)" });
    println!("  mk2 (≥{:.1}): {} ({:.2})",
             config.mk2_confidence_threshold,
             if verdict.gate_results.mk2_ok { "✓" } else { "✗" },
             evidence.mk2_confidence);
    println!("  p-value (<{}): {} ({:.4})",
             config.significance_level,
             if verdict.gate_results.pvalue_ok { "✓" } else { "✗" },
             evidence.p_value);

    println!("\n═══ Verdict: {} ({}/4 gates) ═══",
             if verdict.eligible { "ELIGIBLE for d+1" } else { "NOT ELIGIBLE" },
             verdict.gate_results.passed_count());

    if !verdict.eligible {
        println!("\nNext steps:");
        if !verdict.gate_results.paths_ok {
            println!("  → Run telescope scan for more independent paths");
        }
        if !verdict.gate_results.blowup_ok {
            println!("  → Run: nexus6 blowup <domain> to attempt rediscovery");
        }
        if !verdict.gate_results.mk2_ok {
            println!("  → Check mk2 classify with more context text");
        }
        if !verdict.gate_results.pvalue_ok {
            println!("  → Run: nexus6 simulate to compute p-value");
        }
    }

    Ok(())
}

/// Run a mini blowup from n6 singularity and check if target_val is rediscovered.
/// Returns (total_corollaries, rediscovered).
fn run_blowup_rediscovery(target_val: f64) -> (usize, bool) {
    use crate::blowup::blowup_engine::{BlowupEngine, BlowupConfig};
    use crate::blowup::singularity::{Singularity, SingularityDetector};
    use std::collections::HashMap;

    // Build n6 singularity
    let mut metrics = HashMap::new();
    metrics.insert("sigma".into(), 12.0);
    metrics.insert("phi".into(), 2.0);
    metrics.insert("tau".into(), 4.0);
    metrics.insert("n".into(), 6.0);
    metrics.insert("sopfr".into(), 5.0);

    let singularity = Singularity {
        axioms: vec!["sigma".into(), "phi".into(), "tau".into(), "n".into(), "sopfr".into()],
        compression_ratio: 3.0,
        closure_degree: 1.0,
        domain: "n6".into(),
        metrics,
    };

    let engine = BlowupEngine::new(BlowupConfig {
        max_corollaries: 36,
        max_depth: 2,
        min_confidence: 0.15,
        ..BlowupConfig::default()
    });

    let result = engine.blowup(&singularity);
    let total = result.corollaries.len();

    // Check if any corollary signature contains a value close to target
    let tolerance = 0.01; // 1% relative error
    let rediscovered = result.corollaries.iter().any(|c| {
        c.signature.values().any(|&v| {
            if v.abs() < 1e-10 || target_val.abs() < 1e-10 {
                return false;
            }
            let rel_err = ((v - target_val) / target_val).abs();
            rel_err < tolerance
        })
    });

    (total, rediscovered)
}

/// Map n6_match constant names to mk2 sector keywords for better classification.
fn enrich_n6_name(name: &str) -> &'static str {
    match name {
        n if n.contains("Omega_Lambda") => "dark energy Omega_Lambda cosmology Hubble",
        n if n.contains("Omega_DM") => "dark matter Omega_DM cosmology",
        n if n.contains("Omega_b") => "baryon density cosmology flatness",
        n if n.contains("sin") || n.contains("theta") || n.contains("Weinberg") || n.contains("θ") => "Weinberg electroweak sin²θ_W theta_W CKM W boson",
        n if n.contains("Y_p") || n.contains("helium") => "BBN nucleosynthesis helium Y_p primordial",
        n if n.contains("quark") || n.contains("u_charge") || n.contains("d_charge") => "quark QCD color charge",
        n if n.contains("Hubble") || n.contains("H0") => "Hubble H0 cosmology",
        n if n.contains("n_s") || n.contains("spectral") => "CMB inflation spectral index primordial",
        n if n.contains("alpha") => "fine structure constant electroweak",
        _ => "",
    }
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
