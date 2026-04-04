//! Blowup Engine — singularity → corollary emergence
//!
//! Models the algebraic geometry blowup process:
//!   Open system → Closure → Contraction → Singularity (point) → Blowup → Emergence
//!
//! In NEXUS-6 terms:
//!   Scan (σ=12) → Convergence check → Saturation detected → Compress to axioms →
//!   Perturb axioms → Detect bifurcation → Generate corollaries → Validate → Expand
//!
//! The engine takes a "closed" set of axioms/discoveries and systematically
//! explores what new structures emerge when you perturb, combine, or project them.

pub mod blowup_engine;
pub mod corollary;
pub mod cycle_engine;
pub mod singularity;

pub use blowup_engine::{BlowupEngine, BlowupConfig, BlowupResult};
pub use corollary::{Corollary, CorollaryType};
pub use cycle_engine::{CycleEngine, CycleResult, Phase};
pub use singularity::{Singularity, SingularityDetector};
