//! nexus6 mk2 — Prime-atomic smooth-class engine
//!
//! See `docs/superpowers/specs/2026-04-06-nexus6-mk2-design.md`
//!
//! # Core abstractions
//!
//! - [`primes`] — prime sieve, factorize, prime-set operations
//! - [`smooth`] — SmoothRing trait (φ, τ, σ, sopfr, ρ) over u64
//! - [`types`] — Rational, PrimeSet, Sector, Point (mk2 extensions)

pub mod bridge;
pub mod classify;
pub mod classify_v2;
pub mod compat;
pub mod lattice;
pub mod primes;
pub mod smooth;
pub mod types;

pub use classify::{classify, ClassifyResult};
pub use classify_v2::{classify_v2, default_sectors, ClassifyResultV2, SectorDef};
pub use compat::{n6_match_mk2, n6_exact_ratio_mk2, dual_check, dual_check_batch};
pub use lattice::{Lattice, LatticeNode};
pub use primes::{Prime, PrimeSet, factorize, is_prime, primes_up_to};
pub use smooth::{SmoothRing, euler_ratio, rho};
pub use types::{Rational, Sector};
