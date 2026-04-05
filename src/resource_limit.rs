//! Resource limiter — CPU thread cap + memory guard.
//!
//! Reads `[resource_limits]` from `~/.nexus6/config.toml`.
//! Call `init()` once at startup (before any rayon work).

use std::sync::OnceLock;
use tracing::{info, warn};

/// Runtime-loaded resource limits.
#[derive(Debug, Clone)]
pub struct ResourceLimits {
    /// Maximum rayon threads (0 = use all cores).
    pub max_threads: usize,
    /// Minimum free system memory in MB before allowing heavy work.
    pub min_free_memory_mb: usize,
    /// Maximum lens batch size per scan pass (0 = unlimited).
    pub scan_batch_size: usize,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_threads: 4,
            min_free_memory_mb: 2048,
            scan_batch_size: 0,
        }
    }
}

static LIMITS: OnceLock<ResourceLimits> = OnceLock::new();

/// Initialise resource limits from config and pin the rayon thread-pool.
/// Safe to call multiple times — only the first call takes effect.
pub fn init(limits: ResourceLimits) {
    let limits = LIMITS.get_or_init(|| {
        // Pin rayon global thread-pool
        let threads = if limits.max_threads == 0 {
            num_cpus()
        } else {
            limits.max_threads
        };
        if let Err(e) = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build_global()
        {
            warn!("rayon pool already initialised: {}", e);
        }
        info!(
            "resource_limit: threads={}, min_free_mem={}MB, batch={}",
            threads,
            limits.min_free_memory_mb,
            if limits.scan_batch_size == 0 { "unlimited".to_string() } else { limits.scan_batch_size.to_string() },
        );
        limits
    });
    let _ = limits;
}

/// Get the active limits (falls back to defaults if `init` was never called).
pub fn get() -> &'static ResourceLimits {
    LIMITS.get_or_init(ResourceLimits::default)
}

// ── Memory guard ───────────────────────────────────────────────

/// Returns free physical memory in MB (macOS / Linux).
pub fn free_memory_mb() -> usize {
    #[cfg(target_os = "macos")]
    {
        macos_free_mb()
    }
    #[cfg(target_os = "linux")]
    {
        linux_free_mb()
    }
    #[cfg(not(any(target_os = "macos", target_os = "linux")))]
    {
        usize::MAX // no limit on unsupported OS
    }
}

/// Returns `true` if the system has enough free memory to proceed.
pub fn memory_ok() -> bool {
    let free = free_memory_mb();
    let min = get().min_free_memory_mb;
    if free < min {
        warn!(
            "resource_limit: low memory — {}MB free < {}MB threshold",
            free, min
        );
        false
    } else {
        true
    }
}

/// Returns current process RSS in MB.
pub fn process_rss_mb() -> usize {
    #[cfg(target_os = "macos")]
    {
        // Use ps to get RSS of current process (no libc dependency)
        let pid = std::process::id();
        std::process::Command::new("ps")
            .args(["-o", "rss=", "-p", &pid.to_string()])
            .output()
            .ok()
            .and_then(|o| String::from_utf8_lossy(&o.stdout).trim().parse::<usize>().ok())
            .map(|kb| kb / 1024)
            .unwrap_or(0)
    }
    #[cfg(target_os = "linux")]
    {
        std::fs::read_to_string("/proc/self/statm")
            .ok()
            .and_then(|s| s.split_whitespace().nth(1)?.parse::<usize>().ok())
            .map(|pages| pages * 4096 / (1024 * 1024))
            .unwrap_or(0)
    }
    #[cfg(not(any(target_os = "macos", target_os = "linux")))]
    { 0 }
}

// ── Platform helpers ───────────────────────────────────────────

fn num_cpus() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
}

#[cfg(target_os = "macos")]
fn macos_free_mb() -> usize {
    // Use vm_stat via host_statistics64 — no subprocess needed.
    use std::process::Command;
    // Fallback: parse vm_stat output (lightweight, always available)
    let output = Command::new("vm_stat").output().ok();
    let text = output
        .as_ref()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();

    let page_size: usize = 16384; // Apple Silicon default
    let mut free_pages: usize = 0;
    let mut inactive_pages: usize = 0;
    let mut purgeable_pages: usize = 0;

    for line in text.lines() {
        if line.starts_with("Pages free:") {
            free_pages = parse_vm_stat_val(line);
        } else if line.starts_with("Pages inactive:") {
            inactive_pages = parse_vm_stat_val(line);
        } else if line.starts_with("Pages purgeable:") {
            purgeable_pages = parse_vm_stat_val(line);
        }
    }

    (free_pages + inactive_pages + purgeable_pages) * page_size / (1024 * 1024)
}

#[cfg(target_os = "macos")]
fn parse_vm_stat_val(line: &str) -> usize {
    line.split(':')
        .nth(1)
        .unwrap_or("")
        .trim()
        .trim_end_matches('.')
        .parse()
        .unwrap_or(0)
}

#[cfg(target_os = "linux")]
fn linux_free_mb() -> usize {
    std::fs::read_to_string("/proc/meminfo")
        .ok()
        .and_then(|s| {
            let mut available = None;
            for line in s.lines() {
                if line.starts_with("MemAvailable:") {
                    available = line.split_whitespace().nth(1)?.parse::<usize>().ok();
                    break;
                }
            }
            available
        })
        .map(|kb| kb / 1024)
        .unwrap_or(0)
}
