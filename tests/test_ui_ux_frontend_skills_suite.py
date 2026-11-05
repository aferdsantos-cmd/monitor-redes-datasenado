"""
Suíte de Testes da Arquitetura e Portões das 4 Novas Skills de UI/UX, Front-End, DataViz e Validação Visual.

Valida:
1. Imutabilidade absoluta da Baseline da Fase 01 (16 arquivos WP-01 a WP-16);
2. Estrutura, frontmatter YAML, teto de linhas (<= 85 linhas) e resolução de links;
3. Manuais técnicos aprofundados em references/ (> 45 linhas por manual);
4. Execução das 4 sondas em modo --demo com verificação de saída e 0 KB em /tmp;
5. Testes unitários das travas anti-atalhos (Linter Anti-AI-Slop, Contraste WCAG 2.2,
   Contratos Zod/Nuqs, AST TS/React, ECharts Okabe-Ito, Cobertura 27 UFs e os 4 Portões de QA Visual).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import pytest
import yaml

from src.config_loader import REPO_ROOT
from src.storage.phase_baseline_guard import Phase01BaselineGuard

NEW_UI_UX_FRONTEND_SKILLS = [
    "ui-ux-design-system-and-anti-ai-craft",
    "fe-react-tailwind-radix-architecture",
    "fe-data-viz-grids-maps-and-export",
    "qa-visual-a11y-and-frontend-validator",
]

EXPECTED_NEW_REFERENCES = {
    "ui-ux-design-system-and-anti-ai-craft": [
        "institutional_design_tokens_and_anti_ai_slop.md",
        "data_dense_ux_ergonomics_and_wcag22.md",
    ],
    "fe-react-tailwind-radix-architecture": [
        "radix_react_aria_tailwind_and_framer_motion.md",
        "tanstack_query_nuqs_zod_and_zero_footprint_api.md",
    ],
    "fe-data-viz-grids-maps-and-export": [
        "echarts_visx_statistical_charts_and_bubbles.md",
        "tanstack_table_maps_and_print_docx_export.md",
    ],
    "qa-visual-a11y-and-frontend-validator": [
        "visual_qa_checklist_and_anti_hallucination.md",
        "chrome_devtools_mcp_and_live_ui_inspection.md",
    ],
}

EXPECTED_NEW_SCRIPTS = {
    "ui-ux-design-system-and-anti-ai-craft": "anti_ai_slop_and_design_token_linter.py",
    "fe-react-tailwind-radix-architecture": "frontend_architecture_and_zod_contract_validator.py",
    "fe-data-viz-grids-maps-and-export": "dataviz_echarts_grid_and_print_validator.py",
    "qa-visual-a11y-and-frontend-validator": "visual_ui_and_a11y_quality_gate.py",
}

EXPECTED_DEMO_OUTPUTS = {
    "ui-ux-design-system-and-anti-ai-craft": "Auditoria de Design Tokens e Linter Anti-AI-Slop concluída com 100% de conformidade",
    "fe-react-tailwind-radix-architecture": "Validador de Arquitetura Front-End (React/Radix/Zod/Nuqs/TanStack) concluído com sucesso",
    "fe-data-viz-grids-maps-and-export": "Validador de Visualização Data-Dense (ECharts, TanStack Table, Mapa IBGE 27 UFs e @media print) concluído com sucesso",
    "qa-visual-a11y-and-frontend-validator": "Portão de Qualidade Visual, Acessibilidade WCAG 2.2 e Honestidade Estatística concluído com 100% de conformidade",
}


def _load_module_from_path(module_name: str, file_path: Path) -> Any:
    """Carrega dinamicamente módulo python a partir de caminho absoluto."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Falha ao carregar especificação para {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_phase01_baseline_remains_100_percent_intact():
    """Valida que todos os 16 arquivos da Fase 01 (WP-01 a WP-16) permanecem 100% intocados."""
    guard = Phase01BaselineGuard()
    status = guard.verify_baseline_integrity()
    assert status.is_intact is True, (
        f"Violação da baseline Fase 01! Arquivos divergentes: {status.divergent_files}"
    )


