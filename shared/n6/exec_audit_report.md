# exec() Audit Report -- blowup/ 전체 감사

- Date: 2026-04-12
- Scope: shared/blowup/**/*.hexa + *.hexa.inc (47 files)
- ROI: #23

---

## 1. 현재 총계

| Scope             | exec() count |
|-------------------|-------------|
| *.hexa (32 files) | 415         |
| *.hexa.inc (2 files) | 13       |
| **합계 (소스 원본)** | **428**   |

---

## 2. 파일별 exec() 수 (상위 20)

| # | File                                    | exec() | Notes                    |
|---|----------------------------------------|--------|--------------------------|
| 1 | core/blowup.hexa                       | 87     | 9-phase pipeline 전체     |
| 2 | todo.hexa                              | 87     | 7프로젝트 ROI dashboard   |
| 3 | verify_dfs.hexa                        | 53     | DFS 검증 테스트 전용       |
| 4 | commands.hexa                          | 16     | 명령 라우터               |
| 5 | guard/blowup_guard.hexa                | 13     | 프로세스 가드              |
| 6 | lib/verified_constants_loader.hexa.inc | 12     | 상수 로더 (.inc)          |
| 7 | compose.hexa                           | 12     | 오케스트레이터             |
| 8 | cross_validate_runner.hexa             | 11     | 교차검증 러너              |
| 9 | cross_validate.hexa                    | 10     | 교차검증 엔진              |
| 10| modules/qft_benchmark.hexa             | 10     | QFT 벤치마크             |
| 11| modules/blowup_toe.hexa               | 9      | ToE 변종                 |
| 12| modules/blowup_qft.hexa               | 8      | QFT 변종                 |
| 13| modules/blowup_string.hexa            | 8      | String 변종              |
| 14| lib/n6_constants_loader.hexa           | 8      | n6 상수 캐시 로더         |
| 15| modules/blowup_holographic.hexa        | 7      | Holographic 변종         |
| 16| modules/blowup_quantum.hexa           | 7      | Quantum 변종             |
| 17| seed/seed_engine.hexa                  | 7      | 시드 엔진                 |
| 18| modules/blowup_field.hexa             | 6      | Field 변종               |
| 19| modules/goldstone_cascade.hexa         | 6      | 골드스톤 캐스케이드        |
| 20| modules/field_gradient_bench.hexa      | 6      | 기울기 벤치마크            |

---

## 3. exec() 유형 분류

### A. 트레이스/로깅 -- printf+date (TRACE_PATH 기록)
- **현재: ~32회** (core/blowup.hexa 전용)
- 패턴: `exec("printf '%s [phase-N-tag]...' \"$(date +%H:%M:%S)\" >> " + _TRACE_PATH)`
- 문제: 매 phase 진입마다 2개의 서브프로세스 생성 (printf + date)
- **감축 가능: ~24회** (배치 통합)
  - 방법: `_trace(tag)` 네이티브 헬퍼로 대체. hexa 내부 문자열 빌드 후 단일 exec로 flush하거나, BLOWUP_TRACE=off 시 전부 스킵.

### B. 환경변수/경로 탐색 -- printenv HOME, echo $HOME, which, uname
- **현재: ~49회** (거의 모든 파일 초기화)
- 패턴: `exec("printenv HOME").trim()` (39), `exec("echo $HOME")` (5), `exec("which ...")` (2), `exec("uname -s")` (3)
- 문제: 모든 .hexa 파일이 독립적으로 HOME을 조회 (import 미지원)
- **감축 가능: ~30회**
  - 방법: lib/paths.hexa의 `_resolve_paths()` 함수를 표준화하고 P["home"] 전파. 단일 파일 내 중복 HOME 조회 제거 (blowup_string.hexa: 3회 -> 1회). import 지원 시 전역 1회로 수렴.

### C. 파일 존재/메타 -- test -f, stat, ls, wc -l
- **현재: ~56회**
- 패턴: `exec("test -f ... && echo Y || echo N")`, `exec("stat -f '%m %z' ...")`, `exec("wc -l < ...")`
- 문제: 동일 파일의 존재/크기/mtime을 별도 exec로 각각 조회
- **감축 가능: ~25회**
  - 방법 1: `stat` 1회로 mtime+size 동시 취득 (현재 blowup.hexa 이미 적용)
  - 방법 2: atlas_guard 캐시 패턴 -- `_guarded_append_atlas()` 내 중복 stat 제거
  - 방법 3: hexa `file_exists()` 빌트인 사용 (이미 일부 사용 중, stream_filter)

