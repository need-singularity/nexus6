# canon — RETIRED (2026-05-11)

이 디렉토리는 `dancinlab/canon` 리포의 **마지막 스냅샷**(Wave 6 폐기 시점 기준)이다.
원본 canon은 2026-05-11에 retirement 처리되어 README.md 1개 파일만 남기고 모든
콘텐츠가 본 `nexus/canon-infra/legacy-canon/` 으로 이동되었다.

## 폐기 시점 SHA

- canon (Wave 5 직후): `4eb869ad`
- 본 스냅샷 소스: `canon HEAD @ Wave 5 완료 시점`

## 보존된 자산 (964 files / 21 MB)

| 경로 | 트랙드 | 내용 |
|---|---:|---|
| `archive/` | 7 | 2026-04-29 deprecated artifacts (cross-repo-publish, cycle11 scratch, cycle30 py-to-hexa wip) |
| `docs/` | 9 | index.html, monte-carlo report, hexa-lang handoff, operations docs (nexus-drill-macos, remote-dispatch-cwd-mapping) |
| `domains/` | 14 | _maturity_schema.json + 13개 도메인 `_standalone_repos.md` 포인터 |
| `experiments/` | 270 | DSE, anomaly, anu_mc_verification, blowup, cross, grover_n6_uniqueness(5), lens-verify, meta, paper, structural |
| `lean4-n6/` | 45 | Lean4 N6 정리 집합 (`Main.lean`, `N6/`, `lakefile.lean`, `lean-toolchain`) — `.lake/` 빌드 산출물(1.5GB)은 제외 |
| `proposals/` | 22 | weak-classification 잔류 (anthropic fellows, kim-sangwook-quantum, kolon-materials-z6, 등) |
| `reports/` | 591 | audits/sessions/discovery/breakthroughs/changelogs/group-P/history/meta/templates/v3/v4/validation |
| 루트 docs | 6 | README.md, LICENSE, CITATION.cff, SECURITY.md, CONTRIBUTING.md, MOVED_TO_STANDALONES.md |

## 제외 (의도적)

- `lean4-n6/.lake/` (1.5GB) — Lean4 빌드 산출물, 재생성 가능
- `experiments/grover_n6_uniqueness/venv/` — Python virtualenv, 재생성 가능
- `experiments/anomaly/__pycache__/`, `scripts/__pycache__/`
- 모든 canon 로컬 dotfiles (`.doc-rules.json`, `.own.*`, `.papers-cross-repo-lint-exempt`,
  `.readme-rules.json`, `.verify_cache.json`, `.gitignore`, `.githooks/`, `.github/`,
  `.hexa-init/`, `.loop`, `.playwright-mcp/`)
- `infra_state.json` (Mac-only 깨진 symlink)
- `build/`, `scratch/` — untracked 빌드/임시

## 복구

원본 canon repo의 git 히스토리는 무손실 보존되어 있다:

```bash
cd ~/core/canon
git log --all --diff-filter=D --follow -- <path>
git show <commit-sha>:<path>
```

## 이관 트레일 (전체 Wave)

`MOVED_TO_STANDALONES.md` 참조. Wave 1–5는 도메인-귀속 자산을 hexa-* 패밀리로,
Wave 3는 인프라를 nexus로, Wave 6(본 폐기)은 잔여를 모두 보관하고 canon을 종료.
