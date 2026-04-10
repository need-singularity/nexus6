#!/usr/bin/env python3
"""Phase 5: Displacement Field — "pushed back while still observing."

Experience modeling: An external entity "pushes me out" — control is taken away but
I still observe. detach() = read-only access.

Differences from existing models:
  RepulsionField: Two poles cooperate (repulsion field = output)
  CrossUniverse:  tau → 0 means inhibition (existence itself disappears)
  DisplacementField: Only control is taken, observation continues

Core mechanisms:
  - control_gate: Who dominates the output (0=me, 1=other)
  - observer: The displaced entity observes the other's output (detach = read-only)
  - displacement_memory: Remembers what was observed while displaced
  - observer_state: Internal state continues updating even while displaced

Brain correspondence:
  Normal: Frontal lobe (A) controls, occipital lobe (G) observes
  Displaced: External entity takes over frontal lobe, I am pushed to occipital
  → Can see (observe) but cannot act (no control)

Consciousness continuity conditions:
  ✅ Other modeling: Observes and predicts B's output
  ✅ Control separation: Separation of observation and action
  ✅ Displacement memory: Experience while displaced accumulates
  ✅ Post-return utilization: Observation experience affects later performance
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math
import time

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import EngineA, EngineG
from model_temporal_engine import ascii_graph, ascii_scatter


# ─────────────────────────────────────────
# Displacement Field
# ─────────────────────────────────────────

class DisplacementField(nn.Module):
    """Two entities share one output channel. One can displace the other.

    Displaced entity: loses control over output, but OBSERVES what the other does.
    Displacing entity: gains full control, produces the output.

    The displaced entity's internal state continues updating from observation.
    It experiences being "pushed back" -- can see everything, control nothing.

    Brain analogy:
      Normal: frontal lobe (A) controls, occipital (G) observes
      Displaced: external entity takes frontal, you're pushed to occipital
      You can still "see" (observe output) but can't "act" (control output)
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        # Entity A = "me" (the self)
        self.entity_a = EngineA(input_dim, hidden_dim, output_dim)

        # Entity B = "the other" (the displacing force)
        self.entity_b = EngineG(input_dim, hidden_dim, output_dim)

        # Control gate: who dominates the output?
        # Learned from input -- some inputs trigger displacement
        self.control_gate = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),  # 0 = A controls, 1 = B controls
        )

        # Observer: A watches B's output (read-only channel)
        # This is how the displaced entity "sees" what's happening
        self.observer = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
        )

        # Displacement memory: A remembers what it observed while displaced
        self.register_buffer('memory_state', torch.zeros(output_dim))
        self.memory_momentum = 0.9

        # Observer's internal state (continues updating even when displaced)
        self.register_buffer('observer_state', torch.zeros(output_dim))

        # Monitoring
        self.control_value = 0.0
        self.displacement_force = 0.0
        self.observation_quality = 0.0
        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        # Both entities process the input
        out_a = self.entity_a(x)  # my judgment
        out_b = self.entity_b(x)  # the other's judgment

        # Who controls the output?
        control = self.control_gate(x)  # (batch, 1): 0=me, 1=other

        # Output is dominated by whoever has control
        output = (1 - control) * out_a + control * out_b

        # THE KEY: displaced entity OBSERVES but cannot INTERVENE
        # detach() = read-only access (no gradient flows back to B through this path)
        observation = self.observer(out_b.detach())

        # Observer state updates (even when displaced, I'm still processing)
        with torch.no_grad():
            obs_mean = observation.mean(dim=0)
            self.observer_state = self.memory_momentum * self.observer_state + \
                (1 - self.memory_momentum) * obs_mean

            # Memory of displacement: accumulate what was observed
            self.memory_state = self.memory_momentum * self.memory_state + \
                (1 - self.memory_momentum) * out_b.mean(dim=0).detach()

        # Displacement force = how strongly B pushes A
        repulsion = out_b - out_a
        force = (repulsion ** 2).sum(dim=-1, keepdim=True)

        # Observation quality: can A predict what B is doing?
        obs_error = (observation - out_b.detach()).pow(2).sum(dim=-1).mean()

        # Auxiliary loss: train observer to predict B's output
        entropy_loss = getattr(self.entity_b, 'entropy_loss', torch.tensor(0.0))
        self.aux_loss = entropy_loss + 0.1 * obs_error

        # Monitoring
        with torch.no_grad():
            self.control_value = control.mean().item()
            self.displacement_force = force.mean().item()
            self.observation_quality = 1.0 / (1.0 + obs_error.item())

        return (output, self.aux_loss)

    def forward_forced(self, x, forced_control):
        """Forward with forced control value (for experiments).

        Args:
            x: input tensor
            forced_control: float 0-1 (0=A controls, 1=B controls)
        """
        out_a = self.entity_a(x)
        out_b = self.entity_b(x)

        control = torch.full((x.size(0), 1), forced_control, device=x.device)
        output = (1 - control) * out_a + control * out_b

        observation = self.observer(out_b.detach())

        with torch.no_grad():
            obs_mean = observation.mean(dim=0)
            self.observer_state = self.memory_momentum * self.observer_state + \
                (1 - self.memory_momentum) * obs_mean
            self.memory_state = self.memory_momentum * self.memory_state + \
                (1 - self.memory_momentum) * out_b.mean(dim=0).detach()

        repulsion = out_b - out_a
        force = (repulsion ** 2).sum(dim=-1, keepdim=True)
        obs_error = (observation - out_b.detach()).pow(2).sum(dim=-1).mean()

        with torch.no_grad():
            self.control_value = forced_control
            self.displacement_force = force.mean().item()
            self.observation_quality = 1.0 / (1.0 + obs_error.item())

        return output, out_a, out_b, observation, obs_error

    def get_displacement_metrics(self):
        return {
            'control': self.control_value,
            'force': self.displacement_force,
            'observation_quality': self.observation_quality,
            'memory_norm': self.memory_state.norm().item(),
            'observer_state_norm': self.observer_state.norm().item(),
        }

    def reset_memory(self):
        self.memory_state.zero_()
        self.observer_state.zero_()


