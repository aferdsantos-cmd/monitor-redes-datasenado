"""
Suíte Oficial de Testes da Fase 05 — Bancada Analítica Data-Dense, Conciliação do Protótipo e Validação Visual.

Valida:
1. Imutabilidade absoluta da Baseline da Fase 01 (16 arquivos congelados em config/fase01_baseline_lock.json);
2. Isolamento de diretórios de diálogo (Auditorias/Fase_05/05_Dialogo_Auditoras com 0 arquivos) e higiene de cache;
3. Sincronia exata SHA-256 (100% idêntica) entre datasenado-bancada-360/src/ e src/dashboard/src/;
4. Sondas e Linters Visuais das 4 Skills:
   - anti_ai_slop_and_design_token_linter.py (0 violações em 100% dos arquivos front-end);
   - frontend_architecture_and_zod_contract_validator.py (0 violações arquiteturais e de WAI-ARIA);
   - dataviz_echarts_grid_and_print_validator.py (3 cenários, 27 UFs, @media print e k-anonimato);
   - visual_ui_and_a11y_quality_gate.py (100.0% PASS nos 4 Portões Visuais);
5. Fechamento das 4 Lacunas Operacionais (Categoria C):
   - Lacuna 1: Máquina de Estados do Ciclo de Vida do Monitoramento (7 estados);
   - Lacuna 2: Cadastro de Novo Tema com Trava de Neutralidade Lexical M-04 e settings.yaml intacto;
   - Lacuna 3: Gestão de Sessões e Credenciais das 6 Redes (mascaramento Zero-Footprint e handshake);
   - Lacuna 4: Alertas operacionais de Rate Limit (HTTP 429) e Sub-representação Amostral Regional (n < 15);
6. Geração ponta a ponta dos datasets da bancada para os 3 temas oficiais e tema customizado dinâmico.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List
import pytest

from src.config_loader import REPO_ROOT
from src.storage.phase_baseline_guard import Phase01BaselineGuard

# Adiciona scripts das skills ao path
SKILLS_DIR = REPO_ROOT / "skills"
sys.path.append(str(SKILLS_DIR / "ui-ux-design-system-and-anti-ai-craft" / "scripts"))
sys.path.append(str(SKILLS_DIR / "fe-react-tailwind-radix-architecture" / "scripts"))
sys.path.append(str(SKILLS_DIR / "fe-data-viz-grids-maps-and-export" / "scripts"))
sys.path.append(str(SKILLS_DIR / "qa-visual-a11y-and-frontend-validator" / "scripts"))

from anti_ai_slop_and_design_token_linter import (
    lint_ui_code_anti_ai_slop,
    audit_theme_contrast_compliance,
)
from frontend_architecture_and_zod_contract_validator import (
    lint_frontend_architecture_code,
    validate_monitoring_window_spec,
    parse_url_query_state,
    serialize_url_query_state,
)
from dataviz_echarts_grid_and_print_validator import (
    validate_echarts_options_schema,
    validate_brazilian_uf_mesh,
    validate_media_print_stylesheet,
)
from visual_ui_and_a11y_quality_gate import (
    evaluate_visual_quality_gates,
    verify_gate1_anti_ai_slop_and_typography,
    verify_gate2_wcag_contrast_and_a11y,
    verify_gate3_zero_cls_and_skeletons,
    verify_gate4_statistical_and_lgpd_honesty,
)

from src.ui.connectors_and_credentials_manager import (
    SocialMediaConnectorsSessionManager,
    VALID_PLATFORMS,
)
from src.ui.workbench_api_and_contracts import (
    MonitoringLifecycleStateMachine,
    MonitoringLifecycleState,
    validate_new_theme_registration,
    DataSenadoWorkbenchBackendBridge,
    FORBIDDEN_LEXICAL_TERMS_REGEX,
)
from src.ui.echarts_and_visx_specs_builder import (
    build_three_scenarios_and_rogan_gladen_echarts_spec,
    build_brazilian_27_ufs_choropleth_spec,
    build_bubbles_and_spectra_network_echarts_spec,
    apply_table_k_anonymity_masking,
    OKABE_ITO_PALETTE,
    BRAZIL_27_UFS_SET,
)
from src.ui.frontend_workbench_templates import (
    build_auditable_ui_bundle_from_prototype,
)


@pytest.fixture(autouse=True)
def setup_fase05_lgpd_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configura credencial LGPD HMAC-SHA256 de 64 hexadecimais para testes fail-closed."""
    monkeypatch.setenv(
        "LGPD_HMAC_SECRET_KEY",
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )


