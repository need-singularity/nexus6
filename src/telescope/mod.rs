//! Telescope scan engine with 1013 lenses across 22 core types.
pub mod accel_lenses_a;
pub mod accel_lenses_b;
pub mod accel_lenses_c;
pub mod accel_lenses_d;
pub mod anima_lenses;
pub mod consensus;
pub mod core_lenses;
pub mod cross_lenses;
pub mod domain_combos;
pub mod lens_trait;
pub mod lenses;
pub mod n6_lenses;
pub mod physics_deep_lenses;
pub mod quantum_lenses;
pub mod registry;
pub mod sedi_lenses;
pub mod shared_data;
pub mod tecs_lenses;
pub mod tier;

use std::collections::HashMap;
use std::panic;

use lens_trait::{Lens, LensResult};
#[rustfmt::skip]
use lenses::{
    AllSeeingEyeLens, AudioLens, AutoCalibrationLens, AutocorrelationLens, BarrierLens,
    BatteryChemistryLens, BigBangLens, BoseEinsteinLens, BoundaryLens, CausalLens,
    ChaosLens, ChipArchitectureLens, ClusteringLens, CompassLens, CompressionLens,
    ConcaveLens, ConformalBootstrapLens, ConsciousnessLens, ConsciousnessOrchestratorLens, ConstantCollectorLens,
    ConstantCombinationLens, ConstantDiscoveryEngineLens, ConstantFormulaLens, ContractingScanLens, ConvexLens,
    CorrelationLens, CryptoLens, DensityLens, DestinyLens, DiamondLens,
    DimensionReductionLens, DimensionalBridgeLens, DivergenceLens, ElementCombinationLens, ElementLens,
    EmLens, EngineDiscoveryLens, EntropyLens, EnvironmentLens, EventHorizonLens,
    EvolutionLens, ExoticMatterLens, ExpandingScanLens, FinanceLens, FissionLens,
    FormulaCombinationLens, FractalLens, FusionLens, GodsEyeLens, GoldenRatioLens,
    GoldenZoneLens, GradientLens, GraphLens, GravityLens, HexagonalLens,
    InfiniteDiscoveryLens, InfinityLens, InfoLens, KaleidoscopeLens, KeywordLens,
    LatticeFieldLens, LensDiscoveryLens, LightLens, LightWaveLens, LoRALens,
    MaterialCombinationLens, MedicineLens, MemoryLens, MetricDiscoveryLens, MetricLens,
    MiLens, MirrorLens, ModuleDiscoveryLens, MolecularCombinationLens, MolecularTransformLens,
    MoleculeLens, MultiscaleLens, MutationLens, NetworkLens, OutlierLens,
    OverfittingLens, PhaseTransitionLens, PiLens, PowerLawLens, PrimeLens,
    ProvidenceEyeLens, QuantumJumpLens, QuantumLensImpl, QuantumMicroLens, RatioLens,
    RecursionLens, RecursiveLoopLens, RefractionLens, RelativisticBarrierLens, RenormalizationLens,
    RoboticsLens, RulerLens, ScaleLens, SimulationLens, SingularityLens,
    SolarEfficiencyLens, SpacetimeLens, SpectralLens, SpeculativeDecodeLens, SphericalLens,
    StabilityLens, StationarityLens, StimulusLens, SymmetryBreakingLens, TachyonLens,
    TelepathyLens, TensionLens, TensionLinkLens, ThermoLens, TimeReversalLens,
    TopologyLens, TransformerAnatomyLens, TriangleLens, UbatchUoptimizationLens, UcombinatorialLens,
    UcompletenessLens, UemergenceLens, UextrapolationLens, UflashUattentionUlensLens, UfrustrationLens,
    UinverseLens, UisomorphismLens, UkernelUfusionLens, UperiodicityLens, UsurpriseLens,
    VoidLens, WallInspectionLens, WarpLens, WaveLens, WeightFeedbackLens,
    WeightLearningLens, WormholeLens,
};
use shared_data::SharedData;

/// The Telescope: registers all available lenses and scans data through them.
/// Each lens is isolated via catch_unwind — a panic in one lens does not crash others.
pub struct Telescope {
    lenses: Vec<Box<dyn Lens>>,
}

