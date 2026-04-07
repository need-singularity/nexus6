  ⛔⛔⛔ 이 블록은 삭제/수정/이동 금지! (sync-claude-rules.sh 자동 주입)
  ⛔ 규칙/인프라 원본: shared/ JSON 파일 참조. 절대 삭제하지 마세요!

  ═══════════════════════════════════════════════════════════════
  ★★★ 수렴 기반 운영 — 규칙 원본: shared/absolute_rules.json ★★★
  ═══════════════════════════════════════════════════════════════

  공통 규칙 (R1~R8):
    R1  HEXA-FIRST — .hexa만, sh/py/rs 신규 금지
    R2  하드코딩 절대 금지 — shared/*.jsonl 동적 로드
    R3  NEXUS-6 스캔 의무 — 변경 전후 스캔, 스캔 없이 커밋 금지
    R4  CDO 수렴 — 이슈→해결→규칙승격→재발0
    R5  SSOT — 데이터 원본 JSON 1개, 중복 금지
    R6  발견/결과 자동 기록 — 누락=소실=금지
    R7  sync 블록 삭제/수정/이동 금지
    R8  데이터 파일 로컬 보관 금지 — nexus/shared만 (nexus 제외)

  프로젝트별 규칙: shared/absolute_rules.json → projects 참조

  ═══════════════════════════════════════════════════════════════
  ★ 핵심 인프라 (shared/) ★
  ═══════════════════════════════════════════════════════════════

  코어 인덱스:     shared/core.json (시스템맵 + 명령어 14종 + 프로젝트 7개)
  보호 체계:       shared/core-lockdown.json (L0 22개 / L1 / L2)
  절대 규칙:       shared/absolute_rules.json (공통 R1~R8 + 프로젝트별 17개)
  수렴 추적:       shared/convergence/ (골화/안정/실패 — 7 프로젝트)
  할일 SSOT:       shared/todo/ (수동 + 돌파 엔진 자동)
  성장 루프:       shared/loop/ (nexus/anima/n6 자율 데몬)

  ═══════════════════════════════════════════════════════════════
  ★ NEXUS-6 (1022종 렌즈) — 상세: shared/CLAUDE.md ★
  ═══════════════════════════════════════════════════════════════

  CLI:  nexus scan <domain> | nexus scan --full | nexus verify <value>
  API:  nexus.scan_all() | nexus.analyze() | nexus.n6_check() | nexus.evolve()
  합의: 3+렌즈=후보 | 7+=고신뢰 | 12+=확정
  렌즈: shared/lens_registry.json (1022종)

  ═══════════════════════════════════════════════════════════════
  ★ 명령어 — 상세: shared/core.json → commands ★
  ═══════════════════════════════════════════════════════════════

  못박아줘    → L0 등록 (core-lockdown.json)
  todo/할일   → 돌파 엔진 할일 표 (todo.hexa)
  블로업/돌파 → 9-phase 특이점 (blowup.hexa)
  go          → 전체 TODO 백그라운드 병렬 발사
  설계/궁극의 → 외계인급 설계 파이프라인
  동기화      → 전 리포 sync (sync-all.sh)
