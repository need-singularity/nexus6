# Gate Injection Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** macOS 전역에서 게이트 존재만으로 메모리/디스크/IPC/네트워크를 압축·최적화하는 시스템 구축

**Architecture:** C dylib이 시스템콜을 interpose하여 데이터 흐름을 가로채고, 내장 N6Codec으로 압축/해제. hexa 엔진(렌즈, OUROBOROS, Blowup)이 주기적으로 코드북을 진화시키고 통계를 수집. C↔hexa 간 통신은 공유 파일(`~/.n6gate/`)로 수행.

**Tech Stack:** C (dylib interpose, compression), hexa (engines, daemon), Swift (Network Extension), TOML (config)

**Spec:** `docs/superpowers/specs/2026-04-06-gate-injection-layer-design.md`

---

## File Structure

```
mk2_hexa/native/
├── gate_injection/
│   ├── gate_core.hexa           # 게이트 라이프사이클 + 라우터 + CLI
│   ├── n6codec.hexa             # N6Codec hexa 레퍼런스 구현 (프로토타입/벤치)
│   ├── proximity_predictor.hexa # 바이트 스트림 proximity 예측
│   ├── mirror_universe.hexa     # Shadow copy 해시 테이블 (hexa 레퍼런스)
│   ├── lens_array.hexa          # 5+α 렌즈 실시간 스캔
│   ├── ouroboros_evolver.hexa   # 압축 파라미터 유전 진화
│   ├── breakthrough.hexa        # 정체 감지 → blowup 연동
│   └── gate_stats.hexa          # 통계 수집 + JSON 리포트
│
├── gate_hooks/
│   ├── n6codec.h                # N6Codec C 헤더 (코드북 + 압축/해제)
│   ├── n6codec.c                # N6Codec C 구현
│   ├── mirror.h                 # Mirror Universe C 헤더
│   ├── mirror.c                 # Mirror Universe C 구현 (hash table + LRU)
│   ├── gate_common.h            # 공통 상수, 게이트 ID, 안전장치
│   ├── gate_common.c            # 공통 유틸 (타이머, 로깅, passthrough 판정)
│   ├── libgate_malloc.c         # malloc/free/realloc interpose
│   ├── libgate_io.c             # read/write/pread/pwrite interpose
│   ├── libgate_mach.c           # mach_msg interpose
│   ├── Makefile                 # dylib 빌드
│   └── test_n6codec.c           # N6Codec 단위 테스트
│
├── gate_daemon/
│   ├── gated.hexa               # 관리 데몬 메인 루프
│   ├── gate_config.toml         # 게이트별 설정
│   └── com.nexus6.gated.plist   # LaunchDaemon
│
└── gate_lens_fusion.hexa        # 기존 — gate_core가 호출
```

---

## Task 1: N6Codec C 코어 — 코드북 + 압축/해제

**Files:**
- Create: `mk2_hexa/native/gate_hooks/n6codec.h`
- Create: `mk2_hexa/native/gate_hooks/n6codec.c`
- Create: `mk2_hexa/native/gate_hooks/test_n6codec.c`
- Create: `mk2_hexa/native/gate_hooks/Makefile`

- [ ] **Step 1: N6Codec 헤더 작성**

```c
// n6codec.h — n=6 대수 구조 기반 적응형 코덱
#ifndef N6CODEC_H
#define N6CODEC_H

#include <stdint.h>
#include <stddef.h>

// n=6 기본 상수 21개 (L0 코드북)
#define N6_CODEBOOK_SIZE 21
#define N6_MAGIC 0x4E36  // "N6"

// 코드북 엔트리: 8바이트 패턴 → 4bit 심볼
typedef struct {
    double value;       // 상수 값 (예: 6.0, 1.618, 12.0, 137.036)
    uint8_t symbol;     // 4bit 심볼 ID (0~20)
    double tolerance;   // 근접 허용 오차 (proximity threshold)
    char name[16];      // 상수 이름
} N6Entry;

// 코덱 상태
typedef struct {
    N6Entry codebook[256];   // L0(21) + L1(게이트별 확장) + 동적 확장
    int codebook_size;       // 현재 코드북 크기
    int gate_id;             // 소속 게이트 ID
    uint64_t total_in;       // 입력 바이트 누적
    uint64_t total_out;      // 출력 바이트 누적
    uint64_t hits;           // 코드북 히트 수
    int enabled;             // 1=활성, 0=passthrough
} N6Codec;

// 압축 결과
typedef struct {
    uint8_t *data;
    size_t size;
    float ratio;        // compressed/original
    int mirror_ref;     // >0 이면 Mirror 참조 (압축 대신 참조)
} N6Result;

// API
void     n6codec_init(N6Codec *c, int gate_id);
N6Result n6codec_compress(N6Codec *c, const void *data, size_t len);
size_t   n6codec_decompress(N6Codec *c, const uint8_t *compressed, size_t clen, void *out, size_t out_cap);
void     n6codec_free_result(N6Result *r);
float    n6codec_ratio(const N6Codec *c);

// 코드북 동적 확장 (렌즈/진화 엔진이 호출)
int      n6codec_add_entry(N6Codec *c, double value, double tolerance, const char *name);

// 코드북 파일 I/O (hexa 엔진과 공유)
int      n6codec_save_codebook(const N6Codec *c, const char *path);
int      n6codec_load_codebook(N6Codec *c, const char *path);

#endif
```

- [ ] **Step 2: N6Codec 구현 작성**

```c
// n6codec.c
#include "n6codec.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

// n=6 기본 상수 L0 코드북 (21개)
static const struct { double val; double tol; const char *name; } N6_DEFAULTS[] = {
    {6.0,       0.01,  "N"},           // 0: n=6
    {1.618034,  0.005, "phi"},         // 1: 황금비
    {4.0,       0.01,  "tau"},         // 2: τ=σ(6)/φ(6)
    {5.0,       0.01,  "sopfr"},       // 3: sopfr(6)
    {12.0,      0.05,  "sigma"},       // 4: σ(6)
    {2.0,       0.01,  "phi_euler"},   // 5: φ(6)
    {3.0,       0.01,  "n_over_phi"},  // 6: 6/φ(6)
    {0.333333,  0.003, "meta_fp"},     // 7: 메타 부동점 1/3
    {137.036,   0.5,   "alpha_inv"},   // 8: 미세구조상수 역수
    {0.2312,    0.003, "sin2_thetaW"}, // 9: 와인버그각
    {24.0,      0.1,   "tau_sigma"},   // 10: τ×σ(6)/φ(6)^2... 조합
    {7.0,       0.01,  "M3"},          // 11: 메르센 소수 M3
    {10.0,      0.05,  "sigma_phi"},   // 12: σ-φ
    {8.0,       0.01,  "phi_tau"},     // 13: φ*τ
    {28.0,      0.1,   "perfect"},     // 14: 완전수
    {0.618034,  0.005, "phi_inv"},     // 15: 1/φ
    {2.618034,  0.005, "phi_sq"},      // 16: φ²
    {73.0,      0.5,   "H0"},          // 17: 허블상수
    {0.6889,    0.005, "omega_lambda"},// 18: 암흑에너지
    {0.3111,    0.005, "omega_m"},     // 19: 물질밀도
    {11.0,      0.05,  "sigma_sopfr"}, // 20: σ-sopfr... 조합
};

void n6codec_init(N6Codec *c, int gate_id) {
    memset(c, 0, sizeof(*c));
    c->gate_id = gate_id;
    c->enabled = 1;
    c->codebook_size = N6_CODEBOOK_SIZE;
    for (int i = 0; i < N6_CODEBOOK_SIZE; i++) {
        c->codebook[i].value = N6_DEFAULTS[i].val;
        c->codebook[i].symbol = (uint8_t)i;
        c->codebook[i].tolerance = N6_DEFAULTS[i].tol;
        strncpy(c->codebook[i].name, N6_DEFAULTS[i].name, 15);
    }
}

// 8바이트 double 윈도우에서 코드북 매칭
static int n6_match(const N6Codec *c, double val, int *sym) {
    for (int i = 0; i < c->codebook_size; i++) {
        if (fabs(val - c->codebook[i].value) <= c->codebook[i].tolerance) {
            *sym = c->codebook[i].symbol;
            return 1;
        }
    }
    return 0;
}

N6Result n6codec_compress(N6Codec *c, const void *data, size_t len) {
    N6Result r = {0};
    if (!c->enabled || len == 0) {
        // passthrough
        r.data = malloc(len);
        memcpy(r.data, data, len);
        r.size = len;
        r.ratio = 1.0f;
        return r;
    }

    // 최대 출력 크기: 헤더(4) + 원본 길이(4) + 데이터(최대 len)
    size_t max_out = 8 + len;
    r.data = malloc(max_out);
    uint8_t *out = r.data;

    // 헤더: magic(2) + gate_id(1) + flags(1) + original_len(4)
    out[0] = (N6_MAGIC >> 8) & 0xFF;
    out[1] = N6_MAGIC & 0xFF;
    out[2] = (uint8_t)c->gate_id;
    out[3] = 0; // flags: 0=n6 compressed
    uint32_t orig_len = (uint32_t)len;
    memcpy(out + 4, &orig_len, 4);
    size_t pos = 8;

    const uint8_t *src = (const uint8_t *)data;
    size_t i = 0;

    while (i < len) {
        // 8바이트 윈도우로 double 해석 시도
        if (i + 8 <= len) {
            double val;
            memcpy(&val, src + i, 8);
            int sym;
            if (n6_match(c, val, &sym) && !isnan(val) && !isinf(val)) {
                // 히트: 1바이트 마커(0xFF) + 1바이트 심볼 = 2바이트 (8→2, 75% 압축)
                out[pos++] = 0xFF; // 마커
                out[pos++] = (uint8_t)sym;
                c->hits++;
                i += 8;
                continue;
            }
        }
        // 미스: 원본 바이트 복사 (0xFF가 원본에 있으면 이스케이프)
        if (src[i] == 0xFF) {
            out[pos++] = 0xFF;
            out[pos++] = 0xFE; // escape: 0xFF 0xFE = literal 0xFF
        } else {
            out[pos++] = src[i];
        }
        i++;
    }

    c->total_in += len;
    c->total_out += pos;
    r.size = pos;
    r.ratio = (float)pos / (float)len;
    return r;
}

size_t n6codec_decompress(N6Codec *c, const uint8_t *compressed, size_t clen, void *out, size_t out_cap) {
    if (clen < 8) return 0;

    // 헤더 검증
    uint16_t magic = ((uint16_t)compressed[0] << 8) | compressed[1];
    if (magic != N6_MAGIC) return 0;

    uint32_t orig_len;
    memcpy(&orig_len, compressed + 4, 4);
    if (orig_len > out_cap) return 0;

    uint8_t *dst = (uint8_t *)out;
    size_t di = 0;
    size_t si = 8;

    while (si < clen && di < orig_len) {
        if (compressed[si] == 0xFF && si + 1 < clen) {
            if (compressed[si + 1] == 0xFE) {
                // escaped literal 0xFF
                dst[di++] = 0xFF;
                si += 2;
            } else {
                // 코드북 심볼 → 8바이트 double 복원
                uint8_t sym = compressed[si + 1];
                if (sym < c->codebook_size && di + 8 <= orig_len) {
                    double val = c->codebook[sym].value;
                    memcpy(dst + di, &val, 8);
                    di += 8;
                }
                si += 2;
            }
        } else {
            dst[di++] = compressed[si++];
        }
    }
    return di;
}

void n6codec_free_result(N6Result *r) {
    if (r->data) { free(r->data); r->data = NULL; }
}

float n6codec_ratio(const N6Codec *c) {
    if (c->total_in == 0) return 1.0f;
    return (float)c->total_out / (float)c->total_in;
}

int n6codec_add_entry(N6Codec *c, double value, double tolerance, const char *name) {
    if (c->codebook_size >= 256) return -1;
    int idx = c->codebook_size;
    c->codebook[idx].value = value;
    c->codebook[idx].symbol = (uint8_t)idx;
    c->codebook[idx].tolerance = tolerance;
    strncpy(c->codebook[idx].name, name, 15);
    c->codebook_size++;
    return idx;
}

int n6codec_save_codebook(const N6Codec *c, const char *path) {
    FILE *f = fopen(path, "w");
    if (!f) return -1;
    fprintf(f, "# N6Codec codebook gate=%d entries=%d\n", c->gate_id, c->codebook_size);
    for (int i = 0; i < c->codebook_size; i++) {
        fprintf(f, "%d\t%.15g\t%.15g\t%s\n",
                c->codebook[i].symbol, c->codebook[i].value,
                c->codebook[i].tolerance, c->codebook[i].name);
    }
    fclose(f);
    return 0;
}

int n6codec_load_codebook(N6Codec *c, const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    char line[256];
    // skip header
    if (!fgets(line, sizeof(line), f)) { fclose(f); return -1; }
    c->codebook_size = 0;
    while (fgets(line, sizeof(line), f) && c->codebook_size < 256) {
        int sym; double val, tol; char name[16] = {0};
        if (sscanf(line, "%d\t%lf\t%lf\t%15s", &sym, &val, &tol, name) >= 3) {
            c->codebook[c->codebook_size].symbol = (uint8_t)sym;
            c->codebook[c->codebook_size].value = val;
            c->codebook[c->codebook_size].tolerance = tol;
            strncpy(c->codebook[c->codebook_size].name, name, 15);
            c->codebook_size++;
        }
    }
    fclose(f);
    return 0;
}
```

