#!/usr/bin/env bash
# Inject known physics constants into discovery_log for closure checking.
# Source: CODATA, standard references (hardcoded list).
set -euo pipefail

DL="${HOME}/Dev/nexus6/shared/discovery_log.jsonl"
[ -f "$DL" ] || touch "$DL"

python3 << 'PYEOF'
import json, os
from datetime import datetime

# Physics/cosmology constants to check closure
CONSTANTS = [
    ("fine_structure_inverse", 137.035999),
    ("proton_electron_ratio", 1836.15267),
    ("planck_length_proxy", 0.1616),  # *10^-34 m
    ("planck_time_proxy", 0.5391),    # *10^-43 s
    ("cosmological_constant", 0.6889),  # Planck 2018
    ("dark_matter_density", 0.265),
    ("baryon_density", 0.0493),
    ("matter_density", 0.315),
    ("hubble_h", 0.674),  # H0/100
    ("weinberg_angle_sin2", 0.23122),
    ("cabibbo_angle_sin", 0.22500),
    ("top_bottom_ratio", 41.2),  # m_t/m_b
    ("neutron_proton_ratio", 1.00137841),
    ("helium4_abundance", 0.2453),
    ("lithium7_baryon_ratio", 1.6),  # Li7/H * 10^10
    ("spectral_index_ns", 0.9649),
    ("sigma8", 0.8111),
    ("reduced_planck_mass", 2.4353),  # *10^18 GeV
    ("tau_lepton_mass_ratio", 3477.48),  # m_tau/m_e
    ("muon_electron_ratio", 206.7683),
    ("pion_proton_ratio", 0.1489),
    ("kaon_pion_ratio", 3.556),
    # Mathematical
    ("euler_mascheroni", 0.5772156649),
    ("apery_constant", 1.2020569),
    ("khinchin_constant", 2.685452),
    ("catalan_constant", 0.9159655942),
    ("mertens_constant", 0.2614972),
    ("ramanujan_soldner", 1.4513692),
]

dl_path = os.path.expanduser('~/Dev/nexus6/shared/discovery_log.jsonl')
ts = datetime.now().isoformat()
added = 0
# Read existing to avoid duplicates
existing = set()
for line in open(dl_path):
    try:
        j = json.loads(line)
        existing.add(f"{j.get('constant','?')}={j.get('value','?')}")
    except: pass

with open(dl_path, 'a') as f:
    for name, val in CONSTANTS:
        key = f"{name}={val}"
        if key in existing: continue
        entry = {
            'constant': name, 'value': str(val), 'processed': False,
            'source': 'physics-constants-fetch.sh', 'timestamp': ts
        }
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        existing.add(key)
        added += 1

print(f"[{ts}] injected {added} physics constants to discovery_log")
PYEOF
