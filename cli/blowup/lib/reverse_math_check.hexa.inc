// ═══════════════════════════════════════════════════════════
// reverse_math_check.hexa.inc — Simpson Big Five 체계 판정 휴리스틱
// 설계: shared/blowup/design/mk9_hyperarithmetic.md §2 단계 C
// 사용: .hexa 스크립트 상단에 include
//
//   let rca  = check_rca0(prop_text)
//   let wkl  = check_wkl0(prop_text)
//   let aca  = check_aca0(prop_text)
//   let atr  = check_atr0(prop_text)
//   let p11  = check_pi11_ca0(prop_text)
//   let verdict = reverse_math_consensus(prop_text)
//
// 반환값 (개별 check_*):
//   "TRUE"       — 해당 체계에서 증명 가능 (알려진 reverse-math 결과)
//   "FALSE"      — 해당 체계에서 증명 불가 (strength 부족 알려짐)
//   "UNKNOWN"    — 문헌 DB 에 없음, heuristic 점수도 무결정
//   "UNIVERSAL"  — 모든 체계에서 trivial (Δ₀ 또는 매우 약한 명제)
//
// 반환값 (reverse_math_consensus):
//   "REVERSE-UNIVERSAL-PASS" — 5/5 TRUE
//   "REVERSE-TRUE-PASS"      — 3/5 이상 TRUE
//   "REVERSE-FAIL"           — FALSE 과반 (≥3)
//   "REVERSE-UNKNOWN"        — 그 외 (부분 TRUE / UNKNOWN 다수)
//
// 정책:
//   - 본 모듈은 formal 증명기가 아니라 meta-검증자 (mk9 §2.C 단계 2).
//   - 키워드 매칭 + atlas.n6 known-answer 룩업 기반.
//   - 95% target 정확도 (완전성 포기, Gödel 불완전성).
//   - 화이트리스트 미스 → UNKNOWN (보수적).
// ═══════════════════════════════════════════════════════════

// ─── 내부: 프로퍼티 정규화 (소문자, 공백 정리) ───
fn _rm_normalize(prop: string) -> string {
    let mut s = prop.to_lowercase()
    // 한국어는 그대로 두되, 영문/기호는 소문자 통일
    return s.trim()
}

// ─── 내부: 키워드 포함 검사 ───
fn _rm_has(hay: string, needle: string) -> bool {
    return hay.contains(needle.to_lowercase())
}

// ─── 내부: atlas.n6 에 해당 명제가 이미 등재되었는지 룩업 ───
// atlas.n6 의 관련 라인에서 등급 태그를 간이 추출.
// [10*] / [11*] / [12*] 등급이면 TRUE 시그널, [9?] / [N?] 이면 UNKNOWN 시그널.
fn _rm_atlas_known(prop: string) -> string {
    let home = exec("printenv HOME").trim()
    let atlas = home + "/core/nexus/n6/atlas.n6"
    let exists = exec("test -f '" + atlas + "' && echo y || echo n").trim()
    if exists != "y" { return "MISS" }

    // 첫 8단어 중 식별 키워드 추출
    let toks = prop.split(" ")
    let mut probe = ""
    let mut k: i64 = 0
    while k < len(toks) && k < 3 {
        let t = toks[k].trim()
        if len(t) >= 3 {
            probe = t
            break
        }
        k = k + 1
    }
    if len(probe) == 0 { return "MISS" }

    // grep 보호: single-quote escape
    let safe = probe.replace("'", "")
    let hit = exec("grep -m1 -F -- '" + safe + "' '" + atlas + "' 2>/dev/null || true").trim()
    if len(hit) == 0 { return "MISS" }

    if hit.contains("[12*]") { return "TRUE" }
    if hit.contains("[11*]") { return "TRUE" }
    if hit.contains("[10*]") { return "TRUE" }
    if hit.contains("[10]")  { return "TRUE" }
    if hit.contains("[9?]")  { return "UNKNOWN" }
    if hit.contains("[N?]")  { return "UNKNOWN" }
    if hit.contains("[N!]")  { return "TRUE" }
    return "MISS"
}

