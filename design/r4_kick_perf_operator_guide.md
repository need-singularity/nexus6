# r4 kick perf — operator quick reference

Session deliverable: 15 hive tools + 5 launchd plists + 4 L3 ledgers + 6 L5
dashboards landed during 2026-04-27 /loop session. This is the operator
quick-reference. Detailed history in `convergence/r4_kick_perf_fallback_synthesis_2026_04_27.convergence`.

## Daily quick-check

```sh
# At-a-glance (38 chars, 4 axes)
hive-exec dispatch_status_line
# → [FAIL 0.347 █▇▇▁▇▇▁▇] [DEFER 8/3] [stuck=0] [cap=16]

# Single yes/no health gate
hive-exec cluster_master_verdict
# → __CLUSTER_MASTER_VERDICT__ DEGRADED rate=FAIL(0.347) slot=PASS(5) stuck=0 regression=0

# Daily autonomous log
tail /Users/ghost/.hx/log/dispatch-failure-rate-trend.log
# → 9-sentinel snapshot from Sub-CN cron
```

## L1 tools (hive-exec)

### Monitoring (4)
| Tool | Purpose |
|---|---|
| `dispatch_failure_rate_lint` | measure 30d rate (raw 100 P305 falsifier) |
| `kick_slot_gate` | live Mac saturation probe |
| `stuck_kick_chain_reaper` | detect/reap stuck-pipe zombies |
| `cluster_master_verdict` | composite single yes/no health gate |

### Cleanup (2)
| Tool | Purpose |
|---|---|
| `hexa_runtime_sweeper` | /tmp/.hexa-runtime cleanup + Sub-CA regression detect |
| `tmp_artifact_sweeper` | wider /tmp pattern cleanup |

### Trend dashboards (4 axis + 1 cross + 1 capacity)
| Tool | Purpose |
|---|---|
| `dispatch_failure_rate_trend` | rate 7d trend dashboard |
| `kick_slot_gate_trend` | slot 7d trend dashboard |
| `stuck_kick_chain_trend` | stuck 7d trend dashboard |
| `cluster_master_verdict_trend` | master verdict 7d trend |
| `dispatch_correlation` | Pearson r (rate ↔ defer cross-axis) |
| `cluster_capacity_report` | physical-limit verification per host (`--class all`, `--suggest`) |

### Operator surface (1)
| Tool | Purpose |
|---|---|
| `dispatch_status_line` | compact one-liner (shell prompt / TUI) |

### Audit defense (3)
| Tool | Purpose |
|---|---|
| `audit_ledger_emit` | Sub-EI: validating audit-row appender (use this, NOT raw heredoc) |
| `audit_ledger_lint` | Sub-EH: detect malformed rows in .raw-audit |
| `audit_emit_bypass_lint` | Sub-EK: identify tools NOT using Sub-EI emitter |

## L2 cron (autonomous launchd, 5 plists)

| Plist | Cadence | Purpose |
|---|---|---|
| `dev.hexa-lang.hexa-runtime-sweeper` | hourly | /tmp/.hexa-runtime cleanup + Sub-CA regression |
| `dev.hexa-lang.tmp-artifact-sweeper` | hourly | wider /tmp cleanup |
| `dev.hexa-lang.dispatch-failure-rate` | daily | Sub-BN measurement → Sub-CG ledger |
| `dev.hexa-lang.dispatch-failure-rate-trend` | daily | 9-sentinel cluster health snapshot |
| `dev.hexa-lang.audit-ledger-lint` | daily | Sub-EJ audit-the-auditor scan |

## L3 ledgers (raw 77 schema)

```
state/audit/dispatch_failure_rate.jsonl   (Sub-CG — rate measurements)
state/audit/kick_slot_gate.jsonl          (Sub-CP — saturation events)
state/audit/stuck_kick_chain.jsonl        (Sub-CX — zombie detections)
state/audit/cluster_master_verdict.jsonl  (Sub-DC — composite verdicts)
```

## Capacity tuning workflow

```sh
# 1. Verify physical-limit position
hive-exec cluster_capacity_report --class all

# 2. See unlock recommendations
hive-exec cluster_capacity_report --suggest
# → ready-to-paste export commands

# 3. Apply (optional — only matters for small-class workloads)
# Add to ~/.zshrc:
#   export HEXA_REMOTE_PSI_CLAMP_BASE_HETZNER=60
#   export HEXA_REMOTE_PSI_CLAMP_BASE_UBU=12

# 4. Re-verify
hive-exec cluster_capacity_report --class all
```

## Goal-achieved baseline (2026-04-27T19:33Z)

```
hetzner: dyn=14 clamp=16 effective=14 binding=RAM (avail=125GB PSI=0)
ubu:     dyn=3  clamp=8  effective=3  binding=RAM (avail=29GB PSI=0)
ubu2:    dyn=0  clamp=1  effective=0  binding=RAM (avail=10GB PSI=97 anima)
total = 17 medium-class concurrent slots cluster-wide, ALL binding=RAM
```

All hosts at physical/mathematical RAM-bound limit. Software ceiling no
longer constrains medium/large/gpu workloads. Small-class has 43 latent
slots on hetzner if workload mix shifts (use `--suggest` recommendations).

## Auto-response chain (3 axes)

| Axis | Trigger | Action |
|---|---|---|
| Sub-CK (rate) | FAIL/WARN/PASS transition | improving=advisory; PASS streak≥30=retire-suggest |
| Sub-CL (race) | cache_err state.swap detected | audit row + raw 66 trailer |
| Sub-DG (master) | HEALTHY/DEGRADED/CRITICAL transition | CRITICAL=immediate Sub-CC kickstart |

## Audit trail

```
/Users/ghost/core/nexus/.raw-audit  (raw 85 schema, 50 session rows)
```

All session-edited files chflags uchg locked. Every edit carries verified=true
audit row. raw 1 + raw 85 invariants preserved.
