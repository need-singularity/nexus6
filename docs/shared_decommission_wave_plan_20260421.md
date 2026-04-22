# ~/shared Decommission Wave Plan (2026-04-21)

## 목적

~/shared (586M 잔존) 완전 폐기를 4 wave 단계별로 안전 실행한다.
기초 플랜 `docs/shared_decommission_20260421.md` (9-step 기본안) 을 **위험도 기반 wave** 로 재편성하여 각 단계마다 Go/No-Go 체크, 롤백 지점, 병렬성 추천을 명시한다.

## 교차 참조

- 기초 플랜: `/Users/ghost/core/nexus/docs/shared_decommission_20260421.md` (263 줄)
- SSOT: `/Users/ghost/core/.workspace`
- Memory: `/Users/ghost/.claude/projects/-Users-ghost-core-hexa-lang/memory/project_shared_decommission.md`
- 전체 tarball: `/Users/ghost/etc/shared-backup-20260421-110801.tar.gz` (140M, sha256 미기록 — wave 시작 전 기록 필수)

## 사용자 지시사항 반영 (필수 준수)

1. **로드맵 변환 패스**: ~/config/roadmaps/ 는 사용자가 재생성 예정. tarball 보존만 하고 별도 이관 금지. 삭제 허용.
2. **ROI/TODO 관련 섹션 배제**: 본 문서·스텁·검증 결과물에 ROI/TODO 언급 금지.
3. **안전 최우선**: 각 wave 는 독립 롤백 가능해야 하며, 실패 시 다음 wave 차단.

## 현재 상태 요약 (2026-04-21 측정)

| 경로 | 크기 | 용도 | 비고 |
|------|------|------|------|
| ~/shared 전체 | 586M | 이중 SSOT 잔존 | wave A~D 로 해체 |
| ~/discovery | 400M | 과학적 산출물 | nexus/discovery 와 중복 (77M) |
| ~/calc | 64M | 계산 캐시 | nexus/calc 와 중복 |
| ~/dse | 39M | DSE 출력 | nexus/dse 와 중복 (12M) |
| ~/n6 | 27M | atlas + 확장 파편 | n6-architecture 로 canonical 이관 |
| ~/sim_bridge | 21M | 시뮬 브리지 | nexus/sim_bridge 와 중복 |
| ~/hexa | 5.1M | hexa 포팅 로그 | hexa-lang 으로 이관 |
| ~/logs | 5M | 런타임 로그 | 폐기 |
| ~/bt | 2.2M | bt 감사 결과 | nexus/bt 와 중복 |
| ~/state | 2.4M | 런타임 상태 | nexus/state 와 중복 |
| ~/bisociation | 1.4M | bisociation | nexus/bisociation 와 중복 |
| ~/roadmaps | 1.1M | JSON 로드맵 | **사용자 재생성 예정** (tarball 만 보존) |
| ~/consciousness | 1.5M | 의식 모델 | nexus/consciousness 와 중복 |
| ~/papers | 604K | 논문 관련 | papers/ 로 이관 or 폐기 |
| ~/reports | 72K | 리포트 | 폐기 (tarball) |
| ~/patches | 88K | 패치 | 폐기 (tarball) |
| ~/bench | 164K | 벤치마크 | nexus/bench 로 이관 |
| ~/bridge_state.json | 256K | 런타임 | 폐기 |
| ~/growth_bus.jsonl | 2.5M | 이벤트 버스 | 폐기 (tarball) |
| ~/config/ | 1.9M | infrastructure 등 | nexus/config 와 중복 검토 |
| ~/.runtime | 4K+ | 활성 launchd 상태 | **wave C 에서 owner 결정** |

### 활성 inbound 심볼릭 (끊어지면 장애)

- `/Users/ghost/core/anima/shared -> /Users/ghost/shared` (anima 전체 shared 참조)
- `/Users/ghost/core/nexus/.runtime -> /Users/ghost/.runtime` (nexus runtime)
- `/Users/ghost/core/anima/.shared -> ../nexus/shared` (안전, nexus 경유)
- `/Users/ghost/core/papers/.shared -> ../nexus/shared` (안전, nexus 경유)

