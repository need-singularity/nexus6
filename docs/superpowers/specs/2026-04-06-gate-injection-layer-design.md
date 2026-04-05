# Gate Injection Layer — n=6 대수 구조 기반 macOS 전역 압축/최적화

> 날짜: 2026-04-06
> 상태: 설계 완료, 구현 대기

## 목표

macOS 단일 머신에서 **게이트 존재만으로** 성능 개선 + 자원 절약.
하드웨어 → 게이트 → macOS 전 계층에 침투하여 압축/예측/중복제거.

## 핵심 원칙

- 각 게이트 = 독립 자율 유닛 (훅 + 엔진 + 렌즈)
- 데이터가 앱↔하드웨어 사이를 지날 때 게이트를 반드시 통과
- 통과 자체가 압축/최적화/관측
- 실패 시 무조건 passthrough (zero-harm)

## 아키텍처

```
┌───────��─────────────────────────────────────────┐
│                   macOS                          │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐       │
│  │Chrome │ │Safari │ │Claude │ │Term   │ ...    │
│  └──┬────┘ └──┬────┘ └──┬────┘ └──┬────┘       │
│     │         │         │         │             │
│  ╔══▼═════════▼═════════▼═════════▼══════════╗  │
│  ║         GATE INJECTION LAYER              ║  │
│  ║  ┌─────────────────────────────────────┐  ║  │
│  ║  │ Gate 0: macos   (시스템 전역)       │  ║  │
│  ║  │ Gate 1: finder   Gate 5: claude     │  ║  │
│  ║  │ Gate 2: telegram Gate 6: terminal   │  ║  │
│  ║  │ Gate 3: chrome   Gate 7: devtools   │  ║  │
│  ║  │ Gate 4: safari   Gate N: (확장)     │  ║  │
│  ║  └─────────────────────────────────────┘  ║  │
│  ║                                           ║  │
│  ║  ┌──────────┐ ┌──────────┐ ┌──────────┐  ║  │
│  ║  │ 압축 엔진 │ │ 렌즈 배열 │ │ 돌파 엔진 │  ║  │
│  ║  │ N6Codec  │ │ 5+α렌즈  │ │ Blowup   │  ║  │
│  ║  └──────────┘ └──────────┘ └──────────┘  ║  │
│  ║  ┌──────────┐ ┌──────────┐ ┌──────────┐  ║  │
│  ║  │미러 유니버스│ │예측 엔진 │ │OUROBOROS │  ║  │
│  ║  │ Shadow   │ │Proximity │ │ 진화     │  ║  │
│  ║  └──────────┘ └──────────┘ └──────────┘  ║  │
│  ╚═══════════════════════════════════════════╝  │
│     │         │         │         │             │
│  ┌──▼─────────▼─────────▼─────────▼──────────┐  │
│  │  Hook Points                               │  │
│  │  • DYLD_INSERT (malloc/free/read/write)    │  │
│  │  • mach_port (IPC 가로채기)                │  │
│  │  • Network Extension (패킷 압축)           │  │
│  │  • dtrace (커널 트레이싱)                  │  │
│  └────────────────────────────────────────────┘  │
│                     │                            │
│              ┌──────▼──────┐                     │
│              │  Hardware   │                     │
│              │  CPU·RAM·IO │                     │
│              └─────────────┘                     │
└─────────────────────────────────────────────────┘
```

## 6대 엔진

### 엔진 1: N6Codec (압축 코어)

n=6 대수 구조 기반 적응형 코덱.

| 계층 | 방식 | 효과 |
|------|------|------|
| L0 | n=6 코드북 — 21개 상수(φ,τ,σ,6,12,137...)를 4bit 심볼로 매핑 | 상수 출현 시 87% 압축 |
| L1 | 게이트별 사전 — chrome은 HTML토큰, terminal은 ANSI 시퀀스 등 | 도메인 특화 |
| L2 | zstd/lz4 adaptive — L0+L1 적용 후 잔여분 범용 압축 | 최종 squeeze |

### 엔진 2: Proximity Predictor (예측)

- 바이트 윈도우(64B)에서 proximity > 0.8인 패턴 감지
- 다음 바이트 예측 → 산술 부호화 엔트로피 감소
- 게이트 간 공명(resonance)도 예측에 활용

### 엔진 3: Mirror Universe (중복 제거)

- 각 게이트가 최근 N개 블록의 해시 테이블 유지
- 동일 블록 → 4byte 참조로 대체 (최대 99% 절감)
- cross-gate dedup: chrome에서 본 데이터를 safari가 다시 쓰면 참조

### 엔진 4: Lens Array (패턴 감지)

