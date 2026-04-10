"""ph-training: Automatic model training pipeline powered by Persistent Homology"""

__version__ = "0.1.0"

from .engine import PureFieldEngine
from .ph import (
    compute_h0, compute_h0_from_distance_matrix, get_merges,
    PHMonitor, LayerPHMonitor, TensionPHMonitor,
)
from .trainer import PHTrainer, TrainingResult
from .data import load_data, DATASETS

__all__ = [
    "PureFieldEngine",
    "compute_h0",
    "get_merges",
    "PHMonitor",
    "LayerPHMonitor",
    "TensionPHMonitor",
    "compute_h0_from_distance_matrix",
    "PHTrainer",
    "TrainingResult",
    "load_data",
    "DATASETS",
]
