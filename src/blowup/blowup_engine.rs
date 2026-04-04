//! Blowup Engine — the main emergence driver.
//!
//! Pipeline:
//!   1. Detect singularity (system closed, metrics frozen)
//!   2. Extract axiom set (minimal independent generators)
//!   3. Apply blowup operators:
//!      a. Pairwise axiom interaction → deductions
//!      b. Domain transfer → cross-domain corollaries
//!      c. Symmetry perturbation → bifurcations
//!      d. Projection to subspaces → dimensional reduction corollaries
//!      e. Dual construction → categorical duals
//!      f. Composition of generated corollaries → second-order emergence
//!   4. Filter: n6_check each corollary, keep consensus 3+
//!   5. Feed surviving corollaries back as new scan targets (recursive blowup)
//!
//! This is the "point → expansion" engine. Once Ouroboros saturates,
//! BlowupEngine takes over to generate emergent structure.

use std::collections::HashMap;

use super::corollary::{Corollary, CorollaryType};
use super::singularity::{Singularity, SingularityDetector};

/// Configuration for the blowup engine.
#[derive(Debug, Clone)]
pub struct BlowupConfig {
    /// Maximum corollaries to generate per blowup cycle.
    pub max_corollaries: usize,
    /// Minimum confidence to keep a corollary.
    pub min_confidence: f64,
    /// Maximum recursive depth (blowup of blowup of blowup...).
    pub max_depth: usize,
    /// Domains to attempt transfer into.
    pub transfer_domains: Vec<String>,
    /// Singularity detection config.
    pub singularity_detector: SingularityDetector,
}

impl Default for BlowupConfig {
    fn default() -> Self {
        Self {
            max_corollaries: 216, // 6³ — large enough for depth 2–3
            min_confidence: 0.15,
            max_depth: 6, // n=6
            transfer_domains: vec![
                "physics".into(),
                "mathematics".into(),
                "information".into(),
                "biology".into(),
                "consciousness".into(),
                "architecture".into(),
            ],
            singularity_detector: SingularityDetector::default(),
        }
    }
}

/// Result of a blowup cycle.
#[derive(Debug, Clone)]
pub struct BlowupResult {
    /// The singularity that was blown up.
    pub singularity: Option<Singularity>,
    /// Generated corollaries.
    pub corollaries: Vec<Corollary>,
    /// Corollaries that passed validation.
    pub validated: Vec<Corollary>,
    /// How many recursive levels were explored.
    pub depth_reached: usize,
    /// Corollaries that are axiom candidates (could close a new system).
    pub new_axiom_candidates: Vec<Corollary>,
    /// Total emergence count across all depths.
    pub total_emergences: usize,
}

/// The main blowup engine.
pub struct BlowupEngine {
    config: BlowupConfig,
}

impl BlowupEngine {
    pub fn new(config: BlowupConfig) -> Self {
        Self { config }
    }

    pub fn with_defaults() -> Self {
        Self::new(BlowupConfig::default())
    }

    /// Run blowup on a detected singularity.
    /// Returns all emergent corollaries.
    pub fn blowup(&self, singularity: &Singularity) -> BlowupResult {
        let mut all_corollaries = Vec::new();
        let mut depth = 0;

        // Current axiom set to blow up
        let mut current_axioms = singularity.axioms.clone();
        let mut current_metrics = singularity.metrics.clone();

        while depth < self.config.max_depth {
            let cycle_corollaries = self.blowup_cycle(&current_axioms, &current_metrics, depth);

            if cycle_corollaries.is_empty() {
                break; // No more emergence possible
            }

            // Filter by confidence
            let validated: Vec<Corollary> = cycle_corollaries
                .into_iter()
                .filter(|c| c.confidence >= self.config.min_confidence)
                .collect();

            if validated.is_empty() {
                break;
            }

            // Feed validated corollaries as new axioms for next depth
            // Add both name and signature keys as axioms for richer next-depth exploration
            for c in &validated {
                if c.is_axiom_candidate {
                    current_axioms.push(c.name.clone());
                }
                for (k, v) in &c.signature {
                    current_metrics.insert(k.clone(), *v);
                    // Also promote signature keys as axioms so next depth has more to work with
                    if !current_axioms.contains(k) {
                        current_axioms.push(k.clone());
                    }
                }
            }

            all_corollaries.extend(validated);
            depth += 1;

            if all_corollaries.len() >= self.config.max_corollaries {
                break;
            }
        }

        let new_axiom_candidates: Vec<Corollary> = all_corollaries
            .iter()
            .filter(|c| c.is_axiom_candidate)
            .cloned()
            .collect();

        let total = all_corollaries.len();

        BlowupResult {
            singularity: Some(singularity.clone()),
            corollaries: all_corollaries.clone(),
            validated: all_corollaries,
            depth_reached: depth,
            new_axiom_candidates,
            total_emergences: total,
        }
    }

