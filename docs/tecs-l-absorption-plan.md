# tecs-l 흡수 로드맵

> 생성: 2026-04-10
> 상태: Track A 진행 중 / Track B 보류 / Track C 면제 결정
> 담당: 본 에이전트(재배치/문서화) + 별도 에이전트(코드 삭제)

## 개요

`tecs-l/` 는 nexus 의 **흡수 대상** 리포입니다. 독립 리포가 아닌,
nexus/mk2_hexa/native/ 에 `.hexa` 네이티브로 포팅되는 과정에 있습니다.

## 현황 (2026-04-10)

| 항목 | 수치 | 비고 |
|------|------|------|
| nexus mk2_hexa/native .hexa 모듈 | ~473 | module_counter.hexa 기준 |
| tecs-l .py 파일 (results/docs 제외) | ~644 | |
| tecs-l 포팅된 .hexa (Track A 완료 추정) | ~75 | frontier_*, verify_h_*, math 계열 |
| 포팅 진행률 | ~11% | 650 중 75 |

## 3트랙 분류

### Track A — 진행 중 (hexa-lang 단독 포팅 가능)

hexa-lang 만으로 포팅 가능한 순수 수학/검증 모듈.
외부 의존 없음, 정수/실수/리스트만 사용.

- **카테고리**:
  - `verify/` — frontier_*, verify_h*, verify_round* (검증기)
  - `math/` — arith_*, characterization_*, arithmetic_derivative_*,
    dirichlet_*, torus_knot_*, task1_*, task2_*, oeis_*, ramsey_*,
    game_theory_*, cy3_*, difftopo_*, f2_*, p3_*, prove_*, investigate_*,
    elliptic_*, quadratic_*, search_*, r_chain_*, sporadic_*, ppp_*
  - `engines/` — perfect_number_engine, dfs_engine, proof_engine,
    nuclear_engine, physics_constant_engine, quantum_formula_engine,
    congruence_chain_engine, convergence_engine, discovery_loop,
    model_meta_engine, model_pure_field, model_utils, nstate_calculator,
    brain_singularity, brain_cct_analyzer, brain_analyzer, compass,
    complex_compass, chemistry_engine, consciousness_calc, consciousness_fps,
    session_briefing, texas_quantum, timeline, llm_expert_analyzer

- **진행 수**: ~75 / Track A 대상 ~290 (~26%)

### Track B — 보류 (블로커)

외부 ML/과학계산 라이브러리 의존 → hexa-lang 결정 필요.

| 블로커 | .py 파일 수 | 영향 범위 |
|--------|------------|----------|
| torch | 250 | experiments/exp_*, engines/bitnet_*, golden_moe_*, conscious_lm_*, growing_* |
| sklearn | 79 | verify/verify_gz_*, experiment_* 일부 |
| scipy | 104 | verify/verify_chem_*, verify/verify_bh_*, math/investigate_*, stats 계열 |

- **고유 파일 수 (중복 제거)**: 약 353
- **블로커 해제 조건** (hexa-lang 팀 결정 필요):
  1. **FFI 옵션**: CPython 브리지 → `import_py("torch")` 형태로 call
  2. **네이티브 tensor 옵션**: hexa-lang 에 `tensor<f32>` 타입 + BLAS 바인딩 추가
  3. **하이브리드**: 수치는 hexa, 학습은 runpod 원격 실행

- **대기 카테고리**:
  - `experiments/` — exp_h*, experiment_h_ee_*, experiment_h_sedi_*,
    experiment_anima_*, experiment_cifar_*, experiment_cnn_*
  - `engines/` (ML) — bitnet_golden_moe_*, conscious_lm_*, growing_conscious_lm_*,
    golden_moe_*, model_a~g_*, model_cnn_*, model_displacement_*,
    model_fiber_*, model_empathy_*, model_temporal_*, model_generative_*
  - `verify/` (scipy) — verify_chem_*, verify_bh_*, verify_*_deep

### Track C — 면제 (이관 없음)

nexus 로 포팅하지 않고 tecs-l 에서만 존재하거나 외부 보관으로 대체.