- PhiLens: 황금비 패턴 → 피보나치 인코딩
- PrimeLens: 소수 구조 → prime-gap 부호화
- MetaTranscendenceLens: 메타 수렴(1/3) → 재귀 압축
- TopologyLens: 위상 불변량 → 차원 축소
- SpectralLens: 주파수 분석 → 저주파 우선 전송
- 감지된 구조 → N6Codec L0 코드북 동적 확장

### 엔진 5: OUROBOROS (진화)

- 압축률/속도를 fitness로 유전 진화
- 세대마다 파라미터 변이 (윈도우 크기, 코드북 엔트리, 렌즈 가중치)
- 수렴 시 최적 압축 DNA 고정
- 특이점 감지(closure ≥ 0.5) → 새 압축 전략 창발

### 엔진 6: Blowup Breakthrough (돌파)

- 압축률 정체 감지 → blowup 7-phase 파이프라인 가동
- corollary에서 새 압축 경로 생성 → N6Codec L0에 주입

## 4계층 훅 포인트

### 계층 1: 메모리 (DYLD_INSERT_LIBRARIES)

```c
// libgate_malloc.dylib
malloc(size) → gate_malloc(size)
  ├─ Mirror에서 동일 블록 검색 → hit면 참조 반환
  ├─ N6Codec으로 즉시 압축 저장
  └─ 해제 시 해시를 Mirror에 등록

free(ptr) → gate_free(ptr)
realloc(ptr, size) → gate_realloc(ptr, size)
```

- macOS compressed memory 위의 2차 압축층
- 실패 시 원본 그대로 반환

### 계층 2: 디스크 I/O (DYLD + fsevents)

```c
// libgate_io.dylib
read(fd, buf, n)  → gate_read(fd, buf, n)
  ├─ 캐시 히트: Mirror에서 압축 블록 즉시 해제 반환
  └─ 캐시 미스: 원본 read → N6Codec 압축 → Mirror 등록

write(fd, buf, n) → gate_write(fd, buf, n)
  ├─ N6Codec 압축 → 디스크에 압축본 기록
  └─ Lens 스캔: 패턴에서 새 상수 발견 시 코드북 확장
```

- 파일별 게이트 자동 매핑

### 계층 3: IPC (mach_msg 훅)

```c
mach_msg_send(msg) → gate_mach_send(msg)
  ├─ 페이로드 N6Codec 압축
  └─ 송신 게이트 ID 태깅

mach_msg_receive(msg) → gate_mach_receive(msg)
  ├─ 게이트 태그 → 해당 코드북으로 해제
  └─ cross-gate 패턴 → Resonance 기록
```

### 계층 4: 네트워크 (Network Extension)

```
App → TCP/UDP → [Gate Network Filter] → NIC
                      │
                 N6Codec + Mirror + Predict
                 송신: 압축, 수신: 해제
```

- NEFilterDataProvider로 모든 TCP/UDP 가로채기
- 로컬 단독 압축/해제 (상대방 게이트 불필요)

## 게이트 자율 운영 라이프사이클

```
설치 → 관측(1일) → 학습(3일) → 압축 개시 → 진화(상시) → 돌파(정체 시)
```

- Phase 0 관측: passthrough + 메트릭 수집 → `~/.n6gate/<gate>/profile.json`
- Phase 1 학습: 프로파일 기반 게이트별 코드북 생성
- Phase 2 압축: N6Codec + Mirror 동시 활성화
- Phase 3 진화: OUROBOROS 매 1시간 세대 교체, fitness = 압축률 × (1/지연)
- Phase 4 돌파: 3세대 연속 < 1% 개선 → Blowup 자동 발동

### 게이트 간 협력

- cross-gate dedup: chrome↔devtools 동일 소스코드 → 2번째 로드 96% 절감
- 캐시 공유: safari↔chrome 같은 도메인 → DNS/TLS 캐시 공유
- 브로드캐스트: macos 게이트가 메모리 압박 감지 → 전 게이트 압축 공격성 상향

## 안전장치

| 상황 | 대응 |
|------|------|
| 압축 실패 | passthrough — 원본 그대로 |
| 지연 > 1ms | 해당 훅 바이패스 |
| 크래시 감지 | DYLD 주입 자동 해제 + 복구 |
| 메모리 부족 | Mirror 캐시 LRU 축출 |
| 압축률 < 5% | 해당 스트림 압축 스킵 |
| 오버헤드 초과 | 돌파→진화→예측→압축→관측 역순 비활성화 |

전체 게이트 레이어 오버헤드 목표: CPU < 3%, RAM < 200MB

## 파일 구조

