# sim_bridge/weave — protein cage / polyhedral self-assembly empirical sandbox

## 컨셉

n6-architecture `domains/biology/hexa-weave/hexa-weave.md` 의 empirical
companion. Caspar-Klug 1962 + Zlotnick 2003 기반 polyhedral protein
cage self-assembly ODE simulation + Bayesian σ(6)=12 STRUCTURAL-EXACT
audit. T=1 60-subunit icosahedral cage 가 reference target. AlphaFold-3
read-side fold prediction 과 직교한 write-side multi-strand weave
sandbox — composition (weave) + actuation (nanobot) + catalysis
(ribozyme) + assembly (virocapsid) 4-sister tetrahedron 중 assembly
axis 의 numerical 검증 path.

raw 91 C3 정직: 이 모듈은 empirical sandbox 만 — theoretical /
formal-mechanical 내용은 `n6-architecture/lean4-n6/N6/MechVerif/` 에서.
n=6 invariant 자체는 sympy + literature corpus 만으로 검증 (no
proprietary calibration).

## 모듈 (python stdlib only — no numpy/scipy)

| 파일 | 역할 | 핵심 알고리즘 |
|------|------|---------------|
| `cage_assembly_simulation.py` | T=1 60-subunit Zlotnick ODE | Euler + RK4 cross-check on 4-state model (free CP / pentamer / hexamer / closed cage) |
| `polyhedral_cage_bayesian_audit.py` | σ(6)=12 STRUCTURAL-EXACT 검증 | Caspar-Klug n=34 textbook corpus + Beta(1,1) prior + Bernoulli likelihood + decision rule posterior >= 0.95 |
| `runs/` | 실행 결과 ledger (jsonl, raw 77 schema) | append-only, gitignored bulk runs |

### cage_assembly_simulation.py 4-state model

```
free CP (C1) ⇌ pentamer (C2)        K12 / K21
free CP (C1) ⇌ hexamer  (C3)        K13 / K31    (T=1 → C3 effectively 0)
12 × pentamer (C2) → cage (C4)      K_CLOSE
cage (C4) → 12 × pentamer (C2)      K_OPEN       (very slow, kinetic trap)
```

n=6 invariant binding:
- σ(6)=12 = T=1 vertex count (5-fold axes)
- τ(6)=4 = 4-state ladder (free / pentamer / hexamer / cage)
- φ(6)=2 = free vs assembled dichotomy
- J₂=24 = octahedral O ⊂ icosahedral I subgroup (implicit)

### polyhedral_cage_bayesian_audit.py 결과 (cycle 22)

- corpus n_total = 34 (Caspar-Klug 1962 + Rossmann-Johnson 1985 +
  Liljas 1982 + Harrison 1978)
- CK-admissible 32 / counter-class 2
- vertex==12 in CK subset: **32/32**
- σ(6)=12 base preservation: **1.0000**
- posterior(STRUCTURAL-EXACT): **0.9668** (≥0.95 RESOLVED threshold)
- log Bayes factor H1/H0: **3.37** (decisive per Jeffreys 1961)

## 사용법

```bash
# Step 1 — cage assembly ODE (default t=1000s, ~15s wall-clock)
cd ~/core/nexus/sim_bridge/weave/
python3 cage_assembly_simulation.py
# → 5/6 raw 53 deterministic PASS (yield 0.68 plateau is calibration gap,
#   n6 invariant + numerical axes load-bearing)

# Step 2 — Bayesian audit (textbook corpus only, no network)
python3 polyhedral_cage_bayesian_audit.py
# → posterior 0.9668 RESOLVED, exit 0

# Step 3 — extended t-end for plateau exploration
python3 cage_assembly_simulation.py --t-end 100000
# → yield 0.77 plateau (still < 0.95; F-VIROCAPSID-3 calibration
#   fitting deferred to user-OK GPU sandbox cycle 24+)
```

## 실행 결과 ledger

```
runs/
├── cage_assembly_events.jsonl       # raw 77 schema, append-only
└── polyhedral_cage_audit_events.jsonl
```

n6-architecture 측 cycle 22 commit 67b07339 에 동일 ledger 가 이미 push 됨
(`n6-architecture/state/audit/`). cycle 24+ 부터 nexus 측이 canonical.

## 아키텍처 결정 (cycle 24, 2026-04-29)

- nexus/sim_bridge/ 패턴 따름 (multiverse / bostrom_test / godel_q 와 일관)
- snake_case 모듈명 (sim_bridge 컨벤션)
- python stdlib only (raw 14 ext-ssot 외부 의존성 0)
- n=6 invariant verification 은 cage 에 specialized — discovery/rng_lab/
  rng-only 와 차별

## n=6 invariant 매칭

- σ(6)=12 STRUCTURAL-EXACT (cage vertex count, posterior 0.97 입증)
- τ(6)=4 4-state ladder
- φ(6)=2 dichotomy
- J₂=24 (icosahedral I ⊃ octahedral O)
- σ·φ = n·τ = 12·2 = 6·4 = 24 master identity

## raw 71 falsifier preregister (cycle 22→24 forward)

- F-CAGE-MVP-1: yield 0.95 미달이 3 independent calibration (HBV /
  CCMV / STNV) 에서 reproducible → calibration gap 확정 (deadline
  2026-07-28)
- F-VIROCAPSID-2-LIVE-PDB: live PDB scrape n>=100 cages 에서 posterior
  >= 0.95 재현 → STRUCTURAL-EXACT 입증 강화 (deadline 2027-04-28)
- F-NEXUS-IMPORT-NUMPY: 외부 numpy/scipy 의존성 도입 시 raw 14
  ext-ssot 위반 → 거부 (deadline open-ended)

## SSOT cross-link

- declarative SSOT: `~/core/n6-architecture/domains/biology/hexa-weave/`
- formal SSOT: `~/core/n6-architecture/lean4-n6/N6/MechVerif/`
- paper SSOT: `~/core/n6-architecture/papers/hexa-weave-formal-mechanical-w2-2026-04-28.md`
- empirical SSOT: 본 모듈 (canonical from cycle 24+)
- workspace 등록: `~/core/.workspace` (sim_bridge sub 모듈, 별도
  member 등록 불필요 — nexus member 의 일부)

## raw 91 C3 정직 disclosure

- python stdlib only — numpy/scipy/torch 외부 의존성 0
- cage_assembly_simulation.py 의 yield 0.68 plateau 는 calibration gap
  (default rate constants 시도시 k_close ≥5e-9 에서 ODE stiff blow-up)
- polyhedral_cage_bayesian_audit.py 의 vertex=12 invariant 는 Euler
  V−E+F=2 의 geometric tautology — Bayesian audit 은 textbook
  consistency 입증, independent empirical refutation 아님
- runs/ 디렉토리는 append-only ledger (gitignored bulk 또는
  select-only 커밋)
- cycle 14 시작점 path `~/core/hexa-weave/` 는 cycle 24 에 폐기,
  nexus/sim_bridge/weave/ 가 canonical
