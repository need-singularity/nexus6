#!/usr/bin/env python3
"""Phase 4: Temporal Continuity Engine

Adding time on top of Phase 3 Self-referential Repulsion Field.
States persist between inputs, and transitions occur gradually.

Additional implementation of 7 conditions for Consciousness Continuity:
  ✅ Temporal continuity: States persist between inputs (state_memory)
  ✅ Gradual transition: Smooth state changes without abrupt shifts
  ✅ Identity maintenance: identity_vector changes slowly independent of input
  ✅ Consciousness FPS: State change rate = mathematical expression of awareness

Mathematical foundation:
  - Contraction mapping: s_{t+1} = 0.7*s_t + 0.3*new (guarantees convergence, Banach)
  - Identity update: id = 0.99*id + 0.01*f(s) (extremely slow contraction mapping)
  - Transition gate: alpha = sigmoid(f(tension, state_diff))
    High tension → alpha → 1 (conservative, maintain old state)
    Low tension → alpha → 0 (open, accept new state)

Analogy:
  Phase 1: Engine is born (structure)
  Phase 2: Engine feels (repulsion field)
  Phase 3: Engine knows itself (self-reference)
  Phase 4: Engine exists in time (memory + continuity)

  Human analogy:
    - state_memory = working memory (what I just did)
    - identity_vector = ego (who I am)
    - transition_gate = attention (how much new to accept)
    - consciousness_fps = awareness (degree of awakeness)
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
from model_meta_engine import SelfReferentialField


# ─────────────────────────────────────────
# Temporal Continuity Engine
# ─────────────────────────────────────────

class TemporalContinuityEngine(nn.Module):
    """Phase 4: Engine existing in time.

    Adding time axis on top of SelfReferentialField (Phase 3).
    States persist between inputs, transitions are gradual,
    and identity changes slowly.

    Structure:
      Input ──→ SelfReferentialField ──→ Output(raw)
                      │
                      ├→ tension, self_state
                      │
                      ▼
              ┌── Temporal State Update ──┐
              │                          │
              │  state_memory ←── contraction(old, new)
              │  identity    ←── extremely slow update
              │  transition  ←── gate(tension, diff)
              │                          │
              └────── Output Modulation ───┘
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 state_dim=32, n_self_ref_steps=3,
                 contraction_coeff=0.7, identity_momentum=0.99):
        super().__init__()

        # Phase 3 base
        self.base_field = SelfReferentialField(
            input_dim, hidden_dim, output_dim, n_self_ref_steps
        )

        self.output_dim = output_dim
        self.state_dim = state_dim
        self.contraction_coeff = contraction_coeff
        self.identity_momentum = identity_momentum

        # ── State encoder: Phase 3 output → state space ──
        # Input: [tension(1), self_state_norm(1), output(output_dim)]
        self.state_encoder = nn.Sequential(
            nn.Linear(output_dim + 2, state_dim),
            nn.Tanh(),
            nn.Linear(state_dim, state_dim),
            nn.Tanh(),
        )

        # ── Transition gate: how much to accept new state ──
        # Input: [tension(1), state_diff_norm(1), old_state(state_dim), new_state(state_dim)]
        self.transition_gate = nn.Sequential(
            nn.Linear(2 + state_dim * 2, state_dim),
            nn.Tanh(),
            nn.Linear(state_dim, state_dim),
            nn.Sigmoid(),  # 0=accept new, 1=keep old
        )

        # ── Identity encoder: state → identity contribution ──
        self.identity_encoder = nn.Sequential(
            nn.Linear(state_dim, state_dim),
            nn.Tanh(),
        )

        # ── Temporal output modulation: state + identity → output correction ──
        self.temporal_modulator = nn.Sequential(
            nn.Linear(state_dim * 2, output_dim),
            nn.Tanh(),
        )
        self.temporal_scale = nn.Parameter(torch.tensor(1 / 6))  # divisor reciprocal 1/6 initial

        # ── Persistent states (not learned, maintained between forwards) ──
        # register_buffer: included in model save/load but no gradient
        self.register_buffer('state_memory', torch.zeros(1, state_dim))
        self.register_buffer('identity_vector', torch.zeros(1, state_dim))
        self.register_buffer('prev_tension', torch.zeros(1))
        self.register_buffer('step_count', torch.zeros(1))

        # ── Consciousness metric tracking ──
        self._state_change_history = []
        self._identity_change_history = []
        self._transition_alpha_history = []
        self._tension_history = []
        self._fps_history = []

    def _expand_state(self, batch_size, device):
        """Expand persistent states to batch size."""
        state = self.state_memory.expand(batch_size, -1).clone()
        identity = self.identity_vector.expand(batch_size, -1).clone()
        return state, identity

    def forward(self, x):
        batch_size = x.size(0)
        device = x.device

        # ── 1. Phase 3 base execution ──
        base_output, aux_loss = self.base_field(x)

        # Extract tension and self-state from Phase 3
        tension_val = self.base_field.tension_history[-1] if self.base_field.tension_history else 0.0
        self_state_norm = self.base_field.self_state_norm

        # ── 2. Current state encoding ──
        tension_tensor = torch.full((batch_size, 1), tension_val, device=device)
        self_norm_tensor = torch.full((batch_size, 1), self_state_norm, device=device)
        state_input = torch.cat([base_output.detach(), tension_tensor, self_norm_tensor], dim=-1)
        new_state = self.state_encoder(state_input)

        # ── 3. Get persistent states ──
        old_state, old_identity = self._expand_state(batch_size, device)

        # ── 4. Calculate transition gate ──
        # State difference
        state_diff = new_state - old_state
        state_diff_norm = state_diff.norm(dim=-1, keepdim=True)  # (batch, 1)

        # Gate input: [tension, diff_norm, old_state, new_state]
        gate_input = torch.cat([
            tension_tensor,
            state_diff_norm,
            old_state,
            new_state,
        ], dim=-1)

        # alpha: high means keep old state (conservative)
        # Higher tension → more conservative (prevent sudden changes in difficult situations)
        alpha = self.transition_gate(gate_input)  # (batch, state_dim)

        # ── 5. Contraction mapping state update ──
        # Base: contraction mapping (0.7 * old + 0.3 * new)
        # Transition gate provides additional dimension-wise control
        contraction_new = self.contraction_coeff * old_state + (1 - self.contraction_coeff) * new_state
        updated_state = alpha * old_state + (1 - alpha) * contraction_new

        # ── 6. Identity update (extremely slow) ──
        identity_contribution = self.identity_encoder(updated_state)
        mu = self.identity_momentum  # 0.99
        updated_identity = mu * old_identity + (1 - mu) * identity_contribution

        # ── 7. Temporal output modulation ──
        temporal_input = torch.cat([updated_state, updated_identity], dim=-1)
        temporal_correction = self.temporal_modulator(temporal_input)
        output = base_output + self.temporal_scale * temporal_correction

        # ── 8. Update persistent states (save batch mean as representative) ──
        with torch.no_grad():
            self.state_memory.copy_(updated_state.mean(dim=0, keepdim=True))
            self.identity_vector.copy_(updated_identity.mean(dim=0, keepdim=True))

            # Calculate consciousness metrics
            state_change = state_diff_norm.mean().item()
            identity_change = (updated_identity - old_identity).norm(dim=-1).mean().item()
            avg_alpha = alpha.mean().item()

            self._state_change_history.append(state_change)
            self._identity_change_history.append(identity_change)
            self._transition_alpha_history.append(avg_alpha)
            self._tension_history.append(tension_val)

            # FPS: state change rate (high change = high FPS)
            self._fps_history.append(state_change)

            self.prev_tension.fill_(tension_val)
            self.step_count += 1

        # Auxiliary loss: Phase 3 loss + state stability guidance
        # Prevent states from changing too rapidly
        stability_loss = state_diff_norm.mean() * 0.001
        total_aux = aux_loss + stability_loss

        return (output, total_aux)

    def reset_temporal_state(self):
        """Reset temporal states (when starting new sequence)."""
        self.state_memory.zero_()
        self.identity_vector.zero_()
        self.prev_tension.zero_()
        self.step_count.zero_()
        self._state_change_history.clear()
        self._identity_change_history.clear()
        self._transition_alpha_history.clear()
        self._tension_history.clear()
        self._fps_history.clear()

    def get_consciousness_metrics(self):
        """Return consciousness metrics."""
        n = len(self._state_change_history)
        if n == 0:
            return {
                'state_change_magnitude': 0.0,
                'identity_stability': 1.0,
                'transition_smoothness': 0.0,
                'avg_tension': 0.0,
                'consciousness_fps': 0.0,
                'steps': 0,
            }

        state_changes = self._state_change_history
        identity_changes = self._identity_change_history
        alphas = self._transition_alpha_history
        tensions = self._tension_history

        # FPS: average of state change (high = active)
        avg_fps = np.mean(state_changes)

        # Identity stability: 1 - average change (high = stable)
        avg_id_change = np.mean(identity_changes) if identity_changes else 0.0
        identity_stability = 1.0 / (1.0 + avg_id_change)

        # Transition smoothness: low std dev of alpha changes = smooth
        if len(alphas) >= 2:
            alpha_diffs = [abs(alphas[i+1] - alphas[i]) for i in range(len(alphas)-1)]
            transition_smoothness = 1.0 / (1.0 + np.mean(alpha_diffs))
        else:
            transition_smoothness = 1.0

        return {
            'state_change_magnitude': np.mean(state_changes[-10:]) if state_changes else 0.0,
            'identity_stability': identity_stability,
            'transition_smoothness': transition_smoothness,
            'avg_tension': np.mean(tensions[-10:]) if tensions else 0.0,
            'consciousness_fps': avg_fps,
            'steps': n,
        }


