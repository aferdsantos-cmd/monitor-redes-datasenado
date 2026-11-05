"""
Orquestrador Parametrizado das 6 Plataformas (MonitoringWindowSpec), Bolhas/Espectros e Gancho 360º.

Atende integralmente à Fase 03, ADR-007, ADR-008, ADR-010 e ADR-011:
1. Contrato flexível de parametrização temporal, por plataformas e por amostra (MonitoringWindowSpec);
2. Coleta e harmonização multi-plataforma (YouTube, Telegram, X/Twitter, Instagram/Facebook, TikTok, WhatsApp);
3. Dossiê de Estatísticas Descritivas SQL nativo no DuckDB;
4. Resumo de Bolhas Digitais e Espectros Supervisionados por Expoentes (ADR-010);
5. Contrato de Interoperabilidade com o Ecossistema 360º (ADR-011: Editorial, Buscas, Pesquisas DataSenado).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
)
from src.collectors.instagram_facebook_collector import MetaInstagramFacebookCollector
from src.collectors.telegram_collector import TelegramPublicChannelCollector
from src.collectors.tiktok_collector import TikTokResearchCollector
from src.collectors.whatsapp_collector import WhatsAppPublicGroupsExportCollector
from src.collectors.x_twitter_collector import XTwitterCollector
from src.collectors.youtube_collector import YouTubeOfficialCollector
from src.config_loader import REPO_ROOT, load_settings
from src.storage.duckdb_medallion_lake import EphemeralDuckDBMedallionLake

VALID_PLATFORMS: Set[str] = {
    "youtube",
    "telegram",
    "x_twitter",
    "instagram_facebook",
    "tiktok",
    "whatsapp",
}


@dataclass
class MonitoringWindowSpec:
    """
    Especificação formal de parametrização operacional do monitoramento (ADR-008 Modo 1).
    Permite recortes por tempo (dias, semanas, meses, datas fixas), por plataformas e por amostra.
    """
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    window_days: Optional[int] = None
    window_weeks: Optional[int] = None
    window_months: Optional[int] = None
    selected_platforms: List[str] = field(
        default_factory=lambda: ["youtube", "telegram", "x_twitter", "instagram_facebook", "tiktok", "whatsapp"]
    )
    max_manifestations_per_platform: Optional[int] = None
    max_total_manifestations: Optional[int] = None
    target_sample_size_n: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.selected_platforms:
            self.selected_platforms = list(VALID_PLATFORMS)

        for p in self.selected_platforms:
            if p not in VALID_PLATFORMS:
                raise ValueError(
                    f"Plataforma inválida especificada em MonitoringWindowSpec: '{p}'. "
                    f"Plataformas suportadas: {sorted(list(VALID_PLATFORMS))}"
                )

    def resolve_effective_time_bounds(
        self,
        reference_dt: Optional[datetime] = None,
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Calcula os limites cronológicos de início e fim da janela em UTC."""
        ref = reference_dt or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        eff_end = self.end_datetime or ref
        if eff_end.tzinfo is None:
            eff_end = eff_end.replace(tzinfo=timezone.utc)

        eff_start = self.start_datetime
        if eff_start is not None and eff_start.tzinfo is None:
            eff_start = eff_start.replace(tzinfo=timezone.utc)

        # Atalhos de tempo relativo
        if eff_start is None:
            if self.window_weeks is not None and self.window_weeks > 0:
                eff_start = eff_end - timedelta(days=7 * self.window_weeks)
            elif self.window_months is not None and self.window_months > 0:
                eff_start = eff_end - timedelta(days=30 * self.window_months)
            elif self.window_days is not None and self.window_days > 0:
                eff_start = eff_end - timedelta(days=self.window_days)

        return eff_start, eff_end


