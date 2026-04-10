#!/usr/bin/env python3
"""Generate EVOL-011 through EVOL-110 hypothesis files."""

import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'hypotheses')

# (id, slug, title, hypothesis, table, ascii_art, meaning, grade, grade_text, limits, gz_dep)
hypotheses = []

def h(num, slug, title, hyp, table, ascii, meaning, grade, grade_text, limits, gz="GZ independent (biology)"):
    hypotheses.append((num, slug, title, hyp, table, ascii, meaning, grade, grade_text, limits, gz))

# ============================================================
# CELL BIOLOGY (011-025)
# ============================================================

h(11, "mitosis-six-phases", "Mitosis Phases = P1 = 6",
  "Mitosis consists of exactly 6 distinct phases: prophase, prometaphase, metaphase, anaphase, telophase, and cytokinesis = P1 = 6.",
  """| # | Phase | Key Event |
|---|-------|-----------|
| 1 | Prophase | Chromatin condenses |
| 2 | Prometaphase | Nuclear envelope breaks |
| 3 | Metaphase | Chromosomes align at plate |
| 4 | Anaphase | Sister chromatids separate |
| 5 | Telophase | Nuclear envelopes reform |
| 6 | Cytokinesis | Cytoplasm divides |""",
  """  Mitosis phase flow:

  [Pro] -> [Prometa] -> [Meta] -> [Ana] -> [Telo] -> [Cyto]
    1         2           3         4         5         6

  Total phases = 6 = P1""",
  "Cell division requires exactly P1 steps to faithfully segregate duplicated genomes.",
  "EXACT", "6 phases is standard cell biology (with prometaphase counted separately)",
  "Some textbooks merge prometaphase into prophase, giving 5 phases")

h(12, "cell-cycle-four-phases", "Cell Cycle Phases = tau(6) = 4",
  "The eukaryotic cell cycle has 4 phases: G1, S, G2, M = tau(6) = 4.",
  """| # | Phase | Function | Duration (typical) |
|---|-------|----------|-------------------|
| 1 | G1 | Growth, preparation | 10-12 hr |
| 2 | S | DNA synthesis | 6-8 hr |
| 3 | G2 | Growth, checkpoint | 2-4 hr |
| 4 | M | Mitosis | 1 hr |""",
  """  Cell Cycle (circular):

       G1
      /    \\
    M        S
      \\    /
       G2

  Phases = 4 = tau(6)""",
  "The cell cycle partitions into tau(6) phases, matching the divisor count of the first perfect number.",
  "EXACT", "4 cell cycle phases is universally accepted in cell biology",
  "Some descriptions add G0 (quiescent), making 5")

h(13, "meiosis-two-divisions", "Meiosis Divisions = phi(6) = 2",
  "Meiosis requires exactly 2 successive divisions (meiosis I and II) = phi(6) = 2.",
  """| Division | Type | Result |
|----------|------|--------|
| Meiosis I | Reductional | 2n -> n |
| Meiosis II | Equational | n -> n (sister chromatids) |""",
  """  Meiosis flow:

  [2n] --Meiosis I--> [n] --Meiosis II--> [n]

  Divisions = 2 = phi(6)

  Ploidy: 2n -> n -> n
  Cells:  1  -> 2 -> 4 = tau(6)""",
  "Meiosis uses phi(6) divisions to produce tau(6) daughter cells.",
  "EXACT", "2 meiotic divisions is a fundamental biological fact",
  "None -- universally accepted")

h(14, "meiosis-four-products", "Meiosis Products = tau(6) = 4",
  "Meiosis produces exactly 4 haploid cells from one diploid cell = tau(6) = 4.",
  """| Stage | Cell Count | Ploidy |
|-------|-----------|--------|
| Start | 1 | 2n |
| After Meiosis I | 2 | n |
| After Meiosis II | 4 | n |""",
  """  1 cell --> 2 cells --> 4 cells
  (2n)       (n)         (n)

  Final products = 4 = tau(6)""",
  "The doubling pattern 1->2->4 maps phi(6)->tau(6) exactly.",
  "EXACT", "4 meiotic products is universal in sexually reproducing organisms",
  "In oogenesis, only 1 of 4 becomes a viable egg (3 polar bodies)")

h(15, "organelle-double-membrane", "Double-Membrane Organelles = phi(6) + 1 = 3",
  "Eukaryotic cells have 3 double-membrane organelles: nucleus, mitochondria, chloroplasts = P1/2 = 3.",
  """| # | Organelle | Membranes | Origin |
|---|-----------|-----------|--------|
| 1 | Nucleus | 2 (envelope) | Invagination |
| 2 | Mitochondria | 2 (inner+outer) | Endosymbiosis |
| 3 | Chloroplast | 2 (inner+outer) | Endosymbiosis |""",
  """  Double-membrane organelles:

  Nucleus ====    Mito ====    Chloro ====
  ||      ||     ||    ||     ||      ||
  outer  inner   outer inner  outer  inner

  Count = 3 = P1/2""",
  "The 3 double-membrane organelles reflect the endosymbiotic origin of eukaryotic complexity.",
  "EXACT", "3 double-membrane organelles is standard cell biology",
  "Plant cells only; animal cells have 2 (no chloroplast)")

h(16, "lipid-bilayer-two-layers", "Lipid Bilayer = phi(6) = 2 Layers",
  "All biological membranes consist of a lipid bilayer = phi(6) = 2 leaflets.",
  """| Layer | Composition | Orientation |
|-------|-------------|-------------|
| Outer leaflet | Phospholipids | Hydrophilic heads out |
| Inner leaflet | Phospholipids | Hydrophilic heads in |""",
  """  Membrane cross-section:

  ~~~~~ hydrophilic ~~~~~   Outer leaflet
  ===== hydrophobic =====
  ===== hydrophobic =====
  ~~~~~ hydrophilic ~~~~~   Inner leaflet

  Leaflets = 2 = phi(6)""",
  "The universal bilayer structure = phi(6) is thermodynamically optimal for amphipathic molecules.",
  "EXACT", "Lipid bilayer is the universal membrane structure across all life",
  "None -- universally accepted")

h(17, "cytoskeleton-three-types", "Cytoskeleton Filament Types = P1/2 = 3",
  "The eukaryotic cytoskeleton has 3 major filament types: microfilaments, intermediate filaments, microtubules = P1/2 = 3.",
  """| # | Type | Diameter | Protein |
|---|------|----------|---------|
| 1 | Microfilaments | 7 nm | Actin |
| 2 | Intermediate filaments | 10 nm | Keratins etc. |
| 3 | Microtubules | 25 nm | Tubulin |""",
  """  Diameter scale:

  Micro:  ===     (7 nm)
  Inter:  ======  (10 nm)
  Micro:  ============= (25 nm)

  Types = 3 = P1/2""",
  "Structural integrity of cells requires exactly P1/2 filament systems.",
  "EXACT", "3 cytoskeletal types is universally taught in cell biology",
  "Some classify septins as a 4th type")

h(18, "cell-junctions-three-types", "Cell Junction Types = P1/2 = 3",
  "Animal cells have 3 major junction types: tight junctions, anchoring junctions, gap junctions = P1/2 = 3.",
  """| # | Junction | Function |
|---|---------|----------|
| 1 | Tight junctions | Seal between cells |
| 2 | Anchoring junctions | Mechanical attachment |
| 3 | Gap junctions | Communication channels |""",
  """  Epithelial cell junctions:

  ----[Tight]----    seal
  ----[Anchor]---    attach
  ----[Gap]------    communicate

  Types = 3 = P1/2""",
  "Intercellular communication requires exactly P1/2 junction categories.",
  "EXACT", "3 junction types is standard histology",
  "Anchoring junctions can be subdivided (desmosomes, hemidesmosomes, adherens)")

h(19, "cell-signaling-three-stages", "Cell Signaling Stages = P1/2 = 3",
  "Cell signaling has 3 stages: reception, transduction, response = P1/2 = 3.",
  """| # | Stage | Process |
|---|-------|---------|
| 1 | Reception | Signal binds receptor |
| 2 | Transduction | Relay cascade |
| 3 | Response | Cellular effect |""",
  """  Signal flow:

  [Ligand] -> [Receptor] -> [Cascade] -> [Effect]
              Reception    Transduction   Response

  Stages = 3 = P1/2""",
  "Signal processing follows the P1/2 pipeline structure.",
  "EXACT", "3-stage signaling is the standard framework",
  "More detailed models include additional steps")

h(20, "centriole-triplet-microtubules", "Centriole Microtubule Triplets = P1/2 per Group",
  "Each centriole has microtubules arranged in triplets (groups of 3) = P1/2, with 9 triplets total.",
  """| Structure | Count | n=6 relation |
|-----------|-------|-------------|
| Microtubules per triplet | 3 | P1/2 |
| Triplets per centriole | 9 | 3^2 = (P1/2)^2 |
| Centrioles per centrosome | 2 | phi(6) |""",
  """  Centriole cross-section (9 triplets):

       * *
     *     *
    *       *
     *     *
       * *
         *

  Triplets = 9 = (P1/2)^2
  MTs per triplet = 3 = P1/2""",
  "Centriole architecture encodes P1/2 at multiple scales.",
  "EXACT", "9x3 centriole structure is an established ultrastructural fact",
  "Some organisms have doublets or singlets instead of triplets")

h(21, "autophagy-types-three", "Autophagy Types = P1/2 = 3",
  "There are 3 main types of autophagy: macroautophagy, microautophagy, chaperone-mediated = P1/2 = 3.",
  """| # | Type | Mechanism |
|---|------|-----------|
| 1 | Macroautophagy | Double-membrane autophagosome |
| 2 | Microautophagy | Direct lysosomal invagination |
| 3 | Chaperone-mediated | Hsc70 + LAMP-2A translocation |""",
  """  Autophagy pathways:

  Macro:     [cargo]->[autophagosome]->[lysosome]
  Micro:     [cargo]--->[lysosome invagination]
  CMA:       [cargo+Hsc70]->[LAMP-2A]->[lysosome]

  Types = 3 = P1/2""",
  "Cellular self-digestion operates through P1/2 distinct pathways.",
  "EXACT", "3 autophagy types is standard classification",
  "Subtypes exist (e.g., mitophagy, xenophagy)")

h(22, "apoptosis-pathways-two", "Apoptosis Pathways = phi(6) = 2",
  "Programmed cell death has 2 major pathways: intrinsic (mitochondrial) and extrinsic (death receptor) = phi(6) = 2.",
  """| # | Pathway | Trigger | Key Molecule |
|---|---------|---------|-------------|
| 1 | Intrinsic | DNA damage, stress | Cytochrome c |
| 2 | Extrinsic | Death ligand | Fas/TRAIL |""",
  """  Apoptosis pathways converge:

  Intrinsic --\\
               --> Caspase-3 --> Cell death
  Extrinsic --/

  Pathways = 2 = phi(6)""",
  "Cell death decisions funnel through phi(6) independent pathways.",
  "EXACT", "2 apoptotic pathways is firmly established",
  "Perforin/granzyme pathway sometimes counted as 3rd")

h(23, "endocytosis-three-types", "Endocytosis Types = P1/2 = 3",
  "Major endocytosis types: phagocytosis, pinocytosis, receptor-mediated = P1/2 = 3.",
  """| # | Type | Cargo | Vesicle Size |
|---|------|-------|-------------|
| 1 | Phagocytosis | Large particles | >250 nm |
| 2 | Pinocytosis | Fluid | ~100 nm |
| 3 | Receptor-mediated | Specific ligands | ~120 nm |""",
  """  Endocytosis size scale:

  Phago:    [========]  large
  Pino:     [====]      medium
  Receptor: [=====]     specific

  Types = 3 = P1/2""",
  "Cells internalize material through P1/2 uptake mechanisms.",
  "EXACT", "3 endocytosis types is standard cell biology",
  "Caveolae-mediated sometimes counted separately")

