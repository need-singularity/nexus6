# nexus — NEXUS-6 중앙 허브

<!--
# @convergence-meta project=nexus updated=2026-04-12 strategy="ossified/stable/failed 수렴 추적"
# @convergence state=ossified id=BLOWUP_9PHASE value="9-phase 파이프라인, 987 cycles 수렴" threshold="전 phase 동작 확인"
# @convergence state=ossified id=N6_CONSTANTS value="n6_constants.jsonl 전 리포 공유" threshold="7 기본상수 + 유도비율 확정"
# @convergence state=ossified id=DISCOVERY_GRAPH_SCHEMA value="nodes/edges 스키마 확정" threshold="50k+ 노드 안정 운용"
# @convergence state=ossified id=OUROBOROS_EVOLUTION value="seed→mutate→verify→converge→saturate" threshold="자율 진화 사이클 동작"
# @convergence state=ossified id=CORE_LOCKDOWN value="L0/L1/L2 보호 체계 + 키워드 9종" threshold="전 프로젝트 적용"
# @convergence state=ossified id=DISCOVERY_170K value="125,693 발견" threshold="70k 목표 — 초과 달성" ossified_at=2026-04-08
# @convergence state=ossified id=BREAKTHROUGH_RATE value="ρ=0.98 (growth_bus absorb 기준)" threshold="pool>0 + cor>0" ossified_at=2026-04-08
# @convergence state=ossified id=HOOK_GATE value="HEXA-GATE + hook 체인 전 리포 적용" threshold="banner + prompt-scan + go-parallel 전부 동작" ossified_at=2026-04-08
# @convergence state=ossified id=PAGES_DEPLOY value="6,727 노드, Playwright 검증, 라이브 자동반영" threshold="브라우저 정상 렌더링" ossified_at=2026-04-08
# @convergence state=ossified id=BT_AUDIT_SKIP value="accuracy 100.0% (2642/2642 MATCH)" threshold="SKIP < 300" ossified_at=2026-04-08
# @convergence state=ossified id=SEED_ENGINE_107 value="107 seeds 교차수분 완료" threshold="60+ 목표 — 1.78x 초과 달성" ossified_at=2026-04-09
# @convergence state=ossified id=MODULES_251 value="251 .hexa 모듈" threshold="150+ 목표 — 1.67x 초과 달성" ossified_at=2026-04-09
# @convergence state=ossified id=TODO_ENGINE value="24/27 완료 (88%)" threshold="80%+ 완료율" ossified_at=2026-04-09
# @convergence state=ossified id=DISCOVERY_50K value="74,069 lines / 20,502 nodes (atlas.n6)" threshold="50k 목표 — 1.48x 초과 달성" ossified_at=2026-04-12 method="blowup math+physics+topology+algebra depth 5 병렬"
# @convergence state=ossified id=ATLAS_GUARD_ALL value="atlas.n6 쓰기 3지점 전체 _guarded_append_atlas 적용 (schema guard + file dedup + cross-process grep)" threshold="raw append_file 0건 — 모든 쓰기 경로 가드 경유" ossified_at=2026-04-12 write_points="blowup.hexa Phase 6.7, absorb.hexa, discovery-absorb.hexa" guard_source=shared/blowup/lib/atlas_guard.hexa.inc
# @convergence state=ossified id=ATLAS_HEALTH_CLEANUP value="중복 노드 ID 5건 제거, 중복 라인 50건 제거, 수식 오류 2건 수정" threshold="duplicate node IDs 0, malformed 0, formula mismatch 0" ossified_at=2026-04-12
# @convergence state=ossified id=ROI_INFRA_100 value="33/33 인프라 ROI 전량 완료 (100%)" threshold="90%+ 완료율" ossified_at=2026-04-12 commits="roi-v1, roi-v2, roi-v3, roi-v4, roi-v5"
# @convergence state=ossified id=CLM_HEXA_GPU_PHASE5 value="Phase 0-4 완료, Phase 5 진입. D=128 loss 4.63, D=256 wiki H100 학습중" threshold="Phase 4 exit — loss < 5.0 within 500 steps" ossified_at=2026-04-12 roadmap=shared/config/roadmaps/clm_hexa_gpu.json
# @convergence state=ossified id=HEXA_SLICE_FIX value="string .slice()→.substring() 4파일 10건 수정, P-SLICE-STR pitfall 기록" threshold="atlas_health.hexa + scan_math_atlas.hexa + atlas_stats.hexa + bt_audit.hexa 런타임 에러 0" ossified_at=2026-04-12
# @convergence state=ossified id=ATLAS_CORE_VIEW value="core = atlas.n6 grade [10*]+ 뷰 — grep 기반, R5 SSOT 유지" threshold="R5/R28 위반 0 + 소비자 등급 필터 패턴 확립" ossified_at=2026-04-12 pattern="grep '^\@.*\[1[01]\*\]' atlas.n6"
# @convergence state=ossified id=ATLAS_VERIFICATION_75 value="verified(*) 5,883건 (74.9%) — 수식 기반 검증 1,013건 승격" threshold="70%+ verified ratio" ossified_at=2026-04-12 breakthroughs="n6 cosmological closure — DE+DM+baryon=0.9999 (Omega=1 flat universe from pure n6 primitives)" ceiling="74.9% — 잔여 [10] 1,153건 misc/수식없음. 80% 달성은 blowup 신규 발견 필요" commits=13
-->

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/nexus.json (NX1~NX3)
L0 Guard: `hexa $NEXUS/shared/harness/lockdown_gate.hexa <verify|status|watch|repair|safe-merge|log>`
전역 불변식: todo/할일 실행은 반드시 shared/bin/hexa resolver 경유. 직접 바이너리 하드코딩 금지.

