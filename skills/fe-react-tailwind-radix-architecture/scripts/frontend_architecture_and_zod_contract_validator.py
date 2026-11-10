#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Validador de Arquitetura Front-End, Contratos Zod/Pydantic e Estado Nuqs.

Executa:
1. Validação do contrato espelhado Zod/Pydantic da Barra Operacional (MonitoringWindowSpec);
2. Simulação e validação da sincronização de URL query state no padrão Nuqs (useQueryState);
3. Linter estático em código TypeScript/React para detecção e bloqueio de anti-padrões
   (uso de ': any', window.alert/confirm, <div onClick> sem acessibilidade e localStorage com PII).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse


VALID_THEMES = {
    "reforma_tributaria",
    "regulamentacao_ia",
    "seguranca_publica",
    "pl_ia_2338",
    "pec_escala_6x1",
    "eleicao_presidencia_senado",
    "isencao_ir_5mil_reforma_renda",
    "pec_seguranca_publica_guardas",
    "regulamentacao_apostas_bets_saude",
}
VALID_PLATFORMS = {
    "youtube",
    "telegram",
    "x",
    "x_twitter",
    "meta",
    "instagram_facebook",
    "tiktok",
    "whatsapp",
}
VALID_SCENARIOS = {"C1_HAJEK", "C2_INV_WEIGHT", "C3_RAKING"}

FORBIDDEN_LEXICAL_TERMS = re.compile(r"\b(corrupto|genocida|salvador|mito|ladrao)\b", re.IGNORECASE)


def parse_url_query_state(query_string: str) -> Dict[str, Any]:
    """Simula o parser Nuqs (useQueryState) para decodificar parâmetros da query string da URL."""
    clean_query = query_string.lstrip("?")
    parsed = urllib.parse.parse_qs(clean_query)
    result: Dict[str, Any] = {}

    if "theme" in parsed:
        result["theme_id"] = parsed["theme"][0]
    if "days" in parsed:
        try:
            result["window_days"] = int(parsed["days"][0])
        except ValueError:
            result["window_days"] = None
    if "platforms" in parsed:
        result["selected_platforms"] = parsed["platforms"][0].split(",")
    if "sample_n" in parsed:
        try:
            result["target_sample_size_n"] = int(parsed["sample_n"][0])
        except ValueError:
            result["target_sample_size_n"] = None
    if "scenario" in parsed:
        result["scenario"] = parsed["scenario"][0]
    if "q" in parsed:
        result["lexical_search_query"] = parsed["q"][0]

    return result


def serialize_url_query_state(filters: Dict[str, Any]) -> str:
    """Serializa dicionário de filtros em uma query string URL limpa no padrão Nuqs."""
    query_parts = []
    if "theme_id" in filters:
        query_parts.append(f"theme={urllib.parse.quote_plus(filters['theme_id'])}")
    if "window_days" in filters and filters["window_days"] is not None:
        query_parts.append(f"days={filters['window_days']}")
    if "selected_platforms" in filters and filters["selected_platforms"]:
        platforms_str = ",".join(sorted(filters["selected_platforms"]))
        query_parts.append(f"platforms={urllib.parse.quote_plus(platforms_str)}")
    if "target_sample_size_n" in filters and filters["target_sample_size_n"] is not None:
        query_parts.append(f"sample_n={filters['target_sample_size_n']}")
    if "scenario" in filters:
        query_parts.append(f"scenario={urllib.parse.quote_plus(filters['scenario'])}")
    if "lexical_search_query" in filters and filters["lexical_search_query"]:
        query_parts.append(f"q={urllib.parse.quote_plus(filters['lexical_search_query'])}")

    return "?" + "&".join(query_parts) if query_parts else ""


