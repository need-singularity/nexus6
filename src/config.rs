//! Unified config loader — reads `~/.nexus6/config.toml`.
//!
//! All fields are optional. Priority: CLI args > config.toml > hardcoded defaults.

use serde::Deserialize;

/// Top-level config mirroring `~/.nexus6/config.toml`.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct NexusConfig {
    #[serde(rename = "loop")]
    pub loop_cfg: Option<LoopSection>,
    pub daemon: Option<DaemonSection>,
    pub blowup: Option<BlowupSection>,
    pub evolution: Option<EvolutionSection>,
    pub forge: Option<ForgeSection>,
    pub log_rotation: Option<LogRotationSection>,
    pub materials: Option<MaterialsSection>,
}

// ── Section structs ─────────────────────────────────────────────

#[derive(Debug, Clone, Default, Deserialize)]
pub struct LoopSection {
    /// Default domain for `nexus6 loop`.
    pub domain: Option<String>,
    /// Default number of cycles.
    pub cycles: Option<usize>,
    /// Max OUROBOROS cycles per meta-cycle.
    pub max_ouroboros_cycles: Option<usize>,
    /// Max meta-loop iterations.
    pub max_meta_cycles: Option<usize>,
    /// Forge every N ouroboros cycles (0 = only on saturation).
    pub forge_after_n_cycles: Option<usize>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct DaemonSection {
    /// Default domain for `nexus6 daemon`.
    pub domain: Option<String>,
    /// Interval in minutes between loops.
    pub interval_min: Option<u64>,
    /// Maximum number of loops (None = infinite).
    pub max_loops: Option<usize>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct BlowupSection {
    /// Default domain for `nexus6 blowup`.
    pub domain: Option<String>,
    /// Maximum recursive blowup depth.
    pub max_depth: Option<usize>,
    /// Maximum corollaries per blowup cycle.
    pub max_corollaries: Option<usize>,
    /// Minimum confidence to keep a corollary.
    pub min_confidence: Option<f64>,
    /// Domains to attempt transfer into.
    pub transfer_domains: Option<Vec<String>>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct EvolutionSection {
    /// Default domain.
    pub domain: Option<String>,
    /// Serendipity ratio for lens recommendation (0.0..1.0).
    pub serendipity_ratio: Option<f64>,
    /// Minimum verification score to accept a discovery.
    pub min_verification_score: Option<f64>,
    /// Maximum mutations per cycle.
    pub max_mutations_per_cycle: Option<usize>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct LogRotationSection {
    /// Maximum log file size in bytes before rotation (default: 1 MB).
    pub max_bytes: Option<u64>,
    /// Maximum number of rotated files to keep (default: 5).
    pub max_files: Option<usize>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct MaterialsSection {
    /// Materials Project API key (alternative to MP_API_KEY env var).
    pub api_key: Option<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct ForgeSection {
    /// Maximum candidates to consider per strategy.
    pub max_candidates: Option<usize>,
    /// Minimum confidence threshold (base value).
    pub min_confidence: Option<f64>,
    /// Jaccard similarity threshold for uniqueness.
    pub similarity_threshold: Option<f64>,
}

// ── Loading ─────────────────────────────────────────────────────

impl NexusConfig {
    /// Load config from `~/.nexus6/config.toml`.
    /// Returns `NexusConfig::default()` if file is missing or unreadable.
    pub fn load() -> Self {
        let path = match std::env::var("HOME") {
            Ok(home) => format!("{}/.nexus6/config.toml", home),
            Err(_) => return Self::default(),
        };
        let contents = match std::fs::read_to_string(&path) {
            Ok(s) => s,
            Err(_) => return Self::default(),
        };
        match toml::from_str(&contents) {
            Ok(cfg) => cfg,
            Err(e) => {
                eprintln!("warning: config.toml parse error: {} — using defaults", e);
                Self::default()
            }
        }
    }
}

// ── Convenience helpers ─────────────────────────────────────────

impl NexusConfig {
    /// Build a `MetaLoopConfig` from the `[loop]` section, using hardcoded defaults
    /// for any field not specified.
    pub fn meta_loop_config(&self) -> crate::ouroboros::MetaLoopConfig {
        let l = self.loop_cfg.as_ref();
        crate::ouroboros::MetaLoopConfig {
            max_ouroboros_cycles: l.and_then(|s| s.max_ouroboros_cycles).unwrap_or(6),
            max_meta_cycles: l.and_then(|s| s.max_meta_cycles).unwrap_or(6),
            forge_after_n_cycles: l.and_then(|s| s.forge_after_n_cycles).unwrap_or(3),
            forge_config: self.forge_config(),
        }
    }

    /// Build a `ForgeConfig` from the `[forge]` section.
    pub fn forge_config(&self) -> crate::lens_forge::forge_engine::ForgeConfig {
        let defaults = crate::lens_forge::forge_engine::ForgeConfig::default();
        let f = self.forge.as_ref();
        crate::lens_forge::forge_engine::ForgeConfig {
            max_candidates: f.and_then(|s| s.max_candidates).unwrap_or(defaults.max_candidates),
            min_confidence: f.and_then(|s| s.min_confidence).unwrap_or(defaults.min_confidence),
            similarity_threshold: f
                .and_then(|s| s.similarity_threshold)
                .unwrap_or(defaults.similarity_threshold),
            cycle_number: defaults.cycle_number,
        }
    }

    /// Build a `BlowupConfig` from the `[blowup]` section.
    pub fn blowup_config(&self) -> crate::blowup::BlowupConfig {
        let defaults = crate::blowup::BlowupConfig::default();
        let b = self.blowup.as_ref();
        crate::blowup::BlowupConfig {
            max_corollaries: b.and_then(|s| s.max_corollaries).unwrap_or(defaults.max_corollaries),
            min_confidence: b.and_then(|s| s.min_confidence).unwrap_or(defaults.min_confidence),
            max_depth: b.and_then(|s| s.max_depth).unwrap_or(defaults.max_depth),
            transfer_domains: b
                .and_then(|s| s.transfer_domains.clone())
                .unwrap_or(defaults.transfer_domains),
            singularity_detector: defaults.singularity_detector,
        }
    }

    /// Default domain for loop/daemon commands.
    pub fn default_loop_domain(&self) -> Option<String> {
        self.loop_cfg.as_ref().and_then(|s| s.domain.clone())
    }

    /// Default cycles for `nexus6 loop`.
    pub fn default_loop_cycles(&self) -> usize {
        self.loop_cfg.as_ref().and_then(|s| s.cycles).unwrap_or(1)
    }

    /// Default domain for daemon.
    pub fn default_daemon_domain(&self) -> Option<String> {
        self.daemon.as_ref().and_then(|s| s.domain.clone())
    }

    /// Default interval_min for daemon.
    pub fn default_daemon_interval(&self) -> u64 {
        self.daemon.as_ref().and_then(|s| s.interval_min).unwrap_or(30)
    }

    /// Default max_loops for daemon.
    pub fn default_daemon_max_loops(&self) -> Option<usize> {
        self.daemon.as_ref().and_then(|s| s.max_loops)
    }

    /// Default domain for blowup.
    pub fn default_blowup_domain(&self) -> String {
        self.blowup
            .as_ref()
            .and_then(|s| s.domain.clone())
            .unwrap_or_else(|| "number_theory".to_string())
    }

    /// Default max_depth for blowup.
    pub fn default_blowup_depth(&self) -> usize {
        self.blowup.as_ref().and_then(|s| s.max_depth).unwrap_or(6)
    }

    /// Maximum log file size in bytes before rotation (default: 1 MB).
    pub fn log_rotation_max_bytes(&self) -> u64 {
        self.log_rotation
            .as_ref()
            .and_then(|s| s.max_bytes)
            .unwrap_or(1_048_576)
    }

    /// Maximum number of rotated log files to keep (default: 5).
    pub fn log_rotation_max_files(&self) -> usize {
        self.log_rotation
            .as_ref()
            .and_then(|s| s.max_files)
            .unwrap_or(5)
    }
}

// ── Example config generator ────────────────────────────────────

/// Generate a commented example `config.toml`.
pub fn default_config_toml() -> String {
    r#"# NEXUS-6 Configuration
# Place this file at ~/.nexus6/config.toml
# All values are optional — hardcoded defaults are shown.

[loop]
# domain = "number_theory"
# cycles = 1
# max_ouroboros_cycles = 6
# max_meta_cycles = 6
# forge_after_n_cycles = 3

[daemon]
# domain = "number_theory"
# interval_min = 30
# max_loops = 0          # 0 = infinite

[blowup]
# domain = "number_theory"
# max_depth = 6
# max_corollaries = 216
# min_confidence = 0.15
# transfer_domains = ["physics", "mathematics", "information", "biology", "consciousness", "architecture"]

[evolution]
# domain = "general"
# serendipity_ratio = 0.3
# min_verification_score = 0.5
# max_mutations_per_cycle = 20

[forge]
# max_candidates = 20
# min_confidence = 0.2
# similarity_threshold = 0.8

[materials]
# api_key = "your-materials-project-api-key"

[log_rotation]
# max_bytes = 1048576   # 1 MB
# max_files = 5
"#
    .to_string()
}
