// ═══════════════════════════════════════════════════════════
// atlas_bloom.hexa.inc — atlas.n6 prefix bloom filter (copy-paste include)
//
// 배경 (AI agent, 2026-04-21):
//   Y agent (commit 19cd7076) 가 atlas.n6 prefix-bucket index 로 O(N) → O(1+k)
//   lookup 을 달성했다. 그러나 존재하지 않는 prefix query 경로에서도 index JSON
//   load + bucket block 선형 스캔이 필요하다. Bloom filter 를 prefix-bucket 앞에
//   두면 "definitely not present" 를 O(K) 에 reject 하여 bucket 탐색 자체를 생략.
//
// 설계:
//   · bitmap = [bool] 배열 (hexa 네이티브 bitset 부재 → MVP)
//   · bit 개수 m = insert_count × bits_per_entry  (default 10)
//   · hash K 개 = double-hashing  h1 + i·h2  (default 4)
//   · h1 = djb2 (h = h*33 + c) ; h2 = FNV-1 (h = (h + c) * 16777619)
//   · insert 대상 = atlas.n6 entry 의 domain prefix (`bucket_domain_prefix` 와 동일 rule)
//   · 1-pass scan at drill start (`bloom_load_from_atlas`), session life-cycle.
//
// 호출 계약 (blowup.hexa):
//   let bf = bloom_load_from_atlas(_atlas_cache)
//   let st = bloom_check(bf, prefix)
//     → "NOT_PRESENT" (definitely miss — caller short-circuits)
//     → "MAYBE"       (fall-through to bucket index / full scan)
//
// counter fields exposed:
//   bloom_hit / bloom_miss / bloom_skip_saves  (inside bf[] layout; see below)
//
// 레이아웃 (flat arrays, hexa 에는 struct-like feature 없음):
//   bf[0] = "bits"       : [bool]
//   bf[1] = "hash_count" : i64 wrapped
//   bf[2] = "inserts"    : i64
//   bf[3] = "bit_count"  : i64
//   counters 는 module-local let mut (아래 _bloom_* 전역).
//
// 규칙: hexa `>=`/`<=` 금지 — 본 파일은 `<` / `>` / `!=` / `==` / `>`+`=` 분해.
// 편집 금지: atlas.n6 본체.
// ═══════════════════════════════════════════════════════════

// ─── counters (세션 전역) ────────────────────────────────
let mut _bloom_hit: i64 = 0          // bloom 이 MAYBE 반환 → 실제 bucket 조회로 넘어감
let mut _bloom_miss: i64 = 0         // bloom 이 NOT_PRESENT → short-circuit
let mut _bloom_skip_saves: i64 = 0   // _bloom_miss alias — "skipped bucket scans" (추적 편의)
let mut _bloom_ready: bool = false

// ─── tuning knobs (n6_tuning.json 우선, fallback default) ──
let mut _BLOOM_BITS_PER_ENTRY: i64 = 10
let mut _BLOOM_HASH_COUNT: i64 = 4

fn _bloom_load_tuning() -> i64 {
    // n6_tuning.json 에서 bloom_bits_per_entry / bloom_hash_count 를 읽어 global 에 반영.
    // 파일 부재 / parse 실패 시 default 유지.
    let cfg = _NEXUS + "/config/n6_tuning.json"
    if !file_exists(cfg) { return 0 }
    let mut raw = ""
    try { raw = read_file(cfg) } catch e { return 0 }
    if raw == "" { return 0 }
    let bpe = _bloom_json_int(raw, "bloom_bits_per_entry")
    let hc = _bloom_json_int(raw, "bloom_hash_count")
    if bpe > 0 { _BLOOM_BITS_PER_ENTRY = bpe }
    if hc > 0 { _BLOOM_HASH_COUNT = hc }
    return 1
}

