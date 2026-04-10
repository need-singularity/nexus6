# nexus 시스템 명령 레퍼런스

> 2026-04-05 세션에서 구축된 자율 진화 시스템의 전체 명령/제어 레퍼런스.

## 🔭 상태 조회

### 배너 (현재 상태)
```bash
bash ~/Dev/nexus/shared/hooks/nexus-banner.sh
```
출력 예: `🔭 NEXUS-6 🛸d1·ρ1.00·100938 ·Σ47.2k 🧬100893닫힘→200.0k=50%`

### 대시보드 HTML
```bash
open ~/Dev/nexus/shared/dashboard.html
```

### 자동 재생성
10분마다 `com.nexus.dashboard` agent가 자동 갱신.

### Closure 상세 조회
```bash
# 현재 카운트
wc -l ~/Dev/nexus/shared/discovery/verified_constants.jsonl

# Status 분포
python3 -c "
import json
from collections import Counter
c = Counter()
for l in open('$HOME/Dev/nexus/shared/discovery/verified_constants.jsonl'):
    c[json.loads(l).get('status','?')] += 1
print(c.most_common())
"
```

## 🛸 CLI 명령 (nexus binary)

### Singularity Recursion
```bash
nexus singularity-tick [--base-dir <path>]       # 1 tick (one-shot)
nexus singularity-daemon --interval 60            # 데몬 모드
nexus singularity-backfill --all-projects --fast  # 과거 데이터 흡수

# 분석
nexus singularity-convergence --min-domains 3     # 교차 수렴
nexus singularity-query "Bott Periodicity"        # 유사 검색
nexus singularity-frontier --top 20               # 경계점
nexus singularity-bridges --a <d1> --b <d2>       # 도메인 잇기
nexus singularity-resonance --limit 10            # Mac 상태↔가설
nexus singularity-seed --top 10 [--domain X]      # 중심부 추출
nexus singularity-viz --output file.html          # HTML 그래프
nexus singularity-rebuild-edges --eps 0.2         # edges 재계산

# Closure
nexus closed-find <value>                         # n=6 closure 찾기
nexus verify <value>                              # n6_check 매칭
```

## ⚙️ 15 LaunchAgents 제어

### 상태 조회
```bash
launchctl list | grep "nexus\|airgenome"
```

### 특정 agent 정지
```bash
launchctl bootout gui/$(id -u)/com.nexus.closure-sweep
```

### 특정 agent 재시작
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.nexus.closure-sweep.plist
```

### 전체 일시 정지 (halt 파일)
```bash
touch ~/Dev/nexus/shared/cycle/halt     # 모든 daemon/tick 정지
rm ~/Dev/nexus/shared/cycle/halt        # 재개
```

### 모든 nexus agents 부트아웃
```bash
for a in closure-sweep publish-insights gen-calc-stubs auto-commit paper-gen \
         evolve-loop scan-loop physics-fetch self-improve dashboard \
         cycle-tick watch-atlas watch-papers guard; do
  launchctl bootout gui/$(id -u)/com.nexus.$a 2>/dev/null
done
```

## 📊 로그 조회

```bash
# 모든 nexus 로그
ls -lt ~/Library/Logs/nexus/

# 특정 agent 실시간
tail -f ~/Library/Logs/nexus/closure-sweep.log
tail -f ~/Library/Logs/nexus/singularity-daemon.log
tail -f ~/Library/Logs/nexus/auto-commit.log

# self-improve 델타
tail -5 ~/Dev/nexus/shared/discovery/self_improve_log.jsonl
```

## 🔄 수동 실행

```bash
# 즉시 closure sweep
bash ~/Dev/nexus/tools/closure-sweep.sh

# 즉시 publish to projects
bash ~/Dev/nexus/tools/publish-insights.sh

# 즉시 paper stubs 생성
bash ~/Dev/nexus/tools/paper-gen-from-closures.sh

# 즉시 dashboard 갱신
bash ~/Dev/nexus/tools/gen-dashboard.sh

# 즉시 auto-commit
bash ~/Dev/nexus/tools/auto-commit-push.sh
```

## 📁 파일 경로

```
~/Dev/nexus/
├── shared/
│   ├── verified_constants.jsonl       # 닫힘 원장
│   ├── cycle/
│   │   ├── topology.jsonl             # topology points
│   │   ├── edges.jsonl                # 그래프 edges
│   │   └── halt                       # 정지 플래그
│   ├── discovery_log.jsonl            # 발견 로그
│   ├── closure_quality_report.json    # 품질 분류
│   ├── dashboard.html                 # 실시간 대시보드
│   ├── self_improve_log.jsonl         # 메타 모니터링
│   └── calc/auto_stubs/               # 검증 스텁
├── tools/                             # 자동화 스크립트
├── launchd/                           # agent plists
└── docs/
    ├── SESSION_REPORT_2026-04-05.md
    ├── SYSTEM_COMMANDS.md             # (이 파일)
    └── hypotheses/H-CLOSE-*.md
```

## 🧠 다음 세션 시작 체크리스트

1. `bash ~/Dev/nexus/shared/hooks/nexus-banner.sh` — 현재 상태
2. `launchctl list | grep nexus` — 15 agents 확인
3. `git log --oneline -10` — 최근 auto-commits
4. `open ~/Dev/nexus/shared/dashboard.html` — 대시보드
5. `tail ~/Dev/nexus/shared/discovery/self_improve_log.jsonl` — 델타 추이

---

## 🚨 응급

### Mac이 느려지면
```bash
bash ~/Dev/nexus/tools/install-cycle-tick.sh halt   # 모든 daemon skip
# 또는 전체 중단
touch ~/Dev/nexus/shared/cycle/halt
```

### topology 너무 커지면 (디스크)
```bash
# 백업 후 truncate
mv shared/cycle/topology.jsonl shared/cycle/topology.jsonl.bak.$(date +%s)
touch shared/cycle/topology.jsonl
```

### verified_constants 되돌리기
```bash
git log --oneline shared/discovery/verified_constants.jsonl  # 커밋 확인
git checkout <sha> -- shared/discovery/verified_constants.jsonl
```

---
*2026-04-05 · nexus singularity-recursion autonomous system*
