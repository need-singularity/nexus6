; tree-sitter-hexa — locals.scm
; Scope/definition info for editors that resolve symbols without an LSP.

; ── scopes ────────────────────────────────────────────────
(program) @local.scope
(block)   @local.scope
(function_declaration) @local.scope
(for_statement)        @local.scope
(while_statement)      @local.scope

; ── definitions ───────────────────────────────────────────
(function_declaration name: (identifier) @local.definition.function)
(parameter            name: (identifier) @local.definition.parameter)
(let_declaration      name: (identifier) @local.definition.var)
(for_statement     binding: (identifier) @local.definition.var)
(try_statement error_binding: (identifier) @local.definition.var)

; ── references ────────────────────────────────────────────
(identifier) @local.reference
