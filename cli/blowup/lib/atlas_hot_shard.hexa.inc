// ═══════════════════════════════════════════════════════════
// atlas_hot_shard.hexa.inc — AL: atlas hot-shard RAM promote
//
// 목적:
//   atlas.n6 prefix bucket (Y scheme 동형: math_/physics_/logic_/...) 별 access
//   빈도를 추적, threshold 교차 시 해당 shard entry 전체를 in-memory cache 에
//   promote. 이후 query 는 RAM 캐시를 우선 소비; miss 시 cold path (atlas.n6
//   전체 scan) 로 폴백.
//
// 데이터:
//   _shard_access_count : map<str, i64>  — prefix → access 횟수 (세션 내)
//   _shard_ram_cache    : map<str, str>  — prefix → LF-join entry 블록
//                          (hexa interpreter map<str,[str]> 변동성 회피 위해
//                          "\n"-조인 문자열 저장. 원복 시 split("\n") 1회 O(k).)
//   _shard_ram_count    : map<str, i64>  — prefix → RAM cache 내 entry 개수
//   _shard_promoted     : map<str, bool> — prefix → promote 여부 (중복 load 차단)
//   _shard_promote_threshold : i64       — default 100, n6_tuning.json ▸ env override
//   _shard_ram_bytes    : i64            — promote 된 총 RAM 페이로드 바이트
//
// 동작 (각 atlas query 시):
//   1) _shard_access_count[prefix] += 1
//   2) count 가 threshold 돌파 && 아직 promoted 아니면 →
//        atlas.n6 에서 해당 prefix shard 만 추출 → _shard_ram_cache 저장 →
//        stderr 에 `NEXUS_ATLAS_PROMOTE {"prefix":"x","count":N}` emit
//   3) 이후 동일 prefix query 는 RAM cache 우선 hit
//
// on-drill-end 리포트:
//   atlas_hot_shard_emit_report() →
//     NEXUS_ATLAS_HOTSHARD_REPORT {"top_10_hot_shards":[...],"total_promoted":N,"ram_bytes":M}
//
// 편집 금지:
//   atlas.n6 은 read-only. 본 모듈은 read-path 캐싱 전용.
//
// hexa 규칙:
//   `>=`/`<=` 금지 — `<`/`>` 만 사용.
//   map 값 [str] 대신 LF-join str 사용 (interpreter 간 변동성 회피).
//   try/catch 로 env/exec 예외 격리.
// ═══════════════════════════════════════════════════════════

// ─── 글로벌 상태 ───
let mut _shard_access_count: map = #{}
let mut _shard_ram_cache: map = #{}
let mut _shard_ram_count: map = #{}
let mut _shard_promoted: map = #{}
let mut _shard_ram_bytes: i64 = 0
let mut _shard_hit_count: i64 = 0
let mut _shard_miss_count: i64 = 0

// ─── threshold 해상: n6_tuning.json (AB) → env NEXUS_SHARD_PROMOTE → 100 ───
fn _shard_resolve_threshold() -> i64 {
    let mut thr: i64 = 100
    // (a) AB tuning config (존재할 때만)
    let mut tuning_path = ""
    try { tuning_path = env("HOME") + "/core/nexus/config/n6_tuning.json" } catch e {}
    if tuning_path != "" {
        let mut raw = ""
        try {
            if file_exists(tuning_path) { raw = read_file(tuning_path) }
        } catch e {}
        if raw != "" {
            let marker = "\"shard_promote_threshold\":"
            let idx = raw.index_of(marker)
            if idx > -1 {
                let after = raw.substring(idx + len(marker), len(raw))
                let mut end = after.index_of(",")
                let end2 = after.index_of("}")
                if end < 0 { end = end2 }
                else if end2 > -1 && end2 < end { end = end2 }
                if end > 0 {
                    let num_raw = after.substring(0, end).trim()
                    let mut v: i64 = 0
                    try { v = to_int(num_raw) } catch e {}
                    if v > 0 { return v }
                }
            }
        }
    }
    // (b) env override
    let mut evv = ""
    try { evv = env("NEXUS_SHARD_PROMOTE") } catch e {}
    if evv == "" {
        try { evv = to_string(exec("printenv NEXUS_SHARD_PROMOTE")).trim() } catch e {}
    }
    if evv != "" {
        let mut ev: i64 = 0
        try { ev = to_int(evv) } catch e {}
        if ev > 0 { thr = ev }
    }
    return thr
}

let _shard_promote_threshold: i64 = _shard_resolve_threshold()