def filter_manifestations_by_spec(
    manifestations: Sequence[RawCollectedManifestation],
    spec: MonitoringWindowSpec,
    reference_dt: Optional[datetime] = None,
) -> List[RawCollectedManifestation]:
    """
    Filtra rigorosamente um conjunto de manifestações de acordo com o contrato MonitoringWindowSpec.
    """
    eff_start, eff_end = spec.resolve_effective_time_bounds(reference_dt=reference_dt)
    allowed_platforms = set(spec.selected_platforms)

    filtered: List[RawCollectedManifestation] = []
    platform_counters: Dict[str, int] = defaultdict(int)

    for m in manifestations:
        # 1. Filtro de plataforma
        if m.platform not in allowed_platforms:
            continue

        # 2. Filtro de janela temporal
        m_dt = m.created_at
        if m_dt.tzinfo is None:
            m_dt = m_dt.replace(tzinfo=timezone.utc)

        if eff_start is not None and m_dt < eff_start:
            continue
        if eff_end is not None and m_dt > eff_end:
            continue

        # 3. Limite por plataforma
        if spec.max_manifestations_per_platform is not None:
            if platform_counters[m.platform] >= spec.max_manifestations_per_platform:
                continue

        # 4. Limite global de manifestações
        if spec.max_total_manifestations is not None:
            if len(filtered) >= spec.max_total_manifestations:
                break

        filtered.append(m)
        platform_counters[m.platform] += 1

    return filtered


