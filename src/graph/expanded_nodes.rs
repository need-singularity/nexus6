//! Expanded knowledge graph nodes: Constants, Techniques, Domains, Experiments.
//!
//! Complements bt_nodes.rs to bring the knowledge graph from 130 nodes (BT-only)
//! toward the 500-node target. Adds cross-domain edges connecting BTs to the
//! constants, techniques, domains, and experiments that underpin them.

use super::edge::{Edge, EdgeType};
use super::node::{Node, NodeType};
use super::persistence::DiscoveryGraph;

// ═══════════════════════════════════════════════════════════════
// n=6 Constants (the 6 fundamental + 6 derived = σ=12 total)
// ═══════════════════════════════════════════════════════════════

struct ConstantEntry {
    id: &'static str,
    name: &'static str,
    value: f64,
    formula: &'static str,
    /// Domain tags for cross-referencing with BTs.
    domains: &'static [&'static str],
}

/// The 12 (=sigma) core n=6 constants: 6 fundamental + 6 derived.
const CONSTANTS: &[ConstantEntry] = &[
    ConstantEntry { id: "C-n", name: "n (perfect number)", value: 6.0, formula: "n=6", domains: &["Math", "NumberTheory"] },
    ConstantEntry { id: "C-sigma", name: "sigma (divisor sum)", value: 12.0, formula: "sigma(6)=1+2+3+6=12", domains: &["Math", "AI", "Chip"] },
    ConstantEntry { id: "C-phi", name: "phi (Euler totient)", value: 2.0, formula: "phi(6)=|{1,5}|=2", domains: &["Math", "Crypto", "SC"] },
    ConstantEntry { id: "C-tau", name: "tau (divisor count)", value: 4.0, formula: "tau(6)=|{1,2,3,6}|=4", domains: &["Math", "Particle", "Fusion"] },
    ConstantEntry { id: "C-J2", name: "J2 (Jordan totient)", value: 24.0, formula: "J_2(6)=24", domains: &["Math", "AI", "DisplayAudio", "Energy"] },
    ConstantEntry { id: "C-sopfr", name: "sopfr (sum of prime factors)", value: 5.0, formula: "sopfr(6)=2+3=5", domains: &["Math", "Fusion", "Robotics"] },
    // Derived constants
    ConstantEntry { id: "C-mu", name: "mu (Mobius function)", value: 1.0, formula: "mu(6)=(-1)^2=1", domains: &["Math", "NumberTheory"] },
    ConstantEntry { id: "C-sigma-phi", name: "sigma-phi", value: 10.0, formula: "sigma-phi=12-2=10", domains: &["AI", "Battery", "Energy"] },
    ConstantEntry { id: "C-sigma-tau", name: "sigma-tau", value: 8.0, formula: "sigma-tau=12-4=8", domains: &["AI", "Chip", "Crypto"] },
    ConstantEntry { id: "C-sigma-mu", name: "sigma-mu", value: 11.0, formula: "sigma-mu=12-1=11", domains: &["Particle", "Network", "Chip"] },
    ConstantEntry { id: "C-sigma2", name: "sigma^2", value: 144.0, formula: "sigma^2=12^2=144", domains: &["Chip", "Semiconductor"] },
    ConstantEntry { id: "C-sigma-tau-prod", name: "sigma*tau", value: 48.0, formula: "sigma*tau=12*4=48", domains: &["DisplayAudio", "Semiconductor", "Energy"] },
];

// ═══════════════════════════════════════════════════════════════
// 66 AI Techniques (v3)
// ═══════════════════════════════════════════════════════════════

struct TechniqueEntry {
    id: &'static str,
    name: &'static str,
    key_result: &'static str,
    /// Which n=6 constants this technique uses.
    constants_used: &'static [&'static str],
}

