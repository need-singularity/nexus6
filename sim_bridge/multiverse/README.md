# sim_bridge/multiverse — NEXUS-6 ★18 Quantum Multiverse Interferometer MVP

## 컨셉
M 개 평행 sim 우주를 서로 다른 RNG 시드로 독립 초기화 + 독립 eps 바이트 스트림으로 T 스텝 진화. 우주 쌍(M×(M-1)/2 개) 간 mutual information(MI)을 4-bin plug-in histogram estimator 로 측정. ANU QRNG 와 `/dev/urandom` 두 소스의 MI 분포를 Kolmogorov-Smirnov 2-sample test 로 비교. 두 분포가 유의하게 다르면(p<0.05) ANU QRNG 숨은 상관 또는 우주 공통 substrate 의 시그널 후보.

## 모듈 (모두 hexa-lang)
| 파일 | 역할 | 핵심 수식/알고리즘 |
|------|------|--------------------|
| `mini_world.hexa` | 최소 latent world sim | x_{t+1} = bound(W·x_t + ε), bound(x)=x·S/(S+|x|) |
| `mi_calc.hexa` | pairwise MI (단독 모듈) | MI = Σ p(x,y) log(p(x,y)/(p(x)p(y))) |
| `ks_test.hexa` | 2-sample KS (단독 모듈) | D = sup \|F_A - F_B\|, p = 2Σ(-1)^{k-1}exp(-2k²λ²) |
| `interferometer.hexa` | 메인 드라이버 (mini_world+MI inline 복사) | M 우주 trajectory + pairwise MI matrix |
| `compare_ks.hexa` | 두 mi_values.txt → KS JSON | 위와 동일 |
| `runner.sh` | 파이프라인 실행 | seed 준비 → interferometer×2 → compare_ks → summary.md |

hexa-lang 은 모듈 import 부재로 `interferometer.hexa` 안에 mini_world / mi_calc 함수들을 inline 복사.
단독 모듈 파일들(`mini_world.hexa`, `mi_calc.hexa`, `ks_test.hexa`) 은 자기 테스트(`--self-test`) + 교차검증용.

## n=6 컨벤션
- LATENT_DIM `dim` 기본 64 (= σ²(8). 원래 σ²(6)=144 미니 경제판)
- WORLD_SCALE = 1000 (fixed-point 정수)
- W_BIAS = 43 (근접 n=6 sopfr 영역)
- W 희소 밴드: w[i] = 0.67·x[i-1] − 0.31·x[i] + 0.19·x[i+1] + bias (wrap-around)
- bin 경계 [0, 75, 150, 225, ∞) — mini_world energy 실측 분포 기반 고정

## 실행
```bash
# defaults M=10 T=200 DIM=64
bash runner.sh

# dev (ANU 건너뛰고 urandom 양쪽): rate-limit 아낌
SKIP_ANU=1 bash runner.sh

# 커스텀
M=20 T=500 DIM=32 bash runner.sh
```

## 출력 구조
```
runs/<ts>/
  anu_seed.txt            # decimal space-separated bytes (ANU QRNG 64 + urandom 확장)
  prng_seed.txt           # 전량 urandom
  anu/
    trajectories.jsonl    # M 라인, {"u":i,"tag":"anu","energy":[...T개...]}
    mi_matrix.csv         # M×M, 대칭, scaled×1000
    mi_values.txt         # M*(M-1)/2 라인, pairwise MI (scaled×1000)
    stats.json            # mean/std/min/max (scaled×1000)
    stdout.log
  prng/                   # 동일 구조
  ks_result.json          # {D_scaled, lambda_scaled, p_scaled, scale:1000}
  summary.md              # 사람용 표 + 해석
```

## 출력 해석
모든 수치값은 fixed-point **×1000 scale** (hexa stage0 은 float 미성숙). 해석 시 ÷1000 하면 실제값.

### MI (nats)
- MI 는 자연로그 기준 nats. 4-bin 기준 이론 상한 = ln(4) ≈ 1.386
- T=200 finite-sample bias ≈ (B−1)/(2T) = 3/400 ≈ 0.0075 nats → 실측 평균이 이 근처면 "noise floor"
- NPMI (정규화) 는 `mi_calc.hexa` 단독 자체 테스트에서만 반환

### KS p-value (×1000)
- `p_scaled` < 50 → p < 0.05, **H0 기각** (ANU 분포 ≠ PRNG)
- `p_scaled` ∈ [50, 100] → 경계 (p ∈ [0.05, 0.1])
- `p_scaled` > 200 → H0 유지 (분포 동일)

### 해석 규칙 (honest)
- **p>0.05**: ANU ≡ PRNG (MVP 규모에서). 더 큰 M·T 로 스캔 필요. Phase 0 에선 이것이 기대 default.
- **p<0.05**: 가능 원인 3가지:
  1. ★ ANU QRNG 진짜 숨은 구조 (양자 양자역학 이상치)
  2. mini_world 의 W 행렬이 특정 시드 패턴에 공명하여 bias 증폭
  3. ANU seed (64B) + urandom 확장 혼합의 결합 artifact (label hybrid)
- 반드시 3 회 재실행해서 p 분포 확인 후 결론.

## 제약 (Phase 0 MVP)
- ANU QRNG REST API 1 req/min + 64 B/req → M×(dim+T) 바이트 대부분이 urandom 확장
- 따라서 "ANU vs PRNG" 비교는 실제로 "ANU-head+urandom-tail vs full-urandom" 이며, 차이는 head 64 B 의 seed 초기화에만 영향. 이 한계는 `summary.md` 에 자동 기록됨.
- hexa stage0 무 모듈 시스템 → 코드 중복 (mini_world / mi_calc 인라인)
- 4-bin histogram plug-in MI 는 T→∞ 점근적으로만 올바름. Kraskov-Stögbauer-Grassberger (KSG) k-NN MI 가 더 정확하지만 구현 복잡 → 차후.

## H-* 규칙 준수
- H-NOHOOK: hook 시스템 생성 없음 (runner.sh 만, cron/launchd 미사용)
- H-NOARCHIVE: *.bak / backup/ / archive/ 폴더 생성 안 함. 재실행 시 새 `runs/<ts>/` 생성
- H-NOBLOCK: 모든 실행 단계 유한 (max T=200 steps × M=10 우주 ≈ 수 초)
- H-NOZOMBIE: 실행 시 `timeout` 불필요 (hexa 자체 완료). perl_timeout 미사용.

## 로드맵
| 단계 | 목표 |
|------|------|
| Phase 0 MVP (이것) | M=10, T=200, ANU-head seeding, plug-in MI, KS 비교 |
| Phase 1 | 3회 반복 + Fisher 합성 p, dynamic quantile binning |
| Phase 2 | ANU 다회 호출 (per-universe 완전 ANU seeding), KSG estimator |
| Phase 3 | M=100+, multi-lag MI (t vs t+τ 자기상관), real-time stream |
| Phase 4 | Bell-like entanglement test with commutation measurement pairs |
