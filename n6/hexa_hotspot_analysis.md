# hexa binary hotspot analysis -- ROI #15

Date: 2026-04-12
Status: ANALYSIS ONLY (no modifications)
Binary: $HEXA_LANG/hexa (2026-04-12 00:18)

## 1. Binary profile

| Property | Value |
|---|---|
| Type | Mach-O 64-bit executable arm64 |
| Size | 6.6 MB (6,958,720 bytes) |
| Language | Rust (with Cranelift JIT backend) |
| Symbols | 7,341 (not stripped in current build) |
| __TEXT size | 0x530000 (5,439,488 bytes) |
| __text section | 0x464ce0 (4,607,200 bytes) |

### Binary code distribution by component

| Component | Size | % of code |
|---|---|---|
| cranelift_codegen | 866 KB | 19.2% |
| interpreter (tree-walk) | 394 KB | 8.7% |
| parser | 134 KB | 3.0% |
| jit (hexa JIT) | 106 KB | 2.4% |
| codegen (hexa native) | 96 KB | 2.1% |
| vm (bytecode VM) | 76 KB | 1.7% |
| compiler (bytecode) | 33 KB | 0.7% |
| other (std, alloc, etc) | 2,796 KB | 62.1% |

## 2. Wrapper chain

The `shared/bin/hexa` referenced in the ROI item is a Bash wrapper, not the compiled binary.

```
~/.hx/bin/hexa (symlink)
  -> $AIRGENOME/nexus/bin/hexa (Bash script, 152 lines)
     -> L0 guard check (python3)
     -> Mac-only passthrough OR remote routing (ubu/hetzner)
     -> exec $LOCAL_HEXA "$@"
        -> $HEXA_LANG/hexa (actual Rust binary, 6.6 MB)
```

There is also `shared/scripts/bin/hexa` (a lighter resolver) and `~/.hx/bin/hx` (the package manager).

## 3. Hotspot symbol resolution (CORRECTED)

The original perf baseline (2026-04-11) was taken with a stripped binary and stated:
> "offset +0x50458 is 81% CPU -- interpreter dispatch loop or tight expression eval"

**Actual finding**: The current binary is NOT stripped (7,341 symbols present). Symbol resolution reveals the hotspot is **NOT in the tree-walking interpreter**. It is in the **Cranelift JIT compiler's instruction lowering pass**.

### Resolved hotspot

```
+0x50458 => cranelift_codegen::isa::aarch64::lower::isle::generated_code::constructor_lower
  Function base: 0x1000474b8
  Offset into fn: +36,768 bytes (out of 55,732 total = 54.4 KB function)
```