const TECHNIQUES: &[TechniqueEntry] = &[
    TechniqueEntry { id: "T-01", name: "Cyclotomic Activation (phi6simple)", key_result: "71% FLOPs reduction", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-02", name: "HCN Tensor Alignment", key_result: "10-20% param reduction", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-03", name: "Phi Bottleneck FFN", key_result: "67% param reduction", constants_used: &["C-phi", "C-tau"] },
    TechniqueEntry { id: "T-04", name: "Phi/Tau MoE Routing", key_result: "65% active params", constants_used: &["C-phi", "C-tau"] },
    TechniqueEntry { id: "T-05", name: "Entropy Early Stop", key_result: "33% training saved", constants_used: &["C-n"] },
    TechniqueEntry { id: "T-06", name: "R-Filter Phase Detection", key_result: "Phase detection", constants_used: &["C-n"] },
    TechniqueEntry { id: "T-07", name: "Takens dim=6 Embedding", key_result: "Loss curve diagnostic", constants_used: &["C-n"] },
    TechniqueEntry { id: "T-08", name: "FFT Mix Attention", key_result: "3x faster +0.55%", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-09", name: "Zeta*ln(2) Activation", key_result: "71% FLOPs reduction", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-10", name: "Egyptian MoE (1/2+1/3+1/6=1)", key_result: "Perfect expert routing", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-11", name: "Dedekind Head Pruning", key_result: "~25% attention reduction", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-12", name: "Jordan-Leech MoE (J2=24)", key_result: "24 expert capacity bound", constants_used: &["C-J2", "C-sigma"] },
    TechniqueEntry { id: "T-13", name: "Mobius Sparse Gradients", key_result: "Squarefree topology", constants_used: &["C-mu", "C-n"] },
    TechniqueEntry { id: "T-14", name: "Carmichael LR Schedule", key_result: "lambda(6)=2 cycle", constants_used: &["C-phi"] },
    TechniqueEntry { id: "T-15", name: "Boltzmann Gate (1/e sparsity)", key_result: "63% activation sparsity", constants_used: &["C-n"] },
    TechniqueEntry { id: "T-16", name: "Mertens Dropout (ln(4/3))", key_result: "p=0.288, no search", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-17", name: "Egyptian Fraction Attention", key_result: "~40% FLOPs saved", constants_used: &["C-phi", "C-n"] },
    // BT12 (T-18 ~ T-29) — AI Breakthrough Theorems
    TechniqueEntry { id: "T-18", name: "Chinchilla n=6 Scaling", key_result: "σ-τ=8 compute ratio", constants_used: &["C-sigma-tau", "C-n"] },
    TechniqueEntry { id: "T-19", name: "Computing Architecture σ=12 Ladder", key_result: "12-layer stack", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-20", name: "Transformer σ=12 Atom", key_result: "12-head base", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-21", name: "RoPE Base-6 Encoding", key_result: "n=6 position encoding", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-22", name: "KV-Head φ=2 Universality", key_result: "GQA head ratio=φ", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-23", name: "Inference τ=4 Scaling", key_result: "4-phase decode", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-24", name: "AdamW n=6 Quintuplet", key_result: "sopfr=5 hyperparams", constants_used: &["C-sopfr", "C-n"] },
    TechniqueEntry { id: "T-25", name: "Complete LLM σ-Blueprint", key_result: "Full n=6 architecture", constants_used: &["C-sigma", "C-phi", "C-tau"] },
    TechniqueEntry { id: "T-26", name: "σ-τ=8 Universal AI Constant", key_result: "8-bit quantization bridge", constants_used: &["C-sigma-tau", "C-n"] },
    TechniqueEntry { id: "T-27", name: "8-Layer AI Stack", key_result: "σ-τ=8 hierarchy", constants_used: &["C-sigma-tau", "C-n"] },
    TechniqueEntry { id: "T-28", name: "Diffusion n=6 Steps", key_result: "6-step schedule", constants_used: &["C-n", "C-tau"] },
    TechniqueEntry { id: "T-29", name: "MoE φ/n Activation Law", key_result: "1/3 expert activation", constants_used: &["C-phi", "C-n"] },
    // Model21 (T-30 ~ T-50) — Model architecture
    TechniqueEntry { id: "T-30", name: "BitNet σ-τ=8 Quantization", key_result: "1.58-bit mapping", constants_used: &["C-sigma-tau", "C-n"] },
    TechniqueEntry { id: "T-31", name: "KV Cache τ=4 Compression", key_result: "4x cache reduction", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-32", name: "Speculative φ=2 Decoding", key_result: "draft/verify=φ", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-33", name: "Context Window σ²=144k", key_result: "144k context scaling", constants_used: &["C-sigma2", "C-n"] },
    TechniqueEntry { id: "T-34", name: "FP8/FP16=φ Precision", key_result: "phi precision ratio", constants_used: &["C-phi", "C-sigma-tau"] },
    TechniqueEntry { id: "T-35", name: "ln(4/3) RLHF Regularization", key_result: "Mertens in RLHF", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-36", name: "Tokenizer σ·τ=48k Vocab", key_result: "48k vocabulary", constants_used: &["C-sigma-tau-prod", "C-n"] },
    TechniqueEntry { id: "T-37", name: "0.1 Universal Regularization", key_result: "weight decay=0.1", constants_used: &["C-n", "C-sigma-phi"] },
    TechniqueEntry { id: "T-38", name: "Mamba SSM dim=6", key_result: "6-dim state space", constants_used: &["C-n", "C-tau"] },
    TechniqueEntry { id: "T-39", name: "95/5 Cross-Domain Split", key_result: "95% pretraining", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-40", name: "σ-φ=10 Attention Heads", key_result: "10-head attention", constants_used: &["C-sigma-phi", "C-n"] },
    TechniqueEntry { id: "T-41", name: "J2=24 Expert Capacity", key_result: "24-expert bound", constants_used: &["C-J2", "C-sigma"] },
    TechniqueEntry { id: "T-42", name: "Hexagonal Weight Init", key_result: "6-fold symmetric init", constants_used: &["C-n", "C-phi"] },
    TechniqueEntry { id: "T-43", name: "Perfect Number Batch", key_result: "batch=6k optimal", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-44", name: "τ²/σ=4/3 LR Decay", key_result: "solar-AI ratio", constants_used: &["C-tau", "C-sigma"] },
    TechniqueEntry { id: "T-45", name: "φ²/n=2/3 Byzantine Dropout", key_result: "fault-tolerant p=2/3", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-46", name: "Cyclotomic Norm Layer", key_result: "Φ₆(x) normalization", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-47", name: "Egyptian Fraction Loss", key_result: "1/2+1/3+1/6 multi-task", constants_used: &["C-n", "C-phi"] },
    TechniqueEntry { id: "T-48", name: "Divisor Lattice Skip", key_result: "τ=4 skip connections", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-49", name: "Ramanujan Sparse Projection", key_result: "expander graph projections", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-50", name: "σ-μ=11 Dimensional Embedding", key_result: "11-dim latent space", constants_used: &["C-sigma-mu", "C-n"] },
    // Vision8 (T-51 ~ T-58) — Vision AI
    TechniqueEntry { id: "T-51", name: "ViT Patch σ-φ=10", key_result: "10×10 optimal patch", constants_used: &["C-sigma-phi", "C-n"] },
    TechniqueEntry { id: "T-52", name: "Vision n=6 Backbone", key_result: "6-stage architecture", constants_used: &["C-n", "C-tau"] },
    TechniqueEntry { id: "T-53", name: "NeRF/3DGS dim=6", key_result: "6D positional encoding", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-54", name: "Hexagonal Conv Kernel", key_result: "6-neighbor kernel", constants_used: &["C-n", "C-phi"] },
    TechniqueEntry { id: "T-55", name: "φ=2 Resolution Pyramid", key_result: "2x downsampling", constants_used: &["C-phi", "C-n"] },
    TechniqueEntry { id: "T-56", name: "Egyptian Fraction FPN", key_result: "1/2+1/3+1/6 fusion", constants_used: &["C-n", "C-phi"] },
    TechniqueEntry { id: "T-57", name: "τ=4 Multi-Scale Detection", key_result: "4-level pyramid", constants_used: &["C-tau", "C-n"] },
    TechniqueEntry { id: "T-58", name: "σ=12 Channel Alignment", key_result: "12n channel counts", constants_used: &["C-sigma", "C-n"] },
    // GNN4 (T-59 ~ T-62) — Graph Neural Networks
    TechniqueEntry { id: "T-59", name: "Kissing σ=12 Message Passing", key_result: "max 12 neighbors", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-60", name: "Hexagonal Graph Pooling", key_result: "6-fold coarsening", constants_used: &["C-n", "C-phi"] },
    TechniqueEntry { id: "T-61", name: "Leech Lattice Graph Embed", key_result: "24-dim features", constants_used: &["C-J2", "C-n"] },
    TechniqueEntry { id: "T-62", name: "Möbius Graph Sparsification", key_result: "squarefree pruning", constants_used: &["C-mu", "C-n"] },
    // Other4 (T-63 ~ T-66) — Cross-domain
    TechniqueEntry { id: "T-63", name: "Neural Audio Codec n=6", key_result: "6-band decomposition", constants_used: &["C-n", "C-sigma"] },
    TechniqueEntry { id: "T-64", name: "SE(3) Robot Control", key_result: "6-DoF universal", constants_used: &["C-n", "C-J2"] },
    TechniqueEntry { id: "T-65", name: "Chiplet σ=12 Architecture", key_result: "12-chiplet package", constants_used: &["C-sigma", "C-n"] },
    TechniqueEntry { id: "T-66", name: "Meta Fixed Point 1/3", key_result: "meta-learning convergence", constants_used: &["C-phi", "C-n"] },
];

// ═══════════════════════════════════════════════════════════════
// Knowledge Domains (the unique domains across all BTs)
// ═══════════════════════════════════════════════════════════════

struct DomainEntry {
    id: &'static str,
    name: &'static str,
    category: &'static str,
}

const DOMAINS: &[DomainEntry] = &[
    // Physics
    DomainEntry { id: "D-SC", name: "Superconductor", category: "Physics" },
    DomainEntry { id: "D-Fusion", name: "Fusion", category: "Physics" },
    DomainEntry { id: "D-Tokamak", name: "Tokamak", category: "Physics" },
    DomainEntry { id: "D-Plasma", name: "Plasma", category: "Physics" },
    DomainEntry { id: "D-Particle", name: "Particle", category: "Physics" },
    DomainEntry { id: "D-Cosmology", name: "Cosmology", category: "Physics" },
    DomainEntry { id: "D-StringTheory", name: "StringTheory", category: "Physics" },
    // Computing
    DomainEntry { id: "D-AI", name: "AI", category: "Computing" },
    DomainEntry { id: "D-Chip", name: "Chip", category: "Computing" },
    DomainEntry { id: "D-Semiconductor", name: "Semiconductor", category: "Computing" },
    DomainEntry { id: "D-QC", name: "QC", category: "Computing" },
    DomainEntry { id: "D-Software", name: "Software", category: "Computing" },
    // Math
    DomainEntry { id: "D-Math", name: "Math", category: "Math" },
    DomainEntry { id: "D-NumberTheory", name: "NumberTheory", category: "Math" },
    DomainEntry { id: "D-Topology", name: "Topology", category: "Math" },
    DomainEntry { id: "D-Combinatorics", name: "Combinatorics", category: "Math" },
    DomainEntry { id: "D-CodingTheory", name: "CodingTheory", category: "Math" },
    DomainEntry { id: "D-InfoTheory", name: "InfoTheory", category: "Math" },
    // Energy
    DomainEntry { id: "D-Energy", name: "Energy", category: "Energy" },
    DomainEntry { id: "D-Battery", name: "Battery", category: "Energy" },
    DomainEntry { id: "D-Solar", name: "Solar", category: "Energy" },
    DomainEntry { id: "D-PowerGrid", name: "PowerGrid", category: "Energy" },
    DomainEntry { id: "D-Hydrogen", name: "Hydrogen", category: "Energy" },
    DomainEntry { id: "D-Nuclear", name: "Nuclear", category: "Energy" },
    DomainEntry { id: "D-Thermal", name: "Thermal", category: "Energy" },
    // Materials & Chemistry
    DomainEntry { id: "D-Material", name: "Material", category: "Materials" },
    DomainEntry { id: "D-Chemistry", name: "Chemistry", category: "Materials" },
    // Life Sciences
    DomainEntry { id: "D-Biology", name: "Biology", category: "Life" },
    // Infrastructure
    DomainEntry { id: "D-Network", name: "Network", category: "Infrastructure" },
    DomainEntry { id: "D-Crypto", name: "Crypto", category: "Infrastructure" },
    DomainEntry { id: "D-Blockchain", name: "Blockchain", category: "Infrastructure" },
    // Applied
    DomainEntry { id: "D-DisplayAudio", name: "DisplayAudio", category: "Applied" },
    DomainEntry { id: "D-Music", name: "Music", category: "Applied" },
    DomainEntry { id: "D-Robotics", name: "Robotics", category: "Applied" },
    DomainEntry { id: "D-Automotive", name: "Automotive", category: "Applied" },
    DomainEntry { id: "D-Environment", name: "Environment", category: "Applied" },
    DomainEntry { id: "D-Magnet", name: "Magnet", category: "Physics" },
    DomainEntry { id: "D-Physics", name: "Physics", category: "Physics" },
];

// ═══════════════════════════════════════════════════════════════
// Experiment nodes (12 extended experiments)
// ═══════════════════════════════════════════════════════════════

struct ExperimentEntry {
    id: &'static str,
    name: &'static str,
    techniques_used: &'static [&'static str],
    domains: &'static [&'static str],
}

const EXPERIMENTS: &[ExperimentEntry] = &[
    ExperimentEntry { id: "E-01", name: "Combined Architecture (H-EE-11)", techniques_used: &["T-01", "T-03", "T-08", "T-10"], domains: &["AI", "Chip"] },
    ExperimentEntry { id: "E-02", name: "Cyclotomic Benchmark", techniques_used: &["T-01"], domains: &["AI"] },
    ExperimentEntry { id: "E-03", name: "Egyptian MoE Routing", techniques_used: &["T-10", "T-04"], domains: &["AI"] },
    ExperimentEntry { id: "E-04", name: "FFT Attention Speed", techniques_used: &["T-08"], domains: &["AI", "Chip"] },
    ExperimentEntry { id: "E-05", name: "Entropy Stopping Validation", techniques_used: &["T-05"], domains: &["AI"] },
    ExperimentEntry { id: "E-06", name: "Phi Bottleneck Scaling", techniques_used: &["T-03"], domains: &["AI"] },
    ExperimentEntry { id: "E-07", name: "Dedekind Head Pruning", techniques_used: &["T-11"], domains: &["AI"] },
    ExperimentEntry { id: "E-08", name: "Boltzmann Gate Sparsity", techniques_used: &["T-15"], domains: &["AI"] },
    ExperimentEntry { id: "E-09", name: "Mertens Dropout Search-Free", techniques_used: &["T-16"], domains: &["AI"] },
    ExperimentEntry { id: "E-10", name: "Egyptian Fraction Attention", techniques_used: &["T-17", "T-10"], domains: &["AI"] },
    ExperimentEntry { id: "E-11", name: "Emergent n=6 Self-Organization", techniques_used: &["T-01", "T-10", "T-15"], domains: &["AI", "Math"] },
    ExperimentEntry { id: "E-12", name: "Cascade Cross-Verification", techniques_used: &["T-01", "T-03", "T-08", "T-10", "T-17"], domains: &["AI", "Chip", "Math"] },
];

// ═══════════════════════════════════════════════════════════════
// Public API: populate the graph with expanded nodes
// ═══════════════════════════════════════════════════════════════

/// Add all n=6 constant nodes to the graph. Returns the count of nodes added.
pub fn populate_constants(graph: &mut DiscoveryGraph) -> usize {
    let count = CONSTANTS.len();
    for c in CONSTANTS {
        graph.add_node(Node {
            id: c.id.to_string(),
            node_type: NodeType::Constant,
            domain: c.domains.join(", "),
            project: "n6-architecture".to_string(),
            summary: format!("{} = {} [{}]", c.name, c.value, c.formula),
            confidence: 1.0, // mathematical certainty
            lenses_used: vec!["consciousness".into(), "causal".into()],
            timestamp: "2026-04-03".to_string(),
            mk2_sector: None,
            mk2_confidence: None,
        });
    }
    count
}

/// Add all 66 technique nodes and connect them to the constants they use.
/// Returns the count of nodes added.
pub fn populate_techniques(graph: &mut DiscoveryGraph) -> usize {
    let count = TECHNIQUES.len();
    for t in TECHNIQUES {
        graph.add_node(Node {
            id: t.id.to_string(),
            node_type: NodeType::Technique,
            domain: "AI".to_string(),
            project: "n6-architecture".to_string(),
            summary: format!("{}: {}", t.name, t.key_result),
            confidence: 0.9,
            lenses_used: vec!["consciousness".into(), "topology".into()],
            timestamp: "2026-04-03".to_string(),
            mk2_sector: None,
            mk2_confidence: None,
        });

        // Technique -> Constant edges (Uses)
        for &const_id in t.constants_used {
            graph.add_edge(Edge {
                from: t.id.to_string(),
                to: const_id.to_string(),
                edge_type: EdgeType::Uses,
                strength: 0.9,
                bidirectional: false,
            });
        }
    }
    count
}

/// Add domain nodes and connect BTs to their domains. Returns node count added.
pub fn populate_domains(graph: &mut DiscoveryGraph) -> usize {
    let count = DOMAINS.len();
    for d in DOMAINS {
        graph.add_node(Node {
            id: d.id.to_string(),
            node_type: NodeType::Domain,
            domain: d.category.to_string(),
            project: "n6-architecture".to_string(),
            summary: format!("Domain: {} [{}]", d.name, d.category),
            confidence: 1.0,
            lenses_used: vec![],
            timestamp: "2026-04-03".to_string(),
            mk2_sector: None,
            mk2_confidence: None,
        });
    }

    // Connect BT nodes to domain nodes.
    // We look for existing BT-* nodes and link them to matching D-* domain nodes.
    let bt_nodes: Vec<(String, Vec<String>)> = graph
        .nodes
        .iter()
        .filter(|n| n.node_type == NodeType::Bt)
        .map(|n| {
            let domains: Vec<String> = n.domain.split(", ").map(|s| s.to_string()).collect();
            (n.id.clone(), domains)
        })
        .collect();

    let domain_ids: std::collections::HashSet<String> =
        DOMAINS.iter().map(|d| format!("D-{}", d.name)).collect();

    for (bt_id, bt_domains) in &bt_nodes {
        for domain_name in bt_domains {
            let domain_id = format!("D-{}", domain_name);
            if domain_ids.contains(&domain_id) {
                graph.add_edge(Edge {
                    from: domain_id,
                    to: bt_id.clone(),
                    edge_type: EdgeType::Contains,
                    strength: 1.0,
                    bidirectional: false,
                });
            }
        }
    }

    count
}

/// Add experiment nodes and connect them to techniques and domains.
/// Returns node count added.
pub fn populate_experiments(graph: &mut DiscoveryGraph) -> usize {
    let count = EXPERIMENTS.len();
    for e in EXPERIMENTS {
        graph.add_node(Node {
            id: e.id.to_string(),
            node_type: NodeType::Experiment,
            domain: e.domains.join(", "),
            project: "n6-architecture".to_string(),
            summary: format!("Experiment: {}", e.name),
            confidence: 0.8,
            lenses_used: vec!["consciousness".into(), "causal".into(), "topology".into()],
            timestamp: "2026-04-03".to_string(),
            mk2_sector: None,
            mk2_confidence: None,
        });

        // Experiment -> Technique edges (Uses)
        for &tech_id in e.techniques_used {
            graph.add_edge(Edge {
                from: e.id.to_string(),
                to: tech_id.to_string(),
                edge_type: EdgeType::Uses,
                strength: 0.85,
                bidirectional: false,
            });
        }

        // Experiment -> Domain edges (Contains, reversed)
        for &domain_name in e.domains {
            let domain_id = format!("D-{}", domain_name);
            graph.add_edge(Edge {
                from: domain_id,
                to: e.id.to_string(),
                edge_type: EdgeType::Contains,
                strength: 0.7,
                bidirectional: false,
            });
        }
    }
    count
}

/// Connect constants to BTs that reference them via domain overlap.
/// This creates Constant -> BT edges where the constant's domains overlap
/// with the BT's domains. Returns edge count added.
pub fn connect_constants_to_bts(graph: &mut DiscoveryGraph) -> usize {
    let constant_info: Vec<(String, Vec<String>)> = CONSTANTS
        .iter()
        .map(|c| {
            let domains: Vec<String> = c.domains.iter().map(|d| d.to_string()).collect();
            (c.id.to_string(), domains)
        })
        .collect();

    let bt_info: Vec<(String, Vec<String>)> = graph
        .nodes
        .iter()
        .filter(|n| n.node_type == NodeType::Bt)
        .map(|n| {
            let domains: Vec<String> = n.domain.split(", ").map(|s| s.to_string()).collect();
            (n.id.clone(), domains)
        })
        .collect();

    let mut edge_count = 0;
    for (const_id, const_domains) in &constant_info {
        for (bt_id, bt_domains) in &bt_info {
            let shared: usize = const_domains
                .iter()
                .filter(|d| bt_domains.contains(d))
                .count();
            if shared > 0 {
                let strength = shared as f64 / const_domains.len().max(1) as f64;
                graph.add_edge(Edge {
                    from: const_id.clone(),
                    to: bt_id.clone(),
                    edge_type: EdgeType::Derives,
                    strength,
                    bidirectional: false,
                });
                edge_count += 1;
            }
        }
    }
    edge_count
}

/// Populate the entire expanded knowledge graph in one call.
/// Call this after populate_bt_graph() so BT nodes exist for cross-referencing.
/// Returns (nodes_added, edges_added).
pub fn populate_expanded_graph(graph: &mut DiscoveryGraph) -> (usize, usize) {
    let edges_before = graph.edges.len();

    let n_constants = populate_constants(graph);
    let n_techniques = populate_techniques(graph);
    let n_domains = populate_domains(graph);
    let n_experiments = populate_experiments(graph);
    let _const_bt_edges = connect_constants_to_bts(graph);

    let nodes_added = n_constants + n_techniques + n_domains + n_experiments;
    let edges_added = graph.edges.len() - edges_before;
    (nodes_added, edges_added)
}

/// Total count of expanded node entries (constants + techniques + domains + experiments).
pub fn expanded_node_count() -> usize {
    CONSTANTS.len() + TECHNIQUES.len() + DOMAINS.len() + EXPERIMENTS.len()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::bt_nodes::populate_bt_graph;

    #[test]
    fn test_constant_count_is_sigma() {
        // 12 constants = sigma(6) = 12
        assert_eq!(CONSTANTS.len(), 12, "Should have sigma=12 constants");
    }

    #[test]
    fn test_technique_count_is_66() {
        assert_eq!(TECHNIQUES.len(), 66, "Should have exactly 66 techniques");
    }

    #[test]
    fn test_experiment_count_is_12() {
        // 12 experiments = sigma(6)
        assert_eq!(EXPERIMENTS.len(), 12, "Should have sigma=12 experiments");
    }

    #[test]
    fn test_populate_constants() {
        let mut graph = DiscoveryGraph::new();
        let count = populate_constants(&mut graph);
        assert_eq!(count, 12);
        assert_eq!(graph.nodes.len(), 12);
        assert!(graph.nodes.iter().all(|n| n.node_type == NodeType::Constant));
        assert!(graph.nodes.iter().all(|n| n.confidence == 1.0));
    }

    #[test]
    fn test_populate_techniques_creates_edges() {
        let mut graph = DiscoveryGraph::new();
        populate_constants(&mut graph);
        let count = populate_techniques(&mut graph);
        assert_eq!(count, 66);
        // Each technique uses at least 1 constant, so there should be Uses edges
        let uses_edges: Vec<_> = graph
            .edges
            .iter()
            .filter(|e| e.edge_type == EdgeType::Uses)
            .collect();
        assert!(
            uses_edges.len() >= 66,
            "Should have at least 66 Uses edges, got {}",
            uses_edges.len()
        );
    }

    #[test]
    fn test_populate_domains_connects_bts() {
        let mut graph = DiscoveryGraph::new();
        populate_bt_graph(&mut graph);
        let bt_count = graph.nodes.len();
        let d_count = populate_domains(&mut graph);
        assert!(d_count >= 30, "Should have 30+ domain nodes, got {}", d_count);
        assert_eq!(graph.nodes.len(), bt_count + d_count);

        // Should have Contains edges from domains to BTs
        let contains_edges: Vec<_> = graph
            .edges
            .iter()
            .filter(|e| e.edge_type == EdgeType::Contains)
            .collect();
        assert!(
            contains_edges.len() > 50,
            "Should have many Contains edges, got {}",
            contains_edges.len()
        );
    }

    #[test]
    fn test_populate_experiments() {
        let mut graph = DiscoveryGraph::new();
        populate_constants(&mut graph);
        populate_techniques(&mut graph);
        let count = populate_experiments(&mut graph);
        assert_eq!(count, 12);

        // Experiments should have Uses edges to techniques
        let exp_uses: Vec<_> = graph
            .edges
            .iter()
            .filter(|e| e.from.starts_with("E-") && e.edge_type == EdgeType::Uses)
            .collect();
        assert!(
            exp_uses.len() >= 12,
            "Should have 12+ experiment->technique edges, got {}",
            exp_uses.len()
        );
    }

    #[test]
    fn test_full_expanded_graph() {
        let mut graph = DiscoveryGraph::new();
        populate_bt_graph(&mut graph);
        let (nodes_added, edges_added) = populate_expanded_graph(&mut graph);

        // 127 BT + 12 constants + 66 techniques + 38 domains + 12 experiments = 255+
        let total_nodes = graph.nodes.len();
        assert!(
            total_nodes >= 200,
            "Full graph should have 200+ nodes, got {}",
            total_nodes
        );
        assert!(
            nodes_added >= 120,
            "Should add 120+ expanded nodes, got {}",
            nodes_added
        );
        assert!(
            edges_added > 100,
            "Should add 100+ cross-reference edges, got {}",
            edges_added
        );
    }

    #[test]
    fn test_expanded_node_count() {
        let count = expanded_node_count();
        // 12 + 66 + 38 + 12 = 128
        assert!(
            count >= 128,
            "expanded_node_count should be >= 128, got {}",
            count
        );
    }

    #[test]
    fn test_constants_to_bts_edges() {
        let mut graph = DiscoveryGraph::new();
        populate_bt_graph(&mut graph);
        populate_constants(&mut graph);
        let edge_count = connect_constants_to_bts(&mut graph);
        // sigma constant (domains: Math, AI, Chip) should connect to many BTs
        assert!(
            edge_count > 50,
            "Should create 50+ constant->BT edges, got {}",
            edge_count
        );
    }
}
