//! DFT (Density Functional Theory) verification pipeline.
//!
//! Filters, ranks, and generates input files (VASP POSCAR / Quantum ESPRESSO pw.x)
//! for first-principles validation of predicted material candidates.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

/// A candidate material predicted by upstream ML models, awaiting DFT validation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DftCandidate {
    /// Chemical formula, e.g. "LiCoO2"
    pub formula: String,
    /// Constituent element symbols, e.g. ["Li", "Co", "O"]
    pub elements: Vec<String>,
    /// Space-group symbol or number, e.g. "Fm-3m" or "225"
    pub spacegroup: String,
    /// ML-predicted band gap in eV
    pub predicted_bandgap: f64,
    /// ML-predicted formation energy in eV/atom
    pub predicted_formation_energy: f64,
}

/// Crystal structure archetype used for POSCAR / QE template generation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StructureType {
    Perovskite,
    Spinel,
    Rocksalt,
    Generic,
}

// ---------------------------------------------------------------------------
// Lattice-constant table (Angstrom)
// ---------------------------------------------------------------------------

fn default_lattice_constants() -> HashMap<&'static str, f64> {
    let mut m = HashMap::new();
    m.insert("Li", 3.51);
    m.insert("Na", 4.29);
    m.insert("O", 2.46);
    m.insert("S", 3.13);
    m.insert("Fe", 2.87);
    m.insert("Co", 2.51);
    m.insert("Ni", 3.52);
    m.insert("Mn", 8.91);
    m.insert("Ti", 2.95);
    m.insert("Zr", 3.23);
    m.insert("Al", 4.05);
    m.insert("Si", 5.43);
    m.insert("Cu", 3.61);
    m.insert("Zn", 2.66);
    m.insert("Mg", 3.21);
    m.insert("Ca", 5.58);
    m.insert("Ba", 5.02);
    m.insert("Sr", 6.08);
    m.insert("La", 5.30);
    m.insert("Ce", 5.16);
    m.insert("P", 3.31);
    m.insert("Se", 4.36);
    m.insert("Te", 4.45);
    m
}

/// Estimate an average lattice constant from the elements present.
fn estimate_lattice_constant(elements: &[String]) -> f64 {
    let table = default_lattice_constants();
    let (sum, count) = elements.iter().fold((0.0, 0usize), |(s, c), el| {
        if let Some(&a) = table.get(el.as_str()) {
            (s + a, c + 1)
        } else {
            (s, c)
        }
    });
    if count > 0 {
        sum / count as f64
    } else {
        4.0 // fallback
    }
}

// ---------------------------------------------------------------------------
// Structure-type heuristic
// ---------------------------------------------------------------------------

fn infer_structure_type(candidate: &DftCandidate) -> StructureType {
    let sg = candidate.spacegroup.as_str();
    // Perovskite: Pm-3m (#221)
    if sg == "Pm-3m" || sg == "221" {
        return StructureType::Perovskite;
    }
    // Spinel: Fd-3m (#227)
    if sg == "Fd-3m" || sg == "227" {
        return StructureType::Spinel;
    }
    // Rocksalt: Fm-3m (#225)
    if sg == "Fm-3m" || sg == "225" {
        return StructureType::Rocksalt;
    }
    StructureType::Generic
}

// ---------------------------------------------------------------------------
// DftPipeline
// ---------------------------------------------------------------------------

/// Orchestrates candidate filtering, ranking, and input-file generation.
#[derive(Debug, Default)]
pub struct DftPipeline;

impl DftPipeline {
    pub fn new() -> Self {
        Self
    }

    // ----- filtering -------------------------------------------------------

    /// Basic stability filter:
    /// - formation energy < 0 eV/atom (thermodynamic stability)
    /// - band gap >= 0 (physical plausibility)
    /// - at least one element listed
    pub fn filter_candidates(&self, candidates: Vec<DftCandidate>) -> Vec<DftCandidate> {
        candidates
            .into_iter()
            .filter(|c| {
                c.predicted_formation_energy < 0.0
                    && c.predicted_bandgap >= 0.0
                    && !c.elements.is_empty()
            })
            .collect()
    }

