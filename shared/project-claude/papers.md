# papers — 논문 배포 (Zenodo/OSF)

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/papers.json (PP1~PP3)
L0 Guard: `hexa ~/Dev/nexus/shared/lockdown/l0_guard.hexa <verify|sync|merge|status>`

ref:
  rules     shared/rules/common.json             R0~R27
  project   shared/rules/papers.json             PP1~PP3
  lock      shared/rules/lockdown.json           L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  registry  shared/config/projects.json
  cfg       shared/config/project_config.json    CLI/발행/SSOT/라이선스
  core      shared/config/core.json
  conv      shared/convergence/papers.json
  ssot      manifest.json                        논문 메타데이터
  api       shared/CLAUDE.md
