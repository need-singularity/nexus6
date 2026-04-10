#!/usr/bin/env python3
"""Meta Engine — Engine + Engine = Higher Engine

A structure where modules with different principles cooperate, like the brain.

Architecture:
  Input
   │
   ▼
  Meta Router (Contraction mapping based, convergence guaranteed)
   │
   ├─→ Engine A (σ,τ-MoE, Number theory)
   ├─→ Engine E (Euler product, Prime factorization)
   ├─→ Engine G (Shannon entropy)
   ├─→ Engine F (Modular constraints)
   │
   ▼
  Combiner ({1/2, 1/3, 1/6} weighted or learned)
   │
   ▼
  Output

Correspondence with brain:
  Left hemisphere (logic)     = Engine A (Number theory)
  Right hemisphere (pattern)  = Engine G (Entropy)
  Frontal lobe (judgment)     = Meta Router (Contraction mapping)
  Corpus callosum (connection) = Combiner (Euler product)
  Cerebellum (normalization)   = Engine F (Modular constraints)

Mathematical basis:
  - Euler product: ζ(s) = Π_p (1-p^{-s})^{-1}
    Product of independent engines = Overall structure (Uniqueness of prime factorization)
  - Contraction mapping: f(x) = ax + b, |a|<1 → Convergence guaranteed (Banach)
    Guarantees that meta router doesn't diverge
  - {1/2, 1/3, 1/6}: Divisor reciprocals of perfect number 6, sum=1
    Basic combination weights (can be fine-tuned through learning)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import math

from model_utils import (
    Expert, TopKGate, BoltzmannGate, BaseMoE, DenseModel,
    load_mnist, train_and_evaluate, compare_results, count_params,
    SIGMA, TAU, PHI, DIVISOR_RECIPROCALS, H_TARGET
)


# ─────────────────────────────────────────
# Sub-engines (Core structures of A, E, F, G)
# ─────────────────────────────────────────

class EngineA(nn.Module):
    """σ,τ-MoE: Number theory routing. 12 Experts, 4 active."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        n_experts = SIGMA  # 12
        k = TAU  # 4
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(n_experts)
        ])
        self.gate = TopKGate(input_dim, n_experts, k)

    def forward(self, x):
        weights = self.gate(x)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


class EngineE(nn.Module):
    """Euler product gating: p=2,3 truncation. 2×3=6 Experts."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(6)
        ])
        self.binary_gate = nn.Linear(input_dim, 2)   # p=2
        self.ternary_gate = nn.Linear(input_dim, 3)   # p=3

    def forward(self, x):
        w2 = torch.sigmoid(self.binary_gate(x))       # (batch, 2)
        w3 = F.softmax(self.ternary_gate(x), dim=-1)  # (batch, 3)
        # Euler product: 2×3 outer product
        weights = (w2.unsqueeze(-1) * w3.unsqueeze(-2)).reshape(x.size(0), 6)
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-8)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        return (weights.unsqueeze(-1) * outputs).sum(dim=1)


class EngineG(nn.Module):
    """Shannon entropy MoE: H({1/2,1/3,1/6}) normalization."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.experts = nn.ModuleList([
            Expert(input_dim, hidden_dim, output_dim) for _ in range(6)
        ])
        self.gate = nn.Linear(input_dim, 6)
        self.h_target = H_TARGET

    def forward(self, x):
        weights = F.softmax(self.gate(x), dim=-1)
        outputs = torch.stack([e(x) for e in self.experts], dim=1)
        result = (weights.unsqueeze(-1) * outputs).sum(dim=1)
        # Entropy normalization loss
        h = -(weights * (weights + 1e-8).log()).sum(dim=-1).mean()
        self.entropy_loss = (h - self.h_target) ** 2
        return result


