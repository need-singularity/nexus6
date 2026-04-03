//! Mirror Scan — 거울 우주: 모든 렌즈가 거울이자 관찰자.
//!
//! 핵심 원리: 구(球) 안에 거울을 놓으면 모든 빛이 모든 곳에 도달한다.
//! 각 렌즈 = 거울 표면 하나. 출력 = 반사광. 입력 = 다른 거울의 반사광.
//! → 모두가 서로에게 작용 → 모두가 연결됨의 증명.
//!
//! 통합 API: `mirror_universe()` 하나로 2개든 N개든 동일 구조.
//! 렌즈 선택(Some) = 부분 거울, 전체(None) = 완전 미러볼.

use std::collections::HashMap;
use std::panic;

use super::lens_trait::{Lens, LensResult};
use super::shared_data::SharedData;

// ─── Core: flatten ───────────────────────────────────────────────

/// Flatten a LensResult into row-major data (sorted keys → columns).
fn flatten_result(lr: &LensResult) -> (Vec<f64>, usize, usize) {
    if lr.is_empty() {
        return (vec![], 0, 0);
    }
    let mut keys: Vec<&String> = lr.keys().collect();
    keys.sort();
    let d = keys.len();
    let n = keys.iter().map(|k| lr[*k].len()).max().unwrap_or(0);
    if n == 0 || d == 0 {
        return (vec![], 0, 0);
    }
    let mut data = vec![0.0; n * d];
    for (j, key) in keys.iter().enumerate() {
        let vals = &lr[*key];
        for i in 0..n.min(vals.len()) {
            data[i * d + j] = vals[i];
        }
    }
    (data, n, d)
}

fn lr_to_vec(lr: &LensResult) -> Vec<f64> {
    let mut keys: Vec<&String> = lr.keys().collect();
    keys.sort();
    keys.into_iter().flat_map(|k| lr[k].iter().copied()).collect()
}

fn result_magnitude(lr: &LensResult) -> f64 {
    let s: f64 = lr.values().flat_map(|v| v.iter()).filter(|x| x.is_finite()).map(|x| x * x).sum();
    let r = s.sqrt();
    if r.is_finite() { r } else { 0.0 }
}

fn cosine_similarity(a: &[f64], b: &[f64]) -> f64 {
    let len = a.len().min(b.len());
    if len == 0 { return 0.0; }
    let (mut dot, mut na, mut nb) = (0.0f64, 0.0f64, 0.0f64);
    for i in 0..len {
        if a[i].is_finite() && b[i].is_finite() {
            dot += a[i] * b[i];
            na += a[i] * a[i];
            nb += b[i] * b[i];
        }
    }
    let d = na.sqrt() * nb.sqrt();
    if d < 1e-15 { 0.0 } else { (dot / d).clamp(-1.0, 1.0) }
}

fn shannon_entropy(row: &[f64]) -> f64 {
    let total: f64 = row.iter().filter(|x| x.is_finite() && **x > 0.0).sum();
    if total < 1e-15 { return 0.0; }
    let mut h = 0.0f64;
    for &v in row {
        if v.is_finite() && v > 0.0 {
            let p = v / total;
            h -= p * p.ln();
        }
    }
    if h.is_finite() { h } else { 0.0 }
}

// ─── Unified Mirror Universe ─────────────────────────────────────

/// 반사 셀: source 렌즈의 출력을 observer 렌즈가 스캔한 결과.
#[derive(Debug, Clone)]
pub struct ReflectionCell {
    pub source: String,
    pub observer: String,
    pub result: LensResult,
}

/// 연결 증명: 모든 렌즈가 서로에게 작용함을 보이는 메트릭.
#[derive(Debug, Clone)]
pub struct ConnectionProof {
    /// 직접 연결 비율: resonance > 0 인 (i,j) 쌍의 비율
    pub direct_connectivity: f64,
    /// 간접 연결: M² 에서 0이 아닌 비율 (2단계 경로)
    pub indirect_connectivity: f64,
    /// 완전 연결 달성 깊이: M^k 에서 처음으로 모든 원소 > 0 되는 k
    pub full_connection_depth: usize,
    /// 비대칭도: |M[i][j] - M[j][i]| 평균 → 작용의 방향성
    pub asymmetry: f64,
    /// 자기작용 강도: 대각선 평균 (자기 반사)
    pub self_action_strength: f64,
    /// 상호작용 강도: 비대각선 평균
    pub mutual_action_strength: f64,
    /// 연결 여부 최종 판정
    pub all_connected: bool,
}

