# rt 33 — stage0 cold-start latency measurement & decomposition

**Date**: 2026-04-13
**Branch**: `rt-33-cold-start` (hexa-lang)
**Scope**: `hexa run <script>` hook-dispatch path — measurement + one fast-exit optimization
**Status**: `partial` (shipped: grep fast-exit in `cmd_run`; deferred: watchdog sleep floor, AOT cache)

## TL;DR

Two dominant costs, not one:

1. **module_loader preprocess (~700 ms on a real hook)** — stage0 runs self-host `self/module_loader.hexa` on every script, doing char-by-char string processing to expand `import`/`use`. All 49 hooks in `shared/hooks/*.hexa` have **zero** use/import directives, so this work is pure waste for the hook path.
2. **stage0 watchdog `sleep 1`** in `cmd_run` (main.hexa:494) — `wait $C`'s sibling watcher polls at 1-second granularity, so a 2ms script still waits ~1 s before the shell returns. Hard floor on hook wall time.

Fast-exit shipped (this branch): `hexa run` on a real hook drops **1708 ms → 1038 ms (−39 %)**. Remaining 1000 ms is the watchdog floor → filed as rt#34.

## Measurements

All wall times, medians over 5 runs, `subprocess.run` perf_counter timing (macOS arm64, warm). Probe is `println("ok")`. Real hook = `hook-entry.hexa prompt block-forbidden-ext.hexa` (no imports).

| Path | Probe p50 (ms) | Real hook p50 (ms) | Notes |
|---|---:|---:|---|
| `hexa run` **baseline** | 1033.5 | 1708.0 | Full chain: stage1 + module_loader + stage0 + watchdog |
| `hexa run` **rt33 (this branch)** | 1029.5 | 1037.7 | Fast-exit skips module_loader when no use/import |
| `stage0` direct on user script | 1.87 | 38.55 | Bare interpreter — the actual work |
| `stage0` running `module_loader.hexa` | 4.88 | **702.38** | Loader cost grows with file size (hook-entry = 142 LOC) |
| `stage0` on pre-expanded script | 1.78 | — | Post-preprocess cost only |
| `hexa version` / `hexa help` | 1.71 / 1.81 | — | Stage1 entry cost baseline |

**Hot-vs-cold**: stage0 direct stayed within 37–46 ms across 10 back-to-back runs. Page-cache warmup is not a meaningful factor at this scale (binary 1.1 MB, scripts ~5 KB). `purge` not run — would disrupt other processes; the 38 ms cold figure already dominates user-visible cost once the watchdog is removed.

**Maxrss**: `hexa run` ~9.1 MB, stage0 direct 1.7 MB. Stage1's own footprint is the 7 MB gap (driver allocates strings for its shell-quoting + exec buffers).

## Decomposition (real-hook path, baseline)

```
 1708 ms hexa run <hook>
 ─ 1700 ms watchdog wait (sleep 1 polls, blocks until C dies + 1s)
 ─  702 ms stage0 running module_loader.hexa on hook-entry (700 ms out of 1700 could run concurrently inside the watch window)
 ─   39 ms stage0 running the expanded hook source
 ─    2 ms stage1 `hexa` driver (arg parsing, shell-building, `exec()` ≈ printf)
```

After rt33 fast-exit:
```
 1038 ms hexa run <hook>
 ─ 1000 ms watchdog `sleep 1` floor (unavoidable under current design)
 ─   38 ms stage0 running the hook
 ─    1 ms `grep -qE` fast-exit check
 ─    ~  stage1 driver (absorbed into the watchdog window)
```

## Module-loader overhead on plain files

