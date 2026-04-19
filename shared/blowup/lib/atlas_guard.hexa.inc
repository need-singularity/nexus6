// ═══════════════════════════════════════════════════════════
// AI-native atlas 가드 헬퍼 (core/blowup.hexa에서 발췌)
// 사용: 이 섹션을 모듈 파일 상단(exec/read_file 도입 전)에 copy-paste.
// 창발 보존: 아래 함수들은 append-path에 필터 + dedup만 추가하며
// phase 로직/discovery 계산/seed 진화 등 반환 값에 영향 없음.
// ═══════════════════════════════════════════════════════════

// ─── Schema guard: atlas.n6 라인 포맷 검증 ───
// 유효: 빈줄/# 주석/{"type":/@X ... [grade]/들여쓰기 부속("<-!!->)
fn _valid_atlas_line(line: string) -> bool {
    let t = line.trim()
    if len(t) == 0 { return true }
    // OPT-P8-9: 8 if-chain → single .contains() (core blowup.hexa 동기화)
    let allowed = "#{@\"<>!-"
    return allowed.contains(t[0..1])
}

// ─── Grade whitelist + ordering (AI-native 계층 등급) ───
// 등급 체인 (낮→높):
//   [N?]  CONJECTURE
//   [N!]  breakthrough (conjecture-class, unreviewed)
//   [5]   중간
//   [6]   중간
//   [7]   EMPIRICAL (승격대상)
//   [8]   중간
//   [9]   NEAR
//   [10]  EXACT
//   [10*] EXACT 검증됨
//   [10**] meta-closed  (Phase 10 Meta-Closure 통과)   ← NEW
//   [11*] Δ₀-absolute foundation
//   [12*] Π₀² hyperarithmetic foundation (수동 승급)    ← NEW
// 참고: core blowup.hexa 의 match_grade() 는 수치거리→심볼(EXACT/NEAR/...)
// 매핑이며, 여기의 bracket-suffix 등급은 atlas.n6 라인의 `[...]` 서픽스다.
fn _known_atlas_grade(g: string) -> bool {
    // 정확 일치 기준 허용 등급 whitelist
    if g == "[10*]"  { return true }
    if g == "[10**]" { return true }  // NEW: meta-closed
    if g == "[11*]"  { return true }
    if g == "[12*]"  { return true }  // NEW: Π₀² foundation
    if g == "[10]"   { return true }
    if g == "[9]"    { return true }
    if g == "[8]"    { return true }
    if g == "[7]"    { return true }
    if g == "[6]"    { return true }
    if g == "[5]"    { return true }
    if g == "[N?]"   { return true }
    if g == "[N!]"   { return true }
    return false
}

// grade-to-priority: 숫자가 클수록 높은 등급. 정렬/비교용.
// [10*] < [10**] < [11*] < [12*] 순서 보장.
fn _atlas_grade_priority(g: string) -> i64 {
    if g == "[N?]"   { return 0 }
    if g == "[N!]"   { return 1 }
    if g == "[5]"    { return 5 }
    if g == "[6]"    { return 6 }
    if g == "[7]"    { return 7 }
    if g == "[8]"    { return 8 }
    if g == "[9]"    { return 9 }
    if g == "[10]"   { return 10 }
    if g == "[10*]"  { return 20 }
    if g == "[10**]" { return 25 }  // NEW: between [10*] and [11*]
    if g == "[11*]"  { return 30 }
    if g == "[12*]"  { return 40 }  // NEW: above [11*]
    return -1  // unknown
}

// 라인 꼬리에서 bracket-suffix 등급 추출. 없으면 "".
// "... :: domain [10**]" → "[10**]"
fn _extract_trailing_grade(line: string) -> string {
    let t = line.trim()
    if !t.ends_with("]") { return "" }
    // 마지막 '[' 찾기 — 간단한 역방향 스캔
    let n: i64 = len(t)
    let mut i: i64 = n - 1
    while i >= 0 {
        if t[i..i+1] == "[" { return t[i..n] }
        i = i - 1
    }
    return ""
}

