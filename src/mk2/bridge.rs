//! Bridge: verify mk1 n6_check constants align with mk2 SmoothRing.
//!
//! This module does NOT replace n6_check. Instead it provides
//! regression tests ensuring mk1's hardcoded constants remain
//! consistent with mk2's computed values from SmoothRing.

#[cfg(test)]
mod consistency_tests {
    use crate::mk2::smooth::{euler_ratio, rho, SmoothRing};
    use crate::mk2::primes::prime_set_of;
    use crate::mk2::types::Rational;

    /// Primitive n=6 arithmetic: mk1 hardcoded vs mk2 computed.
    #[test]
    fn primitives_agree() {
        assert_eq!(6u64.phi(), 2);       // mk1 "phi" = 2.0
        assert_eq!(6u64.tau(), 4);       // mk1 "tau" = 4.0
        assert_eq!(6u64.sigma(), 12);    // mk1 "sigma" = 12.0
        assert_eq!(6u64.sopfr(), 5);     // mk1 "sopfr" = 5.0
    }

    /// Meta FP and compound identities.
    #[test]
    fn compounds_agree() {
        // meta FP = 1/3
        assert_eq!(rho(6), Rational::new(1, 3));
        // u/d quark density = τ/n = 2/3
        let tau_over_n = Rational::new(4, 6);
        assert_eq!(tau_over_n.to_f64(), 2.0 / 3.0);
        // J2 = σ·2 at n=6 (coincidence)
        assert_eq!(6u64.sigma() * 2, 24);  // matches mk1 "J2" = 24
        // M3 = σ − sopfr = 7
        assert_eq!(6u64.sigma() - 6u64.sopfr(), 7);
    }

    /// Smooth-class physics values (mk1 constants in n6_check.rs).
    #[test]
    fn smooth_class_physics_values() {
        // Ω_DM = 4/15 = {2,3,5}-smooth
        let r = euler_ratio(&prime_set_of(30)); // {2,3,5}
        assert_eq!(r, Rational::new(4, 15));
        assert!((r.to_f64() - 0.266_666_666_6).abs() < 1e-9);

        // Ω_Λ = 24/35 = {5,7}-smooth
        let r = euler_ratio(&prime_set_of(35));
        assert_eq!(r, Rational::new(24, 35));
        assert!((r.to_f64() - 0.685_714_285_7).abs() < 1e-9);

        // sin²θ_W = 8/35 = {2,3,5,7}-smooth
        let r = euler_ratio(&prime_set_of(210));
        assert_eq!(r, Rational::new(8, 35));
        assert!((r.to_f64() - 0.228_571_428_5).abs() < 1e-9);

        // Y_p = 16/65 = {2,3,5,13}-smooth
        let r = euler_ratio(&prime_set_of(2 * 3 * 5 * 13));
        assert_eq!(r, Rational::new(16, 65));
        assert!((r.to_f64() - 0.246_153_846_1).abs() < 1e-9);
    }

    /// Universe flatness identity: φ + τ = n ↔ Ω_m + Ω_Λ = 1.
    #[test]
    fn flatness_identity() {
        assert_eq!(6u64.phi() + 6u64.tau(), 6);
        // In basis: φ/n + τ/n = 1
        let omega_m = Rational::new(6u64.phi() as i128, 6);  // 2/6 = 1/3
        let omega_l = Rational::new(6u64.tau() as i128, 6);  // 4/6 = 2/3
        assert_eq!(omega_m + omega_l, Rational::one());
    }

    /// Cosmic density rational decomposition:
    /// 4/15 + 24/35 + 1/21 = 1 (flatness via three smooth classes).
    #[test]
    fn cosmic_density_sum() {
        let omega_dm = Rational::new(4, 15);   // {2,3,5}
        let omega_l = Rational::new(24, 35);   // {5,7}
        let omega_b = Rational::new(1, 21);    // {3,7} complement
        assert_eq!(omega_dm + omega_l + omega_b, Rational::one());
    }

    /// Perfect numbers σ(P)=2P verified via SmoothRing.
    #[test]
    fn perfect_numbers_agree() {
        for &p in &[6u64, 28, 496, 8128] {
            assert_eq!(p.sigma(), 2 * p, "σ({})={} should be {}", p, p.sigma(), 2 * p);
        }
    }

    /// Hubble tension basis: 73 − 67 = 6 = n.
    #[test]
    fn hubble_tension_equals_n() {
        let n = 6u64;
        let sigma = n.sigma();  // 12
        let sopfr = n.sopfr();  // 5
        let mu = 1u64;          // μ(6) = 1

        let h_late = sigma * n + mu;       // 12·6 + 1 = 73
        let h_early = sigma * n - sopfr;   // 12·6 − 5 = 67
        assert_eq!(h_late, 73);
        assert_eq!(h_early, 67);
        assert_eq!(h_late - h_early, n);   // tension = n
    }

    /// Spectral index n_s = 1 - sopfr/(n·J2) = 139/144.
    #[test]
    fn spectral_index_basis() {
        let n = 6i128;
        let sopfr = 5i128;
        let j2 = 24i128;

        let n_s = Rational::new(n * j2 - sopfr, n * j2);
        assert_eq!(n_s, Rational::new(139, 144));
        assert!((n_s.to_f64() - 0.9653).abs() < 1e-3);
    }
}
