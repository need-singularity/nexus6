> **APPLIED**: 2026-05-06 — Phase 5a `--diff` dispatch hunks merged into
> `tooling/hexa-introspect/hexa_introspect.hexa` (delegates to sibling
> `diff.hexa` via subprocess) and `bin/hexa-introspect` mode whitelist
> (added `--diff` token). Validated: `hexa-introspect --diff sample.hexa
> sample.hexa` → 7 unchanged; `--diff sample.hexa sample_rename.hexa` →
> 6 unchanged + 1 renamed (greet→hail body_hash_match) + 1 added
> (_clock_ns). **base count**: 5-mode → 6-mode dispatch (+`--diff`).
> Spec § 6.1 LSP 효과 70→80%.

# hexa-introspect Phase 5a — `--diff` Dispatch Patch (2026-05-06)

본 patch 는 **Phase 3 머지 직후** `hexa_introspect.hexa` 와 `bin/hexa-introspect`
에 적용한다. Phase 5a 의 `diff.hexa` 는 이미 독립 entry-point 로 작동하지만
(아래 § 4 참조), 사용자 친화 dispatch 를 위해 `hexa-introspect --diff a b`
형태로도 호출 가능하게 분기를 추가한다.

## 0. 전제

- Phase 3 머지 시점의 `hexa_introspect.hexa` 가 `--ast / --symbols / --check
  / --refs / --hover` 5분기 + (Phase 3 patch md 의 `_resolve_introspect_path`
  류 헬퍼) 를 보유.
- `tooling/hexa-introspect/diff.hexa` 는 **이미 작성/머지** 됨 (본 사이클).
- 본 patch 는 dispatch 분기에 1 hunk 추가 + bin shim mode whitelist 1줄
  추가.

---

## 1. Hunk A — `hexa_introspect.hexa` dispatch 에 `--diff` 분기

**Anchor**: `if mode != "--ast" && mode != "--symbols" && mode != "--check"`
조건 라인 (Phase 3 머지 후 mode 체크가 5분기로 확장된 그 자리).

```diff
- if mode != "--ast" && mode != "--symbols" && mode != "--check"
-     && mode != "--refs" && mode != "--hover" {
+ if mode != "--ast" && mode != "--symbols" && mode != "--check"
+     && mode != "--refs" && mode != "--hover" && mode != "--diff" {
      _usage()
      exit(1)  // @allow-silent-exit
  }
```

**Anchor**: dispatch 본체에서 `if mode == "--check" { ... } exit(0)` 분기 직전
(또는 `--refs / --hover` 분기 옆).

```hexa
if mode == "--diff" {
    // --diff 는 두 인자 (a.hexa, b.hexa) 를 받음. diff.hexa 를 sub-process
    // 로 위임 — 본 wrapper 는 dispatch 만, 알고리즘은 diff.hexa SSOT.
    if len(a) < 5 {
        _usage()
        exit(1)  // @allow-silent-exit
    }
    let a_path = a[3]
    let b_path = a[4]
    // self_dir 추정: 본 hexa_introspect.hexa 의 sibling 으로 diff.hexa 가
    // 있다고 가정 (둘 다 tooling/hexa-introspect/ 안). cwd 가 nexus root 면
    // 그 경로로, 아니면 git toplevel 검색.
    let mut diff_path = "tooling/hexa-introspect/diff.hexa"
    let exists = to_string(exec("test -f '" + diff_path.replace("'", "'\\''")
        + "' && printf yes || printf no")).trim()  // @allow-bare-exec
    if exists != "yes" {
        let top = to_string(exec("git rev-parse --show-toplevel 2>/dev/null")).trim()  // @allow-bare-exec
        if top.len() > 0 { diff_path = top + "/tooling/hexa-introspect/diff.hexa" }
    }
    let hb = to_string(exec("printf '%s' \"${HEXA_BIN:-$HOME/.hx/bin/hexa}\"")).trim()  // @allow-bare-exec
    let cmd = "HEXA_LOCAL=1 HEXA_NO_SENTINEL=1 '"
        + hb.replace("'", "'\\''") + "' run '"
        + diff_path.replace("'", "'\\''") + "' --diff '"
        + a_path.replace("'", "'\\''") + "' '"
        + b_path.replace("'", "'\\''") + "'; echo \"__RC=$?\""
    let out = to_string(exec(cmd))  // @allow-bare-exec
    let rc_at = out.index_of("__RC=")
    let mut rc: i64 = 1
    if rc_at > -1 {
        let tail = out.substring(rc_at + 5, out.len()).trim()
        try { rc = to_int(tail) } catch e {}  // @allow-silent-catch
    }
    let payload = if rc_at > -1 { out.substring(0, rc_at) } else { out }
    print(payload)
    exit(rc)  // @allow-silent-exit
}
```