    // ----- VASP POSCAR generation ------------------------------------------

    /// Generate a VASP 5 POSCAR string with structure-aware templates.
    pub fn generate_poscar(&self, candidate: &DftCandidate) -> String {
        let a = estimate_lattice_constant(&candidate.elements);
        let stype = infer_structure_type(candidate);

        match stype {
            StructureType::Perovskite => self.poscar_perovskite(candidate, a),
            StructureType::Spinel => self.poscar_spinel(candidate, a),
            StructureType::Rocksalt => self.poscar_rocksalt(candidate, a),
            StructureType::Generic => self.poscar_generic(candidate, a),
        }
    }

    fn poscar_perovskite(&self, c: &DftCandidate, a: f64) -> String {
        // ABX3 perovskite: A at corner, B at body-center, X at face-centers
        let elements_line = c.elements.join(" ");
        let counts: Vec<String> = if c.elements.len() >= 3 {
            vec!["1".into(), "1".into(), "3".into()]
        } else {
            c.elements.iter().map(|_| "1".to_string()).collect()
        };
        format!(
            "{formula} — perovskite (DFT candidate)\n\
             {a:.6}\n\
             1.000000  0.000000  0.000000\n\
             0.000000  1.000000  0.000000\n\
             0.000000  0.000000  1.000000\n\
             {elements}\n\
             {counts}\n\
             Direct\n\
             0.000000  0.000000  0.000000\n\
             0.500000  0.500000  0.500000\n\
             0.500000  0.500000  0.000000\n\
             0.500000  0.000000  0.500000\n\
             0.000000  0.500000  0.500000\n",
            formula = c.formula,
            a = a,
            elements = elements_line,
            counts = counts.join("  "),
        )
    }

    fn poscar_spinel(&self, c: &DftCandidate, a: f64) -> String {
        // Simplified spinel AB2X4: 8 atoms in primitive cell
        let elements_line = c.elements.join(" ");
        let counts: Vec<String> = if c.elements.len() >= 3 {
            vec!["2".into(), "4".into(), "8".into()]
        } else {
            c.elements.iter().map(|_| "2".to_string()).collect()
        };
        format!(
            "{formula} — spinel (DFT candidate)\n\
             {a:.6}\n\
             0.500000  0.500000  0.000000\n\
             0.500000  0.000000  0.500000\n\
             0.000000  0.500000  0.500000\n\
             {elements}\n\
             {counts}\n\
             Direct\n\
             0.000000  0.000000  0.000000\n\
             0.250000  0.250000  0.250000\n\
             0.625000  0.625000  0.625000\n\
             0.375000  0.375000  0.375000\n",
            formula = c.formula,
            a = a,
            elements = elements_line,
            counts = counts.join("  "),
        )
    }

    fn poscar_rocksalt(&self, c: &DftCandidate, a: f64) -> String {
        // Rocksalt AB: A at (0,0,0), B at (0.5,0.5,0.5)
        let elements_line = c.elements.join(" ");
        let counts: Vec<String> = if c.elements.len() >= 2 {
            vec!["1".into(), "1".into()]
        } else {
            vec!["2".into()]
        };
        format!(
            "{formula} — rocksalt (DFT candidate)\n\
             {a:.6}\n\
             0.500000  0.500000  0.000000\n\
             0.500000  0.000000  0.500000\n\
             0.000000  0.500000  0.500000\n\
             {elements}\n\
             {counts}\n\
             Direct\n\
             0.000000  0.000000  0.000000\n\
             0.500000  0.500000  0.500000\n",
            formula = c.formula,
            a = a,
            elements = elements_line,
            counts = counts.join("  "),
        )
    }

