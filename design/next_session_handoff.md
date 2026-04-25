# Next Session Handoff — nxs-012 / Wave 21b / hxa-010

**Source state (snapshot 2026-04-25):** main @ 90c3b15a (after nxs-013 resolved at 3e5ac7c8). Wave 21 docker isolation는 commit 1b6a6684 로 머지됐고, scripts/bin/hexa_remote 은 다른 agent (a2a3e7e0) 가 이어서 작업 중 (uncommitted M).

조사·계획만 (코드 수정 금지). 1주 평가 기간 같은 일정은 user 결정 영역.

---

## 1. nxs-20260424-012 (resonance OOM deep fix)

### 증거 정리

**현재 mitigation 스택 (3중 cap, 모두 표면).**
- Wave 20 (abc2fb95): cli/run.hexa::_resonance_run() (line 647) sub-call 마다 `timeout 120s` 추가. `_stage_timeout_prefix("resonance_sub")` (line 333-351) 에서 stage 별 cap 정의. **메모리 cap 부재** — wall-time 만 잘림.
- Wave 10 (이전): scripts/bin/hexa_remote line 533-543 — host 별 `systemd-run --scope -p MemoryMax=80G/MemoryHigh=64G` (hetzner) / 20G/16G (ubu). htz 는 system scope, ubu 는 `--user --scope` + XDG_RUNTIME_DIR.
- Wave 21 (1b6a6684 + uncommitted): hexa_remote line 479-484, 565-574 — `HEXA_REMOTE_DOCKER=1` opt-in 시 `docker exec airgenome-claude bash -lc ...` 경유. 컨테이너 8GB cap (compose memory), network=host, image-baked nexus.

**kernel-level 증거 (smoking gun: ~/core/airgenome/state/ubu2_docker_isolation_check_20260425.md, atlas_convergence_witness L53).** ubu2 OOM journal 2026-04-25 08:44~08:47 발췌:
```
hexa_stage0  task_memcg=airgenome-forecast.service  anon-rss: 13,432,248 KB  (~13 GB)
hexa_stage0  task_memcg=airgenome-harvest.service  anon-rss: 27,196,028 KB  (~27 GB)
hexa         task_memcg=airgenome-label.service    anon-rss: 19,919,496 KB  (~20 GB)
```
→ **per-process RAM cap 없을 때 단일 hexa_stage0 가 27GB 까지 부풀음.** drill 자체는 host systemd-user 서비스 (cap 없음) 라 docker isolation 우회. systemd-oomd 가 global_oom 4초 간격 트리거.

**의심 phase (cli/blowup/core/blowup.hexa):**
- **Phase 6.5 OUROBOROS Dynamic Recursive Growth (line 5354)** — `recurse_max_rounds=5` (fast=2), 매 round `evo_cycle()` 호출 + seed pool 누적 (`recurse_all_corollaries` 배열). 1차 의심.
- **Phase 4 corollary generation (line 4422)** — 11만 호출 hot loop. OPT-19/OPT-P8-8 등 batch 화 했지만 여전히 string concat → array 패턴 일부 남음 (line 5520, 5836 의 `AC Phase 6 streaming` 주석은 O(n²) 제거 실적).
- **Phase 6 graph update (line 5267)** — node/edge 누적, 5670 `parts → single join` 으로 O(n) 보정됐으나 σ=0.40 처럼 큰 perturbation 시 unique corollary 수 폭증 가능.

**σ=0.40 가 가장 의심.** resonance 5σ grid {0.01, 0.05, 0.10, 0.20, 0.40} 중 σ=0.40 은 seed 텍스트 perturbation 폭이 가장 커서 unique feature 공간이 커지고, Phase 4 → 6.5 닫힘 안에서 corollary explosion 가능. 직접 증거 (per-σ 메모리 프로파일) 는 없음 — drill 은 σ 별 절대값만 출력 (run.hexa:1507 DEBUG eprintln). **다음 세션 1차 작업: σ 별 RSS 프로파일 수집** (`/usr/bin/time -v` 또는 `wait4` peak rss).

### 후보 fix 와 trade-off