**hunk 1줄 요약 (Phase 3 머지 dispatch 가 elseif 체인이라면)**:
```diff
+ } else if mode == "--diff" { /* delegate to diff.hexa via subprocess; see § 1 */ }
```

---

## 2. Hunk B — `_usage()` 갱신

```diff
  eprintln("modes:")
  eprintln("  --ast               emit Program AST JSON (Phase 1 spec § 2.1)")
  eprintln("  --symbols           emit Symbol array JSON (Phase 1 spec § 2.2)")
  eprintln("  --check             emit lint NDJSON (Phase 2 spec § 2.3, 6 rules)")
  eprintln("  --check --strict    same, exit 1 if any violation")
  eprintln("  --refs <id>         emit reference NDJSON (Phase 3)")
  eprintln("  --hover <line:col>  emit hover JSON (Phase 3)")
+ eprintln("  --diff <a.hexa> <b.hexa>")
+ eprintln("                      emit symbol-table hash diff NDJSON")
+ eprintln("                      (Phase 5a spec § 3.2; delegates to diff.hexa)")
```

---

## 3. Hunk C — `bin/hexa-introspect` mode whitelist 갱신

**Anchor**: `case "${1}" in` 의 mode list.

```diff
  case "${1}" in
-   --ast|--symbols|--check) ;;
+   --ast|--symbols|--check|--refs|--hover|--diff) ;;
    *) _usage; exit 1 ;;
  esac
```

`--refs / --hover` 는 Phase 3 patch 에서 추가됨 — 본 patch 는 추가로 `--diff`
만 1 토큰 더한다.

추가로 `_usage()` heredoc 의 modes 목록에 다음 1줄:

```diff
   --refs <id>         emit reference NDJSON (Phase 3 spec § 2.4)
   --hover <line:col>  emit hover JSON (Phase 3 spec § 2.5)
+  --diff <a.hexa> <b.hexa>  emit symbol-table hash diff NDJSON (Phase 5a)
```

---

## 4. 머지 전 임시 사용 (Phase 3 미머지 / Phase 5a 단독)

Phase 3 patch 가 아직 머지되지 않았다면 본 dispatch hunk 는 보류하고,
diff.hexa 를 **직접** 호출한다 (현재 가용 SSOT 경로):

```sh
hexa run tooling/hexa-introspect/diff.hexa --diff a.hexa b.hexa
```

또는 `NEXUS_HEXA_INTROSPECT_PATH` 환경변수로 hexa_introspect.hexa 위치를
명시적으로 지정 가능.

bin shim 갱신 후에는 다음과 같이 호출:

```sh
hexa-introspect --diff a.hexa b.hexa
```

---

## 5. 검증 (머지 후)

```sh
# 1. 동일 파일 (모두 unchanged)
hexa-introspect --diff tooling/hexa-introspect/_fixtures/sample.hexa \
                       tooling/hexa-introspect/_fixtures/sample.hexa
# expected: 7 unchanged, exit 0

# 2. rename fixture (greet -> hail, _clock_ns 추가)
hexa-introspect --diff tooling/hexa-introspect/_fixtures/sample.hexa \
                       tooling/hexa-introspect/_fixtures/sample_rename.hexa
# expected: 6 unchanged + 1 renamed (greet→hail, body_hash_match) + 1 added (_clock_ns)

# 3. atlas 모듈 비교 (~30+ changes 가 보통)
hexa-introspect --diff mk2_hexa/mk2/src/atlas/lookup.hexa \
                       mk2_hexa/mk2/src/atlas/recall.hexa
# expected: removed/added/body_changed 혼합, exit 0
```

---

## 6. 후속 (Phase 5b — 본 patch 외 영역)

- `--diff-rename <old> <new> <file>` (Phase 3 `--refs` 활용)
- `--diff-sig <fn> <a> <b>` (sig 변경 + caller 영향 분석)
- `--apply` / `--emit-edit --format=lsp` (WorkspaceEdit emit, LSP rename
  핸들러 호환)
- 디렉토리 모드 (`--diff <olddir>/ <newdir>/`)

상세는 `design/hexa_ast_diff_refactor_spec.md` § 4.2, § 8.
