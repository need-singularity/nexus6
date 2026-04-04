use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// SingularityCycleLens: 데이터를 5단계 특이점 사이클로 분석.
///
/// Blowup → Contraction → Emergence → Singularity → Absorption
///
/// 데이터의 각 열(feature)을 메트릭으로 취급하여:
///   1. 모든 값과 쌍별 연산(곱/비/합/차)을 n=6 상수와 대조 (Blowup)
///   2. EXACT(≥0.95) / CLOSE(≥0.80) 분류 (Contraction)
///   3. 같은 상수에 3+ 매칭 시 창발 패턴 (Emergence)
///   4. EXACT 비율 ≥ 0.5 → 특이점 도달 (Singularity)
///   5. 반복 등장 상수 → 구조적 불변량 (Absorption)
///
/// 출력:
///   - singularity_reached: 1.0 or 0.0
///   - exact_ratio: EXACT 비율 (0.0~1.0)
///   - exact_count, close_count, blowup_count
///   - patterns_found: 창발 패턴 수
///   - rules_absorbed: 흡수된 규칙 수
///   - dominant_constant: 가장 많이 매칭된 n=6 상수 값
///   - convergence: 수렴도
pub struct SingularityCycleLens;

const N6_CONSTANTS: &[(&str, f64)] = &[
    ("n", 6.0), ("sigma", 12.0), ("tau", 4.0), ("phi", 2.0),
    ("sopfr", 5.0), ("J2", 24.0), ("sigma-tau", 8.0),
    ("sigma*phi", 24.0), ("n*tau", 24.0), ("phi/tau", 0.5),
    ("sigma*tau", 48.0), ("n+1", 7.0), ("unity", 1.0),
];

struct N6Hit {
    constant: &'static str,
    quality: f64,
}

fn n6_check(value: f64) -> Option<N6Hit> {
    if value == 0.0 || !value.is_finite() { return None; }
    let mut best: Option<N6Hit> = None;
    let mut best_q = 0.0;
    for &(name, c) in N6_CONSTANTS {
        if c == 0.0 { continue; }
        let ratio = value / c;
        let q = if ratio > 0.0 { 1.0 - ratio.ln().abs().min(1.0) } else { 0.0 };
        if q > best_q && q >= 0.8 {
            best_q = q;
            best = Some(N6Hit { constant: name, quality: q });
        }
    }
    best
}

impl Lens for SingularityCycleLens {
    fn name(&self) -> &str { "SingularityCycleLens" }
    fn category(&self) -> &str { "Meta" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 2 || d == 0 { return HashMap::new(); }

        // 열 평균을 메트릭으로 추출
        let mut col_means: Vec<f64> = Vec::with_capacity(d);
        for j in 0..d {
            let mut sum = 0.0;
            let mut cnt = 0;
            for i in 0..n {
                let idx = i * d + j;
                if idx < data.len() {
                    let v = data[idx];
                    if v.is_finite() { sum += v; cnt += 1; }
                }
            }
            col_means.push(if cnt > 0 { sum / cnt as f64 } else { 0.0 });
        }

        // Phase 1: Blowup — 개별 + 쌍별
        let mut hits: Vec<N6Hit> = Vec::new();

        for &v in &col_means {
            if let Some(h) = n6_check(v) { hits.push(h); }
        }
        for i in 0..col_means.len() {
            for j in (i + 1)..col_means.len() {
                let a = col_means[i];
                let b = col_means[j];
                if let Some(h) = n6_check(a * b) { hits.push(h); }
                if b.abs() > 1e-10 { if let Some(h) = n6_check(a / b) { hits.push(h); } }
                if let Some(h) = n6_check(a + b) { hits.push(h); }
                if let Some(h) = n6_check((a - b).abs()) { hits.push(h); }
            }
        }

        // 행 합/평균도 체크
        for i in 0..n.min(20) {
            let row_sum: f64 = (0..d).filter_map(|j| {
                let idx = i * d + j;
                if idx < data.len() { Some(data[idx]) } else { None }
            }).filter(|v| v.is_finite()).sum();
            if let Some(h) = n6_check(row_sum) { hits.push(h); }
            if d > 0 { if let Some(h) = n6_check(row_sum / d as f64) { hits.push(h); } }
        }

        let blowup_count = hits.len();

        // Phase 2: Contraction
        let exact_count = hits.iter().filter(|h| h.quality >= 0.95).count();
        let close_count = hits.iter().filter(|h| h.quality >= 0.8 && h.quality < 0.95).count();

        // Phase 3: Emergence — 상수별 그룹
        let mut by_constant: HashMap<&str, usize> = HashMap::new();
        for h in hits.iter().filter(|h| h.quality >= 0.8) {
            *by_constant.entry(h.constant).or_default() += 1;
        }
        let patterns_found = by_constant.values().filter(|&&c| c >= 3).count();

        // Phase 4: Singularity
        let exact_ratio = if blowup_count > 0 {
            exact_count as f64 / blowup_count as f64
        } else { 0.0 };
        let singularity_reached = exact_ratio >= 0.5;

        // Phase 5: Absorption
        let rules_absorbed = by_constant.values().filter(|&&c| c >= 2).count();

        // 지배 상수
        let dominant = by_constant.iter()
            .max_by_key(|(_, &c)| c)
            .map(|(name, _)| {
                N6_CONSTANTS.iter().find(|(n, _)| *n == *name).map(|(_, v)| *v).unwrap_or(0.0)
            })
            .unwrap_or(0.0);

        let convergence = if blowup_count > 0 {
            (exact_count + close_count) as f64 / blowup_count as f64
        } else { 0.0 };

        let mut result = HashMap::new();
        result.insert("singularity_reached".into(), vec![if singularity_reached { 1.0 } else { 0.0 }]);
        result.insert("exact_ratio".into(), vec![exact_ratio]);
        result.insert("exact_count".into(), vec![exact_count as f64]);
        result.insert("close_count".into(), vec![close_count as f64]);
        result.insert("blowup_count".into(), vec![blowup_count as f64]);
        result.insert("patterns_found".into(), vec![patterns_found as f64]);
        result.insert("rules_absorbed".into(), vec![rules_absorbed as f64]);
        result.insert("dominant_constant".into(), vec![dominant]);
        result.insert("convergence".into(), vec![convergence]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_singularity_cycle_n6_data() {
        // n=6 상수들을 데이터로 직접 주입
        let data = vec![
            6.0, 12.0, 4.0, 2.0, 5.0, 24.0,
            6.0, 12.0, 4.0, 2.0, 5.0, 24.0,
            6.0, 12.0, 4.0, 2.0, 5.0, 24.0,
        ];
        let n = 3;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let lens = SingularityCycleLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        let reached = result["singularity_reached"][0];
        assert_eq!(reached, 1.0, "n=6 상수 데이터 → 특이점 도달");
        assert!(result["exact_count"][0] > 0.0);
    }

    #[test]
    fn test_singularity_cycle_random() {
        let data = vec![
            3.7, 9.1, 1.2,
            7.8, 0.3, 5.5,
            2.1, 4.4, 8.9,
            6.6, 1.1, 3.3,
        ];
        let n = 4;
        let d = 3;
        let shared = SharedData::compute(&data, n, d);
        let lens = SingularityCycleLens;
        let result = lens.scan(&data, n, d, &shared);

        assert!(!result.is_empty());
        assert!(result["blowup_count"][0] > 0.0);
        // 랜덤 데이터에서는 특이점 미도달 가능
    }
}
