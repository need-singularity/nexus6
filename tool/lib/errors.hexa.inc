// ═══════════════════════════════════════════════════════════
// errors.hexa.inc — 오류 큐 helper (H-ERR-ROUTE / DRAIN / PROMOTE)
// 사용: atlas_guard.hexa.inc 패턴 — 소비자 .hexa 상단에 이 파일 내용을
//       copy-paste (hexa 는 native include 미지원).
//       미래 include 빌트인 추가 시 `include "lib/errors.hexa.inc"` 로 전환.
// 스키마 1행:
//   {"ts":"2026-04-14T10:30:00Z","project":"nexus","severity":"defer",
//    "source":"lint","file":"shared/tool/x.hexa","line":42,
//    "code":"L0","msg":"L0 보호 영역 수정","attempts":0,
//    "status":"open","key":"hash8"}
// SSOT: shared/tool/errors.jsonl
// 규약: 성공 조용, 실패 stderr (linter/entry 패턴과 일치).
// hexa pitfalls 방어: _str(void) coercion, _rfind, _to_int0, try/catch exec.
// ═══════════════════════════════════════════════════════════

let _ERR_HOME = env("HOME")
let _ERR_NEXUS = _ERR_HOME + "/Dev/nexus"
let _ERR_QUEUE = _ERR_NEXUS + "/tool/errors.jsonl"

// ─── void-safe string coercion (split 결과/exec 결과 void 방어) ───
fn _err_str(x) -> string {
    let t = type_of(x)
    if t == "str" || t == "string" { return x }
    return ""
}

// ─── 첫 줄 기반 int 파싱 (grep -c || echo 0 이중출력 방어, R33) ───
fn _err_to_int0(s: string) -> i64 {
    if s == "" { return 0 }
    let first = _err_str(s.split("\n")[0]).trim()
    if first == "" { return 0 }
    return to_int(first)
}

// ─── last_index_of 미구현 우회 (역방향 스캔) ───
fn _err_rfind(s: string, ch: string) -> i64 {
    let n = len(s)
    let mut i: i64 = n - 1
    while i >= 0 {
        if s.substring(i, i + 1) == ch { return i }
        i = i - 1
    }
    return -1
}

// ─── JSON 이스케이프 ───
fn _err_json_escape(s: string) -> string {
    let mut r = s
    r = r.replace("\\", "\\\\")
    r = r.replace("\"", "\\\"")
    r = r.replace("\n", "\\n")
    r = r.replace("\r", "\\r")
    r = r.replace("\t", "\\t")
    return r
}

// ─── shell single-quote 이스케이프 ───
fn _err_shq(s: string) -> string {
    return s.replace("'", "'\\''")
}

// ─── ISO8601 UTC ts ───
fn _err_now_iso() -> string {
    return _err_str(exec("date -u +%Y-%m-%dT%H:%M:%SZ")).trim()
}

// ─── unix ts (초) ───
fn _err_now_unix() -> i64 {
    return _err_to_int0(_err_str(exec("date +%s")).trim())
}

// ─── project basename (cwd 기준, R14 원칙) ───
fn _err_project() -> string {
    let bn = _err_str(exec("basename \"$(pwd)\" 2>/dev/null")).trim()
    if bn == "" { return "unknown" }
    return bn
}

// ─── dedup key — file+code+line 단순 hash (sha256 빌트인 없음, 시스템콜 회피) ───
// 8자리 16진수 — ASCII 표 기반 char code 합산 + FNV-lite. 시스템콜 0.
// 충돌 위험 낮음 (H-ERR dedup 범위: 동일 file+code+line 탐지 목적만).
let _ERR_ASCII = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

fn _err_char_code(ch: string) -> i64 {
    // 공백(32) ~ ~(126) 범위. 그 외 문자는 길이 기반 fallback.
    let idx = _ERR_ASCII.index_of(ch)
    if idx >= 0 { return idx + 32 }
    return 63  // '?' fallback
}

fn _err_hash_key(file: string, code: string, line: i64) -> string {
    let raw = file + "|" + code + "|" + to_string(line)
    let mut h: i64 = 2166136261
    let mut i: i64 = 0
    let n = len(raw)
    while i < n {
        let ch = raw.substring(i, i + 1)
        let c = _err_char_code(ch)
        h = (h * 16777619) + c
        // 32bit mask
        h = h % 4294967296
        if h < 0 { h = h + 4294967296 }
        i = i + 1
    }
    // 8-hex 포맷
    let hex_chars = "0123456789abcdef"
    let mut out = ""
    let mut k: i64 = 7
    while k >= 0 {
        let nib = (h / _err_pow16(k)) % 16
        out = out + hex_chars.substring(nib, nib + 1)
        k = k - 1
    }
    return out
}