    fn poscar_generic(&self, c: &DftCandidate, a: f64) -> String {
        let elements_line = c.elements.join(" ");
        let counts: Vec<String> = c.elements.iter().map(|_| "1".to_string()).collect();
        format!(
            "{formula} — generic (DFT candidate)\n\
             {a:.6}\n\
             1.000000  0.000000  0.000000\n\
             0.000000  1.000000  0.000000\n\
             0.000000  0.000000  1.000000\n\
             {elements}\n\
             {counts}\n\
             Direct\n\
             0.000000  0.000000  0.000000\n",
            formula = c.formula,
            a = a,
            elements = elements_line,
            counts = counts.join("  "),
        )
    }

    // ----- Quantum ESPRESSO pw.x input ------------------------------------

    /// Generate a Quantum ESPRESSO `pw.x` input file.
    pub fn generate_qe_input(&self, candidate: &DftCandidate) -> String {
        let a_bohr = estimate_lattice_constant(&candidate.elements) * 1.8897259886; // Angstrom -> Bohr
        let nat = candidate.elements.len();
        let ntyp = candidate.elements.len(); // simplified: unique count == len
        let ecutwfc = 60.0_f64; // Ry — conservative default
        let ecutrho = ecutwfc * 8.0;

        let atomic_species: String = candidate
            .elements
            .iter()
            .map(|el| {
                format!(
                    "  {el}  {mass:.4}  {el}.UPF",
                    el = el,
                    mass = approximate_mass(el),
                )
            })
            .collect::<Vec<_>>()
            .join("\n");

        let atomic_positions: String = candidate
            .elements
            .iter()
            .enumerate()
            .map(|(i, el)| {
                let frac = i as f64 / nat as f64;
                format!("  {el}  {x:.6}  {y:.6}  {z:.6}", el = el, x = frac, y = frac, z = frac)
            })
            .collect::<Vec<_>>()
            .join("\n");

        format!(
            "&CONTROL\n\
             \x20 calculation = 'scf'\n\
             \x20 prefix      = '{prefix}'\n\
             \x20 outdir      = './tmp'\n\
             \x20 pseudo_dir  = './pseudo'\n\
             /\n\
             &SYSTEM\n\
             \x20 ibrav  = 0\n\
             \x20 celldm(1) = {celldm:.6}\n\
             \x20 nat    = {nat}\n\
             \x20 ntyp   = {ntyp}\n\
             \x20 ecutwfc = {ecutwfc:.1}\n\
             \x20 ecutrho = {ecutrho:.1}\n\
             /\n\
             &ELECTRONS\n\
             \x20 mixing_beta = 0.3\n\
             \x20 conv_thr    = 1.0d-8\n\
             /\n\
             ATOMIC_SPECIES\n\
             {species}\n\
             ATOMIC_POSITIONS {{crystal}}\n\
             {positions}\n\
             K_POINTS {{automatic}}\n\
             \x20 6 6 6  0 0 0\n\
             CELL_PARAMETERS {{bohr}}\n\
             \x20 {celldm:.6}  0.000000  0.000000\n\
             \x20 0.000000  {celldm:.6}  0.000000\n\
             \x20 0.000000  0.000000  {celldm:.6}\n",
            prefix = candidate.formula.to_lowercase(),
            celldm = a_bohr,
            nat = nat,
            ntyp = ntyp,
            ecutwfc = ecutwfc,
            ecutrho = ecutrho,
            species = atomic_species,
            positions = atomic_positions,
        )
    }

    // ----- ranking ---------------------------------------------------------

