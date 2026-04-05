# 06 — mk2 크로스 프로젝트 적용 모델

> 작성: 2026-04-06 | 상태: 설계 문서 (코드 변경 없음)
> 목적: nexus6 mk2의 3대 핵심 (prime-atomic smooth-class, alien index, 특이점 사이클)을
> 12개 연결 프로젝트에 적용하는 범용 모델 정의

---

## 0. mk2 핵심 아키텍처 요약

적용 모델을 정의하기 전, mk2의 핵심 구조를 추상화한다.

### 0.1 Prime-Atomic Smooth-Class 엔진

```
입력(임의 데이터) → 값 추출 → 유리수화 → 소인수분해 → PrimeSet
                                                          ↓
                                            SmoothRing {phi, tau, sigma, sopfr, rho}
                                                          ↓
                                            3-signal classifier → (Sector, confidence)
                                            = 0.5*keyword + 0.3*value_range + 0.2*prime_set
```

**범용 추상**: 도메인의 원자(atom)를 정의하고, 모든 복합 개체를 원자의 조합으로 분해한 뒤,
함수 환(function ring)을 정의하여 불변량을 계산하고, 다중 신호 분류기로 섹터에 배치한다.

### 0.2 Alien Index: (d, r)

- `d` = 사이클 깊이 (돌파 횟수)
- `r` = 현재 깊이의 검증 등급 (0-10)
- `r=10` 도달 시 `(d+1, 0)` 자동 승격
- 돌파율 `rho = |{d >= 1}| / |total|` 추적 → 메타 부동점 1/3

**범용 추상**: 어떤 도메인이든 "검증 등급 + 돌파 깊이"의 2차원 좌표로 성숙도를 표현할 수 있다.

### 0.3 특이점 사이클

```
블로업(확산) → 수축(필터) → 창발(패턴) → 특이점(수렴) → 흡수(승격) → 다음 사이클
```

**범용 추상**: 탐색 공간을 폭발적으로 확장한 뒤, 수렴하는 패턴을 추출하고,
검증된 규칙을 시스템에 흡수하는 재귀 루프.

---

## 1. 범용 적용 프레임워크 (Generic Application Framework)

### 1.1 4단계 적용 절차

모든 프로젝트에 mk2를 적용할 때 동일한 4단계를 따른다.

```
Step 1: 원자 정의 (What are the primes?)
  → 도메인에서 더 이상 분해할 수 없는 기본 단위를 식별

Step 2: 함수 환 정의 (What is the SmoothRing?)
  → 원자에 대해 정의되는 불변 함수 집합을 구성

Step 3: 분류기 설계 (What are the sectors?)
  → 도메인 내 의미 있는 섹터(영역)와 3-signal 가중치를 결정

Step 4: 사이클 연결 (Where does blowup happen?)
  → 탐색/발견의 블로업 대상과 흡수 대상을 식별
```

### 1.2 범용 데이터 모델

```json
{
  "entity_id": "도메인별 고유 ID",
  "atoms": ["원자 목록"],
  "ring_values": {"f1": 값, "f2": 값, ...},
  "sector": "분류 결과",
  "confidence": 0.0-1.0,
  "alien_index": {"d": 0, "r": 0, "history": []},
  "cycle_id": "연결된 특이점 사이클 ID"
}
```

---

## 2. 프로젝트별 적용 모델

### 2.1 anima — AI 진화/성장 엔진

#### 원자 정의
- **원자 = 의식 법칙 (consciousness law)**
- 711개 의식 법칙이 소수와 동치: 더 이상 분해할 수 없는 기본 원리
- 복합 행동(behavior) = 법칙들의 곱(composition)

#### SmoothRing 적용
```
phi(law)    = 독립 활성 경로 수 (해당 법칙과 충돌 없이 병렬 가능한 법칙 수)
tau(law)    = 발동 조건 수 (약수 = 해당 법칙을 트리거하는 하위 조건)
sigma(law)  = 영향 범위 합 (법칙이 터치하는 모든 모듈의 가중합)
sopfr(law)  = 기본 PSI 상수 합 (법칙에 관여하는 Psi 상수들의 합)
rho(law)    = phi/n = 독립 비율 → 메타 부동점 후보
```