h(24, "rna-polymerase-three-types", "Eukaryotic RNA Polymerases = P1/2 = 3",
  "Eukaryotes have 3 main RNA polymerases: Pol I, Pol II, Pol III = P1/2 = 3.",
  """| # | Polymerase | Product |
|---|-----------|---------|
| 1 | RNA Pol I | rRNA (28S, 18S, 5.8S) |
| 2 | RNA Pol II | mRNA, snRNA, miRNA |
| 3 | RNA Pol III | tRNA, 5S rRNA |""",
  """  Transcription division of labor:

  Pol I  --> rRNA (ribosome structural)
  Pol II --> mRNA (protein coding)
  Pol III --> tRNA (translation adaptor)

  Polymerases = 3 = P1/2""",
  "Gene expression requires P1/2 dedicated transcription machines.",
  "EXACT", "3 RNA polymerases in eukaryotes is firmly established",
  "Plants have Pol IV and Pol V for siRNA")

h(25, "cell-compartments-endomembrane", "Endomembrane System Components = P1 = 6",
  "The endomembrane system has 6 major components: ER, Golgi, lysosomes, endosomes, vesicles, plasma membrane = P1 = 6.",
  """| # | Component | Function |
|---|-----------|----------|
| 1 | Endoplasmic reticulum | Synthesis |
| 2 | Golgi apparatus | Modification/sorting |
| 3 | Lysosomes | Degradation |
| 4 | Endosomes | Sorting/recycling |
| 5 | Transport vesicles | Trafficking |
| 6 | Plasma membrane | Boundary |""",
  """  Endomembrane flow:

  ER -> Golgi -> Vesicles -> Plasma membrane
         |                      |
         v                      v
      Lysosomes            Endosomes

  Components = 6 = P1""",
  "The membrane trafficking system comprises exactly P1 stations.",
  "WEAK", "Classification varies by source; some add peroxisomes or vacuoles",
  "Not all sources count exactly 6; depends on textbook")

# ============================================================
# MOLECULAR BIOLOGY (026-045)
# ============================================================

h(26, "rna-six-types", "Major RNA Types = P1 = 6",
  "There are 6 major types of RNA: mRNA, tRNA, rRNA, snRNA, miRNA, siRNA = P1 = 6.",
  """| # | RNA Type | Function |
|---|---------|----------|
| 1 | mRNA | Protein coding |
| 2 | tRNA | Amino acid adaptor |
| 3 | rRNA | Ribosome structure |
| 4 | snRNA | Splicing |
| 5 | miRNA | Gene silencing |
| 6 | siRNA | RNA interference |""",
  """  RNA functional map:

  Coding:      mRNA
  Translation: tRNA, rRNA
  Processing:  snRNA
  Regulation:  miRNA, siRNA

  Total types = 6 = P1""",
  "The RNA world divides into exactly P1 functional categories.",
  "WEAK", "6 major RNA types is commonly taught",
  "piRNA, lncRNA, circRNA, snoRNA etc. expand the list beyond 6")

h(27, "histone-five-types", "Core Histone Types = sopfr(6) = 5",
  "There are 5 histone types: H1, H2A, H2B, H3, H4 = sopfr(6) = 5.",
  """| # | Histone | Role | Copies/nucleosome |
|---|---------|------|------------------|
| 1 | H2A | Core | 2 |
| 2 | H2B | Core | 2 |
| 3 | H3 | Core | 2 |
| 4 | H4 | Core | 2 |
| 5 | H1 | Linker | 1 |""",
  """  Nucleosome structure:

      H1 (linker)
       |
  [H2A-H2B]--DNA--[H3-H4]
  [H2A-H2B]       [H3-H4]

  Core octamer = 4 types x 2 = 8 proteins
  Total histone types = 5 = sopfr(6)""",
  "Chromatin packaging uses sopfr(6) histone types, with tau(6) core types.",
  "EXACT", "5 canonical histone types is universally accepted",
  "Histone variants (H2A.Z, H3.3 etc.) exist but are variants, not new types")

h(28, "spliceosome-five-snrnps", "Spliceosome snRNPs = sopfr(6) = 5",
  "The major spliceosome contains 5 snRNPs: U1, U2, U4, U5, U6 = sopfr(6) = 5.",
  """| # | snRNP | Role in Splicing |
|---|-------|-----------------|
| 1 | U1 | 5' splice site recognition |
| 2 | U2 | Branch point binding |
| 3 | U4 | U6 chaperone |
| 4 | U5 | Exon alignment |
| 5 | U6 | Catalytic center |""",
  """  Spliceosome assembly:

  pre-mRNA: ==exon1==[intron]==exon2==
                |
  U1 binds 5'ss -> U2 binds BP -> U4/U6.U5 joins

  snRNPs = 5 = sopfr(6)
  Note: U3 is NOT in spliceosome (it is nucleolar)""",
  "RNA splicing requires sopfr(6) small nuclear ribonucleoprotein particles.",
  "EXACT", "5 spliceosomal snRNPs is a firmly established fact",
  "Minor spliceosome uses U11, U12, U4atac, U6atac instead")

h(29, "protein-secondary-structures-four", "Protein Secondary Structures = tau(6) = 4",
  "There are 4 levels of protein structure: primary, secondary, tertiary, quaternary = tau(6) = 4.",
  """| # | Level | Description |
|---|-------|-------------|
| 1 | Primary | Amino acid sequence |
| 2 | Secondary | Alpha-helix, beta-sheet |
| 3 | Tertiary | 3D fold |
| 4 | Quaternary | Multi-subunit assembly |""",
  """  Protein structure hierarchy:

  Sequence -> Helix/Sheet -> 3D Fold -> Complex
  Primary    Secondary     Tertiary   Quaternary
    1            2             3          4

  Levels = 4 = tau(6)""",
  "Protein organization has tau(6) hierarchical levels.",
  "EXACT", "4 levels of protein structure is universally taught",
  "Not all proteins have quaternary structure (only multimeric ones)")

h(30, "ribosome-two-subunits", "Ribosome Subunits = phi(6) = 2",
  "All ribosomes consist of exactly 2 subunits: large and small = phi(6) = 2.",
  """| Organism | Small | Large | Combined |
|----------|-------|-------|----------|
| Prokaryote | 30S | 50S | 70S |
| Eukaryote | 40S | 60S | 80S |""",
  """  Ribosome assembly:

  [Small subunit] + [Large subunit] = [Ribosome]
       30S/40S          50S/60S         70S/80S

  Subunits = 2 = phi(6)
  Universal across ALL domains of life""",
  "Translation machinery universally consists of phi(6) subunits.",
  "EXACT", "2 ribosomal subunits is universal across all life",
  "None -- absolutely universal")

h(31, "dna-double-helix-two-strands", "DNA Strands = phi(6) = 2",
  "DNA is a double helix with exactly 2 antiparallel strands = phi(6) = 2.",
  """| Property | Value |
|----------|-------|
| Strands | 2 = phi(6) |
| Base pairs per turn | 10 |
| Helix diameter | 2 nm = phi(6) nm |
| Groove types | 2 (major + minor) = phi(6) |""",
  """  DNA cross-section:

  5'----A==T----3'
  3'----T==A----5'
  5'----G===C---3'
  3'----C===G---5'

  Strands = 2 = phi(6)
  Grooves = 2 = phi(6)""",
  "The molecule of life encodes phi(6) at multiple structural levels.",
  "EXACT", "Double-stranded DNA is the universal genetic material",
  "Some viruses use single-stranded DNA or RNA")

h(32, "start-codon-one", "Start Codons = 1 = Divisor of 6",
  "There is exactly 1 universal start codon (AUG) = smallest divisor of 6.",
  """| Codon | Amino Acid | Function |
|-------|-----------|----------|
| AUG | Methionine | Start codon (universal) |""",
  """  Translation initiation:

  5'-...AUG...UAA/UAG/UGA...-3'
       START              STOP
       1 codon          3 codons

  Start = 1 (divisor of 6)
  Stop = 3 = P1/2""",
  "Translation starts with 1 codon and stops with P1/2 codons.",
  "EXACT", "1 start codon (AUG) is universal",
  "Some organisms use alternative start codons rarely (GUG, UUG in bacteria)")

h(33, "stop-codons-three", "Stop Codons = P1/2 = 3",
  "There are exactly 3 stop codons: UAA, UAG, UGA = P1/2 = 3.",
  """| # | Codon | Name |
|---|-------|------|
| 1 | UAA | Ochre |
| 2 | UAG | Amber |
| 3 | UGA | Opal |""",
  """  Codon usage:

  64 total codons (2^6 = 2^P1)
  61 sense codons
   3 stop codons = P1/2

  61 + 3 = 64 = 2^P1""",
  "Translation termination uses P1/2 stop signals out of 2^P1 total codons.",
  "EXACT", "3 stop codons is a fundamental fact of the genetic code",
  "UGA codes for selenocysteine in some contexts")

h(34, "nucleotide-components-three", "Nucleotide Components = P1/2 = 3",
  "Each nucleotide has 3 components: base, sugar, phosphate = P1/2 = 3.",
  """| # | Component | Examples |
|---|-----------|---------|
| 1 | Nitrogenous base | A, T/U, G, C |
| 2 | Pentose sugar | Deoxyribose/Ribose |
| 3 | Phosphate group | PO4 |""",
  """  Nucleotide structure:

  [Base]---[Sugar]---[Phosphate]
    |         |          |
  Identity  Backbone   Energy/Link

  Components = 3 = P1/2""",
  "The building blocks of genetic information have P1/2 parts.",
  "EXACT", "3 nucleotide components is basic biochemistry",
  "None -- universally accepted")

h(35, "central-dogma-three-steps", "Central Dogma Steps = P1/2 = 3",
  "The central dogma of molecular biology has 3 information transfers: replication, transcription, translation = P1/2 = 3.",
  """| # | Process | From | To |
|---|---------|------|-----|
| 1 | Replication | DNA | DNA |
| 2 | Transcription | DNA | RNA |
| 3 | Translation | RNA | Protein |""",
  """  Central Dogma flow:

  DNA --replication--> DNA
   |
   +--transcription--> RNA --translation--> Protein

  Steps = 3 = P1/2""",
  "Information flow in biology follows P1/2 canonical pathways.",
  "EXACT", "3 steps of the central dogma is foundational molecular biology",
  "Reverse transcription, RNA replication add complexity")

h(36, "codon-reading-frame-three", "Codon Reading Frame = P1/2 = 3",
  "Codons are read in a reading frame of 3 nucleotides = P1/2.",
  """| Position | Role |
|----------|------|
| 1st | Most important for amino acid identity |
| 2nd | Chemical property determinant |
| 3rd | Wobble position (degenerate) |""",
  """  Reading frame:

  ...AUG|GCU|AAA|UGA...
     ^^^|^^^|^^^|^^^
     Met Ala Lys Stop

  Nucleotides per codon = 3 = P1/2
  Possible reading frames = 3 = P1/2""",
  "The genetic code reads P1/2 bases at a time, with P1/2 possible frames.",
  "EXACT", "Triplet codon is universal",
  "None -- absolutely universal")

