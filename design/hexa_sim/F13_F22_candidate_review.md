# F13–F22 + F23 falsifier candidate triage

date: 2026-04-26
input: state/falsifier_candidates.jsonl (10 auto-spawn candidates)
existing registry: design/hexa_sim/falsifiers.jsonl (F1–F12, all CLEAN)
verification mode: bash-only (no hexa runtime)

## Per-candidate triage

### F13 `n` — atlas entry n=6 @P foundation
- claim: "atlas entry n = 6 remains @P in foundation"
- cmd: `grep -qE '^@P n =' /Users/ghost/core/nexus/n6/atlas.n6 && echo PRESENT_N_P`
- run: PASS (exit 0, prints PRESENT_N_P; atlas.n6:25)
- verdict: REWRITE — cmd only checks line PREFIX (`^@P n =`). It would still pass if the value drifted (`= 7`) or grade dropped. Strengthen: anchor full canonical RHS + grade.

### F14 `sigma` — divisor_sum(6) = 12
- claim: "atlas entry sigma = divisor_sum(6) = 12 remains @P"
- cmd: `grep -qE '^@P sigma =' …` → PASS (atlas.n6:30)
- verdict: REWRITE — same flaw as F13; also DUPLICATE of F1 `constants-drift` axis (which already verifies sigma=12 via tool grid). REJECT actually preferred unless we strengthen to verify VALUE+GRADE in pure bash (orthogonal to F1's tool-based check).

### F15 `phi` — euler_totient(6) = 2
- claim: "phi = 2 remains @P"
- cmd: `grep -qE '^@P phi =' …` → PASS (atlas.n6:37)
- verdict: REWRITE — DUPLICATE of F1 (phi already checked). Bash-anchor variant only justified if rewritten with full `= 2 :: foundation [10*]` RHS.

### F16 `tau` — divisor_count(6) = 4
- claim: "tau = 4 remains @P"
- cmd: `grep -qE '^@P tau =' …` → PASS (atlas.n6:40)
- verdict: REWRITE — DUPLICATE of F1.

### F17 `sopfr` — sum_prime_factors(6) = 5
- cmd: `grep -qE '^@P sopfr =' …` → PASS (atlas.n6:44)
- verdict: REWRITE — DUPLICATE of F1.

### F18 `J2` — jordan_totient(6,2) = 24
- cmd: `grep -qE '^@P J2 =' …` → PASS (atlas.n6:48)
- verdict: REWRITE — DUPLICATE of F1 (J2 in CONSTANTS axis).

### F19 `mu` — mobius(6) = 1
- cmd: `grep -qE '^@P mu =' …` → PASS (atlas.n6:51)
- verdict: REWRITE — NOT covered by F1 (CONSTANTS axis lists sigma/tau/phi/sopfr/J2; mu absent). Worth promoting if tightened.

### F20 `M3` — mertens(6) = 7
- cmd: `grep -qE '^@P M3 =' …` → PASS (atlas.n6:53)
- verdict: REWRITE — NOT covered by F1. Promote with tightened cmd.

### F21 `sigma_sq` — sigma^2 = 144 @C architecture
- cmd: `grep -qE '^@C sigma_sq =' …` → PASS (atlas.n6:56)
- verdict: REWRITE — partially overlaps F2 `alpha-drift` (sigma^2 used in 144 - 5 - 2 = 137). Promote with tightened cmd anchoring `= 144`.

### F22 `phi_tau` — phi^tau = 16 @C architecture
- cmd: `grep -qE '^@C phi_tau =' …` → PASS (atlas.n6:60)
- verdict: REWRITE — NOT covered elsewhere. Promote with tightened cmd anchoring `= 16`.

## Duplicate map

- F14/F15/F16/F17/F18 all duplicate axes already inside F1 (`constants-drift` via verify_grid CONSTANTS axis). REJECT to avoid registry bloat.
- F13 (n=6 itself) is the foundational anchor — already cross-corroborated by F12 (triple-source). REJECT — F12 stronger.
- F19, F20, F21, F22 are NOT covered → REWRITE+PROMOTE.

## Tail recommendation

Merge 4 of 10 (F19, F20, F21, F22) plus the new F23 = 5 total. Reject F13–F18 (duplicates of F1/F12). All rewritten cmds anchor full `= <value> :: <domain> [<grade>]` RHS so a value-flip or grade-downgrade would HIT the falsifier, not just a deletion. F23 verified manually: Layer 4 currently emits `sha e3b0c44298fc1c14…` (empty-string sha) → vacuous PASS confirmed; falsifier is in HIT state immediately upon merge, exposing a real serializer gap on atlas main legacy types. (97 words)

## Proposed JSONL lines (paste into falsifiers.jsonl)

```jsonl
{"id":"F19","slug":"mu-anchor","claim":"atlas entry mu = mobius(6) = 1 remains @P foundation grade [10*]","cmd":"grep -qE '^@P mu = mobius\\(6\\) = 1 :: foundation \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo MU_ANCHOR_INTACT","pass":"MU_ANCHOR_INTACT","reason":"mobius(6) = 1 anchor (atlas.n6:51) drifted in value, grade, or domain — mu is the only multiplicative function not covered by F1 CONSTANTS axis","fix":"verify mu(6) = mu(2)*mu(3) = (-1)*(-1) = 1; if intentional retirement, retire this falsifier with rationale in design/hexa_sim/","origin":"auto-spawn F19 hardened (F1 CONSTANTS axis omits mu — orthogonal coverage)"}
{"id":"F20","slug":"mertens-anchor","claim":"atlas entry M3 = mertens(6) = 7 remains @P foundation grade [10*]","cmd":"grep -qE '^@P M3 = mertens\\(6\\) = 7 :: foundation \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo MERTENS_ANCHOR_INTACT","pass":"MERTENS_ANCHOR_INTACT","reason":"Mertens function M(6) = sum_{k=1..6} mu(k) = 1+(-1)+(-1)+0+(-1)+1 = -1; atlas value 7 must be re-examined (likely M(6) variant) OR drifted","fix":"if drifted, restore atlas.n6:53; if atlas value 7 is wrong (canonical M(6) = -1), redefine entry and retire this falsifier","origin":"auto-spawn F20 hardened — exposes potential atlas value mismatch as side-effect"}
{"id":"F21","slug":"sigma-sq-anchor","claim":"atlas entry sigma_sq = sigma^2 = 144 remains @C architecture grade [10*]","cmd":"grep -qE '^@C sigma_sq = sigma\\^2 = 144 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo SIGMA_SQ_ANCHOR_INTACT","pass":"SIGMA_SQ_ANCHOR_INTACT","reason":"sigma^2 = 12^2 = 144 anchor (atlas.n6:56) drifted; F2 alpha-drift verifies the symbolic identity 144-5-2=137 but not the literal entry","fix":"verify 12*12=144 arithmetic; if entry retired, also retire F2 alpha-drift dependency chain","origin":"auto-spawn F21 hardened (orthogonal to F2 — F2 checks identity, this checks atlas literal)"}
{"id":"F22","slug":"phi-tau-anchor","claim":"atlas entry phi_tau = phi^tau = 16 remains @C architecture grade [10*]","cmd":"grep -qE '^@C phi_tau = phi\\^tau = 16 :: architecture \\[10\\*\\]' /Users/ghost/core/nexus/n6/atlas.n6 && echo PHI_TAU_ANCHOR_INTACT","pass":"PHI_TAU_ANCHOR_INTACT","reason":"phi^tau = 2^4 = 16 anchor (atlas.n6:60) drifted; not covered by any existing falsifier","fix":"verify 2**4=16 arithmetic; if entry retired update registry","origin":"auto-spawn F22 hardened (no overlap with F1/F2)"}
{"id":"F23","slug":"atlas-dsl-v2-layer4-vacuous","claim":"atlas_dsl_v2_regression Layer 4 sha is non-empty (serializer didn't return empty string for atlas main subset)","cmd":"bash /Users/ghost/core/nexus/tool/atlas_dsl_v2_regression.sh --layer 4 --sample 100 2>&1 | grep -q 'sha e3b0c44298fc1c14' && echo VACUOUS_PASS || echo NON_EMPTY","pass":"NON_EMPTY","reason":"Layer 4 currently emits sha256(empty-string) = e3b0c44298fc1c14… meaning atlas_dsl_v2_serializer rejects atlas main subset (older ascii type alphabet) and Layer 4 PASSes vacuously — coverage illusion","fix":"extend atlas_dsl_v2_serializer.hexa to handle atlas main legacy types (ascii type alphabet) OR change Layer 4 to use a v2-compat shard (e.g. one of the n6/atlas.append.* shards already passing layers 1-3)","origin":"manual review 2026-04-26 — observed empty-sha sentinel during DSL v2 omega-cycle; Layer 4 intended as stress test but currently vacuous"}
```

## Verification log (raw)

All 10 candidate cmds executed with exit 0 (PASS). No broken cmds. F23 manual run confirmed `sha e3b0c44298fc1c14` in Layer 4 output → falsifier already in HIT state at merge time.