# ==============================================================================
# 1. TESTES DE BASELINE, ISOLAMENTO E SINCRONIA SHA-256
# ==============================================================================

class TestBaselineAndZeroFootprint:
    """Garante imutabilidade da Fase 01, ausência de ruído e sincronia do front-end."""

    def test_baseline_lock_16_files_intact(self) -> None:
        """Todos os 16 arquivos protegidos da Fase 01 devem ter seus hashes intactos."""
        guard = Phase01BaselineGuard(REPO_ROOT)
        report = guard.verify_baseline_integrity()
        assert report.is_intact is True, f"Baseline violada: {report}"
        assert report.checked_count == 16
        assert len(report.modified_files) == 0
        assert len(report.missing_files) == 0

    def test_audit_dialogue_directory_is_empty(self) -> None:
        """Auditorias/Fase_05/05_Dialogo_Auditoras deve conter 0 arquivos."""
        dialogue_dir = REPO_ROOT / "Auditorias" / "Fase_05" / "05_Dialogo_Auditoras"
        if dialogue_dir.exists():
            files = [f for f in dialogue_dir.rglob("*") if f.is_file() and not f.name.startswith(".")]
            assert len(files) == 0, f"Encontrados arquivos em 05_Dialogo_Auditoras: {files}"

    def test_cache_directory_zero_footprint(self) -> None:
        """Cache temporário em /tmp/monitor_datasenado_cache não deve exceder 250 MB."""
        cache_dir = Path("/tmp/monitor_datasenado_cache")
        if cache_dir.exists():
            total_bytes = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            assert total_bytes < 250 * 1024 * 1024, f"Cache excedeu teto de 250 MB: {total_bytes} bytes"

    def test_frontend_trees_exact_sha256_synchrony(self) -> None:
        """datasenado-bancada-360/src/ e src/dashboard/src/ devem ter exata paridade bit a bit."""
        dir1 = REPO_ROOT / "datasenado-bancada-360" / "src"
        dir2 = REPO_ROOT / "src" / "dashboard" / "src"
        assert dir1.exists(), f"Diretório {dir1} não existe"
        assert dir2.exists(), f"Diretório {dir2} não existe"

        files1 = sorted([str(p.relative_to(dir1)) for p in dir1.rglob("*") if p.is_file()])
        files2 = sorted([str(p.relative_to(dir2)) for p in dir2.rglob("*") if p.is_file()])
        assert files1 == files2, f"Discrepância na lista de arquivos entre as duas árvores: {set(files1) ^ set(files2)}"

        for rel in files1:
            h1 = hashlib.sha256((dir1 / rel).read_bytes()).hexdigest()
            h2 = hashlib.sha256((dir2 / rel).read_bytes()).hexdigest()
            assert h1 == h2, f"Divergência de hash SHA-256 no arquivo {rel}: {h1} != {h2}"


# ==============================================================================
# 2. TESTES DE DESIGN SYSTEM E LINTER ANTI-AI-SLOP
# ==============================================================================

class TestVisualAndDesignSystemLinters:
    """Verifica cumprimento estrito das regras de Anti-AI-Slop, tokens e contraste."""

    def test_anti_ai_slop_zero_violations_in_frontend(self) -> None:
        """Nenhum arquivo front-end deve conter gradientes neon, rounded-3xl ou ausência de tabular-nums."""
        dir_fe = REPO_ROOT / "datasenado-bancada-360" / "src"
        violations_count = 0
        details: List[str] = []

        for p in dir_fe.rglob("*"):
            if p.suffix in (".tsx", ".ts", ".css"):
                code = p.read_text(encoding="utf-8")
                errs = lint_ui_code_anti_ai_slop(code)
                if errs:
                    violations_count += len(errs)
                    details.append(f"{p.name}: {errs}")

        assert violations_count == 0, f"Violações de Anti-AI-Slop detectadas:\n" + "\n".join(details)

    def test_anti_ai_slop_catches_neon_gradients(self) -> None:
        """Linter deve barrar gradientes roxo/índigo/rosa de IA."""
        bad_code = '<div className="bg-gradient-to-r from-purple-500 to-indigo-600">Card</div>'
        errs = lint_ui_code_anti_ai_slop(bad_code)
        assert len(errs) > 0
        assert any("Gradiente neon" in e for e in errs)

    def test_anti_ai_slop_catches_rounded_3xl_in_cards(self) -> None:
        """Linter deve barrar cantos inflados rounded-3xl em cards ou painéis."""
        bad_code = '<div className="rounded-3xl border p-4 card-indicator">Metrica</div>'
        errs = lint_ui_code_anti_ai_slop(bad_code)
        assert len(errs) > 0
        assert any("rounded-3xl" in e for e in errs)

    def test_anti_ai_slop_catches_emojis_in_headings(self) -> None:
        """Linter deve barrar emojis em cabeçalhos ou botões."""
        bad_code = '<h2>🚀 Painel de Monitoramento</h2>'
        errs = lint_ui_code_anti_ai_slop(bad_code)
        assert len(errs) > 0
        assert any("Emoji informal" in e for e in errs)

    def test_anti_ai_slop_catches_missing_tabular_nums(self) -> None:
        """Linter deve exigir tabular-nums em cabeçalhos ou tabelas exibindo valores com vírgula ou porcentagem."""
        bad_code = '<h2 className="text-lg font-bold">Favorável: 45,9%</h2>'
        errs = lint_ui_code_anti_ai_slop(bad_code)
        assert len(errs) > 0
        assert any("tabular-nums" in e for e in errs)

    def test_theme_contrast_compliance(self) -> None:
        """audit_theme_contrast_compliance deve aprovar as paletas clara, escura e Okabe-Ito."""
        report = audit_theme_contrast_compliance()
        assert report["all_pass"] is True
        assert len(report["details"]) >= 8


