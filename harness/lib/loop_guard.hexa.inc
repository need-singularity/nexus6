// ═══════════════════════════════════════════════════════════
// lib/loop_guard.hexa.inc — H-NOZOMBIE helper (Phase 2)
// while true / loop 무한루프 방지 — max_iter + deadline 가드.
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//
// usage (권장 — 카운터 + 시간 둘 다):
//   let lg_started = now_sec()
//   let mut lg_iter: i64 = 0
//   while true {
//       if loop_check(lg_iter, 10000, lg_started, 60, "blowup_main") == false { break }
//       lg_iter = lg_iter + 1
//       // ... 본문 ...
//   }
//
// usage (간단 — 카운터만):
//   let mut iter: i64 = 0
//   while true {
//       iter = iter + 1
//       if loop_max_iter(iter, 10000, "phase1") { break }
//       // ... 본문 ...
//   }
//
// 우회: NEXUS_NO_LOOPGUARD=1 (반환값 영구 true, 즉 통과)
// hexa pitfalls: struct 미지원 → 파라미터 전달 패턴.
// ═══════════════════════════════════════════════════════════

// ─── void-safe string coercion ───
fn _lg_str(x) -> string {
    let t = type_of(x)
    if t == "str" || t == "string" { return x }
    return ""
}

// ─── 첫 줄 기반 int 파싱 (grep || echo 0 이중출력 방어) ───
fn _lg_to_int0(s: string) -> i64 {
    if s == "" { return 0 }
    let first = _lg_str(s.split("\n")[0]).trim()
    if first == "" { return 0 }
    return to_int(first)
}

// ─── unix 초 ───
fn now_sec() -> i64 {
    return _lg_to_int0(_lg_str(exec("date +%s")).trim())
}

// ─── 메인 가드: iter/time 둘 다 체크 ───
// 반환 true=계속, false=break.
fn loop_check(iter: i64, max_iter: i64, started: i64, max_sec: i64, label: string) -> bool {
    if env("NEXUS_NO_LOOPGUARD") == "1" { return true }
    if iter > max_iter {
        eprintln("[loop_guard:" + label + "] max_iter=" + to_string(max_iter) + " 초과 (iter=" + to_string(iter) + ")")
        return false
    }
    let elapsed = now_sec() - started
    if elapsed > max_sec {
        eprintln("[loop_guard:" + label + "] timeout " + to_string(elapsed) + "s > " + to_string(max_sec) + "s")
        return false
    }
    return true
}

// ─── 카운터만 (시간 무시) ───
// 반환 true=초과(break 해야 함), false=계속.
// 주의: loop_check 와 sense 반대. 사용처에 맞게 선택.
fn loop_max_iter(iter: i64, max_iter: i64, label: string) -> bool {
    if env("NEXUS_NO_LOOPGUARD") == "1" { return false }
    if iter > max_iter {
        eprintln("[loop_guard:" + label + "] max_iter=" + to_string(max_iter) + " 초과 abort")
        return true
    }
    return false
}

// ─── deadline 체크 (시간만) ───
// 반환 true=계속, false=break.
fn loop_deadline(started: i64, max_sec: i64, label: string) -> bool {
    if env("NEXUS_NO_LOOPGUARD") == "1" { return true }
    let elapsed = now_sec() - started
    if elapsed > max_sec {
        eprintln("[loop_guard:" + label + "] timeout " + to_string(elapsed) + "s > " + to_string(max_sec) + "s")
        return false
    }
    return true
}

// ─── 조용한 체크 (stderr 없음) — tight loop inner ───
fn loop_check_quiet(iter: i64, max_iter: i64, started: i64, max_sec: i64) -> bool {
    if env("NEXUS_NO_LOOPGUARD") == "1" { return true }
    if iter > max_iter { return false }
    if now_sec() - started > max_sec { return false }
    return true
}
