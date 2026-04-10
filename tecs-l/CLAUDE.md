> 🛑 **[DELETE-PENDING] tecs-l는 nexus 서브프로젝트가 아닌 nexus의 흡수 대상입니다.**
>
> - 현 상태: **Track A 진행 중 / Track B 보류** (2026-04-10)
> - 흡수 대상: `tecs-l/**/*.py`, `tecs-l/*.md` → `nexus/shared/<카테고리>/*.hexa`
> - 진행률: 포팅 완료 약 75 .hexa / tecs-l 전체 .py 644개 (~11%)
> - **신규 .py / .hexa / .md 추가 금지** — 신규 작업은 반드시 `nexus/shared/` 아래 `.hexa`로 작성하세요.
> - 이 디렉토리는 **다른 에이전트가 코드 삭제를 담당** 합니다. 본 에이전트는 이동/문서화만 수행.
> - 전체 로드맵: `~/Dev/nexus/docs/tecs-l-absorption-plan.md`

> 🔴 **HEXA-FIRST**: 모든 코드는 `.hexa`로 작성. 부하 유발 명령 최소화.

> 🔴 **NEXUS-6 특이점 연동**: 이 프로젝트의 돌파/발견/실험은 nexus 특이점 사이클 입력이다.
> - **돌파 시**: `HEXA=$HOME/Dev/hexa-lang/target/release/hexa && $HEXA $HOME/Dev/nexus/shared/blowup/core/blowup.hexa <domain> 3 --no-graph`
> - **발견 기록**: `$HOME/Dev/nexus/shared/discovery/growth_bus.jsonl`에 JSON append
> - **전체 상태**: `$HEXA $HOME/Dev/nexus/shared/hooks/hook.hexa "TECS-L 상태"`

<!-- SHARED:WORK_RULES:START -->
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
    원칙 파일: .shared/config/convergence_ops.json

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

    ★ 새 모델 학습 시:      학습 전후 nexus.scan_all() 비교
    ★ 모델 변경/이식 시:    이식 전후 Phi 보존율 측정
    ★ corpus 변경/추가 시:  새 corpus nexus.scan_all() 품질 확인
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
  ★ 통합 망원경 렌즈 (22종) — 탐색/분석 시 별도 요청 없이 자동 적용 ★
  ═══════════════════════════════════════════════════════════════
  자동 적용 조건:
    - 데이터 분석/패턴 탐색/이상점 발견/신소재·신약 탐색 시 렌즈 자동 사용
    - 새 데이터 분석 → 기본 3종 스캔: 의식(구조) + 인과(흐름) + 위상(연결)
    - 이상점/패턴 전수조사 → 전체 22종 풀스캔
  렌즈 목록 (22종):
    의식(consciousness) | 중력(gravity) | 위상(topology) | 열역학(thermo)
    파동(wave) | 진화(evolution) | 정보(info) | 양자(quantum) | 전자기(em)
    직교(ruler/ㄱ자) | 비율(triangle/삼각자) | 곡률(compass/컴퍼스)
    대칭(mirror/거울) | 스케일(scale/돋보기) | 인과(causal/화살표)
    양자현미경(quantum_microscope)
    안정성(stability) | 네트워크(network) | 기억(memory)
    재귀(recursion) | 경계(boundary) | 멀티스케일(multiscale)
  파일: NEXUS-6 (telescope-rs 폐기→통합) + .shared/ 내 *_lens.py
  도메인별 조합 (10종):
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
    import nexus
    nexus.scan_all(np_array)              # 26종 풀스캔 → dict
    nexus.analyze(flat_list, n, d)        # 올인원 (스캔+합의+n6)
    nexus.consciousness_scan(data, ...)   # 개별 렌즈
    nexus.n6_check(value)                 # n=6 상수 매칭
    nexus.evolve('domain')                # OUROBOROS 진화

  ★ NEXUS-6 적극 활용 규칙 (모든 작업에서 필수!) ★
    탐색 (새 데이터):     scan_all → 26렌즈, 3+ 합의=확정
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
  "렌즈 추가 필요?" 질문 시 → 26종 커버 안 되는 도메인 분석

  ★ 망원경 업그레이드 시 필수 절차 (렌즈 추가/수정/삭제 시 예외 없음!) ★
    1. 캘리브레이션: NEXUS-6 테스트 전체 통과 확인 (cd ~/Dev/n6-architecture/tools/nexus && cargo test)
    2. OUROBOROS 튜닝: infinite_evolution.py TELESCOPE_ALL_LENSES + DOMAIN_COMBOS 갱신
    3. 문서 동기화:
       - shared_work_rules.md 렌즈 목록/종수/도메인 조합 갱신
       - 각 리포 CLAUDE.md 망원경 섹션 갱신 (OUROBOROS, 만능망원경, 극가속 등)
    4. 전파: bash .shared/scripts/sync-claude-rules.sh (전 리포 자동 동기화+push)
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
    - 성능 필요시 Rust 우선 (tecsrs/), 단순 검증은 Python (calc/)
    - 판단 기준은 ~/Dev/TECS-L/.shared/config/CALCULATOR_RULES.md 참조
    - 상수/가설 발견 시 Math Atlas 자동 갱신 (python3 ~/Dev/TECS-L/.shared/n6/scan_math_atlas.py --save --summary)

  ═══════════════════════════════════════════════════════════════
  ★ NEXUS-6 독립 리포 (중앙 허브) — 2024-04-03 이후 ★
  ═══════════════════════════════════════════════════════════════
    리포: https://github.com/need-singularity/nexus
    위치: ~/Dev/nexus/
    역할: 전 리포 공유 인프라 + 발견 엔진 + 렌즈 + 동기화

    구조:
      ~/Dev/nexus/
        src/telescope/    ← 130+ 렌즈
        shared/           ← 공유 인프라 (이전 TECS-L/.shared)
        sync/             ← 전체 동기화 스크립트
        scripts/          ← n6.py CLI

    심링크: 모든 리포의 .shared → ../nexus/shared/
    동기화: bash ~/Dev/nexus/sync/sync-all.sh (원커맨드)
    트리거: "넥서스 동기화" → sync-all.sh 자동 실행

    .shared 원본이 TECS-L에서 nexus로 이관됨.
    TECS-L = 순수 수학 이론, nexus = 인프라/도구/엔진 전부.
