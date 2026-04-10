#!/usr/bin/env python3
"""Tension Precognition Experiment
Can tension predict whether the model will get a sample WRONG,
before seeing the answer?

This is the minimal version of "just knowing" -- the model has a feeling
about its own future correctness.

Protocol:
  1. Train RepulsionFieldQuad on MNIST (10 epochs)
  2. Collect per-sample: tension, prediction, correctness, confidence, entropy
  3. Build precognition classifier (logistic regression)
  4. ROC / AUC / precision-recall analysis
  5. Per-digit breakdown
  6. "Just knowing" test: catch errors without rejecting correct ones
  7. Confidence calibration: tension vs confidence scatter
"""

import os
import sys
import time
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_utils import load_mnist, train_and_evaluate, count_params
from model_meta_engine import (
    RepulsionFieldQuad, EngineA, EngineE, EngineG, EngineF,
)

# Try sklearn; fall back to manual logistic regression with torch
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, precision_recall_curve, roc_curve
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ─────────────────────────────────────────
# ASCII output utilities
# ─────────────────────────────────────────

def ascii_bar(value, max_value, width=40, fill='#'):
    if max_value <= 0:
        return ''
    n = int(round(value / max_value * width))
    n = max(0, min(n, width))
    return fill * n


def print_header(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def print_section(title):
    print()
    print(f"  {'─' * 64}")
    print(f"  {title}")
    print(f"  {'─' * 64}")


def ascii_roc_curve(fpr, tpr, auc_val, title='ROC Curve', width=60, height=25):
    """Draw an ASCII ROC curve."""
    print(f"\n  {title} (AUC = {auc_val:.4f})")
    print()

    canvas = [[' '] * (width + 1) for _ in range(height + 1)]

    # Draw axes
    for r in range(height + 1):
        canvas[r][0] = '|'
    for c in range(width + 1):
        canvas[height][c] = '-'
    canvas[height][0] = '+'

    # Plot diagonal (random baseline)
    for i in range(min(width, height) + 1):
        r = height - int(i * height / width) if width > 0 else height
        c = i
        if 0 <= r <= height and 0 <= c <= width:
            canvas[r][c] = '.'

    # Plot ROC curve
    for fp, tp in zip(fpr, tpr):
        c = int(fp * width)
        r = height - int(tp * height)
        c = max(0, min(c, width))
        r = max(0, min(r, height))
        canvas[r][c] = '*'

    # Y-axis labels
    print(f"  TPR")
    for r in range(height + 1):
        tpr_val = 1.0 - r / height
        if r % 5 == 0:
            label = f"{tpr_val:.1f}"
        else:
            label = "   "
        print(f"  {label:>4} {''.join(canvas[r])}")
    print(f"       {'0':>1}{' ' * (width // 2 - 1)}{'0.5':>3}{' ' * (width // 2 - 2)}{'1.0':>3}")
    print(f"       {'FPR':^{width}}")


def ascii_scatter(x, y, xlabel='X', ylabel='Y', title='', width=60, height=20,
                  labels=None):
    """Draw an ASCII scatter plot. labels: array of 0/1 for two groups."""
    print(f"\n  {title}")
    print()

    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    x_range = x_max - x_min if x_max > x_min else 1.0
    y_range = y_max - y_min if y_max > y_min else 1.0

    canvas = [[' '] * (width + 1) for _ in range(height + 1)]

    # Draw axes
    for r in range(height + 1):
        canvas[r][0] = '|'
    for c in range(width + 1):
        canvas[height][c] = '-'
    canvas[height][0] = '+'

    # Subsample to avoid overdrawing
    n = len(x)
    idx = np.random.choice(n, size=min(n, 2000), replace=False)

    for i in idx:
        c = int((x[i] - x_min) / x_range * width)
        r = height - int((y[i] - y_min) / y_range * height)
        c = max(0, min(c, width))
        r = max(0, min(r, height))
        if labels is not None:
            canvas[r][c] = 'x' if labels[i] else 'o'
        else:
            canvas[r][c] = '*'

    print(f"  {ylabel}")
    for r in range(height + 1):
        yval = y_max - r / height * y_range
        if r % 5 == 0:
            label = f"{yval:.2f}"
        else:
            label = "     "
        print(f"  {label:>6} {''.join(canvas[r])}")
    print(f"         {x_min:<.2f}{' ' * (width - 12)}{x_max:>.2f}")
    print(f"         {xlabel:^{width}}")
    if labels is not None:
        print(f"         Legend: o = correct, x = misclassified")


# ─────────────────────────────────────────
# Data collection
# ─────────────────────────────────────────

def collect_all_features(model, test_loader):
    """Collect per-sample features from RepulsionFieldQuad.

    Returns dict with:
        labels, preds, correct,
        t_content, t_structure, t_total,
        confidence, entropy, logits
    """
    model.eval()
    all_labels = []
    all_preds = []
    all_t_content = []
    all_t_structure = []
    all_confidence = []
    all_entropy = []
    all_logits = []

    with torch.no_grad():
        for X, y in test_loader:
            X_flat = X.view(X.size(0), -1)

            # Engine outputs (per-sample tension)
            out_a = model.engine_a(X_flat)
            out_e = model.engine_e(X_flat)
            out_g = model.engine_g(X_flat)
            out_f = model.engine_f(X_flat)

            rep_content = out_a - out_g
            rep_structure = out_e - out_f

            t_content = (rep_content ** 2).sum(dim=-1)
            t_structure = (rep_structure ** 2).sum(dim=-1)

            # Model prediction
            output, _ = model(X_flat)
            probs = F.softmax(output, dim=-1)
            confidence = probs.max(dim=-1).values
            entropy = -(probs * (probs + 1e-8).log()).sum(dim=-1)
            preds = output.argmax(dim=1)

            all_labels.append(y.numpy())
            all_preds.append(preds.cpu().numpy())
            all_t_content.append(t_content.cpu().numpy())
            all_t_structure.append(t_structure.cpu().numpy())
            all_confidence.append(confidence.cpu().numpy())
            all_entropy.append(entropy.cpu().numpy())
            all_logits.append(output.cpu().numpy())

    labels = np.concatenate(all_labels)
    preds = np.concatenate(all_preds)
    t_content = np.concatenate(all_t_content)
    t_structure = np.concatenate(all_t_structure)
    t_total = np.sqrt(t_content * t_structure + 1e-8)
    correct = (labels == preds)
    confidence = np.concatenate(all_confidence)
    entropy = np.concatenate(all_entropy)
    logits = np.concatenate(all_logits)

    return {
        'labels': labels,
        'preds': preds,
        'correct': correct,
        't_content': t_content,
        't_structure': t_structure,
        't_total': t_total,
        'confidence': confidence,
        'entropy': entropy,
        'logits': logits,
    }


# ─────────────────────────────────────────
# Logistic regression (torch fallback)
# ─────────────────────────────────────────

class TorchLogisticRegression:
    """Simple logistic regression using torch, for when sklearn is unavailable."""

    def __init__(self, n_features, lr=0.01, epochs=200):
        self.w = torch.zeros(n_features, requires_grad=True)
        self.b = torch.zeros(1, requires_grad=True)
        self.lr = lr
        self.epochs = epochs

    def fit(self, X, y):
        X_t = torch.tensor(X, dtype=torch.float32)
        y_t = torch.tensor(y, dtype=torch.float32)
        optimizer = torch.optim.LBFGS([self.w, self.b], lr=self.lr, max_iter=20)

        for _ in range(self.epochs):
            def closure():
                optimizer.zero_grad()
                logits = X_t @ self.w + self.b
                loss = F.binary_cross_entropy_with_logits(logits, y_t)
                loss.backward()
                return loss
            optimizer.step(closure)

    def predict_proba(self, X):
        X_t = torch.tensor(X, dtype=torch.float32)
        with torch.no_grad():
            logits = X_t @ self.w + self.b
            p = torch.sigmoid(logits).numpy()
        return np.stack([1 - p, p], axis=1)

    def predict(self, X):
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)


