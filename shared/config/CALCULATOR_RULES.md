# Calculator Development Rules (All Repos)

> 이 파일은 TECS-L family 전체 리포에서 공유하는 계산기 개발 규칙입니다.
> 모든 리포의 CLAUDE.md에서 이 파일을 참조하세요.
> 소스 경로: `~/Dev/TECS-L/.shared/config/CALCULATOR_RULES.md`

---

## 언어 우선순위 (Language Priority)

### 1순위: HEXA — 성능 문제 예상시 반드시 HEXA 우선

적용 기준:
- 반복 > 10,000회
- 실행 시간 > 10초 예상
- 조합 공간 > 10^6
- Monte Carlo 샘플 > 100,000
- Grid scan, brute-force search, 행렬 연산
- 대규모 데이터 파싱/변환

HEXA 프로젝트 구조 (리포별):
```
  nexus:           shared/blowup/**/*.hexa (R14 카테고리 구조, 2026-04-11 refactor)
  TECS-L:           mk2_hexa/native/*.hexa
  n6-architecture:  mk2_hexa/native/*.hexa
  anima:            mk2_hexa/native/*.hexa
  SEDI:             mk2_hexa/native/*.hexa
```

실행 규칙:
```
  # HEXA 네이티브 (nexus — R14 카테고리)
  hexa shared/blowup/todo.hexa [project]       # 할일 엔진
  hexa shared/blowup/core/blowup.hexa <domain> # 9-phase 돌파
  hexa shared/n6/atlas_health.hexa             # atlas 헬스체크
```

### 2순위: Python — 단순 검증, 시각화, 프로토타입

적용 기준:
- 단일 공식 평가, 오차 계산, 테이블 출력
- 외부 데이터 fetch, API 호출
- NumPy/SciPy로 충분한 경우
- 빠른 프로토타입
- 시각화/matplotlib 필요시

---

## 판단 플로우차트

```
  새 계산기 필요?
    ├─ 반복 > 10K or 실행 > 10s or 조합 > 10^6?
    │   └─ YES → HEXA 우선 개발
    │         └─ mk2_hexa/native/<name>.hexa
    └─ NO → Python 개발
          ├─ TECS-L: calc/<name>.py
          ├─ n6-architecture: tools/<name>.py
          └─ 기타: tools/<name>.py
```

---

## 계산기 레지스트리 동기화

모든 계산기는 자동 스캔됩니다:
```bash
  cd ~/Dev/TECS-L
  python3 .shared/scan-calculators.py          # 스캔 (JSON 출력)
  bash .shared/scripts/sync-calculators.sh             # README 동기화
```

지원 파일 형식:
- `*.py` — Python 계산기 (docstring에서 설명 추출)
- `*.hexa` — HEXA 계산기 (헤더 주석에서 설명 추출)

HEXA 파일은 모듈명이 계산기 이름이 됩니다:
```
  mk2_hexa/native/pure_math.hexa  →  이름: "pure_math"
  mk2_hexa/native/classify.hexa   →  이름: "classify"
```

---

## HEXA 계산기 작성 템플릿

```hexa
// Calculator Name — One-line description for registry
// ====================================================
// Detailed description here.
//
// Run: nexus mk2 run <name>
// Usage: nexus mk2 run <name> [--flag1] [--flag2]

module <name>

import constants
import pure_math

fn main() {
    // ... implementation
}
```

## Python 계산기 작성 템플릿

```python
#!/usr/bin/env python3
"""Calculator Name — One-line description for registry.

Usage:
  python tools/<name>.py [--flag1] [--flag2]
"""
```

---

## 현재 HEXA 계산기 목록 (2026-04-06)

| 리포 | 이름 | 설명 |
|------|------|------|
| nexus | mk2_hexa/native/ | 통합 HEXA 엔진 (classify, pure_math, grading, cycle) |
| nexus | constants.hexa | n=6 상수 테이블 + smooth-class 엔진 |
| nexus | alien_index.hexa | 외계인 지수 (d, r) 판정 |
| nexus | gate.hexa | 돌파 게이트 + 검증 파이프라인 |
| nexus | effects.hexa | 이펙트 시스템 (블로업/수축/창발) |
| nexus | cycle.hexa | 특이점 사이클 엔진 |
| nexus | forge.hexa | 렌즈 포지 + 자동 생성 |
