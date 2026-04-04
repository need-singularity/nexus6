//! NEXUS-6 Hook Engine (Rust) — ~5ms per invocation
//!
//! 모든 Claude Code 훅에서 호출되는 단일 바이너리.
//! - 심링크 체크 + 자동 복구
//! - 숫자 n6_check + EXACT 자동 기록
//! - 미처리 발견 조회
//!
//! Usage:
//!   cat $INPUT | nexus6_hook --mode pre-commit
//!   cat $INPUT | nexus6_hook --mode post-edit
//!   cat $INPUT | nexus6_hook --mode post-bash
//!   cat $INPUT | nexus6_hook --mode agent
//!   nexus6_hook --mode pending

use std::env;
use std::fs;
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::process::Command;

use nexus6::config::NexusConfig;
use nexus6::verifier::n6_check::n6_match;
use serde_json::{json, Value};

// ═══ 심링크 체크 ═══

fn get_repo_root() -> Option<PathBuf> {
    let output = Command::new("git")
        .args(["rev-parse", "--show-toplevel"])
        .output()
        .ok()?;
    if output.status.success() {
        Some(PathBuf::from(
            String::from_utf8_lossy(&output.stdout).trim(),
        ))
    } else {
        None
    }
}

fn ensure_symlinks() -> Option<String> {
    let repo = get_repo_root()?;
    let shared = repo.join(".shared");
    let nexus_shared = repo.join("../nexus6/shared");

    if shared.is_symlink() && shared.exists() {
        return None; // OK
    }

    if shared.is_symlink() && !shared.exists() {
        // 깨진 심링크
        let _ = fs::remove_file(&shared);
        if nexus_shared.exists() {
            #[cfg(unix)]
            {
                let _ = std::os::unix::fs::symlink("../nexus6/shared", &shared);
            }
            return Some("🔧 NEXUS-6: 깨진 .shared 심링크 자동 복구 완료".into());
        }
        return Some(
            "❌ NEXUS-6: .shared 심링크 깨짐 + nexus6 없음. bash ~/Dev/nexus6/setup-symlinks.sh 실행 후 세션 재시작 필요"
                .into(),
        );
    }

    if !shared.exists() {
        if nexus_shared.exists() {
            #[cfg(unix)]
            {
                let _ = std::os::unix::fs::symlink("../nexus6/shared", &shared);
            }
            return Some("🔧 NEXUS-6: .shared 심링크 자동 생성 완료".into());
        }
        return Some(
            "❌ NEXUS-6: .shared 없음 + nexus6 없음. bash ~/Dev/nexus6/setup-symlinks.sh 실행 후 세션 재시작 필요"
                .into(),
        );
    }

    None
}

// ═══ 숫자 추출 ═══

fn extract_numbers(text: &str) -> Vec<f64> {
    let re_pattern = regex_lite::Regex::new(r"\b(\d+\.?\d*)\b").unwrap();
    let mut nums: Vec<f64> = re_pattern
        .find_iter(text)
        .filter_map(|m| m.as_str().parse::<f64>().ok())
        .filter(|&v| v > 1.0 && v < 100000.0)
        .collect();
    nums.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    nums.dedup();
    nums.truncate(20);
    nums
}

// ═══ 로그 로테이션 ═══

/// Rotate a log file if it exceeds `max_bytes`.
/// Renames .jsonl → .jsonl.1, .jsonl.1 → .jsonl.2, etc., keeping at most `max_files`.
fn rotate_log_if_needed(path: &Path, max_bytes: u64, max_files: usize) {
    let size = match fs::metadata(path) {
        Ok(m) => m.len(),
        Err(_) => return, // file doesn't exist yet — nothing to rotate
    };
    if size < max_bytes {
        return;
    }

    let path_str = path.to_string_lossy().to_string();

    // Shift existing rotated files: .N → .N+1  (drop oldest if > max_files)
    for i in (1..max_files).rev() {
        let src = format!("{}.{}", path_str, i);
        let dst = format!("{}.{}", path_str, i + 1);
        let _ = fs::rename(&src, &dst);
    }

    // Current file → .1
    let _ = fs::rename(&path_str, format!("{}.1", path_str));
    // A fresh file will be created on next append
}