h(37, "dna-replication-origins", "Replication Fork Components = P1/2 = 3",
  "DNA replication fork has 3 key enzymatic activities: helicase (unwinding), primase (priming), polymerase (synthesis) = P1/2 = 3.",
  """| # | Enzyme | Function |
|---|--------|----------|
| 1 | Helicase | Unwind double helix |
| 2 | Primase | Synthesize RNA primer |
| 3 | DNA Polymerase | Synthesize new strand |""",
  """  Replication fork:

  Helicase ---> Primase ---> Polymerase
  (unwind)     (prime)      (extend)

  Core enzymes = 3 = P1/2""",
  "DNA replication requires P1/2 core enzymatic steps.",
  "WEAK", "3 core enzymes is a simplification; SSB, ligase, topoisomerase also essential",
  "Many more proteins are required at the replication fork")

h(38, "trna-three-binding-sites", "Ribosome tRNA Sites = P1/2 = 3",
  "The ribosome has 3 tRNA binding sites: A (aminoacyl), P (peptidyl), E (exit) = P1/2 = 3.",
  """| # | Site | Function |
|---|------|----------|
| 1 | A-site | Incoming aminoacyl-tRNA |
| 2 | P-site | Peptidyl-tRNA (growing chain) |
| 3 | E-site | Exit of deacylated tRNA |""",
  """  Ribosome tRNA flow:

  --> [A-site] --> [P-site] --> [E-site] -->
     incoming     growing      exiting

  Binding sites = 3 = P1/2""",
  "Translation elongation cycles through P1/2 tRNA positions.",
  "EXACT", "3 ribosomal tRNA sites is universally established",
  "None -- universal across all domains of life")

h(39, "rna-splicing-two-steps", "RNA Splicing Transesterifications = phi(6) = 2",
  "Pre-mRNA splicing occurs via exactly 2 transesterification reactions = phi(6) = 2.",
  """| Step | Reaction | Result |
|------|----------|--------|
| 1 | 2'-OH attacks 5' splice site | Lariat intermediate |
| 2 | 3'-OH of exon1 attacks 3' splice site | Ligated exons |""",
  """  Splicing mechanism:

  Step 1: exon1--[intron==exon2  ->  exon1  +  lariat-exon2
  Step 2: exon1 + lariat-exon2  ->  exon1==exon2  +  lariat

  Transesterifications = 2 = phi(6)""",
  "Intron removal requires exactly phi(6) chemical steps.",
  "EXACT", "2-step splicing mechanism is a proven biochemical fact",
  "None -- well established")

h(40, "nucleosome-histone-octamer", "Nucleosome Core = 2^P1/2 = 8 Histones",
  "Each nucleosome core particle contains 8 histone proteins (2 each of H2A, H2B, H3, H4) = 2^(P1/2) = 8.",
  """| Histone | Copies | Type |
|---------|--------|------|
| H2A | 2 | Core |
| H2B | 2 | Core |
| H3 | 2 | Core |
| H4 | 2 | Core |
| Total | 8 = 2^3 | |""",
  """  Nucleosome:

      ~~~~DNA~~~~
     /            \\
    | H2A H2B      |
    |   H3 H4      |  x 2
     \\            /
      ~~~~DNA~~~~

  Histones = 8 = 2^(P1/2)
  DNA wrapped = ~147 bp""",
  "The histone octamer = 2^(P1/2) is the fundamental chromatin unit.",
  "EXACT", "8 histones per nucleosome is an established structural fact",
  "None -- crystallographically proven")

h(41, "dna-bases-purines-pyrimidines", "Base Classification = phi(6) Groups",
  "DNA bases divide into 2 chemical classes: purines and pyrimidines = phi(6) = 2.",
  """| Class | Members | Rings |
|-------|---------|-------|
| Purines | A, G | 2 double-ring |
| Pyrimidines | C, T/U | 1 single-ring |""",
  """  Base pairing (Chargaff):

  Purine   Pyrimidine
  A ======= T    (2 H-bonds)
  G ======= C    (3 H-bonds)

  Classes = 2 = phi(6)
  Members per class = 2 = phi(6)""",
  "Base complementarity operates across phi(6) chemical classes.",
  "EXACT", "2 base classes is fundamental chemistry",
  "None -- basic organic chemistry")

h(42, "gene-expression-two-steps", "Gene Expression = phi(6) = 2 Steps",
  "Gene expression has 2 main steps: transcription and translation = phi(6) = 2.",
  """| # | Step | Location (eukaryote) |
|---|------|---------------------|
| 1 | Transcription | Nucleus |
| 2 | Translation | Cytoplasm/ER |""",
  """  Gene expression flow:

  [DNA] --transcription--> [mRNA] --translation--> [Protein]
         Step 1                     Step 2

  Steps = 2 = phi(6)""",
  "Converting genetic information to protein requires phi(6) sequential steps.",
  "EXACT", "2-step gene expression is universally accepted",
  "RNA processing (capping, splicing, polyadenylation) adds intermediate steps")

h(43, "operon-three-components", "Operon Components = P1/2 = 3",
  "A bacterial operon has 3 regulatory components: promoter, operator, structural genes = P1/2 = 3.",
  """| # | Component | Function |
|---|-----------|----------|
| 1 | Promoter | RNA pol binding |
| 2 | Operator | Repressor binding |
| 3 | Structural genes | Protein coding |""",
  """  Operon structure:

  |--Promoter--|--Operator--|--Gene1--Gene2--Gene3--|
       P            O              Structural

  Regulatory units = 3 = P1/2""",
  "Prokaryotic gene regulation uses P1/2 architectural elements.",
  "EXACT", "3-component operon model (Jacob-Monod) is classic genetics",
  "Enhancers, attenuators add complexity in some operons")

h(44, "pcr-three-steps", "PCR Cycle Steps = P1/2 = 3",
  "Each PCR cycle has 3 temperature steps: denaturation, annealing, extension = P1/2 = 3.",
  """| # | Step | Temperature | Purpose |
|---|------|-------------|---------|
| 1 | Denaturation | 94-98C | Separate strands |
| 2 | Annealing | 50-65C | Primer binding |
| 3 | Extension | 72C | DNA synthesis |""",
  """  PCR temperature profile:

  95C  ___         ___         ___
      |   |       |   |       |   |
  72C |   |  ___  |   |  ___  |   |  ___
      |   | |   | |   | |   | |   | |   |
  55C |   |_|   |_|   |_|   |_|   |_|   |
      Cycle 1     Cycle 2     Cycle 3

  Steps per cycle = 3 = P1/2""",
  "DNA amplification uses P1/2 thermal steps per cycle.",
  "EXACT", "3 PCR steps is a defined laboratory protocol",
  "Two-step PCR combines annealing+extension")

h(45, "translation-three-phases", "Translation Phases = P1/2 = 3",
  "Protein translation has 3 phases: initiation, elongation, termination = P1/2 = 3.",
  """| # | Phase | Key Event |
|---|-------|-----------|
| 1 | Initiation | AUG recognition, ribosome assembly |
| 2 | Elongation | Peptide bond formation |
| 3 | Termination | Stop codon, release factors |""",
  """  Translation flow:

  [Init] --> [Elongation...] --> [Termination]
   AUG       Peptide bonds       Stop codon
     1            2                  3

  Phases = 3 = P1/2""",
  "Protein synthesis follows P1/2 sequential phases.",
  "EXACT", "3 translation phases is universally taught",
  "None -- universally accepted")

# ============================================================
# BIOCHEMISTRY (046-065)
# ============================================================

h(46, "photosynthesis-six-co2", "Photosynthesis: 6CO2 + 6H2O = P1 Everywhere",
  "The photosynthesis equation 6CO2 + 6H2O -> C6H12O6 + 6O2 has P1=6 appearing in EVERY coefficient and the product structure.",
  """| Component | Count | n=6 relation |
|-----------|-------|-------------|
| CO2 molecules | 6 | P1 |
| H2O molecules | 6 | P1 |
| O2 molecules | 6 | P1 |
| Carbons in glucose | 6 | P1 |
| Hydrogens in glucose | 12 | sigma(6) |
| Oxygens in glucose | 6 | P1 |""",
  """  Photosynthesis equation:

  6 CO2 + 6 H2O  -->  C6 H12 O6 + 6 O2
  ^       ^            ^  ^   ^    ^
  P1      P1           P1 s6  P1   P1

  Every single coefficient = P1 or sigma(6)!
  This is the most P1-dense equation in all of science.""",
  "The equation that sustains all life on Earth is saturated with P1=6.",
  "EXACT", "Photosynthesis stoichiometry is exact chemistry -- no room for interpretation",
  "None -- this is a balanced chemical equation")

h(47, "glucose-six-carbons", "Glucose = C6 (P1 Carbons)",
  "Glucose, the universal energy currency of life, has exactly 6 carbon atoms = P1.",
  """| Property | Value | n=6 relation |
|----------|-------|-------------|
| Carbons | 6 | P1 |
| Hydrogens | 12 | sigma(6) |
| Oxygens | 6 | P1 |
| Molecular formula | C6H12O6 | P1, sigma(6), P1 |""",
  """  Glucose structure (Fischer projection):

       CHO
       |
  H -- C -- OH     Carbon 1
       |
  HO - C -- H      Carbon 2
       |
  H -- C -- OH     Carbon 3
       |
  H -- C -- OH     Carbon 4
       |
       CH2OH       Carbon 5-6

  Carbons = 6 = P1""",
  "Life's primary fuel molecule contains exactly P1 carbon atoms.",
  "EXACT", "Glucose has 6 carbons -- this is a chemical fact",
  "None -- molecular formula is exact")

h(48, "glucose-twelve-hydrogens", "Glucose Hydrogens = sigma(6) = 12",
  "Glucose (C6H12O6) contains exactly 12 hydrogen atoms = sigma(6) = 12.",
  """| Atom | Count | n=6 relation |
|------|-------|-------------|
| C | 6 | P1 |
| H | 12 | sigma(6) |
| O | 6 | P1 |""",
  """  Glucose atomic composition:

  C:  ****** (6 = P1)
  H:  ************ (12 = sigma(6))
  O:  ****** (6 = P1)

  H/C ratio = 12/6 = sigma(6)/P1 = 2 = phi(6)""",
  "Even the H/C ratio of glucose equals phi(6).",
  "EXACT", "C6H12O6 is the molecular formula of glucose",
  "None -- exact chemistry")

h(49, "pyranose-six-membered-ring", "Pyranose Ring = P1 = 6 Atoms",
  "Glucose in solution forms a pyranose ring with 6 atoms (5C + 1O) = P1.",
  """| Position | Atom | Substituent |
|----------|------|------------|
| 1 | C | OH (anomeric) |
| 2 | C | OH |
| 3 | C | OH |
| 4 | C | OH |
| 5 | C | CH2OH |
| 6 | O | (ring oxygen) |""",
  """  Pyranose ring (Haworth projection):

       O
      / \\
     C   C
     |   |
     C   C
      \\ /
       C

  Ring atoms = 6 = P1
  (5 carbons + 1 oxygen)""",
  "The dominant form of glucose in solution is a P1-membered ring.",
  "EXACT", "Pyranose = 6-membered ring is definitional",
  "None -- structural chemistry fact")

h(50, "etc-four-complexes", "Electron Transport Chain Complexes = tau(6) = 4",
  "The mitochondrial electron transport chain has 4 main complexes: I, II, III, IV = tau(6) = 4.",
  """| # | Complex | Function |
|---|---------|----------|
| I | NADH dehydrogenase | NADH oxidation |
| II | Succinate dehydrogenase | FADH2 oxidation |
| III | Cytochrome bc1 | Q cycle |
| IV | Cytochrome c oxidase | O2 reduction |""",
  """  Electron flow:

  NADH -> [I] -> Q -> [III] -> Cyt c -> [IV] -> O2
  FADH2 -> [II] -/

  Complexes = 4 = tau(6)
  (ATP synthase = Complex V, but not in ETC proper)""",
  "Oxidative phosphorylation chains tau(6) electron carriers.",
  "EXACT", "4 ETC complexes is standard biochemistry",
  "ATP synthase (Complex V) sometimes included, making 5")

