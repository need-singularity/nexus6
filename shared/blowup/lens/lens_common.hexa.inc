// ═══════════════════════════════════════════════════════════
// lens_common.hexa.inc — 렌즈 공용 상수 + 헬퍼 (ROI #22)
// copy-paste 소스 (hexa는 import 미지원, atlas_guard.hexa.inc 패턴)
// 창발 보존: 아래 함수들은 순수 수학 유틸로 렌즈 로직에 영향 없음.
// ═══════════════════════════════════════════════════════════

// ─── n=6 공유 상수 ───

comptime const n6     = 6.0
comptime const sigma6 = 12.0
comptime const tau6   = 4.0
comptime const phi6   = 2.0
comptime const sopfr6 = 5.0

// ─── 수학 상수 ───

comptime const pi         = 3.141592653589793
comptime const two_pi     = 6.283185307179586
comptime const e_const    = 2.718281828459045
comptime const phi_golden = 1.618033988749895
comptime const sqrt2      = 1.4142135623730951
comptime const sqrt3      = 1.7320508075688772
comptime const ln2        = 0.6931471805599453

// ─── 기본 수학 헬퍼 ───

pure fn min_f(a: float, b: float) -> float { if a < b { a } else { b } }
pure fn max_f(a: float, b: float) -> float { if a > b { a } else { b } }
pure fn clamp_f(v: float, lo: float, hi: float) -> float { min_f(max_f(v, lo), hi) }
pure fn clamp01(x: float) -> float { max_f(0.0, min_f(1.0, x)) }

pure fn to_int(x: float) -> int {
    if x >= 0.0 { int(x) } else { 0 - int(0.0 - x) }
}

// ─── Taylor 급수 근사 ───

pure fn exp_f(x: float) -> float {
    let cx = clamp_f(x, 0.0 - 20.0, 20.0)
    let mut sum = 1.0
    let mut term = 1.0
    let mut k = 1
    while k <= 20 {
        term = term * cx / to_float(k)
        sum = sum + term
        k = k + 1
    }
    sum
}

pure fn sin_f(x: float) -> float {
    let mut v = x
    while v > pi { v = v - two_pi }
    while v < 0.0 - pi { v = v + two_pi }
    let mut sum = 0.0
    let mut term = v
    let mut k = 1
    while k <= 12 {
        sum = sum + term
        term = 0.0 - term * v * v / to_float((2 * k) * (2 * k + 1))
        k = k + 1
    }
    sum
}

pure fn cos_f(x: float) -> float { sin_f(x + pi / 2.0) }

pure fn pow_f(base: float, exp: int) -> float {
    let mut r = 1.0
    let mut i = 0
    while i < exp {
        r = r * base
        i = i + 1
    }
    r
}

// ─── 리스트 집계 ───

pure fn list_sum(data) -> float {
    let mut s = 0.0
    for v in data { s = s + v }
    s
}

pure fn list_min(data) -> float {
    if data.len() == 0 { return 0.0 }
    let mut m = data[0]
    let mut i = 1
    while i < data.len() {
        if data[i] < m { m = data[i] }
        i = i + 1
    }
    m
}

pure fn list_max(data) -> float {
    if data.len() == 0 { return 0.0 }
    let mut m = data[0]
    let mut i = 1
    while i < data.len() {
        if data[i] > m { m = data[i] }
        i = i + 1
    }
    m
}

pure fn list_std(data, mean: float) -> float {
    sqrt_f(list_variance(data, mean))
}

// ─── 열 통계 (n×d row-major 행렬) ───

pure fn col_means(data, n: int, d: int) -> [] {
    let mut means = []
    let mut j = 0
    while j < d {
        let mut s = 0.0
        let mut i = 0
        while i < n {
            s = s + data[i * d + j]
            i = i + 1
        }
        means = means + [s / to_float(n)]
        j = j + 1
    }
    means
}

pure fn col_stds(data, n: int, d: int, means) -> [] {
    let mut stds = []
    let mut j = 0
    while j < d {
        let m = means[j]
        let mut var = 0.0
        let mut i = 0
        while i < n {
            let diff = data[i * d + j] - m
            var = var + diff * diff
            i = i + 1
        }
        stds = stds + [sqrt_f(var / to_float(n))]
        j = j + 1
    }
    stds
}

