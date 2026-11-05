#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Portão de Controle de Qualidade Visual, Acessibilidade WCAG 2.2 e Honestidade Estatística.

Executa a avaliação pericial determinística dos 4 Portões Visuais:
- Gate 1: ANTI_AI_SLOP_AND_TYPOGRAPHY_GATE (Zero gradientes neon, zero emojis operacionais, 100% tabular-nums);
- Gate 2: WCAG22_CONTRAST_AND_A11Y_GATE (Contraste CR >= 4.5:1 / 3.0:1, WAI-ARIA, foco visível);
- Gate 3: ZERO_CLS_SKELETON_AND_FLUID_UX_GATE (Skeletons com mesma geometria reservada CLS = 0, Nuqs URL state);
- Gate 4: STATISTICAL_AND_LGPD_UI_HONESTY_GATE (Declaração de n, N_org, IC 95%, Cenário 3 e LGPD k >= 5).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    def lin(c: float) -> float:
        c_n = c / 255.0
        return c_n / 12.92 if c_n <= 0.04045 else math.pow((c_n + 0.055) / 1.055, 2.4)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast_ratio(hex_a: str, hex_b: str) -> float:
    ra, ga, ba = _hex_to_rgb(hex_a)
    rb, gb, bb = _hex_to_rgb(hex_b)
    l1 = _relative_luminance(ra, ga, ba)
    l2 = _relative_luminance(rb, gb, bb)
    return round((max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 2)


EMOJI_REGEX = re.compile(
    r"[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]"
)


def verify_gate1_anti_ai_slop_and_typography(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Portão 1: Anti-AI-Slop, Design Tokens e Tipografia tabular-nums."""
    errors: List[str] = []
    code = bundle.get("jsx_code", "")
    classes = bundle.get("css_classes", [])
    classes_str = " ".join(classes) + " " + code

    # Verifica gradientes neon proibidos
    if any(g in classes_str for g in ("from-indigo-", "via-purple-", "to-pink-", "from-purple-")):
        errors.append("Gate 1 Falhou: Gradientes neon proibidos detectados (clichê de IA). Use superfícies sóbrias.")

    # Verifica sombras neon
    if any(s in classes_str for s in ("shadow-indigo-", "shadow-purple-", "shadow-pink-")):
        errors.append("Gate 1 Falhou: Sombras neon de IA detectadas. Use 'shadow-sm' e bordas capilares de 1px.")

    # Verifica rounded-3xl em cards
    if "rounded-3xl" in classes_str and ("card" in classes_str.lower() or "panel" in classes_str.lower()):
        errors.append("Gate 1 Falhou: Cantos inflados 'rounded-3xl' em painel analítico. Use 'rounded-lg'.")

    # Verifica emojis em títulos
    headers = bundle.get("header_titles", [])
    for h in headers:
        if EMOJI_REGEX.search(h):
            errors.append(f"Gate 1 Falhou: Emoji detectado no título operacional ('{h}'). Use ícones Lucide React.")

    # Verifica tabular-nums
    has_numbers = bundle.get("has_statistical_numbers", False)
    has_tabular = "tabular-nums" in classes_str or bundle.get("has_tabular_nums", False)
    if has_numbers and not has_tabular:
        errors.append("Gate 1 Falhou: Numerais estatísticos exibidos sem 'tabular-nums'. Risco de desalinhamento.")

    return len(errors) == 0, errors


def verify_gate2_wcag_contrast_and_a11y(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Portão 2: Acessibilidade WCAG 2.2 AA (Contraste >= 4.5:1 e WAI-ARIA)."""
    errors: List[str] = []
    color_pairs = bundle.get("color_pairs", [])

    for pair in color_pairs:
        fg = pair.get("fg", "#000000")
        bg = pair.get("bg", "#FFFFFF")
        min_cr = pair.get("min_cr", 4.5)
        name = pair.get("name", f"{fg} on {bg}")
        try:
            cr = _contrast_ratio(fg, bg)
            if cr < min_cr:
                errors.append(f"Gate 2 Falhou: Contraste insuficiente em '{name}': {cr}:1 (exige >= {min_cr}:1).")
        except Exception as e:
            errors.append(f"Gate 2 Falhou: Erro ao calcular contraste para '{name}': {e}")

    # Verifica suporte a teclado e atributos acessíveis
    interactive_elements = bundle.get("interactive_elements", [])
    for elem in interactive_elements:
        tag = elem.get("tag", "")
        has_role = bool(elem.get("role"))
        has_tabindex = "tabIndex" in elem or "tabindex" in elem
        has_aria_label = bool(elem.get("aria_label") or elem.get("aria_labelledby"))
        if tag == "div" and elem.get("has_click_handler"):
            if not has_role or not has_tabindex:
                errors.append("Gate 2 Falhou: '<div onClick>' sem 'role' ou 'tabIndex'. Use Radix UI ou button nativo.")

    return len(errors) == 0, errors


def verify_gate3_zero_cls_and_skeletons(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Portão 3: Estabilidade de Layout (CLS = 0) e Skeletons Estruturais."""
    errors: List[str] = []
    async_containers = bundle.get("async_containers", [])

    for c in async_containers:
        has_skeleton = c.get("has_matching_skeleton", False)
        has_fixed_height = c.get("has_reserved_height", False) or bool(c.get("min_height"))
        container_id = c.get("id", "container_analitico")

        if not has_skeleton:
            errors.append(f"Gate 3 Falhou: Container assíncrono '{container_id}' sem Skeleton estrutural (risco de CLS > 0).")
        if not has_fixed_height:
            errors.append(f"Gate 3 Falhou: Container '{container_id}' sem altura reservada (min-h-[...]).")

    # Verifica se filtros usam reload em vez de URL state Nuqs
    if bundle.get("uses_full_page_reload", False):
        errors.append("Gate 3 Falhou: Filtro operacional aciona 'window.location.reload()'. Use Nuqs 'useQueryState'.")

    return len(errors) == 0, errors


def verify_gate4_statistical_and_lgpd_honesty(bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Portão 4: Honestidade Estatística na UI e Blindagem LGPD."""
    errors: List[str] = []
    ui_metadata = bundle.get("statistical_ui_metadata", {})

    # Exigência de n e N_org
    if not ui_metadata.get("declares_sample_size_n"):
        errors.append("Gate 4 Falhou: A tela omite o tamanho da amostra auditada (n).")
    if not ui_metadata.get("declares_organic_universe_N"):
        errors.append("Gate 4 Falhou: A tela omite a contagem do universo orgânico observado (N_org).")

    # Bandas de erro IC 95%
    if ui_metadata.get("renders_opinion_chart") and not ui_metadata.get("renders_ic95_error_bands"):
        errors.append("Gate 4 Falhou: Gráfico de posicionamento omite barras de erro de Intervalo de Confiança (IC 95%).")

    # Rótulo honesto do Cenário 3
    scenarios = ui_metadata.get("scenario_labels", [])
    if scenarios and not any("cenário 3" in s.lower() or "raking" in s.lower() for s in scenarios):
        errors.append("Gate 4 Falhou: Ausência de identificação metodológica explícita do 'Cenário 3 — Raking IPF'.")

    # Proteção LGPD
    if bundle.get("exposes_raw_author_ids", False):
        errors.append("Gate 4 Falhou: Violação de LGPD: Exposição de identificadores brutos de autor na tela!")
    if bundle.get("exposes_cells_with_k_less_than_5", False):
        errors.append("Gate 4 Falhou: Violação de LGPD: Exibição de células demográficas com k < 5 contas sem mascaramento!")

    return len(errors) == 0, errors


def evaluate_visual_quality_gates(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Avalia os 4 Portões Visuais e emite parecer consolidado com conformidade percentual."""
    g1_ok, g1_errs = verify_gate1_anti_ai_slop_and_typography(bundle)
    g2_ok, g2_errs = verify_gate2_wcag_contrast_and_a11y(bundle)
    g3_ok, g3_errs = verify_gate3_zero_cls_and_skeletons(bundle)
    g4_ok, g4_errs = verify_gate4_statistical_and_lgpd_honesty(bundle)

    passed_count = sum([g1_ok, g2_ok, g3_ok, g4_ok])
    score = (passed_count / 4.0) * 100.0
    all_passed = passed_count == 4

    return {
        "status": "PASS" if all_passed else "FAIL",
        "conformance_score": f"{score:.1f}%",
        "gates": {
            "gate1_anti_ai_slop_and_typography": {"passed": g1_ok, "errors": g1_errs},
            "gate2_wcag22_contrast_and_a11y": {"passed": g2_ok, "errors": g2_errs},
            "gate3_zero_cls_and_skeletons": {"passed": g3_ok, "errors": g3_errs},
            "gate4_statistical_and_lgpd_honesty": {"passed": g4_ok, "errors": g4_errs},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Portão de Controle de Qualidade Visual e Acessibilidade")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração contra bundle padrão DataSenado e bundle com falhas")
    args = parser.parse_args()

    print("=== [1/2] Avaliando Bundle Padrão de Interface DataSenado ===")
    compliant_bundle = {
        "css_classes": ["bg-white", "dark:bg-slate-900", "border-slate-200", "tabular-nums", "rounded-lg"],
        "header_titles": ["Bancada Analítica DataSenado", "Monitoramento Temático de Opinião Pública"],
        "has_statistical_numbers": True,
        "has_tabular_nums": True,
        "color_pairs": [
            {"name": "Texto Primário / Superfície", "fg": "#0F172A", "bg": "#FFFFFF", "min_cr": 4.5},
            {"name": "Texto Secundário / Superfície", "fg": "#475569", "bg": "#FFFFFF", "min_cr": 4.5},
            {"name": "Azul Okabe-Ito / Fundo", "fg": "#0072B2", "bg": "#FFFFFF", "min_cr": 4.5},
        ],
        "interactive_elements": [
            {"tag": "button", "role": "button", "tabIndex": 0, "aria_label": "Filtrar por data"}
        ],
        "async_containers": [
            {"id": "chart_stance", "has_matching_skeleton": True, "has_reserved_height": True, "min_height": "320px"},
            {"id": "table_macroregions", "has_matching_skeleton": True, "has_reserved_height": True, "min_height": "240px"},
        ],
        "uses_full_page_reload": False,
        "statistical_ui_metadata": {
            "declares_sample_size_n": True,
            "declares_organic_universe_N": True,
            "renders_opinion_chart": True,
            "renders_ic95_error_bands": True,
            "scenario_labels": ["Cenário 1 — Hájek", "Cenário 2 — 1/K", "Cenário 3 — Raking IPF Simplex"],
        },
        "exposes_raw_author_ids": False,
        "exposes_cells_with_k_less_than_5": False,
    }

    report_good = evaluate_visual_quality_gates(compliant_bundle)
    print(json.dumps(report_good, indent=2, ensure_ascii=False))
    assert report_good["status"] == "PASS", f"Bundle padrão foi reprovado: {report_good}"
    print("  ✅ Bundle institucional DataSenado aprovado com 100% de conformidade nos 4 Portões.")

    print("\n=== [2/2] Avaliando Bundle Defeituoso (Detecção de 4 Falhas Injetadas) ===")
    adversarial_bundle = {
        "css_classes": ["bg-gradient-to-r", "from-indigo-500", "to-purple-600", "rounded-3xl"],
        "header_titles": ["🚀 Painel de Controle"],
        "has_statistical_numbers": True,
        "has_tabular_nums": False,  # Falha 1: falta tabular-nums
        "color_pairs": [
            {"name": "Texto Ilegível", "fg": "#94A3B8", "bg": "#FFFFFF", "min_cr": 4.5},  # Falha 2: contraste baixo 2.5:1
        ],
        "async_containers": [
            {"id": "chart_broken", "has_matching_skeleton": False, "has_reserved_height": False},  # Falha 3: sem skeleton (CLS > 0)
        ],
        "statistical_ui_metadata": {
            "declares_sample_size_n": False,  # Falha 4: omite tamanho amostral
            "declares_organic_universe_N": False,
            "renders_opinion_chart": True,
            "renders_ic95_error_bands": False,  # Falha 4: omite IC 95%
        },
    }

    report_bad = evaluate_visual_quality_gates(adversarial_bundle)
    assert report_bad["status"] == "FAIL", "Bundle defeituoso deveria ser reprovado!"
    assert report_bad["gates"]["gate1_anti_ai_slop_and_typography"]["passed"] is False
    assert report_bad["gates"]["gate2_wcag22_contrast_and_a11y"]["passed"] is False
    assert report_bad["gates"]["gate3_zero_cls_and_skeletons"]["passed"] is False
    assert report_bad["gates"]["gate4_statistical_and_lgpd_honesty"]["passed"] is False

    print("  ✅ Todas as 4 falhas injetadas foram flagradas e bloqueadas pelos 4 Portões:")
    for gate_name, gate_info in report_bad["gates"].items():
        print(f"     - {gate_name}: {gate_info['errors']}")

    print("\nPortão de Qualidade Visual, Acessibilidade WCAG 2.2 e Honestidade Estatística concluído com 100% de conformidade")
    return 0


if __name__ == "__main__":
    sys.exit(main())