h(51, "atp-three-phosphates", "ATP Phosphate Groups = P1/2 = 3",
  "Adenosine triphosphate has 3 phosphate groups = P1/2 = 3.",
  """| Phosphate | Bond | Energy Release |
|-----------|------|---------------|
| Alpha (alpha) | Ester bond | Low |
| Beta (beta) | Anhydride | ~30.5 kJ/mol |
| Gamma (gamma) | Anhydride | ~30.5 kJ/mol |""",
  """  ATP structure:

  Adenine--Ribose--PO4--PO4--PO4
                    a     b     g
                   (low) (high) (high)

  Phosphates = 3 = P1/2

  ATP -> ADP + Pi  (removes 1 of 3)
  ADP -> AMP + Pi  (removes 1 of 2)""",
  "The energy currency of all life carries P1/2 phosphate groups.",
  "EXACT", "ATP has 3 phosphates by definition (tri-phosphate)",
  "None -- definitional")

h(52, "essential-fatty-acids-two", "Essential Fatty Acids = phi(6) = 2",
  "Humans have exactly 2 essential fatty acids: linoleic acid (omega-6) and alpha-linolenic acid (omega-3) = phi(6) = 2.",
  """| # | Fatty Acid | Class | Carbons |
|---|-----------|-------|---------|
| 1 | Linoleic acid | Omega-6 | 18:2 |
| 2 | Alpha-linolenic acid | Omega-3 | 18:3 |""",
  """  Essential fatty acid classes:

  Omega-6: ...=C-C=C-C-C-C-COOH  (linoleic)
  Omega-3: ...=C-C=C-C=C-C-COOH  (alpha-linolenic)

  Essential FAs = 2 = phi(6)
  Omega classes = 2 = phi(6)""",
  "The body cannot synthesize phi(6) fatty acids -- they must come from diet.",
  "EXACT", "2 essential fatty acids is standard nutrition science",
  "Some consider conditionally essential FAs (DHA, EPA, ARA)")

h(53, "deciduous-teeth-twenty", "Deciduous Teeth = tau(6) x sopfr(6) = 20",
  "Humans have 20 deciduous (baby) teeth = tau(6) x sopfr(6) = 4 x 5 = 20.",
  """| Quadrant | Incisors | Canine | Molars | Total |
|----------|----------|--------|--------|-------|
| Upper R | 2 | 1 | 2 | 5 |
| Upper L | 2 | 1 | 2 | 5 |
| Lower R | 2 | 1 | 2 | 5 |
| Lower L | 2 | 1 | 2 | 5 |
| Total | 8 | 4 | 8 | 20 |""",
  """  Dental formula (deciduous):

  Upper:  2-1-2 | 2-1-2
  Lower:  2-1-2 | 2-1-2

  Per quadrant = 5 = sopfr(6)
  Quadrants = 4 = tau(6)
  Total = 20 = tau(6) x sopfr(6)""",
  "Primary dentition = tau(6) quadrants x sopfr(6) teeth each.",
  "EXACT", "20 deciduous teeth is a standard anatomical fact",
  "None -- universally accepted in humans")

h(54, "coagulation-factors-twelve", "Blood Coagulation Factors = sigma(6) = 12",
  "The classical coagulation cascade has 12 named factors: I through XIII (no VI) = sigma(6) = 12.",
  """| Factor | Name | Pathway |
|--------|------|---------|
| I | Fibrinogen | Common |
| II | Prothrombin | Common |
| III | Tissue factor | Extrinsic |
| IV | Calcium | Both |
| V | Proaccelerin | Common |
| VII | Proconvertin | Extrinsic |
| VIII | Anti-hemophilic A | Intrinsic |
| IX | Anti-hemophilic B | Intrinsic |
| X | Stuart-Prower | Common |
| XI | PTA | Intrinsic |
| XII | Hageman | Intrinsic |
| XIII | Fibrin stabilizing | Common |""",
  """  Coagulation cascade:

  Intrinsic: XII->XI->IX->VIII \\
                                --> X->V->II->I->XIII
  Extrinsic: III->VII          /

  Named factors = 12 = sigma(6)
  (Factor VI was found to be activated Factor V)""",
  "Blood clotting requires sigma(6) coagulation factors.",
  "EXACT", "12 coagulation factors (I-XIII minus VI) is standard hematology",
  "Additional factors like prekallikrein, HMWK sometimes included")

h(55, "krebs-cycle-eight-steps", "Krebs Cycle Steps = 2^(P1/2) = 8",
  "The citric acid (Krebs) cycle has 8 enzymatic steps = 2^(P1/2) = 8.",
  """| # | Enzyme | Substrate -> Product |
|---|--------|---------------------|
| 1 | Citrate synthase | OAA + Acetyl-CoA -> Citrate |
| 2 | Aconitase | Citrate -> Isocitrate |
| 3 | Isocitrate DH | Isocitrate -> alpha-KG |
| 4 | alpha-KG DH | alpha-KG -> Succinyl-CoA |
| 5 | Succinyl-CoA synthetase | Succinyl-CoA -> Succinate |
| 6 | Succinate DH | Succinate -> Fumarate |
| 7 | Fumarase | Fumarate -> Malate |
| 8 | Malate DH | Malate -> OAA |""",
  """  Krebs Cycle (circular):

  OAA -1-> Citrate -2-> Isocitrate
   ^                        |
   8                        3
   |                        v
  Malate              alpha-KG
   ^                        |
   7                        4
   |                        v
  Fumarate <-6- Succinate <-5- Succinyl-CoA

  Steps = 8 = 2^(P1/2)""",
  "Central metabolism cycles through 2^(P1/2) enzymatic reactions.",
  "EXACT", "8 steps in the Krebs cycle is standard biochemistry",
  "None -- universally accepted")

h(56, "glycolysis-ten-steps", "Glycolysis Steps = P1 + tau(6) = 10",
  "Glycolysis has exactly 10 enzymatic steps = P1 + tau(6) = 6 + 4 = 10.",
  """| Phase | Steps | n=6 relation |
|-------|-------|-------------|
| Energy investment | 1-5 | sopfr(6) steps |
| Energy payoff | 6-10 | sopfr(6) steps |
| Total | 10 | P1 + tau(6) |""",
  """  Glycolysis:

  Glucose -> [5 steps] -> G3P x2 -> [5 steps] -> 2 Pyruvate
           Investment              Payoff
           5 = sopfr(6)            5 = sopfr(6)

  Total = 10 = P1 + tau(6)""",
  "Glucose breakdown uses P1+tau(6) steps, split into sopfr(6)+sopfr(6).",
  "EXACT", "10 glycolysis steps is a standard biochemical fact",
  "None -- universally accepted")

h(57, "benzene-six-carbons", "Benzene Ring = P1 = 6",
  "Benzene, the fundamental aromatic ring, has exactly 6 carbon atoms = P1.",
  """| Property | Value | n=6 relation |
|----------|-------|-------------|
| Carbons | 6 | P1 |
| Hydrogens | 6 | P1 |
| C-C bonds | 6 | P1 |
| pi electrons | 6 | P1 |""",
  """  Benzene (C6H6):

      H
      |
  H - C - H
     / \\
    C   C     6 carbons in ring
    ||  ||    6 pi electrons
    C   C     6 H atoms
     \\ /
  H - C - H
      |
      H

  Everything = 6 = P1""",
  "Aromatic chemistry is built on the P1-membered ring.",
  "EXACT", "Benzene has 6 carbons by definition",
  "None -- fundamental organic chemistry")

h(58, "amino-acid-groups-four", "Amino Acid Functional Groups = tau(6) = 4",
  "Every amino acid has 4 key groups: amino, carboxyl, hydrogen, R-group = tau(6) = 4.",
  """| # | Group | Role |
|---|-------|------|
| 1 | Amino (-NH2) | Base, peptide bond |
| 2 | Carboxyl (-COOH) | Acid, peptide bond |
| 3 | Hydrogen (-H) | Chirality |
| 4 | R-group (side chain) | Identity/function |""",
  """  Amino acid general structure:

       NH2
        |
  HOOC--C--R
        |
        H

  Groups around alpha-carbon = 4 = tau(6)""",
  "The amino acid scaffold attaches tau(6) substituents to the central carbon.",
  "EXACT", "4 groups on the alpha-carbon is definitional",
  "Glycine has H as R-group, so technically only 3 unique groups")

h(59, "water-molecule-three-atoms", "Water Molecule = P1/2 = 3 Atoms",
  "Water (H2O) consists of 3 atoms: 2 hydrogens + 1 oxygen = P1/2 = 3.",
  """| Atom | Count | Bond Angle |
|------|-------|-----------|
| O | 1 | -- |
| H | 2 | 104.5 degrees |
| Total | 3 = P1/2 | |""",
  """  Water molecule:

    H     H
     \\   /
      O        angle = 104.5 degrees

  Atoms = 3 = P1/2
  The solvent of life""",
  "The molecule enabling all biochemistry has P1/2 atoms.",
  "EXACT", "H2O has 3 atoms -- this is chemistry",
  "None -- trivially true")

h(60, "nadh-carries-two-electrons", "NADH Electron Carriers = phi(6) = 2",
  "The two universal electron carriers in metabolism are NAD+/NADH and FAD/FADH2 = phi(6) = 2.",
  """| # | Carrier | Electrons | Destination |
|---|---------|-----------|-------------|
| 1 | NADH | 2e- + H+ | Complex I |
| 2 | FADH2 | 2e- | Complex II |""",
  """  Electron carrier systems:

  Substrate -> NAD+ -> NADH -> Complex I -> ETC
  Substrate -> FAD  -> FADH2 -> Complex II -> ETC

  Major carriers = 2 = phi(6)
  Electrons per carrier = 2 = phi(6)""",
  "Metabolic redox uses phi(6) major electron carriers, each transferring phi(6) electrons.",
  "EXACT", "NAD and FAD are the 2 major electron carriers",
  "Ubiquinone and cytochrome c also carry electrons but are not primary donors")

h(61, "fatty-acid-synthesis-two-carbons", "Fatty Acid Extension = phi(6) = 2C per Cycle",
  "Fatty acid synthesis extends the chain by 2 carbons per cycle = phi(6) = 2.",
  """| Cycle | Carbons Added | Total (palmitate) |
|-------|-------------|------------------|
| 1 | 2 | 4 |
| 2 | 2 | 6 |
| 3 | 2 | 8 |
| ... | 2 | ... |
| 7 | 2 | 16 |""",
  """  Fatty acid synthesis (palmitate, 16C):

  Acetyl-CoA (2C) + Malonyl-CoA (3C) -> +2C per cycle

  Cycles: 2->4->6->8->10->12->14->16
  Extension per cycle = 2 = phi(6)""",
  "Lipid biosynthesis adds phi(6) carbons per elongation cycle.",
  "EXACT", "2-carbon extension per cycle is established biochemistry",
  "None -- well established")

h(62, "vitamin-classes-two", "Vitamin Solubility Classes = phi(6) = 2",
  "Vitamins are classified into 2 groups: fat-soluble and water-soluble = phi(6) = 2.",
  """| Class | Members | Count |
|-------|---------|-------|
| Fat-soluble | A, D, E, K | 4 = tau(6) |
| Water-soluble | B-complex + C | 9 |
| Total classes | | 2 = phi(6) |""",
  """  Vitamin classification:

  Fat-soluble:   A  D  E  K     (4 = tau(6))
  Water-soluble: B1 B2 B3 B5 B6 B7 B9 B12 C  (9)

  Classes = 2 = phi(6)
  Fat-soluble count = 4 = tau(6)""",
  "Vitamin classes = phi(6), with fat-soluble count = tau(6).",
  "EXACT", "2 vitamin solubility classes is standard nutrition",
  "None -- standard classification")