// ═══ 발견 기록 ═══

fn discovery_log_path() -> PathBuf {
    let home = env::var("HOME").unwrap_or_default();
    PathBuf::from(home).join("Dev/nexus6/shared/discovery_log.jsonl")
}

/// Rotate a log file if it exceeds max_bytes.
/// Renames .jsonl -> .jsonl.1, .jsonl.1 -> .jsonl.2, etc., keeping at most max_files rotated copies.
fn rotate_log_if_needed(path: &str, max_bytes: u64, max_files: usize) {
    let meta = match fs::metadata(path) {
        Ok(m) => m,
        Err(_) => return,
    };
    if meta.len() <= max_bytes {
        return;
    }

    // Shift existing rotated files: .N -> .N+1 (highest first)
    for i in (1..max_files).rev() {
        let src = format!("{}.{}", path, i);
        let dst = format!("{}.{}", path, i + 1);
        let _ = fs::rename(&src, &dst);
    }

    // Rotate current file to .1
    let _ = fs::rename(path, format!("{}.1", path));

    // Delete overflow file if it exists
    let overflow = format!("{}.{}", path, max_files + 1);
    let _ = fs::remove_file(&overflow);
}

fn record_discovery(value: f64, constant: &str, source: &str) {
    let path = discovery_log_path();
    let cfg = NexusConfig::load();
    rotate_log_if_needed(
        path.to_str().unwrap_or(""),
        cfg.log_rotation_max_bytes(),
        cfg.log_rotation_max_files(),
    );
    let entry = json!({
        "timestamp": chrono_now(),
        "value": format!("{}", value),
        "constant": constant,
        "source": source,
        "processed": false
    });
    if let Ok(mut file) = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
    {
        use std::io::Write;
        let _ = writeln!(file, "{}", entry);
    }
}

fn chrono_now() -> String {
    // 간단한 타임스탬프 (외부 crate 없이)
    let output = Command::new("date")
        .args(["+%Y-%m-%dT%H:%M:%S"])
        .output();
    match output {
        Ok(o) => String::from_utf8_lossy(&o.stdout).trim().to_string(),
        Err(_) => "unknown".into(),
    }
}

// ═══ 스캔 + 자동 기록 ═══

struct ScanResult {
    exact: Vec<String>,
    close: Vec<String>,
}

fn scan_numbers(numbers: &[f64], source: &str) -> ScanResult {
    let mut exact = Vec::new();
    let mut close = Vec::new();

    for &v in numbers {
        let (name, quality) = n6_match(v);
        if quality >= 1.0 {
            exact.push(format!("{}={}", v, name));
            record_discovery(v, name, source);
        } else if quality >= 0.8 {
            close.push(format!("{}≈{}", v, name));
        }
    }

    ScanResult { exact, close }
}

fn build_message(result: &ScanResult, extra: Option<&str>) -> Option<String> {
    if result.exact.is_empty() && result.close.is_empty() && extra.is_none() {
        return None;
    }

    let mut parts = Vec::new();

    if !result.exact.is_empty() {
        let items: Vec<&str> = result.exact.iter().map(|s| s.as_str()).take(5).collect();
        parts.push(format!(
            "🔭 NEXUS-6 EXACT (자동기록됨): {}",
            items.join(", ")
        ));
        parts.push("⚠️ 필수: README/가설문서에 반영".into());
    }

    if !result.close.is_empty() {
        let items: Vec<&str> = result.close.iter().map(|s| s.as_str()).take(5).collect();
        parts.push(format!("📐 CLOSE: {}", items.join(", ")));
    }

    if let Some(e) = extra {
        parts.push(e.to_string());
    }

    Some(parts.join(" | "))
}

