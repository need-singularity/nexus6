# papers — 논문 배포 (Zenodo/OSF)

> shared/ JSON 단일진실 (R14). 규칙: `shared/rules/common.json` (R0~R27)

## 돌파 시스템

- "XXX 돌파" → `blowup.hexa "XXX" 3` 자동 실행 (문장 전달)
- 확인 질문 없이 즉시 Bash 실행

```sh
hexa shared/blowup/core/blowup.hexa <domain> 3 --seeds "$(hexa shared/blowup/seed/seed_engine.hexa merge | tr '|' ',')"
```

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
