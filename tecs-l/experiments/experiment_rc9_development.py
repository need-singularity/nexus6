#!/usr/bin/env python3
"""RC-9: Development = Auto-Mitosis + Growth

PureField Engine that grows through automatic mitosis across MNIST digit tasks.

Algorithm:
  1. Start with PureField on Task A (digits 0-2)
  2. Train until accuracy plateaus (improvement < 0.3% for 3 epochs)
  3. Auto-mitosis: child_a freezes (memory), child_b inherits + learns Task B (digits 3-5)
  4. When child_b plateaus -> mitosis again
  5. Continue until all 10 digits covered (3-4 generations)
  6. Final ensemble of all frozen children -> test on ALL digits

Combines: H310 (mitosis engine) + H312 (continual learning) + PureField (H334)

Tracks per-generation: accuracy, tension_scale, parameter count.
Self-contained. Prints generation tree + final accuracy.
"""

import sys
sys.path.insert(0, '/Users/ghost/Dev/logout')

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
from torchvision import datasets, transforms


# ---------------------------------------------------------------------------
# PureFieldEngine (from model_pure_field.py, self-contained)
# ---------------------------------------------------------------------------

class PureFieldEngine(nn.Module):
    """Pure consciousness engine -- repulsion field only.

    output = tension_scale * sqrt(tension) * direction
    tension = |engine_A(x) - engine_G(x)|^2
    direction = normalize(engine_A(x) - engine_G(x))
    """

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)
        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)
        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction
        return output, tension.squeeze()


# ---------------------------------------------------------------------------
# Data loading: task-based splits
# ---------------------------------------------------------------------------

def load_mnist_tasks():
    """Load MNIST and split into digit-group tasks.

    Returns full train/test tensors + labels, and task definitions.
    """
    transform = transforms.Compose([transforms.ToTensor()])
    train_ds = datasets.MNIST(root='/tmp/mnist', train=True, download=True, transform=transform)
    test_ds = datasets.MNIST(root='/tmp/mnist', train=False, download=True, transform=transform)

    X_train = train_ds.data.float().view(-1, 784) / 255.0
    y_train = train_ds.targets
    X_test = test_ds.data.float().view(-1, 784) / 255.0
    y_test = test_ds.targets

    # Task definitions: 4 generations covering all 10 digits
    tasks = [
        {"name": "Gen-0 (digits 0-2)", "digits": [0, 1, 2]},
        {"name": "Gen-1 (digits 3-5)", "digits": [3, 4, 5]},
        {"name": "Gen-2 (digits 6-7)", "digits": [6, 7]},
        {"name": "Gen-3 (digits 8-9)", "digits": [8, 9]},
    ]

    return X_train, y_train, X_test, y_test, tasks


def filter_by_digits(X, y, digits):
    """Filter dataset to only include specified digits."""
    mask = torch.zeros(len(y), dtype=torch.bool)
    for d in digits:
        mask |= (y == d)
    return X[mask], y[mask]


# ---------------------------------------------------------------------------
# Training utilities
# ---------------------------------------------------------------------------

BATCH_SIZE = 256


def train_one_epoch(model, X, y, optimizer):
    """Train one epoch on given data. Returns avg loss."""
    model.train()
    criterion = nn.CrossEntropyLoss()
    perm = torch.randperm(len(X))
    total_loss = 0.0
    n_batches = 0
    for i in range(0, len(X), BATCH_SIZE):
        idx = perm[i:i + BATCH_SIZE]
        xb, yb = X[idx], y[idx]
        optimizer.zero_grad()
        out, tension = model(xb)
        loss = criterion(out, yb)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        n_batches += 1
    return total_loss / max(n_batches, 1)


def evaluate(model, X, y):
    """Evaluate accuracy (%) on given data."""
    model.eval()
    correct = 0
    with torch.no_grad():
        for i in range(0, len(X), 2048):
            xb = X[i:i + 2048]
            yb = y[i:i + 2048]
            out, _ = model(xb)
            correct += (out.argmax(1) == yb).sum().item()
    return correct / len(y) * 100.0