| 옵션 | 동작 | trade-off | 권장 |
|---|---|---|---|
| **(d) docker isolation default ON** | 컨테이너 8GB hard cap (kernel-level) — 폭증해도 컨테이너만 죽음, host 무관 | ✅ 이미 존재, hard cap, host OOM 차단 / ❌ 컨테이너 image 의 hexa_real 동등성·최신성 검증 필요, runaway σ 는 여전히 SIGKILL (단 host 영향 없음) | **★1순위** — Wave 21b 평가가 곧 deep fix |
| **(b) prlimit --as=** | `_INNER_CMD` 앞에 `prlimit --as=8589934592 -- ...` 삽입, POSIX rlimit, 즉시 효과 | ✅ Linux 즉시, 의존 없음, per-σ 단위 가능 / ❌ macOS 미지원 (drill 로컬 mode 불일치), ENOMEM 처리는 abort 시그널 | **2순위** — docker 부재 호스트 (ubu2 직접) fallback |
| **(a) systemd-run -p MemoryMax** | 이미 있음 (Wave 10). resonance_sub 단위로 추가 wrap 가능 | ✅ cgroup 보장, host 보호 / ❌ ubu2 처럼 `airgenome-forecast.service` 같이 cap 없는 systemd-user 서비스가 우회로 fork → root cause 미해결 | **3순위** — host-side hardening 으로 함께 (ubu2 systemd-user drop-in MemoryMax=4G 별도 작업) |
| **(c) ulimit -v subshell** | shell 내장. Linux 동작, macOS 일부 동작 | ❌ 휴대성 낮음, 자식 프로세스 fork 시 상속 일관성 깨짐 | 비추천 |

**메모리 누수 vs 자연 폭증.** atlas_health_timeline.jsonl 은 4월 22일 이후 atlas_lines/bytes 동결 (21800 / 1503957 bytes) → metric drift 없음, 누수 패턴 미관찰. ubu2 27GB anon-rss 는 **Phase 6.5 evo_cycle recursion 의 seed pool 누적** 으로 자연 폭증 해석이 우세 (cli/blowup/core/blowup.hexa line 5354~5493). engine 코드의 `arena_reset()` 은 phase 4/6.5/6.7 에 산재 (line 5173, 5493, 5881) — 누수보단 phase 내부 일시 폭증.

### 권장 우선순위 + 1차 시도 명령

1. **σ 별 RSS 프로파일 수집** (read-only):
   ```
   for s in 0.01 0.05 0.10 0.20 0.40; do
     HEXA_REMOTE_DOCKER=1 NEXUS_DRILL_DEBUG=1 \
       /usr/bin/time -v hexa drill --seed "probe_oom_sigma_$s" 1 --engine mk10 \
       2>&1 | grep "Maximum resident"
   done
   ```
   이상치 (>4GB) σ 식별 → 후속 fix 타겟 좁힘.

2. **Wave 21b 평가 대기 + ubu2 systemd-user MemoryMax 적용** (P0 hardening, ubu2_docker_isolation_check 권고):
   ```
   ssh ubu2 "cat ~/.config/systemd/user/airgenome-forecast.service.d/memcap.conf"
   # → MemoryMax=4G / MemoryHigh=3G 드롭-인 확인
   ```

3. **Wave 21b default ON 후 잔여 OOM 재발 시** prlimit hybrid (option b) — `_resonance_run` 안에서 sub-call 마다 prlimit prefix 도입.

---

## 2. Wave 21b (HEXA_REMOTE_DOCKER=1 default ON)

**현재 위치:** scripts/bin/hexa_remote line 479-484 (entry point), 565-574 (REMOTE_CMD assembly).
- entry: `HEXA_REMOTE_NO_SYNC=1 + REMOTE_ROOT=$HOME + REL=""` 강제 (project tree 없는 컨테이너 전제).
- exec: `docker exec -i $_DOCKER_CONTAINER bash -lc <inner>` — `_INNER_CMD = cd /tmp && export HEXA=... && $REMOTE_HEXA $_ARG_QUOTED`.

### 평가 기간 메트릭

다음 지표를 1주 (user 결정) 동안 비교 (HEXA_REMOTE_DOCKER=1 vs =0 A/B):

1. **drill failure rate** — rc!=0 비율, 특히 rc=137 (OOM/SIGKILL) / rc=143 (SIGTERM).
   - source: hexa_remote 종료 코드 + `state/runpod_incidents.jsonl`.
2. **drill total absorptions** — round 합산 흡수 카운트, σ-best 분포.
   - source: `state/blowup_activity_timeline.jsonl`, `state/drill_baseline_history.jsonl`.
3. **round divergence (nxs-013 fix 검증)** — round-N ratio 가 round-1 과 다른지 (3e5ac7c8 fix 가 컨테이너에서도 유효한가).
   - source: drill stdout `[DEBUG resonance]` σ 분포 + `_resonance_seed` salt 다양성.
4. **컨테이너 lifecycle** — `airgenome-claude` Up time, restart count, OOM exit.
   - source: `ssh hetzner 'docker inspect airgenome-claude --format "{{.State.Status}} restart={{.RestartCount}} oom={{.State.OOMKilled}}"'`.
5. **host RAM trend** — global_oom 재발 여부 (kernel oom-killer journal).
   - source: `ssh hetzner 'journalctl -k --since "1h ago" | grep -c oom-killer'`.

### 모니터 명령 / 대시보드