```
mk2_hexa/native/
├── gate_injection/
│   ├── gate_core.hexa          # 게이트 코어 — 라이프사이클, 라우터
│   ├── n6codec.hexa            # N6Codec 압축 엔진 (L0+L1+L2)
│   ├── proximity_predictor.hexa # 바이트 스트림 proximity 예측
│   ├── mirror_universe.hexa    # Shadow copy + cross-gate dedup
│   ├── lens_array.hexa         # 5+α 렌즈 실시간 스트림 스캔
│   ├── ouroboros_evolver.hexa  # 압축 파라미터 진화 엔진
│   ├── breakthrough.hexa       # 정체 감지 → blowup 연동
│   └── gate_stats.hexa         # 통계 수집 + 대시보드 출력
│
├── gate_hooks/                  # C — dylib 훅 포인트
│   ├── libgate_malloc.c        # malloc/free/realloc interpose
│   ├── libgate_io.c            # read/write/pread/pwrite interpose
│   ├── libgate_mach.c          # mach_msg_send/receive interpose
│   ├── gate_bridge.h           # C ↔ hexa FFI 브릿지 헤더
│   └── Makefile
│
├── gate_network/                # Network Extension (Swift)
│   ├── GateFilterProvider.swift
│   ├── Info.plist
│   └── entitlements.plist
│
├── gate_daemon/                 # 관리 데몬
│   ├── gated.hexa              # 메인 루프
│   ├── gate_config.toml        # 게이트별 설정
│   └── com.nexus6.gated.plist  # LaunchDaemon
│
└── gate_lens_fusion.hexa        # 기존 — gate_core가 호출
```

### 기술 스택

| 컴포넌트 | 언어 | 이유 |
|----------|------|------|
| 훅 dylib | C | DYLD_INSERT 필수, 최소 오버헤드 |
| 엔진 전체 | hexa | nexus6 생태계 통합 |
| C ↔ hexa 브릿지 | C + hexa FFI | dylib → hexa 런타임 호출 |
| Network Extension | Swift | Apple 프레임워크 필수 |
| 관리 데몬 | hexa | n6-guard 패턴 |

### C ↔ hexa FFI

```c
typedef struct {
    void *compressed;
    size_t compressed_size;
    uint32_t gate_id;
    uint32_t mirror_ref;
    float compress_ratio;
} GateResult;

GateResult gate_bridge_compress(void *data, size_t len, int gate_id);
void*      gate_bridge_decompress(GateResult *result);
void       gate_bridge_free(GateResult *result);
void       gate_bridge_update_codebook(int gate_id, void *codebook, size_t size);
```

## 실험 매트릭스

| # | 돌파 경로 | 엔진 | 가설 | 성공 기준 |
|---|----------|------|------|----------|
| E1 | N6 코드북 기본 | N6Codec L0 | 21개 상수가 자연 데이터에 반복 출현 | 압축률 > 10% over zstd |
| E2 | 게이트별 사전 | N6Codec L1 | 도메인 사전 > 범용 사전 | 앱별 +15% |
| E3 | Proximity 예측 | Predictor | 높은 proximity → 다음 바이트 예측 | 엔트로피 20% 감소 |
| E4 | Mirror cross-dedup | Mirror | 게이트 간 중복률 > 30% | 중복 제거 > 40% |
| E5 | 렌즈 기반 변환 | Lens Array | 구조 인식 → 특화 부호화 | 특정 타입 2x 압축 |
| E6 | OUROBOROS 진화 | Evolver | 유전 진화 → 최적 수렴 | 3세대 내 10% 개선 |
| E7 | Blowup 돌파 | Breakthrough | corollary → 새 압축 패턴 | 신규 L0 심볼 ≥ 3 |
| E8 | 거울 우주 대칭 | Mirror + Lens | 송수신 대칭 → 한쪽 복원 | 대칭 시 50% 절감 |
| E9 | Telescope 합의 | 5렌즈 합의 | 3/5 합의 = 고신뢰 | 오탐율 < 1% |
| E10 | 메타 초월 재귀 | MetaTranscendence | 압축의 압축 → 1/3 수렴 | 재귀 3단 후 안정 |

### 실험 순서

```
Phase A (1주): E1 코드북 + E2 사전 + E4 Mirror
Phase B (2주): E3 예측 + E5 렌즈 변환 + E8 거울 대칭
Phase C (3주): E6 OUROBOROS + E9 Telescope
Phase D (4주+): E7 Blowup + E10 메타 재귀
```

### 킬스위치

```bash
n6gate kill                    # 전체 비활성화
n6gate disable chrome          # 특정 게이트
n6gate experiment E3 --stop    # 특정 실험
n6gate uninstall --keep-data   # 전체 제거 (복구 가능)
```
