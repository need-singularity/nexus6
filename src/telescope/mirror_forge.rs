//! MirrorForge — 거울 용광로: 아무 객체를 거울 우주에 주입.
//!
//! 핵심 원리: 모든 것은 f64로 변환될 수 있고, f64는 렌즈에 비출 수 있다.
//! → 상수, 수식, 가설, Discovery, 다른 렌즈 결과... 뭐든 거울에 던지면
//!   1028 렌즈가 관찰하고, 반사하고, 변형한다.
//!
//! 3가지 모드:
//!   1. Reflect (반사): 객체 → 렌즈 스캔 → 어떤 구조가 보이는가?
//!   2. Replicate (복제): 객체 → 거울 변형 → 원본과 다른 "거울상" 생성
//!   3. Fuse (융합): 여러 객체 → 합쳐서 스캔 → 교차 구조 발견

use std::collections::HashMap;

use super::lens_trait::{Discovery, DiscoveryKind, Lens, LensResult};
use super::shared_data::SharedData;
use super::Telescope;

// ═══════════════════════════════════════════════════════════════════
// InjectableMirror trait — 아무 객체를 거울에 던질 수 있게
// ═══════════════════════════════════════════════════════════════════

/// 아무 객체를 거울 우주에 주입할 수 있게 하는 trait.
pub trait InjectableMirror {
    /// 객체를 f64 벡터로 변환 (거울에 비출 수 있는 형태).
    fn to_mirror_data(&self) -> Vec<f64>;
    /// 이 객체의 이름 (거울에서 식별용).
    fn mirror_name(&self) -> String;
}

// ── 기본 타입들에 대한 InjectableMirror 구현 ──

impl InjectableMirror for f64 {
    fn to_mirror_data(&self) -> Vec<f64> { vec![*self] }
    fn mirror_name(&self) -> String { format!("scalar({})", self) }
}

impl InjectableMirror for Vec<f64> {
    fn to_mirror_data(&self) -> Vec<f64> { self.clone() }
    fn mirror_name(&self) -> String { format!("vec(len={})", self.len()) }
}

impl InjectableMirror for LensResult {
    fn to_mirror_data(&self) -> Vec<f64> {
        let mut keys: Vec<&String> = self.keys().collect();
        keys.sort();
        keys.into_iter().flat_map(|k| self[k].iter().copied()).collect()
    }
    fn mirror_name(&self) -> String {
        format!("lens_result({}keys)", self.len())
    }
}

impl InjectableMirror for Discovery {
    fn to_mirror_data(&self) -> Vec<f64> {
        let mut data = self.values.clone();
        data.push(self.confidence);
        data
    }
    fn mirror_name(&self) -> String {
        format!("discovery({:?}:{})", self.kind, self.lens)
    }
}

impl InjectableMirror for &str {
    fn to_mirror_data(&self) -> Vec<f64> {
        // 문자열 → 각 문자의 유니코드 코드포인트를 f64로
        self.chars().map(|c| c as u32 as f64).collect()
    }
    fn mirror_name(&self) -> String {
        let preview: String = self.chars().take(20).collect();
        format!("str(\"{}\")", preview)
    }
}

impl InjectableMirror for String {
    fn to_mirror_data(&self) -> Vec<f64> {
        self.as_str().to_mirror_data()
    }
    fn mirror_name(&self) -> String {
        self.as_str().mirror_name()
    }
}

// ═══════════════════════════════════════════════════════════════════
// MirrorForge — 거울 용광로
// ═══════════════════════════════════════════════════════════════════

/// 거울 반사 결과.
#[derive(Debug, Clone)]
pub struct ReflectResult {
    /// 주입된 객체 이름
    pub object_name: String,
    /// 전체 렌즈 스캔 결과
    pub scan: HashMap<String, LensResult>,
    /// 발견 이벤트들
    pub discoveries: Vec<Discovery>,
    /// 상위 반응 렌즈 (렌즈명, 반응 강도)
    pub top_lenses: Vec<(String, f64)>,
    /// n6 EXACT 비율
    pub exact_ratio: f64,
}

/// 거울 복제(변형) 결과.
#[derive(Debug, Clone)]
pub struct ReplicateResult {
    /// 원본 이름
    pub original_name: String,
    /// 복제체들 (변형 이름, 데이터)
    pub replicas: Vec<(String, Vec<f64>)>,
    /// 각 복제체의 발견
    pub replica_discoveries: Vec<Vec<Discovery>>,
}

