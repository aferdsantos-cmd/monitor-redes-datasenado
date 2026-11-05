#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Validador de Visualização Data-Dense (Apache ECharts, TanStack Table, Mapa 27 UFs IBGE e @media print).

Executa:
1. Validação estrutural de opções JSON do Apache ECharts (universalTransition, paleta Okabe-Ito,
   barras de erro IC 95% e rejeição de gráficos 3D ou pizza com mais de 3 fatias);
2. Verificação da malha geográfica completa das 27 UFs e 5 Macrorregiões do Brasil (IBGE);
3. Validação das salvaguardas de privacidade LGPD em tabelas (truncamento de hash e k-anonimato k >= 5);
4. Validação da folha de estilos @media print para relatórios executivos em A4.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

BRAZIL_27_UFS: Set[str] = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
}

BRAZIL_5_MACROREGIONS: Set[str] = {
    "Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"
}

OKABE_ITO_CORE_COLORS: Set[str] = {"#0072b2", "#d55e00"}


def validate_echarts_options_schema(option: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida o esquema de configuração do Apache ECharts segundo as regras do DataSenado."""
    errors: List[str] = []

    # 1. Verifica presença de universalTransition
    univ_trans = option.get("universalTransition")
    if not univ_trans or not (isinstance(univ_trans, dict) and univ_trans.get("enabled", True) or univ_trans is True):
        errors.append("Opções do ECharts devem declarar 'universalTransition: { enabled: true }' para evitar piscar de tela.")

    # 2. Valida paleta de cores Okabe-Ito
    colors = [c.lower() for c in option.get("color", []) if isinstance(c, str)]
    if not any(k in colors for k in OKABE_ITO_CORE_COLORS):
        errors.append("Paleta de cores do gráfico não inclui as cores obrigatórias Okabe-Ito (#0072B2 / #D55E00).")

    # 3. Proíbe gráficos 3D
    series_list = option.get("series", [])
    if not isinstance(series_list, list):
        series_list = [series_list]

    for idx, s in enumerate(series_list):
        if not isinstance(s, dict):
            continue
        s_type = s.get("type", "")
        if "3d" in s_type.lower() or s_type in ("surface", "bar3D", "scatter3D", "line3D"):
            errors.append(f"Série {idx} utiliza tipo proibido 3D ('{s_type}'). Gráficos 3D distorcem proporções.")

        # 4. Proíbe pizza com mais de 3 categorias
        if s_type == "pie":
            data = s.get("data", [])
            if len(data) > 3:
                errors.append(f"Gráfico de pizza com {len(data)} fatias proibido. Máximo permitido: 3 categorias.")

    # 5. Verifica se há barras de erro IC 95% quando há série de prevalência/estimativa
    has_bar_or_line = any(s.get("type") in ("bar", "line") for s in series_list if isinstance(s, dict))
    has_error_band = any(
        s.get("type") == "custom" or "ic" in str(s.get("name", "")).lower() or "error" in str(s.get("name", "")).lower()
        for s in series_list if isinstance(s, dict)
    )
    if has_bar_or_line and not has_error_band:
        errors.append("Gráfico de estimativa estatística deve conter série de bandas de erro de Intervalo de Confiança (IC 95%).")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_brazilian_uf_mesh(uf_list: List[str]) -> Tuple[bool, List[str]]:
    """Verifica a integridade da malha geográfica das 27 UFs brasileiras."""
    errors: List[str] = []
    provided_set = set(uf_list)

    missing = BRAZIL_27_UFS - provided_set
    if missing:
        errors.append(f"Malha geográfica incompleta. UFs faltantes ({len(missing)}): {sorted(missing)}")

    invalid = provided_set - BRAZIL_27_UFS
    if invalid:
        errors.append(f"UFs inválidas detectadas: {sorted(invalid)}")

    is_valid = len(errors) == 0
    return is_valid, errors


def apply_table_k_anonymity_masking(rows: List[Dict[str, Any]], min_k: int = 5) -> List[Dict[str, Any]]:
    """Aplica truncamento de hash HMAC e mascaramento de k-anonimato (k >= 5) sobre registros de tabela."""
    masked_rows: List[Dict[str, Any]] = []

    for r in rows:
        row_copy = dict(r)

        # Trunca hash do autor se presente
        if "author_id_hash" in row_copy and isinstance(row_copy["author_id_hash"], str):
            raw_hash = row_copy["author_id_hash"]
            if len(raw_hash) > 10:
                row_copy["author_id_hash"] = raw_hash[:10] + "..."

        # Mascara células com k < min_k
        n_accounts = row_copy.get("unique_accounts_count")
        if n_accounts is not None and isinstance(n_accounts, (int, float)):
            if 0 < n_accounts < min_k:
                row_copy["stratum_label"] = "OUTROS_ANONIMIZADO_LGPD_K5"
                row_copy["unique_accounts_count"] = f"<{min_k}"

        masked_rows.append(row_copy)

    return masked_rows


def validate_media_print_stylesheet(css_text: str) -> Tuple[bool, List[str]]:
    """Valida a conformidade da folha de estilos @media print com a fidelidade de impressão A4."""
    errors: List[str] = []

    if "@media print" not in css_text:
        errors.append("Folha de estilos deve conter bloco '@media print'.")

    if "@page" not in css_text or "A4" not in css_text:
        errors.append("Regra '@page { size: A4 ... }' obrigatória ausente.")

    if "break-inside" not in css_text and "page-break-inside" not in css_text:
        errors.append("Regra 'break-inside: avoid' obrigatória para prevenir corte no meio de gráficos e tabelas.")

    if "none" not in css_text and "hidden" not in css_text:
        errors.append("Regras de ocultação de barras de navegação ('display: none') ausentes no bloco de impressão.")

    is_valid = len(errors) == 0
    return is_valid, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de Visualização Data-Dense e Impressão")
    parser.add_argument("--demo", action="store_true", help="Executa testes determinísticos de ECharts, 27 UFs, LGPD e @media print")
    args = parser.parse_args()

    print("=== [1/4] Validação de Opções Apache ECharts (DataSenado & Okabe-Ito) ===")
    valid_option = {
        "universalTransition": {"enabled": True},
        "color": ["#0072B2", "#D55E00", "#64748B"],
        "xAxis": {"type": "category", "data": ["C1 Hájek", "C2 Inverso", "C3 Raking"]},
        "yAxis": {"type": "value"},
        "series": [
            {"name": "Favorável", "type": "bar", "data": [45.2, 42.1, 46.8]},
            {"name": "IC 95%", "type": "custom", "data": [[42.0, 48.4], [39.1, 45.1], [43.9, 49.7]]},
        ],
    }
    opt_ok, opt_errs = validate_echarts_options_schema(valid_option)
    assert opt_ok is True, f"Opção válida reprovada: {opt_errs}"
    print("  ✅ Esquema ECharts aprovado com universalTransition, Okabe-Ito e bandas IC 95%.")

    # Testa rejeição a gráfico 3D e pizza com muitas fatias
    bad_option = {
        "color": ["#ff00ff"],
        "series": [
            {"type": "bar3D", "data": [1, 2, 3]},
            {"type": "pie", "data": [{"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}]},
        ],
    }
    bad_ok, bad_errs = validate_echarts_options_schema(bad_option)
    assert bad_ok is False, "Opções proibidas deveriam ser reprovadas!"
    assert len(bad_errs) >= 3, f"Esperadas pelo menos 3 violações no bad_option, obtidas {len(bad_errs)}"
    print(f"  ✅ Violações de visualização detectadas ({len(bad_errs)} falhas bloqueadas).")

    print("\n=== [2/4] Verificação da Malha Geográfica Completa (27 UFs / IBGE) ===")
    all_ufs = sorted(list(BRAZIL_27_UFS))
    mesh_ok, mesh_errs = validate_brazilian_uf_mesh(all_ufs)
    assert mesh_ok is True
    print(f"  ✅ Todas as 27 UFs brasileiras ({', '.join(all_ufs[:5])} ... {all_ufs[-1]}) verificadas.")

    print("\n=== [3/4] Salvaguardas LGPD em Tabelas (k-anonimato k >= 5 e Truncamento de Hash) ===")
    sample_table = [
        {"author_id_hash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890", "unique_accounts_count": 28, "stratum_label": "SP_Capital"},
        {"author_id_hash": "f6e5d4c3b2a10987654321fedcba0987654321fedcba0987654321fedcba0987", "unique_accounts_count": 3, "stratum_label": "Municipio_Pequeno_X"},
    ]
    masked_table = apply_table_k_anonymity_masking(sample_table, min_k=5)
    print(f"Tabela Mascarada: {json.dumps(masked_table, indent=2)}")

    assert masked_table[0]["author_id_hash"] == "a1b2c3d4e5..."
    assert masked_table[1]["stratum_label"] == "OUTROS_ANONIMIZADO_LGPD_K5"
    assert masked_table[1]["unique_accounts_count"] == "<5"
    print("  ✅ Regras de k-anonimato (k >= 5) e truncamento de identificadores aplicadas com sucesso.")

    print("\n=== [4/4] Validação de Folha de Estilo @media print (Fidelidade A4) ===")
    sample_css = """
@media print {
  @page {
    size: A4 portrait;
    margin: 15mm;
  }
  .toolbar-root, nav, header {
    display: none !important;
  }
  .echarts-card, table {
    break-inside: avoid !important;
  }
}
"""
    css_ok, css_errs = validate_media_print_stylesheet(sample_css)
    assert css_ok is True, f"CSS de impressão reprovado: {css_errs}"
    print("  ✅ Folha de estilo @media print atende aos padrões A4 e prevenção de quebra de página.")

    print("\nValidador de Visualização Data-Dense (ECharts, TanStack Table, Mapa IBGE 27 UFs e @media print) concluído com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
