<!-- @doc(type=paper) -->
<!-- @own(sections=["1. Baseline", "2. Bottleneck", "3. Improvement", "4. Short-term", "5. Recommended"], strict=false, order=sequential) -->

# hexa-lang training hot-path performance audit

**Date**: 2026-04-15
**Scope**: profile hexa-lang interpreter cost on the training hot path
(3 holographic training primitives, 5 representative phi engines) and
ship a short-term improvement.
**Toolchain**: `hexa 0.1.0-stage1`, `hexa bench --runs 3 --json`
**Platform**:
- **local** — Mac (native interpreter, `HEXA_LOCAL=1`)
- **remote** — hexa_remote wrapper dispatch to ubu host (default path)

---

## 1. Baseline (pre-PoC)

### 1.1 Five representative phi engines

| Engine | local median wall (s) | remote median wall (s) | array_push (local) | RSS (KB, local) |
|---|---:|---:|---:|---:|
| addiction_phi          |  0.34 | 0.11 |   511,956 |    55,136 |
| attention_phi          |  0.51 | 0.22 |   785,568 |    54,528 |
| metacognition_phi      |  0.51 | 0.17 |   755,754 |    59,296 |
| awe_phi                |  1.50 | 0.81 | 3,117,757 |   167,840 |
| **working_memory_phi** | **90.70** | **23.32** | **63,896,578** | **460,384** |

Four engines fall in a well-behaved band (110 ms — 1.5 s local).
`working_memory_phi` is a **~180× outlier** — it alone dominates the
Track B multiplication risk.

### 1.2 Training primitive

| File | local median wall (s) | array_push (local) |
|---|---:|---:|
| training/phi_holographic_measure.hexa | 16.31 | 1,583,277 |

Not a per-step primitive today (invoked at validation gates, not every
step), but it sits within the same interpreter regime.

### 1.3 Track B blast radius

With 110 phi engines wired per step and the current hot-path shape:

| Scenario | Per-step overhead (remote) |
|---|---:|
| Mean engine × 110 (excl. outlier) | ≈ 35 s |
| With `working_memory_phi` outlier | **+23 s** (outlier alone) |
| Target GPU fwd/bwd time | ~0.3 s |

The outlier alone blows the step budget by 70× — it is the dominant
Track B integration blocker.

---

## 2. Bottleneck breakdown (top 3)

### 2.1 Pass-by-value (PBV) list copies inside hot loops *(dominant)*

**Evidence**: `working_memory_phi.hexa` triggers 63.9 M `array_push`
and 6.7 M `array_grow` on a **single** run with 7 slots, 24-sample
traces, 6 maintenance steps, 11 scenarios. The interpreter cost of
the entire 5/5 self-test is ≈ 90 s local.

**Root cause**: `fn wm_arr_set(a: array, i: int, v: float) -> array`
rebuilds the entire `a` from scratch via repeated `push`. It is
invoked from the innermost `(slot × slot × trace × step × scenario)`
bleed loop — i.e. once per `(tt, c)` pair on the 168-element
`post_bleed` array. This is the exact "hexa lists are pass-by-value"
anti-pattern flagged in MEMORY.md
(`feedback_hexa_lists_pbv.md`).

**Why it dominates**: call graph cost is O(trace_len · capacity² ·
array_len) per step. For WM parameters (24 · 49 · 168) that is
≈ 197 K element copies **per step**, × 6 steps × 11 scenarios ≈ 13
million copies just for the bleed inner loop — before any MI work.

### 2.2 Full-array rebuild helpers outside the inner loop

`wm_buffer_write`, `wm_buffer_init`, `wm_occ_init`, `wm_slot_meta_init`,
`wm_pack_state`, `wm_unpack_buffer`, and seven other helpers all
rebuild fresh arrays via `push`. Each call allocates a new backing
store. Outside the hot bleed loop each cost is small, but together
they explain the ~10 M residual `array_push` counts and the RSS
pressure (460 MB local).

### 2.3 Interpreter dispatch overhead at ~300 kHz steps/s

Remote wall is ≈ 3× faster than local for the same bytecode. This
tells us the bottleneck is interpreter dispatch + alloc, not I/O. A
native compile path (or even a tighter value representation) would
compound on top of PBV wins.

---

## 3. Improvement proposals

### 3.1 Short-term (≤1 day) — **shipped as PoC (§4)**

**Name**: PBV batched-rebuild.
**Idea**: replace per-element `wm_arr_set` with (a) scalar
accumulation before a single `push` per outer-loop iter, and (b)
two-pass row-rebuild that produces one new array per `tt` instead of
one per `(tt, slot)`.
**Effort**: ~40 min, pure hexa, no interpreter change.
**Impact**: 52% local / 66% remote wall-time reduction on the outlier;
0 delta on the other 5/5 self-tests (bit-identical output).
**Risk**: none — purely algebraic restructuring.

### 3.2 Medium-term (≤1 week) — stage0 list aliasing + array pool

