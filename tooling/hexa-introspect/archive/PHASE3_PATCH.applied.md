> **APPLIED**: 2026-05-06 — Phase 3 (`--refs` / `--hover`) hunks merged into
> `tooling/hexa-introspect/hexa_introspect.hexa` (1733 lines post-merge) and
> `bin/hexa-introspect` mode whitelist. Validated: `--refs`, `--hover` 모드
> NDJSON / JSON 출력 정상. **base count**: introspect dispatch 3-mode
> (`--ast`/`--symbols`/`--check`) → 5-mode (+`--refs`/`--hover`). Spec
> § 6.1 LSP 효과 60→70%.

# hexa-introspect Phase 3 — 적용 가능 patch 묶음 (2026-05-06)

본 patch 는 **Phase 2 (`--check`) 가 머지된 직후** `hexa_introspect.hexa` 와
`bin/hexa-introspect` 에 적용한다. Phase 2 와 충돌 회피를 위해 분기 추가
구간만 한정하며, 전역 함수 추가는 **파일 끝**(decls_to_symbols 다음, _usage
직전)에 모은다. 모든 hunk 는 unified-diff 풍 의사-패치 — 줄 번호는 Phase 2
머지 후 ±몇 줄 흔들릴 수 있어, 각 hunk 의 anchor 토큰을 명시한다.

## 0. 전제

- Phase 2 머지 시점의 `hexa_introspect.hexa` 가 dispatch 부분에서
  `mode == "--ast" / "--symbols" / "--check"` 3분기를 처리한다고 가정.
- 본 patch 는 이를 5분기 (`--refs`, `--hover` 추가) 로 확장하고,
  scanner 헬퍼 (`_is_alpha`, `_is_ident_part`, `_build_line_starts`,
  `_off_line`, `_off_col`, `_kw_to_kind`) 를 그대로 재사용한다.

---

## 1. Hunk A — 신규 헬퍼 추가

**Anchor**: `fn decls_to_symbols` 의 닫는 `}` 직후, `// ─── usage / entry ───`
직전.

