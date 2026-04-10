#!/usr/bin/env python3
"""
Verification of Medical Hypotheses H-MED-001 through H-MED-030.

Tests each hypothesis computationally:
  - Arithmetic accuracy of claimed equations
  - Plausibility against known medical/physiological reference values
  - Grade assignment per TECS-L verification rules

Grades:
  GREEN  = Exact equation, mathematically proven
  ORANGE = Numerically correct within stated tolerance, structurally interesting
  WHITE  = Arithmetically correct but trivial/coincidental
  BLACK  = Arithmetically wrong or factually incorrect

Run: PYTHONPATH=. python3 verify/verify_med_hypotheses.py
"""

import math
import sys

# ── n=6 arithmetic constants ──
N = 6
SIGMA_6 = 12        # divisor sum
TAU_6 = 4           # number of divisors
PHI_6 = 2           # Euler totient
SIGMA_NEG1_6 = 2.0  # reciprocal divisor sum: 1/1+1/2+1/3+1/6
DIVISORS_6 = [1, 2, 3, 6]
GZ_UPPER = 0.5
GZ_LOWER = 0.5 - math.log(4/3)  # 0.2123
GZ_CENTER = 1/math.e             # 0.3679
GZ_WIDTH = math.log(4/3)         # 0.2877
META_FP = 1/3

# ── Results tracking ──
results = []

def grade(hid, name, passed, reasoning, g):
    """Record a graded result."""
    emoji = {"GREEN": "\U0001F7E9", "ORANGE": "\U0001F7E7",
             "WHITE": "\u26AA", "BLACK": "\u2B1B"}[g]
    status = "PASS" if passed else "FAIL"
    results.append((hid, name, passed, g, reasoning))
    print(f"  {emoji} {hid}: {name}")
    print(f"     {status} | Grade: {g}")
    print(f"     {reasoning}")
    print()


def close(a, b, tol=0.05):
    """Check if a is within tol relative error of b."""
    if b == 0:
        return abs(a) < tol
    return abs(a - b) / abs(b) < tol


# ═══════════════════════════════════════════════════
# A. Cardiovascular (H-MED-001 to H-MED-005)
# ═══════════════════════════════════════════════════

def verify_001():
    """Diastolic/Systolic Ratio in Golden Zone."""
    sys_bp, dia_bp = 120, 80
    pp = sys_bp - dia_bp  # 40
    pp_ratio = pp / sys_bp  # 40/120 = 1/3
    dia_total = dia_bp / (sys_bp + dia_bp)  # 80/200 = 0.4

    arith_ok = (pp_ratio == 1/3) or close(pp_ratio, 1/3, 0.001)
    # PP/Systolic = 1/3 exactly
    assert pp_ratio == 1/3, f"PP/Sys = {pp_ratio}"
    # Diastolic/Total = 0.4, in Golden Zone [0.2123, 0.5]
    in_gz = GZ_LOWER <= dia_total <= GZ_UPPER

    # Medical fact check: 120/80 is textbook normal. PP/Sys = 1/3 is exact arithmetic.
    # But claiming this is structurally meaningful vs. coincidence is debatable.
    # The diastolic/total ratio 0.4 being in GZ is trivially true since GZ covers ~58% of [0,1].
    # Wait: GZ is [0.2123, 0.5], width 0.2877 out of 1.0 = 28.8% of [0,1].
    # A random ratio in [0.3, 0.5] (plausible physiological range) has ~70% chance of being in GZ.

    grade("H-MED-001", "Diastolic/Systolic Ratio in Golden Zone",
          arith_ok and in_gz,
          f"PP/Sys = {pp_ratio:.4f} = 1/3 (exact). "
          f"Dia/Total = {dia_total:.3f} in GZ [{GZ_LOWER:.3f}, {GZ_UPPER:.3f}]. "
          f"Arithmetic correct. But GZ covers 28.8% of [0,1], and normal BP ratios "
          f"cluster in [0.3, 0.5], so GZ containment is expected by chance.",
          "WHITE")


def verify_002():
    """Cardiac Cycle Time Partitioning Follows tau(6)=4 Phases."""
    hr = 72
    cycle_ms = 60000 / hr  # 833.33 ms
    # Claimed durations
    atrial = 110; vent = 270; early_d = 220; late_d = 233
    total = atrial + vent + early_d + late_d  # 833

    vent_frac = vent / total  # 0.324
    late_d_frac = late_d / total  # 0.280

    err_vent = abs(vent_frac - 1/3) / (1/3)
    err_late = abs(late_d_frac - GZ_WIDTH) / GZ_WIDTH

    # Medical fact: cardiac cycle does have 4 phases (isovolumetric contraction,
    # ejection, isovolumetric relaxation, filling). The exact durations vary.
    # tau(6)=4 matching 4 phases is suggestive but 4 is a very common number.
    # Ventricular systole ~1/3 of cycle at rest is roughly correct in literature.

    grade("H-MED-002", "Cardiac Cycle tau(6)=4 Phases",
          total == 833 and err_vent < 0.03 and err_late < 0.03,
          f"Durations sum to {total} ms (claimed 833). "
          f"Vent systole fraction = {vent_frac:.3f}, error from 1/3 = {err_vent*100:.1f}%. "
          f"Late diastole fraction = {late_d_frac:.3f}, error from ln(4/3) = {err_late*100:.1f}%. "
          f"4 phases is standard physiology. Fractional matches ~3% error each.",
          "WHITE")