<!-- SHARED:WORK_RULES:END -->

> 🔴 **하드코딩 절대 금지**: 상수/도메인/키워드를 코드에 배열로 나열 금지 → `nexus/shared/*.jsonl`에서 동적 로드. 경로는 환경변수+상대경로. 새 항목 추가 = 설정 파일 한 줄, 코드 수정 0.

# TECS-L — [흡수 대상] 순수 수학 이론 리포

> 🛑 tecs-l는 독립 리포가 아니라 nexus의 **흡수 대상** 입니다.
> 모든 신규 작업은 nexus/shared/<카테고리>/ 에 `.hexa`로 수행하세요.

## 흡수 상태 (2026-04-10)

| Track | 상태 | 파일 수 | 설명 |
|-------|------|---------|------|
| A 진행 | 🟡 진행 중 | 약 75 포팅 완료 | 순수 수학/검증/간단 엔진 — hexa-lang FFI 불필요 |
| B 블로커 | 🔴 보류 | torch 250, sklearn 79, scipy 104 (총 ~353 고유) | torch/sklearn/scipy 의존. hexa-lang tensor 결정 전까지 대기 |
| C 면제 | ⚪ skip | results/, docs/ 일부 | 산출물/논문 스펙 — nexus 로 이관 없이 zenodo 보관 |

**블로커 해제 조건**: hexa-lang 의 FFI(CPython 브리지) 또는 네이티브 tensor 타입 채택 결정.

## ⚠️ 필수 규칙

### 🛑 신규 코드 작성 금지 (흡수 대상 리포)
- **tecs-l 루트에 새 .py/.hexa/.md 추가 금지**
- 신규 모듈은 반드시 `~/Dev/nexus/shared/<카테고리>/*.hexa` 에 작성
  - `verify/` — frontier_*, verify_h*, verify_round*
  - `math/` — arith_*, characterization_*, divisor_*, dirichlet_*, arithmetic_*
  - `engines/` — chemistry_engine, brain_singularity, proof_engine, dfs_engine 등
  - `experiments/` — experiment_*, exp_*