pure fn col_mean(data, n: int, d: int, j: int) -> float {
    let mut s = 0.0
    let mut i = 0
    while i < n {
        s = s + data[i * d + j]
        i = i + 1
    }
    s / max_f(to_float(n), 1.0)
}

pure fn col_std(data, n: int, d: int, j: int, mean: float) -> float {
    let mut v = 0.0
    let mut i = 0
    while i < n {
        let diff = data[i * d + j] - mean
        v = v + diff * diff
        i = i + 1
    }
    sqrt_f(v / to_float(n))
}

// ─── n=6 공명 점수 ───

// 단일 값이 n=6 상수 5개 중 하나와 tol 이내 공명하는지
pure fn _resonates(m: float, tol: float) -> bool {
    let targets = [n6, tau6, sigma6, phi6, sopfr6]
    let mut found = false
    for t in targets {
        if t > 0.000000000001 {
            if abs_f(m - t) / t < tol { found = true }
        }
    }
    found
}

// 목록 중 n=6 상수와 tol 이내 공명 비율
pure fn resonance_score(means, tol: float) -> float {
    let mut hits = 0
    for m in means {
        if _resonates(m, tol) { hits = hits + 1 }
    }
    to_float(hits) / max_f(to_float(means.len()), 1.0)
}

// 차원 n=6 공명 (d가 6에 가까울수록 1)
pure fn dim_n6_score(d: int) -> float {
    max_f(1.0 - abs_f(to_float(d) - n6) / n6 * 2.0, 0.0)
}

// 신호 강도 (mean_abs / (mean_abs + mean_std))
pure fn signal_ratio_score(means, stds, d: int) -> float {
    if d == 0 { return 0.0 }
    let mut std_sum = 0.0
    let mut abs_sum = 0.0
    for s in stds  { std_sum = std_sum + s }
    for m in means { abs_sum = abs_sum + abs_f(m) }
    let mean_std = std_sum / to_float(d)
    let mean_val = abs_sum / to_float(d)
    clamp_f(mean_val / (mean_val + mean_std + 0.000000000001), 0.0, 1.0)
}

// 단조 변화율 (열별 양방향 단조성 평균)
pure fn monotone_score(data, n: int, d: int) -> float {
    if d == 0 { return 0.0 }
    let mut s = 0.0
    let mut j = 0
    while j < d {
        let mut pos = 0
        let mut total = 0
        let mut i = 1
        while i < n {
            let diff = data[i * d + j] - data[(i - 1) * d + j]
            if diff > 0.0 { pos = pos + 1 }
            total = total + 1
            i = i + 1
        }
        if total > 0 {
            let ratio = to_float(pos) / to_float(total)
            s = s + abs_f(ratio - 0.5) * 2.0
        }
        j = j + 1
    }
    s / max_f(to_float(d), 1.0)
}

// ─── JSONL 파서 (n6/physics 상수 로드) ───

fn load_jsonl_kv(path: string) -> list {
    let raw = try { read_file(path) } catch e { return [[], []] }
    let lines = raw.split("\n")
    let mut names = []
    let mut values = []
    for line in lines {
        let trimmed = line.trim()
        if trimmed == "" { continue }
        let mut name = ""
        let mut value = 0.0
        if trimmed.contains("\"name\":\"") {
            let p = trimmed.split("\"name\":\"")
            if p.len() >= 2 { name = p[1].split("\"")[0] }
        }
        if trimmed.contains("\"value\":") {
            let p = trimmed.split("\"value\":")
            if p.len() >= 2 {
                let num_str = p[1].split(",")[0].split("}")[0].trim()
                value = to_float(num_str)
            }
        }
        if name != "" {
            names = names + [name]
            values = values + [value]
        }
    }
    [names, values]
}

fn kv_lookup(data: list, key: string) -> float {
    let names = data[0]
    let values = data[1]
    let mut i = 0
    while i < len(names) {
        if names[i] == key { return values[i] }
        i = i + 1
    }
    0.0
}