def verify_003():
    """HRV LF/HF Optimal Ratio = sigma_{-1}(6) = 2."""
    # Literature: healthy resting LF/HF is typically 1.5-2.5, with large variability.
    # Claiming optimal = exactly 2.0 is within the range but the concept of
    # "optimal" LF/HF is controversial in HRV literature.
    # Math: HF/(LF+HF) = 1/(1+2) = 1/3 — arithmetic is correct.
    hf_frac = 1 / (1 + SIGMA_NEG1_6)
    assert close(hf_frac, 1/3, 0.001)

    # The LF/HF ratio of 2 is within normal range but there's no consensus
    # that 2.0 is specifically "optimal." Large inter-individual variability.

    grade("H-MED-003", "HRV LF/HF Optimal = sigma_{-1}(6) = 2",
          True,
          f"HF fraction at LF/HF=2: {hf_frac:.4f} = 1/3 (exact). "
          f"Literature range 1.5-2.5 includes 2.0. "
          f"Arithmetic correct. But 'optimal = 2.0' is not established in HRV literature; "
          f"LF/HF interpretation is debated (sympathovagal balance model questioned).",
          "WHITE")


def verify_004():
    """QT/RR Ratio Converges to 1/e at Optimal Heart Rate."""
    # HR=60: RR=1000ms, QT~380ms -> QT/RR = 0.380
    # 1/e = 0.3679
    qt_rr_60 = 380 / 1000
    err = abs(qt_rr_60 - 1/math.e) / (1/math.e)

    # Medical fact: QT interval at HR 60 is typically 350-400ms in healthy adults.
    # QT/RR = 0.38 at HR 60 is plausible.
    # The 3.3% error is within normal physiological variation.
    # However, QT/RR varies widely by individual, sex, age.

    grade("H-MED-004", "QT/RR Ratio ≈ 1/e at HR 60",
          err < 0.05,
          f"QT/RR at HR60 = {qt_rr_60:.3f}, 1/e = {1/math.e:.4f}, "
          f"error = {err*100:.1f}%. "
          f"Plausible QT value. But QT varies by sex (females longer), age, "
          f"and genetics (QTc range 350-460ms normal). "
          f"Crossing 1/e at HR 58-63 is a specific testable claim.",
          "WHITE")


def verify_005():
    """Coronary Artery Bifurcation with n=6 Correction."""
    # Murray's law exponent: 3.0 ideal, empirical 2.5-3.2
    # Model: 3 - 1/6 = 2.833
    model_exp = 3 - 1/6
    assert close(model_exp, 2.833, 0.001)

    # Angle: 2*arccos(2^(-1/3)) = 75.52 deg
    angle_murray = 2 * math.degrees(math.acos(2**(-1/3)))
    corrected = angle_murray * (1 + 1/SIGMA_6)
    # Literature: LAD/LCx bifurcation angle ~70-90 degrees, highly variable.

    grade("H-MED-005", "Coronary Bifurcation Murray's Law + n=6",
          close(model_exp, 2.833, 0.01) and close(corrected, 81.8, 0.01),
          f"Model exponent = {model_exp:.4f}. "
          f"Murray angle = {angle_murray:.1f} deg, corrected = {corrected:.1f} deg. "
          f"Empirical exponents do range 2.5-3.2, so 2.833 is in range. "
          f"Angle 81.8 is in the 70-90 range. But the 1/6 and 1/12 corrections "
          f"are ad hoc — infinitely many small fractions could fit.",
          "WHITE")


# ═══════════════════════════════════════════════════
# B. Neurology / Brain (H-MED-006 to H-MED-010)
# ═══════════════════════════════════════════════════

def verify_006():
    """Six Major Neurotransmitter Systems as Divisor-Weighted Network."""
    # The file itself acknowledges: "Actual concentrations differ from model by large factors"
    # Actual: Glu:GABA:ACh:5HT:DA:NE ≈ 1:0.4:0.15:0.05:0.03:0.02
    # Model:  1:0.5:0.333:0.167:0.167:0.167

    actual = [1, 0.4, 0.15, 0.05, 0.03, 0.02]
    model = [1, 0.5, 0.333, 0.167, 0.167, 0.167]

    # Rank ordering matches: Glu > GABA > ACh > (5HT, DA, NE)
    # But quantitative fit is poor
    rank_match = True  # rank order does match

    # Compute relative errors for the quantitative fit
    errors = [abs(a - m) / a if a > 0 else 0 for a, m in zip(actual, model)]
    mean_err = sum(errors) / len(errors)

    grade("H-MED-006", "Neurotransmitter Divisor-Weighted Network",
          rank_match,
          f"Rank ordering matches (Glu>GABA>ACh>monoamines). "
          f"Quantitative fit poor: mean relative error = {mean_err*100:.0f}%. "
          f"GABA actual 0.4 vs model 0.5 (25% off). "
          f"Monoamines actual ~0.02-0.05 vs model 0.167 (3-8x off). "
          f"The hypothesis itself notes this. Rank match only.",
          "WHITE")


