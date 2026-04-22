# hexa-lang 측 own stack 부트스트랩 prompt — G3 cross-repo sync 합류

본 문서는 **hexa-lang maintainer 측에 paste 가능한 spec prompt**. anima paradigm `proposal_stack_paradigm_20260422.md` (P1-P11) + nexus `proposal_sync_hub.hexa` 가 이미 준비됨. hexa-lang 이 own stack + sync 통합 시 4-repo (anima/hexa-lang/airgenome/nexus) 완전 sync 가능.

---

## paste-ready prompt (시작)

```
Working dir: /Users/ghost/core/hexa-lang
관련:
  - $WS = /Users/ghost/core
  - $WS/anima/docs/anima_proposal_stack_paradigm_20260422.md  ← 패러다임 spec (P1-P11 산출물 정의)
  - $WS/anima/state/proposals/  ← anima own stack 참조 모델 (이미 가동 중)
  - $WS/nexus/state/proposals/  ← nexus own stack (G3 hub 호스트, 이미 가동)
  - $WS/nexus/tool/proposal_sync_hub.hexa  ← cross-repo sync hub (호출만)
  - $WS/nexus/schemas/proposal/cross_repo_link/1.json  ← shared schema
  - $WS/anima/docs/upstream_notes/proposal_stack_cross_repo_sync.md  ← 원본 P12 prompt

Task: hexa-lang 에 own proposal stack (anima paradigm 미러) 구축 + nexus
G3 hub 와 sync 통합. nexus 측 hub 호출 1 block (P9 step 8.5 패턴).

세부:

1. 디렉토리 구조 (anima paradigm §1 미러):
   ```
   state/proposals/
   ├── inventory.json        SSOT — schema: hexa-lang.proposal_inventory.v1
   ├── pending/              새 제안 (review 대기)
   ├── refinement/           refine 중
   ├── debate/               충돌 라우팅
   ├── approved/             사용자 approve
   ├── rejected/             reject
   ├── archived/             implement 후 보존
   ├── clusters/             5+ 관련 묶음
   └── meta/                 super-proposal, id migration
   ```
   `.gitkeep` 으로 빈 sub-dir commit. `.gitignore` 에 `state/cross_repo_sync_log.jsonl` 만 ignore.

2. inventory.json 초기 (anima 형식 미러):
   ```json
   {
     "schema": "hexa-lang.proposal_inventory.v1",
     "id_prefix": "hxa",
     "updated_ts": "<UTC>",
     "entries": [],
     "proposals": [],
     "_meta": {
       "owner_repo": "hexa-lang",
       "sister_repos": {
         "anima":     {"prefix": "anima", "inventory_path": "$WS/anima/state/proposals/inventory.json"},
         "nexus":     {"prefix": "nxs",   "inventory_path": "$WS/nexus/state/proposals/inventory.json"},
         "airgenome": {"prefix": "agm",   "inventory_path": "$WS/airgenome/state/proposals/inventory.json"}
       },
       "cross_repo_links": [],
       "created_by": "G3 own stack bootstrap (anima paradigm §1 + §10)"
     }
   }
   ```

3. proposal id prefix `hxa-` (anima `anima-` / nexus `nxs-` / airgenome `agm-` 와 짝).
   기존 hexa-lang proposal (있다면) 첫 hub 실행 시 prefix 자동 부여.

4. P1-P11 미러 구현 (anima paradigm §16 의 12-task batch 그대로):
   - P1 inventory_init / P2 emit / P3 review / P4 approve|reject|implement|archive
   - P5 dashboard / P6 lineage_graph / P7 cluster_detect / P8 conflict_resolve
   - P9 auto_evolution_loop (12h cycle)
   - P10 spec doc / P11 memory note
   - 우선순위 권장: P1 → P2 → P9 (cycle) → P3-P5 (CLI) → P6-P8 (advanced)

5. P9 step 8.5 (nexus G3 hub 호출):
   ```hexa
   // step 8.5 (G3 cross-repo sync) — best-effort.
   let hub = env("HOME") + "/core/nexus/tool/proposal_sync_hub.hexa"
   let hexa_bin = env("HEXA")
   if hexa_bin.len() == 0 { hexa_bin = env("HOME") + "/.hx/bin/hexa" }
   if file_exists(hub) {
       try {
           exec(hexa_bin + " run " + hub + " --apply 2>&1 | tail -20")  // @allow-bare-exec
       } catch e {
           eprintln("cross-repo sync failed (non-fatal): " + to_string(e))
       }
   }
   ```

6. hexa-lang 고유 source signal (anima 의 secret-scan 같은 emit trigger):
   - `cargo build` warnings (rust 컴파일러)
   - `cargo clippy` lints
   - hexa self-host 빌드 fail (build/hexa_stage0 binary mismatch 등)
   - test/ 의 test fail
   - bench/ 의 regression
   각 signal 이 P2 emit 의 input — 자동 proposal 후보 생성.

Hard constraints:
- INVARIANT: state/proposals/ 외 디렉토리 mutate 금지
- DO NOT modify .roadmap (사용자 approve gate)
- DO NOT auto-implement (P4 approve 후에만 module emit)
- nexus repo unreachable 시 G3 hub 호출 graceful skip
- proposal id prefix 'hxa-' 고정

Test plan:
1. state/proposals/ 디렉토리 구조 + inventory.json 생성
2. P1 (inventory_init) 1회 실행 → schema valid
3. P2 (emit) 로 dummy proposal 1개 생성 → pending/ 에 JSON
4. nexus G3 hub 호출 (--dry) → reachable 3개 (+self) 확인
5. P9 1회 실행 → step 8.5 호출 + cross_repo_links.jsonl 생성
6. 재실행 → dedup 동작
7. anima/nexus 측 sidecar 와 link entry 동일 (id sha256 매칭)

Success criteria:
- hexa-lang/state/proposals/ 가동, inventory schema valid
- 12h cycle 매 round 직후 cross_repo_links.jsonl 갱신
- 4 repo (anima/hexa-lang/airgenome/nexus) sidecar 동기화 시작
- 기존 hexa-lang code (compiler/runtime) 변경 0 — 별도 state 만 추가
```

## paste-ready prompt (끝)

---

## 메모

- 본 prompt = anima paradigm §1, §10, §16 + nexus G3 hub spec 통합.
- prerequisite: anima P11 완료 + nexus G3 hub commit (`8a05bc23`+) main 반영.
- airgenome maintainer 측에는 `own_stack_bootstrap_airgenome.md` (동일 패턴)
  별도 prompt.
- own stack 만으로도 anima/hexa-lang 2 repo sync 시작. airgenome 합류는 별 timeline.

세션: 2026-04-22 nexus · G3 후속.