- `tecs-l/results/` — 실험 산출물 (JSON/PNG). Zenodo DOI 로 영구 보관.
- `tecs-l/docs/hypotheses/` — 2,711 가설 문서. `~/Dev/papers/` 로 이관 예정.
- `tecs-l/zenodo/` — 배포 스크립트. papers 리포 통합 대기.
- `tecs-l/tecsrs/` — Rust 계산 엔진. hexa-lang 성능 충분 시 삭제, 아니면
  nexus/src/ 로 이관.
- `tecs-l/eeg/`, `tecs-l/n6-replication/` — 데이터 전용. Zenodo 보관.

## mk2_hexa/native 재배치 계획

### 목표 구조

```
mk2_hexa/native/
├── verify/          # frontier_*, verify_h*, verify_round*
├── math/            # arith_*, characterization_*, dirichlet_*, …
├── engines/         # chemistry_engine, brain_singularity, dfs_engine, …
├── experiments/     # experiment_*, exp_* (Track B 이후)
└── <루트>           # 코어 인프라 (blowup, telescope, command_router, …)
```

### 블로커: 스캐너 재구성 필요

현재 다음 파일들이 `mk2_hexa/native/*.hexa` 를 비재귀로 globbing 합니다:

| 파일 | 용도 | 영향 |
|------|------|------|
| `module_counter.hexa` | 모듈 수 집계 + core.json 동기화 | 서브디렉토리 파일 누락 |
| `theory_registry.hexa` | 이론 등록/지문 계산 | 등록 누락 |
| `todo.hexa` | 모듈 수 집계 | 카운트 오류 |
| `anima_loop.hexa` | anima 루프 모듈 스캔 | 스캔 누락 |
| `sync_docs.hexa` | 문서 생성 시 모듈 수 표시 | 표시값 불일치 |
| `engine_*.hexa` (linguistics, economics, music, meteorology, geology, nexus) | 모듈 존재 여부 체크 | 이미 이동 대상 |

또한 `session_briefing.hexa` 는 **하드코딩** 으로
`hexa mk2_hexa/native/verify_h_stat_1.hexa` 를 호출합니다.

**shared/theory_registry.jsonl** 은 각 모듈에 대해
`"desc":"mk2_hexa/native/<name>.hexa"` 경로를 직접 저장합니다.
서브디렉토리 이동 시 전체 재생성 필요.

### 재배치 전 선행 작업 (블로커 해제)

1. **스캐너 재귀화**: `exec("ls " + dir + "/*.hexa")` →
   `exec("find " + dir + " -name '*.hexa' -type f")` 로 교체
   - 대상: module_counter, theory_registry, todo, anima_loop, sync_docs
2. **theory_registry.jsonl 경로 갱신**: desc 필드 `mk2_hexa/native/<cat>/<name>.hexa`
3. **session_briefing.hexa**: verify_h_stat_1.hexa 경로 갱신
4. **core.json total_files 재동기화**: module_counter --sync
5. **위 완료 후** git mv 수행

## 이번 세션 작업 결과

### 생성한 구조

- `mk2_hexa/native/verify/.gitkeep`
- `mk2_hexa/native/math/.gitkeep`
- `mk2_hexa/native/engines/.gitkeep`
- `mk2_hexa/native/experiments/.gitkeep`

### 수행한 git mv

**0 건** — 모든 이동이 스캐너/레지스트리 블로커에 의해 차단됨.
스캐너 재귀화(선행 작업) 완료 후 일괄 이동 예정.

### 차단된 이동 후보 (75+)

- frontier_500 ~ frontier_2000 (18개) → verify/
- verify_h_bio_1, verify_h_cs_5~6, verify_h_cycl_1_v2, verify_h_mp_15_fractal,
  verify_h_nt_2, verify_h_ph_1~2, verify_h_stat_1, verify_h_top_1~3,
  verify_hcross2_texas, verify_hcx_consciousness, verify_hcx65_j2_coincidence,
  verify_hcx71_r_fractal*, verify_hph_2_15_16, verify_hph_678, verify_hph1_hph17,
  verify_hypotheses (20+) → verify/
- arith_identity_search, arithmetic_derivative_n6, characterization_verifier,
  dirichlet_R_investigation, dirichlet_triple_selfinv, dfs_n6_ag_verify,
  difftopo_n6_verify, p3_shadow_final_count, task1_*, task2_*, investigate_*,
  prove_phi_sigma, oeis_*, quadratic_form_calculator, torus_knot_topology,
  coding_lattice_texas, consciousness_bridge_* (25+) → math/
