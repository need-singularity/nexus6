//! In-process airgenome runner — implements `CycleRunner`.
//!
//! Samples Mac vitals via `airgenome::sample()`, evaluates the 15 pair gates,
//! and encodes the current singularity state as a text invariant. No JSON,
//! no file IO, no process boundary — a single function call.

use airgenome::rules::{firing, severity, Severity};
use airgenome::resource_guard::{self, AdaptiveThrottle, HardLimits, SoftLimits, ThrottleLevel};
use airgenome::{sample, Axis, RULES};

use super::tick::CycleRunner;
use super::topology::{Point, Singularity};

/// Airgenome runner with self-imposed resource limits.
/// 하드 제한(rlimit+nice)은 첫 run() 시 1회 적용,
/// 소프트 적응은 매 run()마다 RSS 체크 후 배치/sleep 조절.
pub struct AirgenomeRunner {
    throttle: Option<AdaptiveThrottle>,
}

impl AirgenomeRunner {
    pub fn new() -> Self {
        Self { throttle: None }
    }

    fn ensure_guard(&mut self) {
        if self.throttle.is_none() {
            match resource_guard::init_guard(HardLimits::default(), SoftLimits::default()) {
                Ok(t) => {
                    tracing::info!("airgenome resource_guard 초기화: {}", t.status());
                    self.throttle = Some(t);
                }
                Err(e) => {
                    tracing::warn!("resource_guard 초기화 실패 (계속 실행): {}", e);
                    self.throttle = Some(AdaptiveThrottle::new(SoftLimits::default()));
                }
            }
        }
    }
}

impl Default for AirgenomeRunner {
    fn default() -> Self {
        Self::new()
    }
}

impl CycleRunner for AirgenomeRunner {
    fn run(&mut self, _domain: &str, _seed: Option<&Point>) -> Singularity {
        // 리소스 가드 초기화 (첫 호출 시 하드 제한 적용)
        self.ensure_guard();

        // 소프트 적응 체크
        if let Some(ref mut throttle) = self.throttle {
            let (level, _scale, sleep_ms) = throttle.check_and_adapt();
            if level != ThrottleLevel::Normal {
                tracing::debug!("airgenome throttle: {}", throttle.status());
            }
            throttle.maybe_sleep(sleep_ms);
        }

        let v = sample();
        let fires = firing(&v);
        let firing_count = fires.len();

        // Build invariant text: axis snapshot + top firing rules + severities.
        let mut parts = Vec::new();
        parts.push(format!(
            "cpu={:.2} ram={:.2} gpu={:.1} npu={:.1} pwr={:.0} io={:.3}",
            v.get(Axis::Cpu),
            v.get(Axis::Ram),
            v.get(Axis::Gpu),
            v.get(Axis::Npu),
            v.get(Axis::Power),
            v.get(Axis::Io),
        ));
        parts.push(format!("firing={}/15", firing_count));

        // Include top rules by severity (Critical first, then Warn).
        let mut ranked: Vec<(usize, Severity)> = fires
            .iter()
            .map(|&k| (k, severity(k, &v)))
            .collect();
        ranked.sort_by_key(|(_, sev)| match sev {
            Severity::Critical => 0,
            Severity::Warn => 1,
            Severity::Ok => 2,
        });
        let top_rules: Vec<String> = ranked
            .iter()
            .take(3)
            .map(|(k, sev)| {
                let rule = &RULES[*k];
                let tag = match sev {
                    Severity::Critical => "!",
                    Severity::Warn => "~",
                    Severity::Ok => "",
                };
                format!("{}{}", tag, rule.name)
            })
            .collect();
        if !top_rules.is_empty() {
            parts.push(format!("top=[{}]", top_rules.join(",")));
        }

        let invariant = parts.join(" | ");

        // confidence = density of firing gates (0..1)
        let confidence = firing_count as f64 / 15.0;
        // novelty = inverse of firing density (sparse state = newer frontier)
        let novelty = 1.0 - confidence;
        // depth = number of firing gates (0..15)
        let depth_reached = firing_count;

        Singularity { invariant, confidence, novelty, depth_reached }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sample_produces_nonempty_invariant() {
        let mut r = AirgenomeRunner::new();
        let s = r.run("architecture_design", None);
        assert!(!s.invariant.is_empty());
        assert!(s.invariant.contains("cpu="));
        assert!(s.invariant.contains("firing="));
        assert!((0.0..=1.0).contains(&s.confidence));
        assert!((0.0..=1.0).contains(&s.novelty));
        assert!(s.depth_reached <= 15);
    }

    #[test]
    fn confidence_plus_novelty_equals_one() {
        let mut r = AirgenomeRunner::new();
        let s = r.run("x", None);
        let sum = s.confidence + s.novelty;
        assert!((sum - 1.0).abs() < 1e-9);
    }
}
