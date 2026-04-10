# Convergence Engine — 적응형 다중영역 수렴점 탐색 엔진

## Summary

골든존 발견 방법론을 일반화한 엔진. 8개 수학/물리 도메인의 ~80개 상수를 조합하여,
3개 이상의 독립 도메인에서 동일 값에 수렴하는 지점을 자동 발견한다.

3가지 탐색 전략을 동시에 실행하며, 실시간 yield 기반으로 탐색 예산을 적응적으로 재배분.

## Architecture

```
convergence_engine.py (단일 파일)

Phase 0: 상수 풀 로드 + 8개 도메인 태깅
  ↓
Phase 1: 3 전략 병렬 실행 (adaptive budget)
  S1: Open Search (전체 조합 depth 1-2)
  S2: Pair Scan (도메인 쌍별 교차)
  S3: Target Backtrack (기존 발견값 역추적)
  ↓
Phase 2: Convergence Detection
  같은 값(±threshold)에 도달한 독립 경로 클러스터링
  ↓
Phase 3: Scoring + Texas Sharpshooter 검증
  ↓
Phase 4: 결과 출력 (Convergence Map)
```

## 8 Domains, ~80 Constants

| ID | Domain       | Constants |
|----|-------------|-----------|
| N  | Number Theory | sigma(6)=12, tau(6)=4, phi(6)=2, sigma(28)=56, tau(28)=6, phi(28)=12, sopfr(6)=5, s(6)=6, mu(6)=1, 6, 28, 496 |
| A  | Analysis     | e, pi, gamma=0.5772, zeta(3)=1.2021, pi^2/6, ln(2), ln(3), ln(4/3), 1/e, e^2 |
| G  | Algebra/Groups | dim(SU(2))=3, dim(SU(3))=8, dim(E8)=248, dim(SO(10))=45, Out(S6)=2, rank(E8)=8 |
| T  | Topology/Geometry | kissing(3)=12, chi(S2)=2, 26(bosonic), 10(superstring), 11(M-theory) |
| C  | Combinatorics | F(6)=8, C(6,3)=20, Catalan(3)=5, Bell(3)=5, T(6)=21, Feigenbaum(delta)=4.669 |
| Q  | Quantum Mechanics | 1/alpha=137.036, alpha_s=0.1185, sin2(theta_W)=0.231, g-2=0.00232, m_e/m_p |
| I  | Quantum Information | ln(2), S_BH, Holevo, Landauer kT*ln2 |
| S  | Statistical Mechanics | lambda_c=0.2700, Onsager(2D)=2/ln(1+sqrt(2)), critical exp nu/beta/gamma |

## 3 Strategies

### S1: Open Search
- 전체 상수 풀에서 depth 1-2 조합 생성
- 모든 도메인 태그 추적
- 기존 dfs_engine 방식 확장

### S2: Pair Scan
- C(8,2)=28개 도메인 쌍에 대해 교차 조합
- 각 쌍에서 발견된 값을 글로벌 클러스터에 등록
- 3개+ 도메인에서 같은 클러스터에 도달하면 수렴점 후보

### S3: Target Backtrack
- 기존 발견값 + 알려진 수학 상수를 타겟으로 고정
- 새 도메인 상수에서 해당 값에 도달하는 경로 역추적
- 기존 발견 강화 + 추가 도메인 연결 발견

## Adaptive Scoring

```
strategy_yield[i] = discoveries[i] / trials[i]
budget[i] = max(0.10, yield[i] / sum(yields))
```

매 1000 조합마다 재계산. 최소 10% 보장으로 어떤 전략도 완전 배제 안 함.

## Convergence Score

```
base       = -log10(relative_error + 1e-15)
domain_bonus = (n_independent_domains - 1) * 15
novelty    = +10 if not matching known discovery
exact_bonus = +50 if error < 1e-12
convergence_score = base + domain_bonus + novelty + exact_bonus
```

## Output Format

Convergence Map: 수렴점별로 도달 경로, 도메인 수, Texas p-value 표시.
Strategy Performance: 전략별 yield, budget 배분 현황.

## CLI

```
python3 convergence_engine.py                     # default depth=2, threshold=0.1%
python3 convergence_engine.py --depth 3           # depth 3 (slow)
python3 convergence_engine.py --threshold 0.01    # 0.01% only
python3 convergence_engine.py --texas             # include Texas test
python3 convergence_engine.py --top 30            # top 30 convergence points
```
