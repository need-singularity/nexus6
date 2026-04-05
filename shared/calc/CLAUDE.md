# calc/ — Calculator Tools

## HEXA 우선 원칙

성능 문제가 예상되는 계산기는 **반드시 HEXA(mk2_hexa/native/)로 먼저 구현**.

### 언제 HEXA를 사용하는가

- 반복 > 10,000회
- 실행 시간 > 10초 예상
- 조합 공간 > 10^6
- Monte Carlo 샘플 > 100,000
- brute-force search, grid scan, large-N 시뮬레이션

### 언제 Python을 사용하는가

- 단순 수식 검증 (1회 계산)
- 오차율 테이블 출력
- 외부 데이터 fetch / API 호출
- 시각화 / ASCII 그래프
- 빠른 프로토타입

### HEXA 프로젝트

```
  위치: mk2_hexa/native/
  실행: nexus6 mk2 run <module>
  모듈: constants.hexa, pure_math.hexa, classify.hexa, grading.hexa, cycle.hexa
```

### Python 계산기 컨벤션

```
  위치: calc/
  실행: python3 calc/<name>.py [--args]
  네이밍: <domain>_<purpose>.py (예: fusion_hypothesis_verifier.py)
  필수: argparse CLI, 출력은 ASCII 테이블/그래프
```

## 현재 계산기 목록

### 검증기 (Verifiers)

| File | Domain | Hypotheses |
|------|--------|-----------|
| `fusion_hypothesis_verifier.py` | FUSION-001~017 | 핵융합 기초 17개 |
| `fusion_plasma_sc_verifier.py` | FUSION-018~037, SC, SCMAG, TOKAMAK | 플라즈마/초전도 53개 |
| `extreme_hypothesis_verifier.py` | 전체 17개 도메인 | 337개 통합 검증 |

### 도구 (Tools)

| File | Purpose |
|------|---------|
| `hypothesis_verifier.py` | 범용 가설 검증 |
| `r_spectrum.py` | R-spectrum 분석 |
| `statistical_tester.py` | Texas Sharpshooter 통계 |
| `experimental_protocol.py` | 실험 프로토콜 생성 |
| `validate_calculators.py` | 계산기 유효성 검사 |