// OPT-P8-9: 라인별 grep -Fxq (N exec) → batched grep -Fxf (1 exec)
// 이전: N줄 × exec("grep -Fxq ...") = N subprocess. 대형 append 시 병목.
// 현재: 배치 패턴파일 → grep -Fxf 1회, hexa 메모리 0. (core blowup.hexa v3 동기화)
// X1 (2026-04-19): atlas-blowup 분리 — JSON 라인은 atlas.blowup.jsonl 로 라우팅.
//   호출자가 atlas.n6 path 를 넘겨도 라인 첫글자 `{` 면 사이드카로 분기.
//   _ATLAS_BLOWUP_PATH 글로벌 미정의 환경에서는 안전하게 본 경로로 폴백.
fn _guarded_append_atlas(path: string, content: string) -> i64 {
    if len(content) == 0 { return 0 }
    let is_atlas = path.contains("atlas.n6")
    // X1: JSON sidecar path — 호출자 측 _ATLAS_BLOWUP_PATH 글로벌 정의 시 자동 라우팅
    let mut json_route_path = ""
    try { if is_atlas { json_route_path = _ATLAS_BLOWUP_PATH } } catch e {}
    let lines = content.split("\n")
    let mut rejected: i64 = 0
    let mut deduped: i64 = 0

    // (1) schema 검증 — 유효 라인만 추출 + dedup 후보 수집
    let mut valid_lines = []
    let mut valid_trimmed = []
    let mut needs_dedup = []
    let mut is_json_line = []
    let mut i: i64 = 0
    while i < len(lines) {
        let line = lines[i]
        if !_valid_atlas_line(line) {
            rejected = rejected + 1
            i = i + 1
            continue
        }
        let t = line.trim()
        let do_dedup = is_atlas && len(t) > 0 && !t.starts_with("#")
        let mut is_json = false
        if is_atlas && len(t) > 0 {
            if t[0..1] == "{" { is_json = true }
        }
        valid_lines = valid_lines.push(line)
        valid_trimmed = valid_trimmed.push(t)
        needs_dedup = needs_dedup.push(do_dedup)
        is_json_line = is_json_line.push(is_json)
        i = i + 1
    }

    // (2) 배치 dedup: grep -Fxf tmpfile (exec 1회)
    let mut dup_set = #{}
    let dedup_count: i64 = len(valid_lines)
    let mut has_any_dedup = false
    i = 0
    while i < dedup_count {
        if needs_dedup[i] { has_any_dedup = true }
        i = i + 1
    }

    if has_any_dedup {
        let _tmp = "/tmp/.atlas_guard_dedup_batch." + to_string(exec("echo $$").trim())
        let mut patterns = []
        i = 0
        while i < dedup_count {
            if needs_dedup[i] {
                patterns = patterns.push(valid_trimmed[i])
            }
            i = i + 1
        }
        try {
            write_file(_tmp, "\n".join(patterns))
            // X1: 두 파일 모두 dedup 검사
            let mut grep_targets = "'" + path + "'"
            if len(json_route_path) > 0 && file_exists(json_route_path) {
                grep_targets = grep_targets + " '" + json_route_path + "'"
            }
            // AI-native: || true 제거 — grep no-match(exit 1) 는 try/catch 처리
            let mut found_raw = ""
            try { found_raw = exec("grep -hFxf '" + _tmp + "' " + grep_targets + " 2>/dev/null") } catch e {}
            let found_lines = found_raw.split("\n")
            for fl in found_lines {
                let ft = fl.trim()
                if len(ft) > 0 {
                    dup_set[ft] = true
                }
            }
        } catch e {}
        try { exec("rm -f '" + _tmp + "' 2>/dev/null") } catch e {}
    }

    // (3) 최종 필터 + X1 라우팅: 라벨 vs JSON 분리 buffer
    let mut clean_label_parts = []
    let mut clean_json_parts = []
    i = 0
    while i < dedup_count {
        if needs_dedup[i] {
            let t = valid_trimmed[i]
            let mut is_dup = false
            try { is_dup = dup_set[t] == true } catch e {}
            if is_dup {
                deduped = deduped + 1
                i = i + 1
                continue
            }
        }
        if is_json_line[i] && len(json_route_path) > 0 {
            clean_json_parts = clean_json_parts.push(valid_lines[i])
        } else {
            clean_label_parts = clean_label_parts.push(valid_lines[i])
        }
        i = i + 1
    }

    if rejected > 0 {
        println("  [schema guard] rejected " + to_string(rejected) + " invalid lines -> " + path)
    }
    if deduped > 0 {
        println("  [dedup guard] skipped " + to_string(deduped) + " duplicate lines -> " + path)
    }
    if len(clean_label_parts) > 0 {
        let mut clean = "\n".join(clean_label_parts)
        if !clean.ends_with("\n") { clean = clean + "\n" }
        try { append_file(path, clean) } catch e {}
    }
    if len(clean_json_parts) > 0 && len(json_route_path) > 0 {
        let mut clean_j = "\n".join(clean_json_parts)
        if !clean_j.ends_with("\n") { clean_j = clean_j + "\n" }
        try { append_file(json_route_path, clean_j) } catch e {}
    }
    return rejected
}

// ─── Intra-batch dedup helper (루프 내부용) ───
fn _batch_dedup_has(s: map, id: string) -> bool {
    let mut hit = false
    try { hit = has_key(s, id) } catch e {}
    return hit
}
