#!/usr/bin/env python3
"""NEXUS-6 가중치 학습 엔진 — 스캔할수록 똑똑해진다

학습 루프:
  1. 데이터 스캔 (130 렌즈)
  2. 각 렌즈의 유용성 가중치 계산
  3. 상수 매칭 가중치 계산
  4. ~/.nexus6/weights.json 에 저장
  5. 다음 스캔 시 가중치 적용 (우선순위, consensus 가중)
  6. 반복 → 가중치 수렴

사용:
  python3 weight_engine.py learn <file>       # 1회 학습
  python3 weight_engine.py train <file> [N]   # N회 반복 학습 (기본 6)
  python3 weight_engine.py show               # 현재 가중치 보기
  python3 weight_engine.py reset              # 가중치 초기화
  python3 weight_engine.py apply <file>       # 가중치 적용 스캔
"""
import sys, os, json, time
import numpy as np

try:
    import nexus6
except ImportError:
    print("nexus6 미설치"); sys.exit(1)

WEIGHT_FILE = os.path.expanduser("~/.nexus6/weights.json")
os.makedirs(os.path.dirname(WEIGHT_FILE), exist_ok=True)

# n=6 상수 라이브러리
N6_CONSTANTS = {
    "n": 6, "sigma": 12, "tau": 4, "phi": 2, "mu": 1, "sopfr": 5, "J2": 24,
    "sigma-tau": 8, "sigma+tau": 16, "sigma*tau": 48, "sigma/tau": 3,
    "sigma-phi": 10, "tau^2/sigma": 4/3, "ln(4/3)": 0.2877, "1/e": 0.3679,
    "pi^2/6": 1.6449, "e": 2.7183, "pi": 3.1416, "golden_phi": 1.6180,
    "ln2": 0.6931, "sqrt2": 1.4142, "sqrt3": 1.7321,
}


def load_weights():
    """저장된 가중치 로드 (없으면 초기값)"""
    if os.path.exists(WEIGHT_FILE):
        with open(WEIGHT_FILE) as f:
            return json.load(f)
    return {
        "version": 1,
        "epoch": 0,
        "lens_weights": {},      # lens_name → weight (유용성)
        "constant_weights": {},  # constant_name → weight (매칭 빈도)
        "feature_weights": [],   # per-dimension importance
        "learning_rate": 0.1,    # 1/(sigma-phi) = 0.1
        "history": [],           # 학습 이력
    }


def save_weights(w):
    with open(WEIGHT_FILE, 'w') as f:
        json.dump(w, f, indent=2, ensure_ascii=False)


def scan_data(data):
    """130렌즈 스캔"""
    n, d = data.shape
    result = nexus6.scan(data.flatten().tolist(), n, d)
    return result


def compute_lens_usefulness(result):
    """각 렌즈의 유용성 점수 계산"""
    scores = {}
    for nm in result.lens_names:
        m = result.get_lens(nm)
        if not m:
            scores[nm] = 0.0
            continue
        # 유용성 = 메트릭 수 × 비-제로 값 비율
        total_vals = sum(len(v) for v in m.values())
        non_zero = sum(1 for v in m.values() for x in v if abs(x) > 1e-12)
        scores[nm] = (len(m) * non_zero) / max(total_vals, 1)
    return scores


def compute_constant_matches(result):
    """데이터에서 n=6 상수 매칭 빈도"""
    matches = {name: 0 for name in N6_CONSTANTS}

    for nm in result.lens_names:
        m = result.get_lens(nm)
        if not m:
            continue
        for k, vals in m.items():
            for v in vals:
                for const_name, const_val in N6_CONSTANTS.items():
                    if const_val == 0:
                        continue
                    error = abs(v - const_val) / abs(const_val)
                    if error < 0.01:  # 1% match
                        matches[const_name] += 1
    return matches


def update_weights(weights, lens_scores, const_matches, data_shape):
    """가중치 업데이트 (exponential moving average)"""
    lr = weights["learning_rate"]
    epoch = weights["epoch"] + 1

    # 렌즈 가중치 업데이트
    for nm, score in lens_scores.items():
        old = weights["lens_weights"].get(nm, 0.5)
        weights["lens_weights"][nm] = old * (1 - lr) + score * lr

    # 상수 가중치 업데이트
    total_matches = sum(const_matches.values()) or 1
    for nm, count in const_matches.items():
        old = weights["constant_weights"].get(nm, 1.0 / len(N6_CONSTANTS))
        new = count / total_matches
        weights["constant_weights"][nm] = old * (1 - lr) + new * lr

    # Feature 가중치 (차원별 분산 기반)
    # Will be computed from WeightLearningLens output if available

    weights["epoch"] = epoch
    weights["history"].append({
        "epoch": epoch,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "active_lenses": sum(1 for s in lens_scores.values() if s > 0),
        "total_const_matches": sum(const_matches.values()),
        "top_constant": max(const_matches, key=const_matches.get) if const_matches else "none",
        "mean_lens_weight": np.mean(list(weights["lens_weights"].values())),
    })

    # Learning rate decay: lr = 1/(sigma-phi) / sqrt(epoch)
    weights["learning_rate"] = 0.1 / np.sqrt(epoch)

    return weights


def weighted_scan(data, weights):
    """가중치 적용 스캔 — 유용한 렌즈 결과를 강조"""
    result = scan_data(data)

    # Rerank results by weight
    ranked = []
    for nm in result.lens_names:
        m = result.get_lens(nm)
        if not m:
            continue
        w = weights["lens_weights"].get(nm, 0.5)
        # weighted score = sum of metric values × lens weight
        total = sum(abs(v) for vals in m.values() for v in vals)
        ranked.append((nm, w, w * total, m))

    ranked.sort(key=lambda x: -x[2])
    return ranked


