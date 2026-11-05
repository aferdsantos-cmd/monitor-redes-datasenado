"""
Módulo de Analytics da Fase 04: Triplo Motor de Inteligência Analítica.

Exporta:
1. Motor 4A: FeatureEngineeringAndAgendaCausalEngine, compute_burstiness, compute_vif_matrix, cusum_detector, granger_causality_test;
2. Motor 4B: CalibratedStanceXAIAndMLOpsEngine, ValidationFoldMetrics, ModelTrainingResults, compute_brier_score, compute_expected_calibration_error;
3. Motor 4C: DigitalBubblesAndSpectrumAnalyzer, BubbleAnalysisReport, CommunityTopologyMetrics, OFFICIAL_SPECTRA;
4. Orquestrador: Phase04IntelligenceOrchestrator, Phase04ConsolidatedDossier.
"""

from src.analytics.calibrated_stance_xai_and_mlops_engine import (
    CalibratedStanceXAIAndMLOpsEngine,
    ModelTrainingResults,
    ValidationFoldMetrics,
    compute_brier_score,
    compute_expected_calibration_error,
    compute_mcnemar_test,
)
from src.analytics.digital_bubbles_and_spectrum_engine import (
    OFFICIAL_SPECTRA,
    BubbleAnalysisReport,
    CommunityTopologyMetrics,
    DigitalBubblesAndSpectrumAnalyzer,
)
from src.analytics.feature_engineering_and_agenda_causal_engine import (
    FeatureEngineeringAndAgendaCausalEngine,
    benjamini_hochberg_fdr,
    compute_burstiness,
    compute_vif_matrix,
    cusum_detector,
    granger_causality_test,
)
from src.analytics.phase04_intelligence_orchestrator import (
    MonitoringWindowSpec,
    Phase04ConsolidatedDossier,
    Phase04IntelligenceOrchestrator,
)

__all__ = [
    # Motor 4A
    "FeatureEngineeringAndAgendaCausalEngine",
    "benjamini_hochberg_fdr",
    "compute_burstiness",
    "compute_vif_matrix",
    "cusum_detector",
    "granger_causality_test",
    # Motor 4B
    "CalibratedStanceXAIAndMLOpsEngine",
    "ValidationFoldMetrics",
    "ModelTrainingResults",
    "compute_brier_score",
    "compute_expected_calibration_error",
    "compute_mcnemar_test",
    # Motor 4C
    "DigitalBubblesAndSpectrumAnalyzer",
    "BubbleAnalysisReport",
    "CommunityTopologyMetrics",
    "OFFICIAL_SPECTRA",
    # Orquestrador
    "Phase04IntelligenceOrchestrator",
    "Phase04ConsolidatedDossier",
    "MonitoringWindowSpec",
]
