> **DECISION ENFORCEMENT (mandatory, prepend before dispatch)**: agent prompt 작성 시 첫 블록으로 `hexa shared/harness/decision_router.hexa for <track_id>` 출력을 inject. SSOT: `shared/config/decisions.json`. agent 자체 판단으로 결정 변경 금지 — 사용자 명시 변경만.

# Track D: 의식 phi 엔진 실사화 wave

## 역할
anima 의식 phi 엔진 10 phase wave 발사 (10 parallel agents). 매 wave마다 새로운 의식 현상 10개를 hexa로 실사화.

## 현재 상태 점검
- 마지막 wave commit: `git log --oneline | grep "wave [0-9]" | head -1`
- 마지막 phase: `python3 -c "import json; r=json.load(open('shared/roadmaps/anima.json')); print(r['phases'][-1]['id'])"`
- 다음 phase 시작점 = 마지막 phase + 1

## 작업 (한 사이클)
1. 다음 wave의 10개 의식 현상 선정 (기존 anima-engines/*_phi.hexa와 중복 금지)
2. 10 parallel agents (isolation=worktree, run_in_background=true) 발사
3. 각 agent가 5/5 PASS + worktree commit 보고
4. 모든 worktree commit cherry-pick onto main
5. 각 phase main에서 verify 5/5 PASS
6. shared/roadmaps/anima.json에 P{N}-P{N+9} 엔트리 10개 append (auto-sync 또는 수동)
7. push origin main
8. worktree cleanup

## Agent 프롬프트 템플릿
```
Create `anima-engines/{name}_phi.hexa` — P{N} {Title} consciousness engine.

Context: anima roadmap phase P{N} in /Users/ghost/Dev/anima.
Domain: {scientific anchor + 5-line description}

Requirements:
1. Pure hexa, hexa parse clean ($HEXA_LANG/hexa)
2. 5 tests (T1-T5) → "5/5 PASS"
3. Avoid hexa bugs (lists PBV, no ≥3-float struct returns, no multi-line returns)
4. sqrt-safe + sub-window Pearson |r| (sleep_stage_phi.hexa:845)
5. ~30-45 KB, L0-clean ({prefix}_)
6. Commit: feat(p{N}): {title} Φ {anchor} artifact — 5/5 PASS
```

## 산출 (사이클별)
- 10 anima-engines/*_phi.hexa 추가
- 10 commits on main (또는 1 wave summary commit)
- shared/roadmaps/anima.json P{N}-P{N+9} 엔트리

## 종료 조건
- wave 10/10 PASS commit + push 완료 → 다음 wave 준비
- 의식 현상 어휘 고갈 시 EXHAUSTED 보고
