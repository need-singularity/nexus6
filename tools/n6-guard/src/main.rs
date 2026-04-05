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

    #[serde(default)]
    task_scheduler: TaskSchedulerConfig,
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

// ── Task Scheduler Config ─────────────────────────────────────

#[derive(Debug, Clone, Deserialize)]
struct TaskSchedulerConfig {
    #[serde(default)]
    enabled: bool,
    #[serde(default = "default_max_concurrent")]
    max_concurrent: usize,
    #[serde(default = "default_task_mem")]
    max_task_memory_mb: usize,
    #[serde(default = "default_task_log_dir")]
    task_log_dir: String,
    #[serde(default)]
    tasks: Vec<TaskDef>,
}

#[derive(Debug, Clone, Deserialize)]
struct TaskDef {
    name: String,
    command: String,
    #[serde(default = "default_task_mode")]
    mode: String,           // "continuous" | "interval"
    #[serde(default)]
    interval_sec: u64,
    #[serde(default = "default_task_mem")]
    max_memory_mb: usize,
    #[serde(default = "default_priority")]
    priority: u8,
}

impl Default for TaskSchedulerConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            max_concurrent: 2,
            max_task_memory_mb: 2048,
            task_log_dir: default_task_log_dir(),
            tasks: vec![],
        }
    }
}

fn default_max_concurrent() -> usize { 2 }
fn default_task_mem() -> usize { 2048 }
fn default_task_log_dir() -> String {
    format!("{}/Library/Logs/nexus6", std::env::var("HOME").unwrap_or_default())
}
fn default_task_mode() -> String { "interval".into() }

// ── Defaults ───────────────────────────────────────────────────

fn default_interval() -> u64 { 5 }
fn default_max_cpu() -> f64 { 400.0 }
fn default_max_mem() -> usize { 16384 }
fn default_min_free() -> usize { 2048 }
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
        task_scheduler: TaskSchedulerConfig::default(),
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
// Feature 8: Task Scheduler (LaunchAgent 통합)
// ════════════════════════════════════════════════════════════════

struct TaskRunner {
    /// 실행 중인 태스크: name → (Child, start_time)
    running: HashMap<String, (std::process::Child, Instant)>,
    /// 마지막 실행 완료 시각: name → Instant
    last_run: HashMap<String, Instant>,
    /// burst 모드: 발견 시그널 수신 시 max_concurrent 일시 상향
    burst_until: Option<Instant>,
}

impl TaskRunner {
    fn new() -> Self {
        Self {
            running: HashMap::new(),
            last_run: HashMap::new(),
            burst_until: None,
        }
    }

    fn effective_max_concurrent(&self, base: usize) -> usize {
        if let Some(until) = self.burst_until {
            if Instant::now() < until {
                return (base + 2).min(4); // burst: +2 슬롯, 최대 4
            }
        }
        base
    }

    fn check_burst_signal(&mut self) {
        // burst 만료 체크
        if let Some(until) = self.burst_until {
            if Instant::now() >= until {
                log_action("TASK-SCHED: burst mode expired — back to normal");
                self.burst_until = None;
            }
        }
        // discovery_log.jsonl에 최근 60초 내 새 발견이 있으면 burst
        let sig_path = format!("{}/Dev/nexus6/shared/discovery_log.jsonl", home());
        if let Ok(meta) = fs::metadata(&sig_path) {
            if let Ok(modified) = meta.modified() {
                if let Ok(elapsed) = SystemTime::now().duration_since(modified) {
                    if elapsed < Duration::from_secs(60) {
                        if self.burst_until.is_none() {
                            log_action("TASK-SCHED: burst mode — discovery signal detected");
                        }
                        self.burst_until = Some(Instant::now() + Duration::from_secs(300)); // 5분간 burst
                    }
                }
            }
        }
    }

