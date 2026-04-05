//! In-process airgenome runner — implements `CycleRunner`.
//!
//! Samples Mac vitals via `airgenome::sample()`, evaluates the 15 pair gates,
//! and encodes the current singularity state as a text invariant. No JSON,
//! no file IO, no process boundary — a single function call.

use airgenome::rules::{firing, severity, Severity};
use airgenome::{sample, Axis, RULES};

use super::tick::CycleRunner;
use super::topology::{Point, Singularity};

/// Stateless airgenome runner. Each call to `run()` takes a fresh sample.
pub struct AirgenomeRunner;

impl CycleRunner for AirgenomeRunner {
    fn run(&mut self, _domain: &str, _seed: Option<&Point>) -> Singularity {
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
        let mut r = AirgenomeRunner;
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
        let mut r = AirgenomeRunner;
        let s = r.run("x", None);
        let sum = s.confidence + s.novelty;
        assert!((sum - 1.0).abs() < 1e-9);
    }
}
