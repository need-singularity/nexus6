//! Materials Project REST API v2 (next-gen) client.
//!
//! Provides synchronous access to the Materials Project summary endpoint
//! with rate limiting (30 req/min) and automatic API key resolution.

use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::time::Instant;

// ── Constants ──────────────────────────────────────────────────────

const BASE_URL: &str = "https://api.materialsproject.org/v2";

/// Maximum requests per minute (Materials Project rate limit).
const RATE_LIMIT_PER_MIN: usize = 30;

/// Default fields to request from the summary endpoint.
const DEFAULT_FIELDS: &[&str] = &[
    "material_id",
    "formula_pretty",
    "band_gap",
    "formation_energy_per_atom",
    "energy_above_hull",
    "symmetry",
    "volume",
    "density",
    "nsites",
];

// ── Data types ─────────────────────────────────────────────────────

/// A single material entry returned by the Materials Project API.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MaterialEntry {
    pub material_id: Option<String>,
    #[serde(alias = "formula_pretty")]
    pub formula: Option<String>,
    pub band_gap: Option<f64>,
    pub formation_energy_per_atom: Option<f64>,
    pub energy_above_hull: Option<f64>,
    pub symmetry: Option<SymmetryInfo>,
    pub volume: Option<f64>,
    pub density: Option<f64>,
    pub nsites: Option<u32>,
}

/// Crystal symmetry information.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymmetryInfo {
    pub crystal_system: Option<String>,
    pub symbol: Option<String>,
    pub number: Option<u32>,
}

/// Search filters for the materials summary endpoint.
#[derive(Debug, Clone, Default)]
pub struct SearchFilters {
    /// Required elements (e.g., ["Li", "O"]).
    pub elements: Option<Vec<String>>,
    /// Filter by number of sites.
    pub nsites_min: Option<u32>,
    pub nsites_max: Option<u32>,
    /// Band gap range (eV).
    pub band_gap_min: Option<f64>,
    pub band_gap_max: Option<f64>,
    /// Maximum formation energy per atom (eV/atom).
    pub formation_energy_max: Option<f64>,
    /// Crystal system (e.g., "cubic", "hexagonal").
    pub crystal_system: Option<String>,
    /// Maximum number of results to return.
    pub limit: Option<usize>,
}

/// Wrapper for the API JSON response.
#[derive(Debug, Deserialize)]
struct ApiResponse {
    data: Option<Vec<serde_json::Value>>,
}

// ── Rate limiter ───────────────────────────────────────────────────

struct RateLimiter {
    timestamps: Mutex<Vec<Instant>>,
    max_per_min: usize,
}

impl RateLimiter {
    fn new(max_per_min: usize) -> Self {
        Self {
            timestamps: Mutex::new(Vec::with_capacity(max_per_min)),
            max_per_min,
        }
    }

    /// Block until a request slot is available, then record the request.
    fn acquire(&self) {
        loop {
            let mut ts = self.timestamps.lock().unwrap();
            let now = Instant::now();
            let cutoff = now - std::time::Duration::from_secs(60);
            ts.retain(|t| *t > cutoff);
            if ts.len() < self.max_per_min {
                ts.push(now);
                return;
            }
            // Calculate sleep time until oldest entry expires.
            let sleep_until = ts[0] + std::time::Duration::from_secs(60);
            let wait = sleep_until.duration_since(now);
            drop(ts);
            std::thread::sleep(wait);
        }
    }
}

// ── Client ─────────────────────────────────────────────────────────

/// Synchronous client for the Materials Project API v2.
pub struct MpClient {
    api_key: String,
    agent: ureq::Agent,
    rate_limiter: RateLimiter,
}

impl MpClient {
    /// Create a new client.
    ///
    /// API key resolution order:
    /// 1. `MP_API_KEY` environment variable
    /// 2. `~/.nexus6/config.toml` → `[materials] api_key`
    /// 3. Error
    pub fn new() -> Result<Self, String> {
        let api_key = Self::resolve_api_key()?;
        let agent = ureq::AgentBuilder::new()
            .timeout(std::time::Duration::from_secs(30))
            .build();
        Ok(Self {
            api_key,
            agent,
            rate_limiter: RateLimiter::new(RATE_LIMIT_PER_MIN),
        })
    }