h(63, "fat-soluble-vitamins-four", "Fat-Soluble Vitamins = tau(6) = 4",
  "There are exactly 4 fat-soluble vitamins: A, D, E, K = tau(6) = 4.",
  """| # | Vitamin | Function |
|---|---------|----------|
| 1 | A | Vision, immunity |
| 2 | D | Calcium absorption |
| 3 | E | Antioxidant |
| 4 | K | Blood clotting |""",
  """  Fat-soluble vitamins:

  A  D  E  K
  1  2  3  4  = tau(6)

  Mnemonic: "ADEK" (all stored in fat tissue)""",
  "The fat-soluble vitamin set has exactly tau(6) members.",
  "EXACT", "4 fat-soluble vitamins is universally accepted",
  "None -- definitional in nutrition science")

h(64, "nucleotide-bases-four", "DNA/RNA Bases per Molecule = tau(6) = 4",
  "Both DNA and RNA use exactly 4 different bases each = tau(6) = 4.",
  """| # | DNA Base | RNA Base |
|---|---------|---------|
| 1 | Adenine | Adenine |
| 2 | Guanine | Guanine |
| 3 | Cytosine | Cytosine |
| 4 | Thymine | Uracil |""",
  """  Base alphabet:

  DNA: {A, G, C, T}  = 4 = tau(6)
  RNA: {A, G, C, U}  = 4 = tau(6)

  Shared: 3 = P1/2
  Unique: 1 each (T vs U)""",
  "The genetic alphabet size = tau(6) in both DNA and RNA.",
  "EXACT", "4 bases per nucleic acid is foundational biology",
  "Modified bases exist (e.g., 5-methylcytosine) but are not canonical")

h(65, "amino-acid-codons-sixty-one", "Sense Codons = 64 - P1/2 = 61",
  "There are 61 sense codons out of 64 total = 2^P1 - P1/2 = 61.",
  """| Category | Count | n=6 relation |
|----------|-------|-------------|
| Total codons | 64 | 2^P1 |
| Stop codons | 3 | P1/2 |
| Sense codons | 61 | 2^P1 - P1/2 |
| Amino acids | 20 | tau(6) x sopfr(6) |""",
  """  Codon allocation:

  Total:  [################] 64 = 2^P1
  Sense:  [###############.] 61
  Stop:   [...]              3 = P1/2

  Degeneracy = 61/20 = 3.05 ~ P1/2""",
  "The genetic code allocates 2^P1 codons minus P1/2 stops for tau(6)*sopfr(6) amino acids.",
  "EXACT", "61 sense codons is a mathematical fact of the genetic code",
  "None -- arithmetic fact")

# ============================================================
# ANATOMY & PHYSIOLOGY (066-085)
# ============================================================

h(66, "insect-legs-six", "Insect Legs = P1 = 6 (Hexapoda)",
  "All insects (Hexapoda) have exactly 6 legs = P1 = 6. This defines the entire class.",
  """| Leg Pair | Segment | Example Use |
|----------|---------|------------|
| 1st pair | Prothorax | Walking/grasping |
| 2nd pair | Mesothorax | Walking |
| 3rd pair | Metathorax | Walking/jumping |""",
  """  Insect body plan:

  [Head] -- [Thorax: T1-T2-T3] -- [Abdomen]
              |    |    |
             L1   L2   L3
             L1   L2   L3

  Legs = 6 = P1
  Thoracic segments = 3 = P1/2
  Leg pairs = 3 = P1/2""",
  "The most species-rich animal class is defined by having P1 legs.",
  "EXACT", "6 legs defines Hexapoda/Insecta -- this is taxonomic definition",
  "None -- definitional")

h(67, "insect-body-three-parts", "Insect Body Segments = P1/2 = 3",
  "All insects have 3 body segments: head, thorax, abdomen = P1/2 = 3.",
  """| # | Segment | Function |
|---|---------|----------|
| 1 | Head | Sensory, feeding |
| 2 | Thorax | Locomotion (legs, wings) |
| 3 | Abdomen | Digestion, reproduction |""",
  """  Insect bauplan:

  [HEAD] --- [THORAX] --- [ABDOMEN]
    1           2            3

  Segments = 3 = P1/2""",
  "Insect body organization follows P1/2 tagmata.",
  "EXACT", "3 body segments defines Insecta",
  "None -- taxonomic definition")

h(68, "extraocular-muscles-six", "Extraocular Muscles = P1 = 6 per Eye",
  "Each human eye is controlled by exactly 6 extraocular muscles = P1.",
  """| # | Muscle | Action |
|---|--------|--------|
| 1 | Superior rectus | Elevation |
| 2 | Inferior rectus | Depression |
| 3 | Medial rectus | Adduction |
| 4 | Lateral rectus | Abduction |
| 5 | Superior oblique | Intorsion |
| 6 | Inferior oblique | Extorsion |""",
  """  Eye movement axes:

       Up (SR)
        |
  In (MR)--+--Out (LR)
        |
      Down (IR)
  + SO (intort) + IO (extort)

  Muscles per eye = 6 = P1""",
  "Precise eye movement requires exactly P1 muscles per eye.",
  "EXACT", "6 extraocular muscles is a standard anatomical fact",
  "None -- universally accepted in anatomy")

h(69, "heart-four-chambers", "Heart Chambers = tau(6) = 4",
  "The mammalian heart has 4 chambers: 2 atria + 2 ventricles = tau(6) = 4.",
  """| # | Chamber | Function |
|---|---------|----------|
| 1 | Right atrium | Receives deoxygenated blood |
| 2 | Right ventricle | Pumps to lungs |
| 3 | Left atrium | Receives oxygenated blood |
| 4 | Left ventricle | Pumps to body |""",
  """  Heart cross-section:

    [RA]  |  [LA]
    ------+------
    [RV]  |  [LV]

  Chambers = 4 = tau(6)
  Sides = 2 = phi(6)
  Layers per side = 2 = phi(6)""",
  "The mammalian heart is a tau(6)-chambered pump with phi(6) sides.",
  "EXACT", "4 heart chambers in mammals is basic anatomy",
  "Fish have 2 chambers, amphibians 3, reptiles 3-4")

h(70, "lung-lobes-five", "Lung Lobes = sopfr(6) = 5",
  "Human lungs have 5 lobes total: 3 right + 2 left = sopfr(6) = 5.",
  """| Lung | Lobes | Names |
|------|-------|-------|
| Right | 3 | Superior, Middle, Inferior |
| Left | 2 | Superior, Inferior |
| Total | 5 = sopfr(6) | |""",
  """  Lung anatomy:

  Right (3):   Left (2):
  [Sup]        [Sup]
  [Mid]        [Inf]
  [Inf]        (heart)

  Right lobes = 3 = P1/2
  Left lobes = 2 = phi(6)
  Total = 5 = sopfr(6)""",
  "Pulmonary architecture: P1/2 right + phi(6) left = sopfr(6) total.",
  "EXACT", "5 lung lobes is standard human anatomy",
  "Some variation exists (accessory lobes); left has 2 due to cardiac notch")

h(71, "digestive-organs-six", "Major Digestive Organs = P1 = 6",
  "The GI tract has 6 major organs: mouth, esophagus, stomach, small intestine, large intestine, rectum/anus = P1 = 6.",
  """| # | Organ | Function |
|---|-------|----------|
| 1 | Mouth | Mechanical + salivary digestion |
| 2 | Esophagus | Transport |
| 3 | Stomach | Acid + pepsin digestion |
| 4 | Small intestine | Absorption |
| 5 | Large intestine | Water absorption |
| 6 | Rectum/Anus | Elimination |""",
  """  GI tract flow:

  Mouth -> Esophagus -> Stomach -> S.I. -> L.I. -> Rectum
    1         2           3         4       5        6

  Organs = 6 = P1""",
  "The alimentary canal passes through P1 major organs.",
  "WEAK", "Classification depends on how organs are grouped",
  "Pharynx, appendix, etc. could be counted separately")

h(72, "large-intestine-six-parts", "Large Intestine Sections = P1 = 6",
  "The large intestine has 6 sections: cecum, ascending, transverse, descending, sigmoid colon, rectum = P1 = 6.",
  """| # | Section | Location |
|---|---------|----------|
| 1 | Cecum | Right lower |
| 2 | Ascending colon | Right side |
| 3 | Transverse colon | Upper cross |
| 4 | Descending colon | Left side |
| 5 | Sigmoid colon | Left lower |
| 6 | Rectum | Terminal |""",
  """  Large intestine layout:

       Transverse (3)
      /              \\
  Ascending(2)   Descending(4)
      |                |
  Cecum (1)      Sigmoid (5)
                       |
                   Rectum (6)

  Sections = 6 = P1""",
  "The large intestine traverses P1 anatomical sections.",
  "EXACT", "6 sections of the large intestine is standard anatomy",
  "Anal canal sometimes counted as 7th section")

h(73, "epidermis-five-layers", "Epidermis Layers = sopfr(6) = 5",
  "The epidermis of thick skin has 5 layers (strata) = sopfr(6) = 5.",
  """| # | Layer (deep to superficial) | Key Feature |
|---|---------------------------|-------------|
| 1 | Stratum basale | Stem cells |
| 2 | Stratum spinosum | Desmosomes |
| 3 | Stratum granulosum | Keratohyalin |
| 4 | Stratum lucidum | Clear, thin |
| 5 | Stratum corneum | Dead, keratinized |""",
  """  Epidermis cross-section (thick skin):

  Surface  ==================  Corneum (5)
           ==================  Lucidum (4)
           ==================  Granulosum (3)
           ==================  Spinosum (2)
  Deep     ==================  Basale (1)

  Layers = 5 = sopfr(6)""",
  "Skin barrier has sopfr(6) protective strata.",
  "EXACT", "5 epidermal layers in thick skin is standard histology",
  "Thin skin has only 4 layers (no stratum lucidum)")

h(74, "voice-types-six", "Human Voice Types = P1 = 6",
  "Classical vocal classification recognizes 6 voice types: soprano, mezzo-soprano, contralto, tenor, baritone, bass = P1 = 6.",
  """| # | Voice Type | Range | Gender |
|---|-----------|-------|--------|
| 1 | Soprano | C4-C6 | Female |
| 2 | Mezzo-soprano | A3-A5 | Female |
| 3 | Contralto | F3-F5 | Female |
| 4 | Tenor | C3-C5 | Male |
| 5 | Baritone | A2-A4 | Male |
| 6 | Bass | E2-E4 | Male |""",
  """  Voice range spectrum:

  High  Soprano =========
        Mezzo   =======
        Contra  ======
        Tenor   =======
        Bari    ======
  Low   Bass    =====

  Types = 6 = P1
  Per gender = 3 = P1/2""",
  "Human vocal diversity spans P1 types with P1/2 per sex.",
  "EXACT", "6 standard voice types is the classical SATB+ system",
  "Countertenor and other subcategories extend beyond 6")

h(75, "taste-types-six", "Taste Modalities = P1 = 6",
  "Humans have 6 basic taste modalities: sweet, sour, salty, bitter, umami, fat (oleogustus) = P1 = 6.",
  """| # | Taste | Receptor Type | Stimulus |
|---|-------|-------------|---------|
| 1 | Sweet | T1R2/T1R3 | Sugars |
| 2 | Sour | OTOP1 | H+ ions |
| 3 | Salty | ENaC | Na+ ions |
| 4 | Bitter | T2Rs | Alkaloids |
| 5 | Umami | T1R1/T1R3 | Glutamate |
| 6 | Fat (oleogustus) | CD36/GPR120 | Fatty acids |""",
  """  Taste modalities:

  Classical 5 + Fat = 6 = P1

  Sweet  Sour  Salty  Bitter  Umami  Fat
    1      2     3      4       5     6""",
  "Including the recently recognized fat taste, gustation has P1 modalities.",
  "WEAK", "Fat taste (oleogustus) is still debated; classical count is 5",
  "Oleogustus not universally accepted yet; some propose more tastes")

