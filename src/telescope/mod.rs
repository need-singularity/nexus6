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
pub mod mirror_scan;
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
use mirror_scan::{
    FreeExploreResult, InfiniteCorridorResult, LensCombination,
    MirrorBallResult, MirrorReflectResult, MirrorUniverseResult,
    SelfReflectionResult,
};
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
    // ── new lenses ──
    AnomalyMatchingLens, ArchitecturalProportionLens, ARIMAHiddenLens, ArnoldClassificationLens,
    BandStructureLens, BaryogenesisLens, BernsteinApproximationLens, BirchSwinnertonDyerLens,
    CalabiYauMetricsLens, CharacterInductionLens, ClassNumberLens, CohomologyRingLens,
    ColorHarmonyLens, CommunicationComplexityLens, ConvexConjugacyLens, CosmologicalConstantLens,
    CPViolationLens, DerivedFunctorLens, DiscreteLogLens, DispersionRelationLens,
    EpigeneticLens, ErgodicityBreakingLens, FisherGeometricLens, FrequencyDependentLens,
    GeneNetworkLens, HarmonicSeriesLens, HexameterLens, HolonomyGroupLens,
    IsogenyWalkLens, IsometryGroupLens, KernelMethodGeometryLens, KTheoryLens,
    LatticeBasisLens, LatticeCongruenceLens, LotkaVolterraLens, MacLaneCoherenceLens,
    MagnonLens, MatroidLens, MetacommunityLens, MetricalLens,
    MinimumSpanningTreeLens, MirrorSymmetryAlgLens, MobiusInversionLens, ModularLens,
    MomentMapLens, NarrativeArcLens, NeutralTheoryLens, PadeApproximantLens,
    ParallelComplexityLens, PhaseLockingLens, PlasmaDispersionLens, PolyhedronFaceLens,
    PopulationVectorLens, ProteinFoldingLens, QuantizationGapLens, QueryComplexityLens,
    RademacherComplexityLens, RateCodeLens, ReconnectionLens, ResolutionTreeLens,
    ResourceCompetitionLens, RunningCouplingLens, ScalarCurvatureLens, SchurFunctorLens,
    SkyrmionLens, SplineInterpolationLens, StateSpaceObservabilityLens, SubdifferentialLens,
    TriangulatedCategoryLens, VCDimensionLens,
    UelectromagneticUwaveLens, UmaxwellUequationLens, UsuperconductorUlensLens,
    UheatUconductionLens, UfaradayUinductionLens, UmagneticUmonopoleLens, UconvectionUpatternLens,
};
use shared_data::SharedData;

/// The Telescope: registers all available lenses and scans data through them.
/// Each lens is isolated via catch_unwind — a panic in one lens does not crash others.
pub struct Telescope {
    pub(crate) lenses: Vec<Box<dyn Lens>>,
}

