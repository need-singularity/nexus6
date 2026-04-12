# nexus — NEXUS-6 중앙 허브

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/nexus.json (NX1~NX3)
L0 Guard: `hexa ~/Dev/nexus/shared/lockdown/l0_guard.hexa <verify|sync|merge|status>`
전역 불변식: todo/할일 실행은 반드시 shared/bin/hexa resolver 경유. 직접 바이너리 하드코딩 금지.

blowup infra:
  fast-path: exact(mtime+size O(1) ~83ms) → incremental(tail O(Δ)) → shell(awk ~0.6s/12MB) → hexa(소규모만)
  sidecar: atlas.n6.stats (mtime/size/lines/hash/nodes/edges/hubs), atlas.n6.deg (degree TSV)
  dedup: _batch_new_ids 해시셋 (Phase 5.5+6, 6.7)
  schema guard: _guarded_append_atlas() 포맷 검증, 무효 라인 reject
  health: `hexa shared/n6/atlas_health.hexa [path] [--verbose]`
  modules: field/holographic/quantum/string/toe — lib/atlas_guard.hexa.inc 공유
  원칙: infra-only 개선. phase 로직/discovery 계산/seed 진화 불변

shared/ tree:
  blowup/        돌파 엔진 — core/guard/modules(5)/lens/ouroboros/seed
  hooks/         Claude Code 훅 (.hexa)
  rules/         AI-native 규칙
  config/        SSOT 정책
  discovery/     발견 허브
  bt/            BreakThrough audit
  convergence/   CDO 수렴 추적
  consciousness/ anima 런타임
  n6/            atlas + 수학 맵
  dse/           Design Space Exploration
  engine/        프로젝트별 엔진
  project-claude/ CLAUDE.md 마스터

L0 보호 (평시 자유 수정, 유저 명시 요청 시만 승인 절차):
  shared/bin — compat 심링크
  shared/hooks/*.hexa — 공용 훅 엔진 전체
  shared/blowup/core/blowup.hexa — 9-phase 파이프라인
  shared/blowup/modules/*.hexa — 5종 변종
  shared/blowup/lib/atlas_guard.hexa.inc — 공통 헬퍼
  shared/blowup/seed/seed_engine.hexa — 시드 엔진
  shared/blowup/commands.hexa — 명령 라우터
  shared/blowup/todo.hexa — 할일 엔진
  shared/blowup/lens/lens_forge.hexa — 렌즈 단조기
  shared/n6/atlas_health.hexa — 헬스체크
  shared/n6/atlas.n6 — 현실 지도 SSOT
  shared/config/core.json — 시스템맵+명령어
  shared/config/absolute_rules.json — 절대 규칙
  shared/config/convergence_ops.json — CDO 수렴
  shared/config/loop/*.json — 성장 루프
  shared/lockdown/ — 잠금 체계
  shared/convergence/ — 수렴 추적
  shared/discovery/reality_map_3d.html — 3D 현실지도
  shared/CLAUDE.md — 전 프로젝트 공유 규칙
  shared/bt/bt_keywords.jsonl — 돌파 키워드
  shared/bt/bt_domains.jsonl — 돌파 도메인
  shared/project-claude/ — CLAUDE.md 마스터
  shared/rules/ — 규칙 체계 SSOT
  docs/index.html — 3D 현실지도 프론트엔드
  CLAUDE.md — 이 파일

ref:
  rules     shared/rules/common.json             R0~R27
  project   shared/rules/nexus.json              NX1~NX3
  lock      shared/rules/lockdown.json           L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  registry  shared/config/projects.json          7프로젝트+번들/검증
  cfg       shared/config/project_config.json    CLI/관례/리소스
  core      shared/config/core.json              시스템맵+14명령+폴더
  conv      shared/convergence/nexus.json
  lenses    shared/config/lens_registry.json     397종
  grammar   shared/config/hexa_grammar.jsonl     hexa-lang+pitfalls P1~P5
  api       shared/CLAUDE.md