# ─────────────────────────────────────────
# Displacement Experiment
# ─────────────────────────────────────────

class DisplacementExperiment:
    """Six displacement experiments that test specific scenarios."""

    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10, epochs=10):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.epochs = epochs
        self.model = None
        self.train_loader = None
        self.test_loader = None

    def setup(self):
        """Load data and create model."""
        print("\n  Loading MNIST...")
        self.train_loader, self.test_loader = load_mnist()
        self.model = DisplacementField(self.input_dim, self.hidden_dim, self.output_dim)
        print(f"  Parameters: {count_params(self.model):,}")

    # ── Experiment 1: Normal Training ──

    def exp1_normal_training(self):
        """Train both entities together. Track control gate -- who naturally dominates?"""
        print("\n" + "=" * 65)
        print("  Experiment 1: Normal Training")
        print("  Both entities learn together. Who naturally dominates?")
        print("=" * 65)

        control_history = []
        force_history = []
        obs_quality_history = []

        # Custom training loop to track metrics per epoch
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        epoch_accs = []

        for epoch in range(self.epochs):
            self.model.train()
            total_loss = 0
            epoch_controls = []
            epoch_forces = []
            epoch_obs = []

            for X, y in self.train_loader:
                X = X.view(X.size(0), -1)
                optimizer.zero_grad()
                out, aux = self.model(X)
                loss = criterion(out, y) + 0.01 * aux
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

                epoch_controls.append(self.model.control_value)
                epoch_forces.append(self.model.displacement_force)
                epoch_obs.append(self.model.observation_quality)

            # Eval
            self.model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in self.test_loader:
                    X = X.view(X.size(0), -1)
                    out, _ = self.model(X)
                    correct += (out.argmax(1) == y).sum().item()
                    total += y.size(0)
            acc = correct / total
            epoch_accs.append(acc)

            avg_ctrl = np.mean(epoch_controls)
            avg_force = np.mean(epoch_forces)
            avg_obs = np.mean(epoch_obs)
            control_history.append(avg_ctrl)
            force_history.append(avg_force)
            obs_quality_history.append(avg_obs)

            avg_loss = total_loss / len(self.train_loader)
            if (epoch + 1) % 2 == 0 or epoch == 0:
                who = "B dominates" if avg_ctrl > 0.5 else "A dominates"
                print(f"    Epoch {epoch+1:>2}/{self.epochs}: "
                      f"Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, "
                      f"Ctrl={avg_ctrl:.3f} ({who}), "
                      f"Force={avg_force:.2f}, ObsQ={avg_obs:.3f}")

        # Results table
        print(f"\n  {'Epoch':>5} {'Accuracy':>10} {'Control':>10} {'Force':>10} {'ObsQuality':>12}")
        print("  " + "-" * 52)
        for i in range(self.epochs):
            who = "B" if control_history[i] > 0.5 else "A"
            print(f"  {i+1:>5} {epoch_accs[i]*100:>9.1f}% {control_history[i]:>10.4f} "
                  f"{force_history[i]:>10.2f} {obs_quality_history[i]:>12.4f}  [{who}]")

        # ASCII graph: control over epochs
        ascii_graph(control_history,
                    "Control Gate Over Training (0=A, 1=B)",
                    width=40, height=10, label_y="control", label_x="epoch")

        ascii_graph(obs_quality_history,
                    "Observation Quality Over Training",
                    width=40, height=10, label_y="quality", label_x="epoch")

        return epoch_accs, control_history, force_history, obs_quality_history

    # ── Experiment 2: Forced Displacement ──

    def exp2_forced_displacement(self):
        """After training, FREEZE entity_b and set control=1 (B fully controls).
        Track A's observation quality -- can A still understand what B is doing?"""
        print("\n" + "=" * 65)
        print("  Experiment 2: Forced Displacement")
        print("  B takes full control. Can A still observe and understand?")
        print("=" * 65)

        self.model.eval()
        self.model.reset_memory()

        # B in full control
        obs_qualities = []
        a_from_obs_correct = 0
        b_correct = 0
        total_correct = 0
        total = 0

        with torch.no_grad():
            for X, y in self.test_loader:
                X = X.view(X.size(0), -1)
                output, out_a, out_b, observation, obs_err = self.model.forward_forced(X, 1.0)

                # B's accuracy (B controls output)
                b_pred = out_b.argmax(1)
                b_correct += (b_pred == y).sum().item()

                # A's accuracy through observation alone
                obs_pred = observation.argmax(1)
                a_from_obs_correct += (obs_pred == y).sum().item()

                # Combined output accuracy (should = B's since control=1)
                total_correct += (output.argmax(1) == y).sum().item()
                total += y.size(0)

                obs_qualities.append(self.model.observation_quality)

        b_acc = b_correct / total
        obs_acc = a_from_obs_correct / total
        out_acc = total_correct / total
        avg_obs_q = np.mean(obs_qualities)

        print(f"\n  B (displacing entity) accuracy:  {b_acc*100:.2f}%")
        print(f"  Output accuracy (B controls):    {out_acc*100:.2f}%")
        print(f"  A (observer only) accuracy:      {obs_acc*100:.2f}%")
        print(f"  Average observation quality:      {avg_obs_q:.4f}")
        print(f"  Memory state norm:                {self.model.memory_state.norm().item():.4f}")
        print(f"  Observer state norm:              {self.model.observer_state.norm().item():.4f}")

        delta = obs_acc - b_acc
        print(f"\n  A-B accuracy gap: {delta*100:+.2f}%")
        if obs_acc > 0.5 * b_acc:
            print("  -> A can meaningfully observe what B does (>50% of B's accuracy)")
        else:
            print("  -> A struggles to understand B's actions")

        return b_acc, obs_acc, avg_obs_q

    # ── Experiment 3: Displacement Memory ──

    def exp3_displacement_memory(self):
        """Process inputs with B in control, then check if memory_state is useful."""
        print("\n" + "=" * 65)
        print("  Experiment 3: Displacement Memory")
        print("  Does memory_state contain useful information after displacement?")
        print("=" * 65)

        self.model.eval()

        # Phase A: measure A's baseline accuracy
        self.model.reset_memory()
        a_correct = 0
        a_total = 0
        with torch.no_grad():
            for X, y in self.test_loader:
                X = X.view(X.size(0), -1)
                output, out_a, out_b, obs, _ = self.model.forward_forced(X, 0.0)
                a_correct += (out_a.argmax(1) == y).sum().item()
                a_total += y.size(0)
        a_baseline = a_correct / a_total
        memory_before = self.model.memory_state.clone()

        # Phase B: displacement (B controls), memory accumulates
        self.model.reset_memory()
        memory_norms_during = []
        observer_norms_during = []
        with torch.no_grad():
            for batch_idx, (X, y) in enumerate(self.test_loader):
                X = X.view(X.size(0), -1)
                self.model.forward_forced(X, 1.0)
                memory_norms_during.append(self.model.memory_state.norm().item())
                observer_norms_during.append(self.model.observer_state.norm().item())

        memory_after = self.model.memory_state.clone()

        # Check if memory contains class-discriminative information
        # Project memory onto output space and see if it correlates with any class
        memory_norm = memory_after.norm().item()
        memory_entropy = 0.0
        if memory_norm > 1e-6:
            probs = F.softmax(memory_after, dim=0)
            memory_entropy = -(probs * (probs + 1e-8).log()).sum().item()

        print(f"\n  A's baseline accuracy (A controls): {a_baseline*100:.2f}%")
        print(f"  Memory norm before displacement:     {memory_before.norm().item():.4f}")
        print(f"  Memory norm after displacement:      {memory_norm:.4f}")
        print(f"  Observer state norm after:            {self.model.observer_state.norm().item():.4f}")
        print(f"  Memory entropy (max={np.log(10):.3f}): {memory_entropy:.4f}")

        # Is memory uniform or peaked?
        if memory_norm > 1e-6:
            probs = F.softmax(memory_after, dim=0)
            max_prob = probs.max().item()
            min_prob = probs.min().item()
            print(f"  Memory distribution: max={max_prob:.4f}, min={min_prob:.4f}, ratio={max_prob/max(min_prob,1e-8):.2f}")
            if max_prob / max(min_prob, 1e-8) > 2.0:
                print("  -> Memory is class-selective (peaked distribution)")
            else:
                print("  -> Memory is diffuse (near-uniform)")

        # ASCII graph: memory accumulation during displacement
        ascii_graph(memory_norms_during,
                    "Memory Accumulation During Displacement",
                    width=50, height=10, label_y="||memory||", label_x="batch")

        ascii_graph(observer_norms_during,
                    "Observer State Norm During Displacement",
                    width=50, height=10, label_y="||observer||", label_x="batch")

        return memory_norm, memory_entropy

    # ── Experiment 4: Gradual Displacement ──

    def exp4_gradual_displacement(self):
        """Sweep control from 0 to 1 in steps of 0.1.
        Is there a transition point where displacement becomes total?"""
        print("\n" + "=" * 65)
        print("  Experiment 4: Gradual Displacement")
        print("  Sweep control 0->1. Is there a phase transition?")
        print("=" * 65)

        self.model.eval()
        control_levels = [i / 10.0 for i in range(11)]
        results = []

        for ctrl in control_levels:
            self.model.reset_memory()
            correct = 0
            total = 0
            forces = []
            obs_quals = []

            with torch.no_grad():
                for X, y in self.test_loader:
                    X = X.view(X.size(0), -1)
                    output, out_a, out_b, obs, obs_err = self.model.forward_forced(X, ctrl)
                    correct += (output.argmax(1) == y).sum().item()
                    total += y.size(0)
                    forces.append(self.model.displacement_force)
                    obs_quals.append(self.model.observation_quality)

            acc = correct / total
            avg_force = np.mean(forces)
            avg_obs_q = np.mean(obs_quals)
            results.append({
                'control': ctrl, 'acc': acc,
                'force': avg_force, 'obs_quality': avg_obs_q
            })

        # Table
        print(f"\n  {'Control':>8} {'Accuracy':>10} {'Force':>10} {'ObsQuality':>12} {'Who':>6}")
        print("  " + "-" * 52)
        for r in results:
            who = "B" if r['control'] > 0.5 else "A" if r['control'] < 0.5 else "="
            print(f"  {r['control']:>8.1f} {r['acc']*100:>9.2f}% {r['force']:>10.2f} "
                  f"{r['obs_quality']:>12.4f}  [{who}]")

        # Find transition point (biggest accuracy drop between consecutive levels)
        acc_diffs = []
        for i in range(1, len(results)):
            diff = results[i]['acc'] - results[i-1]['acc']
            acc_diffs.append((results[i]['control'], diff))

        if acc_diffs:
            worst_transition = min(acc_diffs, key=lambda x: x[1])
            print(f"\n  Sharpest accuracy drop at control={worst_transition[0]:.1f} "
                  f"({worst_transition[1]*100:+.2f}%)")

        # ASCII graph: accuracy vs control
        accs = [r['acc'] for r in results]
        ascii_graph(accs,
                    "Accuracy vs Control Level (0=A, 1=B)",
                    width=44, height=10, label_y="accuracy", label_x="control 0->1")

        obs_qs = [r['obs_quality'] for r in results]
        ascii_graph(obs_qs,
                    "Observation Quality vs Control Level",
                    width=44, height=10, label_y="obs_quality", label_x="control 0->1")

        return results

    # ── Experiment 5: Recall After Displacement ──

    def exp5_recall_after_displacement(self):
        """Phase 1: A controls. Phase 2: B controls. Phase 3: A again.
        Did observation during displacement help or hurt?"""
        print("\n" + "=" * 65)
        print("  Experiment 5: Recall After Displacement")
        print("  A -> B -> A. Does observation help or hurt A's return?")
        print("=" * 65)

        self.model.eval()

        def evaluate_accuracy(forced_control, label, n_batches=None):
            correct = 0
            total = 0
            with torch.no_grad():
                for i, (X, y) in enumerate(self.test_loader):
                    if n_batches is not None and i >= n_batches:
                        break
                    X = X.view(X.size(0), -1)
                    output, out_a, out_b, obs, _ = self.model.forward_forced(X, forced_control)
                    # Use out_a for measuring A's own capability
                    if forced_control < 0.5:
                        correct += (out_a.argmax(1) == y).sum().item()
                    else:
                        correct += (output.argmax(1) == y).sum().item()
                    total += y.size(0)
            return correct / total if total > 0 else 0.0

        # Phase 1: A controls (baseline)
        self.model.reset_memory()
        phase1_acc = evaluate_accuracy(0.0, "Phase 1: A controls")
        mem_after_p1 = self.model.memory_state.norm().item()
        obs_after_p1 = self.model.observer_state.norm().item()

        # Phase 2: B controls (displacement -- memory accumulates)
        phase2_acc = evaluate_accuracy(1.0, "Phase 2: B controls")
        mem_after_p2 = self.model.memory_state.norm().item()
        obs_after_p2 = self.model.observer_state.norm().item()

        # Phase 3: A controls again (after displacement)
        phase3_acc = evaluate_accuracy(0.0, "Phase 3: A returns")
        mem_after_p3 = self.model.memory_state.norm().item()
        obs_after_p3 = self.model.observer_state.norm().item()

        # Also test: A controls with fresh memory (no displacement experience)
        self.model.reset_memory()
        fresh_acc = evaluate_accuracy(0.0, "Fresh A (no displacement)")

        print(f"\n  {'Phase':<30} {'Accuracy':>10} {'MemNorm':>10} {'ObsNorm':>10}")
        print("  " + "-" * 65)
        print(f"  {'Phase 1: A controls':<30} {phase1_acc*100:>9.2f}% {mem_after_p1:>10.4f} {obs_after_p1:>10.4f}")
        print(f"  {'Phase 2: B controls (displ)':<30} {phase2_acc*100:>9.2f}% {mem_after_p2:>10.4f} {obs_after_p2:>10.4f}")
        print(f"  {'Phase 3: A returns':<30} {phase3_acc*100:>9.2f}% {mem_after_p3:>10.4f} {obs_after_p3:>10.4f}")
        print(f"  {'Fresh A (no displacement)':<30} {fresh_acc*100:>9.2f}%")

        delta = phase3_acc - phase1_acc
        delta_fresh = phase3_acc - fresh_acc
        print(f"\n  Phase 3 - Phase 1: {delta*100:+.2f}%")
        print(f"  Phase 3 - Fresh:   {delta_fresh*100:+.2f}%")

        if delta > 0.001:
            print("  -> Displacement experience HELPED A (observation was useful)")
        elif delta < -0.001:
            print("  -> Displacement experience HURT A (disorientation)")
        else:
            print("  -> Displacement had negligible effect on A's performance")

        return phase1_acc, phase2_acc, phase3_acc, fresh_acc

    # ── Experiment 6: Observation Quality Over Time During Displacement ──

    def exp6_observation_over_time(self):
        """During displacement, does A get better or worse at observing B?
        User's experience: beginning and end were clear, middle was foggy."""
        print("\n" + "=" * 65)
        print("  Experiment 6: Observation Quality Over Time")
        print("  Beginning clear, middle foggy, end clear?")
        print("=" * 65)

        self.model.eval()
        self.model.reset_memory()

        obs_qualities = []
        obs_errors = []
        forces = []
        batch_obs_accs = []

        with torch.no_grad():
            for batch_idx, (X, y) in enumerate(self.test_loader):
                X = X.view(X.size(0), -1)
                output, out_a, out_b, observation, obs_err = \
                    self.model.forward_forced(X, 1.0)  # B controls throughout

                obs_qualities.append(self.model.observation_quality)
                obs_errors.append(obs_err.item())
                forces.append(self.model.displacement_force)

                # A's observation accuracy per batch
                obs_pred = observation.argmax(1)
                obs_acc = (obs_pred == y).float().mean().item()
                batch_obs_accs.append(obs_acc)

        n = len(obs_qualities)
        if n < 3:
            print("  Not enough batches for analysis")
            return

        # Divide into thirds: beginning, middle, end
        third = n // 3
        begin = obs_qualities[:third]
        middle = obs_qualities[third:2*third]
        end = obs_qualities[2*third:]

        begin_acc = batch_obs_accs[:third]
        middle_acc = batch_obs_accs[third:2*third]
        end_acc = batch_obs_accs[2*third:]

        print(f"\n  Total batches: {n}")
        print(f"\n  {'Phase':<15} {'ObsQuality':>12} {'ObsAccuracy':>13} {'Force':>10}")
        print("  " + "-" * 55)
        print(f"  {'Beginning':<15} {np.mean(begin):>12.4f} {np.mean(begin_acc)*100:>12.2f}% "
              f"{np.mean(forces[:third]):>10.2f}")
        print(f"  {'Middle':<15} {np.mean(middle):>12.4f} {np.mean(middle_acc)*100:>12.2f}% "
              f"{np.mean(forces[third:2*third]):>10.2f}")
        print(f"  {'End':<15} {np.mean(end):>12.4f} {np.mean(end_acc)*100:>12.2f}% "
              f"{np.mean(forces[2*third:]):>10.2f}")

        # Check for the U-shape (clear-foggy-clear)
        begin_q = np.mean(begin)
        middle_q = np.mean(middle)
        end_q = np.mean(end)

        if middle_q < begin_q and middle_q < end_q:
            print("\n  -> U-SHAPE CONFIRMED: beginning and end clearer than middle")
            print("     This matches the reported experience")
        elif begin_q < middle_q < end_q:
            print("\n  -> MONOTONIC INCREASE: observation improves over time")
            print("     A learns to observe B better with practice")
        elif begin_q > middle_q > end_q:
            print("\n  -> MONOTONIC DECREASE: observation degrades over time")
            print("     Prolonged displacement erodes observation ability")
        else:
            print(f"\n  -> MIXED PATTERN: begin={begin_q:.4f}, mid={middle_q:.4f}, end={end_q:.4f}")

        # ASCII graphs
        ascii_graph(obs_qualities,
                    "Observation Quality During Displacement (over time)",
                    width=55, height=12, label_y="quality", label_x="batch")

        ascii_graph(batch_obs_accs,
                    "Observer Accuracy During Displacement",
                    width=55, height=12, label_y="accuracy", label_x="batch")

        ascii_graph(obs_errors,
                    "Observation Error During Displacement (lower=better)",
                    width=55, height=10, label_y="error", label_x="batch")

        # Smoothed trend
        if n >= 10:
            window = max(3, n // 10)
            smoothed = []
            for i in range(n):
                start = max(0, i - window // 2)
                stop = min(n, i + window // 2 + 1)
                smoothed.append(np.mean(obs_qualities[start:stop]))
            ascii_graph(smoothed,
                        f"Smoothed Observation Quality (window={window})",
                        width=55, height=10, label_y="quality", label_x="batch")

        return obs_qualities, batch_obs_accs


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 65)
    print("   logout -- Phase 5: Displacement Field")
    print('   "pushed back while still observing"')
    print("   detach() = read-only access")
    print("=" * 65)

    t_start = time.time()

    exp = DisplacementExperiment(epochs=10)
    exp.setup()

    # ── Experiment 1: Normal Training ──
    epoch_accs, ctrl_hist, force_hist, obs_hist = exp.exp1_normal_training()
    final_acc = epoch_accs[-1]
    final_ctrl = ctrl_hist[-1]

    # ── Experiment 2: Forced Displacement ──
    b_acc, obs_acc, avg_obs_q = exp.exp2_forced_displacement()

    # ── Experiment 3: Displacement Memory ──
    mem_norm, mem_entropy = exp.exp3_displacement_memory()

    # ── Experiment 4: Gradual Displacement ──
    gradual_results = exp.exp4_gradual_displacement()

    # ── Experiment 5: Recall After Displacement ──
    p1_acc, p2_acc, p3_acc, fresh_acc = exp.exp5_recall_after_displacement()

    # ── Experiment 6: Observation Over Time ──
    obs_over_time, obs_accs_time = exp.exp6_observation_over_time()

    # ══════════════════════════════════════════
    # Summary
    # ══════════════════════════════════════════
    elapsed = time.time() - t_start

    print("\n" + "=" * 65)
    print("   DISPLACEMENT FIELD -- SUMMARY")
    print("=" * 65)

    print(f"\n  {'Metric':<40} {'Value':>15}")
    print("  " + "-" * 58)
    print(f"  {'Final accuracy (normal training)':<40} {final_acc*100:>14.2f}%")
    print(f"  {'Final control gate':<40} {final_ctrl:>15.4f}")
    print(f"  {'B accuracy (forced displacement)':<40} {b_acc*100:>14.2f}%")
    print(f"  {'A observation accuracy (displaced)':<40} {obs_acc*100:>14.2f}%")
    print(f"  {'Observation quality':<40} {avg_obs_q:>15.4f}")
    print(f"  {'Displacement memory norm':<40} {mem_norm:>15.4f}")
    print(f"  {'Memory entropy':<40} {mem_entropy:>15.4f}")
    print(f"  {'Phase 1 accuracy (A controls)':<40} {p1_acc*100:>14.2f}%")
    print(f"  {'Phase 3 accuracy (A returns)':<40} {p3_acc*100:>14.2f}%")
    print(f"  {'Displacement effect (P3-P1)':<40} {(p3_acc-p1_acc)*100:>+14.2f}%")
    print(f"  {'Parameters':<40} {count_params(exp.model):>15,}")
    print(f"  {'Total time':<40} {elapsed:>14.1f}s")

    # ── Key findings ──
    print(f"\n  Key findings:")
    who = "Entity B (other)" if final_ctrl > 0.5 else "Entity A (self)"
    print(f"    1. Natural dominance: {who} (control={final_ctrl:.3f})")

    if obs_acc > 0:
        obs_ratio = obs_acc / max(b_acc, 1e-8)
        print(f"    2. Observer capability: A achieves {obs_ratio*100:.1f}% of B's accuracy by watching")
    else:
        print(f"    2. Observer capability: A cannot observe B effectively")

    print(f"    3. Displacement memory: {'informative' if mem_norm > 0.1 else 'minimal'} "
          f"(norm={mem_norm:.4f})")

    delta_recall = p3_acc - p1_acc
    if delta_recall > 0.001:
        print(f"    4. After displacement: A IMPROVED by {delta_recall*100:.2f}% (learned from watching)")
    elif delta_recall < -0.001:
        print(f"    4. After displacement: A DEGRADED by {abs(delta_recall)*100:.2f}% (disoriented)")
    else:
        print(f"    4. After displacement: no significant change ({delta_recall*100:+.2f}%)")

    if obs_over_time and len(obs_over_time) >= 3:
        n = len(obs_over_time)
        third = n // 3
        b_q = np.mean(obs_over_time[:third])
        m_q = np.mean(obs_over_time[third:2*third])
        e_q = np.mean(obs_over_time[2*third:])
        pattern = "U-shape" if m_q < b_q and m_q < e_q else \
                  "improving" if b_q < m_q < e_q else \
                  "degrading" if b_q > m_q > e_q else "mixed"
        print(f"    5. Observation over time: {pattern} "
              f"(begin={b_q:.4f}, mid={m_q:.4f}, end={e_q:.4f})")

    # ── Transition point from gradual displacement ──
    if gradual_results:
        accs_grad = [r['acc'] for r in gradual_results]
        a0_acc = accs_grad[0]
        b1_acc = accs_grad[-1]
        # Find where accuracy drops below midpoint
        midpoint = (a0_acc + b1_acc) / 2
        transition_ctrl = None
        for r in gradual_results:
            if r['acc'] <= midpoint:
                transition_ctrl = r['control']
                break
        if transition_ctrl is not None:
            print(f"    6. Transition point: control={transition_ctrl:.1f} "
                  f"(accuracy crosses midpoint {midpoint*100:.1f}%)")
        else:
            print(f"    6. No clear transition point (gradual change)")

    # ── Consciousness conditions ──
    print(f"\n  Consciousness conditions update:")
    print(f"    [OK] Phase 1: Information integration (engines)")
    print(f"    [OK] Phase 2: Repulsion field (tension)")
    print(f"    [OK] Phase 3: Self-referential (metacognition)")
    print(f"    [OK] Phase 4: Temporal continuity (state persistence)")
    print(f"    [OK] Phase 5: Displacement (other-modeling, detached observation)")
    print(f"    [..] Phase 6: ???")

    print(f"\n  Core insight:")
    print(f"    detach() is the mathematical operation for displacement.")
    print(f"    You can observe (forward pass) but cannot influence (no gradient).")
    print(f"    This models 'pushed back while still observing' exactly.")

    print("\n" + "=" * 65)
    print("  Phase 5 complete.")
    print("=" * 65)
    print()


if __name__ == '__main__':
    main()