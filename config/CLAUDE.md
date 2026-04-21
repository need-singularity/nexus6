# config/ — SSOT 정책/규칙/락다운/렌즈/문법

L0:
  core-lockdown.json    DEPRECATED (shared/lockdown/lockdown.json 으로 이관)
  absolute_rules.json   R0~R27 (33개) + NX/AN/N6/PP/HX/VD/CT/AG
  core.json             시스템맵 + 14명령 + 폴더

registry:
  projects.json          7 프로젝트 + 번들/검증
  nexus-projects.json    프로젝트 레지스트리
  project_config.json    CLI/관례/리소스
  project_aliases.jsonl  별칭
  installed_tools.json   도구 인벤토리

hosts:
  hetzner.json ubuntu.json vastai.json infrastructure.json  (4 호스트)
  hetzner_prompt.md  원격 실행 프롬프트

lens/grammar:
  lens_registry.json   400 렌즈
  custom_lenses.jsonl  사용자 렌즈
  hexa_grammar.jsonl   hexa-lang + P1~P5
  calculators.json     계산기 카탈로그
  CALCULATOR_RULES.md GRADE_RUBRIC_1_TO_10PLUS.md

sub:
  loop/      자율 데몬 — 하위 CLAUDE.md
  roadmaps/  18 시스템 로드맵 JSON

ops:
  convergence_ops.json  수렴 파이프 (R4,R9~R11)
  claude-settings.json  hooks/settings 미러
  cmd_aliases.jsonl     명령 alias

parent: ../CLAUDE.md → "config"