// 16^k (k<=7) — pow 빌트인 의존 제거
fn _err_pow16(k: i64) -> i64 {
    let mut r: i64 = 1
    let mut i: i64 = 0
    while i < k {
        r = r * 16
        i = i + 1
    }
    return r
}

// ─── 큐 파일 touch (없으면 생성) ───
fn _err_ensure_queue() {
    if !file_exists(_ERR_QUEUE) {
        try { write_file(_ERR_QUEUE, "") } catch e {}
    }
}

// ─── 큐 전체 라인 로드 (없거나 빈 파일이면 빈 배열) ───
fn _err_load_lines() -> [string] {
    _err_ensure_queue()
    let raw = read_file(_ERR_QUEUE)
    if len(raw) == 0 { return [] }
    let parts = raw.split("\n")
    let mut out: [string] = []
    let mut i: i64 = 0
    while i < len(parts) {
        let p = _err_str(parts[i])
        if len(p.trim()) > 0 { out = out.push(p) }
        i = i + 1
    }
    return out
}

// ─── 라인에서 "key":"xxx" 추출 (regex 없이 문자열 스캔) ───
fn _err_extract_field(line: string, field: string) -> string {
    let needle = "\"" + field + "\":"
    let idx = line.index_of(needle)
    if idx < 0 { return "" }
    let rest = line.substring(idx + len(needle), len(line))
    // string 값
    if rest.starts_with("\"") {
        let after = rest.substring(1, len(rest))
        let end = after.index_of("\"")
        if end < 0 { return "" }
        return after.substring(0, end)
    }
    // 숫자 값 — 다음 `,` 또는 `}` 까지
    let comma = rest.index_of(",")
    let brace = rest.index_of("}")
    let mut cut: i64 = len(rest)
    if comma >= 0 && comma < cut { cut = comma }
    if brace >= 0 && brace < cut { cut = brace }
    return rest.substring(0, cut).trim()
}

// ─── 전체 큐 덮어쓰기 ───
fn _err_rewrite(lines: [string]) {
    let mut buf = ""
    let mut i: i64 = 0
    while i < len(lines) {
        buf = buf + _err_str(lines[i]) + "\n"
        i = i + 1
    }
    try { write_file(_ERR_QUEUE, buf) } catch e {}
}

// ─── 한 줄 append (hexa 빌트인 append_file — 쉘 인용 회피) ───
fn _err_append_line(json_line: string) {
    _err_ensure_queue()
    try { append_file(_ERR_QUEUE, json_line + "\n") } catch e {}
}

// ═══════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════

// errors_append — 중복(open) 있으면 attempts+=1, 없으면 새 행
fn errors_append(project: string, severity: string, source: string,
                 file: string, line: i64, code: string, msg: string) -> string {
    let key = _err_hash_key(file, code, line)
    let lines = _err_load_lines()
    let mut found_idx: i64 = -1
    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        let k = _err_extract_field(ln, "key")
        let st = _err_extract_field(ln, "status")
        if k == key && st == "open" { found_idx = i; break }
        i = i + 1
    }

    if found_idx >= 0 {
        // attempts+=1 로 라인 교체 (list[i]=v no-op 방어 → 재구축)
        let old = _err_str(lines[found_idx])
        let prev_attempts = _err_to_int0(_err_extract_field(old, "attempts"))
        let new_attempts = prev_attempts + 1
        // naive replace: "attempts":N
        let mut updated = old
        let pat = "\"attempts\":" + to_string(prev_attempts)
        let rep = "\"attempts\":" + to_string(new_attempts)
        updated = updated.replace(pat, rep)
        let mut new_lines: [string] = []
        let mut j: i64 = 0
        while j < len(lines) {
            if j == found_idx { new_lines = new_lines.push(updated) }
            else { new_lines = new_lines.push(_err_str(lines[j])) }
            j = j + 1
        }
        _err_rewrite(new_lines)
        return key
    }

    // 새 행 build
    let ts = _err_now_iso()
    let proj = if project == "" { _err_project() } else { project }
    let json = "{\"ts\":\"" + ts + "\"," +
               "\"project\":\"" + _err_json_escape(proj) + "\"," +
               "\"severity\":\"" + _err_json_escape(severity) + "\"," +
               "\"source\":\"" + _err_json_escape(source) + "\"," +
               "\"file\":\"" + _err_json_escape(file) + "\"," +
               "\"line\":" + to_string(line) + "," +
               "\"code\":\"" + _err_json_escape(code) + "\"," +
               "\"msg\":\"" + _err_json_escape(msg) + "\"," +
               "\"attempts\":0," +
               "\"status\":\"open\"," +
               "\"key\":\"" + key + "\"}"
    _err_append_line(json)
    return key
}