def validate_monitoring_window_spec(spec_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Valida especificação contra o contrato Zod/Pydantic espelhado."""
    errors: List[str] = []

    # 1. Validação de Tema
    theme = spec_dict.get("theme_id")
    if not theme or theme not in VALID_THEMES:
        errors.append(f"Tema inválido ou ausente: '{theme}'. Temas permitidos: {sorted(VALID_THEMES)}")

    # 2. Janela de Dias
    days = spec_dict.get("window_days")
    if days is None or not isinstance(days, int) or days < 1 or days > 90:
        errors.append(f"Janela 'window_days' inválida ({days}). Deve ser inteiro entre 1 e 90 dias.")

    # 3. Plataformas Selecionadas
    platforms = spec_dict.get("selected_platforms")
    if not platforms or not isinstance(platforms, list) or len(platforms) == 0:
        errors.append("Pelo menos uma plataforma social deve ser selecionada.")
    else:
        invalid_p = [p for p in platforms if p not in VALID_PLATFORMS]
        if invalid_p:
            errors.append(f"Plataformas inválidas detectadas: {invalid_p}. Permitidas: {sorted(VALID_PLATFORMS)}")

    # 4. Tamanho Amostral Alvo
    target_n = spec_dict.get("target_sample_size_n", 30)
    if target_n is not None and (not isinstance(target_n, int) or target_n < 10 or target_n > 1000):
        errors.append(f"Tamanho amostral 'target_sample_size_n' ({target_n}) deve estar entre 10 e 1000 contas.")

    # 5. Cenário Estatístico
    scenario = spec_dict.get("scenario", "C3_RAKING")
    if scenario not in VALID_SCENARIOS:
        errors.append(f"Cenário estatístico inválido: '{scenario}'. Esperado: {sorted(VALID_SCENARIOS)}")

    # 6. Neutralidade Lexical (M-04)
    query = spec_dict.get("lexical_search_query")
    if query:
        if len(query) > 100:
            errors.append("Termo de busca lexical excede o teto de 100 caracteres.")
        if FORBIDDEN_LEXICAL_TERMS.search(query):
            errors.append("Violação de Neutralidade M-04: Termos valorativos/polarizados são proibidos na busca temática neutra!")

    is_valid = len(errors) == 0
    return is_valid, errors


def lint_frontend_architecture_code(source_code: str) -> List[str]:
    """Escaneia código front-end (TypeScript/React) buscando violações arquiteturais e de acessibilidade."""
    violations: List[str] = []
    lines = source_code.splitlines()

    for idx, line in enumerate(lines, start=1):
        # 1. Proibição de : any
        if re.search(r":\s*any\b", line) and not line.strip().startswith("//"):
            violations.append(
                f"Linha {idx}: Tipagem frouxa ': any' detectada. "
                f"Utilize tipos estritos, genéricos ou schemas Zod inferidos (z.infer<typeof ...>)."
            )

        # 2. Proibição de window.alert / confirm / prompt
        if re.search(r"\bwindow\.(alert|confirm|prompt)\s*\(", line) or re.search(r"\b(alert|confirm|prompt)\s*\(", line):
            if "toast." not in line and "Radix" not in line and not line.strip().startswith("//"):
                violations.append(
                    f"Linha {idx}: Chamada de diálogo nativo bloqueante ('alert/confirm/prompt'). "
                    f"Utilize toasts assíncronos Sonner ('toast.success') ou Radix AlertDialog."
                )

        # 3. Proibição de <div onClick sem WAI-ARIA
        if "<div" in line and "onClick=" in line:
            if "role=" not in line or "tabIndex=" not in line:
                violations.append(
                    f"Linha {idx}: Elemento interativo '<div onClick=...>' sem WAI-ARIA. "
                    f"Substitua por primitivo acessível Radix UI (Toolbar.Button / Button) com foco e teclado."
                )

        # 4. Violação Zero-Footprint: localStorage com PII ou dados brutos
        if "localStorage.setItem" in line or "sessionStorage.setItem" in line:
            if any(term in line.lower() for term in ("post", "author", "token", "payload", "hash", "dataset")):
                violations.append(
                    f"Linha {idx}: Violação de Zero-Footprint / LGPD: Armazenamento sensível em localStorage/sessionStorage. "
                    f"Mantenha dados analíticos apenas em memória volátil gerenciada pelo TanStack Query."
                )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validador de Arquitetura Front-End e Contratos Zod")
    parser.add_argument("--demo", action="store_true", help="Executa testes de sincronização Nuqs, Zod e linter estático")
    parser.add_argument("--target-dir", type=Path, help="Diretório contendo código front-end (TypeScript/React)")
    args = parser.parse_args()

    if args.target_dir:
        target = args.target_dir.resolve()
        if not target.exists():
            print(f"[ERRO] Diretório não encontrado: {target}", file=sys.stderr)
            return 1
        all_violations = []
        fe_files = list(target.rglob("*.tsx")) + list(target.rglob("*.ts"))
        for f in fe_files:
            v_list = lint_frontend_architecture_code(f.read_text(encoding="utf-8"))
            if v_list:
                all_violations.extend([f"{f.name}: {v}" for v in v_list])
        if all_violations:
            print(f"Violações de arquitetura front-end encontradas ({len(all_violations)}):")
            for v in all_violations:
                print(f"  ❌ {v}")
            return 1
        print(f"✅ Diretório {target.name} ({len(fe_files)} arquivos) 100% aderente às diretrizes de arquitetura React/Tailwind/Radix.")
        return 0

    print("=== [1/3] Sincronização de URL Query State (Padrão Nuqs) ===")
    demo_filters = {
        "theme_id": "reforma_tributaria",
        "window_days": 14,
        "selected_platforms": ["youtube", "whatsapp", "telegram"],
        "target_sample_size_n": 50,
        "scenario": "C3_RAKING",
    }
    url_query = serialize_url_query_state(demo_filters)
    parsed_back = parse_url_query_state(url_query)

    print(f"Filtros Originais: {json.dumps(demo_filters)}")
    print(f"URL Gerada (Nuqs): {url_query}")
    print(f"Filtros Decodificados: {json.dumps(parsed_back)}")

    assert parsed_back["theme_id"] == demo_filters["theme_id"]
    assert parsed_back["window_days"] == demo_filters["window_days"]
    assert set(parsed_back["selected_platforms"]) == set(demo_filters["selected_platforms"])
    print("  ✅ Sincronização bidirecional de URL state comprovada com fidelidade.")

    print("\n=== [2/3] Validação de Contrato Espelhado Zod/Pydantic ===")
    # Caso 1: Válido
    valid_ok, valid_errs = validate_monitoring_window_spec(demo_filters)
    assert valid_ok is True, f"Filtros válidos falharam: {valid_errs}"
    print("  ✅ Especificação válida aprovada sem ressalvas.")

    # Caso 2: Inválido (dias negativos, sem plataformas e termo polarizado proibido)
    invalid_filters = {
        "theme_id": "tema_inexistente",
        "window_days": -7,
        "selected_platforms": [],
        "lexical_search_query": "projeto do governo corrupto",
    }
    invalid_ok, invalid_errs = validate_monitoring_window_spec(invalid_filters)
    assert invalid_ok is False, "Filtros inválidos deveriam ser reprovados!"
    assert len(invalid_errs) >= 4, f"Esperados pelo menos 4 erros, obtidos {len(invalid_errs)}"
    print(f"  ✅ Violações detectadas pelo contrato Zod ({len(invalid_errs)} erros):")
    for err in invalid_errs:
        print(f"     - {err}")

    print("\n=== [3/3] Linter de Arquitetura Front-End (Anti-Padrões de Código) ===")
    bad_fe_code = """
import React from "react";

export function BadComponent(props: any) {
  function handleClick() {
    window.alert("Filtro aplicado com sucesso!");
    localStorage.setItem("cached_post_payload", JSON.stringify(props.data));
  }

  return (
    <div onClick={handleClick} className="p-4 bg-blue-500">
      Clique aqui
    </div>
  );
}
"""
    good_fe_code = """
import React from "react";
import * as Toolbar from "@radix-ui/react-toolbar";
import { toast } from "sonner";
import { MonitoringWindowSpec } from "./types";

interface FilterBarProps {
  spec: MonitoringWindowSpec;
  onApply: (updated: MonitoringWindowSpec) => void;
}

export function FilterBar({ spec, onApply }: FilterBarProps) {
  function handleClick() {
    toast.success("Filtros atualizados na URL via Nuqs");
    onApply(spec);
  }

  return (
    <Toolbar.Root className="flex h-12 items-center gap-2">
      <Toolbar.Button onClick={handleClick} className="px-3 py-1.5 text-xs font-semibold rounded bg-blue-900 text-white">
        Aplicar
      </Toolbar.Button>
    </Toolbar.Root>
  );
}
"""
    bad_violations = lint_frontend_architecture_code(bad_fe_code)
    good_violations = lint_frontend_architecture_code(good_fe_code)

    print(f"Violações detectadas no código amador: {len(bad_violations)}")
    for v in bad_violations:
        print(f"  ❌ {v}")
    assert len(bad_violations) >= 4, f"Esperadas pelo menos 4 violações, obtidas {len(bad_violations)}"
    assert len(good_violations) == 0, f"Código limpo gerou falsos positivos: {good_violations}"
    print("  ✅ Linter de Arquitetura Front-End validou acessibilidade, tipagem e Zero-Footprint.")

    print("\nValidador de Arquitetura Front-End (React/Radix/Zod/Nuqs/TanStack) concluído com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
