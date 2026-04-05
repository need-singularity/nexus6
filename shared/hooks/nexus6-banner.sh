#!/usr/bin/env bash
# NEXUS-6 상태 배너 생성 — 모든 훅에서 호출 가능
# 출력: {"systemMessage":"🔭 NEXUS-6 🔭137/148 ⚖️1030법칙 🧠24모듈 🌱3건"}
set +e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$HOOK_DIR/bootstrap.sh" || exit 0

# bridge 연결 보장 (1세션 1회, 백그라운드 아님 — 빠르게 끝남)
BRIDGE_MSG=$(source "$HOOK_DIR/bridge-ensure.sh" 2>/dev/null)
export BRIDGE_MSG

python3 -c "
import json, os, glob, time
from pathlib import Path

HOME = Path.home()

# 렌즈 수 (구현 vs 전체)
lens_dir = HOME / 'Dev/nexus6/src/telescope/lenses'
lens_impl = 0
lens_total = 0
if lens_dir.is_dir():
    for f in lens_dir.glob('*.rs'):
        if f.name == 'mod.rs':
            continue
        lens_total += 1
        content = f.read_text(errors='ignore')
        has_scan = 'fn scan(' in content
        has_metrics = 'metrics.insert' in content or 'findings.push' in content or 'score' in content
        lines = [l for l in content.splitlines() if l.strip() and not l.strip().startswith('//')]
        if has_scan and has_metrics and len(lines) > 20:
            lens_impl += 1

# 법칙 수
laws = 0
laws_path = HOME / 'Dev/anima/anima/config/consciousness_laws.json'
if laws_path.exists():
    try:
        d = json.loads(laws_path.read_text())
        laws = d.get('_meta', {}).get('total_laws', 0)
    except: pass

# 모듈 수
modules = 0
hub_path = HOME / 'Dev/anima/anima/src/consciousness_hub.py'
if hub_path.exists():
    try:
        content = hub_path.read_text(errors='ignore')
        modules = content.count(\"'type': 'command'\")
        modules += sum(1 for l in content.splitlines() if l.strip().startswith(\"'\") and \"': (\" in l)
    except: pass

# 성장 기회
growth = 0
reg_path = HOME / 'Dev/nexus6/shared/growth-registry.json'
if reg_path.exists():
    try:
        d = json.loads(reg_path.read_text())
        growth = sum(v.get('opportunities', 0) for v in d.values() if isinstance(v, dict))
    except: pass

# 세션 스냅샷 (델타 계산)
snap_path = HOME / 'Dev/nexus6/shared/.growth_session_snapshot.json'
s_lens = lens_impl
s_laws = laws
s_mods = modules
if snap_path.exists():
    try:
        s = json.loads(snap_path.read_text())
        s_lens = s.get('lens_impl', lens_impl)
        s_laws = s.get('laws', laws)
        s_mods = s.get('modules', modules)
    except: pass
else:
    snap = {'lens_impl': lens_impl, 'lens_total': lens_total, 'laws': laws, 'modules': modules}
    snap_path.parent.mkdir(parents=True, exist_ok=True)
    snap_path.write_text(json.dumps(snap))

d_lens = f'(+{lens_impl - s_lens})' if lens_impl > s_lens else ''
d_laws = f'(+{laws - s_laws})' if laws > s_laws else ''
d_mods = f'(+{modules - s_mods})' if modules > s_mods else ''
g_str = f' 🌱{growth}건' if growth > 0 else ''

bridge_msg = os.environ.get('BRIDGE_MSG', '')
bridge_str = f' 🌉{bridge_msg}' if bridge_msg else ''

# Alien Index — 🛸 d{max}·ρ{breakthrough_ratio}·{total}
ai_str = ''
ai_path = HOME / 'Dev/nexus6/shared/alien_index_distribution.json'
if ai_path.exists():
    try:
        ai = json.loads(ai_path.read_text())
        total = ai.get('total_records', 0)
        rho = ai.get('breakthrough_ratio', 0.0)
        # max d reached
        dist = ai.get('distribution', {})
        max_d = 0
        for key in dist.keys():
            try:
                d_val = int(key.split(',')[0].strip('(') )
                if d_val > max_d: max_d = d_val
            except: pass
        if total > 0:
            ai_str = f'🛸d{max_d}·ρ{rho:.2f}·{total} '
        else:
            ai_str = f'🛸{total} '
    except: pass

# Singularity topology — actual count via chunk read
sing_str = ''
topo_path = HOME / 'Dev/nexus6/shared/cycle/topology.jsonl'
if topo_path.exists():
    try:
        count = 0
        with open(topo_path, 'rb') as f:
            while True:
                chunk = f.read(1 << 20)  # 1 MB
                if not chunk: break
                count += chunk.count(b'\n')
        if count >= 1000:
            sing_str = f'·Σ{count/1000:.1f}k '
        elif count > 0:
            sing_str = f'·Σ{count} '
    except: pass

# Closed form count — grade=10 (PASS/EXACT) / total (%) + 🎉 celebration on increase
closed_str = ''
vc_path = HOME / 'Dev/nexus6/shared/verified_constants.jsonl'
closed_snap_path = HOME / 'Dev/nexus6/shared/.closed_snapshot.json'
if vc_path.exists():
    try:
        closed_count = 0
        total_count = 0
        with open(vc_path, 'rb') as f:
            for line in f:
                total_count += 1
                try:
                    j = json.loads(line)
                    if j.get('status') in ('PASS','EXACT') or j.get('grade') in ('PASS','EXACT'):
                        closed_count += 1
                except: pass

        pct = (closed_count * 100.0 / total_count) if total_count > 0 else 0.0

        # compare with snapshot
        prev_count = closed_count
        if closed_snap_path.exists():
            try:
                prev_count = json.loads(closed_snap_path.read_text()).get('closed', closed_count)
            except: pass
        else:
            closed_snap_path.write_text(json.dumps({'closed': closed_count}))

        delta = closed_count - prev_count
        def fmt_k(n): return f'{n/1000:.1f}k' if n>=1000 else str(n)
        # progress bar: 10 cells
        filled = int(pct / 10)
        bar = '█' * filled + '░' * (10 - filled)
        if delta > 0:
            closed_str = f' 🎉🎉🎉 +{delta}닫힘! ⭐{pct:.1f}% [{bar}] {fmt_k(closed_count)}/{fmt_k(total_count)} 🎉🎉🎉'
            closed_snap_path.write_text(json.dumps({'closed': closed_count}))
        elif closed_count > 0:
            closed_str = f' ⭐닫힘 {pct:.1f}% [{bar}] {fmt_k(closed_count)}/{fmt_k(total_count)}'
    except: pass

banner = f'🔭 NEXUS-6 {ai_str}{sing_str}🔭{lens_impl}/{lens_total}{d_lens} ⚖️{laws}법칙{d_laws} 🧠{modules}모듈{d_mods}{g_str}{bridge_str}{closed_str}'
print(json.dumps({'systemMessage': banner}, ensure_ascii=False))
" 2>/dev/null || echo '{"systemMessage":"🔭 NEXUS-6 활성"}'