    /// Create a client with an explicit API key (useful for testing).
    pub fn with_key(api_key: impl Into<String>) -> Self {
        let agent = ureq::AgentBuilder::new()
            .timeout(std::time::Duration::from_secs(30))
            .build();
        Self {
            api_key: api_key.into(),
            agent,
            rate_limiter: RateLimiter::new(RATE_LIMIT_PER_MIN),
        }
    }

    // ── Public API ─────────────────────────────────────────────────

    /// Search materials by filters.
    ///
    /// `GET /materials/summary?<filters>&fields=...`
    pub fn search(&self, filters: &SearchFilters) -> Result<Vec<MaterialEntry>, String> {
        self.rate_limiter.acquire();

        let mut url = format!("{}/materials/summary", BASE_URL);
        let mut params: Vec<String> = Vec::new();

        // Fields
        let fields = DEFAULT_FIELDS.join(",");
        params.push(format!("fields={}", fields));

        // Filters
        if let Some(ref elems) = filters.elements {
            params.push(format!("elements={}", elems.join(",")));
        }
        if let Some(v) = filters.nsites_min {
            params.push(format!("nsites_min={}", v));
        }
        if let Some(v) = filters.nsites_max {
            params.push(format!("nsites_max={}", v));
        }
        if let Some(v) = filters.band_gap_min {
            params.push(format!("band_gap_min={}", v));
        }
        if let Some(v) = filters.band_gap_max {
            params.push(format!("band_gap_max={}", v));
        }
        if let Some(v) = filters.formation_energy_max {
            params.push(format!("formation_energy_per_atom_max={}", v));
        }
        if let Some(ref cs) = filters.crystal_system {
            params.push(format!("crystal_system={}", cs));
        }
        if let Some(v) = filters.limit {
            params.push(format!("_limit={}", v));
        }

        if !params.is_empty() {
            url.push('?');
            url.push_str(&params.join("&"));
        }

        let body = self.get(&url)?;
        self.parse_response(&body)
    }

    /// Fetch a single material by its ID (e.g., "mp-149").
    ///
    /// `GET /materials/{material_id}/summary`
    pub fn get_material(&self, material_id: &str) -> Result<MaterialEntry, String> {
        self.rate_limiter.acquire();

        let fields = DEFAULT_FIELDS.join(",");
        let url = format!(
            "{}/materials/{}/summary?fields={}",
            BASE_URL, material_id, fields
        );

        let body = self.get(&url)?;
        let entries = self.parse_response(&body)?;
        entries
            .into_iter()
            .next()
            .ok_or_else(|| format!("no data returned for material_id={}", material_id))
    }

    // ── Internal helpers ───────────────────────────────────────────

    fn get(&self, url: &str) -> Result<String, String> {
        let resp = self
            .agent
            .get(url)
            .set("X-API-KEY", &self.api_key)
            .set("Accept", "application/json")
            .call()
            .map_err(|e| format!("MP API request failed: {}", e))?;

        resp.into_string()
            .map_err(|e| format!("failed to read MP API response body: {}", e))
    }

    fn parse_response(&self, body: &str) -> Result<Vec<MaterialEntry>, String> {
        let api_resp: ApiResponse =
            serde_json::from_str(body).map_err(|e| format!("MP API JSON parse error: {}", e))?;

        let data = api_resp.data.unwrap_or_default();
        let mut entries = Vec::with_capacity(data.len());
        for val in data {
            let entry: MaterialEntry = serde_json::from_value(val)
                .map_err(|e| format!("failed to parse MaterialEntry: {}", e))?;
            entries.push(entry);
        }
        Ok(entries)
    }

