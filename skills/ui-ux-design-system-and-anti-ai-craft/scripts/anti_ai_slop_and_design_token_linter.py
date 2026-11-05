#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Auditor de Design Tokens, Contraste WCAG 2.2 e Linter Anti-AI-Slop.

Executa:
1. Cálculo matemático de luminância relativa e razão de contraste WCAG 2.2 AA/AAA;
2. Validação da paleta institucional do DataSenado e paleta científica Okabe-Ito;
3. Linter estático em código UI/JSX para detecção e bloqueio de clichês de IA
   (gradientes neon, sombras coloridas, cantos rounded-3xl, emojis em títulos e falta de tabular-nums).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Converte string hexadecimal (#RRGGBB ou #RGB) para tupla RGB (0-255)."""
    clean_hex = hex_str.strip().lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join(c * 2 for c in clean_hex)
    if len(clean_hex) != 6:
        raise ValueError(f"Formato hexadecimal inválido: '{hex_str}'")
    r = int(clean_hex[0:2], 16)
    g = int(clean_hex[2:4], 16)
    b = int(clean_hex[4:6], 16)
    return r, g, b


def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    """Calcula a luminância relativa sRGB conforme a especificação W3C WCAG 2.2."""
    def linearize(c: float) -> float:
        c_norm = c / 255.0
        if c_norm <= 0.04045:
            return c_norm / 12.92
        return math.pow((c_norm + 0.055) / 1.055, 2.4)

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)

    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calculate_contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Calcula a razão de contraste (CR) entre duas cores: (Lmax + 0.05) / (Lmin + 0.05)."""
    ra, ga, ba = hex_to_rgb(hex_a)
    rb, gb, bb = hex_to_rgb(hex_b)

    l1 = calculate_relative_luminance(ra, ga, ba)
    l2 = calculate_relative_luminance(rb, gb, bb)

    l_max = max(l1, l2)
    l_min = min(l1, l2)

    cr = (l_max + 0.05) / (l_min + 0.05)
    return round(cr, 2)


# Padrões Proibidos de "IA Genérica" (AI-Slop Blacklist)
FORBIDDEN_GRADIENTS = [
    r"from-indigo-",
    r"via-purple-",
    r"to-pink-",
    r"from-purple-",
    r"to-cyan-",
    r"from-blue-600\s+to-violet-600",
]

FORBIDDEN_NEON_SHADOWS = [
    r"shadow-indigo-",
    r"shadow-purple-",
    r"shadow-pink-",
    r"shadow-cyan-",
]

FORBIDDEN_ROUNDED = [
    r"rounded-3xl",
    r"rounded-full\b(?!\s*//\s*avatar)",  # Permite rounded-full apenas para avatares explícitos
]

# Emojis comuns usados em títulos por IAs generativas
EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]"
)


def lint_ui_code_anti_ai_slop(source_code: str) -> List[str]:
    """Escaneia fragmentos de código JSX/HTML/Tailwind e aponta violações de AI-Slop e tipografia."""
    violations: List[str] = []
    lines = source_code.splitlines()

    for idx, line in enumerate(lines, start=1):
        # 1. Gradientes Neon
        for grad in FORBIDDEN_GRADIENTS:
            if re.search(grad, line):
                violations.append(
                    f"Linha {idx}: Gradiente neon genérico detectado ('{grad}'). "
                    f"Substitua por superfícies institucionais sobriedade DataSenado (slate-50 / slate-900)."
                )

        # 2. Sombras Coloridas Neon
        for shadow in FORBIDDEN_NEON_SHADOWS:
            if re.search(shadow, line):
                violations.append(
                    f"Linha {idx}: Sombra neon clichê de IA ('{shadow}'). "
                    f"Utilize sombras neutras sutis ('shadow-sm') e bordas capilares de 1px ('border-slate-200')."
                )

        # 3. Cantos Excessivamente Arredondados
        for rounded in FORBIDDEN_ROUNDED:
            if re.search(rounded, line) and "card" in line.lower() or "panel" in line.lower() or "box" in line.lower():
                violations.append(
                    f"Linha {idx}: Cantos inflados 'rounded-3xl' em painel analítico. "
                    f"Utilize raio profissional de dados ('rounded-md' ou 'rounded-lg')."
                )

        # 4. Emojis em Cabeçalhos e Botões
        if ("<h" in line or "<button" in line or "title=" in line or "header" in line) and EMOJI_PATTERN.search(line):
            match_emoji = EMOJI_PATTERN.search(line).group(0)
            violations.append(
                f"Linha {idx}: Emoji informal detectado ('{match_emoji}'). "
                f"Utilize exclusivamente ícones vetoriais monocromáticos Lucide React (w-4 h-4, strokeWidth=1.75)."
            )

        # 5. Tabelas ou Numerais sem tabular-nums
        if ("<table" in line or "text-lg font-bold" in line or "text-2xl font-bold" in line) and "tabular-nums" not in line:
            # Verifica se há valores numéricos nas proximidades
            if re.search(r"\d+[\.,]\d+", line) or "IC 95%" in line or "%" in line:
                violations.append(
                    f"Linha {idx}: Exibição de valores estatísticos sem 'tabular-nums'. "
                    f"Adicione compulsoriamente a classe 'tabular-nums' para prevenir desalinhamento horizontal."
                )

    return violations


def audit_theme_contrast_compliance() -> Dict[str, Any]:
    """Verifica se todos os pares de cor essenciais atendem ao padrão WCAG 2.2 AA (CR >= 4.5:1 ou 3.0:1)."""
    theme_pairs = [
        {"name": "Modo Claro: Texto Primário sobre Fundo", "fg": "#0F172A", "bg": "#FFFFFF", "min_cr": 4.5},
        {"name": "Modo Claro: Texto Secundário sobre Fundo", "fg": "#475569", "bg": "#FFFFFF", "min_cr": 4.5},
        {"name": "Modo Claro: Borda Capilar sobre Fundo", "fg": "#E2E8F0", "bg": "#FFFFFF", "min_cr": 1.2},  # Linha estrutural
        {"name": "Modo Escuro: Texto Primário sobre Fundo", "fg": "#F8FAFC", "bg": "#0F172A", "min_cr": 4.5},
        {"name": "Modo Escuro: Texto Secundário sobre Fundo", "fg": "#94A3B8", "bg": "#0F172A", "min_cr": 4.5},
        {"name": "Okabe-Ito: Favorável (#0072B2) sobre Fundo Claro", "fg": "#0072B2", "bg": "#FFFFFF", "min_cr": 4.5},
        {"name": "Okabe-Ito: Contrário (#D55E00) sobre Fundo Claro", "fg": "#D55E00", "bg": "#FFFFFF", "min_cr": 3.0},  # Componente gráfico/destaque
        {"name": "Okabe-Ito: Neutro (#64748B) sobre Fundo Claro", "fg": "#64748B", "bg": "#FFFFFF", "min_cr": 4.5},
    ]

    results = []
    all_pass = True
    for pair in theme_pairs:
        cr = calculate_contrast_ratio(pair["fg"], pair["bg"])
        passed = cr >= pair["min_cr"]
        if not passed:
            all_pass = False
        results.append({
            "pair": pair["name"],
            "foreground": pair["fg"],
            "background": pair["bg"],
            "contrast_ratio": f"{cr}:1",
            "required_min": f"{pair['min_cr']}:1",
            "passed": passed,
        })

    return {"all_pass": all_pass, "details": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditor de Design Tokens e Linter Anti-AI-Slop")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração com teste de contraste WCAG 2.2 e linter")
    parser.add_argument("--check-ui", type=Path, help="Caminho para arquivo JSX/TSX/HTML a ser auditado")
    args = parser.parse_args()

    if args.check_ui:
        path = args.check_ui.resolve()
        if not path.exists():
            print(f"[ERRO] Arquivo não encontrado: {path}", file=sys.stderr)
            return 1
        violations = lint_ui_code_anti_ai_slop(path.read_text(encoding="utf-8"))
        if violations:
            print(f"Violações de AI-Slop encontradas em {path.name}:")
            for v in violations:
                print(f"  ❌ {v}")
            return 1
        print(f"✅ Arquivo {path.name} 100% aderente ao Design System DataSenado.")
        return 0

    print("=== [1/2] Auditoria Matemática de Contraste WCAG 2.2 (DataSenado & Okabe-Ito) ===")
    contrast_res = audit_theme_contrast_compliance()
    print(json.dumps(contrast_res, indent=2, ensure_ascii=False))
    assert contrast_res["all_pass"] is True, "Falha na conformidade de contraste WCAG 2.2!"
    print("  ✅ Todos os tokens institucionais atendem aos critérios de contraste WCAG 2.2.")

    print("\n=== [2/2] Linter Anti-AI-Slop: Testando Código Amador vs DataSenado ===")
    bad_code = """
