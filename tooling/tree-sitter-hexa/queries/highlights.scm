; tree-sitter-hexa — highlights.scm
; SSOT for editor syntax highlighting (VS Code, Neovim, Helix, Zed).
;
; Aligned with `design/hexa_token_taxonomy_unified_spec.md` (D 트랙).
; canonical SSOT = LSP semanticTokenTypes (15 base + 4 modifier).
; tree-sitter dotted refinement is permitted where LSP can not express
; the distinction (e.g. `@string.escape`, `@punctuation.*`, `@comment.note`).

; ── keywords ───────────────────────────────────────────────
[
  "fn"
  "let"
  "mut"
  "return"
  "if"
  "else"
  "while"
  "for"
  "in"
  "try"
  "catch"
] @keyword

; boolean literals are keyword-class (LSP id 9) — collapsed from
; the legacy `@boolean` capture per spec § 4.1 / § 5.1 (conflict resolution).
(boolean_literal) @keyword

; ── primitive vs user types ────────────────────────────────
; primitive = LSP type id 1 + modifier defaultLibrary (3) → tree-sitter
; expresses this via dotted refinement.
(primitive_type) @type.builtin

; user-defined types appearing in type positions (parameter / return /
; let annotations) — LSP id 1 (no modifier).
(parameter         type: (identifier) @type)
(let_declaration   type: (identifier) @type)
(function_declaration return_type: (identifier) @type)
(array_type             (identifier) @type)

; ── declarations ───────────────────────────────────────────
(function_declaration name: (identifier) @function)
(parameter            name: (identifier) @variable.parameter)
(let_declaration      name: (identifier) @variable)

; ── decorators (`@test`, `@derive`, …) ─────────────────────
; LSP semantic token type id 14. tree-sitter mainstream capture name
; for decorators is `@attribute` (nvim-treesitter convention).
(decorator (identifier) @attribute)

; ── calls + members ───────────────────────────────────────
; builtin function calls — LSP `function + defaultLibrary` (id 8 + mod 3).
; The builtin list is mirrored from `queries/builtins.list` (SSOT) and
; should match `get_builtins()` in the LSP server when that lands.
((call_expression
  function: (identifier) @function.builtin)
  (#match? @function.builtin "^(println|print|len|to_string|to_int|to_float|assert|panic|format|read_file|write_file|env|argv|exit)$"))

(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (member_expression property: (identifier) @function.method))

(member_expression property: (identifier) @property)

; ── literals ──────────────────────────────────────────────
(integer_literal) @number
(float_literal)   @number.float
(string_literal)  @string
(escape_sequence) @string.escape

; ── operators ─────────────────────────────────────────────
[
  "+" "-" "*" "/" "%"
  "==" "!=" "<" ">" "<=" ">="
  "&&" "||" "!"
  "=" "->"
] @operator

; ── punctuation ───────────────────────────────────────────
[
  "(" ")"
  "{" "}"
  "[" "]"
] @punctuation.bracket

[ "," ":" "." ] @punctuation.delimiter

; ── comments + lint annotations ───────────────────────────
; project convention: `// @allow-bare-exec`, `// @allow-silent-catch`,
; `// @allow-silent-exit`, plus extension candidates `@nohot` / `@hot` /
; `@deprecated` (per spec § 5.6) — surface these as a distinct comment
; refinement so reviewers can spot them at a glance. LSP collapses to
; plain comment (id 10).
((line_comment) @comment.note
  (#match? @comment.note "@(allow-|nohot|hot|deprecated)"))

(line_comment) @comment