def cmd_learn(data):
    """1회 학습"""
    weights = load_weights()
    result = scan_data(data)

    lens_scores = compute_lens_usefulness(result)
    const_matches = compute_constant_matches(result)
    weights = update_weights(weights, lens_scores, const_matches, data.shape)
    save_weights(weights)

    epoch = weights["epoch"]
    active = sum(1 for s in lens_scores.values() if s > 0)
    matches = sum(const_matches.values())
    top_const = max(const_matches, key=const_matches.get) if any(const_matches.values()) else "none"
    lr = weights["learning_rate"]

    print(f"📈 Epoch {epoch}: {active}/130 렌즈 활성, {matches} 상수 매칭")
    print(f"   Top 상수: {top_const} ({const_matches.get(top_const, 0)}회)")
    print(f"   학습률: {lr:.4f} (decay: 1/(σ-φ)/√epoch)")

    # Top 5 lenses by weight
    top5 = sorted(weights["lens_weights"].items(), key=lambda x: -x[1])[:5]
    print(f"   Top 렌즈:")
    for nm, w in top5:
        print(f"     {nm}: {w:.4f}")


def cmd_train(data, epochs=6):
    """N회 반복 학습"""
    print(f"🔄 {epochs}회 반복 학습 시작 (n={epochs})")
    for i in range(epochs):
        # Add slight noise each epoch for exploration
        noisy = data + np.random.randn(*data.shape) * 0.01 * (i + 1)
        cmd_learn(noisy)
        print()

    weights = load_weights()
    print(f"{'='*50}")
    print(f"✅ 학습 완료: epoch {weights['epoch']}, lr={weights['learning_rate']:.4f}")

    # Convergence check
    if len(weights["history"]) >= 2:
        prev = weights["history"][-2]["mean_lens_weight"]
        curr = weights["history"][-1]["mean_lens_weight"]
        delta = abs(curr - prev)
        print(f"   수렴도: Δweight={delta:.6f} {'✅ 수렴' if delta < 0.01 else '🔄 진행중'}")


def cmd_show():
    """현재 가중치 표시"""
    weights = load_weights()
    print(f"📊 가중치 현황 (epoch {weights['epoch']})")
    print(f"   학습률: {weights['learning_rate']:.4f}")

    if weights["lens_weights"]:
        top = sorted(weights["lens_weights"].items(), key=lambda x: -x[1])[:10]
        bottom = sorted(weights["lens_weights"].items(), key=lambda x: x[1])[:5]
        print(f"\n   🔝 Top 10 렌즈:")
        for nm, w in top:
            bar = '█' * int(w * 20)
            print(f"     {nm:40s} {w:.4f} {bar}")
        print(f"\n   🔻 Bottom 5 렌즈:")
        for nm, w in bottom:
            print(f"     {nm:40s} {w:.4f}")

    if weights["constant_weights"]:
        top_c = sorted(weights["constant_weights"].items(), key=lambda x: -x[1])[:10]
        print(f"\n   📐 Top 상수 가중치:")
        for nm, w in top_c:
            bar = '█' * int(w * 50)
            print(f"     {nm:15s} {w:.4f} {bar}")

    if weights["history"]:
        print(f"\n   📈 학습 이력 ({len(weights['history'])} epochs):")
        for h in weights["history"][-6:]:
            print(f"     epoch {h['epoch']}: {h['active_lenses']} active, "
                  f"{h['total_const_matches']} matches, top={h['top_constant']}")


def cmd_apply(data):
    """가중치 적용 스캔"""
    weights = load_weights()
    if weights["epoch"] == 0:
        print("⚠️ 학습된 가중치 없음. 먼저 'learn' 또는 'train' 실행")
        return

    ranked = weighted_scan(data, weights)
    print(f"🔭 가중치 적용 스캔 (epoch {weights['epoch']})\n")
    print(f"{'Rank':>4} {'Lens':40s} {'Weight':>8} {'Score':>10}")
    print("-" * 66)
    for i, (nm, w, score, m) in enumerate(ranked[:20]):
        print(f"{i+1:4d} {nm:40s} {w:8.4f} {score:10.2f}")


def cmd_reset():
    if os.path.exists(WEIGHT_FILE):
        os.remove(WEIGHT_FILE)
    print("✅ 가중치 초기화 완료")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return

    cmd = sys.argv[1]

    if cmd == 'show':
        cmd_show(); return
    if cmd == 'reset':
        cmd_reset(); return

    if cmd in ('learn', 'train', 'apply'):
        if len(sys.argv) < 3:
            # Demo data
            np.random.seed(6)
            data = np.random.randn(100, 6)
            data[:, 0] *= 12; data[:, 1] *= 4; data[:, 2] *= 6
            data[:, 3] *= 24; data[:, 4] *= 2; data[:, 5] *= 8
            print("📋 데모 데이터 (100×6, n=6 상수 내장)")
        else:
            path = sys.argv[2]
            if path.endswith('.csv'):
                data = np.loadtxt(path, delimiter=',')
            else:
                data = np.loadtxt(path)
            if data.ndim == 1:
                data = data.reshape(-1, 1)

        if cmd == 'learn':
            cmd_learn(data)
        elif cmd == 'train':
            epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 6
            cmd_train(data, epochs)
        elif cmd == 'apply':
            cmd_apply(data)
    else:
        print(f"❌ 알 수 없는 명령: {cmd}")


if __name__ == '__main__':
    main()