# ─────────────────────────────────────────
# Metric helpers (no sklearn dependency)
# ─────────────────────────────────────────

def compute_roc(y_true, y_score, n_thresholds=200):
    """Compute ROC curve manually."""
    if HAS_SKLEARN:
        fpr, tpr, thresholds = roc_curve(y_true, y_score)
        auc = roc_auc_score(y_true, y_score)
        return fpr, tpr, thresholds, auc

    thresholds = np.linspace(0, 1, n_thresholds)
    fpr_list, tpr_list = [], []
    pos = y_true.sum()
    neg = len(y_true) - pos
    for t in thresholds:
        pred = (y_score >= t).astype(int)
        tp = ((pred == 1) & (y_true == 1)).sum()
        fp = ((pred == 1) & (y_true == 0)).sum()
        tpr_list.append(tp / max(pos, 1))
        fpr_list.append(fp / max(neg, 1))
    fpr_arr = np.array(fpr_list)
    tpr_arr = np.array(tpr_list)
    # Sort by FPR
    order = np.argsort(fpr_arr)
    fpr_arr = fpr_arr[order]
    tpr_arr = tpr_arr[order]
    # AUC via trapezoidal rule
    auc = np.trapz(tpr_arr, fpr_arr)
    return fpr_arr, tpr_arr, thresholds[order], auc