```hexa
// ─── Phase 3: decl-keyword sniffing ────────────────────────
fn _is_decl_kw(w: string) -> bool {
    if w == "pub" { return true }
    return _kw_to_kind(w) != ""
}

// 토큰 직전의 (공백/개행 무시) 가장 가까운 식별자가 decl 키워드인지 검사.
// `target_start` 는 식별자 토큰의 시작 offset.
fn _prev_word_is_decl_kw(src: string, target_start: i64) -> bool {
    let mut k = target_start - 1
    // skip whitespace + newline
    while k > -1 {
        let c = src.substring(k, k + 1)
        if c == " " || c == "\t" || c == "\r" || c == "\n" { k = k - 1 }
        else { break }
    }
    if k < 0 { return false }
    // identifier characters backward
    let mut e = k + 1
    let mut s = k
    while s > -1 {
        let c = src.substring(s, s + 1)
        if _is_ident_part(c) { s = s - 1 }
        else { break }
    }
    let word = src.substring(s + 1, e)
    return _is_decl_kw(word)
}

// 토큰 종료 직후 첫 비공백/비개행 글자.
fn _next_non_ws_char(src: string, after: i64) -> string {
    let n = src.len()
    let mut k = after
    while k < n {
        let c = src.substring(k, k + 1)
        if c == " " || c == "\t" || c == "\r" { k = k + 1 }
        else { return c }
    }
    return ""
}

// 라인 텍스트 추출 (1-based line, no trailing \n).
fn _line_text(src: string, line_starts: [i64], line: i64) -> string {
    let nl = len(line_starts)
    if line < 1 { return "" }
    if line + 1 > nl - 1 {
        // 마지막 라인 (sentinel 없음): line_starts[line] .. EOF
        return src.substring(line_starts[line], src.len())
    }
    let s = line_starts[line]
    let e = line_starts[line + 1] - 1   // \n 제외
    if e < s { return "" }
    return src.substring(s, e)
}

// ─── Phase 3: scan_refs ────────────────────────────────────
//
// scan_decls 와 동일한 state machine — string/comment/brace 가드 동일.
// 차이: target 식별자 토큰이 등장할 때마다 누적 + decl|call|reference 분류.
fn scan_refs(src: string, target: string) -> [string] {
    let mut refs: [string] = []
    let n = src.len()
    let line_starts = _build_line_starts(src)

    let mut line: i64 = 1
    let mut col: i64 = 1
    let mut i: i64 = 0
    let mut brace_depth: i64 = 0
    let mut block_cmt: i64 = 0
    let mut in_line_cmt: bool = false
    let mut in_str: bool = false
    let mut str_delim: string = ""

    while i < n {
        let c = src.substring(i, i + 1)
        let c2 = if i + 1 < n { src.substring(i + 1, i + 2) } else { "" }

        if c == "\n" {
            if in_line_cmt { in_line_cmt = false }
            line = line + 1; col = 1; i = i + 1; continue
        }
        if block_cmt > 0 {
            if c == "*" && c2 == "/" { block_cmt = block_cmt - 1; i = i + 2; col = col + 2; continue }
            if c == "/" && c2 == "*" { block_cmt = block_cmt + 1; i = i + 2; col = col + 2; continue }
            i = i + 1; col = col + 1; continue
        }
        if in_line_cmt { i = i + 1; col = col + 1; continue }
        if in_str {
            if c == "\\" && i + 1 < n { i = i + 2; col = col + 2; continue }
            if c == str_delim { in_str = false; str_delim = "" }
            i = i + 1; col = col + 1; continue
        }
        if c == "\"" { in_str = true; str_delim = "\""; i = i + 1; col = col + 1; continue }
        if c == "/" && c2 == "/" {
            in_line_cmt = true
            // skip ahead to newline (newline branch resets)
            let mut j = i + 2
            while j < n && src.substring(j, j + 1) != "\n" { j = j + 1 }
            col = col + (j - i); i = j; continue
        }
        if c == "/" && c2 == "*" { block_cmt = 1; i = i + 2; col = col + 2; continue }
        if c == "{" { brace_depth = brace_depth + 1; i = i + 1; col = col + 1; continue }
        if c == "}" {
            brace_depth = brace_depth - 1
            if brace_depth < 0 { brace_depth = 0 }
            i = i + 1; col = col + 1; continue
        }

        if _is_alpha(c) {
            let tok_start = i
            let tok_line = line
            let tok_col = col
            let mut j = i
            while j < n && _is_ident_part(src.substring(j, j + 1)) { j = j + 1 }
            let word = src.substring(tok_start, j)

            if word == target {
                // 분류
                let mut kind = "reference"
                let prev_decl = _prev_word_is_decl_kw(src, tok_start)
                if prev_decl && brace_depth == 0 { kind = "decl" }
                else {
                    let nxt = _next_non_ws_char(src, j)
                    if nxt == "(" { kind = "call" }
                }
                let end_col = tok_col + (j - tok_start)
                let ctx = _line_text(src, line_starts, tok_line).trim()
                let rec = #{
                    "name": word,
                    "line": tok_line,
                    "col": tok_col,
                    "end_line": tok_line,
                    "end_col": end_col,
                    "kind": kind,
                    "context": ctx
                }
                refs.push(rec)
            }

            col = col + (j - tok_start); i = j; continue
        }

        i = i + 1; col = col + 1
    }
    return refs
}

// ─── Phase 3: refs → NDJSON ────────────────────────────────
fn refs_to_ndjson(file: string, refs: [string]) -> string {
    let mut sb: [string] = []
    let mut i = 0
    while i < refs.len() {
        let r = refs[i]
        sb.push("{\"name\":\"")
        sb.push(_json_escape(to_string(r.name)))
        sb.push("\",\"loc\":{\"line\":")
        sb.push(to_string(r.line))
        sb.push(",\"col\":")
        sb.push(to_string(r.col))
        sb.push("},\"end_loc\":{\"line\":")
        sb.push(to_string(r.end_line))
        sb.push(",\"col\":")
        sb.push(to_string(r.end_col))
        sb.push("},\"kind\":\"")
        sb.push(_json_escape(to_string(r.kind)))
        sb.push("\",\"context\":\"")
        sb.push(_json_escape(to_string(r.context)))
        sb.push("\",\"file\":\"")
        sb.push(_json_escape(file))
        sb.push("\"}\n")
        i = i + 1
    }
    return sb.join("")
}

// ─── Phase 3: pick_token_at (line:col → identifier) ────────
//
// 반환: #{ name, start_line, start_col, end_line, end_col } 또는 빈 record.
// "빈 토큰" 표시: name == ""
fn pick_token_at(src: string, line_starts: [i64], line: i64, col: i64) -> string {
    let empty = #{ "name": "", "start_line": 0, "start_col": 0, "end_line": 0, "end_col": 0 }
    let nl = len(line_starts)
    if line < 1 || line + 1 > nl - 1 && line != nl - 1 {
        // out-of-range
        if line + 1 > nl - 1 && line != nl - 1 { return empty }
    }
    let row = _line_text(src, line_starts, line)
    let rn = row.len()
    if col < 1 || col > rn { return empty }
    // col 은 1-based — index = col - 1
    let mut s = col - 1
    // 만약 col 위치 char 가 식별자 아니면 좌우로 한 칸씩 시도
    let here = row.substring(s, s + 1)
    if _is_ident_part(here) == false {
        // 좌측 한 글자 백오프 (예: "fn _ns_now()" 의 "(" 위치 → "_ns_now" 끝과 인접)
        if s > 0 && _is_ident_part(row.substring(s - 1, s)) { s = s - 1 }
        else { return empty }
    }
    // 좌측 확장
    let mut a = s
    while a > 0 && _is_ident_part(row.substring(a - 1, a)) { a = a - 1 }
    // 우측 확장
    let mut b = s + 1
    while b < rn && _is_ident_part(row.substring(b, b + 1)) { b = b + 1 }
    let name = row.substring(a, b)
    if name.len() < 1 { return empty }
    // 식별자가 숫자로 시작하면 토큰 아님
    if _is_digit(name.substring(0, 1)) { return empty }
    let rec = #{
        "name": name,
        "start_line": line, "start_col": a + 1,
        "end_line": line,   "end_col": b + 1
    }
    return rec
}

// ─── Phase 3: hover JSON ───────────────────────────────────
fn hover_to_json(file: string, decl: string) -> string {
    // decl 은 scan_decls 의 record (또는 빈 record — name == "")
    let nm = to_string(decl.name)
    if nm.len() < 1 { return "{}" }
    let mut sb: [string] = []
    sb.push("{\"name\":\"")
    sb.push(_json_escape(nm))
    sb.push("\",\"kind\":\"")
    sb.push(_json_escape(_kind_to_sym(to_string(decl.kind))))
    sb.push("\",\"sig\":")
    let g = to_string(decl.sig)
    if g.len() > 0 { sb.push("\""); sb.push(_json_escape(g)); sb.push("\"") } else { sb.push("null") }
    sb.push(",\"type\":")
    let t = to_string(decl.typ)
    if t.len() > 0 { sb.push("\""); sb.push(_json_escape(t)); sb.push("\"") } else { sb.push("null") }
    sb.push(",\"loc\":{\"line\":")
    sb.push(to_string(decl.start_line))
    sb.push(",\"col\":")
    sb.push(to_string(decl.start_col))
    sb.push("},\"end_loc\":{\"line\":")
    sb.push(to_string(decl.end_line))
    sb.push(",\"col\":")
    sb.push(to_string(decl.end_col))
    sb.push("},\"visibility\":\"")
    sb.push(_json_escape(to_string(decl.visibility)))
    sb.push("\",\"doc\":")
    let dd = to_string(decl.doc)
    if dd.len() > 0 { sb.push("\""); sb.push(_json_escape(dd)); sb.push("\"") } else { sb.push("null") }
    sb.push(",\"file\":\"")
    sb.push(_json_escape(file))
    sb.push("\"}")
    return sb.join("")
}
```