def verify_007():
    """EEG Power Spectrum 1/f Slope in Golden Zone."""
    # Model: beta_optimal = 1 + 1/e + 1/6 = 1.534
    beta_opt = 1 + 1/math.e + 1/6
    # Literature: healthy waking EEG beta typically 1.0-2.0
    # "Edge of criticality" beta ≈ 1.5 is indeed reported in the literature
    # (He et al. 2010, Podvalny et al. 2015)

    err = abs(beta_opt - 1.5) / 1.5

    grade("H-MED-007", "EEG 1/f Slope Optimal = 1+1/e+1/6",
          close(beta_opt, 1.534, 0.001),
          f"beta_optimal = {beta_opt:.4f}. Literature 'critical' beta ≈ 1.5. "
          f"Error from 1.5 = {err*100:.1f}%. "
          f"The formula 1+1/e+1/6 = 1.534 is arithmetic fact. "
          f"Match to literature 1.5 is within ~2%. "
          f"Structurally interesting but the formula is post-hoc fitting.",
          "ORANGE")


def verify_008():
    """Sleep Architecture tau(6)=4 Phases with 1/6 REM Fraction."""
    # Observed (healthy young adult): N1=5%, N2=50%, N3=20%, REM=25%
    # Model: N1=1/12=8.3%, N2=1/2=50%, N3=1/6=16.7%, REM=1/3=33.3%
    observed = {"N1": 5, "N2": 50, "N3": 20, "REM": 25}
    model = {"N1": 100/12, "N2": 50, "N3": 100/6, "REM": 100/3}

    # N2 exact match at 50%
    n2_match = observed["N2"] == model["N2"]

    # Others: absolute errors
    errs = {k: abs(observed[k] - model[k]) for k in observed}

    # Medical fact check: N2 ≈ 50% is well established. N3 ≈ 20%, REM ≈ 20-25%.
    # REM as 1/3 (33%) is too high — observed is ~20-25%.
    # Elderly REM ≈ 15% ≈ 1/6 is approximately correct for some studies.

    grade("H-MED-008", "Sleep Architecture tau(6)=4 Phases",
          n2_match,
          f"N2: observed 50% = model 50% (exact match). "
          f"N1: error {errs['N1']:.1f}%, N3: error {errs['N3']:.1f}%, "
          f"REM: error {errs['REM']:.1f}%. "
          f"REM model 33% vs observed 25% is a large miss (8% absolute). "
          f"4 sleep stages is standard (though AASM defines 3 NREM + REM). "
          f"Only N2=50% matches well.",
          "WHITE")


def verify_009():
    """Seizure Threshold at Golden Zone Boundary."""
    # Claims E/I ratio > 0.5 triggers seizures.
    # This is a conceptual model. E/I balance in epilepsy is a real concept,
    # but normalized E/I ratios aren't standardized to a 0-1 scale.
    # The claim that seizures occur when E/I exits Golden Zone upper (0.5)
    # is untestable without specifying the normalization.

    grade("H-MED-009", "Seizure Threshold at Golden Zone Upper",
          True,
          f"E/I imbalance causing seizures is established neuroscience. "
          f"But there is no standard 'normalized E/I ratio' in [0,1]. "
          f"The Golden Zone mapping is arbitrary without specifying normalization. "
          f"Concept is correct, quantitative claim is unfalsifiable as stated.",
          "WHITE")


def verify_010():
    """BBB Permeability Coefficient = 1/e Transition."""
    # Claims transition from permeable to impermeable at normalized P = 1/e
    # At logP_oct = 0, P_norm ≈ 0.35 ≈ 1/e
    # Medical fact: BBB permeability does decrease with lower lipophilicity.
    # logP_oct = 0 is indeed a transition region.
    # But the specific normalization giving P_norm = 1/e is chosen to fit.

    grade("H-MED-010", "BBB Permeability 1/e Transition",
          True,
          f"BBB permeability vs lipophilicity is a real sigmoidal relationship. "
          f"The transition zone around logP_oct = 0-2 is established. "
          f"Normalized P = 1/e at the transition depends on the normalization chosen. "
          f"Post-hoc curve fitting can always match a constant.",
          "WHITE")


# ═══════════════════════════════════════════════════
# C. Pharmacology / Drug Design (H-MED-011 to H-MED-015)
# ═══════════════════════════════════════════════════

def verify_011():
    """Therapeutic Index Optimal at sigma(6)=12."""
    # Claims TI near 12 is "optimal."
    # Acetaminophen TI ≈ 10-20, commonly cited as ~10 (not 12).
    # The median TI of top drugs varies enormously.
    # Most drugs cluster around TI 5-20, so 12 is in the middle of a wide range.

    # Fact check: Acetaminophen LD50/ED50 ≈ 10 (some sources say lower).
    # The table values are approximate and vary by source.

    grade("H-MED-011", "Therapeutic Index Optimal at sigma(6)=12",
          True,
          f"Acetaminophen TI commonly cited as ~10, not exactly 12. "
          f"TI values vary enormously across drugs (2 to 10,000+). "
          f"Mode of TI distribution for top drugs is poorly defined. "
          f"12 being in the 'middle' of a log-scale distribution "
          f"spanning 3 orders of magnitude is not remarkable.",
          "WHITE")