- brain_analyzer, chemistry_engine, perfect_number_engine 등 (존재 시) → engines/

차단 사유: 스캐너가 모두 비재귀 glob 을 사용 → 이동 시 모듈 카운트
누락 + theory_registry.jsonl 경로 불일치 + core.json 동기화 실패.

## Session 2026-04-10 / 일괄 소형 디렉토리 처리

대상: tecs-l/{tools, tests, docs, zenodo, eeg, serve} + tecs-l 루트 엔진
포팅 위치: mk2_hexa/native/{tools, tests, docs, eeg, zenodo, root_engines, serve}/

### 인벤토리 요약

| 디렉토리 | .py 수 | Track A 포팅 | Track B 보류 | Track C 면제 |
|----------|--------|-------------|-------------|-------------|
| tecs-l/tools/ph-training | 9 | 0 | 5 (ph, engine, trainer, data, cli) + 3 tests/init | 0 |
| tecs-l/tests | 1 | 1 (test_atlas_parser) | 0 | 0 |
| tecs-l/docs/hypotheses | 19 | 6 (h_rob_3/4, hcx481_486, hcx441/442, translate_helper) | 13 (sklearn/scipy/MLP) | 0 |
| tecs-l/zenodo | 4 | 0 | 0 | 4 (Zenodo HTTP API) |
| tecs-l/eeg | 2 | 0 | 0 | 2 (brainflow + scipy plotting) |
| tecs-l/serve | 1 | 0 | 0 | 1 (fastapi + torch) |
| tecs-l 루트 엔진 | 18 | 10 (chemistry, nuclear, physics_constant, congruence_chain, proof, texas_quantum, dfs, llm_expert_analyzer, convergence, discovery_loop) | 8 (perfect_number, quantum_formula, brain_cct, brain_singularity, consciousness_calc/fps, model_meta/pure_field) | 0 |
| **합계** | **54** | **17** | **26** | **7** |

### 결과

- **Track A 포팅**: 17 .hexa (mk2_hexa/native/{root_engines,docs,tests}/)
- **Track B 보류 (.hexanoport)**: 20 markers (root_engines x8, tools x5, docs x1 batch + 1 batch-of-13)
- **Track C 면제 (.hexanoport)**: 7 markers (eeg x2, zenodo x4, serve x1)
- **원본 .py 삭제**: 0 (삭제 금지 규칙 준수)

### Track A 포팅 파일 목록

- `mk2_hexa/native/root_engines/chemistry_engine.hexa`
- `mk2_hexa/native/root_engines/nuclear_engine.hexa`
- `mk2_hexa/native/root_engines/physics_constant_engine.hexa`
- `mk2_hexa/native/root_engines/congruence_chain_engine.hexa`
- `mk2_hexa/native/root_engines/proof_engine.hexa`
- `mk2_hexa/native/root_engines/texas_quantum.hexa`
- `mk2_hexa/native/root_engines/dfs_engine.hexa`
- `mk2_hexa/native/root_engines/llm_expert_analyzer.hexa`
- `mk2_hexa/native/root_engines/convergence_engine.hexa`
- `mk2_hexa/native/root_engines/discovery_loop.hexa`
- `mk2_hexa/native/docs/verify_h_rob_3.hexa`
- `mk2_hexa/native/docs/verify_h_rob_4.hexa`
- `mk2_hexa/native/docs/verify_hcx481_486.hexa`
- `mk2_hexa/native/docs/verify_hcx441.hexa`
- `mk2_hexa/native/docs/verify_hcx442.hexa`
- `mk2_hexa/native/docs/translate_helper.hexa`
- `mk2_hexa/native/tests/test_atlas_parser.hexa`

### 포팅 전략 메모

- `dfs_engine.py` 는 numpy import 가 있지만 실제 사용 0회 → Track A.
- `convergence_engine.py`, `discovery_loop.py` 의 numpy 사용은 mean/std 한두 곳뿐
  → 인라인 산술로 교체.
- `llm_expert_analyzer.py` 도 numpy 호출 0회(미사용) → Track A.
- `verify_hcx441/442` 는 numpy 가 log 한 줄만 사용 → `ln()` 으로 대체.
- 모든 포팅 파일 헤더에 `// Ported from tecs-l/<path>/<name>.py` 주석 포함.

## Progress 2026-04-10 (iter 2)

