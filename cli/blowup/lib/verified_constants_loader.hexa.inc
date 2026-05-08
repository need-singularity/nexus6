// ═══════════════════════════════════════════════════════════
// verified_constants_loader.hexa.inc — 도메인 기반 lazy-load
// 사용: 이 파일을 .hexa 스크립트 상단에 포함 (atlas_guard.hexa.inc 패턴)
//
//   let entries = vc_load_domain("n6-architecture")
//   // → ["{...}", "{...}", ...] 해당 도메인 JSON 라인 배열
//
//   let all = vc_load_domain("*")
//   // → 전체 로드 (폴백)
//
// 원리:
//   1. verified_constants.idx.json 존재+신선 → sed line-range (O(N) → O(k))
//   2. 인덱스 부재/스테일 → 전체 grep 폴백
//   3. 19MB 전체 read_file 회피 — exec(sed/grep) 위임
// ═══════════════════════════════════════════════════════════

fn _vc_paths() -> map {
    let home = exec("printenv HOME").trim()
    let shared = home + "/core/nexus/shared"
    let mut P = #{}
    P["src"] = shared + "/discovery/verified_constants.jsonl"
    P["idx"] = shared + "/discovery/verified_constants.idx.json"
    return P
}

// 인덱스 신선도 검사: idx 존재 + source_mtime 일치
fn _vc_index_fresh() -> bool {
    let P = _vc_paths()
    let idx_exists = exec("test -f '" + P["idx"] + "' && echo y || echo n").trim()
    if idx_exists != "y" { return false }

    // source 현재 mtime
    let src_mtime = exec("stat -f '%m' '" + P["src"] + "' 2>/dev/null || stat -c '%Y' '" + P["src"] + "' 2>/dev/null").trim()

    // idx에 기록된 mtime
    let idx_mtime = exec("/usr/bin/python3 -c 'import json; print(json.load(open(\"" + P["idx"] + "\"))[\"source_mtime\"])' 2>/dev/null").trim()

    return src_mtime == idx_mtime
}

// 인덱스에서 도메인의 start_line, count 조회
// 반환: "start_line\tcount" 또는 빈 문자열 (미발견)
fn _vc_lookup_domain(domain: string) -> string {
    let P = _vc_paths()
    let result = exec("/usr/bin/python3 -c 'import json,sys; d=json.load(open(\"" + P["idx"] + "\"))[\"domains\"].get(sys.argv[1],{}); print(str(d.get(\"start_line\",\"\"))+\"\\t\"+str(d.get(\"count\",\"\")))' '" + domain + "' 2>/dev/null").trim()
    if result == "\t" { return "" }
    return result
}

// 도메인 목록 조회
fn vc_list_domains() -> list {
    let P = _vc_paths()
    if !_vc_index_fresh() {
        // 인덱스 없으면 grep 폴백
        let raw = exec("grep -oP '\"project\":\\s*\"\\K[^\"]+' '" + P["src"] + "' | sort -u").trim()
        return raw.split("\n")
    }
    let raw = exec("/usr/bin/python3 -c 'import json; [print(k) for k in json.load(open(\"" + P["idx"] + "\"))[\"domains\"]]' 2>/dev/null").trim()
    return raw.split("\n")
}

// 핵심: 도메인 기반 lazy-load
// domain="*" → 전체 (폴백), domain="project-name" → 해당 블록만
// 반환: JSON 라인 문자열 배열
fn vc_load_domain(domain: string) -> list {
    let P = _vc_paths()

    // 전체 로드 요청
    if domain == "*" {
        let raw = exec("cat '" + P["src"] + "'").trim()
        return raw.split("\n")
    }

    // 인덱스 경유 fast-path
    if _vc_index_fresh() {
        let lookup = _vc_lookup_domain(domain)
        if lookup != "" {
            let parts = lookup.split("\t")
            if parts.len() == 2 {
                let start = parts[0].trim()
                let count = parts[1].trim()
                if start != "" && count != "" {
                    let end_line = to_string(to_int(start) + to_int(count) - 1)
                    let raw = exec("sed -n '" + start + "," + end_line + "p' '" + P["src"] + "'").trim()
                    if raw != "" {
                        return raw.split("\n")
                    }
                }
            }
        }
        // 도메인 미발견 → 빈 배열
        return []
    }

    // 폴백: grep 필터 (인덱스 스테일/부재)
    let raw = exec("grep '\"project\":.*\"" + domain + "\"' '" + P["src"] + "' 2>/dev/null").trim()
    if raw == "" { return [] }
    return raw.split("\n")
}

// 도메인 라인 수 조회 (로드 없이)
fn vc_domain_count(domain: string) -> int {
    let P = _vc_paths()

    if _vc_index_fresh() {
        let lookup = _vc_lookup_domain(domain)
        if lookup != "" {
            let parts = lookup.split("\t")
            if parts.len() == 2 {
                return to_int(parts[1].trim())
            }
        }
        return 0
    }

    // 폴백
    let c = exec("grep -c '\"project\":.*\"" + domain + "\"' '" + P["src"] + "' 2>/dev/null").trim()
    if c == "" { return 0 }
    return to_int(c)
}
