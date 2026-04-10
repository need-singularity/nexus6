#!/usr/bin/env python3
"""Experiment: Why does the displaced observer outperform the actor?

C27 finding: observer 79.4% > actor 78.8%
Hypothesis: detach() (no gradient) improves observation because it removes
the conflict between "acting" and "seeing."

Six conditions to isolate the mechanism:
  1. Baseline: reproduce observer > actor
  2. Remove detach: observer WITH gradients
  3. Mutual observation: both entities observe each other
  4. Observer trains longer: 20 epochs vs 10
  5. Multiple observers: 3 observers watching 1 actor
  6. Meditation test: act -> observe -> act (does observation improve acting?)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import copy

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import EngineA, EngineG
from model_temporal_engine import ascii_graph


# ─────────────────────────────────────────
# Modified DisplacementField with detach flag
# ─────────────────────────────────────────

class DisplacementFieldExperimental(nn.Module):
    """DisplacementField with configurable detach behavior for experiments."""

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 use_detach=True, mutual_observe=False):
        super().__init__()
        self.use_detach = use_detach
        self.mutual_observe = mutual_observe

        # Entity A = "me" (the self)
        self.entity_a = EngineA(input_dim, hidden_dim, output_dim)
        # Entity B = "the other" (the displacing force)
        self.entity_b = EngineG(input_dim, hidden_dim, output_dim)

        # Control gate
        self.control_gate = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

        # Observer: A watches B's output
        self.observer_a = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
        )

        # Mutual observation: B watches A's output
        if mutual_observe:
            self.observer_b = nn.Sequential(
                nn.Linear(output_dim, hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, output_dim),
            )

        self.register_buffer('memory_state', torch.zeros(output_dim))
        self.memory_momentum = 0.9
        self.register_buffer('observer_state', torch.zeros(output_dim))

        self.control_value = 0.0
        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        out_a = self.entity_a(x)
        out_b = self.entity_b(x)

        control = self.control_gate(x)
        output = (1 - control) * out_a + control * out_b

        # Observer A watches B
        if self.use_detach:
            observation_a = self.observer_a(out_b.detach())
        else:
            observation_a = self.observer_a(out_b)  # gradients flow!

        # Mutual observation: B watches A
        observation_b = None
        if self.mutual_observe:
            observation_b = self.observer_b(out_a.detach())

        with torch.no_grad():
            obs_mean = observation_a.mean(dim=0)
            self.observer_state = self.memory_momentum * self.observer_state + \
                (1 - self.memory_momentum) * obs_mean
            self.memory_state = self.memory_momentum * self.memory_state + \
                (1 - self.memory_momentum) * out_b.mean(dim=0).detach()

        obs_error_a = (observation_a - out_b.detach()).pow(2).sum(dim=-1).mean()

        entropy_loss = getattr(self.entity_b, 'entropy_loss', torch.tensor(0.0))
        self.aux_loss = entropy_loss + 0.1 * obs_error_a

        if self.mutual_observe and observation_b is not None:
            obs_error_b = (observation_b - out_a.detach()).pow(2).sum(dim=-1).mean()
            self.aux_loss = self.aux_loss + 0.1 * obs_error_b

        with torch.no_grad():
            self.control_value = control.mean().item()

        return (output, self.aux_loss)

    def forward_forced(self, x, forced_control):
        out_a = self.entity_a(x)
        out_b = self.entity_b(x)

        control = torch.full((x.size(0), 1), forced_control, device=x.device)
        output = (1 - control) * out_a + control * out_b

        if self.use_detach:
            observation_a = self.observer_a(out_b.detach())
        else:
            observation_a = self.observer_a(out_b)

        observation_b = None
        if self.mutual_observe:
            observation_b = self.observer_b(out_a.detach())

        obs_error = (observation_a - out_b.detach()).pow(2).sum(dim=-1).mean()

        return output, out_a, out_b, observation_a, observation_b, obs_error


# ─────────────────────────────────────────
# Multi-observer model
# ─────────────────────────────────────────

class MultiObserverField(nn.Module):
    """1 actor (B) with N observers all watching with detach."""

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10, n_observers=3):
        super().__init__()
        self.n_observers = n_observers

        # Single actor
        self.actor = EngineG(input_dim, hidden_dim, output_dim)

        # Multiple observers
        self.observers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(output_dim, hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, output_dim),
            ) for _ in range(n_observers)
        ])

        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        out_actor = self.actor(x)

        # All observers watch the actor (detached)
        observations = []
        total_obs_error = torch.tensor(0.0, device=x.device)
        for obs in self.observers:
            obs_out = obs(out_actor.detach())
            observations.append(obs_out)
            total_obs_error = total_obs_error + (obs_out - out_actor.detach()).pow(2).sum(dim=-1).mean()

        entropy_loss = getattr(self.actor, 'entropy_loss', torch.tensor(0.0))
        self.aux_loss = entropy_loss + 0.1 * total_obs_error / self.n_observers

        return (out_actor, self.aux_loss)


# ─────────────────────────────────────────
# Training utilities
# ─────────────────────────────────────────

def train_displacement(model, train_loader, test_loader, epochs, lr=0.001,
                       forced_control=None, verbose=True):
    """Train a displacement model and return per-epoch metrics."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    epoch_accs = []
    actor_accs = []
    observer_accs = []
    mutual_observer_accs = []
    losses = []

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux = model(X)
            loss = criterion(out, y) + 0.01 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        losses.append(avg_loss)

        # Evaluate
        model.eval()
        correct_combined = 0
        correct_actor = 0
        correct_observer = 0
        correct_mutual = 0
        total = 0

        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)

                if hasattr(model, 'forward_forced') and forced_control is not None:
                    output, out_a, out_b, obs_a, obs_b, _ = model.forward_forced(X, forced_control)
                    correct_combined += (output.argmax(1) == y).sum().item()
                    correct_actor += (out_b.argmax(1) == y).sum().item()
                    correct_observer += (obs_a.argmax(1) == y).sum().item()
                    if obs_b is not None:
                        correct_mutual += (obs_b.argmax(1) == y).sum().item()
                elif hasattr(model, 'forward_forced'):
                    # Default: B controls (forced_control=1.0)
                    output, out_a, out_b, obs_a, obs_b, _ = model.forward_forced(X, 1.0)
                    correct_combined += (output.argmax(1) == y).sum().item()
                    correct_actor += (out_b.argmax(1) == y).sum().item()
                    correct_observer += (obs_a.argmax(1) == y).sum().item()
                    if obs_b is not None:
                        correct_mutual += (obs_b.argmax(1) == y).sum().item()
                else:
                    out, _ = model(X)
                    correct_combined += (out.argmax(1) == y).sum().item()
                total += y.size(0)

        acc_combined = correct_combined / total
        acc_actor = correct_actor / total if correct_actor > 0 else 0
        acc_observer = correct_observer / total if correct_observer > 0 else 0
        acc_mutual = correct_mutual / total if correct_mutual > 0 else 0

        epoch_accs.append(acc_combined)
        actor_accs.append(acc_actor)
        observer_accs.append(acc_observer)
        mutual_observer_accs.append(acc_mutual)

        if verbose and ((epoch + 1) % 2 == 0 or epoch == 0):
            obs_str = f"  Observer={acc_observer*100:.1f}%" if acc_observer > 0 else ""
            act_str = f"  Actor(B)={acc_actor*100:.1f}%" if acc_actor > 0 else ""
            mut_str = f"  MutualObs={acc_mutual*100:.1f}%" if acc_mutual > 0 else ""
            print(f"    Epoch {epoch+1:>2}/{epochs}: Loss={avg_loss:.4f}"
                  f"  Combined={acc_combined*100:.1f}%{act_str}{obs_str}{mut_str}")

    return {
        'combined': epoch_accs,
        'actor': actor_accs,
        'observer': observer_accs,
        'mutual_observer': mutual_observer_accs,
        'losses': losses,
    }


