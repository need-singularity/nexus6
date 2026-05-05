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

# nexus kick — auth-store integration

## Canonical CLI

```sh
nexus kick <topic>
```

Singleton invariant since 2026-05-01 (`hive kick` BANNED at hive cli
dispatch). The shim at `~/.hx/bin/nexus` raw-200-bypasses the resolver
and dispatches directly to `~/.hx/packages/nexus/cli/run.hexa cmd_kick`,
which calls `tool/kick_dispatch.hexa <topic>`.

## Why mk2 cycle (2026-05-05)

Pre-2026-05-05 `kick_dispatch.hexa` picked a slot, bound
`CLAUDE_CONFIG_DIR`, and spawned `claude.real` immediately. If the slot's
keychain token had expired since the last `auth-refresh` daemon cycle
(30 min cadence), the spawn hit 401 mid-stream — wasted spawn cost and a
slot rotation budget.

mk2 closes that gap by routing every spawn through
**`auth_slot_pool --ensure-fresh <slot>`** (idempotent, ~1ms fast path
on fresh tokens, ~25s revive on expired tokens). SSOT lives in hive's
`auth_slot_pool_main.hexa`; nexus is a caller via the inline
`_kick_mk2_ensure_fresh` helper in `tool/kick_dispatch.hexa`.

## Dispatch chain

```
nexus kick <topic>
  → ~/.hx/bin/nexus  (shim — canonical-form bypass)
  → ~/.hx/packages/nexus/cli/run.hexa  cmd_kick
  → tool/kick_dispatch.hexa
      ↳ _claude_pick_slot()              → "claudeN"
      ↳ _kick_mk2_ensure_fresh(slot)     → hive auth_slot_pool --ensure-fresh
      ↳ claude.real spawn (CLAUDE_CONFIG_DIR=~/.claude-claudeN)
      ↳ detect rate-limit / auth-fail   → rotate or trailer
```

## Sentinel (existing kick_dispatch surface)

```
__KICK_RESULT__ PASS  witness=<path> tier1=<0|1> falsifier_pass=<0|1>
__KICK_RESULT__ FAIL  witness=<path> tier1=<0|1> falsifier_pass=<0|1>
                      reason=<...> fix=<...>
```

## Internal orchestrator (NOT user CLI)

`tool/kick_mk2_main.hexa` is a programmatic mk2 wrapper providing the
full sequence (pick + ensure-fresh + lock + spawn + mark-success/failure
+ release). Sentinel: `__NEXUS_KICK_MK2__`. Intended for hooks, daemons,
or future cli/run.hexa consolidation — NOT human invocation. End users
should always invoke `nexus kick <topic>`.

```sh
hexa run tool/kick_mk2_main.hexa --selftest        # programmatic selftest
hexa run tool/kick_mk2_main.hexa --topic <t> --dry-run
hexa run tool/kick_mk2_main.hexa --topic <t>       # programmatic kick
```

Exit codes (mk2_main): 0 PASS / 1 usage / 2 no-pickable-slot /
3 lock-fail / 4 spawn-fail / 5 selftest-fail.

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
