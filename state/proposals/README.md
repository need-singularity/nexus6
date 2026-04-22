# nexus/state/proposals — own proposal stack + cross-repo sync hub

Bootstrap (G3, 2026-04-22). 본 디렉토리는 anima `proposal_stack_paradigm` (§1, §10) 의 nexus 구현체.

## 역할

| 축 | 의미 |
|---|---|
| **own stack** | nexus 자체의 proposal (atlas-blowup, roadmap_engine, hexa_remote 등 G axis 작업의 후보 idea 누적) |
| **cross-repo sync hub** | 3 sister repo (anima/hexa-lang/airgenome) inventory 를 스캔, cross_repo_link 자동 emit (mirror/satisfies/depends_on/conflicts) |

## 구조

```
state/proposals/
├── inventory.json        SSOT — entries[] 와 _meta.cross_repo_links[]
├── pending/              새 제안 (review 대기)
├── refinement/           refine 중
├── debate/               충돌 또는 conflict_with 트리거
├── approved/             사용자 approve (구현 가능)
├── rejected/             reject (사유 기록)
├── archived/             implement 후 보존
├── clusters/             5+ 관련 묶음 (cluster proposal)
└── meta/                 super-proposal, id migration log 등
```

## Schema

`anima.proposal_inventory.v1` 와 호환 (nexus 는 v1 그대로 채택). proposal id prefix `nxs-` (anima 의 anima-/hxa-/agm- 와 짝).

## hub tool

`tool/proposal_sync_hub.hexa` (G3 task) — 4 inventory 읽기 → cross_repo_link detect → 4 inventory 의 _meta 갱신.

## INVARIANT (paradigm §6)

- `state/proposals/` 외 디렉토리 mutate 금지 (hub 도 동일)
- `.roadmap` 자동 수정 금지 (사용자 approve gate)
- cross_repo_link dedup: `sha256(src_repo + src_id + tgt_repo + tgt_id + link_type)`
- circular link (A→B→C→A) → debate folder 양쪽 동시 entry
- max 50 new cross_repo_links / cycle (flood protect)
- repo 1개 unreachable 시 graceful skip
