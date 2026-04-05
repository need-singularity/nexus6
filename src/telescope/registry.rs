use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;

/// Category of a lens in the registry.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LensCategory {
    /// The 22 foundational lenses from the telescope specification.
    Core,
    /// The 10 domain-specific lens combinations.
    DomainCombo,
    /// Extended lenses added through incremental expansion (toward 411).
    Extended,
    /// User-defined custom lenses.
    Custom,
}

/// Metadata entry for a single lens in the registry.
#[derive(Debug, Clone)]
pub struct LensEntry {
    pub name: String,
    pub category: LensCategory,
    pub description: String,
    /// Domains where this lens is most effective.
    pub domain_affinity: Vec<String>,
    /// Other lenses that pair well with this one.
    pub complementary: Vec<String>,
}

/// Central registry for all lens metadata.
///
/// This is a *metadata* registry — it stores descriptions, affinities and
/// relationships. The actual scan logic lives in the `Lens` trait implementors.
/// The registry enables discovery ("which lenses suit domain X?") and
/// incremental growth toward the full 411-lens set.
#[derive(Debug, Clone)]
pub struct LensRegistry {
    entries: HashMap<String, LensEntry>,
}

impl LensRegistry {
    /// Create a new registry pre-populated with the 22 Core lenses,
    /// 58 n6-industry lenses, 40 cross-project lenses, 103 TECS-L math
    /// lenses, 88 Anima consciousness lenses, 100 SEDI signal lenses,
    /// 58 accel ML lenses, 57 accel physics/neuro lenses, 55 accel
    /// engineering lenses, 63 accel humanities lenses, 49 physics-deep
    /// lenses, and 10 domain combos (703 total).
    pub fn new() -> Self {
        let mut reg = LensRegistry {
            entries: HashMap::new(),
        };
        for entry in super::core_lenses::core_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::n6_lenses::n6_industry_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::cross_lenses::cross_project_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::tecs_lenses::tecs_math_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::anima_lenses::anima_consciousness_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::sedi_lenses::sedi_signal_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::accel_lenses_a::accel_ml_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::accel_lenses_b::accel_physics_neuro_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::accel_lenses_c::accel_engineering_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::accel_lenses_d::accel_humanities_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::quantum_lenses::quantum_topology_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        for entry in super::physics_deep_lenses::physics_deep_lens_entries() {
            reg.entries.insert(entry.name.clone(), entry);
        }
        // Register the 10 domain combos as DomainCombo-category entries
        for combo in super::domain_combos::default_combos() {
            let entry = LensEntry {
                name: format!("combo_{}", combo.name),
                category: LensCategory::DomainCombo,
                description: format!(
                    "Domain combo '{}' combining [{}] for [{}]",
                    combo.name,
                    combo.lenses.join(", "),
                    combo.target_domains.join(", "),
                ),
                domain_affinity: combo.target_domains,
                complementary: combo.lenses,
            };
            reg.entries.insert(entry.name.clone(), entry);
        }
        // Load persisted custom lenses from disk
        reg.load_custom();
        reg
    }

    /// Register a new lens entry. Overwrites if name already exists.
    pub fn register(&mut self, entry: LensEntry) {
        self.entries.insert(entry.name.clone(), entry);
    }

    /// Look up a lens by name.
    pub fn get(&self, name: &str) -> Option<&LensEntry> {
        self.entries.get(name)
    }

    /// Return all lenses belonging to the given category.
    pub fn by_category(&self, cat: LensCategory) -> Vec<&LensEntry> {
        self.entries
            .values()
            .filter(|e| e.category == cat)
            .collect()
    }

    /// Recommend lenses for a given domain string (case-insensitive substring match).
    pub fn for_domain(&self, domain: &str) -> Vec<&LensEntry> {
        let domain_lower = domain.to_lowercase();
        self.entries
            .values()
            .filter(|e| {
                e.domain_affinity
                    .iter()
                    .any(|d| d.to_lowercase().contains(&domain_lower))
            })
            .collect()
    }

