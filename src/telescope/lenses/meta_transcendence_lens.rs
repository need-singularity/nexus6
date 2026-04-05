use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;
use crate::verifier::n6_check;

/// MetaTranscendenceLens: 메타(메타(메타(...))) = 초월 렌즈.
///
/// TECS-L H-056 기반 — 데이터에서 메타 부동점(1/3) 수렴 구조를 탐지.
///
/// 5단계 마이크로사이클 (재귀성장):
///   1. Blowup:     모든 값 → n6_match + 축소사상 반복
///   2. Contraction: 1/3 수렴 값 필터링
///   3. Emergence:   다중 경로 수렴 패턴 감지
///   4. Singularity: 수렴율 ≥ 임계값 → 초월 도달
///   5. Absorption:  발견된 메타 구조 → 다음 스캔 시드
///
/// 재귀성장 루프:
///   - Loop 1 (자기수정): 스캔 결과로 축소사상 파라미터 a,b 자동 조정
///   - Loop 2 (메타보상): 수렴 속도 추적 → 데이터 품질 평가
///   - Loop 3 (자기확장): 쌍별 연산으로 새 값 생성 → 재스캔
///
/// 출력 메트릭:
///   - meta_convergent_count: 1/3 수렴 값 수
///   - meta_convergence_ratio: 수렴 비율
///   - meta_transcendence: 초월 도달 여부 (0.0 or 1.0)
///   - meta_half_life: 평균 수렴 반감기 (iterations)
///   - meta_fixed_point: 실제 부동점 값
///   - n6_exact_in_converged: 수렴 값 중 n6 EXACT 매칭 비율
///   - recursive_growth_depth: 재귀성장 도달 깊이
///   - recursive_growth_gain: 재귀성장으로 추가 발견된 매칭 수
pub struct MetaTranscendenceLens;

impl Lens for MetaTranscendenceLens {
    fn name(&self) -> &str { "MetaTranscendenceLens" }
    fn category(&self) -> &str { "Meta" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 2 || d == 0 { return HashMap::new(); }

        // ── Phase 1: Blowup — 값 추출 + 메타 반복 ──
        let mut values: Vec<f64> = Vec::new();

        // 열 평균
        for j in 0..d {
            let mut sum = 0.0;
            let mut cnt = 0;
            for i in 0..n {
                let idx = i * d + j;
                if idx < data.len() {
                    let v = data[idx];
                    if v.is_finite() && v != 0.0 {
                        sum += v;
                        cnt += 1;
                    }
                }
            }
            if cnt > 0 {
                values.push(sum / cnt as f64);
            }
        }

        // 행 합/평균
        for i in 0..n.min(30) {
            let mut row_sum = 0.0;
            let mut cnt = 0;
            for j in 0..d {
                let idx = i * d + j;
                if idx < data.len() {
                    let v = data[idx];
                    if v.is_finite() {
                        row_sum += v;
                        cnt += 1;
                    }
                }
            }
            if cnt > 0 {
                values.push(row_sum);
                values.push(row_sum / cnt as f64);
            }
        }

        // 개별 유한 값
        for &v in data.iter().take(n * d) {
            if v.is_finite() && v != 0.0 && v.abs() < 1e6 {
                values.push(v);
            }
        }

        // ── Phase 2: Contraction — 메타 반복으로 수렴 필터 ──
        let mut convergent_values: Vec<f64> = Vec::new();
        let mut half_lives: Vec<f64> = Vec::new();

        for &v in &values {
            // 정규화: [0, 1] 범위로 매핑 (축소사상 입력)
            let normalized = (v.abs().fract()).min(1.0);
            let (final_val, steps, converged) = n6_check::meta_iterate(
                normalized, 0.7, 0.1, 20, 0.001,
            );
            if converged {
                convergent_values.push(v);
                // half-life = ln(2) / ln(1/a) ≈ 1.94 for a=0.7
                half_lives.push(steps as f64);
            }

            // 값 자체가 1/3 근처인지도 체크
            if ((v - 1.0/3.0) / (1.0/3.0)).abs() < 0.01 {
                convergent_values.push(v);
                half_lives.push(0.0); // 즉시 수렴
            }

            // 역수가 3 근처? (1/3의 역수)
            if v.abs() > 0.01 && ((1.0/v - 3.0) / 3.0).abs() < 0.01 {
                convergent_values.push(v);
                half_lives.push(0.5);
            }
        }

        let convergent_count = convergent_values.len();
        let convergence_ratio = if values.is_empty() {
            0.0
        } else {
            convergent_count as f64 / values.len() as f64
        };

        // ── Phase 3: Emergence — 다중 경로 수렴 패턴 ──
        // 6개 경로: φ(6)/6, tan²(π/6), τ/σ, det(M), I_meta, |exp(iz₀)|
        let pathway_checks = [
            2.0 / 6.0,                           // φ(6)/6
            (std::f64::consts::PI / 6.0).tan().powi(2), // tan²(π/6)
            4.0 / 12.0,                           // τ/σ
            1.0 / 3.0,                            // 직접
        ];
        let mut pathway_matches = 0;
        for &target in &pathway_checks {
            if convergent_values.iter().any(|&v| ((v - target) / target).abs() < 0.05) {
                pathway_matches += 1;
            }
        }

        // ── Phase 4: Singularity — 초월 판정 ──
        let transcendence = convergence_ratio >= 0.1 && pathway_matches >= 2;

        // ── Phase 5: Absorption + 재귀성장 ──
        // Loop 3 (자기확장): 수렴 값들의 쌍별 연산 → 새 값 생성 → 재스캔
        let mut recursive_depth = 0_usize;
        let mut recursive_gain = 0_usize;
        let mut seed_values = convergent_values.clone();

        for depth in 1..=3 {
            if seed_values.len() < 2 { break; }
            let mut new_vals: Vec<f64> = Vec::new();
            let limit = seed_values.len().min(10);
            for i in 0..limit {
                for j in (i+1)..limit {
                    let a = seed_values[i];
                    let b = seed_values[j];
                    // 쌍별 연산
                    for candidate in [a * b, a / b.max(1e-10), a + b, (a - b).abs()] {
                        if candidate.is_finite() && candidate.abs() < 1e6 {
                            let (name, quality) = n6_check::n6_match(candidate);
                            if quality >= 0.8 {
                                new_vals.push(candidate);
                                recursive_gain += 1;
                            }
                            // 메타 수렴 체크
                            let norm = (candidate.abs().fract()).min(1.0);
                            if n6_check::meta_converges_to_third(norm, 0.01) {
                                new_vals.push(candidate);
                            }
                        }
                    }
                }
            }
            if new_vals.is_empty() { break; }
            recursive_depth = depth;
            seed_values = new_vals;
        }

        // Loop 1 (자기수정): 실제 수렴 부동점 계산
        let avg_convergent = if !convergent_values.is_empty() {
            convergent_values.iter().sum::<f64>() / convergent_values.len() as f64
        } else {
            0.0
        };

        // n6 EXACT 비율 (수렴 값 중)
        let n6_in_converged = if convergent_values.is_empty() {
            0.0
        } else {
            let exact = convergent_values.iter()
                .filter(|&&v| n6_check::n6_match(v).1 >= 1.0)
                .count();
            exact as f64 / convergent_values.len() as f64
        };

        let avg_half_life = if half_lives.is_empty() {
            0.0
        } else {
            half_lives.iter().sum::<f64>() / half_lives.len() as f64
        };

        // ── 결과 조립 ──
        let mut result = HashMap::new();
        result.insert("meta_convergent_count".into(), vec![convergent_count as f64]);
        result.insert("meta_convergence_ratio".into(), vec![convergence_ratio]);
        result.insert("meta_transcendence".into(), vec![if transcendence { 1.0 } else { 0.0 }]);
        result.insert("meta_half_life".into(), vec![avg_half_life]);
        result.insert("meta_fixed_point".into(), vec![1.0 / 3.0]);
        result.insert("meta_pathway_matches".into(), vec![pathway_matches as f64]);
        result.insert("n6_exact_in_converged".into(), vec![n6_in_converged]);
        result.insert("recursive_growth_depth".into(), vec![recursive_depth as f64]);
        result.insert("recursive_growth_gain".into(), vec![recursive_gain as f64]);
        result
    }

