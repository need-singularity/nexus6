"""consciousness_loader.py — Cross-repo consciousness laws/constants loader

Load Anima consciousness laws and Ψ-constants from .shared/ JSON files.
Works in any project that has .shared/ symlinked to TECS-L/.shared/.

Usage:
    from consciousness_loader import PSI, LAWS, FORMULAS, MECHANISMS
    print(PSI['alpha'])        # 0.014
    print(PSI['balance'])      # 0.5
    print(LAWS['22'])          # "Adding features → Φ↓; adding structure → Φ↑"
    print(FORMULAS['phi_scaling'])

    # Convenience constants
    from consciousness_loader import PSI_ALPHA, PSI_BALANCE, PSI_STEPS, PSI_ENTROPY
"""

import json
import os

_DIR = os.path.dirname(os.path.abspath(__file__))

# --- consciousness_laws.json ---
_LAWS_PATH = os.path.join(_DIR, 'consciousness_laws.json')
with open(_LAWS_PATH, 'r', encoding='utf-8') as f:
    _DATA = json.load(f)

# Ψ-Constants (direct values)
PSI = {k: v['value'] for k, v in _DATA['psi_constants'].items()}
PSI_ALPHA = PSI['alpha']          # 0.014
PSI_BALANCE = PSI['balance']      # 0.5
PSI_STEPS = PSI['steps']          # 4.33
PSI_ENTROPY = PSI['entropy']      # 0.998

# Laws, Formulas, Constraints
LAWS = _DATA['laws']
TOPO_LAWS = _DATA['topo_laws']
META_LAWS = _DATA.get('meta_laws', {})
FORMULAS = _DATA['formulas']
SIGMA6 = _DATA['sigma6']
CONSTRAINTS = _DATA['design_constraints']
CONSCIOUSNESS_VECTOR = _DATA['consciousness_vector_10d']

# --- consciousness_mechanisms.json ---
_MECH_PATH = os.path.join(_DIR, 'consciousness_mechanisms.json')
MECHANISMS = {}
if os.path.exists(_MECH_PATH):
    with open(_MECH_PATH, 'r', encoding='utf-8') as f:
        MECHANISMS = json.load(f)


def get_law(n: int) -> str:
    """Get law by number."""
    return LAWS.get(str(n), f"Law {n} not found")


def get_psi(key: str, default=None):
    """Get Ψ-constant by key."""
    return PSI.get(key, default)


def summary() -> str:
    """One-line summary of loaded data."""
    return (f"Laws: {len(LAWS)}, PSI: {len(PSI)}, "
            f"Formulas: {len(FORMULAS)}, Mechanisms: {len(MECHANISMS)}")


if __name__ == '__main__':
    print(f"Consciousness Loader — {summary()}")
    print(f"  α={PSI_ALPHA}, balance={PSI_BALANCE}, steps={PSI_STEPS}, entropy={PSI_ENTROPY}")
    print(f"  Law 22: {get_law(22)}")