def compute_precision_recall(y_true, y_score, n_thresholds=200):
    """Compute precision-recall curve manually."""
    if HAS_SKLEARN:
        precision, recall, thresholds = precision_recall_curve(y_true, y_score)
        return precision, recall, thresholds

    thresholds = np.linspace(0.01, 0.99, n_thresholds)
    prec_list, rec_list = [], []
    for t in thresholds:
        pred = (y_score >= t).astype(int)
        tp = ((pred == 1) & (y_true == 1)).sum()
        fp = ((pred == 1) & (y_true == 0)).sum()
        fn = ((pred == 0) & (y_true == 1)).sum()
        prec_list.append(tp / max(tp + fp, 1))
        rec_list.append(tp / max(tp + fn, 1))
    return np.array(prec_list), np.array(rec_list), thresholds


# ─────────────────────────────────────────
# Precognition classifier training
# ─────────────────────────────────────────

def build_feature_matrix(data, feature_set='all'):
    """Build feature matrix from collected data.

    feature_set: 'tension_only', 'confidence_only', 'all'
    """
    if feature_set == 'tension_only':
        X = np.stack([data['t_content'], data['t_structure']], axis=1)
    elif feature_set == 'confidence_only':
        X = np.stack([data['confidence'], data['entropy']], axis=1)
    elif feature_set == 'all':
        X = np.stack([
            data['t_content'],
            data['t_structure'],
            data['confidence'],
            data['entropy'],
        ], axis=1)
    else:
        raise ValueError(f"Unknown feature_set: {feature_set}")

    # Normalize features to zero mean, unit variance
    mean = X.mean(axis=0, keepdims=True)
    std = X.std(axis=0, keepdims=True) + 1e-8
    X = (X - mean) / std
    return X, mean, std


def train_precognition_classifier(X_train, y_train):
    """Train logistic regression to predict misclassification."""
    if HAS_SKLEARN:
        clf = LogisticRegression(max_iter=1000, solver='lbfgs', class_weight='balanced')
        clf.fit(X_train, y_train)
        return clf
    else:
        n_features = X_train.shape[1]
        clf = TorchLogisticRegression(n_features, lr=1.0, epochs=50)
        clf.fit(X_train, y_train.astype(np.float32))
        return clf


# ─────────────────────────────────────────
# Analysis functions
# ─────────────────────────────────────────

def analysis_precognition_classifiers(data, split=5000):
    """Train and compare precognition classifiers with different feature sets."""
    print_section("Precognition Classifier: Can tension predict errors?")

    N = len(data['labels'])
    y = (~data['correct']).astype(int)  # target: 1 = misclassified

    n_errors = y.sum()
    n_correct = N - n_errors
    print(f"\n  Dataset: {N} samples, {n_errors} errors ({n_errors/N*100:.1f}%), "
          f"{n_correct} correct ({n_correct/N*100:.1f}%)")

    # Shuffle and split
    rng = np.random.RandomState(42)
    idx = rng.permutation(N)
    train_idx = idx[:split]
    test_idx = idx[split:]

    results = {}

    for name, fset in [('tension_only', 'tension_only'),
                        ('confidence_only', 'confidence_only'),
                        ('tension+confidence', 'all')]:
        X, mean, std = build_feature_matrix(data, fset)
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        clf = train_precognition_classifier(X_train, y_train)
        proba_test = clf.predict_proba(X_test)[:, 1]
        pred_test = (proba_test >= 0.5).astype(int)

        fpr, tpr, thresholds, auc = compute_roc(y_test, proba_test)

        # Accuracy
        acc = (pred_test == y_test).mean()
        # Among predicted errors, how many are actual errors
        tp = ((pred_test == 1) & (y_test == 1)).sum()
        fp = ((pred_test == 1) & (y_test == 0)).sum()
        fn = ((pred_test == 0) & (y_test == 1)).sum()
        tn = ((pred_test == 0) & (y_test == 0)).sum()
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)

        results[name] = {
            'auc': auc, 'acc': acc,
            'precision': precision, 'recall': recall, 'f1': f1,
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'fpr': fpr, 'tpr': tpr, 'thresholds': thresholds,
            'proba': proba_test, 'y_test': y_test,
            'X_test': X_test,
        }

    # Print comparison table
    print(f"\n  {'Model':<25} | {'AUC':>6} | {'Acc':>6} | {'Prec':>6} | {'Recall':>6} | {'F1':>6}")
    print(f"  {'─' * 25}─┼─{'─' * 6}─┼─{'─' * 6}─┼─{'─' * 6}─┼─{'─' * 6}─┼─{'─' * 6}")
    best_auc_name = max(results, key=lambda k: results[k]['auc'])
    for name, r in results.items():
        marker = ' <--' if name == best_auc_name else ''
        print(f"  {name:<25} | {r['auc']:>6.4f} | {r['acc']*100:>5.1f}% | "
              f"{r['precision']*100:>5.1f}% | {r['recall']*100:>5.1f}% | "
              f"{r['f1']:>6.4f}{marker}")

    # Confusion matrices
    for name, r in results.items():
        print(f"\n  Confusion matrix ({name}):")
        print(f"                  Predicted")
        print(f"                  Correct  Error")
        print(f"    Actual Correct  {r['tn']:>5}  {r['fp']:>5}")
        print(f"    Actual Error    {r['fn']:>5}  {r['tp']:>5}")

    return results