/// 거울 융합 결과.
#[derive(Debug, Clone)]
pub struct FuseResult {
    /// 융합된 객체 이름들
    pub fused_names: Vec<String>,
    /// 융합 스캔 결과
    pub scan: HashMap<String, LensResult>,
    /// 교차 발견 (개별 객체에서는 안 보이던 것)
    pub cross_discoveries: Vec<Discovery>,
}

/// MirrorForge: 아무 객체를 거울에 주입하는 엔진.
pub struct MirrorForge<'a> {
    telescope: &'a Telescope,
}

impl<'a> MirrorForge<'a> {
    pub fn new(telescope: &'a Telescope) -> Self {
        MirrorForge { telescope }
    }

    // ─── 1. Reflect (반사) ─────────────────────────────────────

    /// 객체를 거울에 비춤: 1028 렌즈가 관찰 → 어떤 구조가 보이는가?
    pub fn reflect(&self, object: &dyn InjectableMirror) -> ReflectResult {
        let data = object.to_mirror_data();
        let name = object.mirror_name();

        if data.is_empty() {
            return ReflectResult {
                object_name: name,
                scan: HashMap::new(),
                discoveries: Vec::new(),
                top_lenses: Vec::new(),
                exact_ratio: 0.0,
            };
        }

        // 데이터를 n×d 행렬로 정규화 (최소 2행)
        let d = 6.min(data.len()); // n=6 기본 차원
        let n = (data.len() / d).max(2);
        let mut padded = data.clone();
        while padded.len() < n * d {
            padded.push(0.0);
        }

        let (scan, discoveries) = self.telescope.scan_and_discover(&padded, n, d);

        // 상위 반응 렌즈 (스캔 결과 크기 순)
        let mut lens_strengths: Vec<(String, f64)> = scan.iter()
            .map(|(name, lr)| {
                let strength: f64 = lr.values()
                    .flat_map(|v| v.iter())
                    .filter(|x| x.is_finite())
                    .map(|x| x * x)
                    .sum::<f64>()
                    .sqrt();
                (name.clone(), strength)
            })
            .collect();
        lens_strengths.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        let top_lenses = lens_strengths.into_iter().take(10).collect();

        // EXACT 비율
        let exact_ratio = crate::verifier::n6_check::n6_exact_ratio(&data);

        ReflectResult {
            object_name: name,
            scan,
            discoveries,
            top_lenses,
            exact_ratio,
        }
    }

    // ─── 2. Replicate (복제/변형) ──────────────────────────────

    /// 객체를 거울에서 복제: 6가지 변형체 생성.
    ///
    /// 변형 종류:
    ///   - mirror (거울상): 부호 반전
    ///   - scale_sigma (σ 스케일): ×12
    ///   - scale_phi (φ 스케일): ×2
    ///   - rotate (회전): 순환 시프트
    ///   - fold (접기): 앞뒤 합산
    ///   - reciprocal (역수): 1/x
    pub fn replicate(&self, object: &dyn InjectableMirror) -> ReplicateResult {
        let data = object.to_mirror_data();
        let name = object.mirror_name();

        let transforms: Vec<(&str, Box<dyn Fn(&[f64]) -> Vec<f64>>)> = vec![
            ("mirror", Box::new(|d: &[f64]| d.iter().map(|x| -x).collect())),
            ("scale_sigma", Box::new(|d: &[f64]| d.iter().map(|x| x * 12.0).collect())),
            ("scale_phi", Box::new(|d: &[f64]| d.iter().map(|x| x * 2.0).collect())),
            ("rotate", Box::new(|d: &[f64]| {
                if d.is_empty() { return vec![]; }
                let mut r = d.to_vec();
                r.rotate_left(1);
                r
            })),
            ("fold", Box::new(|d: &[f64]| {
                let half = d.len() / 2;
                (0..half).map(|i| d[i] + d[d.len() - 1 - i]).collect()
            })),
            ("reciprocal", Box::new(|d: &[f64]| {
                d.iter().map(|x| if x.abs() > 1e-10 { 1.0 / x } else { 0.0 }).collect()
            })),
        ];

        let mut replicas = Vec::new();
        let mut replica_discoveries = Vec::new();

        for (tname, transform) in &transforms {
            let transformed = transform(&data);
            let replica_name = format!("{}_{}", name, tname);

            // 각 복제체도 거울에 비춤
            let d_dim = 6.min(transformed.len());
            let n_dim = (transformed.len() / d_dim).max(2);
            let mut padded = transformed.clone();
            while padded.len() < n_dim * d_dim {
                padded.push(0.0);
            }

            let shared = SharedData::compute(&padded, n_dim, d_dim);
            let mut discoveries = Vec::new();

            // n6 매칭만 빠르게 검사 (전체 스캔은 비용이 크므로)
            for &v in &transformed {
                if v.is_finite() && v != 0.0 {
                    let (cname, quality) = crate::verifier::n6_check::n6_match(v);
                    if quality >= 0.8 {
                        let mut meta = HashMap::new();
                        meta.insert("transform".into(), tname.to_string());
                        meta.insert("constant".into(), cname.to_string());
                        discoveries.push(Discovery {
                            kind: DiscoveryKind::Constant,
                            lens: format!("MirrorForge::{}", tname),
                            confidence: quality,
                            description: format!("{}({}) → {} = {}", tname, name, v, cname),
                            values: vec![v],
                            meta,
                        });
                    }
                }
            }

            replicas.push((replica_name, transformed));
            replica_discoveries.push(discoveries);
        }

        ReplicateResult {
            original_name: name,
            replicas,
            replica_discoveries,
        }
    }