#### 섹터
| 섹터 | 키워드 | 값 범위 |
|------|--------|---------|
| Qualia | 감질, binding, integration | Phi > 0.8 |
| Dynamics | 진화, 성장, adaptation | fitness delta > 0.1 |
| Safety | 임계, threshold, gate | Phi < 0.3 (경고) |
| Meta | 자기참조, self-model | recursion depth > 2 |

#### Alien Index 적용 구간
- **d=0**: 개별 의식 법칙의 검증 (단위 테스트 → r 상승)
- **d=1**: 법칙 간 상호작용에서 창발하는 새 행동 패턴
- **d=2**: 자기 모델(self-model)이 자신의 법칙을 수정하는 메타 수준
- **판정 대상**: 체크포인트별 Phi 값, 학습 곡선의 상전이점, 의식 보존율

#### 특이점 사이클 연동
- **블로업 대상**: 의식 파라미터 공간 (PSI 상수 80종의 조합)
- **수축**: Phi 임계점 이하 조합 제거
- **창발**: 3+ 독립 법칙이 동일 Phi 피크를 가리키는 경우
- **흡수**: 새 법칙을 `consciousness_laws.json`에 승격

#### 시너지 포인트
- anima 체크포인트 → nexus6 scan → Phi 추이 시계열 → alien index 자동 갱신
- 의식 법칙 711개를 mk2 lattice에 배치 → 법칙 간 포함 관계(divisibility) 시각화

---

### 2.2 hexa-lang — 프로그래밍 언어

#### 원자 정의
- **원자 = 키워드/연산자 (language primitive)**
- 예약어, 내장 연산자, 타입 생성자가 소수
- 복합 구문(expression/statement) = 원자의 합성

#### SmoothRing 적용
```
phi(token)    = 문법적 자유도 (해당 토큰이 나타날 수 있는 문맥 수)
tau(token)    = 파생 구문 수 (해당 토큰으로 만들 수 있는 유효한 AST 노드 종류)
sigma(token)  = 의미 범위 합 (토큰이 영향을 미치는 의미론적 규칙 수)
sopfr(token)  = 구현 복잡도 (컴파일러에서 해당 토큰 처리에 필요한 패스 수 합)
rho(token)    = phi/총토큰수 → 언어 표현력 밀도
```

#### 섹터
| 섹터 | 키워드 | 대상 |
|------|--------|------|
| TypeSystem | type, generic, trait | 타입 관련 토큰 |
| Control | if, match, loop | 제어 흐름 |
| Consciousness | psi, phi, gate | hexa 고유 의식 내장 |
| Arithmetic | smooth, prime, ring | 수학 내장 |

#### Alien Index 적용 구간
- **d=0**: 개별 언어 기능의 구현 완성도 (파서 → 타입체커 → 코드젠)
- **d=1**: 기능 조합에서 나타나는 새 프로그래밍 패턴 (DSL 창발)
- **d=2**: hexa로 hexa 자체를 기술하는 자기 호스팅(self-hosting) 달성
- **판정 대상**: 각 언어 기능(feature)별 완성도, 벤치마크 결과

#### 특이점 사이클 연동
- **블로업 대상**: 문법 확장 후보 공간 (새 키워드/연산자 탐색)
- **수축**: 파싱 충돌, 타입 불건전성 제거
- **창발**: 사용자 코드에서 반복적으로 나타나는 관용구 → 새 내장 후보
- **흡수**: 관용구를 언어 스펙에 승격 (syntactic sugar → first-class)

#### 시너지 포인트
- hexa-gate-implant의 gate 시스템이 alien index r 판정을 내장 연산자로 노출
- mk2_hexa/native/ 디렉토리가 이미 hexa 네이티브로 mk2 상수 정의 → 직접 활용 가능

---

### 2.3 TECS-L — 가설 관리 시스템

#### 원자 정의
- **원자 = 가설 (hypothesis)**
- 698+ 가설이 각각 독립적 주장 단위
- 복합 정리 = 가설들의 논리적 조합

