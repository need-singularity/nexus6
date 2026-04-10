# calc/ — Calculator tools (Python)

HEXA 우선: iter>10K | t>10s | combo>10^6 | MC>100K | brute/grid/large-N → mk2_hexa/native/
Python 한정: 단발 검증 | 오차표 | fetch/API | 시각화 | 프로토타입

HEXA   mk2_hexa/native/  | nexus mk2 run <m>           | constants,pure_math,classify,grading,cycle
Python calc/              | python3 calc/<n>.py [args] | <domain>_<purpose>.py, argparse, ASCII out

verifiers:
  fusion_hypothesis_verifier.py    FUSION-001~017                17
  fusion_plasma_sc_verifier.py     FUSION-018~037,SC,SCMAG,TOKAMAK 53
  extreme_hypothesis_verifier.py   17 도메인 통합               337
tools:
  hypothesis_verifier.py r_spectrum.py statistical_tester.py experimental_protocol.py validate_calculators.py
sub:
  auto_stubs/  verify_*.py (137) — 자동 생성 스텁
  data/MNIST   검증 데이터셋

parent: ../CLAUDE.md → "calc"
