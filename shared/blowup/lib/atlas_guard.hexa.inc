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

// OPT-P8-9: 라인별 grep -Fxq (N exec) → batched grep -Fxf (1 exec)
// 이전: N줄 × exec("grep -Fxq ...") = N subprocess. 대형 append 시 병목.
// 현재: 배치 패턴파일 → grep -Fxf 1회, hexa 메모리 0. (core blowup.hexa v3 동기화)
fn _guarded_append_atlas(path: string, content: string) -> i64 {
    if len(content) == 0 { return 0 }
    let is_atlas = path.contains("atlas.n6")
    let lines = content.split("\n")
    let mut rejected: i64 = 0
    let mut deduped: i64 = 0

    // (1) schema 검증 — 유효 라인만 추출 + dedup 후보 수집
    let mut valid_lines = []
    let mut valid_trimmed = []
    let mut needs_dedup = []
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
        valid_lines = valid_lines.push(line)
        valid_trimmed = valid_trimmed.push(t)
        needs_dedup = needs_dedup.push(do_dedup)
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
            let found_raw = exec("grep -Fxf '" + _tmp + "' '" + path + "' 2>/dev/null || true")
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

    // (3) 최종 필터: dup_set에 있으면 dedup
    let mut clean_parts = []
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
        clean_parts = clean_parts.push(valid_lines[i])
        i = i + 1
    }

    if rejected > 0 {
        println("  [schema guard] rejected " + to_string(rejected) + " invalid lines -> " + path)
    }
    if deduped > 0 {
        println("  [dedup guard] skipped " + to_string(deduped) + " duplicate lines -> " + path)
    }
    if len(clean_parts) > 0 {
        let mut clean = "\n".join(clean_parts)
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
