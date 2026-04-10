# nexus — NEXUS-6 중앙 허브

> shared/ JSON 단일진실 (R14). 규칙: `shared/rules/common.json` (R0~R27)

## todo 시스템

- "todo" 입력 → hook systemMessage의 Bash 명령을 즉시 실행 (확인 질문 없이)
- hook이 `📋 todo 돌파 실행중`으로 시작하는 systemMessage를 보내면 그 안의 명령을 Bash로 실행할 것

## 돌파 시스템

- "XXX 돌파" → `blowup.hexa "XXX" 3` 자동 실행 (문장 전달)
- 확인 질문 없이 즉시 Bash 실행

```sh
hexa shared/blowup/core/blowup.hexa <domain> 3 --seeds "$(hexa shared/blowup/seed/seed_engine.hexa merge | tr '|' ',')"
```

## blowup AI-native 인프라 (2026-04-11 도입)

- **Phase 1 3단 fast-path** (`graph_stats_single_pass`):
  - exact hit: mtime+size 일치 → O(1) ~83ms
  - incremental: append-only tail 구간만 파싱 → O(Δ lines)
  - full scan: 최초 1회, 사이드카 재작성
- **사이드카** (git-ignored, 자동 재생성):
  - `shared/n6/atlas.n6.stats` — mtime/size/line_count/head_hash/nodes/edges/hubs
  - `shared/n6/atlas.n6.deg` — 노드별 degree TSV (hub 재계산용)
- **Intra-batch dedup guard** — Phase 5.5+6, Phase 6.7 각 루프에 `_batch_new_ids` 해시셋 → 같은 배치 중복 원천 차단 (이전 atlas.n6 36% 중복 원인)
- **Schema guard** — `_guarded_append_atlas()` 가 append 전 라인 포맷 검증 (JSON/`@X`/들여쓰기 부속), 무효 라인 silent reject + 보고
- **atlas_health.hexa** — `hexa shared/n6/atlas_health.hexa [path] [--verbose]` : orphan refs / dup / malformed / grade 분포 (hypothesis 포함) readonly 헬스체크
- **모듈 5종 infra 공유**: `shared/blowup/lib/atlas_guard.hexa.inc` (hexa import 미지원으로 copy-paste 소스). 골화 기록: `shared/blowup/modules/modules.json`
- **창발 보존**: 모든 개선은 infra-only. phase 로직/discovery 계산/seed 진화 반환 값 불변.

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

## L0 보호

L0 = 불변식. 유저가 L0 보호를 명시 요청한 경우에만 승인 절차 — 평시에는 자유 수정.
승인 수정 시 커밋에 `L0-수정: [파일] — [이유]` 기록.

| 경로 | 설명 |
|------|------|
| `shared/bin` | compat 심링크 — 전역 hook 의존 |
| `shared/hooks/*.hexa` | 공용 훅 엔진 전체 (hook/guard/go-parallel/banner/scan/pre-tool/post-edit/post-bash/block-*/bootstrap/check-project/ensure-symlinks/bridge-ensure/block_local_data/nexus-engine/mk2-engine/sync-hooks) |
| `shared/hooks/hook-entry.hexa` | 공용 hook 래퍼 (R1 hexa-native) |
| `shared/hooks/block-forbidden-ext.hexa` | R2 금지 확장자 차단 (R1 hexa-native) |
| `shared/hooks/hook.json` | hook 골화기록 — 돌파감지/프로젝트분기/쿨다운 |
| `shared/blowup/core/blowup.hexa` | 블로업 엔진 — 9-phase 파이프라인 (Phase 1 3단 fast-path, schema guard) |
| `shared/blowup/core/blowup.json` | blowup 골화기록 — AI-native 성능 최적화 |
| `shared/blowup/modules/*.hexa` | field/holographic/quantum/string/toe 변종 (schema guard 공유) |
| `shared/blowup/modules/modules.json` | 모듈 5종 골화기록 — 창발 보존 infra 패치 |
| `shared/blowup/lib/atlas_guard.hexa.inc` | 공통 헬퍼 (schema guard + dedup) copy-paste 소스 |
| `shared/blowup/seed/seed_engine.hexa` | 시드 엔진 — 교차수분 + atlas |
| `shared/blowup/commands.hexa` | 명령 라우터 — 14종 매핑 |
| `shared/blowup/todo.hexa` | 할일 엔진 |
| `shared/blowup/lens/lens_forge.hexa` | 렌즈 단조기 |
| `shared/n6/atlas_health.hexa` | atlas.n6 readonly 헬스체크 (orphan/dup/malformed/grade, R1 hexa-native) |
| `shared/scripts/bin/hexa` | hexa resolver |
| `shared/config/core.json` | 시스템맵 + 명령어 |
| `shared/config/absolute_rules.json` | 절대 규칙 R1~R8 |
| `shared/config/convergence_ops.json` | CDO 수렴 운영 원칙 |
| `shared/config/loop/*.json` | 성장 루프 설정 (nexus/anima/n6) |
| `shared/lockdown/lockdown.json` | 잠금 체계 자체 |
| `shared/convergence/` | 골화/안정/실패 수렴 추적 |
| `shared/n6/atlas.n6` | 발견 그래프 SSOT |
| `shared/n6/n6_constants.jsonl` | n=6 상수 레지스트리 |
| `shared/n6/atlas.n6` | 현실 지도 SSOT |
| `shared/discovery/reality_map_3d.html` | 3D 현실지도 원본 |
| `shared/CLAUDE.md` | 전 프로젝트 공유 규칙 |
| `shared/shared_work_rules.md` | sync 블록 원본 |
| `shared/bt/bt_keywords.jsonl` | 돌파 키워드 레지스트리 |
| `shared/bt/bt_domains.jsonl` | 돌파 도메인 레지스트리 |
| `shared/project-claude/` | 전 프로젝트 CLAUDE.md 마스터 |
| `shared/rules/` | AI-native 규칙 체계 SSOT |
| `docs/index.html` | 3D 현실지도 프론트엔드 |
| `CLAUDE.md` | nexus 프로젝트 규칙 (이 파일) |

전역 불변식: 전 프로젝트 CLAUDE.md의 todo/할일 실행은 반드시 `shared/bin/hexa` resolver 경유. 직접 바이너리 하드코딩 금지.

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