export function BadDashboard() {
  return (
    <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-3xl p-8 shadow-indigo-500/50">
      <h1 className="text-3xl font-bold">🚀 Dashboard de Monitoramento</h1>
      <button className="bg-purple-600 rounded-full">🔥 Filtrar</button>
      <div className="text-2xl font-bold">45.8% (IC 95%: [43.1% — 48.5%])</div>
    </div>
  );
}
"""
    good_code = """
import { BarChart3 } from "lucide-react";

export function DataSenadoDashboard() {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-4 shadow-sm">
      <div className="flex items-center gap-2 h-12">
        <BarChart3 className="w-4 h-4 text-slate-700 dark:text-slate-300" aria-hidden="true" />
        <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Bancada Analítica DataSenado</h1>
      </div>
      <div className="font-mono text-xl font-bold tabular-nums text-slate-900 dark:text-slate-50">
        45.8% <span className="text-xs text-slate-500 font-sans tabular-nums">(IC 95%: [43.1% — 48.5%])</span>
      </div>
    </div>
  );
}
"""
    bad_violations = lint_ui_code_anti_ai_slop(bad_code)
    good_violations = lint_ui_code_anti_ai_slop(good_code)

    print(f"Violações detectadas no código com 'cara de IA': {len(bad_violations)}")
    for v in bad_violations:
        print(f"  ❌ {v}")
    assert len(bad_violations) >= 3, f"Esperadas pelo menos 3 violações no bad_code, obtidas {len(bad_violations)}"
    assert len(good_violations) == 0, f"Código profissional gerou falsos positivos: {good_violations}"
    print("  ✅ Linter Anti-AI-Slop bloqueou clichês e aprovou componente institucional.")

    print("\nAuditoria de Design Tokens e Linter Anti-AI-Slop concluída com 100% de conformidade")
    return 0


if __name__ == "__main__":
    sys.exit(main())
