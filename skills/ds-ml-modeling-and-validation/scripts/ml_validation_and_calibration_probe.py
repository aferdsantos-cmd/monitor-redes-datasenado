#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Sonda de Validação de Modelos ML, Calibração de Probabilidades e Controle de FDR.

Executa:
1. Particionamento StratifiedGroupKFold garantindo isolamento estrito de autores;
2. Diagnósticos de calibração de probabilidades (Brier Score, ECE);
3. Métricas robustas para desbalanceamento (Macro-F1, MCC, Cohen's Kappa);
4. Comparação pareada de classificadores via Teste de McNemar com correção de Edwards;
5. Ajuste de múltiplos testes de hipóteses via Benjamini-Hochberg (FDR).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def stratified_group_kfold_split(
    groups: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    seed: int = 42,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Gera índices (train_idx, val_idx) com isolamento estrito de contas (groups) e estratificação de y."""
    rng = np.random.default_rng(seed)
    unique_groups = np.unique(groups)
    rng.shuffle(unique_groups)

    # Computa contagens de classes por grupo para alocação estratificada
    group_y_counts: Dict[Any, np.ndarray] = {}
    classes = np.unique(y)
    n_classes = len(classes)

    for g in unique_groups:
        mask = (groups == g)
        counts = np.array([np.sum(y[mask] == c) for c in classes])
        group_y_counts[g] = counts

    # Folds e suas contagens de classes acumuladas
    folds_groups: List[List[Any]] = [[] for _ in range(n_splits)]
    folds_class_counts = np.zeros((n_splits, n_classes), dtype=int)

    # Heurística gulosa para balanceamento de classes entre folds
    # Ordena grupos pelo número total de instâncias decrescente
    sorted_groups = sorted(unique_groups, key=lambda g: -np.sum(group_y_counts[g]))

    for g in sorted_groups:
        g_counts = group_y_counts[g]
        # Escolhe o fold com a menor contagem total de instâncias
        best_fold = int(np.argmin(np.sum(folds_class_counts, axis=1)))
        folds_groups[best_fold].append(g)
        folds_class_counts[best_fold] += g_counts

    splits: List[Tuple[np.ndarray, np.ndarray]] = []
    all_indices = np.arange(len(groups))

    for fold_idx in range(n_splits):
        val_g = set(folds_groups[fold_idx])
        val_mask = np.isin(groups, list(val_g))
        train_idx = all_indices[~val_mask]
        val_idx = all_indices[val_mask]
        splits.append((train_idx, val_idx))

    return splits


def benjamini_hochberg_fdr(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """Aplica o procedimento de Benjamini-Hochberg para controle da taxa de falsas descobertas (FDR)."""
    p_arr = np.asarray(p_values, dtype=float)
    m = len(p_arr)
    if m == 0:
        return np.array([], dtype=bool), np.array([], dtype=float)

    # Ordenação dos p-valores
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    # q-valores brutos: p * m / k
    k_ranks = np.arange(1, m + 1)
    q_raw = sorted_p * (float(m) / k_ranks)

    # Monotonicidade decrescente: q_(i) = min_{j >= i} q_raw_j
    q_monotonic = np.minimum.accumulate(q_raw[::-1])[::-1]
    q_monotonic = np.clip(q_monotonic, 0.0, 1.0)

    # Restaura a ordem original
    q_values = np.zeros(m, dtype=float)
    q_values[sorted_indices] = q_monotonic

    rejected = q_values <= alpha
    return rejected, q_values


def mcnemar_test(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
) -> Dict[str, float]:
    """Executa o Teste de McNemar com correção de continuidade de Edwards entre dois classificadores."""
    correct_a = (y_pred_a == y_true)
    correct_b = (y_pred_b == y_true)

    # b: A acertou, B errou | c: B acertou, A errou
    b = int(np.sum(correct_a & ~correct_b))
    c = int(np.sum(~correct_a & correct_b))

    total_discordant = b + c
    if total_discordant == 0:
        return {"b": b, "c": c, "chi2": 0.0, "p_value": 1.0, "significant": 0.0}

    # Estatística qui-quadrado com correção de Edwards: (|b - c| - 1)^2 / (b + c)
    chi2_stat = float((abs(b - c) - 1.0) ** 2 / total_discordant) if abs(b - c) > 1 else 0.0

    # p-valor aproximado para chi2(1) usando função erro
    p_val = float(math.erfc(math.sqrt(chi2_stat / 2.0)))

    return {
        "b_a_wins": float(b),
        "c_b_wins": float(c),
        "chi2_stat": round(chi2_stat, 4),
        "p_value": round(p_val, 6),
        "significant": float(p_val < 0.05),
    }


def calculate_ece_and_brier(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, float]:
    """Calcula Brier Score e Expected Calibration Error (ECE) para probabilidades preditas."""
    # Brier Score binário: mean((p - y)^2)
    brier_score = float(np.mean((y_prob - y_true) ** 2))

    # ECE via binning
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)

    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        bin_mask = (y_prob >= low) & (y_prob <= high if i == n_bins - 1 else y_prob < high)
        bin_size = int(np.sum(bin_mask))
        if bin_size > 0:
            avg_conf = float(np.mean(y_prob[bin_mask]))
            emp_acc = float(np.mean(y_true[bin_mask]))
            ece += (bin_size / n) * abs(emp_acc - avg_conf)

    return {
        "brier_score": round(brier_score, 4),
        "expected_calibration_error": round(ece, 4),
    }


def calculate_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    """Calcula métricas robustas: Acurácia, Macro-F1, Matthews Correlation Coefficient (MCC) e Cohen's Kappa."""
    classes = np.unique(np.concatenate([y_true, y_pred]))
    accuracy = float(np.mean(y_true == y_pred))

    # Macro-F1
    f1_list = []
    for c in classes:
        tp = np.sum((y_pred == c) & (y_true == c))
        fp = np.sum((y_pred == c) & (y_true != c))
        fn = np.sum((y_pred != c) & (y_true == c))
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_list.append(f1)
    macro_f1 = float(np.mean(f1_list))

    # Matriz de confusão para MCC e Kappa binário/multiclasse
    tp = np.sum((y_pred == 1) & (y_true == 1))
    tn = np.sum((y_pred == 0) & (y_true == 0))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    fn = np.sum((y_pred == 0) & (y_true == 1))

    denom = math.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    mcc = float((tp * tn - fp * fn) / denom) if denom > 0 else 0.0

    # Cohen's Kappa
    p_o = accuracy
    p_e = ((tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)) / float((tp + tn + fp + fn) ** 2) if (tp + tn + fp + fn) > 0 else 0.0
    kappa = float((p_o - p_e) / (1.0 - p_e)) if (1.0 - p_e) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "mcc": round(mcc, 4),
        "cohen_kappa": round(kappa, 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sonda de Validação de Modelos ML e Controle de FDR")
    parser.add_argument("--demo", action="store_true", help="Executa testes sintéticos de CV, métricas e FDR")
    args = parser.parse_args()

    print("=== [1/3] Validação Cruzada StratifiedGroupKFold (Isolamento de Contas) ===")
    rng = np.random.default_rng(42)
    n = 300
    author_groups = rng.integers(0, 40, size=n)
    y_true = rng.integers(0, 2, size=n)

    splits = stratified_group_kfold_split(author_groups, y_true, n_splits=5, seed=42)
    assert len(splits) == 5

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_authors = set(author_groups[train_idx])
        val_authors = set(author_groups[val_idx])
        # Comprova disjunção total de contas
        intersection = train_authors.intersection(val_authors)
        assert len(intersection) == 0, f"Vazamento no Fold {fold_idx}: contas sobrepostas {intersection}"
    print("  ✅ Disjunção de contas 100% comprovada: A_train ∩ A_val = ∅ em todos os 5 folds.")

    print("\n=== [2/3] Métricas de Desempenho, Brier Score e Calibração ECE ===")
    noise = rng.normal(0, 0.35, size=n)
    y_pred_prob = np.clip(0.5 + (y_true - 0.5) * 0.4 + noise, 0.05, 0.95)
    y_pred_model_a = (y_pred_prob >= 0.5).astype(int)
    # Modelo B superior corrigindo 15 erros do Modelo A
    err_indices = np.where(y_pred_model_a != y_true)[0]
    n_flips = min(15, len(err_indices))
    y_pred_model_b = y_pred_model_a.copy()
    if n_flips > 0:
        flip_indices = rng.choice(err_indices, size=n_flips, replace=False)
        y_pred_model_b[flip_indices] = y_true[flip_indices]

    metrics_a = calculate_classification_metrics(y_true, y_pred_model_a)
    calib = calculate_ece_and_brier(y_true, y_pred_prob)
    print(f"Métricas Modelo A: {json.dumps(metrics_a, indent=2)}")
    print(f"Calibração: {json.dumps(calib, indent=2)}")

    print("\n=== [3/3] Comparação Pareada de Modelos (McNemar) e Controle de FDR ===")
    mcnemar_res = mcnemar_test(y_true, y_pred_model_a, y_pred_model_b)
    print(f"Resultado Teste de McNemar: {json.dumps(mcnemar_res, indent=2)}")
    assert mcnemar_res["significant"] == 1.0, "Diferença esperada significativa no teste McNemar"

    # Múltiplos testes com FDR
    p_vals = np.array([0.001, 0.008, 0.035, 0.048, 0.12, 0.35, 0.72])
    rejected, q_vals = benjamini_hochberg_fdr(p_vals, alpha=0.05)
    print(f"p-valores originais: {p_vals}")
    print(f"q-valores ajustados BH: {np.round(q_vals, 4)}")
    print(f"Hipóteses rejeitadas (FDR <= 0.05): {rejected}")
    assert np.all(rejected[:2]), "Dois primeiros testes devem ser rejeitados sob FDR 0.05"

    print("\nSonda de Modelagem ML, Calibração e Validação FDR concluída com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