// ═══ 모드별 처리 ═══

fn mode_pre_commit(input: &Value) -> Option<String> {
    let cmd = input
        .pointer("/tool_input/command")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if !cmd.starts_with("git commit") {
        return None;
    }
    let output = Command::new("git")
        .args(["diff", "--cached", "--numstat"])
        .output()
        .ok()?;
    let diff = String::from_utf8_lossy(&output.stdout);
    let nums = extract_numbers(&diff);
    if nums.is_empty() {
        return None;
    }
    let result = scan_numbers(&nums, "pre-commit");
    build_message(&result, None)
}

fn mode_post_edit(input: &Value) -> Option<String> {
    let fp = input
        .pointer("/tool_input/file_path")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if fp.is_empty() {
        return None;
    }
    let path = Path::new(fp);
    if !path.is_file() {
        return None;
    }
    let ext = path.extension().and_then(|e| e.to_str()).unwrap_or("");
    if !["md", "json", "toml", "yaml", "yml", "py"].contains(&ext) {
        return None;
    }
    let content = fs::read_to_string(path).ok()?;
    let nums = extract_numbers(&content);
    if nums.is_empty() {
        return None;
    }
    let fname = path.file_name().and_then(|n| n.to_str()).unwrap_or("?");
    let result = scan_numbers(&nums, &format!("post-edit:{}", fname));
    build_message(&result, None)
}

fn mode_post_bash(input: &Value) -> Option<String> {
    let cmd = input
        .pointer("/tool_input/command")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    // python/cargo만
    if !cmd.contains("python3") && !cmd.contains("python") && !cmd.contains("cargo run") {
        return None;
    }
    // nexus6 자체 실행이면 스킵
    if cmd.contains("nexus6") {
        return None;
    }

    let stdout = input
        .pointer("/tool_response/stdout")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if stdout.is_empty() {
        return None;
    }

    let nums = extract_numbers(stdout);
    if nums.is_empty() {
        return None;
    }

    let src = if cmd.len() > 50 { &cmd[..50] } else { cmd };
    let result = scan_numbers(&nums, &format!("post-bash:{}", src));
    build_message(&result, None)
}

fn mode_agent(input: &Value) -> Option<String> {
    let prompt = input
        .pointer("/tool_input/prompt")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    let keywords = [
        "탐색", "분석", "검증", "scan", "analyze", "verify", "발견", "패턴", "상수", "가설",
        "hypothesis", "proof", "n=6", "golden", "bridge", "DFS", "렌즈",
    ];

    let prompt_lower = prompt.to_lowercase();
    let matched = keywords.iter().any(|kw| prompt_lower.contains(&kw.to_lowercase()));

    if !matched {
        return None;
    }

    // 미처리 발견 수
    let pending = count_pending();
    let mut msg =
        "🔭 NEXUS-6: 탐색/분석 에이전트 — import nexus6 필수. 발견 시 즉시 기록.".to_string();
    if pending > 0 {
        msg.push_str(&format!(" | 미처리 발견 {}건 — 에이전트에서 처리 권고", pending));
    }

    Some(msg)
}

fn count_pending() -> usize {
    let path = discovery_log_path();
    if !path.exists() {
        return 0;
    }
    fs::read_to_string(&path)
        .unwrap_or_default()
        .lines()
        .filter(|l| !l.is_empty())
        .filter_map(|l| serde_json::from_str::<Value>(l).ok())
        .filter(|v| v.get("processed").and_then(|p| p.as_bool()) == Some(false))
        .count()
}

// ═══ 성장 스캔 (리포별 .growth/scan.py 디스패치) ═══

fn growth_cooldown_path() -> PathBuf {
    let home = env::var("HOME").unwrap_or_default();
    PathBuf::from(home).join("Dev/nexus6/shared/.growth_last_scan")
}