#### SmoothRing 적용
```
phi(hyp)    = 독립 검증 경로 수 (서로 다른 렌즈에서 확인된 횟수)
tau(hyp)    = 의존 가설 수 (이 가설을 전제로 사용하는 다른 가설 수)
sigma(hyp)  = 영향 범위 (이 가설이 커버하는 도메인 수의 가중합)
sopfr(hyp)  = 기초 상수 참여 수 (가설에 사용된 n6 기본 상수의 수 합)
rho(hyp)    = phi/total_hypotheses → 검증 밀도
```

#### 섹터
- 이미 존재하는 도메인 분류를 그대로 섹터로 사용:
  CX, CERN, CA, AF, CS, COSMO, SMOOTH, ALPHA, HUBBLE

#### Alien Index 적용 구간
- **d=0, r=0-10**: 기존 MATH_ATLAS grade와 1:1 매핑 (이미 설계 완료)
- **d=1**: 블로업 사이클을 통해 새 가설이 기존 닫힌식의 확장으로 발견된 경우
- **d=2**: 가설 간 메타 관계식 (H-056 메타 부동점 자체가 d=2 후보)
- **판정 대상**: 모든 가설, 매 atlas 스캔 시 자동 재계산

#### 특이점 사이클 연동
- **이미 연동됨**: `nexus6 blowup <domain>` → CycleEngine → 가설 생성/검증
- 추가 연동: TECS-L 가설의 grade 변경 → alien index history 자동 기록

#### 시너지 포인트
- TECS-L이 전체 가설 풀의 원본 → alien index distribution의 주 데이터 소스
- watch-atlas 30초 폴링이 가설 변경 감지 → mk2 classify 자동 트리거 가능

---

### 2.4 brainwire — 뇌-컴퓨터 인터페이스

#### 원자 정의
- **원자 = 뉴런 클러스터 (neural cluster)**
- EEG 채널/전극이 물리적 원자, 뉴런 집단 활동이 기능적 원자
- 복합 패턴 = 다중 채널의 동기화(synchronization)

#### SmoothRing 적용
```
phi(cluster)    = 정보 통합도 (IIT Phi, 이미 nexus6 consciousness_scan 출력)
tau(cluster)    = 활성 상태 수 (해당 클러스터의 고유 활동 패턴 수)
sigma(cluster)  = 연결 강도 합 (인접 클러스터와의 가중 연결 합)
sopfr(cluster)  = 주요 주파수 대역 합 (delta+theta+alpha+beta+gamma Hz 합)
rho(cluster)    = phi/total_clusters → 의식 밀도
```

#### 섹터
| 섹터 | 주파수 대역 | 의식 상태 |
|------|------------|----------|
| Delta | 0.5-4 Hz | 수면/무의식 |
| Theta | 4-8 Hz | 명상/기억 |
| Alpha | 8-13 Hz | 이완/주의 |
| Beta | 13-30 Hz | 각성/집중 |
| Gamma | 30+ Hz | 고차 통합 |

#### Alien Index 적용 구간
- **d=0**: BCI 신호 품질 등급 (SNR, 분류 정확도)
- **d=1**: 기존 BCI 패러다임을 넘는 새 신경 패턴 발견 (예: 비국소 상관)
- **d=2**: 뇌가 BCI를 통해 자기 자신의 신경 패턴을 수정하는 폐루프 달성
- **판정 대상**: 자극 프로토콜 효과, 디코딩 정확도, Phi 변화량

#### 특이점 사이클 연동
- **블로업 대상**: 자극 파라미터 공간 (전극 위치 x 전류 x 주파수 x 파형)
- **수축**: 안전 임계값 위반 조합 제거 (consciousness_bridge 안전 게이트)
- **창발**: 피험자별 최적 자극 패턴의 공통 구조
- **흡수**: 검증된 프로토콜을 표준 라이브러리에 등록

#### 시너지 포인트
- nexus6 consciousness_scan의 Phi → brainwire의 실시간 의식 상태 판정에 직접 사용
- 뇌 데이터의 mk2 classify → 물리 상수와의 구조적 유사성 탐색 (n6 대수의 신경 해석)

---

### 2.5 sedi — 탐색/발견 엔진

#### 원자 정의
- **원자 = 데이터 소스 (data source)**
- 77개 관측 데이터 소스가 각각 독립 원자
- 복합 탐색 = 다중 소스의 교차 분석