def analysis_roc_curves(results):
    """Draw ASCII ROC curves for each model."""
    print_section("ROC Curves")

    for name, r in results.items():
        ascii_roc_curve(r['fpr'], r['tpr'], r['auc'],
                       title=f'ROC: {name}', width=50, height=20)


def analysis_precision_recall(results):
    """Precision-recall analysis at various thresholds."""
    print_section("Precision-Recall at Various Thresholds")

    best_name = max(results, key=lambda k: results[k]['auc'])
    r = results[best_name]
    proba = r['proba']
    y_test = r['y_test']

    print(f"\n  Using best model: {best_name} (AUC={r['auc']:.4f})")
    print()
    print(f"  {'Threshold':>10} | {'Precision':>9} | {'Recall':>7} | "
          f"{'FlaggedN':>8} | {'TruePos':>7} | {'FalsePos':>8}")
    print(f"  {'─' * 10}─┼─{'─' * 9}─┼─{'─' * 7}─┼─"
          f"{'─' * 8}─┼─{'─' * 7}─┼─{'─' * 8}")

    for threshold in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        flagged = (proba >= threshold)
        n_flagged = flagged.sum()
        if n_flagged == 0:
            print(f"  {threshold:>10.1f} | {'N/A':>9} | {'N/A':>7} | "
                  f"{n_flagged:>8} | {'N/A':>7} | {'N/A':>8}")
            continue
        tp = ((flagged) & (y_test == 1)).sum()
        fp = ((flagged) & (y_test == 0)).sum()
        fn = ((~flagged) & (y_test == 1)).sum()
        prec = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        print(f"  {threshold:>10.1f} | {prec*100:>8.1f}% | {rec*100:>6.1f}% | "
              f"{n_flagged:>8} | {tp:>7} | {fp:>8}")


def analysis_selective_prediction(data, results):
    """If we reject samples where tension predicts error, what accuracy on remaining?"""
    print_section("Selective Prediction: 'I know that I don't know'")

    best_name = max(results, key=lambda k: results[k]['auc'])
    r = results[best_name]
    proba = r['proba']
    y_test = r['y_test']
    correct_test = (y_test == 0)  # y_test=1 means error, so correct = y_test==0

    # Get original predictions for test set
    N = len(data['labels'])
    rng = np.random.RandomState(42)
    idx = rng.permutation(N)
    test_idx = idx[5000:]
    orig_correct = data['correct'][test_idx]
    orig_acc = orig_correct.mean()

    print(f"\n  Base accuracy (all test samples): {orig_acc*100:.2f}%")
    print(f"  Using model: {best_name}")
    print()
    print(f"  {'Reject%':>8} | {'Threshold':>9} | {'Remaining':>9} | "
          f"{'Acc(rem)':>8} | {'Errors caught':>13} | {'Correct lost':>12}")
    print(f"  {'─' * 8}─┼─{'─' * 9}─┼─{'─' * 9}─┼─"
          f"{'─' * 8}─┼─{'─' * 13}─┼─{'─' * 12}")

    # Sort by predicted error probability and reject top-k%
    sorted_idx = np.argsort(proba)[::-1]

    for reject_pct in [1, 2, 5, 10, 15, 20, 30, 40, 50]:
        n_reject = int(len(proba) * reject_pct / 100)
        reject_set = set(sorted_idx[:n_reject])
        keep_mask = np.array([i not in reject_set for i in range(len(proba))])

        remaining = keep_mask.sum()
        acc_remaining = orig_correct[keep_mask].mean() if remaining > 0 else 0

        # How many actual errors did we catch?
        errors_in_reject = (~orig_correct[~keep_mask]).sum() if (~keep_mask).sum() > 0 else 0
        correct_in_reject = orig_correct[~keep_mask].sum() if (~keep_mask).sum() > 0 else 0
        total_errors = (~orig_correct).sum()

        catch_rate = errors_in_reject / max(total_errors, 1) * 100

        print(f"  {reject_pct:>7}% | {proba[sorted_idx[n_reject-1]] if n_reject > 0 else 0:>9.4f} | "
              f"{remaining:>9} | {acc_remaining*100:>7.2f}% | "
              f"{errors_in_reject:>5}/{total_errors:<5} ({catch_rate:>4.0f}%) | "
              f"{correct_in_reject:>5}")