def test_all_four_new_ui_ux_frontend_skills_exist():
    """Valida a presença de todas as 4 novas pastas de skills em skills/."""
    skills_root = REPO_ROOT / "skills"
    assert skills_root.exists() and skills_root.is_dir()

    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        skill_dir = skills_root / skill_name
        assert skill_dir.exists() and skill_dir.is_dir(), f"Pasta de skill ausente: {skill_dir}"
        assert (skill_dir / "SKILL.md").exists(), f"SKILL.md ausente em {skill_dir}"


def test_new_ui_skills_frontmatter_and_line_limits():
    """Valida frontmatter YAML estrito (name, description > 30 chars) e teto de <= 85 linhas."""
    skills_root = REPO_ROOT / "skills"

    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        skill_md = skills_root / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()

        assert len(lines) <= 85, (
            f"{skill_name}/SKILL.md excedeu 85 linhas ({len(lines)} linhas). Respeite o Progressive Disclosure!"
        )

        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match is not None, f"{skill_name}/SKILL.md não possui delimitadores YAML ---"

        data = yaml.safe_load(match.group(1))
        assert isinstance(data, dict), f"Frontmatter de {skill_name} deve ser um dicionário YAML"
        assert data.get("name") == skill_name, f"Campo 'name' inválido no frontmatter de {skill_name}"
        assert "description" in data and len(str(data["description"]).strip()) > 30, (
            f"Campo 'description' ausente ou excessivamente curto (> 30 chars) em {skill_name}"
        )


def test_new_ui_skills_relative_links_and_deep_references():
    """Garante que todos os links relativos em SKILL.md resolvem para referências e scripts reais (> 45 linhas)."""
    skills_root = REPO_ROOT / "skills"
    link_pattern = re.compile(r"\[.*?\]\(((?:\./|\.\./)[^)]+)\)")

    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        skill_dir = skills_root / skill_name
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        links = link_pattern.findall(content)
        assert len(links) >= 2, f"{skill_name}/SKILL.md deve conter links relativos"

        for link in links:
            target_path = (skill_dir / link.split("#")[0]).resolve()
            assert target_path.exists(), f"Link quebrado em {skill_name}: '{link}' -> {target_path} não existe!"

        # Verifica se as duas referências técnicas profundas esperadas possuem > 45 linhas
        refs = EXPECTED_NEW_REFERENCES[skill_name]
        for ref_filename in refs:
            ref_path = skill_dir / "references" / ref_filename
            assert ref_path.exists(), f"Referência ausente: {ref_path}"
            ref_lines = ref_path.read_text(encoding="utf-8").splitlines()
            assert len(ref_lines) > 45, (
                f"{ref_filename} possui apenas {len(ref_lines)} linhas. Requer > 45 linhas de rigor técnico!"
            )


def test_new_ui_skills_anti_shortcut_and_anti_ai_slop_documented():
    """Valida se todas as novas skills possuem seção explícita de práticas anti-atalhos (MUST DO / MUST NOT DO)."""
    skills_root = REPO_ROOT / "skills"

    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        skill_md = skills_root / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        assert "MUST DO" in content and "MUST NOT DO" in content, (
            f"{skill_name}/SKILL.md deve conter seção anti-atalhos 'MUST DO / MUST NOT DO'"
        )
        assert "Matriz de Roteamento" in content or "Roteamento" in content, (
            f"{skill_name}/SKILL.md deve conter seção de roteamento de competências"
        )