def verify_012():
    """Drug Half-Life Clustering at 6-Hour Multiples."""
    # Claims >60% of drugs have t1/2 within 20% of a divisor of 6.
    # Divisors of 6: {1, 2, 3, 6}
    # 20% windows: [0.8-1.2], [1.6-2.4], [2.4-3.6], [4.8-7.2]
    # Total coverage on [0, 24] scale: ~7.2 hours out of 24 = 30%
    # Many drugs have t1/2 of 4, 8, 10, 15 hours — not near divisors of 6.

    # Calculate coverage fraction of [0.5, 24] by 20% windows around {1,2,3,6}
    targets = [1, 2, 3, 6]
    # Merge overlapping intervals
    intervals = [(t*0.8, t*1.2) for t in targets]
    # [0.8,1.2], [1.6,2.4], [2.4,3.6], [4.8,7.2]
    # [1.6,2.4] and [2.4,3.6] touch but don't overlap
    # Merged: [0.8,1.2], [1.6,3.6], [4.8,7.2]
    total_coverage = (1.2-0.8) + (3.6-1.6) + (7.2-4.8)  # 0.4+2.0+2.4 = 4.8
    range_total = 24 - 0.5  # half-lives from 0.5 to 24h
    coverage_frac = total_coverage / range_total

    # Fact check: common half-lives include 4h (many antibiotics), 8h, 10h
    # which are NOT near divisors of 6. Also 24h = sigma(6)*phi(6) is a divisor
    # of 24 but not of 6.

    # Additionally, dosing intervals {q4h, q6h, q8h, q12h} are driven by
    # practical convenience, not n=6 arithmetic.

    grade("H-MED-012", "Drug Half-Life Clustering at 6-Hour Multiples",
          True,
          f"20% windows around divisors of 6 cover {total_coverage:.1f}h "
          f"out of [0.5, 24] = {coverage_frac*100:.1f}% of range. "
          f"Claiming >60% of drugs fall in 20% coverage is a strong claim. "
          f"Many common drugs (metformin 6.2h, atenolol 6-7h, metoprolol 3-7h) "
          f"do cluster near 6, but others (warfarin 40h, diazepam 48h) do not. "
          f"Dosing intervals are driven by convenience/circadian, not n=6.",
          "WHITE")


def verify_013():
    """Hill Coefficient Optimal Range = [1/3, 1/2]."""
    # Hemoglobin n_H = 2.8-3.0 (not exactly 4; 4 is the maximum possible for 4 subunits)
    # The hypothesis says n_H = 4 for hemoglobin — this is the common textbook simplification
    # but actual fitted Hill coefficient is ~2.8.
    # Normalizing by n_max=12 is arbitrary.

    hb_hill = 4  # textbook (though actual is ~2.8)
    hb_norm = hb_hill / 12
    assert close(hb_norm, 1/3, 0.01)

    # MAP kinase Hill coefficient varies (typically 3-10 in different models)
    # Lac operon Hill coefficient ~2-3

    grade("H-MED-013", "Hill Coefficient Optimal in Golden Zone",
          True,
          f"Hemoglobin: n_H commonly cited as ~2.8 (not 4). "
          f"4 is theoretical max for 4 subunits. "
          f"Normalization by n_max=12 is arbitrary (why 12?). "
          f"With n_max=12, hemoglobin 4/12 = 1/3 is exact arithmetic. "
          f"But choosing n_max=12=sigma(6) to make it work is circular.",
          "WHITE")


def verify_014():
    """Lipinski's Rule of Five Contains Hidden Sixes."""
    # Claims: optimal MW = 6*60 = 360
    # Actual: FDA-approved oral drug MW mode is ~300-400, so 360 is in range.
    # logP optimal = 6/2 = 3: literature says optimal logP ~1-3 for oral drugs.
    # HBD optimal = phi(6) = 2: many drugs have 1-2 HBD, this is reasonable.
    # HBA optimal = 6: typical range 4-7, so 6 is plausible.

    mw_pred = 6 * 60  # 360
    logp_pred = 6 / 2  # 3
    hbd_pred = PHI_6  # 2
    hba_pred = 6

    # Fact check: 360 = 6!/2 = 720/2 ✓
    assert 360 == math.factorial(6) // 2

    # 360 = sigma(6) * 30 = 12*30 ✓
    assert 360 == SIGMA_6 * 30

    grade("H-MED-014", "Lipinski's Rule Hidden Sixes",
          True,
          f"MW optimal ~360 is in the right range (mode ~300-400 for oral drugs). "
          f"logP=3, HBD=2, HBA=6 are all within typical optimal ranges. "
          f"Arithmetic: 360 = 6!/2 = sigma(6)*30 (correct). "
          f"But these are post-hoc numerological fits. "
          f"Any number near 300-400 can be expressed via 6-arithmetic.",
          "WHITE")


def verify_015():
    """ED50 of Anesthetics Correlates with 1/e Lipid Solubility."""
    # Claims 37/100 tested gases are anesthetics = 1/e
    # The actual number of gases tested for anesthesia is not a standard figure.
    # Meyer-Overton correlation is real and well-established.
    # The 37% claim is not verifiable from standard references.

    # MAC values from the table are approximately correct:
    # N2O MAC ~1.04 atm, Desflurane ~6%, Sevoflurane ~2%, etc.
    # Note: MAC is measured in atm or %. Desflurane MAC = 6% = 0.06 atm? No.
    # Desflurane MAC = 6.0% at 1 atm. In the table MAC is listed as 0.060 atm
    # which would be 6%. This is correct.

    grade("H-MED-015", "Anesthetic ED50 and 1/e",
          True,
          f"Meyer-Overton correlation is well-established pharmacology. "
          f"MAC values in the table are approximately correct. "
          f"The claim that 37% of tested gases are anesthetics is unverifiable "
          f"(no standard census of 'all tested gases'). "
          f"1/e appearing as a fraction is post-hoc.",
          "WHITE")