impl Telescope {
    /// Create a new Telescope with all 22 Core lenses registered.
    pub fn new() -> Self {
        #[rustfmt::skip]
        let lenses: Vec<Box<dyn Lens>> = vec![
            Box::new(AllSeeingEyeLens),
            Box::new(AudioLens),
            Box::new(AutoCalibrationLens),
            Box::new(AutocorrelationLens),
            Box::new(BarrierLens),
            Box::new(BatteryChemistryLens),
            Box::new(BigBangLens),
            Box::new(BoseEinsteinLens),
            Box::new(BoundaryLens),
            Box::new(CausalLens),
            Box::new(ChaosLens),
            Box::new(ChipArchitectureLens),
            Box::new(ClusteringLens),
            Box::new(CompassLens),
            Box::new(CompressionLens),
            Box::new(ConcaveLens),
            Box::new(ConformalBootstrapLens),
            Box::new(ConsciousnessLens),
            Box::new(ConsciousnessOrchestratorLens),
            Box::new(ConstantCollectorLens),
            Box::new(ConstantCombinationLens),
            Box::new(ConstantDiscoveryEngineLens),
            Box::new(ConstantFormulaLens),
            Box::new(ContractingScanLens),
            Box::new(ConvexLens),
            Box::new(CorrelationLens),
            Box::new(CryptoLens),
            Box::new(DensityLens),
            Box::new(DestinyLens),
            Box::new(DiamondLens),
            Box::new(DimensionReductionLens),
            Box::new(DimensionalBridgeLens),
            Box::new(DivergenceLens),
            Box::new(ElementCombinationLens),
            Box::new(ElementLens),
            Box::new(EmLens),
            Box::new(EngineDiscoveryLens),
            Box::new(EntropyLens),
            Box::new(EnvironmentLens),
            Box::new(EventHorizonLens),
            Box::new(EvolutionLens),
            Box::new(ExoticMatterLens),
            Box::new(ExpandingScanLens),
            Box::new(FinanceLens),
            Box::new(FissionLens),
            Box::new(FormulaCombinationLens),
            Box::new(FractalLens),
            Box::new(FusionLens),
            Box::new(GodsEyeLens),
            Box::new(GoldenRatioLens),
            Box::new(GoldenZoneLens),
            Box::new(GradientLens),
            Box::new(GraphLens),
            Box::new(GravityLens),
            Box::new(HexagonalLens),
            Box::new(InfiniteDiscoveryLens),
            Box::new(InfinityLens),
            Box::new(InfoLens),
            Box::new(KaleidoscopeLens),
            Box::new(KeywordLens),
            Box::new(LatticeFieldLens),
            Box::new(LensDiscoveryLens),
            Box::new(LightLens),
            Box::new(LightWaveLens),
            Box::new(LoRALens),
            Box::new(MaterialCombinationLens),
            Box::new(MedicineLens),
            Box::new(MemoryLens),
            Box::new(MetricDiscoveryLens),
            Box::new(MetricLens),
            Box::new(MiLens),
            Box::new(MirrorLens),
            Box::new(ModuleDiscoveryLens),
            Box::new(MolecularCombinationLens),
            Box::new(MolecularTransformLens),
            Box::new(MoleculeLens),
            Box::new(MultiscaleLens),
            Box::new(MutationLens),
            Box::new(NetworkLens),
            Box::new(OutlierLens),
            Box::new(OverfittingLens),
            Box::new(PhaseTransitionLens),
            Box::new(PiLens),
            Box::new(PowerLawLens),
            Box::new(PrimeLens),
            Box::new(ProvidenceEyeLens),
            Box::new(QuantumJumpLens),
            Box::new(QuantumLensImpl),
            Box::new(QuantumMicroLens),
            Box::new(RatioLens),
            Box::new(RecursionLens),
            Box::new(RecursiveLoopLens),
            Box::new(RefractionLens),
            Box::new(RelativisticBarrierLens),
            Box::new(RenormalizationLens),
            Box::new(RoboticsLens),
            Box::new(RulerLens),
            Box::new(ScaleLens),
            Box::new(SimulationLens),
            Box::new(SingularityLens),
            Box::new(SolarEfficiencyLens),
            Box::new(SpacetimeLens),
            Box::new(SpectralLens),
            Box::new(SpeculativeDecodeLens),
            Box::new(SphericalLens),
            Box::new(StabilityLens),
            Box::new(StationarityLens),
            Box::new(StimulusLens),
            Box::new(SymmetryBreakingLens),
            Box::new(TachyonLens),
            Box::new(TelepathyLens),
            Box::new(TensionLens),
            Box::new(TensionLinkLens),
            Box::new(ThermoLens),
            Box::new(TimeReversalLens),
            Box::new(TopologyLens),
            Box::new(TransformerAnatomyLens),
            Box::new(TriangleLens),
            Box::new(UbatchUoptimizationLens),
            Box::new(UcombinatorialLens),
            Box::new(UcompletenessLens),
            Box::new(UemergenceLens),
            Box::new(UextrapolationLens),
            Box::new(UflashUattentionUlensLens),
            Box::new(UfrustrationLens),
            Box::new(UinverseLens),
            Box::new(UisomorphismLens),
            Box::new(UkernelUfusionLens),
            Box::new(UperiodicityLens),
            Box::new(UsurpriseLens),
            Box::new(VoidLens),
            Box::new(WallInspectionLens),
            Box::new(WarpLens),
            Box::new(WaveLens),
            Box::new(WeightFeedbackLens),
            Box::new(WeightLearningLens),
            Box::new(WormholeLens),
        ];
        Telescope { lenses }
    }

    /// Scan data through all registered lenses.
    /// Returns lens_name -> LensResult for each lens.
    /// Panics in individual lenses are caught and produce empty results.
    pub fn scan_all(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
    ) -> HashMap<String, LensResult> {
        let shared = SharedData::compute(data, n, d);
        let mut results = HashMap::new();

        for lens in &self.lenses {
            let name = lens.name().to_string();

            let result = panic::catch_unwind(panic::AssertUnwindSafe(|| {
                lens.scan(data, n, d, &shared)
            }));

            match result {
                Ok(lr) => {
                    results.insert(name, lr);
                }
                Err(_) => {
                    results.insert(name, HashMap::new());
                }
            }
        }

        results
    }

    /// Get the number of registered lenses.
    pub fn lens_count(&self) -> usize {
        self.lenses.len()
    }
}

impl Default for Telescope {
    fn default() -> Self {
        Self::new()
    }
}
