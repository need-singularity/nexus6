// kick_dispatch remote-slot-pool divergence audit (2026-04-30)

## Verdict
DIAGNOSTIC — kick_dispatch infra ALIVE on selftest + dry-run paths; FAIL on real spawn due to remote-host slot exhaustion. mac-local `claude_slot_pick.hexa --list` shows 12/12 `available` but kick_dispatch reads a DIFFERENT slot pool (remote ubu1/ubu2/hetzner) which is exhausted.

## Trigger
2026-04-30 r4 paradigm-v12 axis-expansion emission session — `hexa tool/kick_dispatch.hexa <topic>` on 2 attempts both returned `__KICK_RESULT__ FAIL reason=all-claude-slots-exhausted`. Forced raw 100 P305 fallback in-context synthesis for 4 emissions (anima r4 + nexus r4 + review/impl-plan + 1 retry).

## Evidence chain
| Mode | Path | Outcome |
|---|---|---|
| `--selftest` | `kick_dispatch.hexa <topic> --selftest` | `__KICK_RESULT__ PASS` (no spawn, no LLM, no OAuth) |
| `--dry-run`  | `kick_dispatch.hexa <topic> --witness-dir design/kick/ --dry-run` | `__KICK_DRY_RUN__` PASS + envelopes log emitted |
| Real spawn   | `kick_dispatch.hexa <topic>` (default) | `__KICK_RESULT__ FAIL reason=all-claude-slots-exhausted` |

## Root cause: two distinct slot pools
- **mac-local pool** (per `hive/tool/claude_slot_pick.hexa --list`): 12 directories `~/.claude-claude{1..12}` — login-state availability, NOT remote spawn capacity. All 12 reported `available`.
- **remote-host pool** (per user-quoted slot table): ubu1 12 active / ubu2 12 active / hetzner 2 active + 10 cooldown — actual spawn capacity. ALL `active` slots are CURRENTLY OCCUPIED by sister-sessions.

`kick_dispatch.hexa` consults the remote-host pool for spawn capacity; `claude_slot_pick.hexa --list` exposes only the mac-local pool. The two diverge silently — fix-directive `rm ~/.claude-claude*/.kick_limit_until` clears mac-local limit_until tags but does NOT recover remote slots.

## Reproduction
```
cd /Users/ghost/core/nexus
hexa tool/kick_dispatch.hexa <any-topic> --selftest    # PASS
hexa tool/kick_dispatch.hexa <any-topic> --dry-run     # PASS
hexa tool/kick_dispatch.hexa <any-topic>               # FAIL all-claude-slots-exhausted
hexa run /Users/ghost/core/hive/tool/claude_slot_pick.hexa --list  # 12/12 available (mac-local; misleading)
```

## raw 100 P305 cumulative this session
| # | timestamp | topic | fallback path |
|---|---|---|---|
| 1 | 2026-04-29 08:50 | r1 substrate-independence-akida | in-context synthesis (anima) |
| 2 | 2026-04-29 19:00 | r2 brainstorm-exhaustion | in-context synthesis (anima) |
| 3 | 2026-04-29 19:50 | r3 sim-universe refire-3 | in-context synthesis (nexus) |
| 4 | 2026-04-29 20:30 | r3 substrate-independence refire-3 | in-context synthesis (anima) |
| 5 | 2026-04-30 19:50 | r4 paradigm-v12 axis-expansion (anima) | in-context synthesis |
| 6 | 2026-04-30 19:55 | r4 paradigm-v12 axis-expansion (nexus) | in-context synthesis |
| 7 | 2026-04-30 20:05 | r4 review-and-impl-plan | in-context synthesis |
| 8 | 2026-04-30 11:06 | real-kick-test retry | FAIL confirmed (this audit) |

## raw 102 repair-task allocations
- **REPAIR-KICK-2026-04-29-r3-witness-not-captured** (r3-era; OPEN — original kick_health_monitor 5-min auto-heal LIVE but witness emission still failing)
- **REPAIR-KICK-LB-ROUTING-2026-04-30** (this session) — kick_dispatch ubu2-hardcoded path; LB-aware host selection over {ubu1, ubu2, hetzner} pool
- **REPAIR-KICK-SLOT-POOL-VISIBILITY-2026-04-30** (NEW — this audit) — `claude_slot_pick.hexa --list` should expose remote-host pool, not just mac-local; OR kick_dispatch FAIL message should explicitly cite the REMOTE slot table

## Fix recommendations
1. **Short-term (no code change)**: explicit operator awareness — when kick FAILs `all-claude-slots-exhausted`, do NOT trust mac-local `--list`; query remote table directly. Document in `hive/.raw` raw 100 P305 entry.
2. **Medium-term**: extend `claude_slot_pick.hexa --list` with `--remote` flag that queries actual ubu1/ubu2/hetzner slot pool (the table the user quoted earlier).
3. **Long-term (REPAIR-KICK-LB-ROUTING)**: `kick_dispatch.hexa` should call `claude_slot_pick.hexa --remote --pick-most-free` BEFORE spawning, then route to least-loaded host. Currently appears hardcoded to ubu2.

## Sentinels
__KICK_AUDIT__ DIAGNOSTIC pool=2-divergent fallback_count=8 repair_tasks=3
__SLOT_POOL_DIVERGENCE__ mac_local_says_12_available remote_says_all_active_or_cooldown

## Carry-forward
- File raw 100 P305 history-line update with cumulative count 8 (was 7 anchor 2026-04-27)
- Block r5 emission until ≥1 remote slot frees OR raw 100 fallback expressly authorized for r5 also (already standard procedure)
- Schedule REPAIR-KICK-LB-ROUTING + REPAIR-KICK-SLOT-POOL-VISIBILITY follow-up in separate ω-cycles when slot pool recovers
