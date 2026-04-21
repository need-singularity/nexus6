// ═══════════════════════════════════════════════════════════
// lib/pre_tool_write.hexa.inc — Write/Edit PreToolUse 가드 모음
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//       (hexa stage1 native include 미지원. 본 파일은 canonical source.)
//
// 목적: pre_tool_guard.hexa 카테고리 분리 refactor (H-마커 8 혼재 해소).
// 의존: lib/pre_tool_common.hexa.inc (_guard_noname_v_match)
// 참조 main: shared/harness/pre_tool_guard.hexa
//
// 함수 목록 (dispatch 순서):
//   check_forbidden_ext           Write .py/.rs/.sh 신규 차단       (R1 HEXA-FIRST)
//   check_global_claude           ~/.claude/ 수정 차단                (L0)
//   check_shared_protected        shared/hooks shared/config 보호     (L0)
//   check_discovery_json_path     폐기 JSON 신규 생성 차단            (R28)
//   check_calculator_ssot         계산기 .hexa SSOT 강제              (R29)
//   check_roadmap_min             로드맵 최소 경로 문법 강제          (R34)
//   check_no_archive_path         *.bak 폴더/파일 차단                (H-NOARCHIVE)
//   check_no_version_name         _v2/_mk3 버전 suffix 차단           (H-NONAME-V)
//   check_no_hook_file            .git/hooks .claude/hooks 차단       (H-NOHOOK)
//   check_lockdown_tier           L0/L1/L2 lockdown_gate watch 위임   (L0)
//   check_session_lock            area 기반 advisory lock             (H-SESSION-LOCK)
//   check_annot_rules             annot_rules.json 토큰 차단          (H-ANNOT-RULES)
// ═══════════════════════════════════════════════════════════

// R1 HEXA-FIRST: .py/.rs/.sh 신규 파일 차단
fn check_forbidden_ext(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }

    let ext_blocked = file_path.ends_with(".py") || file_path.ends_with(".rs") || file_path.ends_with(".sh")
    if ext_blocked == false { return "" }

    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()
    if exists == "y" { return "" }  // 기존 파일 덮어쓰기는 허용

    return "REJECT: " + file_path + " — .py/.rs/.sh 신규 작성 금지 (HEXA-FIRST R1). .hexa로 작성하세요."
}

// L0: ~/.claude/ 및 ~/.claude-<suffix>/ 글로벌 수정 차단 (settings.json 제외)
//     멀티계정 .claude-claude11/.claude-claude12/ 등도 커버 (2026-04-14)
fn check_global_claude(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }
    let h = env("HOME")
    let in_main = file_path.starts_with(h + "/.claude/")
    let in_multi = file_path.starts_with(h + "/.claude-")
    if in_main == false && in_multi == false { return "" }
    let base = to_string(exec("basename '" + file_path + "'")).trim()
    if base == "settings.json" { return "" }
    return "REJECT: " + file_path + " — 글로벌 ~/.claude*/ 내부 파일 수정 금지 (settings.json 제외). 프로젝트별 .claude/settings.json 경로 사용."
}

// L0: shared/hooks/, shared/config/ L0 파일 직접 수정 차단
fn check_shared_protected(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }

    let protected = [
        "/shared/hooks/hooks-config.json",
        "/shared/config/absolute_rules.json",
        "/shared/config/core-lockdown.json"
    ]
    for p in protected {
        if file_path.contains(p) {
            return "REJECT: " + file_path + " — 공용 L0 설정 직접 수정 금지. sync 스크립트 또는 사용자 명시 승인 후."
        }
    }

    // shared/hooks/*.hexa 수정 차단 (공용 훅 보호)
    if file_path.contains("/shared/hooks/") {
        if file_path.ends_with(".hexa") || file_path.ends_with(".sh") || file_path.ends_with(".py") {
            return "REJECT: " + file_path + " — 공용 훅 직접 수정 금지. harness/ 로 이관 중 — shared/harness/ 사용."
        }
    }

    return ""
}