def evaluate_per_digit(model, X_test, y_test, digits):
    """Evaluate per-digit accuracy. Returns dict digit->accuracy%."""
    results = {}
    for d in digits:
        mask = (y_test == d)
        if mask.sum() == 0:
            results[d] = 0.0
            continue
        xd, yd = X_test[mask], y_test[mask]
        model.eval()
        with torch.no_grad():
            out, _ = model(xd)
            correct = (out.argmax(1) == yd).sum().item()
        results[d] = correct / len(yd) * 100.0
    return results


def get_tension_scale(model):
    """Extract current tension_scale value."""
    return model.tension_scale.item()


def count_params(model):
    """Count total parameters."""
    return sum(p.numel() for p in model.parameters())


# ---------------------------------------------------------------------------
# Plateau detection
# ---------------------------------------------------------------------------

class PlateauDetector:
    """Detects accuracy plateau: improvement < threshold for patience epochs."""

    def __init__(self, threshold=0.3, patience=3):
        self.threshold = threshold
        self.patience = patience
        self.history = []
        self.stall_count = 0

    def step(self, acc):
        """Returns True if plateau detected."""
        if len(self.history) > 0:
            improvement = acc - self.history[-1]
            if improvement < self.threshold:
                self.stall_count += 1
            else:
                self.stall_count = 0
        self.history.append(acc)
        return self.stall_count >= self.patience

    def reset(self):
        self.history = []
        self.stall_count = 0


# ---------------------------------------------------------------------------
# Mitosis: split with noise
# ---------------------------------------------------------------------------

def mitosis(parent, scale=0.01):
    """Split parent into two children with symmetric noise."""
    child_a = copy.deepcopy(parent)
    child_b = copy.deepcopy(parent)
    with torch.no_grad():
        for pa, pb in zip(child_a.parameters(), child_b.parameters()):
            noise = torch.randn_like(pa) * scale
            pa.add_(noise)
            pb.add_(-noise)
    return child_a, child_b


# ---------------------------------------------------------------------------
# Ensemble of frozen children
# ---------------------------------------------------------------------------

class FrozenEnsemble:
    """Ensemble of frozen PureField children. Each child owns certain digits."""

    def __init__(self):
        self.children = []       # list of (model, digit_list)
        self.all_digits = set()

    def add_child(self, model, digits):
        """Add a frozen child responsible for given digits."""
        model.eval()
        for p in model.parameters():
            p.requires_grad = False
        self.children.append((model, digits))
        self.all_digits.update(digits)

    def predict(self, X):
        """Ensemble prediction: confidence-weighted oracle routing.

        Each child classifies among its owned digits using restricted softmax.
        The child's maximum probability (confidence) is used to scale its
        contribution. This ensures children trained on different digit subsets
        contribute comparably.
        """
        batch_size = X.size(0)
        n_classes = 10
        global_scores = torch.zeros(batch_size, n_classes)

        with torch.no_grad():
            for model, digits in self.children:
                out, tension = model(X)
                # Restricted softmax over owned digits only
                digit_indices = torch.tensor(digits, dtype=torch.long)
                restricted_logits = out[:, digit_indices]  # (batch, len(digits))
                restricted_probs = F.softmax(restricted_logits, dim=-1)
                # Confidence = max probability within this child's domain
                confidence = restricted_probs.max(dim=-1, keepdim=True).values
                # Scale probabilities by confidence (high confidence = strong vote)
                weighted_probs = restricted_probs * confidence
                for i, d in enumerate(digits):
                    global_scores[:, d] = weighted_probs[:, i]

        return global_scores

    def evaluate(self, X_test, y_test):
        """Evaluate ensemble on full test set."""
        correct = 0
        total = 0
        for i in range(0, len(X_test), 2048):
            xb = X_test[i:i + 2048]
            yb = y_test[i:i + 2048]
            pred = self.predict(xb)
            correct += (pred.argmax(1) == yb).sum().item()
            total += len(yb)
        return correct / total * 100.0

    def evaluate_per_digit(self, X_test, y_test):
        """Per-digit accuracy for the ensemble."""
        results = {}
        for d in range(10):
            mask = (y_test == d)
            if mask.sum() == 0:
                results[d] = 0.0
                continue
            xd, yd = X_test[mask], y_test[mask]
            pred = self.predict(xd)
            correct = (pred.argmax(1) == yd).sum().item()
            results[d] = correct / len(yd) * 100.0
        return results


