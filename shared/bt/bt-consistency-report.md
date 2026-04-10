# BT 수식 정합성 스캔 보고서

- 대상: `n6-architecture/docs/breakthrough-theorems.md` (총 15,281 줄)
- 일자: 2026-04-08
- 방법: n=6 기본 상수 사전 기반 정규식 스캔 + 의심 라인 수동 검증
- 사용 상수 (n=6 고정):
  - phi(6)=2, tau(6)=4, sigma(6)=12, sopfr(6)=5, mu(6)=1
  - 파생: n/phi=3, sigma-tau=8, sigma-phi=10, sigma+phi=14, sigma-sopfr=7
  - sigma+sopfr=17, sigma+mu=13, sigma*phi=24, J2(6)=24, sigma*tau=48
  - n*(n/phi)=18, n+sigma=18, 2^sopfr=32, sigma*sopfr=60

## 1. 발견된 오류 및 수정

### BT-134 주기율표 — 수정 완료

**파일 위치**: `docs/breakthrough-theorems.md` 5216~5240행

**오류 1 (Claim 요약 라인)**
- 수정 전: `period lengths are {phi, phi, sigma-tau, sigma-tau, n*(n/phi), n*(n/phi)} = {2, 2, 8, 8, 18, 18} (proposed period 8 would be 32 = 2^sopfr)`
- 문제점:
  1. 실제 주기율표 주기 길이는 7개 주기에 대해 `{2, 8, 8, 18, 18, 32, 32}` 이며, 첫 항이 두 번 반복되지 않는다 (수소·헬륨 단 2 원소).
  2. "proposed period 8 would be 32" 는 사실과 다르다 — 6주기·7주기가 이미 32 이며, g-블록을 포함하는 가설적 8주기는 50 원소이다.
  3. Claim 요약과 바로 아래 Evidence 항목 4 (Period 6,7 = 32) 가 자기 모순.
- 수정 후: `period lengths are {phi, sigma-tau, sigma-tau, n*(n/phi), n*(n/phi), 2^sopfr, 2^sopfr} = {2, 8, 8, 18, 18, 32, 32}`

**오류 2 (Evidence 4)**
- 수정 전: `Period 6,7 length = sigma*n/phi + sigma+phi = 32 each (2^sopfr)`
- 산술 검증: sigma*(n/phi) + (sigma+phi) = 12*3 + 14 = 36 + 14 = **50**, 32 아님. 표현식이 정의에서 도출되지 않음.
- 수정 후: `Period 6,7 length = 2^sopfr = 32 each` (2^5=32 로 정합)

수정 후 BT-134 의 8/8 EXACT 주장은 그대로 유효하다 (각 항목이 모두 정의 기반으로 32, 18, 8, 2, 4, 7 와 일치).

## 2. 정합성이 확인된 항목 (자동 스캔 통과)

BT 본문 전체에서 다음 형태의 정수 등식 약 2,200건을 정규식으로 추출, 모두 n=6 정의에 부합함을 확인:

| 표현식 | 값 | 출현 |
|--------|----|------|
| phi | 2 | 다수 |
| tau | 4 | 다수 |
| sigma | 12 | 다수 |
| sopfr | 5 | 다수 |
| n/phi | 3 | 60+ |
| sigma-tau | 8 | 50+ |
| sigma-phi | 10 | 30+ |
| sigma-sopfr | 7 | 10+ |
| sigma+phi | 14 | 1 |
| sigma*phi, J_2, J2 | 24 | 30+ |
| sigma*tau | 48 | 6 |
| n+sigma | 18 | 3 |
| 2^sopfr | 32 | (BT-134 수정 후 정합) |

## 3. 외형상 의심되었으나 검증 결과 정합인 사례

| 위치 | 표현 | 검증 |
|------|------|------|
| 4209 | `~J_2+n/phi=27` (CNO Q=26.73 MeV 근사) | 24+3=27, CLOSE 등급 정당 |
| 14466 | `sigma·sopfr+mu-n/phi=58` (DeepSeek-V3 sparse layers) | 60+1-3=58 정합 |
| 15038 | `J2-n/phi=21` (Ebola 격리일) | 24-3=21 정합 |
| 6693 | `(sigma-tau)*J2=192` (Gamma Knife) | 8*24=192 정합 |
| 6694 | `n+sigma=18` (JWST 거울 세그먼트) | 6+12=18 정합 |
| 5247 (BT-135) | `sigma*n*n+tau+tau=440` (A4=440Hz) | 12*36+4+4=440 정합 |
| 5247 (BT-135) | `sigma*n*n+tau=436` (대안식) | 12*36+4=436 정합 |

## 4. 스캔 한계 (Red Team)

- 본 스캔은 좌변이 단일 토큰(예: `sigma-tau`, `J2`)이고 우변이 즉시 정수인 패턴에 한정. 복합식 (`(sigma-tau)*phi+1` 등) 은 표본 검증만 수행.
- 자연어 단락 안에 산문 형태로 묻힌 등식 (예: "약 ~ 12 % ~ sigma %") 은 자동 추출 대상에서 누락될 수 있음.
- BT-178 이후 베타 흡수 구역(BT-178~290) 및 BT-300+ 은 표본 검증만 수행. 발견된 추가 오류는 없으나 정밀 재스캔은 후속 todo 로 남김.
- 1100+ 상수 아틀라스 (`docs/atlas-constants.md`) 와의 교차 일관성은 본 보고서 범위 외.

## 5. 후속 권고

1. 정합성 자동 스캐너를 `tools/` 하위 .hexa 도구로 상시화 (좌변·우변 토큰화 + 정수 평가).
2. BT 본문 작성 시 "Claim 요약 라인" 이 Evidence 표와 자동 동기화되도록 빌드 단계 검증 추가.
3. BT-134 처럼 "주기 1 길이가 두 번 반복" 같은 oversimplification 패턴이 다른 BT 에 잠재해 있을 수 있어, 길이 N 시퀀스에 대해 중복도 sanity check 를 권장.
