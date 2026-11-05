#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Validador de MLOps de Deriva (PSI / JSD / KS) e Integridade de Model Cards.

Executa:
1. Cálculo do Population Stability Index (PSI) com semáforo (Verde, Amarelo, Vermelho);
2. Divergência de Jensen-Shannon (JSD) e Teste Kolmogorov-Smirnov (KS);
3. Validação estrutural de Model Cards JSON/MD sem dependência de pickle;
4. Trava de segurança para ponto de ruptura de Youden em Rogan-Gladen.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-6,
) -> float:
    """Calcula o Population Stability Index (PSI) entre a distribuição esperada e a observada."""
    exp_clean = expected[~np.isnan(expected)]
    act_clean = actual[~np.isnan(actual)]

    if len(exp_clean) == 0 or len(act_clean) == 0:
        return 0.0

    # Bins baseados nos decis da distribuição de referência (expected)
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(exp_clean, percentiles)
    # Garante que os limites sejam estritamente crescentes
    bin_edges[0] -= 1e-6
    bin_edges[-1] += 1e-6
    for i in range(1, len(bin_edges)):
        if bin_edges[i] <= bin_edges[i - 1]:
            bin_edges[i] = bin_edges[i - 1] + 1e-5

    # Contagens por bin
    exp_counts, _ = np.histogram(exp_clean, bins=bin_edges)
    act_counts, _ = np.histogram(act_clean, bins=bin_edges)

    exp_pct = exp_counts / float(len(exp_clean))
    act_pct = act_counts / float(len(act_clean))

    # Evita divisão por zero com epsilon
    exp_pct = np.clip(exp_pct, epsilon, 1.0)
    act_pct = np.clip(act_pct, epsilon, 1.0)

    psi_val = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(np.maximum(0.0, psi_val))


def calculate_jensen_shannon_divergence(p: np.ndarray, q: np.ndarray) -> float:
    """Calcula a Divergência de Jensen-Shannon (JSD) entre duas distribuições categóricas."""
    p_norm = np.asarray(p, dtype=float)
    q_norm = np.asarray(q, dtype=float)

    p_norm = p_norm / np.sum(p_norm)
    q_norm = q_norm / np.sum(q_norm)

    m = 0.5 * (p_norm + q_norm)

    # KL(P || M) e KL(Q || M)
    def kl_divergence(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))

    jsd = 0.5 * kl_divergence(p_norm, m) + 0.5 * kl_divergence(q_norm, m)
    return float(np.clip(jsd, 0.0, math.log(2.0)))


def calculate_ks_drift(
    reference_sample: np.ndarray,
    current_sample: np.ndarray,
) -> Dict[str, float]:
    """Calcula a estatística Kolmogorov-Smirnov (KS) de descolamento contínuo."""
    ref = np.sort(reference_sample[~np.isnan(reference_sample)])
    curr = np.sort(current_sample[~np.isnan(current_sample)])

    n_ref = len(ref)
    n_curr = len(curr)

    if n_ref == 0 or n_curr == 0:
        return {"ks_statistic": 0.0, "p_value_approx": 1.0, "drift_detected": 0.0}

    all_vals = np.concatenate([ref, curr])
    cdf_ref = np.searchsorted(ref, all_vals, side="right") / n_ref
    cdf_curr = np.searchsorted(curr, all_vals, side="right") / n_curr

    d_stat = float(np.max(np.abs(cdf_ref - cdf_curr)))

    # Aproximação assintótica de Smirnov
    en = math.sqrt((n_ref * n_curr) / (n_ref + n_curr))
    lambda_val = (en + 0.12 + 0.11 / en) * d_stat
    # p-valor Kolmogorov
    p_val = 2.0 * math.exp(-2.0 * (lambda_val ** 2)) if lambda_val > 0 else 1.0
    p_val = float(np.clip(p_val, 0.0, 1.0))

    return {
        "ks_statistic": round(d_stat, 4),
        "p_value_approx": round(p_val, 6),
        "drift_detected": float(p_val < 0.01 and d_stat > 0.10),
    }


