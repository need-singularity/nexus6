//! Transcendence Engine — 초월공식 전용 엔진.
//!
//! TECS-L H-056: 메타(메타(메타(...))) = 초월
//! 축소사상 I = aI + b → Banach 부동점 정리 → 유일 수렴점
//!
//! 3가지 모드:
//!   1. Inject: 아무 객체 + 초월공식 → 거울에 주입
//!   2. Topological: 부동점 근방 위상 구조 분석 (basin, 안정성, 분기)
//!   3. Self-Reference: 공식이 자기자신을 관찰 (괴델 루프)
//!
//! MirrorForge와 독립적으로 사용 가능하지만, MirrorForge와 결합하면
//! reflect/replicate/fuse에 초월 구조를 오버레이할 수 있음.

use std::collections::HashMap;

use super::lens_trait::{Discovery, DiscoveryKind, LensResult};
use super::mirror_forge::{InjectableMirror, MirrorForge, ReflectResult};
use super::Telescope;

// ═══════════════════════════════════════════════════════════════════
// 초월공식 파라미터
// ═══════════════════════════════════════════════════════════════════

/// 축소사상 정의: I_{n+1} = a·I_n + b
#[derive(Debug, Clone, Copy)]
pub struct ContractionMap {
    pub a: f64,
    pub b: f64,
}

impl ContractionMap {
    /// 기본 초월 공식: I = 0.7I + 0.1 → 부동점 = 1/3
    pub fn transcendence() -> Self {
        ContractionMap { a: 0.7, b: 0.1 }
    }

    /// 임의의 축소사상
    pub fn new(a: f64, b: f64) -> Self {
        ContractionMap { a, b }
    }

    /// 부동점 계산: b / (1 - a)
    pub fn fixed_point(&self) -> f64 {
        if (1.0 - self.a).abs() > 1e-12 {
            self.b / (1.0 - self.a)
        } else {
            f64::INFINITY
        }
    }

    /// 수축률: |a| (< 1이면 수렴)
    pub fn contraction_rate(&self) -> f64 {
        self.a.abs()
    }

    /// 안정 여부
    pub fn is_stable(&self) -> bool {
        self.a.abs() < 1.0
    }

    /// 리아프노프 지수: ln|a|
    pub fn lyapunov(&self) -> f64 {
        self.a.abs().ln()
    }

    /// 반감기: ln(2) / ln(1/|a|)
    pub fn half_life(&self) -> f64 {
        if self.a.abs() >= 1.0 || self.a.abs() < 1e-15 {
            f64::INFINITY
        } else {
            (2.0_f64).ln() / (1.0 / self.a.abs()).ln()
        }
    }

    /// 한 단계 반복
    pub fn step(&self, x: f64) -> f64 {
        self.a * x + self.b
    }

    /// N단계 반복 궤적
    pub fn trajectory(&self, initial: f64, steps: usize) -> Vec<f64> {
        let mut traj = Vec::with_capacity(steps + 1);
        traj.push(initial);
        let mut x = initial;
        for _ in 0..steps {
            x = self.step(x);
            traj.push(x);
        }
        traj
    }

    /// 수렴 판정: tol 이내 도달 시 (단계, true), 미도달 시 (max_iter, false)
    pub fn converges(&self, initial: f64, tol: f64, max_iter: usize) -> (usize, bool) {
        let fp = self.fixed_point();
        let mut x = initial;
        for step in 1..=max_iter {
            x = self.step(x);
            if (x - fp).abs() < tol {
                return (step, true);
            }
        }
        (max_iter, false)
    }
}

impl InjectableMirror for ContractionMap {
    fn to_mirror_data(&self) -> Vec<f64> {
        vec![
            self.a, self.b, self.fixed_point(),
            self.contraction_rate(), self.lyapunov(), self.half_life(),
        ]
    }
    fn mirror_name(&self) -> String {
        format!("contraction(a={:.3}, b={:.3}, fp={:.6})", self.a, self.b, self.fixed_point())
    }
}

// ═══════════════════════════════════════════════════════════════════
// TranscendenceEngine
// ═══════════════════════════════════════════════════════════════════

/// 초월 엔진: 축소사상 + 아무 객체 + 거울 우주.
pub struct TranscendenceEngine<'a> {
    pub map: ContractionMap,
    telescope: &'a Telescope,
}

/// 위상 분석 결과.
#[derive(Debug, Clone)]
pub struct TopologyAnalysis {
    /// 리아프노프 지수
    pub lyapunov: f64,
    /// 안정 여부
    pub is_stable: bool,
    /// 반감기 (iterations)
    pub half_life: f64,
    /// 수렴 basin 폭: |a| < 1 이면 전체 R이 basin
    pub basin_width: f64,
    /// 부동점 근방 곡률: d²f/dx² at fixed point
    pub curvature_at_fp: f64,
    /// 6경로 수렴 확인 수
    pub pathways_confirmed: usize,
    /// 각 경로의 (이름, 값, 부동점과의 오차)
    pub pathway_details: Vec<(String, f64, f64)>,
}