---

## 2. Hunk B — `_usage` 갱신

**Anchor**: `fn _usage()` 의 본문.

```diff
 fn _usage() {
     eprintln("usage: hexa run tooling/hexa-introspect/hexa_introspect.hexa <mode> <file.hexa>")
     eprintln("modes:")
     eprintln("  --ast       emit Program AST JSON (Phase 1 spec § 2.1)")
     eprintln("  --symbols   emit Symbol array JSON (Phase 1 spec § 2.2)")
-    eprintln("  --check     emit NDJSON diagnostics (Phase 2 spec § 2.3)")
+    eprintln("  --check     emit NDJSON diagnostics (Phase 2 spec § 2.3)")
+    eprintln("  --refs <file.hexa> <symbol>          emit NDJSON refs (Phase 3 spec § 2.4)")
+    eprintln("  --hover <file.hexa> <line>:<col>     emit single hover JSON (Phase 3 spec § 2.5)")
     eprintln("exit: 0=ok, 1=invalid-args, 2=file-unreadable")
 }
```
(Phase 2 가 `--check` 줄을 추가했다고 가정. 추가 안 됐으면 `--check` 줄도 같이.)

---

## 3. Hunk C — dispatch 분기 확장

**Anchor**: `if mode != "--ast" && mode != "--symbols"` 검증 + 모드 실행 블록.