# ==============================================================================
# 3. TESTES DE ARQUITETURA FRONT-END E CONTRATOS ZOD
# ==============================================================================

class TestFrontendArchitectureAndContracts:
    """Verifica boas práticas de arquitetura React/TypeScript e contratos Zod."""

    def test_frontend_architecture_zero_violations(self) -> None:
        """Nenhum arquivo front-end deve conter ': any', alert nativo ou div onClick sem ARIA."""
        dir_fe = REPO_ROOT / "datasenado-bancada-360" / "src"
        violations_count = 0
        details: List[str] = []

        for p in dir_fe.rglob("*"):
            if p.suffix in (".tsx", ".ts", ".css"):
                code = p.read_text(encoding="utf-8")
                errs = lint_frontend_architecture_code(code)
                if errs:
                    violations_count += len(errs)
                    details.append(f"{p.name}: {errs}")

        assert violations_count == 0, f"Violações de arquitetura detectadas:\n" + "\n".join(details)

    def test_frontend_architecture_catches_loose_any(self) -> None:
        """Linter deve flagrar tipagem frouxa ': any'."""
        bad_code = "const handleData = (payload: any) => { console.log(payload); };"
        errs = lint_frontend_architecture_code(bad_code)
        assert len(errs) > 0
        assert any("Tipagem frouxa" in e for e in errs)

    def test_frontend_architecture_catches_native_alert(self) -> None:
        """Linter deve proibir window.alert/confirm nativo."""
        bad_code = "window.alert('Operação concluída');"
        errs = lint_frontend_architecture_code(bad_code)
        assert len(errs) > 0
        assert any("diálogo nativo" in e for e in errs)

    def test_frontend_architecture_catches_div_onclick_without_aria(self) -> None:
        """Linter deve exigir role e tabIndex em <div onClick=...>."""
        bad_code = '<div onClick={() => doSomething()}>Clique aqui</div>'
        errs = lint_frontend_architecture_code(bad_code)
        assert len(errs) > 0
        assert any("sem WAI-ARIA" in e for e in errs)

    def test_frontend_architecture_catches_pii_localstorage(self) -> None:
        """Linter deve proibir armazenamento de PII ou datasets em localStorage."""
        bad_code = 'localStorage.setItem("author_post_dataset", JSON.stringify(data));'
        errs = lint_frontend_architecture_code(bad_code)
        assert len(errs) > 0
        assert any("Zero-Footprint" in e for e in errs)

    def test_zod_workbench_theme_filter_schema(self) -> None:
        """Contrato de parâmetros deve validar especificação de filtros e janela."""
        valid_spec = {
            "theme_id": "regulamentacao_ia",
            "window_days": 7,
            "selected_platforms": ["youtube", "telegram", "x"],
            "target_sample_size_n": 550,
            "scenario": "C3_RAKING",
            "lexical_search_query": "inteligencia artificial",
        }
        ok, errs = validate_monitoring_window_spec(valid_spec)
        assert ok is True, f"Erros de validação Zod: {errs}"

        # Teste de serialização e parsing Nuqs
        query_str = serialize_url_query_state(valid_spec)
        parsed = parse_url_query_state(query_str)
        assert parsed["theme_id"] == "regulamentacao_ia"
        assert parsed["window_days"] == 7
        assert "youtube" in parsed["selected_platforms"]

    def test_zod_workbench_theme_filter_rejects_invalid(self) -> None:
        """Contrato Zod deve rejeitar tema desconhecido, janela inválida ou plataformas vazias."""
        invalid_spec = {
            "theme_id": "tema_inexistente_xyz",
            "window_days": 999,
            "selected_platforms": [],
            "target_sample_size_n": 5,
        }
        ok, errs = validate_monitoring_window_spec(invalid_spec)
        assert ok is False
        assert len(errs) >= 3


