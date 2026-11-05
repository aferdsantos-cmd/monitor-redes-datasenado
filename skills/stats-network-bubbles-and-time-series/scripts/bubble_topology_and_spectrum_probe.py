#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Sonda de Topologia de Bolhas Digitais, Espectros Políticos e Séries Temporais (ADR-008/ADR-010).

Executa:
1. Modularidade de Newman (Q) com teste de hipótese contra modelo nulo;
2. Índice de Homofilia / Isolamento E-I de Krackhardt & Stern para câmaras de eco;
3. Coeficiente de Participação (P_i) para detecção de pontes discursivas;
4. Propagação Harmônica de Rótulos em Grafos a partir de Expoentes-Semente (ADR-010);
5. Teste F de Causalidade de Granger bivariada para identificação de First-Mover Spectrum (ADR-008).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def compute_newman_modularity(adj_matrix: np.ndarray, communities: np.ndarray) -> float:
    """Calcula a Modularidade de Newman Q para uma partição comunitária."""
    A = np.asarray(adj_matrix, dtype=float)
    m = float(np.sum(A) / 2.0)
    if m < 1e-12:
        return 0.0

    k = np.sum(A, axis=1)
    n = len(communities)
    q = 0.0

    # Vetorizado por comunidade
    for c in np.unique(communities):
        mask = (communities == c)
        A_c = np.sum(A[np.ix_(mask, mask)])
        k_c = np.sum(k[mask])
        q += (A_c / (2.0 * m)) - ((k_c / (2.0 * m)) ** 2)

    return float(q)


def permutation_test_modularity_null(
    adj_matrix: np.ndarray,
    communities: np.ndarray,
    n_permutations: int = 50,
    seed: int = 42,
) -> Dict[str, float]:
    """Testa a significância estatística de Q contra um modelo nulo por permutação de rótulos comunitários."""
    rng = np.random.default_rng(seed)
    q_obs = compute_newman_modularity(adj_matrix, communities)

    null_qs = []
    shuffled_comm = communities.copy()
    for _ in range(n_permutations):
        rng.shuffle(shuffled_comm)
        q_null = compute_newman_modularity(adj_matrix, shuffled_comm)
        null_qs.append(q_null)

    null_arr = np.array(null_qs)
    mu_null = float(np.mean(null_arr))
    sigma_null = float(np.std(null_arr, ddof=1)) if len(null_arr) > 1 else 1e-6
    z_score = float((q_obs - mu_null) / sigma_null) if sigma_null > 1e-12 else 0.0
    p_value = float(np.mean(null_arr >= q_obs))

    return {
        "q_observed": round(q_obs, 4),
        "q_null_mean": round(mu_null, 4),
        "q_null_std": round(sigma_null, 4),
        "z_score": round(z_score, 2),
        "p_value": round(p_value, 4),
    }


def compute_krackhardt_ei_index(adj_matrix: np.ndarray, communities: np.ndarray) -> Dict[int, float]:
    """Calcula o Índice E-I de Krackhardt & Stern para cada comunidade: (E - I) / (E + I)."""
    A = np.asarray(adj_matrix, dtype=float)
    unique_comms = np.unique(communities)
    ei_indices: Dict[int, float] = {}

    for c in unique_comms:
        mask = (communities == c)
        internal = float(np.sum(A[np.ix_(mask, mask)]))
        external = float(np.sum(A[np.ix_(mask, ~mask)]))
        total = internal + external
        if total < 1e-12:
            ei_val = 0.0
        else:
            ei_val = (external - internal) / total
        ei_indices[int(c)] = round(float(ei_val), 4)

    return ei_indices


def compute_participation_coefficient(adj_matrix: np.ndarray, communities: np.ndarray) -> np.ndarray:
    """Calcula o Coeficiente de Participação P_i = 1 - sum((k_is / k_i)^2) para nós-ponte."""
    A = np.asarray(adj_matrix, dtype=float)
    k_total = np.sum(A, axis=1)
    unique_comms = np.unique(communities)
    n = len(communities)
    p_i = np.zeros(n, dtype=float)

    for i in range(n):
        if k_total[i] < 1e-12:
            p_i[i] = 0.0
            continue
        sum_sq = 0.0
        for c in unique_comms:
            k_ic = float(np.sum(A[i, communities == c]))
            sum_sq += (k_ic / k_total[i]) ** 2
        p_i[i] = float(np.clip(1.0 - sum_sq, 0.0, 1.0))

    return p_i


