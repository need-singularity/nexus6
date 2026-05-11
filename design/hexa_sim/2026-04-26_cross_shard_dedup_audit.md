# Cross-shard atlas dedup audit (Ω-cycle)

**Date:** 2026-04-26
**Scope:** 8 atlas shards under `~/core/nexus/n6/` (1 main + 7 append)
**Method:** read-only `bash + grep + awk + comm`
**Companion TSV:** `~/core/nexus/state/cross_shard_dup_report.tsv`

---

## Executive summary

| metric | count |
|---|---|
| total entries (raw `^@TYPE id =` rows, with within-shard duplicates) | **9,166** |
| distinct (type, id) pairs across all shards | **9,110** |
| within-shard duplicates | **0** |
| cross-shard duplicate (type, id) pairs | **56** |
| HARMLESS DUP (identical value on both sides) | **56** |
| CONFLICT (different value) | **0** |
| atlas-main re-definition by an append shard | **56** (all from `chip-p5-2.n6`, all benign) |

**Headline:** zero value conflicts. The recent 4-shard historical absorption (anima / hexa-lang / nexus / CANON) is **collision-free** vs main atlas and vs each other. The only cross-shard overlap is the legacy `atlas.append.chip-p5-2.n6` shard, which is **fully superseded** — every one of its 56 entries already exists verbatim in `atlas.n6`.

---

## Per-shard entry counts

| shard | distinct entries | cross-shard dup share |
|---|---:|---:|
| `atlas.n6` | 8,757 | 56 |
| `atlas.append.hexa-sim-bridges.n6` | 42 | 0 |
| `atlas.append.nexus-historical-absorption-2026-04-26.n6` | 95 | 0 |
| `atlas.append.anima-historical-from-nexus-2026-04-26.n6` | 75 | 0 |
| `atlas.append.hexa-lang-historical-from-nexus-2026-04-26.n6` | 88 | 0 |
| `atlas.append.CANON-historical-from-nexus-2026-04-26.n6` | 50 | 0 |
| `atlas.append.chip-p5-2.n6` | 56 | **56 (100%)** |
| `atlas.append.forge-triple.n6` | 3 | 0 |
| **total raw rows** | **9,166** | — |

Notes:
- `atlas.n6` count is for `^@TYPE id =` definition lines; `@R` reference rows with `id:subkey` syntax are counted as separate keys (the `:` is part of the id token).
- The two pre-existing append shards (`chip-p5-2`, `forge-triple`) were not in the user's list of 5 — they predate the recent absorption cycle. `forge-triple` is fully unique; `chip-p5-2` is fully redundant.

---

## CONFLICT list

**None.** All 56 cross-shard duplicate keys carry identical values on both sides. No urgent action required.

---

## HARMLESS DUP list (56, all `chip-p5-2.n6` ↔ `atlas.n6`)

All entries are `@C SOC-*` chip-architecture facts. Showing first / middle / last for brevity (full list in TSV):

| # | type | id | line in chip-p5-2 | line in atlas.n6 | value |
|---:|---|---|---:|---:|---|
| 1 | `@C` | `SOC-A1-sigma-6` | 20 | 17468 | `12 :: chip-architecture [10*]` |
| 2 | `@C` | `SOC-A2-tau-6` | 24 | 17472 | `4 :: chip-architecture [10*]` |
| 3 | `@C` | `SOC-A3-phi-6` | 28 | 17476 | `2 :: chip-architecture [10*]` |
| 4 | `@C` | `SOC-A4-sopfr-6` | 32 | 17480 | `5 :: chip-architecture [10*]` |
| 5 | `@C` | `SOC-A5-identity-24` | 36 | 17484 | `24 :: chip-architecture [10*]` |
| 6 | `@C` | `SOC-A6-uniqueness-n6` | 40 | 17488 | `1 :: chip-architecture [10*]` |
| 7 | `@C` | `SOC-B-cognitive` | 50 | 17498 | `EXACT900 :: chip-architecture [10*]` |
| 8 | `@C` | `SOC-B-compute` | 46 | 17494 | `EXACT900 :: chip-architecture [10*]` |
| 9 | `@C` | `SOC-B-culture` | 54 | 17502 | `EXACT900 :: chip-architecture [10*]` |
| 10 | `@C` | `SOC-B-energy` | 58 | 17506 | `EXACT900 :: chip-architecture [10*]` |
| ... | (44 more SOC-B/C/E/F/T axis rows, all identical) | | | | |
| 55 | `@C` | `SOC-T14-identity-uniqueness` | (chip-p5-2) | (atlas.n6) | `1 :: chip-architecture [10*]` |
| 56 | `@C` | `SOC-T15-signoff-hash` | (chip-p5-2) | (atlas.n6) | `n6_τ4_σ12_φ2_id24_uniq1 :: chip-architecture [10*]` |

