//! Preflight gates: single-instance lock, memory, loadavg, halt file.
//!
//! Returns GateResult which determines exit code.

use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

use fs2::FileExt;

#[derive(Debug, Clone, PartialEq)]
pub enum GateResult {
    Pass,
    SkipLowMemory { free_mb: usize, min_mb: usize },
    SkipHighLoad { loadavg: f64, max: f64 },
    SkipHalted,
    LockContention,
}

/// Hold an exclusive flock for the lifetime of the struct; dropped → unlocked.
pub struct TickLock { file: File, path: PathBuf }

impl TickLock {
    pub fn acquire(path: &Path) -> std::io::Result<Option<Self>> {
        // Clean stale lock (dead PID) before attempt.
        cleanup_stale(path);

        let file = OpenOptions::new().create(true).read(true).write(true).open(path)?;
        match file.try_lock_exclusive() {
            Ok(()) => {
                // Record PID
                let pid = std::process::id();
                (&file).set_len(0)?;
                (&file).write_all(pid.to_string().as_bytes())?;
                (&file).sync_all()?;
                Ok(Some(Self { file, path: path.to_path_buf() }))
            }
            Err(_) => Ok(None),
        }
    }
}

impl Drop for TickLock {
    fn drop(&mut self) {
        let _ = self.file.unlock();
        // Leave file in place (PID record useful for debug)
    }
}

/// If lock file exists with a dead PID, remove it so acquire() succeeds.
fn cleanup_stale(path: &Path) {
    if !path.exists() { return; }
    let content = match std::fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return,
    };
    let pid: Option<u32> = content.trim().parse().ok();
    if let Some(pid) = pid {
        if !pid_alive(pid) {
            let _ = std::fs::remove_file(path);
        }
    }
}

#[cfg(unix)]
fn pid_alive(pid: u32) -> bool {
    #[cfg(target_os = "linux")]
    { Path::new(&format!("/proc/{}", pid)).exists() }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("ps")
            .args(["-p", &pid.to_string()])
            .output()
            .map(|o| String::from_utf8_lossy(&o.stdout).lines().count() > 1)
            .unwrap_or(false)
    }
}

#[cfg(not(unix))]
fn pid_alive(_pid: u32) -> bool { true }

/// Read 1-min loadavg on Unix. Returns None on unsupported OS.
pub fn loadavg_1min() -> Option<f64> {
    #[cfg(any(target_os = "linux", target_os = "macos"))]
    {
        let out = std::process::Command::new("uptime").output().ok()?;
        let s = String::from_utf8_lossy(&out.stdout);
        let after = s.split("load average").nth(1)?;
        let cleaned: String = after.chars()
            .map(|c| if c == ',' || c == ':' || c == 's' { ' ' } else { c })
            .collect();
        cleaned.split_whitespace().next()?.parse().ok()
    }
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    { None }
}

pub struct PreflightConfig {
    pub min_free_memory_mb: usize,
    pub max_loadavg_1min: f64,
    pub halt_file: PathBuf,
}

/// Run non-lock gates (mem, load, halt). Lock is held by caller.
pub fn check_gates(cfg: &PreflightConfig) -> GateResult {
    if cfg.halt_file.exists() { return GateResult::SkipHalted; }
    let free = crate::resource_limit::free_memory_mb();
    if free < cfg.min_free_memory_mb {
        return GateResult::SkipLowMemory { free_mb: free, min_mb: cfg.min_free_memory_mb };
    }
    if let Some(l) = loadavg_1min() {
        if l > cfg.max_loadavg_1min {
            return GateResult::SkipHighLoad { loadavg: l, max: cfg.max_loadavg_1min };
        }
    }
    GateResult::Pass
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env::temp_dir;

    fn tmp(name: &str) -> PathBuf {
        let mut p = temp_dir();
        p.push(format!("nexus6_preflight_{}_{}", name, std::process::id()));
        let _ = std::fs::remove_file(&p);
        p
    }

    #[test]
    fn lock_acquire_and_release() {
        let p = tmp("lock1");
        let l = TickLock::acquire(&p).unwrap();
        assert!(l.is_some());
        drop(l);
        let l2 = TickLock::acquire(&p).unwrap();
        assert!(l2.is_some());
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn second_acquire_blocks_while_first_held() {
        let p = tmp("lock2");
        let _l = TickLock::acquire(&p).unwrap().unwrap();
        let l2 = TickLock::acquire(&p).unwrap();
        assert!(l2.is_none(), "should not double-acquire");
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn stale_lock_cleaned() {
        let p = tmp("stale");
        std::fs::write(&p, "999999").unwrap();
        let l = TickLock::acquire(&p).unwrap();
        assert!(l.is_some(), "stale lock should be cleaned");
        std::fs::remove_file(&p).ok();
    }

    #[test]
    fn halt_file_blocks() {
        let halt = tmp("halt");
        std::fs::write(&halt, "").unwrap();
        let cfg = PreflightConfig {
            min_free_memory_mb: 0,
            max_loadavg_1min: 1e9,
            halt_file: halt.clone(),
        };
        assert_eq!(check_gates(&cfg), GateResult::SkipHalted);
        std::fs::remove_file(&halt).ok();
    }

    #[test]
    fn halt_absent_passes_mem_check_low_threshold() {
        let halt = tmp("no_halt");
        let _ = std::fs::remove_file(&halt);
        let cfg = PreflightConfig {
            min_free_memory_mb: 0,
            max_loadavg_1min: 1e9,
            halt_file: halt,
        };
        assert_eq!(check_gates(&cfg), GateResult::Pass);
    }

    #[test]
    fn low_memory_trips_gate() {
        let halt = tmp("no_halt2");
        let _ = std::fs::remove_file(&halt);
        let cfg = PreflightConfig {
            min_free_memory_mb: usize::MAX / 2,
            max_loadavg_1min: 1e9,
            halt_file: halt,
        };
        assert!(matches!(check_gates(&cfg), GateResult::SkipLowMemory { .. }));
    }

    #[test]
    fn loadavg_parses_on_unix() {
        #[cfg(any(target_os = "linux", target_os = "macos"))]
        {
            let l = loadavg_1min();
            assert!(l.is_some());
            assert!(l.unwrap() >= 0.0);
        }
    }
}
