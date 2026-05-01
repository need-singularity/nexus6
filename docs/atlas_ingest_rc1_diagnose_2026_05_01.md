# atlas_ingest rc=1 진단 + fix (r7 retry FAIL #2 closure)

**Date**: 2026-05-01
**Scope**: `tool/omega_cycle_atlas_ingest.hexa` (F22 patch)
**Trigger**: r7 retry `__KICK_AUTO_ABSORB__ FAIL reason=ingest-rc-1` (witness landing OK, schema OK, ingest tool itself fails)

## 1. Symptom

```
__KICK_AUTO_ABSORB__ FAIL witness=<...>2026-05-01_anima-nexus-akida-physical-mathematical-limit-saturation-ref_omega_cycle.json reason=ingest-rc-1
```

Direct invocation on remote runner reproduces:

```
omega_cycle_atlas_ingest: unknown arg `tool/omega_cycle_atlas_ingest.hexa`
reason=unknown-arg-tool/omega_cycle_atlas_ingest.hexa fix=hexa run tool/omega_cycle_atlas_ingest.hexa --help
__RC=1
```

Tool rejects its own script path as a CLI argument.

## 2. Root cause — hexa runtime arg layout regression

`args()` builtin returns:
```
arg[0] = <runtime>/hexa_real
arg[1] = run
arg[2] = <SCRIPT_PATH>.hexa     ← previously absent in older runtime
arg[3..] = user args
```

(verified by minimal `argdump.hexa` probe).

The tool's main parser at line 629 began capture at `ai = 2`, which under the old runtime was the first user arg, but now captures the SCRIPT_PATH itself. The arg-loop's else-branch hits "unknown arg" → `exit(1)` before any user flag (e.g. `--witness`) is parsed.

This is **not** a witness-schema gap, **not** a file-IO error, and **not** an absorb conflict. It is an arg-parser off-by-one against an evolved runtime contract.

Cross-check: the same `let mut ai = 2` pattern appears in `tool/atlas_absorb_hook.hexa`, `tool/atlas_absorb_lint.hexa`, and many other nexus tools — they share the same latent bug, but fix scope per turn-mandate is atlas_ingest only (raw 91 disclosure: sister tools likely affected; defer to dedicated sweep).

## 3. Fix (F22)

Robust auto-detection: scan `raw_args` for the entry ending in `.hexa` and start cli capture at the next index. Falls back to `ai = 2` if no `.hexa` entry detected (legacy-layout safety).

Patch lands in `main()` at line 626-650 of `tool/omega_cycle_atlas_ingest.hexa`. No change to selftest, classification, schema-guard, absorb, or audit-ledger logic.

## 4. Verification

| step | command | result |
|------|---------|--------|
| 1. selftest | `hexa run tool/omega_cycle_atlas_ingest.hexa --selftest` | OK — 7 type cases / 12 grade cases / 116 witnesses / slug determinism / emit idempotence — `__RC=0` |
| 2. fresh ingest | `hexa run tool/omega_cycle_atlas_ingest.hexa --witness <r7-witness>` | `__OMEGA_CYCLE_ATLAS_INGEST__ PASS cycles=1 facts=6` — `__RC=0` |
| 3. F21 idempotence (re-run) | same command twice | `__OMEGA_CYCLE_ATLAS_INGEST__ SKIP reason=already-absorbed` — `__RC=0` |

Shard emitted: `n6/atlas.append.anima-nexus-akida-physical-mathematical-limit-saturation-ref.n6` (6 facts auto-classified, all grade [7]).

## 5. r7 retry verdict

PASS expected — outer rc=0, no SKIP-blocking conditions, kick_dispatch's gate (`rc != 0` then `inner_rc != 0`) cleanly passes through to `__KICK_AUTO_ABSORB__ PASS new_lines=<delta>`.

## 6. Cross-check with this turn's commit chain

The hive r58 Stage 22 (`e5aae6fa7`) `last_index_of` fix in kick_dispatch operates on the OUTER rc parser (delimiter detection in absorb-invoke output). This F22 fix operates on the INNER tool's arg parser. They are orthogonal — both required for the kick → witness → ingest → absorb pipeline to close. r58 chain remains intact (no revert).

## 7. Follow-ups (out of scope this turn)

- Sister tools sharing `let mut ai = 2` pattern (raw 91 disclosure list above) — needs a sweep.
- Hexa runtime contract: document `args()` layout in hexa-lang stdlib so future tools don't drift.
