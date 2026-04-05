//! nexus6 mk2 — Prime-atomic smooth-class engine
//!
//! See `docs/superpowers/specs/2026-04-06-nexus6-mk2-design.md`
//!
//! # Core abstractions
//!
//! - [`primes`] — prime sieve, factorize, prime-set operations
//! - [`smooth`] — SmoothRing trait (φ, τ, σ, sopfr, ρ) over u64
//! - [`types`] — Rational, PrimeSet, Sector, Point (mk2 extensions)

pub mod primes;
pub mod smooth;
pub mod types;

pub use primes::{Prime, PrimeSet, factorize, is_prime, primes_up_to};
pub use smooth::{SmoothRing, euler_ratio, rho};
pub use types::{Rational, Sector};