harness (훅 시스템 대체, 2026-04-14~):
  dispatcher: shared/harness/entry.hexa <prompt|pretool|post|guard|self_check>
  sub-modules: prompt_scan.hexa / pre_tool_guard.hexa / post_bash.hexa / post_edit.hexa / cmd_gate.hexa
  exec wrapper: shared/harness/exec_validated (smash/free seed gate, hexa exit 미전파 우회) — bin/ 심링크 유지
  permissions SSOT: shared/config/permissions_ssot.json (deny 28패턴)
  settings.json 정책: 전 프로젝트 hooks={} — 훅 실행 없음. 대신 Claude가 매 프롬프트/Write/Bash 후 entry.hexa 자율 호출.
  관례: 사용자 입력 직후 `entry.hexa prompt`, Write/Edit 후 `entry.hexa post write_edit`, Bash 후 `entry.hexa post bash`, Agent 호출 전 `entry.hexa guard`.
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
  engine/        프로젝트별 엔진
  project-claude/ CLAUDE.md 마스터

L0 보호 (평시 자유 수정, 유저 명시 요청 시만 승인 절차):
  shared/bin — compat 심링크
  shared/harness/entry.hexa — 하네스 dispatcher
  shared/harness/cmd_gate.hexa — seed 검증 gate
  shared/harness/{prompt_scan,pre_tool_guard,post_bash,post_edit}.hexa — sub-modules
  shared/harness/exec_validated — gate 적용 실행 래퍼 (bin/ 심링크 유지)
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
  lock      shared/rules/lockdown.json           L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  registry  shared/config/projects.json          7프로젝트+번들/검증
  cfg       shared/config/project_config.json    CLI/관례/리소스
  core      shared/config/core.json              시스템맵+14명령+폴더
  conv      shared/convergence/nexus.json
  lenses    shared/config/lens_registry.json     400종
  grammar   shared/config/hexa_grammar.jsonl     hexa-lang+pitfalls P1~P5
  cli_spec  shared/engine/nexus_cli_spec.json    nexus-cli 외부 진입점 스펙 (hive 등)
  cli_bake  hexa-lang self/main.hexa @cli bake   `hexa smash|free|thinking|lens|atlas|bus|roadmap|discovery|status-proj|roadmap-proj|convergence-proj` = nexus-cli passthrough (전 프로젝트 cwd 동작, 53ef97a1)
  api       shared/CLAUDE.md