def harmonic_seed_label_propagation(
    adj_matrix: np.ndarray,
    seed_indices: List[int],
    seed_labels: List[int],
    n_classes: int,
    alpha: float = 0.85,
    max_iter: int = 30,
) -> np.ndarray:
    """Executa a propagação harmônica semi-supervisionada de afinidade espectral a partir de expoentes-semente."""
    W = np.asarray(adj_matrix, dtype=float)
    n = W.shape[0]

    # Constrói o Laplaciano normalizado S = D^(-1/2) W D^(-1/2)
    degrees = np.sum(W, axis=1)
    inv_sqrt_d = np.zeros(n, dtype=float)
    nonzero = degrees > 1e-12
    inv_sqrt_d[nonzero] = 1.0 / np.sqrt(degrees[nonzero])
    D_mat = np.diag(inv_sqrt_d)
    S = D_mat @ W @ D_mat

    # Matriz inicial de rótulos Y
    Y = np.zeros((n, n_classes), dtype=float)
    for idx, lbl in zip(seed_indices, seed_labels):
        Y[idx, lbl] = 1.0

    F = Y.copy()
    for _ in range(max_iter):
        F_next = alpha * (S @ F) + (1.0 - alpha) * Y
        if np.max(np.abs(F_next - F)) < 1e-5:
            F = F_next
            break
        F = F_next

    # Normalização no simplex por linha
    row_sums = np.sum(F, axis=1, keepdims=True)
    row_sums[row_sums < 1e-12] = 1.0
    F_normalized = F / row_sums
    return F_normalized


