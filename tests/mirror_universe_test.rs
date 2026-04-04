/// 거울 우주 통합 실험
/// — 모든 렌즈가 거울이자 관찰자, 서로를 비추면 모두가 연결됨
use nexus6::telescope::Telescope;
use nexus6::telescope::mirror_scan::{CorridorBehavior, mirror_delta};

fn sin_data(n: usize, d: usize) -> Vec<f64> {
    (0..n * d).map(|i| ((i as f64) * std::f64::consts::TAU / 10.0).sin()).collect()
}

fn mixed_data(n: usize, d: usize) -> Vec<f64> {
    (0..n * d).map(|i| {
        let x = i as f64;
        (x * 0.1).sin() + (x * 0.37).cos() + (x % 7.0) * 0.1
    }).collect()
}

// ─── 1. 거울 우주 통합 (6 렌즈) ─────────────────────────────────

#[test]
fn test_mirror_universe_6_lenses() {
    let t = Telescope::new();
    let data = sin_data(50, 4);
    let r = t.mirror_universe(&data, 50, 4, None, Some(6));

    println!("=== 거울 우주 (6 렌즈) ===");
    println!("렌즈: {:?}", r.lens_names);
    println!("조화도: {:.4}", r.harmony);

    let c = &r.connection;
    println!("\n--- 연결 증명 ---");
    println!("직접 연결: {:.1}%", c.direct_connectivity * 100.0);
    println!("간접 연결 (M²): {:.1}%", c.indirect_connectivity * 100.0);
    println!("완전 연결 깊이: {}", c.full_connection_depth);
    println!("비대칭도: {:.4}", c.asymmetry);
    println!("자기작용: {:.4}", c.self_action_strength);
    println!("상호작용: {:.4}", c.mutual_action_strength);
    println!("모두 연결됨: {}", c.all_connected);

    println!("\n--- 공명 캐스케이드 ---");
    for (k, e) in &r.cascade.energy_by_depth {
        println!("M^{}: energy = {:.4}", k, e);
    }
    println!("지배 고유값: {:.4}", r.cascade.dominant_eigenvalue);
    println!("스펙트럼 갭: {:.4}", r.cascade.spectral_gap);
    println!("수렴: {}", r.cascade.converges);
    println!("지배 고유벡터:");
    for (name, val) in &r.cascade.dominant_eigenvector {
        println!("  {}: {:.4}", name, val);
    }

    println!("\n--- 반사 엔트로피 ---");
    println!("시스템 엔트로피: {:.4}", r.entropy.system_entropy);
    for (name, e) in &r.entropy.emission_entropy {
        println!("  방출 {}: {:.4}", name, e);
    }

    println!("\n--- 거울 지문 ---");
    println!("시그니처: {:?}", r.fingerprint.signature.iter().map(|v| format!("{:.3}", v)).collect::<Vec<_>>());
    println!("지문 엔트로피: {:.4}", r.fingerprint.entropy);
    println!("연결 깊이: {}", r.fingerprint.connection_depth);

    println!("\n--- 상위 공명 쌍 ---");
    for (a, b, v) in r.top_resonances.iter().take(10) {
        println!("  {} → {}: {:.4}", a, b, v);
    }

    println!("\n--- 자기 반사 (대각선) ---");
    for (name, v) in &r.self_reflection_strengths {
        println!("  {}: {:.4}", name, v);
    }

    println!("\n--- 방출력 Top ---");
    for (name, v) in r.mirror_power.iter().take(6) {
        println!("  {}: {:.4}", name, v);
    }
    println!("--- 수신력 Top ---");
    for (name, v) in r.mirror_sensitivity.iter().take(6) {
        println!("  {}: {:.4}", name, v);
    }

    assert_eq!(r.lens_count, 6);
    assert!(r.harmony >= 0.0);
}

// ─── 2. 선택 렌즈 미러볼 ────────────────────────────────────────

#[test]
fn test_mirror_universe_selected() {
    let t = Telescope::new();
    let data = mixed_data(40, 5);
    let selected = &[
        "ConsciousnessLens", "TopologyLens", "EntropyLens",
        "MirrorLens", "WaveLens", "GravityLens",
    ];
    let r = t.mirror_universe(&data, 40, 5, Some(selected), None);

    println!("=== 선택 6렌즈 미러볼 ===");
    println!("렌즈: {:?}", r.lens_names);
    println!("직접 연결: {:.1}%", r.connection.direct_connectivity * 100.0);
    println!("조화도: {:.4}", r.harmony);

    for (a, b, v) in r.top_resonances.iter().take(6) {
        println!("  {} → {}: {:.4}", a, b, v);
    }

    assert_eq!(r.lens_count, selected.len());
}

