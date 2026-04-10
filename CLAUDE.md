# CLAUDE.md — NEXUS-6 중앙 허브

> 모든 규칙/설정은 shared/ JSON이 단일 진실 (R14). 이 파일은 참조 링크만 유지.

> 🛑 **tecs-l 흡수 진행 중** (2026-04-10): tecs-l/ 는 독립 리포가 아닌 nexus 흡수 대상. Track A 진행 / Track B 보류. 신규 작업은 `mk2_hexa/native/{verify,math,engines,experiments}/*.hexa` 로. 로드맵: `docs/tecs-l-absorption-plan.md`

## 참조

| 항목 | 파일 | 내용 |
|------|------|------|
| 절대 규칙 | `shared/absolute_rules.json` | R1~R21 공통 + 프로젝트별 (NX/AN/N6/PP/HX/VD/CT/AG) |
| 보호 체계 | `shared/core-lockdown.json` | L0/L1/L2 코어 잠금 (L0 37개) |
| 프로젝트 설정 | `shared/project_config.json` | CLI 명령어 구문 / 관례 / 리소스 보호 |
| 시스템 코어 | `shared/core.json` | 시스템맵 + 14종 명령어 + 폴더 구조 |
| 수렴 | `shared/convergence/nexus.json` | CDO 수렴 상태 |
| 수렴 운영 | `shared/convergence_ops.json` | CDO 수렴 운영 원칙 |
| 할일 | `shared/todo/nexus.json` | 우선순위별 TODO |
| 렌즈 | `shared/lens_registry.json` | 397종 망원경 레지스트리 |
| API | `shared/CLAUDE.md` | NEXUS-6 상세 사용법 |
| 문법 | `shared/hexa_grammar.jsonl` | hexa-lang 전체 문법 + pitfalls P1~P5 |
