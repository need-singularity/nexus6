# r7 Nexus Kick Auto-Absorb FAIL — Diagnose + Fix

date: 2026-05-01
scope: r7 anima-nexus akida-physical-mathematical-limit-saturation-refire
chain: hive r58 follow-up #5 (commit 5b18dec36) → r7 absorb FAIL → this doc
authors: claude-agent (raw 91 honest C3)

## TL;DR

r7 kick LLM-stage PASS but `__KICK_AUTO_ABSORB__ FAIL reason=ingest-rc-1`,
followed by `__KICK_RESULT__ FAIL reason=witness-schema-invalid`. Witness
landed at 6626 bytes but is **truncated** — JSON parse fails at line 114
char 6619 with "Unterminated string". Atlas ingest correctly rejected.

**Root cause:** `kick_dispatch.hexa:1604` used `out.index_of("<<WITNESS_JSON_END>>")`
which matched the **first** occurrence. The witness JSON body itself contained
the literal string `"<<WITNESS_JSON_END>>"` as a field value inside `emit{}`
metadata (LLM cited the delimiter as schema doc). Extraction stopped at the
inner mention, dropping ~50% of the witness body — including the `axes_surfaced[]`
array, `tier_1_promotions[]`, `honesty_triad{}`, and trailing closers.

**Fix:** B (inline kick_dispatch patch, no remote sync needed).

---

## 5 candidate verdicts (raw 91)

| # | candidate | verdict | evidence |
|---|---|---|---|
| 1 | ubu2 stale kick_dispatch | NOT-CAUSE | r7 kick fired from Mac per session log; Mac canonical sha=8cf76391 has stdout-capture (line 1601+) |
| 2 | LLM ignored delimiters | NOT-CAUSE | witness file landed (6626 bytes), confirms delimiters present; `emit.mode = "stdout-delimited"` field shows LLM honored protocol |
| 3 | substring detect failed (encoding/whitespace) | NOT-CAUSE-EXACTLY | detect succeeded; truncation is **earlier-than-intended match**, not no-match |
| 4 | stdout leaked to stderr | NOT-CAUSE | `exec(... + " 2>&1; echo __RC=$?")` merges streams; whole stream available |
| 5 | nexus_root() resolve to ~/Dev | NOT-CAUSE | r7 ran on Mac (per `_nexus_root()` candidate fleet, $HOME/core/nexus matches first) |
| **6 (added)** | **first-match close-marker hit JSON internal field** | **CAUSE** | `out.index_of(_ws_marker_close)` returned position inside `emit.delimiter_end: "<<WITNESS_JSON_END>>"`; truncated witness ends mid-string at that exact field |

## Evidence trail

1. Witness file: `$NEXUS/design/kick/2026-04-30_anima-nexus-akida-physical-mathematical-limit-saturation-ref_omega_cycle.json` — 6626 bytes, `python3 -m json.tool` → JSONDecodeError "Unterminated string starting at: line 114 column 24 (char 6619)"
2. Last lines of truncated file:
   ```
   "emit": {
     "mode": "stdout-delimited",
     "delimiter_start": "<<WITNESS_JSON_START>>",
     "delimiter_end": "
   ```
3. Truncation point is inside the value `"<<WITNESS_JSON_END>>"` — the witness self-references the close-delimiter as a metadata field, and `index_of` matched it.
4. Mac canonical `kick_dispatch.hexa` line 1604 (pre-fix): `let _ws_close = out.index_of(_ws_marker_close)` — first-match.
5. ubu2 sha audit: `~/core/nexus/tool/kick_dispatch.hexa` (40a07b7a, 0 markers) is stale; `~/Dev/nexus/tool/kick_dispatch.hexa` (1177b206, 4 markers) has stdout-capture; Mac (8cf76391) is the latest. r7 fired from Mac, so the active path is Mac canonical — Fix A (sync ubu2) is not load-bearing for this specific failure.

## Fix (applied this turn)

**Fix B + C** in `tool/kick_dispatch.hexa`:

1. Replace `out.index_of(_ws_marker_close)` → `out.last_index_of(_ws_marker_close)` (line 1604). Outermost close-delimiter wins; field-value mentions become safe substrings.
2. Replace `out.index_of(_ws_marker_open)` → `out.last_index_of(_ws_marker_open)` (line 1603). Symmetric — defends against prompt-echo regions where the LLM quotes the task instructions back.
3. Switch witness persistence from `printf '%s' '...'` (vulnerable to ARG_MAX truncation on macOS at ~256KB) to heredoc pipe `cat > path << EOF_KICK_WITNESS_R7FIX_2026_05_01\n...\nEOF_...\n`.
4. Strengthen prompt: explicit instruction "the literal strings `<<WITNESS_JSON_START>>` / `<<WITNESS_JSON_END>>` MUST appear EXACTLY TWICE in entire stdout — never as field values inside witness JSON. Use synonyms if referencing."

**Fix A NOT applied** — ubu2 stale `~/core/nexus/tool/kick_dispatch.hexa` is a separate concern (sister-side hygiene); not the cause of this r7 failure. Defer to operator-confirmed cross-host sync.

## Integration test

`tests/integration_r7_absorb_fix.hexa` (~120 LoC) covers:

- F1: extraction with delimiters in correct positions → full body extracted
- F2: extraction with `<<WITNESS_JSON_END>>` literal inside JSON body → last_index_of wins, full body still extracted
- F3: extraction with prompt-echo region (LLM quotes task instructions before emitting actual delimiters) → last-pair wins
- F4: extraction with both delimiters absent → no-op, witness_path untouched
- F5: extraction with start-only (open marker present, close missing) → no-op (_ws_close < 0 guard)
- F6: large witness body (~200KB simulated) via heredoc — verifies ARG_MAX bypass

Test is a unit-style hexa fixture (no claude binary call), executed via mock stdout strings.

## r7 retry feasibility

**Retriable now**: re-fire r7 with the fixed `kick_dispatch.hexa`. Expected outcome — last-pair extraction yields complete witness, atlas ingest accepts, `__KICK_AUTO_ABSORB__ PASS` lands.