def granger_causality_bivariate(
    x_series: np.ndarray,
    y_series: np.ndarray,
    max_lag: int = 2,
) -> Dict[str, float]:
    """Testa se x causa Y no sentido de Granger (modelo autorregressivo irrestrito vs restrito)."""
    x = np.asarray(x_series, dtype=float)
    y = np.asarray(y_series, dtype=float)
    T = len(y)
    if T <= 2 * max_lag + 2:
        return {"f_stat": 0.0, "p_value": 1.0, "is_first_mover": 0.0}

    # Constrói matriz de defasagens
    Y_target = y[max_lag:]
    n_samples = len(Y_target)

    # Modelo restrito: apenas defasagens de y
    X_restricted_cols = [np.ones(n_samples)]
    for lag in range(1, max_lag + 1):
        X_restricted_cols.append(y[max_lag - lag : T - lag])
    X_restr = np.column_stack(X_restricted_cols)

    # Modelo irrestrito: defasagens de y e defasagens de x
    X_unrestricted_cols = list(X_restricted_cols)
    for lag in range(1, max_lag + 1):
        X_unrestricted_cols.append(x[max_lag - lag : T - lag])
    X_unrestr = np.column_stack(X_unrestricted_cols)

    # OLS restrito
    b_restr, res_restr, _, _ = np.linalg.lstsq(X_restr, Y_target, rcond=None)
    ssr_restr = float(np.sum((Y_target - X_restr @ b_restr) ** 2))

    # OLS irrestrito
    b_unrestr, res_unrestr, _, _ = np.linalg.lstsq(X_unrestr, Y_target, rcond=None)
    ssr_unrestr = float(np.sum((Y_target - X_unrestr @ b_unrestr) ** 2))

    df_num = max_lag
    df_denom = n_samples - (2 * max_lag + 1)
    if ss_diff := max(0.0, ssr_restr - ssr_unrestr):
        f_stat = float((ss_diff / df_num) / (max(ssr_unrestr, 1e-12) / df_denom))
    else:
        f_stat = 0.0

    # p-valor aproximado
    p_value = float(1.0 / (1.0 + f_stat)) if f_stat > 0 else 1.0

    return {
        "f_stat": round(f_stat, 4),
        "p_value": round(p_value, 4),
        "is_first_mover": float(p_value < 0.05),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sonda de Topologia de Bolhas e Espectros (ADR-010)")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração com grafo sintético polarizado")
    args = parser.parse_args()

    print("=== [1/3] Grafo Polarizado: Modularidade Q e Teste de Modelo Nulo ===")
    rng = np.random.default_rng(42)
    # Grafo com 2 bolhas densas de 20 nós cada + 2 nós-ponte centrais (total 42 nós)
    n_nodes = 42
    A = np.zeros((n_nodes, n_nodes), dtype=float)

    # Bolha 0 (nós 0 a 19): densa internamente
    for i in range(20):
        for j in range(i + 1, 20):
            if rng.random() < 0.40:
                A[i, j] = A[j, i] = 1.0

    # Bolha 1 (nós 20 a 39): densa internamente
    for i in range(20, 40):
        for j in range(i + 1, 40):
            if rng.random() < 0.40:
                A[i, j] = A[j, i] = 1.0

    # Nós pontes (40 e 41) conectam ambas as bolhas
    for bridge in (40, 41):
        for b0_node in rng.choice(20, size=5, replace=False):
            A[bridge, b0_node] = A[b0_node, bridge] = 1.0
        for b1_node in rng.choice(range(20, 40), size=5, replace=False):
            A[bridge, b1_node] = A[b1_node, bridge] = 1.0

    # Partição de comunidades (bolha 0, bolha 1, pontes na comunidade mista)
    communities = np.zeros(n_nodes, dtype=int)
    communities[20:40] = 1
    communities[40:] = 2

    q_test = permutation_test_modularity_null(A, communities, n_permutations=40, seed=42)
    print(f"Resultados de Modularidade: {json.dumps(q_test, indent=2)}")
    assert q_test["q_observed"] > 0.30, "Modularidade de rede polarizada deve ser expressiva (Q > 0.30)"
    assert q_test["z_score"] > 3.0, "Estrutura comunitária deve ser significante contra modelo nulo"
    print("  ✅ Modularidade Q significante comprovada.")

    print("\n=== [2/3] Índice E-I de Câmaras de Eco e Coeficiente de Participação P_i ===")
    ei_indices = compute_krackhardt_ei_index(A, communities)
    p_coefficients = compute_participation_coefficient(A, communities)
    print(f"Índices E-I por Comunidade: {json.dumps(ei_indices, indent=2)}")
    print(f"P_i Nós-Ponte (40 e 41): {p_coefficients[40]:.3f}, {p_coefficients[41]:.3f}")
    assert ei_indices[0] < -0.30 and ei_indices[1] < -0.30, "Comunidades devem caracterizar câmaras de eco"
    assert p_coefficients[40] > 0.40, "Nó 40 deve atuar como ponte inter-bolhas"
    print("  ✅ Câmaras de eco e nós-ponte quantificados com sucesso.")

    print("\n=== [3/3] Propagação Harmônica de Espectros e Causalidade de Granger ===")
    # Expoentes-semente públicos: nó 0 = Progressista (0), nó 20 = Conservador (1)
    seed_idx = [0, 20]
    seed_lbl = [0, 1]
    affinity_matrix = harmonic_seed_label_propagation(A, seed_idx, seed_lbl, n_classes=2)
    print(f"Afinidade nó 0 (semente): {affinity_matrix[0]}")
    print(f"Afinidade nó 20 (semente): {affinity_matrix[20]}")
    print(f"Afinidade nó 40 (ponte): {affinity_matrix[40]}")
    assert affinity_matrix[0, 0] > 0.90 and affinity_matrix[20, 1] > 0.90
    print("  ✅ Propagação harmônica convergiu consistentemente.")

    # Causalidade de Granger bivariada (Série A antecede Série B por 1 lag)
    t_len = 60
    series_a = np.cumsum(rng.normal(0, 1, size=t_len))
    series_b = np.zeros(t_len)
    series_b[1:] = 0.7 * series_a[:-1] + rng.normal(0, 0.3, size=t_len - 1)

    granger_res = granger_causality_bivariate(series_a, series_b, max_lag=1)
    print(f"Teste de Granger (A -> B): {json.dumps(granger_res, indent=2)}")
    assert granger_res["is_first_mover"] == 1.0, "Série A deve ser identificada como First-Mover"

    print("\nSonda de Topologia de Bolhas Digitais e Espectros (ADR-010) concluída com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
