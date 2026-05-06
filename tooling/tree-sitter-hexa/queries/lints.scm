; tree-sitter-hexa — lints.scm
; SSOT for structural lint queries. Consumed by `nexus check` (or any
; tree-sitter-aware lint runner) to flag hexa idioms that violate project
; convention. Each rule has a stable capture name on the form
; `@error.<rule-id>` so downstream tooling can group / suppress per rule.
;
; Rules
; ─────
; relop-banned        `>=` / `<=` are forbidden in hexa source
;                     (use `> a - 1` / `< a + 1` or refactor).
; bare-exec           `exec(...)` without an `// @allow-bare-exec`
;                     trailing comment is forbidden.
; silent-catch        `catch e { }` (empty catch body) without
;                     `// @allow-silent-catch` swallows errors silently.
; silent-exit         `exit(...)` without `// @allow-silent-exit` skips
;                     the central exit-handler.
; nested-call-exec    `exec` invoked inside another call expression
;                     (e.g. `to_int(exec(...))`) — surface for review.
;
; Suppression: append the matching `// @allow-<rule>` comment to the
; offending line. The grammar already captures these as `@comment.note`
; in `highlights.scm`; the lint runner is expected to pair the comment
; line/column with the diagnostic before emitting it.

; ── relop-banned ──────────────────────────────────────────────
; `>=` and `<=` binary operators.
(binary_expression
  operator: ">="
) @error.relop-banned

(binary_expression
  operator: "<="
) @error.relop-banned

; ── bare-exec ─────────────────────────────────────────────────
; Any direct call to a function named `exec`. The lint runner pairs the
; capture row with the trailing line_comment to decide if it is allowed.
(call_expression
  function: (identifier) @_fn
  (#eq? @_fn "exec")
) @error.bare-exec

; ── silent-catch ──────────────────────────────────────────────
; `catch e { }` where the catch_body has no statements. Lint runner
; checks for a trailing `// @allow-silent-catch` on the same line.
(try_statement
  catch_body: (block) @error.silent-catch
  (#eq? @error.silent-catch "{}"))

; Fallback structural form (used when #eq? text predicate is unavailable
; in the host runtime — match a try_statement whose catch_body is a
; block that contains zero statements).
(try_statement
  error_binding: (identifier)
  catch_body: (block . "}" )) @error.silent-catch.struct

; ── silent-exit ───────────────────────────────────────────────
; Direct call to `exit(...)`. Project policy requires routing through
; `central_exit(...)` unless explicitly allowed.
(call_expression
  function: (identifier) @_fn
  (#eq? @_fn "exit")
) @error.silent-exit

; ── nested-call-exec ──────────────────────────────────────────
; `exec(...)` appearing as an argument inside another call — usually a
; sign of unchecked stdout being parsed inline.
(call_expression
  arguments: (argument_list
    (call_expression
      function: (identifier) @_inner
      (#eq? @_inner "exec")) @error.nested-call-exec))
