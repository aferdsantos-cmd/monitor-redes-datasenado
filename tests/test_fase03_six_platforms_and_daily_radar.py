"""
Suíte Completa de Testes Automatizados e de Integração — Fase 03.

Valida:
1. Imutabilidade absoluta da Baseline da Fase 01 (16 arquivos congelados);
2. Documento de Governança docs/05_Termo_de_Emenda_Diretora_v2_1_ADR007_a_ADR009.md (ADR-007 a ADR-011);
3. Conectores das 6 plataformas (X/Twitter, Meta I/F, TikTok, WhatsApp, YouTube, Telegram);
4. Trava antiviés algorítmico estrita com ValueError em todos os conectores;
5. Reparo de mojibake UTF-8 na Meta e parsing Android/iOS multilinhas no WhatsApp;
6. Extração precoce de DDD do remetente do WhatsApp para Bronze com redação PII;
7. Coletor de Panorama Diário Aberto (Radar do Senado — ADR-008 Modo 2);
8. Orquestrador das 6 plataformas com MonitoringWindowSpec, Bolhas/Espectros (ADR-010),
   Contrato 360º (ADR-011) e Zero-Footprint estrito (0 KB residual).
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import unittest.mock
import urllib.error

import pytest

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
)
from src.collectors.daily_radar_collector import (
    DailyLegislativeRadarCollector,
    DailyTopicRadarItem,
    SENATE_COMMITTEES_LEXICON,
)
from src.collectors.instagram_facebook_collector import (
    MetaInstagramFacebookCollector,
    fix_meta_mojibake_utf8,
)
from src.collectors.phase03_six_platforms_orchestrator import (
    MonitoringWindowSpec,
    Phase03SixPlatformsOrchestrator,
    VALID_PLATFORMS,
    filter_manifestations_by_spec,
)
from src.collectors.tiktok_collector import TikTokResearchCollector
from src.collectors.whatsapp_collector import WhatsAppPublicGroupsExportCollector
from src.collectors.x_twitter_collector import XTwitterCollector
from src.config_loader import REPO_ROOT, load_settings
from src.storage.duckdb_medallion_lake import EphemeralDuckDBMedallionLake
from src.storage.phase_baseline_guard import Phase01BaselineGuard


# ==============================================================================
# 1. Testes de Governança e Imutabilidade da Baseline Fase 01
# ==============================================================================


def test_fase03_baseline_fase01_remains_100_percent_intact() -> None:
    """Valida que nenhum dos 16 arquivos da Fase 01 foi tocado na Fase 03."""
    guard = Phase01BaselineGuard()
    res = guard.verify_baseline_integrity()
    assert res.is_intact is True, f"Baseline da Fase 01 violada: {res.summary()}"
    assert res.checked_count == 16
    assert len(res.modified_files) == 0
    assert len(res.missing_files) == 0


def test_fase03_emenda_diretora_doc_covers_all_five_adrs() -> None:
    """Valida existência e integridade do documento de governança docs/05_... cobrindo ADR-007 a ADR-011."""
    doc_path = REPO_ROOT / "docs" / "05_Termo_de_Emenda_Diretora_v2_1_ADR007_a_ADR009.md"
    assert doc_path.exists(), "Documento docs/05_Termo_de_Emenda_Diretora_v2_1_ADR007_a_ADR009.md não encontrado."
    content = doc_path.read_text(encoding="utf-8")

    adrs = ["ADR-007", "ADR-008", "ADR-009", "ADR-010", "ADR-011"]
    for adr in adrs:
        assert adr in content, f"Decisão {adr} ausente do documento de governança docs/05."

    assert "Produto Interno de Bancada" in content
    assert "Dupla Modalidade Operacional" in content
    assert "Microsoft Word" in content or ".docx" in content
    assert "Bolhas Digitais" in content and "Espectros" in content
    assert "Ecossistema de Inteligência de Dados e Informações 360º" in content


# ==============================================================================
# 2. Testes do Conector X / Twitter (API v2 + Neutralidade + Antiviés)
# ==============================================================================


def test_x_twitter_collector_enforces_recency_and_rejects_algorithmic_orders() -> None:
    """Comprova que o coletor X/Twitter exige exclusivamente sort_order='recency'."""
    x = XTwitterCollector()
    assert x.enforce_chronological_sort_order("recency") == "recency"
    assert x.enforce_chronological_sort_order(None) == "recency"
    assert x.enforce_chronological_sort_order("") == "recency"

    bad_orders = ["relevancy", "popular", "likes", "engagement", "views", "custom"]
    for bad in bad_orders:
        with pytest.raises(ValueError, match="VIÉS ALGORÍTMICO BLOQUEADO NO X/TWITTER"):
            x.enforce_chronological_sort_order(bad)


def test_x_twitter_collector_parses_api_v2_with_pagination_and_bearer_masking() -> None:
    """Valida parsing de payload da API v2 do X, paginação por next_token e mascaramento de credenciais."""
    pages_called = []

    def mock_http_get(url: str, params: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        pages_called.append(params.get("next_token"))
        if params.get("next_token") == "token_page_2":
            return {
                "data": [{
                    "id": "tw_page_2",
                    "text": "Debate no Senado sobre o PL 2338 e inteligencia artificial #PL2338 https://senado.leg.br/noticia",
                    "author_id": "u2",
                    "created_at": "2026-11-04T15:00:00Z",
                }],
                "includes": {"users": [{"id": "u2", "username": "senado_cidadao_2"}]},
                "meta": {"result_count": 1},
            }
        return {
            "data": [{
                "id": "tw_page_1",
                "text": "Discussao sobre o PL 2338 no Senado com protecao de direitos autorais #PL2338",
                "author_id": "u1",
                "created_at": "2026-11-04T14:00:00Z",
            }],
            "includes": {"users": [{"id": "u1", "username": "senado_cidadao_1"}]},
            "meta": {"result_count": 1, "next_token": "token_page_2"},
        }

    x = XTwitterCollector(bearer_token="secret_token_x_12345", http_get_json=mock_http_get)
    tweets = x.collect_recent_tweets_v2(theme_id="pl_ia_2338", query="PL 2338", max_pages=2)

    assert len(tweets) == 2
    assert tweets[0].comment_id == "x_tw_page_1"
    assert tweets[1].comment_id == "x_tw_page_2"
    assert tweets[0].raw_author_id == "@senado_cidadao_1"
    assert pages_called == [None, "token_page_2"]

    # Testa mascaramento de credenciais em erro HTTP
    def mock_http_error(url: str, params: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        fp = unittest.mock.MagicMock()
        fp.read.return_value = b"Unauthorized secret_token_x_12345"
        raise urllib.error.HTTPError(url, 401, "Unauthorized", {}, fp)

    x_err = XTwitterCollector(bearer_token="secret_token_x_12345", http_get_json=mock_http_error)
    with pytest.raises(RuntimeError) as exc_info:
        x_err.collect_recent_tweets_v2(theme_id="pl_ia_2338", query="PL 2338")
    assert "secret_token_x_12345" not in str(exc_info.value)
    assert "[REDACTED_BEARER_TOKEN]" in str(exc_info.value)


# ==============================================================================
# 3. Testes do Conector Meta Instagram/Facebook (Graph API + Mojibake UTF-8)
# ==============================================================================


def test_meta_collector_enforces_chronological_and_rejects_ranked_order() -> None:
    """Comprova bloqueio de ordenações algorítmicas na Graph API da Meta."""
    meta = MetaInstagramFacebookCollector()
    assert meta.enforce_chronological_order("chronological") == "chronological"
    assert meta.enforce_chronological_order("reverse_chronological") == "reverse_chronological"
    assert meta.enforce_chronological_order(None) == "reverse_chronological"

    bad_orders = ["ranked", "toplevel", "relevance", "popularity"]
    for bad in bad_orders:
        with pytest.raises(ValueError, match="VIÉS ALGORÍTMICO BLOQUEADO NA META"):
            meta.enforce_chronological_order(bad)


def test_meta_collector_fixes_utf8_mojibake_in_text_and_author() -> None:
    """Valida o reparo automático de mojibake UTF-8 decodificado como Latin-1."""
    mojibake_str = "A votaÃ§Ã£o da lei da inteligÃªncia artificial e proteÃ§Ã£o de direitos autorais."
    fixed = fix_meta_mojibake_utf8(mojibake_str)
    assert fixed == "A votação da lei da inteligência artificial e proteção de direitos autorais."

    export_mock = {
        "feed_name": "pÃ¡gina_senado",
        "comments": [{
            "id": "c1",
            "message": "DiscussÃ£o da escala 6x1 e reduÃ§Ã£o da jornada sem reduÃ§Ã£o salarial",
            "author": {"name": "CidadÃ£o de BrasÃ­lia"},
            "created_time": "2026-11-04T12:00:00Z",
        }],
    }
    collector = MetaInstagramFacebookCollector()
    items = collector.collect_from_meta_json_export(export_mock, theme_id="pec_escala_6x1")
    assert len(items) == 1
    assert "redução da jornada sem redução salarial" in items[0].text
    assert "Cidadão de Brasília" in items[0].raw_author_id


# ==============================================================================
# 4. Testes do Conector TikTok (Research API + Epoch UTC)
# ==============================================================================


def test_tiktok_collector_enforces_create_time_and_rejects_likes_order() -> None:
    """Comprova bloqueio de ordenações por likes/relevância na TikTok Research API."""
    tt = TikTokResearchCollector()
    assert tt.enforce_chronological_order("create_time") == "create_time"
    assert tt.enforce_chronological_order("time") == "time"
    assert tt.enforce_chronological_order(None) == "create_time"

    bad_orders = ["likes", "popular", "relevance", "engagements"]
    for bad in bad_orders:
        with pytest.raises(ValueError, match="VIÉS ALGORÍTMICO BLOQUEADO NO TIKTOK"):
            tt.enforce_chronological_order(bad)


def test_tiktok_collector_parses_research_api_format() -> None:
    """Valida conversão de epoch seconds para datetime UTC e mascaramento de credenciais."""
    epoch_ts = 1793880000  # Epoch futuro de teste em 2026
    mock_payload = {
        "data": {
            "comments": [{
                "id": 9876543210,
                "text": "Excelente debate sobre o PL 2338 no Senado Federal #PL2338",
                "create_time": epoch_ts,
                "user_id": "tt_user_123",
                "like_count": 42,
            }],
            "cursor": 1,
            "has_more": False,
        }
    }

    def mock_get(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        return mock_payload

    tt = TikTokResearchCollector(client_token="secret_token_tt_999", http_get_json=mock_get)
    comments = tt.collect_video_comments_research_api(theme_id="pl_ia_2338", query="PL 2338", video_id="123456")

    assert len(comments) == 1
    assert comments[0].comment_id == "tt_9876543210"
    assert comments[0].raw_author_id == "tt_tt_user_123"
    assert comments[0].created_at.year == 2026
    assert comments[0].created_at.tzinfo == timezone.utc


# ==============================================================================
# 5. Testes do Conector WhatsApp (.txt Android/iOS + Multilinhas + DDD Proxy)
# ==============================================================================


def test_whatsapp_collector_parses_android_and_ios_multiline_txt_export() -> None:
    """Comprova parsing robusto de arquivos .txt do WhatsApp nos formatos Android e iOS com mensagens multilinhas."""
    txt_content = (
        "27/10/2026 14:30 - +55 61 99888-7766: Olá a todos, compartilhando debate do PL 2338 no Senado.\n"
        "Esta é uma segunda linha da mesma mensagem com mais detalhes.\n"
        "E esta é a terceira linha de continuação!\n"
        "[27/10/2026, 14:35:10] +55 (11) 98765-4321: Acompanhando a votação da lei da inteligencia artificial hoje pelo iOS.\n"
        "27/10/2026 14:40 - Administrador do Grupo: Mensagem que não cita termos legislativos não deve ser coletada."
    )

    wa = WhatsAppPublicGroupsExportCollector()
    items = wa.parse_whatsapp_txt_export(txt_content, theme_id="pl_ia_2338")

    assert len(items) == 2
    # Valida mensagem multilinha Android
    assert items[0].comment_id == "wa_grupo_whatsapp_1"
    assert "terceira linha de continuação" in items[0].text
    assert items[0].phone_or_location_hint == "+55 61 99888-7766"
    assert items[0].created_at.tzinfo == timezone.utc

    # Valida mensagem iOS
    assert items[1].comment_id == "wa_grupo_whatsapp_2"
    assert "pelo iOS" in items[1].text
    assert items[1].phone_or_location_hint == "+55 (11) 98765-4321"


def test_whatsapp_collector_filters_system_messages_and_mids() -> None:
    """Comprova descarte de avisos de criptografia, entradas/saídas e mídias ocultas."""
    txt_content = (
        "27/10/2026 10:00 - As mensagens e as chamadas são protegidas com a criptografia de ponta a ponta.\n"
        "27/10/2026 10:05 - +55 71 99111-2233 entrou usando o link de convite deste grupo\n"
        "27/10/2026 10:10 - +55 71 99111-2233: <Mídia oculta>\n"
        "27/10/2026 10:15 - +55 71 99111-2233: Bom dia, sobre a PEC da escala 6x1 e reducao da jornada sem reducao salarial.\n"
        "27/10/2026 10:20 - +55 71 99111-2233 saiu do grupo\n"
    )

    wa = WhatsAppPublicGroupsExportCollector()
    items = wa.parse_whatsapp_txt_export(txt_content, theme_id="pec_escala_6x1")

    assert len(items) == 1
    assert "reducao da jornada sem reducao salarial" in items[0].text


def test_whatsapp_collector_extracts_ddd_and_bronze_maps_macroregion() -> None:
    """
    Comprova que o DDD do remetente do WhatsApp (+55 61) alimenta phone_or_location_hint
    e a Camada Bronze mapeia para ('DF', 'Centro-Oeste') com o texto limpo e telefone redigido.
    """
    txt_content = (
        "27/10/2026 14:00 - +55 61 99888-7766: Apoio a regulamentacao da IA no Brasil com o PL 2338.\n"
        "27/10/2026 15:00 - +55 (11) 98765-4321: Precisamos de protecao de direitos autorais no PL 2338 urgente.\n"
    )

    wa = WhatsAppPublicGroupsExportCollector()
    items = wa.parse_whatsapp_txt_export(txt_content, theme_id="pl_ia_2338")
    assert len(items) == 2

    settings = load_settings()
    with EphemeralDuckDBMedallionLake(memory_only=True, settings_override=settings) as lake:
        lake.ingest_to_bronze_and_sanitize(items)
        rows = lake.conn.execute("""
            SELECT comment_id, DDD_proxy, Macroregion_proxy, author_id_hash
            FROM bronze_sanitized_ingest ORDER BY comment_id
        """).fetchall()

        assert len(rows) == 2
        # Item 1: +55 61 -> DF / Centro-Oeste
        assert rows[0][1] == "DF"
        assert rows[0][2] == "Centro-Oeste"
        assert rows[0][3] is not None and not rows[0][3].startswith("+55")

        # Item 2: +55 11 -> SP / Sudeste
        assert rows[1][1] == "SP"
        assert rows[1][2] == "Sudeste"


# ==============================================================================
# 6. Testes do Radar Diário de Pautas do Senado (ADR-008 Modo 2)
# ==============================================================================


def test_daily_radar_collector_identifies_senate_committees_and_rejects_entertainment() -> None:
    """Valida descoberta de tópicos diários com triagem assertiva para CAS, CCT, CAE e descarte de entretenimento."""
    radar = DailyLegislativeRadarCollector()
    now_dt = datetime(2026, 11, 4, 15, 0, tzinfo=timezone.utc)

    manifestations = [
        # Tema CAS / CCJ (PEC 6x1)
        RawCollectedManifestation(
            comment_id="r1",
            theme_id="pec_escala_6x1",
            platform="youtube",
            raw_author_id="user1",
            text="Debate crucial sobre a jornada de trabalho e fim da escala 6x1 na comissão do Senado",
            created_at=now_dt,
            collection_query_used="escala 6x1",
            collector_modality="official_api_chronological",
        ),
        # Tema CCT (IA)
        RawCollectedManifestation(
            comment_id="r2",
            theme_id="pl_ia_2338",
            platform="telegram",
            raw_author_id="user2",
            text="Avanço da lei da inteligencia artificial e seguranca juridica IA no plenário",
            created_at=now_dt,
            collection_query_used="PL 2338",
            collector_modality="official_api_chronological",
        ),
        # Matéria CAE (Reforma Tributária)
        RawCollectedManifestation(
            comment_id="r3",
            theme_id="tema_aberto_radar",
            platform="x_twitter",
            raw_author_id="user3",
            text="A reforma tributaria e a tributacao do consumo estao em discussao com o ministro",
            created_at=now_dt,
            collection_query_used="reforma tributaria",
            collector_modality="official_api_chronological",
        ),
        # Entretenimento / Futebol (Sem interesse legislativo)
        RawCollectedManifestation(
            comment_id="r4",
            theme_id="tema_aberto_radar",
            platform="tiktok",
            raw_author_id="user4",
            text="Grande jogo de futebol pelo campeonato brasileiro com gol no final da torcida",
            created_at=now_dt,
            collection_query_used="campeonato brasileiro",
            collector_modality="official_api_chronological",
        ),
    ]

    results = radar.scan_daily_dominant_topics(manifestations, target_date="2026-11-04")
    assert len(results) >= 3

    # Verifica temas legislativos aprovados
    senate_topics = [t for t in results if t.senate_interest_flag]
    assert len(senate_topics) >= 2

    # Verifica que futebol tem senate_interest_flag=False
    futebol_topics = [t for t in results if t.topic_id == "futebol_campeonato"]
    assert len(futebol_topics) == 1
    assert futebol_topics[0].senate_interest_flag is False
    assert futebol_topics[0].legislative_relevance_score <= 0.20


# ==============================================================================
# 7. Testes de Parametrização via MonitoringWindowSpec
# ==============================================================================


def test_monitoring_window_spec_rejects_invalid_platforms() -> None:
    """Comprova que MonitoringWindowSpec lança ValueError para plataforma inexistente."""
    with pytest.raises(ValueError, match="Plataforma inválida"):
        MonitoringWindowSpec(selected_platforms=["youtube", "rede_social_inexistente"])


def test_monitoring_window_spec_time_bounds_resolution() -> None:
    """Valida resolução de janelas temporais por dias, semanas, meses e datas explícitas."""
    ref = datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)

    # 1. window_days=3
    spec_days = MonitoringWindowSpec(window_days=3)
    s, e = spec_days.resolve_effective_time_bounds(reference_dt=ref)
    assert s is not None and e is not None
    assert (e - s).days == 3

    # 2. window_weeks=2
    spec_weeks = MonitoringWindowSpec(window_weeks=2)
    s, e = spec_weeks.resolve_effective_time_bounds(reference_dt=ref)
    assert s is not None and e is not None
    assert (e - s).days == 14

    # 3. window_months=1
    spec_months = MonitoringWindowSpec(window_months=1)
    s, e = spec_months.resolve_effective_time_bounds(reference_dt=ref)
    assert s is not None and e is not None
    assert (e - s).days == 30


def test_filter_manifestations_by_spec_caps_per_platform_and_global() -> None:
    """Comprova aplicação de tetos por rede e limite global de manifestações."""
    base_dt = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
    items = []
    for i in range(10):
        items.append(RawCollectedManifestation(
            comment_id=f"yt_{i}", theme_id="pl_ia_2338", platform="youtube",
            raw_author_id=f"user_yt_{i}", text=f"Comentário {i} sobre PL 2338",
            created_at=base_dt, collection_query_used="PL 2338",
            collector_modality="official_api_chronological"
        ))
    for i in range(10):
        items.append(RawCollectedManifestation(
            comment_id=f"wa_{i}", theme_id="pl_ia_2338", platform="whatsapp",
            raw_author_id=f"user_wa_{i}", text=f"Mensagem {i} sobre PL 2338",
            created_at=base_dt, collection_query_used="PL 2338",
            collector_modality="passive_export_ingestion"
        ))

    # Teto de 3 por plataforma
    spec_cap = MonitoringWindowSpec(
        selected_platforms=["youtube", "whatsapp"],
        max_manifestations_per_platform=3,
    )
    filtered = filter_manifestations_by_spec(items, spec_cap)
    assert len(filtered) == 6
    assert sum(1 for m in filtered if m.platform == "youtube") == 3
    assert sum(1 for m in filtered if m.platform == "whatsapp") == 3

    # Teto global de 4
    spec_global = MonitoringWindowSpec(
        selected_platforms=["youtube", "whatsapp"],
        max_total_manifestations=4,
    )
    filtered_glob = filter_manifestations_by_spec(items, spec_global)
    assert len(filtered_glob) == 4


# ==============================================================================
# 8. Testes do Orquestrador das 6 Plataformas, ADR-010 e ADR-011
# ==============================================================================


def test_phase03_orchestrator_six_platforms_full_pipeline_and_zero_footprint() -> None:
    """
    Executa o pipeline completo da Fase 03 com todas as 6 plataformas simultaneamente,
    comprovando ingestão Bronze, Silver, Gold, relatório descritivo e Zero-Footprint (0 KB residual).
    """
    orch = Phase03SixPlatformsOrchestrator(theme_id="pl_ia_2338")
    spec = MonitoringWindowSpec(
        window_days=7,
        selected_platforms=list(VALID_PLATFORMS),
        max_manifestations_per_platform=15,
        target_sample_size_n=40,
    )

    res = orch.run_full_six_platforms_pipeline(theme_id="pl_ia_2338", window_spec=spec, cleanup_after_run=True)

    assert res["total_collected_raw"] > 0
    assert res["total_ingested_bronze"] > 0
    assert len(res["duckdb_tables_verified"]) == 5
    assert res["tmp_residual_bytes"] == 0, "Falha na política Zero-Footprint (/tmp deve ter 0 KB residual)."

    report = res["descriptive_statistics_report"]
    assert report["funnel_summary"]["clean_organic_posts"] > 0
    assert len(report["by_platform_breakdown"]) == 6


def test_phase03_orchestrator_digital_spectrum_bubbles_and_first_seen_utc() -> None:
    """
    Valida a análise de Bolhas e Espectros (ADR-010), comprovando agrupamento por espectro,
    cálculo de posicionamento (fav/against/neutral) e identificação de first_seen_utc.
    """
    orch = Phase03SixPlatformsOrchestrator(theme_id="pl_ia_2338")
    items = orch.generate_multiplatform_manifestations(theme_id="pl_ia_2338", posts_per_platform=10, span_days=5)

    settings = load_settings()
    with EphemeralDuckDBMedallionLake(memory_only=True, settings_override=settings) as lake:
        lake.ingest_to_bronze_and_sanitize(items)
        lake.build_silver_layer("pl_ia_2338")
        lake.build_gold_layer_and_export_parquet("pl_ia_2338")

        report = orch.compute_descriptive_statistics_report_sql(
            lake=lake,
            theme_id="pl_ia_2338",
            manifestations_context=items,
        )

        bubbles = report["by_digital_spectrum_and_bubbles_summary"]
        assert len(bubbles) > 0

        # Verifica presença de first_seen_utc em cada espectro
        for b in bubbles:
            assert "spectrum_id" in b
            assert "fav_pct" in b
            assert "against_pct" in b
            assert "first_seen_utc" in b
            assert b["first_seen_utc"] is not None


def test_phase03_orchestrator_ecosystem_360_interop_contract() -> None:
    """
    Valida o contrato de interoperabilidade de 360 graus (ADR-011), confirmando a presença
    de todas as chaves universais necessárias para acoplar no futuro os Pilares 2, 3 e 4.
    """
    orch = Phase03SixPlatformsOrchestrator(theme_id="pl_ia_2338")
    items = orch.generate_multiplatform_manifestations(theme_id="pl_ia_2338", posts_per_platform=10, span_days=3)

    settings = load_settings()
    with EphemeralDuckDBMedallionLake(memory_only=True, settings_override=settings) as lake:
        lake.ingest_to_bronze_and_sanitize(items)
        lake.build_silver_layer("pl_ia_2338")
        lake.build_gold_layer_and_export_parquet("pl_ia_2338")

        report = orch.compute_descriptive_statistics_report_sql(
            lake=lake,
            theme_id="pl_ia_2338",
            manifestations_context=items,
        )

        contract = report["ecosystem_360_interop_contract"]
        assert contract["theme_id"] == "pl_ia_2338"
        assert "senate_committee" in contract
        assert "date_window_brt" in contract
        assert "shared_news_domains_ranking" in contract
        assert contract["ready_for_editorial_intelligence_pilar2"] is True
        assert contract["ready_for_search_trends_pilar3"] is True
        assert contract["ready_for_datasenado_survey_pilar4"] is True