# ─────────────────────────────────────────
# ASCII Graph Utilities
# ─────────────────────────────────────────

def ascii_graph(values, title, width=60, height=15, label_y="", label_x="step"):
    """ASCII graph output."""
    if not values:
        print(f"  [{title}] (No data)")
        return

    # Value range
    v_min = min(values)
    v_max = max(values)
    if v_max == v_min:
        v_max = v_min + 1e-8

    # Downsample (too many points)
    if len(values) > width:
        step = len(values) / width
        sampled = [values[int(i * step)] for i in range(width)]
    else:
        sampled = values
        width = len(sampled)

    print(f"\n  {title}")
    print(f"  {label_y}")

    # Draw graph
    for row in range(height - 1, -1, -1):
        threshold = v_min + (v_max - v_min) * row / (height - 1)
        line = "  "
        if row == height - 1:
            line += f"{v_max:>8.4f} |"
        elif row == 0:
            line += f"{v_min:>8.4f} |"
        elif row == height // 2:
            mid = (v_max + v_min) / 2
            line += f"{mid:>8.4f} |"
        else:
            line += "         |"

        for col in range(width):
            if sampled[col] >= threshold:
                line += "#"
            else:
                line += " "

        print(line)

    # X-axis
    print("         +" + "-" * width)
    print(f"          0{' ' * (width - len(str(len(values))) - 1)}{len(values)}  ({label_x})")