fn growth_registry_path() -> PathBuf {
    let home = env::var("HOME").unwrap_or_default();
    PathBuf::from(home).join("Dev/nexus6/shared/growth-registry.json")
}

fn is_growth_cooldown_active(cooldown_secs: u64) -> bool {
    let path = growth_cooldown_path();
    if let Ok(meta) = fs::metadata(&path) {
        if let Ok(modified) = meta.modified() {
            if let Ok(elapsed) = modified.elapsed() {
                return elapsed.as_secs() < cooldown_secs;
            }
        }
    }
    false
}

fn touch_growth_cooldown() {
    let path = growth_cooldown_path();
    let _ = fs::write(&path, chrono_now());
}

fn session_snapshot_path() -> PathBuf {
    let home = env::var("HOME").unwrap_or_default();
    PathBuf::from(home).join("Dev/nexus6/shared/.growth_session_snapshot.json")
}

fn count_lens_implemented() -> (usize, usize) {
    let home = env::var("HOME").unwrap_or_default();
    let lens_dir = PathBuf::from(&home).join("Dev/nexus6/src/telescope/lenses");
    if !lens_dir.is_dir() {
        return (0, 0);
    }
    let mut total = 0usize;
    let mut implemented = 0usize;
    if let Ok(entries) = fs::read_dir(&lens_dir) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.ends_with(".rs") || name == "mod.rs" {
                continue;
            }
            total += 1;
            if let Ok(content) = fs::read_to_string(entry.path()) {
                let has_scan = content.contains("fn scan(");
                let has_metrics = content.contains(".insert(") || content.contains("findings.push") || content.contains("score");
                let lines = content.lines().filter(|l| {
                    let t = l.trim();
                    !t.is_empty() && !t.starts_with("//")
                }).count();
                if has_scan && has_metrics && lines > 20 {
                    implemented += 1;
                }
            }
        }
    }
    (implemented, total)
}

fn count_laws() -> usize {
    let home = env::var("HOME").unwrap_or_default();
    // Try anima first, then check repo-local
    let paths = [
        PathBuf::from(&home).join("Dev/anima/anima/config/consciousness_laws.json"),
    ];
    for p in &paths {
        if let Ok(content) = fs::read_to_string(p) {
            if let Ok(v) = serde_json::from_str::<Value>(&content) {
                if let Some(n) = v.pointer("/_meta/total_laws").and_then(|v| v.as_u64()) {
                    return n as usize;
                }
            }
        }
    }
    0
}

fn count_hub_modules() -> usize {
    let home = env::var("HOME").unwrap_or_default();
    let hub = PathBuf::from(&home).join("Dev/anima/anima/src/consciousness_hub.py");
    if let Ok(content) = fs::read_to_string(&hub) {
        // Count registry entries (lines with ('module', 'Class', [...]))
        content.matches("'type': 'command'").count()
            + content.lines().filter(|l| {
                let t = l.trim();
                t.starts_with("'") && t.contains("': (")
            }).count()
    } else {
        0
    }
}

fn load_or_create_session_snapshot() -> Value {
    let path = session_snapshot_path();
    if path.exists() {
        // Check if this session's snapshot (created within last process lifetime)
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(v) = serde_json::from_str::<Value>(&content) {
                return v;
            }
        }
    }
    // Create new snapshot
    let (lens_impl, lens_total) = count_lens_implemented();
    let laws = count_laws();
    let modules = count_hub_modules();
    let snapshot = json!({
        "lens_impl": lens_impl,
        "lens_total": lens_total,
        "laws": laws,
        "modules": modules,
        "created": chrono_now(),
    });
    let _ = fs::write(&path, serde_json::to_string(&snapshot).unwrap_or_default());
    snapshot
}

fn delta_str(current: usize, baseline: usize) -> String {
    if current > baseline {
        format!("(+{})", current - baseline)
    } else {
        String::new()
    }
}