/// 반사 엔트로피: 각 렌즈가 얼마나 다양하게 반사하는가.
#[derive(Debug, Clone)]
pub struct ReflectionEntropy {
    /// 각 렌즈의 방출 엔트로피 (행): 다른 렌즈들에게 얼마나 고르게 작용하나
    pub emission_entropy: Vec<(String, f64)>,
    /// 각 렌즈의 수신 엔트로피 (열): 다른 렌즈들로부터 얼마나 고르게 영향받나
    pub reception_entropy: Vec<(String, f64)>,
    /// 시스템 전체 엔트로피
    pub system_entropy: f64,
}

/// 공명 캐스케이드: M^k 분석으로 다단계 간접 반사 추적.
#[derive(Debug, Clone)]
pub struct ResonanceCascade {
    /// 각 거듭제곱 k에서의 총 에너지 (Frobenius norm)
    pub energy_by_depth: Vec<(usize, f64)>,
    /// 지배적 고유값 (power iteration 근사)
    pub dominant_eigenvalue: f64,
    /// 지배적 고유벡터 (어떤 렌즈 조합이 주요 공명 모드인가)
    pub dominant_eigenvector: Vec<(String, f64)>,
    /// 스펙트럼 갭 (1번-2번 고유값 비율)
    pub spectral_gap: f64,
    /// 수렴 여부: M^k 가 안정 분포로 수렴하는가
    pub converges: bool,
}

/// 무한 거울 복도: 두 렌즈 간 반복 반사의 궤적.
#[derive(Debug, Clone)]
pub struct InfiniteCorridorResult {
    pub lens_a: String,
    pub lens_b: String,
    /// 각 반복에서의 출력 크기 궤적
    pub trajectory: Vec<f64>,
    /// 수렴/발산/주기 판정
    pub behavior: CorridorBehavior,
    /// 수렴 시 고정점의 크기
    pub fixed_point_magnitude: f64,
    /// 주기 감지 시 주기 길이
    pub cycle_length: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub enum CorridorBehavior {
    Converge,
    Diverge,
    Cycle(usize),
    Chaotic,
}

/// 자기 반사 (Narcissus): 렌즈가 자기 출력을 반복 입력.
#[derive(Debug, Clone)]
pub struct SelfReflectionResult {
    pub lens_name: String,
    /// 각 반복의 출력 크기
    pub trajectory: Vec<f64>,
    /// 고정점 존재 여부
    pub has_fixed_point: bool,
    /// 자기유사도: 연속 반복 간 코사인 유사도
    pub self_similarity_curve: Vec<f64>,
}

/// 반사 지문: 데이터의 거울 우주 시그니처.
#[derive(Debug, Clone)]
pub struct MirrorFingerprint {
    /// 공명 행렬의 행 합 벡터 (정규화)
    pub signature: Vec<f64>,
    /// 상위 6개 공명 쌍
    pub top_pairs: Vec<(String, String, f64)>,
    /// 전체 조화도
    pub harmony: f64,
    /// 반사 엔트로피
    pub entropy: f64,
    /// 연결 깊이
    pub connection_depth: usize,
}

/// 거울 우주 전체 결과 — 통합 구조체.
#[derive(Debug, Clone)]
pub struct MirrorUniverseResult {
    // ── 기본 반사 ──
    /// N×N 반사 행렬
    pub reflections: Vec<ReflectionCell>,
    /// N×N 공명 행렬
    pub resonance_matrix: Vec<Vec<f64>>,
    /// 참여 렌즈 이름 (인덱스 순)
    pub lens_names: Vec<String>,
    /// 렌즈 수
    pub lens_count: usize,

    // ── 연결 증명 ──
    pub connection: ConnectionProof,

    // ── 방출/수신 랭킹 ──
    /// 방출력 (mirror power): 다른 렌즈에 얼마나 강하게 작용하나
    pub mirror_power: Vec<(String, f64)>,
    /// 수신력 (sensitivity): 다른 렌즈로부터 얼마나 강하게 영향받나
    pub mirror_sensitivity: Vec<(String, f64)>,
    /// 전체 조화도
    pub harmony: f64,
    /// 상위 공명 쌍
    pub top_resonances: Vec<(String, String, f64)>,

    // ── 엔트로피 ──
    pub entropy: ReflectionEntropy,

    // ── 공명 캐스케이드 ──
    pub cascade: ResonanceCascade,