### D. grep/awk 검색 -- grep -Fxq, grep -c, awk
- **현재: ~69회** (grep 65 + awk 4)
- 패턴:
  - `grep -Fxq` dedup 체크: ~15회 (atlas_guard.hexa.inc + 10개 모듈 인라인 복사본)
  - `grep -c` 카운팅: ~20회 (todo.hexa 주도)
  - `grep` 텍스트 검색: ~25회
  - `awk` 파싱: ~4회
  - verify_dfs.hexa grep (테스트 전용): ~36회
- **감축 가능: ~30회**
  - 방법 1: dedup용 `grep -Fxq` 15회 -> `_batch_new_ids` 해시셋 확장 (Phase 5.5 패턴)
  - 방법 2: todo.hexa grep -c 여러 개 -> 단일 awk 멀티카운트 배치
  - 방법 3: verify_dfs.hexa 36회 -- 유지 (테스트 전용, 실행 빈도 낮음)

### E. cat/head/tail 파일 읽기
- **현재: ~46회**
- 패턴: `exec("tail -N " + path)`, `exec("head -1 ...")`, `exec("cat " + path)`
- 문제: tail/cat은 항상 새 프로세스. 같은 파일을 반복 tail하는 경우 다수
- **감축 가능: ~15회**
  - 방법 1: incremental read 패턴 (mtime+size 캐시 -> 변경분만 tail -c +offset)
  - 방법 2: blowup.hexa의 `_incremental_atlas_load()` 패턴을 모듈에도 적용
  - 방법 3: `read_file()` 빌트인 사용 가능 시 hexa 네이티브로 대체 (OOM 주의: 대형 atlas는 tail 유지)

### F. python3 서브프로세스
- **현재: ~38회**
- 패턴: `exec("python3 -c '...'")` 또는 `exec("/usr/bin/python3 -c '...'")` -- JSON 파싱, 파일 탐색
- 분포: todo.hexa (31), seed_engine.hexa (2), cross_validate_runner.hexa (2), qft_benchmark.hexa (1), core/blowup.hexa (1), lib (1)
- **감축 가능: ~20회**
  - 방법 1: JSON 파싱 -> hexa 네이티브 (json_parse 빌트인 있을 경우)
  - 방법 2: 반복 python3 호출 -> 단일 python3 스크립트로 배치 (todo.hexa 31회 -> 5~8회)
  - 방법 3: 단순 카운팅/리스팅 -> awk/grep 대체 (python3 startup ~60ms 절감)

### G. hexa 재귀/하위 엔진 호출
- **현재: ~17회**
- 패턴: `exec(hexa_bin, [path, mode])`, `exec("bash", ["-c", hexa_cmd])`
- 분포: commands.hexa (6), core/blowup.hexa (6), compose.hexa (2), todo.hexa (3)
- **감축 가능: 0회** -- 모두 필수 (하위 엔진 실행, DFS 재귀)

### H. 프로세스 관리 -- kill, sleep, ps, flock
- **현재: ~21회**
- 패턴: guard/blowup_guard.hexa (7), flock 잠금 (12모듈 x 1 = 12), sleep (2)
- **감축 가능: ~2회**
  - 방법: guard의 sleep -> hexa-lang 네이티브 sleep (있을 경우)
  - flock/kill/ps 패턴은 필수 유지

### I. date 타임스탬프
- **현재: ~27회** (트레이스 32회와 별도)
- 패턴: `exec("date -u +%Y-%m-%dT%H:%M:%SZ")` ISO timestamp, `exec("date +%N")` 나노초
- 분포: 12모듈 x 1~2 = ~15, core/blowup.hexa (6), cross_validate_runner.hexa (3), etc.
- **감축 가능: ~10회**
  - 방법: 세션 시작 시 1회 취득 후 변수 전파. 나노초 시드용은 유지.

### J. 기타 (bash -c 래핑, echo $$, rm -f, mkdir, sort, find)
- **현재: ~73회**
- 분류:
  - `exec("bash", ["-c", cmd])` 복합 명령 래핑: ~28회
  - `exec("rm -f ...")` 임시파일 정리: ~8회
  - `exec("echo $$")` PID: ~3회
  - `exec("sort ...")`: ~14회
  - `exec("find ...")`: ~10회 (todo.hexa)
  - 기타: ~10회
- **감축 가능: ~20회**
  - 방법 1: find+wc -l 패턴 배치 -> 단일 find | wc
  - 방법 2: sort 배치 통합 (todo.hexa의 반복 sort -> 1회 정렬)