Family breakdown (all 56 are within these axes):
- `SOC-A*` (6): identity / σ τ φ sopfr / uniqueness — 6 dups
- `SOC-B*` (10): exposure axes (compute, cognitive, culture, energy, infra, life, materials, physics, sf-ufo, space) — 10 dups
- `SOC-C*` (7): topology (identity, tier1, top-forward, run-seq, port-width, pipe-depth, top-forward-det) — 7 dups
- `SOC-E*` (6): tier latency / power — 6 dups
- `SOC-F*` (12): pipe / rvq / embed / emotion / prosody / die-area / pad / selforg / chunk / sample-rate / signoff — 12 dups
- `SOC-T*` (15): tapeout sign-off (DRC, LVS, timing, power, SI, antenna, ESD, io-ring, substrate, metal-fill, CMP, ERC, DFM, identity-uniqueness, signoff-hash) — 15 dups

---

## Atlas-main conflicts

**None.** The 4 historical-absorption append shards (anima / hexa-lang / nexus / CANON) and the bridge shard (`hexa-sim-bridges`) **do not redefine any main-atlas entry**. The id-namespacing scheme used in the absorption cycle (e.g. `nexus-historical-...`, `anima-historical-...`) is working as designed.

The 56 chip-p5-2 ↔ atlas.n6 collisions are **not redefinitions in the absorption sense** — they are residue from a 2025-12-era absorption (commit `842eb068 chore(shared-decommission P3.3-nexus)`) that copied SOC-* into main atlas without removing the source append shard. Both sides have remained byte-identical since.

---

## Recommended actions

### A. HARMLESS DUP (chip-p5-2 ↔ atlas.n6, 56 entries)

**Recommended: retire `atlas.append.chip-p5-2.n6`.**

- Canonical source: **`atlas.n6`** (lines 17468 ff.) — this is where any future SOC-* edits will land per main-atlas convention.
- The append shard adds zero new information and risks future drift if either side is edited independently.
- Action: `git mv n6/atlas.append.chip-p5-2.n6 archive/n6/atlas.append.chip-p5-2.n6.retired-2026-04-26` or simply delete (atlas.n6 already carries the data verbatim).
- Skip if there's an external reader / loader that points at the append path — check `nexus/tool/atlas_*.hexa` for hardcoded paths first.

### B. CONFLICT (none)

No action.

### C. Forge-triple, hexa-sim-bridges (unique entries)

Keep as-is. Both shards add net-new ids and have zero overlap.

### D. Tooling improvements

1. **`atlas_dsl_v2_serializer` / `atlas_index`: add a cross-shard collision check.**
   Each load should hash `(type, id) → shard, line`. On second occurrence of the same key:
   - if value byte-equal: warn `HARMLESS_DUP` (severity: notice).
   - if value differs: error `CROSS_SHARD_CONFLICT` (severity: block).
   Exit code 76 (per raw 44 hard-fail convention) on conflict so CI catches drift before merge.

2. **CI guard.** Add `tool/atlas_cross_shard_dedup.hexa` (~30 lines, `bash+grep+awk` per this audit) that produces the same TSV and fails when `value_a_eq_value_b == NO` exists. Run in `.github/workflows/atlas-lint.yml` on PR.

3. **`@R id:subkey` discipline.** The largest within-id sub-namespacing happens via `@R id:-suffix`. The audit treats `id:subkey` as a single token (correct per current grep), but if future tooling parses on `:`, it would mis-bucket. Document this in `~/core/nexus/design/atlas_dsl_v2.md` or the closest spec.

4. **Promotion path for absorbed shards.** Once the 4 historical-absorption append shards (anima, hexa-lang, nexus, CANON) are stable, consider merging them into `atlas.n6` (mirroring the chip-p5-2 pattern) — but only AFTER deciding whether to retain `atlas.append.*` as the canonical SSOT (in which case the chip-p5-2 case suggests the opposite migration — pull SOC-* OUT of atlas.n6 back into the append shard). This audit does not recommend a direction, only that the policy be explicit.

---

## Reproduction

```bash
cd /tmp/dedup_audit
for sh in ~/core/nexus/n6/atlas.n6 ~/core/nexus/n6/atlas.append.*.n6; do
  base=$(basename "$sh")
  grep -nE '^@[A-Z][A-Z0-9_-]* [^ ]+ =' "$sh" | \
    awk -v sh="$base" '{
      match($0,/^[0-9]+:/); ln=substr($0,RSTART,RLENGTH-1);
      rest=substr($0,RLENGTH+1);
      n=split(rest,a," "); print sh"\t"ln"\t"a[1]"\t"a[2];
    }' > "ids_${base}.tsv"
done
cat ids_*.tsv > all_ids.tsv
awk -F'\t' '{print $3"\t"$4"\t"$1}' all_ids.tsv | sort -u | \
  awk -F'\t' '{print $1"\t"$2}' | sort | uniq -c | awk '$1>=2'
```

Output TSV (with value comparison): `~/core/nexus/state/cross_shard_dup_report.tsv` (57 lines = header + 56 rows).
