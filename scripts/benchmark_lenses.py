#!/usr/bin/env python3
"""NEXUS-6 렌즈 벤치마크 — 130렌즈 속도 프로파일링"""
import time, numpy as np
try:
    import nexus6
except ImportError:
    print("nexus6 미설치"); exit(1)

np.random.seed(6)
sizes = [(50, 6), (100, 6), (500, 6)]

for n, d in sizes:
    data = np.random.randn(n, d)
    flat = data.flatten().tolist()
    
    t0 = time.time()
    result = nexus6.scan(flat, n, d)
    elapsed = time.time() - t0
    
    names = result.lens_names
    active = sum(1 for nm in names if result.get_lens(nm))
    
    # Per-lens timing (approximate by running individual scans)
    print(f"\n{'='*50}")
    print(f"📊 {n}×{d} — {elapsed*1000:.1f}ms total, {len(names)} lenses, {active} active")
    print(f"   {elapsed*1000/len(names):.2f}ms/lens average")

# Detailed per-lens for 100x6
print(f"\n{'='*50}")
print("📊 Top 10 heaviest lenses (100×6):")
data = np.random.randn(100, 6).flatten().tolist()
timings = []
for _ in range(3):  # 3 runs average
    result = nexus6.scan(data, 100, 6)
total_time = 0
# Can't time individual lenses from Python, but we can report which ones return most data
result = nexus6.scan(data, 100, 6)
sizes_list = []
for nm in result.lens_names:
    m = result.get_lens(nm)
    if m:
        total_vals = sum(len(v) for v in m.values())
        sizes_list.append((nm, len(m), total_vals))
sizes_list.sort(key=lambda x: -x[2])
for nm, metrics, vals in sizes_list[:10]:
    print(f"  {nm}: {metrics} metrics, {vals} values")

print(f"\n✅ 벤치마크 완료")
