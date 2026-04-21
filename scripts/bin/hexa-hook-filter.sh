#!/bin/bash
# hexa-hook-filter.sh — wrap hexa hook call, strip stage0 noise
# Usage: hexa-hook-filter.sh <hexa-bin> run <hook-path> [args...]
#
# Workarounds for stage0 interpreter bugs (2026-04-13):
# 1) Pointer leak: `if X { ... }` emits HexaVal struct pointer integer
# 2) Banner spam: new stage0 lacks input-file exec → prints 28-line banner
#    on EVERY hook call.
# Filter:
#  - Drop long-integer-only lines (pointer leak)
#  - Drop stage0 self-test banner lines (28 known phrases)
# Remove this wrapper once stage0 is rebuilt.

exec "$@" | sed -E \
  -e '/^[0-9]{8,}$/d' \
  -e '/^Parse error at /d' \
  -e '/^Runtime error: undefined function:/d' \
  -e '/^Runtime error: unknown method /d' \
  -e '/^Test [0-9]+:/d' \
  -e '/^  PASS$/d' \
  -e '/^ExprStmt\(/d' \
  -e '/^AssignStmt\(/d' \
  -e '/^=== HEXA Self-Hosting Parser ===/d' \
  -e '/^=== Self-Hosting Parser: ALL /d' \
  -e '/^=== HEXA Self-Host Interpreter ===$/d' \
  -e '/^Core: eval_expr \+ exec_stmt/d' \
  -e '/^Type: int float bool char ord/d' \
  -e '/^String: contains starts_with/d' \
  -e '/^String\+: repeat pad_left/d' \
  -e '/^Array: push pop len contains/d' \
  -e '/^Array\+: sort enumerate/d' \
  -e '/^Array\+\+: chunk window/d' \
  -e '/^Map: get set keys values/d' \
  -e '/^Map\+: to_array from_array/d' \
  -e '/^Math: abs min max floor/d' \
  -e '/^Math\+: tan asin acos/d' \
  -e '/^Math\+\+: sign gcd lcm/d' \
  -e '/^BinOp: \+ - \* \/ %/d' \
  -e '/^UnaryOp: - ! ~ typeof/d' \
  -e '/^Functional: compose pipe/d' \
  -e '/^Error: error is_error/d' \
  -e '/^Format: format\(\) hex\(\)/d' \
  -e '/^IO: read_file read_lines/d' \
  -e '/^JSON: to_json from_json$/d' \
  -e '/^Util: assert range sort/d' \
  -e '/^Control: if\/else while/d' \
  -e '/^Advanced: closure\/lambda/d' \
  -e '/^G22: default parameter values$/d' \
  -e '/^G23: named arguments$/d' \
  -e '/^Ready for Phase 2 self-hosting pipeline$/d'
