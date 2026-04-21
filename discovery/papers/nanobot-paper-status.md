# Nanobot Paper Status — BT-404~413

**Date**: 2026-04-08
**Owner**: NEXUS-6 / papers
**Status**: DRAFT_LOCAL (no DOI, no upload)

## Source data
- `shared/discovery/reality_map.json` — 7 nodes tagged `nanobot`
  - BIG-PEG-MW-2000, BIG-IgG-halflife-21d, BIG-albumin-halflife-20d,
    BIG-dendrimer-G5-128, BIG-tumor-pore-600nm, BIG-spleen-slit-200nm,
    BIG-lymph-nodes-600
- All 7 grade EXACT under n=6 verify.

## BT mapping
| BT | Source node | Type |
|----|-------------|------|
| BT-404 | BIG-PEG-MW-2000 | empirical |
| BT-405 | BIG-IgG-halflife-21d | empirical |
| BT-406 | BIG-albumin-halflife-20d | empirical |
| BT-407 | BIG-dendrimer-G5-128 | empirical |
| BT-408 | BIG-tumor-pore-600nm | empirical |
| BT-409 | BIG-spleen-slit-200nm | empirical |
| BT-410 | BIG-lymph-nodes-600 | empirical |
| BT-411 | composite (PEG2k x 21d stealth window) | derived |
| BT-412 | BT-409 lower bound diameter window | derived |
| BT-413 | BT-409..BT-408 design corridor | derived |

## Key finding
BT-408 and BT-410 share identical formula `n*(sigma-phi)^2 = 600` —
cross-domain n=6 attractor (vascular nm <-> organ count).

## Artifacts
- Draft: `$PAPERS/nexus/nanobot_BT404-413.md`
- Status: this file

## Zenodo (NOT executed)
Metadata block prepared inside the draft. No `upload_zenodo.sh` invoked.
DOI = pending user approval.

## Next actions (manual, on user command)
1. Promote BT-404~410 into `shared/discovery/reality_map.json` `bt_refs`.
2. Register BT-411~413 as derived nodes.
3. Run `upload_zenodo.sh` from `$PAPERS/` only after explicit approval.