    /// Run blowup from metric history (auto-detect singularity first).
    pub fn blowup_from_history(
        &self,
        history: &[HashMap<String, f64>],
    ) -> BlowupResult {
        match self.config.singularity_detector.detect(history) {
            Some(singularity) => self.blowup(&singularity),
            None => BlowupResult {
                singularity: None,
                corollaries: vec![],
                validated: vec![],
                depth_reached: 0,
                new_axiom_candidates: vec![],
                total_emergences: 0,
            },
        }
    }

    /// One cycle of blowup: generate corollaries from axioms.
    fn blowup_cycle(
        &self,
        axioms: &[String],
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Vec<Corollary> {
        let mut corollaries = Vec::new();

        // 1. Pairwise deduction: for each pair of axioms, generate interaction
        for i in 0..axioms.len() {
            for j in (i + 1)..axioms.len() {
                if let Some(c) = self.deduce(&axioms[i], &axioms[j], metrics, depth) {
                    corollaries.push(c);
                }
            }
        }

        // 2. Domain transfer: each axiom → each transfer domain
        for axiom in axioms {
            for domain in &self.config.transfer_domains {
                if let Some(c) = self.domain_transfer(axiom, domain, metrics, depth) {
                    corollaries.push(c);
                }
            }
        }

        // 3. Symmetry breaking: perturb each axiom
        for axiom in axioms {
            if let Some(c) = self.symmetry_break(axiom, metrics, depth) {
                corollaries.push(c);
            }
        }

        // 4. Bifurcation: small parameter shifts
        for axiom in axioms {
            for shift in N6_PERTURBATIONS {
                if let Some(c) = self.bifurcate(axiom, *shift, metrics, depth) {
                    corollaries.push(c);
                }
            }
        }

        // 5. Projection: collapse pairs of axioms
        for i in 0..axioms.len() {
            for j in (i + 1)..axioms.len() {
                if let Some(c) = self.project(&axioms[i], &axioms[j], metrics, depth) {
                    corollaries.push(c);
                }
            }
        }

        // 6. Dual: categorical dual of each axiom
        for axiom in axioms {
            if let Some(c) = self.dualize(axiom, metrics, depth) {
                corollaries.push(c);
            }
        }

        // 7. Second-order: compose pairs of generated corollaries
        let first_gen = corollaries.clone();
        for i in 0..first_gen.len().min(20) {
            for j in (i + 1)..first_gen.len().min(20) {
                if let Some(c) = self.compose(&first_gen[i], &first_gen[j], depth) {
                    corollaries.push(c);
                }
            }
        }

        corollaries
    }

    /// Pairwise axiom interaction → deduction.
    fn deduce(
        &self,
        a: &str,
        b: &str,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let va = metrics.get(a).copied().unwrap_or(1.0);
        let vb = metrics.get(b).copied().unwrap_or(1.0);

        // Interaction signature: product, ratio, sum
        let product = va * vb;
        let ratio = if vb.abs() > 1e-10 { va / vb } else { 0.0 };
        let sum = va + vb;

        // Confidence based on how "interesting" the interaction is
        // (non-trivial if product or ratio hits an n=6 constant)
        let n6_proximity = n6_distance(product)
            .min(n6_distance(ratio))
            .min(n6_distance(sum));
        let confidence = (1.0 - n6_proximity).max(0.0);

        if confidence < 0.1 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("{a}*{b}"), product);
        sig.insert(format!("{a}/{b}"), ratio);
        sig.insert(format!("{a}+{b}"), sum);

        Some(Corollary {
            name: format!("deduction_{a}_{b}_d{depth}"),
            corollary_type: CorollaryType::Deduction,
            source_axioms: vec![a.to_string(), b.to_string()],
            expression: format!("{a} × {b} = {product:.6}"),
            confidence,
            signature: sig,
            target_domain: "same".into(),
            is_axiom_candidate: confidence > 0.8,
        })
    }

    /// Transfer axiom to a different domain.
    fn domain_transfer(
        &self,
        axiom: &str,
        domain: &str,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let value = metrics.get(axiom).copied().unwrap_or(0.0);
        if value.abs() < 1e-10 {
            return None;
        }

        // Confidence: how well does this value fit n=6 patterns?
        let confidence = (1.0 - n6_distance(value)).max(0.0) * 0.7; // domain transfer is speculative

        if confidence < 0.15 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("{axiom}_in_{domain}"), value);

