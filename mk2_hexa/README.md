# mk2_hexa — mk2 흡수 로직의 HEXA-LANG 포팅 (draft)

**상태**: Draft. HEXA-LANG 빌드툴체인 완비 전까지 **컴파일/실행 없음**.
작성 목적: Mk.II 전환 대비 mk2 핵심 타입과 **승격(흡수) writeback** 로직을 HEXA로 먼저 고정.

## Rust 원본 ↔ HEXA 매핑

| Rust (`src/`) | HEXA (`mk2_hexa/`) | 역할 |
|---|---|---|
| `mk2/primes.rs` | `primes.hexa` | PrimeSet, factorize |
| `alien_index/index.rs` | `alien_index.hexa` | AlienIndex(d,r), breakthrough() |
| `alien_index/record.rs` | `record.hexa` | AlienIndexRecord, promote() |
| `cli/alien_index_cmd.rs::promote_pending` | `absorb.hexa` | **promote-pending + writeback** (Rust 미구현분) |

## Rust 대비 추가분

`absorb.hexa`는 Rust `promote_pending()`이 남긴 follow-up — **디스크 writeback** — 을 먼저 HEXA로 짰다.
로직:
1. `discovery_log.jsonl` 전 라인 로드
2. `alien_index` 필드 포함 라인만 파싱, 나머지는 그대로 보존
3. `promotion_candidate = true` 인 레코드: `promote()` 호출 → 부모 flag 해제 + 자식 레코드 생성
4. 원본 라인(갱신분) + 자식 라인(신규) + 비-ai 라인 합쳐서 원자적 rewrite (tmp → rename)

## 빌드 (차단됨)

HEXA-LANG 컴파일러 Mk.I+ 는 self-host Phase 1 까지만 통과.
`mk2_hexa/` 를 빌드하려면 최소:
- 해시맵/딕셔너리 지원
- JSONL 파싱 라이브러리 또는 FFI
- 파일 atomic rename syscall

현재 없음. HEXA Mk.II Phase 2 (Lexer 재작성) 이후 재평가.