// R28: 폐기된 JSON 발견 저장소 신규 생성 금지 — atlas.n6 단일 SSOT
// 우회: @allow-deprecated-json 주석 또는 archive/deprecated_json/ 경로
fn check_discovery_json_path(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }
    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()
    if exists == "y" { return "" }
    if file_path.contains("/archive/deprecated_json/") { return "" }

    let banned = [
        "discovery_graph.json",
        "discovery_log.jsonl",
        "growth_bus.json",
        "verified_constants.json",
        "module_candidates.json",
        "reality_map.json"
    ]
    let base = to_string(exec("basename '" + file_path + "'")).trim()
    for b in banned {
        if base == b {
            return "REJECT: 폐기 JSON '" + b + "' 신규 생성 금지 (R28) — atlas.n6 단일 SSOT. archive/deprecated_json/ 외 생성 불가"
        }
    }
    return ""
}

// R29: 계산기/검증/스캐너 .hexa 는 shared/n6/scripts/ 단일 SSOT
// 우회: @allow-project-hexa 명시 (프로젝트 전용 도구 필요 시 수동 승인)
fn check_calculator_ssot(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }
    if file_path.ends_with(".hexa") == false { return "" }
    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()
    if exists == "y" { return "" }
    if file_path.contains("/shared/n6/scripts/") { return "" }

    let banned_segments = [
        "/theory/",
        "/predictions/",
        "/proofs/",
        "/breakthroughs/",
        "/papers/",
        "/hexa-lang/docs/"
    ]
    for s in banned_segments {
        if file_path.contains(s) {
            return "REJECT: 계산기/검증 .hexa 는 shared/n6/scripts/ 단일 SSOT (R29) — '" + s + "' 하위 신규 작성 금지. 이론 repo 는 .md 전용"
        }
    }
    return ""
}

// R34: 로드맵 최소 경로 문법 강제 — 신규 roadmap*.json Write 시 금지 키 차단
// 경로 매칭: roadmap*.json | */roadmaps/*.json | *.roadmap.json
// 우회: 파일 내 `"_legacy": true` 또는 `@allow-roadmap-ext` 토큰
fn check_roadmap_min(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }
    if file_path.ends_with(".json") == false { return "" }

    let base = to_string(exec("basename '" + file_path + "'")).trim()
    let is_roadmap = base.starts_with("roadmap") || base.ends_with(".roadmap.json") || file_path.contains("/roadmaps/")
    if is_roadmap == false { return "" }

    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()
    if exists == "y" {
        let legacy = to_string(exec("grep -c '\"_legacy\":[[:space:]]*true\\|@allow-roadmap-ext' '" + file_path + "' 2>/dev/null")).trim()
        if legacy != "0" && legacy != "" { return "" }
    }

    return "REJECT: 로드맵 최소 경로 문법 필수 (R34) — 순차 배열 + 병렬 중첩 + '>' 서브순차 + par_bg 만 허용. phases/tracks/depends_on/priority/est/roi 등 확장 금지. 우회: `\"_legacy\": true` (기존 재배치)"
}

