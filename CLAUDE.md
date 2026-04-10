# nexus — NEXUS-6 중앙 허브

> shared/ JSON 단일진실 (R14). 규칙: `shared/rules/common.json` (R0~R27)

## 돌파 시스템

- "XXX 돌파" → `blowup.hexa "XXX" 3` 자동 실행 (문장 전달)
- 확인 질문 없이 즉시 Bash 실행

```sh
hexa shared/blowup/core/blowup.hexa <domain> 3 --seeds "$(hexa shared/blowup/seed/seed_engine.hexa merge | tr '|' ',')"
```

## shared/ 트리

```
blowup/        돌파 엔진 — core/guard/modules(5)/lens/ouroboros/seed
hooks/         Claude Code 훅 (.hexa) — 돌파감지/문법가드/규칙로더
rules/         AI-native 규칙 — common/project/lockdown/cdo
config/        SSOT 정책 — core.json(14명령)/lens_registry(397)/hexa_grammar
discovery/     발견 허브 — reality_map/growth_bus/theory_registry
bt/            BreakThrough audit — bt_audit.py/auto_bt.log
convergence/   CDO 수렴 추적
consciousness/ anima 런타임 + 법칙망
n6/            n6 atlas + 수학 맵
dse/           Design Space Exploration
engine/        프로젝트별 엔진 .hexa
project-claude/ 프로젝트 CLAUDE.md 마스터
```

## ref

```
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
```