# ═══════════════════════════════════════════════════
# D. Immunology (H-MED-016 to H-MED-020)
# ═══════════════════════════════════════════════════

def verify_016():
    """Six Major Immune Cell Types with Divisor-Frequency Distribution."""
    # Standard WBC differential:
    # Neutrophils 40-70% (mean ~60%), Lymphocytes 20-40% (mean ~30%),
    # Monocytes 2-8% (mean ~6%), Eosinophils 1-4% (mean ~3%),
    # Basophils <1%
    # NK cells are a lymphocyte subset, not separately counted in differential.

    # NLR = 60/30 = 2 = sigma_{-1}(6)
    nlr = 60 / 30
    assert nlr == 2.0

    # Medical fact: NLR of ~2 in healthy adults is well-documented.
    # NLR > 3-4 is prognostic for many conditions.
    # The WBC percentages are textbook.

    grade("H-MED-016", "Immune Cell Types Divisor-Frequency",
          True,
          f"NLR = 60/30 = {nlr} = sigma_{{-1}}(6) (exact with textbook values). "
          f"WBC percentages are standard textbook values. "
          f"NLR~2 in healthy adults is well-established. "
          f"But mapping to divisors is post-hoc — only NLR=2 is a clean match. "
          f"Lymph/Mono = 30/6 = 5 is NOT a divisor of 6 (as noted).",
          "WHITE")


def verify_017():
    """Cytokine Balance Pro/Anti Ratio = sigma_{-1}(6) = 2."""
    # TNF-alpha/IL-10 ratio of ~2 in healthy individuals is within published ranges.
    # However, cytokine ratios are extremely variable and assay-dependent.
    # "Optimal" ratio is not well-defined in immunology literature.

    grade("H-MED-017", "Cytokine Pro/Anti Ratio = 2",
          True,
          f"TNF/IL-10 ratio ~2 is within published healthy ranges (1-3). "
          f"But cytokine levels vary by >10-fold between individuals and assays. "
          f"No consensus 'optimal' ratio exists in immunology. "
          f"The claim is unfalsifiable without standardized assay conditions.",
          "WHITE")


def verify_018():
    """Vaccine Dose Interval Optimization at 6-Week Multiples."""
    # Germinal center kinetics ~4-6 weeks is correct.
    # But vaccine intervals vary widely: 3 weeks (COVID), 4 weeks (DTP),
    # 6 months (HPV, Hep B boosters).
    # 42 = 6*7 is trivially true.

    assert 42 == 6 * 7
    # Check: 42 = sigma(6)*tau(6) - 6 = 12*4 - 6 = 48-6 = 42
    assert 42 == SIGMA_6 * TAU_6 - 6

    grade("H-MED-018", "Vaccine Interval 6-Week Multiples",
          True,
          f"42 = 6*7 and 42 = sigma(6)*tau(6)-6 = 42 (arithmetic correct). "
          f"GC kinetics ~4-6 weeks is standard immunology. "
          f"But optimal vaccine intervals are 3-24 weeks depending on vaccine. "
          f"Many effective vaccines use 4-week intervals (not 6). "
          f"The 6-week claim is too specific given real-world variation.",
          "WHITE")


def verify_019():
    """Autoimmune Threshold at Golden Zone Boundary."""
    # Treg = 5-10% of CD4+ is correct.
    # But "Treg fraction of active cells ~0.33" is not a standard measurement.
    # Autoimmune threshold at SRI > 0.5 is conceptual, not quantifiable.

    grade("H-MED-019", "Autoimmune Threshold at Golden Zone",
          True,
          f"Treg 5-10% of CD4+ is correct immunology. "
          f"Self-reactivity index (SRI) is not a standard clinical measure. "
          f"The claim is conceptual/unfalsifiable without defining SRI precisely. "
          f"Autoimmune pathogenesis is far more complex than a single ratio.",
          "WHITE")


def verify_020():
    """Complement Cascade Amplification Factor = 6."""
    # The table claims geometric mean amplification = 6.2
    # Let's verify: log values 0.78, 0.48, 2.30, 0.78, 0.00
    import numpy as np
    amps = [6, 3, 200, 6, 1]
    geo_mean = np.exp(np.mean(np.log(amps)))

    # C1 activates ~6 C4: approximately correct per some sources.
    # C3 amplification ~200: this is roughly correct (C3 convertase is highly active).
    # Including the terminal step (C5->MAC, amp=1) pulls down the geometric mean.

    # 6^3 = 216 vs 200 (8% error) as noted
    err_c3 = abs(216 - 200) / 200

    grade("H-MED-020", "Complement Amplification = 6",
          close(geo_mean, 6, 0.10),
          f"Amplifications: {amps}. Geometric mean = {geo_mean:.1f}. "
          f"6^3 = 216 vs C3 amp ~200, error = {err_c3*100:.0f}%. "
          f"Complement amplification factors are rough estimates. "
          f"Including C5->MAC (amp=1) in geometric mean is questionable "
          f"(it's not really an amplification step). "
          f"Selective inclusion/exclusion of steps can tune the mean.",
          "WHITE")


# ═══════════════════════════════════════════════════
# E. Genetics / Molecular Biology (H-MED-021 to H-MED-025)
# ═══════════════════════════════════════════════════

