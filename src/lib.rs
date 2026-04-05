pub mod gpu;
pub mod encoder;
pub mod materials;
pub mod verifier;
pub mod graph;
pub mod telescope;
pub mod history;
pub mod ouroboros;
pub mod lens_forge;
pub mod experiment;
pub mod science;
pub mod cli;

pub mod blowup;
pub mod config;
pub mod resource_limit;
pub mod alien_index;
pub mod meta_gate;
pub mod implant;
pub mod pack;
pub mod sentry;

// --- Agent-generated modules ---
pub mod alert;
pub mod api;
pub mod auto_register;
pub mod autonomous;
pub mod consciousness_bridge;
pub mod distributed;
pub mod dream;
pub mod event;
pub mod feedback;
pub mod genetic_prog;
pub mod ingest;
pub mod knowledge;
pub mod pipeline;
pub mod plugin;
pub mod publish;
pub mod reward;
pub mod sandbox;
pub mod scheduler;
pub mod self_improve;
pub mod statistics;
pub mod template;
pub mod time_travel;
pub mod versioning;

// --- Calibration extension ---
pub mod calibration;

// --- Safety gate ---
pub mod safety;

// --- HEXA-GATE (breakthrough gate, Mk.I, from n6-architecture commit 736fc1a6) ---
pub mod gate;

// --- Growth engine ---
pub mod growth;

// --- Cross-module integration ---
pub mod integration;

// --- Infinite singularity recursion ---
pub mod singularity_recursion;

#[cfg(feature = "python")]
pub mod python;

// Comprehensive module tests — do not remove
#[cfg(test)]
mod module_tests;