// H-NOARCHIVE: 신규 archive/backup 파일·폴더 생성 금지 — git commit 으로 변경 이력 보존.
// 격리 예외: /shared/backups/, /shared/archive/, /shared/discovery/archive/, /archive/deprecated_json/
// 우회: NEXUS_ARCHIVE_OK=1 prefix 또는 @allow-archive 토큰.
fn check_no_archive_path(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }
    if file_path.len() == 0 { return "" }
    if file_path.contains("@allow-archive") { return "" }

    if file_path.contains("shared/backups/") { return "" }
    if file_path.contains("shared/archive/") { return "" }
    if file_path.contains("shared/discovery/archive/") { return "" }
    if file_path.contains("archive/deprecated_json/") { return "" }

    let base = to_string(exec("basename '" + file_path + "'")).trim()

    let banned_suffix = [
        [".bak", "*.bak"],
        [".backup", "*.backup"],
        [".old", "*.old"],
        [".orig", "*.orig"],
        [".archived", "*.archived"]
    ]
    for s in banned_suffix {
        if base.ends_with(s[0]) {
            return "REJECT: " + file_path + " — " + s[1] + " 백업 파일 생성 금지 (H-NOARCHIVE). git commit/diff 사용. 우회: NEXUS_ARCHIVE_OK=1 prefix"
        }
    }
    if base.contains(".bak.") {
        return "REJECT: " + file_path + " — *.bak.* 백업 파일 금지 (H-NOARCHIVE). git diff/log 사용. 우회: NEXUS_ARCHIVE_OK=1"
    }

    let banned_infix = ["_backup.", "_archive.", "_old."]
    for s in banned_infix {
        if base.contains(s) {
            return "REJECT: " + file_path + " — '" + s + "' suffix 금지 (H-NOARCHIVE). git history 가 SSOT. 우회: NEXUS_ARCHIVE_OK=1"
        }
    }

    let banned_dir = [
        ["/backup/", "/backup/"],
        ["/backups/", "/backups/"],
        ["/.backup/", "/.backup/"],
        ["/.archive/", "/.archive/"],
        ["/_backup/", "/_backup/"],
        ["/_archive/", "/_archive/"],
        ["/archive/", "/archive/"],
        ["/archives/", "/archives/"]
    ]
    for d in banned_dir {
        if file_path.contains(d[0]) {
            return "REJECT: " + file_path + " — '" + d[1] + "' 폴더 신규 생성 금지 (H-NOARCHIVE). git branch/tag 사용. 격리 예외: shared/backups/, shared/archive/, shared/discovery/archive/, archive/deprecated_json/. 우회: NEXUS_ARCHIVE_OK=1"
        }
    }

    return ""
}

// H-NONAME-V: 파일/폴더명 버전 suffix 금지 — git commit/branch/tag 이 유일 SSOT.
// 의존: _guard_noname_v_match() from pre_tool_common.hexa.inc
// 격리 예외: shared/backups/, shared/archive/, shared/discovery/archive/, archive/deprecated_json/
// 우회: path 에 @allow-version-name 토큰. 기존 파일 덮어쓰기는 통과.
fn check_no_version_name(tool: str, file_path: str) -> str {
    if tool != "Write" { return "" }
    if file_path.len() == 0 { return "" }
    if file_path.contains("@allow-version-name") { return "" }
    if file_path.contains("shared/backups/") { return "" }
    if file_path.contains("shared/archive/") { return "" }
    if file_path.contains("shared/discovery/archive/") { return "" }
    if file_path.contains("archive/deprecated_json/") { return "" }
    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()
    if exists == "y" { return "" }

    let base = to_string(exec("basename '" + file_path + "'")).trim()
    let stem = to_string(exec("echo '" + base + "' | sed 's/\\.[^.]*$//'")).trim()
    let h1 = _guard_noname_v_match(stem)
    if h1 != "" {
        return "REJECT: " + file_path + " — 파일명 '" + base + "' 에 버전 suffix '" + h1 + "' 금지 (H-NONAME-V). git commit/branch/tag 로 버전관리. 우회: path 에 @allow-version-name 토큰"
    }
    let dirname = to_string(exec("dirname '" + file_path + "'")).trim()
    if dirname.len() > 0 && dirname != "." && dirname != "/" {
        let segs_raw = to_string(exec("echo '" + dirname + "' | tr '/' '\\n'"))
        let segs = segs_raw.split("\n")
        for seg in segs {
            let s = to_string(seg).trim()
            if s.len() == 0 { continue }
            if s == "." { continue }
            if s == ".." { continue }
            let h2 = _guard_noname_v_match(s)
            if h2 != "" {
                return "REJECT: " + file_path + " — 폴더명 '" + s + "' 에 버전 suffix '" + h2 + "' 금지 (H-NONAME-V). git commit/branch/tag 로 버전관리. 우회: path 에 @allow-version-name 토큰"
            }
        }
    }
    return ""
}