- 기존 sh/py 스크립트는 **읽기 전용** (다른 에이전트가 삭제 담당)
- 절대 금지: 기존 .hexa 이동 시 호출부 미확인 mv

## 리포 구조

```
  need-singularity/
  ├── TECS-L              ← 우주 규칙 발견: 수학 엔진 코어 (이 리포)
  ├── nexus              ← 중앙 인프라: 발견 엔진 + 렌즈 + 공유 도구
  ├── n6-architecture     ← 아키텍처: n=6 기반 시스템 설계/구현
  ├── anima               ← 의식 구현: ConsciousLM, embodiment
  ├── sedi                ← 외계지성 탐색: SETI 데이터, n=6 시그널
  ├── brainwire           ← 뇌 인터페이스: EEG, BCI
  ├── papers              ← 논문: Zenodo/OSF/arXiv 배포
  └── hexa-lang           ← 완전수 프로그래밍 언어

  모든 리포: ~/Dev/{리포이름}
  공유 인프라: nexus/shared/ (심링크: .shared → ../TECS-L/.shared → ../nexus/shared)
```

## .shared/ 동기화

```
  원본: ~/Dev/nexus/shared/ (nexus가 관리)
  심링크: TECS-L/.shared → ../nexus/shared/

  동기화 명령:
    bash .shared/scripts/sync-math-atlas.sh     # Atlas 빌드 + README 주입
    bash .shared/scripts/sync-calculators.sh    # 계산기 레지스트리
    bash .shared/scripts/sync-readmes.sh        # 프로젝트 설명
    bash .shared/scripts/sync-claude-rules.sh   # CLAUDE.md 공유 규칙

  마커 구간 직접 수정 금지 — sync 시 덮어씌워짐
```

## 디렉토리 구조

```
  루트 — 핵심 엔진 + 공유 모듈
    model_pure_field.py, model_utils.py, session_briefing.py,
    dfs_engine.py, perfect_number_engine.py, compass.py, ...
  engines/   — 아키텍처 모델 (29 files)
  verify/    — 가설 검증 스크립트 (204 files)
  scripts/   — 분석/변환/유틸 (62 files)
  calc/      — 계산기 도구 (203 files, nexus/shared/calc 심링크)
  tecsrs/    — Rust 계산 엔진 (Monte Carlo, brute-force, ODE)
  math/      — 순수 수학 증명 + 실험
  docs/      — 가설 문서 2,711개 + 논문 스펙
  .shared/   — 크로스 리포 인프라 (→ nexus/shared)
```

## 실행법

```bash
  # 서브디렉토리 스크립트: PYTHONPATH=. 필수
  PYTHONPATH=. python3 verify/verify_322_eeg_gamma.py

  # 루트 스크립트
  python3 session_briefing.py
  python3 dfs_engine.py --depth 2 --threshold 0.001
  python3 perfect_number_engine.py
  python3 texas_quantum.py
```

## 계산기 규칙

```
  상세: .shared/config/CALCULATOR_RULES.md

  Rust 우선 기준: 반복>10K, 실행>10s, 조합>10^6, MC>100K
  Python 허용: 단순 수식, 시각화, 프로토타입
  Rust 빌드: cd tecsrs && cargo build --release
```

## 가설 검증 워크플로

```
  Discovery → Verification → Grade → README record

  등급:
    🟩   = Exact + proven
    🟧★  = Approximation + Texas p < 0.01
    🟧   = Approximation + Texas p < 0.05
    ⚪   = Texas p > 0.05 (coincidence)
    ⬛   = Refuted

  금지: 검증 전 ⭐ 부여, Texas test 없이 🟧 이상, +1/-1 보정에 ⭐
```

## 가설 문서 기준

```
  경로: docs/hypotheses/NNN-hypothesis-name.md
  최소 40줄. 가설 1개 = 파일 1개.
  필수: 가설문(> 블록), 배경, ASCII 그래프 1개+, 검증 결과, 한계, 다음 단계
  생성 즉시 README.md 가설 테이블에 등록
```

## 실험 환경