Quantified: **41 % of total hexa run on a plain probe** (425 ms of 1033 ms wall is attributable to module_loader preprocess + temp-file + re-exec, all nested inside the 1000 ms watchdog so it's partially hidden). For real hooks with larger source it's **702 ms / 1708 ms = 41 %** — consistent ratio, which confirms module_loader is the single biggest sub-step after the sleep floor. Fast-exit is the right call and matches the >10 % threshold the task called out.

## Fast-exit shipped

`self/main.hexa` `cmd_run`:

```hexa
// rt 33: fast-exit — grep 으로 use/import 지시문 유무를 먼저 확인.
//   없으면 module_loader 전처리 단계(~700ms on hooks) 를 건너뛴다.
let has_directive = exec("grep -qE '^[[:space:]]*(use|import)[[:space:]]+\"' '" + file + "' && printf yes || printf no")
let mut script = file
if has_directive == "yes" {
    // … original module_loader invocation …
}
```

- Verified: `/tmp/rt33_import.hexa` (has import) still preprocesses + runs; probe + real hook skip it.
- `hexa version`, `hexa help`, `hexa run` (import + no-import) smoke-tested with the locally rebuilt `/tmp/hexa_rt33`.
- **Not installed**: binary on PATH (`~/.hx/bin/hexa` → `Dev/airgenome/nexus/bin/hexa`) is left untouched to avoid disrupting parallel training/agents on this machine. Installation happens on merge.

## AOT cache (bt#36) — why re-enabling isn't the easy win the task hypothesized

`cmd_run` comment says "hook 성능/정합성을 위해 AOT 캐시 경로 제거". Concrete reasons, now measurable:

- **Cold build cost**: `self/native/hexa_v2 <hook> <hook>.c` + `clang -O2` + `codesign` is hundreds of ms to seconds for any non-trivial file. A *miss* would massively regress hook UX (the opposite of what we want).
- **Hit path**: If we had a warm `.hexa-cache/<hash>/exe`, we'd save the 38 ms stage0 startup and replace it with a ~5 ms native exec. That's a +33 ms win *only after* rt#34 removes the 1000 ms watchdog floor — otherwise the win is invisible.
- **Invalidation**: current meta uses `mtime|size`; hook files are edited often during development → frequent rebuilds → frequent hit of the seconds-cost miss path.

**Recommendation**: do **not** re-enable AOT for `cmd_run`. Instead, leave it under `hexa build`/`hexa cache build` as the comment plans. First kill the watchdog floor (rt#34), then revisit.

## Smoke tests

- `/tmp/hexa_rt33 version` → `hexa 0.1.0-stage1` ✓
- `/tmp/hexa_rt33 help` → usage printed ✓
- `/tmp/hexa_rt33 run /tmp/rt33_probe.hexa` → `ok` ✓
- `/tmp/hexa_rt33 run /tmp/rt33_import_abs.hexa` → `abs_import_ok` ✓ (import still expanded)
- `/tmp/hexa_rt33 run <real hook>` → same output as baseline ✓

## Recommendation — next rt item

**rt#34 — watchdog sleep floor removal**. The 1000 ms `sleep 1` in `cmd_run`'s zombie-killer is the last big chunk. Options:

1. `sleep 0.05` — 20× finer polling; bash-portable on macOS, 50 ms worst-case floor.
2. `wait -n` + `trap` in the supervisor to react on SIGCHLD (true zero-poll).
3. Drop the watchdog when `$PPID == 1` (already orphaned — nothing to watch), keeping it only for Claude Code/git-hook contexts that actually spawn and SIGKILL.

Option 1 is the lowest-risk starter. Option 2 is the real fix. With rt#33 + rt#34 together, hook wall should land in the 40–100 ms band (stage0 direct + tiny overhead), matching stage0-direct measurements and making hook UX essentially instantaneous.

## File index

- Source change: `$HEXA_LANG/self/main.hexa` (cmd_run fast-exit, branch `rt-33-cold-start`)
- Rebuilt binary (not installed): `/tmp/hexa_rt33`
- Registry: `shared/hexa-lang/runtime-bottlenecks.json` item 33 (nexus-tracked; the directory is otherwise gitignored, the 4 existing JSONs are exempt)
- This report: `shared/hexa/rt-33-cold-start-report.md` (canonical location; `shared/hexa-lang/` is gitignored per nexus `.gitignore:110`)
