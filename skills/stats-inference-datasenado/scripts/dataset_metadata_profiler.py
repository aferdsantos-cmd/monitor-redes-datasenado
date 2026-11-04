#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Extrator de Metadados Estatísticos e Diagnósticos de Amostragem (Zero Raw Data).

Calcula resumos executivos de momentos estatísticos (média, mediana, IQR, assimetria, curtose),
entropia normalizada de Shannon e célula mínima esperada (E_min) para testes chi-quadrado,
sem jamais expor dados brutos, identificadores individuais ou PII no contexto do prompt.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def _calculate_moments(values: np.ndarray) -> Dict[str, float]:
    """Calcula momentos estatísticos robustos e assimetria/curtose para vetor contínuo."""
    clean = values[~np.isnan(values)]
    n = len(clean)
    if n == 0:
        return {}

    mean_val = float(np.mean(clean))
    std_val = float(np.std(clean, ddof=1)) if n > 1 else 0.0
    median_val = float(np.median(clean))
    q25, q75 = float(np.percentile(clean, 25)), float(np.percentile(clean, 75))
    iqr_val = q75 - q25
    min_val, max_val = float(np.min(clean)), float(np.max(clean))

    # Skewness e Kurtosis amostrais (Fisher-Pearson)
    if n > 2 and std_val > 1e-12:
        diffs = (clean - mean_val) / std_val
        skewness = float(np.mean(diffs ** 3))
        kurtosis = float(np.mean(diffs ** 4) - 3.0)  # Excesso de curtose
    else:
        skewness = 0.0
        kurtosis = 0.0

    return {
        "mean": round(mean_val, 4),
        "sd": round(std_val, 4),
        "median": round(median_val, 4),
        "iqr": round(iqr_val, 4),
        "min": round(min_val, 4),
        "max": round(max_val, 4),
        "skewness": round(skewness, 4),
        "kurtosis": round(kurtosis, 4),
    }


def _shannon_entropy_normalized(counts: Dict[str, int]) -> float:
    """Calcula a entropia normalizada de Shannon H in [0, 1]."""
    total = sum(counts.values())
    k = len(counts)
    if total == 0 or k <= 1:
        return 0.0

    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            h -= p * math.log2(p)

    h_max = math.log2(k)
    return round(h / h_max, 4) if h_max > 0 else 0.0


def _evaluate_contingency_cochran(
    cat_a_vals: List[str], cat_b_vals: List[str]
) -> Tuple[float, float, str]:
    """Avalia o diagnóstico de Cochran para célula mínima esperada em tabela cruzada."""
    n = len(cat_a_vals)
    if n == 0:
        return 0.0, 0.0, "INSUFFICIENT_DATA"

    from collections import Counter
    a_counts = Counter(cat_a_vals)
    b_counts = Counter(cat_b_vals)

    min_expected = float("inf")
    cells_below_5 = 0
    total_cells = len(a_counts) * len(b_counts)

    if total_cells == 0:
        return 0.0, 0.0, "INSUFFICIENT_DATA"

    for r in a_counts.values():
        for c in b_counts.values():
            e_ij = (r * c) / n
            if e_ij < min_expected:
                min_expected = e_ij
            if e_ij < 5.0:
                cells_below_5 += 1

    pct_below_5 = round((cells_below_5 / total_cells) * 100, 2)
    min_exp_rounded = round(min_expected, 2)

    if pct_below_5 <= 20.0 and min_expected >= 1.0:
        status = "CHI2_ASSYMPTOTIC_VALID (E_min >= 1, < 20% < 5)"
    else:
        status = "COCHRAN_VIOLATION_USE_MONTE_CARLO (E_min < 5 em > 20% das celulas)"

    return min_exp_rounded, pct_below_5, status


def generate_demo_dataset() -> Dict[str, List[Any]]:
    """Gera micro-lote sintético determinístico em memória para profiling sem I/O de disco."""
    rng = np.random.default_rng(42)
    n = 50
    platforms = ["x_twitter", "instagram_facebook", "youtube", "telegram", "tiktok", "whatsapp"]
    stances = ["Favoravel", "Contrario", "Neutro"]
    regions = ["Sudeste", "Nordeste", "Sul", "Norte", "Centro-Oeste"]

    data = {
        "author_hash": [f"hash_{i:04d}" for i in range(n)],
        "platform": list(rng.choice(platforms, size=n, p=[0.3, 0.25, 0.2, 0.1, 0.1, 0.05])),
        "stance": list(rng.choice(stances, size=n, p=[0.5, 0.35, 0.15])),
        "macroregion": list(rng.choice(regions, size=n, p=[0.42, 0.27, 0.15, 0.08, 0.08])),
        "coordination_signal_index": list(np.clip(rng.beta(2, 8, size=n), 0, 1)),
        "sentiment_score": list(np.clip(rng.normal(0.1, 0.4, size=n), -1.0, 1.0)),
        "post_count": list(rng.poisson(3.5, size=n) + 1),
    }
    return data


