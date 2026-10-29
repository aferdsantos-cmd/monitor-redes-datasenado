"""
Testes Automatizados da Arquitetura de Skills On-Demand e Eficiência Cognitiva.

Valida a conformidade da estrutura de skills, limites de tokens (Progressive Disclosure),
resolução de links relativos, os 5 Pilares Acadêmicos, execução do verificador de DOIs,
o mapeador sintático AST, o profiler de metadados estatísticos e a interoperabilidade R
conforme OS_Fase00_Skills_v4_Upgrade_Estatistica_Econometria_R_Python.
"""

from pathlib import Path
import re
import json
import os
import subprocess
import sys
import yaml
import pytest

from src.config_loader import REPO_ROOT

EXPECTED_SKILLS = [
    "eng-python-zero-footprint",
    "stats-inference-datasenado",
    "academic-tcc-datasenado",
    "brain-operator-protocol",
    "audit-iia-iso31000-datasenado",
]

EXPECTED_ACADEMIC_REFERENCES = [
    "epistemic_boundaries.md",
    "imrad_writing_and_norms.md",
    "scientific_viz_and_mixed_methods.md",
    "ethics_conep_and_reviewer2_protocol.md",
    "datasenado_report_template.md",
]

EXPECTED_ENG_REFERENCES = [
    "zero_footprint_and_security.md",
    "senior_patterns_and_edge_cases.md",
]

EXPECTED_STATS_REFERENCES = [
    "formulas_and_invariants.md",
    "cib_network_thresholds.md",
    "r_and_python_survey_econometrics.md",
]

EXPECTED_AUDIT_REFERENCES = [
    "owners_intent_and_risk_matrix.md",
    "iia_audit_report_template.md",
]


def test_manifest_and_agents_md_exist_and_bounded():
    """Valida a existência do manifesto .agents/skills.json e limites de AGENTS.md."""
    manifest_path = REPO_ROOT / ".agents" / "skills.json"
    assert manifest_path.exists(), f"Manifesto ausente: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert "entries" in manifest_data, "Manifesto deve conter chave 'entries'"
    assert any(entry.get("path") == "skills" for entry in manifest_data["entries"]), (
        "Manifesto deve apontar para o diretório 'skills'"
    )

    agents_md = REPO_ROOT / "AGENTS.md"
    assert agents_md.exists(), f"AGENTS.md ausente: {agents_md}"

    lines = agents_md.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 50, f"AGENTS.md excedeu 50 linhas ({len(lines)} linhas). Reduza para economia de tokens!"


def test_five_skills_directories_exist():
    """Valida a presença das 5 pastas de skills obrigatórias."""
    skills_root = REPO_ROOT / "skills"
    assert skills_root.exists() and skills_root.is_dir(), "Diretório 'skills/' não encontrado"

    for skill_name in EXPECTED_SKILLS:
        skill_dir = skills_root / skill_name
        assert skill_dir.exists() and skill_dir.is_dir(), f"Skill ausente: {skill_dir}"
        assert (skill_dir / "SKILL.md").exists(), f"SKILL.md ausente em {skill_dir}"


def test_skill_frontmatter_and_line_limits():
    """Valida frontmatter YAML obrigatório e teto de linhas por SKILL.md (85 para eng, stats e audit, 95 para academic, 120 demais)."""
    skills_root = REPO_ROOT / "skills"

    for skill_name in EXPECTED_SKILLS:
        skill_md = skills_root / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()

        if skill_name in ("eng-python-zero-footprint", "stats-inference-datasenado", "audit-iia-iso31000-datasenado"):
            max_lines = 85
        elif skill_name == "academic-tcc-datasenado":
            max_lines = 95
        else:
            max_lines = 120

        assert len(lines) <= max_lines, (
            f"{skill_name}/SKILL.md excedeu {max_lines} linhas ({len(lines)} linhas). "
            f"Mantenha o corpo conciso para economia de tokens!"
        )

        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match is not None, f"{skill_name}/SKILL.md não possui frontmatter YAML válido delimitado por ---"

        yaml_content = match.group(1)
        data = yaml.safe_load(yaml_content)

        assert isinstance(data, dict), f"Frontmatter de {skill_name} deve ser um mapeamento YAML"
        assert "name" in data and data["name"] == skill_name, (
            f"Campo 'name' inválido no frontmatter de {skill_name}: esperado '{skill_name}', obtido '{data.get('name')}'"
        )
        assert "description" in data and len(str(data["description"]).strip()) > 20, (
            f"Campo 'description' ausente ou excessivamente curto no frontmatter de {skill_name}"
        )