fn nexus6_status_banner() -> String {
    let (lens_impl, lens_total) = count_lens_implemented();
    let laws = count_laws();
    let modules = count_hub_modules();

    let snap = load_or_create_session_snapshot();
    let s_lens = snap.get("lens_impl").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
    let s_laws = snap.get("laws").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
    let s_mods = snap.get("modules").and_then(|v| v.as_u64()).unwrap_or(0) as usize;

    let d_lens = delta_str(lens_impl, s_lens);
    let d_laws = delta_str(laws, s_laws);
    let d_mods = delta_str(modules, s_mods);

    let reg = growth_registry_path();
    let total_opps: usize = if reg.exists() {
        fs::read_to_string(&reg)
            .ok()
            .and_then(|s| serde_json::from_str::<Value>(&s).ok())
            .and_then(|v| v.as_object().map(|o| {
                o.values()
                    .filter_map(|v| v.get("opportunities").and_then(|n| n.as_u64()))
                    .sum::<u64>() as usize
            }))
            .unwrap_or(0)
    } else {
        0
    };

    let growth_str = if total_opps > 0 {
        format!(" 🌱{}건", total_opps)
    } else {
        String::new()
    };

    format!(
        "🔭 NEXUS-6 🔭{}/{}{} ⚖️{}법칙{} 🧠{}모듈{}{}",
        lens_impl, lens_total, d_lens,
        laws, d_laws,
        modules, d_mods,
        growth_str
    )
}

fn mode_growth_scan(_input: &Value) -> Option<String> {
    // 30분 쿨다운 — 배너만 출력
    if is_growth_cooldown_active(1800) {
        return Some(nexus6_status_banner());
    }

    let repo = get_repo_root()?;
    let scan_py = repo.join(".growth/scan.py");
    let scan_sh = repo.join(".growth/scan.sh");

    let (cmd, args): (&str, Vec<&str>) = if scan_py.is_file() {
        ("python3", vec![scan_py.to_str()?])
    } else if scan_sh.is_file() {
        ("bash", vec![scan_sh.to_str()?])
    } else {
        return None; // 이 리포에 성장 스캔 없음
    };

    touch_growth_cooldown();

    let output = Command::new(cmd)
        .args(&args)
        .current_dir(&repo)
        .output()
        .ok()?;

    if !output.status.success() {
        return None;
    }

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if stdout.is_empty() {
        return None;
    }

    // scan.py는 JSON {"opportunities": [...]} 또는 plain text 출력
    if let Ok(parsed) = serde_json::from_str::<Value>(&stdout) {
        let opps = parsed.get("opportunities").and_then(|v| v.as_array())?;
        if opps.is_empty() {
            return None;
        }

        // 레지스트리 업데이트
        let repo_name = repo.file_name()?.to_str()?;
        update_registry(repo_name, opps.len(), &chrono_now());

        let mut lines = vec![
            nexus6_status_banner(),
            format!("🌱 성장 기회 {}건:", opps.len()),
        ];
        for opp in opps.iter().take(5) {
            let typ = opp.get("type").and_then(|v| v.as_str()).unwrap_or("?");
            let desc = opp.get("description").and_then(|v| v.as_str()).unwrap_or("?");
            let prio = opp.get("priority").and_then(|v| v.as_str()).unwrap_or("MED");
            lines.push(format!("  [{}] {}: {}", prio, typ, desc));
        }
        Some(lines.join("\n"))
    } else if !stdout.is_empty() {
        Some(format!("🌱 {}", stdout))
    } else {
        None
    }
}