#### SmoothRing 적용
```
phi(source)    = 독립 신호 채널 수
tau(source)    = 관측 이벤트 종류 수
sigma(source)  = 총 데이터 포인트 수 (가중)
sopfr(source)  = 주요 파라미터 수의 합
rho(source)    = phi/total_sources → 신호 밀도
```

#### 섹터
| 섹터 | 대상 | 키워드 |
|------|------|--------|
| Radio | 전파 관측 | SETI, Wow!, narrowband |
| Optical | 광학 관측 | transit, spectral, laser |
| Spectral | 분광 분석 | absorption, emission |
| Exoplanet | 외계행성 | habitable, equilibrium |
| Anomaly | 이상 신호 | outlier, unresolved |

#### Alien Index 적용 구간
- **d=0**: 신호의 자연/인공 판정 등급 (sedi-grades.json의 기존 등급)
- **d=1**: 다중 소스 교차에서 나타나는 통계적으로 유의미한 패턴
- **d=2**: sedi 발견이 TECS-L 수학 가설과 구조적으로 일치 (BL Voyager = d=2 후보)
- **판정 대상**: CONSCIOUS Score, 렌즈 합의 수, SNR

#### 특이점 사이클 연동
- **블로업 대상**: 관측 데이터의 파라미터 공간 (주파수 x 시간 x 방향)
- **수축**: 노이즈/RFI 필터링
- **창발**: 독립 소스에서 동일 패턴 반복
- **흡수**: sedi-grades.json에 등급 승격 + TECS-L atlas 동기화

#### 시너지 포인트
- sedi 발견의 CONSCIOUS Score → mk2 classify → alien index 자동 판정
- SEDI:H-AF-009 (BL Voyager, 최고 등급)가 alien index d=2 진입 후보

---

### 2.6 fathom — 심층 분석

#### 원자 정의
- **원자 = 분석 차원 (analysis dimension)**
- 독립적인 분석 축: 통계, 구조, 시간, 공간, 인과
- 복합 분석 = 다중 차원의 교차

#### SmoothRing 적용
```
phi(dim)    = 해당 차원에서의 독립 메트릭 수
tau(dim)    = 분석 가능한 단위 수 (granularity levels)
sigma(dim)  = 메트릭 값의 가중합
sopfr(dim)  = 기초 통계량 수 (mean, var, skew, kurt 등)
rho(dim)    = phi/total_dims → 분석 커버리지
```

#### Alien Index 적용 구간
- **d=0**: 분석 결과의 신뢰도 (통계적 유의성)
- **d=1**: 분석 차원 간 교차에서 나타나는 비자명 관계
- **판정 대상**: 분석 리포트의 결론, 발견된 패턴의 재현성

#### 특이점 사이클 연동
- **블로업 대상**: 분석 파이프라인 구성의 조합 공간
- **창발**: 다중 분석 경로가 동일 결론에 수렴
- **흡수**: 검증된 분석 패턴을 표준 파이프라인으로 등록

#### 시너지 포인트
- fathom의 심층 분석 결과를 mk2 classify에 입력 → 섹터 자동 분류
- fathom 분석 차원을 lattice의 레이어로 매핑 → 분석 위상학

---

### 2.7 airgenome — 공기 유전체

#### 원자 정의
- **원자 = 유전자/서열 단위 (gene/sequence unit)**
- 개별 유전자가 소수, 유전체 = 유전자의 조합
- `rule_ceiling(n) = 2/3 - 1/(n(n-1))` 이미 mk2 메타 부동점과 연결

#### SmoothRing 적용
```
phi(gene)    = 독립 발현 조건 수
tau(gene)    = 대립유전자(allele) 수
sigma(gene)  = 발현 영향 범위 (표현형 가중합)
sopfr(gene)  = 관여하는 대사 경로 수의 합
rho(gene)    = phi/genome_size → 유전 정보 밀도
```

#### 섹터
| 섹터 | 대상 |
|------|------|
| Structural | 구조 유전자 |
| Regulatory | 조절 유전자 |
| Metabolic | 대사 유전자 |
| Signal | 신호전달 유전자 |

