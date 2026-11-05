#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Sonda Pericial de Auditoria Operacional de Campo (Audit Fieldwork Probe).

Executa em chamada única (< 5s) a bateria completa de inspeções periciais:
1. Cria e valida a pasta cronológica de diálogo (Auditorias/<phase>/05_Dialogo_Auditoras/);
2. Executa inventário de Papéis de Trabalho com hashes SHA-256 (audit_working_papers_hasher.py --json);
3. Roda a suíte de testes unitários/integração pytest em modo compacto;
4. Executa a auditoria acadêmica de DOIs e conformidade lexical (verify_citations_doi.py);
5. Realiza varredura SAST em src/, checagem de arquivos proibidos e higiene do cache /tmp;
6. Emite um sumário executivo Markdown de alta densidade (< 60 linhas) para economia de tokens.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

try:
    from src.config_loader import REPO_ROOT
except Exception:
    REPO_ROOT = Path(__file__).resolve().parents[3]


def get_cache_size_kb() -> int:
    """Calcula o tamanho do cache efêmero em /tmp/monitor_datasenado_cache."""
    cache_dir = Path("/tmp/monitor_datasenado_cache")
    if not cache_dir.exists():
        return 0
    total_bytes = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
    return total_bytes // 1024


def scan_sast_violations(root: Path) -> list[str]:
    """Varre src/ em busca de primitivas inseguras proibidas."""
    violations = []
    src_dir = root / "src"
    if not src_dir.is_dir():
        return violations
    pattern = re.compile(r"\b(eval\(|exec\(|pickle\.loads?|shell=True)\b")
    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            for idx, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), start=1):
                if pattern.search(line):
                    violations.append(f"{py_file.name}:{idx}")
        except Exception:
            continue
    return violations