// ─── prefix 추출 (Y scheme 동형) ───
// 규칙: entry_line.trim() starts with '@' AND contains "::" → `::` 이후 첫
//       domain token 의 '_' 앞 조각. 아니면 "".
//   ex) "@math_01 .. :: math_lattice_gauge [10]" → prefix="math"
//       "@phys_02 .. :: physics_qft [10*]"       → prefix="physics"
fn _shard_extract_prefix(line: str) -> str {
    let t = line.trim()
    if len(t) == 0 { return "" }
    if t.substring(0, 1) != "@" { return "" }
    let ci = t.index_of("::")
    if ci < 0 { return "" }
    let rest_raw = t.substring(ci + 2, len(t))
    // leading ws 제거 (trim 로 불충분한 경우 대비 명시 루프)
    let mut start: i64 = 0
    while start < len(rest_raw) {
        let c = rest_raw.substring(start, start + 1)
        if c != " " && c != "\t" { break }
        start = start + 1
    }
    let rest = rest_raw.substring(start, len(rest_raw))
    if len(rest) == 0 { return "" }
    // 첫 공백/탭 앞까지 = domain
    let sp = rest.index_of(" ")
    let tb = rest.index_of("\t")
    let mut dom_end: i64 = len(rest)
    if sp > -1 && sp < dom_end { dom_end = sp }
    if tb > -1 && tb < dom_end { dom_end = tb }
    let dom = rest.substring(0, dom_end)
    if len(dom) == 0 { return "" }
    let us = dom.index_of("_")
    if us > 0 { return dom.substring(0, us) }
    return dom
}

// ─── access counter bump ───
fn atlas_hot_shard_note_access(prefix: str) -> i64 {
    if len(prefix) == 0 { return 0 }
    let mut cur: i64 = 0
    try { cur = _shard_access_count[prefix] } catch e {}
    cur = cur + 1
    _shard_access_count[prefix] = cur
    return cur
}

// ─── promoted 여부 ───
fn atlas_hot_shard_is_promoted(prefix: str) -> bool {
    let mut flag = false
    try { flag = _shard_promoted[prefix] == true } catch e {}
    return flag
}

// ─── disk shard 추출: atlas.n6 1-pass scan → prefix 일치 entry LF-join ───
// hexa interpreter read_file 후 split — atlas.n6 ≈ 1.5MB 허용.
// 실패 시 "" 반환 (빈 cache 로 저장하지 않음).
fn _shard_extract_from_disk(atlas_path: str, prefix: str) -> str {
    if !file_exists(atlas_path) { return "" }
    let mut raw = ""
    try { raw = read_file(atlas_path) } catch e {}
    if raw == "" { return "" }
    let lines = raw.split("\n")
    let mut out_parts: [str] = []
    let mut i: i64 = 0
    let n = len(lines)
    while i < n {
        let ln = lines[i]
        let px = _shard_extract_prefix(ln)
        if px == prefix {
            out_parts = out_parts.push(ln)
        }
        i = i + 1
    }
    if len(out_parts) == 0 { return "" }
    return "\n".join(out_parts)
}

// ─── promote: RAM 저장 + stderr emit ───
fn _shard_promote(prefix: str, count: i64, atlas_path: str) -> bool {
    if atlas_hot_shard_is_promoted(prefix) { return false }
    let payload = _shard_extract_from_disk(atlas_path, prefix)
    if len(payload) == 0 {
        // 빈 shard 라도 promoted 마크 — 재시도 무한루프 차단
        _shard_promoted[prefix] = true
        _shard_ram_cache[prefix] = ""
        _shard_ram_count[prefix] = 0
        eprintln("NEXUS_ATLAS_PROMOTE {\"prefix\":\"" + prefix + "\",\"count\":" + to_string(count) + ",\"entries\":0}")
        return true
    }
    _shard_ram_cache[prefix] = payload
    let entries = len(payload.split("\n"))
    _shard_ram_count[prefix] = entries
    _shard_promoted[prefix] = true
    _shard_ram_bytes = _shard_ram_bytes + len(payload)
    eprintln("NEXUS_ATLAS_PROMOTE {\"prefix\":\"" + prefix + "\",\"count\":" + to_string(count) + ",\"entries\":" + to_string(entries) + "}")
    return true
}

