#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Auditor de Vazamento de Features (Anti-Leakage) e Diagnóstico de Colinearidade (VIF).

Valida conformidade do pipeline de engenharia de atributos:
1. Detecta vazamento pré-split ou correlações espúrias com o alvo (look-ahead leakage);
2. Calcula o Fator de Inflação da Variância (VIF) para identificar multicolinearidade;
3. Executa Out-of-Fold (OOF) Target Encoding com suavização Empirical Bayes e isolamento de contas;
4. Calcula o Índice de Burstiness de Goh-Barabási para fluxos temporais de postagens.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def compute_burstiness(inter_arrival_times: np.ndarray) -> float:
    """Calcula o Índice de Burstiness de Goh-Barabási B = (sigma - mu) / (sigma + mu)."""
    clean = inter_arrival_times[~np.isnan(inter_arrival_times)]
    if len(clean) < 2:
        return 0.0
    mu = float(np.mean(clean))
    sigma = float(np.std(clean, ddof=1))
    if (sigma + mu) < 1e-12:
        return 0.0
    b = (sigma - mu) / (sigma + mu)
    return float(np.clip(b, -1.0, 1.0))


def audit_feature_leakage(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    threshold: float = 0.85,
) -> List[str]:
    """Identifica atributos com correlação excessiva ou suspeita com a variável alvo."""
    leaked_features: List[str] = []
    y_centered = y - np.mean(y)
    y_std = np.std(y)

    if y_std < 1e-12:
        return leaked_features

    for j, name in enumerate(feature_names):
        col = X[:, j]
        col_std = np.std(col)
        if col_std < 1e-12:
            continue
        corr = float(np.abs(np.mean((col - np.mean(col)) * y_centered) / (col_std * y_std)))
        if corr >= threshold:
            leaked_features.append(name)

    return leaked_features


def compute_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """Calcula o Fator de Inflação da Variância (VIF = 1 / (1 - R^2)) via OLS matricial."""
    n_samples, n_features = X.shape
    vif_dict: Dict[str, float] = {}

    if n_features < 2 or n_samples <= n_features:
        return {name: 1.0 for name in feature_names}

    # Centraliza e padroniza X
    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0)
    X_std[X_std < 1e-12] = 1.0
    X_norm = (X - X_mean) / X_std

    for i in range(n_features):
        y_i = X_norm[:, i]
        mask = np.ones(n_features, dtype=bool)
        mask[i] = False
        X_other = X_norm[:, mask]

        # Adiciona intercepto
        A = np.column_stack([np.ones(n_samples), X_other])
        # OLS via mínimos quadrados lineares
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(A, y_i, rcond=None)
            pred = A @ coeffs
            ss_tot = np.sum((y_i - np.mean(y_i)) ** 2)
            ss_res = np.sum((y_i - pred) ** 2)
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
            r_squared = np.clip(r_squared, 0.0, 0.999999)
            vif_val = 1.0 / (1.0 - r_squared)
        except np.linalg.LinAlgError:
            vif_val = float("inf")

        vif_dict[feature_names[i]] = round(float(vif_val), 2)

    return vif_dict


