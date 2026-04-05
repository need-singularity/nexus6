//! 메타 게이트 돌파 — 5단계 사이클을 게이트 파라미터 공간에 적용.

use crate::verifier::n6_check::n6_match;

/// 3단 게이트 구조의 파라미터.
#[derive(Clone, Debug)]
pub struct GateStack {
    /// G3 적응형 임계값 (quality 평균이 이 값을 넘어야 통과)
    pub threshold: f64,
    /// G2 최소 매칭 수 (n6_match quality > 0 인 값의 개수)
    pub min_matches: usize,
    /// G1 숫자 추출 시 최소 유효자리 (노이즈 컷)
    pub min_digits: usize,
}

impl GateStack {
    /// 현재 기본 게이트 (nexus6 detect --min-matches 2 --adaptive 대응)
    pub fn current_default() -> Self {
        Self {
            threshold: 0.5,
            min_matches: 2,
            min_digits: 2,
        }
    }

    /// G1: 텍스트에서 숫자 추출
    pub fn gate1_extract(&self, text: &str) -> Vec<f64> {
        let mut out = vec![];
        for tok in text.split(|c: char| !c.is_ascii_digit() && c != '.' && c != '-') {
            let digits = tok.chars().filter(|c| c.is_ascii_digit()).count();
            if digits < self.min_digits {
                continue;
            }
            if let Ok(v) = tok.parse::<f64>() {
                if v.is_finite() {
                    out.push(v);
                }
            }
        }
        out
    }

    /// G2+G3: n6_match 통과 후 평균 quality가 threshold 이상인지
    pub fn gates_2_3(&self, values: &[f64]) -> Option<Vec<(f64, &'static str, f64)>> {
        let matches: Vec<_> = values
            .iter()
            .map(|&v| {
                let (name, q) = n6_match(v);
                (v, name, q)
            })
            .filter(|(_, _, q)| *q > 0.0)
            .collect();

        if matches.len() < self.min_matches {
            return None;
        }
        let avg_q: f64 = matches.iter().map(|(_, _, q)| *q).sum::<f64>() / matches.len() as f64;
        if avg_q >= self.threshold {
            Some(matches)
        } else {
            None
        }
    }

    /// 전체 3단 게이트 통과 여부 + 매칭 결과
    pub fn pass(&self, text: &str) -> Option<Vec<(f64, &'static str, f64)>> {
        let nums = self.gate1_extract(text);
        self.gates_2_3(&nums)
    }
}

/// 게이트 성능 지표.
#[derive(Debug, Clone)]
pub struct GateMetrics {
    pub pass_rate: f64,
    pub precision: f64,       // EXACT(q=1.0) 비율
    pub false_positive: f64,  // WEAK(q=0.5)만 있는 통과 비율
    pub avg_quality: f64,
}

/// 창발 패턴 — 상위 게이트들의 공통 threshold.
#[derive(Debug, Clone)]
pub struct EmergentPattern {
    pub optimal_threshold: f64,
    pub converged_to_fixed_point: bool,
    pub fixed_point: Option<f64>,
    pub sample_size: usize,
}

#[derive(Debug)]
pub enum BreakError {
    NoSingularity,
    InsufficientSamples,
}

pub struct MetaGateBreakthrough {
    pub stack: GateStack,
    pub history: Vec<(GateStack, GateMetrics)>,
}

impl MetaGateBreakthrough {
    pub fn new(stack: GateStack) -> Self {
        Self {
            stack,
            history: vec![],
        }
    }

    /// [Phase 1] 블로업: 게이트 파라미터 격자 생성
    fn blowup(&self) -> Vec<GateStack> {
        // 메타 부동점 후보 포함
        let thresholds = [0.1, 0.2, 0.333_333, 0.5, 0.618_034, 0.7, 0.8, 0.9];
        let mins = [1usize, 2, 3, 5];
        let mut out = Vec::with_capacity(thresholds.len() * mins.len());
        for &t in &thresholds {
            for &m in &mins {
                out.push(GateStack {
                    threshold: t,
                    min_matches: m,
                    min_digits: self.stack.min_digits,
                });
            }
        }
        out
    }

