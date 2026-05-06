# Phase 5c — `hexa_introspect.hexa` & `bin/hexa-introspect` dispatch patch

본 문서는 hexa-introspect Phase 5c (`gumtree.hexa`) 의 4 모드를 메인 wrapper
(`hexa_introspect.hexa`) 와 bin shim (`bin/hexa-introspect`) 에 통합하기 위한
**적용 대기 패치** 를 정의한다. 5a (`diff.hexa`) / 5b (`refactor.hexa`) 와
동일하게, 신규 entry-point 가 별도 파일이라 dispatch 통합은 Phase 3 mainline
머지 후 단일 PR 로 적용하는 게 안전하다.

## 1. 신규 mode (Phase 5c)

| mode | 인자 | delegate |
| --- | --- | --- |
| `--diff-tree` | `<a.hexa> <b.hexa>` | `tooling/hexa-introspect/gumtree.hexa --diff-tree …` |
| `--extract` | `<file.hexa> <sl> <el> <new_fn>` | `… --extract …` |
| `--inline` | `<file.hexa> <fn>` | `… --inline …` |
| `--move` | `<fn> <a.hexa> <b.hexa>` | `… --move …` |

## 2. `bin/hexa-introspect` 패치 (적용 대기)

```diff
@@ usage 블록
   --diff <a.hexa> <b.hexa>             emit symbol-table hash diff NDJSON (Phase 5a)
+  --diff-tree <a.hexa> <b.hexa>        emit GumTree tree-edit diff NDJSON (Phase 5c)
+  --extract <file.hexa> <sl> <el> <new_fn>  emit extract refactor plan (Phase 5c)
+  --inline <file.hexa> <fn>            emit inline refactor plan (Phase 5c)
+  --move <fn> <a.hexa> <b.hexa>        emit move refactor plan (Phase 5c)

@@ min_argc / case 블록
-case "${1:-}" in
-  --refs|--hover|--diff) min_argc=3 ;;
-esac
+case "${1:-}" in
+  --refs|--hover|--diff|--diff-tree|--inline) min_argc=3 ;;
+  --move) min_argc=4 ;;
+  --extract) min_argc=5 ;;
+esac

-case "${1}" in
-  --ast|--symbols|--check|--refs|--hover|--diff) ;;
-  *) _usage; exit 1 ;;
-esac
+case "${1}" in
+  --ast|--symbols|--check|--refs|--hover|--diff) ;;
+  --diff-tree|--extract|--inline|--move) ;;
+  *) _usage; exit 1 ;;
+esac
```

## 3. `hexa_introspect.hexa` dispatch 패치 (적용 대기)

```diff
@@ mode whitelist
-if mode != "--ast" && mode != "--symbols" && mode != "--check"
-    && mode != "--refs" && mode != "--hover" && mode != "--diff" {
+if mode != "--ast" && mode != "--symbols" && mode != "--check"
+    && mode != "--refs" && mode != "--hover" && mode != "--diff"
+    && mode != "--diff-tree" && mode != "--extract"
+    && mode != "--inline" && mode != "--move" {
     _usage()
     exit(1)  // @allow-silent-exit
 }

@@ existing --diff dispatch 후 추가
+// `--diff-tree` / `--extract` / `--inline` / `--move` dispatch — Phase 5c.
+// 알고리즘은 sibling `gumtree.hexa` 가 단독 보유 (5a/5b 분리 패턴 동일).
+if mode == "--diff-tree" || mode == "--extract"
+    || mode == "--inline" || mode == "--move" {
+    let mut gumtree_path = "tooling/hexa-introspect/gumtree.hexa"
+    let exists = to_string(exec("test -f '" + gumtree_path.replace("'", "'\\''")
+        + "' && printf yes || printf no")).trim()  // @allow-bare-exec
+    if exists != "yes" {
+        eprintln("hexa-introspect: gumtree.hexa not found at " + gumtree_path)
+        exit(2)  // @allow-silent-exit
+    }
+    // 인자 그대로 전달: a[2..len(a)] (mode 부터)
+    let hb = to_string(exec("printf '%s' \"${HEXA_BIN:-$HOME/.hx/bin/hexa}\"")).trim()  // @allow-bare-exec
+    let mut cmd_parts: [string] = []
+    cmd_parts.push("HEXA_LOCAL=1 HEXA_NO_SENTINEL=1 '" + hb.replace("'", "'\\''") + "'")
+    cmd_parts.push("run '" + gumtree_path.replace("'", "'\\''") + "'")
+    let mut ai = 2
+    while ai < len(a) {
+        cmd_parts.push("'" + a[ai].replace("'", "'\\''") + "'")
+        ai = ai + 1
+    }
+    let cmd = cmd_parts.join(" ")
+    let result = to_string(exec(cmd))  // @allow-bare-exec
+    print(result)
+    exit(0)  // @allow-silent-exit
+}
```

## 4. 적용 시점

- Phase 3 (`--refs`/`--hover`) PR 머지 후 dispatch 영역 변경이 안정화되면 본
  diff 를 단일 PR 로 적용. 적용 시 `_fixtures/sample_extract.hexa`,
  `_fixtures/sample_inline.hexa`, `_fixtures/sample_move_a.hexa`,
  `_fixtures/sample_move_b.hexa` 회귀 검증 (cold run < 5s).

## 5. 우회 호출 (현 시점)

dispatch 통합 전이라도 `hexa run` 직접 호출로 사용 가능:

```bash
hexa run tooling/hexa-introspect/gumtree.hexa --diff-tree a.hexa b.hexa
hexa run tooling/hexa-introspect/gumtree.hexa --extract file.hexa 8 10 compute_total
hexa run tooling/hexa-introspect/gumtree.hexa --inline file.hexa double
hexa run tooling/hexa-introspect/gumtree.hexa --move _safe_token a.hexa b.hexa
```

## 6. 안전 가드

- 모든 모드 stdout = NDJSON 만, 실제 파일 수정 없음 (plan emit 만).
- `apply` 적용은 spec § 8.3 (Phase 5b) `--apply --dry-run` 의 후속 — 본 5c 는
  설계 단계로 분리.