// errors_count_open — status=open 행 수
fn errors_count_open() -> i64 {
    let lines = _err_load_lines()
    let mut c: i64 = 0
    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        if _err_extract_field(ln, "status") == "open" { c = c + 1 }
        i = i + 1
    }
    return c
}

// errors_count_by_code — code 일치 + open 수
fn errors_count_by_code(code: string) -> i64 {
    let lines = _err_load_lines()
    let mut c: i64 = 0
    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        if _err_extract_field(ln, "code") == code &&
           _err_extract_field(ln, "status") == "open" { c = c + 1 }
        i = i + 1
    }
    return c
}

// errors_mark_fixed — 해당 key open→fixed
fn errors_mark_fixed(key: string) -> i64 {
    let lines = _err_load_lines()
    let mut changed: i64 = 0
    let mut new_lines: [string] = []
    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        let k = _err_extract_field(ln, "key")
        let st = _err_extract_field(ln, "status")
        if k == key && st == "open" {
            let updated = ln.replace("\"status\":\"open\"", "\"status\":\"fixed\"")
            new_lines = new_lines.push(updated)
            changed = changed + 1
        } else {
            new_lines = new_lines.push(ln)
        }
        i = i + 1
    }
    if changed > 0 { _err_rewrite(new_lines) }
    return changed
}

// errors_mark_stale_old — 24h 이상 미터치 open → stale
fn errors_mark_stale_old() -> i64 {
    let lines = _err_load_lines()
    let now = _err_now_unix()
    let cutoff = now - 86400
    let mut changed: i64 = 0
    let mut new_lines: [string] = []
    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        let st = _err_extract_field(ln, "status")
        if st != "open" { new_lines = new_lines.push(ln); i = i + 1; continue }
        let ts = _err_extract_field(ln, "ts")
        // ts → unix 변환 via date -d
        let ts_unix = _err_to_int0(_err_str(exec(
            "date -u -j -f '%Y-%m-%dT%H:%M:%SZ' '" + _err_shq(ts) +
            "' +%s 2>/dev/null || date -u -d '" + _err_shq(ts) +
            "' +%s 2>/dev/null || echo 0"
        )).trim())
        if ts_unix > 0 && ts_unix < cutoff {
            let updated = ln.replace("\"status\":\"open\"", "\"status\":\"stale\"")
            new_lines = new_lines.push(updated)
            changed = changed + 1
        } else {
            new_lines = new_lines.push(ln)
        }
        i = i + 1
    }
    if changed > 0 { _err_rewrite(new_lines) }
    return changed
}

// errors_drain_required — open 수 >= threshold 면 true
fn errors_drain_required(threshold: i64) -> bool {
    return errors_count_open() >= threshold
}

// errors_promote_candidates — 같은 (file, code) 의 총 발생(attempts+1 합계)이
// min_recurrence 이상인 대표 key 목록 (mistakes.jsonl 승격 후보).
// 주의: dedup 으로 1 row 에 attempts 가 쌓이므로 row 수가 아닌 occurrences 합산.
fn errors_promote_candidates(min_recurrence: i64) -> [string] {
    let lines = _err_load_lines()
    // parallel list: (file|code) → occurrences 합계, 대표 key
    let mut fc_keys: [string] = []
    let mut fc_occur: [i64] = []
    let mut fc_repr: [string] = []

    let mut i: i64 = 0
    while i < len(lines) {
        let ln = _err_str(lines[i])
        let f = _err_extract_field(ln, "file")
        let c = _err_extract_field(ln, "code")
        let k = _err_extract_field(ln, "key")
        let attempts = _err_to_int0(_err_extract_field(ln, "attempts"))
        let occ = attempts + 1  // attempts 0 = 1회 발생
        let fc = f + "|" + c

        let mut idx: i64 = -1
        let mut j: i64 = 0
        while j < len(fc_keys) {
            if _err_str(fc_keys[j]) == fc { idx = j; break }
            j = j + 1
        }
        if idx < 0 {
            fc_keys = fc_keys.push(fc)
            fc_occur = fc_occur.push(occ)
            fc_repr = fc_repr.push(k)
        } else {
            // occur[idx] += occ (list index no-op 방어 → 재구축)
            let mut new_occ: [i64] = []
            let mut m: i64 = 0
            while m < len(fc_occur) {
                if m == idx { new_occ = new_occ.push(fc_occur[m] + occ) }
                else { new_occ = new_occ.push(fc_occur[m]) }
                m = m + 1
            }
            fc_occur = new_occ
        }
        i = i + 1
    }

    let mut out: [string] = []
    let mut p: i64 = 0
    while p < len(fc_keys) {
        if fc_occur[p] >= min_recurrence {
            out = out.push(_err_str(fc_repr[p]))
        }
        p = p + 1
    }
    return out
}
