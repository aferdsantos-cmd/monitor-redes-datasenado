"""
Suíte Completa de Testes Automatizados e de Integração — Fase 02.

Valida:
1. Imutabilidade da Baseline da Fase 01 via `Phase01BaselineGuard` (bloqueio de push direto e PR workflow);
2. Conectores Reais (YouTube API v3 e Telegram) com Neutralidade Lexical Estrita e trava antiviés cronológica;
3. Data Lake Analítico DuckDB em Arquitetura Medallion (Bronze, Silver, Gold);
4. Exportação Parquet ZSTD sem texto literal de comentários e script companheiro R `survey`;
5. Orquestrador Ponta a Ponta com política Zero-Footprint (0 KB residual).
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List
import unittest.mock

import duckdb
import pyarrow.parquet as pq
import pytest

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
)
from src.collectors.phase02_medallion_pipeline import Phase02MedallionOrchestrator
from src.collectors.telegram_collector import TelegramPublicChannelCollector
from src.collectors.youtube_collector import YouTubeOfficialCollector
from src.config_loader import REPO_ROOT, load_settings
from src.storage.duckdb_medallion_lake import EphemeralDuckDBMedallionLake
from src.storage.phase_baseline_guard import Phase01BaselineGuard


# ==============================================================================
# 1. Testes de Governança Git e Proteção da Baseline da Fase 01
# ==============================================================================


def test_fase01_baseline_lock_integrity_100_percent_intact() -> None:
    """Valida que todos os 16 arquivos da Fase 01 conferem exatamente com o lock criptografico."""
    guard = Phase01BaselineGuard()
    res = guard.verify_baseline_integrity()
    assert res.is_intact is True, f"Baseline da Fase 01 comprometida: {res.summary()}"
    assert res.checked_count == 16
    assert len(res.modified_files) == 0
    assert len(res.missing_files) == 0


def test_fase01_baseline_guard_blocks_unauthorized_modification(tmp_path: Path) -> None:
    """Simula a alteracao de 1 arquivo da Fase 01 e comprova que o guardiao lanca PermissionError."""
    # Cria uma copia do lock apontando para um diretorio temporario com arquivo adulterado
    real_guard = Phase01BaselineGuard()
    manifest = real_guard.load_lock_manifest()

    fake_root = tmp_path / "fake_repo"
    fake_root.mkdir()

    # Copia os arquivos reais ou cria versoes identicas
    for rel_path, meta in manifest["frozen_files"].items():
        dest = fake_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        src = REPO_ROOT / rel_path
        dest.write_bytes(src.read_bytes())

    # Adultera exatamente 1 arquivo da Fase 01
    target_mod = fake_root / "config" / "settings.yaml"
    target_mod.write_text(target_mod.read_text(encoding="utf-8") + "\n# adulteracao_teste: 1\n", encoding="utf-8")

    fake_guard = Phase01BaselineGuard(repo_root=fake_root)
    check = fake_guard.verify_baseline_integrity()
    assert check.is_intact is False
    assert "config/settings.yaml" in check.modified_files

    with pytest.raises(PermissionError, match="BLOQUEIO DE GOVERNANCA GIT"):
        fake_guard.enforce_direct_push_allowed()

    with pytest.raises(PermissionError, match="BLOQUEIO DE SEGURANCA GIT"):
        fake_guard.sync_repository_with_governance(
            commit_message="Tentativa ilegal",
            authorize_fase01_pr=False,
        )


def test_fase01_baseline_guard_allows_pr_workflow_with_version_bump(tmp_path: Path) -> None:
    """Comprova que com authorize_fase01_pr=True e nova versao semantica, o guardiao prepara o PR."""
    real_guard = Phase01BaselineGuard()
    manifest = real_guard.load_lock_manifest()

    fake_root = tmp_path / "fake_repo"
    fake_root.mkdir()
    for rel_path in manifest["frozen_files"].keys():
        dest = fake_root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((REPO_ROOT / rel_path).read_bytes())

    # Modifica README.md
    readme = fake_root / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\n<!-- PR update -->\n", encoding="utf-8")

    fake_changelog = fake_root / "docs" / "CHANGELOG_FASE01.md"
    fake_changelog.parent.mkdir(parents=True, exist_ok=True)
    fake_changelog.write_text("# Changelog Inicial\n", encoding="utf-8")

    fake_guard = Phase01BaselineGuard(
        repo_root=fake_root,
        changelog_path=fake_changelog,
    )

    pr_payload = fake_guard.sync_repository_with_governance(
        commit_message="Atualiza documentacao da Fase 01",
        authorize_fase01_pr=True,
        new_fase01_version="v1.2.1-fase01",
        change_justification="Correcao de instrucoes no README",
        dry_run=True,
    )

    assert pr_payload["action"] == "PULL_REQUEST_WORKFLOW"
    assert pr_payload["status"] == "DRY_RUN_PR_PREPARED"
    assert pr_payload["branch"] == "pr/fase01-v1.2.1-fase01"
    assert "README.md" in pr_payload["modified_files"]


# ==============================================================================
# 2. Testes de Neutralidade Lexical e Redação de PII
# ==============================================================================


def test_base_collector_enforces_lexical_neutrality() -> None:
    """Comprova que termos neutros sao aceitos e termos valorativos/enviesados lancam ValueError."""
    collector = BaseLexicallyNeutralCollector()

    # Termos neutros autorizados devem passar sem erro
    collector.validate_query_lexical_neutrality("pl_ia_2338", "PL 2338")
    collector.validate_query_lexical_neutrality("pl_ia_2338", "Marco Legal da IA")
    collector.validate_query_lexical_neutrality("pec_escala_6x1", "escala 6x1")

    # Termos valorativos favoraveis ou contrarios devem ser bloqueados
    with pytest.raises(ValueError, match="VIOLAÇÃO DE NEUTRALIDADE LEXICAL"):
        collector.validate_query_lexical_neutrality("pl_ia_2338", "censura na IA")

    with pytest.raises(ValueError, match="VIOLAÇÃO DE NEUTRALIDADE LEXICAL"):
        collector.validate_query_lexical_neutrality("pl_ia_2338", "atraso tecnologico")

    with pytest.raises(ValueError, match="VIOLAÇÃO DE NEUTRALIDADE LEXICAL"):
        collector.validate_query_lexical_neutrality("pec_escala_6x1", "dignidade trabalhador 6x1")

    # Termos estranhos ao tema tambem devem ser rejeitados
    with pytest.raises(ValueError, match="nao pertence a lista oficial"):
        collector.validate_query_lexical_neutrality("pl_ia_2338", "reforma tributaria")


def test_base_collector_redacts_pii_and_extracts_entities() -> None:
    """Comprova redacao de CPF, e-mail, telefone, @handle e extracao de URLs e hashtags."""
    raw_sample = (
        "Meu CPF e 123.456.789-00 e meu email e cidadao@gmail.com! "
        "Me liguem no +55 (61) 98765-4321 ou falem com @deputado_silva. "
        "Apoio o #PL2338 confira em https://senado.leg.br/noticia"
    )

    redacted = BaseLexicallyNeutralCollector.redact_pii_from_text(raw_sample)
    assert "123.456.789-00" not in redacted
    assert "[CPF_REDACTED]" in redacted
    assert "cidadao@gmail.com" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert "+55 (61) 98765-4321" not in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "@deputado_silva" not in redacted
    assert "[HANDLE_REDACTED]" in redacted

    urls = BaseLexicallyNeutralCollector.extract_urls(raw_sample)
    assert "https://senado.leg.br/noticia" in urls

    tags = BaseLexicallyNeutralCollector.extract_hashtags(raw_sample)
    assert "#PL2338" in tags


# ==============================================================================
# 3. Testes do Conector do YouTube Data API v3
# ==============================================================================


def test_youtube_collector_blocks_algorithmic_relevance_order() -> None:
    """Comprova que order='relevance' e terminantemente bloqueado para evitar vies de engajamento."""
    yt = YouTubeOfficialCollector()

    with pytest.raises(ValueError, match="VIÉS ALGORÍTMICO BLOQUEADO"):
        yt.enforce_chronological_order("relevance", context="commentThreads")

    with pytest.raises(ValueError, match="VIÉS ALGORÍTMICO BLOQUEADO"):
        yt.enforce_chronological_order("relevance", context="search")

    assert yt.enforce_chronological_order("time", context="commentThreads") == "time"
    assert yt.enforce_chronological_order("date", context="search") == "date"


def test_youtube_collector_parses_v3_api_payload_and_normalizes_utc() -> None:
    """Testa a ingestao de fixtures realistas da API v3 do YouTube."""
    yt = YouTubeOfficialCollector()
    mock_payload = YouTubeOfficialCollector.generate_mock_api_v3_response("vid_123", count=10)

    items = mock_payload.get("items", [])
    assert len(items) == 10

    m = yt.parse_comment_thread_item(items[0], "pl_ia_2338", "PL 2338")
    assert m.platform == "youtube"
    assert m.theme_id == "pl_ia_2338"
    assert m.comment_id.startswith("yt_")
    assert m.created_at.tzinfo == timezone.utc
    assert m.collector_modality == "official_api_chronological"
    assert len(m.text) > 0


def test_youtube_collector_pagination_and_transport_injection() -> None:
    """Testa paginacao via nextPageToken utilizando funcao de transporte http injetada."""
    page_call_count = 0

    def mock_http(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal page_call_count
        page_call_count += 1
        page_token = params.get("pageToken")
        if not page_token:
            return YouTubeOfficialCollector.generate_mock_api_v3_response("vid_page", count=5, next_page_token="tok_page2")
        return YouTubeOfficialCollector.generate_mock_api_v3_response("vid_page", count=5, next_page_token=None)

    yt = YouTubeOfficialCollector(http_get_json=mock_http)
    comments = yt.collect_comments_for_video("vid_page", "pl_ia_2338", "PL 2338", max_comments=10)

    assert len(comments) == 10
    assert page_call_count == 2


# ==============================================================================
# 4. Testes do Conector do Telegram
# ==============================================================================


def test_telegram_collector_parses_polymorphic_json_export() -> None:
    """Testa a ingestao de exportacao oficial do Telegram Desktop com entidades polimorficas."""
    tg = TelegramPublicChannelCollector()
    mock_export = TelegramPublicChannelCollector.generate_mock_telegram_export("pl_ia_2338", count=15)

    results = tg.collect_from_telegram_json_export(mock_export, "pl_ia_2338")
    assert len(results) > 0
    for r in results:
        assert r.platform == "telegram"
        assert r.theme_id == "pl_ia_2338"
        assert r.collector_modality == "passive_export_ingestion"
        assert r.created_at.tzinfo == timezone.utc
        assert r.collection_query_used in ["PL 2338", "PL 2338/2023", "lei da inteligência artificial", "regulamentação da IA"]


def test_telegram_collector_parses_bot_api_updates() -> None:
    """Testa consumo da Telegram Bot API oficial (getUpdates)."""
    def mock_http(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ok": True,
            "result": [
                {
                    "update_id": 991,
                    "channel_post": {
                        "message_id": 101,
                        "date": 1793130000,
                        "chat": {"id": -1001234567, "title": "Debate Publico DF"},
                        "text": "Audiencia publica sobre o PL 2338 no Senado comecou agora. #MarcoLegalIA",
                    },
                },
                {
                    "update_id": 992,
                    "channel_post": {
                        "message_id": 102,
                        "date": 1793130100,
                        "chat": {"id": -1001234567, "title": "Debate Publico DF"},
                        "text": "Mensagem sobre outro assunto nao relacionado a IA.",
                    },
                },
            ],
        }

    tg = TelegramPublicChannelCollector(http_get_json=mock_http, bot_token="fake_token")
    results = tg.collect_from_bot_api_updates("pl_ia_2338")
    assert len(results) == 1
    assert results[0].comment_id == "tg_api_991_101"
    assert results[0].collection_query_used == "PL 2338"


# ==============================================================================
# 5. Testes do Data Lake Medallion DuckDB (Bronze -> Silver -> Gold)
# ==============================================================================


def test_duckdb_bronze_never_stores_raw_author_id_or_pii() -> None:
    """Verifica por query SQL direta que a tabela Bronze nao possui raw_author_id nem PII."""
    raw_manifestation = RawCollectedManifestation(
        comment_id="yt_test_sec_1",
        theme_id="pl_ia_2338",
        platform="youtube",
        raw_author_id="@usuario_real_confidencial",
        text="Meu telefone e (61) 99999-1234 e apoio o PL 2338!",
        created_at=datetime(2026, 10, 27, 12, 0, tzinfo=timezone.utc),
        collection_query_used="PL 2338",
        collector_modality="official_api_chronological",
        phone_or_location_hint="(61) 99999-1234",
    )

    with EphemeralDuckDBMedallionLake(memory_only=True) as lake:
        lake.ingest_to_bronze_and_sanitize([raw_manifestation])

        # Consulta SQL direta
        row = lake.conn.execute("""
            SELECT comment_id, author_id_hash, hmac_key_id, sanitized_text, DDD_proxy, Macroregion_proxy
            FROM bronze_sanitized_ingest
            WHERE comment_id = 'yt_test_sec_1'
        """).fetchone()

        assert row is not None
        assert "@usuario_real_confidencial" not in str(row)
        assert len(row[1]) == 64  # Hash HMAC-SHA256
        assert len(row[2]) == 8   # hmac_key_id
        assert "[PHONE_REDACTED]" in row[3]
        assert row[4] == "DF"
        assert row[5] == "Centro-Oeste"


def test_duckdb_silver_separates_cib_and_builds_organic_frame_sql() -> None:
    """Valida a separacao de CIB na Silver e agregacoes SQL nativas de U_Org."""
    orch = Phase02MedallionOrchestrator(theme_id="pl_ia_2338")
    items = orch.generate_pilot_synthetic_manifestations(youtube_count=30, telegram_count=30)

    with EphemeralDuckDBMedallionLake(memory_only=True) as lake:
        lake.ingest_to_bronze_and_sanitize(items)
        silver_res = lake.build_silver_layer("pl_ia_2338")

        assert silver_res["silver_comments"] == 60
        assert silver_res["organic_accounts"] > 0

        # Testa agregacao analitica SQL nativa por estrato
        summary = lake.get_silver_stratum_summary_sql("pl_ia_2338")
        assert len(summary) > 0
        for st in summary:
            assert "platform" in st
            assert "stratum_key" in st
            assert st["stratum_pop_N"] > 0
            assert st["min_inclusion_prob"] > 0.0


def test_duckdb_gold_exports_zstd_parquet_without_literal_text_and_generates_r_script(tmp_path: Path) -> None:
    """Valida que o Parquet Gold nao contem texto literal (anti-reidentificacao) e gera o script R."""
    orch = Phase02MedallionOrchestrator(theme_id="pl_ia_2338")
    items = orch.generate_pilot_synthetic_manifestations(youtube_count=30, telegram_count=30)

    out_parquet = tmp_path / "gold_test_pl2338.parquet"

    with EphemeralDuckDBMedallionLake(memory_only=True) as lake:
        lake.ingest_to_bronze_and_sanitize(items)
        lake.build_silver_layer("pl_ia_2338")
        gold_info = lake.build_gold_layer_and_export_parquet(
            "pl_ia_2338",
            target_sample_size=25,
            output_parquet_path=out_parquet,
        )

        assert out_parquet.exists()
        assert out_parquet.stat().st_size > 0

        # Inspeciona schema do Parquet gerado com PyArrow
        parquet_tbl = pq.read_table(out_parquet)
        col_names = parquet_tbl.column_names

        # Protecao epistemica e LGPD: PROIBIDO haver coluna de texto literal no Parquet Gold!
        assert "sanitized_text" not in col_names
        assert "text" not in col_names
        assert "author_id_hash" in col_names
        assert "stratum_key" in col_names
        assert "design_weight" in col_names
        assert "stance_label" in col_names

        # Valida gerador de script R survey
        r_code = gold_info["r_companion_script"]
        assert "library(survey)" in r_code
        assert "survey::svydesign" in r_code
        assert "fpc = ~stratum_pop_N" in r_code
        assert "survey::svychisq" in r_code


def test_duckdb_context_manager_zero_footprint_purge() -> None:
    """Valida que o context manager do DuckDB Lake apaga qualquer arquivo de banco local no __exit__."""
    with EphemeralDuckDBMedallionLake(memory_only=False) as lake:
        db_file = lake._local_db_file
        assert db_file is not None
        assert db_file.exists()

    # Apos saida do bloco with, o arquivo duckdb efemero deve estar purgado
    assert not db_file.exists()


# ==============================================================================
# 6. Testes do Orquestrador Ponta a Ponta e Piloto nos Dois Temas
# ==============================================================================


def test_phase02_end_to_end_orchestrator_zero_footprint_cleanup() -> None:
    """Executa o pipeline ponta a ponta e comprova Zero-Footprint (0 KB em /tmp ao final)."""
    orch = Phase02MedallionOrchestrator(theme_id="pl_ia_2338")
    res = orch.run_medallion_pipeline(cleanup_after_run=True)

    assert res["total_collected_bronze"] == 100
    assert res["organic_accounts_N"] > 0
    assert res["sampled_accounts_n"] > 0
    assert len(res["duckdb_tables_verified"]) == 5
    assert res["tmp_residual_bytes"] == 0


def test_phase02_orchestrator_supports_both_pilot_themes() -> None:
    """Comprova funcionamento integro para os dois temas legislativos: pl_ia_2338 e pec_escala_6x1."""
    # Tema 1: PL 2338
    orch_ia = Phase02MedallionOrchestrator(theme_id="pl_ia_2338")
    res_ia = orch_ia.run_medallion_pipeline(cleanup_after_run=True)
    assert res_ia["theme_id"] == "pl_ia_2338"

    # Tema 2: PEC Escala 6x1
    orch_6x1 = Phase02MedallionOrchestrator(theme_id="pec_escala_6x1")
    res_6x1 = orch_6x1.run_medallion_pipeline(cleanup_after_run=True)
    assert res_6x1["theme_id"] == "pec_escala_6x1"
    assert res_6x1["total_collected_bronze"] == 100