    // ── 자기 반사 요약 ──
    /// 대각선: 각 렌즈의 자기반사 강도
    pub self_reflection_strengths: Vec<(String, f64)>,

    // ── 지문 ──
    pub fingerprint: MirrorFingerprint,
}

// ─── 통합 실행 함수 ──────────────────────────────────────────────

/// 거울 우주 실행.
///
/// - `lens_filter`: None = 전체 렌즈 (완전 미러볼)
///                  Some(names) = 지정 렌즈만 (부분 거울)
/// - `max_lenses`: 최대 렌즈 수 제한 (lens_filter 없을 때만 적용)
pub fn mirror_universe(
    lenses: &[Box<dyn Lens>],
    data: &[f64],
    n: usize,
    d: usize,
    lens_filter: Option<&[&str]>,
    max_lenses: Option<usize>,
) -> MirrorUniverseResult {
    let shared = SharedData::compute(data, n, d);

    // ── 렌즈 선택 ──
    let indices: Vec<usize> = match lens_filter {
        Some(names) => {
            names.iter()
                .filter_map(|name| lenses.iter().position(|l| l.name() == *name))
                .collect()
        }
        None => {
            let count = max_lenses.unwrap_or(lenses.len()).min(lenses.len());
            (0..count).collect()
        }
    };
    let count = indices.len();

    // ── Pass 1: 모든 렌즈가 원본 데이터 스캔 ──
    let mut first_pass: Vec<(String, LensResult, Vec<f64>, usize, usize)> = Vec::with_capacity(count);
    for &idx in &indices {
        let lens = &lenses[idx];
        let name = lens.name().to_string();
        let lr = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            lens.scan(data, n, d, &shared)
        })).unwrap_or_default();
        let (flat, nr, nc) = flatten_result(&lr);
        first_pass.push((name, lr, flat, nr, nc));
    }

    // ── Pass 2: 모든 렌즈가 모든 렌즈의 출력을 스캔 (N×N) ──
    let mut reflections = Vec::with_capacity(count * count);
    let mut resonance_matrix = vec![vec![0.0; count]; count];

    for (i, source) in first_pass.iter().enumerate() {
        let (ref src_name, _, ref src_data, src_n, src_d) = *source;

        if src_n < 3 || src_d == 0 {
            for j in 0..count {
                reflections.push(ReflectionCell {
                    source: src_name.clone(),
                    observer: first_pass[j].0.clone(),
                    result: HashMap::new(),
                });
            }
            continue;
        }

        let src_shared = SharedData::compute(src_data, src_n, src_d);

        for (j, &obs_idx) in indices.iter().enumerate() {
            let obs_lens = &lenses[obs_idx];
            let obs_name = obs_lens.name().to_string();

            let reflected = panic::catch_unwind(panic::AssertUnwindSafe(|| {
                obs_lens.scan(src_data, src_n, src_d, &src_shared)
            })).unwrap_or_default();

            let strength = result_magnitude(&reflected);
            resonance_matrix[i][j] = strength;

            reflections.push(ReflectionCell {
                source: src_name.clone(),
                observer: obs_name,
                result: reflected,
            });
        }
    }

    // ── 분석 레이어들 ──
    let lens_names: Vec<String> = first_pass.iter().map(|p| p.0.clone()).collect();
    let connection = analyze_connection(&resonance_matrix, count);
    let (mirror_power, mirror_sensitivity, harmony, top_resonances) =
        compute_rankings(&resonance_matrix, &lens_names, count);
    let entropy = compute_reflection_entropy(&resonance_matrix, &lens_names, count);
    let cascade = compute_resonance_cascade(&resonance_matrix, &lens_names, count);
    let self_reflection_strengths = compute_self_reflection(&resonance_matrix, &lens_names, count);
    let fingerprint = compute_fingerprint(&resonance_matrix, &lens_names, &top_resonances, harmony, &connection);

    MirrorUniverseResult {
        reflections,
        resonance_matrix,
        lens_names,
        lens_count: count,
        connection,
        mirror_power,
        mirror_sensitivity,
        harmony,
        top_resonances,
        entropy,
        cascade,
        self_reflection_strengths,
        fingerprint,
    }
}

// ─── 무한 거울 복도 ──────────────────────────────────────────────