    fn tick(&mut self, cfg: &TaskSchedulerConfig, notify_cfg: &NotifyConfig, last_notify: &mut Instant) {
        if !cfg.enabled { return; }

        let log_dir = expand_tilde(&cfg.task_log_dir);
        let _ = fs::create_dir_all(&log_dir);

        // burst 시그널 확인
        self.check_burst_signal();

        // 1. 완료된 태스크 수거
        let mut finished = Vec::new();
        for (name, (child, start)) in &mut self.running {
            match child.try_wait() {
                Ok(Some(status)) => {
                    let elapsed = start.elapsed().as_secs();
                    log_action(&format!("TASK-DONE: {} — status={} elapsed={}s", name, status, elapsed));
                    finished.push(name.clone());
                }
                Ok(None) => {
                    // 아직 실행 중 — 메모리 체크
                    let pid = child.id();
                    let rss = get_proc_rss(pid);
                    let limit = cfg.tasks.iter()
                        .find(|t| t.name == *name)
                        .map(|t| t.max_memory_mb)
                        .unwrap_or(cfg.max_task_memory_mb);
                    if rss > limit {
                        log_action(&format!("TASK-OOM: {} (pid={}) rss={}MB > limit={}MB — killing",
                            name, pid, rss, limit));
                        let _ = child.kill();
                        finished.push(name.clone());
                        let msg = format!("태스크 {} 메모리 초과로 종료 ({}MB)", name, rss);
                        notify_macos(&msg, notify_cfg, last_notify);
                    }
                }
                Err(_) => {
                    finished.push(name.clone());
                }
            }
        }
        for name in &finished {
            self.running.remove(name);
            self.last_run.insert(name.clone(), Instant::now());
        }

        // 2. 새 태스크 시작 (우선순위순, 동시 실행 제한)
        let max_conc = self.effective_max_concurrent(cfg.max_concurrent);
        if self.running.len() >= max_conc { return; }

        // 우선순위 정렬 (낮을수록 우선)
        let mut ready: Vec<&TaskDef> = cfg.tasks.iter()
            .filter(|t| !self.running.contains_key(&t.name))
            .filter(|t| self.should_run(t))
            .collect();
        ready.sort_by_key(|t| t.priority);

        for task in ready {
            if self.running.len() >= max_conc { break; }
            self.spawn_task(task, &log_dir);
        }
    }

    fn should_run(&self, task: &TaskDef) -> bool {
        if task.mode == "continuous" {
            // continuous는 실행 중이 아니면 항상 시작
            return true;
        }
        // interval: 마지막 실행 후 interval_sec 경과했는지
        match self.last_run.get(&task.name) {
            None => true, // 한 번도 안 돌았음
            Some(last) => last.elapsed() >= Duration::from_secs(task.interval_sec),
        }
    }

    fn spawn_task(&mut self, task: &TaskDef, log_dir: &str) {
        let cmd = expand_tilde(&task.command);
        let log_file = format!("{}/{}.log", log_dir, task.name);

        let stdout = fs::OpenOptions::new()
            .create(true).append(true)
            .open(&log_file);
        let stderr = fs::OpenOptions::new()
            .create(true).append(true)
            .open(&format!("{}/{}-err.log", log_dir, task.name));

        let mut command = Command::new("bash");
        command.args(["-c", &cmd]);

        // nice 설정 — 우선순위 높으면 nice 낮게
        let nice_val = if task.priority <= 2 { 0 } else if task.priority <= 5 { 5 } else { 10 };
        command.env("GUARD_MANAGED", "1");

        if let (Ok(out), Ok(err)) = (stdout, stderr) {
            command.stdout(out).stderr(err);
        }

        match command.spawn() {
            Ok(child) => {
                let pid = child.id();
                log_action(&format!("TASK-START: {} (pid={}) nice={} cmd={}",
                    task.name, pid, nice_val, &cmd[..cmd.len().min(60)]));
                // renice after spawn
                renice_process(pid, nice_val);
                self.running.insert(task.name.clone(), (child, Instant::now()));
            }
            Err(e) => {
                log_action(&format!("TASK-FAIL: {} — {}", task.name, e));
                // 실패해도 last_run 기록해서 즉시 재시도 방지
                self.last_run.insert(task.name.clone(), Instant::now());
            }
        }
    }

    fn shutdown(&mut self) {
        for (name, (child, _)) in &mut self.running {
            log_action(&format!("TASK-SHUTDOWN: killing {}", name));
            let _ = child.kill();
        }
        self.running.clear();
    }