// H-NOHOOK: hook 파일·설정 신규 작성 금지 — 모든 자동 강제는 harness/entry.hexa 자율 호출로.
// 격리 예외: shared/archive/hooks-*, shared/archive/superseded-*, archive/deprecated_*,
//            .git/hooks/{commit-msg,pre-commit,post-commit,pre-push} + .githooks/{commit-msg,pre-commit} (H-COMMIT),
//            .git/hooks/*.sample (git default)
// 우회: NEXUS_HOOK_OK=1 prefix 또는 path 에 @allow-hook 토큰.
fn check_no_hook_file(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }
    if file_path.len() == 0 { return "" }
    if env("NEXUS_HOOK_OK") == "1" { return "" }
    if file_path.contains("@allow-hook") { return "" }
    if file_path.contains("shared/archive/") { return "" }
    if file_path.contains("/archive/superseded-") { return "" }
    if file_path.contains("/archive/deprecated_") { return "" }
    // 자기참조
    if file_path.contains("shared/harness/pre_tool_guard.hexa") { return "" }
    if file_path.contains("shared/harness/lint.hexa") { return "" }
    if file_path.contains("shared/harness/severity_map.json") { return "" }
    if file_path.contains("shared/harness/post_edit.hexa") { return "" }

    let base = to_string(exec("basename '" + file_path + "'")).trim()

    // 1) .git/hooks/*  — sample 통과, H-COMMIT 4종 통과, 그 외 신규 차단
    if file_path.contains("/.git/hooks/") {
        if base.ends_with(".sample") { return "" }
        let h_commit_allowed = (base == "commit-msg" || base == "pre-commit" || base == "post-commit" || base == "pre-push")
        if h_commit_allowed { return "" }
        return "REJECT: " + file_path + " — .git/hooks/ 신규 hook 작성 금지 (H-NOHOOK). harness/entry.hexa 자율 호출로 통합. 허용: commit-msg/pre-commit/post-commit/pre-push (H-COMMIT). 우회: NEXUS_HOOK_OK=1"
    }

    // 2) .githooks/* — H-COMMIT wrapper 외 신규 차단
    if file_path.contains("/.githooks/") {
        let h_commit_allowed = (base == "commit-msg" || base == "pre-commit")
        if h_commit_allowed { return "" }
        return "REJECT: " + file_path + " — .githooks/ 신규 hook wrapper 금지 (H-NOHOOK). H-COMMIT 외 추가 wrapper 불가. 우회: NEXUS_HOOK_OK=1"
    }

    // 3) .claude/hooks/* — Claude Code hook script 신규 작성 차단
    if file_path.contains("/.claude/hooks/") {
        return "REJECT: " + file_path + " — .claude/hooks/ 스크립트 신규 작성 금지 (H-NOHOOK). 모든 자동 행동은 harness/entry.hexa 호출로. 우회: NEXUS_HOOK_OK=1"
    }

    // 4) shared/hooks/ — symlink 격리 (deprecated). 신규 .hexa/.sh/.py/.json 차단
    if file_path.contains("/shared/hooks/") {
        return "REJECT: " + file_path + " — shared/hooks/ deprecated (H-NOHOOK). shared/harness/ 사용. 우회: NEXUS_HOOK_OK=1"
    }

    return ""
}

// L0: lockdown_gate watch 위임. BLOCK=L0, WARN=L1, ALLOW=L2/NONE.
// L0 차단 우회는 사용자 직접 lockdown.json 수정으로만.
fn check_lockdown_tier(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }
    if file_path.len() == 0 { return "" }
    let h = env("HOME")
    let hexa = h + "/Dev/hexa-lang/hexa"
    let gate = h + "/Dev/nexus/shared/harness/lockdown_gate.hexa"
    let result = to_string(exec(hexa + " " + gate + " watch '" + file_path + "' 2>/dev/null")).trim()
    if result.starts_with("BLOCK") {
        return "REJECT: " + file_path + " — L0 보호 파일 (lockdown_gate watch). 사용자 명시 승인 필요"
    }
    return ""
}

