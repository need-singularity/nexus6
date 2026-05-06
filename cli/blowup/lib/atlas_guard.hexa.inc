// ═══════════════════════════════════════════════════════════
// AI-native atlas 가드 헬퍼 (core/blowup.hexa에서 발췌)
// 사용: 이 섹션을 모듈 파일 상단(exec/read_file 도입 전)에 copy-paste.
// 창발 보존: 아래 함수들은 append-path에 필터 + dedup만 추가하며
// phase 로직/discovery 계산/seed 진화 등 반환 값에 영향 없음.
// ═══════════════════════════════════════════════════════════

// ─── Schema guard: atlas.n6 라인 포맷 검증 ───
// 유효: 빈줄/# 주석/{"type":/@X ... [grade]/들여쓰기 부속("<-!!->)
// v2 (2026-04-19): @EXP/@OBS/@NEG/@ANT 태그 + 그 continuation 필드 (lhs=/rhs=/if_true=/test=...)
fn _valid_atlas_line(line: string) -> bool {
    let t = line.trim()
    if len(t) == 0 { return true }
    // OPT-P8-9: 8 if-chain → single .contains() (core blowup.hexa 동기화)
    let allowed = "#{@\"<>!-"
    if allowed.contains(t[0..1]) { return true }
    // v2 continuation: indented key=value rows (lhs=/rhs=/delta=/z=/witness=/
    // note=/if_true=/if_false=/test=/deadline=) — 원본 line (trim 전) 에 leading ws 필수
    if len(line) > 0 && (line[0..1] == " " || line[0..1] == "\t") {
        if _is_v2_continuation_key(t) { return true }
    }
    return false
}

// v2 continuation row 감지 — `<key>=...` or `<key> = ...` 형태 + 허용 key whitelist.
fn _is_v2_continuation_key(t: string) -> bool {
    // axis-M (2026-05-06): unit + external-anchor primitives — see
    // atlas.append.atlas-self-arch-axis-m-unit-anchor-2026-05-06.n6 §2/§7
    // K_core 22 → 24 (ceiling 30, headroom 6 for axis-N+)
    let keys = ["lhs", "rhs", "delta", "z", "witness", "note", "if_true", "if_false", "test", "deadline", "cite", "vintage", "uncertainty", "status", "risks", "contrast", "source", "frame", "scale", "unit", "anchor"]
    for k in keys {
        if t.starts_with(k + "=") { return true }
        if t.starts_with(k + " =") { return true }
        if t.starts_with(k + "  =") { return true }
    }
    return false
}

// ─── Schema v2 tag parser (field-level validation) ───
// v2 tags: @EXP (external witness) / @OBS (observer frame) / @NEG (negation) / @ANT (antithesis)
// 공통 포맷: @TAG id = expr :: domain [grade] @@ key=val key=val ...
// 검증:
//   (1) tag prefix ∈ {@EXP,@OBS,@NEG,@ANT}
//   (2) id = [A-Za-z0-9_]+ (첫 char alpha, 뒤 alnum/_)
//   (3) `::` domain 섹션 존재
//   (4) trailing grade `[...]` 있으면 _known_atlas_grade 통과
//   (5) `@@` 메타 섹션 + 태그별 필수 필드:
//        @EXP: source=
//        @OBS: frame= (scale= 권장)
//        @NEG: contrast= (n= 권장)
//        @ANT: risks= status=
fn _is_v2_tag_line(line: string) -> bool {
    let t = line.trim()
    if len(t) < 5 { return false }
    if t.starts_with("@EXP ") { return true }
    if t.starts_with("@OBS ") { return true }
    if t.starts_with("@NEG ") { return true }
    if t.starts_with("@ANT ") { return true }
    return false
}

fn _extract_v2_tag(line: string) -> string {
    let t = line.trim()
    if t.starts_with("@EXP ") { return "@EXP" }
    if t.starts_with("@OBS ") { return "@OBS" }
    if t.starts_with("@NEG ") { return "@NEG" }
    if t.starts_with("@ANT ") { return "@ANT" }
    return ""
}

// hexa pitfall: 문자열 >=/<= 비교 미지원 → char_code 사용.
fn _is_alnum_id_char(s: string, i: i64) -> bool {
    if i < 0 || i >= len(s) { return false }
    let code = char_code(s, i)
    if code >= 65 && code <= 90 { return true }   // A-Z
    if code >= 97 && code <= 122 { return true }  // a-z
    if code >= 48 && code <= 57 { return true }   // 0-9
    if code == 95 { return true }                  // _
    return false
}

fn _is_alpha_or_under(s: string, i: i64) -> bool {
    if i < 0 || i >= len(s) { return false }
    let code = char_code(s, i)
    if code >= 65 && code <= 90 { return true }
    if code >= 97 && code <= 122 { return true }
    if code == 95 { return true }
    return false
}

