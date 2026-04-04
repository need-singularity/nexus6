//! n6-guard — 시스템 공용 리소스 가드 데몬 (v2)
//!
//! 모든 Dev 프로젝트의 CPU/메모리/디스크를 감시하고 자동 관리.
//!
//! Features:
//!   1. CPU/메모리 스로틀링 (SIGSTOP/SIGCONT)
//!   2. 빌드 큐잉 — 동시 cargo build 직렬화
//!   3. 디스크 감시 — target/ 및 로그 비대화 감지/정리
//!   4. macOS 알림 — 스로틀 발생 시 알림센터 푸시
//!   5. 프로세스 자동 재시작 — 크래시 감지 → respawn
//!   6. 프로젝트간 자원 양보 — idle 시 다른 프로젝트에 코어 할당
//!   7. 사용량 히스토리 — 시계열 기록
//!   8. 로그 로테이션 — guard + 프로젝트 로그 관리
//!   9. nice 자동 조절 — 우선순위별 renice
//!
//! Usage:
//!   n6_guard                    # foreground
//!   n6_guard --daemon           # 백그라운드 데몬
//!   n6_guard --status           # 현재 감시 상태
//!   n6_guard --stop             # 데몬 중지
//!   n6_guard --history          # 사용량 히스토리 요약
//!   n6_guard --disk             # 디스크 사용량 리포트
//!
//! Config: ~/.config/n6-guard.toml

use std::collections::HashMap;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant, SystemTime};

use serde::Deserialize;

// ════════════════════════════════════════════════════════════════
// Config
// ════════════════════════════════════════════════════════════════

#[derive(Debug, Clone, Deserialize)]
struct GuardConfig {
    #[serde(default = "default_interval")]
    interval_sec: u64,

    #[serde(default)]
    global: GlobalLimits,

    #[serde(default)]
    process: HashMap<String, ProcessLimits>,

    #[serde(default)]
    build_queue: BuildQueueConfig,

    #[serde(default)]
    disk: DiskConfig,

    #[serde(default)]
    notify: NotifyConfig,

    #[serde(default)]
    auto_restart: AutoRestartConfig,

    #[serde(default)]
    history: HistoryConfig,

    #[serde(default)]
    log_rotation: LogRotationConfig,
}

