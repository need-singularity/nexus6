# scripts/ — 공용 .hexa 스크립트 + bin (R1 HEXA-FIRST)

sync (R1 migrated .sh → .hexa):
  sync_claude_md.hexa   sync_settings.hexa
  sync-calculators.hexa sync-claude-rules.hexa sync-dse.hexa
  sync-math-atlas.hexa  sync-nexus-lenses.hexa sync-readmes.hexa
  (2026-04-14 산문 md 제거 — sync-all-verify.md/shared_work_rules.md → harness/CLAUDE.md SSOT 단일화)

rotate: rotate_discovery_log.hexa (ROI #3 — discovery_log.jsonl 주간 로테이션+gzip)
        rotate_auto_gap.hexa (ROI #19 — auto_gap.log 일간+크기(5MB) 듀얼 트리거 로테이션+gzip, keep 7일)
stream: stream_discovery_graph.hexa (ROI #8 — NDJSON 스트리밍 유틸. stats/nodes/edges/ids/query/domain/window)

run: nexus_ensure_running.hexa

bin/: 실행 바이너리 디렉토리 (shared/bin → scripts/bin 심링크)
  hexa  : hexa 바이너리 resolver (R1 예외 — bootstrap bash, hexa 를 찾기 전에 실행)
  infra : 4호스트 자원 현황 CLI (R1 예외 — Python3 interpreter 사용, json-only output)
          → SSOT: shared/infra_state.json, config: shared/config/infrastructure.json
          → 사용법: infra | infra json | infra rec

parent: ../CLAUDE.md → "scripts"