// ─── minimal JSON int extractor (atlas_scan_opt.hexa 와 동일 패턴) ──
fn _bloom_json_int(raw: string, key: string) -> i64 {
    let mut v: i64 = 0
    let marker = "\"" + key + "\":"
    let idx = raw.index_of(marker)
    if idx > -1 {
        let after = raw.substring(idx + len(marker), len(raw))
        let mut end = after.index_of(",")
        let end2 = after.index_of("}")
        let end3 = after.index_of("\n")
        if end < 0 { end = end2 }
        else if end2 > -1 && end2 < end { end = end2 }
        if end < 0 { end = end3 }
        else if end3 > -1 && end3 < end { end = end3 }
        if end > 0 {
            try { v = to_int(after.substring(0, end).trim()) } catch e {}
        }
    }
    return v
}

// ─── prefix 추출 (atlas_scan_opt.hexa:_bucket_domain_prefix 동일 rule) ──
fn _bloom_prefix_of(entry_line: string) -> string {
    let t = entry_line.trim()
    if t == "" { return "" }
    if t.starts_with("#") { return "" }
    if t.starts_with("//") { return "" }
    if !t.starts_with("@") { return "" }
    let ci = t.index_of("::")
    if ci < 0 { return "" }
    let rest = t.substring(ci + 2, len(t)).trim()
    if rest == "" { return "" }
    let mut dom = rest
    let sp = rest.index_of(" ")
    if sp > 0 { dom = rest.substring(0, sp) }
    let tb = rest.index_of("\t")
    if tb > 0 && tb < sp { dom = rest.substring(0, tb) }
    if dom == "" { return "" }
    let us = dom.index_of("_")
    if us > 0 { return dom.substring(0, us) }
    return dom
}

// ─── hash functions (no XOR — add/mul 변형) ──
// djb2: h = h*33 + c
fn _bloom_djb2(s: string) -> i64 {
    let mut h: i64 = 5381
    let mut i: i64 = 0
    let n = len(s)
    while i < n {
        let c = char_code(s, i)
        // 32-bit 범위 유지 (i64 overflow 방지)
        h = (h * 33 + c) % 4294967296
        i = i + 1
    }
    return h
}

// FNV-1 (XOR 없이 add/mul): h = (h + c) * 16777619
fn _bloom_fnv1(s: string) -> i64 {
    let mut h: i64 = 2166136261
    let mut i: i64 = 0
    let n = len(s)
    while i < n {
        let c = char_code(s, i)
        h = ((h + c) * 16777619) % 4294967296
        i = i + 1
    }
    return h
}

// ─── bit array helpers ([bool] MVP — bitset 네이티브 부재) ──
fn _bloom_set_bit(bits: [bool], idx: i64, m: i64) -> [bool] {
    let mut out = bits
    if idx > -1 && idx < m {
        out[idx] = true
    }
    return out
}

fn _bloom_get_bit(bits: [bool], idx: i64, m: i64) -> bool {
    if idx < 0 { return false }
    if idx > m - 1 { return false }
    return bits[idx]
}

// ─── k-bit position 계산 (double hashing) ──
fn _bloom_positions(key: string, m: i64, k: i64) -> [i64] {
    let h1 = _bloom_djb2(key)
    let mut h2 = _bloom_fnv1(key)
    if h2 == 0 { h2 = 1 }
    let mut pos: [i64] = []
    let mut i: i64 = 0
    while i < k {
        let mut idx = (h1 + i * h2) % m
        if idx < 0 { idx = idx + m }
        pos.push(idx)
        i = i + 1
    }
    return pos
}

