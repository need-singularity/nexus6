# hive ↔ nexus.atlas — recall layer 진입점

> mk2 `atlas <subcmd>` 4-way recall 레이어를 hive 차원에서 호출하기
> 위한 caps 진입점 명세. nexus 측 SSOT:
> [`../mk2/07-atlas-recall.md`](../mk2/07-atlas-recall.md).

---

## 4 caps 진입점 (`hive.json` `caps` 섹션)

| cap | 책임 | invoke | input | timeout_s |
|-----|------|--------|-------|-----------|
| `atlas_lookup` | atlas KB 상수명 조회 (3-stage bloom→predict→cold) | `hx run nexus atlas lookup {constant}` | `{"constant":"string"}` | 30 |
| `atlas_hypothesis` | math_atlas.json 가설 메타 (id/grade/domain/list) | `hx run nexus atlas hypothesis {selector}` | `{"selector":"string"}` | 30 |
| `atlas_recall` | 수치 → n=6 닫힌 대수 best match | `hx run nexus atlas recall {value}` | `{"value":"string"}` | 30 |
| `atlas_distribution` | atlas KB 분포 (sector/ai/grade/constant 4 축) | `hx run nexus atlas distribution --by {axis}` | `{"axis":"string"}` | 30 |

전체 caps JSON 은 `hive.json` 의 `caps` 객체 참조.

---

## 호출 예 (hive consumer 시점)

### Python / hive bus

```python
# 1. 상수 lookup
result = hive.invoke("nexus.atlas_lookup", {"constant": "alpha_inv"})
# stdout = formatted block (n6_value, err, AI tag, sector ...)

# 2. 가설 조회 — 등급 필터
result = hive.invoke("nexus.atlas_hypothesis", {"selector": "--grade=🟥★★★★"})
# stdout TSV 라인: id\tgrade\tdomain\ttitle

# 3. 가설 조회 — 정확 ID
result = hive.invoke("nexus.atlas_hypothesis", {"selector": "SEDI:H-AF-009"})

# 4. 가설 일람
result = hive.invoke("nexus.atlas_hypothesis", {"selector": "--list"})
# 700 줄 TSV

# 5. 수치 recall
result = hive.invoke("nexus.atlas_recall", {"value": "0.231"})
# stdout: best match + alts

# 6. 분포 카운팅
result = hive.invoke("nexus.atlas_distribution", {"axis": "sector"})
# stdout: ranked count table
```

### CLI 직접 호출 (디버깅)

```sh
# hive harness 우회, nexus 직접:
HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1 \
hexa run mk2_hexa/mk2/src/main.hexa atlas lookup alpha_inv
```

운영 안정성을 위해 `HEXA_LOCAL=1` + `HEXA_RESOLVER_NO_REROUTE=1` 필수
(갭 `subprocess-resolver-env-propagation` 참조).

---

## 권장 timeout / limits

`hive.json` 의 `limits` 는 nexus 자원 (1024MB / 600s) 을 따른다.
각 cap 의 `timeout_s` 는 30s 로 설정. 측정 근거:

- 콜드 스타트 (캐시 미스): 5–8 s (subprocess 3-stage fork + JIT init)
- 워밍 후: 1.8–7.2 s (서브모듈별 in-proc 비용 18 ms ~ 3.2 s)
- 30 s 는 ~4× 마진. cold burst 도 안전.

### 예외 처리

- `recall` 의 큰 값 (예: `> 1e6`): 256-mask × 200-denom 비교가 동일 비용
  → 안정 (~50 ms 이내). timeout 충분.
- `distribution`: total 12,413 entry 선형 스캔 → ~3 s. 다른 axis 도
  유사 비용.
- `hypothesis --list`: 700 가설 in-proc 출력 → ~25 ms.

부하가 더 큰 경우 (atlas 데이터셋 ×10 성장 등) `timeout_s` 를 60 으로
상향 권장.

---

## 출력 규약

stdout 은 사용자/소비자 데이터, stderr 는 NDJSON 메타 (3 줄 — main →
atlas → 서브모듈). hive bus 는 stderr 마지막 줄을 trace 메타로 수집,
앞 두 줄은 무시 가능.

```jsonc
{"stage":"recall","duration_ms":35,"value":0.231,"best_err":0}
NEXUS_MK2_ATLAS_DISPATCH {"subcmd":"recall","rc":0,"duration_us":3292093}
NEXUS_MK2_DISPATCH {"command":"atlas","rc":0,"duration_us":4182413}
```

스키마 상세: [`../mk2/07-atlas-recall.md`](../mk2/07-atlas-recall.md) §NDJSON.

---

## 알려진 제약

1. **module-import 부재** — 4 caps 는 모두 nexus 내부에서 다층
   서브프로세스 호출. 호출당 ~150 ms fork 오버헤드. hive 가 4 caps 를
   동일 요청 내 N회 호출할 때 batch API 가 없음.
2. **운영 환경 변수 의존** — `HEXA_LOCAL=1` + `HEXA_RESOLVER_NO_REROUTE=1`
   부재 시 docker/remote 라우팅으로 hang 가능. hive harness 가 cap 호출
   시 이 env 를 inject 해야 안전.
3. **데이터 SSOT 외부** — `n6/atlas.n6` 와 `discovery/math_atlas.json` 은
   nexus 측에서 다른 에이전트가 관리. cap 응답이 이전과 달라지면
   데이터 변경 가능성 우선 의심.

---

## 관련 문서

- nexus 측 사용법 + smoke 측정치: [`../mk2/07-atlas-recall.md`](../mk2/07-atlas-recall.md)
- 아키텍처: [`../mk2/01-architecture.md`](../mk2/01-architecture.md) §`mk2::atlas`
- hexa-lang 갭 (운영/성능 직결): [`../../design/hexa_lang_gaps_from_atlas.md`](../../design/hexa_lang_gaps_from_atlas.md)
- `hive.json` caps 섹션: 본 저장소 루트