#[derive(Debug, Clone, Deserialize)]
struct GlobalLimits {
    #[serde(default = "default_max_cpu")]
    max_cpu_percent: f64,
    #[serde(default = "default_max_mem")]
    max_memory_mb: usize,
    #[serde(default = "default_min_free")]
    min_free_memory_mb: usize,
    #[serde(default = "default_watch")]
    watch: Vec<String>,
    /// Dev directory to scan for projects (default: ~/Dev)
    #[serde(default = "default_dev_dir")]
    dev_dir: String,
    /// OOM fallback: when watch-list is empty/insufficient during memory pressure,
    /// SIGSTOP top-RSS non-protected processes (default: true)
    #[serde(default = "default_true")]
    oom_fallback_enabled: bool,
    /// Minimum RSS (MB) for a process to be eligible as fallback target (default: 500)
    #[serde(default = "default_oom_min_rss")]
    oom_fallback_min_rss_mb: usize,
    /// Max fallback processes to stop per trigger (default: 3)
    #[serde(default = "default_oom_max_kills")]
    oom_fallback_max_kills: usize,
    /// Extra process names to protect from OOM fallback (never stop)
    #[serde(default)]
    oom_fallback_protect: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
struct ProcessLimits {
    max_cpu_percent: Option<f64>,
    max_memory_mb: Option<usize>,
    #[serde(default = "default_priority")]
    priority: u8,
    /// nice value override (-20..20, default: none)
    nice: Option<i8>,
}

#[derive(Debug, Clone, Deserialize)]
struct BuildQueueConfig {
    /// Enable build queuing (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// Max concurrent cargo/rustc processes (default: 1)
    #[serde(default = "default_one")]
    max_concurrent_builds: usize,
}

#[derive(Debug, Clone, Deserialize)]
struct DiskConfig {
    /// Enable disk monitoring (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// Max target/ directory size in MB before warning (default: 5120 = 5GB)
    #[serde(default = "default_target_max")]
    max_target_mb: usize,
    /// Max single log file size in MB (default: 100)
    #[serde(default = "default_log_max")]
    max_log_file_mb: usize,
    /// Auto-clean target/ when over limit (default: false)
    #[serde(default)]
    auto_clean_target: bool,
    /// Check interval in loop iterations (default: 60 = every 5min at 5s interval)
    #[serde(default = "default_disk_interval")]
    check_every_n: usize,
}

#[derive(Debug, Clone, Deserialize)]
struct NotifyConfig {
    /// Enable macOS notification center (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// Min seconds between notifications (default: 60)
    #[serde(default = "default_notify_cooldown")]
    cooldown_sec: u64,
}

#[derive(Debug, Clone, Deserialize)]
struct AutoRestartConfig {
    /// Enable auto-restart of crashed services (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// Services to monitor and restart
    #[serde(default)]
    services: Vec<ServiceDef>,
}

#[derive(Debug, Clone, Deserialize)]
struct ServiceDef {
    /// Name for display
    name: String,
    /// PID file path (supports ~ expansion)
    pid_file: String,
    /// Command to restart
    restart_cmd: String,
    /// Max restart attempts per hour (default: 3)
    #[serde(default = "default_max_restarts")]
    max_restarts_per_hour: usize,
}

#[derive(Debug, Clone, Deserialize)]
struct HistoryConfig {
    /// Enable usage history logging (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// History file path
    #[serde(default = "default_history_path")]
    path: String,
    /// Max history file size in MB (default: 50)
    #[serde(default = "default_history_max")]
    max_size_mb: usize,
    /// Record every N loop iterations (default: 12 = every 1min at 5s interval)
    #[serde(default = "default_history_interval")]
    record_every_n: usize,
}

#[derive(Debug, Clone, Deserialize)]
struct LogRotationConfig {
    /// Enable log rotation (default: true)
    #[serde(default = "default_true")]
    enabled: bool,
    /// Max log file size in MB (default: 10)
    #[serde(default = "default_rotation_max")]
    max_size_mb: usize,
    /// Max rotated files to keep (default: 3)
    #[serde(default = "default_rotation_keep")]
    max_files: usize,
    /// Additional log directories to manage
    #[serde(default)]
    extra_log_dirs: Vec<String>,
}

// ── Defaults ───────────────────────────────────────────────────

fn default_interval() -> u64 { 5 }
fn default_max_cpu() -> f64 { 400.0 }
fn default_max_mem() -> usize { 16384 }
fn default_min_free() -> usize { 2048 }
fn default_oom_min_rss() -> usize { 500 }
fn default_oom_max_kills() -> usize { 3 }
fn default_priority() -> u8 { 5 }
fn default_true() -> bool { true }
fn default_one() -> usize { 1 }
fn default_target_max() -> usize { 5120 }
fn default_log_max() -> usize { 100 }
fn default_disk_interval() -> usize { 60 }
fn default_notify_cooldown() -> u64 { 60 }
fn default_max_restarts() -> usize { 3 }
fn default_history_max() -> usize { 50 }
fn default_history_interval() -> usize { 12 }
fn default_rotation_max() -> usize { 10 }
fn default_rotation_keep() -> usize { 3 }
fn default_dev_dir() -> String {
    std::env::var("HOME").map(|h| format!("{}/Dev", h)).unwrap_or_else(|_| "/tmp/Dev".into())
}
fn default_watch() -> Vec<String> {
    vec!["nexus6".into(), "anima".into(), "sedi".into(),
         "fathom".into(), "brainwire".into(), "hexa".into()]
}
fn default_history_path() -> String {
    std::env::var("HOME").map(|h| format!("{}/.config/n6-guard-history.jsonl", h))
        .unwrap_or_else(|_| "/tmp/n6-guard-history.jsonl".into())
}

impl Default for GlobalLimits {
    fn default() -> Self {
        Self {
            max_cpu_percent: default_max_cpu(),
            max_memory_mb: default_max_mem(),
            min_free_memory_mb: default_min_free(),
            watch: default_watch(),
            dev_dir: default_dev_dir(),
            oom_fallback_enabled: true,
            oom_fallback_min_rss_mb: default_oom_min_rss(),
            oom_fallback_max_kills: default_oom_max_kills(),
            oom_fallback_protect: vec![],
        }
    }
}

impl Default for BuildQueueConfig {
    fn default() -> Self { Self { enabled: true, max_concurrent_builds: 1 } }
}
impl Default for DiskConfig {
    fn default() -> Self { Self {
        enabled: true, max_target_mb: 5120, max_log_file_mb: 100,
        auto_clean_target: false, check_every_n: 60,
    }}
}
impl Default for NotifyConfig {
    fn default() -> Self { Self { enabled: true, cooldown_sec: 60 } }
}
impl Default for AutoRestartConfig {
    fn default() -> Self { Self { enabled: true, services: vec![] } }
}
impl Default for HistoryConfig {
    fn default() -> Self { Self {
        enabled: true, path: default_history_path(),
        max_size_mb: 50, record_every_n: 12,
    }}
}
impl Default for LogRotationConfig {
    fn default() -> Self { Self {
        enabled: true, max_size_mb: 10, max_files: 3, extra_log_dirs: vec![],
    }}
}
impl Default for GuardConfig {
    fn default() -> Self { Self {
        interval_sec: default_interval(),
        global: GlobalLimits::default(),
        process: HashMap::new(),
        build_queue: BuildQueueConfig::default(),
        disk: DiskConfig::default(),
        notify: NotifyConfig::default(),
        auto_restart: AutoRestartConfig::default(),
        history: HistoryConfig::default(),
        log_rotation: LogRotationConfig::default(),
    }}
}

// ════════════════════════════════════════════════════════════════
// Process info
// ════════════════════════════════════════════════════════════════

#[derive(Debug, Clone)]
struct ProcInfo {
    pid: u32,
    name: String,
    cpu_percent: f64,
    rss_mb: usize,
    stopped: bool,
    nice: i32,
}

fn get_all_procs() -> Vec<ProcInfo> {
    let output = Command::new("ps")
        .args(["-eo", "pid,pcpu,rss,state,ni,comm"])
        .output().ok();
    let text = output.as_ref()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();

    let mut procs = Vec::new();
    for line in text.lines().skip(1) {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() < 6 { continue; }
        let comm = parts[5..].join(" ");
        let basename = comm.rsplit('/').next().unwrap_or(&comm).to_string();
        procs.push(ProcInfo {
            pid: parts[0].parse().unwrap_or(0),
            cpu_percent: parts[1].parse().unwrap_or(0.0),
            rss_mb: parts[2].parse::<usize>().unwrap_or(0) / 1024,
            stopped: parts[3].contains('T'),
            nice: parts[4].parse().unwrap_or(0),
            name: basename,
        });
    }
    procs
}

fn get_monitored_procs(watch: &[String], all: &[ProcInfo]) -> Vec<ProcInfo> {
    all.iter()
        .filter(|p| watch.iter().any(|w| p.name.to_lowercase().contains(&w.to_lowercase())))
        .cloned()
        .collect()
}

/// Names that must NEVER be SIGSTOP'd (kernel/GUI/session-critical).
/// Stopping these would freeze UI, break audio, kill SSH session, etc.
const SYSTEM_PROTECTED: &[&str] = &[
    // kernel / init
    "kernel_task", "launchd", "kextd", "diskarbitrationd",
    // window server / GUI
    "windowserver", "loginwindow", "systemuiserver", "dock", "finder",
    "controlcenter", "notificationcenter", "spotlight", "wallpaper",
    // audio / bluetooth / network
    "coreaudiod", "bluetoothd", "bluetoothuserd", "mdnsresponder",
    "configd", "networkd", "wifiagent", "airportd",
    // spotlight / indexing
    "mds", "mds_stores", "mdworker", "mdworker_shared", "corespotlightd",
    // logging / power
    "syslogd", "powerd", "thermalmonitord", "backupd",
    // ssh / terminal session anchors
    "sshd", "ssh-agent", "ssh",
    // this guard itself
    "n6_guard",
    // user's active tools — don't kill the hand that feeds
    "claude", "claude-code", "code", "cursor", "terminal", "iterm",
    "iterm2", "ghostty", "warp", "alacritty", "kitty", "tmux", "zsh", "bash", "fish",
];

fn is_system_protected(name: &str, extra: &[String]) -> bool {
    let lower = name.to_lowercase();
    if SYSTEM_PROTECTED.iter().any(|p| lower == *p || lower.contains(p)) {
        return true;
    }
    extra.iter().any(|p| lower.contains(&p.to_lowercase()))
}

/// OOM fallback: top-RSS non-protected processes, excluding already-targeted pids.
fn get_fallback_targets(
    all: &[ProcInfo],
    cfg: &GlobalLimits,
    exclude_pids: &std::collections::HashSet<u32>,
    self_pid: u32,
) -> Vec<ProcInfo> {
    let mut candidates: Vec<ProcInfo> = all.iter()
        .filter(|p| {
            !p.stopped
                && p.pid != self_pid
                && p.pid > 1
                && p.rss_mb >= cfg.oom_fallback_min_rss_mb
                && !exclude_pids.contains(&p.pid)
                && !is_system_protected(&p.name, &cfg.oom_fallback_protect)
        })
        .cloned()
        .collect();
    candidates.sort_by(|a, b| b.rss_mb.cmp(&a.rss_mb));
    candidates.truncate(cfg.oom_fallback_max_kills);
    candidates
}

fn get_build_procs(all: &[ProcInfo]) -> Vec<ProcInfo> {
    all.iter()
        .filter(|p| {
            let n = p.name.to_lowercase();
            (n.contains("cargo") || n.contains("rustc") || n.contains("cc1") || n.contains("linker"))
                && p.cpu_percent > 5.0
        })
        .cloned()
        .collect()
}

fn free_memory_mb() -> usize {
    let output = Command::new("vm_stat").output().ok();
    let text = output.as_ref()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();

    let page_size: usize = 16384;
    let mut free = 0usize;
    let mut inactive = 0usize;
    let mut purgeable = 0usize;

    for line in text.lines() {
        if line.starts_with("Pages free:") { free = parse_val(line); }
        else if line.starts_with("Pages inactive:") { inactive = parse_val(line); }
        else if line.starts_with("Pages purgeable:") { purgeable = parse_val(line); }
    }
    (free + inactive + purgeable) * page_size / (1024 * 1024)
}

fn parse_val(line: &str) -> usize {
    line.split(':').nth(1).unwrap_or("").trim().trim_end_matches('.').parse().unwrap_or(0)
}

// ════════════════════════════════════════════════════════════════
// Actions
// ════════════════════════════════════════════════════════════════

fn stop_process(pid: u32) {
    send_signal(pid, 17); // SIGSTOP on macOS
}

fn cont_process(pid: u32) {
    send_signal(pid, 19); // SIGCONT on macOS
}

fn send_signal(pid: u32, sig: i32) {
    Command::new("kill")
        .args([&format!("-{}", sig), &pid.to_string()])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .output().ok();
}

fn renice_process(pid: u32, nice_val: i32) {
    Command::new("renice")
        .args([&nice_val.to_string(), "-p", &pid.to_string()])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .output().ok();
}

fn check_pid_alive(pid: &str) -> bool {
    Command::new("kill").args(["-0", pid])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status().map(|s| s.success()).unwrap_or(false)
}

// ════════════════════════════════════════════════════════════════
// Logging
// ════════════════════════════════════════════════════════════════

fn log_action(msg: &str) {
    let ts = humantime::format_rfc3339_seconds(SystemTime::now());
    let line = format!("[{}] {}\n", ts, msg);
    eprint!("{}", line);
    if let Some(path) = log_path() {
        if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(path) {
            let _ = f.write_all(line.as_bytes());
        }
    }
}

fn home() -> String { std::env::var("HOME").unwrap_or_default() }

fn log_path() -> Option<PathBuf> {
    Some(PathBuf::from(home()).join(".config/n6-guard.log"))
}

fn pid_path() -> PathBuf {
    PathBuf::from(home()).join(".config/n6-guard.pid")
}

// ════════════════════════════════════════════════════════════════
// Feature 1: Build Queue
// ════════════════════════════════════════════════════════════════

struct BuildQueue {
    stopped_builds: HashMap<u32, Instant>,
}

impl BuildQueue {
    fn new() -> Self { Self { stopped_builds: HashMap::new() } }