def test_skill_relative_links_resolve():
    """Garante que todos os links relativos ./references/ e ./scripts/ em SKILL.md apontem para arquivos reais."""
    skills_root = REPO_ROOT / "skills"
    link_pattern = re.compile(r"\[.*?\]\(((?:\./|\.\./)[^)]+)\)")

    for skill_name in EXPECTED_SKILLS:
        skill_dir = skills_root / skill_name
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        links = link_pattern.findall(content)
        assert len(links) > 0, f"{skill_name}/SKILL.md deve conter links para references ou scripts"

        for link in links:
            link_clean = link.split("#")[0]
            target_path = (skill_dir / link_clean).resolve()
            assert target_path.exists(), (
                f"Link quebrado em {skill_name}/SKILL.md: '{link}' -> destino {target_path} não existe!"
            )


def test_verify_gate_script_is_executable_and_portable():
    """Valida se verify_gate.sh existe, é executável e muda para REPO_ROOT antes do pytest."""
    script_path = REPO_ROOT / "skills" / "eng-python-zero-footprint" / "scripts" / "verify_gate.sh"
    assert script_path.exists(), f"Script ausente: {script_path}"
    assert os.access(script_path, os.X_OK), f"Script não possui permissão de execução: {script_path}"

    content = script_path.read_text(encoding="utf-8")
    assert 'REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"' in content, (
        "verify_gate.sh deve computar REPO_ROOT dinamicamente"
    )
    assert 'cd "$REPO_ROOT"' in content, "verify_gate.sh deve executar 'cd \"$REPO_ROOT\"'"

    cd_pos = content.find('cd "$REPO_ROOT"')
    pytest_pos = content.find('pytest')
    assert cd_pos != -1 and pytest_pos != -1 and cd_pos < pytest_pos, (
        "Em verify_gate.sh, 'cd \"$REPO_ROOT\"' deve preceder a execução do pytest para garantir portabilidade!"
    )


def test_academic_skill_five_pillars_modules_exist():
    """Valida a presença de todos os arquivos de referência dos 5 Pilares Científicos e do verificador DOI."""
    academic_dir = REPO_ROOT / "skills" / "academic-tcc-datasenado"
    refs_dir = academic_dir / "references"
    assert refs_dir.exists() and refs_dir.is_dir(), f"Pasta references ausente: {refs_dir}"

    for ref_name in EXPECTED_ACADEMIC_REFERENCES:
        ref_path = refs_dir / ref_name
        assert ref_path.exists(), f"Módulo dos 5 Pilares ausente em references/: {ref_name}"

    script_path = academic_dir / "scripts" / "verify_citations_doi.py"
    assert script_path.exists(), f"Script verify_citations_doi.py ausente: {script_path}"
    assert os.access(script_path, os.X_OK), "verify_citations_doi.py deve ter permissão executável (+x)"


def test_verify_citations_doi_execution_succeeds():
    """Executa o script verify_citations_doi.py e valida que a auditoria aprova com 100% de conformidade."""
    script_path = REPO_ROOT / "skills" / "academic-tcc-datasenado" / "scripts" / "verify_citations_doi.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)

    assert res.returncode == 0, f"verify_citations_doi.py falhou com código {res.returncode}:\n{res.stdout}\n{res.stderr}"
    assert "Auditoria acadêmica e anti-alucinação concluída com 100% de conformidade" in res.stdout, (
        f"Mensagem de sucesso esperada não encontrada na saída:\n{res.stdout}"
    )


def test_eng_senior_skill_modules_exist():
    """Valida a presença dos módulos sênior e referências da skill de engenharia."""
    eng_dir = REPO_ROOT / "skills" / "eng-python-zero-footprint"
    refs_dir = eng_dir / "references"
    assert refs_dir.exists() and refs_dir.is_dir(), f"Pasta references ausente: {refs_dir}"

    for ref_name in EXPECTED_ENG_REFERENCES:
        ref_path = refs_dir / ref_name
        assert ref_path.exists(), f"Módulo sênior ausente em references/: {ref_name}"

    ast_script = eng_dir / "scripts" / "ast_repo_map.py"
    assert ast_script.exists(), f"Script ast_repo_map.py ausente: {ast_script}"
    assert os.access(ast_script, os.X_OK), "ast_repo_map.py deve ter permissão executável (+x)"


