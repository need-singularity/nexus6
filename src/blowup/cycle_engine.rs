//! 5-Phase Cycle Engine — Blowup → Contraction → Emergence → Singularity → Absorption
//!
//! hexa-lang CycleEngine 패턴을 nexus6 렌즈 시스템과 통합.
//! 메트릭 기반 (hexa) + 공리 기반 (nexus6) 하이브리드.

use std::collections::HashMap;

use super::blowup_engine::{BlowupEngine, BlowupConfig, BlowupResult};
use super::singularity::{Singularity, SingularityDetector};
use super::corollary::{Corollary, CorollaryType};

// ── n=6 상수 ──
const N6_CONSTANTS: &[(&str, f64)] = &[
    ("n", 6.0), ("sigma", 12.0), ("tau", 4.0), ("phi", 2.0),
    ("sopfr", 5.0), ("J2", 24.0), ("sigma-tau", 8.0),
    ("sigma*phi", 24.0), ("n*tau", 24.0), ("phi/tau", 0.5),
    ("sigma*tau", 48.0), ("n+1", 7.0), ("unity", 1.0),
    ("1/n", 0.1667), ("1/sigma", 0.0833),
];

/// 사이클 5단계
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Phase {
    Blowup,
    Contraction,
    Emergence,
    Singularity,
    Absorption,
}

impl Phase {
    pub fn name(&self) -> &'static str {
        match self {
            Phase::Blowup => "blowup",
            Phase::Contraction => "contraction",
            Phase::Emergence => "emergence",
            Phase::Singularity => "singularity",
            Phase::Absorption => "absorption",
        }
    }

    pub fn next(&self) -> Phase {
        match self {
            Phase::Blowup => Phase::Contraction,
            Phase::Contraction => Phase::Emergence,
            Phase::Emergence => Phase::Singularity,
            Phase::Singularity => Phase::Absorption,
            Phase::Absorption => Phase::Blowup,
        }
    }
}

/// n=6 매칭 결과
#[derive(Debug, Clone)]
pub struct N6Match {
    pub value: f64,
    pub constant_name: &'static str,
    pub constant_value: f64,
    pub quality: f64,
}

/// 사이클 스냅샷
#[derive(Debug, Clone)]
pub struct CycleSnapshot {
    pub cycle: usize,
    pub exact_ratio: f64,
    pub convergence: f64,
    pub corollaries: usize,
    pub patterns: usize,
    pub rules: usize,
    pub singularity_reached: bool,
}

/// 사이클 실행 결과
#[derive(Debug, Clone, Default)]
pub struct CycleResult {
    pub blowup_count: usize,
    pub exact_count: usize,
    pub close_count: usize,
    pub corollaries_generated: usize,
    pub patterns_found: usize,
    pub rules_absorbed: usize,
    pub singularity_reached: bool,
    pub exact_ratio: f64,
    pub depth_reached: usize,
}

/// 5단계 사이클 엔진 — hexa-lang + nexus6 하이브리드
pub struct CycleEngine {
    pub phase: Phase,
    pub cycle_count: usize,
    pub metrics: HashMap<String, f64>,
    pub axioms: Vec<String>,
    pub domain: String,
    pub history: Vec<CycleSnapshot>,
    pub all_corollaries: Vec<Corollary>,
    pub all_rules: Vec<String>,
    pub singularity_threshold: f64,
    pub singularity_reached: bool,
    pub max_cycles: usize,
}

impl CycleEngine {
    pub fn new(domain: &str) -> Self {
        Self {
            phase: Phase::Blowup,
            cycle_count: 0,
            metrics: HashMap::new(),
            axioms: vec![
                "sigma".into(), "phi".into(), "tau".into(),
                "n".into(), "sopfr".into(), "J2".into(),
            ],
            domain: domain.to_string(),
            history: Vec::new(),
            all_corollaries: Vec::new(),
            all_rules: Vec::new(),
            singularity_threshold: 0.5, // φ/τ
            singularity_reached: false,
            max_cycles: 6, // n=6
        }
    }

    /// 메트릭 주입
    pub fn feed(&mut self, name: &str, value: f64) {
        self.metrics.insert(name.to_string(), value);
    }