        Some(Corollary {
            name: format!("transfer_{axiom}_to_{domain}_d{depth}"),
            corollary_type: CorollaryType::DomainTransfer,
            source_axioms: vec![axiom.to_string()],
            expression: format!("{axiom}={value:.6} projected into {domain}"),
            confidence,
            signature: sig,
            target_domain: domain.to_string(),
            is_axiom_candidate: false,
        })
    }

    /// Perturb axiom symmetry.
    fn symmetry_break(
        &self,
        axiom: &str,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let value = metrics.get(axiom).copied().unwrap_or(0.0);
        // Break symmetry: value ± golden ratio perturbation
        let broken_plus = value + 1.618033988749895;
        let broken_minus = value - 1.618033988749895;

        let best = if n6_distance(broken_plus) < n6_distance(broken_minus) {
            broken_plus
        } else {
            broken_minus
        };

        let confidence = (1.0 - n6_distance(best)).max(0.0);
        if confidence < 0.2 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("{axiom}_broken"), best);

        Some(Corollary {
            name: format!("symbreak_{axiom}_d{depth}"),
            corollary_type: CorollaryType::SymmetryBreaking,
            source_axioms: vec![axiom.to_string()],
            expression: format!("{axiom} ± φ = {best:.6}"),
            confidence,
            signature: sig,
            target_domain: "same".into(),
            is_axiom_candidate: confidence > 0.7,
        })
    }

    /// Bifurcation: shift parameter and check for qualitative change.
    fn bifurcate(
        &self,
        axiom: &str,
        shift: f64,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let value = metrics.get(axiom).copied().unwrap_or(0.0);
        let shifted = value + shift;

        let confidence = (1.0 - n6_distance(shifted)).max(0.0) * 0.6;
        if confidence < 0.2 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("{axiom}_shift_{shift:.3}"), shifted);

        Some(Corollary {
            name: format!("bifurc_{axiom}_{shift:.1}_d{depth}"),
            corollary_type: CorollaryType::Bifurcation,
            source_axioms: vec![axiom.to_string()],
            expression: format!("{axiom} + {shift:.6} = {shifted:.6}"),
            confidence,
            signature: sig,
            target_domain: "same".into(),
            is_axiom_candidate: false,
        })
    }

    /// Project two axioms onto their shared subspace.
    fn project(
        &self,
        a: &str,
        b: &str,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let va = metrics.get(a).copied().unwrap_or(0.0);
        let vb = metrics.get(b).copied().unwrap_or(0.0);

        // Projection: geometric mean (the "shadow" of two values)
        let geom = (va.abs() * vb.abs()).sqrt() * va.signum();
        let confidence = (1.0 - n6_distance(geom)).max(0.0) * 0.8;

        if confidence < 0.15 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("proj_{a}_{b}"), geom);

        Some(Corollary {
            name: format!("proj_{a}_{b}_d{depth}"),
            corollary_type: CorollaryType::Projection,
            source_axioms: vec![a.to_string(), b.to_string()],
            expression: format!("√({a}·{b}) = {geom:.6}"),
            confidence,
            signature: sig,
            target_domain: "reduced".into(),
            is_axiom_candidate: false,
        })
    }

    /// Categorical dual of an axiom.
    fn dualize(
        &self,
        axiom: &str,
        metrics: &HashMap<String, f64>,
        depth: usize,
    ) -> Option<Corollary> {
        let value = metrics.get(axiom).copied().unwrap_or(0.0);
        if value.abs() < 1e-10 {
            return None;
        }

        // Dual: reciprocal (in category theory, reverse all arrows)
        let dual = 1.0 / value;
        let confidence = (1.0 - n6_distance(dual)).max(0.0) * 0.6;

        if confidence < 0.15 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("dual_{axiom}"), dual);

        Some(Corollary {
            name: format!("dual_{axiom}_d{depth}"),
            corollary_type: CorollaryType::Dual,
            source_axioms: vec![axiom.to_string()],
            expression: format!("1/{axiom} = {dual:.6}"),
            confidence,
            signature: sig,
            target_domain: "dual".into(),
            is_axiom_candidate: false,
        })
    }

    /// Compose two corollaries into a second-order emergence.
    fn compose(
        &self,
        a: &Corollary,
        b: &Corollary,
        depth: usize,
    ) -> Option<Corollary> {
        // Combine signatures
        let a_val: f64 = a.signature.values().next().copied().unwrap_or(0.0);
        let b_val: f64 = b.signature.values().next().copied().unwrap_or(0.0);

        if a_val.abs() < 1e-10 || b_val.abs() < 1e-10 {
            return None;
        }

        let composed = a_val * b_val;
        let confidence = (a.confidence * b.confidence) * (1.0 - n6_distance(composed)).max(0.0);

        if confidence < 0.1 {
            return None;
        }

        let mut sig = HashMap::new();
        sig.insert(format!("{}×{}", a.name, b.name), composed);

        let mut sources = a.source_axioms.clone();
        sources.extend(b.source_axioms.clone());
        sources.sort();
        sources.dedup();

        Some(Corollary {
            name: format!("compose_{}_{}_d{depth}", a.name, b.name),
            corollary_type: CorollaryType::Composition,
            source_axioms: sources,
            expression: format!("({}) ∘ ({}) = {composed:.6}", a.expression, b.expression),
            confidence,
            signature: sig,
            target_domain: if a.target_domain == b.target_domain {
                a.target_domain.clone()
            } else {
                "cross".into()
            },
            is_axiom_candidate: confidence > 0.7,
        })
    }
}