def analysis_per_digit(data, results):
    """Per-digit analysis: for which digits is tension most predictive?"""
    print_section("Per-Digit Precognition Analysis")

    best_name = max(results, key=lambda k: results[k]['auc'])

    N = len(data['labels'])
    rng = np.random.RandomState(42)
    idx = rng.permutation(N)
    test_idx = idx[5000:]

    labels_test = data['labels'][test_idx]
    correct_test = data['correct'][test_idx]
    t_total_test = data['t_total'][test_idx]
    preds_test = data['preds'][test_idx]

    proba = results[best_name]['proba']
    y_test = results[best_name]['y_test']

    print(f"\n  Using model: {best_name}")
    print()
    print(f"  {'Digit':>5} | {'N':>5} | {'Errors':>6} | {'ErrRate':>7} | "
          f"{'MeanTens':>8} | {'Tens(ok)':>8} | {'Tens(err)':>8} | {'AUC':>6}")
    print(f"  {'─' * 5}─┼─{'─' * 5}─┼─{'─' * 6}─┼─{'─' * 7}─┼─"
          f"{'─' * 8}─┼─{'─' * 8}─┼─{'─' * 8}─┼─{'─' * 6}")

    digit_aucs = {}
    for d in range(10):
        mask = labels_test == d
        if mask.sum() < 10:
            continue
        nd = mask.sum()
        errs = (~correct_test[mask]).sum()
        err_rate = errs / nd
        mean_t = t_total_test[mask].mean()
        t_ok = t_total_test[mask & correct_test].mean() if (mask & correct_test).sum() > 0 else 0
        t_err = t_total_test[mask & ~correct_test].mean() if (mask & ~correct_test).sum() > 0 else 0

        # Per-digit AUC
        d_proba = proba[mask]
        d_y = y_test[mask]
        if d_y.sum() > 0 and d_y.sum() < len(d_y):
            _, _, _, d_auc = compute_roc(d_y, d_proba)
        else:
            d_auc = float('nan')
        digit_aucs[d] = d_auc

        print(f"  {d:>5} | {nd:>5} | {errs:>6} | {err_rate*100:>6.1f}% | "
              f"{mean_t:>8.2f} | {t_ok:>8.2f} | {t_err:>8.2f} | {d_auc:>6.3f}")

    # Confusion pattern: when tension says "this will be wrong", what's the typical confusion?
    print(f"\n  Confusion pattern (samples flagged as likely errors):")
    flagged = proba >= 0.5
    flagged_errors = flagged & (y_test == 1)

    if flagged_errors.sum() > 0:
        flagged_labels = labels_test[flagged_errors]
        flagged_preds = preds_test[flagged_errors]

        confusion = np.zeros((10, 10), dtype=int)
        for l, p in zip(flagged_labels, flagged_preds):
            confusion[l, p] += 1

        # Top confused pairs
        pairs = []
        for i in range(10):
            for j in range(10):
                if i != j and confusion[i, j] > 0:
                    pairs.append((i, j, confusion[i, j]))
        pairs.sort(key=lambda x: -x[2])

        print(f"  {'True':>5} -> {'Pred':>5} | {'Count':>5}")
        print(f"  {'─' * 5}────{'─' * 5}─┼─{'─' * 5}")
        for true_d, pred_d, cnt in pairs[:10]:
            print(f"  {true_d:>5} -> {pred_d:>5} | {cnt:>5}")
    else:
        print(f"  No flagged errors at threshold=0.5")