// ═══════════════════════════════════════════════════════════
// BIOLOGY 도메인 모듈 — LENS-P2-2
// 생명계 수학 유틸. 렌즈 로직 불변 (순수 상수 + pure fn).
// 의존: exp_f/ln_f/pow_f/abs_f/clamp01/sqrt_f (caller context)
// ═══════════════════════════════════════════════════════════

// ─── 생명 상수 ───

comptime const bio_codons       = 64.0
comptime const bio_amino_acids  = 20.0
comptime const bio_dna_bases    = 4.0
comptime const bio_kleiber_exp  = 0.75
comptime const bio_kt_eV_298K   = 0.02526
comptime const bio_human_chroms = 46.0
comptime const bio_gc_balance   = 0.5

// Michaelis-Menten 효소 운동학: v = Vmax · S / (Km + S)
pure fn bio_michaelis_menten(vmax: float, km: float, s: float) -> float {
    let denom = km + s
    if abs_f(denom) < 0.000000000001 { return 0.0 }
    vmax * s / denom
}

// Hill 협동 결합: θ = L^n / (Kd^n + L^n)
pure fn bio_hill_equation(l: float, kd: float, n: int) -> float {
    let ln_val = pow_f(l, n)
    let kdn    = pow_f(kd, n)
    let denom  = kdn + ln_val
    if abs_f(denom) < 0.000000000001 { return 0.0 }
    ln_val / denom
}

// 로지스틱 성장률: dN/dt = r · N · (1 - N/K)
pure fn bio_logistic_growth_rate(r: float, n: float, k: float) -> float {
    if abs_f(k) < 0.000000000001 { return 0.0 }
    r * n * (1.0 - n / k)
}

// Lotka-Volterra prey 1-step: prey' = prey + dt·(a·prey - b·prey·pred)
pure fn bio_lv_prey_step(prey: float, pred: float, a: float, b: float, dt: float) -> float {
    prey + dt * (a * prey - b * prey * pred)
}

// Lotka-Volterra predator 1-step: pred' = pred + dt·(c·prey·pred - d·pred)
pure fn bio_lv_pred_step(prey: float, pred: float, c: float, d: float, dt: float) -> float {
    pred + dt * (c * prey * pred - d * pred)
}

// Hardy-Weinberg 동형접합 예상 빈도 (p²)
pure fn bio_hw_homozygous(p: float) -> float {
    let cp = clamp01(p)
    cp * cp
}

// GC 함량 비율 (DNA 구성)
pure fn bio_gc_content(gc_count: int, total: int) -> float {
    if total == 0 { return 0.0 }
    to_float(gc_count) / to_float(total)
}

// Shannon 다양도 H = -Σ p·ln(p) (probs 정규화 전제)
pure fn bio_shannon_diversity(probs) -> float {
    let mut h = 0.0
    for p in probs {
        if p > 0.000000000001 {
            h = h + p * ln_f(p)
        }
    }
    0.0 - h
}

// Kleiber 대사율 스케일: M^(3/4)
pure fn bio_kleiber_scale(mass: float) -> float {
    if mass <= 0.000000000001 { return 0.0 }
    exp_f(bio_kleiber_exp * ln_f(mass))
}

// 코돈 축퇴도 (64/20 ≈ 3.2)
pure fn bio_codon_degeneracy() -> float {
    bio_codons / bio_amino_acids
}

// 인구 변화: Malthusian 지수 증가 N(t) = N0·e^(rt)
pure fn bio_malthus_population(n0: float, r: float, t: float) -> float {
    n0 * exp_f(r * t)
}


// ═══════════════════════════════════════════════════════════
// CHEMISTRY 도메인 모듈 — LENS-P2-2
// 물리화학 수학 유틸. 렌즈 로직 불변 (순수 상수 + pure fn).
// 의존: exp_f/ln_f/pow_f/abs_f/sqrt_f (caller context)
// ═══════════════════════════════════════════════════════════

// ─── 화학 상수 ───

comptime const chem_avogadro      = 6.02214076e23
comptime const chem_gas_R         = 8.31446261815324
comptime const chem_kB            = 1.380649e-23
comptime const chem_faraday       = 96485.33212
comptime const chem_e_charge      = 1.602176634e-19
comptime const chem_molar_vol_STP = 22.413996
comptime const chem_T_room        = 298.15
comptime const chem_RT_room       = 2478.82
comptime const chem_ln10          = 2.302585092994046