h(76, "semicircular-canals-three", "Semicircular Canals = P1/2 = 3",
  "Each inner ear has 3 semicircular canals for rotational balance = P1/2 = 3.",
  """| # | Canal | Plane Detected |
|---|-------|---------------|
| 1 | Anterior | Sagittal (nodding) |
| 2 | Posterior | Coronal (tilting) |
| 3 | Lateral | Horizontal (shaking) |""",
  """  3D rotation detection:

       Anterior
        /
  Lateral----+
        \\
       Posterior

  Canals = 3 = P1/2
  Matches 3 spatial rotation axes""",
  "Balance detection requires P1/2 canals for P1/2 rotational degrees of freedom.",
  "EXACT", "3 semicircular canals is universal in vertebrates",
  "None -- conserved across all vertebrates")

h(77, "ear-ossicles-three", "Middle Ear Ossicles = P1/2 = 3",
  "The mammalian middle ear has 3 ossicles: malleus, incus, stapes = P1/2 = 3.",
  """| # | Ossicle | Connects To |
|---|---------|-------------|
| 1 | Malleus (hammer) | Tympanic membrane |
| 2 | Incus (anvil) | Between |
| 3 | Stapes (stirrup) | Oval window |""",
  """  Sound transmission:

  Eardrum -> [Malleus] -> [Incus] -> [Stapes] -> Oval window
                1           2          3

  Ossicles = 3 = P1/2
  (Smallest bones in the human body)""",
  "Sound amplification uses P1/2 ossicles in the impedance-matching chain.",
  "EXACT", "3 middle ear ossicles in mammals is a standard anatomical fact",
  "Reptiles/birds have 1 ossicle (columella); 3 is mammal-specific")

h(78, "cone-types-three", "Retinal Cone Types = P1/2 = 3",
  "Human color vision uses 3 types of cone photoreceptors: S (blue), M (green), L (red) = P1/2 = 3.",
  """| # | Cone Type | Peak Wavelength | Color |
|---|-----------|----------------|-------|
| 1 | S-cone | 420 nm | Blue |
| 2 | M-cone | 530 nm | Green |
| 3 | L-cone | 560 nm | Red |""",
  """  Cone spectral sensitivity:

  Response
    |  S     M    L
    | /\\   /\\   /\\
    |/  \\ /  \\ /  \\
    +----+----+-----> wavelength
    400  500  600  700 nm

  Cone types = 3 = P1/2 (trichromacy)""",
  "Trichromatic vision uses P1/2 photopigments spanning the visible spectrum.",
  "EXACT", "3 cone types is established visual neuroscience",
  "Some women are tetrachromats (4 cone types); most mammals are dichromats")

h(79, "antibody-chains-four", "Antibody Polypeptide Chains = tau(6) = 4",
  "Each antibody (IgG) has 4 polypeptide chains: 2 heavy + 2 light = tau(6) = 4.",
  """| Chain | Count | Size |
|-------|-------|------|
| Heavy (H) | 2 | ~50 kDa |
| Light (L) | 2 | ~25 kDa |
| Total | 4 = tau(6) | |""",
  """  Antibody (IgG) structure:

       Fab          Fab
      /    \\       /    \\
    VL  VH     VL  VH
    |    |      |    |
    CL  CH1    CL  CH1
         |          |
         CH2--------CH2    Fc
         |          |
         CH3--------CH3

  Light chains = 2 = phi(6)
  Heavy chains = 2 = phi(6)
  Total = 4 = tau(6)""",
  "Antibody architecture = phi(6) heavy + phi(6) light = tau(6) chains.",
  "EXACT", "4 chains per IgG is an established immunological fact",
  "IgM is pentameric (20 chains); IgA can be dimeric (8 chains)")

h(80, "germ-layers-three", "Embryonic Germ Layers = P1/2 = 3",
  "All triploblastic animals develop from 3 embryonic germ layers: ectoderm, mesoderm, endoderm = P1/2 = 3.",
  """| # | Germ Layer | Derivatives |
|---|-----------|-------------|
| 1 | Ectoderm | Skin, nervous system |
| 2 | Mesoderm | Muscle, bone, blood |
| 3 | Endoderm | Gut lining, lungs, liver |""",
  """  Embryonic layers (cross-section):

  ===============  Ectoderm (outer)
  ===============  Mesoderm (middle)
  ===============  Endoderm (inner)

  Germ layers = 3 = P1/2""",
  "Animal body plan arises from P1/2 fundamental tissue layers.",
  "EXACT", "3 germ layers is a cornerstone of developmental biology",
  "Diploblasts (cnidarians) have only 2 germ layers")

h(81, "blood-cell-types-three", "Blood Cell Lineages = P1/2 = 3",
  "Blood has 3 main cellular components: red blood cells, white blood cells, platelets = P1/2 = 3.",
  """| # | Cell Type | Function | Count/uL |
|---|-----------|----------|---------|
| 1 | RBC (erythrocytes) | O2 transport | 4-6M |
| 2 | WBC (leukocytes) | Immunity | 4-11K |
| 3 | Platelets (thrombocytes) | Clotting | 150-400K |""",
  """  Blood composition:

  Plasma (55%)
  --------
  RBC (44%)     ]
  WBC (<1%)     ] Formed elements
  Platelets (<1%)]

  Cell types = 3 = P1/2""",
  "Blood contains P1/2 formed element categories.",
  "EXACT", "3 blood cell types is standard hematology",
  "WBCs subdivide into 5 types (neutrophils, lymphocytes, etc.)")

h(82, "leukocyte-types-five", "Leukocyte Types = sopfr(6) = 5",
  "There are 5 types of white blood cells: neutrophils, lymphocytes, monocytes, eosinophils, basophils = sopfr(6) = 5.",
  """| # | WBC Type | % of Total | Function |
|---|---------|-----------|----------|
| 1 | Neutrophils | 60-70% | Phagocytosis |
| 2 | Lymphocytes | 20-25% | Adaptive immunity |
| 3 | Monocytes | 3-8% | Phagocytosis |
| 4 | Eosinophils | 2-4% | Parasites, allergy |
| 5 | Basophils | <1% | Inflammation |""",
  """  WBC differential:

  Neutro: ################ 65%
  Lympho: ######           25%
  Mono:   ##                5%
  Eosino: #                 3%
  Baso:   .                 1%

  Types = 5 = sopfr(6)""",
  "Immune surveillance deploys sopfr(6) leukocyte specialists.",
  "EXACT", "5 WBC types is standard hematology (complete blood count)",
  "NK cells, dendritic cells etc. are subtypes")

h(83, "muscle-types-three", "Muscle Tissue Types = P1/2 = 3",
  "There are 3 types of muscle tissue: skeletal, cardiac, smooth = P1/2 = 3.",
  """| # | Type | Control | Striation |
|---|------|---------|-----------|
| 1 | Skeletal | Voluntary | Striated |
| 2 | Cardiac | Involuntary | Striated |
| 3 | Smooth | Involuntary | Non-striated |""",
  """  Muscle classification:

            Voluntary  Involuntary
  Striated: Skeletal   Cardiac
  Smooth:   --         Smooth

  Types = 3 = P1/2""",
  "The body uses P1/2 muscle types for diverse movement needs.",
  "EXACT", "3 muscle types is basic histology",
  "None -- universally accepted")

h(84, "tissue-types-four", "Primary Tissue Types = tau(6) = 4",
  "The human body has 4 primary tissue types: epithelial, connective, muscle, nervous = tau(6) = 4.",
  """| # | Tissue | Function |
|---|--------|----------|
| 1 | Epithelial | Covering, lining |
| 2 | Connective | Support, binding |
| 3 | Muscle | Movement |
| 4 | Nervous | Communication |""",
  """  Tissue hierarchy:

  Cells -> [4 Tissue Types] -> Organs -> Systems

  Epithelial  Connective  Muscle  Nervous
      1           2          3       4

  Types = 4 = tau(6)""",
  "All human tissues belong to tau(6) fundamental categories.",
  "EXACT", "4 primary tissue types is foundational histology",
  "None -- universally accepted since Bichat")

h(85, "vertebral-regions-five", "Vertebral Column Regions = sopfr(6) = 5",
  "The vertebral column has 5 regions: cervical, thoracic, lumbar, sacral, coccygeal = sopfr(6) = 5.",
  """| # | Region | Vertebrae | n=6 relation |
|---|--------|-----------|-------------|
| 1 | Cervical | 7 | |
| 2 | Thoracic | 12 | sigma(6) |
| 3 | Lumbar | 5 | sopfr(6) |
| 4 | Sacral | 5 (fused) | sopfr(6) |
| 5 | Coccygeal | 4 (fused) | tau(6) |""",
  """  Vertebral column:

  Cervical (7)     ]
  Thoracic (12)    ] = sigma(6)
  Lumbar (5)       ] = sopfr(6)
  Sacral (5)       ] = sopfr(6)
  Coccygeal (4)    ] = tau(6)

  Regions = 5 = sopfr(6)
  Thoracic count = sigma(6) = 12!""",
  "Spinal regions = sopfr(6), with thoracic vertebrae = sigma(6) and coccygeal = tau(6).",
  "EXACT", "5 vertebral regions and their counts are anatomical facts",
  "Coccygeal count varies (3-5); sacral fuse into 1 bone")

# ============================================================
# GENETICS & EVOLUTION (086-110)
# ============================================================

h(86, "mendel-three-laws", "Mendel's Laws = P1/2 = 3",
  "Mendel proposed 3 laws of inheritance: segregation, independent assortment, dominance = P1/2 = 3.",
  """| # | Law | Statement |
|---|-----|-----------|
| 1 | Segregation | Alleles separate in meiosis |
| 2 | Independent Assortment | Genes on different chromosomes assort independently |
| 3 | Dominance | One allele masks another |""",
  """  Mendel's framework:

  Law 1: Aa -> A or a  (segregation)
  Law 2: AaBb -> AB, Ab, aB, ab  (independence)
  Law 3: Aa = A phenotype  (dominance)

  Laws = 3 = P1/2""",
  "The foundation of genetics rests on P1/2 laws.",
  "EXACT", "3 Mendelian laws is standard genetics education",
  "Law of dominance is sometimes considered a principle rather than a law")

h(87, "epigenetic-mechanisms-three", "Major Epigenetic Mechanisms = P1/2 = 3",
  "There are 3 major epigenetic mechanisms: DNA methylation, histone modification, non-coding RNA = P1/2 = 3.",
  """| # | Mechanism | Effect |
|---|-----------|--------|
| 1 | DNA methylation | Gene silencing (CpG) |
| 2 | Histone modification | Chromatin remodeling |
| 3 | Non-coding RNA | Post-transcriptional regulation |""",
  """  Epigenetic layers:

  DNA: --CpG--CpG--CpG--  methylation
       ===histone===       modification
  RNA: ~~~~miRNA~~~~       regulation

  Mechanisms = 3 = P1/2""",
  "Gene regulation beyond sequence uses P1/2 epigenetic systems.",
  "EXACT", "3 major epigenetic mechanisms is the standard framework",
  "Chromatin remodeling sometimes counted as 4th mechanism")

