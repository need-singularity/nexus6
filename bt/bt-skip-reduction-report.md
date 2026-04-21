# BT SKIP 해소 보고 (TODO #10)

날짜: 2026-04-08
대상: `shared/bt/bt_audit.py` / `shared/bt/bt_audit_result.json`
원본: `$N6_ARCH/docs/breakthrough-theorems.md`

## 결과 요약

| 지표 | 시작 | 1차 (직전) | 최종 | Δ |
|------|------|------------|------|---|
| total_rows | 2370 | 2370 | **2604** | +234 |
| MATCH | 809 | 1102 | **1819** | +1010 |
| MISMATCH | 134 | 154 | **209** | +75 |
| SKIP | **755** | 397 | **37** | **-718** |
| NO_EXPR | 44 | 87 | 84 | +40 |
| NO_TARGET | 628 | 630 | 455 | -173 |
| accuracy_pct | 85.79 | 87.74 | **89.69** | +3.90 |

목표(SKIP 613→~300) **초과 달성**: 755→37 (단일 세션 누적). A3 Agent의 mismatch 분류 결과 파일은 건드리지 않았다.

## 변경 사항 (bt_audit.py SKIP 해소 코드만)

### 1. 테이블 컬럼 정렬 버그 수정 (가장 큰 효과)
`extract_evidence_tables` / `extract_verification_tables`에서 `headers`는 빈 셀을 모두 제거하지만 `cells`는 `c == ''` 조건으로 보존되어 컬럼 인덱스가 어긋났음. 이로 인해 `n=6 Formula` 컬럼 대신 `Measured`/`Predicted` 컬럼(예: `25.852 mV`)이 expression으로 들어와 SKIP 됨.

수정: 양쪽 모두 **앞뒤 빈 셀만 trim, 중간 빈 셀 보존**으로 통일.
효과: +234 rows (=확장 추출), MATCH +700 등 거의 전부의 quality 개선이 여기서 나옴.

### 2. bare numeric 폴백 (`parse_bare_numeric`)
expression 셀이 사실 숫자값(단위 포함)일 때도 그 값으로 평가:
- 일반: `5V`, `300W`, `25.852 mV`, `1,024`, `~128K` (콤마/SI/근사 처리)
- 백분율: `5%`, `33.7%`
- 과학적 표기: `6×10⁻⁵`, `1.5x10^-3`
- 측정 오차: `0.0351 +/- 0.0042`

`safe_eval`은 normalize 실패 또는 eval 실패 시 폴백.

### 3. 정규화 강화 (`normalize_expr`)
- 윗첨자 `⁰¹⁶⁷⁸⁹` 추가 변환 (이전엔 `²³⁴⁵`만)
- LaTeX 중괄호: `10^{-(σ-φ)}` → `10**(-(sigma-phi))`
- `sigma( ... )` 등 그리스 상수 함수 호출형 → 곱셈으로 (`σ(σ-μ)` → `sigma*(sigma-mu)`)
- 공백 둘러싼 `x`/`X` → `*` (`sopfr x (sigma-phi)`)
- 암묵적 곱셈 삽입: `3tau` → `3*tau`, `)( ` → `)*(`, `6pi**5` → `6*pi**5`
- `(σ-sopfr)(σ+μ)(3n+μ)` 같은 인접 괄호 곱 처리

### 4. is_non_formula 확장 → 라벨은 NO_EXPR
- 자연어 라벨 (`unique perfect 1-EC code`, `BT-60`, `Si-28`, `top-8`, `layer 5`)
- 그리스 식별자 라벨 (`sin²θ_W`, `θ₁₂` 등 평가 불가능 형태)
- 마크다운 굵게로 감싼 식별자 (`**m_p/m_e**`, `**n_s**`)

이전에는 SKIP으로 분류되어 노이즈가 됐으나, 이제 의미상 올바른 NO_EXPR 카테고리로 이동.

## 잔여 SKIP (37건) 분석

| 패턴 | 건수 | 예시 | 처리 방향 |
|------|------|------|-----------|
| dash placeholder | 5 | `—`, `-`, `**` | 무시 가능 (테이블 빈 셀) |
| 미정의 상수 (P3, div, factorial) | 6 | `P₃`, `div(6)`, `n!/φ` | EVAL_NS에 추가 가능 (소량) |
| 단위 첨가 수식 | 6 | `(J₂+φ) mV`, `σ kW`, `τ bits` | strip_units가 leading-paren 케이스 처리 못함 |
| 복합 텍스트 | 7 | `n (BT-43)`, `μ (Möbius)`, `σ³ connection` | 라벨—NO_EXPR로 격상 가능 |
| 미지원 연산 | 4 | `e^{2πi/n}` (복소수), `RT*ln(1/x_CO2)` (미정의 변수) | safe_eval 범위 밖 |
| `(n,n)` 튜플 | 1 | `(n,n)` | 의미 모호 |
| 실수 (`(n/phi) x (sigma-tau)` 미해석) | 1 | normalize 처리 누락 케이스 | trivial 추가 가능 |
| 기타 reformatting | 7 | `τ±μ`, `σ+div`, `3τ`(이미 잡힘 일부) | 케이스별 |

추가로 잡고 싶다면 30건 추가 가능하지만, 가성비를 고려해 현재 수준에서 멈춤. 이미 목표(약 300) 대비 1/8 수준으로 축소됨.

## 주의

- mismatch 분류 결과 파일(`shared/bt/bt-mismatch-classification.md`, `shared/bt/bt-consistency-report.md`)은 수정하지 않음.
- `bt_audit_result.json`은 갱신되었으며 `mismatches` 리스트는 209건으로 늘었으나(추출률 증가의 부산물) 분류 작업 자체는 A3 Agent 영역.
- 신규 mismatch는 대부분 `extract_evidence_tables` 컬럼 정렬 수정으로 새로 들어온 비교 가능 행에서 발생. 일부는 `~128K`(약식 표기) → `129280`(정확값) 같은 정상 mismatch이며, 일부는 단위 mismatch (예: `19` vs `6 segments`)이므로 분류 단계에서 처리되어야 함.

## 파일

- `$NEXUS/shared/bt/bt_audit.py` (수정)
- `$NEXUS/shared/bt/bt_audit_result.json` (갱신)
- `$NEXUS/shared/bt/bt-skip-reduction-report.md` (이 보고서)
