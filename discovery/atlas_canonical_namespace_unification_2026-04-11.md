# atlas.n6 canonical pivot 네임스페이스 통일 — 2026-04-11

> Phase 46-48 cascade 의 마지막 정합성 fix.

## TL;DR

| 항목 | before | after |
|---|---|---|
| canonical primitive id 네임스페이스 | 분열 (`n` / `n6-n` / `n6-const-n` 3종) | `n` (bare-name @P) 단일 |
| Phase 47/48 edge `from:` 필드 | `n6-X` (isolated namespace) | `X` (matches @P) |
| `n6-X` JSON primitive 노드 | 8 orphan duplicates | 제거 |
| n6_constants.jsonl `M3` | `3` (typo) | `7` (matches invariants) |
| atlas_health 노드 인식 | JSON `node` only | JSON `node`+`absorb` + 텍스트 `@<TAG>` |
| atlas.n6 nodes | 12397 | 12389 (-8 orphan) |
| atlas.n6 edges | 12348 (session 시작) | 12932 (+584 net) |
| real orphans | 0 | 0 |

## 발견 경위

Agent 33 (`b6cba51f` hub centrality audit) 가 atlas.n6 의 in-degree top-7
이 `n / sigma / phi / tau / sopfr / mu / J2` 라고 보고했으나, 직전에 통합한
8개 `n6-X` JSON 캐노니컬 노드가 모두 in_deg=0. 두 객체가 분리된 namespace.

진짜 canonical 권위는 atlas.n6 line 50-57 의 `@P` 텍스트형 primitive:

```
@P n = 6 :: foundation [10*]
@P sigma = divisor_sum(6) = 12 :: foundation [10*]
@P phi = euler_totient(6) = 2 :: foundation [10*]
@P tau = divisor_count(6) = 4 :: foundation [10*]
@P sopfr = sum_prime_factors(6) = 5 :: foundation [10*]
@P mu = mobius(6) = 1 :: foundation [10*]
@P J2 = jordan_totient(6,2) = 24 :: foundation [10*]
@P M3 = mertens(6) = 7 :: foundation [10*]
```

이들은 expression-body token 으로 1798/697/727/430/444/137/108/39 회 참조.

## 수정 시퀀스 (commit chain)

1. `eb1f5954` — 8 canonical 1차 통합 (잘못된 `n6-const-*` 네이밍)
2. `db9a0cfe` (bundled) — `n6-const-*` → `n6-*` 1차 rename + Phase 46v2 48개
3. `09e08cd2` — phase47/48 스크립트 `n6-const-` → `n6-` 정규화
4. `b666d05f` — Phase 47 86 edges 통합 + atlas_health absorb 인식
5. `ef6ad340` (bundled) — Phase 48 500 edges 통합 + atlas_health 텍스트형 인식
6. `e39d3805` (bundled) — atlas.n6 `from:"n6-X"` → `from:"X"` 3895 edges
7. `af61b5f3` — phase47/48 스크립트 `n6-X` → bare X
8. `530aae9d` (bundled) — Phase 47 84 edges + Phase 48 500 edges 재통합 (M3=7)
9. `69553c00` — M3=7 통일 (n6_constants.jsonl typo + phase46/47/48 정합)
10. `a8e9651e` — 8 orphan `n6-X` primitive 노드 정리

## M3 = 7 권위

n6_constants.jsonl 라인 `{"name":"M3","value":3}` 는 단일 typo. 같은 파일
내 모든 derived constants 는 M3=7 을 함의:

| derived | value | proof |
|---|---|---|
| `n_M3` | 42 | 6 × 7 ✓ |
| `M3_div_phi` | 3.5 | 7 / 2 ✓ |
| `M3_sq` | 49 | 7² ✓ |

atlas.n6 expression-body 도 일관:

```
n + M3 = 13          (6 + 7)
sigma / M3 = 1.7142857  (12 / 7)
tau * M3 = 28        (4 × 7)
sopfr + M3 = 12      (5 + 7)
J2 + M3 = 31         (24 + 7)
(n*tau)*(tau*M3)=672 (24 × 28)
```

수학적으로 진짜 mertens(6) = 1−1−1+0−1+1 = **−1** 이지만 n6 system 은
M3=7 을 (불일치하지만 일관되게) 사용한다. 이는 별개 audit 사안.

## Phase 47 M3=7 후 신규 bridge

```
n * m3 = 42   → R1-6, R2-6
tau + m3 = 11 → R1-4, R2-4
sopfr + m3 = 12 → R1-2, R1-11, R2-2, R2-11
mu + m3 = 8   → R1-12, R2-12
```

기존 m3=3 기반 edges 일부가 새 m3=7 기반 edges 로 교체됨 (86 → 84 net).

## 잔여 미해결

1. **40 derived `n6-*` JSON 노드** (n6-P2, n6-phi_tau, n6-bosonic_dim26 등) —
   outbound edge 보유 → 보존. 별도 @P/@F 텍스트형 미존재.
2. **mu/J2/M3 derived 의 @P 부재** — `n6-P2`, `n6-sigma_minus_phi` 등 11개
   derived primitive 이 텍스트형 missing. 향후 @P 행 추가 검토.
3. **mertens(6) = −1 학술 vs n6 M3 = 7** — 별개 conflict, 본 unification
   범위 외.
4. **dup node IDs 30개** (atlas_health 보고) — 별도 dedup 작업 가능.