// H-SESSION-LOCK: 파일 area 기반 advisory lock — 다중 세션 동시 편집 race 방지.
// WARN-only (exit 미전파 제약 + 기존 워크플로우 보존). 우회: NEXUS_LOCK_OK=1
fn check_session_lock(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }
    if file_path.len() == 0 { return "" }
    if env("NEXUS_LOCK_OK") == "1" { return "" }
    let h = env("HOME")
    let HEXA_BIN = h + "/Dev/nexus/shared/bin/hexa"
    let LOCK = h + "/Dev/nexus/shared/harness/session_lock.hexa"
    let area = to_string(exec(HEXA_BIN + " run " + LOCK + " derive '" + file_path + "' 2>/dev/null")).trim()
    if area == "" || area == "misc" { return "" }
    let out = to_string(exec(HEXA_BIN + " run " + LOCK + " acquire '" + area + "' 600 2>&1")).trim()
    if out.contains("BLOCK") {
        eprintln("[H-SESSION-LOCK WARN] " + out)
    }
    return ""
}

// ═══════════════════════════════════════════════════════════
// [ANNOT-RULES] — annot_rules.json 소비 (H-ANNOT-RULES, 2026-04-16)
// SSOT: shared/config/annot_rules.json (kind=name forbid[], kind=enforce pattern)
// 우회: NEXUS_ANNOT_OK=1 (사용자 수동 override)
// 본 함수는 기존 가드 로직을 건드리지 않는 add-on — 매치 시 REJECT 반환.
// stdin JSON 분기 (check_annot_rules_stdin) 은 dispatcher/main 전용으로 본 inc 에서 제외.
// ═══════════════════════════════════════════════════════════

// annot_rules.json → 토큰 리스트 (탭 구분).
// name 룰 forbid[] 은 @* 패턴 하에 있으므로 '@' prefix 붙여 `@train` 형태로 확장.
// enforce 룰 pattern 은 'a|b' 형태 그대로 (split 은 scan 단계).
// jq 우선, grep fallback. 실패 시 빈 문자열.
fn _annot_load_forbids() -> str {
    let h = env("HOME")
    let rules = h + "/Dev/nexus/shared/config/annot_rules.json"
    let exists = to_string(exec("test -f '" + rules + "' && echo y || echo n")).trim()  // @allow-bare-exec
    if exists != "y" { return "" }

    // jq 있으면: (1) name 룰 forbid — pattern이 @* 이면 '@' prefix 붙이고, 한국어는 그대로.
    //           (2) enforce 룰 pattern — 원본 ('@train*|훈련' 형태).
    let jq_ok = to_string(exec("command -v jq >/dev/null 2>&1 && echo y || echo n")).trim()  // @allow-bare-exec
    if jq_ok == "y" {
        let cmd = "jq -r '" +
                  "[ .rules[] | select(.kind==\"name\") | .pattern as $pat | .forbid[]? | " +
                  "   if ($pat == \"@*\" and (test(\"^[A-Za-z_]\") )) then (\"@\" + .) else . end ] + " +
                  "[ .rules[] | select(.kind==\"enforce\") | .pattern ] | unique | @tsv" +
                  "' '" + rules + "' 2>/dev/null"
        let out = to_string(exec(cmd)).trim()  // @allow-bare-exec
        if out.len() > 0 { return out }
    }

    // fallback: grep 로 대략 추출 — @ prefix 복원 불가능하므로 bare 토큰만.
    // (jq 없을 때는 enforce pattern '@train*' 와 bare forbid '훈련'/'cargo' 에만 의존)
    let gcmd = "grep -oE '\"(forbid|pattern)\":[[:space:]]*\\[?[^\\]]*' '" + rules + "' 2>/dev/null | " +
               "grep -oE '\"[^\"]+\"' | sed 's/^\"//;s/\"$//' | " +
               "grep -v -E '^(forbid|pattern)$' | sort -u | tr '\\n' '\\t'"
    let out2 = to_string(exec(gcmd)).trim()  // @allow-bare-exec
    return out2
}

