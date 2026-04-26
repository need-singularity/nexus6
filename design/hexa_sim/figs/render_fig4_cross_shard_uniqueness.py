#!/usr/bin/env python3
# render_fig4_cross_shard_uniqueness.py
# ----------------------------------------------------------------------
# Paper Fig 4 — Cross-shard uniqueness: 11 shards / 9165 tuples / 0 collisions.
# Source data:
#   state/atlas_sha256.tsv                             (per-shard line counts)
#   tool/atlas_cross_shard_collision.sh witness        (9165 unique / 0 collisions)
# Outputs:
#   design/hexa_sim/figs/fig4_cross_shard_uniqueness.svg (vector)
#   design/hexa_sim/figs/fig4_cross_shard_uniqueness.png (300 dpi raster)
# Deps: python3 (stdlib) + matplotlib >= 3.5
# Run:  python3 render_fig4_cross_shard_uniqueness.py
# ----------------------------------------------------------------------
import os, sys
TSV = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'state', 'atlas_sha256.tsv')
OUT = os.path.dirname(os.path.abspath(__file__))
UNIQUE_TUPLES = 9165   # tool/atlas_cross_shard_collision.sh sentinel
COLLISIONS    = 0      # tool/atlas_cross_shard_collision.sh sentinel

def short_label(p):
    base = os.path.basename(p)
    if base == 'atlas.n6':
        return 'atlas.n6 (main)'
    s = base.replace('atlas.append.', '')
    s = s.replace('historical-from-nexus-2026-04-26', 'hist-26')
    s = s.replace('historical-absorption-2026-04-26', 'absorb-26')
    s = s.replace('-cont', '+cont')
    return s.rsplit('.n6', 1)[0]

def parse():
    rows = []
    with open(TSV) as f:
        for line in f:
            if line.startswith('#') or line.startswith('shard_path') or not line.strip():
                continue
            parts = line.rstrip().split('\t')
            if len(parts) >= 3:
                rows.append((parts[0], int(parts[2])))
    return rows

def main():
    rows = parse()
    total = sum(n for _, n in rows)
    print(f'[fig4] shards={len(rows)} total_lines={total} unique_tuples={UNIQUE_TUPLES} collisions={COLLISIONS}')
    for path, n in rows:
        print(f'  {n:>6}  {path}')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('[fig4] matplotlib not installed; data dump above is sufficient. '
              'Install: python3 -m pip install --user matplotlib', file=sys.stderr)
        return 0

    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9,
                         'axes.titlesize': 11, 'axes.labelsize': 10,
                         'figure.dpi': 100, 'savefig.bbox': 'tight'})
    rows_sorted = sorted(rows, key=lambda r: -r[1])
    labels  = [short_label(p) for p, _ in rows_sorted]
    counts  = [n for _, n in rows_sorted]
    colors  = ['#4878a6' if 'main' in lab else '#7fa8c9' for lab in labels]

    fig, ax = plt.subplots(figsize=(8, 5))
    y = list(range(len(labels)))
    bars = ax.barh(y, counts, color=colors, edgecolor='black', linewidth=0.4)
    for i, n in enumerate(counts):
        ax.text(n + max(counts) * 0.01, i, f'{n:,}', va='center', fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('shard line count (raw .n6 entries)')
    ax.set_title('Cross-shard uniqueness: 11 shards / 9,165 tuples / 0 collisions')
    ax.set_xlim(0, max(counts) * 1.15)
    ax.grid(axis='x', alpha=0.25, linestyle=':')
    caption = (f'cumulative raw lines = {total:,}  ->  dedup primitive  ->  '
               f'{UNIQUE_TUPLES:,} unique tuples  /  {COLLISIONS} collisions  '
               f'(1 main shard + {len(rows)-1} append shards)')
    fig.text(0.5, -0.04, caption, ha='center', fontsize=8, style='italic')
    svg = os.path.join(OUT, 'fig4_cross_shard_uniqueness.svg')
    png = os.path.join(OUT, 'fig4_cross_shard_uniqueness.png')
    fig.savefig(svg)
    fig.savefig(png, dpi=300)
    print(f'[fig4] wrote {svg}')
    print(f'[fig4] wrote {png}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
