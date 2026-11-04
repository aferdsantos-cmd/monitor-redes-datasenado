#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Script de Verificação Anti-Alucinação de Citações, Sintaxe de DOI e Conformidade Lexical.

Parte integrante do Pilar 3 da Skill academic-tcc-datasenado.
Opera por padrão em modo 100% offline e determinístico (< 0.5s), com flag opcional --online
para validação de metadados junto à API pública da Crossref.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[3]

DOI_REGEX = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")

PROHIBITED_PHRASES = [
    "1 cidadão = 1 opinião",
    "1 cidadao = 1 opiniao",
    "1 cidadao, 1 opiniao",
    "1 cidadão, 1 opinião",
    "opinião dos brasileiros sobre o projeto",
    "opiniao dos brasileiros sobre o projeto",
    "margem de erro da pesquisa: ±",
    "margem de erro da pesquisa: +-",
]


def extract_dois_from_text(text: str) -> list[str]:
    """Extrai identificadores DOI encontrados em links ou menções de texto."""
    raw_matches = re.findall(r"https?://doi\.org/([^\s\)\]`\"'>]+)", text)
    cleaned = []
    for m in raw_matches:
        doi = m.rstrip(".,;:)")
        cleaned.append(doi)
    return cleaned


def check_prohibited_terms(file_path: Path, text: str) -> list[str]:
    """
    Verifica se o arquivo contém termos epistemologicamente proibidos
    fora de tabelas de vocabulário controlado e glossários.
    """
    violations = []
    lines = text.splitlines()
    in_glossary_or_table = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Ignora cabeçalhos de glossário ou tabelas comparativas
        if any(h in line.lower() for h in ["glossário", "glossario", "termos proibidos", "vocabulário controlado", "tabela de precisão"]):
            in_glossary_or_table = True
            continue

        if stripped.startswith("# ") or stripped.startswith("## "):
            in_glossary_or_table = any(h in line.lower() for h in ["glossário", "glossario", "termos proibidos", "vocabulário controlado"])

        # Linhas de tabela markdown
        if stripped.startswith("|") and stripped.endswith("|"):
            continue

        # Linhas dentro de citações que exemplificam erros
        if stripped.startswith(">") and "proibido" in stripped.lower():
            continue

        lower_line = stripped.lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in lower_line:
                violations.append(f"{file_path.name}:{idx} -> Encontrado termo proibido: '{phrase}'")

    return violations


def verify_doi_online(doi: str) -> bool:
    """Verifica a existência real do DOI na API pública Crossref."""
    url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": "DataSenadoResearchVerifier/1.0 (mailto:datasenado@senado.leg.br)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificador Anti-Alucinação de Citações e DOIs")
    parser.add_argument("--online", action="store_true", help="Valida DOIs contra a API pública Crossref")
    args = parser.parse_args()

    target_files: list[Path] = []
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        target_files.extend(sorted(docs_dir.glob("*.md")))

    refs_dir = REPO_ROOT / "skills" / "academic-tcc-datasenado" / "references"
    if refs_dir.exists():
        target_files.extend(sorted(refs_dir.glob("*.md")))

    if not target_files:
        print("[ERRO] Nenhum arquivo Markdown encontrado para verificação.")
        return 1

    total_dois_checked = 0
    invalid_doi_syntax: list[str] = []
    all_lexical_violations: list[str] = []
    unique_dois: set[str] = set()

    for path in target_files:
        content = path.read_text(encoding="utf-8")

        # 1. Checagem lexical
        violations = check_prohibited_terms(path, content)
        all_lexical_violations.extend(violations)

        # 2. Extração e validação de DOIs
        dois = extract_dois_from_text(content)
        for doi in dois:
            total_dois_checked += 1
            unique_dois.add(doi)
            if not DOI_REGEX.match(doi):
                invalid_doi_syntax.append(f"{path.name} -> DOI com sintaxe inválida: '{doi}'")

    print(f"=== Verificação Anti-Alucinação e Conformidade Acadêmica ===")
    print(f"Arquivos inspecionados: {len(target_files)}")
    print(f"DOIs verificados: {total_dois_checked} (Únicos: {len(unique_dois)})")

    success = True

    if invalid_doi_syntax:
        print("\n[FALHA] DOIs com sintaxe fora do padrão ISO 26324:")
        for err in invalid_doi_syntax:
            print(f"  ❌ {err}")
        success = False
    else:
        print("  ✅ Todos os DOIs seguem a sintaxe oficial ISO 26324.")

    if all_lexical_violations:
        print("\n[FALHA] Violações de conformidade terminológica encontradas:")
        for v in all_lexical_violations:
            print(f"  ❌ {v}")
        success = False
    else:
        print("  ✅ Nenhuma violação lexical de vocabulário proibido detectada.")

    if args.online and unique_dois:
        print(f"\nConsultando API da Crossref para {len(unique_dois)} DOIs únicos...")
        online_failures = []
        for doi in sorted(unique_dois):
            valid = verify_doi_online(doi)
            if valid:
                print(f"  ✅ [Crossref 200 OK] {doi}")
            else:
                print(f"  ❌ [Crossref NOT FOUND / ERROR] {doi}")
                online_failures.append(doi)
        if online_failures:
            success = False

    if success:
        print("\n[SUCESSO] Auditoria acadêmica e anti-alucinação concluída com 100% de conformidade.")
        return 0
    else:
        print("\n[FALHA] Foram encontrados erros na validação acadêmica.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