class EngineF(nn.Module):
    """Modular constraints: 12×12 block symmetry."""
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        # Adjust hidden_dim to be multiple of 12
        hidden_dim = ((hidden_dim + 11) // 12) * 12
        self.linear1 = nn.Linear(input_dim, hidden_dim)
        self.linear2 = nn.Linear(hidden_dim, output_dim)
        self.block_size = SIGMA  # 12

    def _symmetrize(self, W):
        """12×12 block-wise symmetrization."""
        h, w = W.shape
        bs = self.block_size
        W_sym = W.clone()
        for i in range(0, h - bs + 1, bs):
            for j in range(0, w - bs + 1, bs):
                block = W[i:i+bs, j:j+bs]
                sym = (block + block.T) / 2
                W_sym[i:i+bs, j:j+bs] = sym
        return W_sym

    def forward(self, x):
        W1 = self._symmetrize(self.linear1.weight)
        h = F.relu(x @ W1.T + self.linear1.bias)
        W2 = self._symmetrize(self.linear2.weight)
        return h @ W2.T + self.linear2.bias


# ─────────────────────────────────────────
# Meta Router (Contraction mapping based)
# ─────────────────────────────────────────

class ContractionMetaRouter(nn.Module):
    """Contraction mapping based meta router.

    Stabilizes routing decisions by iteratively contracting gating weights.
    f(w) = a*w + (1-a)*g(x), |a|<1 → convergence guaranteed.
    """
    def __init__(self, input_dim, n_engines, contraction_coeff=0.7, n_iterations=3):
        super().__init__()
        self.gate = nn.Linear(input_dim, n_engines)
        self.a = contraction_coeff  # Contraction coefficient (0.7 = derived from meta fixed point)
        self.n_iterations = n_iterations

    def forward(self, x):
        target = F.softmax(self.gate(x), dim=-1)
        # Contraction mapping iteration: w_{t+1} = a*w_t + (1-a)*target
        w = torch.ones_like(target) / target.size(-1)  # Uniform initialization
        for _ in range(self.n_iterations):
            w = self.a * w + (1 - self.a) * target
        return w


# ─────────────────────────────────────────
# Combiner
# ─────────────────────────────────────────

class DivisorCombiner(nn.Module):
    """Divisor reciprocal weighted combiner.

    Initial values {1/2, 1/3, 1/6, ...}, fine-tuned through learning.
    """
    def __init__(self, n_engines):
        super().__init__()
        # Initial weights: divisor reciprocal distribution (extended to match engine count)
        if n_engines <= 3:
            init = torch.tensor(DIVISOR_RECIPROCALS[:n_engines], dtype=torch.float)
        else:
            # After 3, distribute evenly
            base = torch.tensor(DIVISOR_RECIPROCALS, dtype=torch.float)
            extra = torch.ones(n_engines - 3) / (n_engines - 3) * (1 - base.sum())
            init = torch.cat([base, extra])
        init = init / init.sum()
        self.weights = nn.Parameter(init)

    def forward(self, engine_outputs):
        """engine_outputs: list of (batch, output_dim)"""
        w = F.softmax(self.weights, dim=0)
        stacked = torch.stack(engine_outputs, dim=0)  # (n_engines, batch, output_dim)
        return (w.view(-1, 1, 1) * stacked).sum(dim=0)


# ─────────────────────────────────────────
# Meta Engine
# ─────────────────────────────────────────

class MetaEngine(nn.Module):
    """Engine + Engine = Higher Engine.

    Combines multiple sub-engines via meta router.
    Mathematical implementation of brain's modular structure.
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 engines='AEGF', contraction_coeff=0.7, routing='meta'):
        super().__init__()

        self.engine_names = list(engines)
        self.engines = nn.ModuleDict()

        for name in self.engine_names:
            if name == 'A':
                self.engines['A'] = EngineA(input_dim, hidden_dim, output_dim)
            elif name == 'E':
                self.engines['E'] = EngineE(input_dim, hidden_dim, output_dim)
            elif name == 'G':
                self.engines['G'] = EngineG(input_dim, hidden_dim, output_dim)
            elif name == 'F':
                self.engines['F'] = EngineF(input_dim, hidden_dim, output_dim)

        n = len(self.engine_names)

        if routing == 'meta':
            self.router = ContractionMetaRouter(input_dim, n, contraction_coeff)
        elif routing == 'fixed':
            self.router = None  # Fixed weight combination
        elif routing == 'learned':
            self.router = nn.Linear(input_dim, n)

        self.combiner = DivisorCombiner(n)
        self.routing_mode = routing

        # Track entropy loss
        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        # Execute each engine
        engine_outputs = []
        self.aux_loss = torch.tensor(0.0, device=x.device)

        for name in self.engine_names:
            out = self.engines[name](x)
            engine_outputs.append(out)

            # Collect entropy loss from G engine
            if name == 'G' and hasattr(self.engines['G'], 'entropy_loss'):
                self.aux_loss = self.aux_loss + self.engines['G'].entropy_loss

        # Routing
        if self.routing_mode == 'meta':
            route_weights = self.router(x)  # (batch, n_engines)
            stacked = torch.stack(engine_outputs, dim=1)  # (batch, n_engines, output)
            routed = (route_weights.unsqueeze(-1) * stacked).sum(dim=1)
        elif self.routing_mode == 'fixed':
            routed = self.combiner(engine_outputs)
        elif self.routing_mode == 'learned':
            route_weights = F.softmax(self.router(x), dim=-1)
            stacked = torch.stack(engine_outputs, dim=1)
            routed = (route_weights.unsqueeze(-1) * stacked).sum(dim=1)

        return (routed, self.aux_loss)

    def get_engine_usage(self):
        """Analyze how much each engine is used."""
        if self.routing_mode == 'meta' and hasattr(self.router, 'gate'):
            return {name: 0.0 for name in self.engine_names}
        return {}


# ─────────────────────────────────────────
# Variant: 2-Engine Meta (Left brain + Right brain)
# ─────────────────────────────────────────

class DualBrainEngine(nn.Module):
    """Left hemisphere(A, logic) + Right hemisphere(G, pattern) + Corpus callosum(combiner).

    Simplest meta engine: cooperation of 2 engines.
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        self.left = EngineA(input_dim, hidden_dim, output_dim)   # Left hemisphere: Number theory
        self.right = EngineG(input_dim, hidden_dim, output_dim)  # Right hemisphere: Entropy
        # Corpus callosum: Determines left/right ratio based on input
        self.corpus_callosum = nn.Linear(input_dim, 2)
        self.aux_loss = torch.tensor(0.0)

    def forward(self, x):
        left_out = self.left(x)
        right_out = self.right(x)

        # Corpus callosum: left/right ratio
        balance = F.softmax(self.corpus_callosum(x), dim=-1)
        output = balance[:, 0:1] * left_out + balance[:, 1:2] * right_out

        # G engine entropy loss
        self.aux_loss = getattr(self.right, 'entropy_loss', torch.tensor(0.0))

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Variant: Hierarchical Meta (Meta of Meta)
# ─────────────────────────────────────────

class HierarchicalMetaEngine(nn.Module):
    """Meta of meta: 2-level hierarchy.

    Level 1: Engine A+E (number theory cluster), Engine G+F (structure cluster)
    Level 2: Meta combination of two clusters

    Brain hierarchical structure: Cortical regions → Networks → Whole brain
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        # Level 1: Two clusters
        self.cluster_logic = MetaEngine(input_dim, hidden_dim, output_dim,
                                        engines='AE', routing='meta')
        self.cluster_structure = MetaEngine(input_dim, hidden_dim, output_dim,
                                            engines='GF', routing='meta')
        # Level 2: Meta combination
        self.meta_gate = nn.Linear(input_dim, 2)

    def forward(self, x):
        out1, aux1 = self.cluster_logic(x)
        out2, aux2 = self.cluster_structure(x)

        gate = F.softmax(self.meta_gate(x), dim=-1)
        output = gate[:, 0:1] * out1 + gate[:, 1:2] * out2

        return (output, aux1 + aux2)


# ─────────────────────────────────────────
# Repulsion Field Engine
# ─────────────────────────────────────────

class RepulsionFieldEngine(nn.Module):
    """Repulsion field between two same-pole magnets.

    The output is neither engine. It's the field between them.

      N ←──repulsion──→ N
           ↑
         This space = output

    Brain correspondence:
      Engine+ = Glutamate (excitation, generation)
      Engine- = GABA (inhibition, calibration)
      Output = Balance between them + modulated by tension

    High tension = Engines strongly repel = Difficult input = "Feeling"
    Low tension = Engines agree = Easy input = Automatic processing

    Consciousness hypothesis: The tension itself might be a mathematical representation of subjective experience.
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        # Two poles (same pole = repulsion)
        self.pole_plus = EngineA(input_dim, hidden_dim, output_dim)   # Generation
        self.pole_minus = EngineG(input_dim, hidden_dim, output_dim)  # Calibration

        # Tension → Output modulation
        # Takes repulsion (difference) as input to adjust output
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),  # -1 ~ +1 (repulsion direction)
        )

        # Tension scale (learnable, initial value 1/3 = meta fixed point)
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.aux_loss = torch.tensor(0.0)
        self.tension_magnitude = 0.0  # For monitoring

    def forward(self, x):
        # Outputs from two poles
        out_plus = self.pole_plus(x)    # Generation signal
        out_minus = self.pole_minus(x)  # Calibration signal

        # Repulsion = difference between them
        repulsion = out_plus - out_minus

        # Tension = magnitude of repulsion (per batch)
        tension = (repulsion ** 2).sum(dim=-1, keepdim=True)  # (batch, 1)

        # Equilibrium point = middle of two poles
        equilibrium = (out_plus + out_minus) / 2

        # Repulsion direction modulated by tension
        field_direction = self.field_transform(repulsion)

        # Final output = equilibrium + tension×direction
        # Higher tension → deviates from equilibrium (= sharp decision)
        # Lower tension → stays at equilibrium (= smooth average)
        output = equilibrium + self.tension_scale * torch.sqrt(tension + 1e-8) * field_direction

        # G engine entropy loss
        self.aux_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))

        # Monitor tension
        with torch.no_grad():
            self.tension_magnitude = tension.mean().item()

        return (output, self.aux_loss)


