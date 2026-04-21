// ═══════════════════════════════════════════════════════════
// lib/safe_exec.hexa.inc — H-NOZOMBIE helper (Phase 2)
// 외부 명령 timeout 강제 호출 헬퍼. exec(...) 직접 호출 대신 사용.
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste
//       (hexa stage1 native include 미지원).
//
// usage:
//   let out = safe_exec("ls /tmp", 30)              // 30s timeout
//   let out = safe_exec_str("date +%s", 5)          // 결과 trim() 까지
//   let rc_out = safe_exec_with_rc("test -f x", 5)  // [rc, body]
//
// 우회: NEXUS_NO_TIMEOUT=1 env (perl_timeout.sh 가 처리)
// 부재 시 graceful degrade — wrapper 없으면 exec 그대로.
// hexa pitfalls 방어: _str(void), len(x) 글로벌, 리스트 push rebuild.
// ═══════════════════════════════════════════════════════════

let _SE_HOME = env("HOME")
let _SE_WRAPPER = _SE_HOME + "/Dev/nexus/shared/harness/perl_timeout.sh"

// ─── void-safe string coercion (split/exec 결과 방어) ───
fn _se_str(x) -> string {
    let t = type_of(x)
    if t == "str" || t == "string" { return x }
    return ""
}

// ─── shell single-quote 이스케이프 ───
fn _se_shq(s: string) -> string {
    return "'" + s.replace("'", "'\\''") + "'"
}

// ─── wrapper 존재 여부 (부재 시 degrade) ───
fn _se_wrapper_ok() -> bool {
    let r = _se_str(exec("test -x '" + _SE_WRAPPER + "' && echo y || echo n")).trim()
    return r == "y"
}

// ─── 명령을 perl_timeout.sh 로 래핑 ───
fn _se_wrap(cmd: string, timeout_sec: i64) -> string {
    if !_se_wrapper_ok() {
        return cmd
    }
    // perl_timeout.sh <seconds> bash -c '<cmd>'
    return "'" + _SE_WRAPPER + "' " + to_string(timeout_sec) + " bash -c " + _se_shq(cmd)
}

// ─── main API: safe_exec — stdout+stderr 합침 ───
fn safe_exec(cmd: string, timeout_sec: i64) -> string {
    let wrapped = _se_wrap(cmd, timeout_sec)
    return _se_str(exec(wrapped + " 2>&1"))
}

// ─── trim 된 결과 ───
fn safe_exec_str(cmd: string, timeout_sec: i64) -> string {
    return safe_exec(cmd, timeout_sec).trim()
}

// ─── stderr 버림 (stdout 만) ───
fn safe_exec_silent(cmd: string, timeout_sec: i64) -> string {
    let wrapped = _se_wrap(cmd, timeout_sec)
    return _se_str(exec(wrapped + " 2>/dev/null"))
}

// ─── rc + body 둘 다 반환 ([rc_str, body_str]) ───
// hexa stage1 tuple 미지원 → 2-elem 배열.
// bash echo $? sentinel 로 exit code 캡처. __SE_RC__= 라인은 body 에서 제거.
fn safe_exec_with_rc(cmd: string, timeout_sec: i64) -> [string] {
    let wrapped = _se_wrap(cmd, timeout_sec)
    let combined = "(" + wrapped + " 2>&1; echo \"__SE_RC__=$?\")"
    let raw = _se_str(exec(combined))
    let parts = raw.split("\n")
    let mut rc = "0"
    let mut clean_lines: [string] = []
    let mut i: i64 = 0
    let n = len(parts)
    while i < n {
        let ln = _se_str(parts[i])
        if ln.starts_with("__SE_RC__=") {
            // 값 추출 — starts_with 이후 substring
            rc = ln.substring(10, len(ln)).trim()
        } else {
            clean_lines = clean_lines.push(ln)
        }
        i = i + 1
    }
    // 재결합 — 마지막 빈 줄 제거
    let mut body = ""
    let mut j: i64 = 0
    let m = len(clean_lines)
    while j < m {
        if j > 0 { body = body + "\n" }
        body = body + _se_str(clean_lines[j])
        j = j + 1
    }
    // 끝 trailing \n 제거 (echo __SE_RC__ 앞 줄바꿈 잔존)
    if body.ends_with("\n") {
        body = body.substring(0, len(body) - 1)
    }
    return [rc, body]
}

// ─── 편의 함수: exit code 만 ───
fn safe_exec_rc(cmd: string, timeout_sec: i64) -> i64 {
    let r = safe_exec_with_rc(cmd, timeout_sec)
    return to_int(_se_str(r[0]))
}
