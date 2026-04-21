# DEPRECATED — 2026-04-20 roadmap unification

이 디렉토리 파일 전부 2026-04-20 이전 anima 로드맵 JSON 들. Canonical 3 파일로 통합됨:

- `shared/roadmaps/anima.json` — main linker + mandatory common gates (5-gate: G_INPUT/G_SUBSTRATE/G_TRAIN/G_EVAL/G_VALIDITY/G_ARTIFACT/G_DECISION)
- `shared/roadmaps/dest_alm.json` — ALM production detail
- `shared/roadmaps/dest_clm.json` — CLM research + ship detail

참조 docs:
- `/Users/ghost/Dev/anima/docs/alm_clm_roles_canonical_20260420.md` — ALM/CLM 역할 SSOT

## Why unified

1. 로드맵 파일 분산 → 참조 혼란
2. ALM/CLM 역할 정의가 각 파일에 흩어져 있어 canonical 부재 (2026-04-20 역할 혼동 사고)
3. Mandatory common gates 도입 (ALM r12 corpus vacuum 사고 이후)

## Files archived

| File | 원래 역할 | 후속 |
|---|---|---|
| anima_full_pre.json | nexus main SSOT 837 LOC | anima.json 으로 통합 (slim linker) |
| anima.json.bak.* | 자동 백업들 | 관상용 참조 |
| anima-train.json | 학습 specific | dest_alm.json / dest_clm.json 에 흡수 |
| alm_consciousness_standalone.json | ALM standalone 계획 | dest_alm.json 흡수 |
| clm_consciousness_standalone.json | CLM standalone 계획 | dest_clm.json 흡수 |
| _report.md | 상태 리포트 | ephemeral, 관상용 |

## Do not revive

새 anima 로드맵 작업은 canonical 3 파일에만 반영. 이 archive 는 역사/참조 용도.