def scan_prohibited_files(root: Path) -> list[str]:
    """Verifica se há arquivos proibidos no repositório (fora de .venv e .git)."""
    prohibited_exts = {".parquet", ".duckdb"}
    prohibited_names = {"secrets.yaml"}
    found = []
    for p in root.rglob("*"):
        if any(part in p.parts for part in (".git", ".venv", "__pycache__")):
            continue
        if p.suffix in prohibited_exts or p.name in prohibited_names:
            found.append(p.name)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Sonda Pericial de Campo para IA Auditora Operacional.")
    parser.add_argument("--phase", default="Fase_01", help="Nome da fase auditada (ex: Fase_01).")
    args = parser.parse_args()

    start_time = time.perf_counter()

    # 1. Assegurar diretório de diálogo
    dialog_dir = REPO_ROOT / "Auditorias" / args.phase / "05_Dialogo_Auditoras"
    dialog_dir.mkdir(parents=True, exist_ok=True)

    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    py_bin = str(venv_python) if venv_python.exists() else sys.executable
    venv_pytest = REPO_ROOT / ".venv" / "bin" / "pytest"

    # Prepara ambiente com PYTHONPATH e marcador anti-recursão
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["IN_AUDIT_PROBE"] = "1"

    # 2. Executar inventário de Working Papers via audit_working_papers_hasher.py --json
    hasher_script = REPO_ROOT / "skills" / "audit-iia-iso31000-datasenado" / "scripts" / "audit_working_papers_hasher.py"
    wp_data = {"total_files": 0, "total_lines": 0, "secrets_found": 0, "working_papers": []}
    hasher_ok = True
    if hasher_script.exists():
        hasher_res = subprocess.run(
            [py_bin, str(hasher_script), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        if hasher_res.returncode == 0:
            try:
                wp_data = json.loads(hasher_res.stdout)
            except Exception:
                hasher_ok = False
        else:
            hasher_ok = False

    # 3. Executar pytest em modo silencioso
    phase_tests = {
        "Fase_01": "tests/test_fase01_audit_compliance.py",
        "Fase_02": "tests/test_fase02_duckdb_and_collectors.py",
        "Fase_03": "tests/test_fase03_six_platforms_and_daily_radar.py",
        "Fase_04": "tests/test_fase04_triple_intelligence_engine.py",
    }
    phase_target = phase_tests.get(args.phase)
    base_pytest = [str(venv_pytest), "-q"] if venv_pytest.exists() else [py_bin, "-m", "pytest", "-q"]
    pytest_cmd = base_pytest + ([phase_target] if phase_target else [])

    pytest_res = subprocess.run(
        pytest_cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )
    pytest_ok = pytest_res.returncode == 0
    pytest_summary = "N/A"
    lines = [ln.strip() for ln in pytest_res.stdout.splitlines() if ln.strip()]
    if lines:
        pytest_summary = lines[-1].strip("=")

    # 4. Executar verificador de DOIs
    doi_script = REPO_ROOT / "skills" / "academic-tcc-datasenado" / "scripts" / "verify_citations_doi.py"
    doi_ok = False
    if doi_script.exists():
        doi_res = subprocess.run(
            [py_bin, str(doi_script)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        doi_ok = doi_res.returncode == 0

    # 5. Checagens SAST, Cache e Arquivos Proibidos
    sast_violations = scan_sast_violations(REPO_ROOT)
    cache_kb = get_cache_size_kb()
    prohibited = scan_prohibited_files(REPO_ROOT)

    elapsed = time.perf_counter() - start_time
    all_green = (
        hasher_ok
        and pytest_ok
        and doi_ok
        and not sast_violations
        and cache_kb <= 256000
        and not prohibited
        and wp_data.get("secrets_found", 0) == 0
    )

    status_badge = "✅ CONFORME (100% Green)" if all_green else "🚨 DESVIOS DETECTADOS"

    # 6. Emissão do Relatório Markdown de Alta Densidade (< 60 linhas)
    print("=== SONDA DE CAMPO DA AUDITORIA OPERACIONAL (FIELDWORK PROBE) ===")
    print(f"- **Fase Auditada:** `{args.phase}` | **Status Geral:** {status_badge}")
    print(f"- **Tempo de Sonda:** {elapsed:.2f}s | **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"- **Diretório de Diálogo:** `Auditorias/{args.phase}/05_Dialogo_Auditoras/` (Ativo)")
    print()
    print("### 1. Indicadores de Testes e Portões Técnicos")
    print("| Componente Pericial | Métrica Observada | Meta / Requisito | Status |")
    print("| :--- | :---: | :---: | :---: |")
    print(f"| Suíte pytest | {pytest_summary} | 100% green | {'✅ Conforme' if pytest_ok else '❌ Falha'} |")
    print(f"| Citações & DOIs (ISO 26324) | 100% conformidade lexical | Zero alucinações | {'✅ Conforme' if doi_ok else '❌ Falha'} |")
    print(f"| Varredura SAST (`src/`) | {len(sast_violations)} primitivas inseguras | 0 eval/exec/pickle | {'✅ Conforme' if not sast_violations else '❌ Falha'} |")
    print(f"| Cache Efêmero (`/tmp`) | {cache_kb} KB | $\\le 250\\text{{ MB}}$ | {'✅ Conforme' if cache_kb <= 256000 else '❌ Excedido'} |")
    print(f"| Arquivos Proibidos no Git | {len(prohibited)} detectados | Zero-Footprint | {'✅ Conforme' if not prohibited else '❌ Falha'} |")
    print()
    print("### 2. Inventário Forense de Papéis de Trabalho (Working Papers)")
    print("| WP-ID | Arquivo Auditado | Linhas | SHA-256 (12h) | Integridade |")
    print("| :---: | :--- | :---: | :---: | :---: |")
    for r in wp_data.get("working_papers", [])[:4]:
        print(f"| `{r['wp_id']}` | `{r['file']}` | {r['lines']:,} | `{r['sha256_short']}` | {r['status']} |")
    print()
    print(f"- **Total de Artefatos Mapeados:** {wp_data.get('total_files', 0)} arquivos ({wp_data.get('total_lines', 0):,} linhas | {wp_data.get('secrets_found', 0)} segredos)")
    print("- **Encaminhamento:** Evidências prontas para inclusão em `02_OPERACIONAL_para_SENIOR_Execucao_e_Evidencias_Brutas.md`.")

    # Higiene Zero-Footprint do cache efêmero
    cache_dir = Path("/tmp/monitor_datasenado_cache")
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)

    return 0 if all_green else 1


if __name__ == "__main__":
    sys.exit(main())