# ==============================================================================
# 4. TESTES DE DATAVIZ ECHARTS, MALHA 27 UFS E IMPRESSÃO A4
# ==============================================================================

class TestDataVizEchartsGridAndPrint:
    """Verifica conformidade do Apache ECharts, malha das 27 UFs e estilo @media print."""

    def test_echarts_options_schema_pass(self) -> None:
        """Especificação do comparativo de 3 cenários deve ser aprovada."""
        scenarios = [
            {"name": "Cenário 1 — Hájek", "favoravel": 45.0, "contrario": 35.0, "neutro": 20.0, "favoravelCi": [42.0, 48.0], "contrarioCi": [32.0, 38.0], "neutroCi": [17.0, 23.0]},
            {"name": "Cenário 2 — Equiponderado", "favoravel": 44.0, "contrario": 36.0, "neutro": 20.0, "favoravelCi": [41.0, 47.0], "contrarioCi": [33.0, 39.0], "neutroCi": [17.0, 23.0]},
            {"name": "Cenário 3 — Raking IPF", "favoravel": 46.0, "contrario": 34.0, "neutro": 20.0, "favoravelCi": [43.0, 49.0], "contrarioCi": [31.0, 37.0], "neutroCi": [17.0, 23.0]},
        ]
        spec = build_three_scenarios_and_rogan_gladen_echarts_spec(scenarios)
        ok, errs = validate_echarts_options_schema(spec)
        assert ok is True, f"Erros na especificação ECharts: {errs}"

    def test_echarts_rejects_pie_over_three_slices(self) -> None:
        """Validador deve rejeitar gráficos de pizza com mais de 3 fatias."""
        bad_spec = {
            "series": [
                {
                    "type": "pie",
                    "data": [{"value": 10}, {"value": 20}, {"value": 30}, {"value": 40}],
                }
            ]
        }
        ok, errs = validate_echarts_options_schema(bad_spec)
        assert ok is False
        assert any("pizza" in e.lower() for e in errs)

    def test_echarts_rejects_missing_error_bands(self) -> None:
        """Gráficos com barras ou linhas devem exigir bandas de erro IC 95%."""
        bad_spec = {
            "series": [
                {"type": "bar", "name": "Estimativa", "data": [45, 35, 20]}
            ]
        }
        ok, errs = validate_echarts_options_schema(bad_spec)
        assert ok is False
        assert any("intervalo de confiança" in e.lower() or "ic 95%" in e.lower() for e in errs)

    def test_brazilian_27_ufs_mesh_pass(self) -> None:
        """Especificação do mapa de calor deve cobrir exatamente as 27 UFs."""
        geo_spec = build_brazilian_27_ufs_choropleth_spec()
        ok, errs = validate_brazilian_uf_mesh(geo_spec["ufs"])
        assert ok is True, f"Erros na malha das 27 UFs: {errs}"

    def test_brazilian_uf_mesh_detects_missing_ufs(self) -> None:
        """Validador deve rejeitar malha incompleta."""
        incomplete = ["SP", "RJ", "MG", "BA"]
        ok, errs = validate_brazilian_uf_mesh(incomplete)
        assert ok is False
        assert any("incompleta" in e.lower() for e in errs)

    def test_brazilian_uf_mesh_detects_invalid_ufs(self) -> None:
        """Validador deve rejeitar UFs fictícias."""
        with_invalid = list(BRAZIL_27_UFS_SET) + ["XX", "ZZ"]
        ok, errs = validate_brazilian_uf_mesh(with_invalid)
        assert ok is False
        assert any("inválidas" in e.lower() for e in errs)

    def test_media_print_stylesheet_pass(self) -> None:
        """datasenado-bancada-360/src/index.css deve conter @media print A4 completo."""
        css_path = REPO_ROOT / "datasenado-bancada-360" / "src" / "index.css"
        css_text = css_path.read_text(encoding="utf-8")
        ok, errs = validate_media_print_stylesheet(css_text)
        assert ok is True, f"Erros na folha de impressão: {errs}"

    def test_media_print_stylesheet_rejects_missing_a4(self) -> None:
        """Validador deve reprovar CSS sem @page size A4."""
        bad_css = "@media print { .header { display: none; } }"
        ok, errs = validate_media_print_stylesheet(bad_css)
        assert ok is False
        assert any("A4" in e for e in errs)

    def test_k_anonymity_masking_truncates_hash_and_k_less_than_5(self) -> None:
        """apply_table_k_anonymity_masking deve truncar hash HMAC e mascarar células k < 5."""
        records = [
            {"uf": "SP", "unique_accounts_count": 150, "author_id_hash": "a1b2c3d4e5f67890abcdef1234567890"},
            {"uf": "RR", "unique_accounts_count": 3, "author_id_hash": "f0e1d2c3b4a56789fedcba0987654321"},
        ]
        masked = apply_table_k_anonymity_masking(records, min_k=5)
        assert masked[0]["author_id_hash"] == "a1b2c3d4e5..."
        assert masked[0]["unique_accounts_count"] == 150
        assert masked[1]["author_id_hash"] == "f0e1d2c3b4..."
        assert masked[1]["unique_accounts_count"] == "<5"
        assert masked[1]["stratum_label"] == "OUTROS_ANONIMIZADO_LGPD_K5"