    fn enforce(&mut self, cfg: &BuildQueueConfig, all_procs: &[ProcInfo]) {
        if !cfg.enabled { return; }

        let builds = get_build_procs(all_procs);
        let active: Vec<&ProcInfo> = builds.iter().filter(|p| !p.stopped).collect();

        // Resume builds that were stopped if under limit now
        if active.len() < cfg.max_concurrent_builds {
            let to_resume: Vec<u32> = self.stopped_builds.keys()
                .copied()
                .filter(|pid| builds.iter().any(|p| p.pid == *pid && p.stopped))
                .take(cfg.max_concurrent_builds - active.len())
                .collect();
            for pid in to_resume {
                log_action(&format!("BUILD-QUEUE RESUME pid={}", pid));
                cont_process(pid);
                self.stopped_builds.remove(&pid);
            }
        }

        // Stop excess builds
        if active.len() > cfg.max_concurrent_builds {
            let mut sorted = active.clone();
            sorted.sort_by(|a, b| a.cpu_percent.partial_cmp(&b.cpu_percent).unwrap_or(std::cmp::Ordering::Equal));
            for excess in sorted.iter().take(active.len() - cfg.max_concurrent_builds) {
                log_action(&format!("BUILD-QUEUE STOP {} (pid={}) — {} concurrent builds > limit {}",
                    excess.name, excess.pid, active.len(), cfg.max_concurrent_builds));
                stop_process(excess.pid);
                self.stopped_builds.insert(excess.pid, Instant::now());
            }
        }

        // Cleanup exited
        self.stopped_builds.retain(|pid, _| builds.iter().any(|p| p.pid == *pid));
    }
}

// ════════════════════════════════════════════════════════════════
// Feature 2: Disk Monitor
// ════════════════════════════════════════════════════════════════

fn check_disk(cfg: &DiskConfig, dev_dir: &str, notify_cfg: &NotifyConfig, last_notify: &mut Instant) {
    if !cfg.enabled { return; }

    let entries = match fs::read_dir(dev_dir) {
        Ok(e) => e,
        Err(_) => return,
    };

    for entry in entries.flatten() {
        let project_path = entry.path();
        if !project_path.is_dir() { continue; }

        let target_dir = project_path.join("target");
        if target_dir.is_dir() {
            let size_mb = dir_size_mb(&target_dir);
            if size_mb > cfg.max_target_mb {
                let msg = format!("DISK: {}/target = {}MB (limit: {}MB)",
                    project_path.file_name().unwrap_or_default().to_string_lossy(),
                    size_mb, cfg.max_target_mb);
                log_action(&msg);

                if cfg.auto_clean_target {
                    log_action(&format!("DISK: auto-cleaning {}", target_dir.display()));
                    let _ = Command::new("cargo")
                        .args(["clean"])
                        .current_dir(&project_path)
                        .output();
                } else {
                    notify_macos(&msg, notify_cfg, last_notify);
                }
            }
        }

        // Check log files
        check_log_files(&project_path, cfg.max_log_file_mb);
    }
}

fn check_log_files(dir: &Path, max_mb: usize) {
    let walk = |p: &Path| -> Vec<PathBuf> {
        let mut logs = Vec::new();
        if let Ok(entries) = fs::read_dir(p) {
            for e in entries.flatten() {
                let path = e.path();
                if path.extension().map_or(false, |ext| ext == "log") {
                    logs.push(path);
                }
            }
        }
        logs
    };

    for log in walk(dir) {
        if let Ok(meta) = fs::metadata(&log) {
            let size_mb = meta.len() as usize / (1024 * 1024);
            if size_mb > max_mb {
                log_action(&format!("DISK: large log {} = {}MB — truncating",
                    log.display(), size_mb));
                // Keep last 1000 lines
                if let Ok(content) = fs::read_to_string(&log) {
                    let lines: Vec<&str> = content.lines().collect();
                    let keep = &lines[lines.len().saturating_sub(1000)..];
                    let _ = fs::write(&log, keep.join("\n"));
                }
            }
        }
    }
}

fn dir_size_mb(path: &Path) -> usize {
    let output = Command::new("du")
        .args(["-sm", &path.to_string_lossy()])
        .output().ok();
    output.and_then(|o| {
        String::from_utf8_lossy(&o.stdout)
            .split_whitespace().next()
            .and_then(|s| s.parse::<usize>().ok())
    }).unwrap_or(0)
}

fn print_disk_report(dev_dir: &str) {
    println!("═══ n6-guard disk report ═══\n");
    println!("{:<20} {:>10} {:>10}", "PROJECT", "target/", "logs/");
    println!("{}", "─".repeat(44));

    let entries = match fs::read_dir(dev_dir) {
        Ok(e) => e,
        Err(_) => { println!("Cannot read {}", dev_dir); return; }
    };

    let mut total_target = 0usize;
    for entry in entries.flatten() {
        let p = entry.path();
        if !p.is_dir() { continue; }
        let name = p.file_name().unwrap_or_default().to_string_lossy().to_string();
        let target = p.join("target");
        let t_size = if target.is_dir() { dir_size_mb(&target) } else { 0 };
        total_target += t_size;

        if t_size > 0 {
            println!("{:<20} {:>8}MB {:>10}", name, t_size, "-");
        }
    }
    println!("{}", "─".repeat(44));
    println!("{:<20} {:>8}MB", "TOTAL", total_target);
}

// ════════════════════════════════════════════════════════════════
// Feature 3: macOS Notifications
// ════════════════════════════════════════════════════════════════

fn notify_macos(msg: &str, cfg: &NotifyConfig, last: &mut Instant) {
    if !cfg.enabled { return; }
    if last.elapsed() < Duration::from_secs(cfg.cooldown_sec) { return; }

    let script = format!(
        "display notification \"{}\" with title \"n6-guard\" sound name \"Basso\"",
        msg.replace('"', "'")
    );
    Command::new("osascript")
        .args(["-e", &script])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .spawn().ok();

    *last = Instant::now();
}

// ════════════════════════════════════════════════════════════════
// Feature 4: Auto-restart
// ════════════════════════════════════════════════════════════════

struct RestartTracker {
    attempts: HashMap<String, Vec<Instant>>,
}

impl RestartTracker {
    fn new() -> Self { Self { attempts: HashMap::new() } }