h(88, "stem-cell-potency-five", "Stem Cell Potency Levels = sopfr(6) = 5",
  "Stem cells have 5 potency levels: totipotent, pluripotent, multipotent, oligopotent, unipotent = sopfr(6) = 5.",
  """| # | Potency | Example | Can Become |
|---|---------|---------|-----------|
| 1 | Totipotent | Zygote | Any cell + placenta |
| 2 | Pluripotent | ESC, iPSC | Any cell type |
| 3 | Multipotent | HSC | Multiple related types |
| 4 | Oligopotent | Lymphoid progenitor | Few types |
| 5 | Unipotent | Muscle satellite | One type |""",
  """  Potency hierarchy:

  Totipotent > Pluripotent > Multipotent > Oligopotent > Unipotent
       1            2            3             4            5

  Levels = 5 = sopfr(6)""",
  "Stem cell differentiation has sopfr(6) levels of developmental potential.",
  "EXACT", "5 potency levels is the standard classification",
  "Some combine oligopotent/unipotent or add nullipotent")

h(89, "hardy-weinberg-three-terms", "Hardy-Weinberg Genotype Terms = P1/2 = 3",
  "The Hardy-Weinberg equation has 3 genotype terms: p^2 + 2pq + q^2 = 1, mapping to P1/2 = 3.",
  """| Term | Genotype | Frequency |
|------|----------|-----------|
| p^2 | AA (homozygous dominant) | p^2 |
| 2pq | Aa (heterozygous) | 2pq |
| q^2 | aa (homozygous recessive) | q^2 |""",
  """  Hardy-Weinberg:

  p^2 + 2pq + q^2 = 1
  (p + q)^2 = 1

  Genotype classes = 3 = P1/2
  Allele classes = 2 = phi(6)""",
  "Population genetics equilibrium partitions into P1/2 genotype classes from phi(6) alleles.",
  "EXACT", "3 HW terms is a mathematical expansion of (p+q)^2",
  "Multi-allelic systems have more terms")

h(90, "leucine-six-codons", "Leucine Codons = P1 = 6",
  "Leucine (Leu) is encoded by exactly 6 codons: UUA, UUG, CUU, CUC, CUA, CUG = P1 = 6.",
  """| # | Codon | Codon Family |
|---|-------|-------------|
| 1 | UUA | UU- family |
| 2 | UUG | UU- family |
| 3 | CUU | CU- family |
| 4 | CUC | CU- family |
| 5 | CUA | CU- family |
| 6 | CUG | CU- family |""",
  """  Codon distribution (amino acids with most codons):

  Leu: 6 codons = P1  ******
  Ser: 6 codons = P1  ******
  Arg: 6 codons = P1  ******

  Three amino acids share the maximum of P1 codons""",
  "The maximum codon degeneracy = P1, shared by exactly 3 = P1/2 amino acids.",
  "EXACT", "6 codons for Leu is a fact of the standard genetic code",
  "None -- genetic code is universal")

h(91, "serine-six-codons", "Serine Codons = P1 = 6",
  "Serine (Ser) is encoded by exactly 6 codons: UCU, UCC, UCA, UCG, AGU, AGC = P1 = 6.",
  """| # | Codon | Codon Family |
|---|-------|-------------|
| 1 | UCU | UC- family |
| 2 | UCC | UC- family |
| 3 | UCA | UC- family |
| 4 | UCG | UC- family |
| 5 | AGU | AG- family |
| 6 | AGC | AG- family |""",
  """  Serine codon split:

  UC- family: UCU UCC UCA UCG  (4 = tau(6))
  AG- family: AGU AGC          (2 = phi(6))
  Total:                        6 = P1

  Split: tau(6) + phi(6) = P1""",
  "Serine's codons split as tau(6) + phi(6) = P1 across two codon families.",
  "EXACT", "6 codons for Ser is a fact of the standard genetic code",
  "None -- genetic code is universal")

h(92, "arginine-six-codons", "Arginine Codons = P1 = 6",
  "Arginine (Arg) is encoded by exactly 6 codons: CGU, CGC, CGA, CGG, AGA, AGG = P1 = 6.",
  """| # | Codon | Codon Family |
|---|-------|-------------|
| 1 | CGU | CG- family |
| 2 | CGC | CG- family |
| 3 | CGA | CG- family |
| 4 | CGG | CG- family |
| 5 | AGA | AG- family |
| 6 | AGG | AG- family |""",
  """  Arginine codon split:

  CG- family: CGU CGC CGA CGG  (4 = tau(6))
  AG- family: AGA AGG          (2 = phi(6))
  Total:                        6 = P1

  Same tau(6)+phi(6) split as Serine!""",
  "Arginine mirrors Serine's tau(6)+phi(6) codon split.",
  "EXACT", "6 codons for Arg is a fact of the standard genetic code",
  "None -- genetic code is universal")

h(93, "wobble-position-third", "Wobble Position = P1/2 = 3rd Nucleotide",
  "The wobble position in a codon is the 3rd nucleotide = P1/2 = 3.",
  """| Position | Importance | Degeneracy |
|----------|-----------|-----------|
| 1st | Highest | Low |
| 2nd | High | Low |
| 3rd (wobble) | Lowest | Highest |""",
  """  Codon positions:

  Position:  1   2   3
  Role:     key key wobble
  Freedom:  low low HIGH

  Wobble = position 3 = P1/2""",
  "Genetic code degeneracy concentrates at position P1/2.",
  "EXACT", "3rd position wobble is a fundamental property of the genetic code",
  "None -- universally accepted")

h(94, "thoracic-vertebrae-twelve", "Thoracic Vertebrae = sigma(6) = 12",
  "Humans have exactly 12 thoracic vertebrae = sigma(6) = 12.",
  """| Region | Count | n=6 relation |
|--------|-------|-------------|
| Cervical | 7 | -- |
| Thoracic | 12 | sigma(6) |
| Lumbar | 5 | sopfr(6) |""",
  """  Thoracic spine:

  T1  --rib 1
  T2  --rib 2
  T3  --rib 3
  T4  --rib 4
  T5  --rib 5
  T6  --rib 6
  T7  --rib 7
  T8  --rib 8
  T9  --rib 9
  T10 --rib 10
  T11 --rib 11
  T12 --rib 12

  Count = 12 = sigma(6)""",
  "The rib-bearing vertebral segment has sigma(6) members.",
  "EXACT", "12 thoracic vertebrae is a standard anatomical fact",
  "Rarely, 11 or 13 thoracic vertebrae occur as anatomical variants")

h(95, "lumbar-vertebrae-five", "Lumbar Vertebrae = sopfr(6) = 5",
  "Humans have exactly 5 lumbar vertebrae = sopfr(6) = 5.",
  """| Vertebra | Feature |
|----------|---------|
| L1 | Conus medullaris level |
| L2 | Cauda equina begins |
| L3 | Spinal needle target |
| L4 | Iliac crest level |
| L5 | Lumbosacral joint |""",
  """  Lumbar spine:

  L1 ===
  L2 ===
  L3 ===  <- lumbar puncture
  L4 ===
  L5 ===

  Count = 5 = sopfr(6)""",
  "The weight-bearing lower spine has sopfr(6) vertebrae.",
  "EXACT", "5 lumbar vertebrae is standard anatomy (most humans)",
  "Sacralization of L5 or lumbarization of S1 can give 4 or 6")

h(96, "coccygeal-vertebrae-four", "Coccygeal Vertebrae = tau(6) = 4",
  "The coccyx (tailbone) typically consists of 4 fused vertebrae = tau(6) = 4.",
  """| Vertebra | Status |
|----------|--------|
| Co1 | Largest, sometimes mobile |
| Co2 | Fused |
| Co3 | Fused |
| Co4 | Smallest |""",
  """  Coccyx:

  [Co1]
  [Co2]  fused
  [Co3]
  [Co4]

  Count = 4 = tau(6) (most common)""",
  "The vestigial tail has tau(6) fused vertebrae.",
  "WEAK", "Most commonly 4, but ranges from 3 to 5",
  "Significant individual variation (3-5 segments)")

h(97, "blood-types-four", "ABO Blood Types = tau(6) = 4",
  "The ABO blood group system has 4 types: A, B, AB, O = tau(6) = 4.",
  """| # | Blood Type | Antigens | Antibodies |
|---|-----------|----------|-----------|
| 1 | A | A | Anti-B |
| 2 | B | B | Anti-A |
| 3 | AB | A and B | None |
| 4 | O | None | Anti-A, Anti-B |""",
  """  ABO compatibility:

        Donate to:
  O  -> A, B, AB, O  (universal donor)
  A  -> A, AB
  B  -> B, AB
  AB -> AB           (universal recipient)

  Types = 4 = tau(6)""",
  "Blood typing has tau(6) phenotypic categories.",
  "EXACT", "4 ABO blood types is standard hematology",
  "Rh factor doubles to 8; other blood group systems exist")

h(98, "complement-pathways-three", "Complement Pathways = P1/2 = 3",
  "The complement system has 3 activation pathways: classical, alternative, lectin = P1/2 = 3.",
  """| # | Pathway | Trigger |
|---|---------|---------|
| 1 | Classical | Antibody-antigen complexes |
| 2 | Alternative | Spontaneous C3 hydrolysis |
| 3 | Lectin (MBL) | Mannose on pathogens |""",
  """  Complement activation:

  Classical --\\
  Alternative --> C3 convertase --> MAC --> Lysis
  Lectin ------/

  Pathways = 3 = P1/2
  All converge on C3""",
  "Innate immunity activates complement through P1/2 independent pathways.",
  "EXACT", "3 complement pathways is standard immunology",
  "None -- well established")

h(99, "immunoglobulin-classes-five", "Immunoglobulin Classes = sopfr(6) = 5",
  "There are 5 classes (isotypes) of immunoglobulins: IgG, IgA, IgM, IgD, IgE = sopfr(6) = 5.",
  """| # | Class | Function | Structure |
|---|-------|----------|-----------|
| 1 | IgG | Most abundant, crosses placenta | Monomer |
| 2 | IgA | Mucosal immunity | Dimer |
| 3 | IgM | First responder | Pentamer |
| 4 | IgD | B-cell receptor | Monomer |
| 5 | IgE | Allergy, parasites | Monomer |""",
  """  Ig class abundance in serum:

  IgG: ################## 75%
  IgA: #####              15%
  IgM: ###                10%
  IgD: .                  <1%
  IgE: .                  <0.01%

  Classes = 5 = sopfr(6)""",
  "The adaptive immune system deploys sopfr(6) antibody isotypes.",
  "EXACT", "5 Ig classes is standard immunology",
  "IgG has 4 subclasses; IgA has 2 subclasses")

h(100, "chromosome-dna-packing-six-levels", "DNA Packing Levels = P1 = 6",
  "DNA packaging from double helix to metaphase chromosome has 6 levels of organization = P1 = 6.",
  """| # | Level | Diameter | Structure |
|---|-------|----------|-----------|
| 1 | DNA double helix | 2 nm | B-form DNA |
| 2 | Nucleosome (beads) | 11 nm | 147bp + histone octamer |
| 3 | 30nm fiber | 30 nm | Solenoid/zigzag |
| 4 | Chromatin loops | 300 nm | Loop domains |
| 5 | Chromatid | 700 nm | Condensed fiber |
| 6 | Metaphase chromosome | 1400 nm | Maximum compaction |""",
  """  DNA compaction hierarchy:

  2nm  -> 11nm -> 30nm -> 300nm -> 700nm -> 1400nm
  helix   bead   fiber   loop    chromatid  chromosome
   1       2      3       4        5          6

  Levels = 6 = P1
  Compaction ratio ~ 10,000x""",
  "Genome packaging uses P1 hierarchical levels from helix to chromosome.",
  "WEAK", "6-level model is commonly taught but 30nm fiber is debated",
  "30nm fiber existence in vivo is disputed; fractal models suggest continuous compaction")

