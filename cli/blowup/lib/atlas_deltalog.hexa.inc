// ═══════════════════════════════════════════════════════════
// atlas_deltalog.hexa.inc — atlas.n6 append-only delta-log + periodic compact
//
// 배경:
//   drill 이 atlas 에 entry 추가 시 이전 구현은 매 append 마다 1.5MB 본체
//   append_file() 호출. 수십만 drill 돌 때 flush/sync 비용 누적 → O(N²)
//   쓰기. delta-log 로 전환 — 모든 신규 line 은 atlas.n6.log 에만 쌓이고,
//   본체 atlas.n6 은 compact 시점에만 갱신된다.
//
// 설계:
//   atlas.n6        : 메인 (compact 된 SSOT, append 경로에서 touch 안 함)
//   atlas.n6.log    : append-only delta (한 줄 = atlas entry 한 줄)
//   atlas.n6.log.compacting  : compact 전이 로크 파일 (임시 atomic)
//
//   쓰기 경로: atlas.n6.log append (O(1) I/O, 중복 dedup 은 기존 가드가 수행)
//   읽기 경로: graph_load_with_log() — atlas.n6 + atlas.n6.log 를 merge
//   compact trigger:
//     (a) _deltalog_maybe_compact() — log 크기 > main * 0.25 → compact
//     (b) drill 세션 종료 시 — cli/run.hexa 에서 _deltalog_compact_force() 호출
//     (c) 수동 — scripts/atlas_compact.sh
//
// atomicity:
//   compact = read(main)+read(log) → LWW merge (동일 id 의 중복 entry 는
//   log 의 마지막 값 우선) → write_file(main.tmp) → rename(main.tmp, main) →
//   truncate(log, 0). rename 은 POSIX atomic.
//
// conflict:
//   AI/AJ agent 와 동일 atlas 터치 회피 → 이 include 는 delta-log 파일만
//   새로 추가하고, 메인은 compact 시점에만 rename 으로 갱신. 메인 write
//   중 read 는 원자적으로 이전 버전 보임.
//
// LWW semantics:
//   id 추출 (_atlas_extract_id) 가능한 라인만 LWW 적용, 그 외 (주석, 들여쓰기
//   부속, v2 continuation) 는 log 순서대로 append.
//
// hexa API:
//   append_file / read_file / write_file / file_exists / file_size — native.
// ═══════════════════════════════════════════════════════════

// 델타-로그 off 스위치 (환경변수). 0 또는 미설정 = on, 1 = bypass 직접 append.
fn _deltalog_enabled() -> bool {
    let mut v = ""
    try { v = env("NEXUS_ATLAS_DELTALOG") } catch e {}
    if v == "0" { return false }
    if v == "off" { return false }
    if v == "OFF" { return false }
    return true
}

// compact trigger ratio (log_size / main_size). 기본 0.25 (25%).
fn _deltalog_trigger_ratio() -> i64 {
    // 정수 percent 로 환경변수에서 읽음 (기본 25)
    let mut v = ""
    try { v = env("NEXUS_ATLAS_DELTALOG_PCT") } catch e {}
    if v == "" { return 25 }
    let mut n: i64 = 25
    try { n = to_int(v.trim()) } catch e {}
    if n < 1 { n = 25 }
    if n > 100 { n = 25 }
    return n
}

// atlas.n6 path 에 대응하는 delta-log path.
//   "/x/atlas.n6" → "/x/atlas.n6.log"
//   signals / blowup sidecar / events 는 deltalog 대상 아님.
fn _deltalog_path(atlas_path: string) -> string {
    // signals / blowup 사이드카는 제외 (별도 파일)
    if atlas_path.contains(".signals.n6") { return "" }
    if atlas_path.contains("atlas.blowup") { return "" }
    if atlas_path.contains("atlas.n6.events") { return "" }
    if atlas_path.contains("atlas.n6.log") { return "" }
    // atlas.n6 body 만 대상
    if !atlas_path.contains("atlas.n6") { return "" }
    return atlas_path + ".log"
}

// file size wrapper — 존재하지 않으면 0.
fn _deltalog_size(p: string) -> i64 {
    if !file_exists(p) { return 0 }
    let mut s: i64 = 0
    try { s = file_size(p) } catch e {}
    return s
}

// ─── append 경로 ────────────────────────────────────────────
// _guarded_append_atlas 가 schema / dedup 통과한 "깨끗한 버퍼" 를 넘길 때
// 본체 대신 delta-log 로 라우팅. 반환값 = 기록한 바이트 수 (0 = skip).
fn _deltalog_append(atlas_path: string, clean_buf: string) -> i64 {
    if len(clean_buf) == 0 { return 0 }
    let log_path = _deltalog_path(atlas_path)
    if log_path == "" { return 0 }  // deltalog 대상 아님
    // append_file 은 native — O(1) 쓰기.
    try { append_file(log_path, clean_buf) } catch e { return 0 }
    return len(clean_buf)
}