### 디렉토리별 진척 (live count)

| tecs-l 디렉토리 | 잔여 .py | mk2_hexa/native 대응 | 포팅된 .hexa | Track A 대상 (비블로커) | % 완료 (A 대비) |
|----------------|---------|---------------------|-------------|----------------------|---------------|
| verify (154) | 154 | verify/ | 46 | ~118 | ~39% |
| experiments (193) | 193 | experiments/ | 11 | ~14 (179 블로커) | ~79% of A |
| math (87) | 87 | math/ | 25 | ~59 | ~42% |
| engines (28) | 28 | engines/ + root_engines/ | 1 + 10 = 11 | ~1 (27 블로커) | 블로커 우세 |
| scripts (37) | 37 | scripts/ | 37 | ~21 | scripts 초과(호스트 원본) |
| tools (9) | 9 | tools/ | 0 | 0 (5 보류 + tests) | 0% |
| docs (19) | 19 | docs/ | 6 | 6 | 100% of A |
| tests (1) | 1 | tests/ | 1 | 1 | 100% |
| zenodo (4) | 4 | — | 0 | 0 (Track C) | 면제 |
| eeg (2) | 2 | eeg/ | 0 | 0 (Track C) | 면제 |
| serve (1) | 1 | serve/ | 0 | 0 (Track C) | 면제 |
| n6-replication (1) | 1 | n6_replication/ | 19 | 1 | 초과 |
| 루트 엔진 (18) | 18 | root_engines/ | 10 | 10 | 100% of A |
| **합계** | **554** | — | **641** (중복/신규 포함) | — | — |

### 핵심 지표

- hexanoport 마커: **53개** (engines 28, root_engines 8, tools 5, zenodo 4, scripts 3, eeg 2, docs/n6/serve 1)
- mk2_hexa/native 루트: 475개 (대부분 재배치 대기 — 스캐너 블로커)
- 서브디렉토리 누적: 166개 (verify 46, scripts 37, math 25, n6_replication 19, experiments 11, root_engines 10, _compilable 10, docs 6, tests 1, engines 1)

### 다음 우선순위 3건 (의존성 최소 / 영향력 최대)

1. **verify/ 비블로커 잔여 ~72개 포팅** — 154 중 36만 블로커, 118이 Track A. math/engines 와 독립, mk2_hexa/native/ 이동 없이 신규 파일만 생성하므로 스캐너 블로커 회피. 최대 커버리지 상승.
2. **math/ Track A ~34개 추가 포팅** — 87 중 59가 비블로커, 현재 25. 순수 수학 루틴이라 FFI 불필요, 독립 파일. verify 와 병렬 가능.
3. **스캐너 5개 재귀화** (module_counter, theory_registry, todo, anima_loop, sync_docs) — 재배치 전체의 단일 블로커. 해제 시 75+ 루트 파일 일괄 git mv 가능, core.json/theory_registry.jsonl 동기화 복원.

### 충돌 플래그

- 다른 에이전트가 mk2_hexa/native/ 에 신규 .hexa 추가 중: 본 감사 시점 루트 475 > 계획 당시 473. 서브디렉토리 누적 166 > 전 세션 기록 75+. **충돌 위험 낮음** (신규 파일 생성 only).
- 스캐너 재귀화 작업은 **단일 에이전트 전담 필수** — module_counter/theory_registry/todo/anima_loop/sync_docs 동시 수정 금지.
- theory_registry.jsonl desc 경로 갱신은 스캐너 재귀화 이후에만 (현재 루트 경로 하드코딩 다수).

## Progress 2026-04-10 (iter 3)

### 디렉토리별 진척 (live count, iter 2 대비 델타)