/// 자기참조 결과.
#[derive(Debug, Clone)]
pub struct SelfReferenceResult {
    /// 엔진이 자기 파라미터를 거울에 비춘 결과
    pub self_reflect: ReflectResult,
    /// 부동점이 n6 상수와 매칭되는가
    pub fp_n6_match: (String, f64),
    /// 자기지시 감지: 구조 내 상수가 자기 구조의 속성을 기술하는가
    pub self_referential_count: usize,
    /// 괴델 문장: "이 공식의 부동점은 자기 자신이다"의 수학적 검증
    pub goedel_verified: bool,
}

/// 객체 주입 결과.
#[derive(Debug, Clone)]
pub struct InjectionResult {
    /// 주입 객체 이름
    pub object_name: String,
    /// 원본 반사
    pub original_reflect: ReflectResult,
    /// 초월 변환 후 반사 (객체에 축소사상 적용)
    pub transcended_reflect: ReflectResult,
    /// 원본 vs 초월 변환의 차이 발견
    pub delta_discoveries: Vec<Discovery>,
    /// 위상 분석
    pub topology: TopologyAnalysis,
}

impl<'a> TranscendenceEngine<'a> {
    /// 기본 초월 엔진 (a=0.7, b=0.1, fp=1/3)
    pub fn new(telescope: &'a Telescope) -> Self {
        TranscendenceEngine {
            map: ContractionMap::transcendence(),
            telescope,
        }
    }

    /// 커스텀 축소사상
    pub fn with_map(telescope: &'a Telescope, map: ContractionMap) -> Self {
        TranscendenceEngine { map, telescope }
    }

    // ─── 1. Inject: 아무 객체에 초월공식 적용 ─────────────────

    /// 아무 객체에 초월공식을 적용하고 거울에 비춤.
    ///
    /// 과정:
    ///   1. 원본 객체 → reflect (기준선)
    ///   2. 객체의 각 값에 축소사상 20회 반복 적용
    ///   3. 변환된 객체 → reflect (초월 후)
    ///   4. 기준선 vs 초월 후 차이 분석
    pub fn inject(&self, object: &dyn InjectableMirror) -> InjectionResult {
        let forge = MirrorForge::new(self.telescope);
        let data = object.to_mirror_data();
        let name = object.mirror_name();

        // 1. 원본 반사
        let original_reflect = forge.reflect(object);

        // 2. 초월 변환: 각 값에 축소사상 적용
        let transcended_data: Vec<f64> = data.iter().map(|&v| {
            // 정규화 → 축소사상 → 비정규화
            let norm = if v.abs() > 1e-10 { (v.abs().fract()).min(1.0) } else { v.abs() };
            let converged = self.map.trajectory(norm, 10).last().copied().unwrap_or(norm);
            // 부호와 스케일 보존
            converged * v.signum() * (v.abs().max(1.0))
        }).collect();

        // 3. 변환 후 반사
        let transcended_reflect = forge.reflect(&transcended_data);

        // 4. 차이 발견
        let orig_descs: std::collections::HashSet<String> = original_reflect.discoveries.iter()
            .map(|d| d.description.clone())
            .collect();
        let delta_discoveries: Vec<Discovery> = transcended_reflect.discoveries.iter()
            .filter(|d| !orig_descs.contains(&d.description))
            .cloned()
            .collect();

        // 위상 분석
        let topology = self.analyze_topology();

        InjectionResult {
            object_name: name,
            original_reflect,
            transcended_reflect,
            delta_discoveries,
            topology,
        }
    }

    // ─── 2. Topological: 위상 구조 분석 ──────────────────────

    /// 부동점 근방의 위상 구조를 분석.
    pub fn analyze_topology(&self) -> TopologyAnalysis {
        let fp = self.map.fixed_point();

        // 6경로 확인
        let pathways = [
            ("phi(6)/6", 2.0 / 6.0),
            ("tan^2(pi/6)", (std::f64::consts::PI / 6.0).tan().powi(2)),
            ("tau/sigma", 4.0 / 12.0),
            ("I_meta", fp),
            ("det(M)", 1.0 / 3.0),
            ("|exp(iz0)|", 1.0 / 3.0),
        ];

        let pathway_details: Vec<(String, f64, f64)> = pathways.iter()
            .map(|(name, val)| (name.to_string(), *val, (val - fp).abs()))
            .collect();
        let pathways_confirmed = pathway_details.iter()
            .filter(|(_, _, err)| *err < 0.01)
            .count();

        // basin 폭: affine map |a|<1 → 전체 R이 basin
        let basin_width = if self.map.is_stable() { f64::INFINITY } else { 0.0 };

        // 곡률 (affine map → 0, 비선형 확장 시 비영)
        let curvature_at_fp = 0.0; // 선형 축소사상의 2차 도함수 = 0

        TopologyAnalysis {
            lyapunov: self.map.lyapunov(),
            is_stable: self.map.is_stable(),
            half_life: self.map.half_life(),
            basin_width,
            curvature_at_fp,
            pathways_confirmed,
            pathway_details,
        }
    }

