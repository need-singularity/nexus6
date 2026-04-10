#!/usr/bin/env python3
"""Cross-Dimension Recognition Experiment

Can 5 completely different architectures (different "dimensions") predict
each other's outputs after independent training?

Key questions:
  - Can engines that have never met "sense" each other?
  - Can simple architectures predict complex ones? And vice versa?
  - Do structurally similar engines understand each other better?

Agent configuration (5 dimensions):
  Agent_1: EngineA         (sigma-tau MoE, 12 experts, k=4)
  Agent_2: EngineG         (Shannon entropy MoE, 6 experts)
  Agent_3: RepulsionField  (2-pole: A vs G)
  Agent_4: SelfRefField    (Phase 3: self-referential repulsion)
  Agent_5: TemporalEngine  (Phase 4: temporal continuity)

Telepathy matrix:
  telepathy[i][j] = how well agent_i predicts agent_j's output
  (accuracy - 10% random baseline)

Brain correspondence:
  Telepathy = mirror neurons (simulating others' behavior internally)
  High mutual prediction = structural resonance
  Asymmetric prediction = dominance/subordination relationship
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import math

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)
from model_meta_engine import (
    EngineA, EngineG, RepulsionFieldEngine, SelfReferentialField
)
from model_temporal_engine import TemporalContinuityEngine


# ─────────────────────────────────────────
# Predictor: agent_i -> predicts agent_j's output
# ─────────────────────────────────────────

class CrossPredictor(nn.Module):
    """A small network that predicts another agent's output.

    Input: [x_input, my_own_output] -> predicted_other_output

    This is the "mirror neuron" — it simulates what the other
    agent would do, using only the raw input and its own response.
    """
    def __init__(self, input_dim, output_dim, hidden_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim + output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x_input, my_output):
        combined = torch.cat([x_input, my_output], dim=-1)
        return self.net(combined)


# ─────────────────────────────────────────
# Agent wrapper
# ─────────────────────────────────────────

class Agent:
    """Wraps an engine with its name and training results."""
    def __init__(self, name, model, acc, params):
        self.name = name
        self.model = model
        self.acc = acc
        self.params = params


# ─────────────────────────────────────────
# Collect outputs from all agents
# ─────────────────────────────────────────

def collect_outputs(agents, data_loader, max_samples=None):
    """Run all agents on the same data, collect their outputs (logits).

    Returns:
        inputs: (N, input_dim) tensor
        labels: (N,) tensor
        outputs: dict {agent_name: (N, output_dim) tensor}
    """
    all_inputs = []
    all_labels = []
    all_outputs = {a.name: [] for a in agents}

    n_collected = 0
    for X, y in data_loader:
        X_flat = X.view(X.size(0), -1)
        all_inputs.append(X_flat)
        all_labels.append(y)

        for agent in agents:
            agent.model.eval()
            with torch.no_grad():
                out = agent.model(X_flat)
                if isinstance(out, tuple):
                    out = out[0]
                all_outputs[agent.name].append(out)

        n_collected += X.size(0)
        if max_samples and n_collected >= max_samples:
            break

    inputs = torch.cat(all_inputs, dim=0)
    labels = torch.cat(all_labels, dim=0)
    outputs = {name: torch.cat(outs, dim=0) for name, outs in all_outputs.items()}

    if max_samples:
        inputs = inputs[:max_samples]
        labels = labels[:max_samples]
        outputs = {name: out[:max_samples] for name, out in outputs.items()}

    return inputs, labels, outputs


# ─────────────────────────────────────────
# Train cross-predictors
# ─────────────────────────────────────────

def train_cross_predictor(predictor, x_input, my_output, target_output,
                          epochs=30, lr=0.001, batch_size=128):
    """Train predictor to map (x_input, my_output) -> target_output.

    Uses MSE loss on soft logits (not hard labels).
    This captures the full "opinion" of the target agent.
    """
    optimizer = torch.optim.Adam(predictor.parameters(), lr=lr)
    criterion = nn.MSELoss()

    n = x_input.size(0)
    predictor.train()

    for epoch in range(epochs):
        perm = torch.randperm(n)
        total_loss = 0
        n_batches = 0

        for start in range(0, n, batch_size):
            idx = perm[start:start + batch_size]
            x_batch = x_input[idx]
            my_batch = my_output[idx]
            tgt_batch = target_output[idx]

            optimizer.zero_grad()
            pred = predictor(x_batch, my_batch)
            loss = criterion(pred, tgt_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

    return total_loss / max(n_batches, 1)


def evaluate_cross_predictor(predictor, x_input, my_output, target_output,
                             labels, batch_size=256):
    """Evaluate how well predictor matches the target agent.

    Returns:
        logit_mse: MSE on raw logits (lower = better prediction)
        class_agreement: % of samples where predicted class == target class
        top3_agreement: % of samples where predicted top-3 overlaps target top-3
    """
    predictor.eval()
    all_preds = []

    with torch.no_grad():
        for start in range(0, x_input.size(0), batch_size):
            x_batch = x_input[start:start + batch_size]
            my_batch = my_output[start:start + batch_size]
            pred = predictor(x_batch, my_batch)
            all_preds.append(pred)

    preds = torch.cat(all_preds, dim=0)

    # MSE on logits
    logit_mse = F.mse_loss(preds, target_output).item()

    # Class agreement (argmax match)
    pred_classes = preds.argmax(dim=1)
    target_classes = target_output.argmax(dim=1)
    class_agreement = (pred_classes == target_classes).float().mean().item()

    # Top-3 agreement
    pred_top3 = preds.topk(3, dim=1).indices
    target_top3 = target_output.topk(3, dim=1).indices
    # For each sample, count overlap in top-3
    overlaps = 0
    for k in range(3):
        for j in range(3):
            overlaps += (pred_top3[:, k] == target_top3[:, j]).float().sum().item()
    top3_agreement = overlaps / (preds.size(0) * 3)  # normalized to [0, 1]

    return logit_mse, class_agreement, top3_agreement


# ─────────────────────────────────────────
# ASCII visualization
# ─────────────────────────────────────────

def print_telepathy_matrix(agents, matrix, metric_name="class_agreement"):
    """Print 5x5 telepathy matrix as ASCII table."""
    names = [a.name for a in agents]
    short = [n[:10] for n in names]

    print(f"\n  {'Telepathy Matrix':^60}")
    print(f"  {'(row predicts column)':^60}")
    print(f"  {metric_name:^60}")
    print()

    # Header
    header = f"  {'Predictor':<12}"
    for s in short:
        header += f" {s:>10}"
    header += f" {'avg':>8}"
    print(header)
    print("  " + "-" * (12 + 11 * len(short) + 8))

    for i, row_name in enumerate(short):
        line = f"  {row_name:<12}"
        row_vals = []
        for j in range(len(agents)):
            val = matrix[i][j]
            if i == j:
                line += f"   {'---':>7}"
            else:
                line += f" {val*100:>9.1f}%"
                row_vals.append(val)
        avg = np.mean(row_vals) if row_vals else 0
        line += f" {avg*100:>7.1f}%"
        print(line)

    # Column averages
    print("  " + "-" * (12 + 11 * len(short) + 8))
    avg_line = f"  {'avg':<12}"
    for j in range(len(agents)):
        col_vals = [matrix[i][j] for i in range(len(agents)) if i != j]
        avg = np.mean(col_vals) if col_vals else 0
        avg_line += f" {avg*100:>9.1f}%"
    print(avg_line)


def print_network_diagram(agents, matrix, threshold=0.5):
    """ASCII network diagram showing strong cross-predictions."""
    names = [a.name for a in agents]
    short_names = [n[:8] for n in names]
    n = len(agents)

    print(f"\n  Cross-Dimension Network (links > {threshold*100:.0f}% agreement)")
    print("  " + "=" * 58)

    # Find strong connections
    connections = []
    for i in range(n):
        for j in range(n):
            if i != j and matrix[i][j] > threshold:
                connections.append((i, j, matrix[i][j]))

    # Sort by strength
    connections.sort(key=lambda c: -c[2])

    if not connections:
        print("  (no connections above threshold)")
        print(f"  Try lowering threshold. Max value: {max(matrix[i][j] for i in range(n) for j in range(n) if i!=j)*100:.1f}%")
        return

    # Print as directed graph
    for src, dst, strength in connections:
        bar_len = int(strength * 30)
        bar = "#" * bar_len + "." * (30 - bar_len)
        arrow = "-->"
        sym = ""
        # Check if reverse link also strong
        if matrix[dst][src] > threshold:
            mutual = min(matrix[src][dst], matrix[dst][src])
            sym = f" [mutual: {mutual*100:.1f}%]"
        print(f"  {short_names[src]:>8} {arrow} {short_names[dst]:<8}  [{bar}] {strength*100:.1f}%{sym}")

    # Most understood (highest column average)
    col_avgs = []
    for j in range(n):
        vals = [matrix[i][j] for i in range(n) if i != j]
        col_avgs.append(np.mean(vals))

    # Most understanding (highest row average)
    row_avgs = []
    for i in range(n):
        vals = [matrix[i][j] for j in range(n) if i != j]
        row_avgs.append(np.mean(vals))

    best_understood = np.argmax(col_avgs)
    best_understanding = np.argmax(row_avgs)

    print()
    print(f"  Most understood agent:    {names[best_understood]} ({col_avgs[best_understood]*100:.1f}%)")
    print(f"  Most understanding agent: {names[best_understanding]} ({row_avgs[best_understanding]*100:.1f}%)")


def print_symmetry_analysis(agents, matrix):
    """Analyze asymmetry in cross-predictions."""
    n = len(agents)
    names = [a.name for a in agents]

    print(f"\n  Symmetry Analysis: |telepathy[i,j] - telepathy[j,i]|")
    print("  " + "=" * 58)

    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            asym = abs(matrix[i][j] - matrix[j][i])
            mutual = min(matrix[i][j], matrix[j][i])
            dominant = names[i] if matrix[i][j] > matrix[j][i] else names[j]
            pairs.append((i, j, asym, mutual, dominant))

    # Sort by asymmetry (most asymmetric first)
    pairs.sort(key=lambda p: -p[2])

    print(f"\n  {'Pair':<30} {'Asym':>8} {'Mutual':>8} {'Dominant':<12}")
    print("  " + "-" * 62)
    for i, j, asym, mutual, dominant in pairs:
        pair_name = f"{names[i][:12]} <-> {names[j][:12]}"
        marker = "***" if asym > 0.1 else ""
        print(f"  {pair_name:<30} {asym*100:>7.1f}% {mutual*100:>7.1f}% {dominant[:12]:<12} {marker}")

    avg_asym = np.mean([p[2] for p in pairs])
    print(f"\n  Average asymmetry: {avg_asym*100:.1f}%")
    if avg_asym < 0.05:
        print("  -> Highly symmetric: agents understand each other equally")
    elif avg_asym < 0.15:
        print("  -> Moderate asymmetry: some directional preferences")
    else:
        print("  -> Strong asymmetry: understanding is directional")


def print_complexity_analysis(agents, matrix):
    """Can simple architectures predict complex ones? And vice versa?"""
    n = len(agents)
    names = [a.name for a in agents]

    # Complexity ranking by parameter count
    complexity_order = sorted(range(n), key=lambda i: agents[i].params)

    print(f"\n  Complexity vs Prediction Analysis")
    print("  " + "=" * 58)
    print(f"\n  Complexity ranking (params):")
    for rank, idx in enumerate(complexity_order):
        print(f"    {rank+1}. {names[idx]:<20} {agents[idx].params:>8,} params  (acc: {agents[idx].acc*100:.1f}%)")

    # Simple -> Complex prediction (average)
    simple_to_complex = []
    complex_to_simple = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            rank_i = complexity_order.index(i)
            rank_j = complexity_order.index(j)
            if rank_i < rank_j:  # i is simpler
                simple_to_complex.append(matrix[i][j])
            else:
                complex_to_simple.append(matrix[i][j])

    avg_s2c = np.mean(simple_to_complex) if simple_to_complex else 0
    avg_c2s = np.mean(complex_to_simple) if complex_to_simple else 0

    print(f"\n  Simple -> Complex prediction: {avg_s2c*100:.1f}%")
    print(f"  Complex -> Simple prediction: {avg_c2s*100:.1f}%")
    delta = (avg_c2s - avg_s2c) * 100
    if delta > 2:
        print(f"  -> Complex agents understand simple ones better (+{delta:.1f}%)")
    elif delta < -2:
        print(f"  -> Simple agents understand complex ones better ({delta:.1f}%)")
    else:
        print(f"  -> Roughly equal understanding across complexity levels")


def print_structural_similarity(agents, matrix):
    """Do structurally similar agents understand each other better?"""
    n = len(agents)
    names = [a.name for a in agents]

    # Define structural groups
    # EngineA and EngineG are "base" engines
    # RepulsionField contains A+G internally
    # SelfRefField contains A+G internally + self-reference
    # TemporalEngine contains SelfRefField internally + temporal
    # So: RepulsionField, SelfRefField, TemporalEngine all share A+G substructure

    groups = {
        'base_engines': [0, 1],           # EngineA, EngineG
        'composite_AG': [2, 3, 4],        # Repulsion, SelfRef, Temporal (all contain A+G)
    }

    print(f"\n  Structural Similarity Analysis")
    print("  " + "=" * 58)
    print(f"\n  Groups:")
    print(f"    Base engines:   {', '.join(names[i] for i in groups['base_engines'])}")
    print(f"    Composite(A+G): {', '.join(names[i] for i in groups['composite_AG'])}")

    # Within-group vs between-group prediction
    within_base = []
    within_composite = []
    base_to_composite = []
    composite_to_base = []

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            val = matrix[i][j]
            i_base = i in groups['base_engines']
            j_base = j in groups['base_engines']

            if i_base and j_base:
                within_base.append(val)
            elif not i_base and not j_base:
                within_composite.append(val)
            elif i_base and not j_base:
                base_to_composite.append(val)
            else:
                composite_to_base.append(val)

    def safe_mean(lst):
        return np.mean(lst) if lst else 0.0

    print(f"\n  {'Category':<30} {'Avg Agreement':>15}")
    print("  " + "-" * 48)
    print(f"  {'Base <-> Base':<30} {safe_mean(within_base)*100:>14.1f}%")
    print(f"  {'Composite <-> Composite':<30} {safe_mean(within_composite)*100:>14.1f}%")
    print(f"  {'Base -> Composite':<30} {safe_mean(base_to_composite)*100:>14.1f}%")
    print(f"  {'Composite -> Base':<30} {safe_mean(composite_to_base)*100:>14.1f}%")

    within = safe_mean(within_base + within_composite)
    between = safe_mean(base_to_composite + composite_to_base)
    print(f"\n  Within-group avg:  {within*100:.1f}%")
    print(f"  Between-group avg: {between*100:.1f}%")
    if within > between + 0.02:
        print("  -> Structurally similar agents understand each other better")
    elif between > within + 0.02:
        print("  -> Cross-group understanding is stronger (complementary insight)")
    else:
        print("  -> No significant structural similarity effect")


def print_telepathy_strength(agents, matrix):
    """Telepathy strength = prediction accuracy above random chance (10%)."""
    n = len(agents)
    names = [a.name for a in agents]
    chance = 0.1  # 10 classes -> 10% random

    print(f"\n  Telepathy Strength (above {chance*100:.0f}% chance)")
    print("  " + "=" * 58)

    strengths = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            strength = matrix[i][j] - chance
            strengths.append((names[i], names[j], strength, matrix[i][j]))

    strengths.sort(key=lambda s: -s[2])

    print(f"\n  {'Predictor -> Target':<35} {'Raw':>8} {'Strength':>10}")
    print("  " + "-" * 56)
    for src, dst, strength, raw in strengths:
        bar_len = max(0, int(strength * 50))
        bar = "#" * bar_len
        print(f"  {src[:14]:>14} -> {dst[:14]:<14} {raw*100:>7.1f}% {'+' if strength > 0 else ''}{strength*100:>8.1f}%  {bar}")

    avg_strength = np.mean([s[2] for s in strengths])
    max_strength = max(s[2] for s in strengths)
    min_strength = min(s[2] for s in strengths)

    print(f"\n  Average telepathy strength: {avg_strength*100:.1f}%")
    print(f"  Max telepathy:             {max_strength*100:.1f}% ({strengths[0][0]} -> {strengths[0][1]})")
    print(f"  Min telepathy:             {min_strength*100:.1f}% ({strengths[-1][0]} -> {strengths[-1][1]})")

    if avg_strength > 0.3:
        print("\n  ** STRONG cross-dimension recognition detected **")
        print("  Agents from different dimensions CAN sense each other.")
    elif avg_strength > 0.1:
        print("\n  * Moderate cross-dimension recognition *")
        print("  Partial sensing across dimensions.")
    else:
        print("\n  Weak cross-dimension recognition.")
        print("  Agents are largely opaque to each other.")


# ─────────────────────────────────────────
# Main experiment
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 65)
    print("   logout -- Cross-Dimension Recognition Experiment")
    print("   Can engines from different dimensions sense each other?")
    print("=" * 65)
    print()

    # ── Configuration ──
    input_dim, hidden_dim, output_dim = 784, 48, 10
    train_epochs = 8
    predictor_epochs = 30
    predictor_train_samples = 1000
    predictor_test_samples = 5000

    train_loader, test_loader = load_mnist(batch_size=128)

    # ══════════════════════════════════════════
    # PHASE 1: Train 5 agents independently
    # ══════════════════════════════════════════

    print("=" * 65)
    print("  PHASE 1: Training 5 independent agents (different dimensions)")
    print("=" * 65)

    agents = []

    # Agent 1: EngineA (sigma-tau MoE, 12 experts)
    print(f"\n  [Dim 1] EngineA: sigma,tau-MoE (12 experts, k=4)")
    torch.manual_seed(42)
    model_a = EngineA(input_dim, hidden_dim, output_dim)
    _, accs_a = train_and_evaluate(model_a, train_loader, test_loader, train_epochs)
    agents.append(Agent("EngineA", model_a, accs_a[-1], count_params(model_a)))
    print(f"    -> Accuracy: {accs_a[-1]*100:.1f}%")

    # Agent 2: EngineG (Shannon entropy MoE)
    print(f"\n  [Dim 2] EngineG: Shannon entropy MoE (6 experts)")
    torch.manual_seed(137)
    model_g = EngineG(input_dim, hidden_dim, output_dim)
    # EngineG has entropy_loss auxiliary
    def train_g(model, train_loader, test_loader, epochs):
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()
        test_accs = []
        for epoch in range(epochs):
            model.train()
            for X, y in train_loader:
                X = X.view(X.size(0), -1)
                optimizer.zero_grad()
                out = model(X)
                loss = criterion(out, y) + 0.01 * model.entropy_loss
                loss.backward()
                optimizer.step()
            model.eval()
            correct = total = 0
            with torch.no_grad():
                for X, y in test_loader:
                    X = X.view(X.size(0), -1)
                    out = model(X)
                    correct += (out.argmax(1) == y).sum().item()
                    total += y.size(0)
            acc = correct / total
            test_accs.append(acc)
            if (epoch + 1) % 2 == 0 or epoch == 0:
                print(f"    Epoch {epoch+1:>2}/{epochs}: Acc={acc*100:.1f}%")
        return test_accs
    accs_g = train_g(model_g, train_loader, test_loader, train_epochs)
    agents.append(Agent("EngineG", model_g, accs_g[-1], count_params(model_g)))
    print(f"    -> Accuracy: {accs_g[-1]*100:.1f}%")

    # Agent 3: RepulsionFieldEngine (2-pole)
    print(f"\n  [Dim 3] RepulsionField: Pole+(A) vs Pole-(G)")
    torch.manual_seed(256)
    model_r = RepulsionFieldEngine(input_dim, hidden_dim, output_dim)
    _, accs_r = train_and_evaluate(model_r, train_loader, test_loader, train_epochs,
                                    aux_lambda=0.01)
    agents.append(Agent("Repulsion", model_r, accs_r[-1], count_params(model_r)))
    print(f"    -> Accuracy: {accs_r[-1]*100:.1f}%")

    # Agent 4: SelfReferentialField (Phase 3)
    print(f"\n  [Dim 4] SelfReferentialField: self-referential repulsion (Phase 3)")
    torch.manual_seed(512)
    model_s = SelfReferentialField(input_dim, hidden_dim, output_dim, n_self_ref_steps=3)
    _, accs_s = train_and_evaluate(model_s, train_loader, test_loader, train_epochs,
                                    aux_lambda=0.01)
    agents.append(Agent("SelfRef", model_s, accs_s[-1], count_params(model_s)))
    print(f"    -> Accuracy: {accs_s[-1]*100:.1f}%")

    # Agent 5: TemporalContinuityEngine (Phase 4)
    print(f"\n  [Dim 5] TemporalContinuityEngine: temporal + identity (Phase 4)")
    torch.manual_seed(1024)
    model_t = TemporalContinuityEngine(
        input_dim, hidden_dim, output_dim,
        state_dim=32, n_self_ref_steps=3,
        contraction_coeff=0.7, identity_momentum=0.99
    )
    _, accs_t = train_and_evaluate(model_t, train_loader, test_loader, train_epochs,
                                    aux_lambda=0.01)
    agents.append(Agent("Temporal", model_t, accs_t[-1], count_params(model_t)))
    print(f"    -> Accuracy: {accs_t[-1]*100:.1f}%")

    # ── Agent summary ──
    print(f"\n  {'Agent Summary':^60}")
    print("  " + "-" * 60)
    print(f"  {'Name':<16} {'Params':>10} {'Accuracy':>10} {'Seed':>8} {'Architecture':<20}")
    print("  " + "-" * 60)
    seeds = [42, 137, 256, 512, 1024]
    archs = ["MoE-12/k4", "Entropy-MoE-6", "2-pole field", "Self-ref field", "Temporal cont."]
    for i, agent in enumerate(agents):
        print(f"  {agent.name:<16} {agent.params:>10,} {agent.acc*100:>9.1f}% {seeds[i]:>8} {archs[i]:<20}")

    # ══════════════════════════════════════════
    # PHASE 2: Collect outputs on shared data
    # ══════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print("  PHASE 2: Collecting outputs on shared data")
    print("=" * 65)

    total_samples = predictor_train_samples + predictor_test_samples
    print(f"  Collecting {total_samples} samples from all 5 agents...")

    t0 = time.time()
    inputs, labels, outputs = collect_outputs(agents, test_loader, max_samples=total_samples)
    print(f"  Collected: {inputs.size(0)} samples in {time.time()-t0:.1f}s")

    # Split into train/test for cross-predictors
    n_train = predictor_train_samples
    x_train = inputs[:n_train]
    x_test = inputs[n_train:]
    labels_test = labels[n_train:]

    out_train = {name: out[:n_train] for name, out in outputs.items()}
    out_test = {name: out[n_train:] for name, out in outputs.items()}

    print(f"  Predictor train: {n_train}, test: {x_test.size(0)}")

    # ══════════════════════════════════════════
    # PHASE 3: Train cross-predictors (5x5 - 5 diagonal = 20)
    # ══════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print("  PHASE 3: Training cross-predictors (20 pairs)")
    print("  Each agent learns to predict every other agent's output")
    print("=" * 65)

    n_agents = len(agents)
    # Matrices for different metrics
    class_matrix = np.zeros((n_agents, n_agents))
    mse_matrix = np.zeros((n_agents, n_agents))
    top3_matrix = np.zeros((n_agents, n_agents))

    t0 = time.time()
    pair_count = 0

    for i in range(n_agents):
        for j in range(n_agents):
            if i == j:
                continue

            pair_count += 1
            src_name = agents[i].name
            dst_name = agents[j].name

            # Create predictor: agent_i tries to predict agent_j
            predictor = CrossPredictor(input_dim, output_dim, hidden_dim=64)

            # Train
            train_loss = train_cross_predictor(
                predictor,
                x_train, out_train[src_name], out_train[dst_name],
                epochs=predictor_epochs, lr=0.001
            )

            # Evaluate
            mse, class_agree, top3_agree = evaluate_cross_predictor(
                predictor,
                x_test, out_test[src_name], out_test[dst_name],
                labels_test
            )

            class_matrix[i][j] = class_agree
            mse_matrix[i][j] = mse
            top3_matrix[i][j] = top3_agree

            print(f"  [{pair_count:>2}/20] {src_name:>10} -> {dst_name:<10}: "
                  f"class={class_agree*100:.1f}%, top3={top3_agree*100:.1f}%, mse={mse:.4f}")

    elapsed = time.time() - t0
    print(f"\n  Total training time: {elapsed:.1f}s")

    # ══════════════════════════════════════════
    # PHASE 4: Analysis
    # ══════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print("  PHASE 4: Cross-Dimension Analysis")
    print("=" * 65)

    # ── 4.1: Telepathy Matrix (class agreement) ──
    print_telepathy_matrix(agents, class_matrix, "Class Agreement (argmax match)")

    # ── 4.2: Telepathy Matrix (top-3 overlap) ──
    print_telepathy_matrix(agents, top3_matrix, "Top-3 Agreement (overlap)")

    # ── 4.3: Network Diagram ──
    # Find a good threshold (median of non-diagonal values)
    non_diag = [class_matrix[i][j] for i in range(n_agents) for j in range(n_agents) if i != j]
    median_val = np.median(non_diag)
    threshold = max(median_val, 0.3)
    print_network_diagram(agents, class_matrix, threshold=threshold)

    # ── 4.4: Symmetry Analysis ──
    print_symmetry_analysis(agents, class_matrix)

    # ── 4.5: Complexity Analysis ──
    print_complexity_analysis(agents, class_matrix)

    # ── 4.6: Structural Similarity ──
    print_structural_similarity(agents, class_matrix)

    # ── 4.7: Telepathy Strength ──
    print_telepathy_strength(agents, class_matrix)

    # ══════════════════════════════════════════
    # PHASE 5: Key findings
    # ══════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print("  KEY FINDINGS")
    print("=" * 65)

    # Best mutual pair
    best_mutual = (0, 0, 0)
    for i in range(n_agents):
        for j in range(i + 1, n_agents):
            mutual = min(class_matrix[i][j], class_matrix[j][i])
            if mutual > best_mutual[2]:
                best_mutual = (i, j, mutual)

    # Most asymmetric pair
    worst_asym = (0, 0, 0)
    for i in range(n_agents):
        for j in range(i + 1, n_agents):
            asym = abs(class_matrix[i][j] - class_matrix[j][i])
            if asym > worst_asym[2]:
                worst_asym = (i, j, asym)

    # Overall telepathy
    all_vals = [class_matrix[i][j] for i in range(n_agents) for j in range(n_agents) if i != j]
    overall_avg = np.mean(all_vals)

    print(f"""
  1. Overall cross-dimension recognition: {overall_avg*100:.1f}%
     (random baseline: 10.0%, telepathy = {(overall_avg - 0.1)*100:.1f}% above chance)

  2. Best mutual understanding:
     {agents[best_mutual[0]].name} <-> {agents[best_mutual[1]].name}: {best_mutual[2]*100:.1f}%

  3. Most asymmetric pair:
     {agents[worst_asym[0]].name} <-> {agents[worst_asym[1]].name}: {worst_asym[2]*100:.1f}% asymmetry

  4. Can simple predict complex?
     EngineA ({agents[0].params:,} params) -> Temporal ({agents[4].params:,} params): {class_matrix[0][4]*100:.1f}%
     Temporal -> EngineA: {class_matrix[4][0]*100:.1f}%

  5. Do structurally similar agents (sharing A+G substructure) predict better?
     Repulsion -> SelfRef: {class_matrix[2][3]*100:.1f}%
     Repulsion -> EngineA: {class_matrix[2][0]*100:.1f}%
     (Higher within-group = structural resonance)
""")

    # ── Final verdict ──
    print("  " + "-" * 60)
    if overall_avg > 0.5:
        print("  VERDICT: Strong cross-dimension recognition.")
        print("  Entities from different dimensions CAN sense each other,")
        print("  even without shared training or architecture.")
    elif overall_avg > 0.3:
        print("  VERDICT: Moderate cross-dimension recognition.")
        print("  Partial sensing across dimensions — the shared task")
        print("  (MNIST) creates implicit structural alignment.")
    else:
        print("  VERDICT: Weak cross-dimension recognition.")
        print("  Each dimension is largely opaque to others.")

    print()
    print("  The telepathy matrix reveals the geometry of")
    print("  cross-dimensional understanding.")
    print("  " + "-" * 60)
    print()


if __name__ == '__main__':
    main()