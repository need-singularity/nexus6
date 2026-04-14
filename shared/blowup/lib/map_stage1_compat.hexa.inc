// ═══════════════════════════════════════════════════════════
// map_stage1_compat — hexa stage1 인터프리터 map IndexAssign no-op 우회 헬퍼
// 2026-04-14  NEXUS-6 DISC-P1-1 NDJSON 파서 blocker 대응
//
// 배경:
//   stage1 인터프리터(build/hexa_stage0)의 NK_ASSIGN 핸들러가 TAG_MAP 을 처리
//   하지 않아 `map[k] = v` 가 silent no-op.  (self/hexa_full.hexa 의 fix 는
//   ef7ccc1 에 있으나 현재 stage0 바이너리가 stale — hexa_v2 가 invariant DSL
//   전파 실패로 rebuild 불가.)  근본 fix 전까지 사용 가능한 parallel-list
//   기반 공식 우회.
//
// 사용법:
//   // (1) 이 파일을 모듈 상단에 복사 붙여넣기.
//   // (2) 맵 대신 `keys` / `vals` 두 리스트를 함께 관리.
//   let mut ks = []
//   let mut vs = []
//   // set
//   let pair = map_set_list(ks, vs, "alpha", 1)
//   ks = pair[0] ; vs = pair[1]
//   // get (기본값 지정)
//   let v = map_get_or(ks, vs, "alpha", 0)
//   // contains
//   if map_has(ks, "alpha") { ... }
//   // 증가 (도메인 카운터 관용구)
//   let pair2 = map_bump(ks, vs, "alpha")
//   ks = pair2[0] ; vs = pair2[1]
//
// 성능: O(n) per op (선형탐색).  NDJSON 도메인 수 ≤ ~100 이므로 수용.
//       10000 key 이상은 wrapping 파일 단위로 sorted-list binary-search 고려.
// ═══════════════════════════════════════════════════════════

// 키 인덱스 반환. 없으면 -1.
fn map_idx(ks: list, k: string) -> i64 {
    let n = len(ks)
    let mut i = 0
    while i < n {
        if to_string(ks[i]) == k { return i }
        i = i + 1
    }
    return -1
}

// 존재 여부.
fn map_has(ks: list, k: string) -> bool {
    return map_idx(ks, k) >= 0
}

// get — 기본값 지정. key 없으면 default.
fn map_get_or(ks: list, vs: list, k: string, default_v) {
    let i = map_idx(ks, k)
    if i < 0 { return default_v }
    return vs[i]
}

// set — append 또는 교체. [new_ks, new_vs] pair 반환.
fn map_set_list(ks: list, vs: list, k: string, v) -> list {
    let i = map_idx(ks, k)
    if i < 0 {
        return [ks + [k], vs + [v]]
    }
    // 기존 키 교체: 슬라이스+concat (stage1 list[i]=v 도 no-op 이므로)
    // NOTE: stage1 slice pitfall #2 — `vs[i+1..len(vs)]` 처럼 식 포함 슬라이스는
    //       결과가 scalar (vs[i+1]) 로 무너진다. 반드시 `let start = i+1;
    //       let end = len(vs); vs[start..end]` 로 변수 분리.
    let start = i + 1
    let end = len(vs)
    let head = vs[0..i]
    let tail = vs[start..end]
    let new_vs = head + [v] + tail
    return [ks, new_vs]
}

// bump — 정수 카운터 +1. key 없으면 1 로 삽입.
fn map_bump(ks: list, vs: list, k: string) -> list {
    let cur = to_int(map_get_or(ks, vs, k, 0))
    return map_set_list(ks, vs, k, cur + 1)
}

// add_n — 정수 가산 (bump 의 일반화).  key 없으면 n 으로 삽입.
fn map_add_n(ks: list, vs: list, k: string, n: i64) -> list {
    let cur = to_int(map_get_or(ks, vs, k, 0))
    return map_set_list(ks, vs, k, cur + n)
}

// delete — 키 제거. 없으면 원본 반환.
fn map_del_list(ks: list, vs: list, k: string) -> list {
    let i = map_idx(ks, k)
    if i < 0 { return [ks, vs] }
    // stage1 slice pitfall #2 우회 (map_set_list 와 동일)
    let start = i + 1
    let end_k = len(ks)
    let end_v = len(vs)
    let kh = ks[0..i]
    let kt = ks[start..end_k]
    let vh = vs[0..i]
    let vt = vs[start..end_v]
    let new_ks = kh + kt
    let new_vs = vh + vt
    return [new_ks, new_vs]
}

// len — 키 개수.
fn map_len(ks: list) -> i64 {
    return len(ks)
}

// keys / values — 호환성 위한 얕은 래퍼 (동일 리스트 반환).
fn map_keys(ks: list) -> list { return ks }
fn map_values(vs: list) -> list { return vs }