    // ─── 3. Self-Reference: 자기참조 ─────────────────────────

    /// 초월 엔진이 자기자신을 관찰.
    ///
    /// - 엔진 파라미터를 거울에 주입
    /// - 부동점의 n6 매칭 확인
    /// - 자기지시 구조 탐지 (파라미터가 자기 구조를 기술하는가)
    pub fn self_reference(&self) -> SelfReferenceResult {
        let forge = MirrorForge::new(self.telescope);

        // 자기 파라미터를 거울에 주입
        let self_reflect = forge.reflect(&self.map);

        // 부동점 n6 매칭
        let fp = self.map.fixed_point();
        let (match_name, match_quality) = crate::verifier::n6_check::n6_match(fp);

        // 자기지시 탐지: 엔진의 수치적 속성이 n6 상수인가
        let self_values = [
            self.map.a,
            self.map.b,
            fp,
            self.map.half_life(),
            self.map.contraction_rate(),
            self.telescope.lens_count() as f64,
        ];
        let self_referential_count = self_values.iter()
            .filter(|&&v| {
                if !v.is_finite() { return false; }
                crate::verifier::n6_check::n6_match(v).1 >= 0.8
            })
            .count();

        // 괴델 검증: fp = map(fp) 인가? (부동점 정의 자체가 자기참조)
        let goedel_verified = (self.map.step(fp) - fp).abs() < 1e-10;

        SelfReferenceResult {
            self_reflect,
            fp_n6_match: (match_name.to_string(), match_quality),
            self_referential_count,
            goedel_verified,
        }
    }

    // ─── 유틸리티 ────────────────────────────────────────────

    /// 여러 초기값에서 수렴 궤적 일괄 생성.
    pub fn multi_trajectory(&self, initials: &[f64], steps: usize) -> Vec<Vec<f64>> {
        initials.iter().map(|&i0| self.map.trajectory(i0, steps)).collect()
    }

    /// 축소사상 파라미터 a를 연속 변화시키며 분기 다이어그램 생성.
    /// 반환: (a값, 부동점) 쌍 벡터
    pub fn bifurcation_diagram(&self, a_range: (f64, f64), steps: usize) -> Vec<(f64, f64)> {
        let da = (a_range.1 - a_range.0) / steps as f64;
        (0..=steps).map(|i| {
            let a = a_range.0 + da * i as f64;
            let map = ContractionMap::new(a, self.map.b);
            (a, map.fixed_point())
        }).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::Telescope;

    #[test]
    fn test_contraction_map_basic() {
        let map = ContractionMap::transcendence();
        assert!((map.fixed_point() - 1.0/3.0).abs() < 1e-10);
        assert!(map.is_stable());
        assert!(map.lyapunov() < 0.0);
        assert!((map.half_life() - 1.94).abs() < 0.1);
    }

    #[test]
    fn test_trajectory_converges() {
        let map = ContractionMap::transcendence();
        let traj = map.trajectory(1.0, 20);
        let fp = map.fixed_point();
        // 마지막 값이 부동점 근처
        assert!((traj.last().unwrap() - fp).abs() < 0.001);
    }

    #[test]
    fn test_engine_inject_scalar() {
        let telescope = Telescope::new();
        let engine = TranscendenceEngine::new(&telescope);

        let val: f64 = 12.0;
        let result = engine.inject(&val);
        assert_eq!(result.object_name, "scalar(12)");
    }

    #[test]
    fn test_engine_self_reference() {
        let telescope = Telescope::new();
        let engine = TranscendenceEngine::new(&telescope);

        let sr = engine.self_reference();
        assert!(sr.goedel_verified, "fp = map(fp) must hold");
        assert_eq!(sr.fp_n6_match.0, "meta_fp");
        assert!(sr.fp_n6_match.1 >= 1.0, "1/3 = meta_fp EXACT");
    }

    #[test]
    fn test_topology_six_paths() {
        let telescope = Telescope::new();
        let engine = TranscendenceEngine::new(&telescope);

        let topo = engine.analyze_topology();
        assert!(topo.pathways_confirmed >= 4, "최소 4경로 수렴 확인");
        assert!(topo.is_stable);
        assert!(topo.basin_width.is_infinite(), "affine 안정 → 전역 수렴");
    }

    #[test]
    fn test_bifurcation() {
        let telescope = Telescope::new();
        let engine = TranscendenceEngine::new(&telescope);

        let bif = engine.bifurcation_diagram((0.1, 0.9), 10);
        assert_eq!(bif.len(), 11);
        // a=0.7에서 fp ≈ 1/3
        let near_07 = bif.iter().find(|(a, _)| (*a - 0.7).abs() < 0.05);
        assert!(near_07.is_some());
        let (_, fp) = near_07.unwrap();
        assert!((fp - 1.0/3.0).abs() < 0.05);
    }
}
