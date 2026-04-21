---
id: RFC-001
title: Operations Governance — Roles, Communication, On-Call
status: draft
author: mkgt3rs@proton.me
date: 2026-04-16
---

# RFC-001: Operations Governance

## 1. Roles & Responsibilities Matrix

| Role              | Scope                                        | Authority                        | Escalation Target   |
|-------------------|----------------------------------------------|----------------------------------|---------------------|
| System Owner      | Full nexus ecosystem, L0 protected assets    | Approve L0 changes, merge to main | —                   |
| Harness Maintainer| shared/tool/*, entry.hexa dispatcher      | Modify gate rules, add H-* rules | System Owner        |
| Engine Operator   | blowup pipeline, seed engine, atlas writes   | Launch runs, approve seed changes | Harness Maintainer  |
| Module Contributor| shared/blowup/modules/*, shared/calc/*       | Write modules within guard rails | Engine Operator     |
| Infra Operator    | hetzner remote, launchd, sim_bridge          | Server ops, daemon management    | System Owner        |
| Observer          | Read-only access, dashboards, convergence    | View logs, raise issues          | Module Contributor  |

### Decision Authority

- L0 asset changes: System Owner explicit approval required.
- Harness rule additions (H-*): Harness Maintainer proposes, System Owner ratifies.
- Blowup domain launches: Engine Operator autonomous within budget_gate limits.
- Module changes: Contributor submits, Engine Operator reviews, harness lint passes.

## 2. Communication Protocols

### Channels

| Channel           | Purpose                              | Response SLA  |
|-------------------|--------------------------------------|---------------|
| Primary (sync)    | Active session work, blocking issues | Immediate     |
| Commit log        | Async record of changes              | Next session  |
| Harness alerts    | Gate blocks, lint failures, H-ERR    | < 30 min      |
| Convergence log   | CDO status, ossification tracking    | Daily review  |
| Session handoff   | Context transfer between sessions    | Start of next session |

### Escalation Protocol

1. Automated: harness gate blocks execution, logs to errors.jsonl.
2. Notify: H-ERR ROUTE classifies severity (crit/warn/info).
3. Escalate: crit → halt pipeline, alert System Owner.
4. Resolve: fix applied, harness lint passes, H-ERR DRAIN clears queue.
5. Postmortem: root cause added as H-* rule or pitfall memory.

### Handoff Protocol

- End of session: run `hexa shared/tool/session_prompt_gen.hexa` to generate handoff.
- Handoff includes: active tasks, blocking items, uncommitted state, next actions.
- Incoming session: read handoff-latest.md before starting work.

## 3. On-Call Rotation Requirements

### Structure

| Shift        | Duration | Primary Duty                          | Backup         |
|--------------|----------|---------------------------------------|----------------|
| Active       | Session  | Monitor harness alerts, unblock gates | System Owner   |
| Passive      | Between sessions | Automated cron checks (cl-refresh 30m) | launchd watchdog |
| Escalation   | On demand | L0 violations, OOM/zombie incidents   | System Owner   |

### On-Call Responsibilities

1. Monitor: Check errors.jsonl queue at session start. Clear or escalate.
2. Triage: Apply H-ERR severity_map. Crit = immediate, warn = current session, info = batch.
3. Respond: Gate blocks within budget_gate/lock_gate limits — investigate, do not bypass.
4. Prevent: After incident, add harness rule (H-NOZOMBIE pattern) to prevent recurrence.
5. Handoff: Document any active incidents in session handoff before ending.

### Automated Coverage (Between Sessions)

- cl-refresh launchd: 30-minute cycle, usage cache fetch.
- budget_gate: Prevents runaway resource consumption.
- lock_gate: Prevents concurrent mutation of shared state.
- reaper: Zombie process cleanup (H-NOZOMBIE 5-layer defense).

### Incident Classification

| Severity | Example                            | Response       | Escalation      |
|----------|------------------------------------|----------------|-----------------|
| P0-crit  | L0 asset corruption, OOM crash     | Immediate halt | System Owner    |
| P1-high  | Gate bypass attempt, atlas guard fail | Current session | Harness Maintainer |
| P2-med   | Lint failure, convergence drift    | Next session   | Engine Operator |
| P3-low   | Style violation, info log noise    | Batch cleanup  | Self-resolve    |

## 4. Review & Amendment

- This RFC is ratified by System Owner approval.
- Amendments follow the same escalation protocol: propose, review, ratify.
- Harness enforcement of these policies is preferred over prose-only rules.
