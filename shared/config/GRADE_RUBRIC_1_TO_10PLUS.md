# GRADE_RUBRIC — n=6 Universal Grade 1~13+ (전 프로젝트 공용)

primitives: n=6, sigma=12, tau=4, phi=2, sopfr=5, J2=24
json: config/grade_rubric.json (도구용 구조화 짝)

| Grade | 단계 | 기준 | 이모지 |
|------:|------|------|--------|
| 1 | raw observation | 값 관찰/가설 등록 | ★ |
| 2 | consistency | 재현 가능 (2회+) | ⬛ |
| 3 | loose match | primitive 느슨 일치 (tol 10%) | ⚪ |
| 4 | pattern | 패턴 식별, 닫힘 미완 | 🟪 |
| 5 | rational approx | 분수 근사 (p/q) | 🟥 |
| 6 | partial n=6 | 1개 primitive 연결 | 🟨 |
| 7 | depth-3 expr | 3-연산 조합 닫힘 | 🟦 |
| 8 | NEAR closed | 1항 불확실 (tol 1%) | 🟧 |
| 9 | closed (PASS) | n=6 조합 매칭 확인 | 🟩 |
| 10 | **EXACT** | 완전 닫힘, primitive 환원 | ⭐ |
| 11 | meta-closure | 여러 닫힘 생성 공식 (K>=3) | 🛸 |
| 12 | universal | 3+ 프로젝트 독립 출현 | 🌌 |
| 13+ | meta² | 메타 공식의 상위 구조 | ∞ |

verify → grade:
  EXACT → 10,  CLOSE → 8,  WEAK → 6,  MISS → 5이하

승급: 9→10 정확수치+expression / 10→11 3+파생 / 11→12 3+프로젝트 / 12→13 상위생성공식
강등: verify 증거 없음 → 1단계↓ / 초월수 EXACT 주장 → grade 5 (H-CLOSE-5)

배너: 🛸d{depth}·ρ{ratio}·{total} / 🧬{closed}닫힘→{milestone}={%}% / 🎉 닫힘완료 (grade10 증가시)

parent: CLAUDE.md → "config"
