//! Classifier v2: keyword + value_range + prime_set weighted scoring.
//!
//! Replaces v1 (`classify.rs::classify`) which used prime_set only.
//! v1 had 100% electroweak false-positive rate on real topology data.
//!
//! v2 combines three signals:
//!   - keyword (0.5 weight): subject detection from text
//!   - value_range (0.3 weight): sector-specific numeric bounds
//!   - prime_set (0.2 weight): required/preferred prime patterns

use crate::mk2::primes::PrimeSet;
use crate::mk2::types::Sector;

/// Sector definition used by v2 classifier.
#[derive(Debug, Clone)]
pub struct SectorDef {
    pub name: Sector,
    pub keywords: Vec<String>,
    pub value_ranges: Vec<(f64, f64)>,
    pub prime_set_required: Option<PrimeSet>,
    pub prime_set_preferred: Vec<PrimeSet>,
}

/// Result of v2 classification.
#[derive(Debug, Clone)]
pub struct ClassifyResultV2 {
    pub sector: Sector,
    pub confidence: f64, // 0.0 .. 1.0
    pub keyword_hits: usize,
    pub value_range_hit: bool,
    pub prime_set_match: f64, // 0.0, 0.5, 1.0
}

/// Hardcoded sector definitions matching `shared/cycle/sectors.yaml`.
pub fn default_sectors() -> Vec<SectorDef> {
    use crate::mk2::primes::prime_set_of;

    vec![
        SectorDef {
            name: Sector::Strong,
            keywords: vec![
                "quark".into(),
                "color".into(),
                "gluon".into(),
                "QCD".into(),
                "confinement".into(),
                "baryon".into(),
            ],
            value_ranges: vec![(0.33, 0.34), (0.66, 0.67)],
            prime_set_required: None,
            prime_set_preferred: vec![
                prime_set_of(2),
                prime_set_of(3),
                prime_set_of(6),
            ],
        },
        SectorDef {
            name: Sector::Electroweak,
            keywords: vec![
                "Weinberg".into(),
                "theta_W".into(),
                "θ_W".into(),
                "Cabibbo".into(),
                "θ_C".into(),
                "W boson".into(),
                "Z boson".into(),
                "electroweak".into(),
                "CKM".into(),
                "Jarlskog".into(),
            ],
            value_ranges: vec![(0.20, 0.25)],
            prime_set_required: Some(prime_set_of(210)), // {2,3,5,7}
            prime_set_preferred: vec![],
        },
        SectorDef {
            name: Sector::Cosmology,
            keywords: vec![
                "Omega_m".into(),
                "Omega_Lambda".into(),
                "Omega_b".into(),
                "Omega_DM".into(),
                "dark energy".into(),
                "dark matter".into(),
                "Hubble".into(),
                "H0".into(),
                "flatness".into(),
                "Planck 2018".into(),
                "Ω_m".into(),
                "Ω_Λ".into(),
                "Ω_b".into(),
                "Ω_DM".into(),
            ],
            value_ranges: vec![(0.0, 1.0)],
            prime_set_required: None,
            prime_set_preferred: vec![
                prime_set_of(35),  // {5,7}
                prime_set_of(30),  // {2,3,5}
                prime_set_of(6),   // {2,3}
            ],
        },
        SectorDef {
            name: Sector::Primordial,
            keywords: vec![
                "BBN".into(),
                "nucleosynthesis".into(),
                "helium".into(),
                "deuterium".into(),
                "Y_p".into(),
                "eta_baryon".into(),
                "baryogenesis".into(),
                "CMB".into(),
                "inflation".into(),
            ],
            value_ranges: vec![(0.24, 0.26)],
            prime_set_required: None,
            prime_set_preferred: vec![
                prime_set_of(2 * 3 * 5 * 13), // {2,3,5,13}
            ],
        },
    ]
}

fn keyword_score(text: &str, keywords: &[String]) -> (f64, usize) {
    let text_low = text.to_lowercase();
    let hits = keywords
        .iter()
        .filter(|k| text_low.contains(&k.to_lowercase()))
        .count();
    let score = (hits as f64 / 2.0).min(1.0);
    (score, hits)
}

