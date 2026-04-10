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

// append_file 전 라인 필터링 (무효 라인 거부 + 보고)
// _atlas_path: atlas.n6 경로 (모듈마다 변수명 다를 수 있음)
fn _guarded_append_atlas(path: string, content: string) -> i64 {
    if len(content) == 0 { return 0 }
    let lines = content.split("\n")
    let mut clean = ""
    let mut rejected: i64 = 0
    let mut first = true
    let mut i: i64 = 0
    while i < len(lines) {
        let line = lines[i]
        if _valid_atlas_line(line) {
            if !first { clean = clean + "\n" }
            clean = clean + line
            first = false
        } else {
            rejected = rejected + 1
        }
        i = i + 1
    }
    if rejected > 0 {
        println("  [schema guard] rejected " + to_string(rejected) + " invalid lines -> " + path)
    }
    if len(clean) > 0 {
        try { append_file(path, clean) } catch e {}
    }
    return rejected
}

// ─── Intra-batch dedup helper (루프 내부용) ───
// 사용 예:
//   let mut _batch_ids = #{}
//   ... 루프 내 ...
//   if !_batch_dedup_has(_batch_ids, node_id) && !graph_node_exists(content, node_id) {
//       _batch_ids[node_id] = true
//       // 실제 append 수행
//   }
fn _batch_dedup_has(s: map, id: string) -> bool {
    let mut hit = false
    try { hit = has_key(s, id) } catch e {}
    return hit
}
