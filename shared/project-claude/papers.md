# papers — 논문 배포 (Zenodo/OSF)

## 명령어 (shared/config/commands.json)

| 명령 | 동작 |
|------|------|
| `todo` / `할일` | 전 프로젝트 할일 표 |
| `go` / `가자` | 모든 TODO 병렬 발사 |
| `smash` / `부셔` | 블로업 돌파 엔진 |
| `explore` / `탐색` | 5모듈 자율 DFS |
| `list` / `목록` | 이 명령어 표 다시 출력 |

> shared/ JSON 단일진실 (R14). 규칙: `shared/rules/common.json` (R0~R27)

## ⛔ 규칙 준수 (필수)

작업 시작 전 `shared/rules/common.json` + `shared/rules/papers.json` 을 읽고 전 규칙 준수. 위반 시 즉시 수정.

## ref

```
rules     shared/rules/common.json             R0~R27 공통
project   shared/rules/papers.json             PP1~PP3
lock      shared/rules/lockdown.json           L0/L1/L2
cdo       shared/rules/convergence_ops.json    CDO 수렴
registry  shared/config/projects.json
cfg       shared/config/project_config.json    CLI/발행/SSOT/라이선스
core      shared/config/core.json
conv      shared/convergence/papers.json
ssot      manifest.json                        논문 메타데이터
api       shared/CLAUDE.md
```
