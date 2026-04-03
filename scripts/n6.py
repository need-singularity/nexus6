#!/usr/bin/env python3
"""NEXUS-6 통합 CLI — 전 리포용

사용법:
  python3 n6.py scan <file>         # 130렌즈 전체 스캔
  python3 n6.py discover <file>     # 상수/수식 발견
  python3 n6.py consciousness <file># 의식 오케스트레이션
  python3 n6.py golden-zone <file>  # 골든존 분석
  python3 n6.py calibrate <file>    # 자동 캘리브레이션
  python3 n6.py learn <file>        # 가중치 학습
  python3 n6.py recursive <file>    # 재귀 루프
  python3 n6.py metric <file>       # 매트릭 추적
  python3 n6.py combine <file>      # 조합 엔진
  python3 n6.py full <file>         # 풀 파이프라인
  python3 n6.py demo                # 데모
"""
import sys, os, json, time
import numpy as np
try:
    import nexus6
except ImportError:
    print("⚠️  nexus6 미설치: cd ~/Dev/nexus6 && maturin develop --features python")
    sys.exit(1)

def load_data(path):
    if path.endswith('.json'):
        return np.array(json.load(open(path)), dtype=np.float64)
    elif path.endswith('.csv'):
        return np.loadtxt(path, delimiter=',', dtype=np.float64)
    return np.loadtxt(path, dtype=np.float64)

def demo_data():
    np.random.seed(6)
    base = np.random.randn(100, 6)
    base[:, 0] *= 12; base[:, 1] *= 4; base[:, 2] *= 6
    base[:, 3] *= 24; base[:, 4] *= 2; base[:, 5] *= 8
    return base

def do_scan(data):
    n, d = data.shape
    t0 = time.time()
    result = nexus6.scan(data.flatten().tolist(), n, d)
    elapsed = time.time() - t0
    names = result.lens_names
    active = [nm for nm in names if result.get_lens(nm)]
    print(f"⏱️  {elapsed:.2f}초 | {len(active)}/{len(names)} 렌즈 활성")
    return result, names

def show_lenses(result, lens_list):
    for name in lens_list:
        metrics = result.get_lens(name)
        if not metrics: continue
        keys = list(metrics.keys())[:3]
        preview = ", ".join(f"{k}={metrics[k][0]:.4f}" if metrics[k] else f"{k}=[]" for k in keys)
        print(f"  {name}: {preview}")

def cmd_scan(data):
    print("🔭 전체 스캔...")
    result, names = do_scan(data)
    show_lenses(result, names)

def cmd_discover(data):
    print("🔍 상수/수식 발견...")
    result, _ = do_scan(data)
    for key in ['ConstantDiscoveryEngineLens','ConstantCollectorLens','ConstantCombinationLens','FormulaCombinationLens']:
        m = result.get_lens(key)
        if m:
            print(f"\n📐 {key}:")
            for k, v in sorted(m.items()):
                print(f"  {k}: {[round(x,4) for x in v[:5]]}")

def cmd_consciousness(data):
    print("🧠 의식 오케스트레이션...")
    result, _ = do_scan(data)
    for key in ['ConsciousnessLens','ConsciousnessOrchestratorLens']:
        m = result.get_lens(key)
        if m:
            print(f"\n🧠 {key}:")
            for k, v in sorted(m.items()):
                print(f"  {k}: {[round(x,4) for x in v[:6]]}")

def cmd_golden_zone(data):
    print("✨ 골든존 (1/e±ln(4/3))...")
    result, _ = do_scan(data)
    m = result.get_lens('GoldenZoneLens')
    if m:
        for k, v in sorted(m.items()):
            print(f"  {k}: {[round(x,4) for x in v[:6]]}")

def cmd_calibrate(data):
    print("⚙️  캘리브레이션...")
    result, _ = do_scan(data)
    m = result.get_lens('AutoCalibrationLens')
    if m:
        for k, v in sorted(m.items()):
            print(f"  {k}: {[round(x,4) for x in v[:6]]}")

def cmd_learn(data):
    print("📈 가중치 학습...")
    result, _ = do_scan(data)
    m = result.get_lens('WeightLearningLens')
    if m:
        for k, v in sorted(m.items()):
            print(f"  {k}: {[round(x,4) for x in v[:8]]}")