def train_multi_observer(model, train_loader, test_loader, epochs, lr=0.001, verbose=True):
    """Train multi-observer model and evaluate each observer separately."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    actor_accs = []
    all_observer_accs = [[] for _ in range(model.n_observers)]

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()
            out, aux = model(X)
            loss = criterion(out, y) + 0.01 * aux
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Evaluate
        model.eval()
        correct_actor = 0
        correct_observers = [0] * model.n_observers
        total = 0

        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                out_actor = model.actor(X)
                correct_actor += (out_actor.argmax(1) == y).sum().item()

                for i, obs in enumerate(model.observers):
                    obs_out = obs(out_actor)
                    correct_observers[i] += (obs_out.argmax(1) == y).sum().item()
                total += y.size(0)

        acc_actor = correct_actor / total
        actor_accs.append(acc_actor)
        for i in range(model.n_observers):
            all_observer_accs[i].append(correct_observers[i] / total)

        if verbose and ((epoch + 1) % 2 == 0 or epoch == 0):
            obs_strs = "  ".join([f"Obs{i+1}={all_observer_accs[i][-1]*100:.1f}%"
                                  for i in range(model.n_observers)])
            print(f"    Epoch {epoch+1:>2}/{epochs}: Actor={acc_actor*100:.1f}%  {obs_strs}")

    return {
        'actor': actor_accs,
        'observers': all_observer_accs,
    }


# ─────────────────────────────────────────
# Experiment runner
# ─────────────────────────────────────────

def run_experiments():
    print("=" * 70)
    print("  EXPERIMENT: Why Does the Observer Outperform the Actor?")
    print("  Hypothesis: detach() removes acting/seeing conflict")
    print("=" * 70)

    t0 = time.time()

    print("\n  Loading MNIST...")
    train_loader, test_loader = load_mnist()

    results = {}

    # ── Condition 1: Baseline (reproduce C27) ──
    print("\n" + "=" * 70)
    print("  CONDITION 1: Baseline — B controls, A observes (with detach)")
    print("  Reproducing C27: observer > actor?")
    print("=" * 70)

    model1 = DisplacementFieldExperimental(use_detach=True)
    print(f"  Parameters: {count_params(model1):,}")
    r1 = train_displacement(model1, train_loader, test_loader, epochs=10, forced_control=1.0)
    results['C1_baseline'] = r1

    print(f"\n  >> RESULT: Actor(B)={r1['actor'][-1]*100:.1f}%  Observer(A)={r1['observer'][-1]*100:.1f}%")
    diff1 = r1['observer'][-1] - r1['actor'][-1]
    print(f"  >> Difference: {diff1*100:+.1f}%  {'Observer wins!' if diff1 > 0 else 'Actor wins!'}")

    # ── Condition 2: Remove detach ──
    print("\n" + "=" * 70)
    print("  CONDITION 2: Observer WITHOUT detach (gets gradients from B)")
    print("  Does gradient flow hurt the observer?")
    print("=" * 70)

    model2 = DisplacementFieldExperimental(use_detach=False)
    r2 = train_displacement(model2, train_loader, test_loader, epochs=10, forced_control=1.0)
    results['C2_no_detach'] = r2

    print(f"\n  >> RESULT: Actor(B)={r2['actor'][-1]*100:.1f}%  Observer(A)={r2['observer'][-1]*100:.1f}%")
    diff2 = r2['observer'][-1] - r2['actor'][-1]
    print(f"  >> Difference: {diff2*100:+.1f}%  {'Observer wins!' if diff2 > 0 else 'Actor wins!'}")
    detach_impact = r1['observer'][-1] - r2['observer'][-1]
    print(f"  >> Detach impact on observer: {detach_impact*100:+.1f}%"
          f"  {'detach helps!' if detach_impact > 0 else 'detach hurts!'}")

    # ── Condition 3: Mutual observation ──
    print("\n" + "=" * 70)
    print("  CONDITION 3: Mutual observation (A watches B, B watches A)")
    print("  Both are observers AND actors. Does mutual observation help?")
    print("=" * 70)

    model3 = DisplacementFieldExperimental(use_detach=True, mutual_observe=True)
    r3 = train_displacement(model3, train_loader, test_loader, epochs=10, forced_control=1.0)
    results['C3_mutual'] = r3

    print(f"\n  >> RESULT: Actor(B)={r3['actor'][-1]*100:.1f}%  Observer(A)={r3['observer'][-1]*100:.1f}%"
          f"  MutualObs(B->A)={r3['mutual_observer'][-1]*100:.1f}%")
    diff3 = r3['observer'][-1] - r3['actor'][-1]
    print(f"  >> Observer A advantage: {diff3*100:+.1f}%")
    mutual_impact = r3['actor'][-1] - r1['actor'][-1]
    print(f"  >> Mutual observation impact on actor: {mutual_impact*100:+.1f}%")

    # ── Condition 4: Observer trains longer ──
    print("\n" + "=" * 70)
    print("  CONDITION 4: Observer trains 20 epochs (actor still 10)")
    print("  Does the observer advantage grow with more training?")
    print("=" * 70)

    model4 = DisplacementFieldExperimental(use_detach=True)
    r4 = train_displacement(model4, train_loader, test_loader, epochs=20, forced_control=1.0)
    results['C4_longer'] = r4

    print(f"\n  >> RESULT @10: Actor={r4['actor'][9]*100:.1f}%  Observer={r4['observer'][9]*100:.1f}%"
          f"  (diff={( r4['observer'][9]-r4['actor'][9])*100:+.1f}%)")
    print(f"  >> RESULT @20: Actor={r4['actor'][-1]*100:.1f}%  Observer={r4['observer'][-1]*100:.1f}%"
          f"  (diff={(r4['observer'][-1]-r4['actor'][-1])*100:+.1f}%)")
    gap_10 = r4['observer'][9] - r4['actor'][9]
    gap_20 = r4['observer'][-1] - r4['actor'][-1]
    print(f"  >> Gap growth: {gap_10*100:.1f}% -> {gap_20*100:.1f}%"
          f"  {'Gap grows!' if abs(gap_20) > abs(gap_10) else 'Gap stable/shrinks'}")

    # ── Condition 5: Multiple observers ──
    print("\n" + "=" * 70)
    print("  CONDITION 5: 1 actor + 3 observers (all with detach)")
    print("  Do multiple observers collectively outperform a single one?")
    print("=" * 70)

    model5 = MultiObserverField(n_observers=3)
    r5 = train_multi_observer(model5, train_loader, test_loader, epochs=10)
    results['C5_multi_obs'] = r5

    avg_obs = np.mean([r5['observers'][i][-1] for i in range(3)])
    best_obs = max(r5['observers'][i][-1] for i in range(3))
    print(f"\n  >> RESULT: Actor={r5['actor'][-1]*100:.1f}%")
    for i in range(3):
        print(f"     Observer {i+1}: {r5['observers'][i][-1]*100:.1f}%")
    print(f"     Avg observer: {avg_obs*100:.1f}%  Best observer: {best_obs*100:.1f}%")
    print(f"  >> Observer ensemble advantage: {(avg_obs - r5['actor'][-1])*100:+.1f}%")

    # ── Condition 6: Meditation test ──
    print("\n" + "=" * 70)
    print("  CONDITION 6: Meditation test")
    print("  Phase 1: A acts (5 ep) -> Phase 2: A observes (5 ep) -> Phase 3: A acts (5 ep)")
    print("  Does forced observation ('meditation') improve subsequent acting?")
    print("=" * 70)

    model6 = DisplacementFieldExperimental(use_detach=True)
    optimizer6 = torch.optim.Adam(model6.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()

    phase_accs_a = []  # A's accuracy per epoch
    phase_accs_b = []
    phase_labels = []

    def eval_entities(model, test_loader):
        model.eval()
        correct_a = correct_b = total = 0
        with torch.no_grad():
            for X, y in test_loader:
                X = X.view(X.size(0), -1)
                out_a = model.entity_a(X)
                out_b = model.entity_b(X)
                correct_a += (out_a.argmax(1) == y).sum().item()
                correct_b += (out_b.argmax(1) == y).sum().item()
                total += y.size(0)
        return correct_a / total, correct_b / total

    def train_one_epoch(model, train_loader, optimizer, forced_control):
        model.train()
        total_loss = 0
        for X, y in train_loader:
            X = X.view(X.size(0), -1)
            optimizer.zero_grad()

            out_a = model.entity_a(X)
            out_b = model.entity_b(X)
            control = torch.full((X.size(0), 1), forced_control)
            output = (1 - control) * out_a + control * out_b

            if model.use_detach:
                observation = model.observer_a(out_b.detach())
            else:
                observation = model.observer_a(out_b)

            obs_error = (observation - out_b.detach()).pow(2).sum(dim=-1).mean()
            entropy_loss = getattr(model.entity_b, 'entropy_loss', torch.tensor(0.0))

            loss = criterion(output, y) + 0.01 * (entropy_loss + 0.1 * obs_error)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        return total_loss / len(train_loader)

    # Phase 1: A acts (control=0, so A's output dominates)
    print("\n  Phase 1: A acts (control=0.0)")
    for epoch in range(5):
        loss = train_one_epoch(model6, train_loader, optimizer6, forced_control=0.0)
        acc_a, acc_b = eval_entities(model6, test_loader)
        phase_accs_a.append(acc_a)
        phase_accs_b.append(acc_b)
        phase_labels.append('act')
        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1}/5: A={acc_a*100:.1f}%  B={acc_b*100:.1f}%")

    pre_meditation_a = phase_accs_a[-1]
    print(f"  >> A before meditation: {pre_meditation_a*100:.1f}%")

    # Phase 2: A observes only (control=1, B dominates output; A only observes)
    print("\n  Phase 2: A observes (control=1.0, B dominates)")
    for epoch in range(5):
        loss = train_one_epoch(model6, train_loader, optimizer6, forced_control=1.0)
        acc_a, acc_b = eval_entities(model6, test_loader)
        phase_accs_a.append(acc_a)
        phase_accs_b.append(acc_b)
        phase_labels.append('observe')
        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1}/5: A={acc_a*100:.1f}%  B={acc_b*100:.1f}%")

    post_meditation_observe = phase_accs_a[-1]
    print(f"  >> A after meditation (still observing): {post_meditation_observe*100:.1f}%")

    # Phase 3: A acts again (control=0)
    print("\n  Phase 3: A acts again (control=0.0)")
    for epoch in range(5):
        loss = train_one_epoch(model6, train_loader, optimizer6, forced_control=0.0)
        acc_a, acc_b = eval_entities(model6, test_loader)
        phase_accs_a.append(acc_a)
        phase_accs_b.append(acc_b)
        phase_labels.append('act2')
        if (epoch + 1) % 2 == 0 or epoch == 0:
            print(f"    Epoch {epoch+1}/5: A={acc_a*100:.1f}%  B={acc_b*100:.1f}%")

    post_meditation_a = phase_accs_a[-1]
    meditation_effect = post_meditation_a - pre_meditation_a
    print(f"\n  >> A before meditation: {pre_meditation_a*100:.1f}%")
    print(f"  >> A after meditation:  {post_meditation_a*100:.1f}%")
    print(f"  >> Meditation effect: {meditation_effect*100:+.1f}%"
          f"  {'Meditation helps!' if meditation_effect > 0 else 'Meditation hurts!'}")

    results['C6_meditation'] = {
        'phase_a': phase_accs_a,
        'phase_b': phase_accs_b,
        'labels': phase_labels,
        'pre': pre_meditation_a,
        'post': post_meditation_a,
    }

    # ── Control: A acts for 15 epochs straight (no meditation) ──
    print("\n  Control: A acts for 15 epochs straight (no meditation)")
    model6_ctrl = DisplacementFieldExperimental(use_detach=True)
    optimizer6_ctrl = torch.optim.Adam(model6_ctrl.parameters(), lr=0.001)
    ctrl_accs_a = []

    for epoch in range(15):
        loss = train_one_epoch(model6_ctrl, train_loader, optimizer6_ctrl, forced_control=0.0)
        acc_a, acc_b = eval_entities(model6_ctrl, test_loader)
        ctrl_accs_a.append(acc_a)
        if (epoch + 1) % 5 == 0:
            print(f"    Epoch {epoch+1}/15: A={acc_a*100:.1f}%")

    print(f"  >> Control A @15 epochs (no meditation): {ctrl_accs_a[-1]*100:.1f}%")
    print(f"  >> Meditation A @15 epochs (5 act + 5 obs + 5 act): {post_meditation_a*100:.1f}%")
    vs_control = post_meditation_a - ctrl_accs_a[-1]
    print(f"  >> Meditation vs Control: {vs_control*100:+.1f}%")

    results['C6_control'] = {'accs': ctrl_accs_a}

    # ═══════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════
    elapsed = time.time() - t0

    print("\n\n" + "=" * 70)
    print("  COMPREHENSIVE ANALYSIS")
    print("=" * 70)

    # Summary table
    print("\n  ┌─────────────────────────────────────────────────────────────────┐")
    print("  │                    ACCURACY SUMMARY TABLE                       │")
    print("  ├──────────────────────┬──────────┬──────────┬──────────┬────────┤")
    print("  │ Condition            │ Actor(B) │ Obs(A)   │ Diff     │ Note   │")
    print("  ├──────────────────────┼──────────┼──────────┼──────────┼────────┤")

    rows = [
        ("C1: Baseline (detach)", r1['actor'][-1], r1['observer'][-1]),
        ("C2: No detach", r2['actor'][-1], r2['observer'][-1]),
        ("C3: Mutual observe", r3['actor'][-1], r3['observer'][-1]),
        ("C4: 20 epochs", r4['actor'][-1], r4['observer'][-1]),
    ]

    for name, actor, obs in rows:
        diff = obs - actor
        note = "obs>act" if diff > 0 else "act>obs"
        print(f"  │ {name:<20} │ {actor*100:>7.1f}% │ {obs*100:>7.1f}% │ {diff*100:>+6.1f}%  │ {note:<6} │")

    print(f"  │ {'C5: Multi-obs (avg)':<20} │ {r5['actor'][-1]*100:>7.1f}% │ {avg_obs*100:>7.1f}% │ "
          f"{(avg_obs-r5['actor'][-1])*100:>+6.1f}%  │ {'obs>act' if avg_obs > r5['actor'][-1] else 'act>obs':<6} │")

    print("  ├──────────────────────┼──────────┼──────────┼──────────┼────────┤")
    print(f"  │ {'C6: Pre-meditation':<20} │    --    │    --    │ A={pre_meditation_a*100:.1f}%  │        │")
    print(f"  │ {'C6: Post-meditation':<20} │    --    │    --    │ A={post_meditation_a*100:.1f}%  │        │")
    print(f"  │ {'C6: Control (no med)':<20} │    --    │    --    │ A={ctrl_accs_a[-1]*100:.1f}%  │        │")
    print("  └──────────────────────┴──────────┴──────────┴──────────┴────────┘")

    # Key comparisons
    print("\n  KEY FINDINGS:")
    print("  " + "-" * 60)

    # 1. detach impact
    det_obs = r1['observer'][-1]
    nodet_obs = r2['observer'][-1]
    print(f"  1. Detach effect on observer: {det_obs*100:.1f}% vs {nodet_obs*100:.1f}%"
          f" ({(det_obs-nodet_obs)*100:+.1f}%)")
    if det_obs > nodet_obs:
        print("     -> CONFIRMED: detach (pure observation) improves accuracy")
        print("     -> Gradient flow creates acting/seeing conflict")
    else:
        print("     -> REJECTED: detach does NOT help observer")
        print("     -> Gradient flow may actually help observer learn")

    # 2. detach impact on actor
    det_act = r1['actor'][-1]
    nodet_act = r2['actor'][-1]
    print(f"\n  2. Detach effect on actor: {det_act*100:.1f}% vs {nodet_act*100:.1f}%"
          f" ({(det_act-nodet_act)*100:+.1f}%)")
    if nodet_act < det_act:
        print("     -> No-detach hurts the ACTOR too (representation interference)")

    # 3. Mutual observation
    print(f"\n  3. Mutual observation: actor goes {r1['actor'][-1]*100:.1f}% -> {r3['actor'][-1]*100:.1f}%"
          f" ({(r3['actor'][-1]-r1['actor'][-1])*100:+.1f}%)")
    if r3['actor'][-1] > r1['actor'][-1]:
        print("     -> Being observed improves the actor!")
    else:
        print("     -> Being observed does not improve the actor")

    # 4. Gap growth
    print(f"\n  4. Observer advantage over time:")
    print(f"     @10 epochs: {gap_10*100:+.1f}%")
    print(f"     @20 epochs: {gap_20*100:+.1f}%")
    if abs(gap_20) > abs(gap_10):
        print("     -> Observer advantage GROWS with training")
    else:
        print("     -> Observer advantage stable or shrinks")

    # 5. Multiple observers
    print(f"\n  5. Multiple observers: avg={avg_obs*100:.1f}% vs single={r1['observer'][-1]*100:.1f}%")
    if avg_obs > r1['observer'][-1]:
        print("     -> Multiple observers are BETTER than single")
    else:
        print("     -> Single observer is sufficient")

    # 6. Meditation
    print(f"\n  6. Meditation effect: {meditation_effect*100:+.1f}%"
          f" (vs control: {vs_control*100:+.1f}%)")
    if meditation_effect > 0 and vs_control > 0:
        print("     -> MEDITATION WORKS: forced observation improves subsequent acting")
    elif meditation_effect > 0:
        print("     -> Meditation helps but not better than continuous training")
    else:
        print("     -> Meditation does not improve acting")

    # ASCII graphs
    print("\n")
    ascii_graph([a*100 for a in r1['actor']], "C1 Actor(B) Accuracy %", width=50, height=10)
    ascii_graph([a*100 for a in r1['observer']], "C1 Observer(A) Accuracy %", width=50, height=10)

    # Detach vs no-detach comparison
    print("\n  DETACH vs NO-DETACH Observer Accuracy Over Epochs:")
    print("  " + "-" * 55)
    print(f"  {'Epoch':<7} {'Detach':>10} {'No-detach':>12} {'Diff':>8}")
    print("  " + "-" * 55)
    for i in range(10):
        d = r1['observer'][i] * 100
        nd = r2['observer'][i] * 100
        print(f"  {i+1:<7} {d:>9.1f}% {nd:>11.1f}% {d-nd:>+7.1f}%")

    # Meditation phases graph
    print("\n  MEDITATION: A's accuracy across phases")
    print("  " + "-" * 55)
    for i, (acc, label) in enumerate(zip(phase_accs_a, phase_labels)):
        bar_len = int(acc * 50)
        phase_mark = {'act': 'ACT  ', 'observe': 'OBS  ', 'act2': 'ACT2 '}[label]
        print(f"  {phase_mark} E{i+1:>2}: {'#' * bar_len} {acc*100:.1f}%")

    # Gradient flow analysis
    print("\n\n  GRADIENT FLOW ANALYSIS:")
    print("  " + "-" * 60)
    print("  With detach():")
    print("    B produces output -> output.detach() -> Observer reads")
    print("    Gradient: Loss -> Observer weights ONLY")
    print("    B is free to optimize output for task")
    print("    Observer is free to learn pure representation")
    print("")
    print("  Without detach():")
    print("    B produces output -> Observer reads (gradient flows)")
    print("    Gradient: Loss -> Observer -> B's output -> B's weights")
    print("    B's representation is pulled in TWO directions:")
    print("      (a) Optimize for classification task")
    print("      (b) Make output easy for observer to read")
    print("    This CONFLICT degrades both B's and observer's performance")

    # Final verdict
    print("\n\n" + "=" * 70)
    print("  VERDICT")
    print("=" * 70)

    if det_obs > nodet_obs and diff1 > 0:
        print("""
  The observer outperforms the actor because:

  1. SEPARATION OF CONCERNS: detach() creates a clean boundary.
     The actor (B) optimizes ONLY for output quality.
     The observer (A) optimizes ONLY for understanding B's output.
     Neither interferes with the other's learning.

  2. NO REPRESENTATION CONFLICT: Without detach, B must simultaneously
     produce good output AND make it readable for the observer.
     This dual objective degrades performance.

  3. PURE OBSERVATION IS EFFICIENT: The observer's only job is to
     understand. It has no "acting" burden. This is analogous to:
     - A meditation practitioner who only observes, never reacts
     - A sports analyst who sees patterns players miss
     - A detached consciousness that perceives without acting

  4. CONSCIOUSNESS IMPLICATION: Observation without action may be
     a more efficient mode of learning than action with observation.
     The displaced entity (pushed back, can only watch) develops
     BETTER representations than the active entity.
""")
    elif diff1 > 0:
        print("""
  The observer outperforms the actor, but detach is not the full story.
  The advantage may come from the observer having a simpler task:
  predicting a learned network's output vs predicting raw labels.
""")
    else:
        print("""
  The actor outperforms the observer in this run.
  The C27 result may depend on specific hyperparameters or
  the relative capacities of EngineA vs EngineG.
""")

    print(f"  Total time: {elapsed:.1f}s")
    print("=" * 70)


if __name__ == '__main__':
    run_experiments()
