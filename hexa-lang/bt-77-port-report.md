# BT 77 — RT 32-E Port to Rust Interpreter: Blocker Report

**Date:** 2026-04-13
**Status:** BLOCKED — port is a **no-op** (the pattern does not exist in Rust)
**Session:** investigation, single session

## TL;DR

The 1-element array wrapper pattern that RT 32-E removed from `self/hexa_full.hexa` does **not exist** in the Rust interpreter. Rust's `eval_expr(&mut self, expr: &Expr)` already takes a reference and dispatches via `match expr` with no intermediate allocation. Porting RT 32-E to Rust yields zero speedup. Recommend Alternative 2 below.

## Step 1 — Rust Source Location

**Found, but deleted from trunk.**

- Current `main` HEAD: `src/` directory is **gone** — removed in commit `94ffd0f feat(self): 완전한 self-host 흡수 — src/ 147 rs 삭제 REAL` (2026-04-11).
- Pre-deletion tree recoverable from `94ffd0f^`: 147 `.rs` files including `src/interpreter.rs` (15,981 lines).
- H100 pod `/workspace/hexa-lang/` has **no `.rs` source files** (verified via SSH). Only compiled binary `/usr/local/bin/hexa` (9.1 MB, cranelift-based, dated Apr 11 18:09 UTC — confirmed Rust via strings grep for `cranelift-codegen-0.130.0`, `regalloc2-0.15.0`, etc.).
- Git branches with Rust source still accessible: `origin/perf/interpreter-phase1-v2`, `origin/ml/*` clusters, and any pre-`94ffd0f` SHA.

Extracted to `/tmp/bt77_interpreter.rs` for this investigation.

## Step 2 — eval_expr Pattern Analysis

Rust `src/interpreter.rs:1854`:

```rust
fn eval_expr(&mut self, expr: &Expr) -> Result<Value, HexaError> {
    match expr {
        Expr::IntLit(n) => Ok(Value::Int(*n)),
        Expr::FloatLit(n) => Ok(Value::Float(*n)),
        ...
        Expr::Binary(left, op, right) => {
            let l = self.eval_expr(left)?;   // recurses on &Expr, no allocation
            ...
        }
    }
}
```

- Signature takes `&Expr` — a reference, zero allocation.
- Grep for `vec![expr]`, `Vec::from([expr])`, `&[expr]`, `eval_expr_inner`, `eval_expr_at`, `tmp_arr` in interpreter.rs: **no matches** in the dispatch hot path. The 30 `vec![...]` occurrences are all builder seeds (closure thunks, fold accumulators, map/filter `call_function` arg marshalling), not per-node wrappers.
- The RT 32-E hotspot is an artifact of stage1 hexa_full.hexa using array-index dispatch (`exec_stmt_at(arr, idx)`) where each call-site allocated a 1-element wrapper array. Rust uses direct `&Expr` dispatch, so this allocation class does not exist.
- RT 32-H already audited the entire stage1 file (14,986 lines) and confirmed no additional wrapper-pattern targets; conclusion applies transitively to Rust (which is structurally cleaner).

## Step 3 — Port Scope

**No port possible** — there is no wrapper to remove. The observed stage1 speedup (-88.9% push, -45% wall) was fixing a stage1-specific code-gen quirk, not a general interpreter design issue.

## Alternative Strategies (ranked by effort/ROI)

**Alt 1 — Apply `perf/interpreter-phase1` Rust work to stage1** (unclear fit)
Branch `origin/perf/interpreter-phase1` (commit `b148378`) contains 5 Rust-origin hotpath fixes (string→enum dispatch, fn_cache, memo_hash). These already landed in `self/interpreter.hexa` as hexa code. For **Rust interpreter** acceleration they are already applied (the pod binary dates from this era). ROI for pod: ~0. Skip.

**Alt 2 — Replace Rust hexa binary with C stage0 (RECOMMENDED)**
Today's session built `build/hexa_stage0` from `self/hexa_full.hexa` (post-RT-32-E) via `self/native/hexa_v2 → /tmp/hexa_full_regen.c → clang -O2`. This binary has the RT 32-E, 32-H, and all current optimizations.
- Effort: ~30 min (copy stage0 binary to pod, stage it at `/tmp/hexa_stage0`, smoke test a training script outside training loop, A/B compare push counts / wall).
- Risk: stage0 must be Linux x86_64; local build is macOS arm64. Need to build stage0 on pod (clang available) or on Ubuntu host (see `project_linux_native_hexa_2026_04_12`).
- Training impact: if stage0 is functionally equivalent, GPU util 0% → 30–50% expected (matches stage1 -45% wall).
- Non-disruptive: only replace after current H100 training step 1450/3000 completes, or schedule between training rounds.

**Alt 3 — Restore Rust src/ and apply RT 32-series analogs**
Pull pre-`94ffd0f` Rust tree, find NEW hotspots via cargo flamegraph on a d64 micro, apply patches, rebuild.
- Effort: 4–8 hours (restore tree, `cargo build --release` on pod ~10 min, profile, patch, cycle).
- ROI uncertain: phase1 already fixed obvious stuff; further gains likely require AST/env refactor, not simple wrapper removal.
- Reviving `src/` fights the self-host absorption decision (94ffd0f).

**Alt 4 — Build Linux native stage0 on pod**
Extends Alt 2: compile `/tmp/hexa_full_regen.c` directly on pod with pod-side clang. C source portable, artifact native.
- Effort: 45–60 min once macOS→Linux C build path confirmed (some `@abi` / clang flag tweaks may be needed).
- This is the actual "port to pod" action that delivers the RT 32-E win on H100.

## Recommendation

**Alt 4** (build stage0 C source on pod, deploy as `/tmp/hexa_stage0`, A/B vs Rust `/usr/local/bin/hexa` on a training smoke script, cut over between training rounds). This is the path where RT 32-E's measured -45% wall actually reaches H100.

Open BT for Alt 4: provision `/tmp/hexa_full_regen.c` transfer to pod + clang build + A/B harness on a 50-step CLM micro.

## Do-not-do

- Do not replace `/usr/local/bin/hexa` mid-training (step 1450/3000 in progress).
- Do not revive `src/*.rs` — contradicts self-host absorption; low ROI given stage0 path exists.
- Do not port RT 32-E literally to Rust — zero-effect change.