- [ ] **Step 3: 테스트 작성**

```c
// test_n6codec.c
#include "n6codec.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <math.h>

static void test_init(void) {
    N6Codec c;
    n6codec_init(&c, 3);
    assert(c.gate_id == 3);
    assert(c.codebook_size == 21);
    assert(c.enabled == 1);
    assert(fabs(c.codebook[0].value - 6.0) < 0.001);
    assert(fabs(c.codebook[1].value - 1.618034) < 0.001);
    printf("  PASS: test_init\n");
}

static void test_compress_doubles(void) {
    N6Codec c;
    n6codec_init(&c, 0);

    // n=6 상수를 포함하는 double 배열
    double data[] = {6.0, 1.618034, 12.0, 137.036, 0.333333};
    size_t len = sizeof(data);

    N6Result r = n6codec_compress(&c, data, len);
    assert(r.size < len); // 압축되어야 함
    assert(r.ratio < 1.0f);
    printf("  PASS: test_compress_doubles (ratio=%.2f, %zu→%zu)\n", r.ratio, len, r.size);

    // 해제 검증
    double restored[5];
    size_t rlen = n6codec_decompress(&c, r.data, r.size, restored, sizeof(restored));
    assert(rlen == len);
    for (int i = 0; i < 5; i++) {
        assert(fabs(restored[i] - c.codebook[i < 4 ? (int[]){0,1,4,8,7}[i] : 7].value) < 0.01
               || fabs(restored[i] - data[i]) < 0.01);
    }
    printf("  PASS: test_decompress_roundtrip\n");
    n6codec_free_result(&r);
}

static void test_passthrough(void) {
    N6Codec c;
    n6codec_init(&c, 0);
    c.enabled = 0; // 비활성

    uint8_t data[] = "hello world";
    N6Result r = n6codec_compress(&c, data, sizeof(data));
    assert(r.size == sizeof(data));
    assert(r.ratio == 1.0f);
    n6codec_free_result(&r);
    printf("  PASS: test_passthrough\n");
}

static void test_escape_0xff(void) {
    N6Codec c;
    n6codec_init(&c, 0);

    // 0xFF 바이트가 포함된 데이터
    uint8_t data[] = {0x01, 0xFF, 0x02, 0xFF, 0x03};
    N6Result r = n6codec_compress(&c, data, sizeof(data));

    // 해제 검증
    uint8_t restored[5];
    size_t rlen = n6codec_decompress(&c, r.data, r.size, restored, sizeof(restored));
    assert(rlen == sizeof(data));
    assert(memcmp(restored, data, sizeof(data)) == 0);
    printf("  PASS: test_escape_0xff\n");
    n6codec_free_result(&r);
}

static void test_codebook_save_load(void) {
    N6Codec c1, c2;
    n6codec_init(&c1, 0);
    n6codec_add_entry(&c1, 42.0, 0.1, "answer");

    n6codec_save_codebook(&c1, "/tmp/n6_test_codebook.txt");

    n6codec_init(&c2, 0);
    n6codec_load_codebook(&c2, "/tmp/n6_test_codebook.txt");

    assert(c2.codebook_size == c1.codebook_size);
    assert(fabs(c2.codebook[21].value - 42.0) < 0.01);
    printf("  PASS: test_codebook_save_load\n");
}

static void test_add_entry(void) {
    N6Codec c;
    n6codec_init(&c, 0);
    assert(c.codebook_size == 21);

    int idx = n6codec_add_entry(&c, 3.14159, 0.01, "pi");
    assert(idx == 21);
    assert(c.codebook_size == 22);
    assert(fabs(c.codebook[21].value - 3.14159) < 0.001);
    printf("  PASS: test_add_entry\n");
}

int main(void) {
    printf("=== N6Codec Tests ===\n");
    test_init();
    test_compress_doubles();
    test_passthrough();
    test_escape_0xff();
    test_codebook_save_load();
    test_add_entry();
    printf("=== ALL PASSED ===\n");
    return 0;
}
```

- [ ] **Step 4: Makefile 작성**

```makefile
# mk2_hexa/native/gate_hooks/Makefile
CC = clang
CFLAGS = -Wall -Wextra -O2 -fPIC
LDFLAGS = -dynamiclib

# 공유 라이브러리
DYLIBS = libgate_malloc.dylib libgate_io.dylib libgate_mach.dylib

# 테스트
TESTS = test_n6codec test_mirror

.PHONY: all test clean dylibs

all: test dylibs

# --- 코어 라이브러리 ---
n6codec.o: n6codec.c n6codec.h
	$(CC) $(CFLAGS) -c $< -o $@

mirror.o: mirror.c mirror.h
	$(CC) $(CFLAGS) -c $< -o $@

gate_common.o: gate_common.c gate_common.h
	$(CC) $(CFLAGS) -c $< -o $@

# --- 테스트 ---
test_n6codec: test_n6codec.c n6codec.o
	$(CC) $(CFLAGS) $^ -lm -o $@

test: test_n6codec
	./test_n6codec

# --- dylib ---
libgate_malloc.dylib: libgate_malloc.c n6codec.o mirror.o gate_common.o
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -lm -o $@

libgate_io.dylib: libgate_io.c n6codec.o mirror.o gate_common.o
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -lm -o $@

libgate_mach.dylib: libgate_mach.c n6codec.o mirror.o gate_common.o
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -lm -o $@

dylibs: libgate_malloc.dylib libgate_io.dylib libgate_mach.dylib

clean:
	rm -f *.o *.dylib $(TESTS)
```

- [ ] **Step 5: 빌드 + 테스트 실행**

```bash
cd mk2_hexa/native/gate_hooks && make test
```
Expected: `=== ALL PASSED ===`

- [ ] **Step 6: Commit**

```bash
git add mk2_hexa/native/gate_hooks/
git commit -m "feat(gate): N6Codec C 코어 — 21개 상수 코드북 + 압축/해제 + 테스트"
```

---

## Task 2: Mirror Universe C 코어 — 해시 테이블 + LRU + cross-gate dedup

**Files:**
- Create: `mk2_hexa/native/gate_hooks/mirror.h`
- Create: `mk2_hexa/native/gate_hooks/mirror.c`
- Modify: `mk2_hexa/native/gate_hooks/Makefile` (test_mirror 추가)

- [ ] **Step 1: Mirror 헤더 작성**