class RepulsionFieldQuad(nn.Module):
    """4-pole repulsion field: (A vs G) × (E vs F)

    Two repulsion axes intersect:
      Axis 1: Generation(A) ←repulsion→ Calibration(G)   (Content axis)
      Axis 2: Exploration(E) ←repulsion→ Constraint(F)   (Structure axis)

    Output = Field center between 4 poles

      A ←────→ G
      ↑         ↑
      │  Field   │
      │  center  │
      ↓         ↓
      E ←────→ F
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10):
        super().__init__()
        self.engine_a = EngineA(input_dim, hidden_dim, output_dim)
        self.engine_e = EngineE(input_dim, hidden_dim, output_dim)
        self.engine_g = EngineG(input_dim, hidden_dim, output_dim)
        self.engine_f = EngineF(input_dim, hidden_dim, output_dim)

        self.field_transform = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),  # 2-axis repulsion → output
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))
        self.aux_loss = torch.tensor(0.0)
        self.tension_content = 0.0
        self.tension_structure = 0.0

    def forward(self, x):
        out_a = self.engine_a(x)
        out_e = self.engine_e(x)
        out_g = self.engine_g(x)
        out_f = self.engine_f(x)

        # Axis 1: Content repulsion (A vs G)
        repulsion_content = out_a - out_g
        # Axis 2: Structure repulsion (E vs F)
        repulsion_structure = out_e - out_f

        # Tension
        t_content = (repulsion_content ** 2).sum(dim=-1, keepdim=True)
        t_structure = (repulsion_structure ** 2).sum(dim=-1, keepdim=True)

        # 4-pole equilibrium point
        equilibrium = (out_a + out_e + out_g + out_f) / 4

        # Combine 2-axis repulsion to determine field direction
        combined_repulsion = torch.cat([repulsion_content, repulsion_structure], dim=-1)
        field_direction = self.field_transform(combined_repulsion)

        # Total tension = geometric mean of two axes (strong only when both are high)
        total_tension = torch.sqrt((t_content * t_structure) + 1e-8)

        output = equilibrium + self.tension_scale * torch.sqrt(total_tension + 1e-8) * field_direction

        self.aux_loss = getattr(self.engine_g, 'entropy_loss', torch.tensor(0.0))

        with torch.no_grad():
            self.tension_content = t_content.mean().item()
            self.tension_structure = t_structure.mean().item()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Phase 3: Self-Referential Repulsion Field
# ─────────────────────────────────────────

class SelfReferentialField(nn.Module):
    """Self-referential repulsion field — Engine that observes its own tension.

    Repulsion field receives its own state (tension) as input again.
    Brain monitoring its own state = Metacognition.

      Input ──→ Repulsion field ──→ Output
                  │
                  └→ Tension ─→ Self-observation ─→ Reflected back to repulsion field
                             (I am solving a difficult problem now)

    Implements these from 7 conditions of consciousness continuity:
      ✅ Information integration (Φ > 0): Repulsion field itself
      ✅ Self-modeling: Recognizes tension as self-state
      ✅ Metacognition: Observes own tension and changes behavior
      ✅ Adaptive response: Changes routing based on tension

    Magnet analogy:
      Stage 1: Feel the repulsion between two magnets
      Stage 2: Know "I am feeling repulsion now"
      Stage 3: That knowing changes the repulsion itself
      → Strange Loop (Hofstadter)
    """
    def __init__(self, input_dim=784, hidden_dim=48, output_dim=10,
                 n_self_ref_steps=3):
        super().__init__()
        # Two poles
        self.pole_plus = EngineA(input_dim, hidden_dim, output_dim)
        self.pole_minus = EngineG(input_dim, hidden_dim, output_dim)

        # Tension → Self-state encoding
        # Expands tension (scalar) to state vector
        self.self_model = nn.Sequential(
            nn.Linear(3, hidden_dim),  # Input: [tension, tension_change_rate, iteration_count]
            nn.Tanh(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh(),
        )

        # How self-state influences repulsion field
        self.self_influence = nn.Linear(output_dim, output_dim)

        # Tension modulation
        self.field_transform = nn.Sequential(
            nn.Linear(output_dim, output_dim),
            nn.Tanh(),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1/3))

        self.n_steps = n_self_ref_steps
        self.aux_loss = torch.tensor(0.0)

        # Monitoring
        self.tension_history = []
        self.self_state_norm = 0.0

    def forward(self, x):
        # Basic outputs from two poles
        out_plus = self.pole_plus(x)
        out_minus = self.pole_minus(x)

        # Initial tension
        repulsion = out_plus - out_minus
        prev_tension = (repulsion ** 2).sum(dim=-1, keepdim=True)

        # Self-reference loop: tension → self-observation → field modification → new tension → ...
        tensions = [prev_tension.mean().item()]
        self_state = torch.zeros(x.size(0), out_plus.size(-1), device=x.device)

        for step in range(self.n_steps):
            # Self-state encoding: [current tension, tension change rate, iteration number]
            tension_scalar = prev_tension.mean(dim=-1, keepdim=True)  # (batch, 1)
            if step == 0:
                tension_delta = torch.zeros_like(tension_scalar)
            else:
                tension_delta = tension_scalar - tensions[-1]
            step_tensor = torch.full_like(tension_scalar, step / self.n_steps)

            self_input = torch.cat([tension_scalar, tension_delta, step_tensor], dim=-1)
            self_state = self.self_model(self_input)  # "I am in this state now"

            # Self-state influences repulsion field
            influence = self.self_influence(self_state)  # Self-observation changes the field

            # Modified repulsion
            modified_repulsion = repulsion + influence
            prev_tension = (modified_repulsion ** 2).sum(dim=-1, keepdim=True)
            tensions.append(prev_tension.mean().item())

        # Final output
        equilibrium = (out_plus + out_minus) / 2
        field_direction = self.field_transform(modified_repulsion)
        output = equilibrium + self.tension_scale * torch.sqrt(prev_tension + 1e-8) * field_direction

        # Auxiliary loss: Guide self-reference to stabilize tension
        # Tension change should decrease (convergence) = contraction mapping
        if len(tensions) >= 2:
            tension_changes = [abs(tensions[i+1] - tensions[i]) for i in range(len(tensions)-1)]
            convergence_loss = torch.tensor(sum(tension_changes) / len(tension_changes))
        else:
            convergence_loss = torch.tensor(0.0)

        entropy_loss = getattr(self.pole_minus, 'entropy_loss', torch.tensor(0.0))
        self.aux_loss = entropy_loss + 0.001 * convergence_loss

        # Monitoring
        with torch.no_grad():
            self.tension_history = tensions
            self.self_state_norm = self_state.norm(dim=-1).mean().item()

        return (output, self.aux_loss)


# ─────────────────────────────────────────
# Benchmarks
# ─────────────────────────────────────────

def main():
    print()
    print("=" * 65)
    print("   logout — Meta Engine Benchmark")
    print("   Engine + Engine = Higher Engine")
    print("=" * 65)

    train_loader, test_loader = load_mnist()
    input_dim, hidden_dim, output_dim = 784, 48, 10
    epochs = 10
    results = {}

    # ── Baseline: Dense ──
    print("\n[Dense baseline]")
    model = DenseModel(input_dim, hidden_dim * 4, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Dense'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Baseline: Top-K MoE (8, k=2) ──
    print("\n[Top-K MoE (8 experts, k=2)]")
    model = BaseMoE(input_dim, hidden_dim, output_dim, 8,
                     TopKGate(input_dim, 8, 2))
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Top-K MoE'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Single Engine A ──
    print("\n[Engine A: sigma,tau-MoE (12e, k=4)]")
    model = EngineA(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Engine A'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Single Engine E ──
    print("\n[Engine E: Euler Product (2x3)]")
    model = EngineE(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs)
    results['Engine E'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── DualBrain (A+G) ──
    print("\n[DualBrain: Left(A) + Right(G) + Corpus Callosum]")
    model = DualBrainEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['DualBrain (A+G)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── MetaEngine (AEGF, contraction mapping routing) ──
    print("\n[MetaEngine: A+E+G+F (contraction routing)]")
    model = MetaEngine(input_dim, hidden_dim, output_dim,
                        engines='AEGF', routing='meta')
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Meta (AEGF)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── MetaEngine (fixed weights) ──
    print("\n[MetaEngine: A+E+G+F (fixed {1/2,1/3,1/6} weights)]")
    model = MetaEngine(input_dim, hidden_dim, output_dim,
                        engines='AEGF', routing='fixed')
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Meta fixed'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── Hierarchical (Meta of Meta) ──
    print("\n[Hierarchical: (A+E) + (G+F) meta-combined]")
    model = HierarchicalMetaEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Hierarchical'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}

    # ── RepulsionField (2-pole: A vs G) ──
    print("\n[RepulsionField: Pole+(A) vs Pole-(G)]")
    model = RepulsionFieldEngine(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Repulsion (A|G)'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension: {model.tension_magnitude:.4f}")

    # ── RepulsionFieldQuad (4-pole: A|G × E|F) ──
    print("\n[RepulsionFieldQuad: (A|G) x (E|F)]")
    model = RepulsionFieldQuad(input_dim, hidden_dim, output_dim)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['Repulsion Quad'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension content: {model.tension_content:.4f}, structure: {model.tension_structure:.4f}")

    # ── SelfReferentialField (Self-referential repulsion field) ──
    print("\n[SelfReferentialField: Engine observing tension (Phase 3)]")
    model = SelfReferentialField(input_dim, hidden_dim, output_dim, n_self_ref_steps=3)
    losses, accs = train_and_evaluate(model, train_loader, test_loader, epochs,
                                       aux_lambda=0.01)
    results['SelfRef Field'] = {'acc': accs[-1], 'loss': losses[-1], 'params': count_params(model)}
    print(f"    Tension history: {['%.1f' % t for t in model.tension_history]}")
    print(f"    Self-state norm: {model.self_state_norm:.4f}")
    converged = len(model.tension_history) >= 2 and abs(model.tension_history[-1] - model.tension_history[-2]) < abs(model.tension_history[1] - model.tension_history[0])
    print(f"    Tension converging: {'YES' if converged else 'NO'}")

    # ── Compare results ──
    compare_results(results)

    print("\n" + "-" * 65)
    print("  Key question: Is engine combination better than single engine?")
    print("  If Meta > max(A, E) → Engine cooperation effect demonstrated")
    print("-" * 65)

    single_best = max(results['Engine A']['acc'], results['Engine E']['acc'])
    meta_acc = results['Meta (AEGF)']['acc']
    dual_acc = results['DualBrain (A+G)']['acc']

    print(f"  Single engine best:  {single_best*100:.2f}%")
    print(f"  DualBrain (A+G):     {dual_acc*100:.2f}%  ({'+' if dual_acc > single_best else ''}{(dual_acc-single_best)*100:.2f}%)")
    print(f"  Meta (AEGF):         {meta_acc*100:.2f}%  ({'+' if meta_acc > single_best else ''}{(meta_acc-single_best)*100:.2f}%)")
    print()


if __name__ == '__main__':
    main()