    /// 메트릭 일괄 주입
    pub fn feed_map(&mut self, map: &HashMap<String, f64>) {
        for (k, v) in map {
            self.metrics.insert(k.clone(), *v);
        }
    }

    /// 자동 수렴 루프 — 특이점 도달 또는 max_cycles까지
    pub fn run_until_singularity(&mut self) -> Vec<CycleResult> {
        let mut results = Vec::new();
        for _ in 0..self.max_cycles {
            let result = self.run_cycle();
            let reached = result.singularity_reached;
            results.push(result);
            if reached {
                break;
            }
        }
        results
    }

    /// 한 사이클 실행
    pub fn run_cycle(&mut self) -> CycleResult {
        self.cycle_count += 1;
        let mut result = CycleResult::default();

        // Phase 1: Blowup — n6 체크 + BlowupEngine
        self.phase = Phase::Blowup;
        let n6_matches = self.phase_blowup();
        result.blowup_count = n6_matches.len();

        // 공리 기반 blowup
        let singularity = Singularity {
            axioms: self.axioms.clone(),
            compression_ratio: 6.0,
            closure_degree: 1.0,
            domain: self.domain.clone(),
            metrics: self.metrics.clone(),
        };
        let engine = BlowupEngine::new(BlowupConfig {
            max_corollaries: 216,
            min_confidence: 0.15,
            max_depth: 6,
            transfer_domains: vec![self.domain.clone()],
            ..BlowupConfig::default()
        });
        let blowup_result = engine.blowup(&singularity);
        result.corollaries_generated = blowup_result.total_emergences;
        result.depth_reached = blowup_result.depth_reached;

        // Phase 2: Contraction — EXACT/CLOSE 분리
        self.phase = Phase::Contraction;
        let exact: Vec<&N6Match> = n6_matches.iter().filter(|m| m.quality >= 0.95).collect();
        let close: Vec<&N6Match> = n6_matches.iter().filter(|m| m.quality >= 0.8 && m.quality < 0.95).collect();
        result.exact_count = exact.len();
        result.close_count = close.len();

        // Phase 3: Emergence — 패턴 합의
        self.phase = Phase::Emergence;
        let mut by_constant: HashMap<&str, usize> = HashMap::new();
        for m in &exact {
            *by_constant.entry(m.constant_name).or_default() += 1;
        }
        result.patterns_found = by_constant.values().filter(|&&c| c >= 3).count();

        // 공리 기반 corollaries를 axiom pool에 피드
        for c in &blowup_result.validated {
            if c.is_axiom_candidate && !self.axioms.contains(&c.name) {
                self.axioms.push(c.name.clone());
            }
            for (k, v) in &c.signature {
                self.metrics.insert(k.clone(), *v);
            }
        }
        self.all_corollaries.extend(blowup_result.validated);

        // Phase 4: Singularity — 임계점 체크
        self.phase = Phase::Singularity;
        let total = result.blowup_count.max(1);
        result.exact_ratio = result.exact_count as f64 / total as f64;
        result.singularity_reached = result.exact_ratio >= self.singularity_threshold;
        self.singularity_reached = result.singularity_reached;

        // Phase 5: Absorption — 규칙 생성
        self.phase = Phase::Absorption;
        for (constant, count) in &by_constant {
            if *count >= 2 {
                let rule = format!("AR-{}-c{}: {} appears {} times", constant, self.cycle_count, constant, count);
                self.all_rules.push(rule);
                result.rules_absorbed += 1;
            }
        }

        // 히스토리
        self.history.push(CycleSnapshot {
            cycle: self.cycle_count,
            exact_ratio: result.exact_ratio,
            convergence: if result.blowup_count > 0 {
                result.exact_count as f64 / result.blowup_count as f64
            } else { 0.0 },
            corollaries: result.corollaries_generated,
            patterns: result.patterns_found,
            rules: result.rules_absorbed,
            singularity_reached: result.singularity_reached,
        });

        self.phase = Phase::Blowup;
        result
    }