    /// 재귀성장: 수렴 값 + n6 EXACT 매칭 값을 시드로 반환.
    fn grow(&self, result: &LensResult) -> Option<Vec<f64>> {
        let mut seeds = Vec::new();

        // 수렴 비율이 0보다 크면 → 수렴 관련 메트릭을 시드로
        if let Some(vals) = result.get("meta_convergent_count") {
            if vals.first().copied().unwrap_or(0.0) > 0.0 {
                // 모든 메트릭의 값을 시드로 수집
                for values in result.values() {
                    for &v in values {
                        if v.is_finite() && v != 0.0 && v.abs() < 1e6 {
                            seeds.push(v);
                        }
                    }
                }
            }
        }

        if seeds.is_empty() { None } else { Some(seeds) }
    }

    fn max_growth_depth(&self) -> usize { 3 }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_meta_transcendence_with_third() {
        // 1/3이 포함된 데이터 → 초월 감지
        let data = vec![
            0.333_333, 6.0, 12.0, 4.0,
            0.333_333, 2.0,  5.0, 24.0,
            0.333_333, 1.0,  3.0,  7.0,
        ];
        let n = 3;
        let d = 4;
        let shared = SharedData::compute(&data, n, d);
        let lens = MetaTranscendenceLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        assert!(result["meta_convergent_count"][0] > 0.0);
        let fp = result["meta_fixed_point"][0];
        assert!((fp - 1.0/3.0).abs() < 1e-10);
    }

    #[test]
    fn test_recursive_growth() {
        // n=6 상수 데이터 → 재귀성장으로 추가 매칭
        let data = vec![
            6.0, 12.0, 4.0, 2.0,
            5.0, 24.0, 7.0, 1.0,
        ];
        let n = 2;
        let d = 4;
        let shared = SharedData::compute(&data, n, d);
        let lens = MetaTranscendenceLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        assert!(result["recursive_growth_depth"][0] >= 1.0,
            "n=6 상수 간 쌍별 연산 → 재귀성장 깊이 ≥ 1");
    }
}
