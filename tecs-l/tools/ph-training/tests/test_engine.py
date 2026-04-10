"""Tests for PureFieldEngine."""

import torch
import pytest
from ph_training import PureFieldEngine


def test_forward_shape():
    model = PureFieldEngine(input_dim=784, hidden_dim=64, output_dim=10)
    x = torch.randn(32, 784)
    output, tension = model(x)
    assert output.shape == (32, 10)
    assert tension.shape == (32,)


def test_tension_nonnegative():
    model = PureFieldEngine(input_dim=100, hidden_dim=32, output_dim=5)
    x = torch.randn(16, 100)
    _, tension = model(x)
    assert (tension >= 0).all()


def test_direction_unit_norm():
    model = PureFieldEngine(input_dim=100, hidden_dim=32, output_dim=5)
    x = torch.randn(16, 100)
    direction, _ = model.extract_directions(x)
    norms = torch.norm(direction, dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)


def test_tension_scale_learnable():
    model = PureFieldEngine(input_dim=100, hidden_dim=32, output_dim=5)
    assert model.tension_scale.requires_grad
    x = torch.randn(8, 100)
    y = torch.randint(0, 5, (8,))
    output, _ = model(x)
    loss = torch.nn.functional.cross_entropy(output, y)
    loss.backward()
    assert model.tension_scale.grad is not None
