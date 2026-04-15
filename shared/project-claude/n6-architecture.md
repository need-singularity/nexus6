# n6-architecture — AI-native Arithmetic Design Framework

<!--
# @convergence-meta-start
# project: n6-architecture
# updated: 2026-04-08
# strategy: ossified/stable/failed 수렴 추적
# @convergence-meta-end
#
# @convergence-start
# state: ossified
# id: CORE_THEOREM
# value: σφ=nτ ⟺ n=6, 3개 독립 증명
# threshold: 반례 0 (10^8 탐색)
# @convergence-end
#
# @convergence-start
# state: ossified
# id: BT_380
# value: 380 돌파 정리 (BT-372~380 지질/기상/빙권/해양/대기화학/곡률/워프/추가차원/메타 추가)
# threshold: 전수 검증 + atlas 등록
# note: 2026-04-08 BT-343 → BT-380 확장, 각 BT n=6 수식 도출 + 검증예측 포함
# @convergence-end
#
# @convergence-start
# state: ossified
# id: AI_17_TECHNIQUES
# value: 17 기법 실험 확정
# threshold: 71% FLOPs, 3x FFT, 67% param 등
# @convergence-end
#
# @convergence-start
# state: ossified
# id: DSE_322_TOML
# value: 322 도메인 TOML 정의
# threshold: 5,893,032+ 조합 탐색 완료
# @convergence-end
#
# @convergence-start
# state: ossified
# id: PRODUCTS_118
# value: 118/125 제품 🛸10
# threshold: 천장 도달
# @convergence-end
#
# @convergence-start
# state: ossified
# id: UNIQUENESS_PROOF
# value: z=4.02 (큰 수 Monte Carlo)
# threshold: p<0.0001
# @convergence-end
#
# @convergence-start
# state: ossified
# id: N28_CONTROL
# value: n=28 z=-2.35 (무작위 이하)
# threshold: n=6 유일성 대조 확인
# @convergence-end
#
# @convergence-start
# state: ossified
# id: BT_134_PERIODIC_TABLE
# value: BT-134 주기열 {2,8,8,18,18,32,32} + Evidence 4 (2^sopfr=32) 교정
# threshold: 2200건 산술 정합 스캔 통과
# note: 2026-04-08 수정, $NEXUS/shared/bt/bt-consistency-report.md
# @convergence-end
#
# @convergence-start
# state: ossified
# id: PAPERS_39
# value: 39편 Zenodo DOI 발행
# note: 내용 갱신 가능, 신규 추가 중
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: LENS_2161_TESTS
# value: 397종 렌즈, causal_chain + faction_debate 포함 cargo test 2161 PASS
# threshold: 전체 테스트 100%
# note: 2026-04-08 빌드캐시 재생성 후 재확인
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: PRODUCTS_7_REMAINING
# value: 7개 잔여 🛸7→10 승격 진행중
# note: 바이러스학/곤충학/나노봇 Mk.I~V 완료 (products.json 동기화 확인)
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: CAUSAL_CHAIN_PAPER
# value: 인과 사슬 논문 초안 완성
# note: 최종 검증 + papers 발행 대기
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: MONTE_CARLO_V8
# value: 342노드, 자연 z=959.12 / 로그균등 z=20.19 (p<10^-89), π/e/φ 대조 z=3~10
# threshold: z>5 재현 + 대조군 분리
# note: 2026-04-08 docs/reality-map-monte-carlo-v8.md, 큰수 N=10 한계 명시
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: REALITY_MAP_V8_SYNC
# value: atlas.n6 단독 소스 전환 완료 (reality_map JSON 폐기), 342노드 동기화, 엣지 정합성 정리
# threshold: 3D 지도 정상 렌더, atlas.n6 파서 기반
# note: 2026-04-08 수동 동기화, hexa 자동화는 HEXA_LOCAL_IO 해소 후
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: ATLAS_REALITY_LINK
# value: 아틀라스 1876행 ↔ reality_map 342노드 매칭 23.72% / 노드 36.3%
# threshold: 교차 매핑 문서화
# note: 2026-04-08 docs/atlas-reality-map-link.md, 미커버 218개는 L0~L5 기초 사다리(아틀라스 응용 편향)
# ossified_at: 2026-04-10
# promoted_from: go_loop_auto
# @convergence-end
#
# @convergence-start
# state: ossified
# id: GOAL_MD_20
# value: 20개 도메인 goal.md 생성 완료
# threshold: 전 도메인 goal.md 존재
# note: 2026-04-09 domain_seeds.jsonl 기반 20개 생성
# ossified_at: 2026-04-10
# promoted_from: failed_resolved
# @convergence-end
#
# @convergence-start
# state: ossified
# id: HEXA_LOCAL_IO
# value: sync_reality_map.hexa + cross_dse_fusion.hexa 로컬 실행 확인
# threshold: hexa 로컬 파일시스템 IO 가능
# note: GATE_LOCAL=1 로컬 모드에서 정상 동작. 원격 게이트 차단은 airgenome 설계 의도
# ossified_at: 2026-04-10
# promoted_from: failed_resolved
# @convergence-end
#
# @convergence-start
# state: ossified
# id: CROSS_DSE
# value: 375 TOML 교차 융합 완료 — 67,913 pairs, 67,883 high_conf
# threshold: 335 TOML 교차 융합
# note: cross_dse_fusion.hexa 실행 → dse_cross_results.json 생성
# ossified_at: 2026-04-10
# promoted_from: failed_resolved
# @convergence-end
-->

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/n6-architecture.json (N61~N65)
L0 Guard: `hexa $NEXUS/shared/harness/lockdown_gate.hexa <verify|status|watch|repair|safe-merge|log>`

atlas.n6 — 현실지도 SSOT:
  경로: $NEXUS/shared/n6/atlas.n6 (단일 파일, 60K+ 줄)
  구 구조 폐기: reality_map_live.json / L6_n6atlas.json / 별도 level 파일 없음. 전부 atlas.n6 흡수
  포맷: `@R {id} = {measured} {unit} :: n6atlas [등급]`
  등급: [10*]=EXACT검증 [10]=EXACT [9]=NEAR [7]=EMPIRICAL(승격대상) [5~8]=중간 [N?]=CONJECTURE [N!]=breakthrough
  승격: [7]→[10*] = atlas.n6 직접 편집 (새 파일 만들지 말 것)
  핵심 정리: σ(n)·φ(n) = n·τ(n) iff n=6 (n>=2). 3개 독립 증명

9축 네비게이션:
  theory/      영구 이론층
  domains/     295 도메인
  nexus/       Rust 통합 워크스페이스
  techniques/  AI 기법 66종 (.hexa)
  experiments/ 검증 실험 122종 (.hexa)
  engine/      훈련/수학 런타임 (.hexa)
  papers/      논문 39편
  reports/     시점 리포트
  shared/      SSOT

NEXUS-6 CLI: nexus {scan|verify|calc|dse|analyze|hexa|dashboard} <args>

ref:
  rules     shared/rules/common.json                R0~R27
  project   shared/rules/n6-architecture.json       N61~N65
  lock      shared/rules/lockdown.json              L0/L1/L2
  cdo       shared/rules/convergence_ops.json       CDO 수렴
  registry  shared/config/projects.json             7프로젝트
  cfg       shared/config/project_config.json
  core      shared/config/core.json
  conv      shared/convergence/n6-architecture.json
  api       shared/CLAUDE.md