# ==============================================================================
# 5. TESTES DO QUALITY GATE VISUAL (4 PORTÕES PASS 100%)
# ==============================================================================

class TestVisualQualityGates:
    """Verifica a execução pericial dos 4 Portões do visual_ui_and_a11y_quality_gate.py."""

    def test_prototype_bundle_passes_all_four_gates_100_percent(self) -> None:
        """Bundle extraído dos arquivos reais do protótipo deve atingir 100.0% PASS."""
        bundle = build_auditable_ui_bundle_from_prototype()
        result = evaluate_visual_quality_gates(bundle)
        assert result["status"] == "PASS", f"Portões falharam: {result}"
        assert result["conformance_score"] == "100.0%"
        assert result["gates"]["gate1_anti_ai_slop_and_typography"]["passed"] is True
        assert result["gates"]["gate2_wcag22_contrast_and_a11y"]["passed"] is True
        assert result["gates"]["gate3_zero_cls_and_skeletons"]["passed"] is True
        assert result["gates"]["gate4_statistical_and_lgpd_honesty"]["passed"] is True

    def test_quality_gates_reject_adversarial_bundle(self) -> None:
        """Bundle defeituoso com violações injetadas deve ser reprovado com FAIL nos 4 Portões."""
        adversarial = {
            "css_classes": ["from-purple-500", "shadow-indigo-500", "rounded-3xl", "panel-box"],
            "header_titles": ["🚀 Título com Emoji"],
            "has_statistical_numbers": True,
            "has_tabular_nums": False,
            "color_pairs": [{"fg": "#94A3B8", "bg": "#FFFFFF", "min_cr": 4.5}],
            "async_containers": [{"id": "chart", "has_matching_skeleton": False, "has_reserved_height": False}],
            "statistical_ui_metadata": {
                "declares_sample_size_n": False,
                "declares_organic_universe_N": False,
                "renders_opinion_chart": True,
                "renders_ic95_error_bands": False,
            },
        }
        res = evaluate_visual_quality_gates(adversarial)
        assert res["status"] == "FAIL"
        assert res["conformance_score"] == "0.0%"
        assert res["gates"]["gate1_anti_ai_slop_and_typography"]["passed"] is False
        assert res["gates"]["gate2_wcag22_contrast_and_a11y"]["passed"] is False
        assert res["gates"]["gate3_zero_cls_and_skeletons"]["passed"] is False
        assert res["gates"]["gate4_statistical_and_lgpd_honesty"]["passed"] is False

    def test_gate1_anti_ai_slop_blocker(self) -> None:
        """Gate 1 deve reprovar código com classes neon."""
        bad_b = {"css_classes": ["from-indigo-600"], "header_titles": []}
        ok, errs = verify_gate1_anti_ai_slop_and_typography(bad_b)
        assert ok is False
        assert any("Gradientes neon" in e for e in errs)

    def test_gate2_wcag22_contrast_blocker(self) -> None:
        """Gate 2 deve reprovar contraste abaixo de 4.5:1."""
        bad_b = {"color_pairs": [{"fg": "#777777", "bg": "#888888", "min_cr": 4.5, "name": "cinza sobre cinza"}]}
        ok, errs = verify_gate2_wcag_contrast_and_a11y(bad_b)
        assert ok is False
        assert any("Contraste insuficiente" in e for e in errs)

    def test_gate3_zero_cls_skeleton_blocker(self) -> None:
        """Gate 3 deve reprovar container assíncrono sem Skeleton estrutural."""
        bad_b = {"async_containers": [{"id": "radar", "has_matching_skeleton": False, "has_reserved_height": False}]}
        ok, errs = verify_gate3_zero_cls_and_skeletons(bad_b)
        assert ok is False
        assert any("sem Skeleton" in e for e in errs)

    def test_gate4_statistical_and_lgpd_honesty_blocker(self) -> None:
        """Gate 4 deve reprovar omissão de n e N_org."""
        bad_b = {"statistical_ui_metadata": {"declares_sample_size_n": False, "declares_organic_universe_N": False}}
        ok, errs = verify_gate4_statistical_and_lgpd_honesty(bad_b)
        assert ok is False
        assert any("amostra" in e for e in errs)


