"""
Suíte de Testes Automatizados — Fase 05 (v3):
Launcher Único (1-Click), Servidor REST Local, Portões Sequenciais de Aprovação Humana
(Bronze -> Silver -> Gold), Calibração Humana às Cegas, Sandbox e Tratado Metodológico.

Valida os 6 Pilares da Ordem de Serviço OS-FASE05-V3-2026:
1. Atalho Único (1-Click) executável e Servidor REST Local (porta 8765);
2. Telemetria em tempo real, ETA e Alertas de Portão Humano;
3. Portões Sequenciais Estritos de Aprovação Humana e Manipulação de Camadas Medallion;
4. Calibração Humana às Cegas (Rogan-Gladen) e Simulador Passo a Passo (Sandbox);
5. Tratado Metodológico Bilíngue (Leigo vs. Científico) e Limitações Institucionais;
6. Paridade SHA-256 e Imutabilidade da Baseline da Fase 01.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import time
from typing import Any, Dict, List
import urllib.error
import urllib.request

import pytest

from src.config_loader import REPO_ROOT
from src.ui.workbench_api_and_contracts import (
    DataSenadoWorkbenchBackendBridge,
    MonitoringLifecycleStateMachine,
    HumanGateStatus,
)
from src.ui.local_workbench_server import LocalWorkbenchServer


@pytest.fixture(autouse=True)
def ensure_hmac_secret_key() -> None:
    """Garante chave HMAC de 64 hexadecimais para execução de testes sob política fail-closed."""
    key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    os.environ["LGPD_HMAC_SECRET_KEY"] = key


class TestPilar1LauncherAndLocalRestServer:
    """Testes do Pilar 1: Script de 1-Click e Servidor REST Local Zero-Footprint."""

    def test_run_workbench_360_script_exists_and_executable(self) -> None:
        """Verifica se scripts/run_workbench_360.sh existe e possui permissão de execução (+x)."""
        script_path = REPO_ROOT / "scripts" / "run_workbench_360.sh"
        assert script_path.exists(), "scripts/run_workbench_360.sh deve existir"
        st = os.stat(script_path)
        assert bool(st.st_mode & stat.S_IXUSR), "scripts/run_workbench_360.sh deve ter permissão de execução (+x)"
        content = script_path.read_text(encoding="utf-8")
        assert "LGPD_HMAC_SECRET_KEY" in content
        assert "local_workbench_server" in content
        assert "datasenado-bancada-360" in content

    def test_iniciar_bancada_command_exists_and_executable(self) -> None:
        """Verifica se iniciar_bancada_datasenado.command existe na raiz e é executável no macOS."""
        cmd_path = REPO_ROOT / "iniciar_bancada_datasenado.command"
        assert cmd_path.exists(), "iniciar_bancada_datasenado.command deve existir na raiz"
        st = os.stat(cmd_path)
        assert bool(st.st_mode & stat.S_IXUSR), "iniciar_bancada_datasenado.command deve ter permissão de execução (+x)"
        content = cmd_path.read_text(encoding="utf-8")
        assert "run_workbench_360.sh" in content

    def test_vite_proxy_configuration_in_both_trees(self) -> None:
        """Verifica se datasenado-bancada-360 e src/dashboard configuram o proxy /api -> http://127.0.0.1:8765."""
        for tree_path in [
            REPO_ROOT / "datasenado-bancada-360" / "vite.config.ts",
            REPO_ROOT / "src" / "dashboard" / "vite.config.ts",
        ]:
            assert tree_path.exists()
            content = tree_path.read_text(encoding="utf-8")
            assert "/api" in content
            assert "http://127.0.0.1:8765" in content

    def test_local_workbench_server_lifecycle_and_health_endpoint(self) -> None:
        """Testa inicialização do servidor HTTP, endpoint /api/health e CORS preflight OPTIONS."""
        with LocalWorkbenchServer(port=8771) as server:
            time.sleep(0.3)
            # GET /api/health
            req = urllib.request.urlopen("http://127.0.0.1:8771/api/health")
            assert req.status == 200
            data = json.loads(req.read().decode("utf-8"))
            assert data["status"] == "UP"
            assert data["zero_footprint"] is True
            assert data["fail_closed_hmac"] is True
            assert "eleicao_presidencia_senado" in data["themes"]

            # OPTIONS /api/health (CORS)
            opt_req = urllib.request.Request("http://127.0.0.1:8771/api/health", method="OPTIONS")
            with urllib.request.urlopen(opt_req) as opt_res:
                assert opt_res.status == 204
                assert opt_res.headers.get("Access-Control-Allow-Origin") == "*"

    def test_local_workbench_server_themes_and_theme_detail_endpoints(self) -> None:
        """Testa listagem de temas e obtenção do ThemeDataset completo via REST."""
        with LocalWorkbenchServer(port=8772) as server:
            time.sleep(0.3)
            # GET /api/themes
            req = urllib.request.urlopen("http://127.0.0.1:8772/api/themes")
            themes_res = json.loads(req.read().decode("utf-8"))
            assert "themes" in themes_res
            assert len(themes_res["themes"]) >= 3

            # GET /api/themes/eleicao_presidencia_senado
            req2 = urllib.request.urlopen("http://127.0.0.1:8772/api/themes/eleicao_presidencia_senado?window=7d&n=550")
            dataset = json.loads(req2.read().decode("utf-8"))
            assert dataset["id"] == "eleicao_presidencia_senado"
            assert "humanGates" in dataset
            assert "bronzeSampleRecords" in dataset
            assert "silverQuarantineRecords" in dataset
            assert "silverOrganicRecords" in dataset
            assert "goldSampleUnits" in dataset
            assert "blindAuditItems" in dataset
            assert "humanCalibration" in dataset

    def test_local_workbench_server_radar_and_docx_endpoints(self) -> None:
        """Testa endpoints /api/radar e /api/reports/<id>/docx."""
        with LocalWorkbenchServer(port=8773) as server:
            time.sleep(0.3)
            # GET /api/radar
            req = urllib.request.urlopen("http://127.0.0.1:8773/api/radar?window_days=1")
            radar = json.loads(req.read().decode("utf-8"))
            assert "rankedTopics" in radar or "ranked_topics" in radar

            # GET /api/reports/eleicao_presidencia_senado/docx
            req_docx = urllib.request.urlopen("http://127.0.0.1:8773/api/reports/eleicao_presidencia_senado/docx")
            assert req_docx.status == 200
            assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in req_docx.headers.get("Content-Type")
            content = req_docx.read()
            assert len(content) > 1000  # Pacote zip docx válido