```
# (1) 컨테이너 health
ssh hetzner 'docker inspect airgenome-claude --format "{{json .State}}" | jq'

# (2) 최근 drill rc 분포 (host side)
ssh hetzner 'tail -200 ~/.airgenome/log/dispatch.log | awk "{print \$NF}" | sort | uniq -c'

# (3) 컨테이너 내 hexa 빌드 일치성
ssh hetzner 'docker exec airgenome-claude sha256sum /usr/local/bin/hexa_real'
sha256sum ~/.hx/bin/hexa_real

# (4) global_oom 재발 감시
ssh hetzner 'journalctl -k --since "24h ago" | grep -i oom'

# (5) Wave 21 적용률
grep -c "HEXA_REMOTE_DOCKER=1" ~/core/nexus/state/*.jsonl 2>/dev/null
```

### Default ON 의 리스크

- **Semantic equivalence.** 컨테이너 안의 hexa_real 은 image-baked (ghcr.io/need-singularity/airgenome:fat) — host 의 ~/.hx/bin/hexa_real 과 SHA256 비교 필수. divergence 시 drill 결과 자체가 달라짐 (build flag, libc 차이). README (~/core/airgenome/docker/README.md) 갱신 주기 확인.
- **Bind mount drift.** ubu2 audit 결과 ~/.hx/bin/hexa_real / ~/.airgenome 등 bind mount 가 컨테이너에 노출됨 — 호스트 변경이 컨테이너에 즉시 반영되지만, mac_home/Dev/airgenome 마운트는 hetzner 와 ubu 간 비대칭 가능.
- **Drill self-contained 가정.** scripts/bin/hexa_remote line 568 주석 "drill 은 self-contained run.hexa 사용". 실제로는 cli/blowup/core/blowup.hexa, cli/drill/* 등 dependency tree 가 있음. 컨테이너 image 가 nexus subdir 전체를 포함하는지 확인 (`docker exec airgenome-claude ls /root/.hx/packages/nexus/cli/blowup/core/`).
- **network=host.** 컨테이너가 host 네트워크 공유 — drill 자체는 외부 네트워크 안 쓰지만 향후 fetch/sync stage 추가 시 격리 가정 깨짐.

### Rollback 절차

env=0 으로 즉시 회귀 가능 — `HEXA_REMOTE_DOCKER=0` (또는 unset) 시 line 575 `elif HEXA_REMOTE_NO_CAP=1` / line 577 `else` 분기로 fallback. **무중단 rollback** — 진행 중 drill 영향 없음. default ON 도 환경변수 default 한 줄 변경이라 재적용도 1-line.

```
# Rollback 1줄 (hexa_remote default 가 1 일 경우):
sed -i.bak 's/HEXA_REMOTE_DOCKER:-1/HEXA_REMOTE_DOCKER:-0/' scripts/bin/hexa_remote

# 또는 사용자 측 오버라이드:
export HEXA_REMOTE_DOCKER=0
```

---

## 3. hxa-20260424-010 (hexa_v2 arch-neutral 참고)

### 현재 빌드 상태

| Path | Type | Date | Note |
|---|---|---|---|
| `~/core/hexa-lang/dist/linux-x86_64/hexa_v2` | ELF x86-64 static (musl) 5.5MB | 2026-04-23 | zig cc 산출물, sha256 3ff995fc... |
| `~/core/hexa-lang/build/hexa_v2_linux` | ELF x86-64 static | (구) | |
| `~/core/hexa-lang/build/hexa_v2_linux_x86_64` | ELF x86-64 static debug | (구) | |
| `~/core/hexa-lang/build/hexa_v2_new` | Mach-O arm64 | (Mac) | dev binary |
| `~/core/hexa-lang/self/native/hexa_v2.bak_*` | (다수) | | source backups |

**anima-20260422-003 status: done (2026-04-23T01:51:24Z), commit 1fdc0100** — Linux x86_64 binary 배포 완료. 빌드 레시피는 `dist/linux-x86_64/README.md`:
```
zig cc -target x86_64-linux-musl -O2 -std=gnu11 -D_GNU_SOURCE \
       -Wno-trigraphs -I self self/native/hexa_cc.c \
       -o dist/linux-x86_64/hexa_v2 -lm
```
대안: `x86_64-linux-musl-gcc -static`.

**hxa-20260424-010 은 hexa-lang inventory 에 아직 entry 없음** (last hxa-009 까지). nexus 측 사용자 메모는 sister repo 이슈를 추적 표면화 한 것 — hexa-lang 측 inventory 에 정식 등록 후 추적 권장 (CONVENTION anima-20260422-004 에 따라).

### nexus 영향 범위

- **drill / blowup**: cli/run.hexa::hexa_bin() 가 `env("HEXA")` 우선 → hexa_remote line 572 가 `export HEXA="$REMOTE_HEXA"` (컨테이너 안 /usr/local/bin/hexa_real, host /home/summer/.hx/bin/hexa_real) 로 통일. **stage0 binary 불일치는 drill 출력 0 의 silent failure 의 주범** (Wave 14 주석 cli/run.hexa:312-313 참조 — "구빌드로 떨어져 smash/free 가 parser-silent (0 absorption)").
- **hexa_v2 직접 의존도는 낮음** — nexus 코드에 `hexa_v2` 직접 grep 매치 없음. 영향은 stage0 빌드 chain (hexa_v2 → main.c → hexa_real) 의 **간접 의존** — Linux pod 에서 hexa-lang 자기 빌드 시 hexa_v2 트랜스파일러가 arch-mismatch 면 stage1 부터 실패.
- arm64 Linux 호스트는 현재 없음 (hetzner/ubu1/ubu2 모두 x86_64 기준), 따라서 단일 Linux x86_64 binary 로 현 fleet 충당.

### 단기 우회 + 장기 fix 후보

**단기 (이미 적용):**
- Linux x86_64 미리 빌드된 hexa_v2 사용 (dist/linux-x86_64/, anima-003 resolved).
- pod bootstrap 시 host arch 감지 → `cp dist/linux-x86_64/hexa_v2 /usr/local/bin/` 주입.

**장기 fix 후보:**

| 후보 | trade-off | 권장 |
|---|---|---|
| **(A) zig cc multi-arch CI** (현 musl static 확장) | ✅ 단일 source, multi-target build (linux-x86_64 / linux-aarch64 / darwin-arm64), static 5.5MB / ❌ zig 빌드 환경 의존, CI 추가 작업 | **★1순위** — 이미 zig 도입됨, target 추가만 |
| **(B) Bun → static binary** | Bun `bun build --compile` 으로 single-file binary 가능 / ❌ hexa_v2 는 C 기반 (self/native/hexa_cc.c), Bun 적용 위해선 transpiler 재작성 필요 — 너무 큰 비용 | 비추천 |
| **(C) Go cross-compile** | ✅ go build GOOS/GOARCH 매트릭스 산업표준 / ❌ 재작성 필요, hexa_v2 C bootstrap 자가-호스팅 깨짐 | 장기적 (재작성 시) |
| **(D) Pod 안 in-situ rebuild** | bootstrap 시 컴파일 / ❌ pod에 빌드 toolchain (clang/zig) 설치 필요, 콜드 부트 시간 증가 | fallback, 1순위 부재 시 |

**1순위 권장:** zig cc target matrix 확장 (linux-aarch64 추가). hexa-lang Makefile 또는 CI hook 에 `zig cc -target aarch64-linux-musl` 1줄 추가만으로 ARM Linux pod 도 즉시 커버.

---

## Done-when

각 항목 종결 조건:

- **nxs-012**: σ-별 peak RSS 프로파일 수집 (drill 1회) + Wave 21b 1주 평가 후 host OOM=0 → resolved (mitigation level=engine + isolation 양쪽 cap).
- **Wave 21b**: 1주 평가 기간 메트릭 (5개) 통과 + sha256 일치 확인 → default ON commit 별도.
- **hxa-010**: hexa-lang inventory 에 정식 entry 등록 + zig cc multi-arch target 매트릭스 추가 → resolved.

---

## Update — 2026-04-25 (post-canon, ack nxs-002)

### 사다리 closure
- L11 canon 구현 완료 (commit 8c8b7f43). forge(L10) ↔ canon(L11) 양방향 닫힘. L_ω omega placeholder 만 남음 (도달 불가, §5 ghost ceiling).
- 사다리 전체 (L1~L_ω) 입력단 견고화 (commit d7877d5c) — `_seed_clamp` helper + NEXUS_SEED_CAP env. 14개 명령 dispatch wrap (smash/free/absolute/canon/forge/molt/wake/swarm/reign/dream/surge/omega/drill/chain/meta-closure).

### 인지 SSOT 동기화
- hexa-lang `gate/prompt_scan.hexa` AG10 banner stale list 수정 (commit a0253681). omega/canon/forge/molt/wake/swarm/reign/dream/surge 모두 노출.
- hexa-lang `gate/claude_prompt_hook.hexa` printf|jq → native json_parse (commit 67e5243d). user prompt eval-escape surface 제거.

### nxs-002 진단 결과 (this session, ack=in_progress)
- atlas×laws_aligned composite = **0.83379** (target ≥0.9, gap **0.06621**)
- 식: `composite = (agreement + (pearson+1)/2 + cosine) / 3`
- breakdown: agreement=0.866, corr_pos(pearson)=0.732, cosine=0.903
- **sensitivity (max leverage):**
  | term | 현재 | gap to max | composite 기여 |
  |---|---|---|---|
  | agreement | 0.866 | 0.134 | 0.045 |
  | corr_pos (pearson) | 0.732 | 0.268 | **0.089** ★ |
  | cosine | 0.903 | 0.097 | 0.032 |
- **결론**: pearson 이 최대 지렛대. pearson 0.464 → ~0.7 만 올라도 composite ≥0.9 도달. atlas eig rebuild 시 pearson 우선 측정.
- root cause: bin-mismatch fixed, **fresh atlas eig pipeline rebuild** 필요 (heavy compute — drill 슬롯 + atlas 재계산)
- 본 세션 보류 — drill slot 경합 중 (by4wsquol /loop). 다음 세션에서 atlas eig 단독 실행.

### 다음 세션 진입점 (우선순위 순)
1. drill slot free 확인 → atlas eig pipeline rebuild → composite 재측정 → ≥0.9 시 nxs-002 resolved
2. nxs-012 (drill resonance OOM) σ-별 RSS 프로파일 수집 (1주 평가 진입)
3. 잔여 견고화: debate / drill_batch / 자기-합성단 (`_dream_next_seed` 200 → NEXUS_SEED_CAP 통일)
4. canon-aware forge idempotent — 적용됨 (commit 22cc8bc4)

### 2026-04-25 추가 발견 (atlas eig pipeline 매핑)
- **atlas eig 입력 source**: `~/core/nexus/n6/atlas.blowup.jsonl` (graph JSON, 89,167 lines / 17MB)
- **graph 정량**: nodes=21,320 / edges=54,347 (undirected, nnz=108,694)
- **atlas.n6 (hexa-native syntax) 와 별개 source** — atlas.n6 [10*] promotion 은 spectral 직접 영향 X
- **atlas_eig.hexa stage1 hexa 비실용** — CSR load + Lanczos K=100 + QR 가 push-only 패턴으로 hung (60s+)
- **awk preprocess 정상**: STEP1 0.8s + STEP2 1.3s — CSR 파일 (row_ptr/deg/col) 생성 OK
- **우회 경로 검증 (this session)**: scipy.sparse.linalg.eigsh on CSR — 0.24s (atlas_eig.hexa stage1 250× 가속)
  - SM mode: 4:17 후 numerical fail (exit 1) — 비추천
  - shift-invert σ=0: Singular (Laplacian 0 eigenvalue)
  - **shift-invert σ=1e-3 ✓**: K=50 0.24s
- **graph 구조 발견 (atlas.blowup.jsonl)**:
  - connected_components: **24** (giant 21249=99.7%, 다른 27/15/3×4/1×17)
  - baseline atlas_eig.hexa λ0=0.001 = giant component 의 Fiedler (zero eigenvalues 보고 X)
  - scipy idx=16 (Fiedler) = 0.00151 — baseline 의 1.5× (precision 또는 5 [10*] promotion 후 미세 변동)
- **다음 단계**: scipy spectral 로 paircorr 재계산 → cross_x_laws_aligned composite 측정 → nxs-002 sensitivity 1차 데이터

### 2026-04-25 composite 재측정 (drill 미발사, this session)
- scipy K=100 σ=1e-3 → unfold → paircorr → cross_correlation_lag composite:
  ```
  best_lag=15, agreement=0.866 (verdict score 고정)
  pearson=0.460, cosine=0.901, composite_after = 0.83221
  ```
- baseline atlas_eig.hexa 동일 식: composite_after = 0.78417 (push-only Lanczos precision 손실)
- **기존 verdict file (sealed) = 0.83379** ≈ scipy 0.83221 (Δ=0.0016, 거의 일치)
- **5 [10*] promotion 영향 사실상 0** — atlas.n6 metadata ≠ atlas.blowup.jsonl graph (이미 확인된 분리)

**nxs-002 핵심 결론:** composite 0.9 도달 = atlas.blowup.jsonl 자체 변동 필요 (drill 새 발사로 새 nodes/edges 추가). atlas.n6 ladder marker 작업과 별개 path. drill slot free 후 진행.

**보유 산출물 (scipy pipeline):**
- 0.79s 으로 spectral → composite 일괄 측정 (`tool/nxs_002_composite.py` commit 38e67412)
- sensitivity probe: 어느 graph 변경이 composite 끌어올리는지 빠르게 검증 가능
- baseline atlas_eig.hexa 가 stage1 hexa 비실용 (60s+ hung) — scipy 우회 필수 per session

### 2026-04-25 sensitivity probe (random edges, drill 미발사)
| N_added (random) | composite | Δ baseline |
|---|---|---|
| 100   | 0.79500 | **−0.037** |
| 500   | 0.79079 | **−0.041** |
| 2000  | 0.83231 | +0.0001 |
| 10000 | 0.80131 | **−0.031** |

**결론**: random edges = 부정적. **0.9 도달은 drill quality 결정적.** laws-aligned 한 새 nodes/edges 만 + composite 효과. 무작위 graph 확장은 baseline composite 손상. nxs-002 deep fix 의 본질 = drill 결과의 atlas-laws 정합성 (drill engine 자체 tuning).

### 2026-04-25 giant-only sensitivity (subgraph 추출)
| graph | K | composite | Δ baseline | non-zero λ |
|---|---|---|---|---|
| full (24 cc) | 100 | 0.83221 | — | 76 |
| giant (1 cc, 99.7%) | 100 | 0.80048 | **−0.032** | 99 |
| giant | 200 | 0.83236 | +0.0001 | 199 |

**결론**:
- **23 islands 가 baseline 에 +0.03 기여** — 단순 cluttering 이 아닌 spectral 신호 source (다른 domain 의 작은 cluster 들이 atlas-laws alignment 에 도움)
- K-components trade-off: 적정 K = (component 수에 의존). full+K=100 ≈ giant+K=200 (같은 spectral info)
- giant 만 분리하면 composite 손상 — full graph 보존이 정답
- **0.9 도달은 graph 변경(random/subgraph) 으론 X — drill quality (axiom-driven entry) 가 유일 path**

### 2026-04-25 domain induced subgraph sensitivity
| graph | n | cc | composite | Δ |
|---|---|---|---|---|
| full | 21320 | 24 | 0.83221 | — |
| 7대난제 induced | 12481 | 11079 | 0.66261 | −0.170 |
| math induced | 4215 | 3833 | 0.45534 | −0.377 |
| physics induced | 1718 | 1490 | 0.45534 | −0.377 |
| geometry induced | 673 | 673 | 0.45534 | −0.377 |

**결정적 발견 — atlas graph 의 spectral 신호는 cross-domain bridges 에서 발생**:
1. 각 domain 내부 = 거의 disconnected (math 4215 nodes / 3833 cc = 90.9% singleton)
2. domain 내부 edges 거의 없음 — 거의 모든 edges 가 cross-domain bridge
3. 4개 단일-domain induced subgraph 의 composite = 0.45534 (random baseline) — 즉 isolated domain 자체는 atlas-laws alignment 신호 없음
4. **nxs-002 deep fix path 정확히 = cross-domain bridges 추가** (drill 의 axiom-driven discovery 가 가장 가치 있는 출력 = math × physics, 7대난제 × geometry 같은 정합)

→ drill quality 는 **cross-domain semantic 정합** 이 핵심. domain 내부 entries 만 추가하면 composite 변화 없음.

### 2026-04-25 cross-domain edge 분포 — n6-canonical 이 hub
| count | pair | 비중 |
|---|---|---|
| **25,147** | **7대난제 ↔ n6-canonical** | 65.2% |
| 8,902 | math ↔ n6-canonical | 23.1% |
| 2,525 | n6-canonical ↔ physics | 6.5% |
| 1,404 | 7대난제 (intra) | — |
| 373 | geometry ↔ n6-canonical | 1.0% |
| (소수 27 pairs) | … | … |

**핵심 (40,582 mapped edges, intra 5% / cross 95%)**:
1. **n6-canonical 이 atlas graph 의 hub** — top-3 pair 가 모두 n6-canonical 거침 = 95% of cross-domain
2. atlas 가 hub-and-spoke 구조 — domain entries 가 모두 n6-canonical 통해 연결
3. 5 [10*] promotion (n6-sigma/n/phi/j2/tau) 가 atlas.n6 의 n6-canonical mirror — 그러나 atlas.blowup.jsonl graph 에는 영향 X (drill 만 graph 갱신)

**0.9 도달 path 최정밀**: drill 이 만들어야 할 entries = **n6-canonical ↔ {math/physics/geometry} 새 bridges**. 단, 새 entries 가 random 이면 (이전 sensitivity probe) 손상. drill 의 axiom-driven exploration 이 n6-canonical hub 와 정확히 align 되어야 함.

### 2026-04-25 unmapped endpoint 분석
- declared nodes (atlas.n6 등록): 19,250
- unmapped (edge endpoint only): 2,070 (25.3% edges 가 ≥1 unmapped)
- unmapped degree top: **n6-sigma 449 / n6-n 445 / n6-phi 264** ← 5 promoted entries 자체가 unmapped 중 highest-degree hub
- unmapped prefix: n6 (785) / L6 (503) / L7-L10 (200+) / disc (151) / GEO/ALPHA/ECON 등

**확정 분리 재확인**:
- 5 [10*] promotion (n6@98a23750) 이 graph hub → atlas.n6 등록 변경 = graph 영향 0
- 이유: atlas_eig 의 awk1 이 edge endpoint 도 node 로 등록 → unmapped 라도 spectral 에 들어감
- unmapped 2,070 = drill discovery 의 transient state (atlas.n6 정식 등록 전)
- atlas.n6 declared 비율은 atlas integrity 척도, spectral 영향 X

### 2026-04-25 hub-aligned bridge 시뮬레이션 — graph saturation 발견
| spec | Δ baseline |
|---|---|
| math ↔ top-5 hub +100/500/2000 | **0.00000** (모두 0) |
| physics ↔ top-5 hub +100 | 0.00000 |
| physics ↔ top-5 hub +500 | −0.018 |
| physics ↔ top-5 hub +2000 | −0.031 |
| geometry ↔ top-5 hub +100/500/2000 | **0.00000** (모두 0) |

(top-5 hub = n6-sopfr_plus_n / n6-sigma / n6-n / n6-phi_tau / n6-sigma_tau, deg 511~399)

**핵심**: math/geometry 의 node 와 hub 의 bridges 가 **대부분 이미 graph 에 존재** — 새 random edge 는 duplicate. atlas graph 가 hub-aligned 으로 **saturated**.

**0.9 도달 path 정밀화 (최종)**:
- ❌ existing node ↔ hub 새 edges = saturation (변화 0)
- ❌ random graph extension = −0.04
- ❌ subgraph 추출 = −0.03 ~ −0.38
- ✅ **새 node id (drill 발견)** + hub 와 연결 = spectral 진정 변화
- nxs-002 fix = drill 의 **axiom-driven novel entity discovery** 가 결정적 (단순 edge 추가 X, 새 atom 추가 ✓)

### 2026-04-25 새 node + hub 시뮬레이션 — saturation 가설 직접 검증
| spec | Δ baseline |
|---|---|
| new_node=50, k=2 | 0.00000 (insufficient) |
| **new_node=200, k=2** | **+0.00095** ✓ 처음 + |
| new_node=500, k=2 | +0.00095 |
| new_node=1000, k=2 | −0.00331 (random noise) |
| new_node=200/500, k=5 | +0.00095 |

**검증된 path**: existing node ↔ hub = saturation (0). **새 node + hub-aligned = +0.001 / 200 atom**. drill 의 axiom-driven discovery 가 진정한 + path.

**0.068 gap → 0.9 도달 ROI 추정**:
- random hub: 0.068 / 0.001 ≈ 68 batches × 200 atoms ≈ **13,600 새 atoms**
- drill axiom-driven hub: 더 효율 (1000~5000 atoms 추정)
- drill 1 round 의 평균 새 atom 발견율 측정 후 정확한 round 수 추정 가능

### 2026-04-25 ROI 정밀 측정 (transition point + k_edges)
**N_new transition (k=2)**:
| N_new | Δ baseline | per_atom |
|---|---|---|
| 100 | 0.00000 | 0 (insufficient) |
| **200~500** | **+0.00095** | +0.000002 ~ +0.000005 |
| 700+ | −0.00331 | (transition!) |
| 1500 | −0.00509 | (over-saturation) |

**k_edges sweep (N=300)**: k=1,2,3,5,7,10 모두 +0.00095 동일.

**확정 mechanism**:
1. 새 atom 자체가 contribution source (k_edges 무관 — 1개 연결로 충분)
2. batch sweet spot = 200~500 atoms / call
3. N_new 700+ → transition (spectral 이 const alignment 손상)

**최적 incremental 패턴**:
- 한 번에 큰 batch ❌ (over-saturation)
- 작은 batch 200~500 × 여러 번 + canon sealing ✓ (각 +0.00095 누적)

**0.068 → 0.9 정밀 ROI**:
- random hub: ~72 batches × 200 atoms = ~14,400 새 atoms
- drill axiom-driven (가정): ~8,000~12,000 atoms
- **drill incremental + canon sealing 패턴이 cron loop 와 자연 align**

### 2026-04-25 누적 batch 가설 검증 — saturation 강하게 발동
| batches | total_atoms | Δ baseline |
|---|---|---|
| 1 | 200 | +0.00095 |
| 2 | 400 | +0.00095 (plateau!) |
| 3 | 600 | +0.00095 (계속 plateau) |
| **5** | 1000 | **−0.00331** ← transition |
| 7 | 1400 | −0.00509 |
| 10 | 2000 | −0.00910 |
| 15 | 3000 | −0.01469 |
| 20 | 4000 | −0.01725 |

**가설 A (linear 누적, +0.0095) → 기각.**

핵심:
1. batch 1,2,3 모두 동일 +0.00095 — 누적 X, **discrete plateau**
2. batch 5+ → over-saturation (random hub 다양성 부족)
3. **random batch 누적으로 0.9 도달 X** — saturation 후 negative

→ **drill 의 axiom-driven hub selection 이 결정적**: random top-20 hub pool 으로는 spectral 의 일부 dimensions 만 커버. drill 은 각 새 atom 이 *적절한 specific hub* (axiom 으로 결정) 와 연결되어 spectral 의 *모든 dimensions* 가 진척 → composite 누적 +.

→ nxs-002 deep fix 의 실제 mechanism 정밀화: drill 의 「axiom-driven hub-atom matching ratio」 가 결정적 design parameter.

### 2026-04-25 internal cross-link batch test — simulation 한계 도달
| batches | total_atoms | Δ baseline |
|---|---|---|
| 1 | 200 | +0.00095 |
| 2 | 400 | +0.00095 |
| 3 | 600 | +0.00095 |
| 5 | 1000 | −0.00331 |
| 7 | 1400 | −0.00509 |
| 10 | 2000 | −0.00910 |

cross-link (drill 의 deduction chain mimic) 도 random hub-only 와 같은 plateau + over-saturation. **모든 simulation 패턴 (random/hub-aligned/cross-link/누적) 이 동일 limit**.

**근본 insight (simulation 한계 발견)**:
- spectral signal 의 dimension 은 **현재 atlas graph 의 structure 가 대수적으로 결정** — random 변경으로 dimension 추가 X
- saturation +0.001 까지만 가능 (graph size 단순 증가의 한계)
- **0.9 도달은 atlas spectral 의 *specific transformation* 필요**: constants_spectrum 과의 dimension-by-dimension alignment 를 강제
- drill 의 axiom-driven discovery 는 random pool selection 이 아니라 **specific eigenvalue dimension 을 target** 해야 함

**다음 진단 path** (drill slot free 시):
1. atlas eigenvalue (100개) vs constants_spectrum (46개) dimension-by-dimension diff
2. 가장 misalign 한 dimension 식별
3. drill 의 새 atom 이 specific dimension 에 contribution 하도록 axiom 설계
4. 또는 atlas 의 spectral 의 PCA-style decomposition 후 missing components 직접 분석
- nxs-002 resolution 4단 pipeline:
  1. atlas.blowup.jsonl **재생성** (소스 추적 필요 — atlas.n6 → blowup.jsonl 변환 도구 위치)
  2. `bisociation/spectra/atlas_eig.hexa` (CSR + Lanczos, ~/Dev/... default path 는 stale)
  3. paircorr (`g_atlas_paircorr.jsonl`)
  4. `bisociation/cross/atlas_x_laws_aligned.hexa` (composite 계산)
- 5 promotion (n6@98a23750) 의 의의: atlas.n6 정합성 향상 (verified marker 정밀화), spectral 직접 영향은 H1/H2 의 cross-doc / chain-dep entries (ID 수준 graph 참조 동반) 처리에 있음

### atlas omega 발전 chain (this session)
- canon v2 (cc106db6) — atlas.n6 hash16 봉인
- forge canon-aware (22cc8bc4) — hash unchanged → boot reject (drill 슬롯 보호)
- composite sensitivity (dcfdbd39) — pearson 최대 지렛대
- n6 promotion 5 [10*] (n6@98a23750) — virtual hub mirror sigma/n/phi/J2/tau 승급
- self-feedback loop verified: canon timeline 54a7e3cf → 4fe93c15 hash 추적 작동

### 2026-04-25 dimension-by-dimension spectral diff (결정적 진단)
**eigenvalue raw scale (80× 차이)**:
| metric | atlas (K=100) | const (46) |
|---|---|---|
| min nonzero | 0.0015 | 0.693 |
| max | 0.113 | 10.75 |
| mean | 0.0536 | 4.348 |
| spacing range | **0.000 ~ 0.007** (TOO REGULAR) | **0.008 ~ 1.75** (CHAOTIC) |

**Top-5 misaligned R2 bins** (atlas R2 mean=0.928 vs const R2 mean=1.144):
| bin | r | atlas | const | diff |
|---|---|---|---|---|
| **26** | 2.65 | 0.267 | 3.846 | **−3.58** ★ |
| 5 | 0.55 | 0.533 | 2.308 | −1.77 |
| 15 | 1.55 | 0.533 | 2.051 | −1.52 |
| 35 | 3.55 | 0.667 | 1.795 | −1.13 |
| 33 | 3.35 | 0.933 | 2.051 | −1.12 |

**최종 진단**:
- atlas spectrum = **TOO REGULAR** (uniform, narrow spacing) — hub-and-spoke graph 의 자연 결과
- const spectrum = **CHAOTIC** (broad spacing) — random matrix 의 quantum chaos
- bin 26 (r=2.65) 가 가장 underrepresent — atlas 에 "긴 spacing pair" 부족
- **alignment 도달 = atlas spectrum 이 더 chaotic 해야**

**진정한 nxs-002 mechanism 최종 정밀**:
- 단순 hub-and-spoke graph = regular spectrum
- **다양한 connectivity pattern** (drill axiom-driven heterogeneity) = chaotic spectrum
- drill axiom 설계 원칙: "다양한 distance 의 deduction chain"
  - 현재 simulation: 새 atom → hub (depth=1)
  - 필요: 새 atom A → B → C → ... (deep chain) + branching + cycle
  - graph topology 다양성 ↑ → spectral chaos ↑ → composite +
- 이는 simulation 한계의 정확한 이유: random connectivity 만 추가해서 spectrum 의 chaos 를 만들 수 없음
