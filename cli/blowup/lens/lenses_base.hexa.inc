// ═══════════════════════════════════════════════════════════
// lenses_base.hexa.inc — 렌즈 공용 상수 + 헬퍼 통합 (ROI #22)
// copy-paste 소스 (hexa는 import 미지원, atlas_guard.hexa.inc 패턴)
// 창발 보존: 아래 함수들은 순수 수학/유틸로 렌즈 로직에 영향 없음.
// 이전: 6개 lenses_*.hexa에 ~700줄 중복 → 이 파일 1곳으로 통합.
// ═══════════════════════════════════════════════════════════

// ─── 수학 상수 ───

comptime const pi         = 3.141592653589793
comptime const two_pi     = 6.283185307179586
comptime const e_const    = 2.718281828459045
comptime const phi_golden = 1.618033988749895
comptime const sqrt2      = 1.4142135623730951
comptime const sqrt3      = 1.7320508075688772
comptime const ln2        = 0.6931471805599453
comptime const one_third  = 0.33333333333333

// ─── n=6 공유 상수 ───

comptime const n6     = 6.0
comptime const sigma6 = 12.0
comptime const tau6   = 4.0
comptime const phi6   = 2.0
comptime const sopfr6 = 5.0

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

pure fn atan_f(x: float) -> float {
    if abs_f(x) > 1.0 {
        let s = if x > 0.0 { 1.0 } else { 0.0 - 1.0 }
        return s * pi / 2.0 - atan_f(1.0 / x)
    }
    let mut sum = 0.0
    let mut term = x
    let x2 = x * x
    let mut k = 0
    while k < 12 {
        let denom = to_float(2 * k + 1)
        sum = sum + term / denom
        term = 0.0 - term * x2
        k = k + 1
    }
    sum
}

pure fn asin_f(x: float) -> float {
    let cx = clamp_f(x, 0.0 - 1.0, 1.0)
    atan_f(cx / max_f(sqrt_f(1.0 - cx * cx), 0.000001))
}

pure fn floor_f(x: float) -> int {
    let i = to_int(x)
    if to_float(i) > x { i - 1 } else { i }
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

// ─── 거리/유사도 ───

pure fn row_dist(data, d: int, i: int, j: int) -> float {
    let mut s = 0.0
    let mut k = 0
    while k < d {
        let diff = data[i * d + k] - data[j * d + k]
        s = s + diff * diff
        k = k + 1
    }
    sqrt_f(s)
}

pure fn pairwise_dist(data, i: int, j: int) -> float {
    abs_f(data[i] - data[j])
}

pure fn cosine_sim(a, b) -> float {
    let n = if a.len() < b.len() { a.len() } else { b.len() }
    let mut dot = 0.0
    let mut na = 0.0
    let mut nb = 0.0
    let mut i = 0
    while i < n {
        dot = dot + a[i] * b[i]
        na = na + a[i] * a[i]
        nb = nb + b[i] * b[i]
        i = i + 1
    }
    if na > 0.000000000001 && nb > 0.000000000001 { dot / (sqrt_f(na) * sqrt_f(nb)) } else { 0.0 }
}

// ─── 시계열/통계 ───

pure fn autocorr_lag(data, lag: int) -> float {
    let mean = list_mean(data)
    let mut cov = 0.0
    let mut var = 0.0
    let mut i = 0
    while i < data.len() - lag {
        let d0 = data[i] - mean
        let d1 = data[i + lag] - mean
        cov = cov + d0 * d1
        var = var + d0 * d0
        i = i + 1
    }
    if var > 0.000000000001 { cov / var } else { 0.0 }
}

pure fn shannon_entropy(data) -> float {
    if data.len() < 2 { return 0.0 }
    let sorted = list_sort(data)
    let mut bins = []
    let mut counts = []
    let mut current = sorted[0]
    let mut count = 1
    let mut i = 1
    while i < sorted.len() {
        if abs_f(sorted[i] - current) < 0.01 {
            count = count + 1
        } else {
            bins = bins + [current]
            counts = counts + [count]
            current = sorted[i]
            count = 1
        }
        i = i + 1
    }
    bins = bins + [current]
    counts = counts + [count]
    let total = to_float(data.len())
    let mut ent = 0.0
    for c in counts {
        let p = to_float(c) / total
        if p > 0.0 { ent = ent - p * ln_f(p) }
    }
    ent
}

pure fn count_sign_changes(data) -> int {
    let mut c = 0
    let mut i = 1
    while i < data.len() {
        if (data[i - 1] > 0.0 && data[i] < 0.0) || (data[i - 1] < 0.0 && data[i] > 0.0) {
            c = c + 1
        }
        i = i + 1
    }
    c
}

// ─── 회귀/소수 판정 ───

pure fn linreg(xs, ys) {
    let n = min_f(to_float(xs.len()), to_float(ys.len()))
    let ni = to_int(n)
    if ni < 2 { return [0.0, 0.0] }
    let mut sx = 0.0
    let mut sy = 0.0
    let mut sxx = 0.0
    let mut sxy = 0.0
    let mut syy = 0.0
    let mut i = 0
    while i < ni {
        sx = sx + xs[i]
        sy = sy + ys[i]
        sxx = sxx + xs[i] * xs[i]
        sxy = sxy + xs[i] * ys[i]
        syy = syy + ys[i] * ys[i]
        i = i + 1
    }
    let denom = n * sxx - sx * sx
    if abs_f(denom) < 0.000000000000001 { return [0.0, 0.0] }
    let slope = (n * sxy - sx * sy) / denom
    let ss_res_num = syy - sy * sy / n - slope * (sxy - sx * sy / n)
    let ss_tot = syy - sy * sy / n
    let r2 = if abs_f(ss_tot) > 0.000000000000001 { 1.0 - ss_res_num / ss_tot } else { 0.0 }
    [slope, clamp_f(r2, 0.0, 1.0)]
}

pure fn is_prime(val: int) -> bool {
    if val < 2 { return false }
    if val < 4 { return true }
    if val % 2 == 0 || val % 3 == 0 { return false }
    let mut i = 5
    while i * i <= val {
        if val % i == 0 || val % (i + 2) == 0 { return false }
        i = i + 6
    }
    true
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

fn load_n6_consts() -> list {
    let home = exec("printenv HOME")
    let path = home + "/Dev/nexus/n6/n6_constants.jsonl"
    let raw = try { read_file(path) } catch e { return [#{}, [], []] }
    let lines = raw.split("\n")
    let mut names = []
    let mut values = []
    let mut lookup = #{}
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
            lookup[name] = value
        }
    }
    [lookup, names, values]
}

fn n6_const(consts: list, name: string) -> f64 {
    let lookup = consts[0]
    try {
        return to_float(lookup[name])
    } catch e {
        return 0.0
    }
}

fn n6_values(consts: list) -> list {
    consts[1]
}

// ─── exp_approx (가벼운 6차 근사, math용) ───

pure fn exp_approx(x: float) -> float {
    let cx = clamp_f(x, -20.0, 20.0)
    let mut sum = 1.0
    let mut term = cx
    sum = sum + term
    term = term * cx / 2.0
    sum = sum + term
    term = term * cx / 3.0
    sum = sum + term
    term = term * cx / 4.0
    sum = sum + term
    term = term * cx / 5.0
    sum = sum + term
    term = term * cx / 6.0
    sum = sum + term
    term = term * cx / 7.0
    sum = sum + term
    term = term * cx / 8.0
    sum = sum + term
    if sum < 0.0 { 0.0 } else { sum }
}
