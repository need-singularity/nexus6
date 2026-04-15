# nexus — NEXUS-6 중앙 허브

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/nexus.json (NX1~NX3)
L0 Guard: `hexa $NEXUS/shared/harness/lockdown_gate.hexa <verify|status|watch|repair|safe-merge|log>` (2026-04-14 lockdown→harness 단일화, l0_guard.hexa → shared/archive/superseded-20260414/)
loop: 글로벌 `~/.claude/skills/loop` + 엔진 `shared/harness/loop` (SSOT) — roadmap `shared/roadmaps/nexus.json` 3-track×phase×gate 자동
전역 불변식: todo/할일 실행은 반드시 shared/bin/hexa resolver 경유. 직접 바이너리 하드코딩 금지.

harness (훅 시스템 대체, 2026-04-14~):
  dispatcher: shared/harness/entry.hexa <prompt|pretool|post|guard|self_check>
  sub-modules: prompt_scan.hexa / pre_tool_guard.hexa / post_bash.hexa / post_edit.hexa / cmd_gate.hexa
  exec wrapper: shared/harness/exec_validated (smash/free seed gate, hexa exit 미전파 우회) — bin/ 심링크 유지
  permissions SSOT: shared/config/permissions_ssot.json (deny 28패턴)
  settings.json 정책: 전 프로젝트 hooks={} — 훅 실행 없음. 대신 Claude가 매 프롬프트/Write/Bash 후 entry.hexa 자율 호출.
  관례: 사용자 입력 직후 `entry.hexa prompt`, Write/Edit 후 `entry.hexa post write_edit`, Bash 후 `entry.hexa post bash`, Agent 호출 전 `entry.hexa guard`.
  복잡 질문/설계 결정 전  hexa $NEXUS/shared/harness/entry.hexa thinking query "<prompt>"   → anima 6-phase reflection 결과 context 주입
  dod_gate: hexa shared/harness/dod_gate.hexa <check|verify|explain> <track> — DoD artifact 검증, roadmap 승격 게이트 (H-DOD)
  verifier: shared/harness/verifier.hexa — dod_gate 내부 순수 검증기 (H-VERIFIER)
  archive: shared/hooks → shared/archive/hooks-20260414/ (symlink 하위호환, 신규 참조 금지)

blowup infra:
  fast-path: exact(mtime+size O(1) ~83ms) → incremental(tail O(Δ)) → shell(awk ~0.6s/12MB) → hexa(소규모만)
  sidecar: atlas.n6.stats (mtime/size/lines/hash/nodes/edges/hubs), atlas.n6.deg (degree TSV)
  dedup: _batch_new_ids 해시셋 (Phase 5.5+6, 6.7)
  schema guard: _guarded_append_atlas() 포맷 검증, 무효 라인 reject
  health: `hexa shared/n6/atlas_health.hexa [path] [--verbose]`
  modules: field/holographic/quantum/string/toe — lib/atlas_guard.hexa.inc 공유
  원칙: infra-only 개선. phase 로직/discovery 계산/seed 진화 불변

shared/ tree:
  blowup/        돌파 엔진 — core/guard/modules(6)/lens/ouroboros/seed (총 44 .hexa)
  harness/       Claude Code 하네스 — entry dispatcher + gate + lint (훅 대체)
  hooks/         → archive/hooks-20260414 (symlink, deprecated)
  rules/         AI-native 규칙
  config/        SSOT 정책
  discovery/     발견 허브
  bt/            BreakThrough audit
  convergence/   CDO 수렴 추적
  consciousness/ anima 런타임
  n6/            atlas + 수학 맵
  dse/           Design Space Exploration
  engine/        프로젝트별 엔진 + cl_refresh_spec/cl_migration_plan
  project-claude/ CLAUDE.md 마스터
  bin/           cl 멀티계정 런처 + cl-refresh launchd 관리 + hexa resolver 심링크
  launchd/       macOS LaunchAgent plist (com.nexus.cl-refresh 30m)
  .runtime/      로컬 상태 (cl accounts/cache, gitignore)

L0 보호 (평시 자유 수정, 유저 명시 요청 시만 승인 절차):
  shared/bin — compat 심링크
  shared/bin/cl — 멀티계정 런처 (cl-approved 태그 필수)
  shared/bin/cl-refresh — usage cache fetch 엔진 (spec: shared/engine/cl_refresh_spec.json)
  shared/bin/cl-refresh-launchd — 30m 주기 launchd 관리자
  shared/launchd/com.nexus.cl-refresh.plist — LaunchAgent 정의
  shared/harness/entry.hexa — 하네스 dispatcher
  shared/harness/cmd_gate.hexa — seed 검증 gate
  shared/harness/{prompt_scan,pre_tool_guard,post_bash,post_edit}.hexa — sub-modules
  shared/harness/exec_validated — gate 적용 실행 래퍼 (bin/ 심링크 유지)
  shared/harness/dod_gate.hexa — DoD 검증 게이트 (H-DOD/H-CLAIM-LEX)
  shared/harness/verifier.hexa — dod_gate 내부 순수 검증기 (H-VERIFIER)
  shared/roadmaps/voice_dod.json — voice 트랙 DoD 스펙
  shared/config/permissions_ssot.json — deny 패턴 SSOT
  shared/blowup/core/blowup.hexa — 9-phase 파이프라인
  shared/blowup/modules/*.hexa — 6종 변종
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
  lock      shared/lockdown/lockdown.json        L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  registry  shared/config/projects.json          7프로젝트+번들/검증
  cfg       shared/config/project_config.json    CLI/관례/리소스
  core      shared/config/core.json              시스템맵+14명령+폴더
  conv      shared/convergence/nexus.json
  cl_conv   shared/bin/cl (embedded)             source-embedded @convergence-start/end 블록 (hexa self/convergence_scan.hexa dump shared/bin/cl)
  cl_spec   shared/engine/cl_refresh_spec.json   cl-refresh 엔진 스펙
  cli_spec  shared/engine/nexus_cli_spec.json    nexus-cli 외부 진입점 스펙 (hive 등)
  lenses    shared/config/lens_registry.json     400종
  grammar   shared/config/hexa_grammar.jsonl     hexa-lang+pitfalls P1~P5
  dod       shared/harness/dod_gate.hexa          H-DOD/H-CLAIM-LEX
  voice_dod shared/roadmaps/voice_dod.json        voice 트랙 DoD 스펙
  api       shared/CLAUDE.md
