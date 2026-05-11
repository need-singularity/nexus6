# shared/n6/constants/ — fallback note

**Status**: fallback 모드 (raw#10 proof-carrying).

이 디렉토리는 `~/core/canon/experiments/monte-carlo-v9.hexa` 의
`load_const_digits(name)` 런타임 로더가 조회하는 canonical 위치입니다.

## Fallback 동작

파일 부재 시 consumer(monte-carlo-v9)는 내장 하드코드 `PI_300` / `E_300` 로
graceful fallback 합니다 — raw 위반 아님 (degraded mode 명시).

## 확장 시

필요한 파일명:
- `pi.txt`  — π 자릿수 (300+ digits)
- `e.txt`   — e 자릿수 (300+ digits)

파일 추가 시 consumer 가 자동으로 디스크 버전을 우선 사용합니다.

## R-refs

- raw#10: proof-carrying (fallback 존재/모드 명시)
- canonical relocation: TODO — `~/` → `$NEXUS/n6/constants/` 이전 예정