    fn check_and_restart(&mut self, cfg: &AutoRestartConfig) {
        if !cfg.enabled { return; }

        for svc in &cfg.services {
            let pid_file = expand_tilde(&svc.pid_file);

            // Read PID file
            let pid_str = match fs::read_to_string(&pid_file) {
                Ok(s) => s.trim().to_string(),
                Err(_) => continue, // No PID file = not expected to be running
            };

            if pid_str.is_empty() { continue; }

            // Check if alive
            if check_pid_alive(&pid_str) { continue; }

            // Dead — check restart limit
            let attempts = self.attempts.entry(svc.name.clone()).or_default();
            let hour_ago = Instant::now() - Duration::from_secs(3600);
            attempts.retain(|t| *t > hour_ago);

            if attempts.len() >= svc.max_restarts_per_hour {
                log_action(&format!("AUTO-RESTART: {} crashed but {} restarts in last hour — skipping",
                    svc.name, attempts.len()));
                continue;
            }

            // Restart
            log_action(&format!("AUTO-RESTART: {} (pid={}) is dead — restarting: {}",
                svc.name, pid_str, svc.restart_cmd));

            let parts: Vec<&str> = svc.restart_cmd.split_whitespace().collect();
            if let Some((cmd, args)) = parts.split_first() {
                let _ = Command::new(cmd)
                    .args(args)
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .spawn();
            }

            // Remove stale PID file
            let _ = fs::remove_file(&pid_file);
            attempts.push(Instant::now());
        }
    }
}

fn expand_tilde(path: &str) -> String {
    if path.starts_with('~') {
        path.replacen('~', &home(), 1)
    } else {
        path.to_string()
    }
}

// ════════════════════════════════════════════════════════════════
// Feature 5: Resource Yielding (dynamic nice)
// ════════════════════════════════════════════════════════════════

fn apply_nice_adjustments(cfg: &GuardConfig, monitored: &[ProcInfo]) {
    // Separate active (CPU > 1%) from idle
    let active: Vec<&ProcInfo> = monitored.iter().filter(|p| p.cpu_percent > 1.0 && !p.stopped).collect();
    let idle: Vec<&ProcInfo> = monitored.iter().filter(|p| p.cpu_percent <= 1.0 && !p.stopped).collect();

    for proc in &active {
        // Check per-process nice override
        if let Some(plim) = cfg.process.get(&proc.name) {
            if let Some(target_nice) = plim.nice {
                if proc.nice != target_nice as i32 {
                    log_action(&format!("NICE: {} (pid={}) {} → {}",
                        proc.name, proc.pid, proc.nice, target_nice));
                    renice_process(proc.pid, target_nice as i32);
                }
                continue;
            }
        }

        // Dynamic: if many projects active, raise nice for low-priority ones
        if active.len() > 2 {
            let pri = cfg.process.get(&proc.name).map(|p| p.priority).unwrap_or(5);
            let target_nice = if pri >= 7 { 10 } else if pri >= 5 { 5 } else { 0 };
            if proc.nice != target_nice {
                renice_process(proc.pid, target_nice);
            }
        }
    }

    // Idle processes get low priority
    for proc in &idle {
        if proc.nice < 10 {
            renice_process(proc.pid, 10);
        }
    }
}

// ════════════════════════════════════════════════════════════════
// Feature 6: Usage History
// ════════════════════════════════════════════════════════════════

fn record_history(cfg: &HistoryConfig, monitored: &[ProcInfo], free_mem: usize) {
    if !cfg.enabled { return; }

    let ts = humantime::format_rfc3339_seconds(SystemTime::now());
    let total_cpu: f64 = monitored.iter().map(|p| p.cpu_percent).sum();
    let total_rss: usize = monitored.iter().map(|p| p.rss_mb).sum();

    // Per-project summary
    let mut by_name: HashMap<&str, (f64, usize)> = HashMap::new();
    for p in monitored {
        let entry = by_name.entry(&p.name).or_default();
        entry.0 += p.cpu_percent;
        entry.1 += p.rss_mb;
    }

    let projects: Vec<String> = by_name.iter()
        .map(|(name, (cpu, mem))| format!("\"{}\":{{\"cpu\":{:.1},\"mem\":{}}}", name, cpu, mem))
        .collect();

    let record = format!(
        "{{\"ts\":\"{}\",\"free_mb\":{},\"total_cpu\":{:.1},\"total_rss\":{},\"procs\":{},\"projects\":{{{}}}}}\n",
        ts, free_mem, total_cpu, total_rss, monitored.len(), projects.join(",")
    );

    if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&cfg.path) {
        let _ = f.write_all(record.as_bytes());
    }

