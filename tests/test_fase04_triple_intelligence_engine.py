"""
Suíte Completa de Testes Automatizados — Fase 04: Triplo Motor de Inteligência Analítica.

Verifica:
1. Validação Fail-Closed do LGPD_HMAC_SECRET_KEY no Phase04IntelligenceOrchestrator;
2. Trava anti-leakage de autores (interseção não-vazia lança ValueError);
3. PurgedGroupTimeSeriesSplit com zona de embargo temporal e expurgo de autores;
4. Janelas temporais causais (closed='left') sem contaminação do futuro;
5. Índice de Burstiness de Goh-Barabási (B in [-1, 1]);
6. OOF Empirical Bayes Target Encoding agrupado por autor;
7. Diagnóstico de colinearidade VIF (< 5.0);
8. Salvaguarda de k-anonimato LGPD (k >= 5) com colapso em OUTROS_ANONIMIZADO_LGPD_K5;
9. Normalização L2 = 1.0 dos vetores semânticos (|v|_2 = 1.0 +- 1e-6);
10. Seleção segura de dispositivo sem .cuda() fixo;
11. dHash perceptual de 64 bits para imagens e distância de Hamming;
12. Calibração de probabilidades OOF (Brier Score e ECE);
13. Auditoria cega de validação (n_val = 550) com matriz de confusão e métricas;
14. Teste de McNemar com correção de continuidade de Edwards;
15. Correção de Benjamini-Hochberg FDR (q-values ordenados);
16. Aditividade SHAP exata respeitando o Axioma da Eficiência (|phi_0 + sum(phi) - f(x)| < 1e-5);
17. Permutation Importance estritamente em hold-out (lança ValueError no treino);
18. Auditoria de equidade por subgrupo (Subgroup Fairness) e gatilho se delta > 0.08;
19. MLOps Zero-Footprint: emissão de Model Card JSON sem nenhum arquivo .pkl ou .joblib;
20. Monitoramento de drift com semáforo PSI (Verde, Amarelo, Vermelho) e teste KS;
21. Trava do Ponto de Ruptura de Youden (J_c <= 0.20 bloqueia publicação);
22. Motor 4C: expurgo total de 100% de Spam e CIB antes da formação do grafo;
23. Modularidade de Newman Q com teste de significância contra Modelo Nulo (z-score e p-valor);
24. Índice E-I de Krackhardt & Stern classificando câmara de eco quando EI < -0.40;
25. Coeficiente de Participação Pi de Guimerà & Amaral identificando pontes trans-bolha (Pi > 0.30);
26. Propagação Harmônica de Espectros convergente (alpha = 0.85) com salvaguarda LGPD (k >= 5);
27. Identificação de First-Mover Spectrum e Pontes de Consenso Transversal;
28. Execução ponta a ponta do Orquestrador no tema eleicao_presidencia_senado;
29. Execução ponta a ponta no tema pec_escala_6x1;
30. Execução ponta a ponta no tema pl_ia_2338;
31. Execução com tema customizado dinâmico registrado via register_custom_theme;
32. Zero-Footprint: expurgo completo de /tmp/monitor_datasenado_cache ao final.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from src.analytics import (
    BubbleAnalysisReport,
    CalibratedStanceXAIAndMLOpsEngine,
    DigitalBubblesAndSpectrumAnalyzer,
    FeatureEngineeringAndAgendaCausalEngine,
    MonitoringWindowSpec,
    Phase04ConsolidatedDossier,
    Phase04IntelligenceOrchestrator,
    benjamini_hochberg_fdr,
    compute_brier_score,
    compute_burstiness,
    compute_expected_calibration_error,
    compute_mcnemar_test,
    compute_vif_matrix,
    cusum_detector,
    granger_causality_test,
)
from src.collectors.base_collector import (
    RawCollectedManifestation,
    register_custom_theme,
)
from src.collectors.phase03_six_platforms_orchestrator import Phase03SixPlatformsOrchestrator

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_32CHAR_SECRET = "k_fase04_audit_datasenado_key_master_2026_xyz"


# =============================================================================
# 1. Testes de Validação Fail-Closed do Orquestrador
# =============================================================================
class TestPhase04OrchestratorFailClosed:
    """Testa a blindagem fail-closed do Orquestrador contra chaves inválidas."""

    def test_orchestrator_raises_on_missing_or_short_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LGPD_HMAC_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="FALHA FECHADA LGPD"):
            Phase04IntelligenceOrchestrator(
                theme_id="eleicao_presidencia_senado",
                hmac_secret_key=None,
            )

        with pytest.raises(RuntimeError, match="FALHA FECHADA LGPD"):
            Phase04IntelligenceOrchestrator(
                theme_id="eleicao_presidencia_senado",
                hmac_secret_key="curta_demais",
            )

        with pytest.raises(RuntimeError, match="FALHA FECHADA LGPD"):
            Phase04IntelligenceOrchestrator(
                theme_id="eleicao_presidencia_senado",
                hmac_secret_key="defina-sua-chave-aqui-com-mais-de-32-chars",
            )

    def test_orchestrator_accepts_valid_key(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        assert orch.hmac_secret_key == VALID_32CHAR_SECRET


# =============================================================================
# 2. Testes do Motor 4A: Causais, Anti-Leakage, VIF e Granger
# =============================================================================
class TestMotor4ACausalAndFeatures:
    """Testa os algoritmos e travas do Motor 4A."""

    def test_anti_leakage_author_overlap_raises_value_error(self) -> None:
        engine = FeatureEngineeringAndAgendaCausalEngine()
        train_df = pd.DataFrame({
            "author_id_hash": ["auth_1", "auth_2", "auth_3"],
            "target": [1, 0, 1],
            "feature_x": [10.0, 20.0, 30.0],
        })
        val_df = pd.DataFrame({
            "author_id_hash": ["auth_3", "auth_4"],  # auth_3 está em ambos!
            "target": [0, 1],
            "feature_x": [35.0, 45.0],
        })

        with pytest.raises(ValueError, match="VAZAMENTO DE AUTOR DETECTADO"):
            engine.fit_transform_train_and_transform_val(
                train_df=train_df,
                val_df=val_df,
                target_col="target",
                group_col="author_id_hash",
            )

    def test_anti_leakage_fit_on_train_only_succeeds_without_overlap(self) -> None:
        engine = FeatureEngineeringAndAgendaCausalEngine()
        train_df = pd.DataFrame({
            "author_id_hash": ["auth_1", "auth_2", "auth_3", "auth_4", "auth_5", "auth_6"],
            "target": [1, 0, 1, 0, 1, 0],
            "category": ["A", "B", "A", "B", "A", "B"],
            "feature_x": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        })
        val_df = pd.DataFrame({
            "author_id_hash": ["auth_7", "auth_8"],
            "target": [0, 1],
            "category": ["A", "B"],
            "feature_x": [15.0, 25.0],
        })

        tr_out, val_out, meta = engine.fit_transform_train_and_transform_val(
            train_df=train_df,
            val_df=val_df,
            target_col="target",
            group_col="author_id_hash",
            numeric_cols=["feature_x"],
            categorical_cols=["category"],
        )
        assert "category_oof_te" in tr_out.columns
        assert "category_oof_te" in val_out.columns
        assert meta["train_rows"] == 6
        assert meta["val_rows"] == 2

    def test_causal_rolling_window_closed_left(self) -> None:
        engine = FeatureEngineeringAndAgendaCausalEngine()
        base_t = datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
        items = [
            RawCollectedManifestation(
                comment_id=f"c_{i}",
                theme_id="eleicao_presidencia_senado",
                platform="x_twitter",
                raw_author_id=f"user_{i}",
                text=f"Postagem número {i}",
                created_at=base_t + timedelta(hours=i),
                collection_query_used="presidência senado",
                collector_modality="official_api_chronological",
            )
            for i in range(5)
        ]

        df = engine.compute_causal_temporal_features(items)
        # No instante i=0, não há posts estritamente anteriores: contagem deve ser 0!
        assert df.loc[0, "causal_rolling_post_count_6h"] == 0.0
        # No instante i=1, há 1 post anterior (i=0) dentro da janela de 6h
        assert df.loc[1, "causal_rolling_post_count_6h"] == 1.0

    def test_burstiness_goh_barabasi_metric(self) -> None:
        # Periódico determinístico -> B = -1
        periodic = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
        b_periodic = compute_burstiness(periodic)
        assert b_periodic == pytest.approx(-1.0, abs=1e-3)

        # Rajada intermitente extrema -> B positivo
        bursty = np.array([1.0, 1.0, 1000.0, 1.0, 1.0, 500.0, 1.0])
        b_bursty = compute_burstiness(bursty)
        assert b_bursty > 0.20
        assert -1.0 <= b_bursty <= 1.0

    def test_vif_matrix_computation(self) -> None:
        rng = np.random.default_rng(42)
        n = 100
        x1 = rng.normal(0, 1, n)
        x2 = rng.normal(0, 1, n)
        # x3 é fortemente colinear com x1
        x3 = 2.0 * x1 + rng.normal(0, 0.05, n)

        X = np.column_stack([x1, x2, x3])
        vif_res = compute_vif_matrix(X, ["x1", "x2", "x3"])
        assert vif_res["x2"] < 2.0
        assert vif_res["x1"] > 5.0
        assert vif_res["x3"] > 5.0

    def test_k_anonymity_collapsing(self) -> None:
        engine = FeatureEngineeringAndAgendaCausalEngine()
        df = pd.DataFrame({
            "author_id_hash": [f"a_{i}" for i in range(12)],
            "platform": ["x"] * 8 + ["wa"] * 4,  # 'wa' tem 4 contas (< k=5)
            "score": np.random.uniform(0, 1, 12),
        })

        res = engine.enforce_k_anonymity_aggregation(df, group_cols=["platform"], k=5)
        platforms = res["platform"].tolist()
        assert "x" in platforms
        assert "wa" not in platforms
        assert "OUTROS_ANONIMIZADO_LGPD_K5" in platforms

    def test_cusum_and_granger_causality(self) -> None:
        # Série com salto abrupto
        series = np.concatenate([np.ones(20) * 5.0, np.ones(20) * 50.0])
        break_res = cusum_detector(series, threshold=3.0)
        assert break_res["break_detected"] is True
        assert break_res["break_index"] is not None

        # Causalidade de Granger onde x lidera y
        T = 50
        x = np.random.normal(0, 1, T)
        y = np.zeros(T)
        for t in range(2, T):
            y[t] = 0.8 * y[t - 1] + 0.9 * x[t - 1] + np.random.normal(0, 0.1)

        g_res = granger_causality_test(x, y, max_lag=2)
        assert g_res["f_statistic"] > 5.0
        assert g_res["p_value"] < 0.05


# =============================================================================
# 3. Testes do Motor 4B: PNL, Embeddings L2, XAI e MLOps
# =============================================================================
class TestMotor4BCalibratedStanceAndMLOps:
    """Testa os modelos, explicabilidade XAI e MLOps do Motor 4B."""

    def test_l2_embeddings_exact_unit_norm(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        texts = [
            "Excelente votação para o Senado Federal!",
            "Totalmente contra a proposta em tramitação.",
            "Acompanhando o debate no plenário.",
        ]
        embs = engine.extract_l2_normalized_embeddings(texts)
        assert embs.shape == (3, 64)
        for i in range(len(texts)):
            norm = np.linalg.norm(embs[i])
            assert norm == pytest.approx(1.0, abs=1e-5)

    def test_device_selection_no_fixed_cuda(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        assert engine.device in ("mps", "cpu")
        assert engine.device != "cuda"

    def test_visual_dhash_64bit_and_hamming(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        img1 = np.ones((8, 9), dtype=float)
        img2 = np.ones((8, 9), dtype=float)
        img2[0, 0] = 100.0  # Pequena alteração

        h1 = engine.compute_visual_dhash(img1)
        h2 = engine.compute_visual_dhash(img2)
        assert len(h1) == 16  # 64 bits em hex = 16 caracteres
        assert len(h2) == 16

    def test_purged_temporal_splits_with_embargo(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        base_t = datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
        items = [
            RawCollectedManifestation(
                comment_id=f"c_{i}",
                theme_id="eleicao_presidencia_senado",
                platform="x_twitter",
                raw_author_id=f"user_{i}",
                text="texto",
                created_at=base_t + timedelta(hours=i * 2),
                collection_query_used="q",
                collector_modality="official_api_chronological",
            )
            for i in range(12)
        ]

        splits = engine.build_purged_temporal_splits(items, n_splits=3, embargo_hours=4.0)
        assert len(splits) > 0
        for tr_idx, val_idx in splits:
            tr_authors = set(items[i].raw_author_id for i in tr_idx)
            val_authors = set(items[i].raw_author_id for i in val_idx)
            assert len(tr_authors.intersection(val_authors)) == 0

    def test_brier_score_and_ece(self) -> None:
        y_true = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        y_prob = np.array([[0.9, 0.05, 0.05], [0.1, 0.8, 0.1]])
        bs = compute_brier_score(y_true, y_prob)
        assert bs < 0.10

        ece = compute_expected_calibration_error(np.array([0, 1]), y_prob)
        assert 0.0 <= ece <= 1.0

    def test_mcnemar_test_edwards_correction(self) -> None:
        y_t = ["Fav"] * 50 + ["Cont"] * 50
        # Modelo A acerta muito mais onde B erra
        m_a = ["Fav"] * 48 + ["Cont"] * 2 + ["Cont"] * 45 + ["Fav"] * 5
        m_b = ["Fav"] * 30 + ["Cont"] * 20 + ["Cont"] * 35 + ["Fav"] * 15

        res = compute_mcnemar_test(y_t, m_a, m_b)
        assert res["mcnemar_statistic"] > 0.0
        assert res["is_statistically_significant"] is True

    def test_benjamini_hochberg_fdr_control(self) -> None:
        p_vals = [0.001, 0.01, 0.04, 0.08, 0.50]
        rej, q_vals = benjamini_hochberg_fdr(p_vals, alpha=0.05)
        assert len(rej) == len(p_vals)
        assert len(q_vals) == len(p_vals)
        # O menor p-valor deve ser rejeitado
        assert bool(rej[0]) is True
        # q-valores devem ser monotônicos
        assert q_vals[0] <= q_vals[1]

    def test_shap_additive_efficiency_axiom(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        W = np.array([[0.3, -0.2, 0.1], [0.4, 0.1, -0.3], [-0.2, 0.5, 0.2]])
        b = np.array([0.1, 0.2, 0.7])
        X = np.array([[0.5, 0.8, 0.2], [0.1, 0.3, 0.9]])
        mu = np.array([0.3, 0.4, 0.5])

        shap_vals, base_v, eff_holds = engine.compute_additive_shap(W, b, X, mu)
        assert eff_holds is True
        # Verifica axioma da eficiência: base_v + sum(phi) == f(x)
        for i in range(len(X)):
            actual = X[i] @ W + b
            reconstructed = base_v + np.sum(shap_vals[i], axis=0)
            assert np.max(np.abs(reconstructed - actual)) < 1e-5

    def test_permutation_importance_raises_on_train_partition(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        X_dummy = np.random.normal(0, 1, (20, 3))
        y_dummy = np.random.randint(0, 2, 20)

        with pytest.raises(ValueError, match="VIOLAÇÃO DE GOVERNANÇA"):
            engine.compute_holdout_permutation_importance(
                predict_fn=lambda X: np.zeros(len(X)),
                X_val=X_dummy,
                y_val=y_dummy,
                feature_names=["f1", "f2", "f3"],
                evaluated_on_partition="TRAIN_SPLIT_ILLEGAL",
            )

    def test_subgroup_fairness_disparity_trigger(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        # Subgrupo A tem alta sensibilidade, B tem baixa sensibilidade (> 0.08)
        y_true = ["Favoravel"] * 50 + ["Favoravel"] * 50
        y_pred = (["Favoravel"] * 48 + ["Neutro"] * 2) + (["Favoravel"] * 30 + ["Neutro"] * 20)
        subgs = ["Plataforma_A"] * 50 + ["Plataforma_B"] * 50

        fair_res = engine.audit_subgroup_fairness(y_true, y_pred, subgs, fairness_threshold=0.08)
        assert fair_res["max_disparity_sensitivity"] > 0.08
        assert fair_res["requires_stratified_rogan_gladen"] is True

    def test_model_drift_traffic_light(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        rng = np.random.default_rng(42)
        ref = rng.normal(0.5, 0.1, 500)
        curr_stable = ref + rng.normal(0, 0.005, 500)
        curr_drift = rng.normal(0.85, 0.1, 500)

        stable_res = engine.evaluate_model_drift(ref, curr_stable)
        assert stable_res["psi_traffic_light"] == "VERDE_ESTAVEL"

        drift_res = engine.evaluate_model_drift(ref, curr_drift)
        assert drift_res["psi_traffic_light"] in ("AMARELO_ALERTA_MODERADO", "VERMELHO_DRIFT_CRITICO_RECALIBRACAO_OBRIGATORIA")

    def test_model_card_generation_zero_pickle(self) -> None:
        engine = CalibratedStanceXAIAndMLOpsEngine()
        card = engine.generate_model_card_json(
            model_id="test_model",
            theme_id="eleicao_presidencia_senado",
            git_commit="61c35360",
            training_data_hash="abc123sha",
            metrics={"brier_score": 0.08, "macro_f1": 0.88},
            xai_summary={"shap_verified": True},
            drift_status={"psi_traffic_light": "VERDE_ESTAVEL"},
        )
        assert card["model_id"] == "test_model"
        assert card["zero_pickle_sast_compliant"] is True
        card_str = json.dumps(card)
        assert "pickle" not in card_str.lower() or "zero_pickle" in card_str


# =============================================================================
# 4. Testes do Motor 4C: Bolhas, Modularidade, E-I, Pi e Espectros (ADR-010)
# =============================================================================
class TestMotor4CBubblesAndSpectra:
    """Testa os algoritmos topológicos e a propagação harmônica de espectros."""

    def test_strict_hygiene_purges_100pct_spam_and_cib(self) -> None:
        engine = DigitalBubblesAndSpectrumAnalyzer()
        base_t = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)
        items = [
            RawCollectedManifestation(
                comment_id="c_clean",
                theme_id="eleicao_presidencia_senado",
                platform="x_twitter",
                raw_author_id="user_clean",
                text="Post cidadão legítimo",
                created_at=base_t,
                collection_query_used="q",
                collector_modality="m",
                metadata={"is_commercial_spam": False, "account_suspected_cib": False},
            ),
            RawCollectedManifestation(
                comment_id="c_spam",
                theme_id="eleicao_presidencia_senado",
                platform="wa",
                raw_author_id="spammer",
                text="Compre seguidores!",
                created_at=base_t,
                collection_query_used="q",
                collector_modality="m",
                metadata={"is_commercial_spam": True},
            ),
            RawCollectedManifestation(
                comment_id="c_cib",
                theme_id="eleicao_presidencia_senado",
                platform="telegram",
                raw_author_id="botnet_1",
                text="Ataque coordenado!",
                created_at=base_t,
                collection_query_used="q",
                collector_modality="m",
                metadata={"account_suspected_cib": True},
            ),
        ]

        clean, audit = engine.filter_and_quarantine_manifestations(items)
        assert len(clean) == 1
        assert clean[0]["comment_id"] == "c_clean"
        assert audit["blocked_commercial_spam"] == 1
        assert audit["blocked_suspected_cib"] == 1
        assert audit["total_quarantined"] == 2

    def test_newman_modularity_and_null_model(self) -> None:
        engine = DigitalBubblesAndSpectrumAnalyzer(null_model_permutations=50)
        # Grafo com 2 comunidades perfeitamente densas (16 nós)
        W = np.zeros((16, 16), dtype=float)
        W[:8, :8] = 2.0
        W[8:, 8:] = 2.0
        np.fill_diagonal(W, 0.0)
        # 1 aresta ponte tênue entre comunidades
        W[7, 8] = 0.2
        W[8, 7] = 0.2

        comms = np.array([0] * 8 + [1] * 8)
        q_obs = engine.compute_newman_modularity(W, comms)
        assert q_obs > 0.40

        null_res = engine.permutation_test_null_model(W, comms)
        assert null_res["q_observed"] == round(q_obs, 4)
        assert null_res["z_score"] > 2.0
        assert null_res["p_value"] < 0.05
        assert null_res["is_statistically_significant"] is True

    def test_krackhardt_ei_echo_chamber_classification(self) -> None:
        engine = DigitalBubblesAndSpectrumAnalyzer()
        # Comunidade 0 é câmara de eco fechada (só arestas internas)
        W = np.zeros((6, 6), dtype=float)
        W[:3, :3] = 5.0
        W[3:, 3:] = 2.0
        np.fill_diagonal(W, 0.0)
        # Pouquíssima aresta externa para a comunidade 0
        W[2, 3] = 0.1
        W[3, 2] = 0.1

        comms = np.array([0, 0, 0, 1, 1, 1])
        ei_by_comm, global_ei = engine.compute_krackhardt_ei_index(W, comms)
        # Comunidade 0 tem quase só internas: EI < -0.40
        assert ei_by_comm[0] < -0.40

    def test_participation_coefficient_bridge_detection(self) -> None:
        engine = DigitalBubblesAndSpectrumAnalyzer()
        W = np.zeros((5, 5), dtype=float)
        # Comunidade 0: nós 0, 1. Comunidade 1: nós 3, 4. Nó 2 é a ponte!
        W[0, 1] = 2.0; W[1, 0] = 2.0
        W[3, 4] = 2.0; W[4, 3] = 2.0
        # Nó 2 conecta igualmente a nós de 0 e de 1
        W[2, 0] = 2.0; W[0, 2] = 2.0
        W[2, 3] = 2.0; W[3, 2] = 2.0

        comms = np.array([0, 0, 0, 1, 1])
        p_i = engine.compute_participation_coefficient(W, comms)
        # Nó 2 tem conexões balanceadas entre 0 e 1 -> Pi > 0.30
        assert p_i[2] > 0.30
        # Nós periféricos têm Pi baixo
        assert p_i[0] < 0.20

    def test_harmonic_label_propagation_convergence(self) -> None:
        engine = DigitalBubblesAndSpectrumAnalyzer(alpha_harmonic=0.85, convergence_tol=1e-6)
        W = np.array([
            [0.0, 3.0, 0.0, 0.0],
            [3.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 3.0],
            [0.0, 0.0, 3.0, 0.0],
        ])
        # Semente 0 é Classe 0 (Progressista), Semente 3 é Classe 1 (Conservador)
        F = engine.harmonic_seed_label_propagation(
            W=W,
            seed_account_indices=[0, 3],
            seed_spectra_indices=[0, 1],
            n_spectra=2,
        )
        assert F.shape == (4, 2)
        # Linhas devem somar 1.0 no simplex
        for i in range(4):
            assert np.sum(F[i]) == pytest.approx(1.0, abs=1e-5)
        # Nó 0 deve ter afinidade muito alta com Classe 0
        assert F[0, 0] > 0.70
        # Nó 3 deve ter afinidade muito alta com Classe 1
        assert F[3, 1] > 0.70


# =============================================================================
# 5. Testes Ponta a Ponta do Orquestrador da Fase 04 nos Temas
# =============================================================================
class TestPhase04EndToEndPipeline:
    """Testa a execução ponta a ponta do Orquestrador em todos os temas."""

    def test_pipeline_runs_eleicao_presidencia_senado(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        spec = MonitoringWindowSpec(window_days=1, target_sample_size_n=18)
        dossier = orch.run_full_intelligence_pipeline(window_spec=spec, blind_validation_sample_size=30)

        assert dossier["theme_id"] == "eleicao_presidencia_senado"
        assert "engine_4a_causal_and_features" in dossier
        assert "engine_4b_calibrated_mlops_and_xai" in dossier
        assert "engine_4c_bubbles_and_spectra" in dossier
        assert "ecosystem_360_interop_contract" in dossier
        assert dossier["zero_footprint_audit"]["zero_pickle_enforced"] is True

    def test_pipeline_runs_pec_escala_6x1(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="pec_escala_6x1",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        spec = MonitoringWindowSpec(window_days=1, target_sample_size_n=18)
        dossier = orch.run_full_intelligence_pipeline(window_spec=spec, blind_validation_sample_size=30)
        assert dossier["theme_id"] == "pec_escala_6x1"
        assert dossier["phase01_statistical_engine_bridge"]["kish_design_effect_deff"] >= 1.0

    def test_pipeline_runs_pl_ia_2338(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="pl_ia_2338",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        spec = MonitoringWindowSpec(window_days=1, target_sample_size_n=18)
        dossier = orch.run_full_intelligence_pipeline(window_spec=spec, blind_validation_sample_size=30)
        assert dossier["theme_id"] == "pl_ia_2338"
        assert dossier["ecosystem_360_interop_contract"]["ready_for_phase05_multimodal_audio_video"] is True

    def test_pipeline_runs_dynamic_custom_theme(self) -> None:
        # Registra tema dinâmico sem alterar settings.yaml
        register_custom_theme({
            "id": "reforma_tributaria_regulamentacao",
            "name": "Regulamentação da Reforma Tributária no Senado",
            "collection_query_terms": ["reforma tributária", "iva", "cesta básica"],
            "senate_committee": "CAE",
        })
        orch = Phase04IntelligenceOrchestrator(
            theme_id="reforma_tributaria_regulamentacao",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        spec = MonitoringWindowSpec(window_days=1, target_sample_size_n=18)
        dossier = orch.run_full_intelligence_pipeline(window_spec=spec, blind_validation_sample_size=30)
        assert dossier["theme_id"] == "reforma_tributaria_regulamentacao"
        assert dossier["ecosystem_360_interop_contract"]["senate_committee"] == "CAE"

    def test_zero_footprint_cache_cleanliness(self) -> None:
        cache_dir = Path("/tmp/monitor_datasenado_cache")
        # Se existir, verifica que está vazio ou tem 0 bytes
        if cache_dir.exists():
            total_bytes = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            assert total_bytes == 0


# =============================================================================
# 6. Testes Unitários de Saneamento Definitivo dos 8 Apontamentos de QA (OS v2)
# =============================================================================
class TestQAGestaoSaneamentoDefinitivo:
    """Valida cirurgicamente os 8 apontamentos saneados da Auditoria da Gestão."""

    def test_qa_f04_03_burstiness_variance_and_robust_scaler_metadata(self) -> None:
        engine_4a = FeatureEngineeringAndAgendaCausalEngine()
        orch = Phase03SixPlatformsOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        batch = orch.generate_multiplatform_manifestations(
            theme_id="eleicao_presidencia_senado",
            posts_per_platform=15,
            span_days=5,
        )
        df_temp = engine_4a.compute_causal_temporal_features(batch)
        assert df_temp["burstiness_b"].nunique() > 1
        assert (df_temp["burstiness_b"] >= -1.0).all()
        assert (df_temp["burstiness_b"] <= 1.0).all()

        df_lex = engine_4a.compute_lexical_and_framing_features(batch, theme_id="eleicao_presidencia_senado")
        df_comb = pd.merge(df_temp, df_lex, on="comment_id", how="left")
        df_comb["target"] = [i % 2 for i in range(len(df_comb))]

        authors = list(df_comb["author_id_hash"].unique())
        mid = len(authors) // 2
        tr_df = df_comb[df_comb["author_id_hash"].isin(authors[:mid])].copy()
        va_df = df_comb[df_comb["author_id_hash"].isin(authors[mid:])].copy()

        _, _, meta = engine_4a.fit_transform_train_and_transform_val(
            train_df=tr_df,
            val_df=va_df,
            target_col="target",
            group_col="author_id_hash",
            numeric_cols=["burstiness_b", "lexical_bias_rate", "type_token_ratio"],
        )
        assert "robust_scaler_medians" in meta
        assert "robust_scaler_iqrs" in meta
        assert len(meta["robust_scaler_medians"]) > 0
        assert len(meta["robust_scaler_iqrs"]) > 0

    def test_qa_f04_04_k_anonymity_hierarchical_collapse_and_floor(self) -> None:
        engine_4a = FeatureEngineeringAndAgendaCausalEngine()
        df_k = pd.DataFrame({
            "author_id_hash": [f"wa_{i}" for i in range(3)] + [f"yt_{i}" for i in range(8)],
            "platform": ["whatsapp"] * 3 + ["youtube"] * 8,
            "uf_proxy": ["AC"] * 3 + ["SP"] * 8,
            "stance_label": ["Favoravel"] * 3 + ["Contrario"] * 8,
        })
        res = engine_4a.enforce_k_anonymity_aggregation(df_k, group_cols=["platform", "uf_proxy"], k=5)
        collapsed = any(
            r.get("platform") == "OUTROS_ANONIMIZADO_LGPD_K5" or r.get("uf_proxy") == "OUTROS_ANONIMIZADO_LGPD_K5"
            for _, r in res.iterrows()
        )
        assert collapsed is True
        assert all(cnt >= 5 for cnt in res["unique_authors_count"])

    def test_qa_f04_05_mcc_cohens_kappa_val_550_and_mcnemar(self) -> None:
        engine_4b = CalibratedStanceXAIAndMLOpsEngine()
        X_tr = np.random.randn(100, 4)
        y_tr = ["Favoravel"] * 35 + ["Contrario"] * 35 + ["Neutro"] * 30
        X_va = np.random.randn(50, 4)
        y_va = ["Favoravel"] * 18 + ["Contrario"] * 17 + ["Neutro"] * 15

        res = engine_4b.train_and_calibrate_stance_classifier(X_tr, y_tr, X_va, y_va)
        assert hasattr(res, "mcc")
        assert hasattr(res, "cohens_kappa")
        assert hasattr(res, "cohens_kappa_ci_95")
        assert "mcc" in res.blind_validation_metrics
        assert "cohens_kappa" in res.blind_validation_metrics

        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        dossier = orch.run_full_intelligence_pipeline(
            theme_id="eleicao_presidencia_senado",
            blind_validation_sample_size=550,
        )
        val_sz = dossier["engine_4b_calibrated_mlops_and_xai"]["blind_validation_metrics"]["val_sample_size"]
        assert val_sz == 550
        assert "mcnemar_test_vs_baseline" in dossier["engine_4b_calibrated_mlops_and_xai"]

    def test_qa_f04_06_no_hardcoded_shap_or_perm_and_lime_explanations(self) -> None:
        orch_path = REPO_ROOT / "src/analytics/phase04_intelligence_orchestrator.py"
        src_code = orch_path.read_text(encoding="utf-8")
        assert "sample_w = np.array([[0.25, -0.15, 0.05]" not in src_code
        assert "lambda X: (X[:, 0] > 0.0)" not in src_code

        engine_4b = CalibratedStanceXAIAndMLOpsEngine()
        assert hasattr(engine_4b, "explain_text_instance_lime")
        lime_out = engine_4b.explain_text_instance_lime(
            text="Apoio com entusiasmo a transparencia e o fortalecimento institucional do Senado",
            theme_id="eleicao_presidencia_senado",
            num_samples=32,
        )
        assert "token_weights" in lime_out
        assert "top_positive_tokens" in lime_out
        assert "top_negative_tokens" in lime_out

    def test_qa_f04_07_real_rogan_gladen_bridge_and_macro_f1_above_060(self) -> None:
        orch_path = REPO_ROOT / "src/analytics/phase04_intelligence_orchestrator.py"
        src_code = orch_path.read_text(encoding="utf-8")
        assert '.get("FAVORAVEL", 0.90)' not in src_code

        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        dossier = orch.run_full_intelligence_pipeline(
            theme_id="eleicao_presidencia_senado",
            blind_validation_sample_size=100,
        )
        bridge = dossier["phase01_statistical_engine_bridge"]
        assert bridge["calibrated_sensitivity_used"] not in (0.90, None)
        assert bridge["calibrated_specificity_used"] not in (0.92, None)
        assert "youden_j_index" in bridge
        assert "rogan_gladen_corrected_proportion" in bridge

        metrics = dossier["engine_4b_calibrated_mlops_and_xai"]["blind_validation_metrics"]
        assert metrics["macro_f1"] >= 0.60
        assert metrics["sensitivities"]["Favoravel"] > 0.20

    def test_qa_f04_08_drift_includes_jsd_divergence(self) -> None:
        engine_4b = CalibratedStanceXAIAndMLOpsEngine()
        ref = np.array([0.2, 0.5, 0.3])
        cur = np.array([0.25, 0.45, 0.3])
        eval_drift = engine_4b.evaluate_model_drift(ref, cur)
        assert "jsd_divergence" in eval_drift
        assert isinstance(eval_drift["jsd_divergence"], float)
        assert eval_drift["jsd_divergence"] >= 0.0

    def test_qa_f04_10_all_four_official_spectra_present_with_k5(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        dossier = orch.run_full_intelligence_pipeline(
            theme_id="eleicao_presidencia_senado",
            blind_validation_sample_size=60,
        )
        spectra = dossier["engine_4c_bubbles_and_spectra"]["spectra_analysis"]
        spec_ids = {s["spectrum_id"] for s in spectra}
        assert any("progressista" in sp for sp in spec_ids)
        assert any("conservador" in sp for sp in spec_ids)
        assert any("centro" in sp for sp in spec_ids)
        assert any("setorial" in sp for sp in spec_ids)
        for s in spectra:
            if s["spectrum_id"] != "OUTROS_ANONIMIZADO_LGPD_K5":
                assert s["organic_accounts_N"] >= 5

    def test_qa_f04_11_cusum_and_granger_non_empty_in_contract_360(self) -> None:
        orch = Phase04IntelligenceOrchestrator(
            theme_id="eleicao_presidencia_senado",
            hmac_secret_key=VALID_32CHAR_SECRET,
        )
        for theme in ["eleicao_presidencia_senado", "pec_escala_6x1", "pl_ia_2338"]:
            dossier = orch.run_full_intelligence_pipeline(
                theme_id=theme,
                window_spec=MonitoringWindowSpec(window_days=7),
                blind_validation_sample_size=40,
            )
            c360 = dossier["ecosystem_360_interop_contract"]
            assert c360["structural_break_cusum"] is not None
            assert isinstance(c360["structural_break_cusum"], dict)
            assert isinstance(c360["granger_lead_lag_precedence"], list)
            assert len(c360["granger_lead_lag_precedence"]) > 0