class Phase03SixPlatformsOrchestrator:
    """
    Orquestrador Unificado do Pipeline Multi-Plataforma para as 6 Redes Sociais.
    """

    def __init__(
        self,
        theme_id: str = "pl_ia_2338",
        hmac_secret_key: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.theme_id = theme_id
        self.settings = settings_override or load_settings()
        self.hmac_secret_key = (
            hmac_secret_key
            or os.environ.get("DATASENADO_HMAC_SECRET_KEY")
            or "k_datasenado_audit_fase03_master_2026"
        )
        # Inicializa os conectores das 6 plataformas
        self.yt_collector = YouTubeOfficialCollector(settings_override=self.settings)
        self.tg_collector = TelegramPublicChannelCollector(settings_override=self.settings)
        self.x_collector = XTwitterCollector(settings_override=self.settings)
        self.meta_collector = MetaInstagramFacebookCollector(settings_override=self.settings)
        self.tiktok_collector = TikTokResearchCollector(settings_override=self.settings)
        self.wa_collector = WhatsAppPublicGroupsExportCollector(settings_override=self.settings)

    def generate_multiplatform_manifestations(
        self,
        theme_id: Optional[str] = None,
        posts_per_platform: int = 25,
        span_days: int = 7,
        selected_platforms: Optional[List[str]] = None,
    ) -> List[RawCollectedManifestation]:
        """
        Gera lote representativo distribuído ao longo de span_days para as plataformas selecionadas.
        """
        tid = theme_id or self.theme_id
        platforms = set(selected_platforms or VALID_PLATFORMS)
        all_manifestations: List[RawCollectedManifestation] = []
        now_utc = datetime.now(timezone.utc)

        # 1. YouTube
        if "youtube" in platforms:
            q_term = "PL 2338" if tid == "pl_ia_2338" else "escala 6x1"
            yt_mock = YouTubeOfficialCollector.generate_mock_api_v3_response(
                video_id=f"vid_{tid}_senado",
                count=posts_per_platform,
                theme_id=tid,
            )
            for i, item in enumerate(yt_mock.get("items", [])):
                m = self.yt_collector.parse_comment_thread_item(item, tid, q_term)
                # Harmoniza timestamp para dentro da janela span_days
                day_offset = i % max(1, span_days)
                m.created_at = now_utc - timedelta(days=day_offset, hours=(i * 2) % 24)
                # Enriquecimento com metadados de bolha/espectro
                m.metadata.setdefault("exponent_seed_id", f"yt_channel_senado_{tid}")
                m.metadata.setdefault("spectrum_seed_hint", "espectro_centro_institucional")
                all_manifestations.append(m)

        # 2. Telegram
        if "telegram" in platforms:
            tg_mock = TelegramPublicChannelCollector.generate_mock_telegram_export(
                theme_id=tid,
                count=posts_per_platform,
            )
            tg_items = self.tg_collector.collect_from_telegram_json_export(tg_mock, tid)
            for i, m in enumerate(tg_items):
                day_offset = i % max(1, span_days)
                m.created_at = now_utc - timedelta(days=day_offset, hours=(i * 2) % 24)
                m.metadata.setdefault("exponent_seed_id", "tg_canal_noticias_senado")
                m.metadata.setdefault("spectrum_seed_hint", "espectro_progressista")
            all_manifestations.extend(tg_items)

        # 3. X / Twitter
        if "x_twitter" in platforms:
            q_term = "PL 2338" if tid == "pl_ia_2338" else "escala 6x1"
            x_mock = XTwitterCollector.generate_mock_x_v2_response(
                query=q_term,
                count=posts_per_platform,
                span_days=span_days,
                theme_id=tid,
            )
            x_items = self.x_collector.collect_from_json_export(x_mock, tid)
            all_manifestations.extend(x_items)

        # 4. Meta Instagram / Facebook
        if "instagram_facebook" in platforms:
            meta_mock = MetaInstagramFacebookCollector.generate_mock_meta_export(
                theme_id=tid,
                count=posts_per_platform,
                span_days=span_days,
            )
            meta_items = self.meta_collector.collect_from_meta_json_export(meta_mock, tid)
            all_manifestations.extend(meta_items)

        # 5. TikTok
        if "tiktok" in platforms:
            tt_mock = TikTokResearchCollector.generate_mock_tiktok_response(
                theme_id=tid,
                count=posts_per_platform,
                span_days=span_days,
            )
            tt_items = self.tiktok_collector.collect_from_tiktok_json_export(tt_mock, tid)
            all_manifestations.extend(tt_items)

        # 6. WhatsApp
        if "whatsapp" in platforms:
            wa_txt = WhatsAppPublicGroupsExportCollector.generate_mock_whatsapp_txt_export(
                theme_id=tid,
                count=posts_per_platform,
                span_days=span_days,
            )
            wa_items = self.wa_collector.parse_whatsapp_txt_export(wa_txt, tid, channel_name="grupo_cidadania_brasil")
            all_manifestations.extend(wa_items)

        return all_manifestations

    # Alias oficial
    generate_weekly_multiplatform_manifestations = generate_multiplatform_manifestations

    def compute_descriptive_statistics_report_sql(
        self,
        lake: EphemeralDuckDBMedallionLake,
        theme_id: str,
        manifestations_context: Optional[Sequence[RawCollectedManifestation]] = None,
    ) -> Dict[str, Any]:
        """
        Executa consultas analíticas SQL no DuckDB para compor o Dossiê Descritivo
        e o contrato de interoperabilidade de 360 graus (ADR-010 e ADR-011).
        """
        conn = lake.conn

        # 1. Funil de Integridade Amostral (Bronze -> Silver -> Gold)
        total_raw = conn.execute("SELECT count(*) FROM bronze_sanitized_ingest WHERE theme_id = ?", [theme_id]).fetchone()[0]
        spam_count = conn.execute("SELECT count(*) FROM silver_comments_classified WHERE theme_id = ? AND is_commercial_spam = true", [theme_id]).fetchone()[0]
        cib_posts_count = conn.execute("SELECT count(*) FROM silver_comments_classified WHERE theme_id = ? AND account_suspected_cib = true", [theme_id]).fetchone()[0]
        clean_posts_count = conn.execute("SELECT count(*) FROM silver_comments_classified WHERE theme_id = ? AND is_commercial_spam = false AND account_suspected_cib = false", [theme_id]).fetchone()[0]
        organic_accounts_N = conn.execute("SELECT count(*) FROM silver_organic_accounts_frame WHERE theme_id = ?", [theme_id]).fetchone()[0]
        retention_pct = round((clean_posts_count / max(1, total_raw)) * 100.0, 2)

        funnel_summary = {
            "total_raw_posts": total_raw,
            "quarantined_spam_posts": spam_count,
            "quarantined_cib_posts": cib_posts_count,
            "quarantined_cib_accounts": conn.execute("SELECT count(DISTINCT author_id_hash) FROM silver_comments_classified WHERE theme_id = ? AND account_suspected_cib = true", [theme_id]).fetchone()[0],
            "clean_organic_posts": clean_posts_count,
            "clean_organic_unique_accounts_N": organic_accounts_N,
            "retention_rate_pct": retention_pct,
        }

        # 2. Distribuição por Plataforma
        plat_rows = conn.execute("""
            SELECT platform,
                   count(*) as total_posts,
                   sum(CASE WHEN is_commercial_spam THEN 1 ELSE 0 END) as spam_cnt,
                   sum(CASE WHEN account_suspected_cib THEN 1 ELSE 0 END) as cib_cnt,
                   sum(CASE WHEN stance_label = 'Favoravel' AND NOT is_commercial_spam AND NOT account_suspected_cib THEN 1 ELSE 0 END) as fav_cnt,
                   sum(CASE WHEN stance_label = 'Contrario' AND NOT is_commercial_spam AND NOT account_suspected_cib THEN 1 ELSE 0 END) as against_cnt,
                   sum(CASE WHEN stance_label = 'Neutro' AND NOT is_commercial_spam AND NOT account_suspected_cib THEN 1 ELSE 0 END) as neu_cnt
            FROM silver_comments_classified
            WHERE theme_id = ?
            GROUP BY platform
            ORDER BY total_posts DESC
        """, [theme_id]).fetchall()

        by_platform_breakdown = []
        for r in plat_rows:
            p_name, tot_p, sp, cb, fav, ag, neu = r
            clean_p = fav + ag + neu
            by_platform_breakdown.append({
                "platform": p_name,
                "raw_posts": tot_p,
                "spam_posts": sp,
                "cib_posts": cb,
                "clean_organic_posts": clean_p,
                "fav_pct": round((fav / max(1, clean_p)) * 100.0, 2),
                "against_pct": round((ag / max(1, clean_p)) * 100.0, 2),
                "neutral_pct": round((neu / max(1, clean_p)) * 100.0, 2),
            })

        # 3. Série Temporal Diária
        day_rows = conn.execute("""
            SELECT day_brt,
                   count(*) as posts_cnt,
                   sum(CASE WHEN account_suspected_cib THEN 1 ELSE 0 END) as cib_attacks,
                   sum(CASE WHEN stance_label = 'Favoravel' THEN 1 ELSE 0 END) as fav_cnt,
                   sum(CASE WHEN stance_label = 'Contrario' THEN 1 ELSE 0 END) as ag_cnt
            FROM silver_comments_classified
            WHERE theme_id = ?
            GROUP BY day_brt
            ORDER BY day_brt ASC
        """, [theme_id]).fetchall()

        by_day_timeseries = [
            {
                "day_brt": r[0],
                "total_posts": r[1],
                "cib_attacks_blocked": r[2],
                "favorable_count": r[3],
                "against_count": r[4],
                "stance_balance": r[3] - r[4],
            }
            for r in day_rows
        ]

        # 4. Turnos e Macrorregiões
        shift_rows = conn.execute("""
            SELECT shift_brt, count(*) FROM silver_comments_classified WHERE theme_id = ? GROUP BY shift_brt
        """, [theme_id]).fetchall()
        by_shift_breakdown = {r[0]: r[1] for r in shift_rows}

        reg_rows = conn.execute("""
            SELECT Macroregion_proxy, count(*) FROM silver_organic_accounts_frame WHERE theme_id = ? GROUP BY Macroregion_proxy
        """, [theme_id]).fetchall()
        by_macroregion_breakdown = {r[0]: r[1] for r in reg_rows}

        # 5. Inteligência de Bolhas Digitais e Espectros (ADR-010)
        # Extrai os metadados contextuais das manifestações fornecidas
        spectrum_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "posts_count": 0,
            "fav_count": 0,
            "against_count": 0,
            "neutral_count": 0,
            "exponents": Counter(),
            "first_seen_utc": None,
        })

        if manifestations_context:
            # Mapeia stance das manifestações a partir do banco
            stance_map = dict(conn.execute("SELECT comment_id, stance_label FROM silver_comments_classified WHERE theme_id = ?", [theme_id]).fetchall())
            for m in manifestations_context:
                if m.theme_id != theme_id:
                    continue
                spec_id = m.metadata.get("spectrum_seed_hint") or "nao_rotulado_unsupervised"
                exp_id = m.metadata.get("exponent_seed_id") or "seed_geral"
                s_label = stance_map.get(m.comment_id, "Neutro")

                st = spectrum_stats[spec_id]
                st["posts_count"] += 1
                if s_label == "Favoravel":
                    st["fav_count"] += 1
                elif s_label == "Contrario":
                    st["against_count"] += 1
                else:
                    st["neutral_count"] += 1
                st["exponents"][exp_id] += 1

                m_utc = m.created_at.isoformat()
                if st["first_seen_utc"] is None or m_utc < st["first_seen_utc"]:
                    st["first_seen_utc"] = m_utc

        by_digital_spectrum_summary = []
        for spec_k, val in spectrum_stats.items():
            tot_s = max(1, val["posts_count"])
            top_exps = [exp for exp, _ in val["exponents"].most_common(3)]
            by_digital_spectrum_summary.append({
                "spectrum_id": spec_k,
                "top_exponent_seeds": top_exps,
                "organic_posts_count": val["posts_count"],
                "fav_pct": round((val["fav_count"] / tot_s) * 100.0, 2),
                "against_pct": round((val["against_count"] / tot_s) * 100.0, 2),
                "neutral_pct": round((val["neutral_count"] / tot_s) * 100.0, 2),
                "first_seen_utc": val["first_seen_utc"],
            })

        # Ordena por primeiro registro cronológico para identificar qual espectro iniciou a pauta
        by_digital_spectrum_summary.sort(key=lambda x: (x["first_seen_utc"] or "9999"))

        # 6. Domínios de Mídia Jornalística mais citados (Pilar 2 / ADR-011)
        media_domains_counter: Counter = Counter()
        if manifestations_context:
            for m in manifestations_context:
                doms = m.metadata.get("shared_news_domains", [])
                for d in doms:
                    media_domains_counter[d] += 1

        top_news_domains = [{"domain": d, "citations_count": cnt} for d, cnt in media_domains_counter.most_common(5)]

        # 7. Contrato de Interoperabilidade 360º (ADR-011)
        start_day = by_day_timeseries[0]["day_brt"] if by_day_timeseries else "N/A"
        end_day = by_day_timeseries[-1]["day_brt"] if by_day_timeseries else "N/A"
        theme_cfg = self.settings.get("pilot_themes", [{}])[0]

        ecosystem_360_interop_contract = {
            "theme_id": theme_id,
            "senate_committee": "CCT/CCJ" if "2338" in theme_id else "CAS/CCJ",
            "date_window_brt": {
                "start_day": start_day,
                "end_day": end_day,
                "total_days_active": len(by_day_timeseries),
            },
            "shared_news_domains_ranking": top_news_domains,
            "collection_query_terms": theme_cfg.get("collection_query_terms", []),
            "active_spectra": [s["spectrum_id"] for s in by_digital_spectrum_summary],
            "ready_for_editorial_intelligence_pilar2": True,
            "ready_for_search_trends_pilar3": True,
            "ready_for_datasenado_survey_pilar4": True,
        }

        return {
            "theme_id": theme_id,
            "funnel_summary": funnel_summary,
            "by_platform_breakdown": by_platform_breakdown,
            "by_day_timeseries": by_day_timeseries,
            "by_shift_breakdown": by_shift_breakdown,
            "by_macroregion_breakdown": by_macroregion_breakdown,
            "by_digital_spectrum_and_bubbles_summary": by_digital_spectrum_summary,
            "top_news_domains": top_news_domains,
            "ecosystem_360_interop_contract": ecosystem_360_interop_contract,
        }

    def run_full_six_platforms_pipeline(
        self,
        theme_id: Optional[str] = None,
        window_spec: Optional[MonitoringWindowSpec] = None,
        manifestations: Optional[Sequence[RawCollectedManifestation]] = None,
        cleanup_after_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa ponta a ponta o pipeline de monitoramento multi-plataforma:
        1. Resolução da especificação de janela e plataformas (MonitoringWindowSpec);
        2. Coleta ou geração de dados multi-plataforma com filtragem por spec;
        3. Ingestão Bronze (com extração de DDD proxy antes da redação PII e HMAC);
        4. Construção da Camada Silver (LSH, CIB, U_Org);
        5. Geração da Camada Gold (amostragem de Hamilton com meta target_sample_size_n, 3 cenários, Parquet ZSTD, R script);
        6. Computação do Dossiê Descritivo SQL + ADR-010 + ADR-011;
        7. Limpeza e expurgo Zero-Footprint.
        """
        tid = theme_id or self.theme_id
        spec = window_spec or MonitoringWindowSpec()

        # Obtém manifestações brutas
        raw_items = manifestations or self.generate_multiplatform_manifestations(
            theme_id=tid,
            posts_per_platform=30,
            span_days=spec.window_days or 7,
            selected_platforms=spec.selected_platforms,
        )

        # Aplica a filtragem formal da especificação de janela
        filtered_items = filter_manifestations_by_spec(raw_items, spec)

        with EphemeralDuckDBMedallionLake(
            hmac_secret_key=self.hmac_secret_key,
            settings_override=self.settings,
        ) as lake:
            # 1. Ingestão na Camada Bronze
            n_bronze = lake.ingest_to_bronze_and_sanitize(filtered_items)

            # 2. Processamento da Camada Silver
            silver_info = lake.build_silver_layer(tid)

            # 3. Geração da Camada Gold (aplicando meta de amostra se especificada no spec)
            target_n = spec.target_sample_size_n or (self.settings.get("sampling_engine", {}).get("sample_sizes", {}).get("clean_organic_n", 60))
            gold_info = lake.build_gold_layer_and_export_parquet(
                theme_id=tid,
                target_sample_size=target_n,
            )

            # 4. Geração do Dossiê de Estatísticas Descritivas SQL
            descriptive_report = self.compute_descriptive_statistics_report_sql(
                lake=lake,
                theme_id=tid,
                manifestations_context=filtered_items,
            )

            tables_summary = [r[0] for r in lake.conn.execute("SHOW TABLES").fetchall()]

            result = {
                "theme_id": tid,
                "window_spec": spec,
                "total_collected_raw": len(raw_items),
                "total_ingested_bronze": n_bronze,
                "silver_info": silver_info,
                "gold_info": gold_info,
                "descriptive_statistics_report": descriptive_report,
                "duckdb_tables_verified": tables_summary,
                "r_companion_script": gold_info.get("r_companion_script"),
                "parquet_gold_path": gold_info.get("parquet_gold_path"),
            }

        # Verificação da política Zero-Footprint ao final
        cache_dir = Path("/tmp/monitor_datasenado_cache")
        if cleanup_after_run and cache_dir.exists():
            for f in cache_dir.rglob("*"):
                if f.is_file():
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass
        residual_bytes = 0
        if cache_dir.exists():
            for f in cache_dir.rglob("*"):
                if f.is_file():
                    residual_bytes += f.stat().st_size
        result["tmp_residual_bytes"] = residual_bytes

        return result