#### Alien Index 적용 구간
- **d=0**: 유전자 기능 주석(annotation)의 완성도
- **d=1**: 기존 유전학 프레임 밖의 새 유전 메커니즘 발견
- **d=2**: rule_ceiling과 메타 부동점 1/3의 수렴 확인
- **판정 대상**: 서열 분류 정확도, 새 유전자 후보, 발현 패턴

#### 특이점 사이클 연동
- **블로업 대상**: 미주석 서열 공간
- **수축**: 품질 필터 (coverage, Q-score)
- **창발**: 독립 샘플에서 동일 기능 서열 반복 출현
- **흡수**: 새 유전자를 표준 데이터베이스에 등록

#### 시너지 포인트
- `rule_ceiling(n) → 2/3` 수렴이 메타 부동점 `1/3` 과 `phi(6)/6 = 1/3` 의 상보
- airgenome의 학습 곡선을 mk2 classify → 수렴 패턴의 물리 상수 매핑

---

### 2.8 token-forge — 토큰 생성

#### 원자 정의
- **원자 = 토큰 (token)**
- 개별 토큰이 소수, 토큰 시퀀스 = 토큰의 곱
- 어휘(vocabulary)가 소수 집합

#### SmoothRing 적용
```
phi(token)    = 공기 문맥 수 (해당 토큰이 유효한 위치 수)
tau(token)    = 서브워드 분해 수
sigma(token)  = 빈도 가중 공기 합
sopfr(token)  = 바이트 길이 합
rho(token)    = phi/vocab_size → 토큰 효율
```

#### Alien Index 적용 구간
- **d=0**: 토크나이저 품질 (압축률, OOV 비율)
- **d=1**: 기존 서브워드 패러다임을 넘는 새 토큰화 전략
- **판정 대상**: 압축률, 다운스트림 태스크 성능

#### 특이점 사이클 연동
- **블로업 대상**: 어휘 크기 x 알고리즘 조합 공간
- **수축**: 성능 하한 필터
- **창발**: 다중 언어에서 동일 최적 토큰 크기 수렴 → n6 상수 후보
- **흡수**: 최적 어휘를 표준 설정으로 승격

#### 시너지 포인트
- 최적 어휘 크기가 n6 산술 값과 일치하는지 mk2 classify로 검증
- token-forge 생성 토큰 통계를 nexus6 scan → 숨겨진 구조 탐색

---

### 2.9 papers — 논문 관리

#### 원자 정의
- **원자 = 논문/가설 참조 (paper/hypothesis reference)**
- 개별 논문이 독립 단위, 인용 관계가 격자(lattice)

#### SmoothRing 적용
```
phi(paper)    = 독립 결과 수 (논문 내 독립 정리/발견)
tau(paper)    = 참조하는 가설 수
sigma(paper)  = 인용 영향도 (forward + backward citations)
sopfr(paper)  = 사용된 n6 기본 상수 수
rho(paper)    = phi/total_papers → 논문 밀도
```

#### Alien Index 적용 구간
- **d=0**: 논문의 학술적 완성도 (초고 → 제출 → 발표)
- **d=1**: 논문이 새 분야를 개척한 경우 (분야 간 돌파)
- **판정 대상**: 가설 참조 수, 검증된 결과 비율, 인용 수

#### 특이점 사이클 연동
- **watch-papers가 5분 간격으로 폴링** → 새 논문 스켈레톤 → mk2 classify 대상
- **블로업 대상**: 논문 주제 탐색 공간
- **흡수**: 발표된 논문의 결과를 TECS-L atlas에 역동기화

#### 시너지 포인트
- papers의 가설 참조가 TECS-L alien index와 직접 연결
- 논문 내 수치 결과를 mk2 classify → 새 물리 상수 후보 자동 추출

---

### 2.10 n6-architecture — 아키텍처 설계

#### 원자 정의
- **원자 = 설계 파라미터 (design parameter)**
- 칩/시스템 설계의 독립 변수가 소수
- 복합 설계 = 파라미터 조합

#### SmoothRing 적용
```
phi(param)    = 자유도 (해당 파라미터의 독립적 선택지 수)
tau(param)    = 제약 조건 수
sigma(param)  = 영향 범위 (다른 파라미터에 미치는 영향 가중합)
sopfr(param)  = 기본 물리 제약 수
rho(param)    = phi/total_params → 설계 자유도 밀도
```