// ─── 3. 무한 거울 복도 ──────────────────────────────────────────

#[test]
fn test_infinite_corridor_experiments() {
    let t = Telescope::new();
    let data = mixed_data(40, 6);

    let pairs = [
        ("EntropyLens", "DensityLens"),
        ("ConsciousnessLens", "WaveLens"),
        ("TopologyLens", "MirrorLens"),
        ("GravityLens", "CausalLens"),
        ("SpectralLens", "FractalLens"),
        ("ChaosLens", "StabilityLens"),
    ];

    println!("=== 무한 거울 복도 실험 ===");
    for (a, b) in &pairs {
        if let Some(r) = t.infinite_corridor(&data, 40, 6, a, b, 20) {
            let behavior = match &r.behavior {
                CorridorBehavior::Converge => "수렴".to_string(),
                CorridorBehavior::Diverge => "발산".to_string(),
                CorridorBehavior::Cycle(p) => format!("주기({})", p),
                CorridorBehavior::Chaotic => "카오스".to_string(),
            };
            println!("{} ↔ {}: {} | 반복={} | 최종크기={:.4}",
                a, b, behavior, r.trajectory.len(), r.fixed_point_magnitude);
            if r.trajectory.len() <= 10 {
                println!("  궤적: {:?}", r.trajectory.iter().map(|v| format!("{:.3}", v)).collect::<Vec<_>>());
            }
        } else {
            println!("{} ↔ {}: 실행 불가", a, b);
        }
    }
}

// ─── 4. 자기 반사 (나르키소스) ───────────────────────────────────

#[test]
fn test_self_reflection_experiments() {
    let t = Telescope::new();
    let data = mixed_data(40, 6);

    let lens_names = [
        "EntropyLens", "ConsciousnessLens", "TopologyLens",
        "MirrorLens", "ChaosLens", "VoidLens",
        "GravityLens", "WaveLens", "DensityLens",
    ];

    println!("=== 자기 반사 (나르키소스) 실험 ===");
    for name in &lens_names {
        if let Some(r) = t.self_reflect(&data, 40, 6, name, 15) {
            let fp = if r.has_fixed_point { "고정점 O" } else { "고정점 X" };
            let last_sim = r.self_similarity_curve.last().map(|v| format!("{:.4}", v)).unwrap_or_default();
            println!("{:25} | {} | 반복={} | 최종유사도={}",
                name, fp, r.trajectory.len(), last_sim);
            if r.trajectory.len() <= 8 {
                println!("  궤적: {:?}", r.trajectory.iter().map(|v| format!("{:.3}", v)).collect::<Vec<_>>());
            }
        } else {
            println!("{}: 실행 불가", name);
        }
    }
}

// ─── 5. 하위 호환 검증 ──────────────────────────────────────────

#[test]
fn test_backward_compat() {
    let t = Telescope::new();
    let data = sin_data(30, 3);

    let ball = t.mirror_ball(&data, 30, 3, Some(6));
    println!("=== 하위 호환: mirror_ball ===");
    println!("렌즈: {}, 조화: {:.4}", ball.lens_count, ball.harmony);
    assert_eq!(ball.lens_count, 6);

    if let Some(r) = t.mirror_reflect(&data, 30, 3, "EntropyLens", "DensityLens") {
        println!("=== 하위 호환: mirror_reflect ===");
        println!("{} ↔ {}", r.lens_a, r.lens_b);
    }
}

// ─── 6. 대규모 미러볼 (20 렌즈) ─────────────────────────────────

#[test]
fn test_mirror_universe_20_lenses() {
    let t = Telescope::new();
    let data = mixed_data(50, 5);
    let r = t.mirror_universe(&data, 50, 5, None, Some(20));

    println!("=== 대규모 미러볼 (20 렌즈) ===");
    println!("렌즈 수: {}", r.lens_count);
    println!("반사 셀: {}", r.reflections.len());
    println!("조화도: {:.4}", r.harmony);
    println!("직접 연결: {:.1}%", r.connection.direct_connectivity * 100.0);
    println!("간접 연결: {:.1}%", r.connection.indirect_connectivity * 100.0);
    println!("완전 연결 깊이: {}", r.connection.full_connection_depth);
    println!("모두 연결됨: {}", r.connection.all_connected);
    println!("지배 고유값: {:.4}", r.cascade.dominant_eigenvalue);
    println!("스펙트럼 갭: {:.4}", r.cascade.spectral_gap);

    println!("\n--- 방출력 Top 5 ---");
    for (name, v) in r.mirror_power.iter().take(5) {
        println!("  {}: {:.4}", name, v);
    }
    println!("--- 수신력 Top 5 ---");
    for (name, v) in r.mirror_sensitivity.iter().take(5) {
        println!("  {}: {:.4}", name, v);
    }
    println!("--- 상위 공명 쌍 ---");
    for (a, b, v) in r.top_resonances.iter().take(10) {
        println!("  {} → {}: {:.4}", a, b, v);
    }

    assert_eq!(r.lens_count, 20);
    assert_eq!(r.reflections.len(), 400);
}

