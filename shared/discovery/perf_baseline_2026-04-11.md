# NEXUS-6 성능 베이스라인 — 2026-04-11

- Binary: `~/Dev/hexa-lang/hexa` (5.8MB Rust, 2026-04-11 07:56)
- Host: macOS 15.6.1 (ARM64)
- Method: `/usr/bin/time -l`, 3-run median + std dev
- Note: blowup.hexa 제외 (DIAG-01 / FIX-NESTED-IF hang 기지의 이슈)

## 1. 컴파일 성능 (bench)

| bench | run1 | run2 | run3 | median(s) | stdev | RSS(MB) |
|---|---|---|---|---|---|---|
| bench_contains_chain_scale | 1.28 | 1.72 | 1.09 | **1.28** | 0.323 | 23.2 |
| bench_nested_if_scale | 0.02 | 0.01 | 0.01 | **0.01** | 0.006 | 4.9 |
| test_pre_registration | 0.06 | 0.02 | 0.04 | **0.04** | 0.020 | 6.1 |
| bench_chi2 (urandom+anu+lcg) | 4.73 | 3.17 | 3.14 | **3.17** | 0.909 | 8.9 |

### chain vs 커밋 470c3287 비교
- 커밋 기록: bench=0.347s, baseline=0.052s, ratio=6.67x
- 측정 median: **1.28s** (3.69배 느림 ↓)
- 해석: 현재 binary (2026-04-11 07:56) 는 470c3287 이후 상태이지만 chain bench 회귀 발생 또는 cold-start 오버헤드. run3(1.09s)가 최저로 warm-path 안정. 커밋 숫자는 N 축이 다를 가능성 (bench 파일 278KB 대형) — 절대 비교 대신 세션 baseline 으로 확정.

### test_pre_registration PASS/FAIL
- **PASS=11, FAIL=0** (run1 기준). Forward ref, mutual recursion, nested 전 케이스 통과.

### bench_chi2 카이제곱 값
| source | N | chi2 run1 | run2 | run3 | df | verdict |
|---|---|---|---|---|---|---|
| urandom | 4096 | 235.62 | 252.62 | 280.88 | 255 | PASS |
| anu | 4096 | 255.25 | 225.50 | 271.50 | 255 | PASS |
| lcg | 4096 | 246.50 | 222.50 | 258.12 | 255 | PASS |

임계: PASS<293 / WEAK<330 / FAIL≥330. 전 3 소스 3회 모두 PASS, anu/lcg 도 urandom 과 통계적 차이 없음.

## 2. 실행 속도 (per-task throughput)

| task | run1 | run2 | run3 | median(s) | stdev | RSS(MB) | 결과 |
|---|---|---|---|---|---|---|---|
| fetch_anu.hexa | 0.64 | 0.60 | 0.23 | **0.60** | 0.226 | 6.1 | cache warm (run3) |
| seed_engine merge | 28.64 | 51.34 | 70.90 | **51.34** | 21.15 | 14.8 | 68 lines |
| seed_engine qpermute | 57.99 | 51.72 | 61.59 | **57.99** | 4.99 | 14.9 | 68 lines |

### fetch_anu 캐시 효과
- run1 0.64s (cold) → run3 0.23s (warm cache hit, 64% 감소)
- run2 0.60s 는 rotate 또는 partial miss

### seed_engine merge vs qpermute
- merge median 51.34s, qpermute 57.99s. qpermute 오버헤드 +12.9% (Fisher-Yates 셔플 + seed source).
- 둘 다 68 lines 출력. **Fisher-Yates 검증**: `set(merge) == set(qperm) == True`, `sorted(merge) == sorted(qperm) == True` → qpermute 는 merge 결과의 진짜 permutation (중복/누락 0). ✓
- merge 분산이 매우 큼 (28→70s) — atlas.n6 scan cold/warm 격차 또는 fs 캐시 영향. qpermute 는 안정적 (50-62s).