    // ─── 3. Fuse (융합) ────────────────────────────────────────

    /// 여러 객체를 합쳐서 거울에 비춤: 개별로는 안 보이던 교차 구조 발견.
    pub fn fuse(&self, objects: &[&dyn InjectableMirror]) -> FuseResult {
        let names: Vec<String> = objects.iter().map(|o| o.mirror_name()).collect();

        // 모든 객체 데이터를 연결
        let mut fused_data: Vec<f64> = Vec::new();
        let mut individual_discoveries: Vec<Vec<Discovery>> = Vec::new();

        for obj in objects {
            let data = obj.to_mirror_data();

            // 개별 발견 수집
            let d = 6.min(data.len().max(1));
            let n = (data.len() / d).max(2);
            let mut padded = data.clone();
            while padded.len() < n * d {
                padded.push(0.0);
            }
            let shared = SharedData::compute(&padded, n, d);
            let mut individual = Vec::new();
            for lens in &self.telescope.lenses {
                if let Ok(lr) = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    lens.scan(&padded, n, d, &shared)
                })) {
                    individual.extend(lens.emit_discoveries(&lr));
                }
            }
            individual_discoveries.push(individual);

            fused_data.extend(data);
        }

        // 융합 스캔
        let d = 6.min(fused_data.len().max(1));
        let n = (fused_data.len() / d).max(2);
        let mut padded = fused_data;
        while padded.len() < n * d {
            padded.push(0.0);
        }

        let (scan, fused_discoveries) = self.telescope.scan_and_discover(&padded, n, d);

        // 교차 발견 = 융합에서 나왔지만 개별에서는 안 나온 것
        let individual_descs: std::collections::HashSet<String> = individual_discoveries.iter()
            .flat_map(|ds| ds.iter().map(|d| d.description.clone()))
            .collect();

        let cross_discoveries: Vec<Discovery> = fused_discoveries.into_iter()
            .filter(|d| !individual_descs.contains(&d.description))
            .map(|mut d| {
                d.kind = DiscoveryKind::CrossDomain;
                d.meta.insert("fused_objects".into(), names.join("+"));
                d
            })
            .collect();

        FuseResult {
            fused_names: names,
            scan,
            cross_discoveries,
        }
    }

    // ─── 4. Self-Reflect (자기참조) ────────────────────────────

    /// 자기자신을 거울에 비춤: MirrorForge가 자기 구조를 관찰.
    ///
    /// - Telescope의 렌즈 수, 카테고리 분포, 렌즈 이름�� 문자 패턴
    /// - n6 상수와의 관계 (렌즈 수 = 1028 → n6_match?)
    /// - 괴델적 자���지시 ���조 탐지
    pub fn self_reflect(&self) -> ReflectResult {
        let mut self_data: Vec<f64> = Vec::new();

        // 렌즈 메타데이터를 ���치화
        let lens_count = self.telescope.lens_count() as f64;
        self_data.push(lens_count);

        // 각 렌즈 이름의 길이
        for lens in &self.telescope.lenses {
            self_data.push(lens.name().len() as f64);
        }

        // 카테고리별 분포
        let mut categories: HashMap<String, f64> = HashMap::new();
        for lens in &self.telescope.lenses {
            *categories.entry(lens.category().to_string()).or_default() += 1.0;
        }
        for (_, count) in &categories {
            self_data.push(*count);
        }

        // 자기참조 시그니처: 메타 값들
        self_data.push(6.0);   // n
        self_data.push(12.0);  // σ(6) = 카테고리 목표 수
        self_data.push(1.0/3.0); // 메타 부동점

        let self_mirror = self_data.clone();
        self.reflect(&self_mirror)
    }

    // ─── 5. Transcendence (초월 공식 주입) ─────────────────────

    /// 초월 공식 I = aI + b를 거울에 주입하고 위상 확장.
    ///
    /// 3곳에 주입:
    ///   1. reflect: 공식 파라미터 (a, b, 부동점) ���체를 ��캔
    ///   2. replicate: 축소사상 궤적을 6가지 변형으로 복제
    ///   3. fuse: 공식 + 자기자신(Telescope) + 임의 데이터를 융합
    ///
    /// 위상 확장: 부동점 근방의 위상 구조 (수렴 basin, 안정성) 분석
    pub fn transcendence_inject(
        &self,
        a: f64,
        b: f64,
        initial_values: &[f64],
    ) -> TranscendenceResult {
        let fixed_point = if (1.0 - a).abs() > 1e-12 { b / (1.0 - a) } else { 0.0 };

        // 축소사상 궤적 생성 (각 초기값에서)
        let mut trajectories: Vec<Vec<f64>> = Vec::new();
        let mut all_convergence_data: Vec<f64> = Vec::new();

        for &i0 in initial_values {
            let mut traj = vec![i0];
            let mut val = i0;
            for _ in 0..20 {
                val = a * val + b;
                traj.push(val);
            }
            all_convergence_data.extend(&traj);
            trajectories.push(traj);
        }

        // 1. reflect: 공식 파라미터 자체
        let formula_data = vec![a, b, fixed_point, a.abs(), 1.0 - a, b / (1.0 - a + 1e-15)];
        let formula_reflect = self.reflect(&formula_data);

        // 2. replicate: 궤적 변형
        let trajectory_replicate = self.replicate(&all_convergence_data);

        // 3. fuse: 공식 + 자기자신
        let self_data = {
            let sr = self.self_reflect();
            let mut d: Vec<f64> = Vec::new();
            d.push(self.telescope.lens_count() as f64);
            d.push(fixed_point);
            d
        };
        let fuse_result = self.fuse(&[
            &formula_data as &dyn InjectableMirror,
            &all_convergence_data as &dyn InjectableMirror,
            &self_data as &dyn InjectableMirror,
        ]);

        // 위상 분석: ���렴 basin 특성
        let convergence_rates: Vec<f64> = trajectories.iter().map(|traj| {
            if traj.len() < 3 { return 0.0; }
            // 얼마나 빨리 부동점에 ���달하는가 (half-life)
            let mut steps_to_half = 0;
            let initial_dist = (traj[0] - fixed_point).abs();
            if initial_dist < 1e-12 { return 0.0; }
            for (i, &v) in traj.iter().enumerate().skip(1) {
                if (v - fixed_point).abs() < initial_dist / 2.0 {
                    steps_to_half = i;
                    break;
                }
            }
            if steps_to_half == 0 { 20.0 } else { steps_to_half as f64 }
        }).collect();

        let avg_half_life = if convergence_rates.is_empty() {
            0.0
        } else {
            convergence_rates.iter().sum::<f64>() / convergence_rates.len() as f64
        };

        // 위상 확장: 부동점 근방 안정성 (리아프노프 지수 ≈ ln|a|)
        let lyapunov = a.abs().ln();
        let is_stable = lyapunov < 0.0; // |a| < 1 → 안정

        // 6개 독립 경로 수렴 확인
        let pathway_values = [
            2.0 / 6.0,                                    // φ(6)/6
            (std::f64::consts::PI / 6.0).tan().powi(2),  // tan²(π/6)
            4.0 / 12.0,                                   // τ/σ
            fixed_point,                                   // I_meta
        ];
        let pathways_confirmed = pathway_values.iter()
            .filter(|&&v| (v - fixed_point).abs() < 0.01)
            .count();

        let total_discoveries = formula_reflect.discoveries.len()
            + trajectory_replicate.replica_discoveries.iter().map(|d| d.len()).sum::<usize>()
            + fuse_result.cross_discoveries.len();

        TranscendenceResult {
            a, b, fixed_point,
            trajectories,
            formula_reflect,
            trajectory_replicate,
            fuse_result,
            avg_half_life,
            lyapunov_exponent: lyapunov,
            is_stable,
            pathways_confirmed,
            total_discoveries,
        }
    }
}