```c
// mirror.h — Shadow copy hash table with LRU eviction
#ifndef MIRROR_H
#define MIRROR_H

#include <stdint.h>
#include <stddef.h>

#define MIRROR_BUCKETS 65536   // 64K 버킷
#define MIRROR_MAX_MB  64      // 게이트당 최대 64MB

typedef struct mirror_entry {
    uint64_t hash;              // xxhash of block
    uint32_t ref_id;            // 참조 ID (1-based, 0=empty)
    uint32_t size;              // 원본 데이터 크기
    void *data;                 // 원본 데이터 사본
    uint64_t last_access;       // LRU 타임스탬프
    int gate_id;                // 소속 게이트 (-1=cross-gate)
    struct mirror_entry *next;  // 체이닝
} MirrorEntry;

typedef struct {
    MirrorEntry *buckets[MIRROR_BUCKETS];
    uint32_t next_ref;          // 다음 참조 ID
    size_t total_bytes;         // 현재 사용 메모리
    size_t max_bytes;           // 최대 메모리 (MIRROR_MAX_MB * 1024 * 1024)
    uint64_t hits;
    uint64_t misses;
    uint64_t evictions;
    int gate_id;
} Mirror;

void     mirror_init(Mirror *m, int gate_id);
void     mirror_destroy(Mirror *m);

// 데이터 블록의 해시 검색 → hit면 ref_id 반환, miss면 0
uint32_t mirror_lookup(Mirror *m, const void *data, size_t len);

// 데이터 블록 등록 → ref_id 반환
uint32_t mirror_insert(Mirror *m, const void *data, size_t len);

// ref_id로 원본 데이터 복원
const void* mirror_resolve(const Mirror *m, uint32_t ref_id, size_t *out_len);

// LRU 축출 (메모리 압박 시)
void     mirror_evict_lru(Mirror *m, size_t target_free);

// 통계
float    mirror_hit_rate(const Mirror *m);
size_t   mirror_used_bytes(const Mirror *m);

#endif
```

- [ ] **Step 2: Mirror 구현 작성**

```c
// mirror.c
#include "mirror.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// 간단한 해시 (FNV-1a 64bit)
static uint64_t fnv1a(const void *data, size_t len) {
    uint64_t h = 0xcbf29ce484222325ULL;
    const uint8_t *p = (const uint8_t *)data;
    for (size_t i = 0; i < len; i++) {
        h ^= p[i];
        h *= 0x100000001b3ULL;
    }
    return h;
}

static uint64_t timestamp_counter = 0;
static uint64_t next_ts(void) { return ++timestamp_counter; }

void mirror_init(Mirror *m, int gate_id) {
    memset(m, 0, sizeof(*m));
    m->gate_id = gate_id;
    m->next_ref = 1;
    m->max_bytes = MIRROR_MAX_MB * 1024ULL * 1024ULL;
}

void mirror_destroy(Mirror *m) {
    for (int i = 0; i < MIRROR_BUCKETS; i++) {
        MirrorEntry *e = m->buckets[i];
        while (e) {
            MirrorEntry *next = e->next;
            free(e->data);
            free(e);
            e = next;
        }
        m->buckets[i] = NULL;
    }
    m->total_bytes = 0;
}

uint32_t mirror_lookup(Mirror *m, const void *data, size_t len) {
    uint64_t h = fnv1a(data, len);
    int bucket = h % MIRROR_BUCKETS;

    MirrorEntry *e = m->buckets[bucket];
    while (e) {
        if (e->hash == h && e->size == (uint32_t)len &&
            memcmp(e->data, data, len) == 0) {
            e->last_access = next_ts();
            m->hits++;
            return e->ref_id;
        }
        e = e->next;
    }
    m->misses++;
    return 0;
}

uint32_t mirror_insert(Mirror *m, const void *data, size_t len) {
    // 메모리 초과 시 축출
    while (m->total_bytes + len > m->max_bytes) {
        mirror_evict_lru(m, len);
    }

    uint64_t h = fnv1a(data, len);
    int bucket = h % MIRROR_BUCKETS;

    MirrorEntry *e = calloc(1, sizeof(MirrorEntry));
    e->hash = h;
    e->ref_id = m->next_ref++;
    e->size = (uint32_t)len;
    e->data = malloc(len);
    memcpy(e->data, data, len);
    e->last_access = next_ts();
    e->gate_id = m->gate_id;
    e->next = m->buckets[bucket];
    m->buckets[bucket] = e;
    m->total_bytes += len + sizeof(MirrorEntry);

    return e->ref_id;
}

const void* mirror_resolve(const Mirror *m, uint32_t ref_id, size_t *out_len) {
    for (int i = 0; i < MIRROR_BUCKETS; i++) {
        MirrorEntry *e = m->buckets[i];
        while (e) {
            if (e->ref_id == ref_id) {
                if (out_len) *out_len = e->size;
                return e->data;
            }
            e = e->next;
        }
    }
    return NULL;
}

void mirror_evict_lru(Mirror *m, size_t target_free) {
    size_t freed = 0;
    while (freed < target_free) {
        // 전체에서 가장 오래된 엔트리 찾기
        MirrorEntry *oldest = NULL;
        int oldest_bucket = -1;
        MirrorEntry *oldest_prev = NULL;

        for (int i = 0; i < MIRROR_BUCKETS; i++) {
            MirrorEntry *prev = NULL;
            MirrorEntry *e = m->buckets[i];
            while (e) {
                if (!oldest || e->last_access < oldest->last_access) {
                    oldest = e;
                    oldest_bucket = i;
                    oldest_prev = prev;
                }
                prev = e;
                e = e->next;
            }
        }

        if (!oldest) break;

        // 제거
        if (oldest_prev) oldest_prev->next = oldest->next;
        else m->buckets[oldest_bucket] = oldest->next;

        freed += oldest->size + sizeof(MirrorEntry);
        m->total_bytes -= oldest->size + sizeof(MirrorEntry);
        m->evictions++;
        free(oldest->data);
        free(oldest);
    }
}

float mirror_hit_rate(const Mirror *m) {
    uint64_t total = m->hits + m->misses;
    if (total == 0) return 0.0f;
    return (float)m->hits / (float)total;
}

size_t mirror_used_bytes(const Mirror *m) {
    return m->total_bytes;
}
```

- [ ] **Step 3: Mirror 테스트 작성 + Makefile 업데이트**

test_mirror.c:
```c
#include "mirror.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

static void test_insert_lookup(void) {
    Mirror m;
    mirror_init(&m, 0);

    uint8_t data[] = "hello gate world";
    uint32_t ref = mirror_insert(&m, data, sizeof(data));
    assert(ref > 0);

    uint32_t ref2 = mirror_lookup(&m, data, sizeof(data));
    assert(ref2 == ref);
    assert(m.hits == 1);
    printf("  PASS: test_insert_lookup\n");
    mirror_destroy(&m);
}

static void test_miss(void) {
    Mirror m;
    mirror_init(&m, 0);

    uint8_t data[] = "test";
    uint32_t ref = mirror_lookup(&m, data, sizeof(data));
    assert(ref == 0);
    assert(m.misses == 1);
    printf("  PASS: test_miss\n");
    mirror_destroy(&m);
}

static void test_resolve(void) {
    Mirror m;
    mirror_init(&m, 0);

    uint8_t data[] = "compressed payload";
    uint32_t ref = mirror_insert(&m, data, sizeof(data));

    size_t len;
    const void *resolved = mirror_resolve(&m, ref, &len);
    assert(resolved != NULL);
    assert(len == sizeof(data));
    assert(memcmp(resolved, data, len) == 0);
    printf("  PASS: test_resolve\n");
    mirror_destroy(&m);
}

static void test_dedup(void) {
    Mirror m;
    mirror_init(&m, 0);

    uint8_t block[4096];
    memset(block, 0xAB, sizeof(block));

    uint32_t ref1 = mirror_insert(&m, block, sizeof(block));
    uint32_t ref2 = mirror_lookup(&m, block, sizeof(block));
    assert(ref2 == ref1); // dedup!
    printf("  PASS: test_dedup (4K block)\n");
    mirror_destroy(&m);
}

int main(void) {
    printf("=== Mirror Universe Tests ===\n");
    test_insert_lookup();
    test_miss();
    test_resolve();
    test_dedup();
    printf("=== ALL PASSED ===\n");
    return 0;
}
```

Makefile에 추가:
```makefile
test_mirror: test_mirror.c mirror.o
	$(CC) $(CFLAGS) $^ -o $@

test: test_n6codec test_mirror
	./test_n6codec
	./test_mirror
```

- [ ] **Step 4: 빌드 + 테스트**

```bash
cd mk2_hexa/native/gate_hooks && make test
```

- [ ] **Step 5: Commit**

```bash
git add mk2_hexa/native/gate_hooks/mirror.*
git commit -m "feat(gate): Mirror Universe C 코어 — FNV-1a 해시 + LRU 축출 + dedup"
```

---

## Task 3: Gate Common — 안전장치 + 로깅 + passthrough 판정

**Files:**
- Create: `mk2_hexa/native/gate_hooks/gate_common.h`
- Create: `mk2_hexa/native/gate_hooks/gate_common.c`

- [ ] **Step 1: gate_common 헤더 작성**

```c
// gate_common.h — 공통 상수, 안전장치, 로깅
#ifndef GATE_COMMON_H
#define GATE_COMMON_H

#include <stdint.h>
#include <stddef.h>
#include <time.h>

// 게이트 ID
#define GATE_MACOS    0
#define GATE_FINDER   1
#define GATE_TELEGRAM 2
#define GATE_CHROME   3
#define GATE_SAFARI   4
#define GATE_CLAUDE   5
#define GATE_TERMINAL 6
#define GATE_DEVTOOLS 7
#define GATE_MAX      8

// 안전장치 임계값
#define GATE_MAX_LATENCY_US  1000    // 1ms 초과 시 바이패스
#define GATE_MIN_RATIO       0.05f   // 5% 미만 압축률이면 스킵
#define GATE_MAX_RAM_MB      200     // 전체 게이트 레이어 최대 RAM

// 통계 구조체
typedef struct {
    uint64_t calls;
    uint64_t bypasses;        // passthrough 횟수
    uint64_t errors;
    uint64_t total_in_bytes;
    uint64_t total_out_bytes;
    double   avg_latency_us;
    float    current_ratio;
    time_t   last_update;
} GateStats;

// 안전장치: 호출 전 체크 → 0이면 passthrough, 1이면 진행
int  gate_should_process(int gate_id, size_t data_len);

// 타이밍: 마이크로초 타이머
uint64_t gate_timer_start(void);
uint64_t gate_timer_elapsed_us(uint64_t start);

// 지연 초과 시 자동 바이패스 등록
void gate_register_slow(int gate_id, uint64_t latency_us);

// 통계 기록 (공유 파일로 export)
void gate_update_stats(int gate_id, size_t in_bytes, size_t out_bytes, uint64_t latency_us);
int  gate_export_stats(const char *path);  // ~/.n6gate/stats.json

// 프로세스명으로 gate_id 결정
int  gate_id_from_process(const char *proc_name);

// 로깅 (stderr + 파일)
void gate_log(int gate_id, const char *fmt, ...);

// 전역 킬스위치
int  gate_is_killed(void);  // ~/.n6gate/kill 파일 존재하면 1

#endif
```

