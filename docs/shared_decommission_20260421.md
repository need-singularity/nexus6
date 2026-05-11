# ~/shared Decommission Plan (2026-04-21)

## 배경

이중 SSOT 상태가 확인됨.

- `~/shared` 실사용 용량: 596M (활성 데이터 다수 포함)
- `~/core/nexus/shared` 용량: 179M (중복/부분 사본)
- `~/core/.shared-backup-20260421-022340/` 363M (중간 시점 부분 백업)
- 기존 memory 기록은 "~/shared = backup only" 로 명시되어 있었으나 실제로는 nexus harness/atlas/n6 runtime 이 활성 상태로 참조 중
- 기록과 현실 불일치 → SSOT 단일화 대상 (raw#5 single-source-of-truth 위반 상태)

~/shared 내부 주요 그룹:

| 그룹 | 추정 크기 | 성격 | 이관 대상 |
|------|----------|------|----------|
| n6/ (atlas 계열) | 2~3M | canonical data | CANON 소유 |
| harness/ | 수십 MB | roadmap DSL/runner | nexus (코드) + 별도 변환 트랙 |
| discoveries/ | 다수 JSON | 과학적 산출물 | CANON/discoveries |
| research/ | 다수 | 연구 로그 | nexus/research |
| lenses/, rules/, hooks/, bin/, scripts/, lib/ | 레거시 | 중복 파편 | 폐기 |
| .runtime/ | 변동 | 실행 상태 | nexus/.runtime 또는 tmp |

## 결정 사항

1. **atlas.n6 canonical 위치: `~/core/canon/atlas/atlas.n6`**
   - 소유 도메인은 CANON (174 lens + BT + DSE 원산지)
   - 이전 임시 canonical 이었던 `~/core/data/n6/atlas.n6` 는 symlink backward compat 로 유지 (마이그레이션 후 제거 예정)
2. **~/shared 백업 tarball: `~/etc/shared-backup-*.tar.gz`**
   - `~/core/.shared-backup-...` 은 core 내부 오염이므로 core 밖 `~/etc/` 로 이동 (raw#1 외부 공간 분리)
3. **로드맵 JSON → .roadmap DSL 변환은 별도 트랙**
   - 이번 decommission 스코프에 포함하지 않음 (스코프 확장 시 복잡도 폭증)
   - 트랙 분리: 우선 shared/tool/*.json 은 이관 전까지 nexus/harness-legacy/ 로 임시 이주

## 프로젝트 표준 레이아웃 (raw 준수)

### 루트 6 SSOT (raw#0, raw#5)
```
<project>/
├── .raw          ← 원 규칙 (chflags uchg 잠금, raw#1)
├── .own          ← 소유/책임 선언
├── .ext          ← 외부 의존 선언
├── .roadmap      ← 진행 로드맵 DSL
├── .loop         ← 자체 피드백 루프
└── .raw-audit    ← hash-chain 감사
```

### 표준 디렉토리
```
<project>/
├── tool/         ← hexa-only 도구 (raw#9)
├── test/         ← 테스트 (fixtures/ 포함)
├── self/         ← self-referential (hexa-lang 등)
├── doc/ 또는 docs/  ← 프로젝트 문서 (기존 컨벤션 유지)
├── cli/          ← 진입점 (raw#11 snake_case)
└── <domain>/     ← bench, atlas, research 등 도메인별
```

### 금지 (raw 위반)
- `shared/` (루트 레벨의 잡식 폴더, raw#5 단일 SSOT 위반)
- `commands.json` (raw#9 hexa-only)
- CamelCase 파일명 (raw#11 snake_case)

## raw 매트릭스 (30 규칙 준수)

| raw | 이름 | 위반 여부 | 영향 | 대응 |
|-----|------|----------|------|------|
| raw#0 | ssot-roots | 현재 위반 | ~/shared 이중 SSOT | decommission 실행 |
| raw#1 | chflags-uchg | 부분 위반 | shared/.raw-ref 잠금 해제 | tarball 후 잠금 이관 |
| raw#5 | single-source-of-truth | 위반 | atlas.n6 이중 | CANON 단일화 |
| raw#9 | hexa-only | OK | - | harness .json 변환은 별도 트랙 |
| raw#11 | snake_case | OK | - | 유지 |
| raw#13 | tree-structure | 경고 | shared/ 루트 폴더 잡식 | 도메인 분산 |
| raw#17 | hash-chain | OK | - | .raw-audit 재앵커 필요 |
| raw#24 | foundation-axioms-locked | 위험 | hash 재앵커 실패 시 체인 깨짐 | dry-run 후 commit |
| raw#28 | dependency-graph | 경고 | ~/shared → 9 프로젝트 inbound edge | 마이그레이션 순서 수립 |
| raw#30 | irreversibility | 주의 | tarball 복원 가능 범위 내 | rm 전 sha256 검증 |

## 이관 매핑

| From (~/*) | To | 방식 |
|-------------------|-----|------|
| n6/atlas.n6 | ~/core/canon/atlas/atlas.n6 | mv + sha256 검증 |
| n6/atlas.signals.n6 | ~/core/canon/atlas/atlas.signals.n6 | mv + sha256 검증 |
| n6/atlas.live.json | ~/core/canon/atlas/ | mv |
| discoveries/ | ~/core/canon/discoveries/ | mv + git add |
| research/ | ~/core/nexus/research/ | mv + git add |
| harness/ | ~/core/nexus/harness-legacy/ | 이관 후 .roadmap DSL 변환 (별도 트랙) |
| bench/ | ~/core/nexus/bench/ | mv |
| n6/ 기타 | ~/core/canon/ | mv |
| config/infrastructure.json | ~/core/nexus/config/ (유지) | 기존 심볼릭 해소 |
| .runtime/ | ~/core/nexus/.runtime/ | mv, gitignore |

## 폐기 대상

### Tier 1 (즉시 삭제 후 tarball 만 보존)
- `~/lenses/` (CANON 에 원본 있음)
- `~/rules/` (.raw 로 이미 흡수)
- `~/hooks/` (.githooks 으로 이관 완료)
- `~/bin/` (~/.hx/bin 로 이관 완료)
- `~/scripts/` (hexa-only 위반, raw#9)
- `~/lib/` (중복 js/py 레거시)

### Tier 2 (tarball 후 보류 검토)
- `~/tool/*.json` → .roadmap DSL 변환 트랙으로 이월
- `~/.runtime/` → nexus/.runtime 로 이관 후 폐기

## 9 프로젝트 표준 적용 체크리스트

| 프로젝트 | .raw | .own | .ext | .roadmap | .loop | .raw-audit | tool/ | test/ | 문서 dir | cli/ | 비고 |
|---------|------|------|------|----------|-------|-----------|-------|-------|---------|------|------|
| airgenome | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | docs/ | - | harvest pipeline |
| anima | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | doc/ | cli/ | AGI 본체 |
| contact | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | - | - | - | - | 최소 구조 |
| data | - | - | - | - | - | - | - | - | - | - | canonical sink (SSOT 예외) |
| hexa-lang | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | docs/ | - | 자기참조 도구 |
| hexa-os | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | docs/ | - | OS 레이어 |
| CANON | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | docs/ | - | 174 lens owner (atlas 신규 owner) |
| nexus | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | 있음 | 있음 | docs/ | cli/ | CLI 진입 |
| papers | 확인 | 확인 | 확인 | 확인 | 확인 | 확인 | - | - | - | - | 논문 리포 |
| void | - | - | - | - | - | - | - | - | - | - | scratch (SSOT 예외) |

체크리스트는 decommission 후 각 프로젝트에서 6 SSOT 누락 여부를 재검증한다.

## 실행 순서 (9 step)

1. **사전 스냅샷**: `tar czf ~/etc/shared-backup-20260421-full.tar.gz ~/shared` (sha256 기록)
2. **.workspace 업데이트 (dry-run)**: atlas source path → `../canon/atlas/atlas.n6`
3. **atlas 이관**: `~/n6/atlas.n6` → `~/core/canon/atlas/atlas.n6` (same-fs mv, sha256 비교)
4. **symlink 재연결**: `~/core/nexus/n6/atlas.n6` → `../../../canon/atlas/atlas.n6`, `~/core/hexa-lang/n6/atlas.n6` 도 동일
5. **domain 이관**: discoveries → CANON, research → nexus/research, bench → nexus/bench
6. **harness 임시 이주**: shared/harness → nexus/harness-legacy (.roadmap 변환 트랙 ticket 발행)
7. **Tier 1 폐기**: lenses/rules/hooks/bin/scripts/lib 삭제 (tarball 존재 검증 후)
8. **.raw-audit 재앵커**: 9 프로젝트 모두 hash-chain head 갱신, raw#24 dry-run 통과 확인
9. **~/shared rm -rf**: 모든 이관 완료 + workspace_sync --check PASS 확인 후 최종 제거

각 step 마다 rollback 시점 기록 (tarball sha256 + git commit sha).

## 위험 요소

- **raw#24 foundation-axioms-locked hash 재앵커 실패**: hash-chain 깨지면 9 프로젝트 전체 audit 정지. 대응: step 8 을 dry-run 으로 먼저 실행, 실패 시 roll forward 가능한 지점까지만 진행.
- **심볼릭 끊김**: `nexus/.runtime → ~/.runtime` 등 dangling 발생 시 launchd 데몬 fail. 대응: step 1 전에 `find ~/core -type l -lname '*~/shared*'` 로 전체 심볼릭 목록 덤프 후 일괄 재작성 스크립트 준비.
- **로드맵 변환 보류 중 SSOT 비동기**: shared/tool/*.json 을 legacy 폴더로 옮긴 동안 .roadmap DSL 과 duplicate. 대응: harness-legacy 폴더에 `.roadmap-pending` marker 파일 배치, workspace_sync 가 경고만 출력하도록 flag 추가.
- **workspace_sync.hexa line 237 syntax error (기존 known issue)**: --check 불가 상태라 최종 검증을 hexa upgrade 이후로 미뤄야 함. 대응: hexa 업그레이드 우선 완료, 그 후 step 8~9 진행.
- **~/core 내부 .shared-backup-20260421-022340/ 가 아직 존재 (363M)**: step 1 tarball 생성 후 이 내부 백업도 ~/etc 로 이동하고 제거.

## 실행 Go/No-Go 기준

- Go: workspace_sync --check 준비 완료 + hexa upgrade 완료 + tarball sha256 재검증 완료
- No-Go: 위 3 조건 중 하나라도 미충족 → 이 문서의 step 1 (스냅샷) 만 실행하고 대기

## 상세 실행 스크립트 초안

실제 실행 시 아래 블록을 hexa 툴로 래핑하여 단계별 커밋. 여기서는 참고용 평문 시나리오.

### Step 1: 전체 스냅샷
```
mkdir -p ~/etc
tar czf ~/etc/shared-backup-20260421-full.tar.gz -C ~ shared
shasum -a 256 ~/etc/shared-backup-20260421-full.tar.gz > ~/etc/shared-backup-20260421-full.sha256
ls -la ~/etc/shared-backup-20260421-full.tar.gz
```
검증: 출력 크기가 ~600M ± 10% 범위 + sha256 파일 1 라인.

### Step 2: .workspace dry-run diff
```
# before
resource atlas.n6
  owner    nexus
  source   ../data/n6/atlas.n6
  target   shared/n6/atlas.n6

# after
resource atlas.n6
  owner    CANON
  source   ../canon/atlas/atlas.n6
  target   shared/n6/atlas.n6
```
owner 변경이 핵심. workspace_sync 가 새 owner 로부터 상대경로를 재계산하도록 둠.

### Step 3: atlas mv (same-fs)
```
mkdir -p ~/core/canon/atlas
mv ~/n6/atlas.n6 ~/core/canon/atlas/atlas.n6
mv ~/n6/atlas.signals.n6 ~/core/canon/atlas/atlas.signals.n6
# 사전/사후 sha256 비교
```
사전 sha256 기록 파일 필수. inode 이동이라 atomic 이지만 rollback 위해 tarball 안에 원본 보존.

### Step 4: symlink 재연결 (자동화 스크립트)
```
# 모든 dangling 후보 수집
find ~/core -type l 2>/dev/null | while read l; do
  target=$(readlink "$l")
  case "$target" in
    *shared/n6/atlas*) echo "RELINK $l -> atlas canonical" ;;
    *shared/n6/atlas.signals*) echo "RELINK $l -> signals canonical" ;;
  esac
done
```
대상 목록 확정 후 일괄 ln -sf 적용. 재연결 후 각 프로젝트 tool/ 에서 atlas 열기 테스트 1 회.

### Step 5~6: 도메인 이관
- `mv ~/discoveries ~/core/canon/discoveries` 후 `git add` + 커밋 (CANON)
- `mv ~/research ~/core/nexus/research` 후 `git add` + 커밋 (nexus)
- `mv ~/harness ~/core/nexus/harness-legacy` + 마커 파일 생성:
  ```
  touch ~/core/nexus/harness-legacy/.roadmap-pending
  ```
- `mv ~/bench ~/core/nexus/bench` 후 커밋

### Step 7: Tier 1 폐기
```
for d in lenses rules hooks bin scripts lib; do
  if [ -d ~/$d ]; then
    # tarball 내 존재 여부 확인
    tar tzf ~/etc/shared-backup-20260421-full.tar.gz | grep -q "^shared/$d/" && rm -rf ~/$d
  fi
done
```
반드시 tarball 내 동일 path 존재 여부 검증 후 삭제. 미검증 시 skip.

### Step 8: .raw-audit 재앵커 (9 프로젝트)
```
for p in airgenome anima contact hexa-lang hexa-os CANON nexus papers void; do
  hexa ~/core/hexa-lang/tool/raw_audit.hexa --project ~/core/$p --reanchor-dry
done
```
모두 DRY PASS 면 --reanchor 본 실행. 하나라도 FAIL 시 중단 + 해당 프로젝트 개별 조사.

### Step 9: 최종 제거
```
# 필수 선결 조건
# - workspace_sync --check: PASS
# - 모든 심볼릭 재연결 완료
# - Tier 1 완전 폐기
# - tarball sha256 최종 확인

rm -rf ~/shared
rm -rf ~/core/.shared-backup-20260421-022340  # core 내부 오염 정리
```

## 롤백 절차 (재난 시)

1. `~/shared` 재생성: `cd ~ && tar xzf ~/etc/shared-backup-20260421-full.tar.gz`
2. git 각 프로젝트에서 해당 이관 커밋 `git revert <sha>` (mv 커밋만 역적용)
3. .workspace 이전 버전으로 체크아웃 (이전 커밋 sha 기록 필수)
4. symlink 복원: step 4 에서 작성한 재연결 스크립트의 역방향 스크립트 실행
5. 각 프로젝트 .raw-audit 이전 head 로 재앵커 (raw#24 dry-run 먼저)

롤백 성공 조건: workspace_sync --check PASS + 9 프로젝트 raw-audit OK + atlas.n6 sha256 일치.

## 결정 이력

- 2026-04-21: 이 문서 작성. 기존 atlas canonical `~/core/data/n6/atlas.n6` → CANON 소유로 재결정. 관련 memory (project_atlas_ssot.md, project_core_workspace.md) 동시 갱신. 신규 memory `project_shared_decommission.md` 생성.
- 이 결정은 raw#0, raw#5, raw#13, raw#28 기준 평가 통과 (이중 SSOT 해소 + 도메인 소유 명확화).

## 참고

- `/Users/ghost/core/hexa-lang/tool/workspace_sync.hexa` — .workspace parser (line 237 syntax 이슈 선결)
- `/Users/ghost/core/.workspace` — SSOT resource/member DSL
- `/Users/ghost/.claude/projects/-Users-ghost-core-hexa-lang/memory/project_raw_audit.md` — raw#0-30 규칙 정의
- `/Users/ghost/.claude/projects/-Users-ghost-core-hexa-lang/memory/project_shared_decommission.md` — 이 플랜의 memory pointer
