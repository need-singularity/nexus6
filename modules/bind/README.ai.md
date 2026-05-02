---
schema: nexus/modules/bind/README/v1
last_updated: 2026-05-02
ssot: nexus/modules/bind/README.ai.md
status: live
related_specs:
  - hive/spec/dispatch_framework_v1.spec.yaml
related_raws: [91, 92, 117, 264, 267, 270, 271, 272, 273]
related_cores:
  - nexus/core/bind/source.hexa
  - nexus/core/bind/registry.hexa
  - nexus/core/bind/router.hexa
  - nexus/core/bind/bind_main.hexa
related_state:
  - nexus/state/active_bindings.hxc
related_handler:
  - nexus/tool/handlers/outside_noise_clm_handler.hexa
---

# nexus/modules/bind/ — bind axis subscriber modules

## TL;DR

nexus side bind framework subscriber modules. Each module implements
dispatch_framework_v1 Section 2 handler_contract:

```
pub fn on_<axis>_axis_fire(payload: BindPayload) -> BindResult
```

Subscribers are registered in `nexus/state/active_bindings.hxc` (declarative
SSOT) and dispatched by `nexus/core/bind/router.hexa` via subprocess exec to
the matching handler (preserved CLI tool stays byte-identical; subscriber is
a thin axis-fire→CLI-call adapter layer, raw 270/272 dogfood).

## Modules registered (Round 1)

| Axis | Subscriber module | Handler (preserved) | Scope |
|------|-------------------|---------------------|-------|
| `outside_noise` | `outside_noise.hexa` | `nexus/tool/handlers/outside_noise_clm_handler.hexa` (510 LOC, sha e59f09a8) | axis_loop |

## Architecture

```
                    nexus/core/bind/                     nexus/modules/bind/
                    ─────────────────                    ───────────────────
                                                          
   bind_main.hexa ── router.hexa ── (axis: "outside_noise")  ──── outside_noise.hexa
        │                │                                              │
        │                ↓                                              │
        │        nexus_bind_router_pick_handler                         │
        │        ↓                                                      │
        │   registry.hexa  ←── reads ──── state/active_bindings.hxc     │
        │   (declarative SSOT)                                          │
        │                                                               ↓
        │                                              env-encoded subprocess exec
        │                                              with --bind-fire flag
        │                                                               ↓
        ↓                                       nexus/tool/handlers/outside_noise_clm_handler.hexa
   source.hexa                                  (preserved CLI dispatcher,
   (BindPayload/BindResult/                     dual entry path: CLI direct + bind subscriber)
    BindSubscription/BindIssue
    contract structs)
```

## Spec conformance — dispatch_framework_v1 Section mapping

| Section | Implementation | Notes |
|---------|----------------|-------|
| 1 event_schema | `BindPayload`/`BindResult`/`BindSubscription`/`BindIssue` in `source.hexa` | Field-level mirror of TypedPayload/HandlerResult/Subscription/Issue (forward-compat superset) |
| 2 handler_contract | `pub fn on_<axis>_axis_fire(payload: BindPayload) -> BindResult` per module | Default timeout 30s, default cost_cap $0.01 USD |
| 3 subscription_lifecycle | `state/active_bindings.hxc` declarative + `bind_main.hexa` imperative | Drift detection emits F-DISPATCH-2 on validate |
| 4 composition | `axis_loop` scope (sequential default) | Parallel/DAG deferred per stage0 limitation |

## How to add a new axis subscriber

1. Create `nexus/modules/bind/<axis_name>.hexa` (mirrors `outside_noise.hexa`)
2. Implement `pub fn on_<axis_name>_axis_fire(payload: BindPayload) -> BindResult`
3. Register binding in `nexus/state/active_bindings.hxc`:
   ```
   bind axis=<name> handler=<abs_path> scope=axis_loop grade=design predicate=always
   ```
4. Verify: `hexa run nexus/core/bind/bind_main.hexa validate <axis_name>`
5. Test: `hexa run nexus/core/bind/bind_main.hexa fire <axis_name> c0`

## raw#10 caveats (module-level)

1. Subscriber wrapper does NOT re-implement handler logic — preserved CLI
   tool is the source of truth for axis-specific pipeline.
2. Subprocess exec adds dispatch overhead vs direct CLI invocation
   (measured by `nexus/bench/bench_outside_noise_bind.hexa`).
3. cycle_id mapping convention: `c<N>` prefix → handler `--cycle <N>`.
4. MOCK env propagation only works when handler honors `--mock` flag.
5. Verdict normalization grep is brittle — sentinel format change requires
   router._normalize_verdict update.

## Related preserved files (audit byte-identical)

- `nexus/tool/handlers/outside_noise_clm_handler.hexa` — handler (510 LOC, sha e59f09a8)
  - Round 2 patch (THIS BG-B): adds `--bind-fire` flag recognition + new
    function `on_outside_noise_axis_fire` (additive — CLI path preserved).
