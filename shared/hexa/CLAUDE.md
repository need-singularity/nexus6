# hexa/ — hexa-lang 변환/포팅 + 문법

artifacts:
  hexa-lang_breakthroughs.json           돌파 기록
  hexa_speed_ideas.jsonl                 속도 최적화 아이디어
  porting_log.jsonl                      Python → hexa 포팅 로그
  hexa_to_anima_20260410{,_corrected,_final}.json

sub:
  grammar/  spec.jsonl pitfalls.jsonl effects.jsonl autofix.json
            convergence.json changelog.jsonl issues.jsonl

ref: ../config/hexa_grammar.jsonl (SSOT 문법 + P1~P5)

parent: ../CLAUDE.md → "hexa"
