// ═══════════════════════════════════════════════════════════
// lib/lock_acquire.hexa.inc — H-NOZOMBIE helper (Phase 2)
// 장기 실행 .hexa 모듈 자체 lock — 동일 인스턴스 동시 실행 방지.
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//
// usage:
//   if try_acquire_self_lock("blowup", 5) == false {
//       eprintln("[blowup] 다른 인스턴스 실행중 — 종료")
//       return
//   }
//   // ... 본문 ...
//   release_self_lock("blowup")
//
// 우회: NEXUS_NO_LOCK=1 env (호출측 return true)
// gate 부재 시 graceful degrade (통과).
// ═══════════════════════════════════════════════════════════

let _LK_HOME = env("HOME")
let _LK_GATE = _LK_HOME + "/core/nexus/tool/lock_gate.sh"

// ─── void-safe string coercion ───
fn _lk_str(x) -> string {
    let t = type_of(x)
    if t == "str" || t == "string" { return x }
    return ""
}

// ─── gate 존재 여부 ───
fn _lk_gate_ok() -> bool {
    let r = _lk_str(exec("test -x '" + _LK_GATE + "' && echo y || echo n")).trim()
    return r == "y"
}

// ─── lock name 의 쉘 안전성 (영문/숫자/_-.만 허용) ───
fn _lk_safe_name(name: string) -> string {
    let mut out = ""
    let n = len(name)
    let allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
    let mut i: i64 = 0
    while i < n {
        let ch = name.substring(i, i + 1)
        if allowed.index_of(ch) >= 0 {
            out = out + ch
        } else {
            out = out + "_"
        }
        i = i + 1
    }
    if len(out) == 0 { return "unnamed" }
    return out
}

// ─── acquire: 성공 true / 실패 false ───
// wait_sec=0 이면 즉시 non-blocking.
fn try_acquire_self_lock(name: string, wait_sec: i64) -> bool {
    if env("NEXUS_NO_LOCK") == "1" { return true }
    if !_lk_gate_ok() { return true }  // gate 부재 → degrade
    let safe = _lk_safe_name(name)
    // lock_gate.sh acquire <name> <wait_s> ; exit 0=hold, 75=busy
    let cmd = "bash '" + _LK_GATE + "' acquire '" + safe + "' " + to_string(wait_sec) +
              " >/dev/null 2>&1; echo $?"
    let rc = _lk_str(exec(cmd)).trim()
    return rc == "0"
}

// ─── release ───
fn release_self_lock(name: string) {
    if env("NEXUS_NO_LOCK") == "1" { return }
    if !_lk_gate_ok() { return }
    let safe = _lk_safe_name(name)
    exec("bash '" + _LK_GATE + "' release '" + safe + "' >/dev/null 2>&1")
}

// ─── status: "HELD pid=N ts=T" / "FREE" / "" (gate 부재) ───
fn lock_status(name: string) -> string {
    if !_lk_gate_ok() { return "" }
    let safe = _lk_safe_name(name)
    return _lk_str(exec("bash '" + _LK_GATE + "' status '" + safe + "' 2>/dev/null")).trim()
}

// ─── gc: stale lock 청소 (600s+ 또는 dead pid) ───
fn lock_gc() {
    if !_lk_gate_ok() { return }
    exec("bash '" + _LK_GATE + "' gc >/dev/null 2>&1")
}