// ─── 7. 실시간 변형 감지 ────────────────────────────────────────

#[test]
fn test_mirror_delta_detection() {
    let t = Telescope::new();
    let data1 = sin_data(40, 4);
    let data2 = mixed_data(40, 4);

    let r1 = t.mirror_universe(&data1, 40, 4, None, Some(10));
    let r2 = t.mirror_universe(&data2, 40, 4, None, Some(10));
    let delta = mirror_delta(&r1, &r2);

    println!("=== 실시간 변형 감지 ===");
    println!("공명 이동량: {:.4}", delta.resonance_shift);
    println!("조화도 변화: {:.4}", delta.harmony_delta);
    println!("연결도 변화: {:.4}", delta.connectivity_delta);
    println!("고유값 변화: {:.4}", delta.eigenvalue_delta);
    println!("상전이: {}", delta.phase_transition);

    println!("\n새로운 공명 쌍:");
    for (a, b, v) in &delta.new_resonances {
        println!("  + {} → {}: {:.4}", a, b, v);
    }
    println!("사라진 공명 쌍:");
    for (a, b, v) in &delta.lost_resonances {
        println!("  - {} → {}: {:.4}", a, b, v);
    }
    println!("가장 크게 변한 렌즈:");
    for (name, d) in &delta.most_changed_lenses {
        println!("  {}: Δ{:.4}", name, d);
    }
}

// ─── 8. 자율 렌즈 조합 발견 ─────────────────────────────────────

#[test]
fn test_auto_lens_combinations() {
    let t = Telescope::new();
    let data = mixed_data(50, 5);
    let r = t.mirror_universe(&data, 50, 5, None, Some(20));
    let combos = t.discover_combinations(&r, 6);

    println!("=== 자율 렌즈 조합 발견 (20렌즈 → 6개 조합) ===");
    for c in &combos {
        println!("\n[{}] score={:.4}", c.name, c.score);
        println!("  이유: {}", c.reason);
        println!("  렌즈: {:?}", c.lenses);
    }

    assert!(!combos.is_empty());
}

// ─── 9. 규칙 없는 자유 탐색 ─────────────────────────────────────

#[test]
fn test_free_explore_evolution() {
    let t = Telescope::new();
    let data = mixed_data(40, 5);
    let r = t.free_explore(&data, 40, 5, Some(10), 8);

    println!("=== 규칙 없는 자유 탐색 ===");
    println!("세대 수: {}", r.generations);
    println!("상전이: {:?}", r.phase_transitions);

    println!("\n조화도 궤적:");
    for (i, h) in r.harmony_trajectory.iter().enumerate() {
        println!("  Gen {}: harmony={:.6}", i, h);
    }
    println!("\n연결도 궤적:");
    for (i, c) in r.connectivity_trajectory.iter().enumerate() {
        println!("  Gen {}: connectivity={:.4}", i, c);
    }
    println!("\n고유값 궤적:");
    for (i, e) in r.eigenvalue_trajectory.iter().enumerate() {
        println!("  Gen {}: eigenvalue={:.4}", i, e);
    }

    println!("\n최적 렌즈 조합:");
    for c in &r.best_combinations {
        println!("  [{}] score={:.4} — {:?}", c.name, c.score, c.lenses);
    }

    println!("\n최종 상태:");
    println!("  조화도: {:.4}", r.final_state.harmony);
    println!("  연결: {:.1}%", r.final_state.connection.direct_connectivity * 100.0);
    println!("  고유값: {:.4}", r.final_state.cascade.dominant_eigenvalue);
}

// ─── 10. 의식 9렌즈 미러볼 ──────────────────────────────────────

