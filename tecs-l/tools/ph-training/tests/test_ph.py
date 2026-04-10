"""Tests for PH computation and monitoring."""

import numpy as np
import pytest
from ph_training import compute_h0, get_merges, PHMonitor


def _make_directions(n_classes=5, n_per_class=50, dim=10, sep=1.0):
    """Generate test direction vectors with separable classes."""
    rng = np.random.RandomState(42)
    dirs = []
    labels = []
    for c in range(n_classes):
        center = np.zeros(dim)
        center[c % dim] = sep
        d = center + rng.randn(n_per_class, dim) * 0.1
        norms = np.linalg.norm(d, axis=1, keepdims=True)
        d = d / np.clip(norms, 1e-8, None)
        dirs.append(d)
        labels.extend([c] * n_per_class)
    return np.concatenate(dirs), np.array(labels)


def test_compute_h0_basic():
    dirs, labels = _make_directions(n_classes=5)
    h0 = compute_h0(dirs, labels, n_classes=5)
    assert isinstance(h0, float)
    assert h0 > 0


def test_compute_h0_separated_vs_mixed():
    """Well-separated classes should have higher H0 than mixed classes."""
    dirs_sep, labels_sep = _make_directions(n_classes=5, sep=2.0)
    dirs_mix, labels_mix = _make_directions(n_classes=5, sep=0.01)
    h0_sep = compute_h0(dirs_sep, labels_sep, 5)
    h0_mix = compute_h0(dirs_mix, labels_mix, 5)
    assert h0_sep > h0_mix


def test_get_merges():
    n = 5
    cos_dist = np.array([
        [0.0, 0.1, 0.5, 0.8, 0.9],
        [0.1, 0.0, 0.6, 0.7, 0.85],
        [0.5, 0.6, 0.0, 0.2, 0.3],
        [0.8, 0.7, 0.2, 0.0, 0.4],
        [0.9, 0.85, 0.3, 0.4, 0.0],
    ])
    merges = get_merges(cos_dist, n)
    assert len(merges) == n - 1
    # First merge should be the closest pair (0,1) at distance 0.1
    assert merges[0] == (0.1, 0, 1)


def test_ph_monitor_ok():
    dirs_tr, labels_tr = _make_directions(5, sep=1.0)
    dirs_te, labels_te = _make_directions(5, sep=1.0)

    monitor = PHMonitor(n_classes=5, gap_threshold=0.5)
    status = monitor.check(dirs_tr, labels_tr, dirs_te, labels_te)

    assert status.status in ("OK", "WATCH", "ALERT")
    assert status.h0_gap >= 0
    assert len(status.merges) == 4  # n_classes - 1


def test_ph_monitor_alert_and_early_stop():
    """Large train/test gap should trigger alerts and early stop."""
    dirs_tr, labels_tr = _make_directions(5, sep=3.0)
    dirs_te, labels_te = _make_directions(5, sep=0.01)

    monitor = PHMonitor(n_classes=5, gap_threshold=0.01)

    for _ in range(4):
        status = monitor.check(dirs_tr, labels_tr, dirs_te, labels_te)

    assert status.alert
    assert monitor.should_stop
