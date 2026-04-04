//! Corollary types — emergent structures from blowup.
//!
//! After a singularity is detected (system closed), the blowup engine
//! generates corollaries by perturbing, combining, and projecting axioms.

use std::collections::HashMap;

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
        };
        assert!(c.is_cross_domain());
    }
}