def cmd_recursive(data):
    print("🔄 재귀 루프...")
    result, _ = do_scan(data)
    for key in ['RecursiveLoopLens','InfiniteDiscoveryLens']:
        m = result.get_lens(key)
        if m:
            print(f"\n🔄 {key}:")
            for k, v in sorted(m.items()):
                print(f"  {k}: {[round(x,4) for x in v[:6]]}")

def cmd_metric(data):
    print("📊 매트릭 추적...")
    result, _ = do_scan(data)
    for key in ['MetricLens','MetricDiscoveryLens']:
        m = result.get_lens(key)
        if m:
            print(f"\n📊 {key}:")
            for k, v in sorted(m.items()):
                print(f"  {k}: {[round(x,4) for x in v[:6]]}")

def cmd_combine(data):
    print("🧪 조합 엔진...")
    result, _ = do_scan(data)
    for key in ['ConstantCombinationLens','FormulaCombinationLens','ConstantFormulaLens',
                'MolecularCombinationLens','MaterialCombinationLens','ElementCombinationLens']:
        m = result.get_lens(key)
        if m:
            print(f"\n🧪 {key}:")
            for k, v in sorted(m.items()):
                print(f"  {k}: {[round(x,4) for x in v[:5]]}")

def cmd_full(data):
    print("=" * 60)
    print("🚀 NEXUS-6 풀 파이프라인")
    print("=" * 60)
    n, d = data.shape
    print(f"데이터: {n}×{d}\n")
    result, names = do_scan(data)
    cats = {
        '🧠 의식': ['ConsciousnessLens','ConsciousnessOrchestratorLens'],
        '🔭 물리': ['WarpLens','SpacetimeLens','FusionLens','FissionLens','TachyonLens'],
        '📐 수학': ['PiLens','PrimeLens','GoldenRatioLens','InfinityLens','GoldenZoneLens'],
        '🔍 발견': ['ConstantDiscoveryEngineLens','LensDiscoveryLens','EngineDiscoveryLens'],
        '📈 학습': ['WeightLearningLens','AutoCalibrationLens','OverfittingLens'],
        '🔄 재귀': ['RecursiveLoopLens','InfiniteDiscoveryLens'],
        '🧪 조합': ['ConstantCombinationLens','FormulaCombinationLens','ElementCombinationLens'],
        '👁 관측': ['GodsEyeLens','AllSeeingEyeLens','ProvidenceEyeLens'],
        '⚡ 동역학': ['ChaosLens','StabilityLens','TensionLens','EventHorizonLens'],
        '💎 구조': ['DiamondLens','SphericalLens','KaleidoscopeLens','DimensionalBridgeLens'],
    }
    for cat, lenses in cats.items():
        active = [l for l in lenses if result.get_lens(l)]
        if active:
            print(f"{cat} ({len(active)}/{len(lenses)}):")
            for l in active:
                m = result.get_lens(l)
                fk = next(iter(m))
                print(f"  {l}: {fk}={m[fk][0]:.4f}" if m[fk] else f"  {l}: {fk}=[]")
            print()
    total_active = sum(1 for nm in names if result.get_lens(nm))
    print(f"{'='*60}\n총 {total_active}/{len(names)} 렌즈 활성\n{'='*60}")

COMMANDS = {
    'scan': cmd_scan, 'discover': cmd_discover, 'consciousness': cmd_consciousness,
    'golden-zone': cmd_golden_zone, 'calibrate': cmd_calibrate, 'learn': cmd_learn,
    'recursive': cmd_recursive, 'metric': cmd_metric, 'combine': cmd_combine, 'full': cmd_full,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h','--help'):
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == 'demo':
        cmd_full(demo_data()); return
    if cmd not in COMMANDS:
        print(f"❌ 알 수 없는 명령: {cmd}\n사용 가능: {', '.join(COMMANDS)}, demo"); return
    if len(sys.argv) < 3:
        print(f"❌ 데이터 필요: python3 n6.py {cmd} <file>"); return
    data = load_data(sys.argv[2])
    if data.ndim == 1: data = data.reshape(-1, 1)
    COMMANDS[cmd](data)

if __name__ == '__main__':
    main()