class TestPilar3e4HumanGatesAndMedallionManipulation:
    """Testes dos Pilares 3 e 4: Portões Sequenciais Estritos de Aprovação Humana e Manipulação."""

    def test_human_gates_initial_state_and_locks(self) -> None:
        """Verifica que novos temas iniciam com Portão 1 pendente e Portões 2 e 3 bloqueados."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_teste_portoes")
        state = sm.get_state("tema_teste_portoes")
        gates = state["human_gates"]

        assert gates["bronze_gate"]["status"] == HumanGateStatus.PENDENTE_APROVACAO_HUMANA
        assert gates["silver_gate"]["status"] == HumanGateStatus.BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR
        assert gates["gold_gate"]["status"] == HumanGateStatus.BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR

    def test_strict_lock_cannot_advance_to_silver_without_bronze_approval(self) -> None:
        """Tentar avançar para Silver com enforce_human_gates=True sem aprovar Portão Bronze dispara erro ou bloqueio."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_trava_bronze")
        with pytest.raises(ValueError, match="Trava de Portão Humano"):
            sm.set_state("tema_trava_bronze", "DESCONTAMINACAO_SILVER_CIB_SPAM", enforce_human_gates=True)

    def test_strict_lock_cannot_advance_to_gold_without_silver_approval(self) -> None:
        """Tentar avançar para Gold sem aprovação da Camada Silver dispara erro."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_trava_silver")
        # Aprova apenas Bronze
        sm.manipulate_medallion_layer("tema_trava_silver", "approve_gate", {"gate": "bronze"})
        sm.set_state("tema_trava_silver", "DESCONTAMINACAO_SILVER_CIB_SPAM", enforce_human_gates=False)

        with pytest.raises(ValueError, match="Trava de Portão Humano"):
            sm.set_state("tema_trava_silver", "CALIBRACAO_RAKING_IPF_ROGAN_GLADEN", enforce_human_gates=True)

    def test_sequential_approval_unlocks_layers_in_order(self) -> None:
        """Aprovação sequencial Bronze -> Silver -> Gold destrava ordenadamente."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_sequencial")

        # 1. Aprova Bronze
        res1 = sm.manipulate_medallion_layer("tema_sequencial", "approve_gate", {"gate": "bronze"})
        assert res1["human_gates"]["bronze_gate"]["status"] == HumanGateStatus.APROVADO_PELO_ANALISTA
        assert res1["human_gates"]["silver_gate"]["status"] == HumanGateStatus.PENDENTE_APROVACAO_HUMANA

        # 2. Aprova Silver
        res2 = sm.manipulate_medallion_layer("tema_sequencial", "approve_gate", {"gate": "silver"})
        assert res2["human_gates"]["silver_gate"]["status"] == HumanGateStatus.APROVADO_PELO_ANALISTA
        assert res2["human_gates"]["gold_gate"]["status"] == HumanGateStatus.PENDENTE_APROVACAO_HUMANA

        # 3. Aprova Gold
        res3 = sm.manipulate_medallion_layer("tema_sequencial", "approve_gate", {"gate": "gold"})
        assert res3["human_gates"]["gold_gate"]["status"] == HumanGateStatus.APROVADO_PELO_ANALISTA

    def test_cannot_approve_silver_before_bronze(self) -> None:
        """Tentar pular etapa e aprovar Silver diretamente sem Bronze aprovado lança ValueError."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_pulo_etapa")
        with pytest.raises(ValueError, match="Trava Estrita"):
            sm.manipulate_medallion_layer("tema_pulo_etapa", "approve_gate", {"gate": "silver"})

    def test_cannot_approve_gold_before_silver(self) -> None:
        """Tentar pular etapa e aprovar Gold diretamente sem Silver aprovado lança ValueError."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_pulo_gold")
        sm.manipulate_medallion_layer("tema_pulo_gold", "approve_gate", {"gate": "bronze"})
        with pytest.raises(ValueError, match="Trava Estrita"):
            sm.manipulate_medallion_layer("tema_pulo_gold", "approve_gate", {"gate": "gold"})

    def test_bronze_layer_exclude_and_include_noise(self) -> None:
        """Verifica que o analista pode marcar registros como ruído e depois reintegrá-los."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_ruido")
        sm.manipulate_medallion_layer("tema_ruido", "exclude_noise", {"record_id": "rec_ruido_1"})
        state = sm.get_state("tema_ruido")
        assert "rec_ruido_1" in state["human_gates"]["bronze_gate"]["excluded_record_ids"]

        sm.manipulate_medallion_layer("tema_ruido", "include_record", {"record_id": "rec_ruido_1"})
        state2 = sm.get_state("tema_ruido")
        assert "rec_ruido_1" not in state2["human_gates"]["bronze_gate"]["excluded_record_ids"]

    def test_silver_layer_rescue_false_positive_and_quarantine_false_negative(self) -> None:
        """Verifica resgate de falso positivo para orgânico e envio de falso negativo para quarentena."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_silver_audit")
        # Resgata falso positivo
        sm.manipulate_medallion_layer("tema_silver_audit", "override_to_organic", {"record_id": "quar_falso_pos"})
        state = sm.get_state("tema_silver_audit")
        assert "quar_falso_pos" in state["human_gates"]["silver_gate"]["overridden_to_organic_ids"]

        # Envia falso negativo para quarentena
        sm.manipulate_medallion_layer("tema_silver_audit", "override_to_quarantine", {"record_id": "org_falso_neg"})
        state2 = sm.get_state("tema_silver_audit")
        assert "org_falso_neg" in state2["human_gates"]["silver_gate"]["overridden_to_quarantine_ids"]

    def test_gold_layer_resample_updates_seed_and_sample_size(self) -> None:
        """Verifica que resample_gold sorteia nova seed e redefine o Portão 3 para pendente."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_resample")
        res = sm.manipulate_medallion_layer("tema_resample", "resample_gold", {"random_seed": 77, "target_sample_size": 800})
        gold_gate = res["human_gates"]["gold_gate"]
        assert gold_gate["random_seed"] == 77
        assert gold_gate["target_sample_size"] == 800
        assert gold_gate["status"] == HumanGateStatus.PENDENTE_APROVACAO_HUMANA


class TestPilar5BlindHumanAuditAndSandbox:
    """Testes do Pilar 5: Calibração Humana às Cegas e Simulador Passo a Passo."""

    def test_blind_human_audit_recalculates_cohen_kappa_and_rogan_gladen(self) -> None:
        """Rotulagem às cegas pelo humano recalcula a matriz 3x3, Kappa e prevalência corrigida."""
        bridge = DataSenadoWorkbenchBackendBridge()
        # Votação favorável
        metrics = bridge.submit_blind_human_validation("pl_ia_2338", "rec_audit_01", "FAVORAVEL")
        assert "cohen_kappa" in metrics
        assert -1.0 <= metrics["cohen_kappa"] <= 1.0
        assert 0.0 <= metrics["sensitivity"] <= 1.0
        assert 0.0 <= metrics["specificity"] <= 1.0
        assert metrics["total_audited"] >= 1
        assert "last_audit_result" in metrics
        assert metrics["last_audit_result"]["human_stance"] == "FAVORAVEL"

    def test_blind_human_audit_rejects_invalid_stance(self) -> None:
        """Postura inválida dispara ValueError."""
        bridge = DataSenadoWorkbenchBackendBridge()
        with pytest.raises(ValueError, match="Postura humana inválida"):
            bridge.submit_blind_human_validation("pl_ia_2338", "rec_audit_02", "TALVEZ")

    def test_sandbox_executes_all_six_pipeline_stages(self) -> None:
        """O simulador Sandbox executa e retorna detalhadamente os 6 passos matemáticos."""
        bridge = DataSenadoWorkbenchBackendBridge()
        res = bridge.run_sandbox_step_by_step(
            text="Apoio o marco legal de inteligência artificial pelo avanço dos direitos fundamentais @senador",
            platform="x_twitter",
            uf="SP",
            theme_id="pl_ia_2338",
        )

        assert "step1_lgpd" in res
        assert "@usuario_anonimizado" in res["step1_lgpd"]["scrubbed_text"]
        assert len(res["step1_lgpd"]["author_id_hash"]) >= 16

        assert "step2_silver_cib" in res
        assert res["step2_silver_cib"]["verdict"] in ["ORGANICO", "QUARENTENA"]

        assert "step3_feature_engineering" in res
        assert res["step3_feature_engineering"]["token_count"] > 0

        assert "step4_classifier_xai" in res
        assert res["step4_classifier_xai"]["predicted_stance"] in ["FAVORAVEL", "CONTRARIO", "NEUTRO"]
        assert len(res["step4_classifier_xai"]["shap_tokens"]) > 0

        assert "step5_digital_spectrum" in res
        assert "primary_spectrum_id" in res["step5_digital_spectrum"]

        assert "step6_sample_weighting" in res
        assert "rogan_gladen_formula" in res["step6_sample_weighting"]

    def test_sandbox_rejects_empty_text(self) -> None:
        """Simulador rejeita texto vazio com ValueError."""
        bridge = DataSenadoWorkbenchBackendBridge()
        with pytest.raises(ValueError, match="não pode ser vazio"):
            bridge.run_sandbox_step_by_step("")


class TestPilar6MethodologyAndScienceModule:
    """Testes do Pilar 6: Tratado Metodológico Bilíngue, Critérios e Limitações."""

    def test_module6_component_exists_in_both_frontend_trees(self) -> None:
        """Verifica existência de Module6MethodologyAndScience.tsx em ambas as árvores."""
        p1 = REPO_ROOT / "datasenado-bancada-360" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx"
        p2 = REPO_ROOT / "src" / "dashboard" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx"
        assert p1.exists()
        assert p2.exists()
        assert hashlib.sha256(p1.read_bytes()).hexdigest() == hashlib.sha256(p2.read_bytes()).hexdigest()

    def test_module6_covers_all_eight_pipeline_steps(self) -> None:
        """Verifica se o componente cobre as 8 etapas com formulação para leigos e matemáticos."""
        content = (REPO_ROOT / "datasenado-bancada-360" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx").read_text(encoding="utf-8")
        assert "Coleta Neutra e Interoperável" in content
        assert "Pseudonimização Criptográfica LGPD" in content
        assert "Expurgo de Robôs e Spam Comercial" in content
        assert "Princípio \"1 Cidadão = 1 Voz\"" in content
        assert "Amostragem Estratificada de Neyman" in content
        assert "Raking IPF" in content
        assert "Correção Oficial de Rogan-Gladen" in content
        assert "Causalidade de Granger" in content

    def test_module6_covers_key_mathematical_criteria_and_thresholds(self) -> None:
        """Verifica se todos os limiares numéricos chave estão documentados com justificativa."""
        content = (REPO_ROOT / "datasenado-bancada-360" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx").read_text(encoding="utf-8")
        assert "n = 550" in content
        assert "k ≥ 5" in content
        assert "[0.25, 4.00]" in content
        assert "J = Se + Sp - 1 > 0.15" in content
        assert "κ ≥ 0.70" in content
        assert "Jaccard ≥ 0.85" in content
        assert "E-I < -0.40" in content

    def test_module6_includes_scientific_bibliography_with_dois(self) -> None:
        """Verifica inclusão dos artigos seminais com DOIs correspondentes."""
        content = (REPO_ROOT / "datasenado-bancada-360" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx").read_text(encoding="utf-8")
        assert "Meng, Xiao-Li" in content
        assert "10.1214/18-AOAS1185BR" in content
        assert "Rogan, Walter J." in content
        assert "10.1093/oxfordjournals.aje.a112510" in content
        assert "Deming, W. Edwards" in content
        assert "Newman, Mark E. J." in content
        assert "Sweeney, Latanya" in content

    def test_module6_enforces_institutional_honesty_boundaries(self) -> None:
        """Verifica presença em destaque do quadro 'O Que PODE vs. NÃO PODE Afirmar'."""
        content = (REPO_ROOT / "datasenado-bancada-360" / "src" / "components" / "modules" / "Module6MethodologyAndScience.tsx").read_text(encoding="utf-8")
        assert "O Que VOCÊ PODE Afirmar com Rigor Científico" in content
        assert "O Que VOCÊ JAMAIS PODE Afirmar" in content
        assert "NÃO É PESQUISA DA POPULAÇÃO BRASILEIRA" in content
        assert "Raking não elimina viés não-ignorável (MNAR)" in content
        assert "Precedência de Granger não é causa física direta" in content


class TestAchadosCriticosFase05V2Saneados:
    """Testes específicos para os 8 Achados Críticos saneados da Seção 2 do PVQ v2."""

    def test_achado1_dual_contract_human_gates(self) -> None:
        """Achado 1: Contrato expõe chaves camelCase e snake_case simultaneamente."""
        bridge = DataSenadoWorkbenchBackendBridge()
        dataset = bridge.build_complete_frontend_theme_dataset("eleicao_presidencia_senado")
        gates = dataset["humanGates"]
        # Verifica camelCase
        assert "bronzeGate" in gates
        assert "silverGate" in gates
        assert "goldGate" in gates
        assert "randomSeed" in gates["goldGate"]
        assert "targetSampleSize" in gates["goldGate"]
        # Verifica snake_case
        assert "bronze_gate" in gates
        assert "silver_gate" in gates
        assert "gold_gate" in gates
        assert "random_seed" in gates["gold_gate"]

    def test_achado2_and_4_resample_gold_empirical_difference(self) -> None:
        """Achado 2 & 4: Mudar random_seed altera empiricamente unidades amostrais e pesos."""
        bridge = DataSenadoWorkbenchBackendBridge()
        bridge.manipulate_medallion_layer("pec_escala_6x1", "resample_gold", {"random_seed": 42, "target_sample_size": 400})
        ds1 = bridge.build_complete_frontend_theme_dataset("pec_escala_6x1")
        units1 = [u["id"] for u in ds1["goldSampleUnits"]]
        weights1 = [u["rakingWeight"] for u in ds1["goldSampleUnits"]]

        bridge.manipulate_medallion_layer("pec_escala_6x1", "resample_gold", {"random_seed": 777, "target_sample_size": 400})
        ds2 = bridge.build_complete_frontend_theme_dataset("pec_escala_6x1")
        units2 = [u["id"] for u in ds2["goldSampleUnits"]]
        weights2 = [u["rakingWeight"] for u in ds2["goldSampleUnits"]]

        assert units1 != units2, "Unidades amostrais devem ser diferentes para seeds distintas"
        assert weights1 != weights2, "Pesos amostrais devem ser diferentes para seeds distintas"

    def test_achado3_strict_lifecycle_lock_in_backend(self) -> None:
        """Achado 3: Backend recusa avançar ciclo de vida se portão não estiver aprovado."""
        sm = MonitoringLifecycleStateMachine(theme_id="tema_teste_trava_ciclo")
        with pytest.raises(ValueError, match="Trava de Portão Humano"):
            sm.set_state("tema_teste_trava_ciclo", "DESCONTAMINACAO_SILVER_CIB_SPAM", enforce_human_gates=True)

    def test_achado5_fail_closed_import_no_secret_injected_in_module_scope(self) -> None:
        """Achado 5: Importar local_workbench_server não pode poluir escopo com chave HMAC global."""
        # Salva estado atual
        old_val = os.environ.get("LGPD_HMAC_SECRET_KEY")
        if "LGPD_HMAC_SECRET_KEY" in os.environ:
            del os.environ["LGPD_HMAC_SECRET_KEY"]
        try:
            # Reimporta módulo em novo namespace
            import importlib
            import src.ui.local_workbench_server as srv_mod
            importlib.reload(srv_mod)
            assert "LGPD_HMAC_SECRET_KEY" not in os.environ, "Chave HMAC não deve ser gerada no import!"
        finally:
            if old_val:
                os.environ["LGPD_HMAC_SECRET_KEY"] = old_val

    def test_achado6_appsec_dos_and_prototype_pollution(self) -> None:
        """Achado 6: Servidor rejeita payloads > 64KB e protege contra prototype pollution."""
        with LocalWorkbenchServer(port=8774) as server:
            time.sleep(0.3)
            # Payload excessivo (> 65536 bytes)
            big_body = json.dumps({"text": "A" * 70000}).encode("utf-8")
            req_big = urllib.request.Request(
                "http://127.0.0.1:8774/api/sandbox/step-by-step",
                data=big_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(req_big)
            assert exc_info.value.code in (413, 400)

            # Prototype pollution
            proto_body = json.dumps({"__proto__": {"polluted": True}, "text": "teste"}).encode("utf-8")
            req_proto = urllib.request.Request(
                "http://127.0.0.1:8774/api/sandbox/step-by-step",
                data=proto_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as exc_proto:
                urllib.request.urlopen(req_proto)
            assert exc_proto.value.code == 400

    def test_achado7_docx_includes_human_gates_and_boundaries(self) -> None:
        """Achado 7: Relatório Word OOXML inclui Portões Humanos e Fronteiras de Inferência."""
        bridge = DataSenadoWorkbenchBackendBridge()
        docx_buf = bridge.generate_executive_docx_report("eleicao_presidencia_senado")
        docx_bytes = docx_buf.getvalue()
        assert len(docx_bytes) > 1000
        # Inspeção do ZIP/XML
        import io
        import zipfile
        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as zf:
            xml_text = zf.read("word/document.xml").decode("utf-8")
            assert "Portões de Homologação Humana" in xml_text or "Portões" in xml_text
            assert "Fronteiras de Inferência" in xml_text or "O QUE ESTE MONITORAMENTO AFIRMA" in xml_text

    def test_achado8_custom_theme_registration_and_end_to_end_endpoints(self) -> None:
        """Achado 8: Novo tema personalizado é registrado e opera em todas as rotas."""
        with LocalWorkbenchServer(port=8775) as server:
            time.sleep(0.3)
            reg_body = json.dumps({
                "id": "pl_4173_ciberseguranca",
                "title": "PL 4.173 Cibersegurança e Infraestruturas Críticas",
                "committee": "CCT",
                "queries": ["cibersegurança", "infraestrutura crítica", "PL 4173"],
            }).encode("utf-8")

            req_reg = urllib.request.Request(
                "http://127.0.0.1:8775/api/themes/register",
                data=reg_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req_reg) as res:
                assert res.status == 201
                data = json.loads(res.read().decode("utf-8"))
                assert data["id"] == "pl_4173_ciberseguranca"
                assert data["humanGates"]["bronzeGate"]["status"] == "PENDENTE_APROVACAO_HUMANA"

            # Consulta o tema recém-criado
            req_get = urllib.request.urlopen("http://127.0.0.1:8775/api/themes/pl_4173_ciberseguranca")
            assert req_get.status == 200
            theme_data = json.loads(req_get.read().decode("utf-8"))
            assert theme_data["title"] == "PL 4.173 Cibersegurança e Infraestruturas Críticas"


class TestParityAndGovernance:
    """Testes de Paridade SHA-256 e Preservação da Baseline."""

    def test_frontend_exact_sha256_synchrony_across_all_files(self) -> None:
        """Garante 100% de paridade SHA-256 entre datasenado-bancada-360/src e src/dashboard/src."""
        dir1 = REPO_ROOT / "datasenado-bancada-360" / "src"
        dir2 = REPO_ROOT / "src" / "dashboard" / "src"

        for p1 in dir1.rglob("*"):
            if p1.is_file():
                rel = p1.relative_to(dir1)
                p2 = dir2 / rel
                assert p2.exists(), f"Arquivo espelho ausente em src/dashboard/src: {rel}"
                h1 = hashlib.sha256(p1.read_bytes()).hexdigest()
                h2 = hashlib.sha256(p2.read_bytes()).hexdigest()
                assert h1 == h2, f"Discrepância SHA-256 no arquivo: {rel}"

    def test_dialogue_auditoras_has_zero_files(self) -> None:
        """Auditorias/Fase_05/05_Dialogo_Auditoras/ deve ter exatamente 0 arquivos."""
        d = REPO_ROOT / "Auditorias" / "Fase_05" / "05_Dialogo_Auditoras"
        if d.exists():
            files = [f for f in d.iterdir() if f.is_file() and not f.name.startswith(".")]
            assert len(files) == 0, f"Pasta de diálogo não está vazia: {files}"
