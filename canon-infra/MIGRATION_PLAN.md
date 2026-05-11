# canon-infra — Migration Plan & Snapshot

**작성**: 2026-05-11
**Source**: `dancinlab/canon@2ad85661`
**Destination**: `dancinlab/nexus/canon-infra/` (이 폴더)
**Commits**: canon `e3e6b16e` (MOVE) · nexus `cf6be439` (import)

---

## 1. 목적

`canon` 리포는 2026-05-06 이후 점진적 축소(Canon Minimization Migration) 중이다.
도메인 자산은 `hexa-*` 표준 호환 리포군으로, AI/ML 자산은 `hexa-codex`로
이미 이관 완료되었다. 본 Wave 3에서는 **canon 인프라(런타임/도구/상태/스키마)**를
`nexus`의 단일 하위 폴더로 통째로 이동시켜 두 가지를 달성한다:

1. canon을 **순수 연구 산출물 저장소**로 정제 (theory + experiments + reports + proposals + papers)
2. canon 런타임 인프라를 **nexus 우주 발견 엔진**과 물리적으로 동거시켜
   소비 지점(nexus)과 정의 지점(canon-infra)의 거리를 0으로 만든다.

---

## 2. 마이그레이션 웨이브 연표

| Wave | 날짜 | 범위 | Canon SHA (pre) | 목적지 | 파일 수 |
|---|---|---|---|---|---:|
| 1 | 2026-05-10 | `papers/` · `theory/proofs/` · `bridge/origins/` 잔류 연구물 | `a86ca143` | 28개 `hexa-*` repos | 228 |
| 1.5 | 2026-05-10 | `domains/` 299개 spec | `ded52144` | 32 standalones | 360 |
| 2 | 2026-05-11 | `techniques/` (68 AI 기법 × 8축) + `experiments/ai-efficiency/` | `93e6ef4c` | `hexa-codex` | 304 |
| **3** | **2026-05-11** | **canon 인프라 24항목** | **`2ad85661`** | **`nexus/canon-infra/`** | **1,808** |
| **4** | **2026-05-11** | **`theory/` (n=6 이론층) + `formal/lean4/`** | **`50e6f679`** | **`hexa-meta`** | **260** |
| **5** | **2026-05-11** | **도메인-귀속 잔여** (chip-verify, hexa-weave proposals, LLM/AI reports, BT 14) | **`ceced262`** | **14 repos** (hexa-chip/bio/codex/cern/rtsc/fusion/cosmos/matter/arts/millennium/forge/meta/aura/senses + anima) | **112** |

---

## 3. 본 Wave 이관 명세

### 3.1 이관된 디렉토리 (16)

| Source | Tracked files | 역할 |
|---|---:|---|
| `engine/` | 19 | n=6 트레이너, anima tension, consciousness constraint, ouroboros verifier, hexa gate mk3, leech24 surface, phi efficiency bridge, thermodynamic frame |
| `scanners/` | 50 | claim.json 형식 invariant 스캐너 (01–54) — arithmetic, falsification(n28/n496/n8128), engine integrity, dispatcher, audit retention, generator orbits 등 |
| `canonshared/` | 45 | SSOT — `_shared_constants.hexa`, `discovery_graph.json`, `discovery_log.jsonl`(symlink), `growth_bus.jsonl`(symlink), `hexa_grammar.jsonl`(symlink), brainstorm/, config/, convergence/, dse/, logs/, n6/, schemas/, tools/ |
| `canon_meta/` | 6 | 메타 docs (doc/) |
| `bridge/` | 31 | Rust 바이너리 src + `crates/dashboard`, `ecosystem_9projects.hexa`, `ouroboros_5phase.hexa`, growth/health/monitor 스크립트 |
| `convergence/` | 1 | (단일 파일) |
| `hooks/` | 1 | `pre-commit-n6-integrity` |
| `tool/` | 70 | canon 도구 70종 |
| `tools/` | 4 | `build_registry.hexa`, `check_drift.hexa`, `inject_provenance.hexa`, `standalone_seeds.tsv` |
| `shared/` | 1 | `roadmaps/` |
| `scripts/` | 26 | 빌드/싱크/감사 (`monotone/`) |
| `design/` | 114 | 설계 문서 |
| `state/` | 1053 | 런타임 상태 — audit, blockers, clay_millennium_kick_loop, cli_authoring, discovery_absorption, falsifier_monitor, hxc, markers, proposals, safety_bypass_audit, sim_cascade_s2, triad_lint |
| `raw_archive/` | 11 | pre-canon 스냅샷 |
| `bin/` | 6 | runtime binaries (`canon_meta`, `check_remote_dispatch.sh`, `hexa-local`, `n6`, `n6_verify_run`, `nx` 심볼릭) |
| `config/` | 9 | launchd plists |