// ─── 내부: reverse-math 문헌 기반 whitelist ───
// Simpson SOSOA, Dzhafarov-Mummert 표준 결과.
// 각 항목: (system_min, keyword_set)
// system_min 이상 체계에서 증명 가능 (사슬: RCA₀<WKL₀<ACA₀<ATR₀<Π¹₁-CA₀).
//
// 초기 시드 (mk9 §2.C 단계 2 & §8 테스트 시나리오 기반).
fn _rm_whitelist_min_system(prop: string) -> string {
    let p = _rm_normalize(prop)

    // === RCA₀ 등급 (유한 구조, Δ₁ comprehension) ===
    if _rm_has(p, "sylow")                { return "RCA0" }
    if _rm_has(p, "fermat little")        { return "RCA0" }
    if _rm_has(p, "wilson")               { return "RCA0" }
    if _rm_has(p, "euclid")   && _rm_has(p, "prime") { return "RCA0" }
    if _rm_has(p, "bertrand")             { return "RCA0" }
    if _rm_has(p, "sigma_6")  || _rm_has(p, "σ(6)") { return "RCA0" }
    if _rm_has(p, "tau(6)")   || _rm_has(p, "τ(6)") { return "RCA0" }
    if _rm_has(p, "perfect number") && _rm_has(p, "6 = ") { return "RCA0" }
    if _rm_has(p, "out(s_n)") || _rm_has(p, "out(s6)") { return "RCA0" }
    if _rm_has(p, "finite group")         { return "RCA0" }

    // === WKL₀ 등급 (compactness, 약 König) ===
    if _rm_has(p, "heine-borel")          { return "WKL0" }
    if _rm_has(p, "compactness")          { return "WKL0" }
    if _rm_has(p, "gödel completeness") || _rm_has(p, "godel completeness") { return "WKL0" }
    if _rm_has(p, "brouwer fixed")        { return "WKL0" }
    if _rm_has(p, "weak könig") || _rm_has(p, "weak konig") { return "WKL0" }
    if _rm_has(p, "vinogradov")           { return "WKL0" }
    if _rm_has(p, "goldbach") && _rm_has(p, "weak") { return "WKL0" }

    // === ACA₀ 등급 (arithmetical comprehension ≈ PA) ===
    if _rm_has(p, "bolzano-weierstrass")  { return "ACA0" }
    if _rm_has(p, "bolzano")              { return "ACA0" }
    if _rm_has(p, "ramsey") && _rm_has(p, "3") { return "ACA0" }
    if _rm_has(p, "könig lemma") || _rm_has(p, "konig lemma") { return "ACA0" }
    if _rm_has(p, "arithmetical comprehension") { return "ACA0" }
    if _rm_has(p, "4-color") || _rm_has(p, "four color") || _rm_has(p, "4-착색") { return "ACA0" }
    if _rm_has(p, "schläfli") || _rm_has(p, "schlafli") { return "ACA0" }
    if _rm_has(p, "정다포체") && _rm_has(p, "6") { return "ACA0" }

    // === ATR₀ 등급 (transfinite recursion, well-ordering) ===
    if _rm_has(p, "transfinite recursion") { return "ATR0" }
    if _rm_has(p, "ulm")                   { return "ATR0" }
    if _rm_has(p, "comparability of well-ordering") { return "ATR0" }
    if _rm_has(p, "hausdorff")             { return "ATR0" }
    if _rm_has(p, "open determinacy")      { return "ATR0" }

    // === Π¹₁-CA₀ 등급 ===
    if _rm_has(p, "cantor-bendixson")      { return "PI11_CA0" }
    if _rm_has(p, "perfect set")           { return "PI11_CA0" }
    if _rm_has(p, "σ¹₁")  || _rm_has(p, "sigma_1_1") { return "PI11_CA0" }
    if _rm_has(p, "π¹₁")  || _rm_has(p, "pi_1_1")    { return "PI11_CA0" }

    // === 알려진 미해결/blacklist ===
    if _rm_has(p, "perfect") && _rm_has(p, "infinite") { return "OPEN" }
    if _rm_has(p, "odd perfect")           { return "OPEN" }
    if _rm_has(p, "riemann hypothesis")    { return "OPEN" }
    if _rm_has(p, "twin prime")            { return "OPEN" }
    if _rm_has(p, "goldbach") && !_rm_has(p, "weak") { return "OPEN" }
    if _rm_has(p, "con(zfc)") || _rm_has(p, "consistency of zfc") { return "OPEN" }

    return "MISS"
}

// ─── 내부: 체계 강도 사슬 비교 ───
// target 체계가 required 이상 강도인가?
// 순서: RCA0 < WKL0 < ACA0 < ATR0 < PI11_CA0
fn _rm_system_rank(sys: string) -> i64 {
    if sys == "RCA0"     { return 1 }
    if sys == "WKL0"     { return 2 }
    if sys == "ACA0"     { return 3 }
    if sys == "ATR0"     { return 4 }
    if sys == "PI11_CA0" { return 5 }
    return 0
}

