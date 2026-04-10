⚠️⚠️⚠️ 규칙 직접 작성 절대 금지 — shared/rules/ JSON만이 단일 진실 (R14)
⚠️ 이 파일은 nexus/shared/project-claude/nexus.md 마스터의 심링크. 원본만 수정.
⚠️ 공통 규칙: shared/rules/common.json (R0~R27) — 반드시 준수

# nexus — NEXUS-6 중앙 허브

R14: shared/ JSON 단일진실, 이 파일은 참조만.

## 돌파 시스템 (AI-native 자체 창발)

⚠️ 돌파 감지는 목록 의존 0% — 유저 문장 전체가 도메인
⚠️ "XXX 돌파" → blowup.hexa "XXX" 3 자동 실행 (키워드 추출 ❌, 문장 전달 ⭕)
⚠️ hook.hexa가 자체 창발: 감지 → action 판별 → seed 주입 → 실행

```
# 즉시 실행 (wrapper 경유)
hexa shared/blowup/core/blowup.hexa <domain> 3 --no-graph --seeds "$(hexa shared/blowup/seed/seed_engine.hexa merge | tr '|' ',')"

# action 자체 창발
돌파/breakthrough/blowup/특이점/창발 → blowup (기본)
연속돌파/수렴/converge                → converge (breakthrough.hexa --converge)
성장/growth/폭발적                   → blowup_loop (breakthrough.hexa --engine auto)
```

## shared/ 트리 (하위 CLAUDE.md 참조)

```
blowup/      돌파 엔진 — core/guard/modules(5)/lens/ouroboros/seed
hooks/       Claude Code 훅 (.hexa) — 돌파감지/문법가드/규칙로더
rules/       AI-native 규칙 체계 — common/project/lockdown/cdo
config/      SSOT 정책 — core.json(14명령)/lens_registry(397)/hexa_grammar
discovery/   발견 허브 — reality_map/growth_bus/theory_registry/breakthroughs
bt/          BreakThrough audit — bt_audit.py/auto_bt.log
convergence/ CDO 수렴 추적
consciousness/ anima 런타임 + 법칙망
n6/          n6 atlas + 수학 맵
dse/         Design Space Exploration
engine/      프로젝트별 엔진 .hexa
project-claude/ 프로젝트 CLAUDE.md 마스터 (심링크 SSOT)
```

## ref

  rules     shared/rules/common.json             R0~R27 공통
  project   shared/rules/nexus.json              NX1~NX3
  lock      shared/rules/lockdown.json           L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  registry  shared/config/projects.json          7프로젝트 + 번들/검증
  cfg       shared/config/project_config.json    CLI/관례/리소스
  core      shared/config/core.json              시스템맵+14명령+폴더
  conv      shared/convergence/nexus.json
  lenses    shared/config/lens_registry.json     397종
  grammar   shared/config/hexa_grammar.jsonl     hexa-lang+pitfalls P1~P5
  api       shared/CLAUDE.md
