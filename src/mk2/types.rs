//! Core types: Rational, Sector
//!
//! # Design decisions
//!
//! - Rational: (i128, i128) custom, gcd-reduced
//! - Sector: fixed enum + Custom(String) dynamic extension

use serde::{Deserialize, Serialize};
use std::fmt;

/// Rational number p/q (reduced to lowest terms, q > 0).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Rational {
    num: i128,
    den: i128,
}

impl Rational {
    pub fn new(num: i128, den: i128) -> Self {
        assert!(den != 0, "zero denominator");
        let (mut n, mut d) = (num, den);
        if d < 0 {
            n = -n;
            d = -d;
        }
        let g = gcd(n.unsigned_abs() as i128, d);
        Self { num: n / g, den: d / g }
    }

    pub fn from_int(n: i128) -> Self {
        Self { num: n, den: 1 }
    }

    pub fn zero() -> Self {
        Self { num: 0, den: 1 }
    }

    pub fn one() -> Self {
        Self { num: 1, den: 1 }
    }

    pub fn num(&self) -> i128 {
        self.num
    }

    pub fn den(&self) -> i128 {
        self.den
    }

    pub fn to_f64(&self) -> f64 {
        self.num as f64 / self.den as f64
    }

    pub fn reciprocal(&self) -> Self {
        assert!(self.num != 0, "reciprocal of zero");
        Self::new(self.den, self.num)
    }
}

fn gcd(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.abs(), b.abs());
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    if a == 0 { 1 } else { a }
}

impl std::ops::Add for Rational {
    type Output = Self;
    fn add(self, rhs: Self) -> Self {
        Self::new(self.num * rhs.den + rhs.num * self.den, self.den * rhs.den)
    }
}

impl std::ops::Sub for Rational {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self {
        Self::new(self.num * rhs.den - rhs.num * self.den, self.den * rhs.den)
    }
}

impl std::ops::Mul for Rational {
    type Output = Self;
    fn mul(self, rhs: Self) -> Self {
        Self::new(self.num * rhs.num, self.den * rhs.den)
    }
}

impl std::ops::Div for Rational {
    type Output = Self;
    fn div(self, rhs: Self) -> Self {
        assert!(rhs.num != 0, "division by zero");
        Self::new(self.num * rhs.den, self.den * rhs.num)
    }
}

impl fmt::Display for Rational {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.den == 1 {
            write!(f, "{}", self.num)
        } else {
            write!(f, "{}/{}", self.num, self.den)
        }
    }
}

/// Physics sector classification.
///
/// Fixed core variants + Custom(String) for dynamic extension.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Sector {
    Strong,       // color/quark charges
    Electroweak,  // θ_W, θ_C, W/Z mass ratios
    Cosmology,    // Ω_m, Ω_Λ, Ω_b, Ω_DM
    Primordial,   // BBN era (Y_p, η)
    Unknown,
    Custom(String),
}

impl fmt::Display for Sector {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Strong => write!(f, "strong"),
            Self::Electroweak => write!(f, "electroweak"),
            Self::Cosmology => write!(f, "cosmology"),
            Self::Primordial => write!(f, "primordial"),
            Self::Unknown => write!(f, "unknown"),
            Self::Custom(s) => write!(f, "custom:{}", s),
        }
    }
}

impl Sector {
    /// Tolerance for this sector (relative error) when classifying.
    pub fn tolerance(&self) -> f64 {
        match self {
            Self::Strong => 0.001,       // 0.1%
            Self::Electroweak => 0.02,   // 2%
            Self::Cosmology => 0.05,     // 5%
            Self::Primordial => 0.10,    // 10%
            Self::Unknown => 0.10,
            Self::Custom(_) => 0.05,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rational_basic() {
        let a = Rational::new(4, 15);
        let b = Rational::new(24, 35);
        let c = Rational::new(1, 21);
        // cosmic density sum: 4/15 + 24/35 + 1/21 = 1
        let sum = a + b + c;
        assert_eq!(sum, Rational::one());
    }

    #[test]
    fn rational_reduce() {
        let r = Rational::new(8, 35);
        assert_eq!(r.num(), 8);
        assert_eq!(r.den(), 35);
        let r2 = Rational::new(48, 210); // should reduce to 8/35
        assert_eq!(r2, r);
    }

    #[test]
    fn rational_arithmetic() {
        let r = Rational::new(2, 6); // reduces to 1/3
        assert_eq!(r, Rational::new(1, 3));
        assert_eq!(r.to_f64(), 1.0 / 3.0);

        let inv = r.reciprocal();
        assert_eq!(inv, Rational::new(3, 1));
    }

    #[test]
    fn sector_tolerance() {
        assert_eq!(Sector::Strong.tolerance(), 0.001);
        assert_eq!(Sector::Cosmology.tolerance(), 0.05);
        assert_eq!(Sector::Custom("test".into()).tolerance(), 0.05);
    }
}
