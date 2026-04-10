# scripts/ — 공용 bash 스크립트 + bin

sync:
  sync-calculators.sh sync-claude-rules.sh sync-dse.sh
  sync-math-atlas.sh sync-nexus-lenses.sh sync-readmes.sh
  sync-all-verify.md

run: nexus_ensure_running.sh

bin/: 실행 심볼릭 링크 디렉토리

parent: ../CLAUDE.md → "scripts"