fn update_registry(repo_name: &str, count: usize, timestamp: &str) {
    let path = growth_registry_path();
    let mut registry: Value = if path.exists() {
        fs::read_to_string(&path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_else(|| json!({}))
    } else {
        json!({})
    };

    registry[repo_name] = json!({
        "last_scan": timestamp,
        "opportunities": count,
    });

    let _ = fs::write(&path, serde_json::to_string_pretty(&registry).unwrap_or_default());
}

fn mode_growth_report() -> Option<String> {
    let path = growth_registry_path();
    if !path.exists() {
        return Some("🌱 성장 레지스트리 없음 — 아직 스캔 실행 안 됨".into());
    }

    let registry: Value = fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())?;

    let obj = registry.as_object()?;
    if obj.is_empty() {
        return Some("🌱 등록된 리포 없음".into());
    }

    let mut lines = vec!["🌱 전 리포 성장 현황:".to_string()];
    let mut total = 0usize;
    for (repo, info) in obj {
        let count = info.get("opportunities").and_then(|v| v.as_u64()).unwrap_or(0);
        let ts = info.get("last_scan").and_then(|v| v.as_str()).unwrap_or("?");
        total += count as usize;
        let icon = if count > 0 { "🔄" } else { "✅" };
        lines.push(format!("  {} {} — {}건 ({})", icon, repo, count, &ts[..10.min(ts.len())]));
    }
    lines.push(format!("  총 {}건", total));

    Some(lines.join("\n"))
}

fn mode_pending() -> Option<String> {
    let path = discovery_log_path();
    if !path.exists() {
        return None;
    }

    let entries: Vec<Value> = fs::read_to_string(&path)
        .unwrap_or_default()
        .lines()
        .filter(|l| !l.is_empty())
        .filter_map(|l| serde_json::from_str::<Value>(l).ok())
        .filter(|v| v.get("processed").and_then(|p| p.as_bool()) == Some(false))
        .collect();

    if entries.is_empty() {
        return None;
    }

    let mut lines = vec![format!("⚠️ 미처리 NEXUS-6 발견 {}건:", entries.len())];
    for e in entries.iter().rev().take(10) {
        let val = e.get("value").and_then(|v| v.as_str()).unwrap_or("?");
        let con = e.get("constant").and_then(|v| v.as_str()).unwrap_or("?");
        let src = e.get("source").and_then(|v| v.as_str()).unwrap_or("?");
        let ts = e.get("timestamp").and_then(|v| v.as_str()).unwrap_or("?");
        lines.push(format!("  {}={} ({}, {})", val, con, src, &ts[..10.min(ts.len())]));
    }
    lines.push("필수: atlas/README에 반영 후 processed=true로 갱신".into());

    Some(lines.join("\n"))
}

// ═══ 메인 ═══

fn main() {
    let args: Vec<String> = env::args().collect();

    let mode = args
        .iter()
        .position(|a| a == "--mode")
        .and_then(|i| args.get(i + 1))
        .map(|s| s.as_str())
        .unwrap_or("");

    // 1. 심링크 체크 (항상)
    if let Some(symlink_msg) = ensure_symlinks() {
        let out = json!({"systemMessage": symlink_msg});
        println!("{}", out);
        if symlink_msg.contains("❌") {
            // 복구 불가 → 여기서 종료
            return;
        }
    }

    // 2. stdin 불필요 모드
    match mode {
        "pending" => {
            if let Some(msg) = mode_pending() {
                println!("{}", json!({"systemMessage": msg}));
            }
            return;
        }
        "growth-report" => {
            if let Some(msg) = mode_growth_report() {
                println!("{}", json!({"systemMessage": msg}));
            }
            return;
        }
        _ => {}
    }

    // 3. stdin 읽기
    let mut input_str = String::new();
    if io::stdin().read_to_string(&mut input_str).is_err() {
        return;
    }

    let input: Value = match serde_json::from_str(&input_str) {
        Ok(v) => v,
        Err(_) => return,
    };

    // 4. 모드 디스패치
    let msg = match mode {
        "pre-commit" => mode_pre_commit(&input),
        "post-edit" => mode_post_edit(&input),
        "post-bash" => mode_post_bash(&input),
        "agent" => mode_agent(&input),
        "growth-scan" => mode_growth_scan(&input),
        _ => None,
    };

    if let Some(m) = msg {
        println!("{}", json!({"systemMessage": m}));
    }
}