    /// Phase 1: n=6 체크 (모든 메트릭 + 쌍별 연산)
    fn phase_blowup(&self) -> Vec<N6Match> {
        let mut matches = Vec::new();

        // 개별 값 체크
        for (_, &value) in &self.metrics {
            if let Some(m) = n6_check(value) {
                matches.push(m);
            }
        }

        // 쌍별 연산 (곱, 비율, 합)
        let vals: Vec<f64> = self.metrics.values().copied().collect();
        for i in 0..vals.len() {
            for j in (i + 1)..vals.len() {
                if vals[j].abs() > 1e-10 {
                    if let Some(m) = n6_check(vals[i] / vals[j]) { matches.push(m); }
                }
                if let Some(m) = n6_check(vals[i] * vals[j]) { matches.push(m); }
                if let Some(m) = n6_check(vals[i] + vals[j]) { matches.push(m); }
                if let Some(m) = n6_check((vals[i] - vals[j]).abs()) { matches.push(m); }
            }
        }
        matches
    }

    /// 리포트 생성
    pub fn report(&self) -> String {
        let mut out = String::new();
        out.push_str("═══ NEXUS-6 Singularity Cycle Engine ═══\n");
        out.push_str(&format!("Domain: {} | Cycles: {} | Axioms: {}\n",
            self.domain, self.cycle_count, self.axioms.len()));
        out.push_str(&format!("Corollaries: {} | Rules: {}\n",
            self.all_corollaries.len(), self.all_rules.len()));
        out.push_str(&format!("Singularity: {}\n",
            if self.singularity_reached { "★ REACHED ★" } else { "approaching..." }));

        if !self.history.is_empty() {
            out.push_str("\nHistory:\n");
            for s in &self.history {
                out.push_str(&format!(
                    "  C{}: exact={:.1}% cor={} pat={} rules={} {}\n",
                    s.cycle, s.exact_ratio * 100.0, s.corollaries,
                    s.patterns, s.rules,
                    if s.singularity_reached { "★" } else { "·" }
                ));
            }
        }
        out
    }
}

/// n=6 상수 매칭
fn n6_check(value: f64) -> Option<N6Match> {
    if value == 0.0 || value.is_nan() || value.is_infinite() {
        return None;
    }

    let mut best: Option<N6Match> = None;
    let mut best_quality = 0.0;

    for &(name, constant) in N6_CONSTANTS {
        if constant == 0.0 { continue; }
        let ratio = value / constant;
        let quality = if ratio > 0.0 {
            1.0 - ratio.ln().abs().min(1.0)
        } else { 0.0 };

        if quality > best_quality && quality >= 0.8 {
            best_quality = quality;
            best = Some(N6Match {
                value,
                constant_name: name,
                constant_value: constant,
                quality,
            });
        }
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_n6_check_exact() {
        let m = n6_check(12.0).unwrap();
        assert_eq!(m.constant_name, "sigma");
        assert!(m.quality > 0.99);
    }

    #[test]
    fn test_n6_check_close() {
        let m = n6_check(11.5);
        assert!(m.is_some());
        let m = m.unwrap();
        assert!(m.quality >= 0.8);
    }

    #[test]
    fn test_cycle_engine_basic() {
        let mut engine = CycleEngine::new("test");
        engine.feed("sigma", 12.0);
        engine.feed("tau", 4.0);
        engine.feed("n", 6.0);
        let result = engine.run_cycle();
        assert!(result.exact_count > 0);
        assert!(result.blowup_count > 0);
    }

    #[test]
    fn test_cycle_engine_singularity() {
        let mut engine = CycleEngine::new("test");
        // 모든 n=6 상수 주입 → 특이점 즉시 도달
        engine.feed("sigma", 12.0);
        engine.feed("tau", 4.0);
        engine.feed("phi", 2.0);
        engine.feed("n", 6.0);
        engine.feed("sopfr", 5.0);
        engine.feed("J2", 24.0);
        let results = engine.run_until_singularity();
        assert!(!results.is_empty());
        assert!(results.last().unwrap().singularity_reached);
    }

    #[test]
    fn test_phase_transition() {
        let p = Phase::Blowup;
        assert_eq!(p.next(), Phase::Contraction);
        assert_eq!(Phase::Absorption.next(), Phase::Blowup);
    }
}
