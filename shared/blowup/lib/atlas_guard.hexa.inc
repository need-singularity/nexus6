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
    let first = t[0..1]
    if first == "#" { return true }
    if first == "{" { return true }
    if first == "@" { return true }
    if first == "\"" { return true }
    if first == "<" { return true }
    if first == ">" { return true }
    if first == "!" { return true }
    if first == "-" { return true }
    return false
}

// append_file 전 (1) schema 검증 (2) 기존 라인 dedup (3) append.
// atlas.n6 대상: 기존 파일 읽어서 라인셋 빌드 → 중복 원천 차단.
// inter-process dedup — concurrent blowup 30+ 실행 시 중복 방지.
fn _guarded_append_atlas(path: string, content: string) -> i64 {
    if len(content) == 0 { return 0 }

    // (1) 기존 파일 라인셋 로드 (dedup용)
    let mut existing = #{}
    let is_atlas = path.contains("atlas.n6")
    if is_atlas {
        try {
            let cur = read_file(path)
            let cur_lines = cur.split("\n")
            let mut ei: i64 = 0
            while ei < len(cur_lines) {
                let el = cur_lines[ei].trim()
                if len(el) > 0 {
                    existing[el] = true
                }
                ei = ei + 1
            }
        } catch e {}
    }

    // (2) schema 검증 + dedup 필터링
    let lines = content.split("\n")
    let mut clean = ""
    let mut rejected: i64 = 0
    let mut deduped: i64 = 0
    let mut first = true
    let mut i: i64 = 0
    while i < len(lines) {
        let line = lines[i]
        if !_valid_atlas_line(line) {
            rejected = rejected + 1
            i = i + 1
            continue
        }
        let t = line.trim()
        if is_atlas && len(t) > 0 && !t.starts_with("#") {
            let mut already = false
            try { already = has_key(existing, t) } catch e {}
            if already {
                deduped = deduped + 1
                i = i + 1
                continue
            }
            existing[t] = true
        }
        if !first { clean = clean + "\n" }
        clean = clean + line
        first = false
        i = i + 1
    }
    if rejected > 0 {
        println("  [schema guard] rejected " + to_string(rejected) + " invalid lines -> " + path)
    }
    if deduped > 0 {
        println("  [dedup guard] skipped " + to_string(deduped) + " duplicate lines -> " + path)
    }
    if len(clean) > 0 {
        if !clean.ends_with("\n") { clean = clean + "\n" }
        try { append_file(path, clean) } catch e {}
    }
    return rejected
}

// ─── Intra-batch dedup helper (루프 내부용) ───
fn _batch_dedup_has(s: map, id: string) -> bool {
    let mut hit = false
    try { hit = has_key(s, id) } catch e {}
    return hit
}