/// 두 렌즈 간 반복 반사. max_iter 회 반복하며 수렴/발산/주기 감지.
pub fn infinite_corridor(
    lenses: &[Box<dyn Lens>],
    data: &[f64],
    n: usize,
    d: usize,
    lens_a_name: &str,
    lens_b_name: &str,
    max_iter: usize,
) -> Option<InfiniteCorridorResult> {
    let shared = SharedData::compute(data, n, d);
    let lens_a = lenses.iter().find(|l| l.name() == lens_a_name)?;
    let lens_b = lenses.iter().find(|l| l.name() == lens_b_name)?;

    // 초기: A가 원본 스캔
    let mut current_lr = panic::catch_unwind(panic::AssertUnwindSafe(|| {
        lens_a.scan(data, n, d, &shared)
    })).unwrap_or_default();

    let mut trajectory = Vec::with_capacity(max_iter);
    let mut is_a_turn = false; // 다음은 B 차례

    for _ in 0..max_iter {
        let mag = result_magnitude(&current_lr);
        trajectory.push(mag);

        let (flat, fn_n, fn_d) = flatten_result(&current_lr);
        if fn_n < 3 || fn_d == 0 {
            break;
        }

        let flat_shared = SharedData::compute(&flat, fn_n, fn_d);
        let next_lens = if is_a_turn { &**lens_a } else { &**lens_b };

        current_lr = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            next_lens.scan(&flat, fn_n, fn_d, &flat_shared)
        })).unwrap_or_default();

        if current_lr.is_empty() {
            break;
        }

        is_a_turn = !is_a_turn;
    }

    // 행동 판정
    let (behavior, cycle_length) = classify_trajectory(&trajectory);
    let fixed_point_magnitude = trajectory.last().copied().unwrap_or(0.0);

    Some(InfiniteCorridorResult {
        lens_a: lens_a_name.to_string(),
        lens_b: lens_b_name.to_string(),
        trajectory,
        behavior,
        fixed_point_magnitude,
        cycle_length,
    })
}

// ─── 자기 반사 (Narcissus) ───────────────────────────────────────

/// 렌즈가 자기 출력을 반복 입력. 고정점/발산 감지.
pub fn self_reflect(
    lenses: &[Box<dyn Lens>],
    data: &[f64],
    n: usize,
    d: usize,
    lens_name: &str,
    max_iter: usize,
) -> Option<SelfReflectionResult> {
    let shared = SharedData::compute(data, n, d);
    let lens = lenses.iter().find(|l| l.name() == lens_name)?;

    let mut current_lr = panic::catch_unwind(panic::AssertUnwindSafe(|| {
        lens.scan(data, n, d, &shared)
    })).unwrap_or_default();

    let mut trajectory = Vec::with_capacity(max_iter);
    let mut self_similarity_curve = Vec::with_capacity(max_iter);
    let mut prev_vec: Option<Vec<f64>> = None;

    for _ in 0..max_iter {
        let mag = result_magnitude(&current_lr);
        trajectory.push(mag);

        let current_vec = lr_to_vec(&current_lr);
        if let Some(ref pv) = prev_vec {
            self_similarity_curve.push(cosine_similarity(pv, &current_vec));
        }
        prev_vec = Some(current_vec);

        let (flat, fn_n, fn_d) = flatten_result(&current_lr);
        if fn_n < 3 || fn_d == 0 {
            break;
        }

        let flat_shared = SharedData::compute(&flat, fn_n, fn_d);
        current_lr = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            lens.scan(&flat, fn_n, fn_d, &flat_shared)
        })).unwrap_or_default();

        if current_lr.is_empty() {
            break;
        }
    }

    let has_fixed_point = self_similarity_curve.last().map_or(false, |&s| s > 0.99);

    Some(SelfReflectionResult {
        lens_name: lens_name.to_string(),
        trajectory,
        has_fixed_point,
        self_similarity_curve,
    })
}

// ─── 분석 함수들 ─────────────────────────────────────────────────