### nexus repo 상태 (2026-04-21 11:45 기준)

```
M  cli/run.hexa   (staged)
UU shared/tool/roadmap_calibration.json   (merge conflict)
UU shared/tool/roadmap_checkpoint.hexa
UU shared/tool/roadmap_cli.hexa
UU shared/tool/roadmap_dispatch.hexa
UU shared/tool/roadmap_edges.hexa
UU shared/tool/roadmap_explain.hexa
UU shared/tool/roadmap_kahn.hexa
UU shared/tool/roadmap_portfolio.hexa
UU shared/tool/roadmap_signals.hexa
UU shared/tool/roadmap_vi.hexa
```

**→ E agent 가 해소 중. 본 문서 commit 은 충돌 해소 후에만.**

## Wave 개요

| Wave | 이름 | 위험도 | 병렬성 | 선결 조건 |
|------|------|-------|--------|----------|
| A | 안전 이관 | 낮음 | 프로젝트별 bg 병렬 | tarball sha256 기록 |
| B | 중복 정리 | 중간 | 순차 (diff 확인) | wave A 완료 |
| C | 심볼릭 끊기 | 중간 | 직렬 (의존성) | wave B 완료 |
| D | 최종 제거 | 높음 | 없음 (단일) | wave A+B+C 전부 Go |

각 wave 가 **독립적으로 No-Go** 일 때 다음 wave 는 보류되고, 이전 wave 는 그대로 둔 채 진단 모드로 전환한다.

---

## Wave A — 안전 이관 (risk: 낮음)

### 목적

~/shared 에만 있는 고유 데이터를 명확한 새 소유 프로젝트로 옮긴다. 중복이 없어 충돌 없고, 이동 즉시 검증 가능.

### 대상 매핑