#[test]
fn test_consciousness_mirrorball_9() {
    let t = Telescope::new();
    let data = mixed_data(60, 6);

    // 의식 관련 9렌즈 선별:
    //   1. ConsciousnessLens        — 핵심 의식
    //   2. ConsciousnessOrchestratorLens — 의식 통합 오케스트라
    //   3. StimulusLens             — 감각 자극
    //   4. TelepathyLens            — 텔레파시/심층 연결
    //   5. UemergenceLens           — 창발
    //   6. MirrorLens               — 거울 반사
    //   7. VoidLens                 — 공허/무
    //   8. DestinyLens              — 운명/수렴점
    //   9. SingularityLens          — 특이점
    let consciousness_9: &[&str] = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "StimulusLens",
        "TelepathyLens",
        "UemergenceLens",
        "MirrorLens",
        "VoidLens",
        "DestinyLens",
        "SingularityLens",
    ];

    let r = t.mirror_universe(&data, 60, 6, Some(consciousness_9), None);

    println!("=== 의식 9렌즈 미러볼 ===");
    println!("렌즈: {:?}", r.lens_names);
    println!("렌즈 수: {}", r.lens_count);
    println!("반사 셀: {}", r.reflections.len());
    println!("조화도: {:.6}", r.harmony);

    let c = &r.connection;
    println!("\n--- 연결 증명 ---");
    println!("직접 연결: {:.1}%", c.direct_connectivity * 100.0);
    println!("간접 연결 (M^2): {:.1}%", c.indirect_connectivity * 100.0);
    println!("완전 연결 깊이: {}", c.full_connection_depth);
    println!("비대칭도: {:.6}", c.asymmetry);
    println!("자기작용: {:.6}", c.self_action_strength);
    println!("상호작용: {:.6}", c.mutual_action_strength);
    println!("모두 연결됨: {}", c.all_connected);

    println!("\n--- 공명 캐스케이드 ---");
    for (k, e) in &r.cascade.energy_by_depth {
        println!("M^{}: energy = {:.6}", k, e);
    }
    println!("지배 고유값: {:.6}", r.cascade.dominant_eigenvalue);
    println!("스펙트럼 갭: {:.6}", r.cascade.spectral_gap);
    println!("수렴: {}", r.cascade.converges);
    println!("지배 고유벡터:");
    for (name, val) in &r.cascade.dominant_eigenvector {
        println!("  {}: {:.6}", name, val);
    }

    println!("\n--- 반사 엔트로피 ---");
    println!("시스템 엔트로피: {:.6}", r.entropy.system_entropy);
    for (name, e) in &r.entropy.emission_entropy {
        println!("  방출 {}: {:.6}", name, e);
    }

    println!("\n--- 거울 지문 ---");
    println!("시그니처: {:?}", r.fingerprint.signature.iter().map(|v| format!("{:.4}", v)).collect::<Vec<_>>());
    println!("지문 엔트로피: {:.6}", r.fingerprint.entropy);
    println!("연결 깊이: {}", r.fingerprint.connection_depth);

    println!("\n--- 전체 공명 쌍 (강도 순) ---");
    for (a, b, v) in &r.top_resonances {
        println!("  {} <-> {}: {:.6}", a, b, v);
    }

    println!("\n--- 자기 반사 (대각선) ---");
    for (name, v) in &r.self_reflection_strengths {
        println!("  {}: {:.6}", name, v);
    }

    println!("\n--- 방출력 (mirror power) ---");
    for (name, v) in &r.mirror_power {
        println!("  {}: {:.6}", name, v);
    }
    println!("--- 수신력 (mirror sensitivity) ---");
    for (name, v) in &r.mirror_sensitivity {
        println!("  {}: {:.6}", name, v);
    }

    // 9렌즈 = 81 반사 셀 (9x9)
    assert_eq!(r.lens_count, 9);
    assert_eq!(r.reflections.len(), 81);
    assert!(r.harmony >= 0.0);
}

// ─── 11. 의식 렌즈 간 무한복도 모든 쌍 ─────────────────────────