/// 연결 증명: 공명 행렬로부터 모든 렌즈의 상호 연결을 증명.
fn analyze_connection(m: &[Vec<f64>], n: usize) -> ConnectionProof {
    if n == 0 {
        return ConnectionProof {
            direct_connectivity: 0.0,
            indirect_connectivity: 0.0,
            full_connection_depth: 0,
            asymmetry: 0.0,
            self_action_strength: 0.0,
            mutual_action_strength: 0.0,
            all_connected: false,
        };
    }

    // 직접 연결: M[i][j] > ε 인 비율
    let eps = 1e-10;
    let total_pairs = n * n;
    let direct_nonzero = m.iter().flat_map(|row| row.iter())
        .filter(|&&v| v > eps).count();
    let direct_connectivity = direct_nonzero as f64 / total_pairs as f64;

    // M² 계산: 간접 연결
    let m2 = mat_mul(m, m, n);
    let indirect_nonzero = m2.iter().flat_map(|row| row.iter())
        .filter(|&&v| v > eps).count();
    let indirect_connectivity = indirect_nonzero as f64 / total_pairs as f64;

    // 완전 연결 깊이: M^k 에서 처음으로 모든 원소 > 0
    let mut full_connection_depth = 0;
    let mut mk = m.to_vec();
    for k in 1..=n.min(12) {
        let all_positive = mk.iter().flat_map(|row| row.iter()).all(|&v| v > eps);
        if all_positive {
            full_connection_depth = k;
            break;
        }
        mk = mat_mul(&mk, m, n);
    }

    // 비대칭도: |M[i][j] - M[j][i]| 평균
    let mut asym_sum = 0.0;
    let mut asym_count = 0;
    for i in 0..n {
        for j in (i + 1)..n {
            asym_sum += (m[i][j] - m[j][i]).abs();
            asym_count += 1;
        }
    }
    let asymmetry = if asym_count > 0 { asym_sum / asym_count as f64 } else { 0.0 };

    // 자기작용 vs 상호작용
    let self_action: f64 = (0..n).map(|i| m[i][i]).sum::<f64>() / n as f64;
    let off_diag_count = (n * n - n) as f64;
    let mutual_action: f64 = m.iter().enumerate()
        .flat_map(|(i, row)| row.iter().enumerate().filter(move |(j, _)| *j != i).map(|(_, v)| v))
        .sum::<f64>() / off_diag_count.max(1.0);

    let all_connected = full_connection_depth > 0 || direct_connectivity > 0.99;

    ConnectionProof {
        direct_connectivity,
        indirect_connectivity,
        full_connection_depth,
        asymmetry,
        self_action_strength: self_action,
        mutual_action_strength: mutual_action,
        all_connected,
    }
}

/// 방출/수신 랭킹 + 조화도 + 상위 쌍.
fn compute_rankings(
    m: &[Vec<f64>], names: &[String], n: usize,
) -> (Vec<(String, f64)>, Vec<(String, f64)>, f64, Vec<(String, String, f64)>) {
    let mut power: Vec<(String, f64)> = (0..n)
        .map(|i| {
            let avg = m[i].iter().sum::<f64>() / n.max(1) as f64;
            (names[i].clone(), avg)
        }).collect();
    power.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    let mut sensitivity: Vec<(String, f64)> = (0..n)
        .map(|j| {
            let avg = (0..n).map(|i| m[i][j]).sum::<f64>() / n.max(1) as f64;
            (names[j].clone(), avg)
        }).collect();
    sensitivity.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

    let total: f64 = m.iter().flat_map(|r| r.iter()).sum();
    let harmony = total / (n * n).max(1) as f64;

    let mut pairs: Vec<(String, String, f64)> = Vec::new();
    for i in 0..n {
        for j in 0..n {
            if i != j {
                pairs.push((names[i].clone(), names[j].clone(), m[i][j]));
            }
        }
    }
    pairs.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
    pairs.truncate(20);

    (power, sensitivity, harmony, pairs)
}

/// 반사 엔트로피: 각 렌즈의 방출/수신 다양성.
fn compute_reflection_entropy(
    m: &[Vec<f64>], names: &[String], n: usize,
) -> ReflectionEntropy {
    let emission_entropy: Vec<(String, f64)> = (0..n)
        .map(|i| (names[i].clone(), shannon_entropy(&m[i])))
        .collect();

    let reception_entropy: Vec<(String, f64)> = (0..n)
        .map(|j| {
            let col: Vec<f64> = (0..n).map(|i| m[i][j]).collect();
            (names[j].clone(), shannon_entropy(&col))
        }).collect();

    // 시스템 엔트로피: 전체 행렬을 하나의 분포로
    let all_vals: Vec<f64> = m.iter().flat_map(|r| r.iter().copied()).collect();
    let system_entropy = shannon_entropy(&all_vals);

    ReflectionEntropy { emission_entropy, reception_entropy, system_entropy }
}