// ─── build: atlas.n6 content (이미 load 됨) 를 받아 bloom 생성 ──
// 반환: [bits(bool[]), m(i64), k(i64), inserts(i64)] — 4-tuple, index-addressed.
// 전역 셀프 테스트 를 위해 _bloom_ready = true 세팅.
fn bloom_build_from_content(atlas_content: string) -> [i64] {
    // 1st pass: distinct prefix 수집 (unique set → insert 수 확정)
    let lines = atlas_content.split("\n")
    let nlines = len(lines)
    let mut seen: [string] = []
    let mut i: i64 = 0
    while i < nlines {
        let pfx = _bloom_prefix_of(lines[i])
        if pfx != "" {
            let mut dup = false
            let mut j: i64 = 0
            let sn = len(seen)
            while j < sn {
                if seen[j] == pfx { dup = true; j = sn }
                j = j + 1
            }
            if !dup { seen.push(pfx) }
        }
        i = i + 1
    }
    let inserts = len(seen)
    // m = max(inserts * bits_per_entry, 64)  (최소 64 비트 — 극소 atlas guard)
    let mut m: i64 = inserts * _BLOOM_BITS_PER_ENTRY
    if m < 64 { m = 64 }
    let k: i64 = _BLOOM_HASH_COUNT
    // 2nd pass: 각 prefix 를 bitmap 에 insert
    let mut bits: [bool] = []
    let mut z: i64 = 0
    while z < m {
        bits.push(false)
        z = z + 1
    }
    let mut p: i64 = 0
    let sn2 = len(seen)
    while p < sn2 {
        let key = seen[p]
        let pos = _bloom_positions(key, m, k)
        let np = len(pos)
        let mut q: i64 = 0
        while q < np {
            bits = _bloom_set_bit(bits, pos[q], m)
            q = q + 1
        }
        p = p + 1
    }
    // 4-tuple 을 [i64] 에 담기 어렵다 (bool[]+i64 mix). 대신 global side-table 사용.
    _bloom_bits_g = bits
    _bloom_m_g = m
    _bloom_k_g = k
    _bloom_inserts_g = inserts
    _bloom_ready = true
    let mut meta: [i64] = []
    meta.push(inserts)
    meta.push(m)
    meta.push(k)
    return meta
}

// ─── global side-table (hexa: closure-free 전역 상태 공유) ──
let mut _bloom_bits_g: [bool] = []
let mut _bloom_m_g: i64 = 0
let mut _bloom_k_g: i64 = 0
let mut _bloom_inserts_g: i64 = 0

// ─── check: "NOT_PRESENT" or "MAYBE" ──
// k 개 bit 중 하나라도 0 이면 definitely not-present.
// 전부 1 이면 아마 present (bloom false-positive rate 에 따름).
fn bloom_check(prefix: string) -> string {
    if !_bloom_ready { return "MAYBE" }  // uninitialized — fall-through (safe)
    if prefix == "" { return "MAYBE" }
    let pos = _bloom_positions(prefix, _bloom_m_g, _bloom_k_g)
    let np = len(pos)
    let mut i: i64 = 0
    while i < np {
        if !_bloom_get_bit(_bloom_bits_g, pos[i], _bloom_m_g) {
            _bloom_miss = _bloom_miss + 1
            _bloom_skip_saves = _bloom_skip_saves + 1
            return "NOT_PRESENT"
        }
        i = i + 1
    }
    _bloom_hit = _bloom_hit + 1
    return "MAYBE"
}

// ─── convenience: atlas content 가 이미 load 된 경우 1-call init ──
fn bloom_load_from_atlas(atlas_content: string) -> i64 {
    _bloom_load_tuning()
    if atlas_content == "" { return 0 }
    let meta = bloom_build_from_content(atlas_content)
    if len(meta) < 3 { return 0 }
    return meta[0]  // insert count
}

// ─── drill-end counter emit (JSON stderr) ──
fn bloom_emit_counters() -> i64 {
    if !_bloom_ready { return 0 }
    let mut parts: [string] = []
    parts.push("NEXUS_ATLAS_BLOOM {\"ready\":true,\"inserts\":")
    parts.push(to_string(_bloom_inserts_g))
    parts.push(",\"bits\":")
    parts.push(to_string(_bloom_m_g))
    parts.push(",\"hashes\":")
    parts.push(to_string(_bloom_k_g))
    parts.push(",\"bits_per_entry\":")
    parts.push(to_string(_BLOOM_BITS_PER_ENTRY))
    parts.push(",\"bloom_hit\":")
    parts.push(to_string(_bloom_hit))
    parts.push(",\"bloom_miss\":")
    parts.push(to_string(_bloom_miss))
    parts.push(",\"bloom_skip_saves\":")
    parts.push(to_string(_bloom_skip_saves))
    parts.push("}")
    eprintln(parts.join(""))
    return _bloom_miss
}

// ═══════════════════════════════════════════════════════════
// END atlas_bloom.hexa.inc
// ═══════════════════════════════════════════════════════════