- [ ] **Step 2: gate_common 구현 작성**

```c
// gate_common.c
#include "gate_common.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <mach/mach_time.h>
#include <sys/stat.h>

static GateStats g_stats[GATE_MAX] = {0};
static int g_bypass[GATE_MAX] = {0};  // 바이패스 카운터 (연속 느린 호출)
static int g_killed = -1;             // -1=미확인, 0=활성, 1=킬

int gate_should_process(int gate_id, size_t data_len) {
    if (gate_id < 0 || gate_id >= GATE_MAX) return 0;
    if (gate_is_killed()) return 0;
    if (data_len == 0) return 0;
    if (g_bypass[gate_id] > 3) {
        // 연속 3회 느려서 바이패스됨 — 100회마다 재시도
        g_stats[gate_id].calls++;
        if (g_stats[gate_id].calls % 100 == 0) {
            g_bypass[gate_id] = 0; // 리셋
            return 1;
        }
        g_stats[gate_id].bypasses++;
        return 0;
    }
    return 1;
}

uint64_t gate_timer_start(void) {
    return mach_absolute_time();
}

uint64_t gate_timer_elapsed_us(uint64_t start) {
    uint64_t end = mach_absolute_time();
    mach_timebase_info_data_t tb;
    mach_timebase_info(&tb);
    return (end - start) * tb.numer / tb.denom / 1000;
}

void gate_register_slow(int gate_id, uint64_t latency_us) {
    if (gate_id < 0 || gate_id >= GATE_MAX) return;
    if (latency_us > GATE_MAX_LATENCY_US) {
        g_bypass[gate_id]++;
    } else {
        if (g_bypass[gate_id] > 0) g_bypass[gate_id]--;
    }
}

void gate_update_stats(int gate_id, size_t in_bytes, size_t out_bytes, uint64_t latency_us) {
    if (gate_id < 0 || gate_id >= GATE_MAX) return;
    GateStats *s = &g_stats[gate_id];
    s->calls++;
    s->total_in_bytes += in_bytes;
    s->total_out_bytes += out_bytes;
    double alpha = 0.01;
    s->avg_latency_us = s->avg_latency_us * (1.0 - alpha) + (double)latency_us * alpha;
    if (s->total_in_bytes > 0) {
        s->current_ratio = (float)s->total_out_bytes / (float)s->total_in_bytes;
    }
    s->last_update = time(NULL);
}

int gate_export_stats(const char *path) {
    FILE *f = fopen(path, "w");
    if (!f) return -1;
    const char *names[] = {"macos","finder","telegram","chrome","safari","claude","terminal","devtools"};
    fprintf(f, "{\n");
    for (int i = 0; i < GATE_MAX; i++) {
        GateStats *s = &g_stats[i];
        fprintf(f, "  \"%s\": {\"calls\":%llu, \"ratio\":%.4f, \"latency_us\":%.1f, "
                "\"saved_mb\":%.2f, \"bypasses\":%llu}%s\n",
                names[i], s->calls, s->current_ratio, s->avg_latency_us,
                (double)(s->total_in_bytes - s->total_out_bytes) / (1024.0*1024.0),
                s->bypasses,
                (i < GATE_MAX - 1) ? "," : "");
    }
    fprintf(f, "}\n");
    fclose(f);
    return 0;
}

int gate_id_from_process(const char *proc_name) {
    if (!proc_name) return GATE_MACOS;
    if (strstr(proc_name, "Finder")) return GATE_FINDER;
    if (strstr(proc_name, "Telegram")) return GATE_TELEGRAM;
    if (strstr(proc_name, "Chrome") || strstr(proc_name, "chrome")) return GATE_CHROME;
    if (strstr(proc_name, "Safari") || strstr(proc_name, "safari")) return GATE_SAFARI;
    if (strstr(proc_name, "Claude") || strstr(proc_name, "claude")) return GATE_CLAUDE;
    if (strstr(proc_name, "Terminal") || strstr(proc_name, "zsh") || strstr(proc_name, "bash")) return GATE_TERMINAL;
    if (strstr(proc_name, "Xcode") || strstr(proc_name, "Code")) return GATE_DEVTOOLS;
    return GATE_MACOS;
}

void gate_log(int gate_id, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[n6gate:%d] ", gate_id);
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
}

int gate_is_killed(void) {
    // 캐시: 100번 호출마다 파일 체크
    static int check_count = 0;
    if (g_killed >= 0 && check_count++ < 100) return g_killed;
    check_count = 0;

    const char *home = getenv("HOME");
    if (!home) { g_killed = 0; return 0; }
    char path[512];
    snprintf(path, sizeof(path), "%s/.n6gate/kill", home);
    struct stat st;
    g_killed = (stat(path, &st) == 0) ? 1 : 0;
    return g_killed;
}
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_hooks/gate_common.*
git commit -m "feat(gate): gate_common — 안전장치(바이패스/킬스위치) + 통계 + 타이머"
```

---

## Task 4: libgate_malloc.dylib — malloc/free interpose

**Files:**
- Create: `mk2_hexa/native/gate_hooks/libgate_malloc.c`

- [ ] **Step 1: malloc interpose 구현**

```c
// libgate_malloc.c — DYLD_INSERT_LIBRARIES로 주입되는 malloc interpose
#include "n6codec.h"
#include "mirror.h"
#include "gate_common.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <mach-o/dyld-interposing.h>

// 전역 상태 (프로세스당 1개)
static N6Codec g_codec;
static Mirror  g_mirror;
static int     g_initialized = 0;
static int     g_gate_id = GATE_MACOS;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;

// 재진입 방지 (malloc 내부에서 malloc 호출 방지)
static __thread int g_reentrant = 0;

static void gate_malloc_init(void) {
    if (g_initialized) return;

    // 프로세스명으로 게이트 결정
    const char *prog = getprogname();
    g_gate_id = gate_id_from_process(prog);

    n6codec_init(&g_codec, g_gate_id);
    mirror_init(&g_mirror, g_gate_id);

    // 저장된 코드북 로드 시도
    char path[512];
    const char *home = getenv("HOME");
    if (home) {
        snprintf(path, sizeof(path), "%s/.n6gate/codebook_%d.txt", home, g_gate_id);
        n6codec_load_codebook(&g_codec, path);
    }

    g_initialized = 1;
    gate_log(g_gate_id, "gate_malloc initialized for %s (gate=%d)", prog, g_gate_id);
}

// --- interposed malloc ---
void *gate_malloc(size_t size) {
    if (!g_initialized) gate_malloc_init();
    if (g_reentrant || !gate_should_process(g_gate_id, size)) {
        return malloc(size);
    }

    // 64바이트 미만: 압축 오버헤드가 더 큼 → passthrough
    if (size < 64) return malloc(size);

    // 실제 malloc은 항상 실행 (앱이 쓸 메모리)
    void *ptr = malloc(size);
    if (!ptr) return NULL;

    // Mirror 등록 (비동기적으로 — 다음 동일 할당에서 dedup 가능)
    g_reentrant = 1;
    pthread_mutex_lock(&g_lock);

    uint64_t t0 = gate_timer_start();
    mirror_insert(&g_mirror, ptr, size);
    uint64_t elapsed = gate_timer_elapsed_us(t0);

    gate_update_stats(g_gate_id, size, size, elapsed);
    gate_register_slow(g_gate_id, elapsed);

    pthread_mutex_unlock(&g_lock);
    g_reentrant = 0;

    return ptr;
}

// --- interposed free ---
void gate_free(void *ptr) {
    // 특별한 처리 없이 free (Mirror는 자체 LRU로 관리)
    free(ptr);
}

// --- DYLD interpose ---
DYLD_INTERPOSE(gate_malloc, malloc)
DYLD_INTERPOSE(gate_free, free)
```

- [ ] **Step 2: 빌드**

```bash
cd mk2_hexa/native/gate_hooks && make libgate_malloc.dylib
```

- [ ] **Step 3: 간단한 테스트 (echo에 주입)**

```bash
mkdir -p ~/.n6gate
DYLD_INSERT_LIBRARIES=./libgate_malloc.dylib /bin/echo "gate test" 2>&1
```
Expected: `gate test` 출력 + stderr에 `[n6gate:6] gate_malloc initialized` 류 로그

- [ ] **Step 4: Commit**

```bash
git add mk2_hexa/native/gate_hooks/libgate_malloc.c
git commit -m "feat(gate): libgate_malloc — DYLD interpose malloc/free + Mirror 등록"
```

---

## Task 5: libgate_io.dylib — read/write interpose + N6Codec 압축

**Files:**
- Create: `mk2_hexa/native/gate_hooks/libgate_io.c`

- [ ] **Step 1: I/O interpose 구현**