### 3.2 이관된 루트 파일 (8)

| File | 역할 |
|---|---|
| `INDEX.json` | canon 9축 manifest SSOT (theory/domains/bridge/techniques/experiments/engine/papers/reports/canonshared) |
| `hive.json` | hive coordination state |
| `loop-rules.json` | 루프 규칙 |
| `project.hexa` | 프로젝트 선언 |
| `standalone_registry.toml` | standalone repo 레지스트리 (hexa-ufo BUNDLE seed) |
| `build_log.txt` | 빌드 로그 |
| `README.md.sealed.hash` | README 봉인 해시 |
| `Makefile` | test 자동화 (cargo 기반) |

### 3.3 합계
- **Tracked from canon**: 1,457 files (이중 `state/`만 1,053)
- **Copied to nexus/canon-infra/**: 1,808 files (untracked 포함, 일부 broken symlink)
- **Canon LOC 감소**: −152,103 lines
- **Nexus LOC 증가**: +131,965 lines (차이는 .gitignore/untracked 미커밋분)

---

## 4. canon 잔류 자산 (이관 대상 아님)

| 경로 | 크기 | 사유 |
|---|---:|---|
| `theory/` | 5.8M | **연구 SSOT** — proofs/breakthroughs/constants/predictions/roadmap (※ §6 참조) |
| `experiments/` | 157M | DSE/anomaly/meta/blowup/grover_n6_uniqueness/anu_mc 검증 인프라 |
| `reports/` | 11M | audits/sessions/discovery/breakthroughs 메타 기록 |
| `proposals/` | 1.1M | 제안서 (일부 도메인-귀속 가능, §7 참조) |
| `data/` | 170M | cremona/arxiv 연구 데이터 |
| `domains/` | 120K | 표준 포인터 파일 (`_standalone_repos.md`) |
| `lean4-n6/` | 1.5G | Lean4 toolchain 빌드 산출물 |
| `formal/` | 272K | Lean4 정형 증명 (Sigma, Weave) — theory에 의존 |
| `papers/` | — | (비어있음, 이전 wave에서 이관 완료) |
| Root docs | — | `README.md`, `LICENSE`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `MOVED_TO_STANDALONES.md`, `.gitignore` |

---

## 5. 복구 방법

본 이관은 **MOVE 패턴**(canon 측 git rm + nexus 측 신규 import).
canon의 git 히스토리는 무손실로 보존된다.

```bash
# canon 측에서 무엇이 어떤 시점에 옮겨졌는지 확인
cd ~/core/canon
git log --diff-filter=D --follow -- <path-before-move>
git show 2ad85661:<path-before-move>   # MOVE 직전 스냅샷

# nexus 측 현재 위치
cd ~/core/nexus/canon-infra/<same-path>
```

---

## 6. theory/ 이관 — Wave 4 (✅ 완료, 2026-05-11)

사용자 결정: `hexa-meta`로 이관 (대안 신규 `hexa-theory` 미선택).
완료 Commit: canon `ceced262` (MOVE) · hexa-meta `e954dbe` (import).

### 6.0 실행 결과 요약

| 도착 (hexa-meta) | 출발 (canon) | 파일 수 |
|---|---|---:|
| `breakthroughs/` | `theory/breakthroughs/` | 6 |
| `constants/` | `theory/constants/` | 5 |
| `flow/` | `theory/flow/` | 4 |
| `predictions/` | `theory/predictions/` | 117 |
| `preprints/` | `theory/preprints/` | 1 |
| `roadmap-v2/` | `theory/roadmap-v2/` | 65 |
| `roadmap-v3/` | `theory/roadmap-v3/` | 3 |
| `study/` | `theory/study/` | 48 |
| `_theory_index.json` | `theory/_index.json` | 1 (이름 변경) |
| `formal/lean4/` | `formal/lean4/` | 10 (`.olean` 제외) |
| **합계** | — | **260** |

### 6.1 (참고) 사전 검색 결과: **`hexa-meta`** 가 최적 호스트

**근거** (`hexa-meta/README.md` 인용):
> "🌀 hexa-meta — n=6 meta-theory · self-architecture · proof-cert · discovery tooling.
> The n=6 framework reflecting on itself: meta-theorems, self-organizing
> architecture papers, proof-certification chains, and the domain-agnostic
> discovery / DSE / verification tooling that powers every other `hexa-*` repo."

**기존 hexa-meta 구성**:
- `proofs/` (11) — attractor-meta-theorem, ouroboros-alpha-universality, mk4-trident-final-verdict, theorem-r1-uniqueness, honest-limitations, the-number-24, …
- `papers/` (24) — n6-arch-*, n6-mk3-synthesis, n6-cross-dse-matrix-112, n=6-convergence-80-domains, …
- `tools/` (15) — discovery-engine, deep-miner, formula-miner, universal-dse, hypothesis-grader, …

**canon `theory/`의 7 하위축이 깔끔하게 매핑됨**:

| canon path | hexa-meta 목적지 | 비고 |
|---|---|---|
| `theory/breakthroughs/` (2.3M) | `hexa-meta/breakthroughs/` | BT 카탈로그, _hypotheses_index.json |
| `theory/predictions/` (988K) | `hexa-meta/predictions/` | pre-registered + verify_SIG-*.hexa |
| `theory/study/` (1000K) | `hexa-meta/study/` | p0/p1/p2/p3 연구 방법론 |
| `theory/roadmap-v2/` (1.5M) | `hexa-meta/roadmap/` | millennium-v3/v4 디자인, n6arch-axes |
| `theory/roadmap-v3/` (20K) | `hexa-meta/roadmap/` | (v2와 통합 또는 v3 폴더 분리) |
| `theory/constants/` (88K) | `hexa-meta/constants/` | n=6 invariants |
| `theory/flow/` (36K) | `hexa-meta/flow/` | workflow 정의 |
| `theory/preprints/` (16K) | `hexa-meta/preprints/` | preprints |
| `formal/lean4/` (10 files) | `hexa-meta/formal/lean4/` | (선택) Lean4 정형증명 동반 이관 |

### 6.2 대안: 신규 `hexa-theory` 생성

만약 hexa-meta의 "meta-tooling" 성격과 분리하고 싶다면 신규 리포 `hexa-theory`를
만들 수 있다. 사용자 요청 시 **이모지 후보군**:

| 후보 | 의미 | 톤 |
|---|---|---|
| **📐** | 기하·증명·자/컴퍼스 | formal, classical |
| **🧮** | 주판·계산 | 산술/수론 |
| **🔬** | 현미경·검증 | 실험·예측 |
| **📜** | 두루마리·고전 | timeless theory |
| **🌐** | 망·지도 | breakthrough roadmap |
| **🪐** | 행성·궤도 | n=6 우주론 |
| **♾️** | 무한 | ouroboros/순환 |
| **🜔** | 연금술 일라스틱 (rare) | 통합·메타 |

**추천**: `📐` (theory = 증명 + 정밀) 또는 `📜` (timeless 강조). hexa-meta가 이미
`🌀` (ouroboros)을 사용하므로 시각적 구분 확보.

### 6.3 권장 결론 → 적용됨

- ~~1차 권장~~ **선택 완료**: theory/ + formal/lean4/ → `hexa-meta`로 통합 (Wave 4)
- 2차 옵션(신규 `hexa-theory`): 미선택

---

## 7. Wave 5 — 도메인-귀속 잔여 분산 (✅ 완료, 2026-05-11)

이전 세션 보고서에서 식별된 잔류 도메인-귀속 파일들이 Wave 5에서 자연 호스트로 분산되었다.

### 7.0 Wave 5 실행 결과

| Repo | Source | Count | Commit |
|---|---|---:|---|
| hexa-chip | chip-verify (27 chip-only) + samsung-foundry + chip-arch-guide | 29 | `3f2c2b7` |
| anima | verify_anima_soc + consciousness-cluster-bt + consciousness-triple-fusion | 3 | `3c284ca2b` |
| hexa-aura | verify_bci_6ch_n6 | 1 | `ed7eb16` |
| hexa-senses | n6_speak integration bench + report | 2 | `2d10533` |
| hexa-codex | 6 LLM/AI discovery reports | 6 | `baaef0e` |
| hexa-bio | 57 hexa-weave proposals + bt-1387 + bt-1391 | 59 | `ab87022` |
| hexa-cern | bt-1176 nuclear + bt-1386 standard-model | 2 | `b824962` |
| hexa-rtsc | bt-1163-1168 superconductor-v5 | 1 | `2be4afb` |
| hexa-fusion | bt-1169-1174 fusion-v5 | 1 | `ae2f6d9` |
| hexa-cosmos | bt-1108 dimensional-perception | 1 | `668fc65` |
| hexa-matter | bt-1388 ionic-octahedral | 1 | `692257e` |
| hexa-arts | bt-1390 hsv-color-hexad | 1 | `da00292` |
| hexa-millennium | bt-1392 millennium-7-breakthrough-ideas | 1 | `80a23e0` |
| hexa-forge | forge-triple-fusion | 1 | `d603de4` |
| hexa-meta | bt-1389 cube-octahedron-duality (math) | 1 | `7786f12` |
| **합계** | — | **112** | canon `4eb869ad` |

### 7.4 캐넌에 잔류 (분류 약함 또는 일반)

다음 항목은 도메인-귀속이 약하거나 일반 메모로 판단되어 canon에 잔류:

- `proposals/cat_litter_mk2_trial_2026_05_01.md`
- `proposals/critical-mineral-conflict-arbitration_2026_05_06.md`
- `proposals/kim-sangwook-quantum.md`
- `proposals/own1-hard-english-only-translation-roadmap-2026-04-24.md`
- `proposals/yoo-hyunjun-architecture.md`
- `proposals/sod-youtube.md`
- `proposals/south-africa-applied-tech.md`
- `proposals/south-africa-tech-stack-2026-04-25.md`
- `proposals/kolon-materials-z6.md` (calc 측 결정과 일치)
- `reports/breakthroughs/bt-1175-water-treatment-2026-04-12.md` (hexa-earth 후보지만 보류)

## 8. 이전 Wave 추가 후보 (보존)

이전 세션 보고서에서 식별된 잔류 도메인-귀속 파일들 — 본 Wave에 포함되지 않음.

### 7.1 강력 후보

| 자산 | 권장 이관지 |
|---|---|
| `experiments/chip-verify/` (18 files) | `hexa-chip` (verify_anima_soc → anima, verify_bci_6ch_n6 → hexa-aura, n6_speak → hexa-senses 분기 검토) |
| `proposals/hexa_weave_*` + `hexa-weave-*` (57 files) | `hexa-bio` (hexa-weave는 bio 산하) |
| `proposals/samsung-foundry-hexa-6stage.md` | `hexa-chip` |
| `reports/discovery/chip-architecture-guide.md` | `hexa-chip` |

### 7.2 AI/LLM 누락분 → hexa-codex 추가 이관

| 자산 | 권장 |
|---|---|
| `reports/discovery/LLM-001-018-llm-improvement-n6.md` | `hexa-codex` |
| `reports/discovery/LLM-DEEP-architecture-constants-n6.md` | `hexa-codex` |
| `reports/discovery/ai-algorithm-new-hypotheses-2026.md` | `hexa-codex` |
| `reports/discovery/ai-energy-savings-guide.md` | `hexa-codex` |
| `reports/discovery/llm-improvement-new-hypotheses-2026.md` | `hexa-codex` |
| `reports/discovery/n6-optimal-llm-spec.md` | `hexa-codex` |
| `reports/discovery/consciousness-cluster-bt.md` | `anima` |

### 7.3 Breakthrough 도메인-타이트 (총 14)

| BT id | 도메인 |
|---|---|
| bt-1163-1168 superconductor-v5 | `hexa-rtsc` |
| bt-1169-1174 fusion-v5 | `hexa-fusion` |
| bt-1108 dimensional-perception | `hexa-cosmos` |
| bt-1175 water-treatment | `hexa-earth`? |
| bt-1176 nuclear-reactor-kinetics | `hexa-cern` |
| bt-1386 standard-model | `hexa-cern` |
| bt-1387 huckel-aromatic | `hexa-bio`? |
| bt-1388 ionic-octahedral | `hexa-matter`? |
| bt-1389 cube-octahedron-duality | (수학 — 캐넌/hexa-meta 유지) |
| bt-1390 hsv-color-hexad | `hexa-arts` |
| bt-1391 photosynthesis-equation | `hexa-bio` |
| bt-1392 millennium-7-breakthrough-ideas | (밀레니엄 — `hexa-millennium`) |
| consciousness-triple-fusion | `anima` |
| forge-triple-fusion | `hexa-forge` |

### 7.4 약한 후보 (검토 필요)

- `proposals/cat_litter_mk2_trial_2026_05_01.md` → `hexa-pet`?
- `proposals/critical-mineral-conflict-arbitration_*.md` → `hexa-earth`/`hexa-finance`?
- `proposals/kim-sangwook-quantum.md` → `hexa-cern`?
- `proposals/own1-hard-english-only-translation-*.md` → `hexa-lang`?
- `proposals/yoo-hyunjun-architecture.md` → 분류 어려움
- `proposals/sod-youtube.md` → 캐넌 유지 추천
- `proposals/south-africa-*.md` (2건) → 캐넌 유지 추천
- `proposals/kolon-materials-z6.md` → 캐넌 유지 (calc 측 결정과 일치)

---

## 8. 알려진 이슈

### 8.1 깨진 심볼링크 3개 (보존됨)

`canonshared/` 내 다음 심볼릭은 캐넌 원본에서도 이미 깨진 상태였으며, 그대로 보존되었다:

- `discovery_log.jsonl` → `../../nexus/shared/discovery_log.jsonl`
- `growth_bus.jsonl` → `../../nexus/shared/growth_bus.jsonl`
- `hexa_grammar.jsonl` → `../../nexus/shared/config/hexa_grammar.jsonl`

타깃 `nexus/shared/`는 Linux 환경에 존재하지 않음 (원래 Mac 호스트 SSOT 경로).
**현재 위치 기준 상대 경로도 동일하게 깨져 있음** (`nexus/canon-infra/canonshared/../../nexus/shared/` =
`nexus/nexus/shared/`로 잘못 해석). 향후 정리 필요.

**해결안 후보**:
1. `nexus/shared/` 디렉토리 생성 + 실제 파일 배치 (SSOT 복원)
2. 심볼릭 타깃을 `../../discovery_log.jsonl` 등 nexus 루트로 갱신 (실제 파일이 그곳에 존재)
3. 심볼릭 제거 후 실제 파일 복사

### 8.2 `infra_state.json` 심볼릭 제외

canon 루트의 `infra_state.json` → `/Users/ghost/core/nexus/infra_state.json`은
Mac 호스트 절대 경로이며 Linux에서 미해석. 본 이관에서 **이관 대상 제외**.
canon 측에도 untracked 상태 그대로 잔존 (git이 추적하지 않음).

### 8.3 untracked 잔여물

- `build/` (256K, untracked) — 빌드 산출물, 재생성 가능, 캐넌 잔류
- `scratch/` (252K, untracked) — 임시 작업, 캐넌 잔류
- `state/audit/alien_grade_events.jsonl` — 단일 권한 거부 파일, 다른 사본은 정상 이관

---

## 9. 후속 액션 권장 순서

1. **theory/ 이관 결정** (§6) — `hexa-meta` vs 신규 `hexa-theory` 선택
2. **chip-verify 이관** (§7.1) — anima/aura/senses 분기 정리 포함
3. **hexa_weave 제안서 57건 → hexa-bio** (§7.1)
4. **AI/LLM 누락 7건 → hexa-codex** (§7.2)
5. **Breakthrough 14건 도메인 재배치** (§7.3)
6. **canonshared 심볼릭 복구** (§8.1)
7. **canon README + INDEX 갱신** — INDEX.json은 이관되었으므로 canon 측에 축소판 새 INDEX 작성 필요

---

## 10. canon 측 후속 변경 권장

Wave 4 이후 canon은 9축 중 **3축만 보유** (모두 연구 산출물):

| 축 (INDEX.json 기준) | 캐넌 잔존 | 이전됨 |
|---|---|---|
| theory | ❌ | `hexa-meta/{breakthroughs,constants,flow,predictions,preprints,roadmap-v2,roadmap-v3,study}/` (Wave 4) |
| domains | 포인터만 | `hexa-*` family (Wave 1.5) |
| bridge | ❌ | `nexus/canon-infra/bridge/` (Wave 3) |
| techniques | ❌ | `hexa-codex/techniques/` (Wave 2) |
| experiments | ✅ (chip-verify 제외 권장) | `hexa-codex/experiments/ai-efficiency/` (Wave 2) |
| engine | ❌ | `nexus/canon-infra/engine/` (Wave 3) |
| papers | ❌ (비어있음) | `hexa-*` (Wave 1) |
| reports | ✅ (일부 도메인-타이트 제외 권장) | — |
| canonshared | ❌ | `nexus/canon-infra/canonshared/` (Wave 3) |

**현재 canon 트랙드 트리** (Wave 4 직후):
- 도트파일/설정: `.doc-rules.json`, `.githooks/`, `.github/`, `.gitignore`, `.hexa-init/`, `.loop`, `.own.cognitive`, `.own.group_p`, `.own.readme`, `.papers-cross-repo-lint-exempt`, `.playwright-mcp/`, `.readme-rules.json`, `.verify_cache.json`
- 루트 docs: `README.md`, `LICENSE`, `CITATION.cff`, `SECURITY.md`, `CONTRIBUTING.md`, `MOVED_TO_STANDALONES.md`
- 콘텐츠 7개: `archive/`, `docs/`, `domains/`(포인터), `experiments/`, `lean4-n6/`, `proposals/`, `reports/`

**INDEX.json (canon측 신규 필요)**: 3축 모델로 재작성 권장 — experiments/reports/proposals + legacy(archive/docs/lean4-n6/domains-pointer).

---

*문서 위치*: `nexus/canon-infra/MIGRATION_PLAN.md`
*Wave 3 작성일*: 2026-05-11
*Author*: dancinlife + Claude Opus 4.7
