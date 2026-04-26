# PAPER author/affiliation decision log

- Date: 2026-04-26
- Operator: dancinlife (this session)
- Trigger: Ω-cycle (오메가 사이클) — paper author/affiliation 결정 적용, 'all go' user authorization
- Predecessor commit: `89f7afab` (PAPER_DRAFT_v4.md created with `[ANONYMOUS — pending user authorization for attribution]`)

## Decision

| field        | value                                  | source                          |
|--------------|----------------------------------------|---------------------------------|
| author name  | dancinlife                             | `git config user.name`, session |
| email        | mk225599@proton.me                     | user auto-memory (MEMORY.md)    |
| affiliation  | Independent Researcher                 | default (사용자 명시 없음)      |
| ORCID        | not yet assigned (omitted)             | unknown — conservative omit     |
| git email    | nerve011235@gmail.com (commit-only)    | not used in paper attribution   |

Email choice rationale: paper attribution uses the contact email recorded in user memory (`mk225599@proton.me`), not the git commit email (`nerve011235@gmail.com`). git email is for VCS operational identity; paper attribution is for academic correspondence.

## Files updated (8 placeholder strings → real attribution)

| file                                                  | line | field             | from → to                                                      |
|-------------------------------------------------------|-----:|-------------------|----------------------------------------------------------------|
| design/hexa_sim/PAPER_DRAFT_v4.md                     |    3 | YAML `author`     | `[ANONYMOUS …]` → `dancinlife (Independent Researcher) <…>`    |
| design/hexa_sim/PAPER_DRAFT_v4.md                     |   12 | body `Authors / Affiliation.` | `[ANONYMOUS …]` → `dancinlife, Independent Researcher (…)` |
| design/hexa_sim/PAPER_DRAFT_v3.md                     |    3 | YAML `author`     | (same as v4)                                                   |
| design/hexa_sim/PAPER_DRAFT_v3.md                     |   12 | body header       | (same as v4)                                                   |
| design/hexa_sim/PAPER_DRAFT_v2.md                     |    3 | YAML `author`     | (same as v4)                                                   |
| design/hexa_sim/PAPER_DRAFT_v2.md                     |   12 | body header       | (same as v4)                                                   |
| design/hexa_sim/PAPER_DRAFT_v1.md                     |    3 | YAML `author`     | (same as v4)                                                   |
| design/hexa_sim/PAPER_DRAFT_v1.md                     |   12 | body header       | (same as v4)                                                   |

## Files NOT modified (intentional)

- **PAPER_S1_INTRODUCTION.md** — no author placeholder (verified by grep).
- **PAPER_BIBLIOGRAPHY.md** — no `Authors` section / no author placeholder (verified).
- **PAPER_DRAFT_v1_POLISH_LOG.md** — historical log; raw 77 audit-append-only mandates byte-identity preservation. The 3 remaining `ANONYMOUS` strings inside the log are intentional historical record of the prior polish step, not active placeholders.
- **PAPER_DRAFT_v{1..4}.md line ~2187** — `Affiliation: <optional>` template line lives inside the *Reproduction confirmation* protocol block (for independent third-party reproducers). Not the paper's own author/affiliation.

## Future amendment (user override)

The user may amend any of the four populated fields with a follow-up commit:

- legal name vs. handle (`dancinlife` is the git author handle; for arXiv submission, full legal name may be preferred)
- affiliation upgrade (e.g., university / lab when applicable)
- ORCID iD assignment (recommended for arXiv attribution; obtain from https://orcid.org)
- co-authors (this commit registers a single-author paper; multi-author block should be added if collaborators are credited)

Any such amendment should be a separate commit on top of this one (raw 77 audit-append-only — this commit is itself trackable in the audit chain).

## arXiv-readiness

With this commit, the four `PAPER_DRAFT_v{1..4}.md` files no longer carry the blocking `[ANONYMOUS …]` placeholder, so the author block satisfies arXiv submission's mandatory attribution field. Other arXiv readiness gates (license declaration, figure files, abstract length, etc.) are tracked in their respective sections of v4 and are not affected by this decision.
