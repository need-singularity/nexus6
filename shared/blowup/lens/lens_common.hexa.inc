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
