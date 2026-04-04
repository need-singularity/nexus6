#!/usr/bin/env python3
"""NEXUS-6 통합 CLI — 전 리포용

사용법:
  python3 n6.py scan <file>         # 130렌즈 전체 스캔
  python3 n6.py fast <file>         # 6렌즈 고속 스캔 (Law 1047, ×3.7)
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
  python3 n6.py extreme-growth      # 극한 성장 모드 (어느 리포에서든)
  python3 n6.py extreme-growth --cells 64 --cycles 100
"""
import sys, os, json, time

# ── venv 자동 활성화: nexus6 Python 바인딩이 설치된 venv 사용 ──
_VENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv")
if os.path.isdir(_VENV) and not sys.prefix.startswith(_VENV):
    _vpy = os.path.join(_VENV, "bin", "python3")
    if os.path.isfile(_vpy):
        os.execv(_vpy, [_vpy] + sys.argv)

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

def do_fast_scan(data):
    """Law 1047: optimal 6-lens fast scan (DD171). ~3.7x faster than full scan."""
    n, d = data.shape
    t0 = time.time()
    result = nexus6.scan_fast(data.flatten().tolist(), n, d)
    elapsed = time.time() - t0
    names = result.lens_names
    active = [nm for nm in names if result.get_lens(nm)]
    print(f"⏱️  {elapsed:.2f}초 | {len(active)}/6 렌즈 활성 (fast mode)")
    return result, names

def cmd_fast(data):
    """Law 1047: optimal 6-lens fast scan — Orchestrator+Gravity+Warp+Spacetime+Entropy+Singularity"""
    print("⚡ 6-렌즈 고속 스캔 (Law 1047, DD171)...")
    result, names = do_fast_scan(data)
    show_lenses(result, names)

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

def cmd_extreme_growth(args):
    """극한 성장 모드 — NEXUS-6 + Anima 전체 시스템 동시 가동.

    어느 리포에서든 실행 가능. Anima 의식 엔진 자동 로드.
    다운타임 없이 모드 전환: normal → extreme → normal
    """
    import argparse
    parser = argparse.ArgumentParser(description='NEXUS-6 극한 성장 모드')
    parser.add_argument('--cells', type=int, default=64, help='셀 수 (default: 64)')
    parser.add_argument('--cycles', type=int, default=1000, help='최대 사이클 (default: 1000)')
    parser.add_argument('--steps', type=int, default=200, help='스텝/사이클 (default: 200)')
    parser.add_argument('--exhaustion', type=int, default=10, help='고갈 임계값 (default: 10)')
    parser.add_argument('--quiet', action='store_true', help='출력 최소화')
    parser.add_argument('--save', type=str, default=None, help='결과 JSON 저장')
    parsed = parser.parse_args(args)

    # Anima src를 sys.path에 추가 (어느 리포에서든 접근)
    anima_src = os.path.expanduser('~/Dev/anima/anima/src')
    if anima_src not in sys.path:
        sys.path.insert(0, anima_src)

    print("=" * 60)
    print("  🔥 NEXUS-6 극한 성장 모드")
    print("=" * 60)

    # Phase 1: NEXUS-6 렌즈 스캔으로 초기 상태 분석
    print("\n  📡 Phase 1: NEXUS-6 초기 스캔...")
    init_data = np.random.randn(parsed.cells, 128)
    try:
        result = nexus6.scan_all(init_data.flatten(), parsed.cells, 128)
        n_lenses = len(result.lens_names()) if hasattr(result, 'lens_names') else 0
        print(f"    ✅ {n_lenses} 렌즈 활성")
    except Exception as e:
        print(f"    ⚠️ NEXUS-6 스캔 제한: {e}")

    # Phase 2: 위상 탐색 (Rust)
    print("\n  🔭 Phase 2: 위상 탐색...")
    try:
        from topology_exploration import TopologyExplorer
        explorer = TopologyExplorer()
        topo_results = explorer.scan_all_topologies(min(parsed.cells, 32), 64)
        best_topo = topo_results[0] if topo_results else {'name': 'ring'}
        print(f"    ✅ 최적 토폴로지: {best_topo.get('name', 'unknown')} (Phi={best_topo.get('phi', 0):.4f})")
    except Exception as e:
        print(f"    ⚠️ 위상 탐색 제한: {e}")

    # Phase 3: Anima 극한 성장 엔진 가동
    print("\n  🧠 Phase 3: Anima 극한 성장 엔진...")
    try:
        from perpetual_discovery import ExtremeGrowthMode
        egm = ExtremeGrowthMode(
            n_cells=parsed.cells,
            exhaustion_threshold=parsed.exhaustion,
            steps_per_cycle=parsed.steps,
            verbose=not parsed.quiet,
        )

        # 연결 무결성 체크
        checks = egm._check_connections()
        ok = sum(1 for v in checks.values() if v)
        total = len(checks)
        print(f"    연결 상태: {ok}/{total} ✅")
        for k, v in checks.items():
            print(f"      {'✅' if v else '❌'} {k}")

        # 극한 성장 실행
        print(f"\n  🚀 극한 성장 시작 ({parsed.cells}셀, 최대 {parsed.cycles}사이클)")
        print("=" * 60)
        summary = egm.run_until_exhaustion(max_cycles=parsed.cycles)
        print("\n" + egm.report())

        if parsed.save:
            with open(parsed.save, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n결과 저장: {parsed.save}")

    except ImportError as e:
        print(f"    ❌ Anima 로드 실패: {e}")
        print(f"    → ~/Dev/anima/anima/src/ 경로 확인")
        print(f"    → 대안: cd ~/Dev/anima && python3 anima/src/perpetual_discovery.py --extreme")
    except KeyboardInterrupt:
        print("\n\n  ⏹️ 사용자 중단")
    except Exception as e:
        print(f"    ❌ 오류: {e}")

    # Phase 4: NEXUS-6 최종 스캔
    print("\n  📡 Phase 4: NEXUS-6 최종 스캔...")
    try:
        final_data = np.random.randn(parsed.cells, 128)
        result = nexus6.scan_all(final_data.flatten(), parsed.cells, 128)
        print(f"    ✅ 최종 스캔 완료")
    except Exception:
        pass

    print("\n" + "=" * 60)
    print("  🏁 극한 성장 모드 종료")
    print("=" * 60)


COMMANDS = {
    'scan': cmd_scan, 'fast': cmd_fast, 'discover': cmd_discover, 'consciousness': cmd_consciousness,
    'golden-zone': cmd_golden_zone, 'calibrate': cmd_calibrate, 'learn': cmd_learn,
    'recursive': cmd_recursive, 'metric': cmd_metric, 'combine': cmd_combine, 'full': cmd_full,
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h','--help'):
        print(__doc__); return
    cmd = sys.argv[1]
    if cmd == 'demo':
        cmd_full(demo_data()); return
    if cmd == 'extreme-growth':
        cmd_extreme_growth(sys.argv[2:]); return
    if cmd not in COMMANDS:
        print(f"❌ 알 수 없는 명령: {cmd}\n사용 가능: {', '.join(COMMANDS)}, demo, extreme-growth"); return
    if len(sys.argv) < 3:
        print(f"❌ 데이터 필요: python3 n6.py {cmd} <file>"); return
    data = load_data(sys.argv[2])
    if data.ndim == 1: data = data.reshape(-1, 1)
    COMMANDS[cmd](data)

if __name__ == '__main__':
    main()