def validate_model_card_json(card_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida se o Model Card contém os campos canônicos obrigatórios e rejeita uso de pickle."""
    errors: List[str] = []

    required_keys = [
        "model_id",
        "task",
        "architecture",
        "code_commit_sha",
        "training_data",
        "validation_metrics_oof",
        "rogan_gladen_matrix",
    ]
    for k in required_keys:
        if k not in card_dict:
            errors.append(f"Chave obrigatória ausente: '{k}'")

    # Scanner contra referências a pickle
    card_str = json.dumps(card_dict)
    if "pickle" in card_str.lower() or ".pkl" in card_str.lower():
        errors.append("Violação SAST / Segurança: Menção a serialização 'pickle' ou '.pkl' detectada no Model Card!")

    is_valid = len(errors) == 0
    return is_valid, errors


def check_rogan_gladen_youden_breakdown(se: float, sp: float) -> Tuple[bool, float]:
    """Verifica se o Índice de Youden satisfaz J = Se + Sp - 1 > 0.20."""
    j_index = float(se + sp - 1.0)
    is_valid = j_index > 0.20
    return is_valid, round(j_index, 4)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador MLOps de Drift e Model Card")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração com drift estável, crítico e Model Card")
    args = parser.parse_args()

    print("=== [1/3] Monitoramento de Data Drift via Population Stability Index (PSI) ===")
    rng = np.random.default_rng(42)
    ref_data = rng.normal(loc=0.0, scale=1.0, size=1000)

    # Cenário 1: Estável (PSI < 0.10)
    stable_data = rng.normal(loc=0.02, scale=1.02, size=1000)
    psi_stable = calculate_psi(ref_data, stable_data)
    print(f"Cenário 1 (Estável) -> PSI: {psi_stable:.4f}")
    assert psi_stable < 0.10, f"Esperado PSI < 0.10 no cenário estável, obtido {psi_stable}"
    print("  ✅ Semáforo Verde confirmado (PSI < 0.10).")

    # Cenário 2: Deriva Crítica (PSI >= 0.25)
    drifted_data = rng.normal(loc=0.9, scale=1.4, size=1000)
    psi_drifted = calculate_psi(ref_data, drifted_data)
    print(f"Cenário 2 (Deriva Crítica) -> PSI: {psi_drifted:.4f}")
    assert psi_drifted >= 0.25, f"Esperado PSI >= 0.25 no cenário com drift, obtido {psi_drifted}"
    print("  ✅ Semáforo Vermelho confirmado (PSI >= 0.25: aciona recalibração).")

    print("\n=== [2/3] Divergência de Jensen-Shannon (JSD) e Teste KS ===")
    p_dist = np.array([0.4, 0.3, 0.2, 0.1])
    q_dist = np.array([0.1, 0.2, 0.3, 0.4])
    jsd_val = calculate_jensen_shannon_divergence(p_dist, q_dist)
    print(f"JSD entre distribuições de tópicos: {jsd_val:.4f}")
    assert jsd_val > 0.10

    ks_res = calculate_ks_drift(ref_data, drifted_data)
    print(f"Diagnóstico KS: {json.dumps(ks_res, indent=2)}")
    assert ks_res["drift_detected"] == 1.0
    print("  ✅ Teste Kolmogorov-Smirnov detectou o descolamento distributivo com sucesso.")

    print("\n=== [3/3] Validação Estrutural de Model Card e Trava de Youden ===")
    valid_card = {
        "model_id": "datasenado-stance-linear-v1.0",
        "task": "legislative_opinion_stance_classification",
        "architecture": "regularized_logistic_with_platt_scaling",
        "code_commit_sha": "7af3548b",
        "training_data": {"dataset_fingerprint_sha256": "abc12345", "n_samples": 4200},
        "validation_metrics_oof": {"macro_f1": 0.84, "mcc": 0.68},
        "rogan_gladen_matrix": {"sensitivity": 0.85, "specificity": 0.90},
    }
    is_valid, errs = validate_model_card_json(valid_card)
    assert is_valid, f"Model Card válido foi reprovado: {errs}"
    print("  ✅ Model Card JSON validado com sucesso (100% de conformidade, zero pickle).")

    # Testa rejeição a pickle
    bad_card = valid_card.copy()
    bad_card["serialization"] = "pickle.dump(model, open('m.pkl', 'wb'))"
    is_bad_valid, bad_errs = validate_model_card_json(bad_card)
    assert not is_bad_valid, "Model Card com pickle deveria ser rejeitado!"
    print("  ✅ Validador bloqueou tentativa de uso de serialização pickle.")

    # Trava de Youden
    youden_ok, j_val = check_rogan_gladen_youden_breakdown(se=0.85, sp=0.90)
    print(f"Índice de Youden J: {j_val} (Válido: {youden_ok})")
    assert youden_ok and j_val > 0.20

    print("\nValidador MLOps de Drift (PSI/JSD) e Model Card concluído com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