impl Telescope {
    /// Create a new Telescope with all 22 Core lenses registered.
    pub fn new() -> Self {
        #[rustfmt::skip]
        let lenses: Vec<Box<dyn Lens>> = vec![
            Box::new(AllSeeingEyeLens),
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
            Box::new(EventHorizonLens),
            Box::new(EvolutionLens),
            Box::new(ExoticMatterLens),
            Box::new(ExpandingScanLens),
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
            Box::new(WeightLearningLens),
            Box::new(WormholeLens),
            // ── new lenses ──
            Box::new(AnomalyMatchingLens),
            Box::new(ArchitecturalProportionLens),
            Box::new(ARIMAHiddenLens),
            Box::new(ArnoldClassificationLens),
            Box::new(AudioLens),
            Box::new(BandStructureLens),
            Box::new(BaryogenesisLens),
            Box::new(BernsteinApproximationLens),
            Box::new(BirchSwinnertonDyerLens),
            Box::new(CalabiYauMetricsLens),
            Box::new(CharacterInductionLens),
            Box::new(ClassNumberLens),
            Box::new(CohomologyRingLens),
            Box::new(ColorHarmonyLens),
            Box::new(CommunicationComplexityLens),
            Box::new(ConvexConjugacyLens),
            Box::new(CosmologicalConstantLens),
            Box::new(CPViolationLens),
            Box::new(CryptoLens),
            Box::new(DerivedFunctorLens),
            Box::new(DiscreteLogLens),
            Box::new(DispersionRelationLens),
            Box::new(EnvironmentLens),
            Box::new(EpigeneticLens),
            Box::new(ErgodicityBreakingLens),
            Box::new(FinanceLens),
            Box::new(FisherGeometricLens),
            Box::new(FrequencyDependentLens),
            Box::new(GeneNetworkLens),
            Box::new(HarmonicSeriesLens),
            Box::new(HexameterLens),
            Box::new(HolonomyGroupLens),
            Box::new(IsogenyWalkLens),
            Box::new(IsometryGroupLens),
            Box::new(KernelMethodGeometryLens),
            Box::new(KTheoryLens),
            Box::new(LatticeBasisLens),
            Box::new(LatticeCongruenceLens),
            Box::new(LotkaVolterraLens),
            Box::new(MacLaneCoherenceLens),
            Box::new(MagnonLens),
            Box::new(MatroidLens),
            Box::new(MedicineLens),
            Box::new(MetacommunityLens),
            Box::new(MetricalLens),
            Box::new(MinimumSpanningTreeLens),
            Box::new(MirrorSymmetryAlgLens),
            Box::new(MobiusInversionLens),
            Box::new(ModularLens),
            Box::new(MomentMapLens),
            Box::new(NarrativeArcLens),
            Box::new(NeutralTheoryLens),
            Box::new(PadeApproximantLens),
            Box::new(ParallelComplexityLens),
            Box::new(PhaseLockingLens),
            Box::new(PlasmaDispersionLens),
            Box::new(PolyhedronFaceLens),
            Box::new(PopulationVectorLens),
            Box::new(ProteinFoldingLens),
            Box::new(QuantizationGapLens),
            Box::new(QueryComplexityLens),
            Box::new(RademacherComplexityLens),
            Box::new(RateCodeLens),
            Box::new(ReconnectionLens),
            Box::new(ResolutionTreeLens),
            Box::new(ResourceCompetitionLens),
            Box::new(RoboticsLens),
            Box::new(RunningCouplingLens),
            Box::new(ScalarCurvatureLens),
            Box::new(SchurFunctorLens),
            Box::new(SkyrmionLens),
            Box::new(SplineInterpolationLens),
            Box::new(StateSpaceObservabilityLens),
            Box::new(SubdifferentialLens),
            Box::new(TriangulatedCategoryLens),
            Box::new(VCDimensionLens),
            Box::new(WeightFeedbackLens),
            Box::new(UelectromagneticUwaveLens),
            Box::new(UmaxwellUequationLens),
            Box::new(UsuperconductorUlensLens),
            Box::new(UheatUconductionLens),
            Box::new(UfaradayUinductionLens),
            Box::new(UmagneticUmonopoleLens),
            Box::new(UconvectionUpatternLens),
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

    /// Retire inactive lenses whose scan results are empty.
    /// Returns the names of removed lenses.
    pub fn retire_inactive(&mut self, data: &[f64], n: usize, d: usize) -> Vec<String> {
        let shared = SharedData::compute(data, n, d);
        let mut retired = Vec::new();
        self.lenses.retain(|lens| {
            let result = panic::catch_unwind(panic::AssertUnwindSafe(|| {
                lens.scan(data, n, d, &shared)
            }));
            match result {
                Ok(lr) if lr.is_empty() => {
                    retired.push(lens.name().to_string());
                    false
                }
                Err(_) => {
                    retired.push(lens.name().to_string());
                    false
                }
                _ => true,
            }
        });
        retired
    }

    // ─── 거울 우주 (통합 API) ────────────────────────────────────

    /// 거울 우주: 모든 렌즈가 거울이자 관찰자 — 서로를 비추면 모두가 연결됨.
    pub fn mirror_universe(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        lens_filter: Option<&[&str]>,
        max_lenses: Option<usize>,
    ) -> MirrorUniverseResult {
        mirror_scan::mirror_universe(&self.lenses, data, n, d, lens_filter, max_lenses)
    }

    /// 무한 거울 복도: 두 렌즈 간 반복 반사 → 수렴/발산/주기 감지.
    pub fn infinite_corridor(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        lens_a: &str,
        lens_b: &str,
        max_iter: usize,
    ) -> Option<InfiniteCorridorResult> {
        mirror_scan::infinite_corridor(&self.lenses, data, n, d, lens_a, lens_b, max_iter)
    }

    /// 자기 반사 (Narcissus): 렌즈가 자기 출력을 반복 입력 → 고정점 탐색.
    pub fn self_reflect(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        lens_name: &str,
        max_iter: usize,
    ) -> Option<SelfReflectionResult> {
        mirror_scan::self_reflect(&self.lenses, data, n, d, lens_name, max_iter)
    }

    // ─── 실시간 변형 + 자율 탐색 ───────────────────────────────

    /// 자율 렌즈 조합 발견: 미러볼 결과에서 최적 렌즈 조합 자동 탐색.
    pub fn discover_combinations(
        &self,
        result: &MirrorUniverseResult,
        combo_size: usize,
    ) -> Vec<LensCombination> {
        mirror_scan::discover_combinations(result, combo_size)
    }

    /// 규칙 없는 자유 탐색: 미러볼을 세대별로 변형하며 진화.
    pub fn free_explore(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        max_lenses: Option<usize>,
        max_generations: usize,
    ) -> FreeExploreResult {
        mirror_scan::free_explore(&self.lenses, data, n, d, max_lenses, max_generations)
    }

    // ─── 하위 호환 ──────────────────────────────────────────────

    /// 거울반사 (2개 렌즈). mirror_universe의 부분 호출.
    pub fn mirror_reflect(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        lens_a: &str,
        lens_b: &str,
    ) -> Option<MirrorReflectResult> {
        mirror_scan::mirror_reflect(&self.lenses, data, n, d, lens_a, lens_b)
    }

    /// 미러볼 (N개 렌즈). mirror_universe의 전체 호출.
    pub fn mirror_ball(
        &self,
        data: &[f64],
        n: usize,
        d: usize,
        max_lenses: Option<usize>,
    ) -> MirrorBallResult {
        mirror_scan::mirror_ball(&self.lenses, data, n, d, max_lenses)
    }
}

impl Default for Telescope {
    fn default() -> Self {
        Self::new()
    }
}