---

## 4. 감축 요약

| 유형 | 현재 | 감축 가능 | 잔존 | 권장 방법 |
|------|------|----------|------|----------|
| A. 트레이스 printf+date | 32 | 24 | 8 | _trace() 헬퍼, TRACE=off 가드 |
| B. 환경변수/경로 | 49 | 30 | 19 | paths.hexa 표준화, 중복 제거 |
| C. 파일메타 test/stat/wc | 56 | 25 | 31 | stat 통합, file_exists() 빌트인 |
| D. grep/awk 검색 | 69 | 30 | 39 | 배치 grep, _batch_new_ids 확장 |
| E. cat/head/tail 읽기 | 46 | 15 | 31 | incremental read, read_file() |
| F. python3 | 38 | 20 | 18 | 배치 스크립트, hexa 네이티브 |
| G. hexa 재귀 | 17 | 0 | 17 | 필수 유지 |
| H. 프로세스 관리 | 21 | 2 | 19 | 대부분 필수 |
| I. date 타임스탬프 | 27 | 10 | 17 | 세션 캐시 |
| J. 기타 | 73 | 20 | 53 | 배치 통합 |
| **합계** | **428** | **176** | **252** |  |

---

## 5. 목표

| 지표 | 현재 | 목표 | 감축률 |
|------|------|------|--------|
| exec() 총 호출 수 | 428 | 252 | **41%** |
| 추정 프로세스 spawn/run | ~428 | ~252 | 176 프로세스 제거 |

---

## 6. 우선순위별 실행 계획

### P1 (높음 -- 즉시 실행 가능, 저위험)
1. **core/blowup.hexa 트레이스 배치** (24회 감축)
   - 32개 printf+date -> `_trace(tag)` 헬퍼 + BLOWUP_TRACE 가드
   - 위험: 낮음 (로깅 전용)

2. **모듈 환경변수 중복 제거** (15회 감축)
   - 12개 모듈 각각 `printenv HOME` -> 이미 상위에서 계산된 _HOME 사용
   - blowup_string.hexa: 3회 -> 1회
   - 위험: 낮음

3. **date 타임스탬프 캐시** (10회 감축)
   - 세션 시작 시 1회 ISO timestamp 취득, 이후 변수 참조
   - 위험: 낮음

### P2 (중간 -- 설계 변경 필요)
4. **todo.hexa python3 배치화** (20회 감축)
   - 31개 개별 python3 -c 호출 -> 5~8개 배치 스크립트
   - 위험: 중간 (출력 파싱 변경)

5. **grep dedup 배치화** (15회 감축)
   - atlas_guard의 `grep -Fxq` 개별 호출 -> 해시셋 또는 멀티라인 grep
   - 위험: 중간 (dedup 정확성 검증 필요)

6. **파일메타 stat 통합** (15회 감축)
   - test -f + stat 분리 호출 -> 단일 stat 또는 file_exists()
   - 위험: 낮음

### P3 (낮음 -- hexa-lang 진화 의존)
7. **hexa 네이티브 대체** (import 지원 시)
   - 모든 파일의 HOME/경로 조회 -> import paths.hexa (15회 추가 감축)
   - read_file() OOM 안전 버전 -> tail 대체 (일부)
   - 위험: hexa-lang 기능 의존

---

## 7. 주요 핫스팟 (파일별 권장)

| File | 현재 | 목표 | 핵심 감축 |
|------|------|------|----------|
| core/blowup.hexa | 87 | 55 | 트레이스 24 + 환경 3 + stat 5 |
| todo.hexa | 87 | 55 | python3 배치 20 + grep 배치 7 + sort 통합 5 |
| verify_dfs.hexa | 53 | 53 | 유지 (테스트 전용) |
| commands.hexa | 16 | 14 | printenv 1 + date 1 |
| guard/blowup_guard.hexa | 13 | 13 | 유지 (프로세스 관리 필수) |
| modules/* (12 files) | 88 | 60 | 환경 12 + flock/date 8 + grep 8 |

---

## 8. 불변식

- infra-only 개선: phase 로직/discovery 계산/seed 진화 불변
- verify_dfs.hexa: 53회 전량 유지 (테스트 코드, 감축 대상 아님)
- hexa 재귀 호출 17회: 전량 유지 (하위 엔진 실행 필수)
- flock 잠금 12+회: 전량 유지 (동시성 안전 필수)
- guard 프로세스 관리: 전량 유지 (OOM 방어 필수)