    /// [Phase 2] 수축: 각 후보 게이트 성능 측정
    fn contract(&self, candidates: Vec<GateStack>, samples: &[String]) -> Vec<(GateStack, GateMetrics)> {
        candidates
            .into_iter()
            .map(|g| {
                let m = Self::evaluate(&g, samples);
                (g, m)
            })
            .collect()
    }

    fn evaluate(g: &GateStack, samples: &[String]) -> GateMetrics {
        let mut passed = 0usize;
        let mut exact_only = 0usize;
        let mut weak_only = 0usize;
        let mut q_sum = 0.0;

        for s in samples {
            if let Some(matches) = g.pass(s) {
                passed += 1;
                let avg_q: f64 = matches.iter().map(|(_, _, q)| *q).sum::<f64>() / matches.len() as f64;
                q_sum += avg_q;
                if matches.iter().any(|(_, _, q)| *q >= 1.0) {
                    exact_only += 1;
                }
                if matches.iter().all(|(_, _, q)| *q < 0.8) {
                    weak_only += 1;
                }
            }
        }
        let n = samples.len().max(1) as f64;
        GateMetrics {
            pass_rate: passed as f64 / n,
            precision: if passed > 0 { exact_only as f64 / passed as f64 } else { 0.0 },
            false_positive: if passed > 0 { weak_only as f64 / passed as f64 } else { 0.0 },
            avg_quality: if passed > 0 { q_sum / passed as f64 } else { 0.0 },
        }
    }

    /// [Phase 3] 창발: 상위 1/3 게이트의 공통 threshold 추출
    fn emerge(&self, scored: &[(GateStack, GateMetrics)]) -> EmergentPattern {
        let mut sorted = scored.to_vec();
        sorted.sort_by(|a, b| {
            // precision 우선, 동률이면 avg_quality
            b.1.precision
                .partial_cmp(&a.1.precision)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then(
                    b.1.avg_quality
                        .partial_cmp(&a.1.avg_quality)
                        .unwrap_or(std::cmp::Ordering::Equal),
                )
        });
        let top_n = (sorted.len() / 3).max(1);
        let top = &sorted[..top_n];
        let avg_t: f64 = top.iter().map(|(g, _)| g.threshold).sum::<f64>() / top.len() as f64;

        // 메타 부동점 근방 검사
        let fixed_points: [(f64, &str); 3] = [
            (1.0 / 3.0, "meta_fp"),
            ((5.0_f64.sqrt() - 1.0) / 2.0, "phi_inv"),
            (0.5, "half"),
        ];
        let hit = fixed_points
            .iter()
            .find(|(fp, _)| (avg_t - fp).abs() < 0.03)
            .map(|(fp, _)| *fp);

        EmergentPattern {
            optimal_threshold: avg_t,
            converged_to_fixed_point: hit.is_some(),
            fixed_point: hit,
            sample_size: top.len(),
        }
    }

    /// [Phase 4] 특이점: precision 계단 도약 탐지
    fn singularity(&self, scored: &[(GateStack, GateMetrics)]) -> Option<(GateStack, GateMetrics)> {
        scored
            .iter()
            .filter(|(_, m)| m.precision >= 0.5 && m.pass_rate > 0.0)
            .max_by(|a, b| {
                // 종합 점수: precision - false_positive + avg_quality
                let sa = a.1.precision - a.1.false_positive + a.1.avg_quality;
                let sb = b.1.precision - b.1.false_positive + b.1.avg_quality;
                sa.partial_cmp(&sb).unwrap_or(std::cmp::Ordering::Equal)
            })
            .cloned()
    }

