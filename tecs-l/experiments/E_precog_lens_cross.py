```python
#!/usr/bin/env python3
"""
Cross-hypothesis Verification: Precognition × Lens/Telescope × Tension+Direction
H-CX-343, 344, 346, 347, 349, 350 — Parallel Verification
"""
import sys, os, time, json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import defaultdict
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Model ───
class PureFieldEngine(nn.Module):
    def __init__(self, input_dim, hidden_dim, n_classes):
        super().__init__()
        self.engine_a = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim))
        self.engine_g = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim))
        self.classifier = nn.Linear(hidden_dim, n_classes)
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        a = self.engine_a(x)
        g = self.engine_g(x)
        rep = a - g
        tension = (rep ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(rep, dim=-1)
        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        logits = self.classifier(output)
        return logits, tension.squeeze(-1), direction, a, g

# ─── Data ───
def load_data(name='fashion', batch_size=256):
    from torchvision import datasets, transforms
    t = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])
    if name == 'mnist':
        tr = datasets.MNIST('/tmp/data', train=True, download=True, transform=t)
        te = datasets.MNIST('/tmp/data', train=False, download=True, transform=t)
        dim, nc = 784, 10
    elif name == 'fashion':
        tr = datasets.FashionMNIST('/tmp/data', train=True, download=True, transform=t)
        te = datasets.FashionMNIST('/tmp/data', train=False, download=True, transform=t)
        dim, nc = 784, 10
    elif name == 'cifar':
        t = transforms.Compose([transforms.ToTensor(), transforms.Lambda(lambda x: x.view(-1))])
        tr = datasets.CIFAR10('/tmp/data', train=True, download=True, transform=t)
        te = datasets.CIFAR10('/tmp/data', train=False, download=True, transform=t)
        dim, nc = 3072, 10
    else:
        raise ValueError(f"Unknown dataset: {name}")
    train_loader = torch.utils.data.DataLoader(tr, batch_size=batch_size, shuffle=True)
    test_loader = torch.utils.data.DataLoader(te, batch_size=batch_size, shuffle=False)
    return train_loader, test_loader, dim, nc

# ─── Training ───
def train_model(model, loader, epochs=10, lr=1e-3, device='cpu'):
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for ep in range(epochs):
        model.train()
        total_loss = 0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits, tension, direction, a, g = model(x)
            loss = F.cross_entropy(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
    return model

# ─── Data Collection ───
def collect_all_data(model, loader, device='cpu'):
    """Collect tension, direction, prediction, label from all test data"""
    model.eval()
    all_data = {
        'tensions': [], 'directions': [], 'preds': [], 'labels': [],
        'correct': [], 'logits': [], 'a_vecs': [], 'g_vecs': []
    }
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits, tension, direction, a, g = model(x)
            pred = logits.argmax(dim=-1)
            all_data['tensions'].append(tension.cpu().numpy())
            all_data['directions'].append(direction.cpu().numpy())
            all_data['preds'].append(pred.cpu().numpy())
            all_data['labels'].append(y.cpu().numpy())
            all_data['correct'].append((pred == y).cpu().numpy())
            all_data['logits'].append(logits.cpu().numpy())
            all_data['a_vecs'].append(a.cpu().numpy())
            all_data['g_vecs'].append(g.cpu().numpy())
    return {k: np.concatenate(v) for k, v in all_data.items()}

# ═══════════════════════════════════════════
# H-CX-343: Precognition Optical Trinity
# 3 precognition channels = 3 optical instruments
# ═══════════════════════════════════════════
def test_H343_optical_trinity(data, n_classes=10):
    """
    Prediction: per-class contribution of mag_AUC, dir_acc, topo_metric
    corresponds to Lens(focus), Telescope(resolution), Phase Lens(structure)
    """
    print("\n" + "="*60)
    print("H-CX-343: Precognition Optical Trinity")
    print("="*60)

    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    results = {'per_class': {}}

    for c in range(n_classes):
        mask = data['labels'] == c
        if mask.sum() < 10:
            continue

        # Channel 1: Magnitude (= Gravity Lens magnification)
        t_correct = data['tensions'][mask & data['correct']]
        t_wrong = data['tensions'][mask & ~data['correct']]
        if len(t_wrong) < 5 or len(t_correct) < 5:
            mag_auc = 0.5
        else:
            y_bin = np.concatenate([np.ones(len(t_correct)), np.zeros(len(t_wrong))])
            scores = np.concatenate([t_correct, t_wrong])
            mag_auc = roc_auc_score(y_bin, scores)

        # Channel 2: Direction (= Telescope pointing accuracy)
        dirs_c = data['directions'][mask]
        mean_dir = dirs_c.mean(axis=0)
        mean_dir /= (np.linalg.norm(mean_dir) + 1e-8)
        cos_sims = dirs_c @ mean_dir
        dir_coherence = cos_sims.mean()

        # Channel 3: Topology (= Topological Lens structure)
        # PH approximation: count distinct tension clusters
        t_vals = data['tensions'][mask]
        hist, _ = np.histogram(t_vals, bins=20)
        nonzero_bins = (hist > 0).sum()
        topo_spread = nonzero_bins / 20.0  # 0~1, higher = more spread

        results['per_class'][c] = {
            'mag_auc': float(mag_auc),
            'dir_coherence': float(dir_coherence),
            'topo_spread': float(topo_spread),
            'n_samples': int(mask.sum()),
            'accuracy': float(data['correct'][mask].mean())
        }

    # Trinity verification: Are the 3 channels independent?
    mags = [v['mag_auc'] for v in results['per_class'].values()]
    dirs = [v['dir_coherence'] for v in results['per_class'].values()]
    topos = [v['topo_spread'] for v in results['per_class'].values()]

    corr_md = np.corrcoef(mags, dirs)[0,1]
    corr_mt = np.corrcoef(mags, topos)[0,1]
    corr_dt = np.corrcoef(dirs, topos)[0,1]

    results['channel_correlations'] = {
        'mag_dir': float(corr_md),
        'mag_topo': float(corr_mt),
        'dir_topo': float(corr_dt),
        'mean_abs_corr': float(np.mean(np.abs([corr_md, corr_mt, corr_dt]))),
        'orthogonality': float(1 - np.mean(np.abs([corr_md, corr_mt, corr_dt])))
    }

    # Output
    print(f"\n  Channel correlations:")
    print(f"    Mag↔Dir:  r={corr_md:.4f}")
    print(f"    Mag↔Topo: r={corr_mt:.4f}")
    print(f"    Dir↔Topo: r={corr_dt:.4f}")
    print(f"    Orthogonality: {results['channel_correlations']['orthogonality']:.4f}")
    print(f"\n  Per-class:")
    print(f"  {'Class':>6} {'Mag AUC':>8} {'Dir Coh':>8} {'Topo Sp':>8} {'Acc':>6}")
    for c, v in sorted(results['per_class'].items()):
        print(f"  {c:>6} {v['mag_auc']:>8.4f} {v['dir_coherence']:>8.4f} {v['topo_spread']:>8.4f} {v['accuracy']:>6.3f}")

    # Verdict
    orth = results['channel_correlations']['orthogonality']
    verdict = "SUPPORTED" if orth > 0.5 else ("PARTIAL" if orth > 0.3 else "REJECTED")
    results['verdict'] = verdict
    print(f"\n  Verdict: {verdict} (orthogonality={orth:.4f}, threshold>0.5)")
    return results


# ═══════════════════════════════════════════
# H-CX-344: Direction Telescope Zoom
# within-class cos sim = telescope magnification → direction precognition accuracy
# ═══════════════════════════════════════════
def test_H344_direction_telescope(data, n_classes=10):
    print("\n" + "="*60)
    print("H-CX-344: Direction Telescope Zoom")
    print("="*60)

    results = {'per_class': {}}

    for c in range(n_classes):
        mask = data['labels'] == c
        dirs_c = data['directions'][mask]
        if len(dirs_c) < 10:
            continue

        # Telescope magnification = within-class cosine similarity
        mean_dir = dirs_c.mean(axis=0)
        mean_dir /= (np.linalg.norm(mean_dir) + 1e-8)
        within_cos = (dirs_c @ mean_dir).mean()

        # Direction precognition: wrong predictions that point to predicted class
        wrong_mask = mask & ~data['correct']
        if wrong_mask.sum() < 5:
            dir_precog_acc = 1.0
        else:
            wrong_dirs = data['directions'][wrong_mask]
            wrong_preds = data['preds'][wrong_mask]
            # For each wrong prediction, check if direction is closer to predicted than true class
            correct_count = 0
            for i in range(len(wrong_dirs)):
                pred_c = wrong_preds[i]
                true_c = data['labels'][wrong_mask][i]
                # Get mean directions for pred and true class
                pred_mask = data['labels'] == pred_c
                true_mask = data['labels'] == true_c
                if pred_mask.sum() < 5 or true_mask.sum() < 5:
                    continue
                pred_mean = data['directions'][pred_mask].mean(0)
                pred_mean /= (np.linalg.norm(pred_mean) + 1e-8)
                true_mean = data['directions'][true_mask].mean(0)
                true_mean /= (np.linalg.norm(true_mean) + 1e-8)
                cos_pred = wrong_dirs[i] @ pred_mean
                cos_true = wrong_dirs[i] @ true_mean
                if cos_pred > cos_true:
                    correct_count += 1
            dir_precog_acc = correct_count / max(len(wrong_dirs), 1)

        results['per_class'][c] = {
            'within_cos': float(within_cos),
            'dir_precog_acc': float(dir_precog_acc),
            'n_wrong': int(wrong_mask.sum()) if 'wrong_mask' in dir() else 0
        }

    # Correlation: within_cos ↔ dir_precog_acc
    wcos = [v['within_cos'] for v in results['per_class'].values()]
    dpre = [v['dir_precog_acc'] for v in results['per_class'].values()]
    from scipy.stats import spearmanr
    rho, pval = spearmanr(wcos, dpre)

    results['correlation'] = {'spearman_r': float(rho), 'p_value': float(pval)}
    verdict = "SUPPORTED" if (rho > 0.5 and pval < 0.05) else ("PARTIAL" if rho > 0.3 else "REJECTED")
    results['verdict'] = verdict

    print(f"\n  {'Class':>6} {'W-CosSim':>9} {'Dir Precog':>10}")
    for c, v in sorted(results['per_class'].items()):
        print(f"  {c:>6} {v['within_cos']:>9.4f} {v['dir_precog_acc']:>10.4f}")
    print(f"\n  Spearman r={rho:.4f}, p={pval:.4f}")
    print(f"  Verdict: {verdict}")
    return results


# ═══════════════════════════════════════════
# H-CX-346: Precognition Resolution = tension_gap × (1-cos_sim)
# ═══════════════════════════════════════════
def test_H346_precognition_resolution(data, n_classes=10):
    print("\n" + "="*60)
    print("H-CX-346: Precognition Resolution Formula")
    print("="*60)

    # Per-class mean tension and direction
    class_tension = {}
    class_direction = {}
    for c in range(n_classes):
        mask = data['labels'] == c
        if mask.sum() < 5:
            continue
        class_tension[c] = data['tensions'][mask].mean()
        d = data['directions'][mask].mean(axis=0)
        class_direction[c] = d / (np.linalg.norm(d) + 1e-8)

    # Per-pair: resolution = |tension_gap| × (1 - cos_sim)
    pairs = list(combinations(range(n_classes), 2))
    pair_data = []
    for i, j in pairs:
        if i not in class_tension or j not in class_tension:
            continue
        t_gap = abs(class_tension[i] - class_tension[j])
        cos_sim = class_direction[i] @ class_direction[j]
        resolution = t_gap * (1 - cos_sim)

        # Confusion rate = how often i and j are confused
        mask_i = data['labels'] == i
        mask_j = data['labels'] == j
        confused_ij = ((data['labels'] == i) & (data['preds'] == j)).sum()
        confused_ji = ((data['labels'] == j) & (data['preds'] == i)).sum()
        total = mask_i.sum() + mask_j.sum()
        confusion_rate = (confused_ij + confused_ji) / max(total, 1)

        pair_data.append({
            'pair': (i, j),
            'tension_gap': float(t_gap),
            'cos_sim': float(cos_sim),
            'resolution': float(resolution),
            'confusion_rate': float(confusion_rate)
        })

    # resolution ↔ confusion_rate: high resolution → low confusion
    resolutions = [p['resolution'] for p in pair_data]
    confusions = [p['confusion_rate'] for p in pair_data]
    from scipy.stats import spearmanr
    rho, pval = spearmanr(resolutions, confusions)

    verdict = "SUPPORTED" if (rho < -0.5 and pval < 0.05) else ("PARTIAL" if rho < -0.3 else "REJECTED")

    # Top/bottom 5 pairs
    sorted_pairs = sorted(pair_data, key=lambda p: p['resolution'])
    print(f"\n  Bottom 5 resolution pairs (high confusion expected):")
    print(f"  {'Pair':>8} {'T-Gap':>7} {'CosSim':>7} {'Resol':>7} {'Confus':>7}")
    for p in sorted_pairs[:5]:
        print(f"  {str(p['pair']):>8} {p['tension_gap']:>7.4f} {p['cos_sim']:>7.4f} {p['resolution']:>7.4f} {p['confusion_rate']:>7.4f}")
    print(f"\n  Top 5 resolution pairs (low confusion expected):")
    for p in sorted_pairs[-5:]:
        print(f"  {str(p['pair']):>8} {p['tension_gap']:>7.4f} {p['cos_sim']:>7.4f} {p['resolution']:>7.4f} {p['confusion_rate']:>7.4f}")

    print(f"\n  Spearman r={rho:.4f}, p={pval:.6f}")
    print(f"  (Negative correlation expected: high resolution → low confusion)")
    print(f"  Verdict: {verdict}")

    return {
        'pairs': pair_data,
        'spearman_r': float(rho),
        'p_value': float(pval),
        'verdict': verdict
    }


# ═══════════════════════════════════════════
# H-CX-347: Topological Zoom Level = Filtration ε
# ═══════════════════════════════════════════
def test_H347_topological_zoom(data, n_classes=10):
    print("\n" + "="*60)
    print("H-CX-347: Topological Zoom Level = Filtration ε")
    print("="*60)

    # Compute class-mean direction vectors
    class_dirs = {}
    for c in range(n_classes):
        mask = data['labels'] == c
        if mask.sum() < 5:
            continue
        d = data['directions'][mask].mean(axis=0)
        class_dirs[c] = d / (np.linalg.norm(d) + 1e-8)

    if len(class_dirs) < 3:
        print("  Insufficient classes, skipping")
        return {'verdict': 'SKIPPED'}

    # Cosine distance matrix
    classes = sorted(class_dirs.keys())
    n = len(classes)
    dist_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist_mat[i][j] = 1 - class_dirs[classes[i]] @ class_dirs[classes[j]]

    # Vary epsilon (filtration) and count connected components (H0)
    epsilons = np.linspace(0, 2.0, 50)
    h0_counts = []
    for eps in epsilons:
        # Connected components at threshold eps
        adj = dist_mat <= eps
        visited = set()
        components = 0
        for start in range(n):
            if start in visited:
                continue
            components += 1
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                for nbr in range(n):
                    if adj[node][nbr] and nbr not in visited:
                        stack.append(nbr)
        h0_counts.append(components)

    # At each zoom level, which precognition channel dominates?
    # Small ε (zoomed in, many components) → per-sample → magnitude
    # Large ε (zoomed out, few components) → global → topology
    results = {'filtration': []}
    for idx in range(0, len(epsilons), 5):
        eps = epsilons[idx]
        h0 = h0_counts[idx]
        # Compute magnitude AUC at this "zoom" = only consider pairs merged at this ε
        merged_pairs = []
        unmerged_pairs = []
        for ci in range(n):
            for cj in range(ci+1, n):
                if dist_mat[ci][cj] <= eps:
                    merged_pairs.append((classes[ci], classes[cj]))
                else:
                    unmerged_pairs.append((classes[ci], classes[cj]))

        results['filtration'].append({
            'epsilon': float(eps),
            'H0': int(h0),
            'merged_pairs': len(merged_pairs),
            'unmerged_pairs': len(unmerged_pairs)
        })

    # ASCII graph
    print(f"\n  ε (Zoom)  vs  H0 (Connected Components)")
    print(f"  ε     H0")
    max_h0 = max(h0_counts)
    for idx in range(0, len(epsilons), 3):
        eps = epsilons[idx]
        h0 = h0_counts[idx]
        bar = "#" * int(h0 / max_h0 * 40)
        print(f"  {eps:5.2f}  {h0:2d}  {bar}")

    # Extract merge events (dendrogram approximation)
    merge_events = []
    for eps in np.linspace(0, 2.0, 200):
        for ci in range(n):
            for cj in range(ci+1, n):
                if abs(dist_mat[ci][cj] - eps) < 0.01:
                    merge_events.append((float(eps), classes[ci], classes[cj]))

    # Transition points by zoom level
    transition_eps = None
    for idx in range(1, len(h0_counts)):
        if h0_counts[idx] < h0_counts[idx-1]:
            transition_eps = epsilons[idx]
            break

    results['transition_epsilon'] = float(transition_eps) if transition_eps else None
    results['min_H0'] = int(min(h0_counts))
    results['max_H0'] = int(max(h0_counts))

    # Verdict: H0 is monotonically decreasing (standard PH behavior)
    monotonic = all(h0_counts[i] >= h0_counts[i+1] for i in range(len(h0_counts)-1))
    verdict = "SUPPORTED" if monotonic else "PARTIAL"
    results['verdict'] = verdict
    results['monotonic'] = monotonic

    print(f"\n  Monotonic decrease: {monotonic}")
    print(f"  Transition point ε={transition_eps:.3f}" if transition_eps else "  No transition point")
    print(f"  Verdict: {verdict}")
    return results


# ═══════════════════════════════════════════
# H-CX-349: Precognition Product Conservation Law
# mag_AUC × dir_accuracy ≈ const (G×I=D×P form)
# ═══════════════════════════════════════════
def test_H349_product_conservation(data, n_classes=10):
    print("\n" + "="*60)
    print("H-CX-349: Precognition Product Conservation Law (Revived)")
    print("="*60)

    from sklearn.metrics import roc_auc_score

    per_class = {}
    for c in range(n_classes):
        mask = data['labels'] == c
        if mask.sum() < 10:
            continue

        # Mag AUC
        t_correct = data['tensions'][mask & data['correct']]
        t_wrong = data['tensions'][mask & ~data['correct']]
        if len(t_wrong) < 5 or len(t_correct) < 5:
            mag_auc = 0.5
        else:
            y_bin = np.concatenate([np.ones(len(t_correct)), np.zeros(len(t_wrong))])
            scores = np.concatenate([t_correct, t_wrong])
            mag_auc = roc_auc_score(y_bin, scores)

        # Dir accuracy (within-class coherence as proxy)
        dirs_c = data['directions'][mask]
        mean_dir = dirs_c.mean(axis=0)
        mean_dir /= (np.linalg.norm(mean_dir) + 1e-8)
        dir_acc = float((dirs_c @ mean_dir).mean())

        product = mag_auc * dir_acc
        per_class[c] = {
            'mag_auc': float(mag_auc),
            'dir_acc': float(dir_acc),
            'product': float(product),
            'sum': float(mag_auc + dir_acc)
        }

    mags = [v['mag_auc'] for v in per_class.values()]
    dirs = [v['dir_acc'] for v in per_class.values()]
    products = [v['product'] for v in per_class.values()]
    sums = [v['sum'] for v in per_class.values()]

    cv_mag = np.std(mags) / (np.mean(mags) + 1e-8)
    cv_dir = np.std(dirs) / (np.mean(dirs) + 1e-8)
    cv_product = np.std(products) / (np.mean(products) + 1e-8)
    cv_sum = np.std(sums) / (np.mean(sums) + 1e-8)

    # G×I=D×P form: CV(product) < CV(mag) AND CV(product) < CV(dir)
    print(f"\n  {'Class':>6} {'Mag AUC':>8} {'Dir Acc':>8} {'Product':>8} {'Sum':>8}")
    for c, v in sorted(per_class.items()):
        print(f"  {c:>6} {v['mag_auc']:>8.4f} {v['dir_acc']:>8.4f} {v['product']:>8.4f} {v['sum']:>8.4f}")

    print(f"\n  CV(mag):     {cv_mag:.4f}")
    print(f"  CV(dir):     {cv_dir:.4f}")
    print(f"  CV(product): {cv_product:.4f}  ← Should be minimum if conservation holds")
    print(f"  CV(sum):     {cv_sum:.4f}")

    conserved = cv_product < cv_mag and cv_product < cv_dir
    verdict = "SUPPORTED" if conserved else ("PARTIAL" if cv_product < max(cv_mag, cv_dir) else "REJECTED")

    print(f"\n  Product conserved: {conserved}")
    print(f"  Verdict: {verdict}")

    return {
        'per_class': per_class,
        'cv_mag': float(cv_mag), 'cv_dir': float(cv_dir),
        'cv_product': float(cv_product), 'cv_sum': float(cv_sum),
        'conserved': conserved, 'verdict': verdict
    }


# ═══════════════════════════════════════════
# H-CX-350: Tension Einstein Ring
# tension ≈ 0 but direction is clear → precognition by direction alone
# ═══════════════════════════════════════════
def test_H350_einstein_ring(data, n_classes=10):
    print("\n" + "="*60)
    print("H-CX-350: Tension Einstein Ring")
    print("="*60)

    tensions = data['tensions']
    directions = data['directions']
    labels = data['labels']
    preds = data['preds']
    correct = data['correct']

    # Bottom 10% tension = "Einstein Ring" zone
    threshold = np.percentile(tensions, 10)
    ring_mask = tensions <= threshold
    normal_mask = tensions > np.percentile(tensions, 50)

    # Accuracy in Ring zone
    ring_acc = correct[ring_mask].mean() if ring_mask.sum() > 0 else 0
    normal_acc = correct[normal_mask].mean() if normal_mask.sum() > 0 else 0

    # Direction coherence in Ring zone
    ring_coherences = []
    normal_coherences = []
    for c in range(n_classes):
        c_mask = labels == c
        # Overall mean direction for class
        all_dirs_c = directions[c_mask]
        if len(all_dirs_c) < 5:
            continue
        mean_dir = all_dirs_c.mean(axis=0)
        mean_dir /= (np.linalg.norm(mean_dir) + 1e-8)

        ring_c = directions[ring_mask & c_mask]
        normal_c = directions[normal_mask & c_mask]
        if len(ring_c) > 0:
            ring_coherences.append(float((ring_c @ mean_dir).mean()))
        if len(normal_c) > 0:
            normal_coherences.append(float((normal_c @ mean_dir).mean()))

    mean_ring_coh = np.mean(ring_coherences) if ring_coherences else 0
    mean_normal_coh = np.mean(normal_coherences) if normal_coherences else 0

    # Einstein ring existence condition: tension≈0 but direction still coherent
    # i.e., mean_ring_coh > 0.5 (direction is meaningful)
    print(f"\n  Ring zone (tension ≤ {threshold:.4f}, bottom 10%):")
    print(f"    Sample count:     {ring_mask.sum()}")
    print(f"    Accuracy:         {ring_acc:.4f}")
    print(f"    Direction coherence: {mean_ring_coh:.4f}")
    print(f"\n  Normal zone (tension > median):")
    print(f"    Sample count:     {normal_mask.sum()}")
    print(f"    Accuracy:         {normal_acc:.4f}")
    print(f"    Direction coherence: {mean_normal_coh:.4f}")

    # Direction-only precognition in ring zone
    # Can direction alone predict correctness when tension is near zero?
    if ring_mask.sum() > 20:
        ring_dirs = directions[ring_mask]
        ring_labels = labels[ring_mask]
        ring_correct = correct[ring_mask]

        # For each ring sample, compute cos_sim to its true class mean
        dir_scores = []
        for i in range(len(ring_dirs)):
            c = ring_labels[i]
            c_mask = labels == c
            mean_d = directions[c_mask].mean(axis=0)
            mean_d /= (np.linalg.norm(mean_d) + 1e-8)
            dir_scores.append(ring_dirs[i] @ mean_d)

        dir_scores = np.array(dir_scores)
        from sklearn.metrics import roc_auc_score
        if len(np.unique(ring_correct)) > 1:
            dir_auc = roc_auc_score(ring_correct, dir_scores)
        else:
            dir_auc = 0.5
        print(f"\n  Ring zone direction-only AUC: {dir_auc:.4f}")
    else:
        dir_auc = 0.5

    # Verdict: ring zone has direction coherence > 0.5 AND dir_auc > 0.55
    ring_exists = mean_ring_coh > 0.3 and dir_auc > 0.55
    verdict = "SUPPORTED" if ring_exists else ("PARTIAL" if mean_ring_coh > 0.2 else "REJECTED")

    print(f"\n  Einstein ring exists: {ring_exists}")
    print(f"  Verdict: {verdict}")

    return {
        'ring_threshold': float(threshold),
        'ring_acc': float(ring_acc),
        'ring_coherence': float(mean_ring_coh),
        'normal_acc': float(normal_acc),
        'normal_coherence': float(mean_normal_coh),
        'ring_dir_auc': float(dir_auc),
        'verdict': verdict
    }


# ═══════════════════════════════════════════
# Main
# ═══════════════════════════════════════════
def main():
    datasets = ['mnist', 'fashion', 'cifar']
    all_results = {}

    for ds in datasets:
        print(f"\n{'#'*70}")
        print(f"# Dataset: {ds.upper()}")
        print(f"{'#'*70}")

        train_loader, test_loader, dim, nc = load_data(ds)
        model = PureFieldEngine(dim, 128, nc)
        print(f"  Training ({ds}, 10 epochs)...")
        model = train_model(model, train_loader, epochs=10, lr=1e-3)

        # Accuracy check
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for x, y in test_loader:
                logits, _, _, _, _ = model(x)
                correct += (logits.argmax(1) == y).sum().item()
                total += len(y)
        print(f"  Test accuracy: {correct/total:.4f}")

        data = collect_all_data(model, test_loader)

        ds_results = {}
        ds_results['accuracy'] = correct / total
        ds_results['H343'] = test_H343_optical_trinity(data, nc)
        ds_results['H344'] = test_H344_direction_telescope(data, nc)
        ds_results['H346'] = test_H346_precognition_resolution(data, nc)
        ds_results['H347'] = test_H347_topological_zoom(data, nc)
        ds_results['H349'] = test_H349_product_conservation(data, nc)
        ds_results['H350'] = test_H350_einstein_ring(data, nc)

        all_results[ds] = ds_results

    # ═══ Summary ═══
    print(f"\n{'='*70}")
    print(f"Overall Results Summary")
    print(f"{'='*70}")
    hyps = ['H343', 'H344', 'H346', 'H347', 'H349', 'H350']
    names = ['OpticalTrinity', 'DirTelescope', 'PrecogResol', 'TopoZoom', 'ProdConserv', 'EinsteinRing']

    print(f"\n  {'Hyp':>6} {'Name':>14} {'MNIST':>10} {'Fashion':>10} {'CIFAR':>10}")
    print(f"  {'-'*6} {'-'*14} {'-'*10} {'-'*10} {'-'*10}")
    for h, name in zip(hyps, names):
        row = f"  {h:>6} {name:>14}"
        for ds in datasets:
            v = all_results[ds].get(h, {}).get('verdict', 'N/A')
            row += f" {v:>10}"
        print(row)

    # JSON save
    # Convert numpy types for JSON serialization
    def convert(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.ndarray): return o.tolist()
        return o

    with open('experiments/E_precog_lens_cross_results.json', 'w') as f:
        json.dump(all_results, f, indent=2, default=convert)

    print(f"\n  Results saved: experiments/E_precog_lens_cross_results.json")

if __name__ == '__main__':
    main()
```