// v2 id 추출: `@TAG ID = ...` 에서 ID 부분. 유효하지 않으면 "".
fn _extract_v2_id(line: string) -> string {
    let t = line.trim()
    // @TAG 뒤 공백, 그 뒤 id
    let sp = t.index_of(" ")
    if sp < 0 { return "" }
    // skip leading spaces manually (no trim_start dep)
    let mut start: i64 = sp + 1
    while start < len(t) {
        let c = t.substring(start, start + 1)
        if c != " " && c != "\t" { break }
        start = start + 1
    }
    // id 끝: 첫 ' ' or '=' or '\t'
    let mut end: i64 = start
    while end < len(t) {
        let c = t.substring(end, end + 1)
        if c == " " || c == "=" || c == "\t" { break }
        end = end + 1
    }
    if end == start { return "" }
    let id = t.substring(start, end)
    if len(id) == 0 { return "" }
    // id validation: 첫 char alpha/underscore, 나머지 alnum/_
    if !_is_alpha_or_under(id, 0) { return "" }
    let mut i: i64 = 1
    while i < len(id) {
        if !_is_alnum_id_char(id, i) { return "" }
        i = i + 1
    }
    return id
}

// v2 태그별 필수 `@@ key=` 필드 검증.
fn _valid_v2_meta_fields(line: string, tag: string) -> bool {
    let t = line.trim()
    let at_idx = t.index_of("@@")
    if at_idx < 0 { return false }
    let meta = t.substring(at_idx + 2, len(t))
    if tag == "@EXP" {
        if meta.contains("source=") { return true }
        return false
    }
    if tag == "@OBS" {
        if meta.contains("frame=") { return true }
        return false
    }
    if tag == "@NEG" {
        if meta.contains("contrast=") { return true }
        return false
    }
    if tag == "@ANT" {
        if meta.contains("risks=") && meta.contains("status=") { return true }
        return false
    }
    return false
}

// 종합 v2 line 검증: 헤더 line 전체. continuation 은 _valid_atlas_line 에서 별도 처리.
fn _valid_v2_line(line: string) -> bool {
    if !_is_v2_tag_line(line) { return false }
    let tag = _extract_v2_tag(line)
    let id = _extract_v2_id(line)
    if len(id) == 0 { return false }
    let t = line.trim()
    // `::` domain required
    if !t.contains(" :: ") && !t.contains("::") { return false }
    // trailing grade optional, if present validate
    let g = _extract_trailing_grade(t)
    if len(g) > 0 && !_known_atlas_grade(g) {
        // v2 also accepts [N!] / [10*!] style which _known_atlas_grade already covers,
        // 및 draft 샘플 [7?] = conjecture-class → _known_atlas_grade 미포함 → accept
        if g != "[7?]" && g != "[10*!]" && g != "[4?]" { return false }
    }
    // required meta fields per tag
    return _valid_v2_meta_fields(line, tag)
}

// ─── Staging-only gate: v2 태그는 atlas.signals.n6 에만 기록 허용 ───
// atlas.n6 body 에 v2 태그 append 시도하면 reject (DRAFT §4, §9 non-goal).
fn _is_signals_path(path: string) -> bool {
    return path.contains("atlas.signals.n6") || path.contains(".signals.n6") || path.contains("atlas.signals.staging")
}

fn _is_atlas_body_path(path: string) -> bool {
    if _is_signals_path(path) { return false }
    return path.contains("atlas.n6")
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
    let is_signals = _is_signals_path(path)
    let is_body = _is_atlas_body_path(path)
    // X1: JSON sidecar path — 호출자 측 _ATLAS_BLOWUP_PATH 글로벌 정의 시 자동 라우팅
    let mut json_route_path = ""
    try { if is_atlas && !is_signals { json_route_path = _ATLAS_BLOWUP_PATH } } catch e {}
    let lines = content.split("\n")
    let mut rejected: i64 = 0
    let mut deduped: i64 = 0
    let mut v2_body_rejected: i64 = 0

    // (1) schema 검증 — 유효 라인만 추출 + dedup 후보 수집
    let mut valid_lines = []
    let mut valid_trimmed = []
    let mut needs_dedup = []
    let mut is_json_line = []
    let mut i: i64 = 0
    while i < len(lines) {
        let line = lines[i]
        // v2 tag staging gate: atlas.n6 body 에 v2 태그 append 차단 (DRAFT §4, §9)
        if _is_v2_tag_line(line) {
            if is_body && !is_signals {
                v2_body_rejected = v2_body_rejected + 1
                rejected = rejected + 1
                i = i + 1
                continue
            }
            // v2 field-level 검증 (signals path 허용)
            if !_valid_v2_line(line) {
                rejected = rejected + 1
                i = i + 1
                continue
            }
        }
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
    if v2_body_rejected > 0 {
        println("  [schema v2 guard] " + to_string(v2_body_rejected) + " v2 tags blocked from atlas.n6 body (staging: atlas.signals.n6)")
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