// compact 필요 여부.
//   log_size > main_size * pct / 100 → true
//   main 이 존재하지 않거나 비어있으면 false (compact 할 것 없음).
fn _deltalog_should_compact(atlas_path: string) -> bool {
    let log_path = _deltalog_path(atlas_path)
    if log_path == "" { return false }
    if !file_exists(log_path) { return false }
    let log_sz = _deltalog_size(log_path)
    if log_sz < 1 { return false }
    let main_sz = _deltalog_size(atlas_path)
    if main_sz < 1 { return true }  // main 이 비어있으면 log 만 있는 상태 → compact 추천
    let pct = _deltalog_trigger_ratio()
    // log_sz * 100 > main_sz * pct  (정수 안전 비교)
    if log_sz * 100 > main_sz * pct { return true }
    return false
}

// ─── id 추출 (LWW merge 용) ──────────────────────────────────
// atlas entry 포맷: "@<TYPE> <id> = <expr> :: <domain> [<grade>]"
// 또는 JSON: {"type":"node","id":"<id>",...}
// LWW 적용 대상이 아닌 라인 ("", "#...", 들여쓰기 부속) → "".
fn _deltalog_extract_id(line: string) -> string {
    let t = line.trim()
    if len(t) == 0 { return "" }
    if t.starts_with("#") { return "" }
    if t.starts_with("//") { return "" }
    // 들여쓰기 부속 (<-, ->, ==, !!, |>, "...)
    if t.starts_with("<-") { return "" }
    if t.starts_with("->") { return "" }
    if t.starts_with("==") { return "" }
    if t.starts_with("!!") { return "" }
    if t.starts_with("|>") { return "" }
    if t.starts_with("=>") { return "" }
    if t.starts_with("~>") { return "" }
    if t.starts_with("\"") { return "" }
    // v2 continuation (lhs= rhs= ...) — id 없음
    if t.contains("=") && !t.starts_with("@") && !t.starts_with("{") { return "" }
    // JSON line: "id":"..."
    if t.starts_with("{") {
        let marker = "\"id\":\""
        let idx = t.index_of(marker)
        if idx < 0 { return "" }
        let after = t.substring(idx + len(marker), len(t))
        let q = after.index_of("\"")
        if q < 0 { return "" }
        return after.substring(0, q)
    }
    // @-tag line: 첫 whitespace split
    if t.starts_with("@") {
        // "@X id = ..." — 첫 공백 → 태그 끝 / 두번째 공백 → id 끝
        let sp1 = t.index_of(" ")
        if sp1 < 0 { return "" }
        let rest = t.substring(sp1 + 1, len(t))
        // skip leading ws
        let mut start: i64 = 0
        while start < len(rest) {
            let c = rest.substring(start, start + 1)
            if c != " " && c != "\t" { break }
            start = start + 1
        }
        let mut end: i64 = start
        while end < len(rest) {
            let c = rest.substring(end, end + 1)
            if c == " " || c == "\t" || c == "=" { break }
            end = end + 1
        }
        if end == start { return "" }
        return rest.substring(start, end)
    }
    return ""
}

