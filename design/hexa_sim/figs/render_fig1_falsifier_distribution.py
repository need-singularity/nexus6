#!/usr/bin/env python3
# render_fig1_falsifier_distribution.py
# ----------------------------------------------------------------------
# Paper Fig 1 — 115-falsifier distribution by atlas type x grade.
# Source data:
#   design/hexa_sim/falsifiers.jsonl                     (115 entries — total)
#   design/hexa_sim/PAPER_FIGURES_PLAN.md  Fig 1 table   (per-type [10]/[11] split)
# Outputs:
#   design/hexa_sim/figs/fig1_falsifier_distribution.svg (vector)
#   design/hexa_sim/figs/fig1_falsifier_distribution.png (300 dpi raster)
# Deps: python3 (stdlib) + matplotlib >= 3.5
# Run:  python3 render_fig1_falsifier_distribution.py
# Reproducer (matplotlib install): python3 -m pip install --user matplotlib
# ----------------------------------------------------------------------
import json, os, sys
SRC = os.path.join(os.path.dirname(__file__), '..', 'falsifiers.jsonl')
OUT = os.path.dirname(os.path.abspath(__file__))

# --- data extraction --------------------------------------------------
def count_total():
    with open(SRC) as f:
        return sum(1 for ln in f if ln.strip())

# Per-type [10]/[11] split — canonical from PAPER_FIGURES_PLAN.md Fig 1
# table; per-type split ~approximate (sentinel emits totals only).
# Order: dominance descending matches plan.
TYPES   = ['@P', '@F', '@R', '@C', '@X', '@L', '@S', '@M', '@T']
G10     = [ 22 ,  13 ,   9 ,   8 ,   9 ,   4 ,   4 ,   4 ,   3 ]
G11     = [  4 ,   3 ,   2 ,   2 ,   1 ,   1 ,   1 ,   1 ,   0 ]
ROLES   = ['primitive', 'fact', 'relation', 'compound', 'cross-shard',
           'law', 'structure', 'meta', 'topology']

def main():
    total = count_total()
    sum10, sum11 = sum(G10), sum(G11)
    print(f'[fig1] falsifiers.jsonl total = {total}')
    print(f'[fig1] [10] sum = {sum10}, [11] sum = {sum11}, total split = {sum10+sum11}')
    for t, a, b, r in zip(TYPES, G10, G11, ROLES):
        print(f'  {t:>3}  [10]={a:>2}  [11]={b:>2}  total={a+b:>2}  ({r})')
    if total != sum10 + sum11:
        print(f'[fig1] note: sum(per-type) = {sum10+sum11}; jsonl total = {total} '
              '(per-type split is approximate per PAPER_FIGURES_PLAN.md Fig 1).')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('[fig1] matplotlib not installed; data dump above is sufficient. '
              'Install: python3 -m pip install --user matplotlib', file=sys.stderr)
        return 0

    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9,
                         'axes.titlesize': 11, 'axes.labelsize': 10,
                         'figure.dpi': 100, 'savefig.bbox': 'tight'})
    fig, ax = plt.subplots(figsize=(8, 5))
    x = list(range(len(TYPES)))
    b1 = ax.bar(x, G10, color='#4878a6', edgecolor='black', linewidth=0.4, label='[10] baseline')
    b2 = ax.bar(x, G11, bottom=G10, color='#d65f5f', edgecolor='black', linewidth=0.4, label='[11] strict load-bearing')
    for i, (a, b) in enumerate(zip(G10, G11)):
        ax.text(i, a + b + 0.4, str(a + b), ha='center', va='bottom', fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(TYPES)
    ax.set_xlabel('atlas type discriminator')
    ax.set_ylabel('falsifier count')
    ax.set_title('Falsifier registry distribution by atlas type and grade')
    ax.set_ylim(0, max(a + b for a, b in zip(G10, G11)) + 5)
    ax.legend(loc='upper right', frameon=False)
    ax.grid(axis='y', alpha=0.25, linestyle=':')
    fig.text(0.5, -0.02,
             f'{total} entries / per-type [10]/[11] split per PAPER_FIGURES_PLAN.md Fig 1',
             ha='center', fontsize=8, style='italic')
    svg = os.path.join(OUT, 'fig1_falsifier_distribution.svg')
    png = os.path.join(OUT, 'fig1_falsifier_distribution.png')
    fig.savefig(svg)
    fig.savefig(png, dpi=300)
    print(f'[fig1] wrote {svg}')
    print(f'[fig1] wrote {png}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