```c
// libgate_io.c — read/write interpose with N6Codec compression
#include "n6codec.h"
#include "mirror.h"
#include "gate_common.h"
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <mach-o/dyld-interposing.h>

static N6Codec g_codec;
static Mirror  g_mirror;
static int     g_initialized = 0;
static int     g_gate_id = GATE_MACOS;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static __thread int g_reentrant = 0;

static void gate_io_init(void) {
    if (g_initialized) return;
    const char *prog = getprogname();
    g_gate_id = gate_id_from_process(prog);
    n6codec_init(&g_codec, g_gate_id);
    mirror_init(&g_mirror, g_gate_id);
    g_initialized = 1;
    gate_log(g_gate_id, "gate_io initialized for %s", prog);
}

// --- interposed read ---
ssize_t gate_read(int fd, void *buf, size_t nbyte) {
    ssize_t ret = read(fd, buf, nbyte);
    if (ret <= 0 || g_reentrant) return ret;
    if (!g_initialized) gate_io_init();
    if (!gate_should_process(g_gate_id, (size_t)ret)) return ret;

    // 256바이트 미만: 스킵
    if (ret < 256) return ret;

    g_reentrant = 1;
    pthread_mutex_lock(&g_lock);

    uint64_t t0 = gate_timer_start();

    // Mirror 체크 — 이미 본 데이터면 히트 기록
    uint32_t ref = mirror_lookup(&g_mirror, buf, (size_t)ret);
    if (ref == 0) {
        // 새 데이터: Mirror에 등록 + Codec으로 프로파일링
        mirror_insert(&g_mirror, buf, (size_t)ret);
    }

    uint64_t elapsed = gate_timer_elapsed_us(t0);
    gate_update_stats(g_gate_id, (size_t)ret, (size_t)ret, elapsed);
    gate_register_slow(g_gate_id, elapsed);

    pthread_mutex_unlock(&g_lock);
    g_reentrant = 0;

    return ret;
}

// --- interposed write ---
ssize_t gate_write(int fd, const void *buf, size_t nbyte) {
    if (g_reentrant || nbyte < 256) return write(fd, buf, nbyte);
    if (!g_initialized) gate_io_init();
    if (!gate_should_process(g_gate_id, nbyte)) return write(fd, buf, nbyte);

    g_reentrant = 1;
    pthread_mutex_lock(&g_lock);

    uint64_t t0 = gate_timer_start();

    // Mirror dedup 체크
    uint32_t ref = mirror_lookup(&g_mirror, buf, nbyte);
    if (ref == 0) {
        mirror_insert(&g_mirror, buf, nbyte);
    }

    // N6Codec 압축 시도 (통계 수집 목적 — 실제 디스크에는 원본 기록)
    N6Result cr = n6codec_compress(&g_codec, buf, nbyte);
    gate_update_stats(g_gate_id, nbyte, cr.size, gate_timer_elapsed_us(t0));
    gate_register_slow(g_gate_id, gate_timer_elapsed_us(t0));
    n6codec_free_result(&cr);

    pthread_mutex_unlock(&g_lock);
    g_reentrant = 0;

    // 원본 기록 (Phase 0 관측 모드: 실제 압축 기록은 Phase 2에서)
    return write(fd, buf, nbyte);
}

DYLD_INTERPOSE(gate_read, read)
DYLD_INTERPOSE(gate_write, write)
```

- [ ] **Step 2: 빌드 + 테스트**

```bash
cd mk2_hexa/native/gate_hooks && make libgate_io.dylib
DYLD_INSERT_LIBRARIES=./libgate_io.dylib cat /etc/hosts 2>&1 | head -3
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_hooks/libgate_io.c
git commit -m "feat(gate): libgate_io — read/write interpose + Mirror dedup + N6Codec 프로파일링"
```

---

## Task 6: libgate_mach.dylib — mach_msg IPC interpose

**Files:**
- Create: `mk2_hexa/native/gate_hooks/libgate_mach.c`

- [ ] **Step 1: mach_msg interpose 구현**

```c
// libgate_mach.c — mach_msg interpose for IPC compression
#include "n6codec.h"
#include "mirror.h"
#include "gate_common.h"
#include <mach/mach.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#include <mach-o/dyld-interposing.h>

static N6Codec g_codec;
static Mirror  g_mirror;
static int     g_initialized = 0;
static int     g_gate_id = GATE_MACOS;
static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static __thread int g_reentrant = 0;

static void gate_mach_init(void) {
    if (g_initialized) return;
    const char *prog = getprogname();
    g_gate_id = gate_id_from_process(prog);
    n6codec_init(&g_codec, g_gate_id);
    mirror_init(&g_mirror, g_gate_id);
    g_initialized = 1;
}

mach_msg_return_t gate_mach_msg(
    mach_msg_header_t *msg,
    mach_msg_option_t option,
    mach_msg_size_t send_size,
    mach_msg_size_t recv_size,
    mach_port_name_t recv_name,
    mach_msg_timeout_t timeout,
    mach_port_name_t notify)
{
    if (!g_initialized) gate_mach_init();

    // 송신 시: 페이로드 프로파일링
    if ((option & MACH_SEND_MSG) && send_size > sizeof(mach_msg_header_t) + 64) {
        if (!g_reentrant && gate_should_process(g_gate_id, send_size)) {
            g_reentrant = 1;
            pthread_mutex_lock(&g_lock);

            uint64_t t0 = gate_timer_start();
            size_t payload_size = send_size - sizeof(mach_msg_header_t);
            void *payload = (uint8_t *)msg + sizeof(mach_msg_header_t);

            mirror_lookup(&g_mirror, payload, payload_size);
            mirror_insert(&g_mirror, payload, payload_size);

            gate_update_stats(g_gate_id, payload_size, payload_size, gate_timer_elapsed_us(t0));
            pthread_mutex_unlock(&g_lock);
            g_reentrant = 0;
        }
    }

    return mach_msg(msg, option, send_size, recv_size, recv_name, timeout, notify);
}

DYLD_INTERPOSE(gate_mach_msg, mach_msg)
```

- [ ] **Step 2: 빌드**

```bash
cd mk2_hexa/native/gate_hooks && make libgate_mach.dylib
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_hooks/libgate_mach.c
git commit -m "feat(gate): libgate_mach — mach_msg IPC interpose + Mirror 프로파일링"
```

---

## Task 7: N6Codec hexa 레퍼런스 — 프로토타입 + 벤치마크

**Files:**
- Create: `mk2_hexa/native/gate_injection/n6codec.hexa`

- [ ] **Step 1: hexa N6Codec 구현**

```hexa
// n6codec.hexa — N6Codec hexa 레퍼런스 (프로토타입 + 벤치마크)
// C 구현과 동일한 로직, hexa에서 테스트/벤치 가능

struct N6Entry {
    value: float,
    symbol: int,
    tolerance: float,
    name: string
}

fn default_codebook() -> [N6Entry] {
    let cb = []
    cb.push(N6Entry { value: 6.0,      symbol: 0,  tolerance: 0.01,  name: "N" })
    cb.push(N6Entry { value: 1.618034, symbol: 1,  tolerance: 0.005, name: "phi" })
    cb.push(N6Entry { value: 4.0,      symbol: 2,  tolerance: 0.01,  name: "tau" })
    cb.push(N6Entry { value: 5.0,      symbol: 3,  tolerance: 0.01,  name: "sopfr" })
    cb.push(N6Entry { value: 12.0,     symbol: 4,  tolerance: 0.05,  name: "sigma" })
    cb.push(N6Entry { value: 2.0,      symbol: 5,  tolerance: 0.01,  name: "phi_euler" })
    cb.push(N6Entry { value: 3.0,      symbol: 6,  tolerance: 0.01,  name: "n_over_phi" })
    cb.push(N6Entry { value: 0.333333, symbol: 7,  tolerance: 0.003, name: "meta_fp" })
    cb.push(N6Entry { value: 137.036,  symbol: 8,  tolerance: 0.5,   name: "alpha_inv" })
    cb.push(N6Entry { value: 0.2312,   symbol: 9,  tolerance: 0.003, name: "sin2_thetaW" })
    cb.push(N6Entry { value: 24.0,     symbol: 10, tolerance: 0.1,   name: "tau_sigma" })
    cb.push(N6Entry { value: 7.0,      symbol: 11, tolerance: 0.01,  name: "M3" })
    cb.push(N6Entry { value: 10.0,     symbol: 12, tolerance: 0.05,  name: "sigma_phi" })
    cb.push(N6Entry { value: 8.0,      symbol: 13, tolerance: 0.01,  name: "phi_tau" })
    cb.push(N6Entry { value: 28.0,     symbol: 14, tolerance: 0.1,   name: "perfect" })
    cb.push(N6Entry { value: 0.618034, symbol: 15, tolerance: 0.005, name: "phi_inv" })
    cb.push(N6Entry { value: 2.618034, symbol: 16, tolerance: 0.005, name: "phi_sq" })
    cb.push(N6Entry { value: 73.0,     symbol: 17, tolerance: 0.5,   name: "H0" })
    cb.push(N6Entry { value: 0.6889,   symbol: 18, tolerance: 0.005, name: "omega_lambda" })
    cb.push(N6Entry { value: 0.3111,   symbol: 19, tolerance: 0.005, name: "omega_m" })
    cb.push(N6Entry { value: 11.0,     symbol: 20, tolerance: 0.05,  name: "sigma_sopfr" })
    return cb
}

fn n6_proximity(val: float, codebook: [N6Entry]) -> float {
    let mut best = 0.0
    let mut i = 0
    while i < codebook.len() {
        let entry = codebook[i]
        let dist = val - entry.value
        let abs_dist = if dist < 0.0 { 0.0 - dist } else { dist }
        let max_range = if entry.value > 1.0 { entry.value } else { 1.0 }
        let prox = 1.0 - abs_dist / max_range
        if prox > best { best = prox }
        i = i + 1
    }
    return if best < 0.0 { 0.0 } else { best }
}

fn bench_codebook() -> int {
    let cb = default_codebook()
    println("=== N6Codec hexa benchmark ===")
    println("Codebook size: " + to_string(cb.len()))

    // 테스트: 각 상수의 proximity = 1.0
    let mut pass = 0
    let mut i = 0
    while i < cb.len() {
        let prox = n6_proximity(cb[i].value, cb)
        if prox >= 0.99 {
            pass = pass + 1
        } else {
            println("  FAIL: " + cb[i].name + " prox=" + to_string(prox))
        }
        i = i + 1
    }
    println("Self-test: " + to_string(pass) + "/" + to_string(cb.len()) + " passed")

    // 벤치: 랜덤 값들의 proximity 분포
    let test_values = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 24.0, 42.0, 100.0, 137.0]
    let mut hits = 0
    let mut vi = 0
    while vi < test_values.len() {
        let p = n6_proximity(test_values[vi], cb)
        if p > 0.95 {
            hits = hits + 1
            println("  HIT: " + to_string(test_values[vi]) + " -> prox=" + to_string(p))
        }
        vi = vi + 1
    }
    println("Hit rate on test values: " + to_string(hits) + "/" + to_string(test_values.len()))

    return pass
}

fn save_codebook(codebook: [N6Entry], path: string) {
    let mut content = "# N6Codec codebook entries=" + to_string(codebook.len()) + "\n"
    let mut i = 0
    while i < codebook.len() {
        let e = codebook[i]
        content = content + to_string(e.symbol) + "\t" + to_string(e.value) + "\t" + to_string(e.tolerance) + "\t" + e.name + "\n"
        i = i + 1
    }
    write_file(path, content)
    println("Codebook saved to " + path)
}

fn main() {
    let result = bench_codebook()

    // 코드북 저장 (C 코어와 공유)
    let home = env("HOME")
    let dir = home + "/.n6gate"
    exec("mkdir", ["-p", dir])
    save_codebook(default_codebook(), dir + "/codebook_default.txt")

    println("=== done (" + to_string(result) + " passed) ===")
}

main()
```