// Arrhenius 반응 속도: k = A · exp(-Ea / RT)
pure fn chem_arrhenius_rate(a_pre: float, ea: float, t_kelvin: float) -> float {
    if t_kelvin < 0.000000000001 { return 0.0 }
    let exponent = 0.0 - ea / (chem_gas_R * t_kelvin)
    a_pre * exp_f(exponent)
}

// 이상기체 압력: P = nRT/V
pure fn chem_ideal_gas_pressure(n_mol: float, t_kelvin: float, v: float) -> float {
    if abs_f(v) < 0.000000000001 { return 0.0 }
    n_mol * chem_gas_R * t_kelvin / v
}

// 이상기체 부피: V = nRT/P
pure fn chem_ideal_gas_volume(n_mol: float, t_kelvin: float, p: float) -> float {
    if abs_f(p) < 0.000000000001 { return 0.0 }
    n_mol * chem_gas_R * t_kelvin / p
}

// Nernst 전위: E = E0 - (RT / nF) · ln(Q)
pure fn chem_nernst_potential(e0: float, n_elec: int, q: float, t_kelvin: float) -> float {
    if n_elec == 0 { return e0 }
    if q < 0.000000000001 { return e0 }
    let coeff = chem_gas_R * t_kelvin / (to_float(n_elec) * chem_faraday)
    e0 - coeff * ln_f(q)
}

// log10 헬퍼: ln(x) / ln(10)
pure fn chem_log10(x: float) -> float {
    if x <= 0.000000000001 { return 0.0 - 1000000.0 }
    ln_f(x) / chem_ln10
}

// pH ← [H+]: pH = -log10([H+])
pure fn chem_ph_from_h(h_conc: float) -> float {
    0.0 - chem_log10(h_conc)
}

// [H+] ← pH: [H+] = 10^(-pH) = exp(-pH · ln10)
pure fn chem_h_from_ph(ph: float) -> float {
    exp_f((0.0 - ph) * chem_ln10)
}

// Henderson-Hasselbalch: pH = pKa + log10([A-]/[HA])
pure fn chem_henderson_hasselbalch(pka: float, a_minus: float, ha: float) -> float {
    if ha < 0.000000000001 { return pka }
    if a_minus < 0.000000000001 { return pka }
    pka + chem_log10(a_minus / ha)
}

// 평형상수 K_eq ← ΔG°: K = exp(-ΔG / RT)
pure fn chem_equilibrium_k(delta_g: float, t_kelvin: float) -> float {
    if t_kelvin < 0.000000000001 { return 1.0 }
    exp_f(0.0 - delta_g / (chem_gas_R * t_kelvin))
}

// 1차 반응 반감기: t½ = ln(2) / k
pure fn chem_half_life_first_order(k_rate: float) -> float {
    if abs_f(k_rate) < 0.000000000001 { return 0.0 }
    ln2 / k_rate
}

// Van der Waals 보정 압력: P = nRT/(V - nb) - a·n²/V²
pure fn chem_vdw_pressure(n_mol: float, t_kelvin: float, v: float, a_vdw: float, b_vdw: float) -> float {
    let denom_v = v - n_mol * b_vdw
    if abs_f(denom_v) < 0.000000000001 { return 0.0 }
    if abs_f(v) < 0.000000000001 { return 0.0 }
    let repulsive  = n_mol * chem_gas_R * t_kelvin / denom_v
    let attractive = a_vdw * n_mol * n_mol / (v * v)
    repulsive - attractive
}

// 화학양론 잔차 (observed vs ideal 비율 RMS 거리, 0=완벽)
pure fn chem_stoichiometry_residual(observed, ideal) -> float {
    if observed.len() == 0 { return 0.0 }
    if observed.len() != ideal.len() { return 0.0 }
    let mut sum = 0.0
    let mut i = 0
    while i < observed.len() {
        let diff = observed[i] - ideal[i]
        sum = sum + diff * diff
        i = i + 1
    }
    sqrt_f(sum / to_float(observed.len()))
}