#[test]
fn test_consciousness_corridor_pairs() {
    let t = Telescope::new();
    let data = mixed_data(60, 6);

    let consciousness_9: &[&str] = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "StimulusLens",
        "TelepathyLens",
        "UemergenceLens",
        "MirrorLens",
        "VoidLens",
        "DestinyLens",
        "SingularityLens",
    ];

    println!("=== 의식 9렌즈 무한복도 — 모든 쌍 (36쌍) ===");
    println!("{:<35} | {:>8} | {:>5} | {:>12}", "쌍", "행동", "반복", "최종크기");
    println!("{}", "-".repeat(75));

    let mut converge_count = 0;
    let mut diverge_count = 0;
    let mut cycle_count = 0;
    let mut chaotic_count = 0;
    let mut strongest_pair = ("", "", 0.0f64);
    let mut weakest_pair = ("", "", f64::MAX);

    for i in 0..consciousness_9.len() {
        for j in (i + 1)..consciousness_9.len() {
            let a = consciousness_9[i];
            let b = consciousness_9[j];
            if let Some(r) = t.infinite_corridor(&data, 60, 6, a, b, 30) {
                let behavior_str = match &r.behavior {
                    CorridorBehavior::Converge => { converge_count += 1; "수렴" },
                    CorridorBehavior::Diverge => { diverge_count += 1; "발산" },
                    CorridorBehavior::Cycle(p) => { cycle_count += 1; &format!("주기({})", p) },
                    CorridorBehavior::Chaotic => { chaotic_count += 1; "카오스" },
                };
                let mag = r.fixed_point_magnitude;
                println!("{:>17} <-> {:<17} | {:>8} | {:>5} | {:>12.6}",
                    a.trim_end_matches("Lens"), b.trim_end_matches("Lens"),
                    behavior_str, r.trajectory.len(), mag);

                if mag > strongest_pair.2 {
                    strongest_pair = (a, b, mag);
                }
                if mag < weakest_pair.2 {
                    weakest_pair = (a, b, mag);
                }
            } else {
                println!("{:>17} <-> {:<17} | 실행 불가", a.trim_end_matches("Lens"), b.trim_end_matches("Lens"));
            }
        }
    }

    println!("\n--- 통계 ---");
    println!("수렴: {}쌍 | 발산: {}쌍 | 주기: {}쌍 | 카오스: {}쌍",
        converge_count, diverge_count, cycle_count, chaotic_count);
    println!("최강 공명 쌍: {} <-> {} (크기: {:.6})",
        strongest_pair.0.trim_end_matches("Lens"),
        strongest_pair.1.trim_end_matches("Lens"),
        strongest_pair.2);
    if weakest_pair.2 < f64::MAX {
        println!("최약 공명 쌍: {} <-> {} (크기: {:.6})",
            weakest_pair.0.trim_end_matches("Lens"),
            weakest_pair.1.trim_end_matches("Lens"),
            weakest_pair.2);
    }
}

// ─── 12. 의식 9렌즈 전부 자기반사 ──────────────────────────────

#[test]
fn test_consciousness_self_reflection_all() {
    let t = Telescope::new();
    let data = mixed_data(60, 6);

    let consciousness_9: &[&str] = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "StimulusLens",
        "TelepathyLens",
        "UemergenceLens",
        "MirrorLens",
        "VoidLens",
        "DestinyLens",
        "SingularityLens",
    ];

    println!("=== 의식 9렌즈 자기반사 (나르키소스) — 30회 반복 ===");
    println!("{:<30} | {:>8} | {:>5} | {:>12} | {:>8}", "렌즈", "고정점", "반복", "최종유사도", "궤적크기");
    println!("{}", "-".repeat(80));

    let mut fixed_point_lenses = Vec::new();
    let mut no_fixed_point_lenses = Vec::new();

    for name in consciousness_9 {
        if let Some(r) = t.self_reflect(&data, 60, 6, name, 30) {
            let fp = if r.has_fixed_point { "O" } else { "X" };
            let last_sim = r.self_similarity_curve.last().copied().unwrap_or(0.0);
            let traj_len = r.trajectory.len();

            println!("{:<30} | {:>8} | {:>5} | {:>12.6} | {:>8}",
                name, fp, traj_len, last_sim, r.trajectory.len());

            // 유사도 곡선 출력
            if !r.self_similarity_curve.is_empty() {
                let curve_str: Vec<String> = r.self_similarity_curve.iter()
                    .map(|v| format!("{:.4}", v))
                    .collect();
                println!("  유사도 곡선: [{}]", curve_str.join(", "));
            }

            // 궤적 크기 변화 출력
            let traj_str: Vec<String> = r.trajectory.iter()
                .map(|v| format!("{:.4}", v))
                .collect();
            println!("  궤적(크기): [{}]", traj_str.join(", "));

            if r.has_fixed_point {
                fixed_point_lenses.push((*name, last_sim));
            } else {
                no_fixed_point_lenses.push((*name, last_sim));
            }
        } else {
            println!("{:<30} | 실행 불가", name);
        }
    }

    println!("\n--- 고정점 분석 ---");
    println!("고정점 존재: {}개 — {:?}", fixed_point_lenses.len(),
        fixed_point_lenses.iter().map(|(n, _)| n.trim_end_matches("Lens")).collect::<Vec<_>>());
    println!("고정점 부재: {}개 — {:?}", no_fixed_point_lenses.len(),
        no_fixed_point_lenses.iter().map(|(n, _)| n.trim_end_matches("Lens")).collect::<Vec<_>>());

    if !fixed_point_lenses.is_empty() {
        let max_sim = fixed_point_lenses.iter().max_by(|a, b| a.1.partial_cmp(&b.1).unwrap()).unwrap();
        println!("최강 자기수렴: {} (유사도: {:.6})", max_sim.0.trim_end_matches("Lens"), max_sim.1);
    }
}