def test_ast_repo_map_execution_and_content():
    """Executa ast_repo_map.py e valida velocidade e extração de símbolos chave de src/."""
    script_path = REPO_ROOT / "skills" / "eng-python-zero-footprint" / "scripts" / "ast_repo_map.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=5)

    assert res.returncode == 0, f"ast_repo_map.py falhou:\n{res.stdout}\n{res.stderr}"

    expected_symbols = [
        "LGPDCleanerAndCIBGraphEngine",
        "ObservedUniverseStratifiedSampler",
        "DigitalDiscourseStatisticalEngine",
        "ZeroFootprintStorage",
        "normalize_ascii",
    ]
    for sym in expected_symbols:
        assert sym in res.stdout, f"Símbolo esperado '{sym}' não encontrado no mapa AST gerado:\n{res.stdout}"

    assert "Mapeamento AST concluído com sucesso" in res.stdout


def test_stats_skill_modules_and_r_interoperability_exist():
    """Valida referências de estatística, scripts canônicos de R e seed locking."""
    stats_dir = REPO_ROOT / "skills" / "stats-inference-datasenado"
    refs_dir = stats_dir / "references"
    assert refs_dir.exists() and refs_dir.is_dir(), f"Pasta references ausente: {refs_dir}"

    for ref_name in EXPECTED_STATS_REFERENCES:
        ref_path = refs_dir / ref_name
        assert ref_path.exists(), f"Módulo estatístico ausente em references/: {ref_name}"

    r_doc = refs_dir / "r_and_python_survey_econometrics.md"
    content = r_doc.read_text(encoding="utf-8")
    assert "survey::svydesign" in content, "r_and_python_survey_econometrics.md deve conter 'survey::svydesign'"
    assert "calibrate" in content, "r_and_python_survey_econometrics.md deve conter 'calibrate'"
    assert "svychisq" in content, "r_and_python_survey_econometrics.md deve conter 'svychisq'"
    assert "set.seed(42)" in content, "r_and_python_survey_econometrics.md deve conter 'set.seed(42)'"


def test_dataset_metadata_profiler_execution_and_content():
    """Executa dataset_metadata_profiler.py --demo e valida extração de momentos estatísticos."""
    script_path = REPO_ROOT / "skills" / "stats-inference-datasenado" / "scripts" / "dataset_metadata_profiler.py"
    assert script_path.exists(), f"Script ausente: {script_path}"
    assert os.access(script_path, os.X_OK), "dataset_metadata_profiler.py deve ser executável (+x)"

    res = subprocess.run([sys.executable, str(script_path), "--demo"], capture_output=True, text=True, timeout=5)
    assert res.returncode == 0, f"dataset_metadata_profiler.py falhou:\n{res.stdout}\n{res.stderr}"

    stdout = res.stdout
    assert "skewness" in stdout, "Saída deve conter momento 'skewness'"
    assert "kurtosis" in stdout, "Saída deve conter momento 'kurtosis'"
    assert "shannon_entropy" in stdout, "Saída deve conter 'shannon_entropy'"
    assert "min_expected_cell" in stdout, "Saída deve conter diagnóstico 'min_expected_cell'"
    assert "Metadados extraídos com sucesso" in stdout, "Mensagem de sucesso esperada não encontrada"


def test_audit_iia_skill_modules_and_working_papers_hasher():
    """Valida módulos da skill de auditoria IIA/ISO 31000 e execução do audit_working_papers_hasher.py."""
    audit_dir = REPO_ROOT / "skills" / "audit-iia-iso31000-datasenado"
    refs_dir = audit_dir / "references"
    assert refs_dir.exists() and refs_dir.is_dir(), f"Pasta references ausente: {refs_dir}"

    for ref_name in EXPECTED_AUDIT_REFERENCES:
        ref_path = refs_dir / ref_name
        assert ref_path.exists(), f"Módulo de auditoria ausente em references/: {ref_name}"

    hasher_script = audit_dir / "scripts" / "audit_working_papers_hasher.py"
    assert hasher_script.exists(), f"Script audit_working_papers_hasher.py ausente: {hasher_script}"
    assert os.access(hasher_script, os.X_OK), "audit_working_papers_hasher.py deve ter permissão executável (+x)"

    res = subprocess.run([sys.executable, str(hasher_script)], capture_output=True, text=True, timeout=5)
    assert res.returncode == 0, f"audit_working_papers_hasher.py falhou:\n{res.stdout}\n{res.stderr}"

    stdout = res.stdout
    assert "WP-01" in stdout, "Saída deve conter 'WP-01'"
    assert "SHA-256" in stdout, "Saída deve conter 'SHA-256'"
    assert "src/" in stdout, "Saída deve listar arquivos de 'src/'"
    assert "Íntegro (SHA-256 Validado)" in stdout, "Saída deve indicar status íntegro"