```diff
-if mode != "--ast" && mode != "--symbols" {
+if mode != "--ast" && mode != "--symbols" && mode != "--check"
+    && mode != "--refs" && mode != "--hover" {
     _usage()
     exit(1)  // @allow-silent-exit
 }
```

dispatch 끝부분 (현재 `if mode == "--ast" { ... } else { ... }` 자리):

```hexa
let t0 = _ns_now()
let decls = scan_decls(src)
let t1 = _ns_now()
let ms = (t1 - t0) / 1000000

if mode == "--ast" {
    println(decls_to_ast(file, decls))
    _emit_meta("complete", ms, decls.len(), file)
} else if mode == "--symbols" {
    println(decls_to_symbols(file, decls))
    _emit_meta("complete", ms, decls.len(), file)
} else if mode == "--check" {
    // (Phase 2 의 출력 로직)
    println(decls_to_check(file, src, decls))
    _emit_meta("complete", ms, decls.len(), file)
} else if mode == "--refs" {
    if len(a) < 5 {
        eprintln("hexa-introspect: --refs requires <symbol>"); _usage(); exit(1)  // @allow-silent-exit
    }
    let target = a[4]
    let refs = scan_refs(src, target)
    let t2 = _ns_now()
    let out = refs_to_ndjson(file, refs)
    if out.len() > 0 { print(out) }   // NDJSON: trailing \n included per line
    _emit_meta("refs", (t2 - t0) / 1000000, refs.len(), file)
} else if mode == "--hover" {
    if len(a) < 5 {
        eprintln("hexa-introspect: --hover requires <line>:<col>"); _usage(); exit(1)  // @allow-silent-exit
    }
    let lc = a[4]
    let parts = lc.split(":")
    if parts.len() < 2 {
        eprintln("hexa-introspect: --hover expects <line>:<col>"); _usage(); exit(1)  // @allow-silent-exit
    }
    let mut hl: i64 = 0
    let mut hc: i64 = 0
    try { hl = to_int(parts[0]) } catch e {}  // @allow-silent-catch
    try { hc = to_int(parts[1]) } catch e2 {}  // @allow-silent-catch
    let line_starts = _build_line_starts(src)
    let tok = pick_token_at(src, line_starts, hl, hc)
    let mut hit = #{ "name":"", "kind":"", "start_line":0, "start_col":0,
                     "end_line":0, "end_col":0, "typ":"", "sig":"",
                     "visibility":"priv", "doc":"" }
    if to_string(tok.name).len() > 0 {
        let mut k = 0
        while k < decls.len() {
            if to_string(decls[k].name) == to_string(tok.name) { hit = decls[k]; break }
            k = k + 1
        }
    }
    println(hover_to_json(file, hit))
    _emit_meta("hover", (_ns_now() - t0) / 1000000,
        if to_string(hit.name).len() > 0 { 1 } else { 0 }, file)
}
```

> Note: 기존 `_emit_meta("complete", ...)` 가 trailing 위치에 1회 호출되던 구조였다면,
> 본 분기 확장으로 각 모드 내부에서 호출하도록 옮긴다 (Phase 2 가 이미 그렇게 했을
> 가능성 큼 — 충돌 시 Phase 2 의 자리 그대로).

---

## 4. Hunk D — `bin/hexa-introspect` 모드 화이트리스트 확장

**Anchor**: `case "${1}" in --ast|--symbols) ;; *) _usage; exit 1 ;; esac`

```diff
 case "${1}" in
-  --ast|--symbols) ;;
+  --ast|--symbols|--check|--refs|--hover) ;;
   *) _usage; exit 1 ;;
 esac
```