    // Size check
    if let Ok(meta) = fs::metadata(&cfg.path) {
        if meta.len() > (cfg.max_size_mb as u64) * 1024 * 1024 {
            rotate_file(&cfg.path, 3);
        }
    }
}

fn print_history_summary(cfg: &HistoryConfig) {
    println!("═══ n6-guard usage history ═══\n");

    let content = match fs::read_to_string(&cfg.path) {
        Ok(c) => c,
        Err(_) => { println!("No history file found at {}", cfg.path); return; }
    };

    let lines: Vec<&str> = content.lines().collect();
    let recent = &lines[lines.len().saturating_sub(60)..]; // Last ~5 min

    let mut max_cpu = 0.0f64;
    let mut max_rss = 0usize;
    let mut min_free = usize::MAX;
    let mut count = 0;
    let mut sum_cpu = 0.0f64;
    let mut sum_rss = 0usize;

    for line in recent {
        // Simple parsing without serde
        if let Some(cpu) = extract_json_f64(line, "total_cpu") {
            sum_cpu += cpu;
            if cpu > max_cpu { max_cpu = cpu; }
        }
        if let Some(rss) = extract_json_usize(line, "total_rss") {
            sum_rss += rss;
            if rss > max_rss { max_rss = rss; }
        }
        if let Some(free) = extract_json_usize(line, "free_mb") {
            if free < min_free { min_free = free; }
        }
        count += 1;
    }

    if count > 0 {
        println!("Records:    {} (last ~5 min)", count);
        println!("Avg CPU:    {:.1}%", sum_cpu / count as f64);
        println!("Max CPU:    {:.1}%", max_cpu);
        println!("Avg RSS:    {}MB", sum_rss / count);
        println!("Max RSS:    {}MB", max_rss);
        println!("Min Free:   {}MB", if min_free == usize::MAX { 0 } else { min_free });
        println!("\nTotal history: {} records", lines.len());
    } else {
        println!("No recent records.");
    }
}

fn extract_json_f64(line: &str, key: &str) -> Option<f64> {
    let pattern = format!("\"{}\":", key);
    let start = line.find(&pattern)? + pattern.len();
    let rest = &line[start..];
    let end = rest.find(|c: char| c == ',' || c == '}' || c == ' ')?;
    rest[..end].parse().ok()
}

fn extract_json_usize(line: &str, key: &str) -> Option<usize> {
    extract_json_f64(line, key).map(|f| f as usize)
}

// ════════════════════════════════════════════════════════════════
// Feature 7: Log Rotation
// ════════════════════════════════════════════════════════════════

fn rotate_logs(cfg: &LogRotationConfig) {
    if !cfg.enabled { return; }

    let max_bytes = (cfg.max_size_mb as u64) * 1024 * 1024;

    // Guard's own log
    if let Some(path) = log_path() {
        if let Ok(meta) = fs::metadata(&path) {
            if meta.len() > max_bytes {
                rotate_file(&path.to_string_lossy(), cfg.max_files);
            }
        }
    }

    // nexus6 logs
    let n6_log_dir = format!("{}/.nexus6", home());
    rotate_dir_logs(&n6_log_dir, max_bytes, cfg.max_files);

    // Extra dirs
    for dir in &cfg.extra_log_dirs {
        let dir = expand_tilde(dir);
        rotate_dir_logs(&dir, max_bytes, cfg.max_files);
    }
}