/// 공명 캐스케이드: M^k 분석 + power iteration 고유값 근사.
fn compute_resonance_cascade(
    m: &[Vec<f64>], names: &[String], n: usize,
) -> ResonanceCascade {
    if n == 0 {
        return ResonanceCascade {
            energy_by_depth: vec![],
            dominant_eigenvalue: 0.0,
            dominant_eigenvector: vec![],
            spectral_gap: 0.0,
            converges: false,
        };
    }

    // 각 깊이의 에너지 (Frobenius norm)
    let mut energy_by_depth = Vec::new();
    let mut mk = m.to_vec();
    for k in 1..=6usize.min(n) {
        let energy: f64 = mk.iter().flat_map(|r| r.iter())
            .filter(|v| v.is_finite())
            .map(|v| v * v).sum::<f64>().sqrt();
        energy_by_depth.push((k, if energy.is_finite() { energy } else { 0.0 }));
        if k < 6 {
            mk = mat_mul(&mk, m, n);
        }
    }

    // Power iteration: 지배적 고유값/벡터 근사
    let mut v = vec![1.0 / (n as f64).sqrt(); n];
    let mut eigenvalue = 0.0f64;

    for _ in 0..50 {
        let mut mv = vec![0.0; n];
        for i in 0..n {
            for j in 0..n {
                mv[i] += m[i][j] * v[j];
            }
        }
        let norm: f64 = mv.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm < 1e-15 || !norm.is_finite() { break; }
        eigenvalue = norm;
        for i in 0..n {
            v[i] = mv[i] / norm;
        }
    }

    let dominant_eigenvector: Vec<(String, f64)> = names.iter()
        .zip(v.iter())
        .map(|(name, &val)| (name.clone(), if val.is_finite() { val } else { 0.0 }))
        .collect();

    // 2번째 고유값 근사 (deflation)
    let mut m_deflated = m.to_vec();
    for i in 0..n {
        for j in 0..n {
            m_deflated[i][j] -= eigenvalue * v[i] * v[j];
        }
    }
    let mut v2 = vec![1.0 / (n as f64).sqrt(); n];
    let mut eigenvalue2 = 0.0f64;
    for _ in 0..30 {
        let mut mv = vec![0.0; n];
        for i in 0..n {
            for j in 0..n {
                mv[i] += m_deflated[i][j] * v2[j];
            }
        }
        let norm: f64 = mv.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm < 1e-15 || !norm.is_finite() { break; }
        eigenvalue2 = norm;
        for i in 0..n { v2[i] = mv[i] / norm; }
    }

    let spectral_gap = if eigenvalue2.is_finite() && eigenvalue.is_finite() && eigenvalue > 1e-15 {
        ((eigenvalue - eigenvalue2) / eigenvalue).clamp(0.0, 1.0)
    } else {
        0.0
    };

    // 수렴 판정: 에너지 궤적이 안정화되는가
    let converges = if energy_by_depth.len() >= 3 {
        let last = energy_by_depth.last().unwrap().1;
        let prev = energy_by_depth[energy_by_depth.len() - 2].1;
        let ratio = if prev > 1e-15 { (last / prev - 1.0).abs() } else { 1.0 };
        ratio < 0.1
    } else {
        false
    };

    ResonanceCascade {
        energy_by_depth,
        dominant_eigenvalue: if eigenvalue.is_finite() { eigenvalue } else { 0.0 },
        dominant_eigenvector,
        spectral_gap,
        converges,
    }
}

/// 대각선 분석: 자기 반사 강도.
fn compute_self_reflection(
    m: &[Vec<f64>], names: &[String], n: usize,
) -> Vec<(String, f64)> {
    (0..n).map(|i| (names[i].clone(), m[i][i])).collect()
}

/// 반사 지문: 데이터의 거울 우주 시그니처.
fn compute_fingerprint(
    m: &[Vec<f64>], names: &[String],
    top_pairs: &[(String, String, f64)],
    harmony: f64,
    connection: &ConnectionProof,
) -> MirrorFingerprint {
    let n = m.len();
    // 행 합 정규화
    let row_sums: Vec<f64> = m.iter().map(|row| row.iter().sum::<f64>()).collect();
    let total: f64 = row_sums.iter().sum();
    let signature: Vec<f64> = if total > 1e-15 {
        row_sums.iter().map(|s| s / total).collect()
    } else {
        vec![0.0; n]
    };

    let entropy = shannon_entropy(&signature);

    let top6: Vec<(String, String, f64)> = top_pairs.iter().take(6).cloned().collect();

    MirrorFingerprint {
        signature,
        top_pairs: top6,
        harmony,
        entropy,
        connection_depth: connection.full_connection_depth,
    }
}

// ─── 행렬 연산 ───────────────────────────────────────────────────