// content 에서 annot_rules 금지 토큰 매치 스캔. 매치 시 "H-XXX — <token>" 반환, 없으면 ""
fn _annot_scan_content(content: str) -> str {
    if content.len() == 0 { return "" }
    let forbids_tsv = _annot_load_forbids()
    if forbids_tsv.len() == 0 { return "" }

    let toks = forbids_tsv.split("\t")
    for t_raw in toks {
        let t = to_string(t_raw).trim()
        if t.len() == 0 { continue }

        // enforce pattern 은 "a|b|c" 형태 — | 로 split. bare 토큰도 배열에 섞여 있으므로 동일 loop.
        let parts = t.split("|")
        for p_raw in parts {
            let p_star = to_string(p_raw).trim()
            if p_star.len() == 0 { continue }

            // "@train*" → "@train" prefix 매치
            let mut needle = p_star
            let is_glob = needle.ends_with("*")
            if is_glob { needle = needle.substring(0, needle.len() - 1) }
            if needle.len() == 0 { continue }

            // 금지 토큰 매치 — needle 에 '@' 포함(annotation) 또는 한국어('훈련') 만 검사.
            // bare ASCII 단어 (train/rust/cargo/trainer/training/rust_ext) 는 코멘트 오탐 회피를 위해 skip.
            // jq branch 에서 '@' prefix 자동으로 붙기 때문에, 여기 bare ASCII 는 보통 enforce pattern 의 |-split 결과.
            let has_at = needle.starts_with("@")
            let has_non_ascii = (needle == "훈련")
            if has_at == false && has_non_ascii == false { continue }

            if content.contains(needle) {
                // id 추정 — @train*/훈련 → H-NO-TRAIN, @rust*/@cargo → H-NO-RUST, 그 외 → annot
                let mut id = "annot"
                if needle.contains("train") || needle == "훈련" { id = "H-NO-TRAIN" }
                else if needle.contains("rust") || needle.contains("cargo") { id = "H-NO-RUST" }
                return id + " — " + needle
            }
        }
    }
    return ""
}

// Write/Edit 시 파일 content annot_rules 검사 (SSOT shared/config/annot_rules.json)
// file_path 가 존재하면 디스크 content 를 읽고, 없으면 skip (stdin JSON mode 에서 content 주입).
fn check_annot_rules(tool: str, file_path: str) -> str {
    if tool != "Write" && tool != "Edit" { return "" }
    if env("NEXUS_ANNOT_OK") == "1" { return "" }
    if file_path.len() == 0 { return "" }
    if file_path.contains("@allow-annot") { return "" }
    // 자기참조 — annot_rules.json 자체 및 본 guard 는 제외
    if file_path.contains("/shared/config/annot_rules.json") { return "" }
    if file_path.contains("/shared/harness/pre_tool_guard.hexa") { return "" }
    if file_path.contains("/shared/harness/lint_annot.hexa") { return "" }
    if file_path.contains("/shared/archive/") { return "" }

    let exists = to_string(exec("test -f '" + file_path + "' && echo y || echo n")).trim()  // @allow-bare-exec
    if exists != "y" { return "" }
    let content = to_string(exec("cat '" + file_path + "' 2>/dev/null"))  // @allow-bare-exec
    let hit = _annot_scan_content(content)
    if hit.len() == 0 { return "" }
    return "REJECT: " + file_path + " — annot_rule: " + hit + " (H-ANNOT-RULES, shared/config/annot_rules.json). 우회: NEXUS_ANNOT_OK=1 prefix 또는 경로에 @allow-annot 토큰"
}