- [ ] **Step 2: 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/n6codec.hexa
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/n6codec.hexa
git commit -m "feat(gate): N6Codec hexa 레퍼런스 — 21개 코드북 + proximity + 벤치마크"
```

---

## Task 8: gate_stats.hexa — 통계 수집 + JSON 대시보드

**Files:**
- Create: `mk2_hexa/native/gate_injection/gate_stats.hexa`

- [ ] **Step 1: 통계 수집 모듈 구현**

```hexa
// gate_stats.hexa — 게이트 통계 수집 + JSON 리포트
// C dylib이 기록한 ~/.n6gate/stats.json 을 읽고 분석

fn read_stats() -> string {
    let home = env("HOME")
    let path = home + "/.n6gate/stats.json"
    if file_exists(path) {
        return read_file(path)
    }
    return ""
}

fn report() {
    println("╔══════════════════════════════════════════════════╗")
    println("║        GATE INJECTION LAYER — STATUS            ║")
    println("╚══════════════════════════════════════════════════╝")

    let stats = read_stats()
    if stats == "" {
        println("  (no stats yet — gates not active)")
        println("  activate: DYLD_INSERT_LIBRARIES=libgate_malloc.dylib <app>")
        return
    }

    println(stats)

    // 킬스위치 상태
    let home = env("HOME")
    if file_exists(home + "/.n6gate/kill") {
        println("\n  *** KILLSWITCH ACTIVE — all gates bypassed ***")
    } else {
        println("\n  gates: ACTIVE")
    }

    // 코드북 상태
    let mut i = 0
    while i < 8 {
        let cb_path = home + "/.n6gate/codebook_" + to_string(i) + ".txt"
        if file_exists(cb_path) {
            let content = read_file(cb_path)
            let lines = content.split("\n")
            println("  codebook[" + to_string(i) + "]: " + to_string(lines.len() - 1) + " entries")
        }
        i = i + 1
    }
}

fn kill() {
    let home = env("HOME")
    exec("mkdir", ["-p", home + "/.n6gate"])
    write_file(home + "/.n6gate/kill", "1")
    println("KILLSWITCH ACTIVATED — all gates will passthrough")
}

fn revive() {
    let home = env("HOME")
    let path = home + "/.n6gate/kill"
    if file_exists(path) {
        exec("rm", [path])
        println("KILLSWITCH REMOVED — gates will resume")
    } else {
        println("gates already active")
    }
}

fn main() {
    let a = args()
    if a.len() >= 2 {
        if a[1] == "kill" { kill() }
        else if a[1] == "revive" { revive() }
        else { report() }
    } else {
        report()
    }
}

main()
```

- [ ] **Step 2: 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_stats.hexa
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_stats.hexa kill
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_stats.hexa revive
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/gate_stats.hexa
git commit -m "feat(gate): gate_stats — 통계 대시보드 + 킬스위치 관리"
```

---

## Task 9: gate_core.hexa — 게이트 라이프사이클 + CLI

**Files:**
- Create: `mk2_hexa/native/gate_injection/gate_core.hexa`

- [ ] **Step 1: 게이트 코어 + CLI 구현**

```hexa
// gate_core.hexa — 게이트 라이프사이클 관리 + n6gate CLI
// 사용법: hexa gate_core.hexa <command> [args]

fn ensure_dirs() {
    let home = env("HOME")
    exec("mkdir", ["-p", home + "/.n6gate"])
    let mut i = 0
    while i < 8 {
        exec("mkdir", ["-p", home + "/.n6gate/gate_" + to_string(i)])
        i = i + 1
    }
}

fn gate_names() -> [string] {
    return ["macos", "finder", "telegram", "chrome", "safari", "claude", "terminal", "devtools"]
}

fn hooks_dir() -> string {
    let a = args()
    // 실행 파일 기준으로 gate_hooks 경로 유추
    return env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_hooks"
}

fn cmd_status() {
    println("=== n6gate status ===")
    let names = gate_names()
    let home = env("HOME")

    // 킬스위치
    if file_exists(home + "/.n6gate/kill") {
        println("KILLSWITCH: ON (all gates bypassed)")
    } else {
        println("KILLSWITCH: off")
    }

    // dylib 존재 확인
    let hdir = hooks_dir()
    let libs = ["libgate_malloc.dylib", "libgate_io.dylib", "libgate_mach.dylib"]
    let mut li = 0
    while li < libs.len() {
        let exists = file_exists(hdir + "/" + libs[li])
        println("  " + libs[li] + ": " + if exists { "BUILT" } else { "not built" })
        li = li + 1
    }

    // 통계
    if file_exists(home + "/.n6gate/stats.json") {
        println("\n--- stats ---")
        println(read_file(home + "/.n6gate/stats.json"))
    }
}

fn cmd_inject(app_path: string) {
    let hdir = hooks_dir()
    let dylib = hdir + "/libgate_malloc.dylib"
    if file_exists(dylib) {
        println("Injecting gate into: " + app_path)
        println("DYLD_INSERT_LIBRARIES=" + dylib + " " + app_path)
        // 실제 실행
        exec("env", ["DYLD_INSERT_LIBRARIES=" + dylib, app_path])
    } else {
        println("ERROR: dylib not built. Run: cd gate_hooks && make")
    }
}

fn cmd_build() {
    let hdir = hooks_dir()
    println("Building gate dylibs...")
    let result = shell("cd " + hdir + " && make 2>&1")
    println(result)
}

fn cmd_bench() {
    println("=== N6Codec Benchmark ===")
    // hexa 레퍼런스 벤치
    let home = env("HOME")
    let hexa = env("HOME") + "/Dev/hexa-lang/target/release/hexa"
    let result = shell(hexa + " " + env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_injection/n6codec.hexa 2>&1")
    println(result)
}

fn cmd_help() {
    println("n6gate — Gate Injection Layer CLI")
    println("")
    println("Commands:")
    println("  status          게이트 상태 확인")
    println("  build           dylib 빌드")
    println("  inject <app>    앱에 게이트 주입")
    println("  bench           N6Codec 벤치마크")
    println("  kill            전체 게이트 비활성화")
    println("  revive          게이트 재활성화")
    println("  stats           통계 대시보드")
}

fn main() {
    ensure_dirs()
    let a = args()
    if a.len() < 2 {
        cmd_help()
        return
    }
    let cmd = a[1]
    if cmd == "status" { cmd_status() }
    else if cmd == "build" { cmd_build() }
    else if cmd == "inject" {
        if a.len() >= 3 { cmd_inject(a[2]) }
        else { println("Usage: n6gate inject <app_path>") }
    }
    else if cmd == "bench" { cmd_bench() }
    else if cmd == "kill" {
        let home = env("HOME")
        exec("mkdir", ["-p", home + "/.n6gate"])
        write_file(home + "/.n6gate/kill", "1")
        println("KILLSWITCH ACTIVATED")
    }
    else if cmd == "revive" {
        let home = env("HOME")
        if file_exists(home + "/.n6gate/kill") {
            exec("rm", [home + "/.n6gate/kill"])
        }
        println("Gates resumed")
    }
    else if cmd == "stats" {
        let result = shell(env("HOME") + "/Dev/hexa-lang/target/release/hexa " + env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_injection/gate_stats.hexa 2>&1")
        println(result)
    }
    else { cmd_help() }
}

main()
```

- [ ] **Step 2: 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_core.hexa status
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_core.hexa help
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/gate_core.hexa
git commit -m "feat(gate): gate_core — CLI (status/build/inject/bench/kill/revive)"
```

---

## Task 10: lens_array.hexa — 5렌즈 실시간 스트림 스캔

**Files:**
- Create: `mk2_hexa/native/gate_injection/lens_array.hexa`

- [ ] **Step 1: 렌즈 배열 구현**

기존 gate_lens_fusion.hexa의 렌즈 로직을 압축 컨텍스트에 맞게 재구성.
스트림 데이터(바이트 배열)를 받아서 n=6 패턴 감지 → 코드북 확장 제안.

```hexa
// lens_array.hexa — 5+α 렌즈 실시간 스캔
// 입력: 데이터 프로파일 (바이트 분포, 빈도)
// 출력: 코드북 확장 제안 + 패턴 리포트

struct LensResult {
    lens_name: string,
    pattern: string,
    confidence: float,
    suggested_value: float,
    suggested_name: string
}

fn phi_lens(values: [float]) -> [LensResult] {
    // 황금비 패턴 감지: 연속 값의 비율이 φ에 근접
    let phi = 1.618034
    let results = []
    let mut i = 0
    while i + 1 < values.len() {
        if values[i] > 0.0 {
            let ratio = values[i + 1] / values[i]
            let dist = ratio - phi
            let abs_dist = if dist < 0.0 { 0.0 - dist } else { dist }
            if abs_dist < 0.1 {
                results.push(LensResult {
                    lens_name: "PhiLens",
                    pattern: "ratio[" + to_string(i) + ":" + to_string(i+1) + "]=" + to_string(ratio),
                    confidence: 1.0 - abs_dist / phi,
                    suggested_value: ratio,
                    suggested_name: "phi_ratio_" + to_string(i)
                })
            }
        }
        i = i + 1
    }
    return results
}