추가로 `_usage()` 의 modes 섹션에 두 줄 추가:

```diff
 modes:
   --ast       emit Program AST JSON (Phase 1 spec § 2.1)
   --symbols   emit Symbol array JSON (Phase 1 spec § 2.2)
+  --check     emit NDJSON diagnostics (Phase 2 spec § 2.3)
+  --refs <file.hexa> <symbol>          emit NDJSON refs (Phase 3 § 2.4)
+  --hover <file.hexa> <line>:<col>     emit single hover JSON (Phase 3 § 2.5)
 exit: 0=ok, 1=invalid-args, 2=file-unreadable
```

또한 인자 개수 가드 갱신 — `--refs` / `--hover` 는 3개 인자 필요:

```diff
-if [ $# -lt 2 ]; then _usage; exit 1; fi
+# --refs/--hover 는 mode + file + token 의 3개 위치 인자 필요
+min_argc=2
+case "${1:-}" in
+  --refs|--hover) min_argc=3 ;;
+esac
+if [ $# -lt "$min_argc" ]; then _usage; exit 1; fi
```

---

## 5. 적용 후 검증 (수용 기준)

```bash
# build/exec layer 가 캐시 안 끼게 PATH 설정
export PATH="/Users/ghost/core/nexus/tooling/hexa-introspect/bin:$PATH"
LP=mk2_hexa/mk2/src/atlas/lookup.hexa

# refs — _ns_now: decl=1 (line 26), call=2 (line 279, 368)
hexa-introspect --refs "$LP" _ns_now \
  | jq -c '{l:.loc.line,k:.kind}'
# 기대:
#   {"l":26,"k":"decl"}
#   {"l":279,"k":"call"}
#   {"l":368,"k":"call"}

# hover — fn 정의 라인
hexa-introspect --hover "$LP" 26:1 \
  | jq '{name,kind,sig}'
# 기대:
#   {"name":"_ns_now","kind":"fn","sig":"fn _ns_now() -> i64"}

# hover — 빈 위치
hexa-introspect --hover "$LP" 999:1
# 기대: {}  (exit 0)

# hover — 호출 사이트 위치 (line 279 col 13 = "_ns_now()" 의 _ns_now 토큰)
hexa-introspect --hover "$LP" 279:13 \
  | jq '{name,kind,sig}'
# 기대: 동일 (토큰명 → decl 표 lookup → fn _ns_now() -> i64)
```

회귀 테스트 (Phase 1/2):
```bash
hexa-introspect --symbols "$LP" | jq 'length'    # 기존과 동일
hexa-introspect --check   "$LP" | head -5         # Phase 2 그대로
```

---

## 6. 적용 순서 (Phase 2 머지 후 안전한 리니어)

1. `git pull` 후 Phase 2 로 갱신된 `hexa_introspect.hexa` 확인.
2. Hunk A 를 `decls_to_symbols` 다음에 paste.
3. Hunk B (usage 두 줄 추가).
4. Hunk C dispatch 확장 — Phase 2 가 만든 `--check` 분기 그대로 두고 뒤에 `--refs` /
   `--hover` 분기 append.
5. Hunk D `bin/hexa-introspect` 의 case + arg-count.
6. 검증 § 5 실행. 모두 통과 시 commit.
7. spec.md § 6 / § 10 갱신 — Phase 3 행, "70% → 80%".

## 7. 알려진 제약 / 후속

- `decl` 분류는 _prev_word_is_decl_kw 가 `pub` 만 한 단계 백트래킹 — `pub fn`
  까지만 인식. `@derive(...)` attribute 가 앞에 있으면 인식 못 함 (현재 atlas
  코드 베이스에 attribute 사용 거의 없음 — 운영상 OK). 추후 hexa attribute
  도입 시 `_prev_word_is_decl_kw` 를 토큰 backtrack loop 로 확장.
- `--hover` 가 동일 이름 동일 파일 다중 decl 인 경우 첫 매칭 사용 (예:
  trait method overload). 본 spec 단계에서 OK.
- `_off_line` / `_off_col` 가 `i + 1` overflow 검사 없음 — 30KB 파일 i64 범위
  내 안전. 큰 파일 (>2GB) 도입 시 별도 검토.