    fn print_status(&mut self, cfg: &TaskSchedulerConfig) {
        if !cfg.enabled {
            println!("\nTask scheduler: disabled");
            return;
        }
        let max_conc = self.effective_max_concurrent(cfg.max_concurrent);
        let burst = self.burst_until.map_or(false, |u| Instant::now() < u);
        println!("\n── Task Scheduler ── (slots: {}/{}{}) ──",
            self.running.len(), max_conc, if burst { " 🔥BURST" } else { "" });
        println!("{:<18} {:>6} {:>8} {:>10}", "TASK", "PID", "RSS(MB)", "UPTIME");
        println!("{}", "─".repeat(46));

        for (name, (child, start)) in &self.running {
            let pid = child.id();
            let rss = get_proc_rss(pid);
            let up = start.elapsed().as_secs();
            println!("{:<18} {:>6} {:>8} {:>8}s", name, pid, rss, up);
        }

        // 대기 중 태스크
        let waiting: Vec<&TaskDef> = cfg.tasks.iter()
            .filter(|t| !self.running.contains_key(&t.name))
            .collect();
        if !waiting.is_empty() {
            println!("\nWaiting:");
            for t in &waiting {
                let next_in = self.last_run.get(&t.name)
                    .map(|l| t.interval_sec.saturating_sub(l.elapsed().as_secs()))
                    .unwrap_or(0);
                println!("  {} — mode={} next_in={}s pri={}", t.name, t.mode, next_in, t.priority);
            }
        }
    }
}

fn get_proc_rss(pid: u32) -> usize {
    let output = Command::new("ps")
        .args(["-p", &pid.to_string(), "-o", "rss="])
        .output().ok();
    output.and_then(|o| {
        String::from_utf8_lossy(&o.stdout).trim().parse::<usize>().ok()
    }).unwrap_or(0) / 1024 // KB → MB
}

// ════════════════════════════════════════════════════════════════
// Main Loop
// ════════════════════════════════════════════════════════════════

fn guard_loop(cfg: &GuardConfig) {
    log_action(&format!("n6-guard v2 started — interval={}s cpu_limit={:.0}% mem_limit={}MB min_free={}MB",
        cfg.interval_sec, cfg.global.max_cpu_percent, cfg.global.max_memory_mb, cfg.global.min_free_memory_mb));
    log_action(&format!("features: build_queue={} disk={} notify={} auto_restart={} history={} log_rotation={}",
        cfg.build_queue.enabled, cfg.disk.enabled, cfg.notify.enabled,
        cfg.auto_restart.enabled, cfg.history.enabled, cfg.log_rotation.enabled));
    log_action(&format!("watching: {:?}", cfg.global.watch));

    // Shutdown handler
    let shutdown = Arc::new(AtomicBool::new(false));
    let shutdown_clone = shutdown.clone();
    let _ = ctrlc::set_handler(move || { shutdown_clone.store(true, Ordering::SeqCst); });

    let mut stopped_pids: HashMap<u32, Instant> = HashMap::new();
    let mut build_queue = BuildQueue::new();
    let mut restart_tracker = RestartTracker::new();
    let mut task_runner = TaskRunner::new();
    let mut last_notify = Instant::now() - Duration::from_secs(120);
    let mut loop_count: usize = 0;

    loop {
        // Graceful shutdown
        if shutdown.load(Ordering::SeqCst) {
            log_action("shutdown — resuming all stopped processes");
            for (&pid, _) in &stopped_pids {
                cont_process(pid);
            }
            for (&pid, _) in &build_queue.stopped_builds {
                cont_process(pid);
            }
            task_runner.shutdown();
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
        } else {
            // Resume
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

        // ── Feature: Task Scheduler ──
        task_runner.tick(&cfg.task_scheduler, &cfg.notify, &mut last_notify);

        // ── Ghost reaper ──
        stopped_pids.retain(|pid, ts| {
            let exists = monitored.iter().any(|p| p.pid == *pid);
            if !exists {
                log_action(&format!("REAP ghost pid={} (stopped {}s ago)", pid, ts.elapsed().as_secs()));
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

    // Task scheduler summary
    if cfg.task_scheduler.enabled {
        println!("\n── Task Scheduler ({} tasks, max_concurrent={}) ──",
            cfg.task_scheduler.tasks.len(), cfg.task_scheduler.max_concurrent);
        for t in &cfg.task_scheduler.tasks {
            println!("  {:<18} mode={:<10} interval={}s pri={} mem_limit={}MB",
                t.name, t.mode, t.interval_sec, t.priority, t.max_memory_mb);
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