fn rotate_dir_logs(dir: &str, max_bytes: u64, max_files: usize) {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().map_or(false, |e| e == "log") {
            if let Ok(meta) = fs::metadata(&path) {
                if meta.len() > max_bytes {
                    rotate_file(&path.to_string_lossy(), max_files);
                }
            }
        }
    }
}

fn rotate_file(path: &str, max_files: usize) {
    log_action(&format!("LOG-ROTATE: {}", path));

    // Shift existing rotated files
    for i in (1..max_files).rev() {
        let from = format!("{}.{}", path, i);
        let to = format!("{}.{}", path, i + 1);
        let _ = fs::rename(&from, &to);
    }

    // Rotate current
    let _ = fs::rename(path, &format!("{}.1", path));

    // Delete oldest
    let oldest = format!("{}.{}", path, max_files + 1);
    let _ = fs::remove_file(&oldest);
}

// ════════════════════════════════════════════════════════════════
// Ghost reaper
// ════════════════════════════════════════════════════════════════

fn reap_stale_pid_files() {
    let dir = format!("{}/.nexus6", home());
    let entries = match fs::read_dir(&dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.extension().map_or(false, |e| e == "pid") {
            if let Ok(pid_str) = fs::read_to_string(&path) {
                let pid_str = pid_str.trim();
                if !pid_str.is_empty() && !check_pid_alive(pid_str) {
                    log_action(&format!("REAP stale PID: {} (pid={})", path.display(), pid_str));
                    let _ = fs::remove_file(&path);
                }
            }
        }
    }
}

// ════════════════════════════════════════════════════════════════
// Main Loop
// ════════════════════════════════════════════════════════════════

