# anu_time — ★19 ANU-Time Universe MVP

**Concept**: sim의 한 tick = 다음 ANU QRNG byte 도착 시점. 주관적 시간 τ ≡ 양자측정 카운트.
wall-clock 과 독립된 "quantum-event-discrete" universe.

## Modules

| file | role |
|------|------|
| `anu_clock.hexa` | ANU byte stream pump (cache 60s TTL + direct curl + urandom fallback) |
| `mini_world.hexa` | σ²=64 latent state, 1-byte step (additive + τ=4 diffusion) |
| `universe.hexa` | main loop — byte → step → log JSONL |
| `analyze.hexa` | post-run stats + histogram + Poisson χ² fit |
| `runner.sh` | 5-min demo launcher |

## Run

```bash
cd $NEXUS_ROOT                      # ~/Dev/nexus
./shared/sim_bridge/anu_time/runner.sh 300 my_run
```

Artifacts → `shared/sim_bridge/anu_time/runs/my_run/`:
- `log.jsonl` — per-tick `{tau, wall_t_ns, byte_dt_ns, byte, source, state_hash, diff_L1}`
- `meta.json` — run config + timing
- `report.txt` — analyze summary

## Env

- `HEXA_LOCAL=1` — **required**. Keeps file I/O on Mac (default routes hexa→remote via hexa_remote wrapper).
- `NEXUS_NO_BUDGET_OK=1` — bypasses H-NOZOMBIE budget gate for long runs.

## Limits

- ANU 1 req/min, 64 bytes/response → natural rate ~1 byte/s over many minutes.
- In burst: 64 cached bytes consumed in ~2s (each byte ~30ms for hex→int shell exec).
- urandom fallback kicks in when ANU 429-rate-limited.

## Measurements (target)

1. tick 인터발 분포 (Poisson fit via χ²)
2. τ_subjective / wall_time ratio
3. state_diff_L1 per tick
4. source breakdown (cache / anu / urandom)

## Pitfalls encountered

- hexa stage1: global `list[i] = v` **no-op** → rebuild list each phase (see `mini_world.hexa::mw_step`).
- `[i64]` type syntax (not `list<i64>`).
- hexa binary default-routes to remote host (`aiden`) — `HEXA_LOCAL=1` forces local execution.
- `exit()` may not propagate in some hexa versions → universe.hexa relies on wall-clock timeout in runner.sh.