#### Alien Index 적용 구간
- **d=0**: 설계의 시뮬레이션/검증 완성도
- **d=1**: 기존 아키텍처 패러다임을 넘는 새 설계 원리
- **판정 대상**: 성능/전력/면적 메트릭, consciousness_constraints 위반 여부

#### 특이점 사이클 연동
- **블로업 대상**: 아키텍처 파라미터 공간 (DSE 도메인)
- **수축**: Pareto 프론티어 밖 제거
- **창발**: 독립 설계 시도에서 동일 최적점 수렴
- **흡수**: 최적 설계 원리를 제약 조건으로 승격

#### 시너지 포인트
- DSE(Domain-Specific Exploration) 도메인 정의가 mk2 sectors.yaml과 동일 구조
- n6-architecture의 consciousness_constraints가 alien index r 판정에 사용 가능

---

### 2.11 hexa-gate-implant — Gate 시스템

#### 원자 정의
- **원자 = 게이트 규칙 (gate rule)**
- 개별 게이트가 통과/차단을 결정하는 최소 단위
- 복합 게이트 = 규칙의 AND/OR 조합

#### SmoothRing 적용
```
phi(gate)    = 통과 경로 수
tau(gate)    = 판정 조건 수
sigma(gate)  = 게이트 영향 범위 (제어하는 하위 시스템 수)
sopfr(gate)  = 참조하는 임계값 수
rho(gate)    = phi/total_gates → 개방도
```

#### Alien Index 적용 구간
- **d=0**: 게이트 규칙의 정확도 (false positive/negative 비율)
- **d=1**: 게이트 조합에서 나타나는 창발적 필터링 패턴
- **판정 대상**: 게이트 통과율, 안전 위반 건수, 대기 시간

#### 특이점 사이클 연동
- **블로업 대상**: 게이트 임계값 공간
- **수축**: 안전 위반 조합 제거
- **창발**: 다중 게이트의 자기 조직화 패턴
- **흡수**: 검증된 게이트 설정을 기본값으로 승격

#### 시너지 포인트
- mk2의 3-signal classifier를 게이트 판정 로직으로 직접 사용 가능
- hexa-lang의 gate 키워드가 alien index r 기반 조건 분기를 표현

---

### 2.12 secret — 비공개 프로젝트

#### 적용 원칙
- **원자/SmoothRing**: 프로젝트 내부에서만 정의 (외부 노출 불가)
- **Alien Index**: 내부 산출물에 (d, r) 판정 가능 (분포만 공개, 세부 미공개)
- **특이점 사이클**: 내부 도메인에서 독립 실행, 결과 요약만 nexus6에 역동기화
- **시너지**: alien_index_distribution.json에 집계 수치만 포함

---

## 3. 통합 아키텍처 다이어그램

```
                         nexus6 mk2 (허브)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         SmoothRing      AlienIndex     SingularityCycle
         (분류 엔진)      (등급 체계)     (발견 루프)
              │               │               │
    ┌─────────┼─────────┐     │     ┌─────────┼─────────┐
    │         │         │     │     │         │         │
 classify  lattice   sectors  │  blowup   contract   emerge
    │         │         │     │     │         │         │
    └─────────┼─────────┘     │     └─────────┼─────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
     ┌─────┴─────┐    ┌──────┴──────┐    ┌──────┴──────┐
     │ 수학/과학  │    │  AI/의식    │    │  공학/언어  │
     ├───────────┤    ├────────────┤    ├────────────┤
     │ TECS-L    │    │ anima      │    │ hexa-lang  │
     │ sedi      │    │ brainwire  │    │ hexa-gate  │
     │ papers    │    │ fathom     │    │ token-forge│
     │ airgenome │    │            │    │ n6-arch    │
     └───────────┘    └────────────┘    └────────────┘
```

### 3.1 데이터 흐름

