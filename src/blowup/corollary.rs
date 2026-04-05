//! Corollary types — emergent structures from blowup.
//!
//! After a singularity is detected (system closed), the blowup engine
//! generates corollaries by perturbing, combining, and projecting axioms.

use std::collections::HashMap;

use crate::mk2::primes::PrimeSet;
use crate::mk2::types::Sector;

/// How a corollary was generated.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CorollaryType {
    /// Direct logical consequence of axioms (A ∧ B → C).
    Deduction,
    /// Cross-domain transfer (axiom from domain X applied to domain Y).
    DomainTransfer,
    /// Symmetry breaking: perturb a symmetry in the axiom set.
    SymmetryBreaking,
    /// Bifurcation: small parameter change → qualitatively different structure.
    Bifurcation,
    /// Composition: combine two corollaries to get a third.
    Composition,
    /// Projection: project axioms onto a lower-dimensional subspace.
    Projection,
    /// Dual: take the categorical dual of a corollary.
    Dual,
}

/// A single emergent corollary.
#[derive(Debug, Clone)]
pub struct Corollary {
    /// Human-readable name.
    pub name: String,
    /// How it was generated.
    pub corollary_type: CorollaryType,
    /// The axioms used to derive this corollary.
    pub source_axioms: Vec<String>,
    /// The emergent property/value.
    pub expression: String,
    /// Confidence score (0.0..1.0) — how strongly the corollary follows.
    pub confidence: f64,
    /// Numerical signature if applicable.
    pub signature: HashMap<String, f64>,
    /// Which domain this corollary extends into.
    pub target_domain: String,
    /// Is this corollary itself a potential new axiom?
    pub is_axiom_candidate: bool,
    /// mk2: physics sector classification (None = not yet classified).
    pub mk2_sector: Option<Sector>,
    /// mk2: prime set of signature values.
    pub mk2_prime_set: Option<PrimeSet>,
    /// mk2: classification confidence (0.0..1.0).
    pub mk2_confidence: Option<f64>,
}

impl Corollary {
    /// Check if this corollary is non-trivial (not just restating an axiom).
    pub fn is_nontrivial(&self) -> bool {
        self.confidence > 0.1 && !self.expression.is_empty()
    }

    /// Check if this corollary opens a new domain (not same as source).
    pub fn is_cross_domain(&self) -> bool {
        matches!(
            self.corollary_type,
            CorollaryType::DomainTransfer | CorollaryType::Projection
        )
    }

    /// Run mk2 classify_v2 on this corollary's expression + signature values.
    /// Enriches mk2_sector, mk2_prime_set, mk2_confidence in-place.
    pub fn classify_mk2(&mut self) {
        let values: Vec<f64> = self.signature.values().copied().collect();
        let text = format!("{} {}", self.name, self.expression);

        // Build prime_set from signature values (only small rationals)
        let mut ps = PrimeSet::empty();
        for &v in &values {
            if v.is_finite() && v.abs() > 1e-10 && v.abs() < 1e6 {
                // Try small denominators only (smooth-class relevant range)
                for den in &[1u64, 2, 3, 5, 6, 7, 15, 21, 35, 105, 210] {
                    let num = (v * *den as f64).round() as i128;
                    if num > 0 && ((num as f64 / *den as f64) - v).abs() < 1e-6 {
                        for (p, _) in crate::mk2::primes::factorize(num.unsigned_abs() as u64) {
                            ps.insert(p);
                        }
                        for (p, _) in crate::mk2::primes::factorize(*den) {
                            ps.insert(p);
                        }
                        break;
                    }
                }
            }
        }

        let sectors = crate::mk2::classify_v2::default_sectors();
        let result = crate::mk2::classify_v2::classify_v2(&text, &values, &ps, &sectors);

        self.mk2_sector = Some(result.sector);
        self.mk2_prime_set = Some(ps);
        self.mk2_confidence = Some(result.confidence);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_corollary_nontrivial() {
        let c = Corollary {
            name: "bridge_theorem".into(),
            corollary_type: CorollaryType::Deduction,
            source_axioms: vec!["P1".into(), "P3".into()],
            expression: "G = D × P / I".into(),
            confidence: 0.95,
            signature: HashMap::new(),
            target_domain: "growth".into(),
            is_axiom_candidate: false,
            mk2_sector: None,
            mk2_prime_set: None,
            mk2_confidence: None,
        };
        assert!(c.is_nontrivial());
        assert!(!c.is_cross_domain());
    }

    #[test]
    fn test_cross_domain() {
        let c = Corollary {
            name: "transferred".into(),
            corollary_type: CorollaryType::DomainTransfer,
            source_axioms: vec!["sigma".into()],
            expression: "σ=12 in music theory".into(),
            confidence: 0.7,
            signature: HashMap::new(),
            target_domain: "music".into(),
            is_axiom_candidate: true,
            mk2_sector: None,
            mk2_prime_set: None,
            mk2_confidence: None,
        };
        assert!(c.is_cross_domain());
    }

    #[test]
    fn test_classify_mk2_cosmology() {
        let mut sig = HashMap::new();
        sig.insert("Omega_Lambda".into(), 0.6857);
        let mut c = Corollary {
            name: "dark_energy".into(),
            corollary_type: CorollaryType::Deduction,
            source_axioms: vec!["Omega_Lambda".into()],
            expression: "Hubble dark energy fraction Ω_Λ = 24/35".into(),
            confidence: 0.9,
            signature: sig,
            target_domain: "physics".into(),
            is_axiom_candidate: false,
            mk2_sector: None,
            mk2_prime_set: None,
            mk2_confidence: None,
        };
        c.classify_mk2();
        assert!(c.mk2_sector.is_some());
        assert!(c.mk2_confidence.unwrap() > 0.0);
        // "Hubble" + "dark energy" keywords → cosmology
        assert_eq!(c.mk2_sector.unwrap(), Sector::Cosmology);
    }

    #[test]
    fn test_classify_mk2_unknown() {
        let mut c = Corollary {
            name: "random".into(),
            corollary_type: CorollaryType::Dual,
            source_axioms: vec![],
            expression: "abstract nonsense".into(),
            confidence: 0.3,
            signature: HashMap::new(),
            target_domain: "math".into(),
            is_axiom_candidate: false,
            mk2_sector: None,
            mk2_prime_set: None,
            mk2_confidence: None,
        };
        c.classify_mk2();
        assert_eq!(c.mk2_sector.unwrap(), Sector::Unknown);
    }
}