def test_agents_md_and_existing_skills_respect_wp16_bounds():
    """Valida que AGENTS.md, eng-python e academic-tcc foram atualizados respeitando os limites da Fase 01."""
    agents_md = REPO_ROOT / "AGENTS.md"
    eng_md = REPO_ROOT / "skills" / "eng-python-zero-footprint" / "SKILL.md"
    academic_md = REPO_ROOT / "skills" / "academic-tcc-datasenado" / "SKILL.md"

    agents_lines = agents_md.read_text(encoding="utf-8").splitlines()
    eng_lines = eng_md.read_text(encoding="utf-8").splitlines()
    academic_lines = academic_md.read_text(encoding="utf-8").splitlines()

    assert len(agents_lines) <= 50, f"AGENTS.md excedeu 50 linhas ({len(agents_lines)})"
    assert len(eng_lines) <= 85, f"eng-python-zero-footprint/SKILL.md excedeu 85 linhas ({len(eng_lines)})"
    assert len(academic_lines) <= 95, f"academic-tcc-datasenado/SKILL.md excedeu 95 linhas ({len(academic_lines)})"

    agents_content = "\n".join(agents_lines)
    eng_content = "\n".join(eng_lines)
    academic_content = "\n".join(academic_lines)

    # Verifica se as 17 skills estão referenciadas
    assert "Catálogo das 17 Skills do Projeto" in agents_content or "17" in agents_content
    assert "ui-ux-design-system-and-anti-ai-craft" in agents_content
    assert "fe-react-tailwind-radix-architecture" in agents_content
    assert "fe-data-viz-grids-maps-and-export" in agents_content
    assert "qa-visual-a11y-and-frontend-validator" in agents_content

    assert "fe-react-tailwind-radix-architecture" in eng_content
    assert "qa-visual-a11y-and-frontend-validator" in eng_content

    assert "ui-ux-design-system-and-anti-ai-craft" in academic_content
    assert "fe-data-viz-grids-maps-and-export" in academic_content


def test_scripts_executable_permissions():
    """Garante que todas as 4 sondas possuem permissão de execução (+x)."""
    skills_root = REPO_ROOT / "skills"
    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        script_file = EXPECTED_NEW_SCRIPTS[skill_name]
        script_path = skills_root / skill_name / "scripts" / script_file
        assert script_path.exists(), f"Script ausente: {script_path}"
        assert os.access(script_path, os.X_OK), f"Script {script_file} não possui permissão executável (+x)"


