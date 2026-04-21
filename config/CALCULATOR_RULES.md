# CALCULATOR_RULES — 전 프로젝트 계산기 개발 규칙

priority:
  1순위  HEXA   반복>10K / 실행>10s / 조합>10^6 / MC>100K / grid·brute·행렬·대규모파싱
  2순위  Python 단일공식 / 오차계산 / fetch·API / numpy·scipy / 시각화·프로토타입

hexa 경로:
  nexus            shared/blowup/**/*.hexa (R14 카테고리)
  n6-architecture  shared/blowup/core/*.hexa
  anima            shared/blowup/core/*.hexa

판단:
  반복>10K or 실행>10s or 조합>10^6 → HEXA (shared/blowup/core/<name>.hexa)
  else → Python (tools/<name>.py)

레지스트리: config/calculators.json (자동 스캔)
지원: *.py (docstring), *.hexa (헤더 주석)

hexa 템플릿:
  // <Name> — <한 줄 설명>
  module <name>
  import constants
  fn main() { ... }

python 템플릿:
  """<Name> — <한 줄 설명>. Usage: python tools/<name>.py"""

parent: CLAUDE.md → "config"
