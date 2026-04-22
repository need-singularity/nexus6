# anima 측 호출 prompt — proposal_sync_hub 통합 (G3 후속)

본 문서는 anima `tool/auto_evolution_loop.hexa` (P9) 의 step 9 (notify) 직전에 nexus 의 `proposal_sync_hub` 를 호출하는 1줄 patch prompt. anima maintainer 가 그대로 paste 후 적용 가능.

---

## paste-ready prompt (시작)

```
Working dir: /Users/ghost/core/anima
관련:
  - $WS = /Users/ghost/core
  - $WS/nexus/tool/proposal_sync_hub.hexa  ← 본 patch 가 호출할 hub
  - $WS/nexus/state/proposals/inventory.json  ← nexus 측 own stack (sync 대상)
  - $WS/nexus/schemas/proposal/cross_repo_link/1.json  ← shared schema
  - $WS/anima/tool/auto_evolution_loop.hexa  ← 본 patch 의 대상 파일 (P9 산출물)
  - $WS/anima/state/proposals/  ← anima own stack (이미 존재)
  - $WS/anima/state/cross_repo_links.jsonl  ← hub 가 append 할 사이드카 (생성 자동)
  - $WS/anima/docs/anima_proposal_stack_paradigm_20260422.md  ← P12 spec §10

Task: anima auto_evolution_loop.hexa 의 step 9 (notify) 직전에 nexus
proposal_sync_hub 를 1줄 (실제로는 wrapper exec block) 호출 추가.

세부:

1. 위치: tool/auto_evolution_loop.hexa 의 step 9 (notify) 시작 직전.
   기존 step 1-8 (emit/refine/cluster/lineage/dashboard/...) 후, 사용자 알림
   직전이 cross-repo sync 결과까지 포함 알림 가능한 시점.

2. 호출:
   ```
   // step 8.5 (G3 cross-repo sync) — best-effort, 실패해도 cycle 진행.
   // 4 repo (anima/hexa-lang/airgenome/nexus) inventory 스캔 → cross_repo_link
   // emit + dedup. nexus 가 hub 호스트 (paradigm §10).
   let hub = env("HOME") + "/core/nexus/tool/proposal_sync_hub.hexa"
   let hexa_bin = env("HEXA")
   if hexa_bin.len() == 0 { hexa_bin = env("HOME") + "/.hx/bin/hexa" }
   try {
       exec(hexa_bin + " run " + hub + " --apply 2>&1 | tail -20")  // @allow-bare-exec
   } catch e {
       eprintln("cross-repo sync failed (non-fatal): " + to_string(e))
   }
   ```

3. log: hub 가 자체 `state/cross_repo_sync_log.jsonl` 에 기록. anima 의
   cycle log 에는 별도 entry 불필요 (hub log 가 SSOT).

4. step 9 (notify) 메시지에 cross-repo 결과 포함 (옵션):
   - sync_log 마지막 라인의 `new_links` 카운트 추출
   - notify 메시지에 "🔗 cross-repo: N new links" 한 줄 추가

Hard constraints:
- INVARIANT: anima 측 코드 변경은 P9 의 **1 block (5-10줄)** 만.
  step 1-8 로직 변경 금지.
- DO NOT modify nexus 측 파일 (hub 자체 호출만).
- DO NOT 호출 결과 fail 시 cycle 중단 — try/catch 로 best-effort.
- nexus repo unreachable (path 없음) 시 hub 호출 자체 skip:
  ```
  if !file_exists(hub) { return }
  ```
- hub 가 stage0 SIGKILL 받아도 anima cycle 영향 없음 (try/catch + best-effort).

Test plan:
1. nexus 의 proposal_sync_hub.hexa --help 로 동작 확인 (anima 측 빌드 환경)
2. anima auto_evolution_loop.hexa 1회 manual 실행 → step 8.5 호출 확증
3. anima/state/cross_repo_links.jsonl 생성 확인 (nexus 가 anima 측 path 도
   append)
4. nexus/state/cross_repo_links.jsonl 동일 link 존재 확인 (양방향 mirror)
5. 재실행 → dedup 동작 (no new entry)
6. notify 메시지에 cross-repo 카운트 포함 확인

Success criteria:
- anima 12h cycle 매 round 직후 cross_repo_links.jsonl 갱신
- nexus / anima 양쪽 sidecar 의 link entry 동일 (id sha256 매칭)
- anima cycle 자체는 hub 실패 시에도 정상 종료
- step 1-8 의 logic/output 변경 0 (regression 없음)
```

## paste-ready prompt (끝)

---

## 메모

- 본 prompt 는 nexus G3 hub 가 commit `8a05bc23` (이번 세션) 으로 main 에
  반영된 뒤 paste 가능.
- nexus side 에선 hub 가 standalone 동작 (anima 호출 없이도). anima 측
  patch 후 양쪽 자동 동기화.
- hexa-lang/airgenome maintainer 측은 own stack 구축 prerequisite. 그 전에
  anima/nexus 2 repo 만으로도 sync 동작 (paradigm §10 의 "2 repo 라도 의미").
- 본 patch 는 P9 step 8.5 (intermediate). step 9 (notify) 와는 별개 — hub
  실패 시에도 cycle 정상 종료가 핵심 invariant.

## 관련 문서

- nexus/state/proposals/README.md — nexus own stack 디렉토리 spec
- nexus/schemas/proposal/cross_repo_link/1.json — shared schema (4 repo 공통)
- nexus/tool/proposal_sync_hub.hexa — hub 본체
- anima/docs/anima_proposal_stack_paradigm_20260422.md §10 — paradigm spec
- anima/docs/upstream_notes/proposal_stack_cross_repo_sync.md — cross-repo
  sync 원본 prompt (hexa-lang/airgenome maintainer 측)

세션: 2026-04-22 nexus · G3 task 후속.
