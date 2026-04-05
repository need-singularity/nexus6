/// N=6 constant definition: (name, value)
/// 확장: verified_constants.jsonl에서 수집한 2600+ 검증 상수 중 핵심 닫힌식 통합.
const N6_CONSTANTS: &[(&str, f64)] = &[
    // ── Primitives (n=6의 기본값) ──────────────────────────
    ("n", 6.0),
    ("sigma", 12.0),
    ("phi", 2.0),
    ("tau", 4.0),
    ("J2", 24.0),
    ("sopfr", 5.0),
    ("mu", 1.0),
    // ── Simple combinations ─────────────────────────────
    ("sigma-phi", 10.0),
    ("sigma-tau", 8.0),
    ("sigma-mu", 11.0),
    ("sigma+phi", 14.0),
    ("sigma+tau", 16.0),
    ("sigma+n", 18.0),
    ("sigma*tau", 48.0),
    ("sigma*n", 72.0),
    ("sigma*phi", 24.0),
    ("sigma*J2", 288.0),
    ("sigma*sopfr", 60.0),
    ("sigma^2", 144.0),
    ("sigma^3", 1728.0),
    ("phi^tau", 16.0),
    ("phi^sopfr", 32.0),
    ("sopfr^2", 25.0),
    ("sopfr^3", 125.0),
    ("J2^2", 576.0),
    ("J2+tau", 28.0),        // σ(12) = 28
    ("J2-tau", 20.0),
    ("tau^2", 16.0),
    ("n^2", 36.0),
    ("n^3", 216.0),
    // ── Ratios / fractions ──────────────────────────────
    ("tau^2/sigma", 1.333_333_333),
    ("n/phi", 3.0),
    ("n/tau", 1.5),
    ("sigma/n", 2.0),
    ("sigma/tau", 3.0),
    ("J2/sigma", 2.0),
    ("J2/n", 4.0),
    ("sopfr/tau", 1.25),
    ("pi/n", 0.523_598_776),
    ("pi/sigma", 0.261_799_388),
    // ── Transcendentals (verified closed-forms) ────────
    ("pi", 3.141_592_653_589_793),
    ("e", 2.718_281_828_459_045),
    ("sqrt_phi", 1.414_213_562_373_095),    // √2
    ("sqrt_n/phi", 1.732_050_807_568_877),  // √3
    ("sqrt_sopfr", 2.236_067_977_499_79),   // √5
    ("sqrt_n", 2.449_489_742_783_178),      // √6
    ("sqrt_sigma", 3.464_101_615_137_754),  // √12
    ("ln_phi", 0.693_147_180_559_945),      // ln(2)
    ("ln(4/3)", 0.287_682_072_451_780),
    ("ln_sigma-phi", 2.302_585_092_994_045),// ln(10)
    // ── Compound closed-forms (derived) ─────────────────
    ("(1+sqrt_sopfr)/phi", 1.618_033_988_749_895), // golden ratio
    ("1+sqrt_phi", 2.414_213_562_373_095),         // silver ratio
    ("1/e", 0.367_879_441_171_442),
    ("pi^2/n", 1.644_934_066_848_226),             // ζ(2)
    ("pi*phi", 6.283_185_307_179_586),             // 2π
    ("pi^phi/n", 1.644_934_066_848_226),           // π²/6
    // ── n=6 관련 특수값 (perfect number family) ────────
    ("M3", 7.0),             // 2³-1 = σ-sopfr = n+μ
    ("P2", 28.0),            // 2nd perfect number = σ(12)
    ("P3", 496.0),           // 3rd perfect number = φ^τ · (2^sopfr-1)
    ("P4", 8128.0),          // 4th perfect number = 2⁶ · 127 = n·(2^M3-1) · σ^0
    ("2^sopfr-1", 31.0),     // Mersenne-5 (P3 prime)
    ("2^M3-1", 127.0),       // Mersenne-7 (P4 prime)
    // ── Physical exponents (dimensionless) ──────────────
    ("J2-mu", 23.0),         // Avogadro exponent mantissa
    ("-J2+mu", -23.0),       // Boltzmann exponent
];

/// Match a value against n=6 constants.
/// Returns (constant_name, match_quality) where quality is:
///   1.0 = EXACT (< 0.1% error)
///   0.8 = CLOSE (< 5% error)
///   0.5 = WEAK  (< 10% error)
///   0.0 = NONE
pub fn n6_match(value: f64) -> (&'static str, f64) {
    if value == 0.0 {
        return ("none", 0.0);
    }

    let mut best_name = "none";
    let mut best_quality = 0.0_f64;
    let mut best_error = f64::MAX;

    for &(name, constant) in N6_CONSTANTS {
        if constant == 0.0 {
            continue;
        }
        let error = ((value - constant) / constant).abs();

        let quality = if error < 0.001 {
            1.0 // EXACT
        } else if error < 0.05 {
            0.8 // CLOSE
        } else if error < 0.10 {
            0.5 // WEAK
        } else {
            0.0
        };

        // Pick highest quality; break ties by smallest error (skip quality=0)
        if quality > 0.0
            && (quality > best_quality || (quality == best_quality && error < best_error))
        {
            best_name = name;
            best_quality = quality;
            best_error = error;
        }
    }

    (best_name, best_quality)
}

/// Fraction of values that match EXACT (quality == 1.0) against any n=6 constant.
pub fn n6_exact_ratio(values: &[f64]) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let exact_count = values.iter().filter(|&&v| n6_match(v).1 >= 1.0).count();
    exact_count as f64 / values.len() as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_constants_count() {
        assert!(N6_CONSTANTS.len() >= 20, "Need 20+ constants, got {}", N6_CONSTANTS.len());
    }
}