/// n=6 canonical constants for proximity checking.
const N6_CONSTANTS: &[f64] = &[
    6.0,            // n
    12.0,           // σ(6)
    4.0,            // τ(6)
    2.0,            // φ(6)
    5.0,            // sopfr(6)
    1.618033988750, // golden ratio
    0.287682072,    // ln(4/3)
    24.0,           // J2 = 4!
    10.0,           // σ-φ
    8.0,            // σ-τ
    1.333333333,    // τ²/σ
    3.0,            // ω(6) = distinct prime factors
    0.166666667,    // 1/6
    0.083333333,    // 1/12
    36.0,           // 6²
    720.0,          // 6!
];

/// n=6 perturbation shifts for bifurcation analysis.
const N6_PERTURBATIONS: &[f64] = &[
    0.287682072,  // ln(4/3)
    1.618033989,  // φ (golden)
    -1.618033989, // -φ
    0.166666667,  // 1/6
    -0.166666667, // -1/6
    2.449489743,  // √6
];

/// Distance from value to nearest n=6 constant (normalized 0..1).
fn n6_distance(value: f64) -> f64 {
    if value.is_nan() || value.is_infinite() {
        return 1.0;
    }
    let min_dist = N6_CONSTANTS
        .iter()
        .map(|c| (value - c).abs() / (c.abs().max(1.0)))
        .fold(f64::INFINITY, f64::min);
    min_dist.min(1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_singularity() -> Singularity {
        let mut metrics = HashMap::new();
        metrics.insert("sigma".into(), 12.0);
        metrics.insert("phi".into(), 2.0);
        metrics.insert("tau".into(), 4.0);
        metrics.insert("n".into(), 6.0);
        metrics.insert("sopfr".into(), 5.0);

        Singularity {
            axioms: vec!["sigma".into(), "phi".into(), "tau".into(), "n".into(), "sopfr".into()],
            compression_ratio: 3.0,
            closure_degree: 1.0,
            domain: "n6".into(),
            metrics,
        }
    }

    #[test]
    fn test_blowup_generates_corollaries() {
        let engine = BlowupEngine::with_defaults();
        let singularity = make_singularity();
        let result = engine.blowup(&singularity);

        assert!(!result.corollaries.is_empty());
        assert!(result.total_emergences > 0);
        println!("Generated {} corollaries at depth {}",
                 result.total_emergences, result.depth_reached);

        for c in &result.corollaries[..result.corollaries.len().min(10)] {
            println!("  {:?}: {} (conf={:.3})", c.corollary_type, c.expression, c.confidence);
        }
    }

    #[test]
    fn test_blowup_recursive_depth() {
        let engine = BlowupEngine::new(BlowupConfig {
            max_depth: 3,
            min_confidence: 0.1,
            ..BlowupConfig::default()
        });
        let singularity = make_singularity();
        let result = engine.blowup(&singularity);

        assert!(result.depth_reached >= 1);
        println!("Reached depth {}, {} total emergences",
                 result.depth_reached, result.total_emergences);
    }

    #[test]
    fn test_blowup_from_frozen_history() {
        let engine = BlowupEngine::new(BlowupConfig {
            singularity_detector: SingularityDetector {
                min_closure: 0.5,
                min_compression: 1.0,
                window: 3,
            },
            min_confidence: 0.05,
            ..BlowupConfig::default()
        });

        let snapshot: HashMap<String, f64> = vec![
            ("sigma".into(), 12.0),
            ("tau".into(), 4.0),
            ("phi".into(), 2.0),
            ("n".into(), 6.0),
        ]
        .into_iter()
        .collect();

        let history = vec![snapshot.clone(), snapshot.clone(), snapshot.clone()];
        let result = engine.blowup_from_history(&history);

        assert!(result.singularity.is_some());
        assert!(!result.corollaries.is_empty());
        println!("From history: {} emergences", result.total_emergences);
    }

    #[test]
    fn test_n6_distance() {
        assert!(n6_distance(6.0) < 0.01);
        assert!(n6_distance(12.0) < 0.01);
        assert!(n6_distance(1.618033989) < 0.01);
        assert!(n6_distance(5000.0) > 0.5);
    }
}
