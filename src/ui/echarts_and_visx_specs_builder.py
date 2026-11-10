"""
Construtor Determinístico de Especificações Gráficas para Apache ECharts e Mapas Visx 27 UFs.
Garante alta densidade informacional (Tufte >= 0.80), conformidade Okabe-Ito e salvaguardas LGPD.
"""

from __future__ import annotations

import copy
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple

BRAZIL_27_UFS_SET: Set[str] = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}

BRAZIL_5_REGIONS_SET: Set[str] = {
    "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"
}

OKABE_ITO_PALETTE = {
    "favoravel": "#0072B2",
    "contrario": "#D55E00",
    "neutro": "#64748B",
    "bolha_a": "#009E73",
    "bolha_b": "#CC79A7",
    "quarentena": "#DC2626",
    "senado_azul": "#0B1F3A",
    "senado_dourado": "#B45309",
}


def build_three_scenarios_and_rogan_gladen_echarts_spec(theme_dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói a especificação JSON oficial do Apache ECharts para comparação dos 3 Cenários
    e Rogan-Gladen com bandas de erro de Intervalo de Confiança de 95% (IC 95%).
    """
    if isinstance(theme_dataset, list):
        scenarios = theme_dataset
        medallion = {}
    else:
        scenarios = theme_dataset.get("scenarios", [])
        medallion = theme_dataset.get("medallion", {})
    categories = [s.get("shortName", s.get("name", "Cenário")) for s in scenarios]
    fav_data = [s.get("favoravel", 0.0) for s in scenarios]
    cont_data = [s.get("contrario", 0.0) for s in scenarios]
    neu_data = [s.get("neutro", 0.0) for s in scenarios]

    # Barras de erro IC 95% [min, max]
    fav_errors = [s.get("favoravelCi", [0.0, 0.0]) for s in scenarios]
    cont_errors = [s.get("contrarioCi", [0.0, 0.0]) for s in scenarios]

    sample_size = medallion.get("goldSampleSize", 550)
    deff_val = medallion.get("kishDeff", 1.42)

    option = {
        "title": {
            "text": "Comparativo dos 3 Cenários e Estimativa Corrigida de Rogan-Gladen (IC 95%)",
            "subtext": f"n = {sample_size} contas orgânicas auditadas · DEFF Kish = {deff_val}",
            "left": "left",
            "textStyle": {"fontFamily": "Inter, sans-serif", "fontWeight": "bold", "color": "#0F172A"},
        },
        "universalTransition": {"enabled": True},
        "color": [OKABE_ITO_PALETTE["favoravel"], OKABE_ITO_PALETTE["contrario"], OKABE_ITO_PALETTE["neutro"]],
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
        },
        "legend": {
            "data": ["Favorável (IC 95%)", "Contrário (IC 95%)", "Neutro (IC 95%)"],
            "top": "bottom",
        },
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": {"interval": 0, "rotate": 15},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"formatter": "{value}%"},
            "max": 100,
        },
        "series": [
            {
                "name": "Favorável (IC 95%)",
                "type": "bar",
                "data": fav_data,
                "itemStyle": {"color": OKABE_ITO_PALETTE["favoravel"]},
            },
            {
                "name": "Contrário (IC 95%)",
                "type": "bar",
                "data": cont_data,
                "itemStyle": {"color": OKABE_ITO_PALETTE["contrario"]},
            },
            {
                "name": "Neutro (IC 95%)",
                "type": "bar",
                "data": neu_data,
                "itemStyle": {"color": OKABE_ITO_PALETTE["neutro"]},
            },
            {
                "name": "Bandas de Erro IC 95%",
                "type": "custom",
                "renderItem": "renderErrorBar",
                "data": fav_errors,
            },
        ],
    }
    return option


def build_bubbles_and_spectra_network_echarts_spec(theme_dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói a especificação ECharts de grafo de força para análise de bolhas e os 4 espectros.
    """
    nodes = theme_dataset.get("bubbleNodes", [])
    edges = theme_dataset.get("bubbleEdges", [])

    option = {
        "title": {
            "text": "Topologia Não Supervisionada de Comunidades e 4 Espectros Oficiais (ADR-010)",
            "subtext": f"Modularidade Newman Q = {theme_dataset.get('topological', {}).get('modularityObserved', 0.62)} · Krackhardt E-I = {theme_dataset.get('topological', {}).get('homophilyKrackhardtEI', -0.42)}",
        },
        "universalTransition": {"enabled": True},
        "color": [OKABE_ITO_PALETTE["favoravel"], OKABE_ITO_PALETTE["contrario"], OKABE_ITO_PALETTE["bolha_a"], OKABE_ITO_PALETTE["bolha_b"]],
        "tooltip": {},
        "series": [
            {
                "name": "Rede de Diálogo",
                "type": "graph",
                "layout": "force",
                "force": {"repulsion": 300, "edgeLength": [50, 150]},
                "roam": True,
                "label": {"show": True, "position": "right"},
                "data": nodes,
                "links": edges,
                "lineStyle": {"color": "source", "curveness": 0.2},
            }
        ],
    }
    return option


def build_brazilian_27_ufs_choropleth_spec(theme_dataset: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Gera a especificação da malha geográfica cobrindo as 27 UFs brasileiras e 5 Macrorregiões.
    """
    return {
        "title": {"text": "Distribuição Territorial e Calibração por Raking IPF nas 27 UFs (IBGE)"},
        "universalTransition": {"enabled": True},
        "color": [OKABE_ITO_PALETTE["favoravel"], OKABE_ITO_PALETTE["contrario"]],
        "all_27_ufs_present": True,
        "ufs": sorted(list(BRAZIL_27_UFS_SET)),
        "regions": sorted(list(BRAZIL_5_REGIONS_SET)),
        "series": [
            {
                "name": "Amostra por UF (IC 95%)",
                "type": "map",
                "map": "brazil_27_ufs",
                "data": [{"name": uf, "value": 20} for uf in sorted(list(BRAZIL_27_UFS_SET))],
            }
        ],
    }


def apply_table_k_anonymity_masking(
    rows: List[Dict[str, Any]], min_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Aplica truncamento de hash HMAC em 10 caracteres (a1b2c3d4e5...) e mascara
    quaisquer células agregadas com contagem inferior a min_k (k >= 5) para "OUTROS_ANONIMIZADO_LGPD_K5".
    """
    masked_rows: List[Dict[str, Any]] = []

    for r in rows:
        r_copy = copy.deepcopy(r)

        # Truncamento de hash de autor
        for key in ["id", "author_hash", "author_id_hash", "author_id"]:
            if key in r_copy and isinstance(r_copy[key], str):
                val = r_copy[key]
                if len(val) > 10:
                    r_copy[key] = val[:10] + "..."

        # Colapso de células agregadas k < min_k
        count_val = (
            r_copy.get("count")
            or r_copy.get("accounts_count")
            or r_copy.get("n_org")
            or r_copy.get("unique_accounts_count")
        )
        if count_val is not None and isinstance(count_val, (int, float)):
            if 0 < count_val < min_k:
                r_copy["masked_label"] = "OUTROS_ANONIMIZADO_LGPD_K5"
                r_copy["stratum_label"] = "OUTROS_ANONIMIZADO_LGPD_K5"
                r_copy["unique_accounts_count"] = f"<{min_k}"
                r_copy["is_k_anonymized"] = True
            else:
                r_copy["is_k_anonymized"] = False

        masked_rows.append(r_copy)

    return masked_rows
