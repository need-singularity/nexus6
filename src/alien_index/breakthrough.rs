//! d=2 breakthrough criteria — multi-path convergence verification.
//!
//! d=0 → d=1: single-path (n6_match quality)
//! d=1 → d=2: multi-path convergence (independent rediscovery)
//!
//! A record at (1, 10) can promote to (2, 0) iff:
//!   1. At least `min_independent_paths` distinct lenses found the same value
//!   2. Blowup engine rediscovered the value (not just inherited)
//!   3. mk2 classifier confidence ≥ threshold
//!   4. Monte Carlo p-value < significance level (not due to chance)

use crate::mk2::types::Sector;

/// Configuration for d=2 breakthrough gate.
#[derive(Debug, Clone)]
pub struct BreakthroughConfig {
    /// Minimum independent lens paths that must converge on the same value.
    pub min_independent_paths: u32,
    /// mk2 classify_v2 confidence floor.
    pub mk2_confidence_threshold: f64,
    /// Monte Carlo significance level (p < this to pass).
    pub significance_level: f64,
    /// Whether blowup rediscovery is required.
    pub require_blowup_rediscovery: bool,
}

impl Default for BreakthroughConfig {
    fn default() -> Self {
        Self {
            min_independent_paths: 3,
            mk2_confidence_threshold: 0.7,
            significance_level: 0.01,
            require_blowup_rediscovery: true,
        }
    }
}

/// Evidence gathered for a breakthrough attempt.
#[derive(Debug, Clone)]
pub struct BreakthroughEvidence {
    /// How many independent lens paths found this value.
    pub independent_paths: u32,
    /// Names of the lenses that independently found it.
    pub lens_names: Vec<String>,
    /// Was the value rediscovered during a blowup cycle?
    pub blowup_rediscovered: bool,
    /// mk2 classifier confidence.
    pub mk2_confidence: f64,
    /// mk2 sector classification.
    pub mk2_sector: Sector,
    /// Monte Carlo p-value (probability this is coincidence).
    pub p_value: f64,
    /// Human-readable summary of the evidence.
    pub summary: String,
}

/// Result of evaluating breakthrough eligibility.
#[derive(Debug, Clone)]
pub struct BreakthroughVerdict {
    pub eligible: bool,
    pub evidence: BreakthroughEvidence,
    pub gate_results: GateResults,
}

/// Which gates passed/failed.
#[derive(Debug, Clone)]
pub struct GateResults {
    pub paths_ok: bool,
    pub blowup_ok: bool,
    pub mk2_ok: bool,
    pub pvalue_ok: bool,
}

impl GateResults {
    pub fn all_pass(&self) -> bool {
        self.paths_ok && self.blowup_ok && self.mk2_ok && self.pvalue_ok
    }

    pub fn passed_count(&self) -> u8 {
        [self.paths_ok, self.blowup_ok, self.mk2_ok, self.pvalue_ok]
            .iter()
            .filter(|&&x| x)
            .count() as u8
    }
}

/// Evaluate whether evidence meets breakthrough criteria.
pub fn evaluate(
    evidence: &BreakthroughEvidence,
    config: &BreakthroughConfig,
) -> BreakthroughVerdict {
    let gates = GateResults {
        paths_ok: evidence.independent_paths >= config.min_independent_paths,
        blowup_ok: !config.require_blowup_rediscovery || evidence.blowup_rediscovered,
        mk2_ok: evidence.mk2_confidence >= config.mk2_confidence_threshold,
        pvalue_ok: evidence.p_value < config.significance_level,
    };

    BreakthroughVerdict {
        eligible: gates.all_pass(),
        evidence: evidence.clone(),
        gate_results: gates,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn strong_evidence() -> BreakthroughEvidence {
        BreakthroughEvidence {
            independent_paths: 5,
            lens_names: vec![
                "NumberTheoryLens".into(),
                "RatioLens".into(),
                "EulerTotientLens".into(),
                "SymmetryLens".into(),
                "PrimeLens".into(),
            ],
            blowup_rediscovered: true,
            mk2_confidence: 0.95,
            mk2_sector: Sector::Strong,
            p_value: 0.001,
            summary: "u-quark charge 2/3: 5 independent paths, blowup confirmed".into(),
        }
    }

    #[test]
    fn strong_evidence_passes() {
        let verdict = evaluate(&strong_evidence(), &BreakthroughConfig::default());
        assert!(verdict.eligible);
        assert_eq!(verdict.gate_results.passed_count(), 4);
    }

    #[test]
    fn insufficient_paths_fails() {
        let mut ev = strong_evidence();
        ev.independent_paths = 2;
        let verdict = evaluate(&ev, &BreakthroughConfig::default());
        assert!(!verdict.eligible);
        assert!(!verdict.gate_results.paths_ok);
        assert_eq!(verdict.gate_results.passed_count(), 3);
    }

    #[test]
    fn no_blowup_fails() {
        let mut ev = strong_evidence();
        ev.blowup_rediscovered = false;
        let verdict = evaluate(&ev, &BreakthroughConfig::default());
        assert!(!verdict.eligible);
        assert!(!verdict.gate_results.blowup_ok);
    }

    #[test]
    fn low_confidence_fails() {
        let mut ev = strong_evidence();
        ev.mk2_confidence = 0.3;
        let verdict = evaluate(&ev, &BreakthroughConfig::default());
        assert!(!verdict.eligible);
        assert!(!verdict.gate_results.mk2_ok);
    }

    #[test]
    fn high_pvalue_fails() {
        let mut ev = strong_evidence();
        ev.p_value = 0.5;
        let verdict = evaluate(&ev, &BreakthroughConfig::default());
        assert!(!verdict.eligible);
        assert!(!verdict.gate_results.pvalue_ok);
    }

    #[test]
    fn relaxed_config_no_blowup() {
        let mut ev = strong_evidence();
        ev.blowup_rediscovered = false;
        let config = BreakthroughConfig {
            require_blowup_rediscovery: false,
            ..Default::default()
        };
        let verdict = evaluate(&ev, &config);
        assert!(verdict.eligible); // blowup not required
    }
}