@pytest.mark.parametrize("skill_name", NEW_UI_UX_FRONTEND_SKILLS)
def test_new_ui_skills_script_execution_demo(skill_name: str):
    """Executa a sonda de cada uma das 4 novas skills com --demo e valida saída e 0 KB em /tmp."""
    script_file = EXPECTED_NEW_SCRIPTS[skill_name]
    script_path = REPO_ROOT / "skills" / skill_name / "scripts" / script_file

    res = subprocess.run(
        [sys.executable, str(script_path), "--demo"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res.returncode == 0, f"{script_file} falhou com código {res.returncode}:\n{res.stdout}\n{res.stderr}"

    expected_msg = EXPECTED_DEMO_OUTPUTS[skill_name]
    assert expected_msg in res.stdout, f"Mensagem esperada '{expected_msg}' não encontrada na saída de {script_file}"

    # Verificação de 0 KB em /tmp
    cache_dir = Path("/tmp/monitor_datasenado_cache")
    if cache_dir.exists():
        files = list(cache_dir.iterdir())
        assert len(files) == 0, f"Resíduo em {cache_dir} detectado após execução de {script_file}: {files}"


def test_linter_rejects_neon_gradients_emojis_and_validates_contrast():
    """Valida que o linter Anti-AI-Slop detecta gradientes roxos/neon, emojis decorativos e calcula contraste WCAG 2.2."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "ui-ux-design-system-and-anti-ai-craft"
        / "scripts"
        / "anti_ai_slop_and_design_token_linter.py"
    )
    linter_mod = _load_module_from_path("anti_ai_linter_mod", script_path)

    bad_code = """
    <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-3xl backdrop-blur-xl">
        <h2 className="title">🚀 Bem-vindo à nossa plataforma com IA Mágica ✨</h2>
    </div>
    """
    violations = linter_mod.lint_ui_code_anti_ai_slop(bad_code)
    assert len(violations) >= 2, f"Esperadas pelo menos 2 violações no bad_code, obtidas: {violations}"
    assert any("gradiente neon" in v.lower() for v in violations)
    assert any("emoji" in v.lower() for v in violations)

    clean_code = """
    <div className="bg-[#FFFFFF] text-[#0B1A30] border border-[#CBD5E1] rounded-lg p-4">
        <h2 className="text-lg font-serif">Indicadores de Amostragem do DataSenado</h2>
    </div>
    """
    clean_violations = linter_mod.lint_ui_code_anti_ai_slop(clean_code)
    assert len(clean_violations) == 0, f"Código limpo gerou falsos positivos: {clean_violations}"

    # Validação de contraste WCAG 2.2
    contrast_pass = linter_mod.calculate_contrast_ratio("#0B1A30", "#FFFFFF")
    assert contrast_pass > 12.0, f"Contraste entre azul institucional e branco deve ser alto: {contrast_pass}"

    contrast_fail = linter_mod.calculate_contrast_ratio("#999999", "#FFFFFF")
    assert contrast_fail < 4.5, f"Cinza claro sobre branco deve falhar WCAG AA para texto normal: {contrast_fail}"


def test_zod_validator_syncs_nuqs_url_and_blocks_invalid_inputs():
    """Valida se o schema Zod/Pydantic e Nuqs serializa e valida filtros de monitoramento."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "fe-react-tailwind-radix-architecture"
        / "scripts"
        / "frontend_architecture_and_zod_contract_validator.py"
    )
    fe_mod = _load_module_from_path("fe_arch_mod", script_path)

    valid_spec = {
        "theme_id": "reforma_tributaria",
        "window_days": 14,
        "selected_platforms": ["youtube", "whatsapp"],
        "target_sample_size_n": 50,
        "scenario": "C3_RAKING",
        "lexical_search_query": "aliquota unificada",
    }
    is_valid, errors = fe_mod.validate_monitoring_window_spec(valid_spec)
    assert is_valid is True, f"Parâmetros válidos rejeitados: {errors}"

    # Nuqs serialization / parse
    url = fe_mod.serialize_url_query_state(valid_spec)
    assert "theme=reforma_tributaria" in url
    assert "days=14" in url
    parsed = fe_mod.parse_url_query_state(url)
    assert parsed["theme_id"] == "reforma_tributaria"
    assert parsed["window_days"] == 14

    # Neutralidade Lexical M-04 e validação de tema
    invalid_spec = {
        "theme_id": "tema_inexistente",
        "window_days": 180,  # Max 90
        "selected_platforms": ["orkut"],
        "target_sample_size_n": 5,  # Min 10
        "scenario": "INVALIDO",
        "lexical_search_query": "politico ladrao",  # Violação de neutralidade
    }
    is_valid_inj, errors_inj = fe_mod.validate_monitoring_window_spec(invalid_spec)
    assert is_valid_inj is False
    assert len(errors_inj) >= 5
    assert any("Neutralidade" in err for err in errors_inj)


def test_frontend_linter_flags_any_alert_and_localstorage():
    """Valida que o analisador estático de front-end barra 'any', 'alert()' e 'localStorage'."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "fe-react-tailwind-radix-architecture"
        / "scripts"
        / "frontend_architecture_and_zod_contract_validator.py"
    )
    fe_mod = _load_module_from_path("fe_arch_mod_2", script_path)

    bad_ts = """
    function handleAction(event: any) {
        window.alert("Erro no formulário");
        localStorage.setItem("user_token", "secret123");
        return <div onClick={() => {}} className="btn">Clique</div>;
    }
    """
    violations = fe_mod.lint_frontend_architecture_code(bad_ts)
    assert len(violations) >= 3
    assert any("any" in v for v in violations)
    assert any("alert" in v for v in violations)
    assert any("localStorage" in v for v in violations)


def test_echarts_validator_enforces_ic95_okabe_ito_and_blocks_3d_pie():
    """Valida se a especificação ECharts exige paleta Okabe-Ito, IC 95% e bloqueia gráficos de pizza e 3D."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "fe-data-viz-grids-maps-and-export"
        / "scripts"
        / "dataviz_echarts_grid_and_print_validator.py"
    )
    dv_mod = _load_module_from_path("dataviz_mod", script_path)

    bad_pie_spec = {
        "universalTransition": {"enabled": True},
        "color": ["#0072b2", "#d55e00"],
        "series": [
            {"type": "pie", "name": "Distribuicao", "data": [1, 2, 3, 4, 5]}
        ]
    }
    is_valid_pie, errs_pie = dv_mod.validate_echarts_options_schema(bad_pie_spec)
    assert is_valid_pie is False
    assert any("pizza" in err.lower() for err in errs_pie)

    bad_color_spec = {
        "universalTransition": {"enabled": True},
        "color": ["#8A2BE2", "#00FFFF"],
        "series": [
            {"type": "bar", "name": "Votos", "data": [10, 20]},
            {"type": "custom", "name": "IC95", "data": [[0, 41, 49]]},
        ],
    }
    is_valid_color, errs_color = dv_mod.validate_echarts_options_schema(bad_color_spec)
    assert is_valid_color is False
    assert any("okabe-ito" in err.lower() for err in errs_color)

    good_spec = {
        "universalTransition": {"enabled": True},
        "color": ["#0072B2", "#D55E00", "#999999"],
        "series": [
            {"type": "bar", "name": "Favorável", "data": [45]},
            {"type": "custom", "name": "IC 95%", "data": [[0, 41, 49]]},
        ],
    }
    is_valid_good, errs_good = dv_mod.validate_echarts_options_schema(good_spec)
    assert is_valid_good is True, f"Especificação conforme foi rejeitada: {errs_good}"