def analysis_just_knowing(data, results):
    """The 'just knowing' test:
    Set a tension threshold that catches 50% of errors.
    How many correct samples does it also reject?
    """
    print_section("The 'Just Knowing' Test")

    best_name = max(results, key=lambda k: results[k]['auc'])
    r = results[best_name]
    proba = r['proba']
    y_test = r['y_test']

    N = len(data['labels'])
    rng = np.random.RandomState(42)
    idx = rng.permutation(N)
    test_idx = idx[5000:]
    orig_correct = data['correct'][test_idx]

    total_errors = (~orig_correct).sum()
    total_correct = orig_correct.sum()

    print(f"\n  Model: {best_name}")
    print(f"  Total errors: {total_errors}, Total correct: {total_correct}")
    print()

    # Find thresholds that catch various fractions of errors
    targets = [0.25, 0.50, 0.75, 0.90]
    error_proba = proba[y_test == 1]
    correct_proba = proba[y_test == 0]

    print(f"  {'CatchRate':>9} | {'Threshold':>9} | {'Errors caught':>13} | "
          f"{'Correct rejected':>16} | {'FPR':>6} | {'Ideal FPR':>9}")
    print(f"  {'─' * 9}─┼─{'─' * 9}─┼─{'─' * 13}─┼─"
          f"{'─' * 16}─┼─{'─' * 6}─┼─{'─' * 9}")

    for target_catch in targets:
        if len(error_proba) == 0:
            continue
        # Find threshold to catch target_catch fraction of errors
        threshold = np.percentile(error_proba, (1 - target_catch) * 100)
        flagged = proba >= threshold
        errors_caught = (flagged & (y_test == 1)).sum()
        correct_rejected = (flagged & (y_test == 0)).sum()
        fpr = correct_rejected / max(total_correct, 1)

        # Ideal FPR = 0 (catch errors only)
        print(f"  {target_catch*100:>8.0f}% | {threshold:>9.4f} | "
              f"{errors_caught:>5}/{total_errors:<5}     | "
              f"{correct_rejected:>6}/{total_correct:<6}       | "
              f"{fpr*100:>5.1f}% | {0.0:>8.1f}%")

    # Interpretation
    print(f"\n  Interpretation:")
    if len(error_proba) > 0:
        # At 50% catch rate
        t50 = np.percentile(error_proba, 50)
        fp50 = (correct_proba >= t50).sum()
        fpr50 = fp50 / max(len(correct_proba), 1)
        ratio = (total_errors / 2) / max(fp50, 1)  # errors caught per correct rejected

        print(f"    To catch 50% of errors:")
        print(f"      We must also reject {fp50} correct samples (FPR={fpr50*100:.1f}%)")
        print(f"      Ratio: {ratio:.2f} true errors per false alarm")
        if fpr50 < 0.05:
            print(f"      --> EXCELLENT: Low false positive rate (<5%)")
            print(f"      --> The model 'just knows' when it will fail")
        elif fpr50 < 0.15:
            print(f"      --> GOOD: Moderate false positive rate (<15%)")
            print(f"      --> Tension carries meaningful precognitive signal")
        elif fpr50 < 0.30:
            print(f"      --> FAIR: Higher false positive rate (<30%)")
            print(f"      --> Some precognitive signal, but noisy")
        else:
            print(f"      --> WEAK: High false positive rate (>30%)")
            print(f"      --> Limited precognitive ability")