def empirical_bayes_oof_target_encode(
    groups: np.ndarray,
    categories: np.ndarray,
    y: np.ndarray,
    m_smoothing: float = 10.0,
    n_splits: int = 5,
    seed: int = 42,
) -> np.ndarray:
    """Calcula Out-of-Fold Target Encoding com Bayes empírico agrupado por autor."""
    rng = np.random.default_rng(seed)
    unique_groups = np.unique(groups)
    rng.shuffle(unique_groups)

    group_folds = np.array_split(unique_groups, n_splits)
    encoded = np.zeros(len(y), dtype=float)
    global_prior = float(np.mean(y))

    for fold_idx, val_groups in enumerate(group_folds):
        val_mask = np.isin(groups, val_groups)
        train_mask = ~val_mask

        # Estatísticas do treino
        train_cats = categories[train_mask]
        train_y = y[train_mask]
        train_prior = float(np.mean(train_y)) if len(train_y) > 0 else global_prior

        cat_stats: Dict[Any, Tuple[float, int]] = {}
        for c in np.unique(train_cats):
            c_mask = (train_cats == c)
            cat_stats[c] = (float(np.mean(train_y[c_mask])), int(np.sum(c_mask)))

        # Codifica o fold de validação
        val_cats = categories[val_mask]
        fold_encoded = np.zeros(len(val_cats), dtype=float)
        for i, c in enumerate(val_cats):
            if c in cat_stats:
                mean_c, n_c = cat_stats[c]
                lambda_c = n_c / (n_c + m_smoothing)
                fold_encoded[i] = lambda_c * mean_c + (1.0 - lambda_c) * train_prior
            else:
                fold_encoded[i] = train_prior

        encoded[val_mask] = fold_encoded

    return encoded


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditor de Feature Leakage e Colinearidade")
    parser.add_argument("--demo", action="store_true", help="Executa auditoria sintética com detecção de vazamento e VIF")
    args = parser.parse_args()

    print("=== [1/3] Auditoria de Vazamento de Variáveis (Anti-Leakage) ===")
    rng = np.random.default_rng(42)
    n = 200

    y = rng.integers(0, 2, size=n)
    causal_feature = y * 0.4 + rng.normal(0, 1, size=n)
    leaked_feature = y * 0.99 + rng.normal(0, 0.05, size=n)  # Look-ahead leakage
    collinear_a = rng.normal(0, 1, size=n)
    collinear_b = collinear_a * 0.98 + rng.normal(0, 0.05, size=n)  # VIF alto

    X = np.column_stack([causal_feature, leaked_feature, collinear_a, collinear_b])
    names = ["causal_eng_lag1", "future_leak_post_reaction", "collinear_metric_a", "collinear_metric_b"]

    leaks = audit_feature_leakage(X, y, names, threshold=0.85)
    print(f"Features analisadas: {names}")
    print(f"Features com vazamento detectadas: {leaks}")
    assert "future_leak_post_reaction" in leaks, "A feature de vazamento não foi flagrada!"
    print("  ✅ Feature com look-ahead leakage detectada com sucesso.")

    print("\n=== [2/3] Diagnóstico de Colinearidade (VIF) ===")
    vifs = compute_vif(X, names)
    print(f"Resultados VIF: {json.dumps(vifs, indent=2)}")
    assert vifs["collinear_metric_a"] > 10.0 or vifs["collinear_metric_b"] > 10.0, "VIF alto não detectado!"
    print("  ✅ Colinearidade severa (VIF > 10) identificada corretamente.")

    print("\n=== [3/3] Out-of-Fold Target Encoding e Burstiness ===")
    authors = rng.integers(0, 25, size=n)
    topics = rng.choice(["saude", "economia", "educacao", "seguranca"], size=n)
    oof_encoded = empirical_bayes_oof_target_encode(authors, topics, y, m_smoothing=10.0)

    # Verifica integridade do OOF
    assert len(oof_encoded) == n
    assert not np.isnan(oof_encoded).any()
    print("  ✅ Out-of-Fold Target Encoding computado sem vazamento.")

    # Teste de Burstiness de Goh-Barabási
    intervals_periodic = np.ones(50) * 10.0  # Bot periódico
    intervals_bursty = rng.exponential(scale=5.0, size=50)  # Engajamento humano
    b_bot = compute_burstiness(intervals_periodic)
    b_human = compute_burstiness(intervals_bursty)
    print(f"Burstiness Bot (periódico): {b_bot:.2f} | Burstiness Orgânico: {b_human:.2f}")
    assert b_bot < -0.8, "Bot periódico deveria apresentar B próximo de -1"

    print("\nAuditoria de Feature Engineering e Anti-Leakage concluída com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