fn guard_loop(cfg: &GuardConfig) {
    log_action(&format!("n6-guard v2 started — interval={}s cpu_limit={:.0}% mem_limit={}MB min_free={}MB",
        cfg.interval_sec, cfg.global.max_cpu_percent, cfg.global.max_memory_mb, cfg.global.min_free_memory_mb));
    log_action(&format!("features: build_queue={} disk={} notify={} auto_restart={} history={} log_rotation={} oom_fallback={}",
        cfg.build_queue.enabled, cfg.disk.enabled, cfg.notify.enabled,
        cfg.auto_restart.enabled, cfg.history.enabled, cfg.log_rotation.enabled,
        cfg.global.oom_fallback_enabled));
    if cfg.global.oom_fallback_enabled {
        log_action(&format!("oom_fallback: min_rss={}MB max_kills={} kill_escalation_below={}MB extra_protect={:?}",
            cfg.global.oom_fallback_min_rss_mb, cfg.global.oom_fallback_max_kills,
            cfg.global.min_free_memory_mb / 2, cfg.global.oom_fallback_protect));
    }
    log_action(&format!("watching: {:?}", cfg.global.watch));

    // Shutdown handler
    let shutdown = Arc::new(AtomicBool::new(false));
    let shutdown_clone = shutdown.clone();
    let _ = ctrlc::set_handler(move || { shutdown_clone.store(true, Ordering::SeqCst); });

    let mut stopped_pids: HashMap<u32, Instant> = HashMap::new();
    let mut fallback_stopped: HashMap<u32, (String, Instant)> = HashMap::new();
    let mut build_queue = BuildQueue::new();
    let mut restart_tracker = RestartTracker::new();
    let mut last_notify = Instant::now() - Duration::from_secs(120);
    let mut loop_count: usize = 0;

    loop {
        // Graceful shutdown
        if shutdown.load(Ordering::SeqCst) {
            log_action("shutdown — resuming all stopped processes");
            for (&pid, _) in &stopped_pids {
                cont_process(pid);
            }
            for (&pid, _) in &fallback_stopped {
                cont_process(pid);
            }
            for (&pid, _) in &build_queue.stopped_builds {
                cont_process(pid);
            }
            let _ = fs::remove_file(pid_path());
            log_action("n6-guard exited cleanly");
            std::process::exit(0);
        }

        let all_procs = get_all_procs();
        let monitored = get_monitored_procs(&cfg.global.watch, &all_procs);
        let free_mem = free_memory_mb();
        let total_cpu: f64 = monitored.iter().map(|p| p.cpu_percent).sum();
        let total_rss: usize = monitored.iter().map(|p| p.rss_mb).sum();

        let mem_critical = free_mem < cfg.global.min_free_memory_mb;
        let cpu_over = total_cpu > cfg.global.max_cpu_percent;
        let mem_over = total_rss > cfg.global.max_memory_mb;

        // ── Core throttling ──
        if mem_critical || cpu_over || mem_over {
            let mut targets: Vec<&ProcInfo> = monitored.iter()
                .filter(|p| !p.stopped)
                .collect();
            targets.sort_by(|a, b| {
                let pa = cfg.process.get(&a.name).map(|p| p.priority).unwrap_or(5);
                let pb = cfg.process.get(&b.name).map(|p| p.priority).unwrap_or(5);
                pb.cmp(&pa).then(b.cpu_percent.partial_cmp(&a.cpu_percent).unwrap_or(std::cmp::Ordering::Equal))
            });

            // Per-process limits
            for proc in &monitored {
                if proc.stopped { continue; }
                if let Some(plim) = cfg.process.get(&proc.name) {
                    let mem_ex = plim.max_memory_mb.map_or(false, |m| proc.rss_mb > m);
                    let cpu_ex = plim.max_cpu_percent.map_or(false, |c| proc.cpu_percent > c);
                    if mem_ex || cpu_ex {
                        let msg = format!("THROTTLE {} (pid={}) — cpu={:.1}% rss={}MB",
                            proc.name, proc.pid, proc.cpu_percent, proc.rss_mb);
                        log_action(&msg);
                        notify_macos(&msg, &cfg.notify, &mut last_notify);
                        stop_process(proc.pid);
                        stopped_pids.insert(proc.pid, Instant::now());
                    }
                }
            }

            // Global throttle
            let mut running_cpu = total_cpu;
            let mut running_rss = total_rss;
            for target in &targets {
                if running_cpu <= cfg.global.max_cpu_percent
                    && running_rss <= cfg.global.max_memory_mb
                    && !mem_critical { break; }

                if stopped_pids.contains_key(&target.pid) { continue; }

                let msg = format!("THROTTLE {} (pid={}) cpu={:.1}% rss={}MB [global: cpu={:.0}% rss={}MB free={}MB]",
                    target.name, target.pid, target.cpu_percent, target.rss_mb,
                    running_cpu, running_rss, free_mem);
                log_action(&msg);
                notify_macos(&msg, &cfg.notify, &mut last_notify);
                stop_process(target.pid);
                stopped_pids.insert(target.pid, Instant::now());
                running_cpu -= target.cpu_percent;
                running_rss -= target.rss_mb;
            }

            // ── OOM Fallback: watch-list can't relieve memory pressure ──
            // Triggers when free memory is below threshold regardless of whether
            // monitored procs exist. SIGSTOP halts further allocation; if free
            // memory drops below half the threshold, escalate to SIGTERM (kill)
            // to actually release RSS.
            if cfg.global.oom_fallback_enabled && mem_critical {
                let mut excluded: std::collections::HashSet<u32> =
                    stopped_pids.keys().copied().collect();
                excluded.extend(fallback_stopped.keys().copied());
                excluded.extend(build_queue.stopped_builds.keys().copied());
                let self_pid = std::process::id();
                let fallback = get_fallback_targets(
                    &all_procs, &cfg.global, &excluded, self_pid,
                );

                let kill_threshold = cfg.global.min_free_memory_mb / 2;
                let emergency = free_mem < kill_threshold;

                for target in &fallback {
                    let action = if emergency { "KILL" } else { "STOP" };
                    let msg = format!(
                        "OOM-FALLBACK {} {} (pid={}) rss={}MB [free={}MB < {}MB{}]",
                        action, target.name, target.pid, target.rss_mb,
                        free_mem, cfg.global.min_free_memory_mb,
                        if emergency { format!(", emergency<{}", kill_threshold) } else { String::new() },
                    );
                    log_action(&msg);
                    notify_macos(&msg, &cfg.notify, &mut last_notify);
                    if emergency {
                        send_signal(target.pid, 15); // SIGTERM
                    } else {
                        stop_process(target.pid);
                        fallback_stopped.insert(
                            target.pid,
                            (target.name.clone(), Instant::now()),
                        );
                    }
                }
            }
        } else {
            // Resume monitored procs
            let to_resume: Vec<u32> = stopped_pids.keys().copied()
                .filter(|pid| monitored.iter().any(|p| p.pid == *pid && p.stopped))
                .collect();
            for pid in to_resume {
                if let Some(p) = monitored.iter().find(|p| p.pid == pid) {
                    log_action(&format!("RESUME {} (pid={})", p.name, pid));
                }
                cont_process(pid);
                stopped_pids.remove(&pid);
            }

            // Resume OOM-fallback stopped procs (memory has recovered)
            let fb_to_resume: Vec<u32> = fallback_stopped.keys().copied()
                .filter(|pid| all_procs.iter().any(|p| p.pid == *pid && p.stopped))
                .collect();
            for pid in fb_to_resume {
                if let Some((name, _)) = fallback_stopped.get(&pid) {
                    log_action(&format!("OOM-RESUME {} (pid={})", name, pid));
                }
                cont_process(pid);
                fallback_stopped.remove(&pid);
            }
        }

        // ── Feature: Build Queue ──
        build_queue.enforce(&cfg.build_queue, &all_procs);

        // ── Feature: Nice adjustments ──
        apply_nice_adjustments(cfg, &monitored);

        // ── Feature: Auto-restart ──
        restart_tracker.check_and_restart(&cfg.auto_restart);

        // ── Feature: History ──
        if cfg.history.enabled && loop_count % cfg.history.record_every_n == 0 {
            record_history(&cfg.history, &monitored, free_mem);
        }

        // ── Feature: Disk monitor (less frequent) ──
        if cfg.disk.enabled && loop_count % cfg.disk.check_every_n == 0 {
            check_disk(&cfg.disk, &expand_tilde(&cfg.global.dev_dir), &cfg.notify, &mut last_notify);
        }

        // ── Feature: Log rotation (every 5 min) ──
        if cfg.log_rotation.enabled && loop_count % 60 == 0 {
            rotate_logs(&cfg.log_rotation);
        }

        // ── Ghost reaper ──
        stopped_pids.retain(|pid, ts| {
            let exists = monitored.iter().any(|p| p.pid == *pid);
            if !exists {
                log_action(&format!("REAP ghost pid={} (stopped {}s ago)", pid, ts.elapsed().as_secs()));
            }
            exists
        });
        fallback_stopped.retain(|pid, (name, ts)| {
            let exists = all_procs.iter().any(|p| p.pid == *pid);
            if !exists {
                log_action(&format!("REAP OOM-fallback ghost {} (pid={}, {}s ago)",
                    name, pid, ts.elapsed().as_secs()));
            }
            exists
        });
        reap_stale_pid_files();

        loop_count += 1;
        thread::sleep(Duration::from_secs(cfg.interval_sec));
    }
}

// ════════════════════════════════════════════════════════════════
// Config I/O
// ════════════════════════════════════════════════════════════════

fn config_path() -> PathBuf {
    PathBuf::from(home()).join(".config/n6-guard.toml")
}

fn load_config() -> GuardConfig {
    let path = config_path();
    match fs::read_to_string(&path) {
        Ok(s) => match toml::from_str(&s) {
            Ok(cfg) => cfg,
            Err(e) => {
                eprintln!("warning: config parse error: {} — using defaults", e);
                GuardConfig::default()
            }
        },
        Err(_) => {
            eprintln!("info: {} not found — using defaults", path.display());
            GuardConfig::default()
        }
    }
}

