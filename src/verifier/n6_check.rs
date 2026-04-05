//! n6_check — mk2 흡수 완료.
//!
//! 모든 상수가 mk2 SmoothRing에서 계산됨 (하드코딩 제거).
//! API 완전 호환: `n6_match(f64)`, `n6_exact_ratio(&[f64])`.
//!
//! 추가 기능 (mk1에 없던 것):
//! - `meta_iterate`: 축소사상 반복 → 부동점 수렴
//! - `meta_converges_to_third`: 1/3 수렴 판정

use crate::mk2::compat::{n6_match_mk2, n6_exact_ratio_mk2};

/// Match a value against n=6 constants (mk2 SmoothRing computed).
/// Returns (constant_name, match_quality) where quality is:
///   1.0 = EXACT (< 0.1% error)
///   0.8 = CLOSE (< 5% error)
///   0.5 = WEAK  (< 10% error)
///   0.0 = NONE
#[inline]
pub fn n6_match(value: f64) -> (&'static str, f64) {
    n6_match_mk2(value)
}

/// Fraction of values that match EXACT (quality == 1.0) against any n=6 constant.
#[inline]
pub fn n6_exact_ratio(values: &[f64]) -> f64 {
    n6_exact_ratio_mk2(values)
}

/// Contraction map iteration: I_{k+1} = α·I_k + β, returns (final, steps, converged).
pub fn meta_iterate(initial: f64, alpha: f64, beta: f64, tol: f64, max_steps: usize) -> (f64, usize, bool) {
    let mut val = initial;
    for step in 0..max_steps {
        let next = alpha * val + beta;
        if (next - val).abs() < tol {
            return (next, step + 1, true);
        }
        val = next;
    }
    (val, max_steps, false)
}

/// Check whether a value converges to 1/3 under standard contraction (α=0.7, β=0.1).
pub fn meta_converges_to_third(value: f64, tolerance: f64) -> bool {
    let (fp, _, converged) = meta_iterate(value, 0.7, 0.1, 1e-12, 200);
    converged && (fp - 1.0 / 3.0).abs() < tolerance
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mk2_powered_basics() {
        let (name, q) = n6_match(12.0);
        assert_eq!(name, "sigma");
        assert_eq!(q, 1.0);

        let (name, q) = n6_match(6.0);
        assert_eq!(name, "n");
        assert_eq!(q, 1.0);

        let (name, q) = n6_match(24.0);
        assert_eq!(name, "J2");
        assert_eq!(q, 1.0);
    }

    #[test]
    fn test_exact_ratio() {
        let ratio = n6_exact_ratio(&[6.0, 12.0, 9999.0]);
        assert!((ratio - 2.0 / 3.0).abs() < 0.01);
    }

    #[test]
    fn test_meta_converges() {
        assert!(meta_converges_to_third(0.0, 0.01));
        assert!(meta_converges_to_third(1.0, 0.01));
        assert!(meta_converges_to_third(0.5, 0.01));
    }

    #[test]
    fn test_no_match() {
        let (_, q) = n6_match(9999.0);
        assert_eq!(q, 0.0);

        let (_, q) = n6_match(0.0);
        assert_eq!(q, 0.0);
    }

    #[test]
    fn test_smooth_class_physics() {
        let (name, q) = n6_match(0.266_666_666_6);
        assert!(q >= 1.0, "Ω_DM should EXACT: {} q={}", name, q);

        let (name, q) = n6_match(0.685_714_285_7);
        assert!(q >= 1.0, "Ω_Λ should EXACT: {} q={}", name, q);
    }
}