def profile_dataset_dict(data: Dict[str, List[Any]], dataset_name: str) -> Dict[str, Any]:
    """Produz resumo executivo de metadados sem vazar nenhuma linha de dados brutos."""
    n_rows = len(next(iter(data.values()))) if data else 0
    n_cols = len(data)

    variable_summaries: Dict[str, Any] = {}
    cat_columns = []

    for col_name, raw_vals in data.items():
        n_nulls = sum(1 for v in raw_vals if v is None)
        pct_nulls = round((n_nulls / n_rows) * 100, 2) if n_rows > 0 else 0.0

        sample_val = next((v for v in raw_vals if v is not None), None)

        if isinstance(sample_val, (int, float, np.integer, np.floating)) and not isinstance(sample_val, bool):
            arr = np.array([v if v is not None else np.nan for v in raw_vals], dtype=float)
            moments = _calculate_moments(arr)
            variable_summaries[col_name] = {
                "type": "continuous" if isinstance(sample_val, (float, np.floating)) else "discrete_integer",
                "null_count": n_nulls,
                "null_pct": pct_nulls,
                "moments": moments,
            }
        elif "hash" in col_name.lower() or "id" in col_name.lower():
            unique_count = len(set(raw_vals))
            variable_summaries[col_name] = {
                "type": "hash_identifier",
                "null_count": n_nulls,
                "null_pct": pct_nulls,
                "unique_keys": unique_count,
                "uniqueness_ratio": round(unique_count / n_rows, 4) if n_rows > 0 else 0.0,
            }
        else:
            cat_columns.append(col_name)
            from collections import Counter
            counts = Counter(str(v) for v in raw_vals if v is not None)
            total_valid = sum(counts.values())
            top_cats = {
                k: round((c / total_valid) * 100, 2)
                for k, c in counts.most_common(5)
            } if total_valid > 0 else {}

            entropy = _shannon_entropy_normalized(counts)
            variable_summaries[col_name] = {
                "type": "categorical",
                "null_count": n_nulls,
                "null_pct": pct_nulls,
                "cardinality": len(counts),
                "top_proportions_pct": top_cats,
                "shannon_entropy": entropy,
            }

    # Diagnóstico de Contingência (Cross-Tab Cochran)
    contingency_diagnostic = {}
    if len(cat_columns) >= 2:
        col_a, col_b = cat_columns[0], cat_columns[1]
        e_min, pct_low, status = _evaluate_contingency_cochran(
            [str(v) for v in data[col_a]], [str(v) for v in data[col_b]]
        )
        contingency_diagnostic = {
            "cross_table": f"{col_a} x {col_b}",
            "min_expected_cell": e_min,
            "pct_cells_below_5": pct_low,
            "sampling_diagnostic": status,
        }

    return {
        "dataset_name": dataset_name,
        "n_records": n_rows,
        "n_variables": n_cols,
        "variables": variable_summaries,
        "contingency_diagnostics": contingency_diagnostic,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrator de Metadados Estatísticos (Zero Raw Data)")
    parser.add_argument("--input", type=Path, help="Caminho para arquivo Parquet, JSON ou CSV")
    parser.add_argument("--demo", action="store_true", help="Gera micro-dataset sintético em memória para validação imediata")
    args = parser.parse_args()

    if args.demo or not args.input:
        data = generate_demo_dataset()
        dataset_name = "demo_synthetic_sample_n50"
    else:
        target_path = args.input.resolve()
        if not target_path.exists():
            print(f"[ERRO] Arquivo não encontrado: {target_path}", file=sys.stderr)
            return 1
        dataset_name = target_path.name
        if target_path.suffix == ".parquet":
            import duckdb
            with duckdb.connect() as con:
                df = con.execute(f"SELECT * FROM '{target_path}'").df()
                data = {col: df[col].tolist() for col in df.columns}
        elif target_path.suffix == ".json":
            with open(target_path, "r", encoding="utf-8") as f:
                raw_json = json.load(f)
                if isinstance(raw_json, list) and raw_json:
                    cols = list(raw_json[0].keys())
                    data = {c: [row.get(c) for row in raw_json] for c in cols}
                else:
                    data = {}
        else:
            print(f"[ERRO] Formato de arquivo não suportado: {target_path.suffix}", file=sys.stderr)
            return 1

    profile = profile_dataset_dict(data, dataset_name)
    print("=== Perfil Executivo de Metadados Estatísticos (Zero Raw Data) ===")
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    print("\n✅ Metadados extraídos com sucesso. Nenhum dado individual bruto foi exposto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
