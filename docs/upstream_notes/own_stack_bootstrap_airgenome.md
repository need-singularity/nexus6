# airgenome 측 own stack 부트스트랩 prompt — G3 cross-repo sync 합류

본 문서는 **airgenome maintainer 측에 paste 가능한 spec prompt**. anima paradigm `proposal_stack_paradigm_20260422.md` (P1-P11) + nexus `proposal_sync_hub.hexa` 가 이미 준비됨. airgenome 이 own stack + sync 통합 시 4-repo (anima/hexa-lang/airgenome/nexus) 완전 sync 가능.

---

## paste-ready prompt (시작)

```
Working dir: /Users/ghost/core/airgenome
관련:
  - $WS = /Users/ghost/core
  - $WS/anima/docs/anima_proposal_stack_paradigm_20260422.md  ← 패러다임 spec (P1-P11 정의)
  - $WS/anima/state/proposals/  ← anima own stack 참조 모델 (이미 가동)
  - $WS/nexus/state/proposals/  ← nexus own stack (G3 hub 호스트)
  - $WS/nexus/tool/proposal_sync_hub.hexa  ← cross-repo sync hub (호출만)
  - $WS/nexus/schemas/proposal/cross_repo_link/1.json  ← shared schema
  - $WS/anima/docs/upstream_notes/proposal_stack_cross_repo_sync.md  ← 원본 P12 prompt

Task: airgenome 에 own proposal stack (anima paradigm 미러) 구축 + nexus
G3 hub 와 sync 통합. nexus 측 hub 호출 1 block (P9 step 8.5 패턴).

세부:

1. 디렉토리 구조 (anima paradigm §1 미러):
   ```
   state/proposals/
   ├── inventory.json        SSOT — schema: airgenome.proposal_inventory.v1
   ├── pending/              새 제안
   ├── refinement/           refine 중
   ├── debate/               충돌 라우팅
   ├── approved/             사용자 approve
   ├── rejected/             reject
   ├── archived/             implement 후 보존
   ├── clusters/             5+ 묶음
   └── meta/                 super-proposal, id migration
   ```
   `.gitkeep` 으로 빈 sub-dir commit. `state/cross_repo_sync_log.jsonl` 만 ignore.

2. inventory.json 초기 (anima 형식 미러):
   ```json
   {
     "schema": "airgenome.proposal_inventory.v1",
     "id_prefix": "agm",
     "updated_ts": "<UTC>",
     "entries": [],
     "proposals": [],
     "_meta": {
       "owner_repo": "airgenome",
       "sister_repos": {
         "anima":     {"prefix": "anima", "inventory_path": "$WS/anima/state/proposals/inventory.json"},
         "hexa-lang": {"prefix": "hxa",   "inventory_path": "$WS/hexa-lang/state/proposals/inventory.json"},
         "nexus":     {"prefix": "nxs",   "inventory_path": "$WS/nexus/state/proposals/inventory.json"}
       },
       "cross_repo_links": [],
       "created_by": "G3 own stack bootstrap (anima paradigm §1 + §10)"
     }
   }
   ```

3. proposal id prefix `agm-` (anima `anima-` / hexa-lang `hxa-` / nexus `nxs-` 와 짝).

4. P1-P11 미러 — anima paradigm §16 12-task batch 그대로.
   우선순위 권장: P1 → P2 → P9 → P3-P5 → P6-P8.

5. P9 step 8.5 (nexus G3 hub 호출) — 동일 hexa-lang 패턴.

6. airgenome 고유 source signal (anima 의 secret-scan 같은 emit trigger):
   - host 6-axis genome metric 의 axis별 anomaly (M14)
   - airgenome harvest jsonl 의 outlier (top RSS/CPU process drift)
   - probe failure streak (특정 host 연속 N회 fail)
   - runaway_guard SIGKILL 이벤트 (L7-class 사전 차단 학습)
   - dispatch_state.json 의 worker imbalance
   - infra_state.json stale > 30min
   - hexa_remote rc=137 빈도 (cgroup OOM)
   - docker container restart 횟수 spike
   각 signal 이 P2 emit input — 자동 proposal 후보. (M14 의 6-axis genome 이
   이미 풍부한 metric 제공)

7. airgenome 만의 추가 cross-repo 패턴:
   - airgenome 의 host issue → nexus 측 hexa_remote tuning proposal (cross_repo_link satisfies/depends_on)
   - airgenome 의 docker pattern 변경 → hexa-lang 측 systemd unit pattern 동기화

Hard constraints:
- INVARIANT: state/proposals/ 외 mutate 금지 (특히 bin/, modules/, config/)
- DO NOT modify .roadmap (사용자 approve gate)
- DO NOT auto-implement (P4 approve 후 module emit)
- DO NOT modify L0-locked files (chflags uchg 걸린 hexa_remote 등)
- nexus repo unreachable 시 G3 hub 호출 graceful skip
- proposal id prefix 'agm-' 고정

Test plan:
1. state/proposals/ 디렉토리 + inventory.json 생성
2. P1 1회 실행 → schema valid
3. P2 로 dummy host-axis anomaly proposal 1개 생성 → pending/
4. nexus G3 hub --dry → 4 reachable 확인
5. P9 1회 실행 → step 8.5 호출 + cross_repo_links.jsonl
6. 재실행 → dedup
7. 4 repo sidecar 동기화 확증

Success criteria:
- airgenome/state/proposals/ 가동, schema valid
- 12h cycle 매 round 직후 cross_repo_links.jsonl 갱신
- 4 repo sidecar 완전 동기화 (P12 spec 의 "4 repo wisdom 누적" 시작)
- 기존 airgenome runtime (M14 supervisor, dispatch, runaway_guard) 변경 0
```

## paste-ready prompt (끝)

---

## 메모

- 본 prompt = anima paradigm §1, §10, §16 + nexus G3 hub spec 통합 + airgenome
  고유 signal 7종.
- prerequisite: anima P11 완료 + nexus G3 hub commit (`8a05bc23`+) main 반영.
- airgenome 의 M14 6-axis genome metric 이 이미 sufficient signal 제공 — emit
  쉬운 저층 (anima 의 secret-scan/lint signal 보다 훨씬 풍부).
- hexa-lang maintainer 측에는 `own_stack_bootstrap_hexa-lang.md` (동일 패턴).

세션: 2026-04-22 nexus · G3 후속.