h(101, "domains-of-life-three", "Domains of Life = P1/2 = 3",
  "Life is classified into 3 domains: Bacteria, Archaea, Eukarya = P1/2 = 3.",
  """| # | Domain | Cell Type | Examples |
|---|--------|-----------|---------|
| 1 | Bacteria | Prokaryotic | E. coli, Streptococcus |
| 2 | Archaea | Prokaryotic | Methanogens, halophiles |
| 3 | Eukarya | Eukaryotic | Animals, plants, fungi |""",
  """  Tree of Life:

         LUCA
        / | \\
       /  |  \\
  Bacteria Archaea Eukarya
     1       2       3

  Domains = 3 = P1/2""",
  "The fundamental classification of all life uses P1/2 domains (Woese, 1977).",
  "EXACT", "3 domains of life is the current consensus classification",
  "Some propose 2 domains (Bacteria + Archaea/Eukarya)")

h(102, "natural-selection-four-conditions", "Natural Selection Conditions = tau(6) = 4",
  "Natural selection requires 4 conditions: variation, heritability, differential fitness, overproduction = tau(6) = 4.",
  """| # | Condition | Description |
|---|-----------|-------------|
| 1 | Variation | Individuals differ |
| 2 | Heritability | Traits are inherited |
| 3 | Differential fitness | Some variants reproduce more |
| 4 | Overproduction | More offspring than can survive |""",
  """  Darwin's logic:

  Variation + Heritability + Selection pressure + Overproduction
      1            2              3                    4

  = Evolution by natural selection

  Conditions = 4 = tau(6)""",
  "Evolution by natural selection requires tau(6) necessary conditions.",
  "EXACT", "4 conditions for natural selection is the standard Darwinian framework",
  "Some formulations use 3 conditions (combining overproduction into selection)")

h(103, "speciation-types-four", "Speciation Modes = tau(6) = 4",
  "There are 4 modes of speciation: allopatric, sympatric, peripatric, parapatric = tau(6) = 4.",
  """| # | Mode | Mechanism |
|---|------|-----------|
| 1 | Allopatric | Geographic isolation |
| 2 | Sympatric | No geographic barrier |
| 3 | Peripatric | Small peripheral population |
| 4 | Parapatric | Adjacent populations |""",
  """  Speciation geography:

  Allo:  [A] |||barrier||| [B]  separated
  Sym:   [A+B in same area]     together
  Peri:  [AAAA].[b]             edge group
  Para:  [AAAA][BBBB]           adjacent

  Modes = 4 = tau(6)""",
  "Speciation occurs through tau(6) geographic/reproductive modes.",
  "EXACT", "4 speciation modes is the standard classification",
  "Hybrid speciation sometimes added as 5th mode")

h(104, "evolutionary-forces-four", "Evolutionary Forces = tau(6) = 4",
  "There are 4 fundamental forces of evolution: mutation, selection, drift, gene flow = tau(6) = 4.",
  """| # | Force | Effect on Allele Frequency |
|---|-------|--------------------------|
| 1 | Mutation | Creates new alleles |
| 2 | Natural selection | Directional change |
| 3 | Genetic drift | Random change |
| 4 | Gene flow | Homogenizes populations |""",
  """  Evolutionary forces:

  Mutation:   ====>  (new variation)
  Selection:  =====> (directional)
  Drift:      ~~>    (random)
  Gene flow:  <====> (mixing)

  Forces = 4 = tau(6)""",
  "Population genetics recognizes tau(6) forces that change allele frequencies.",
  "EXACT", "4 evolutionary forces is the standard population genetics framework",
  "Non-random mating sometimes listed as 5th force")

h(105, "rib-pairs-twelve", "Rib Pairs = sigma(6) = 12",
  "Humans have 12 pairs of ribs = sigma(6) = 12.",
  """| Category | Pairs | Ribs |
|----------|-------|------|
| True ribs | 1-7 | 14 |
| False ribs | 8-10 | 6 = P1 |
| Floating ribs | 11-12 | 4 = tau(6) |
| Total pairs | 12 = sigma(6) | 24 |""",
  """  Rib cage:

  Pairs 1-7:   True ribs (7)
  Pairs 8-10:  False ribs (3 = P1/2)
  Pairs 11-12: Floating ribs (2 = phi(6))

  Total pairs = 12 = sigma(6)
  True + False + Floating = 7 + 3 + 2""",
  "The thoracic cage has sigma(6) rib pairs protecting vital organs.",
  "EXACT", "12 rib pairs is a standard anatomical fact",
  "Cervical ribs (13th pair) occur rarely as anatomical variant")

h(106, "cranial-nerves-twelve", "Cranial Nerves = sigma(6) = 12",
  "There are 12 pairs of cranial nerves = sigma(6) = 12.",
  """| # | Nerve | Function |
|---|-------|----------|
| I | Olfactory | Smell |
| II | Optic | Vision |
| III | Oculomotor | Eye movement |
| IV | Trochlear | Eye movement |
| V | Trigeminal | Face sensation |
| VI | Abducens | Eye movement |
| VII | Facial | Facial expression |
| VIII | Vestibulocochlear | Hearing/balance |
| IX | Glossopharyngeal | Taste/swallow |
| X | Vagus | Parasympathetic |
| XI | Accessory | Head/shoulder |
| XII | Hypoglossal | Tongue |""",
  """  Cranial nerve count:

  Sensory only:    I, II, VIII           (3 = P1/2)
  Motor only:      III, IV, VI, XI, XII  (5 = sopfr(6))
  Mixed:           V, VII, IX, X         (4 = tau(6))

  Total = 12 = sigma(6)""",
  "The cranial nerve complement = sigma(6), subdividing into P1/2 + sopfr(6) + tau(6).",
  "EXACT", "12 cranial nerves is a foundational anatomical fact",
  "Terminal nerve (nerve 0) sometimes counted, giving 13")

h(107, "glucose-formula-symmetry", "Glucose C6H12O6 Triple-P1 Symmetry",
  "Glucose (C6H12O6) has the remarkable property that C=P1, H=sigma(6), O=P1 -- the formula is written in n=6 constants.",
  """| Atom | Count | n=6 constant | Relation |
|------|-------|-------------|----------|
| C | 6 | P1 | First perfect number |
| H | 12 | sigma(6) | Sum of divisors |
| O | 6 | P1 | First perfect number |
| C/O | 1 | Unity | |
| H/C | 2 | phi(6) | Euler totient |
| H/O | 2 | phi(6) | Euler totient |""",
  """  Glucose formula decomposition:

  C  6  H 12  O  6
  |  |  |  |  |  |
  C P1  H s6  O P1

  Ratios:
  H/C = 12/6 = 2 = phi(6)
  H/O = 12/6 = 2 = phi(6)
  C/O = 6/6  = 1
  C+O = 12   = sigma(6) = H""",
  "Glucose's molecular formula is entirely expressible in n=6 arithmetic functions.",
  "EXACT", "C6H12O6 is the molecular formula of glucose -- pure chemistry",
  "This is the same molecule as EVOL-047/048 viewed from the symmetry angle")

h(108, "sex-determination-two-systems", "Major Sex Determination = phi(6) = 2 Chromosomes",
  "Mammalian sex is determined by 2 sex chromosomes (X and Y) = phi(6) = 2.",
  """| System | Chromosomes | Male | Female |
|--------|------------|------|--------|
| XY (mammals) | X, Y | XY | XX |
| ZW (birds) | Z, W | ZZ | ZW |""",
  """  Sex determination:

  Mammals: XX (female) vs XY (male)
  Birds:   ZZ (male)   vs ZW (female)

  Sex chromosomes per system = 2 = phi(6)
  Possible sexes = 2 = phi(6)""",
  "Chromosomal sex determination uses phi(6) sex chromosomes producing phi(6) sexes.",
  "EXACT", "2 sex chromosomes is standard genetics",
  "Some organisms have more complex systems (e.g., platypus has 10 sex chromosomes)")

h(109, "dna-repair-six-mechanisms", "Major DNA Repair Mechanisms = P1 = 6",
  "There are 6 major DNA repair pathways: BER, NER, MMR, HR, NHEJ, direct reversal = P1 = 6.",
  """| # | Pathway | Damage Type |
|---|---------|------------|
| 1 | Base excision repair (BER) | Small base lesions |
| 2 | Nucleotide excision repair (NER) | Bulky adducts |
| 3 | Mismatch repair (MMR) | Replication errors |
| 4 | Homologous recombination (HR) | DSB (accurate) |
| 5 | Non-homologous end joining (NHEJ) | DSB (fast) |
| 6 | Direct reversal | Alkylation, UV dimers |""",
  """  DNA repair pathways:

  Single-strand: BER, NER, MMR      (3 = P1/2)
  Double-strand: HR, NHEJ           (2 = phi(6))
  Direct:        Reversal           (1)

  Total = 3 + 2 + 1 = 6 = P1
  Note: 1 + 2 + 3 = 6 (perfect number property!)""",
  "Genome integrity maintenance uses P1 repair pathways, subdivided as 1+2+3=P1.",
  "EXACT", "6 major DNA repair pathways is the standard classification",
  "Translesion synthesis and interstrand crosslink repair sometimes added")

h(110, "genetic-code-amino-acids-twenty", "Amino Acids = tau(6) x sopfr(6) = 20",
  "The standard genetic code encodes 20 amino acids = tau(6) x sopfr(6) = 4 x 5 = 20.",
  """| Property | Value | n=6 relation |
|----------|-------|-------------|
| Amino acids | 20 | tau(6) x sopfr(6) |
| Codons | 64 | 2^P1 |
| Stop codons | 3 | P1/2 |
| Sense codons | 61 | 2^P1 - P1/2 |
| Max degeneracy | 6 | P1 (Leu, Ser, Arg) |
| Bases | 4 | tau(6) |""",
  """  Genetic code summary:

  tau(6) bases -> P1/2 per codon -> 2^P1 codons
     4               3                64

  Encode: tau(6) x sopfr(6) = 20 amino acids
  Max codons per AA = P1 = 6 (Leu, Ser, Arg)

  The entire genetic code is expressible in n=6 constants!""",
  "The genetic code is completely parametrized by arithmetic functions of the first perfect number.",
  "EXACT", "20 standard amino acids is a fundamental fact of biochemistry",
  "Selenocysteine (21st) and pyrrolysine (22nd) exist in some organisms")


# ============================================================
# GENERATE FILES
# ============================================================

grade_counts = {"EXACT": 0, "WEAK": 0, "INCONCLUSIVE": 0}
grade_emoji = {"EXACT": "\U0001f7e9", "WEAK": "\U0001f7e7", "INCONCLUSIVE": "\u26aa"}

os.makedirs(OUT_DIR, exist_ok=True)

for (num, slug, title, hyp, table, ascii, meaning, grade, grade_text, limits, gz) in hypotheses:
    emoji = grade_emoji[grade]
    grade_counts[grade] += 1

    content = f"""# EVOL-{num:03d}: {title}

> **Hypothesis**: {hyp}

## Numerical Verification

{table}

## Structure

```
{ascii}
```

## Structural Meaning

{meaning}

## Grade

{emoji} {grade} -- {grade_text}

## Limitations
- {limits}

## GZ Dependency
{gz}
"""

    fname = f"EVOL-{num:03d}-{slug}.md"
    fpath = os.path.join(OUT_DIR, fname)
    with open(fpath, 'w') as f:
        f.write(content)
    print(f"  Created {fname}")

print(f"\n=== Summary ===")
print(f"Total files created: {len(hypotheses)}")
for g, c in sorted(grade_counts.items()):
    print(f"  {grade_emoji[g]} {g}: {c}")
print(f"\nAll files in: {os.path.abspath(OUT_DIR)}")