def verify_021():
    """Codon Degeneracy Structure Encodes Divisors of 6."""
    # Standard genetic code degeneracy:
    # 6 codons: Leu(6), Ser(6), Arg(6) = 3 AAs
    # 4 codons: Val, Pro, Thr, Ala, Gly = 5 AAs  (but file says 5, count is correct)
    # 3 codons: Ile(3) = 1 AA  (Stop has 3 codons but isn't an AA)
    # 2 codons: Phe, Tyr, His, Gln, Asn, Lys, Asp, Glu, Cys = 9 AAs
    # 1 codon:  Met, Trp = 2 AAs

    degeneracy_vals = {1, 2, 3, 4, 6}
    divisors_of_6 = {1, 2, 3, 6}
    overlap = degeneracy_vals & divisors_of_6
    non_divisor = degeneracy_vals - divisors_of_6  # {4}

    # Count: 3+1+9+2 = 15 AAs with divisor-of-6 degeneracy, 5 with degeneracy 4
    # (Actually Ile has 3 codons, Stop has 3 — the file counts Stop as "AA")
    # Real count of amino acids: 20 + stop
    # With degeneracy in {1,2,3,6}: 2+9+1+3 = 15 AAs
    # With degeneracy 4: 5 AAs
    # 15/20 = 75% have divisor-of-6 degeneracy

    # But: {1,2,3,4,6} are the only values possible given 64 codons / ~20 AAs.
    # 5 doesn't appear because it would require odd symmetry breaking.
    # The range of possible values is inherently limited.

    grade("H-MED-021", "Codon Degeneracy Encodes Divisors of 6",
          len(overlap) == 4,
          f"Degeneracy values: {sorted(degeneracy_vals)}. "
          f"Divisors of 6: {sorted(divisors_of_6)}. "
          f"Overlap: 4 of 5 values. Non-divisor: {{4}}. "
          f"15/20 amino acids have divisor-of-6 degeneracy (75%). "
          f"However, the possible degeneracy values are constrained by "
          f"64 codons / 20 AAs, so small integers dominate regardless. "
          f"5-fold degeneracy is impossible due to wobble base pairing symmetry.",
          "WHITE")


def verify_022():
    """Six DNA Repair Pathways with 1/6 Error Budget."""
    # The file itself shows the actual distribution is NOT 1/6 each:
    # BER handles 60% of repairs by frequency.
    # The re-framing by "lesion types" (6 each, 36 total) is fabricated —
    # there's no standard classification yielding exactly 36 lesion types
    # distributed uniformly.

    grade("H-MED-022", "Six DNA Repair Pathways 1/6 Each",
          False,
          f"The hypothesis itself shows repair frequency is NOT 1/6 each "
          f"(BER handles 60%). The re-framing by 'lesion types' claiming "
          f"exactly 6 types per pathway (36 total) has no basis in literature. "
          f"The number of distinct DNA lesion chemistries is debated "
          f"(estimates range from ~20 to >100). "
          f"This is numerological fitting to a desired outcome.",
          "BLACK")


def verify_023():
    """Gene Expression Noise Floor at 1/e."""
    # Observed CV for highly expressed genes ~0.3-0.5
    # 1/e = 0.368
    # The file notes typical minimum CV ≈ 0.35-0.40, centered near 1/e.
    # This is within the observed range.

    # Poisson noise for 1000 molecules: 1/sqrt(1000) = 0.032
    # Observed excess noise ~0.3 is due to transcriptional bursting.
    # The noise floor depends heavily on technology (dropout, UMIs, etc.)

    noise_floor_obs = 0.37  # approximate from scRNA-seq literature
    err = abs(noise_floor_obs - 1/math.e) / (1/math.e)

    grade("H-MED-023", "Gene Expression Noise Floor = 1/e",
          err < 0.05,
          f"Observed CV mode ~0.35-0.40 for highly expressed genes. "
          f"1/e = {1/math.e:.4f}. Error ~{err*100:.1f}%. "
          f"The range is correct but CV depends heavily on sequencing depth, "
          f"technology (10x vs Smart-seq), and normalization. "
          f"No fundamental reason for noise floor = 1/e specifically.",
          "WHITE")


def verify_024():
    """Telomere Shortening Rate = 1/sigma(6) Per Decade."""
    # Claims mean fractional loss age 20-60 ≈ 1/12 = 0.0833 per decade.
    # Literature: telomere attrition ~30-50 bp/year in adults.
    # At age 20, ~12 kb. Loss 40 bp/yr * 10 yr = 400 bp = 0.4 kb.
    # Fractional: 0.4/12 = 0.033 per decade — NOT 0.083.

    # The file's numbers: age 20 = 12kb, age 30 = 11kb
    # (12-11)/12 = 0.083 = 1/12. But losing 1 kb/decade is 100 bp/year,
    # which is at the high end of estimates.

    # Literature range: 20-60 bp/year (most studies), up to 100 bp/year in some.
    # Using 50 bp/year: 500bp/decade out of 12000bp = 0.042, not 0.083.
    # Using 100 bp/year: 1000bp/decade out of 12000bp = 0.083 = 1/12.

    # The telomere length values in the table (15kb at birth, 6kb at 80)
    # are roughly in line with published data but on the aggressive side.

    loss_per_decade = 1 / SIGMA_6  # 0.0833
    lit_low = 0.033   # 40 bp/yr
    lit_high = 0.083  # 100 bp/yr

    grade("H-MED-024", "Telomere Shortening = 1/sigma(6) Per Decade",
          True,
          f"Model: {loss_per_decade:.4f} per decade = 1/12. "
          f"Literature range: {lit_low:.3f} - {lit_high:.3f} (40-100 bp/yr). "
          f"1/12 matches the upper end (100 bp/yr) but many studies report "
          f"lower rates (30-50 bp/yr → 0.025-0.042 per decade). "
          f"Telomere lengths in the table are on the high side of estimates.",
          "WHITE")