// ─── merge (LWW) ────────────────────────────────────────────
// main + log 을 읽어 병합된 문자열을 반환. id 있는 라인은 LWW (log 가 최신),
// id 없는 라인 (주석/들여쓰기/blank) 은 main 의 순서 유지 + log 의 그 다음
// 붙는 라인은 직전 id 의 부속 으로 간주해 "그 id 아래" 에 놓이게 한다.
//
// 단순 구현 (정확도 우선):
//   1) main lines 을 순회, 각 라인에 id 있으면 seen[id] = line. 부속은 이전 id 뒤에.
//   2) log lines 을 순회, id 있는 라인은 seen[id] 갱신 + 순서 리스트에 없으면 추가.
//   3) 최종 출력 = main 순서대로 id 블록을 재조립.
// 단, hexa interpreter 의 hashmap + list 퍼포먼스를 고려 — atlas 수 만 line
// 수준에서 동작해야 함 (atlas.n6 ≈ 30k line). LWW 범위는 log 쪽만 교체.
fn _deltalog_merge(main_path: string, log_path: string) -> string {
    let mut main_text = ""
    if file_exists(main_path) {
        try { main_text = read_file(main_path) } catch e {}
    }
    let mut log_text = ""
    if file_exists(log_path) {
        try { log_text = read_file(log_path) } catch e {}
    }
    if len(log_text) == 0 {
        return main_text
    }
    // 1) log 에서 id → last line 맵 수집 (중복 발생 시 마지막 승).
    //    id 없는 라인은 "append-tail" 리스트에 그대로 밀어넣어 끝에 붙인다.
    let log_lines = log_text.split("\n")
    let mut log_id_line = #{}    // id → last line with that id
    let mut log_id_order = []    // first-seen id 순서 (main 에 없는 신규 id append 용)
    let mut log_tail_attachments = #{}  // id → [attachment_lines]  (id 다음 들여쓰기 라인들)
    let mut log_pure_tail = []   // 어떤 id 에도 붙지 않는 꼬리 라인 (드물)
    let mut li: i64 = 0
    let mut cur_id = ""
    while li < len(log_lines) {
        let ln = log_lines[li]
        let id = _deltalog_extract_id(ln)
        if len(id) > 0 {
            // 새 id entry
            let mut first_time = false
            try { first_time = (log_id_line[id] == null) } catch e { first_time = true }
            // hexa 퍼스트타임 체크: has_key 없으면 추가
            let mut known = false
            try { if log_id_line[id] != null { known = true } } catch e {}
            if !known { log_id_order = log_id_order.push(id) }
            log_id_line[id] = ln
            // 기존 부속 리스트 초기화 (id 가 log 에서 다시 등장했으면 이전 부속은 버림)
            log_tail_attachments[id] = []
            cur_id = id
        } else {
            // 부속 — 현재 id 아래 첨부, cur_id 없으면 pure_tail
            let t = ln.trim()
            if len(t) == 0 {
                // 공백 라인은 부속/분리 모두 될 수 있음 — id 있는 바로 뒤에만 붙이고 그 외는 스킵
                if len(cur_id) > 0 {
                    let mut lst = []
                    try { lst = log_tail_attachments[cur_id] } catch e {}
                    lst = lst.push(ln)
                    log_tail_attachments[cur_id] = lst
                }
            } else if len(cur_id) > 0 {
                let mut lst = []
                try { lst = log_tail_attachments[cur_id] } catch e {}
                lst = lst.push(ln)
                log_tail_attachments[cur_id] = lst
            } else {
                log_pure_tail = log_pure_tail.push(ln)
            }
        }
        li = li + 1
    }

    // 2) main 을 순회하며 id 있는 라인 은 log 에 있으면 교체, 없으면 그대로.
    //    main 의 부속 (들여쓰기) 은 main 의 id 갱신 시 log 부속으로 교체.
    let main_lines = main_text.split("\n")
    let mut out_parts = []
    let mut replaced_ids = #{}
    let mut mi: i64 = 0
    let mlen = len(main_lines)
    while mi < mlen {
        let ln = main_lines[mi]
        let id = _deltalog_extract_id(ln)
        if len(id) > 0 {
            let mut has_log = false
            try { if log_id_line[id] != null { has_log = true } } catch e {}
            if has_log {
                // 교체 — main 의 부속 라인들을 스킵하고 log 의 라인+부속 삽입
                let new_ln = to_string(log_id_line[id])
                out_parts = out_parts.push(new_ln)
                let mut atts = []
                try { atts = log_tail_attachments[id] } catch e {}
                let mut ai: i64 = 0
                while ai < len(atts) {
                    out_parts = out_parts.push(to_string(atts[ai]))
                    ai = ai + 1
                }
                replaced_ids[id] = true
                // main 의 기존 부속 건너뛰기
                mi = mi + 1
                while mi < mlen {
                    let nxt = main_lines[mi]
                    let nxt_id = _deltalog_extract_id(nxt)
                    if len(nxt_id) > 0 { break }
                    let t = nxt.trim()
                    if len(t) == 0 { break }
                    // 들여쓰기 부속
                    mi = mi + 1
                }
                continue
            } else {
                out_parts = out_parts.push(ln)
            }
        } else {
            out_parts = out_parts.push(ln)
        }
        mi = mi + 1
    }

    // 3) log 의 신규 id (main 에 없던 것) 을 tail 로 append.
    let oi_n = len(log_id_order)
    let mut oi: i64 = 0
    while oi < oi_n {
        let id = to_string(log_id_order[oi])
        let mut done = false
        try { done = (replaced_ids[id] == true) } catch e {}
        if !done {
            let ln = to_string(log_id_line[id])
            out_parts = out_parts.push(ln)
            let mut atts = []
            try { atts = log_tail_attachments[id] } catch e {}
            let mut ai: i64 = 0
            while ai < len(atts) {
                out_parts = out_parts.push(to_string(atts[ai]))
                ai = ai + 1
            }
        }
        oi = oi + 1
    }
    // 4) pure tail (드물)
    let mut pi: i64 = 0
    while pi < len(log_pure_tail) {
        out_parts = out_parts.push(to_string(log_pure_tail[pi]))
        pi = pi + 1
    }

    let merged = out_parts.join("\n")
    return merged
}