# ==============================================================================
# 6. TESTES DAS 4 LACUNAS OPERACIONAIS (CATEGORIA C)
# ==============================================================================

class TestOperationalGapsBackendAndConnectors:
    """Valida o fechamento completo das 4 Lacunas Operacionais identificadas no protótipo."""

    def test_lacuna1_lifecycle_state_machine_initial_state(self) -> None:
        """Lacuna 1: Máquina de estados deve iniciar em CADASTRADO_AGUARDANDO_DISPARO (0%)."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_teste")
        assert sm.current_state == MonitoringLifecycleState.CADASTRADO_AGUARDANDO_DISPARO
        assert sm.progress_percentage == 0
        assert len(sm.history) == 1

    def test_lacuna1_lifecycle_state_machine_transitions_all_seven_states(self) -> None:
        """Lacuna 1: Deve permitir transição sequencial auditável pelos 7 estados."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_teste")
        expected_seq = [
            (MonitoringLifecycleState.VALIDANDO_SESSOES_CONECTORES, 15),
            (MonitoringLifecycleState.COLETA_EM_ANDAMENTO_6_REDES, 45),
            (MonitoringLifecycleState.DESCONTAMINACAO_SILVER_CIB_SPAM, 70),
            (MonitoringLifecycleState.CALIBRACAO_RAKING_IPF_ROGAN_GLADEN, 90),
            (MonitoringLifecycleState.PRONTO_PARA_ANALISE_E_BOLETIM, 100),
        ]
        for st, pct in expected_seq:
            res = sm.transition_to(st, details={"etapa": st})
            assert res["status"] == st
            assert res["progress_percent"] == pct

        # Teste de estado de contingência
        alert_res = sm.transition_to(MonitoringLifecycleState.ALERTA_OPERACIONAL_BACKOFF_OU_CREDENCIAIS, details={"motivo": "HTTP 429"})
        assert alert_res["status"] == MonitoringLifecycleState.ALERTA_OPERACIONAL_BACKOFF_OU_CREDENCIAIS
        assert len(sm.history) == 7

    def test_lacuna1_lifecycle_advance_or_run(self) -> None:
        """Lacuna 1: advance_or_run_monitoring_lifecycle deve executar o ciclo completo."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_auto")
        summary = sm.advance_or_run_monitoring_lifecycle(target_state=MonitoringLifecycleState.PRONTO_PARA_ANALISE_E_BOLETIM)
        assert summary["theme_id"] == "tema_auto"
        assert summary["final_state"] == MonitoringLifecycleState.PRONTO_PARA_ANALISE_E_BOLETIM
        assert summary["progress_percent"] == 100
        assert len(summary["event_log"]) >= 5

    def test_lacuna2_theme_registration_success(self) -> None:
        """Lacuna 2: Cadastro válido com termos neutros deve ser aprovado."""
        valid_payload = {
            "theme_id": "pec_seguranca_publica",
            "name": "PEC da Segurança Pública e Integração Policial",
            "senate_committee": "CSP",
            "window_days": 15,
            "target_sample_size_n": 550,
            "selected_platforms": ["youtube", "x_twitter", "telegram"],
            "collection_query_terms": ["seguranca publica", "integracao policial", "pec seguranca"],
            "legislative_context": "Audiência pública marcada na CSP.",
        }
        validated = validate_new_theme_registration(valid_payload)
        assert validated["theme_id"] == "pec_seguranca_publica"
        assert validated["senate_committee"] == "CSP"
        assert len(validated["collection_query_terms"]) == 3

    def test_lacuna2_theme_registration_blocks_forbidden_terms_rule_m04(self) -> None:
        """Lacuna 2: Validador deve barrar termos valorativos/polarizados conforme Regra M-04."""
        forbidden_samples = [
            "pec da policia contra corruptos",
            "projeto contra o genocida",
            "apoio ao mito no senado",
            "ladrao de verbas publicas",
            "traidor da constituicao",
            "golpistas no congresso",
            "parlamentar vendido",
        ]
        for term in forbidden_samples:
            payload = {
                "theme_id": "teste_bloqueio",
                "name": f"Monitoramento sobre {term}",
                "senate_committee": "CCJ",
                "collection_query_terms": [term],
            }
            with pytest.raises(ValueError) as excinfo:
                validate_new_theme_registration(payload)
            assert "M-04" in str(excinfo.value)
            assert "Neutralidade Lexical" in str(excinfo.value)

    def test_lacuna2_theme_registration_does_not_modify_settings_yaml(self) -> None:
        """Lacuna 2: O cadastro dinâmico não deve alterar config/settings.yaml (hash afb2d506fe9f)."""
        settings_path = REPO_ROOT / "config" / "settings.yaml"
        initial_hash = hashlib.sha256(settings_path.read_bytes()).hexdigest()
        assert initial_hash.startswith("afb2d506fe9f"), f"settings.yaml já começou alterado: {initial_hash}"

        bridge = DataSenadoWorkbenchBackendBridge(REPO_ROOT)
        bridge.register_custom_theme({
            "theme_id": "tema_dinamico_sem_disco",
            "name": "Reforma Tributária e Imposto Seletivo",
            "senate_committee": "CAE",
            "collection_query_terms": ["imposto seletivo", "reforma tributaria"],
        })

        after_hash = hashlib.sha256(settings_path.read_bytes()).hexdigest()
        assert after_hash == initial_hash, "Violação de Imutabilidade: settings.yaml foi modificado pelo cadastro!"

    def test_lacuna3_connectors_manager_six_platforms_health(self) -> None:
        """Lacuna 3: Gerenciador de conectores deve monitorar as 6 plataformas oficiais."""
        mgr = SocialMediaConnectorsSessionManager()
        health_data = mgr.get_all_connectors_health_and_sessions()
        connectors = health_data["connectors"]
        assert len(connectors) == 6
        assert health_data["total_platforms"] == 6
        for plat in VALID_PLATFORMS:
            assert plat in connectors
            info = connectors[plat]
            assert "status" in info
            assert info["jitter_min_seconds"] >= 3.0
            assert info["jitter_max_seconds"] <= 10.0
            assert info["fail_closed_hmac_active"] is True

    def test_lacuna3_connectors_secret_masking_zero_footprint(self) -> None:
        """Lacuna 3: Nenhuma credencial bruta pode ser retornada em texto claro."""
        mgr = SocialMediaConnectorsSessionManager()
        res = mgr.validate_and_update_session_credentials("x_twitter", {
            "auth_token": "super_secret_auth_token_value_12345",
            "ct0": "secret_ct0_value_67890",
        })
        assert res["status"] == "CONECTADO_HTTP_200"
        masked = res["updated_credentials"]["ct0"]
        assert "secret_ct0" not in masked
        assert "MASCARADO_LGPD_SEC" in masked

    def test_lacuna3_connectors_handshake_tests(self) -> None:
        """Lacuna 3: test_connector_handshake deve validar conectividade com jitter."""
        mgr = SocialMediaConnectorsSessionManager()
        for plat in ["youtube", "telegram", "x_twitter", "instagram_facebook", "tiktok", "whatsapp"]:
            handshake = mgr.test_connector_handshake(plat)
            assert handshake["platform_id"] == plat
            assert handshake["http_code"] in (200, 401, 403, 429)
            assert handshake["handshake_success"] is True

    def test_lacuna4_simulate_rate_limit_and_subrepresentation_alerts(self) -> None:
        """Lacuna 4: Deve gerar alertas de backoff HTTP 429 e sub-representação amostral regional (n < 15)."""
        mgr = SocialMediaConnectorsSessionManager()
        mgr.test_connector_handshake("instagram_facebook", force_simulated_outcome=429)
        regional_counts = {
            "Sudeste": 320,
            "Nordeste": 140,
            "Sul": 90,
            "Centro-Oeste": 45,
            "Norte": 12,  # Sub-representado: n = 12 < 15
        }
        alerts = mgr.simulate_rate_limit_and_subrepresentation_alerts(
            platform_id="instagram_facebook",
            region_counts=regional_counts,
        )
        assert alerts["has_alerts"] is True
        assert alerts["alerts_count"] >= 2
        alert_types = [a["type"] for a in alerts["alerts"]]
        assert "RATE_LIMIT_BACKOFF_ACTIVE" in alert_types
        assert "SUBREPRESENTACAO_AMOSTRAL_REGIONAL" in alert_types
        sub_alert = next(a for a in alerts["alerts"] if a["type"] == "SUBREPRESENTACAO_AMOSTRAL_REGIONAL")
        assert sub_alert["region"] == "Norte"
        assert sub_alert["observed_count"] == 12
        assert "Kish" in sub_alert["message"]


# ==============================================================================
# 7. TESTES DA PONTE DE BACKEND E GERAÇÃO DOS DATASETS FRONT-END
# ==============================================================================

class TestEndToEndBridgeDatasetGeneration:
    """Valida a integração real entre o front-end e o orquestrador das Fases 01 a 04."""

    def test_bridge_generates_theme_eleicao_presidencia_senado(self) -> None:
        """Bridge deve gerar o ThemeDataset completo para a eleição da presidência do Senado."""
        bridge = DataSenadoWorkbenchBackendBridge(REPO_ROOT)
        dataset = bridge.build_complete_frontend_theme_dataset("eleicao_presidencia_senado", window_spec="7d")
        assert dataset["id"] == "eleicao_presidencia_senado"
        assert dataset["committee"] == "Mesa Diretora"
        assert dataset["medallion"]["goldSampleSize"] == 550
        assert dataset["medallion"]["kishDeff"] > 1.0
        assert len(dataset["scenarios"]) == 5
        assert any(s["scenarioId"] == "rogan_gladen" for s in dataset["scenarios"])
        assert len(dataset["rakingDiagnostics"]) == 5
        assert len(dataset["spectrums"]) == 4
        assert dataset["lifecycleStatus"] == "PRONTO_PARA_ANALISE_E_BOLETIM"
        assert dataset["lifecycleProgressPercent"] == 100

    def test_bridge_generates_theme_pec_escala_6x1(self) -> None:
        """Bridge deve gerar o ThemeDataset para a PEC da Escala 6x1."""
        bridge = DataSenadoWorkbenchBackendBridge(REPO_ROOT)
        dataset = bridge.build_complete_frontend_theme_dataset("pec_escala_6x1", window_spec="7d")
        assert dataset["id"] == "pec_escala_6x1"
        assert dataset["committee"] == "CCJ"
        assert len(dataset["auditRecords"]) > 0
        # Hashes de autor devem estar truncados em 10 caracteres
        for rec in dataset["auditRecords"]:
            assert len(rec["id"]) <= 16
            assert "shapDetails" in rec

    def test_bridge_generates_theme_pl_ia_2338(self) -> None:
        """Bridge deve gerar o ThemeDataset para o PL de Inteligência Artificial 2338."""
        bridge = DataSenadoWorkbenchBackendBridge(REPO_ROOT)
        dataset = bridge.build_complete_frontend_theme_dataset("pl_ia_2338", window_spec="7d")
        assert dataset["id"] == "pl_ia_2338"
        assert dataset["committee"] == "CCT"
        assert dataset["topological"]["modularityObserved"] > 0
        assert len(dataset["bubbleNodes"]) > 0
        assert len(dataset["bubbleEdges"]) > 0

    def test_bridge_generates_custom_registered_theme(self) -> None:
        """Bridge deve gerar ThemeDataset para tema registrado dinamicamente sem poluir disco."""
        bridge = DataSenadoWorkbenchBackendBridge(REPO_ROOT)
        reg_result = bridge.register_custom_theme({
            "theme_id": "marco_hidrogenio_verde",
            "name": "Marco Legal do Hidrogênio de Baixo Carbono",
            "senate_committee": "CMA",
            "window_days": 30,
            "target_sample_size_n": 300,
            "selected_platforms": ["youtube", "telegram", "x_twitter"],
            "collection_query_terms": ["hidrogenio verde", "baixo carbono", "cma senado"],
            "legislative_context": "Regulamentação de incentivos fiscais e transição energética.",
        })
        assert reg_result["theme_id"] == "marco_hidrogenio_verde"

        dataset = bridge.build_complete_frontend_theme_dataset("marco_hidrogenio_verde", window_spec="30d")
        assert dataset["id"] == "marco_hidrogenio_verde"
        assert dataset["committee"] == "CMA"
        assert dataset["medallion"]["goldSampleSize"] == 300
        assert dataset["lifecycleStatus"] in ("PRONTO_PARA_ANALISE_E_BOLETIM", "CADASTRADO_AGUARDANDO_DISPARO")