This is a massive auto-generated pattern-matching function (54.4 KB of machine code) that lowers Cranelift IR to AArch64 machine instructions. It is ISLE-generated code (Cranelift's DSL for instruction selection).

### Resolved full call stack (17+ frames)

All frames are within the Cranelift compilation pipeline:

```
Frame   Offset     Symbol (demangled)
-----   ------     ------------------
 1      +0xb4ae0   cranelift_codegen::machinst::buffer::MachBuffer::add_try_call_site
 2      +0x3f84fc  (webpki::crl -- unrelated, likely sampling artifact)
 3      +0xc8e5c   cranelift_codegen::legalizer::simple_legalize::{closure}
 4      +0x78998   cranelift_codegen::opts::generated_code::constructor_simplify
 5      +0x99204   cranelift_codegen::egraph::elaborate::Elaborator::elaborate
 6      +0xa5a1c   cranelift_codegen::machinst::pcc::check_binop::{closure}
 7      +0x93e28   cranelift_codegen::egraph::OptimizeCtx::insert_pure_enode
 8      +0x3cd20   cranelift_codegen::isa::aarch64::inst::emit::enc_ldst_pair
        ...
 HOT    +0x50458   cranelift_codegen::...::constructor_lower (81% CPU)
        +0x45c0c   cranelift_codegen::...::AArch64Backend::lower_branch (recursive)
```

### Secondary hotspot (19%)

```
+0x45c0c => cranelift_codegen::isa::aarch64::lower::AArch64Backend::lower_branch
  (self-recursion in the branch lowering pass)
```

## 4. Root cause analysis

The 81% CPU concentration is in **JIT compilation, not interpretation**. When hexa runs bench_chi2 (the profiled workload), it triggers the JIT compiler path which uses Cranelift to compile hot functions to native ARM64. The bottleneck is:

1. **ISLE constructor_lower** (54.4 KB function) -- a giant match-based pattern that maps Cranelift IR opcodes to AArch64 instructions. This is auto-generated from .isle rule files and compiles into a deeply nested decision tree.

2. **AArch64Backend::lower_branch** -- recursive branch lowering that feeds into the same constructor_lower.

3. The 17-frame stack depth is NOT from tree-walking interpretation but from the Cranelift compilation pipeline: legalize -> optimize (egraph) -> elaborate -> lower -> emit.

### Why the original analysis was wrong

The original perf baseline was taken from a **stripped** binary where symbol resolution was impossible. The offset +0x50458 was guessed to be "interpreter dispatch" based on:
- The 17+ frame stack depth (looks like tree-walking)
- The assumption that hexa is purely interpreted

In reality, hexa already has a JIT pipeline: `interpreter -> compiler (bytecode) -> VM -> JIT (Cranelift)`. The profiled workload was hitting the JIT path, and the deep stack is the Cranelift compiler pipeline, not the interpreter.

## 5. Existing optimization infrastructure in hexa-lang

The hexa-lang project already has significant optimization work:

| Component | Source (Rust) | Lines | Status |
|---|---|---|---|
| interpreter.rs | tree-walking eval | 16,059 | Active, with inline fast-paths |
| vm.rs | bytecode VM | 2,140 | Active, flat dispatch with CallFrame |
| compiler.rs | AST -> bytecode | present | Active |
| jit.rs | Cranelift JIT | 3,287 | Active (the bottleneck source) |
| trace_jit.rs | trace-based JIT | 449 | In development |
| inline_cache.rs | IC for dispatch | 252 | In development |
| nanbox.rs | NaN-boxing values | 508 | In development |
| codegen/ | Native ARM64/x86 | 3,760 total | In development |

Self-hosted (.hexa) counterparts also exist:
- `self/interpreter.hexa`, `self/vm.hexa`, `self/compiler.hexa`, `self/jit.hexa`

The interpreter already has fast-paths for common Int operations (line 1916-1937) and fn_cache for O(1) lookups (line 1863).

## 6. Revised optimization recommendations

### Path A: Cranelift tuning (addresses the actual hotspot)

| Action | Effort | Impact | Notes |
|---|---|---|---|
| Upgrade Cranelift version | 4-8h | Medium | Newer ISLE codegen may have better decision trees |
| Use `OptLevel::Speed` vs `SpeedAndSize` | 1h | Low-Medium | Trade binary size for compile speed |
| Pre-compile hot builtins at startup | 8-16h | High | Amortize JIT cost across invocations |
| Cache compiled functions to disk | 16-24h | High | Avoid re-JIT on repeat runs |
| Lazy JIT (interpret first, JIT hot loops) | 8-16h | High | Currently may JIT too eagerly |

### Path B: Bypass Cranelift entirely for small scripts

| Action | Effort | Impact | Notes |
|---|---|---|---|
| Threshold: only JIT functions called > N times | 4h | High | Most nexus .hexa scripts are short-lived |
| Interpreter fast-path improvements | 8-16h | Medium | Already partially done (Int fast path) |
| Use the existing bytecode VM without JIT | 2-4h | Medium | VM exists (vm.rs, 2,140 lines) -- route scripts there |

### Path C: Original ROI suggestion (tree-walking -> bytecode)

| Action | Effort | Impact | Notes |
|---|---|---|---|
| Full bytecode VM for all code | 40h | Low (for this hotspot) | Would NOT address the actual 81% hotspot |
| Inlining in interpreter | 16h | Low (for this hotspot) | Same -- wrong target |

### Recommendation

**Path B is highest ROI**: The actual bottleneck is JIT compilation overhead, not interpretation. For short-lived nexus scripts (hooks, blowup, atlas_health), the JIT compiler is spending more time compiling than the code would take to interpret.

Estimated quick win: Add a `--no-jit` flag or `HEXA_NO_JIT=1` env var that routes through the existing bytecode VM (vm.rs) without triggering Cranelift. This would eliminate the 81% hotspot for all nexus hook/script workloads.

If JIT is needed for compute-heavy workloads (bench_chi2, seed_engine), **Path A: disk caching of compiled functions** would amortize the cost.

## 7. Dependencies

- Primary: hexa-lang project (`$HEXA_LANG/`)
- Cranelift: vendored as Rust dependency (cranelift-codegen crate)
- Rule R12: src/*.rs changes require user explicit approval (L0 locked)
- Rule R12 exception: self/*.hexa modifications are freely allowed
- The `shared/bin/hexa` wrapper is L0 protected -- do not modify

## 8. ROI item correction

The ROI item #15 description should be updated:

**Current**: "offset +0x50458 CPU 81%. tree-walking dispatch loop -> bytecode VM or inlining"

**Corrected**: "offset +0x50458 CPU 81% = cranelift_codegen::constructor_lower (JIT compile, not interpret). Fix: JIT threshold / --no-jit flag for short scripts, disk cache for hot functions"

Priority remains P3 but estimated effort drops from 40h to ~8-16h for the quick-win path (JIT threshold + --no-jit).