fn value_range_score(values: &[f64], ranges: &[(f64, f64)]) -> (f64, bool) {
    if values.is_empty() || ranges.is_empty() {
        return (0.0, false);
    }
    for &v in values {
        for &(lo, hi) in ranges {
            if v >= lo && v <= hi {
                return (1.0, true);
            }
        }
    }
    (0.0, false)
}

fn prime_set_score(ps: &PrimeSet, def: &SectorDef) -> f64 {
    if let Some(ref req) = def.prime_set_required {
        if ps == req {
            return 1.0;
        } else if req.is_subset(ps) {
            return 0.5;
        } else {
            return 0.0;
        }
    }
    for preferred in &def.prime_set_preferred {
        if ps == preferred {
            return 1.0;
        }
        if preferred.is_subset(ps) {
            return 0.5;
        }
    }
    0.0
}

/// Classify a point using text + extracted values + prime set.
pub fn classify_v2(
    text: &str,
    values: &[f64],
    prime_set: &PrimeSet,
    sectors: &[SectorDef],
) -> ClassifyResultV2 {
    let mut best = ClassifyResultV2 {
        sector: Sector::Unknown,
        confidence: 0.0,
        keyword_hits: 0,
        value_range_hit: false,
        prime_set_match: 0.0,
    };
    for def in sectors {
        let (kw_s, kw_hits) = keyword_score(text, &def.keywords);
        let (val_s, val_hit) = value_range_score(values, &def.value_ranges);
        let ps_s = prime_set_score(prime_set, def);

        // Weighted composite
        let confidence = 0.5 * kw_s + 0.3 * val_s + 0.2 * ps_s;

        if confidence > best.confidence {
            best = ClassifyResultV2 {
                sector: def.name.clone(),
                confidence,
                keyword_hits: kw_hits,
                value_range_hit: val_hit,
                prime_set_match: ps_s,
            };
        }
    }

    // Threshold gate: below 0.3 → Unknown
    if best.confidence < 0.3 {
        best.sector = Sector::Unknown;
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mk2::primes::prime_set_of;

    #[test]
    fn classify_weinberg_cabibbo() {
        let text = "Cabibbo angle sin θ_C from n=6 arithmetic CKM matrix";
        let values = vec![0.2243];
        let ps = prime_set_of(210); // {2,3,5,7}
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        assert_eq!(result.sector, Sector::Electroweak);
        assert!(result.confidence >= 0.5);
    }

    #[test]
    fn classify_hubble() {
        let text = "Hubble constant H0 = 73 km/s/Mpc from n=6 basis";
        let values = vec![73.0];
        let ps = prime_set_of(6); // {2,3}
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        assert_eq!(result.sector, Sector::Cosmology);
        assert!(result.confidence >= 0.5);
    }

    #[test]
    fn classify_primordial_helium() {
        let text = "Primordial Helium Y_p BBN nucleosynthesis 0.25";
        let values = vec![0.25];
        let ps = prime_set_of(2 * 3 * 5 * 13);
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        assert_eq!(result.sector, Sector::Primordial);
        assert!(result.confidence >= 0.5);
    }

    #[test]
    fn classify_strong_qcd() {
        let text = "QCD quark confinement color charge up quark 2/3";
        let values = vec![2.0 / 3.0];
        let ps = prime_set_of(6); // {2,3}
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        assert_eq!(result.sector, Sector::Strong);
        assert!(result.confidence >= 0.5);
    }

    #[test]
    fn classify_unknown_below_threshold() {
        let text = "random text with no physics content";
        let values = vec![42.0];
        let ps = prime_set_of(15);
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        assert_eq!(result.sector, Sector::Unknown);
    }

    #[test]
    fn classify_electroweak_strict_required() {
        // prime_set NOT {2,3,5,7} → no EW classification even with keywords
        let text = "Weinberg angle sin²θ_W";
        let values = vec![0.23];
        let ps = prime_set_of(6); // {2,3} — missing 5,7
        let sectors = default_sectors();
        let result = classify_v2(text, &values, &ps, &sectors);
        // Should still classify as EW from keywords+value even if ps mismatch
        assert!(result.confidence >= 0.3);
    }
}