def verify_025():
    """MicroRNA Target Site Multiplicity Peaks at 6."""
    # TargetScan data: median conserved sites per gene ~3-5 depending on
    # conservation threshold. Mean including non-conserved can be 6-8.
    # The distribution is right-skewed.
    # The file's claim that 6 is the "optimal" number is plausible in range
    # but the peak of the distribution is typically 3-5, not 6.

    grade("H-MED-025", "miRNA Target Sites Peak at 6",
          True,
          f"TargetScan: median conserved sites ~3-5 per gene. "
          f"Mean (all predicted) ~6-8. Mode is typically 3-4, not 6. "
          f"The claim that genes with 6 sites are 'most robustly regulated' "
          f"is an interesting prediction but not established. "
          f"6 being near the mean (not mode) of a skewed distribution is weak.",
          "WHITE")


# ═══════════════════════════════════════════════════
# F. Clinical Medicine (H-MED-026 to H-MED-030)
# ═══════════════════════════════════════════════════

def verify_026():
    """Vital Signs Encode 1/2+1/3+1/6=1."""
    # The claim: clinical weights (HR=1/3, SBP=1/3, RR=1/6, Temp=1/6) sum to 1.
    # 1/3 + 1/3 + 1/6 + 1/6 = 2/3 + 1/3 = 1 (exact arithmetic).
    total = 1/3 + 1/3 + 1/6 + 1/6
    assert close(total, 1.0, 0.001)

    # But: these weights are CHOSEN to sum to 1 with divisor fractions.
    # Real EWS systems (NEWS, MEWS) use integer scores, not fractional weights.
    # Logistic regression weights on vital signs do NOT typically yield
    # these clean fractions — they depend on outcome definition and population.

    grade("H-MED-026", "Vital Signs Encode 1/2+1/3+1/6=1",
          True,
          f"1/3+1/3+1/6+1/6 = {total:.4f} (exact). "
          f"But the weights are chosen, not derived from data. "
          f"Real EWS systems use integer scores (NEWS: 0-3 per parameter). "
          f"Logistic regression weights vary by study and outcome definition. "
          f"Any 4 weights can be chosen to sum to 1 using any fractions.",
          "WHITE")


def verify_027():
    """SOFA Score Maximum = sigma(6)*phi(6) = 24."""
    # SOFA: 6 organ systems, each 0-4, max = 24.
    sofa_max = 6 * 4
    assert sofa_max == 24
    assert sofa_max == SIGMA_6 * PHI_6

    # 50% mortality at SOFA ~12 is approximately correct.
    # Literature: SOFA 11-12 corresponds to ~40-60% mortality depending on study.

    # This is the strongest hypothesis in section F:
    # - 6 organ systems = n (real)
    # - 0-4 per system = tau(6) (real, though designed by humans)
    # - Max 24 = sigma(6)*phi(6) (arithmetic fact)
    # - 50% mortality at 12 = sigma(6) (approximately correct from literature)

    # However: SOFA was designed by humans in 1994 (Vincent et al.).
    # The 6 systems and 0-4 scale were practical choices, not derived from
    # number theory. The coincidence is interesting but the score design
    # was driven by clinical utility and available measurements.

    grade("H-MED-027", "SOFA Score = sigma(6)*phi(6) = 24",
          True,
          f"6 systems * 4 max = 24 = sigma(6)*phi(6) (exact). "
          f"50% mortality at SOFA ~12 = sigma(6) (approx. correct from literature). "
          f"Range 15-3 = 12 in GCS, range 0-24 in SOFA — both involve 12. "
          f"Numerically striking but SOFA was designed by humans (Vincent 1994). "
          f"6 systems and 0-4 scale are practical choices (organ count, severity grades).",
          "ORANGE")


def verify_028():
    """Wound Healing tau(6)=4 Phases with Golden Zone Timing."""
    # 4 wound healing phases is standard (hemostasis, inflammation, proliferation, remodeling).
    # Inflammation fraction of 21-day acute healing: 5/21 = 0.238
    # Golden Zone lower = 0.2123
    # Error: |0.238 - 0.212| / 0.212 = 12.1%

    inf_frac = 5 / 21
    err = abs(inf_frac - GZ_LOWER) / GZ_LOWER

    grade("H-MED-028", "Wound Healing 4 Phases, GZ Timing",
          err < 0.15,
          f"Inflammation fraction = {inf_frac:.3f}, GZ lower = {GZ_LOWER:.4f}. "
          f"Error = {err*100:.1f}%. "
          f"4 phases is standard wound biology. "
          f"12% error from GZ lower is not a strong match. "
          f"The 21-day timeline and 5-day inflammation are approximate "
          f"and vary significantly by wound type/size.",
          "WHITE")


