# calc/ — Calculator tools (Python)

HEXA 우선: iter>10K | t>10s | combo>10^6 | MC>100K | brute/grid/large-N → shared/blowup/ (R14)
Python 한정: 단발 검증 | 오차표 | fetch/API | 시각화 | 프로토타입

HEXA   shared/blowup/    | hexa smash --seed "<d>" [--depth 3] (권장, cmd_gate+audit) / hexa run shared/blowup/core/blowup.hexa <d> (raw) | todo,blowup,core,modules,lens,ouroboros,seed
Python calc/              | python3 calc/<n>.py [args] | <domain>_<purpose>.py, argparse, ASCII out

verifiers:
  fusion_hypothesis_verifier.py    FUSION-001~017                17
  fusion_plasma_sc_verifier.py     FUSION-018~037,SC,SCMAG,TOKAMAK 53
  extreme_hypothesis_verifier.py   17 도메인 통합               337
tools:
  hypothesis_verifier.py r_spectrum.py statistical_tester.py experimental_protocol.py validate_calculators.py
sub:
  auto_stubs/        verify_*.hexa (140, gitignored) — 자동 생성 스텁
  auto_stubs_gen.hexa  스텁 발사기 — --import-py(1회) / --emit / --status / --append <json>|- (manifest +1 + stub emit, id dedup, sentinel __APPEND_RESULT__ OK_NEW|OK_DUP|FAIL). SSOT: auto_stubs/manifest.jsonl
  data/MNIST   검증 데이터셋

parent: ../CLAUDE.md → "calc"