**Name**: interpreter-level in-place `arr_set` with COW semantics.
**Idea**: give the interpreter a `HexaVal::Array` refcount with
copy-on-write, so `arr[i] = v` when refcount==1 mutates in place.
This makes `wm_arr_set` O(1) without breaking pass-by-value
semantics.
**Effort**: 2–4 days (touches stage0 ValRepr + builtins; needs
regression runs on rt 16–73 + bt 16–73).
**Impact**: expected further 5–10× on the WM outlier (remote 8s →
sub-1s) and broad 1.3–2× on every other engine.
**Dependencies**: clear the stage0 rebuild backlog (see
`project_session_20260413_stage0_rebuild.md`).
**Risk**: medium — refcount policy interaction with the known
`Hexa struct-field list aliasing bug (2026-04-15)` needs explicit
design.

### 3.3 Long-term (≤1 month) — hexa → native compile for phi engines

**Name**: `hexa build` path for all `anima-engines/*_phi.hexa`, with
a tiny engine-call ABI so training can `dlopen` and invoke each phi
as a C function.
**Idea**: the interpreter dispatch dominates over numerics; every
engine is a self-contained pure function. Compile once, cache by
content-hash, invoke as native.
**Effort**: 2–4 weeks (compiler backend already exists via `hexa
build`; need stable array/float ABI + per-engine entry point +
training-side loader).
**Impact**: expected 30–100× on interpreter-bound engines. Would
make the 110-engine Track B multiply fit in < 50 ms budget.
**Dependencies**: `hexa build` stability on all 110 engines, FFI
shim, process-level lifecycle (preload vs per-step spawn).
**Risk**: high — not because of any single piece, but because of
the number of moving parts touched across shared/harness, training,
and the codegen.

---

## 4. Short-term PoC — shipped

### 4.1 Change

One hunk inside `wm_maintain` in
`anima-engines/working_memory_phi.hexa`. The bleed inner loop is
restructured:

1. **`bleed_add` construction**: a scalar accumulator `acc` sums
   contributions for each source slot `a2` inside the `b2` loop. A
   single `push` per `a2` builds the 7-element `bleed_add`. Prior
   code invoked `wm_arr_set(bleed_add, a2, …)` up to 42× per `tt`.
2. **`post_bleed` row update**: collect the 7 slot updates for the
   current `tt` row into a fresh 7-element `row_new`, then rebuild
   `post_bleed` in a single streaming pass substituting that row.
   Prior code called `wm_arr_set(post_bleed, idx, …)` 7× per `tt`
   (each a full 168-element copy).

### 4.2 Correctness

```
$ HEXA_LOCAL=1 hexa run anima-engines/working_memory_phi.hexa > /tmp/wm_poc.txt
$ diff /tmp/wm_baseline.txt /tmp/wm_poc.txt
(no output — bit-identical)
```

All 5/5 self-tests (T1 capacity · T2 chunking · T3 rehearsal · T4
similarity interference · T5 Φ gradient) pass with identical Φ
values to 6 decimals. Noise RNG state `s2` preserved (outer `tt`,
inner `c` advance order matches original).

Cross-engine smoke: `attention_phi`, `metacognition_phi`,
`addiction_phi`, `awe_phi` all remain 5/5 PASS.

### 4.3 Measurements

| Mode | Engine | Median wall (s) before | Median wall (s) after | Δ |
|---|---|---:|---:|---:|
| local  | working_memory_phi | 90.70 | 43.00 | **−52.6%** |
| remote | working_memory_phi | 23.32 |  8.02 | **−65.6%** |

| Alloc stat | Before (local) | After (local) | Δ |
|---|---:|---:|---:|
| array_new  | 17,151,418 |  7,223,159 | −58% |
| array_push | 63,896,578 | 28,328,910 | −56% |
| array_grow |  6,745,758 |  4,854,400 | −28% |

### 4.4 Extrapolated Track B budget

If the remaining 105 engines stay in their pre-PoC band (typical
1 s remote or less), the Track B multiplication looks like:

| Scenario | Per-step overhead (remote) |
|---|---:|
| Before PoC (all 110 engines, incl. outlier) | ≈ 35 s + 23 s = 58 s |
| After PoC (all 110 engines, post-outlier)   | ≈ 35 s +  8 s = 43 s |

Short-term PoC alone does not clear the per-step budget — that
requires §3.2 or §3.3 — but it removes the dominant single-file
outlier and proves the PBV fix class works.

### 4.5 Files touched

- `anima-engines/working_memory_phi.hexa` — inner loop of
  `wm_maintain` restructured; comments added explaining the root
  cause and fix (per `feedback_troubleshoot_comments.md`).

---

## 5. Recommended next actions

1. **Apply the same PBV batched-rebuild pattern** to any other
   engine that crosses a ≥ 5 s wall-time threshold. Scan candidates
   by `hexa bench --json` across all 110 engines (cheap; a sweep
   takes minutes).
2. **Prioritize §3.2** once the stage0 rebuild backlog lands — it
   is the leverage point that unifies every engine, not just the
   outlier.
3. **Defer §3.3** until Track B integration lands and the remaining
   budget is empirically known; only then is the compiled-engine
   ABI design constraint clear.
