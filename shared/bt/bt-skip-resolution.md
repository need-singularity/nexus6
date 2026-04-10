# BT Audit SKIP 해소 보고서

- 일자: 2026-04-08
- 대상: `shared/bt_audit.py` (BT EXACT 수식 자동 검산기)
- 산출물: `shared/bt_audit_result.json`
- 작업 범위: SKIP 613건만 (mismatch 141건은 별도 A 에이전트 담당)

## 1. SKIP 사유별 분류 (개선 전 613건)

| 분류 | 건수 | 패턴 |
|------|-----:|------|
| `other` (라벨/비-수식) | 354 | `**Koide Q**`, `α_s(M_Z)`, `Mertens dropout`, `25 μm` |
| `unicode_sub_sup` | 68 | `K₁`, `n²`, `σ³` (유니코드 첨자/지수) |
| `num_unit` | 67 | `12 (A100)`, `±500 kV`, `5×` |
| `list_comma` | 28 | `[24, 12, 8]`, `2, 4, 8` |
| `md_bold_label` | 21 | `**n_s**`, `**Koide Q**` |
| `other_eq` | 17 | `(sigma-tau)*n = 48` |
| `list_brace` | 15 | `{2, 4, 8}` |
| `bare_label` | 11 | `Si`, `N_eff` |
| `label_eq` | 10 | `mu = 1`, `sigma = 12` |
| `tex` | 10 | `V_ub\\`, `\\Lambda` |
| `list_bracket` | 6 | `[7, 4, 3]` |
| `ladder` | 4 | `2 → 4 → 8` |
| 기타 | 2 | |

## 2. `bt_audit.py` 보강 사항

### 2.1 단위 정규식 버그 수정 (가장 큰 회귀 원인)
기존 `re.sub(r'...|s|ms|...', flags=IGNORECASE)` 가 `sigma` 의 `ma` 부분에 매치되어
`sigma` → `sig` 로 잘려 평가 실패. 선행 숫자/괄호 lookbehind `(?<=[\d\)])` 추가, 케이스 구분.

### 2.2 유니코드 첨자/지수 분리 처리
- 아래첨자: `K₁` → `K1`
- 윗첨자: `n²` → `n**2`, `σ³+μ` → `sigma**3+mu`
연속 윗첨자를 한 번에 `**N` 으로 묶는 `_convert_superscripts` 추가.

### 2.3 리스트/래더 분해 (`split_list_expr` / `split_list_value`)
`[a,b,c]`, `{a,b,c}`, `a → b → c` 를 원소별로 평가하고
Predicted/Known 에서 동일 길이 리스트를 추출하여 element-wise 비교.

### 2.4 라벨 우변 값 사용 (label_eq)
`mu = 1` 처럼 좌변이 단순 식별자면 우변 값을 평가 대상으로 사용.

### 2.5 비-수식 라벨 신규 상태 `NO_EXPR`
마크다운 굵게, LaTeX 잔재(`\`), 식별자(인자) 형태, `m_t/m_W` 같은 라벨/이름은
SKIP 이 아니라 별도 NO_EXPR 로 분류 (검산 대상이 아님을 명시).

### 2.6 단위 패턴 확장
`A100`, `MLA`, `S0-S5` 등 반복 출현 토큰을 단위 목록에 추가.
`(괄호 주석)` 은 선행 숫자가 있을 때만 제거 (식별자 보호).

## 3. 재실행 결과

| 지표 | 개선 전 | 개선 후 | Δ |
|------|------:|------:|--:|
| MATCH | 1044 | **1102** | +58 |
| MISMATCH | 141 | 154 | +13 |
| SKIP | 613 | **397** | **−216 (−35.2%)** |
| NO_EXPR (신규) | — | 87 | +87 |
| NO_TARGET | 572 | 630 | +58 |
| 정합률 | 88.10% | 88.02% | −0.08 pp |

총 검산 행 2370 (불변). MATCH 회귀 0 건.

### 상태 전이 (SKIP → ?)
- SKIP → NO_EXPR : 83 (라벨/이름으로 재분류)
- SKIP → NO_TARGET : 75 (수식은 평가됐으나 비교 대상 부재)
- SKIP → MATCH : 44 (신규 정합)
- SKIP → MISMATCH : 13 (신규 불일치, A 에이전트 후속 검토 대상)
- 잔존 SKIP : 397

## 4. 잔존 SKIP 397건 분석

| 분류 | 건수 | 처리 방향 |
|------:|-----:|----------|
| `other` (자유 산문/특수 표기) | 301 | 본문 표 작성 가이드라인 보강 필요 |
| `num_unit` | 70 | 값-셀이 수식 열에 잘못 들어간 케이스 — `extract_evidence_tables` 컬럼 매핑 정밀화 필요 |
| `unicode_sub_sup` | 13 | 복합 윗첨자 (`10⁻ˢᵒᵖᶠʳ`) — 문자 윗첨자까지 매핑 확장 |
| `list_comma` | 5 | 함수 인자와 리스트 모호성 |
| 기타 | 8 | — |

## 5. 후속 권고

1. **컬럼 매핑 정밀화**: `extract_evidence_tables` 가 "Predicted/Known" 컬럼 값을 "Expression" 열로 오인하는 사례 (≈70건). 헤더 휴리스틱을 강화하면 num_unit 그룹 일괄 해소 가능.
2. **본문 표기 가이드**: 수식 열에는 반드시 `n=6` 정의 토큰 또는 `**` 거듭제곱만 사용. 자유 텍스트 라벨은 별도 열로 분리.
3. **A 에이전트 인계**: 신규 13건의 SKIP→MISMATCH 는 mismatch 분류 작업에 합류시킬 것.
4. **t1/CI 통합**: `bt_audit.py` 를 `tools/` 하위 정합성 스캐너로 상시화 (BT 정합성 보고서 §5.1 후속).

## 6. 변경 파일

- `shared/bt_audit.py` — 정규화 보강 + NO_EXPR 도입 + 리스트 분해
- `shared/bt_audit_result.json` — 재실행 산출물 (SKIP 397)
- `shared/bt-skip-resolution.md` — 본 보고서