    /// Total number of registered lenses.
    pub fn len(&self) -> usize {
        self.entries.len()
    }

    /// Whether the registry is empty.
    pub fn is_empty(&self) -> bool {
        self.entries.is_empty()
    }

    /// Iterator over all entries.
    pub fn iter(&self) -> impl Iterator<Item = (&String, &LensEntry)> {
        self.entries.iter()
    }

    // ── Custom lens persistence ──────────────────────────────────

    fn custom_lenses_path() -> PathBuf {
        let home = std::env::var("HOME").unwrap_or_default();
        PathBuf::from(home).join("Dev/nexus6/shared/custom_lenses.jsonl")
    }

    /// Load custom lenses from disk and register them.
    pub fn load_custom(&mut self) {
        let path = Self::custom_lenses_path();
        let content = match fs::read_to_string(&path) {
            Ok(c) => c,
            Err(_) => return,
        };
        let mut count = 0;
        for line in content.lines() {
            if line.trim().is_empty() { continue; }
            // Simple JSON parsing: {"name":"...","description":"...","domain_affinity":["..."],"complementary":["..."]}
            if let Some(entry) = Self::parse_custom_lens_line(line) {
                self.entries.insert(entry.name.clone(), entry);
                count += 1;
            }
        }
        if count > 0 {
            eprintln!("[registry] loaded {} custom lenses from {}", count, path.display());
        }
    }

    /// Save all Custom category lenses to disk (append-safe JSONL).
    pub fn save_custom(&self) {
        let path = Self::custom_lenses_path();
        let customs: Vec<&LensEntry> = self.by_category(LensCategory::Custom);
        if customs.is_empty() { return; }
        let mut lines = Vec::new();
        for e in &customs {
            let domains: Vec<String> = e.domain_affinity.iter().map(|d| format!("\"{}\"", d)).collect();
            let comps: Vec<String> = e.complementary.iter().map(|c| format!("\"{}\"", c)).collect();
            lines.push(format!(
                "{{\"name\":\"{}\",\"description\":\"{}\",\"domain_affinity\":[{}],\"complementary\":[{}]}}",
                e.name.replace('"', "'"),
                e.description.replace('"', "'"),
                domains.join(","),
                comps.join(","),
            ));
        }
        if let Err(err) = fs::write(&path, lines.join("\n") + "\n") {
            eprintln!("[registry] failed to save custom lenses: {}", err);
        } else {
            eprintln!("[registry] saved {} custom lenses to {}", customs.len(), path.display());
        }
    }

    fn parse_custom_lens_line(line: &str) -> Option<LensEntry> {
        // Minimal JSON parse for {"name":"...", ...}
        let extract = |key: &str| -> Option<String> {
            let pattern = format!("\"{}\":\"", key);
            let start = line.find(&pattern)? + pattern.len();
            let rest = &line[start..];
            let end = rest.find('"')?;
            Some(rest[..end].to_string())
        };
        let extract_arr = |key: &str| -> Vec<String> {
            let pattern = format!("\"{}\":[", key);
            let start = match line.find(&pattern) {
                Some(s) => s + pattern.len(),
                None => return vec![],
            };
            let rest = &line[start..];
            let end = match rest.find(']') {
                Some(e) => e,
                None => return vec![],
            };
            rest[..end].split(',')
                .map(|s| s.trim().trim_matches('"').to_string())
                .filter(|s| !s.is_empty())
                .collect()
        };

        Some(LensEntry {
            name: extract("name")?,
            category: LensCategory::Custom,
            description: extract("description").unwrap_or_default(),
            domain_affinity: extract_arr("domain_affinity"),
            complementary: extract_arr("complementary"),
        })
    }
}

impl Default for LensRegistry {
    fn default() -> Self {
        Self::new()
    }
}