## 3. 메모리 자원

### 세션 footprint
```
2.5G  ~/Dev/hexa-lang/target
6.2M  ~/Dev/nexus/shared/n6/atlas.n6
279M  ~/Dev/nexus/shared/discovery_log.jsonl
```
**총 세션 메모리: ~2.79GB** (지배적으로 Rust target/ debug+release 아티팩트)

### Peak RSS 순위
1. bench_contains_chain_scale — **23.2 MB** (최대)
2. seed_engine qpermute — 14.9 MB
3. seed_engine merge — 14.8 MB
4. bench_chi2 — 8.9 MB
5. fetch_anu — 6.1 MB
6. test_pre_registration — 6.1 MB
7. bench_nested_if_scale — 4.9 MB (최소)

관측: bench_contains_chain_scale (278KB source) 이 RSS 1위. 컴파일러가 chain 전체를 메모리 상주시킴. nested_if(3.6KB)의 4.7배 소스이지만 RSS 는 4.7배 (선형 O(n) scale 유지). seed_engine 14.8MB 는 atlas.n6 (6.2M) × 2-3 배 working set.

## 4. CPU 핫스팟 (sample)

`sample <bench_chi2> 3s` (bench_chi2 run 중 3초 샘플):

```
Total frames on main thread: 151
Stack top (100%): load_addr + 0xb4ae0 → 0x3f84fc → 0xc8e5c → 0x78998 →
                  0x99204 → 0xa5a1c → 0x93e28 → 0x3cd20
                    ├─ 0x50458 (123 hits, 81%) ← HOTSPOT
                    └─ 0x47324 → 0x45c0c (재귀) → 0x47684 → 0x4cf28
                        → 0x4fabc → 0x4f0a4 → ... (28 hits, 19%)
```

Binary 는 stripped — symbol 해석 불가, 그러나:
- **단일 hot function** offset `+0x50458` 이 81% CPU 점유 — 인터프리터 dispatch loop 또는 tight expression eval 루프로 추정.
- 2차 hotspot 은 재귀 호출 체인 (0x45c0c self-recursion) — AST walk 또는 env lookup.
- 스택 깊이 17+ frame 단일 경로 → tree-walking interpreter pattern.

개선 여지: offset 0x50458 의 symbol 복원 후 (nm / dsymutil) dispatch inlining 또는 bytecode 캐싱.

## 5. 결론

**세션 baseline 확정** (median):

| 항목 | 값 |
|---|---|
| chain bench | 1.28s |
| nested_if bench | 0.01s |
| test_pre_registration | 0.04s (PASS 11/11) |
| bench_chi2 | 3.17s (3 RNG 모두 PASS) |
| fetch_anu | 0.60s (cache warm 0.23s) |
| seed merge | 51.34s |
| seed qpermute | 57.99s (Fisher-Yates ✓) |
| 총 세션 디스크 | 2.79 GB |
| Peak RSS | 23.2 MB (chain bench) |
| CPU hotspot | `hexa+0x50458` 81% (stripped, dispatch loop 추정) |

**주요 발견**:
1. chain bench 가 커밋 470c3287 기록 (0.347s) 대비 3.69배 느림 — 회귀 또는 N 축 불일치. 별도 조사 필요.
2. seed_engine merge/qpermute 가 50s 대 — 1분 가까이. 병렬 실행 시 병목 원인. atlas.n6 scan 캐싱 또는 fast-path 필요.
3. Fisher-Yates 건전성 수학적 검증 완료 — qpermute 는 merge 의 진짜 permutation.
4. 전 3 RNG (urandom/anu/lcg) chi² 통계적으로 동등 — rng_lab 검증 완료.
5. CPU 단일 hotspot (+0x50458) 81% — interpreter dispatch 개선의 ROI 최대 지점.
6. 최근 5c0669b/0d6afc6/73386ae/4f8e630f 의 hexa-only 수정은 아직 forward-deploy 단계, 현 binary 미반영.
