# godel_q — NEXUS-6 Gödel-Quantum-Schmidhuber Bootstrap (★20 MVP)

Fixed-point seeker: ANU QRNG entropy → pick mutation → verify gate → log.
Schmidhuber-style Gödel machine with a quantum oracle. **MVP only logs — no
git commit, no touching anything outside this directory.**

## Layout

| file | role |
|------|------|
| `mutation_target.hexa` | dummy target — ALL mutations apply to a sandboxed **copy** of this file |
| `anu_source.hexa` | ANU QRNG client (curl + python JSON parse); `/dev/urandom` fallback; 60s cache |
| `mutation_picker.hexa` | 4 ANU bytes → `(line, op, mag)` TSV |
| `mutator.hexa` | applies a single whitelist op to `src` → writes to `dst` |
| `verify_gate.hexa` | `hexa parse` + sandbox run + metric extract + hash |
| `bootstrap.hexa` | main loop (max 100 iters, logs `runs/<ts>/mutations.jsonl`) |
| `runner.sh` | 30-min wall runner |

## Whitelist ops

- `tweak_const` : first integer literal on line ± {1, 10}
- `swap_op`     : first space-bounded operator swap `+↔-`, `*↔/`
- `rename_var`  : append `_m` to first `let`-bound identifier on the line, propagate below

## Safety invariants (ENFORCED by code structure, not convention)

1. Mutation target path is always `mutation_target.hexa` under `sim_bridge/godel_q/`. Writes land in `runs/<ts>/candidate.hexa`. Source is read-only.
2. No git operations. No external file touches.
3. `bootstrap.hexa` caps `max_iters` at 100.
4. `runner.sh` enforces `timeout 1800` wall.
5. L0 protected paths never referenced (verified by grep against `CLAUDE.md` L0 list).

## Run

```bash
cd shared/sim_bridge/godel_q
./runner.sh 100
```

Output: `runs/<YYYYMMDD-HHMMSS>/mutations.jsonl` (one JSON per iter + start/end header).

## Metric

`metric = |r1| + |r2| + |r3|` parsed from sandboxed `compute/score` prints.
Baseline (unmodified target) = 174. A mutation is "accepted" iff it applied AND
its candidate both parses and runs AND `metric >= baseline`.

## Honesty notes

- No true QRNG hardware. ANU REST is rate-limited (1 req/min, 64 bytes). Fallback is `/dev/urandom` (honest label via `source=` field).
- "Fixed-point" in MVP is operational: successive accepts with same output hash ≥ N times. N not reached in 100 iters is normal.
- `shared/discovery/rng_lab/fetch_anu.hexa` currently segfaults on `hexa_stage0` (observed 2026-04-16); `anu_source.hexa` is a minimal in-house re-implementation and does not replace the rng_lab module.