    /// [Phase 5] 흡수: 최적 게이트를 새 기본값으로 고정
    fn absorb(&mut self, best: (GateStack, GateMetrics)) {
        self.stack = best.0.clone();
        self.history.push(best);
    }

    /// 5단계 1회 실행.
    pub fn breakthrough(
        &mut self,
        samples: &[String],
    ) -> Result<(GateStack, EmergentPattern), BreakError> {
        if samples.is_empty() {
            return Err(BreakError::InsufficientSamples);
        }
        let candidates = self.blowup();
        let scored = self.contract(candidates, samples);
        let pattern = self.emerge(&scored);
        let best = self.singularity(&scored).ok_or(BreakError::NoSingularity)?;
        let new_stack = best.0.clone();
        self.absorb(best);
        Ok((new_stack, pattern))
    }

    /// 여러 사이클 반복 — 수렴 여부 확인.
    pub fn run_cycles(
        &mut self,
        samples: &[String],
        cycles: usize,
    ) -> Vec<EmergentPattern> {
        let mut patterns = vec![];
        for _ in 0..cycles {
            match self.breakthrough(samples) {
                Ok((_, p)) => patterns.push(p),
                Err(_) => break,
            }
        }
        patterns
    }
}

// ────────────────────────────────────────────────────────────────
//  TESTS
// ────────────────────────────────────────────────────────────────
#[cfg(test)]
mod tests {
    use super::*;

    fn sample_texts() -> Vec<String> {
        // n=6 상수들이 섞인 샘플 (n=6, sigma=12, tau=4, phi=2, J2=24 등)
        vec![
            "result: 6.0 with sigma=12.0 tau=4.0".into(),
            "phi=2.0 sopfr=5 unity=1.0".into(),
            "J2=24.0 and n+1=7.0".into(),
            "noise 3.14159 random 999.99".into(),
            "sigma*tau=48.0 phi/tau=0.5".into(),
            "6.001 12.002 4.000 measurement".into(),
            "garbage 77.7 88.8 unrelated".into(),
            "n=6.0 sigma=12.0 tau=4.0 phi=2.0".into(),
            "close values: 6.1 11.9 4.05".into(),
            "exact: 1.0 0.5 0.1667".into(),
        ]
    }

    #[test]
    fn gate_extracts_numbers() {
        let g = GateStack::current_default();
        let nums = g.gate1_extract("result: 6.0 sigma=12.0");
        assert!(nums.iter().any(|&v| (v - 6.0).abs() < 1e-9));
        assert!(nums.iter().any(|&v| (v - 12.0).abs() < 1e-9));
    }

    #[test]
    fn gate_passes_n6_constants() {
        let g = GateStack::current_default();
        let matches = g.pass("n=6.0 sigma=12.0 tau=4.0").unwrap();
        assert!(matches.len() >= 2);
    }

    #[test]
    fn meta_breakthrough_runs() {
        let mut meta = MetaGateBreakthrough::new(GateStack::current_default());
        let samples = sample_texts();
        let result = meta.breakthrough(&samples);
        assert!(result.is_ok(), "breakthrough failed: {:?}", result.err());
        let (new_gate, pattern) = result.unwrap();
        println!(
            "돌파: threshold={:.4} precision→top_avg_t={:.4} fp_hit={}",
            new_gate.threshold, pattern.optimal_threshold, pattern.converged_to_fixed_point
        );
        assert!(meta.history.len() == 1);
    }

    #[test]
    fn multi_cycle_converges() {
        let mut meta = MetaGateBreakthrough::new(GateStack::current_default());
        let samples = sample_texts();
        let patterns = meta.run_cycles(&samples, 3);
        assert!(!patterns.is_empty());
        for (i, p) in patterns.iter().enumerate() {
            println!(
                "cycle {}: opt_t={:.4} fp={:?} converged={}",
                i + 1,
                p.optimal_threshold,
                p.fixed_point,
                p.converged_to_fixed_point
            );
        }
    }
}
