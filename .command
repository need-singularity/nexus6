# nexus /.command — declarative subcommand registry SSOT
# Mirrors hexa-lang /.command schema (3-repo convergence per hive raw 83).
# Source of truth: cli/run.hexa subcommand dispatch (5800+ lines).
# Cross-ref: /core/.workspace 의 `command <name>` 블록 (member nexus exports nx CLI).
# Created 2026-04-27.
#
# Format:
#   command <name> <category> "<description>"
#     keywords <k1> <k2> ...
#     handler <relative/path.hexa>
#     entry <subcommand-token>
#     shim <yes|no>
#     subcommands <s1> <s2> ...   (optional)
#
# Categories: engines | audit | bridge | core | ops

command kick engines "kick (ω-cycle) executor — kick ≡ ω-cycle full equivalence"
  keywords kick ω-cycle 킥 사이클 omega cycle
  handler cli/run.hexa
  entry kick
  shim yes
  subcommands tree run bench help
  why nexus 의 atomic 작업 단위. K≥3 직교 axes (raw 48) + falsifier 5 사전등록 (raw 71) + parent-sid (raw 44) + sentinel `__KICK_RESULT__` (raw 80) 강제. .guide 워크플로 1-10 단계 참조.
  proof tool/kick_dispatch.hexa
  proof tool/kick_tree.hexa
  proof tool/kick_bench.hexa

command omega engines "L_ω apex drill (default depth=auto, speculate=3, adaptive=on)"
  keywords omega 옴메가 ω-apex
  handler cli/run.hexa
  entry omega
  shim yes
  why kick 의 L2 stratum 이지만 별도 top-level 진입점. seed-driven exhaustive Ω-saturation cycle.
  proof cli/run.hexa (omega subcommand 분기)

command drill engines "F6 DRILL_GAP divergent seed 발사 (N>=3 angles)"
  keywords drill 드릴
  handler cli/run.hexa
  entry drill
  shim yes
  why kick stratum 으로 통합 (kick run --stratum drill) 이지만 단독 호출 호환 보존.
  proof cli/run.hexa (drill subcommand 분기)
  note kick 의 L2 stratum 으로 absorbed — 새 작업은 `nexus kick run <topic> --stratum drill` 권장.

command atlas audit "atlas.n6 검색/추가 — 외부접근 §3 독점 subcmd"
  keywords atlas 지도 atlas.n6
  handler cli/run.hexa
  entry atlas
  shim yes
  subcommands search add list
  why atlas.n6 (n6-architecture canonical) 검색 진입점. .own atlas-absorb-mandatory 와 cross-link.
  proof cli/run.hexa (atlas subcommand 분기)

command roadmap audit "로드맵 조회/상태 — next/list/status"
  keywords roadmap 로드맵
  handler cli/run.hexa
  entry roadmap
  shim yes
  subcommands next list status
  why .roadmap SSOT 조회. raw 87 sync-witness + raw 88 transition-gate 와 cross-link.
  proof cli/run.hexa (roadmap subcommand 분기)
  proof tool/roadmap_engine.hexa

command bus audit "이벤트 버스 publish/tail/history"
  keywords bus 버스 event
  handler cli/run.hexa
  entry bus
  shim yes
  subcommands publish tail history
  why cross-tool 이벤트 publish/subscribe. ω-cycle 진행 상황 + atlas absorb 완료 알림 등.
  proof cli/run.hexa (bus subcommand 분기)

command status ops "harness/loop/cl pool 헬스 요약"
  keywords status 헬스 상태 health
  handler cli/run.hexa
  entry status
  shim yes
  proof cli/run.hexa (status subcommand 분기)

command doctor ops "통합 진단 — hexa bin/core/launchd/ring/throttle"
  keywords doctor 진단 diagnose
  handler cli/run.hexa
  entry doctor
  shim yes
  proof cli/run.hexa (doctor subcommand 분기)

command scan audit "code/config pattern scan"
  keywords scan 스캔
  handler cli/run.hexa
  entry scan
  shim yes
  proof cli/run.hexa (scan subcommand 분기)

command record audit "convergence entry recorder"
  keywords record 기록 수렴
  handler cli/run.hexa
  entry record
  shim yes
  why /core/.workspace `# @convergence` 라인 자동 append.
  proof cli/run.hexa (record subcommand 분기)

# follow-up:
#   1. tool/command_lint.hexa — validate parity between cli/run.hexa dispatch table ↔ .command ↔ /core/.workspace
#   2. each command auto-generates --help from .command entry (currently hardcoded in cli/run.hexa)
#   3. /core/.workspace 의 8개 command 블록 (kick/scan/record/atlas/roadmap/bus/status/doctor) 과 sync 검사
#   4. raw 1 os-lock 확장 — chflags uchg .command