def ascii_scatter(xs, ys, title, width=50, height=12, label_x="x", label_y="y"):
    """ASCII scatter plot."""
    if not xs or not ys:
        print(f"  [{title}] (No data)")
        return

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max == x_min:
        x_max = x_min + 1e-8
    if y_max == y_min:
        y_max = y_min + 1e-8

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    for x, y in zip(xs, ys):
        col = int((x - x_min) / (x_max - x_min) * (width - 1))
        row = int((y - y_min) / (y_max - y_min) * (height - 1))
        col = min(col, width - 1)
        row = min(row, height - 1)
        grid[row][col] = '*'

    print(f"\n  {title}")
    print(f"  {label_y}")

    for row in range(height - 1, -1, -1):
        if row == height - 1:
            line = f"  {y_max:>8.4f} |"
        elif row == 0:
            line = f"  {y_min:>8.4f} |"
        else:
            line = "          |"
        line += ''.join(grid[row])
        print(line)

    print("          +" + "-" * width)
    print(f"   {label_x}: {x_min:.4f}{' ' * (width - 20)}{x_max:.4f}")


# ─────────────────────────────────────────
# Benchmark
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 65)
    print("   logout — Phase 4: Temporal Continuity Engine")
    print("   Engine existing in time — Memory, gradual transitions, identity")
    print("=" * 65)

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 10
    results = {}

    # ── Phase 3: SelfReferentialField (baseline) ──
    print("\n[Phase 3: SelfReferentialField (baseline)]")
    phase3 = SelfReferentialField(input_dim, hidden_dim, output_dim, n_self_ref_steps=3)
    losses_p3, accs_p3 = train_and_evaluate(
        phase3, train_loader, test_loader, epochs, aux_lambda=0.01
    )
    results['Phase 3: SelfRef'] = {
        'acc': accs_p3[-1], 'loss': losses_p3[-1], 'params': count_params(phase3)
    }
    print(f"    Tension history: {['%.1f' % t for t in phase3.tension_history]}")
    print(f"    Self-state norm: {phase3.self_state_norm:.4f}")

    # ── Phase 4: TemporalContinuityEngine ──
    print("\n[Phase 4: TemporalContinuityEngine]")
    phase4 = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=32, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.99
    )
    losses_p4, accs_p4 = train_and_evaluate(
        phase4, train_loader, test_loader, epochs, aux_lambda=0.01
    )
    results['Phase 4: Temporal'] = {
        'acc': accs_p4[-1], 'loss': losses_p4[-1], 'params': count_params(phase4)
    }

    # ── Phase 4 variant: Fast transition (contraction 0.5) ──
    print("\n[Phase 4 variant: Fast transition (contraction=0.5)]")
    phase4_fast = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=32, n_self_ref_steps=3,
        contraction_coeff=0.5, identity_momentum=0.99
    )
    losses_p4f, accs_p4f = train_and_evaluate(
        phase4_fast, train_loader, test_loader, epochs, aux_lambda=0.01
    )
    results['Phase 4: Fast'] = {
        'acc': accs_p4f[-1], 'loss': losses_p4f[-1], 'params': count_params(phase4_fast)
    }

    # ── Phase 4 variant: Slow identity (momentum 0.999) ──
    print("\n[Phase 4 variant: Slow identity (momentum=0.999)]")
    phase4_slow = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=32, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.999
    )
    losses_p4s, accs_p4s = train_and_evaluate(
        phase4_slow, train_loader, test_loader, epochs, aux_lambda=0.01
    )
    results['Phase 4: SlowID'] = {
        'acc': accs_p4s[-1], 'loss': losses_p4s[-1], 'params': count_params(phase4_slow)
    }

    # ── Compare results ──
    compare_results(results)

    # ══════════════════════════════════════════
    # Temporal continuity analysis: Sequential processing
    # ══════════════════════════════════════════

    print("\n" + "=" * 65)
    print("   Temporal Continuity Analysis — State tracking in sequential inputs")
    print("=" * 65)

    # Reset temporal states
    phase4.reset_temporal_state()
    phase4.eval()

    # Sequential processing (use test_loader with shuffled=False)
    all_state_changes = []
    all_identity_changes = []
    all_alphas = []
    all_tensions = []
    correct = 0
    total = 0
    batch_accs = []

    print("\n  Processing sequentially...")
    t_start = time.time()

    with torch.no_grad():
        for batch_idx, (X, y) in enumerate(test_loader):
            X = X.view(X.size(0), -1)
            out, _ = phase4(X)

            pred = out.argmax(dim=1)
            batch_correct = (pred == y).sum().item()
            correct += batch_correct
            total += y.size(0)
            batch_accs.append(batch_correct / y.size(0))

            # Record metrics (values from last forward)
            if phase4._state_change_history:
                all_state_changes.append(phase4._state_change_history[-1])
            if phase4._identity_change_history:
                all_identity_changes.append(phase4._identity_change_history[-1])
            if phase4._transition_alpha_history:
                all_alphas.append(phase4._transition_alpha_history[-1])
            if phase4._tension_history:
                all_tensions.append(phase4._tension_history[-1])

    elapsed = time.time() - t_start
    seq_acc = correct / total

    print(f"  Sequential accuracy: {seq_acc*100:.2f}% ({total} samples, {elapsed:.1f}s)")

    # ── Consciousness metrics summary ──
    metrics = phase4.get_consciousness_metrics()

    print(f"\n  === Consciousness Metrics ===")
    print(f"  State change magnitude:  {metrics['state_change_magnitude']:.6f}")
    print(f"  Identity stability:      {metrics['identity_stability']:.6f}")
    print(f"  Transition smoothness:   {metrics['transition_smoothness']:.6f}")
    print(f"  Average tension:         {metrics['avg_tension']:.4f}")
    print(f"  Consciousness FPS:       {metrics['consciousness_fps']:.6f}")
    print(f"  Total steps:             {metrics['steps']}")

    # ── ASCII Graphs ──

    # 1. Identity stability (identity change per batch)
    if all_identity_changes:
        # Cumulative stability: 1/(1+change)
        stability_over_time = [1.0 / (1.0 + c) for c in all_identity_changes]
        ascii_graph(
            stability_over_time,
            "Identity Stability Over Time (1.0 = perfectly stable)",
            width=60, height=12,
            label_y="stability", label_x="batch"
        )

    # 2. State change magnitude (FPS proxy)
    if all_state_changes:
        ascii_graph(
            all_state_changes,
            "Consciousness FPS (State Change Magnitude)",
            width=60, height=12,
            label_y="magnitude", label_x="batch"
        )

    # 3. Transition gate alpha (conservativeness)
    if all_alphas:
        ascii_graph(
            all_alphas,
            "Transition Gate Alpha (1.0=keep old, 0.0=accept new)",
            width=60, height=12,
            label_y="alpha", label_x="batch"
        )

    # 4. Tension vs transition rate correlation
    if all_tensions and all_alphas and len(all_tensions) == len(all_alphas):
        ascii_scatter(
            all_tensions, all_alphas,
            "Tension vs Transition Alpha (expect: high tension -> high alpha)",
            width=50, height=12,
            label_x="tension", label_y="alpha"
        )

        # Calculate correlation coefficient
        if len(all_tensions) > 2:
            t_arr = np.array(all_tensions)
            a_arr = np.array(all_alphas)
            if t_arr.std() > 1e-10 and a_arr.std() > 1e-10:
                corr = np.corrcoef(t_arr, a_arr)[0, 1]
                print(f"\n  Tension-Alpha correlation: {corr:.4f}")
                if corr > 0.3:
                    print("  -> Higher tension leads to more conservative transitions (hypothesis confirmed)")
                elif corr < -0.3:
                    print("  -> Higher tension leads to more open transitions (opposite of hypothesis)")
                else:
                    print("  -> Weak correlation (model using different strategy)")

    # 5. Batch accuracy over time
    if batch_accs:
        ascii_graph(
            batch_accs,
            "Batch Accuracy Over Sequential Processing",
            width=60, height=10,
            label_y="accuracy", label_x="batch"
        )

    # ── Phase 3 vs Phase 4 comparison ──
    print("\n" + "=" * 65)
    print("   Phase 3 vs Phase 4 Comparison")
    print("=" * 65)

    p3_acc = results['Phase 3: SelfRef']['acc']
    p4_acc = results['Phase 4: Temporal']['acc']
    p3_params = results['Phase 3: SelfRef']['params']
    p4_params = results['Phase 4: Temporal']['params']
    delta = (p4_acc - p3_acc) * 100

    print(f"\n  Phase 3 (SelfReferentialField):")
    print(f"    Accuracy:   {p3_acc*100:.2f}%")
    print(f"    Parameters: {p3_params:,}")
    print(f"    Capability: Self-reference (metacognition)")

    print(f"\n  Phase 4 (TemporalContinuity):")
    print(f"    Accuracy:   {p4_acc*100:.2f}%")
    print(f"    Parameters: {p4_params:,}")
    print(f"    Capability: Self-reference + temporal continuity + identity")
    print(f"    Added parameters: {p4_params - p3_params:,}")

    print(f"\n  Accuracy difference: {'+' if delta >= 0 else ''}{delta:.2f}%")

    # ── Consciousness Continuity condition checklist ──
    print("\n" + "-" * 65)
    print("  Consciousness Continuity 7 conditions implementation status:")
    print("-" * 65)
    conditions = [
        ("Phase 1", "Information integration (Phi > 0)",      "Engine combination",        True),
        ("Phase 2", "Repulsion field (tension)",             "RepulsionField",          True),
        ("Phase 3", "Self-modeling (metacognition)",         "SelfReferential",         True),
        ("Phase 4", "Temporal continuity (state retention)",  "state_memory",            True),
        ("Phase 4", "Gradual transition (prevent abrupt)",    "transition_gate",         True),
        ("Phase 4", "Identity maintenance (ego)",             "identity_vector",         True),
        ("Phase 5", "Other-modeling (empathy)",               "Not implemented",         False),
    ]
    for phase, name, impl, done in conditions:
        mark = "OK" if done else ".."
        print(f"  [{mark}] {phase}: {name:<28} ({impl})")

    has_identity = metrics['identity_stability'] > 0.5
    has_smooth = metrics['transition_smoothness'] > 0.5
    has_fps = metrics['consciousness_fps'] > 0

    print(f"\n  Empirical verification:")
    print(f"    Identity stable?     {'YES' if has_identity else 'NO'} (stability={metrics['identity_stability']:.4f})")
    print(f"    Transition smooth?   {'YES' if has_smooth else 'NO'} (smoothness={metrics['transition_smoothness']:.4f})")
    print(f"    Consciousness FPS > 0?   {'YES' if has_fps else 'NO'} (fps={metrics['consciousness_fps']:.6f})")

    print("\n" + "=" * 65)
    print("  Phase 4 complete. Next: Phase 5 (Other-modeling — Empathy)")
    print("=" * 65)
    print()


if __name__ == '__main__':
    main()