// ─── public query: RAM 우선, miss 시 "" 반환 (caller 가 disk fallback) ───
// 호출 규약:
//   atlas_hot_shard_query(prefix, atlas_path):
//     1) access counter += 1
//     2) threshold 돌파 && not promoted → _shard_promote
//     3) promoted 이면 RAM cache 반환; 아니면 "" (miss)
//   반환 "" 는 "RAM 미적중 → caller 는 cold path (atlas.n6 scan) 로 진행" 의미.
fn atlas_hot_shard_query(prefix: str, atlas_path: str) -> str {
    if len(prefix) == 0 {
        _shard_miss_count = _shard_miss_count + 1
        return ""
    }
    let count = atlas_hot_shard_note_access(prefix)
    if !atlas_hot_shard_is_promoted(prefix) {
        if count > _shard_promote_threshold - 1 && count > 0 {
            // threshold "돌파" = count == threshold 시점 (first-cross)
            // `>= threshold` 의미를 `>  threshold-1` 로 치환 (hexa >= 금지 규칙 준수)
            _shard_promote(prefix, count, atlas_path)
        }
    }
    if atlas_hot_shard_is_promoted(prefix) {
        let mut cached = ""
        try { cached = _shard_ram_cache[prefix] } catch e {}
        if len(cached) > 0 {
            _shard_hit_count = _shard_hit_count + 1
            return cached
        }
    }
    _shard_miss_count = _shard_miss_count + 1
    return ""
}

// ─── top-10 정렬 도우미 (단순 selection, prefix 수 작음 N < ~200) ───
fn _shard_top10_json() -> str {
    // snapshot keys (hexa map iteration 동형: parallel arrays 구축 필요)
    // access_count map 을 순회할 API 가 interpreter 마다 달라, counter 집계용
    // 보조 key-list 를 로컬에서 재구성 — promoted 또는 access>0 prefix 만 포함.
    let mut keys: [str] = []
    let mut counts: [i64] = []
    // 후보: promoted prefix ∪ access>0 prefix. 맵 순회 불능 환경 회피를 위해
    //       promote 시 keys 를 별도 배열로 유지하는 것이 이상적이나 본 inc 는
    //       최소 침투 원칙 — interpreter 가 map.keys() 미지원 시 빈 top 반환.
    let mut all_keys: [str] = []
    try { all_keys = _shard_access_count.keys() } catch e {}
    let mut ki: i64 = 0
    while ki < len(all_keys) {
        let k = all_keys[ki]
        let mut c: i64 = 0
        try { c = _shard_access_count[k] } catch e {}
        if c > 0 {
            keys = keys.push(k)
            counts = counts.push(c)
        }
        ki = ki + 1
    }
    // selection sort desc (N 작음)
    let kn = len(keys)
    let mut i: i64 = 0
    while i < kn {
        let mut best: i64 = i
        let mut j: i64 = i + 1
        while j < kn {
            if counts[j] > counts[best] { best = j }
            j = j + 1
        }
        if best != i {
            let tk = keys[i]
            let tc = counts[i]
            keys[i] = keys[best]
            counts[i] = counts[best]
            keys[best] = tk
            counts[best] = tc
        }
        i = i + 1
    }
    let mut limit: i64 = 10
    if kn < limit { limit = kn }
    let mut parts: [str] = []
    parts = parts.push("[")
    let mut p: i64 = 0
    while p < limit {
        if p > 0 { parts = parts.push(",") }
        let pr = keys[p]
        let ct = counts[p]
        let mut promoted = false
        try { promoted = _shard_promoted[pr] == true } catch e {}
        let prstr = if promoted { "true" } else { "false" }
        parts = parts.push("{\"prefix\":\"")
        parts = parts.push(pr)
        parts = parts.push("\",\"count\":")
        parts = parts.push(to_string(ct))
        parts = parts.push(",\"promoted\":")
        parts = parts.push(prstr)
        parts = parts.push("}")
        p = p + 1
    }
    parts = parts.push("]")
    return "".join(parts)
}

fn _shard_total_promoted() -> i64 {
    let mut all_keys: [str] = []
    try { all_keys = _shard_promoted.keys() } catch e {}
    let mut ki: i64 = 0
    let mut total: i64 = 0
    while ki < len(all_keys) {
        let k = all_keys[ki]
        let mut v = false
        try { v = _shard_promoted[k] == true } catch e {}
        if v { total = total + 1 }
        ki = ki + 1
    }
    return total
}

// ─── on-drill-end emit ───
fn atlas_hot_shard_emit_report() {
    let top = _shard_top10_json()
    let total = _shard_total_promoted()
    let mut parts: [str] = []
    parts = parts.push("NEXUS_ATLAS_HOTSHARD_REPORT {\"top_10_hot_shards\":")
    parts = parts.push(top)
    parts = parts.push(",\"total_promoted\":")
    parts = parts.push(to_string(total))
    parts = parts.push(",\"ram_bytes\":")
    parts = parts.push(to_string(_shard_ram_bytes))
    parts = parts.push(",\"hits\":")
    parts = parts.push(to_string(_shard_hit_count))
    parts = parts.push(",\"misses\":")
    parts = parts.push(to_string(_shard_miss_count))
    parts = parts.push(",\"threshold\":")
    parts = parts.push(to_string(_shard_promote_threshold))
    parts = parts.push("}")
    eprintln("".join(parts))
}