    /// Rank candidates by a composite score (lower is better).
    ///
    /// Score = formation_energy - 0.5 * bandgap
    /// (more negative formation energy + larger bandgap = better score)
    ///
    /// Returns `(original_index, score)` sorted ascending.
    pub fn rank_candidates(&self, candidates: &[DftCandidate]) -> Vec<(usize, f64)> {
        let mut ranked: Vec<(usize, f64)> = candidates
            .iter()
            .enumerate()
            .map(|(i, c)| {
                let score = c.predicted_formation_energy - 0.5 * c.predicted_bandgap;
                (i, score)
            })
            .collect();
        ranked.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
        ranked
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Rough atomic masses for QE input (amu).
fn approximate_mass(element: &str) -> f64 {
    match element {
        "H" => 1.008,
        "Li" => 6.941,
        "Be" => 9.012,
        "B" => 10.81,
        "C" => 12.011,
        "N" => 14.007,
        "O" => 15.999,
        "F" => 18.998,
        "Na" => 22.990,
        "Mg" => 24.305,
        "Al" => 26.982,
        "Si" => 28.086,
        "P" => 30.974,
        "S" => 32.065,
        "Cl" => 35.453,
        "K" => 39.098,
        "Ca" => 40.078,
        "Ti" => 47.867,
        "V" => 50.942,
        "Cr" => 51.996,
        "Mn" => 54.938,
        "Fe" => 55.845,
        "Co" => 58.933,
        "Ni" => 58.693,
        "Cu" => 63.546,
        "Zn" => 65.38,
        "Ga" => 69.723,
        "Ge" => 72.63,
        "Se" => 78.971,
        "Sr" => 87.62,
        "Zr" => 91.224,
        "Nb" => 92.906,
        "Mo" => 95.95,
        "Ba" => 137.327,
        "La" => 138.905,
        "Ce" => 140.116,
        "Te" => 127.60,
        _ => 50.0, // fallback
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_candidates() -> Vec<DftCandidate> {
        vec![
            DftCandidate {
                formula: "LiCoO2".into(),
                elements: vec!["Li".into(), "Co".into(), "O".into()],
                spacegroup: "Fm-3m".into(),
                predicted_bandgap: 2.5,
                predicted_formation_energy: -1.2,
            },
            DftCandidate {
                formula: "NaMnO3".into(),
                elements: vec!["Na".into(), "Mn".into(), "O".into()],
                spacegroup: "Pm-3m".into(),
                predicted_bandgap: 1.8,
                predicted_formation_energy: -0.8,
            },
            // unstable — should be filtered out
            DftCandidate {
                formula: "FeS2".into(),
                elements: vec!["Fe".into(), "S".into()],
                spacegroup: "Pa-3".into(),
                predicted_bandgap: 0.9,
                predicted_formation_energy: 0.3,
            },
        ]
    }

    #[test]
    fn test_filter_removes_positive_formation_energy() {
        let pipe = DftPipeline::new();
        let result = pipe.filter_candidates(sample_candidates());
        assert_eq!(result.len(), 2);
        assert!(result.iter().all(|c| c.predicted_formation_energy < 0.0));
    }

    #[test]
    fn test_poscar_contains_formula() {
        let pipe = DftPipeline::new();
        let c = &sample_candidates()[0]; // LiCoO2, rocksalt
        let poscar = pipe.generate_poscar(c);
        assert!(poscar.contains("LiCoO2"));
        assert!(poscar.contains("rocksalt"));
    }

    #[test]
    fn test_poscar_perovskite_template() {
        let pipe = DftPipeline::new();
        let c = &sample_candidates()[1]; // NaMnO3, Pm-3m
        let poscar = pipe.generate_poscar(c);
        assert!(poscar.contains("perovskite"));
        assert!(poscar.contains("0.500000  0.500000  0.500000")); // B-site
    }

    #[test]
    fn test_qe_input_has_required_sections() {
        let pipe = DftPipeline::new();
        let c = &sample_candidates()[0];
        let qe = pipe.generate_qe_input(c);
        assert!(qe.contains("&CONTROL"));
        assert!(qe.contains("&SYSTEM"));
        assert!(qe.contains("ATOMIC_SPECIES"));
        assert!(qe.contains("ATOMIC_POSITIONS"));
        assert!(qe.contains("K_POINTS"));
        assert!(qe.contains("CELL_PARAMETERS"));
    }

    #[test]
    fn test_rank_order() {
        let pipe = DftPipeline::new();
        let candidates = sample_candidates();
        let ranked = pipe.rank_candidates(&candidates);
        // First entry should have the lowest (most negative) score
        assert!(ranked[0].1 <= ranked[1].1);
    }
}