fn prime_lens(values: [float]) -> [LensResult] {
    // 소수 간격 패턴 감지
    let primes = [2.0, 3.0, 5.0, 7.0, 11.0, 13.0, 17.0, 19.0, 23.0, 29.0, 31.0]
    let results = []
    let mut vi = 0
    while vi < values.len() {
        let mut pi = 0
        while pi < primes.len() {
            let dist = values[vi] - primes[pi]
            let abs_dist = if dist < 0.0 { 0.0 - dist } else { dist }
            if abs_dist < 0.5 {
                results.push(LensResult {
                    lens_name: "PrimeLens",
                    pattern: "val[" + to_string(vi) + "]~prime(" + to_string(primes[pi]) + ")",
                    confidence: 1.0 - abs_dist / primes[pi],
                    suggested_value: primes[pi],
                    suggested_name: "prime_" + to_string(to_int(primes[pi]))
                })
            }
            pi = pi + 1
        }
        vi = vi + 1
    }
    return results
}

fn meta_lens(values: [float]) -> [LensResult] {
    // 메타 부동점 1/3 수렴 패턴
    let fp = 0.333333
    let results = []
    let mut i = 0
    while i < values.len() {
        let dist = values[i] - fp
        let abs_dist = if dist < 0.0 { 0.0 - dist } else { dist }
        if abs_dist < 0.03 {
            results.push(LensResult {
                lens_name: "MetaTranscendenceLens",
                pattern: "val[" + to_string(i) + "]=" + to_string(values[i]) + "~1/3",
                confidence: 1.0 - abs_dist / fp,
                suggested_value: fp,
                suggested_name: "meta_fp"
            })
        }
        i = i + 1
    }
    return results
}

fn spectral_lens(values: [float]) -> [LensResult] {
    // 주파수 분석: 반복 패턴 간격 감지
    let results = []
    if values.len() < 4 { return results }
    let mut i = 0
    while i + 2 < values.len() {
        let diff1 = values[i + 1] - values[i]
        let diff2 = values[i + 2] - values[i + 1]
        let delta = diff1 - diff2
        let abs_delta = if delta < 0.0 { 0.0 - delta } else { delta }
        if abs_delta < 0.1 && diff1 > 0.01 {
            results.push(LensResult {
                lens_name: "SpectralLens",
                pattern: "linear[" + to_string(i) + ":" + to_string(i+2) + "] stride=" + to_string(diff1),
                confidence: 1.0 - abs_delta,
                suggested_value: diff1,
                suggested_name: "stride_" + to_string(i)
            })
        }
        i = i + 1
    }
    return results
}

fn topology_lens(values: [float]) -> [LensResult] {
    // 위상 불변량: 값의 순서 패턴 (상승/하강 횟수)
    let results = []
    let mut ups = 0
    let mut downs = 0
    let mut i = 0
    while i + 1 < values.len() {
        if values[i + 1] > values[i] { ups = ups + 1 }
        else if values[i + 1] < values[i] { downs = downs + 1 }
        i = i + 1
    }
    let total = ups + downs
    if total > 0 {
        let ratio = to_float(ups) / to_float(total)
        results.push(LensResult {
            lens_name: "TopologyLens",
            pattern: "up/down=" + to_string(ups) + "/" + to_string(downs) + " ratio=" + to_string(ratio),
            confidence: ratio,
            suggested_value: ratio,
            suggested_name: "topo_ratio"
        })
    }
    return results
}

fn scan_all(values: [float]) -> [LensResult] {
    let all = []
    let r1 = phi_lens(values)
    let r2 = prime_lens(values)
    let r3 = meta_lens(values)
    let r4 = spectral_lens(values)
    let r5 = topology_lens(values)
    let mut i = 0
    while i < r1.len() { all.push(r1[i]); i = i + 1 }
    i = 0
    while i < r2.len() { all.push(r2[i]); i = i + 1 }
    i = 0
    while i < r3.len() { all.push(r3[i]); i = i + 1 }
    i = 0
    while i < r4.len() { all.push(r4[i]); i = i + 1 }
    i = 0
    while i < r5.len() { all.push(r5[i]); i = i + 1 }
    return all
}

fn main() {
    println("=== Lens Array — Stream Pattern Scan ===")
    // 테스트 데이터: 시스템 메트릭 시뮬레이션
    let values = [6.0, 9.708, 15.708, 3.0, 5.0, 8.09, 0.333, 12.0, 137.0, 0.231, 7.0, 28.0]
    let results = scan_all(values)

    let mut i = 0
    while i < results.len() {
        let r = results[i]
        println("  [" + r.lens_name + "] " + r.pattern + " conf=" + to_string(r.confidence))
        i = i + 1
    }
    println("Total patterns: " + to_string(results.len()))
}

main()
```

- [ ] **Step 2: 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/lens_array.hexa
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/lens_array.hexa
git commit -m "feat(gate): lens_array — 5렌즈(Phi/Prime/Meta/Spectral/Topology) 스트림 스캔"
```

---

## Task 11: ouroboros_evolver.hexa — 압축 파라미터 유전 진화

**Files:**
- Create: `mk2_hexa/native/gate_injection/ouroboros_evolver.hexa`

- [ ] **Step 1: OUROBOROS 진화 엔진 구현**

```hexa
// ouroboros_evolver.hexa — 압축 파라미터 유전 진화
// 각 게이트의 압축 전략을 진화시킴

struct Genome {
    window_size: int,        // 압축 윈도우 크기 (64~4096)
    codebook_aggression: float, // 코드북 매칭 공격성 (0.5~2.0)
    mirror_max_mb: int,      // Mirror 최대 MB (16~128)
    min_block_size: int,     // 최소 처리 블록 (32~512)
    fitness: float           // 적합도 = 압축률 × (1/지연)
}

fn random_genome() -> Genome {
    // 의사 난수 (시간 기반)
    let t = to_float(to_int(time()))
    let r1 = to_int(t) % 4033 + 64
    let r2 = (to_float(to_int(t) % 150) / 100.0) + 0.5
    let r3 = to_int(t) % 113 + 16
    let r4 = to_int(t) % 481 + 32
    return Genome {
        window_size: r1,
        codebook_aggression: r2,
        mirror_max_mb: r3,
        min_block_size: r4,
        fitness: 0.0
    }
}

fn crossover(a: Genome, b: Genome) -> Genome {
    // 단순 교차: 절반씩
    return Genome {
        window_size: a.window_size,
        codebook_aggression: b.codebook_aggression,
        mirror_max_mb: a.mirror_max_mb,
        min_block_size: b.min_block_size,
        fitness: 0.0
    }
}

fn mutate(g: Genome, rate: float) -> Genome {
    let t = to_float(to_int(time()))
    let mut out = g
    // 변이: rate 확률로 파라미터 변경
    let r = (to_int(t) % 100) / 100.0
    if r < rate {
        out.window_size = out.window_size + (to_int(t) % 65) - 32
        if out.window_size < 64 { out.window_size = 64 }
        if out.window_size > 4096 { out.window_size = 4096 }
    }
    let r2 = (to_int(t) % 97) / 100.0
    if r2 < rate {
        out.codebook_aggression = out.codebook_aggression + (to_float(to_int(t) % 41) - 20.0) / 100.0
        if out.codebook_aggression < 0.5 { out.codebook_aggression = 0.5 }
        if out.codebook_aggression > 2.0 { out.codebook_aggression = 2.0 }
    }
    out.fitness = 0.0
    return out
}

fn evolve(population: [Genome], generations: int) -> Genome {
    let mut pop = population
    let mut gen = 0
    while gen < generations {
        // 적합도 평가 (시뮬레이션: window_size가 클수록 압축률↑, 너무 크면 지연↑)
        let mut i = 0
        while i < pop.len() {
            let g = pop[i]
            let ratio = 0.3 + to_float(g.window_size) / 8192.0
            let latency = 100.0 + to_float(g.window_size) * 0.5 + to_float(g.mirror_max_mb) * 2.0
            pop[i].fitness = ratio * (1000.0 / latency) * g.codebook_aggression
            i = i + 1
        }

        // 정렬 (버블 — 소규모)
        let mut si = 0
        while si < pop.len() {
            let mut sj = si + 1
            while sj < pop.len() {
                if pop[sj].fitness > pop[si].fitness {
                    let tmp = pop[si]
                    pop[si] = pop[sj]
                    pop[sj] = tmp
                }
                sj = sj + 1
            }
            si = si + 1
        }

        println("  gen " + to_string(gen) + ": best fitness=" + to_string(pop[0].fitness) +
                " window=" + to_string(pop[0].window_size) +
                " aggr=" + to_string(pop[0].codebook_aggression))

        // 상위 50% 생존 + 교차 + 변이
        let half = pop.len() / 2
        let mut new_pop = []
        let mut ni = 0
        while ni < half {
            new_pop.push(pop[ni])
            ni = ni + 1
        }
        ni = 0
        while ni < half {
            let child = crossover(pop[ni], pop[(ni + 1) % half])
            new_pop.push(mutate(child, 0.3))
            ni = ni + 1
        }
        pop = new_pop

        gen = gen + 1
    }
    return pop[0]
}

fn main() {
    println("=== OUROBOROS Compression Evolver ===")

    // 초기 집단 생성
    let mut population = []
    let mut i = 0
    while i < 20 {
        population.push(random_genome())
        i = i + 1
    }

    let best = evolve(population, 10)
    println("\n=== Best Genome ===")
    println("  window_size: " + to_string(best.window_size))
    println("  codebook_aggression: " + to_string(best.codebook_aggression))
    println("  mirror_max_mb: " + to_string(best.mirror_max_mb))
    println("  min_block_size: " + to_string(best.min_block_size))
    println("  fitness: " + to_string(best.fitness))

    // 결과 저장
    let home = env("HOME")
    let path = home + "/.n6gate/best_genome.txt"
    exec("mkdir", ["-p", home + "/.n6gate"])
    write_file(path, "window_size=" + to_string(best.window_size) + "\n" +
        "codebook_aggression=" + to_string(best.codebook_aggression) + "\n" +
        "mirror_max_mb=" + to_string(best.mirror_max_mb) + "\n" +
        "min_block_size=" + to_string(best.min_block_size) + "\n" +
        "fitness=" + to_string(best.fitness) + "\n")
    println("Saved to " + path)
}

main()
```