| 디렉토리 | tecs-l .py (Δ) | .hexa (Δ) | .hexanoport | iter3 비고 |
|---------|---------------|-----------|-------------|------------|
| verify | 141 (−13) | 65 (+19) | 19 | 대폭 진척, ~80 잔여 추정(A) |
| experiments | 158 (−35) | 22 (+11) | 17 | 삭제 우세, 대부분 torch 블로커 |
| math | 62 (−25) | 25 (0) | 10 | .py 감소(삭제) but 포팅 정체 |
| engines | 28 (0) | 1 (0) | 28 | 전량 블로커/보류 (노포트 완료) |
| scripts | 37 (0) | 37 (0) | 3 | 완료 (포팅+보류 분류 끝) |
| tools | 9 (0) | 0 (0) | 8 | 전량 ph-training 보류 (완료) |
| docs | 1 (−18) | 18 (+12) | 1 | 거의 완료 |
| tests | 0 (−1) | 1 (0) | 0 | 완료 |
| eeg | 2 | 0 | 2 | Track C 완료 |
| serve | 1 | 0 | 1 | Track C 완료 |
| zenodo | 4 | — | 4(root) | Track C 완료 |
| n6-replication | 1 | 19 | 1 | 완료 |
| 루트 엔진 | 18 | 10(root_engines) | 8 | 완료 |
| **tecs-l .py 합계** | **462** (−92) | — | — | −17% vs iter2 (554) |
| mk2_hexa/native 총 | — | **684** (+43) | **102** (+49) | 루트 476, 서브 208 |

### 누적 흡수율

- tecs-l 원본 ~650 기준: 삭제/포팅/보류 마커 188 → **약 29% 흡수** (iter2 ~15%)
- Track A+B+C 분류 완료 디렉토리: 8/13 (tests, scripts, tools, docs, eeg, serve, zenodo, n6, root_engines)
- Track A 실포팅율 추정: 190/290 ≈ **66%** (iter2 ~26%)

### 잔여 Track A 후보 (비블로커, 식별)

1. **verify/ ~80건** — 여전히 최대 표적. 141 중 noport19 제외, 기포팅 62 차감 → ~60 신규 포팅 여지. frontier_*, verify_h_nt/ph/top 계열.
2. **math/ ~25건** — 62 중 noport10 제외 32 중 기포팅 중복 감안 ~25 잔여. arith/oeis/quadratic/torus 계열 Track A 확정.
3. **experiments/ ~5건** — 158 중 ~14 비블로커 추정, 11 포팅 완료 → ~3~5 잔여. numpy 경량 사용자 위주.

### Track B 우세 디렉토리 (FFI/native tensor 결정 필요 순)

| 우선순위 | 디렉토리 | 블로커 파일 추정 | 블로커 종류 |
|---------|---------|----------------|-------------|
| **1** | experiments/ | ~150 | torch (학습 루프 전면) |
| **2** | engines/ | 27 | torch (model_*, bitnet_*, moe_*) |
| **3** | verify/ | ~36 | scipy (verify_chem_*, verify_bh_*) |
| 4 | math/ | ~25 | scipy.stats / numpy 중량 |
| 5 | tools/ | 5 | torch (ph-training) |

→ **torch 블로커 단독으로 engines+experiments+tools ≈ 180개** 차단. FFI 또는 native tensor 결정 시 흡수율 29%→70% 즉시 점프 가능.

### 핵심 권고

1. **verify/ + math/ Track A 완주** (~105건, 1~2 세션): 흡수율 29%→45% 도달. 독립 파일만 생성 → 스캐너 블로커 회피.
2. **스캐너 재귀화 블로커는 여전히 미해제**: iter2 체크리스트 5개 항목 변동 없음. 루트 476 → 이동 불가. 단일 에이전트 전담 필요.
3. **hexa-lang 팀 결정 요청 긴급도 상향**: torch FFI vs native tensor. 180건 차단 중. 결정 없이는 흡수 상한 ~50%.
4. **충돌 상태**: mk2_hexa/native .hexa 641→684 (+43), noport 53→102 (+49). 다른 에이전트 활발히 작업 중 — 본 감사 read-only 유지 확인.

## 다음 세션 체크리스트

- [ ] 스캐너 5개 (`module_counter`, `theory_registry`, `todo`,
  `anima_loop`, `sync_docs`) 재귀 스캔으로 리팩터
- [ ] `session_briefing.hexa` verify_h_stat_1 경로 업데이트
- [ ] `shared/theory_registry.jsonl` desc 경로 일괄 갱신 (또는 재생성)
- [ ] `core.json.total_files` module_counter --sync 로 재계산
- [ ] 카테고리별 git mv 일괄 수행 (본 로드맵 대상 75+)
- [ ] hexa-lang 팀과 Track B 블로커 해제 협의 (FFI vs native tensor)
- [ ] Track C 면제 대상 Zenodo 백업 상태 확인
- [ ] 최종 삭제 에이전트에게 체크리스트 전달 (Track A 100% 포팅 후)