| From | To | 크기 | 사유 |
|------|-----|------|------|
| ~/n6/atlas.n6 | ~/core/n6-architecture/atlas/atlas.n6 | canonical | owner=n6-architecture |
| ~/n6/atlas.signals.n6 | ~/core/n6-architecture/atlas/atlas.signals.n6 | canonical | owner=n6-architecture |
| ~/n6/atlas.blowup.jsonl | ~/core/n6-architecture/atlas/atlas.blowup.jsonl | 17M | 확장 데이터 |
| ~/n6/atlas_phase*.jsonl | ~/core/n6-architecture/atlas/ | ~640K | phase 스캔 결과 |
| ~/n6/atlas_*.hexa | ~/core/n6-architecture/tool/ | ~120K | raw#9 hexa-only 준수 (tool/) |
| ~/bench/ | ~/core/nexus/bench/ | 164K | raw#6 nexus 소유 |
| ~/hexa/ | ~/core/hexa-lang/feedback/ (선별) | 5.1M | hexa 포팅 로그 (hexa-lang 소유) |
| ~/papers/ | ~/core/papers/inbox/ | 604K | 논문 관련 |
| ~/SECRET.md | ~/etc/secret/ | 2.9K | 외부 (raw#14 ext-ssot) |

### 사전 검증

1. tarball sha256 기록: `shasum -a 256 ~/etc/shared-backup-20260421-110801.tar.gz > ~/etc/shared-backup-20260421-110801.sha256`
2. 대상 프로젝트 각각 `.raw`, `.own` 존재 확인 (9 프로젝트 중 7 개 OK, contact/void 제외)
3. 대상 디렉토리 비어있음 확인 (예: `ls -la ~/core/n6-architecture/atlas/` 가 없으면 생성)
4. 각 대상 프로젝트 git clean (uncommitted 없어야 함)

### 실행 명령 예시 (A-1: atlas canonical)

```bash
# pre-hash
pre_hash=$(shasum -a 256 ~/n6/atlas.n6 | awk '{print $1}')
mkdir -p ~/core/n6-architecture/atlas
mv ~/n6/atlas.n6 ~/core/n6-architecture/atlas/atlas.n6
# post-hash
post_hash=$(shasum -a 256 ~/core/n6-architecture/atlas/atlas.n6 | awk '{print $1}')
[ "$pre_hash" = "$post_hash" ] || { echo "FAIL"; exit 1; }
cd ~/core/n6-architecture && git add atlas/atlas.n6 && git commit -m "feat(atlas): canonical atlas.n6 이관 (from ~/n6)"
```

### 실행 명령 예시 (A-2: bench 이관)

```bash
cd ~/core/nexus
mkdir -p bench
for f in ~/bench/*; do
  git mv "$f" bench/ 2>/dev/null || mv "$f" bench/
done
git add bench && git commit -m "feat(bench): ~/bench 이관 — Wave A"
```

### 실행 명령 예시 (A-3: .hexa 를 tool/ 로, raw#9 준수)

```bash
cd ~/core/n6-architecture
mkdir -p tool
for f in ~/n6/atlas_*.hexa; do
  base=$(basename "$f")
  mv "$f" tool/"$base"
done
git add tool && git commit -m "feat(tool): atlas 도구 이관 (raw#9 hexa-only)"
```

### 사후 검증

- 각 이관 파일 sha256 pre/post 일치
- 각 대상 repo `git log -1` 으로 커밋 확인
- `readlink ~/core/nexus/n6/atlas.n6` 이전 symlink 가 dangling 되지 않도록 다음 wave 에서 처리

### 롤백 방법

- 대상 repo `git revert <sha>` (각 이관 커밋)
- tarball 에서 원본 추출: `tar xzf ~/etc/shared-backup-20260421-110801.tar.gz -C /tmp/rollback shared/n6/atlas.n6`
- `/tmp/rollback/n6/atlas.n6` → `~/n6/atlas.n6` 복구

### 위험 요소 + 완화

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| mv 중 OS 크래시 (inode 이동 중단) | 낮음 | high | same-fs mv 는 atomic, tarball 존재 |
| 대상 repo git lock 충돌 | 중간 | low | raw#25 concurrent-git-lock exp-backoff |
| hexa 파일이 외부 경로 참조 중 | 낮음 | med | mv 후 grep 으로 참조 확인 |

### Raw 매트릭스

- raw#6 folder-naming: bench/, tool/ 은 명시적 도메인 폴더 OK
- raw#8 file-naming: _old/_new/_bak 접미 파일 확인 (현재 없음)
- raw#9 hexa-only: .hexa 는 tool/, .json 은 data/ 로 분리
- raw#14 ext-ssot: SECRET.md 는 ~/etc/secret/ 로 외부화
- raw#24 foundation-axioms: atlas hash 재앵커는 wave D 에서 별도 단계

### Go/No-Go

- **Go**: tarball sha256 기록 OK + 7 대상 프로젝트 git clean
- **No-Go**: 위 2 조건 중 하나라도 실패 → wave 전체 보류, 원인 해소 후 재진입

### 병렬성 추천

프로젝트별 독립이므로 **3 개 bg 병렬 가능**:
- bg1: n6-architecture (atlas + phase jsonl + tool)
- bg2: nexus (bench)
- bg3: hexa-lang (hexa/ 선별) + papers (inbox)

각 bg 는 자기 프로젝트만 git commit, 서로 repo 가 다르므로 lock 충돌 없음.

---

## Wave B — 중복 정리 (risk: 중간)

### 목적

~/shared 와 ~/core/nexus/shared 에 동시 존재하는 항목 중 **nexus/shared 를 canonical 로 채택** 하고 ~/shared 측 제거. 단, diff 로 최신본 확인 후.

### 대상 (중복 경로)

| 경로 | ~/shared 크기 | nexus/shared 크기 | 결정 |
|------|---------------|-------------------|------|
| discovery/ | 400M | 77M | diff 필요. ~/shared 가 더 큼 → 추가 파일 선별 후 nexus 로 merge, 나머지 tarball |
| calc/ | 64M | 372K | ~/shared 가 더 큼 → 차이 nexus 로 merge |
| dse/ | 39M | 12M | diff 후 최신본 nexus 에 유지 |
| sim_bridge/ | 21M | (확인 필요) | diff |
| consciousness/ | 1.5M | 1.1M | diff |
| convergence/ | 836K | 764K | diff |
| bisociation/ | 1.4M | 1.4M | 동일 → ~/shared 측 삭제 |
| bt/ | 2.2M | 1.4M | diff |
| state/ | 2.4M | (확인 필요) | diff + 최신 timestamp 우선 |
| config/ | 1.9M | 1.9M | infrastructure.json 등 — workspace resource 이므로 nexus canonical 유지 |
| engine/ | 592K | 592K | 동일 예상 → 삭제 |
| engines_bt/ | 44K | 44K | 동일 예상 → 삭제 |
| logs/ | 5M | (확인 필요) | tarball 후 폐기 |
| hexa_pitfalls_log.jsonl | 1.9M | 1.9M | 동일 → 삭제 |
| discovery_log.2026-04-12.jsonl.gz | 6.5M | 6.5M | 동일 → 삭제 |
| discovery_log.sqlite | 16K | 16K | 동일 → 삭제 |
| per_source_genome_ts.jsonl | 96K | 96K | 동일 → 삭제 |
| infra_state.json | 4K | 4K | workspace resource — nexus canonical |

### 사전 검증 (각 경로마다)

```bash
# diff 로 추가 파일 식별
diff -rq ~/discovery ~/core/nexus/discovery > /tmp/discovery.diff
# "Only in /Users/ghost/discovery: foo" 항목만 수작업 판단
grep "^Only in /Users/ghost/shared" /tmp/discovery.diff
```

판단 기준:
- ~/shared 에만 존재 + 과학적 산출물 → nexus/shared 로 merge
- ~/shared 에만 존재 + 로그/임시 → tarball 만 보존, 삭제
- 양쪽 존재 + 다름 → mtime 최신본 채택 후 sha256 기록
- 양쪽 존재 + 동일 → ~/shared 측 삭제

### 실행 명령 템플릿

```bash
# B-1: bisociation (동일 예상, 검증 후 삭제)
diff -rq ~/bisociation ~/core/nexus/bisociation
# 출력이 없거나 "differ" 없음 → 안전
rm -rf ~/bisociation

# B-2: discovery merge (차이만)
cd ~/core/nexus
rsync -av --ignore-existing ~/discovery/ shared/discovery/
git add shared/discovery && git commit -m "feat(shared): discovery 차이 병합 — Wave B"
rm -rf ~/discovery
```

### 사후 검증

- nexus/shared git status clean
- ~/<path> 가 더 이상 존재하지 않음
- `~/shared` 총 용량이 목표치까지 감소 (추적: `du -sh ~/shared`)

### 롤백 방법

- nexus git: `git revert <merge-commit-sha>`
- 삭제된 ~/<path> 복구: `tar xzf ~/etc/shared-backup-20260421-110801.tar.gz -C /tmp/rollback shared/<path>` 후 `mv /tmp/rollback/<path> ~/`

### 위험 요소 + 완화

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| diff 놓친 고유 파일 삭제 | 중간 | high | `--ignore-existing` rsync 로 merge 우선, 그 후 삭제 |
| ~/calc 거대 diff 누락 | 높음 | med | calc 는 수작업 파일 목록 검토 |
| mtime 역전 (~/shared 가 최신) | 낮음 | med | find -newer 체크 |
| nexus/.runtime 실시간 변경 | 중간 | high | wave C 까지 .runtime 미건드림 |

### Raw 매트릭스

- raw#5 single-source-of-truth: nexus/shared 단일화로 준수
- raw#6 folder-naming: nexus/ 자체가 잡식 폴더 징후 (추후 나눌 대상이지만 wave B 범위 밖)
- raw#21 deprecated-symlink: ~/shared 잔존 심볼릭은 archive/ 로 이동 금지, 끊어서 wave C 에서 제거

### Go/No-Go

- **Go**: Wave A 완료 + 각 경로 diff 분석 완료 + nexus repo clean
- **No-Go**: discovery diff 가 >100 건이면 사람 검토 필요 → 보류

### 병렬성 추천

**순차 권장**. diff 확인이 인적 판단을 요구하므로 한 경로씩 처리. 단, "동일 예상" 소형 경로 (bisociation/engine/engines_bt) 는 한 batch 로 묶어 1 커밋.

---

## Wave C — 심볼릭 끊기 (risk: 중간)

### 목적

~/shared 를 가리키는 inbound 심볼릭을 **다른 canonical 로 재연결** 하거나 **제거** 한다. Wave D 전에 dangling 이 발생하면 launchd/데몬 fail 방지.

### 대상 심볼릭 (사전 수집)

```bash
find ~/core -type l 2>/dev/null | while read l; do
  t=$(readlink "$l")
  case "$t" in *shared*|*Users/ghost/shared*) echo "$l -> $t" ;;
  esac
done > /tmp/shared_symlinks.txt
```

예상 항목:
1. `/Users/ghost/core/anima/shared -> /Users/ghost/shared` — **직접 참조, 가장 위험**
2. `/Users/ghost/core/nexus/.runtime -> /Users/ghost/.runtime` — runtime 활성
3. `/Users/ghost/core/anima/ready/config/installed_tools.json -> ../../../.shared/installed_tools.json` — .shared 경유
4. `/Users/ghost/core/anima/ready/config/consciousness_mechanisms.json -> ../../../.shared/consciousness_mechanisms.json`
5. `/Users/ghost/core/anima/experiments/data/law_network.json -> ../../consciousness/law_network.json`
6. `/Users/ghost/core/.shared-backup-20260421-022340/archive/hooks-20260414/loop-guard.hexa -> /Users/ghost/Dev/nexus/tool/loop-guard.hexa` — 백업 내 외부 참조

### C-1: anima/shared 교체

anima 가 `shared/*` 을 광범위 참조하므로 본 심볼릭 제거는 anima 에 연쇄 영향.

```bash
# 검증: anima 가 ~/shared 의 무엇을 참조하는지
grep -r "~/shared\|/Users/ghost/shared" ~/core/anima --include="*.hexa" --include="*.json" | head -50
```

결과가 없거나 모두 nexus/shared 로 대체 가능하면:
```bash
rm /Users/ghost/core/anima/shared
ln -s ../nexus/shared /Users/ghost/core/anima/shared
cd ~/core/anima && git add shared && git commit -m "chore(symlink): anima/shared → nexus/shared 재연결 — Wave C"
```

결과가 있고 대체 불가능한 특정 파일이 있다면 → wave A 로 돌아가 해당 파일 먼저 이관.

### C-2: nexus/.runtime owner 결정

옵션:
- **(a) nexus/.runtime 독립 실디렉토리** (nexus 소유 런타임)
- **(b) ~/etc/nexus-runtime/ 로 외부화** (raw#14 ext-ssot)

권장: **(a)**. 이유: nexus 가 본질적 owner 이며 외부화하면 다른 심볼릭 추가.

```bash
# 현재 live 런타임 스냅샷
rsync -a ~/.runtime/ /tmp/runtime_snapshot/
# nexus 에 실디렉토리 생성 (기존 심볼릭 제거)
rm /Users/ghost/core/nexus/.runtime
mkdir -p /Users/ghost/core/nexus/.runtime
rsync -a /tmp/runtime_snapshot/ /Users/ghost/core/nexus/.runtime/
# .gitignore 에 추가 (runtime 파일은 repo 에 들어가면 안 됨)
echo "shared/.runtime/" >> /Users/ghost/core/nexus/.gitignore
cd ~/core/nexus && git add .gitignore && git commit -m "chore(runtime): .runtime 실디렉토리화 + gitignore — Wave C"
```

### C-3: 백업 디렉토리 외부 참조 제거

`~/core/.shared-backup-20260421-022340/` 는 core 내부 오염. 심볼릭이 외부 ~/Dev/nexus 를 가리키므로 dangling 예상.

```bash
# 이미 tarball 에 포함되었는지 확인 후 삭제
tar tzf ~/etc/shared-backup-20260421-110801.tar.gz | grep -q ".shared-backup-20260421-022340" && echo "존재" || echo "불포함"
# 존재 시 ~/etc/ 로 이동 (core 밖으로)
mv ~/core/.shared-backup-20260421-022340 ~/etc/shared-backup-20260421-022340-core-internal
```

### 사전 검증

- `/tmp/shared_symlinks.txt` 전체 항목 검토 완료
- 각 심볼릭의 consumer 식별 (launchd plist, 데몬, hexa 도구 등) 완료

### 사후 검증

```bash
# dangling 검사
find ~/core -type l 2>/dev/null | while read l; do
  [ ! -e "$l" ] && echo "DANGLING: $l -> $(readlink $l)"
done
```

출력이 비어있어야 Go.

### 롤백 방법

- 심볼릭 재생성: C-1/C-2 각 단계 커밋 revert
- `.runtime` 내용 복구: `/tmp/runtime_snapshot` 또는 tarball

### 위험 요소 + 완화

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| launchd 데몬이 .runtime 참조 중 | 높음 | high | rsync 로 live 스냅샷 후 교체 (zero-downtime 근접) |
| anima 코드가 ~/shared 경로 하드코딩 | 중간 | high | 사전 grep 로 전수 조사 |
| git 이 심볼릭 대신 내용 커밋 | 낮음 | med | `git ls-files -s shared/.runtime` 으로 symlink 모드(120000) 확인 |

### Raw 매트릭스

- raw#21 deprecated-symlink: archive/ 가 아닌 직접 심볼릭은 원칙 제거 대상
- raw#28 dependency-graph: inbound edge 를 명시적으로 기록 후 재연결

### Go/No-Go

- **Go**: Wave B 완료 + `/tmp/shared_symlinks.txt` 전수 검토 + launchd 데몬 실행 영향 확인
- **No-Go**: launchd 활성 의존 > 0 → 데몬 중지 후 재진입

### 병렬성 추천

**직렬 필수**. 심볼릭 간 의존성 있음 (anima/shared 제거 전에 anima 개별 심볼릭 먼저, 등).

---

## Wave D — 최종 제거 (risk: 높음)

### 목적

~/shared 잔존 내용 tarball 재확인 후 **`rm -rf ~/shared`** 단행. 복구 불가 단계.

### 대상

- `~/` 전체 디렉토리
- `~/core/.shared-backup-20260421-022340/` (wave C 에서 이동되었으면 skip)
- 잔존 dangling 심볼릭 일괄 제거 (발견 시)

### 사전 검증 (Go/No-Go 의 Go 조건)

1. tarball sha256 재검증: `shasum -a 256 -c ~/etc/shared-backup-20260421-110801.sha256`
2. ~/shared 현재 용량 기록: `du -sh ~/shared > ~/etc/shared-final-size.txt`
3. 중요 데이터 부재 확인 — 다음 스팟체크:
   - `~/n6/atlas.n6` 존재하지 않아야 함 (wave A 완료 증거)
   - `~/bench/` 존재하지 않아야 함
4. 모든 inbound 심볼릭 제거 또는 재연결됨 (`find ~/core -type l | xargs -I {} sh -c 'readlink "{}" | grep -q shared && echo {}'` 출력 없음)
5. workspace_sync --check PASS (hexa 업그레이드 선결)
6. 9 프로젝트 `.raw-audit` head 재앵커 dry-run PASS (raw#24)

### 실행 명령

```bash
# 최종 스냅샷 (wave A/B/C 후 잔존만)
tar czf ~/etc/shared-final-residue-20260421.tar.gz -C ~ shared 2>/dev/null
shasum -a 256 ~/etc/shared-final-residue-20260421.tar.gz > ~/etc/shared-final-residue-20260421.sha256

# 확인
ls -la ~/etc/shared-final-residue-20260421.tar.gz
du -sh ~/shared

# 최종 제거
rm -rf ~/shared

# 검증
ls ~/shared 2>&1 | head -3   # "No such file" 이어야 함
find ~/core -type l -name '*shared*' 2>/dev/null | xargs -I {} sh -c '[ ! -e "{}" ] && echo "DANGLING: {}"'
```

### 사후 검증

- `~/shared` 부재
- `workspace_sync --check` PASS
- 9 프로젝트 `hexa tool/raw_audit.hexa --project .` PASS
- launchd 데몬 5 분 관찰 (이상 로그 없음)

### 롤백 방법

- Wave D 는 **완전 롤백 어려움**. tarball 에서 전체 복원:
  ```bash
  cd ~ && tar xzf ~/etc/shared-backup-20260421-110801.tar.gz
  # wave A/B/C 의 각 git commit revert 필요
  ```
- 복원 후 atlas canonical 위치를 원복하려면 wave A 커밋 전수 revert.

### 위험 요소 + 완화

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| 숨겨진 hardcoded ~/shared 참조 | 중간 | high | `grep -r "~/shared\|/Users/ghost/shared" ~/core` 전수 사전 조사 |
| 삭제 후 launchd 부팅 실패 | 낮음 | high | wave C 에서 .runtime 이미 재배치 |
| tarball 무결성 손실 | 낮음 | critical | sha256 재검증 + 별도 외부 미디어 백업 권장 |
| raw#30 irreversibility 위반 | 일부 | med | tarball 으로 복원 가능 범위 유지 (30 일 보존) |

### Raw 매트릭스

- raw#0 ssot-roots: ~/shared 제거 → 단일 SSOT 달성
- raw#5 single-source-of-truth: 이중 SSOT 해소 완료
- raw#24 foundation-axioms-locked: hash 재앵커 완료 선결
- raw#30 irreversibility: tarball 보존으로 복원 가능 (단, git 되돌리기는 수작업)

### Go/No-Go

- **Go**: Wave A/B/C 모두 완료 + 위 사전 검증 6 항목 모두 PASS
- **No-Go**: 하나라도 실패 → ~/shared 유지, 원인 문서화 후 재진입

### 병렬성

**없음**. 단일 원자 작업.

---

## 전역 체크리스트

실행 전 필히 확인:

- [ ] nexus repo merge conflict 해소됨 (E agent 완료)
- [ ] tarball `~/etc/shared-backup-20260421-110801.tar.gz` sha256 기록됨
- [ ] workspace_sync.hexa line 237 syntax error 해소됨 (hexa upgrade)
- [ ] 9 프로젝트 `.raw-audit` 현재 head 기록됨 (롤백용)
- [ ] launchd 활성 데몬 목록 기록됨 (wave C 영향 파악용)
- [ ] `grep -r "~/shared\|/Users/ghost/shared" ~/core --include="*.hexa" --include="*.json"` 결과 검토 완료

## 결정 이력

- 2026-04-21 12:xx: 본 wave plan 작성 (D agent 기초 플랜 참조). 4 wave 로 재편.
- nexus repo 충돌 상태: commit 보류. 충돌 해소 후 `docs(nexus): ~/shared decommission wave plan — A/B/C/D 단계별 실행` 커밋.

## 다음 단계

1. nexus merge conflict 해소 대기 (E agent)
2. 본 문서 nexus 커밋
3. Wave A 실행 준비:
   - tarball sha256 기록
   - 대상 프로젝트 git clean 확인
   - 3 bg agent 할당 (n6-architecture / nexus / hexa-lang+papers)
4. Wave A 결과 회고 후 B 진입 Go/No-Go 판단
