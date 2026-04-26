# PAPER_DRAFT_v5 Pandoc dry-run smoke log

- **Date.** 2026-04-26
- **Operator.** dancinlife (Ω-cycle session, Pandoc smoke axis)
- **Trigger.** Ω-cycle (오메가 사이클) — `PAPER_V5_ARXIV_PREP_LOG.md` documented
  the Pandoc smoke command but did not execute it; this log records the actual
  dry-run.
- **Subject commit ancestor.** `a0794250` (PAPER_DRAFT_v5.md, 14,855 words / 2,336 lines).
- **raw 71 compliance.** v5 source byte-untouched; all artefacts under `/tmp/`.

## Toolchain

| component   | version / path                                  |
|-------------|-------------------------------------------------|
| pandoc      | `3.9.0.2` (`/opt/homebrew/bin/pandoc`, Lua 5.4) |
| xelatex     | `/Library/TeX/texbin/xelatex` (TeX Live 2026)   |
| pdflatex    | `/Library/TeX/texbin/pdflatex` (available, unused) |
| lualatex    | `/Library/TeX/texbin/lualatex` (available, unused) |

## Run 1 — PDF (xelatex)

```
PATH=/Library/TeX/texbin:$PATH pandoc -f markdown-yaml_metadata_block \
  design/hexa_sim/PAPER_DRAFT_v5.md \
  -o /tmp/paper_v5_smoke.pdf \
  --pdf-engine=xelatex \
  --metadata title="n=6 as foundational invariant"
```

| metric         | value                              |
|----------------|------------------------------------|
| exit status    | `0` (PASS)                         |
| wall time      | `2.66 s` (user 2.13 s + sys 0.26 s)|
| output path    | `/tmp/paper_v5_smoke.pdf`          |
| size           | `250,764 B` (245 KB)               |
| format         | PDF 1.7 (zip deflate)              |
| log            | `/tmp/pandoc_smoke.log` (65 lines) |
| errors         | `0`                                |
| warnings       | `65` (all "Missing character" font glyph)|

### First-attempt failure (for record)

The naïve invocation (no `-f` extension override) failed:

```
Error parsing YAML metadata at "PAPER_DRAFT_v5.md" (line 1339, column 1):
YAML parse exception at line 12, column 0: did not find expected <document start>
```

Root cause: the v5 doc uses `---` thematic-break separators throughout (e.g.
between §10 and §11 at line 1339); pandoc's `yaml_metadata_block` extension
re-parses every `---` as a candidate frontmatter opener. Mitigation:
`-f markdown-yaml_metadata_block` (disable the extension after the leading
YAML is consumed via `--metadata`).

## Run 2 — HTML (mathjax)

```
pandoc -f markdown-yaml_metadata_block design/hexa_sim/PAPER_DRAFT_v5.md \
  -o /tmp/paper_v5_smoke.html -s --mathjax
```

| metric    | value                       |
|-----------|-----------------------------|
| exit      | `0` (PASS, silent)          |
| size      | `175,850 B` (172 KB)        |
| output    | `/tmp/paper_v5_smoke.html`  |

## arXiv-specific checks

| axis                     | finding                                                                  | status |
|--------------------------|--------------------------------------------------------------------------|--------|
| LaTeX math `$...$`       | 423 inline math runs; 13 display `$$`; all balanced (xelatex compiled)   | OK     |
| `\mathrm{}` leakage      | 5 occurrences, all inside `$...$` (no raw bleed into prose)              | OK     |
| BibTeX-style entries     | 21 `@…{…}` records present; doc also has 52 dash-prefixed bib lines      | OK     |
| 88-ref claim             | Body cross-cites § markers; full bibliography in `PAPER_BIBLIOGRAPHY.md` (per prep log) — body has the partial bib only; ToC count not counted in smoke | NOTE |
| Cross-references (§N)    | §1, §1.2, §1.4, …, §13.16 — all syntactic; no broken `??` markers        | OK     |
| Mermaid block (Fig 2)    | `flowchart LR` at line 1540; pandoc passes as `<pre><code class="mermaid">`; ASCII fallback present immediately below | DEGRADE |
| Markdown tables          | 118 pipe-table rows; xelatex render OK                                   | OK     |
| Unicode glyphs           | 23 distinct chars not in Latin Modern: `α λ μ π σ τ φ χ 𝜎 ⁵ ⁻ ₀ ₂ ₄ ₆ ℤ ↔ ≅ ≈ ⋅ ⟺ ᵏ ⁿ` — rendered as `?` boxes | WARN |
| Raw LaTeX command leak   | `pdftotext` not present (cannot count glyphs in PDF text); inspection of `\\\\(mathrm\|cong\|sigma\|varphi)` against source shows zero raw bleed outside `$...$` | OK |

## Recommendations (pre-arXiv)

1. **Unicode glyph fallback (P0).** Add to a future YAML header (or pandoc
   invocation) `mainfont: "Latin Modern Math"` or `--variable mainfontfallback="STIX Two Math:; Symbola:"`, or pre-substitute `α → \alpha`, `≅ → \cong`, etc. via a short sed pass on a build copy. arXiv's TeX build runs `pdflatex` by default and would render these as boxes too; switching the doc to use TeX math throughout is the durable fix.
2. **Mermaid (P1).** arXiv won't render mermaid; Fig 2 already ships an ASCII
   fallback. Either (a) export the mermaid block to `figs/fig2_defense_layers.{svg,png}` like Figs 1/4, or (b) drop the mermaid block (keep ASCII) for the arXiv submission.
3. **YAML/`---` collision (P1).** Document the
   `-f markdown-yaml_metadata_block` invariant in `PAPER_V5_ARXIV_PREP_LOG.md`'s
   Pandoc command, or convert mid-doc `---` separators to `***`/blank-line breaks. arXiv's TeX route doesn't re-parse YAML so this is local-only, but
   the smoke command in the prep log is currently misleading.

## Verdict

| question                                        | answer |
|-------------------------------------------------|--------|
| Pandoc installed?                               | **Y** (3.9.0.2) |
| PDF generated?                                  | **Y** (`/tmp/paper_v5_smoke.pdf`, 245 KB, 2.66 s) |
| HTML generated?                                 | **Y** (`/tmp/paper_v5_smoke.html`, 172 KB) |
| LaTeX leak detected?                            | **N** (all `\mathrm` inside `$...$`) |
| arXiv submit-ready (post-smoke)?                | **Conditional Y** — PDF compiles end-to-end with zero TeX errors; the 23-glyph unicode-fallback gap is cosmetic-only (arXiv will compile but show boxes for those glyphs); fix per Recommendation 1 before final upload. Mermaid fallback (Recommendation 2) is one extra PNG export. |

Smoke artefacts ephemeral under `/tmp/` (raw 71): `paper_v5_smoke.pdf`,
`paper_v5_smoke.html`, `pandoc_smoke.log`, `pandoc_smoke_html.log`.