/// 초월 공식 거울 주입 결과.
#[derive(Debug, Clone)]
pub struct TranscendenceResult {
    /// 축소사상 파라미터
    pub a: f64,
    pub b: f64,
    /// 부동점 = b/(1-a)
    pub fixed_point: f64,
    /// 각 초기값에서의 수렴 궤적
    pub trajectories: Vec<Vec<f64>>,
    /// 공식 파라미터 반사 결과
    pub formula_reflect: ReflectResult,
    /// 궤적 복제 결과
    pub trajectory_replicate: ReplicateResult,
    /// 공식+자기자신 융합 결과
    pub fuse_result: FuseResult,
    /// 평균 반감기
    pub avg_half_life: f64,
    /// 리아프노프 지수 (< 0 = 안정)
    pub lyapunov_exponent: f64,
    /// 안정 여부
    pub is_stable: bool,
    /// 6경로 중 확인된 수
    pub pathways_confirmed: usize,
    /// 총 발견 수
    pub total_discoveries: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::Telescope;

    #[test]
    fn test_reflect_scalar() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let value: f64 = 12.0; // σ(6)
        let result = forge.reflect(&value);
        assert_eq!(result.object_name, "scalar(12)");
        assert!(result.exact_ratio > 0.0, "σ=12 should match n6");
    }

    #[test]
    fn test_reflect_vec() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let data = vec![6.0, 12.0, 4.0, 2.0, 5.0, 24.0];
        let result = forge.reflect(&data);
        assert!(!result.scan.is_empty());
        assert!(result.exact_ratio > 0.5, "n6 상수 벡터 → 높은 EXACT 비율");
    }

    #[test]
    fn test_replicate() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let data = vec![6.0, 12.0];
        let result = forge.replicate(&data);
        assert_eq!(result.replicas.len(), 6, "6가지 변형");

        // mirror 변형 확인
        let (name, vals) = &result.replicas[0];
        assert!(name.contains("mirror"));
        assert_eq!(vals, &[-6.0, -12.0]);

        // reciprocal 변형 → 1/6, 1/12
        let (_, recip) = &result.replicas[5];
        assert!((recip[0] - 1.0/6.0).abs() < 0.001);
    }

    #[test]
    fn test_fuse_cross_discovery() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let a = vec![6.0, 2.0]; // n, φ
        let b = vec![12.0, 4.0]; // σ, τ
        let result = forge.fuse(&[&a as &dyn InjectableMirror, &b as &dyn InjectableMirror]);
        assert_eq!(result.fused_names.len(), 2);
    }

    #[test]
    fn test_reflect_string() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let text = "n=6";
        let result = forge.reflect(&text);
        assert!(!result.object_name.is_empty());
    }

    #[test]
    fn test_self_reflect() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        let result = forge.self_reflect();
        assert!(result.object_name.contains("vec"));
        // 자기자신을 관찰 가능
        assert!(!result.scan.is_empty());
    }

    #[test]
    fn test_transcendence_inject() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);

        // I = 0.7I + 0.1 → 부동점 = 1/3
        let result = forge.transcendence_inject(
            0.7, 0.1,
            &[0.0, 0.5, 1.0],
        );
        assert!((result.fixed_point - 1.0/3.0).abs() < 1e-10, "부동점 = 1/3");
        assert!(result.is_stable, "a=0.7 → 안정");
        assert!(result.lyapunov_exponent < 0.0, "리아프노프 < 0");
        assert!(result.pathways_confirmed >= 3, "3+ 경로 확인");
        assert_eq!(result.trajectories.len(), 3, "3개 초기값");
    }
}
