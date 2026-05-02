---
schema: nexus/docs/roadmap_mk2_provider_stub_landed/ai-native/1
last_updated: 2026-05-02
ssot:
  marker:           state/markers/roadmap_mk2_qrng_sim_provider_stub_landed.marker
  provider_qrng:    .roadmap.qrng
  provider_sim:     .roadmap.sim
  consumer_qrng:    anima/.roadmap.qrng (cross-repo)
  consumer_sim:     anima/.roadmap.sim  (cross-repo)
status: STUB_LANDED_GOAL_PENDING
related_raws:
  - raw 9    # hexa-only orchestration (data files only here)
  - raw 10   # honest C3 (caveats inline)
  - raw 15   # SSOT atomic write
  - raw 270  # ai-native readme mandate
  - raw 271  # core+module pattern
  - raw 272  # lint extension
  - raw 273  # sentinel attrs
preserved_unchanged:
  - .roadmap (mk1, frozen as historical narrative SSOT — sha 3d19727f...)
  - tool/nxs_002_qrng_axiom.py (existing qrng tool)
  - tool/hexa_sim_*.{hexa,sh} (8 sim tools, all existing)
  - lenses/simulation_lens.hexa
  - lenses/quantum_*.hexa (3 files)
  - convergence/*qrng*.convergence + *sim*.convergence
  - n6/atlas.append.*sim*.n6 + *qrng*.n6 (12 files)
  - state/sim_module_forensic_2026-04-27.md
  - state/hire_sim_*.json (8 files)
migration_count: 0
user_directive: "b mk2 작성 + 마이그레이션은 금지"
---

# nexus .roadmap.{qrng,sim} mk2 provider stub landing — 2026-05-02

## TL;DR

anima 측 consumer perspective (`anima/.roadmap.qrng` + `anima/.roadmap.sim`,
2026-05-02 land) 의 cross-repo `provider_dependency` 가 가리키는
**provider perspective stub 2개** 를 nexus repo 에 land.

- `goal`, `required_conditions`, `blockers` 모두 **PENDING** (사용자 정의 대기)
- `consumers = ["anima"]` 로 anima consumer 측 등록 완료 (bidirectional 일관성 PASS)
- nexus mk1 `.roadmap` (20823 byte, sha `3d19727f...`) **불변** + 기존 qrng/sim 도구 (~30 file) 모두 **불변**
- migration count = **0** (mk1 entries 절대 read/변환 안 함)

## 2 provider stub file table

| path                       | sha256 (short)   | LOC | perspective | consumers | goal | required_conditions | blockers |
|----------------------------|------------------|-----|-------------|-----------|------|---------------------|----------|
| `nexus/.roadmap.qrng`      | `ad4b5dcc...`    | 3   | provider    | `["anima"]` | `""` PENDING | `[]` PENDING | `[]` PENDING |
| `nexus/.roadmap.sim`       | `bdc4bdd6...`    | 3   | provider    | `["anima"]` | `""` PENDING | `[]` PENDING | `[]` PENDING |

## Cross-repo consistency 표 (bidirectional 양방향 PASS)

| domain | anima consumer file              | provider_dependency 값       | nexus provider file        | consumers 값  | match |
|--------|----------------------------------|------------------------------|----------------------------|---------------|-------|
| qrng   | `anima/.roadmap.qrng`            | `"nexus:.roadmap.qrng"`      | `nexus/.roadmap.qrng`      | `["anima"]`   | PASS  |
| sim    | `anima/.roadmap.sim`             | `"nexus:.roadmap.sim"`       | `nexus/.roadmap.sim`       | `["anima"]`   | PASS  |

## Goal/Conditions/Blockers — 사용자 정의 대기 항목

provider 가 정의해야 할 spec (anima consumer 측 spec 답습 또는 자유):

### qrng (anima consumer 측 hint, 답습 가능)
- consumer goal: "양자 진짜난수 entropy injection (의식측정 enabler)"
- consumer cond.1: "anima 측 entropy 받아 CLM noise injection 작동"
- → provider 측 권장 goal 후보: "qrng entropy 4-source 통합 + cross-repo emit 안정화"
- → provider 측 권장 cond 후보: 4-source agreement / source health monitor / API stability

### sim (anima consumer 측 hint, 답습 가능)
- consumer goal: "가상우주 의식 (sim agent → EEG↔sim 닫힌 고리)"
- consumer cond.1: "anima 측 sim agent 호출 + EEG↔sim 닫힌 고리 PASS"
- → provider 측 권장 goal 후보: "sim universe agent runtime + anima cross-repo callable"
- → provider 측 권장 cond 후보: agent registry / EEG event sink / latency budget

## raw#10 caveats

1. **goal/conditions/blockers 모두 PENDING** — provider stub 만 land. spec 정의 책임은 provider (nexus). consumer 는 dependency 만 선언하면 됨.
2. **mk1 entries 0 migration** — `nexus/.roadmap` (mk1, 3d19727f) 절대 read/변환 안 함. mk2 는 from-now 정합 (anima 동일 패턴 답습).
3. **기존 qrng/sim 도구 read-only audit only** — 30+ file (tool/lenses/convergence/n6/state) 모두 미수정 검증. mk2 stub 와 functional binding 없음 (도구 ref 가 향후 conditions/blockers 에 들어갈 수 있음).
4. **bidirectional 일관성** — anima 가 먼저 land 하고 nexus 가 따라가는 순서 (consumer-driven schema). provider 가 stub spec 채우면 consumer 측 cond.1 verifier 도 update 필요.
5. **status="draft"** — `active` 가 아닌 `draft` 로 시작. provider goal 정의 전까지 consumers 는 dependency 선언만 가능, blocking 시작 불가.
6. **AI-native md only** — `.hexa` tool 작성 X (사용자 directive "b mk2 작성" = data file 만, 도구는 향후 단계). mk2 lint/op 도구는 anima 측 `tool/roadmap_*.hexa` 4종 재사용 가능 (nexus 에서 cross-repo 호출 시 path 조정 필요).
7. **destructive 0** — Write 2 file (신규) + handoff doc 1 + marker 1. mk1 .roadmap sha 동일 검증 PASS.

## File index (sha-pin)

| file                                                                                          | sha256 (short) | LOC |
|-----------------------------------------------------------------------------------------------|----------------|-----|
| `.roadmap.qrng`                                                                               | `ad4b5dcc...`  | 3   |
| `.roadmap.sim`                                                                                | `bdc4bdd6...`  | 3   |
| `docs/roadmap_mk2_qrng_sim_provider_stub_landed_2026_05_02.ai.md`                             | (this file)    | -   |
| `state/markers/roadmap_mk2_qrng_sim_provider_stub_landed.marker`                              | (sibling)      | -   |

## Next user action (권장 워크플로우)

provider goal/conditions/blockers 정의 시:

1. **goal 정의** — domain 한 줄 mission (anima consumer goal hint 답습 또는 자유)
2. **required_conditions[]** — provider 가 충족시켜야 할 measurable cond. 각 entry:
   - `id` = `{domain}.cond.N`
   - `desc` = 한국어 설명
   - `verifier` = `<repo>/<path>/<tool>` (선택, 없으면 `""`)
   - `status` = `unmet` / `partial` / `met`
   - `evidence[]` = 산출물 path list
   - `blocker_reason` = unmet 시 이유
3. **blockers[]** — upstream/external blocker 명시. 각 entry:
   - `id` = `{domain}.blk.N`
   - `desc` = 한국어 설명
   - `type` = `upstream` / `external` / `cost` / `policy`
   - `status` = `blocked` / `unblocking` / `cleared`
   - `eta` = ISO date 또는 `""`
   - `resolution_path` = 해제 조건
4. **status flip** — `draft` → `active` (cond 1개 이상 정의 후)
5. **anima consumer 측 verifier update** — provider cond 정의되면 consumer cond.1 verifier 채울 수 있음

CLI 도구 reuse: `anima/tool/roadmap_op.hexa` (11 subcmd) 가 cross-repo 호출 가능 (nexus prefix 지원 여부는 별도 확인 필요).