def test_dataviz_validator_enforces_27_ufs_and_k_anonymity_masking():
    """Valida checagem de integridade das 27 UFs brasileiras e mascaramento de células n < 5."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "fe-data-viz-grids-maps-and-export"
        / "scripts"
        / "dataviz_echarts_grid_and_print_validator.py"
    )
    dv_mod = _load_module_from_path("dataviz_mod_2", script_path)

    # Incompleto (faltando DF e AC)
    all_ufs = [
        "AL", "AP", "AM", "BA", "CE", "ES", "GO", "MA",
        "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
    ]
    is_ok, errs = dv_mod.validate_brazilian_uf_mesh(all_ufs)
    assert is_ok is False
    assert any("DF" in e for e in errs)
    assert any("AC" in e for e in errs)

    complete_ufs = all_ufs + ["AC", "DF"]
    is_complete, errs_c = dv_mod.validate_brazilian_uf_mesh(complete_ufs)
    assert is_complete is True, f"27 UFs completas foram rejeitadas: {errs_c}"

    # Mascaramento k-anonimato (k=5) e truncamento de hash
    sample_rows = [
        {"stratum_label": "SP", "unique_accounts_count": 1500, "author_id_hash": "a1b2c3d4e5f67890abcdef"},
        {"stratum_label": "RR", "unique_accounts_count": 3, "author_id_hash": "1234567890abcdef"},
        {"stratum_label": "DF", "unique_accounts_count": 120, "author_id_hash": "short"},
    ]
    masked = dv_mod.apply_table_k_anonymity_masking(sample_rows, min_k=5)
    assert masked[0]["unique_accounts_count"] == 1500
    assert masked[0]["author_id_hash"].endswith("...")
    assert masked[1]["unique_accounts_count"] == "<5"
    assert masked[1]["stratum_label"] == "OUTROS_ANONIMIZADO_LGPD_K5"
    assert masked[2]["unique_accounts_count"] == 120

    # Validação de @media print
    css = """
    @media print {
        @page { size: A4 portrait; margin: 12mm; }
        .no-print { display: none !important; }
        .chart-box { break-inside: avoid; }
    }
    """
    css_valid, css_errs = dv_mod.validate_media_print_stylesheet(css)
    assert css_valid is True, f"CSS válido reprovado: {css_errs}"


def test_visual_qa_quality_gate_evaluates_four_gates():
    """Valida a avaliação dos 4 portões de qualidade visual (Design, A11y, Performance, Estatística)."""
    script_path = (
        REPO_ROOT
        / "skills"
        / "qa-visual-a11y-and-frontend-validator"
        / "scripts"
        / "visual_ui_and_a11y_quality_gate.py"
    )
    qa_mod = _load_module_from_path("qa_mod", script_path)

    compliant_bundle = {
        "css_classes": ["bg-white", "dark:bg-slate-900", "border-slate-200", "tabular-nums", "rounded-lg"],
        "header_titles": ["Bancada Analítica DataSenado", "Monitoramento Temático de Opinião Pública"],
        "has_statistical_numbers": True,
        "has_tabular_nums": True,
        "color_pairs": [
            {"name": "Texto Primário", "fg": "#0B1A30", "bg": "#FFFFFF", "min_cr": 4.5},
            {"name": "Favorável Okabe-Ito", "fg": "#0072B2", "bg": "#FFFFFF", "min_cr": 4.5},
        ],
        "async_containers": [
            {"id": "grafico_prevalencia", "has_matching_skeleton": True, "has_reserved_height": True},
        ],
        "uses_full_page_reload": False,
        "statistical_ui_metadata": {
            "declares_sample_size_n": True,
            "declares_organic_universe_N": True,
            "renders_opinion_chart": True,
            "renders_ic95_error_bands": True,
            "scenario_labels": ["Cenário 3 — Raking IPF"],
        },
        "exposes_raw_author_ids": False,
        "exposes_cells_with_k_less_than_5": False,
    }
    report = qa_mod.evaluate_visual_quality_gates(compliant_bundle)
    assert report["status"] == "PASS"
    assert report["conformance_score"] == "100.0%"

    non_compliant_bundle = {
        "css_classes": ["bg-gradient-to-r", "from-purple-500", "shadow-indigo-500", "rounded-3xl card"],
        "header_titles": ["Painel Mágico ✨", "Dashboard de IA 🚀"],
        "has_statistical_numbers": True,
        "has_tabular_nums": False,
        "color_pairs": [
            {"name": "Texto Fraco", "fg": "#999999", "bg": "#FFFFFF", "min_cr": 4.5},
        ],
        "async_containers": [
            {"id": "container_pesado", "has_matching_skeleton": False, "has_reserved_height": False},
        ],
        "uses_full_page_reload": True,
        "statistical_ui_metadata": {
            "declares_sample_size_n": False,
            "declares_organic_universe_N": False,
            "renders_opinion_chart": True,
            "renders_ic95_error_bands": False,
            "scenario_labels": [],
        },
        "exposes_raw_author_ids": True,
        "exposes_cells_with_k_less_than_5": True,
    }
    fail_report = qa_mod.evaluate_visual_quality_gates(non_compliant_bundle)
    assert fail_report["status"] == "FAIL"
    assert fail_report["conformance_score"] == "0.0%"
    assert all(g["passed"] is False for g in fail_report["gates"].values())


def test_no_pickle_in_frontend_or_dataviz_code():
    """Garante que nenhum script ou referência técnica de front-end recomenda ou usa 'pickle'."""
    skills_root = REPO_ROOT / "skills"
    for skill_name in NEW_UI_UX_FRONTEND_SKILLS:
        skill_dir = skills_root / skill_name
        for file_path in skill_dir.rglob("*.py"):
            content = file_path.read_text(encoding="utf-8")
            assert "import pickle" not in content, f"Uso proibido de pickle detectado em {file_path}"
            assert "pickle.dump" not in content, f"Uso proibido de pickle.dump detectado em {file_path}"
            assert "pickle.load" not in content, f"Uso proibido de pickle.load detectado em {file_path}"