def analysis_confidence_calibration(data, results):
    """Scatter plot: tension vs confidence. Find overconfident errors."""
    print_section("Confidence Calibration: Tension vs Confidence")

    N = len(data['labels'])
    rng = np.random.RandomState(42)
    idx = rng.permutation(N)
    test_idx = idx[5000:]

    tension = data['t_total'][test_idx]
    confidence = data['confidence'][test_idx]
    correct = data['correct'][test_idx]

    # ASCII scatter: tension vs confidence
    ascii_scatter(tension, confidence,
                  xlabel='Total Tension', ylabel='Confidence',
                  title='Tension vs Confidence (o=correct, x=error)',
                  labels=(~correct).astype(int))

    # Overconfident errors: confidence > 0.9 but wrong
    overconfident_errors = (~correct) & (confidence > 0.9)
    n_oc = overconfident_errors.sum()
    n_errors = (~correct).sum()

    print(f"\n  Overconfident errors (confidence > 0.9 but wrong): {n_oc}/{n_errors} "
          f"({n_oc/max(n_errors,1)*100:.1f}% of all errors)")

    if n_oc > 0:
        oc_tension = tension[overconfident_errors]
        normal_error_tension = tension[(~correct) & (confidence <= 0.9)]
        correct_tension = tension[correct]

        print(f"    Mean tension of overconfident errors: {oc_tension.mean():.4f}")
        if len(normal_error_tension) > 0:
            print(f"    Mean tension of other errors:         {normal_error_tension.mean():.4f}")
        print(f"    Mean tension of correct samples:      {correct_tension.mean():.4f}")

        # Can tension detect overconfident errors?
        if len(normal_error_tension) > 0 and oc_tension.mean() > correct_tension.mean():
            ratio = oc_tension.mean() / (correct_tension.mean() + 1e-8)
            print(f"    Tension ratio (overconfident error / correct): {ratio:.2f}x")
            print(f"    --> Tension CAN flag overconfident errors" if ratio > 1.2
                  else f"    --> Tension provides limited signal for overconfident errors")

    # Uncertain but correct: confidence < 0.5 but right
    uncertain_correct = correct & (confidence < 0.5)
    n_uc = uncertain_correct.sum()
    n_correct = correct.sum()

    print(f"\n  Uncertain but correct (confidence < 0.5 but right): {n_uc}/{n_correct} "
          f"({n_uc/max(n_correct,1)*100:.1f}% of correct)")

    if n_uc > 0:
        uc_tension = tension[uncertain_correct]
        confident_correct_tension = tension[correct & (confidence >= 0.5)]
        print(f"    Mean tension of uncertain-correct: {uc_tension.mean():.4f}")
        if len(confident_correct_tension) > 0:
            print(f"    Mean tension of confident-correct: {confident_correct_tension.mean():.4f}")

    # Quadrant analysis
    print(f"\n  Quadrant Analysis (median split):")
    t_med = np.median(tension)
    c_med = np.median(confidence)
    quadrants = {
        'Low-T, High-C (easy)':   (tension < t_med) & (confidence >= c_med),
        'High-T, High-C (overconf)': (tension >= t_med) & (confidence >= c_med),
        'Low-T, Low-C (uncertain)':  (tension < t_med) & (confidence < c_med),
        'High-T, Low-C (hard)':   (tension >= t_med) & (confidence < c_med),
    }
    print(f"  {'Quadrant':<30} | {'N':>5} | {'Errors':>6} | {'ErrRate':>7} | {'MeanTens':>8} | {'MeanConf':>8}")
    print(f"  {'─' * 30}─┼─{'─' * 5}─┼─{'─' * 6}─┼─{'─' * 7}─┼─{'─' * 8}─┼─{'─' * 8}")

    for qname, qmask in quadrants.items():
        nq = qmask.sum()
        if nq == 0:
            continue
        nerr = (~correct[qmask]).sum()
        errrate = nerr / nq
        mt = tension[qmask].mean()
        mc = confidence[qmask].mean()
        print(f"  {qname:<30} | {nq:>5} | {nerr:>6} | {errrate*100:>6.1f}% | "
              f"{mt:>8.2f} | {mc:>8.4f}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    t0 = time.time()

    print()
    print("=" * 72)
    print("   logout -- Tension Precognition Experiment")
    print("   Can the model 'just know' when it will be wrong?")
    print("=" * 72)

    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 10

    # ── 1. Load data ──
    print("\n  Loading MNIST...")
    train_loader, test_loader = load_mnist(batch_size=128)

    # ── 2. Train RepulsionFieldQuad ──
    print_header("Phase 1: Training RepulsionFieldQuad (10 epochs)")

    model = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    print(f"  Parameters: {count_params(model):,}")

    losses, accs = train_and_evaluate(
        model, train_loader, test_loader,
        epochs=epochs, aux_lambda=0.01, verbose=True
    )
    print(f"\n  Final accuracy: {accs[-1] * 100:.2f}%")
    print(f"  Final tension: content={model.tension_content:.4f}, "
          f"structure={model.tension_structure:.4f}")

    # ── 3. Collect per-sample features ──
    print_header("Phase 2: Collecting per-sample features (10,000 test samples)")

    data = collect_all_features(model, test_loader)
    n_total = len(data['labels'])
    n_errors = (~data['correct']).sum()
    print(f"  Collected {n_total} samples")
    print(f"  Correct: {data['correct'].sum()} ({data['correct'].mean()*100:.1f}%)")
    print(f"  Errors:  {n_errors} ({n_errors/n_total*100:.1f}%)")
    print(f"  Mean tension: content={data['t_content'].mean():.4f}, "
          f"structure={data['t_structure'].mean():.4f}, "
          f"total={data['t_total'].mean():.4f}")
    print(f"  Mean confidence: {data['confidence'].mean():.4f}")
    print(f"  Mean entropy: {data['entropy'].mean():.4f}")

    # Quick check: tension difference between correct and wrong
    t_ok = data['t_total'][data['correct']].mean()
    t_err = data['t_total'][~data['correct']].mean() if n_errors > 0 else 0
    print(f"\n  Tension (correct):  {t_ok:.4f}")
    print(f"  Tension (error):    {t_err:.4f}")
    if n_errors > 0:
        ratio = t_err / (t_ok + 1e-8)
        print(f"  Ratio (error/correct): {ratio:.2f}x")

    # ── 4. Precognition classifiers ──
    print_header("Phase 3: Precognition Classifiers")
    results = analysis_precognition_classifiers(data)

    # ── 5. ROC curves ──
    print_header("Phase 4: ROC Curves")
    analysis_roc_curves(results)

    # ── 6. Precision-recall ──
    print_header("Phase 5: Precision-Recall Analysis")
    analysis_precision_recall(results)

    # ── 7. Selective prediction ──
    print_header("Phase 6: Selective Prediction")
    analysis_selective_prediction(data, results)

    # ── 8. Per-digit analysis ──
    print_header("Phase 7: Per-Digit Precognition")
    analysis_per_digit(data, results)

    # ── 9. The "just knowing" test ──
    print_header("Phase 8: The 'Just Knowing' Test")
    analysis_just_knowing(data, results)

    # ── 10. Confidence calibration ──
    print_header("Phase 9: Confidence Calibration")
    analysis_confidence_calibration(data, results)

    # ── Summary ──
    print_header("FINAL SUMMARY")

    best_name = max(results, key=lambda k: results[k]['auc'])
    best_auc = results[best_name]['auc']

    print(f"\n  Model accuracy: {accs[-1]*100:.2f}%")
    print(f"  Total errors in test set: {n_errors}")
    print()
    print(f"  Precognition Results:")
    for name, r in results.items():
        marker = ' <-- best' if name == best_name else ''
        print(f"    {name:<25} AUC={r['auc']:.4f} Prec={r['precision']*100:.1f}% "
              f"Rec={r['recall']*100:.1f}%{marker}")
    print()

    if best_auc > 0.80:
        print(f"  STRONG PRECOGNITION (AUC={best_auc:.4f} > 0.80)")
        print(f"  The model's tension field reliably predicts its own errors.")
        print(f"  This is 'just knowing' -- an internal signal of future correctness.")
    elif best_auc > 0.65:
        print(f"  MODERATE PRECOGNITION (AUC={best_auc:.4f} > 0.65)")
        print(f"  Tension carries meaningful signal about future errors.")
        print(f"  The model has partial self-awareness of its limitations.")
    elif best_auc > 0.55:
        print(f"  WEAK PRECOGNITION (AUC={best_auc:.4f} > 0.55)")
        print(f"  Slight signal above random chance.")
    else:
        print(f"  NO PRECOGNITION (AUC={best_auc:.4f} <= 0.55)")
        print(f"  Tension does not predict errors better than random.")

    if n_errors > 0:
        tension_only_auc = results.get('tension_only', {}).get('auc', 0)
        conf_only_auc = results.get('confidence_only', {}).get('auc', 0)
        combined_auc = results.get('tension+confidence', {}).get('auc', 0)
        if tension_only_auc > 0.55 and combined_auc > conf_only_auc + 0.01:
            print(f"\n  TENSION ADDS VALUE beyond confidence alone:")
            print(f"    Confidence-only AUC: {conf_only_auc:.4f}")
            print(f"    Tension+Confidence:  {combined_auc:.4f}")
            print(f"    Improvement:         +{(combined_auc - conf_only_auc):.4f}")
            print(f"    --> Tension carries UNIQUE information about error likelihood")
        elif tension_only_auc > 0.55:
            print(f"\n  Tension alone has AUC={tension_only_auc:.4f} (above random)")
            print(f"  But combining with confidence does not significantly improve.")
        else:
            print(f"\n  Tension alone: AUC={tension_only_auc:.4f}")

    elapsed = time.time() - t0
    print(f"\n  Total elapsed: {elapsed:.1f}s")
    print(f"  sklearn available: {HAS_SKLEARN}")
    print(f"  Done.")
    print()


if __name__ == '__main__':
    main()