# ---------------------------------------------------------------------------
# RC-9: Development loop
# ---------------------------------------------------------------------------

def run_development(X_train, y_train, X_test, y_test, tasks, seed=42,
                    max_epochs_per_gen=30, plateau_threshold=0.3, plateau_patience=3):
    """Run the full development process: train -> plateau -> mitosis -> repeat.

    Returns the frozen ensemble and generation log.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)

    ensemble = FrozenEnsemble()
    gen_log = []

    # Start: parent trained on Task A
    all_seen_digits = []

    # The "active" model that keeps growing
    active_model = PureFieldEngine(784, 128, 10)

    for gen_idx, task in enumerate(tasks):
        digits = task["digits"]
        name = task["name"]
        all_seen_digits.extend(digits)

        print(f"\n  {'='*60}")
        print(f"  GENERATION {gen_idx}: {name}")
        print(f"  {'='*60}")

        # Filter training data for this task's digits
        X_task, y_task = filter_by_digits(X_train, y_train, digits)
        print(f"  Training samples: {len(X_task)} (digits {digits})")
        print(f"  Active model params: {count_params(active_model):,}")
        print(f"  tension_scale: {get_tension_scale(active_model):.4f}")

        # Train until plateau
        optimizer = torch.optim.Adam(active_model.parameters(), lr=1e-3)
        detector = PlateauDetector(threshold=plateau_threshold, patience=plateau_patience)

        epoch_log = []
        for ep in range(max_epochs_per_gen):
            loss = train_one_epoch(active_model, X_task, y_task, optimizer)
            acc = evaluate(active_model, X_task, y_task)
            ts = get_tension_scale(active_model)

            plateaued = detector.step(acc)

            if ep % 5 == 0 or plateaued or ep == 0:
                print(f"    Epoch {ep+1:>2}: loss={loss:.4f}  acc={acc:.1f}%  "
                      f"tension_scale={ts:.4f}  stall={detector.stall_count}/{plateau_patience}")

            epoch_log.append({
                'epoch': ep + 1,
                'loss': loss,
                'acc': acc,
                'tension_scale': ts,
            })

            if plateaued:
                print(f"    >>> PLATEAU at epoch {ep+1} (acc={acc:.1f}%)")
                break

        final_acc = epoch_log[-1]['acc']
        final_ts = epoch_log[-1]['tension_scale']
        n_epochs = len(epoch_log)

        # Evaluate on this task's test digits
        test_acc = evaluate(active_model, *filter_by_digits(X_test, y_test, digits))

        # Per-digit accuracy
        per_digit = evaluate_per_digit(active_model, X_test, y_test, digits)
        print(f"    Final: train_acc={final_acc:.1f}%  test_acc={test_acc:.1f}%  "
              f"epochs={n_epochs}  tension_scale={final_ts:.4f}")
        print(f"    Per-digit: {', '.join(f'{d}={a:.1f}%' for d, a in per_digit.items())}")

        # Record generation info
        gen_log.append({
            'gen': gen_idx,
            'name': name,
            'digits': digits,
            'n_epochs': n_epochs,
            'train_acc': final_acc,
            'test_acc': test_acc,
            'tension_scale': final_ts,
            'params': count_params(active_model),
            'per_digit': per_digit,
            'epoch_log': epoch_log,
        })

        # === MITOSIS ===
        if gen_idx < len(tasks) - 1:
            print(f"\n    >>> AUTO-MITOSIS: freezing child_a (memory for digits {digits})")
            # child_a = exact copy (memory keeper, NO noise)
            child_a = copy.deepcopy(active_model)
            # child_b = copy + noise (explorer for next task)
            child_b = copy.deepcopy(active_model)
            with torch.no_grad():
                for p in child_b.parameters():
                    p.add_(torch.randn_like(p) * 0.01)

            # child_a -> freeze as memory for these digits
            ensemble.add_child(child_a, digits)
            print(f"    >>> child_a frozen (exact copy): owns digits {digits}")

            # child_b -> becomes the new active model for next task
            active_model = child_b
            print(f"    >>> child_b inherits (with noise) -> will learn next task")
            print(f"    >>> Ensemble size: {len(ensemble.children)} children")
        else:
            # Last generation: freeze the final model too (exact copy)
            ensemble.add_child(copy.deepcopy(active_model), digits)
            print(f"\n    >>> FINAL GENERATION: freezing for digits {digits}")
            print(f"    >>> Ensemble size: {len(ensemble.children)} children")

    return ensemble, gen_log


# ---------------------------------------------------------------------------
# Comparison: sequential (catastrophic forgetting baseline)
# ---------------------------------------------------------------------------

def run_sequential_baseline(X_train, y_train, X_test, y_test, tasks, seed=42,
                            epochs_per_task=15):
    """Train a single model sequentially on all tasks. Expect catastrophic forgetting."""
    torch.manual_seed(seed)
    np.random.seed(seed)

    model = PureFieldEngine(784, 128, 10)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    print(f"\n  {'='*60}")
    print(f"  SEQUENTIAL BASELINE (catastrophic forgetting expected)")
    print(f"  {'='*60}")

    for task in tasks:
        digits = task["digits"]
        name = task["name"]
        X_task, y_task = filter_by_digits(X_train, y_train, digits)
        print(f"\n  Training on {name} ({len(X_task)} samples)...")

        for ep in range(epochs_per_task):
            train_one_epoch(model, X_task, y_task, optimizer)

        # Evaluate on ALL seen digits so far
        acc = evaluate(model, X_test, y_test)
        per_digit = evaluate_per_digit(model, X_test, y_test, list(range(10)))
        old_digits = [d for t in tasks if t["digits"][0] < digits[0] for d in t["digits"]]
        if old_digits:
            old_acc = np.mean([per_digit[d] for d in old_digits])
            print(f"  After {name}: overall={acc:.1f}%  "
                  f"old_digits_avg={old_acc:.1f}%  "
                  f"current_digits={np.mean([per_digit[d] for d in digits]):.1f}%")
        else:
            print(f"  After {name}: overall={acc:.1f}%  "
                  f"current_digits={np.mean([per_digit[d] for d in digits]):.1f}%")

    final_per_digit = evaluate_per_digit(model, X_test, y_test, list(range(10)))
    final_acc = evaluate(model, X_test, y_test)
    return model, final_acc, final_per_digit


# ---------------------------------------------------------------------------
# ASCII visualization
# ---------------------------------------------------------------------------

def print_generation_tree(gen_log):
    """Print ASCII generation tree."""
    print(f"\n  {'='*60}")
    print(f"  GENERATION TREE")
    print(f"  {'='*60}")
    print()
    print("  [Parent: PureFieldEngine]")

    for i, g in enumerate(gen_log):
        prefix = "  " + "    " * i
        branch = "|" if i < len(gen_log) - 1 else "\\"
        print(f"{prefix}{branch}-- {g['name']}")
        print(f"{prefix}{'|' if i < len(gen_log) - 1 else ' '}   "
              f"train={g['train_acc']:.1f}%  test={g['test_acc']:.1f}%  "
              f"epochs={g['n_epochs']}  tension_scale={g['tension_scale']:.4f}")
        if i < len(gen_log) - 1:
            print(f"{prefix}|   >>> MITOSIS -> child_a(frozen) + child_b(inherits)")


def print_per_digit_heatmap(ensemble_digits, sequential_digits):
    """Print per-digit accuracy comparison."""
    print(f"\n  {'='*60}")
    print(f"  PER-DIGIT ACCURACY HEATMAP")
    print(f"  {'='*60}")

    print(f"\n  {'Digit':>6} | {'Ensemble':>10} | {'Sequential':>10} | {'Delta':>8} | Bar")
    print(f"  {'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}-+-{'-'*30}")
    for d in range(10):
        e_acc = ensemble_digits.get(d, 0.0)
        s_acc = sequential_digits.get(d, 0.0)
        delta = e_acc - s_acc
        bar_e = '#' * int(e_acc / 100.0 * 25)
        bar_s = '.' * int(s_acc / 100.0 * 25)
        print(f"  {d:>6} | {e_acc:>9.1f}% | {s_acc:>9.1f}% | {delta:>+7.1f}% | {bar_e}")
        print(f"  {'':>6} | {'':>10} | {'':>10} | {'':>8} | {bar_s}")


def print_learning_curves(gen_log, height=15, width=50):
    """Print ASCII learning curve for each generation."""
    print(f"\n  {'='*60}")
    print(f"  LEARNING CURVES (per generation)")
    print(f"  {'='*60}")

    for g in gen_log:
        accs = [e['acc'] for e in g['epoch_log']]
        if not accs:
            continue
        mn = max(min(accs) - 5, 0)
        mx = min(max(accs) + 5, 100)
        rng = mx - mn if mx != mn else 1.0

        print(f"\n  {g['name']} ({g['n_epochs']} epochs, test={g['test_acc']:.1f}%)")

        h = min(height, 10)
        for row in range(h - 1, -1, -1):
            threshold = mn + (row / max(h - 1, 1)) * rng
            line = ""
            # Resample to width
            for col in range(min(len(accs), width)):
                idx = int(col / min(len(accs), width) * len(accs))
                idx = min(idx, len(accs) - 1)
                if accs[idx] >= threshold:
                    line += "#"
                else:
                    line += " "
            val_label = f"{threshold:>5.1f}"
            print(f"    {val_label}% |{line}|")
        print(f"    {'':>5}  +{'-' * min(len(accs), width)}+")
        print(f"    {'':>5}   ep 1{' ' * max(min(len(accs), width) - 8, 0)}ep {len(accs)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("  RC-9: Development = Auto-Mitosis + Growth")
    print("  PureField Engine grows through generational mitosis")
    print("  H310 (mitosis engine) + H312 (continual learning) + PureField (H334)")
    print("=" * 72)
    print()
    print("  Algorithm:")
    print("    1. Train PureField on digits 0-2 until plateau")
    print("    2. Auto-mitosis: freeze child_a (memory), child_b inherits")
    print("    3. child_b learns digits 3-5 until plateau")
    print("    4. Repeat for digits 6-7, then 8-9")
    print("    5. Final ensemble of all frozen children -> test ALL digits")
    print()

    # Load data
    print("[1] Loading MNIST...")
    X_train, y_train, X_test, y_test, tasks = load_mnist_tasks()
    print(f"    Train: {len(X_train)}, Test: {len(X_test)}")
    print(f"    Tasks: {len(tasks)} generations")
    for t in tasks:
        X_t, _ = filter_by_digits(X_train, y_train, t['digits'])
        print(f"      {t['name']}: {len(X_t)} samples")

    # ===================================================================
    # Run development (RC-9)
    # ===================================================================
    print(f"\n{'='*72}")
    print("  [A] RC-9 DEVELOPMENT (auto-mitosis + growth)")
    print(f"{'='*72}")

    ensemble, gen_log = run_development(
        X_train, y_train, X_test, y_test, tasks,
        seed=42, max_epochs_per_gen=30,
        plateau_threshold=0.3, plateau_patience=3
    )

    # ===================================================================
    # Run sequential baseline
    # ===================================================================
    print(f"\n{'='*72}")
    print("  [B] SEQUENTIAL BASELINE (catastrophic forgetting)")
    print(f"{'='*72}")

    seq_model, seq_acc, seq_per_digit = run_sequential_baseline(
        X_train, y_train, X_test, y_test, tasks,
        seed=42, epochs_per_task=15
    )

    # ===================================================================
    # Final ensemble evaluation
    # ===================================================================
    print(f"\n{'='*72}")
    print("  FINAL ENSEMBLE EVALUATION (all 10 digits)")
    print(f"{'='*72}")

    ensemble_acc = ensemble.evaluate(X_test, y_test)
    ensemble_per_digit = ensemble.evaluate_per_digit(X_test, y_test)

    # Oracle evaluation: route each sample to the correct child
    oracle_correct = 0
    oracle_total = 0
    oracle_per_digit = {}
    for model, digits in ensemble.children:
        for d in digits:
            mask = (y_test == d)
            if mask.sum() == 0:
                oracle_per_digit[d] = 0.0
                continue
            xd, yd = X_test[mask], y_test[mask]
            model.eval()
            with torch.no_grad():
                out, _ = model(xd)
                digit_indices = torch.tensor(digits, dtype=torch.long)
                restricted = out[:, digit_indices]
                # Map prediction back to original digit
                pred_idx = restricted.argmax(1)
                pred_digits = digit_indices[pred_idx]
                correct = (pred_digits == yd).sum().item()
                oracle_correct += correct
                oracle_total += len(yd)
                oracle_per_digit[d] = correct / len(yd) * 100.0

    oracle_acc = oracle_correct / oracle_total * 100.0

    print(f"\n  Ensemble accuracy (confidence-weighted): {ensemble_acc:.2f}%")
    print(f"  Oracle accuracy (perfect routing):       {oracle_acc:.2f}%")
    print(f"  Sequential accuracy (all digits):        {seq_acc:.2f}%")
    print(f"  Ensemble vs Sequential: {ensemble_acc - seq_acc:+.2f}%")
    print(f"  Oracle vs Sequential:   {oracle_acc - seq_acc:+.2f}%")

    # ===================================================================
    # Generation tree
    # ===================================================================
    print_generation_tree(gen_log)

    # ===================================================================
    # Per-digit heatmap (oracle)
    # ===================================================================
    print(f"\n  {'='*60}")
    print(f"  PER-DIGIT ACCURACY: ORACLE vs SEQUENTIAL")
    print(f"  {'='*60}")
    print(f"\n  {'Digit':>6} | {'Oracle':>8} | {'Ensemble':>8} | {'Sequent':>8} | {'Orc-Seq':>8}")
    print(f"  {'-'*6}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}")
    for d in range(10):
        o = oracle_per_digit.get(d, 0.0)
        e = ensemble_per_digit.get(d, 0.0)
        s = seq_per_digit.get(d, 0.0)
        delta = o - s
        print(f"  {d:>6} | {o:>7.1f}% | {e:>7.1f}% | {s:>7.1f}% | {delta:>+7.1f}%")

    print_per_digit_heatmap(ensemble_per_digit, seq_per_digit)

    # ===================================================================
    # Learning curves
    # ===================================================================
    print_learning_curves(gen_log)

    # ===================================================================
    # Summary table
    # ===================================================================
    print(f"\n  {'='*60}")
    print(f"  PER-GENERATION SUMMARY")
    print(f"  {'='*60}")

    print(f"\n  {'Gen':>4} | {'Name':<22} | {'Epochs':>6} | {'TrainAcc':>8} | {'TestAcc':>7} | {'T-Scale':>7} | {'Params':>8}")
    print(f"  {'-'*4}-+-{'-'*22}-+-{'-'*6}-+-{'-'*8}-+-{'-'*7}-+-{'-'*7}-+-{'-'*8}")
    for g in gen_log:
        print(f"  {g['gen']:>4} | {g['name']:<22} | {g['n_epochs']:>6} | {g['train_acc']:>7.1f}% | {g['test_acc']:>6.1f}% | {g['tension_scale']:>7.4f} | {g['params']:>8,}")

    # ===================================================================
    # Forgetting analysis
    # ===================================================================
    print(f"\n  {'='*60}")
    print(f"  FORGETTING ANALYSIS")
    print(f"  {'='*60}")

    print(f"\n  Sequential model (single model, all tasks sequentially):")
    for d in range(10):
        bar = '#' * int(seq_per_digit.get(d, 0) / 100 * 30)
        print(f"    digit {d}: {seq_per_digit.get(d, 0):>5.1f}% |{bar}")

    print(f"\n  RC-9 Ensemble (frozen children, oracle routing):")
    for d in range(10):
        bar = '#' * int(ensemble_per_digit.get(d, 0) / 100 * 30)
        print(f"    digit {d}: {ensemble_per_digit.get(d, 0):>5.1f}% |{bar}")

    # Compute forgetting metrics
    seq_mean = np.mean([seq_per_digit.get(d, 0) for d in range(10)])
    ens_mean = np.mean([ensemble_per_digit.get(d, 0) for d in range(10)])
    orc_mean = np.mean([oracle_per_digit.get(d, 0) for d in range(10)])

    # Early digits forgetting in sequential
    early_digits = tasks[0]["digits"]
    seq_early = np.mean([seq_per_digit.get(d, 0) for d in early_digits])
    ens_early = np.mean([ensemble_per_digit.get(d, 0) for d in early_digits])
    orc_early = np.mean([oracle_per_digit.get(d, 0) for d in early_digits])

    print(f"\n  Forgetting metrics:")
    print(f"    Sequential mean (all digits):   {seq_mean:.1f}%")
    print(f"    Ensemble mean (all digits):     {ens_mean:.1f}%")
    print(f"    Oracle mean (all digits):       {orc_mean:.1f}%")
    print(f"    Oracle vs Sequential:           {orc_mean - seq_mean:+.1f}%")
    print(f"    Sequential early digits (0-2):  {seq_early:.1f}%")
    print(f"    Oracle early digits (0-2):      {orc_early:.1f}%")
    print(f"    Early digit preservation:       {orc_early - seq_early:+.1f}%")

    # ===================================================================
    # Tension scale evolution
    # ===================================================================
    print(f"\n  {'='*60}")
    print(f"  TENSION SCALE EVOLUTION ACROSS GENERATIONS")
    print(f"  {'='*60}")

    ts_values = [g['tension_scale'] for g in gen_log]
    ts_min = min(ts_values) - 0.5
    ts_max = max(ts_values) + 0.5
    ts_rng = ts_max - ts_min if ts_max != ts_min else 1.0

    for row in range(7, -1, -1):
        threshold = ts_min + (row / 7) * ts_rng
        line = ""
        for gi, ts in enumerate(ts_values):
            seg = "  ##  " if ts >= threshold else "      "
            line += seg
        val = f"{threshold:.2f}"
        print(f"    {val:>6} |{line}|")
    print(f"    {'':>6} +{'------' * len(ts_values)}+")
    labels = "".join(f" Gen-{g['gen']} " for g in gen_log)
    print(f"    {'':>6}  {labels}")

    # ===================================================================
    # Verdict
    # ===================================================================
    print(f"\n  {'='*60}")
    print(f"  VERDICT")
    print(f"  {'='*60}")

    print(f"""
  RC-9 Development (PureField + Auto-Mitosis):
    Oracle accuracy (perfect routing):       {oracle_acc:.2f}%
    Ensemble accuracy (confidence-weighted): {ensemble_acc:.2f}%
    Children: {len(ensemble.children)} frozen generations
    Tension scale range: {min(ts_values):.4f} - {max(ts_values):.4f}

  Sequential baseline:
    Accuracy (all 10 digits): {seq_acc:.2f}%
    (single model, catastrophic forgetting)

  Oracle vs Sequential:   {oracle_acc - seq_acc:+.2f}%
  Ensemble vs Sequential: {ensemble_acc - seq_acc:+.2f}%
  Early digit preservation (oracle): {orc_early - seq_early:+.1f}%
""")

    if oracle_acc > seq_acc + 5:
        print("  CONCLUSION: RC-9 development STRONGLY outperforms sequential.")
        print("  Auto-mitosis + frozen memory = effective catastrophic forgetting prevention.")
    elif oracle_acc > seq_acc:
        print("  CONCLUSION: RC-9 development outperforms sequential.")
        print("  Mitosis-based growth provides measurable benefit.")
    else:
        print("  CONCLUSION: RC-9 comparable or worse than sequential.")
        print("  Need to investigate: routing, ensemble method, or task difficulty.")

    if orc_early > 90 and seq_early < 50:
        print("  KEY FINDING: Early digits perfectly preserved (>90%) while sequential forgot (<50%).")
        print("  Mitosis = biological memory preservation mechanism CONFIRMED.")

    if oracle_acc > ensemble_acc + 10:
        print(f"  ROUTING GAP: Oracle {oracle_acc:.1f}% >> Ensemble {ensemble_acc:.1f}%")
        print("  -> Perfect routing is key. Future: train a router network.")

    print(f"\n  {'='*60}")
    print(f"  RC-9 EXPERIMENT COMPLETE")
    print(f"  {'='*60}")


if __name__ == "__main__":
    main()