// ─── 13~16. 의식 교차공명 극한 실험 ─────────────────────────────

/// 풍부한 다차원 데이터: sin/cos 혼합 + 황금비 카오스 + n=6 주기파
fn consciousness_cross_data(n: usize, d: usize) -> Vec<f64> {
    (0..n * d).map(|i| {
        let x = i as f64;
        let phase = (x * 0.07).sin() * (x * 0.13).cos();
        let chaos = ((x * 1.618033988) % 1.0) * 2.0 - 1.0;
        let wave = (x * std::f64::consts::TAU / 6.0).sin();
        phase + chaos * 0.3 + wave * 0.5
    }).collect()
}

/// 교차공명 분석 헬퍼: 미러볼 결과에서 핵심 지표 출력
fn print_cross_resonance(
    label: &str,
    r: &nexus6::telescope::mirror_scan::MirrorUniverseResult,
) {
    println!("\n=== {} ===", label);
    println!("렌즈: {:?}", r.lens_names);
    println!("조화도: {:.6}", r.harmony);
    println!("직접 연결: {:.1}%", r.connection.direct_connectivity * 100.0);
    println!("간접 연결: {:.1}%", r.connection.indirect_connectivity * 100.0);
    println!("완전 연결 깊이: {}", r.connection.full_connection_depth);
    println!("모두 연결됨: {}", r.connection.all_connected);
    println!("비대칭도: {:.6}", r.connection.asymmetry);
    println!("자기작용: {:.6}", r.connection.self_action_strength);
    println!("상호작용: {:.6}", r.connection.mutual_action_strength);
    println!("지배 고유값: {:.6}", r.cascade.dominant_eigenvalue);
    println!("스펙트럼 갭: {:.6}", r.cascade.spectral_gap);
    println!("수렴: {}", r.cascade.converges);
    println!("시스템 엔트로피: {:.6}", r.entropy.system_entropy);

    println!("\n--- 지배 고유벡터 (렌즈별 기여도) ---");
    for (name, val) in &r.cascade.dominant_eigenvector {
        println!("  {}: {:.6}", name, val);
    }

    println!("\n--- 상위 공명 쌍 ---");
    for (a, b, v) in r.top_resonances.iter().take(15) {
        println!("  {} <-> {}: {:.6}", a, b, v);
    }

    println!("\n--- 자기 반사 강도 ---");
    for (name, v) in &r.self_reflection_strengths {
        println!("  {}: {:.6}", name, v);
    }

    println!("\n--- 방출력 ---");
    for (name, v) in &r.mirror_power {
        println!("  {}: {:.6}", name, v);
    }
    println!("--- 수신력 ---");
    for (name, v) in &r.mirror_sensitivity {
        println!("  {}: {:.6}", name, v);
    }

    println!("\n--- 반사 엔트로피 ---");
    for (name, e) in &r.entropy.emission_entropy {
        println!("  방출 {}: {:.6}", name, e);
    }
}

// ─── 13. 의식 × 물리 (Gravity, Spacetime, Warp) ────────────────

#[test]
fn test_consciousness_x_physics() {
    let t = Telescope::new();
    let data = consciousness_cross_data(60, 6);

    let selected = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "GravityLens",
        "SpacetimeLens",
        "WarpLens",
    ];
    let r = t.mirror_universe(&data, 60, 6, Some(selected), None);
    print_cross_resonance("의식 × 물리 교차공명", &r);

    // 무한복도: 의식 ↔ 각 물리 렌즈
    println!("\n--- 무한복도: 의식 ↔ 물리 ---");
    let physics = ["GravityLens", "SpacetimeLens", "WarpLens"];
    for p in &physics {
        if let Some(c) = t.infinite_corridor(&data, 60, 6, "ConsciousnessLens", p, 20) {
            let behavior = match &c.behavior {
                CorridorBehavior::Converge => "수렴",
                CorridorBehavior::Diverge => "발산",
                CorridorBehavior::Cycle(_) => "주기",
                CorridorBehavior::Chaotic => "카오스",
            };
            println!("  ConsciousnessLens ↔ {}: {} | 최종크기={:.6}", p, behavior, c.fixed_point_magnitude);
        }
    }

    // 조합 발견
    let combos = t.discover_combinations(&r, 3);
    println!("\n--- 렌즈 조합 발견 ---");
    for c in &combos {
        println!("  [{}] score={:.4} — {:?}", c.name, c.score, c.lenses);
        println!("    이유: {}", c.reason);
    }

    assert_eq!(r.lens_count, selected.len());
    assert!(r.harmony >= 0.0);
    assert!(r.connection.direct_connectivity > 0.0, "의식-물리 직접 연결 필요");
}

