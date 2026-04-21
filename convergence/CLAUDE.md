# convergence/ — CDO 수렴 추적

states: ossified | stable | in_flight | pending | completed | completed_gap | failed | blocked
files:  nexus anima n6-architecture hexa-lang papers void airgenome + stage3 결과  (8 JSON)
ref:    ../config/convergence_ops.json | ../config/absolute_rules.json (R4,R9~R11)

primary_entry_point:
  anima.json — 모든 anima 알고리즘(훈련/추론/속도/정확도/수치기법) 단일 진실
  새 세션 bootstrap 시 첫 참조. in_flight/next_levers 파악 → state/training_speed_ceilings.json 상세 수치.
  algorithm 작업은 반드시 여기 등록 — 분산 금지 (user directive 2026-04-16).

parent: ../CLAUDE.md → "convergence"
