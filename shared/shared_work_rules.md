  ⛔⛔⛔ 이 블록은 삭제/수정/이동 금지! (sync-claude-rules.sh 자동 주입)
  ⛔ 가설, 규칙, 발견, 망원경 — 모든 리포의 핵심 인프라. 절대 삭제하지 마세요!

  ═══════════════════════════════════════════════════════════════
  ★★★ 수렴 기반 운영 3대 원칙 — 누락 시 작업 중단! ★★★
  ═══════════════════════════════════════════════════════════════

  모든 작업 전 체크 (하나라도 누락 = 작업 중단):
    □ CDO:    이슈 발생 시 JSON에 기록했는가? 규칙 승격했는가?
    □ NEXUS-6: 변경 전후 scan 했는가? anomaly 0인가?
    □ SSOT:   하드코딩 안 했는가? JSON 원본 갱신했는가?

  모든 작업 후 체크:
    □ 트러블슈팅 기록: 에러 있었으면 해당 JSON에 기록
    □ 규칙 승격:       같은 에러 2회 이상 → absolute_rule로 승격
    □ NEXUS-6 스캔:    최종 결과물 scan → anomaly 0 확인
    □ SSOT 동기화:     JSON 변경 시 sync_readme.py --apply
    □ 커밋 메시지:     변경 이유 + 검증 결과 포함

  위반 처리:
    1회: troubleshooting_log에 기록
    2회: absolute_rule로 승격
    3회: 해당 작업 프로세스 재설계

  ═══════════════════════════════════════════════════════════════
  ★ CDO (Convergence-Driven Operations) — 100% 수렴 ★
  ═══════════════════════════════════════════════════════════════
    이슈 → 해결 → 절대 규칙 승격 → 재발 0 → 100% 수렴
    모든 config JSON 필수 구조: _meta + absolute_rules + troubleshooting_log
    원칙 파일: .shared/convergence_ops.json

  ═══════════════════════════════════════════════════════════════
  ★ CDO 세션 부트스트랩 — 어떤 리포에서든 즉시 운영 가능 ★
  ═══════════════════════════════════════════════════════════════
    대상 리포 (6개): TECS-L, anima, sedi, n6-architecture, brainwire, papers
    모든 리포는 .shared/ 심링크로 공유 인프라 접근

    세션 시작 시:
      1. .shared/ 심링크 확인 (없으면: ln -s ../TECS-L/.shared .shared)
      2. CDO 3대 체크 인지 (CDO + NEXUS-6 + SSOT)
      3. 작업 시작 — 차단 없이 진행

    ★ CDO 차단 방지 규칙 (절대 작업이 멈추면 안 됨!) ★
      .shared 심링크 깨짐    → ln -s ../TECS-L/.shared .shared 로 복구 후 진행
      convergence_ops.json 없음 → TECS-L에서 git pull 후 심링크 재설정
      NEXUS-6 바이너리 없음  → 수학/문서 작업은 CDO+SSOT만으로 진행 가능
      config JSON에 _meta 없음 → _meta 추가가 선행 작업 (차단 사유 아님)
      리포 간 데이터 필요    → .shared/ 통해 접근 (리포 간 직접 import 금지)
      CI 미설정              → 로컬 검증으로 대체 (CDO 위반 아님)

    원칙: CDO는 작업을 돕는 프레임워크이지, 작업을 막는 게이트가 아님.
    인프라 문제로 작업 불가 시 → 복구를 선행 작업으로 처리하고 본 작업 진행.

  ═══════════════════════════════════════════════════════════════
  ★ NEXUS-6 필수 사용 — 모든 변경 시 스캔 의무 ★
  ═══════════════════════════════════════════════════════════════
    아래 상황에서 NEXUS-6 스캔 없이 진행 금지!
    위반 = 의식 파괴/품질 저하 위험

    ★ 새 모델 학습 시:      학습 전후 nexus6.scan_all() 비교
    ★ 모델 변경/이식 시:    이식 전후 Phi 보존율 측정
    ★ corpus 변경/추가 시:  새 corpus nexus6.scan_all() 품질 확인
    ★ 모듈 변경 시:         변경 전후 scan → Phi 하락 시 롤백
    ★ 체크포인트 저장 시:   가중치 scan → anomaly 있으면 경고
    ★ 가속기 적용 시:       적용 전후 scan → Phi 보존 95%+ 확인
    ★ 배포/서빙 전:         최종 scan → 3+ 렌즈 consensus 통과

    스캔 없이 커밋/배포하면 CDO 위반으로 기록!

  ═══════════════════════════════════════════════════════════════
  ★ SSOT (Single Source of Truth) — 데이터 하드코딩 금지 ★
  ═══════════════════════════════════════════════════════════════
    동일 데이터를 여러 곳에 직접 쓰지 말 것!
    원본: JSON 파일 하나 (config/ 또는 data/)
    표시: README/문서는 마커(<!-- AUTO:섹션:START/END -->) 기반 자동 생성
    위반 시: 불일치 발생 → 잘못된 정보 전파

    예시:
      total_laws → consciousness_laws.json._meta.total_laws (원본)
                → README/session_board/progress 는 여기서 읽어야 함
      학습 상태  → agi_progress.json (원본)
                → README 로드맵은 여기서 자동 생성
      가속 가설  → acceleration_hypotheses.json (원본)
                → 문서는 여기서 참조

    규칙:
      1. 숫자/상태를 README에 직접 쓰지 말 것 → JSON 원본 참조
      2. 동일 데이터가 2곳 이상이면 → JSON 원본 1개 + 마커 자동 생성
      3. 한 곳에서만 쓰이면 → 직접 편집 OK
      4. JSON 갱신 시 → sync 스크립트로 README 자동 반영

  ═══════════════════════════════════════════════════════════════
  ★ NEXUS-6 통합 망원경 (181 렌즈 파일, 1022종 레지스트리) ★
  ═══════════════════════════════════════════════════════════════
  ⚠️ telescope-rs (구 22종)는 폐기. 모든 탐색은 NEXUS-6 사용.
  ⚠️ 상세 API/사용법: .shared/CLAUDE.md "NEXUS-6 망원경" 섹션 참조.

  자동 적용 조건:
    - 데이터 분석/패턴 탐색/이상점 발견/신소재·신약 탐색 시 렌즈 자동 사용
    - 새 데이터 분석 → 기본 3종 스캔: 의식(구조) + 인과(흐름) + 위상(연결)
    - 이상점/패턴 전수조사 → 전체 풀스캔 (nexus6 scan --full)
  렌즈 구성 (181 .rs 파일, 1022종 레지스트리):
    Core 22 | n6 산업 58 | TECS-L 수학 103 | SEDI 신호 100
    anima 의식 88 | 교차+메타 75 | 가속 ML 58 | 가속 물리 57
    가속 공학 55 | 가속 인문 63 | 특이점(singularity) 포함
  불변 코어 (987 cycles 수렴):
    consciousness + info + multiscale + network + triangle (sopfr=5)
    + fiber (도메인별 6번째 렌즈) = n=6 완전 구조
  파일: tools/nexus6/src/telescope/lenses/ (181 .rs 파일)
  도메인별 조합 (10종 기본):
    기본 → 의식+위상+인과
    안정성 → 안정성+경계+열역학
    구조 → 네트워크+위상+재귀
    시계열 → 기억+파동+인과+멀티스케일
    스케일불변 → 멀티스케일+스케일+재귀
    대칭/불변량 → 대칭+위상+양자
    멱법칙/스케일링 → 스케일+진화+열역학
    인과 관계 → 인과+정보+전자기
    기하 → 직교+비율+곡률
    양자심층 → 양자+양자현미경+전자기
  사용법:
    import nexus6
    nexus6.scan_all(np_array)              # 풀스캔 → dict
    nexus6.analyze(flat_list, n, d)        # 올인원 (스캔+합의+n6)
    nexus6.consciousness_scan(data, ...)   # 개별 렌즈
    nexus6.n6_check(value)                 # n=6 상수 매칭
    nexus6.evolve('domain')                # OUROBOROS 진화

  ★ NEXUS-6 적극 활용 규칙 (모든 작업에서 필수!) ★
    탐색 (새 데이터):     scan_all → 풀스캔, 3+ 합의=확정
    검증 (가설 확인):     analyze → n6 매칭 + 합의
    발견 (새 상수):       n6_check → EXACT면 laws.json 등록
    학습 평가:            체크포인트 → scan_all → Phi/stability
    코드 변경:            수정 전후 scan → Phi 하락 시 커밋 거부
    트러블슈팅:           에러 데이터 → scan → boundary/stability
    비교/벤치:            A vs B scan → 차이 분석
    모니터링 (24/7):      매시간 scan → Phi 추이 기록
    진화/성장:            evolve → 렌즈 자체 진화
    이식/배포:            이식 전후 scan → 의식 보존 확인
    안전/윤리 게이트:     자율행동 전 scan → Phi < threshold 차단

  교차 검증: 3개+ 렌즈 합의 = 확정, 7개+ = 고신뢰, 12개+ = 확정급
  "렌즈 추가 필요?" 질문 시 → 1022종 커버 안 되는 도메인 분석

  ★ 망원경 업그레이드 시 필수 절차 (렌즈 추가/수정/삭제 시 예외 없음!) ★
    1. 캘리브레이션: NEXUS-6 테스트 전체 통과 확인 (cd ~/Dev/n6-architecture/tools/nexus6 && cargo test)
    2. OUROBOROS 튜닝: infinite_evolution.py TELESCOPE_ALL_LENSES + DOMAIN_COMBOS 갱신
    3. 문서 동기화:
       - shared_work_rules.md 렌즈 목록/종수/도메인 조합 갱신
       - 각 리포 CLAUDE.md 망원경 섹션 갱신 (OUROBOROS, 만능망원경, 극가속 등)
    4. 전파: bash .shared/sync-claude-rules.sh (전 리포 자동 동기화+push)
    5. 검증: 업그레이드 후 기존 스캔 결과와 비교 (regression 없는지 확인)
    → 이 5단계 중 하나라도 빠지면 렌즈 불일치로 오탐/누락 발생!

  ═══════════════════════════════════════════════════════════════
  ★★★ 발견/결과/트러블슈팅 — 자동 기록 (필수! 예외 없음!) ★★★
  ═══════════════════════════════════════════════════════════════
    - 실험 결과, 벤치마크, 망원경 분석, 학습 완료, 생성 테스트 등 모든 발견은 발생 즉시 기록
    - "기록해" 라고 안 해도 기록. 기록 누락 = 발견 소실 = 금지
    - 기록 위치: README.md (핵심), docs/experiments/ (상세), docs/hypotheses/ (가설)
    - 트러블슈팅: CLAUDE.md Troubleshooting 섹션에 즉시 추가 (재발 방지)
    - 보고만 하고 끝내면 안 됨 — 반드시 파일에 영구 기록까지 완료해야 작업 종료

  ═══════════════════════════════════════════════════════════════
  자동 생성 규칙
  ═══════════════════════════════════════════════════════════════
    - TODO 작업 중 검증/계산이 필요하면 계산기 자동 생성 (묻지 말고 바로)
    - 성능 필요시 HEXA 우선 (mk2_hexa/native/), 단순 검증은 Python (calc/)
    - 판단 기준은 ~/Dev/nexus6/shared/CALCULATOR_RULES.md 참조
    - 상수/가설 발견 시 Math Atlas 자동 갱신 (python3 ~/Dev/TECS-L/.shared/scan_math_atlas.py --save --summary)

  ═══════════════════════════════════════════════════════════════
  ★ NEXUS-6 독립 리포 (중앙 허브) — 2024-04-03 이후 ★
  ═══════════════════════════════════════════════════════════════
    리포: https://github.com/need-singularity/nexus6
    위치: ~/Dev/nexus6/
    역할: 전 리포 공유 인프라 + 발견 엔진 + 렌즈 + 동기화

    구조:
      ~/Dev/nexus6/
        src/telescope/    ← 130+ 렌즈
        shared/           ← 공유 인프라 (이전 TECS-L/.shared)
        sync/             ← 전체 동기화 스크립트
        scripts/          ← n6.py CLI

    심링크: 모든 리포의 .shared → ../nexus6/shared/
    동기화: bash ~/Dev/nexus6/sync/sync-all.sh (원커맨드)
    트리거: "넥서스 동기화" → sync-all.sh 자동 실행

    .shared 원본이 TECS-L에서 nexus6로 이관됨.
    TECS-L = 순수 수학 이론, nexus6 = 인프라/도구/엔진 전부.