- [ ] **Step 2: 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/ouroboros_evolver.hexa
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/ouroboros_evolver.hexa
git commit -m "feat(gate): OUROBOROS 진화 엔진 — 압축 파라미터 유전 진화 (20개체 × 10세대)"
```

---

## Task 12: mirror_universe.hexa + breakthrough.hexa + proximity_predictor.hexa

**Files:**
- Create: `mk2_hexa/native/gate_injection/mirror_universe.hexa`
- Create: `mk2_hexa/native/gate_injection/breakthrough.hexa`
- Create: `mk2_hexa/native/gate_injection/proximity_predictor.hexa`

- [ ] **Step 1: mirror_universe.hexa 구현**

hexa 레퍼런스 — 파일 기반 dedup 시뮬레이션.

```hexa
// mirror_universe.hexa — Shadow copy + cross-gate dedup (hexa 레퍼런스)

fn simple_hash(s: string) -> string {
    // 간단한 문자열 해시 (DJB2)
    let mut h = 5381
    let mut i = 0
    while i < s.len() {
        h = h * 33 + to_int(s[i])
        i = i + 1
    }
    return to_string(h)
}

fn mirror_scan(data_dir: string) -> int {
    println("=== Mirror Universe — Dedup Scan ===")
    println("Scanning: " + data_dir)

    let result = shell("find " + data_dir + " -type f -size +1k 2>/dev/null | head -100")
    let files = result.split("\n")
    let mut hashes = []
    let mut dupes = 0
    let mut total = 0

    let mut i = 0
    while i < files.len() {
        if files[i] != "" {
            let h = shell("md5 -q " + files[i] + " 2>/dev/null")
            if h != "" {
                let mut found = false
                let mut j = 0
                while j < hashes.len() {
                    if hashes[j] == h { found = true; dupes = dupes + 1 }
                    j = j + 1
                }
                if found == false { hashes.push(h) }
                total = total + 1
            }
        }
        i = i + 1
    }

    println("  files scanned: " + to_string(total))
    println("  unique: " + to_string(hashes.len()))
    println("  duplicates: " + to_string(dupes))
    if total > 0 {
        let dedup_ratio = to_float(dupes) / to_float(total) * 100.0
        println("  dedup potential: " + to_string(dedup_ratio) + "%")
    }
    return dupes
}

fn main() {
    let a = args()
    if a.len() >= 2 {
        mirror_scan(a[1])
    } else {
        mirror_scan(env("HOME") + "/.n6gate")
    }
}

main()
```

- [ ] **Step 2: breakthrough.hexa 구현**

```hexa
// breakthrough.hexa — 정체 감지 → blowup 연동

fn check_stagnation() -> bool {
    // stats.json 에서 최근 3회 ratio 변화 확인
    let home = env("HOME")
    let path = home + "/.n6gate/ratio_history.txt"
    if file_exists(path) == false { return false }
    let content = read_file(path)
    let lines = content.split("\n")
    if lines.len() < 3 { return false }

    // 마지막 3줄의 ratio 비교
    let r1 = to_float(lines[lines.len() - 3])
    let r2 = to_float(lines[lines.len() - 2])
    let r3 = to_float(lines[lines.len() - 1])

    let d1 = r2 - r1
    let d2 = r3 - r2
    let abs_d1 = if d1 < 0.0 { 0.0 - d1 } else { d1 }
    let abs_d2 = if d2 < 0.0 { 0.0 - d2 } else { d2 }

    // 두 차이 모두 1% 미만이면 정체
    return abs_d1 < 0.01 && abs_d2 < 0.01
}

fn trigger_blowup() {
    println("*** STAGNATION DETECTED — triggering blowup ***")
    let hexa = env("HOME") + "/Dev/hexa-lang/target/release/hexa"
    let blowup = env("HOME") + "/Dev/nexus6/mk2_hexa/native/blowup.hexa"
    let seeds = shell(hexa + " " + env("HOME") + "/Dev/nexus6/mk2_hexa/native/seed_engine.hexa merge 2>&1")
    let result = shell(hexa + " " + blowup + " compression 3 --no-graph --seeds \"" + seeds + "\" 2>&1")
    println(result)
}

fn main() {
    println("=== Breakthrough Engine ===")
    if check_stagnation() {
        trigger_blowup()
    } else {
        println("No stagnation detected — compression still improving")
    }
}

main()
```

- [ ] **Step 3: proximity_predictor.hexa 구현**

```hexa
// proximity_predictor.hexa — 바이트 스트림 proximity 예측

fn predict_next(window: [float], codebook_values: [float]) -> float {
    // 윈도우의 마지막 N개 값으로 다음 값 예측
    // 방법: 가장 가까운 코드북 값과의 패턴 반복 추정
    if window.len() < 2 { return 0.0 }

    // 추세선: 마지막 2개의 차이
    let diff = window[window.len() - 1] - window[window.len() - 2]
    let predicted = window[window.len() - 1] + diff

    // 예측값이 코드북에 근접하면 confidence 높음
    let mut best_dist = 999999.0
    let mut i = 0
    while i < codebook_values.len() {
        let d = predicted - codebook_values[i]
        let abs_d = if d < 0.0 { 0.0 - d } else { d }
        if abs_d < best_dist { best_dist = abs_d }
        i = i + 1
    }

    return predicted
}

fn main() {
    println("=== Proximity Predictor ===")
    let codebook = [6.0, 1.618, 4.0, 5.0, 12.0, 2.0, 3.0, 0.333, 137.0, 0.231]
    let window = [2.0, 4.0, 6.0]
    let pred = predict_next(window, codebook)
    println("Window: [2, 4, 6] -> predicted: " + to_string(pred))
    println("Expected: 8.0 (linear trend)")

    let window2 = [1.0, 1.618, 2.618]
    let pred2 = predict_next(window2, codebook)
    println("Window: [1, 1.618, 2.618] -> predicted: " + to_string(pred2))
    println("Expected: ~4.236 (phi progression)")
}

main()
```

- [ ] **Step 4: 전체 실행 테스트**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/mirror_universe.hexa
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/breakthrough.hexa
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/proximity_predictor.hexa
```

- [ ] **Step 5: Commit**

```bash
git add mk2_hexa/native/gate_injection/mirror_universe.hexa mk2_hexa/native/gate_injection/breakthrough.hexa mk2_hexa/native/gate_injection/proximity_predictor.hexa
git commit -m "feat(gate): Mirror Universe + Breakthrough + Proximity Predictor hexa 엔진"
```

---

## Task 13: 통합 테스트 — E1 코드북 기본 실험

**Files:**
- Modify: `mk2_hexa/native/gate_injection/gate_core.hexa` (experiment 커맨드 추가)

- [ ] **Step 1: E1 실험 스크립트 작성**

gate_core.hexa에 `experiment` 커맨드 추가:

```hexa
// gate_core.hexa 에 추가할 함수
fn cmd_experiment_e1() {
    println("=== Experiment E1: N6 Codebook Basic ===")
    println("Hypothesis: n=6 constants appear in natural data → 4bit symbol compression")
    println("")

    // Step 1: 코드북 생성
    let hexa = env("HOME") + "/Dev/hexa-lang/target/release/hexa"
    let codec_result = shell(hexa + " " + env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_injection/n6codec.hexa 2>&1")
    println(codec_result)

    // Step 2: 실데이터 프로파일링
    println("\n--- Real Data Profiling ---")

    // discovery_log 분석 (n=6 상수 출현 빈도)
    let log_path = env("HOME") + "/Dev/nexus6/shared/discovery_log.jsonl"
    let line_count = shell("wc -l < " + log_path + " 2>/dev/null")
    println("  discovery_log entries: " + line_count)

    // 시스템 메트릭에서 n=6 proximity 측정
    let procs = shell("ps aux | wc -l | tr -d ' '")
    let load = shell("sysctl -n vm.loadavg | awk '{print $2}'")
    let ncpu = shell("sysctl -n hw.ncpu")
    println("  system: procs=" + procs + " load=" + load + " ncpu=" + ncpu)

    // Step 3: 렌즈 스캔
    let lens_result = shell(hexa + " " + env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_injection/lens_array.hexa 2>&1")
    println("\n--- Lens Scan ---")
    println(lens_result)

    // Step 4: C dylib 빌드 확인
    let hooks_dir = env("HOME") + "/Dev/nexus6/mk2_hexa/native/gate_hooks"
    if file_exists(hooks_dir + "/libgate_malloc.dylib") {
        println("\n--- dylib: BUILT ---")
        // Step 5: 간단한 프로세스에 주입 테스트
        let inject_result = shell("DYLD_INSERT_LIBRARIES=" + hooks_dir + "/libgate_malloc.dylib /bin/echo 'E1 test' 2>&1")
        println("  inject test: " + inject_result)
    } else {
        println("\n--- dylib: NOT BUILT (run: n6gate build) ---")
    }

    println("\n=== E1 Complete ===")
}
```

- [ ] **Step 2: 통합 실행**

```bash
/opt/homebrew/bin/hexa mk2_hexa/native/gate_injection/gate_core.hexa experiment e1
```

- [ ] **Step 3: Commit**

```bash
git add mk2_hexa/native/gate_injection/gate_core.hexa
git commit -m "feat(gate): E1 실험 — N6 코드북 기본 통합 테스트"
```

---

## Execution Summary

| Task | Component | Language | 의존성 |
|------|-----------|---------|--------|
| 1 | N6Codec C 코어 | C | 없음 |
| 2 | Mirror Universe C | C | 없음 |
| 3 | Gate Common (안전장치) | C | 없음 |
| 4 | libgate_malloc.dylib | C | 1, 2, 3 |
| 5 | libgate_io.dylib | C | 1, 2, 3 |
| 6 | libgate_mach.dylib | C | 1, 2, 3 |
| 7 | N6Codec hexa 레퍼런스 | hexa | 없음 |
| 8 | gate_stats.hexa | hexa | 없음 |
| 9 | gate_core.hexa CLI | hexa | 7, 8 |
| 10 | lens_array.hexa | hexa | 없음 |
| 11 | ouroboros_evolver.hexa | hexa | 없음 |
| 12 | mirror+breakthrough+predictor | hexa | 없음 |
| 13 | E1 통합 테스트 | hexa+C | 1-12 |

**병렬 가능:** Task 1-3 (C 코어), Task 7-12 (hexa 엔진) 동시 진행 가능
