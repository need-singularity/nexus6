"""PureFieldEngine — Dual-engine repulsion field model.

output = tension_scale * sqrt(tension) * direction
tension = |engine_A(x) - engine_G(x)|^2
direction = normalize(engine_A(x) - engine_G(x))
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class PureFieldEngine(nn.Module):
    """Dual-engine repulsion field model.

    Two independent engines (A and G) produce representations.
    The output emerges from the repulsion between them —
    not from either engine alone, but from the space between.

    Args:
        input_dim: Input dimension (MNIST=784, CIFAR=3072)
        hidden_dim: Hidden layer dimension
        output_dim: Number of output classes
        dropout: Dropout rate
    """

    def __init__(self, input_dim=784, hidden_dim=128, output_dim=10, dropout=0.3):
        super().__init__()
        self.engine_a = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
        self.engine_g = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )
        self.tension_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x):
        """Forward pass.

        Args:
            x: Input tensor (B, input_dim)

        Returns:
            output: Classification logits (B, output_dim)
            tension: Tension scalar per sample (B,)
        """
        out_a = self.engine_a(x)
        out_g = self.engine_g(x)

        repulsion = out_a - out_g
        tension = (repulsion ** 2).mean(dim=-1, keepdim=True)
        direction = F.normalize(repulsion, dim=-1)

        output = self.tension_scale * torch.sqrt(tension + 1e-8) * direction

        return output, tension.squeeze(-1)

    def extract_directions(self, x):
        """Extract direction vectors and magnitudes (no grad).

        Args:
            x: Input tensor (B, input_dim)

        Returns:
            direction: Unit direction vectors (B, output_dim)
            magnitude: Tension magnitude per sample (B,)
        """
        with torch.no_grad():
            a = self.engine_a(x)
            g = self.engine_g(x)
            rep = a - g
            direction = F.normalize(rep, dim=-1)
            magnitude = torch.sqrt((rep ** 2).mean(dim=-1) + 1e-8)
        return direction, magnitude