// ─── compact ────────────────────────────────────────────────
// atomicity: merge → write tmp → rename → truncate log.
// 반환값 = 새 main 크기 (bytes), 실패 시 -1.
fn _deltalog_compact(atlas_path: string) -> i64 {
    let log_path = _deltalog_path(atlas_path)
    if log_path == "" { return -1 }
    if !file_exists(log_path) { return 0 }  // 할 일 없음
    let log_sz = _deltalog_size(log_path)
    if log_sz < 1 { return 0 }
    // 이미 다른 프로세스가 compact 중인지 체크 — compacting 락 파일 존재 여부.
    let lock_path = log_path + ".compacting"
    if file_exists(lock_path) {
        // 안전 위해 skip — 다음 trigger 때 재시도.
        return -1
    }
    // 락 생성 (best-effort, flock 은 hexa 에서 직접 불가 → 파일 존재 기반 advisory)
    try { write_file(lock_path, to_string(now())) } catch e {}
    let merged = _deltalog_merge(atlas_path, log_path)
    let tmp_path = atlas_path + ".compact.tmp"
    let mut ok = false
    try { write_file(tmp_path, merged); ok = true } catch e {}
    if !ok {
        try { exec("rm -f '" + lock_path + "' 2>/dev/null") } catch e {}
        return -1
    }
    // atomic rename
    let rename_cmd = "mv -f '" + tmp_path + "' '" + atlas_path + "'"
    let mut r_ok = false
    try { exec(rename_cmd); r_ok = true } catch e {}
    if !r_ok {
        try { exec("rm -f '" + tmp_path + "' '" + lock_path + "' 2>/dev/null") } catch e {}
        return -1
    }
    // truncate log (새 파일로 덮어씀 — 0 byte)
    try { write_file(log_path, "") } catch e {}
    // lock 제거
    try { exec("rm -f '" + lock_path + "' 2>/dev/null") } catch e {}
    // bucket index 재빌드 (best-effort)
    let nexus_root_dir = _HOME + "/core/nexus"
    let scan_opt = nexus_root_dir + "/n6/atlas_scan_opt.hexa"
    if file_exists(scan_opt) {
        try { exec(_HEXA_BIN + " '" + scan_opt + "' build >/dev/null 2>&1") } catch e {}
    }
    return _deltalog_size(atlas_path)
}

// ─── 자동 트리거 (append 경로에서 호출) ───────────────────────
// append 직후 _deltalog_should_compact() 참이면 compact 수행.
// drill 루프 안에서 너무 자주 돌지 않도록 trigger_ratio 로 방어.
fn _deltalog_maybe_compact(atlas_path: string) -> i64 {
    if !_deltalog_enabled() { return 0 }
    if !_deltalog_should_compact(atlas_path) { return 0 }
    return _deltalog_compact(atlas_path)
}

// ─── 강제 compact (drill 세션 종료 / 수동 호출) ────────────────
fn _deltalog_compact_force(atlas_path: string) -> i64 {
    if !_deltalog_enabled() { return 0 }
    let log_path = _deltalog_path(atlas_path)
    if log_path == "" { return 0 }
    if !file_exists(log_path) { return 0 }
    if _deltalog_size(log_path) < 1 { return 0 }
    return _deltalog_compact(atlas_path)
}

// ─── 읽기 경로 wrapper (graph_load_with_log) ──────────────────
// blowup/atlas_health 등에서 atlas.n6 내용을 "현재 상태" 로 보려면
// main+log 을 merge 해서 돌려준다. 본 시점 compact 안 하고 memory 에서만.
fn _deltalog_read_merged(atlas_path: string) -> string {
    if !_deltalog_enabled() {
        if file_exists(atlas_path) {
            let mut r = ""
            try { r = read_file(atlas_path) } catch e {}
            return r
        }
        return ""
    }
    let log_path = _deltalog_path(atlas_path)
    if log_path == "" || !file_exists(log_path) {
        let mut r = ""
        if file_exists(atlas_path) {
            try { r = read_file(atlas_path) } catch e {}
        }
        return r
    }
    return _deltalog_merge(atlas_path, log_path)
}