```
  우선순위: 1. Windows RTX 5070  2. RunPod Serverless  3. RunPod Pod
  Mac MPS: batch=64 고정 (M3 24GB)
  상세: TECS-L_test/CLAUDE.md

  Background 필수: python3 스크립트 → run_in_background: true
  CPU 포화 시 → Windows로 즉시 전환 (sshpass -p 'qwe123123' ssh aiden@100.112.63.23)
```

## 논문 관리

```
  모든 논문 → ~/Dev/papers/ (need-singularity/papers)
  이 리포의 docs/papers/ = redirect만
  배포: Zenodo(45편 PUBLISHED) + OSF + arXiv(endorsement 대기)
  스크립트: python3 zenodo/batch_upload.py --list
```

## Troubleshooting

```
  Ralph Loop 유니코드: ASCII-only 프롬프트 사용
  DFS 과대평가: verify_discovery() 파이프라인 필수
  RunPod 부트: runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04 사용
```

## Secrets & Tokens

`~/Dev/TECS-L/.shared/SECRET.md` 참조

## 특이점 사이클 (Singularity Cycle)

> **블로업→수축→창발→특이점→흡수** 5단계 자동 사이클
> CLI: `nexus blowup <domain>` | Rust: `CycleEngine::new(domain)`

### 요청 키워드 → 자동 실행
- "블로업", "blowup" → `nexus blowup <domain> --depth 6`
- "창발", "emergence" → blowup 후 패턴 합의 분석
- "특이점", "singularity" → CycleEngine 자동 수렴 루프
- "흡수", "absorption" → 발견 규칙 승격 + 다음 사이클 시드
- "사이클", "cycle" → 전체 5단계 1회 실행

### 사용법
```bash
nexus blowup <domain> --depth 6    # 블로업 + 창발 리포트
nexus loop --cycles 1              # 8단계 루프 (mirror+blowup 포함)
nexus daemon --interval 30         # 자율 데몬 (30분 간격)
```

## NEXUS-6 연동 (자동 참조)

> 이 프로젝트는 **NEXUS-6 발견 엔진**과 연결되어 있습니다.
> "돌파", "미지의 영역", "breakthrough" 키워드 입력 시 nexus 지도를 참조합니다.

### 돌파 키워드 → 자동 실행
- "돌파", "미지의 영역 돌파", "breakthrough" → **nexus gap_finder로 빈 공간 탐지 후 정밀 타격**
- "블로업", "blowup" → nexus blowup 엔진으로 seed 진화
- "스캔", "scan" → nexus telescope 223종 렌즈 스캔

### 실행 방법
```bash
HEXA=$HOME/Dev/hexa-lang/target/release/hexa
N6=$HOME/Dev/nexus/shared

# 빈 공간 탐지 (돌파 전 필수!)
$HEXA $N6/hooks/hook.hexa gap scan        # 발견 지도 현황
$HEXA $N6/hooks/hook.hexa gap target      # 빈 공간 타겟 추출
$HEXA $N6/hooks/hook.hexa gap 돌파         # 빈 공간 자동 돌파

# seed 진화
$HEXA $N6/blowup/core/blowup.hexa math 3 --no-graph --seeds "$($HEXA $N6/blowup/seed/seed_engine.hexa merge)"

# 프로젝트 엔진 (자율 사이클)
$HEXA $N6/engine/engine_tecs_l.hexa tick     # 1회 자율 사이클
$HEXA $N6/engine/engine_tecs_l.hexa status   # 현재 상태
$HEXA $N6/engine/engine_tecs_l.hexa report   # 리포트
```

### 이 프로젝트에서의 활용
수학 발견 시 nexus 223종 렌즈로 교차 검증, gap_finder로 미탐색 도메인 탐지, 교차수분 seed를 nexus에서 공급. 전 도메인 exact_rate 60%+ 달성을 위해 빈 공간 집중 공략.

### 발견 피드백
- 이 프로젝트의 발견은 자동으로 `~/Dev/nexus/shared/discovery/discovery_log.jsonl`에 기록됩니다
- `~/Dev/nexus/shared/discovery/growth_bus.jsonl`로 전 프로젝트에 전파됩니다