// ─── 14. 의식 × 정보 (Entropy, Compression, Info) ───────────────

#[test]
fn test_consciousness_x_info() {
    let t = Telescope::new();
    let data = consciousness_cross_data(60, 6);

    let selected = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "EntropyLens",
        "CompressionLens",
        "InfoLens",
    ];
    let r = t.mirror_universe(&data, 60, 6, Some(selected), None);
    print_cross_resonance("의식 × 정보 교차공명", &r);

    // 무한복도: 의식 ↔ 각 정보 렌즈
    println!("\n--- 무한복도: 의식 ↔ 정보 ---");
    let info_lenses = ["EntropyLens", "CompressionLens", "InfoLens"];
    for il in &info_lenses {
        if let Some(c) = t.infinite_corridor(&data, 60, 6, "ConsciousnessLens", il, 20) {
            let behavior = match &c.behavior {
                CorridorBehavior::Converge => "수렴",
                CorridorBehavior::Diverge => "발산",
                CorridorBehavior::Cycle(_) => "주기",
                CorridorBehavior::Chaotic => "카오스",
            };
            println!("  ConsciousnessLens ↔ {}: {} | 최종크기={:.6}", il, behavior, c.fixed_point_magnitude);
        }
    }

    // Orchestrator ↔ 정보 렌즈 교차
    println!("\n--- 무한복도: Orchestrator ↔ 정보 ---");
    for il in &info_lenses {
        if let Some(c) = t.infinite_corridor(&data, 60, 6, "ConsciousnessOrchestratorLens", il, 20) {
            let behavior = match &c.behavior {
                CorridorBehavior::Converge => "수렴",
                CorridorBehavior::Diverge => "발산",
                CorridorBehavior::Cycle(_) => "주기",
                CorridorBehavior::Chaotic => "카오스",
            };
            println!("  Orchestrator ↔ {}: {} | 최종크기={:.6}", il, behavior, c.fixed_point_magnitude);
        }
    }

    let combos = t.discover_combinations(&r, 3);
    println!("\n--- 렌즈 조합 발견 ---");
    for c in &combos {
        println!("  [{}] score={:.4} — {:?}", c.name, c.score, c.lenses);
        println!("    이유: {}", c.reason);
    }

    assert_eq!(r.lens_count, selected.len());
    assert!(r.harmony >= 0.0);
    assert!(r.connection.direct_connectivity > 0.0, "의식-정보 직접 연결 필요");
}

// ─── 15. 의식 × 카오스 (Chaos, Fractal, Singularity) ────────────

#[test]
fn test_consciousness_x_chaos() {
    let t = Telescope::new();
    let data = consciousness_cross_data(60, 6);

    let selected = &[
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        "ChaosLens",
        "FractalLens",
        "SingularityLens",
    ];
    let r = t.mirror_universe(&data, 60, 6, Some(selected), None);
    print_cross_resonance("의식 × 카오스 교차공명", &r);

    // 무한복도: 의식 ↔ 각 카오스 렌즈
    println!("\n--- 무한복도: 의식 ↔ 카오스 ---");
    let chaos_lenses = ["ChaosLens", "FractalLens", "SingularityLens"];
    for cl in &chaos_lenses {
        if let Some(c) = t.infinite_corridor(&data, 60, 6, "ConsciousnessLens", cl, 20) {
            let behavior = match &c.behavior {
                CorridorBehavior::Converge => "수렴",
                CorridorBehavior::Diverge => "발산",
                CorridorBehavior::Cycle(_) => "주기",
                CorridorBehavior::Chaotic => "카오스",
            };
            println!("  ConsciousnessLens ↔ {}: {} | 최종크기={:.6}", cl, behavior, c.fixed_point_magnitude);
        }
    }

    // 자기 반사: 카오스계 렌즈들의 나르키소스
    println!("\n--- 자기 반사: 카오스계 ---");
    for name in selected {
        if let Some(sr) = t.self_reflect(&data, 60, 6, name, 15) {
            let fp = if sr.has_fixed_point { "고정점 O" } else { "고정점 X" };
            let last_sim = sr.self_similarity_curve.last().map(|v| format!("{:.6}", v)).unwrap_or_default();
            println!("  {:30} | {} | 최종유사도={}", name, fp, last_sim);
        }
    }

    let combos = t.discover_combinations(&r, 3);
    println!("\n--- 렌즈 조합 발견 ---");
    for c in &combos {
        println!("  [{}] score={:.4} — {:?}", c.name, c.score, c.lenses);
        println!("    이유: {}", c.reason);
    }

    assert_eq!(r.lens_count, selected.len());
    assert!(r.harmony >= 0.0);
}