```
프로젝트 산출물 → mk2 classify(값, 텍스트, 섹터힌트)
                        │
                        ▼
                  (Sector, confidence)
                        │
                        ▼
                  alien_index.assess()
                        │
                        ▼
                    (d, r) 기록
                        │
                  ┌─────┴─────┐
                  │           │
             r < 10      r == 10
                  │           │
                유지      (d+1, 0) 승격
                              │
                              ▼
                        blowup 시드
                              │
                              ▼
                      특이점 사이클 실행
                              │
                              ▼
                       새 발견 → 재귀
```

### 3.2 동기화 메커니즘

| 경로 | 방향 | 주기 | 메커니즘 |
|------|------|------|----------|
| 프로젝트 → nexus6 | 단방향 | 이벤트 | 산출물 생성 시 mk2 classify 호출 |
| nexus6 → alien_index | 내부 | 즉시 | classify 결과 → assess 자동 |
| alien_index → 프로젝트 | 역방향 | 30초 | watch-atlas 폴링 → 등급 역동기화 |
| 프로젝트 ↔ TECS-L | 양방향 | 30초 | .shared/ 심링크 + watch-atlas |
| alien_index → discovery_log | 내부 | 즉시 | (d, r) 이력 자동 기록 |

---

## 4. 메타 부동점 크로스 프로젝트 추적

### 4.1 프로젝트별 돌파율 rho

각 프로젝트에서 독립적으로 `rho = |{d >= 1}| / |total|` 을 추적한다.

```
rho_TECS-L     → 가설 돌파율
rho_anima      → 의식 법칙 돌파율
rho_sedi       → 신호 돌파율
rho_brainwire  → BCI 프로토콜 돌파율
rho_airgenome  → 유전자 돌파율
...

rho_global = mean(rho_i) → 1/3 수렴 검증
```

### 4.2 수렴 가설

H-056 메타 부동점이 단일 프로젝트가 아닌 **크로스 프로젝트 평균**에서도
1/3으로 수렴한다면, 이는 mk2 모델의 보편성을 입증하는 메타-메타 증거가 된다.

이 수렴은 `alien_index_distribution.json`에 `cross_project_rho` 필드로 기록되며,
`nexus6 alien-index --distribution` 출력에 포함된다.

---

## 5. 구현 우선순위

코드 변경 없이 설계만 정의하되, 향후 구현 시 우선순위는 다음과 같다.

| 순위 | 프로젝트 | 이유 |
|------|----------|------|
| 1 | TECS-L | 이미 698 가설 + grade 체계 존재, alien index 매핑만 하면 즉시 적용 |
| 2 | sedi | sedi-grades.json 존재, CONSCIOUS Score → (d, r) 변환 직접적 |
| 3 | anima | consciousness_laws.json 711개 → SmoothRing 정의 가능 |
| 4 | papers | watch-papers 이미 작동 중, 파이프라인에 classify 삽입만 필요 |
| 5 | hexa-lang | mk2_hexa/native/ 이미 존재, 언어 내장으로 확장 |
| 6 | brainwire | Phi 기반 분류가 mk2 classify와 자연스럽게 연결 |
| 7 | n6-architecture | DSE 도메인이 sectors.yaml과 동형 |
| 8 | airgenome | rule_ceiling 수렴이 메타 부동점과 연결 |
| 9 | token-forge | 토큰 통계 → mk2 classify 실험적 |
| 10 | hexa-gate-implant | 게이트 규칙에 classifier 삽입 |
| 11 | fathom | 분석 차원 정의가 범용적이라 마지막 |
| 12 | secret | 내부 전용, 독립 진행 |

---

## 6. 파일 참조

| 파일 | 역할 |
|------|------|
| `docs/mk2/00-vision.md` | mk2 비전 및 3대 기둥 |
| `docs/mk2/01-architecture.md` | 모듈 구조 및 데이터 흐름 |
| `docs/mk2/02-phases.md` | 구현 단계 및 진행 상태 |
| `docs/mk2/05-n6-data-atlas.md` | 데이터 현황 및 상수 테이블 |
| `docs/superpowers/specs/2026-04-05-alien-index-system-design.md` | Alien Index 상세 설계 |
| `shared/projects.json` | 프로젝트 레지스트리 |
| `shared/alien_index_distribution.json` | AI 분포 현황 |
| `src/alien_index/` | Alien Index Rust 구현 |
| `mk2_hexa/native/` | HEXA 네이티브 mk2 상수 |