// ─── 내부: 지정 체계에서 증명 가능 판정 ───
// min_sys 이상 강도 체계이면 TRUE, 아니면 UNKNOWN (반증 근거 없음).
// OPEN 은 UNKNOWN.
// Δ₀-류 atlas known answer 는 UNIVERSAL.
fn _rm_judge(prop: string, target_sys: string) -> string {
    // 1순위: atlas known-answer
    let atlas_sig = _rm_atlas_known(prop)
    if atlas_sig == "TRUE"    { /* 하지만 체계 강도 확인 필요 — fallthrough */ }
    if atlas_sig == "UNKNOWN" { return "UNKNOWN" }

    // 2순위: whitelist 룩업
    let min_sys = _rm_whitelist_min_system(prop)

    if min_sys == "OPEN" { return "UNKNOWN" }
    if min_sys == "MISS" {
        // atlas 에 있고 [10*]+ 인 경우 → 최소 ACA₀ 수준으로 간주 (보수)
        if atlas_sig == "TRUE" {
            let tr = _rm_system_rank(target_sys)
            if tr >= 3 { return "TRUE" }
            return "UNKNOWN"
        }
        return "UNKNOWN"
    }

    // 사슬: min_sys 이상 체계면 증명 가능
    let min_rank = _rm_system_rank(min_sys)
    let tgt_rank = _rm_system_rank(target_sys)
    if min_rank == 0 || tgt_rank == 0 { return "UNKNOWN" }

    if tgt_rank >= min_rank {
        // RCA₀ 에서 증명 가능하면 전체 체계에서 TRUE → UNIVERSAL 후보
        if min_rank == 1 && tgt_rank == 5 { return "TRUE" }
        return "TRUE"
    }
    // target 이 약해서 증명 불가
    return "FALSE"
}

// ═══════════════════════════════════════════════════════════
// 공개 API — 5 체계 판정 fn
// ═══════════════════════════════════════════════════════════

fn check_rca0(prop: string) -> string {
    return _rm_judge(prop, "RCA0")
}

fn check_wkl0(prop: string) -> string {
    return _rm_judge(prop, "WKL0")
}

fn check_aca0(prop: string) -> string {
    return _rm_judge(prop, "ACA0")
}

fn check_atr0(prop: string) -> string {
    return _rm_judge(prop, "ATR0")
}

fn check_pi11_ca0(prop: string) -> string {
    return _rm_judge(prop, "PI11_CA0")
}

// ═══════════════════════════════════════════════════════════
// 종합 판정 — 3/5 / 5/5 / FAIL 분류
// ═══════════════════════════════════════════════════════════

fn reverse_math_consensus(prop: string) -> string {
    let r1 = check_rca0(prop)
    let r2 = check_wkl0(prop)
    let r3 = check_aca0(prop)
    let r4 = check_atr0(prop)
    let r5 = check_pi11_ca0(prop)

    let results = [r1, r2, r3, r4, r5]

    let mut n_true: i64 = 0
    let mut n_false: i64 = 0
    let mut n_unknown: i64 = 0
    let mut n_universal: i64 = 0

    let mut i: i64 = 0
    while i < 5 {
        let r = results[i]
        if r == "TRUE"       { n_true = n_true + 1 }
        if r == "FALSE"      { n_false = n_false + 1 }
        if r == "UNKNOWN"    { n_unknown = n_unknown + 1 }
        if r == "UNIVERSAL"  { n_universal = n_universal + 1 }
        i = i + 1
    }

    // UNIVERSAL 이 5 = 전 체계 trivial
    if n_universal == 5 { return "REVERSE-UNIVERSAL-PASS" }

    // 5/5 TRUE = universal pass (mk9 §2.C 단계 3 정당화: RCA₀ 증명 → 5/5)
    let n_pass = n_true + n_universal
    if n_pass >= 5 { return "REVERSE-UNIVERSAL-PASS" }

    // 3/5 이상 TRUE = true pass
    if n_pass >= 3 { return "REVERSE-TRUE-PASS" }

    // FALSE 과반 (≥3) = fail
    if n_false >= 3 { return "REVERSE-FAIL" }

    // 그 외 — UNKNOWN 다수이거나 결정 불가
    return "REVERSE-UNKNOWN"
}

// ═══════════════════════════════════════════════════════════
// 디버깅 보조 — 5 체계 결과 문자열 (진단 출력용)
// ═══════════════════════════════════════════════════════════

fn reverse_math_report(prop: string) -> string {
    let r1 = check_rca0(prop)
    let r2 = check_wkl0(prop)
    let r3 = check_aca0(prop)
    let r4 = check_atr0(prop)
    let r5 = check_pi11_ca0(prop)
    let c  = reverse_math_consensus(prop)
    return "RCA0=" + r1 + " WKL0=" + r2 + " ACA0=" + r3 + " ATR0=" + r4 + " PI11=" + r5 + " :: " + c
}