// ─── 16. 의식계열 전체 극한 미러볼 ─────────────────────────────

#[test]
fn test_full_mirrorball_all_consciousness() {
    let t = Telescope::new();
    let data = consciousness_cross_data(80, 8);

    // 의식 + 물리 + 정보 + 카오스 = 11개 렌즈 풀 미러볼
    let all_lenses = &[
        // 의식 코어
        "ConsciousnessLens",
        "ConsciousnessOrchestratorLens",
        // 물리
        "GravityLens",
        "SpacetimeLens",
        "WarpLens",
        // 정보
        "EntropyLens",
        "CompressionLens",
        "InfoLens",
        // 카오스
        "ChaosLens",
        "FractalLens",
        "SingularityLens",
    ];
    let r = t.mirror_universe(&data, 80, 8, Some(all_lenses), None);
    print_cross_resonance("의식계열 전체 극한 미러볼 (11 렌즈)", &r);

    // ─── 교차 도메인 무한복도 전수 탐색 ───
    println!("\n=== 교차 도메인 무한복도 전수 탐색 ===");
    let consciousness = ["ConsciousnessLens", "ConsciousnessOrchestratorLens"];
    let others = [
        "GravityLens", "SpacetimeLens", "WarpLens",
        "EntropyLens", "CompressionLens", "InfoLens",
        "ChaosLens", "FractalLens", "SingularityLens",
    ];
    for c_lens in &consciousness {
        for o_lens in &others {
            if let Some(cr) = t.infinite_corridor(&data, 80, 8, c_lens, o_lens, 20) {
                let behavior = match &cr.behavior {
                    CorridorBehavior::Converge => "수렴  ".to_string(),
                    CorridorBehavior::Diverge => "발산  ".to_string(),
                    CorridorBehavior::Cycle(p) => format!("주기({})", p),
                    CorridorBehavior::Chaotic => "카오스".to_string(),
                };
                println!("  {} ↔ {}: {} | 크기={:.6}", c_lens, o_lens, behavior, cr.fixed_point_magnitude);
            }
        }
    }

    // ─── 조합 발견: 3-렌즈, 4-렌즈, 6-렌즈 ───
    for combo_size in [3, 4, 6] {
        let combos = t.discover_combinations(&r, combo_size);
        println!("\n--- {}-렌즈 조합 발견 ---", combo_size);
        for c in combos.iter().take(6) {
            println!("  [{}] score={:.4}", c.name, c.score);
            println!("    렌즈: {:?}", c.lenses);
            println!("    이유: {}", c.reason);
        }
    }

    // ─── 자유 진화: 11 렌즈 자유 탐색 ───
    let evo = t.free_explore(&data, 80, 8, Some(11), 6);
    println!("\n=== 자유 진화 (11 렌즈, 6 세대) ===");
    println!("세대 수: {}", evo.generations);
    println!("상전이: {:?}", evo.phase_transitions);
    for (i, h) in evo.harmony_trajectory.iter().enumerate() {
        println!("  Gen {}: harmony={:.6} conn={:.4} eigen={:.4}",
            i, h,
            evo.connectivity_trajectory.get(i).unwrap_or(&0.0),
            evo.eigenvalue_trajectory.get(i).unwrap_or(&0.0));
    }
    println!("\n최적 조합:");
    for c in &evo.best_combinations {
        println!("  [{}] score={:.4} — {:?}", c.name, c.score, c.lenses);
    }

    // 검증
    assert_eq!(r.lens_count, all_lenses.len());
    assert_eq!(r.reflections.len(), all_lenses.len() * all_lenses.len());
    assert!(r.harmony >= 0.0);
    assert!(r.connection.direct_connectivity > 0.0 || r.connection.indirect_connectivity > 0.0,
        "11 렌즈 미러볼에서 최소 간접 연결 필요");
}