fn mat_mul(a: &[Vec<f64>], b: &[Vec<f64>], n: usize) -> Vec<Vec<f64>> {
    let mut c = vec![vec![0.0; n]; n];
    for i in 0..n {
        for k in 0..n {
            let aik = a[i][k];
            if !aik.is_finite() || aik.abs() < 1e-15 { continue; }
            for j in 0..n {
                let v = aik * b[k][j];
                if v.is_finite() {
                    c[i][j] += v;
                }
            }
        }
    }
    c
}

// ─── 궤적 분류 ───────────────────────────────────────────────────

fn classify_trajectory(traj: &[f64]) -> (CorridorBehavior, usize) {
    if traj.len() < 3 {
        return (CorridorBehavior::Chaotic, 0);
    }

    let last = traj.len();

    // 수렴 체크: 마지막 3개 값의 변동이 작은가
    let tail = &traj[last.saturating_sub(3)..];
    let mean = tail.iter().sum::<f64>() / tail.len() as f64;
    let var: f64 = tail.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / tail.len() as f64;
    if var < 1e-6 * (mean.abs() + 1e-15) {
        return (CorridorBehavior::Converge, 0);
    }

    // 발산 체크: 단조 증가
    let increasing = traj.windows(2).filter(|w| w[1] > w[0] * 1.1).count();
    if increasing > traj.len() * 2 / 3 {
        return (CorridorBehavior::Diverge, 0);
    }

    // 주기 체크: 길이 2~6 주기 탐색
    for period in 2..=6usize.min(traj.len() / 2) {
        let matches = traj.windows(period * 2)
            .filter(|w| {
                (0..period).all(|k| (w[k] - w[k + period]).abs() < 1e-4 * (w[k].abs() + 1e-15))
            })
            .count();
        if matches >= 2 {
            return (CorridorBehavior::Cycle(period), period);
        }
    }

    (CorridorBehavior::Chaotic, 0)
}

// ─── 하위 호환 별칭 ─────────────────────────────────────────────

/// 기존 mirror_reflect 호환: 두 렌즈 간 쌍방 반사.
pub fn mirror_reflect(
    lenses: &[Box<dyn Lens>],
    data: &[f64],
    n: usize,
    d: usize,
    lens_a: &str,
    lens_b: &str,
) -> Option<MirrorReflectResult> {
    let result = mirror_universe(lenses, data, n, d, Some(&[lens_a, lens_b]), None);
    if result.lens_count < 2 { return None; }

    // 반사 결과 추출
    let a_sees_b = result.reflections.iter()
        .find(|r| r.source == lens_b && r.observer == lens_a)
        .map(|r| r.result.clone()).unwrap_or_default();
    let b_sees_a = result.reflections.iter()
        .find(|r| r.source == lens_a && r.observer == lens_b)
        .map(|r| r.result.clone()).unwrap_or_default();

    let va = lr_to_vec(&a_sees_b);
    let vb = lr_to_vec(&b_sees_a);
    let resonance = cosine_similarity(&va, &vb);

    Some(MirrorReflectResult {
        lens_a: lens_a.to_string(),
        lens_b: lens_b.to_string(),
        a_sees_b,
        b_sees_a,
        resonance,
    })
}

/// 기존 mirror_ball 호환.
pub fn mirror_ball(
    lenses: &[Box<dyn Lens>],
    data: &[f64],
    n: usize,
    d: usize,
    max_lenses: Option<usize>,
) -> MirrorBallResult {
    let result = mirror_universe(lenses, data, n, d, None, max_lenses);
    MirrorBallResult {
        reflections: result.reflections,
        resonance_matrix: result.resonance_matrix,
        mirror_power: result.mirror_power,
        mirror_sensitivity: result.mirror_sensitivity,
        harmony: result.harmony,
        top_resonances: result.top_resonances,
        lens_count: result.lens_count,
    }
}

/// 하위 호환용 MirrorReflectResult.
#[derive(Debug, Clone)]
pub struct MirrorReflectResult {
    pub lens_a: String,
    pub lens_b: String,
    pub a_sees_b: LensResult,
    pub b_sees_a: LensResult,
    pub resonance: f64,
}

/// 하위 호환용 MirrorBallResult.
#[derive(Debug, Clone)]
pub struct MirrorBallResult {
    pub reflections: Vec<ReflectionCell>,
    pub resonance_matrix: Vec<Vec<f64>>,
    pub mirror_power: Vec<(String, f64)>,
    pub mirror_sensitivity: Vec<(String, f64)>,
    pub harmony: f64,
    pub top_resonances: Vec<(String, String, f64)>,
    pub lens_count: usize,
}