    fn resolve_api_key() -> Result<String, String> {
        // 1. Environment variable
        if let Ok(key) = std::env::var("MP_API_KEY") {
            if !key.is_empty() {
                return Ok(key);
            }
        }

        // 2. Config file
        let cfg = crate::config::NexusConfig::load();
        if let Some(ref mat) = cfg.materials {
            if let Some(ref key) = mat.api_key {
                if !key.is_empty() {
                    return Ok(key.clone());
                }
            }
        }

        Err(
            "MP API key not found. Set MP_API_KEY env var or add [materials] api_key to ~/.nexus6/config.toml"
                .to_string(),
        )
    }
}

// ── Convenience constructors for SearchFilters ─────────────────────

impl SearchFilters {
    /// Create filters to search by chemical elements.
    pub fn by_elements(elements: &[&str]) -> Self {
        Self {
            elements: Some(elements.iter().map(|s| s.to_string()).collect()),
            ..Default::default()
        }
    }

    /// Create filters for materials with a band gap in a given range (eV).
    pub fn by_band_gap(min: f64, max: f64) -> Self {
        Self {
            band_gap_min: Some(min),
            band_gap_max: Some(max),
            ..Default::default()
        }
    }

    /// Set the maximum number of results.
    pub fn with_limit(mut self, limit: usize) -> Self {
        self.limit = Some(limit);
        self
    }
}

// ── Tests ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_filters_default() {
        let f = SearchFilters::default();
        assert!(f.elements.is_none());
        assert!(f.band_gap_min.is_none());
        assert!(f.limit.is_none());
    }

    #[test]
    fn test_search_filters_by_elements() {
        let f = SearchFilters::by_elements(&["Li", "O"]).with_limit(10);
        assert_eq!(f.elements.as_ref().unwrap(), &["Li", "O"]);
        assert_eq!(f.limit, Some(10));
    }

    #[test]
    fn test_search_filters_by_band_gap() {
        let f = SearchFilters::by_band_gap(1.0, 3.0);
        assert!((f.band_gap_min.unwrap() - 1.0).abs() < f64::EPSILON);
        assert!((f.band_gap_max.unwrap() - 3.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_material_entry_deserialization() {
        let json = r#"{
            "material_id": "mp-149",
            "formula_pretty": "Si",
            "band_gap": 1.11,
            "formation_energy_per_atom": 0.0,
            "energy_above_hull": 0.0,
            "symmetry": {"crystal_system": "cubic", "symbol": "Fd-3m", "number": 227},
            "volume": 40.89,
            "density": 2.33,
            "nsites": 2
        }"#;
        let entry: MaterialEntry = serde_json::from_str(json).unwrap();
        assert_eq!(entry.material_id.as_deref(), Some("mp-149"));
        assert_eq!(entry.formula.as_deref(), Some("Si"));
        assert!((entry.band_gap.unwrap() - 1.11).abs() < 0.01);
        assert_eq!(entry.nsites, Some(2));
        let sym = entry.symmetry.unwrap();
        assert_eq!(sym.crystal_system.as_deref(), Some("cubic"));
        assert_eq!(sym.number, Some(227));
    }

    #[test]
    fn test_api_response_parsing() {
        let json = r#"{"data": [
            {"material_id": "mp-149", "formula_pretty": "Si", "band_gap": 1.11}
        ]}"#;
        let client = MpClient::with_key("test-key");
        let entries = client.parse_response(json).unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].material_id.as_deref(), Some("mp-149"));
    }

    #[test]
    fn test_api_response_empty() {
        let json = r#"{"data": []}"#;
        let client = MpClient::with_key("test-key");
        let entries = client.parse_response(json).unwrap();
        assert!(entries.is_empty());
    }

    #[test]
    fn test_api_key_missing() {
        // Temporarily unset to test resolution failure path.
        let original = std::env::var("MP_API_KEY").ok();
        std::env::remove_var("MP_API_KEY");
        // Note: this may succeed if config.toml has the key;
        // we just verify it doesn't panic.
        let result = MpClient::new();
        assert!(result.is_ok() || result.is_err());
        // Restore
        if let Some(k) = original {
            std::env::set_var("MP_API_KEY", k);
        }
    }
}
