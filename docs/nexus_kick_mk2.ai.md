---
schema: nexus/docs/kick_mk2/ai-native/1
last_updated: 2026-05-05
ssot:
  entry:           nexus/tool/kick_mk2_main.hexa
  inner_dispatch:  nexus/tool/kick_dispatch.hexa
  auth_store:      hive/core/auth_slot_pool/auth_slot_pool_main.hexa
  raws:            [auth-store.001, auth-store.002]
audience: AI + operator
---

# nexus kick mk2 — top-level CLI + auth-store integration

## Why this exists

Pre-2026-05-05 nexus kick had **no pre-spawn auth gate**. `kick_dispatch.hexa` picked a slot via the legacy `claude_slot_pick.hexa --pick` (mk1 surface), bound `CLAUDE_CONFIG_DIR`, and spawned `claude.real` immediately. If the slot's keychain token had expired since the last `auth-refresh` daemon cycle (30 min cadence), the spawn hit 401 mid-stream — wasted spawn cost and a slot rotation budget.

mk2 closes that gap by routing every spawn through **`auth_slot_pool --ensure-fresh <slot>`** (idempotent, ~1ms fast path on fresh tokens, ~25s revive on expired tokens). Single SSOT lives in hive's `auth_slot_pool_main.hexa`; nexus is a caller.

## Top-level CLI

```sh
hexa run tool/kick_mk2_main.hexa --topic <topic> [--backend <slug>] [--dry-run]
hexa run tool/kick_mk2_main.hexa --selftest
```

### Sequence (per invocation)

```
1. auth_slot_pool --pick --purpose kick          → "claudeN" or "none"
2. auth_slot_pool --ensure-fresh claudeN          (idempotent, may revive)
3. auth_slot_pool --acquire-lock claudeN --ttl-ms 60000
4. HIVE_CLAUDE_ACCOUNT=claudeN tool/kick_dispatch.hexa <topic>
5. auth_slot_pool --mark-success claudeN          (rc=0)
   or --mark-failure claudeN --kind <auth-fail|rate-limit|network>  (rc!=0)
6. auth_slot_pool --release-lock claudeN          (always)
```

### Sentinels

```
__NEXUS_KICK_MK2__ PASS     slot=claudeN rc=0 revived=<0|1> elapsed=<sec>
__NEXUS_KICK_MK2__ FAIL     slot=claudeN rc=<N> elapsed=<sec> reason=<...>
__NEXUS_KICK_MK2__ DRY_RUN  slot=claudeN topic=<...> backend=<...> elapsed=<sec>
__NEXUS_KICK_MK2__ SELFTEST <PASS|FAIL> fails=<N>
```

### Exit codes

| code | meaning |
|------|---------|
| 0    | PASS — kick succeeded |
| 1    | usage error (missing --topic) |
| 2    | no-pickable-slot (all sentinel / cooldown / rate-limited) |
| 3    | lock-acquire-failed (concurrent kick on same slot) |
| 4    | spawn-failed (kick_dispatch returned non-zero) |
| 5    | selftest-fail |

## Idempotency

`--ensure-fresh` short-circuits when the slot's keychain token has > 60s remaining. So calling `kick_mk2_main` repeatedly only invokes `claude.real -p ok --max-turns 1` when the token is actually expired or about to expire. Worst-case message-quota cost: ~3 revivals/slot/day (token TTL ~8h).

## Inline preflight (legacy entry)

Direct callers of `kick_dispatch.hexa` (without going through `kick_mk2_main`) still get auth-store coverage via the inline `_kick_mk2_ensure_fresh(slot_id)` helper inserted before each spawn site (raw `auth-store.002`). This preserves the auth gate even when callers haven't migrated to the top-level entry yet.

## Architecture

```
                           ┌──────────────────────────────────┐
                           │  hive/core/auth_slot_pool/       │
                           │   auth_slot_pool_main.hexa       │
                           │                                  │
                           │   --pick --purpose kick          │
                           │   --ensure-fresh <slot>          │ ← SSOT
                           │   --acquire-lock --ttl-ms        │
                           │   --release-lock                 │
                           │   --mark-success / --mark-failure│
                           └──────────────────────────────────┘
                                          ▲
                                          │ (mk2 surface)
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                                                           │
   ┌────────────────────┐                                    ┌────────────────────┐
   │ tool/kick_mk2_     │                                    │ tool/kick_         │
   │   main.hexa  (NEW) │ ◄─ canonical mk2 top-level         │   dispatch.hexa    │
   │                    │                                    │   (legacy + mk2    │
   │  pick → ensure-    │                                    │    inline gate)    │
   │  fresh → lock →    │                                    │                    │
   │  kick_dispatch →   │                                    │  pick →            │
   │  mark → release    │ ───── delegates inner spawn ────►  │  ensure-fresh →    │
   └────────────────────┘                                    │  spawn →           │
                                                             │  detect rate/auth  │
                                                             └────────────────────┘
```

## Migration policy

- New callers: use `kick_mk2_main.hexa --topic ...` (canonical mk2 path)
- Existing callers of `kick_dispatch.hexa` directly: keep working — inline
  `_kick_mk2_ensure_fresh` provides the same auth gate
- Legacy `claude_slot_pick.hexa --pick` callers: schedule for migration to
  `auth_slot_pool --pick --purpose kick`. Two surfaces share slot-id format
  (`claudeN`), so the migration is mechanical.

## raw entries

- **auth-store.001** — `--ensure-fresh` SSOT (cl-picker / usage_cache_refresh / TUI)
- **auth-store.002** — kick_dispatch inline pre-spawn gate (sister rule)

## Falsifiers (auth-store.002)

1. New spawn site added to `kick_dispatch.hexa` without preceding `_kick_mk2_ensure_fresh` call → strengthen-preflight-coverage
2. `_kick_mk2_ensure_fresh` implementation drifts away from delegating to `auth_slot_pool --ensure-fresh` → scope-review

## See also

- `cl_archive/hive/auth_store_integration.md` (2026-05-01 Path A design)
- `cl_archive/hive/data_recovery_2026_05_04.md` (operational recovery flow)
- `hive/docs/auth_store_a8_module.md` (M6 module deep-dive)