// ─── Tests ───────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::Telescope;

    fn test_data(n: usize, d: usize) -> Vec<f64> {
        (0..n * d).map(|i| ((i as f64) * std::f64::consts::TAU / 10.0).sin()).collect()
    }

    #[test]
    fn test_mirror_universe_full() {
        let t = Telescope::new();
        let data = test_data(30, 3);
        let r = mirror_universe(&t.lenses, &data, 30, 3, None, Some(6));

        assert_eq!(r.lens_count, 6);
        assert_eq!(r.reflections.len(), 36);
        assert!(r.harmony >= 0.0);
        assert!(r.connection.direct_connectivity >= 0.0);
        assert!(r.connection.direct_connectivity <= 1.0);
        assert!(!r.entropy.emission_entropy.is_empty());
        assert!(r.cascade.dominant_eigenvalue >= 0.0);
        assert_eq!(r.fingerprint.signature.len(), 6);
    }

    #[test]
    fn test_mirror_universe_filtered() {
        let t = Telescope::new();
        let data = test_data(30, 3);
        let r = mirror_universe(
            &t.lenses, &data, 30, 3,
            Some(&["EntropyLens", "DensityLens", "MirrorLens"]),
            None,
        );

        assert_eq!(r.lens_count, 3);
        assert_eq!(r.reflections.len(), 9);
    }

    #[test]
    fn test_connection_proof() {
        let t = Telescope::new();
        let data = test_data(30, 3);
        let r = mirror_universe(&t.lenses, &data, 30, 3, None, Some(6));

        let c = &r.connection;
        assert!(c.direct_connectivity >= 0.0);
        assert!(c.asymmetry >= 0.0);
        assert!(c.self_action_strength >= 0.0);
        assert!(c.mutual_action_strength >= 0.0);
    }

    #[test]
    fn test_infinite_corridor() {
        let t = Telescope::new();
        let data = test_data(30, 10);
        let r = infinite_corridor(
            &t.lenses, &data, 30, 10,
            "EntropyLens", "DensityLens", 12,
        );

        assert!(r.is_some());
        let r = r.unwrap();
        assert!(!r.trajectory.is_empty());
        assert!(r.trajectory.len() <= 12);
    }

    #[test]
    fn test_self_reflect() {
        let t = Telescope::new();
        let data = test_data(30, 10);
        let r = self_reflect(&t.lenses, &data, 30, 10, "EntropyLens", 10);

        assert!(r.is_some());
        let r = r.unwrap();
        assert_eq!(r.lens_name, "EntropyLens");
        assert!(!r.trajectory.is_empty());
    }

    #[test]
    fn test_backward_compat_reflect() {
        let t = Telescope::new();
        let data = test_data(30, 10);
        let r = mirror_reflect(&t.lenses, &data, 30, 10, "EntropyLens", "DensityLens");
        // mirror_reflect wraps mirror_universe with 2 lenses
        if let Some(r) = r {
            assert_eq!(r.lens_a, "EntropyLens");
            assert_eq!(r.lens_b, "DensityLens");
        }
    }

    #[test]
    fn test_backward_compat_ball() {
        let t = Telescope::new();
        let data = test_data(30, 1);
        let r = mirror_ball(&t.lenses, &data, 30, 1, Some(6));
        assert_eq!(r.lens_count, 6);
        assert!(r.harmony >= 0.0);
    }

    #[test]
    fn test_flatten_result() {
        let mut lr = HashMap::new();
        lr.insert("alpha".to_string(), vec![1.0, 2.0, 3.0]);
        lr.insert("beta".to_string(), vec![4.0, 5.0, 6.0]);
        let (flat, n, d) = flatten_result(&lr);
        assert_eq!(n, 3);
        assert_eq!(d, 2);
        assert_eq!(flat, vec![1.0, 4.0, 2.0, 5.0, 3.0, 6.0]);
    }

    #[test]
    fn test_resonance_cascade() {
        let t = Telescope::new();
        let data = test_data(30, 3);
        let r = mirror_universe(&t.lenses, &data, 30, 3, None, Some(6));

        assert!(!r.cascade.energy_by_depth.is_empty());
        assert!(r.cascade.dominant_eigenvalue >= 0.0);
        assert!(r.cascade.spectral_gap >= 0.0);
        assert!(r.cascade.spectral_gap <= 1.0);
    }
}