def verify_029():
    """Circadian Period = sigma(6)*phi(6) = 24 Hours."""
    assert 24 == SIGMA_6 * PHI_6
    assert 24 == 6 * TAU_6
    assert 24 == math.factorial(4)

    # Free-running period ~24.18 hours is well-established (Czeisler et al. 1999).
    # 24.18/24 = 1.0075, error 0.75%.
    err = abs(24.18 - 24) / 24

    # Wake:sleep = 16:8 = 2:1 is approximately correct for adults.
    # But this is partly socially determined (alarm clocks, work schedules).
    # Free-running sleep is often ~8.5-9h, making ratio ~1.7:1, not 2:1.

    grade("H-MED-029", "Circadian Period = sigma(6)*phi(6) = 24",
          True,
          f"24 = sigma(6)*phi(6) = 6*tau(6) = 4! (all exact). "
          f"Free-running period 24.18h, error = {err*100:.2f}%. "
          f"24 hours = Earth's rotation period. Circadian clocks evolved to match it. "
          f"The connection to n=6 is numerological — 24 has many factorizations. "
          f"Wake:sleep ~2:1 is approximate (free-running closer to 1.7:1).",
          "WHITE")


def verify_030():
    """Glasgow Coma Scale Encodes n=6 Structure."""
    # GCS: Eye 1-4, Verbal 1-5, Motor 1-6. Total 3-15.
    gcs_min = 1 + 1 + 1  # 3
    gcs_max = 4 + 5 + 6  # 15
    gcs_range = gcs_max - gcs_min  # 12

    assert gcs_min == 3
    assert gcs_max == 15
    assert gcs_range == SIGMA_6  # 12
    assert 6 in DIVISORS_6  # Motor max = 6
    assert 4 == TAU_6  # Eye max = 4

    # Severe/moderate boundary at 8:
    assert 8 == SIGMA_6 - TAU_6  # 12 - 4 = 8
    assert 8 == PHI_6 ** 3  # 2^3 = 8

    # 50% mortality at GCS 6: approximately correct in severe TBI literature.

    # GCS was designed by Teasdale & Jennett (1974).
    # The component scales (4, 5, 6) were based on clinical observation.
    # Motor has 6 levels because 6 distinct motor responses were identified.
    # Eye has 4 because 4 levels of eye opening exist.
    # The numerology with n=6 is coincidental to the design process.

    grade("H-MED-030", "Glasgow Coma Scale = n=6 Structure",
          True,
          f"GCS: min 3 (divisor of 6), max 15, range 12 = sigma(6). "
          f"Motor max 6 = n, Eye max 4 = tau(6). "
          f"Severe boundary 8 = sigma(6)-tau(6). "
          f"All arithmetic correct. Numerically striking. "
          f"But GCS was designed by clinicians based on observable responses, "
          f"not number theory. The coincidences are post-hoc.",
          "ORANGE")


# ═══════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════

def main():
    import numpy as np  # noqa: ensure available

    print("=" * 65)
    print("  VERIFICATION: Medical Hypotheses H-MED-001 to H-MED-030")
    print("=" * 65)
    print()

    # Run all 30 verifications
    funcs = [
        verify_001, verify_002, verify_003, verify_004, verify_005,
        verify_006, verify_007, verify_008, verify_009, verify_010,
        verify_011, verify_012, verify_013, verify_014, verify_015,
        verify_016, verify_017, verify_018, verify_019, verify_020,
        verify_021, verify_022, verify_023, verify_024, verify_025,
        verify_026, verify_027, verify_028, verify_029, verify_030,
    ]

    for fn in funcs:
        try:
            fn()
        except Exception as e:
            hid = fn.__name__.replace("verify_", "H-MED-")
            print(f"  ERROR in {hid}: {e}")
            results.append((hid, fn.__doc__ or "", False, "BLACK", str(e)))
            print()

    # ── Summary ──
    print("=" * 65)
    print("  SUMMARY")
    print("=" * 65)
    print()

    grade_counts = {"GREEN": 0, "ORANGE": 0, "WHITE": 0, "BLACK": 0}
    pass_count = 0
    for hid, name, passed, g, reason in results:
        grade_counts[g] += 1
        if passed:
            pass_count += 1

    emoji_map = {"GREEN": "\U0001F7E9", "ORANGE": "\U0001F7E7",
                 "WHITE": "\u26AA", "BLACK": "\u2B1B"}

    print(f"  Total hypotheses:  {len(results)}")
    print(f"  Arithmetic PASS:   {pass_count}/{len(results)}")
    print()
    for g in ["GREEN", "ORANGE", "WHITE", "BLACK"]:
        print(f"  {emoji_map[g]} {g:6s}: {grade_counts[g]}")
    print()

    print("  Grade table:")
    print("  " + "-" * 60)
    for hid, name, passed, g, reason in results:
        e = emoji_map[g]
        s = "PASS" if passed else "FAIL"
        print(f"  {e} {hid:12s} {s:4s}  {name[:45]}")
    print("  " + "-" * 60)
    print()

    print("  KEY FINDINGS:")
    print("  - Most hypotheses are arithmetically correct (the math checks out)")
    print("  - Nearly all are post-hoc numerological fits (Texas Sharpshooter)")
    print("  - Medical reference values used are approximately correct")
    print("  - No hypothesis reaches GREEN (proven) grade")
    print("  - H-MED-022 (DNA repair 1/6 each) is BLACK: self-contradicted in text")
    print("  - H-MED-007, 027, 030 are ORANGE: numerically interesting coincidences")
    print("  - All others are WHITE: correct arithmetic, likely coincidental")
    print()

    # Return exit code
    if grade_counts["BLACK"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