fn write_default_config() {
    let path = config_path();
    if path.exists() { return; }
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    let example = r#"# n6-guard v2 — system resource guard
# Config: ~/.config/n6-guard.toml

interval_sec = 5

[global]
max_cpu_percent = 400.0        # 4 cores (M3 = 8 cores)
max_memory_mb = 16384          # 16GB total RSS cap
min_free_memory_mb = 2048      # throttle if free < 2GB
dev_dir = "~/Dev"
watch = ["nexus6", "anima", "sedi", "fathom", "brainwire", "hexa"]

# ── OOM Fallback ──
# watch-list 밖 프로세스가 메모리를 폭주시킬 때 작동.
# min_free_memory_mb 이하면 RSS 상위 프로세스 SIGSTOP,
# min_free/2 이하면 SIGTERM으로 에스컬레이션.
oom_fallback_enabled = true
oom_fallback_min_rss_mb = 500      # 500MB 미만 프로세스는 후보 제외
oom_fallback_max_kills = 3         # 한 번에 최대 3개까지 정지/종료
oom_fallback_protect = []          # 추가 보호 프로세스명 (부분일치)

# ── Build Queue ──
[build_queue]
enabled = true
max_concurrent_builds = 1      # 동시 cargo build 1개만

# ── Disk Monitor ──
[disk]
enabled = true
max_target_mb = 5120           # target/ 5GB 초과 시 경고
max_log_file_mb = 100          # 로그파일 100MB 초과 시 truncate
auto_clean_target = false      # true면 자동 cargo clean
check_every_n = 60             # 60 loops = 5분마다

# ── macOS Notifications ──
[notify]
enabled = true
cooldown_sec = 60              # 알림 간 최소 간격

# ── Auto-restart ──
[auto_restart]
enabled = true
# services = [
#   { name = "nexus6-daemon", pid_file = "~/.nexus6/daemon.pid", restart_cmd = "nexus6 daemon", max_restarts_per_hour = 3 },
#   { name = "nexus6-loop",   pid_file = "~/.nexus6/loop.pid",   restart_cmd = "nexus6 loop",   max_restarts_per_hour = 3 },
# ]

# ── Usage History ──
[history]
enabled = true
max_size_mb = 50
record_every_n = 12            # 12 loops = 1분마다

# ── Log Rotation ──
[log_rotation]
enabled = true
max_size_mb = 10
max_files = 3
extra_log_dirs = ["~/.nexus6"]

# ── Per-process overrides ──
# [process.nexus6]
# max_cpu_percent = 200.0
# max_memory_mb = 4096
# priority = 3                 # lower = more protected
# nice = 0                     # manual nice override

# [process.anima]
# max_memory_mb = 8192
# priority = 7                 # higher = throttled first
# nice = 5
"#;
    let _ = fs::write(&path, example);
    eprintln!("created default config: {}", path.display());
}

// ════════════════════════════════════════════════════════════════
// Entrypoint
// ════════════════════════════════════════════════════════════════

fn print_status(cfg: &GuardConfig) {
    let all = get_all_procs();
    let monitored = get_monitored_procs(&cfg.global.watch, &all);
    let builds = get_build_procs(&all);
    let free = free_memory_mb();
    let total_cpu: f64 = monitored.iter().map(|p| p.cpu_percent).sum();
    let total_rss: usize = monitored.iter().map(|p| p.rss_mb).sum();

    println!("═══ n6-guard v2 status ═══");
    println!("Free memory:  {}MB (threshold: {}MB)", free, cfg.global.min_free_memory_mb);
    println!("Total CPU:    {:.1}% / {:.0}%", total_cpu, cfg.global.max_cpu_percent);
    println!("Total RSS:    {}MB / {}MB", total_rss, cfg.global.max_memory_mb);
    println!("Builds:       {} active (limit: {})", builds.len(), cfg.build_queue.max_concurrent_builds);
    println!();

    if monitored.is_empty() {
        println!("No monitored processes found.");
    } else {
        println!("{:<8} {:<20} {:>8} {:>8} {:>6} {:<8}", "PID", "NAME", "CPU%", "RSS(MB)", "NICE", "STATE");
        println!("{}", "─".repeat(62));
        for p in &monitored {
            println!("{:<8} {:<20} {:>8.1} {:>8} {:>6} {:<8}",
                p.pid, p.name, p.cpu_percent, p.rss_mb, p.nice,
                if p.stopped { "STOPPED" } else { "running" }
            );
        }
    }

    if !builds.is_empty() {
        println!("\n── Active builds ──");
        for b in &builds {
            println!("  pid={} {} cpu={:.1}%", b.pid, b.name, b.cpu_percent);
        }
    }

    // Daemon status
    if let Ok(pid_str) = fs::read_to_string(pid_path()) {
        let pid = pid_str.trim();
        if check_pid_alive(pid) {
            println!("\nDaemon: running (pid={})", pid);
        } else {
            println!("\nDaemon: dead (stale pid={})", pid);
        }
    } else {
        println!("\nDaemon: not running");
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    write_default_config();
    let cfg = load_config();

    if args.iter().any(|a| a == "--status" || a == "-s") {
        print_status(&cfg);
        return;
    }

    if args.iter().any(|a| a == "--history" || a == "-h") {
        print_history_summary(&cfg.history);
        return;
    }

    if args.iter().any(|a| a == "--disk") {
        print_disk_report(&expand_tilde(&cfg.global.dev_dir));
        return;
    }

    if args.iter().any(|a| a == "--stop") {
        if let Ok(pid_str) = fs::read_to_string(pid_path()) {
            if let Ok(pid) = pid_str.trim().parse::<u32>() {
                send_signal(pid, 15); // SIGTERM
                let _ = fs::remove_file(pid_path());
                println!("n6-guard stopped (pid={})", pid);
            }
        } else {
            println!("n6-guard is not running");
        }
        return;
    }

    if args.iter().any(|a| a == "--daemon" || a == "-d") {
        let exe = std::env::current_exe().unwrap();
        let child = Command::new(exe)
            .args(["--fg"])
            .stdout(std::process::Stdio::null())
            .stderr(std::process::Stdio::null())
            .spawn();
        match child {
            Ok(c) => {
                let _ = fs::write(pid_path(), c.id().to_string());
                println!("n6-guard v2 daemon started (pid={})", c.id());
            }
            Err(e) => eprintln!("failed to start daemon: {}", e),
        }
        return;
    }

    // Write PID file
    let _ = fs::write(pid_path(), std::process::id().to_string());

    // Foreground or --fg
    guard_loop(&cfg);
}
