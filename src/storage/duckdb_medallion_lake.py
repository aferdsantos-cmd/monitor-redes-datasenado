"""
Data Lake Analitico Colunar Efemero em DuckDB com Arquitetura Medallion (Fase 02).

Implementa o fluxo de dados em 3 camadas colunares:
1. Camada Bronze: Ingestao bruta sanitizada com redacao de PII e pseudonimizacao HMAC-SHA256 (Art. 13 LGPD);
2. Camada Silver: Classificacao forense de spam/CIB e construcao do quadro deduplicado de contas organicas;
3. Camada Gold: Amostra sorteada (sem texto literal para protecao de reidentificacao reversa),
   estimativas dos 3 Cenarios estatisticos e exportacao Parquet ZSTD com script companheiro R survey.
"""

from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
import unicodedata
from zoneinfo import ZoneInfo

import duckdb
import numpy as np

from src.cleaning.lgpd_and_bot_filter import (
    LGPDCleanerAndCIBGraphEngine,
    SocialPost,
)
from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    PHONE_PATTERN,
    RawCollectedManifestation,
)
from src.config_loader import load_settings
from src.sampling.stratified_sampler import (
    ObservedUniverseStratifiedSampler,
    get_time_slice_stratum,
    to_brazil_timezone,
)
from src.stats.opinion_inference_engine import DigitalDiscourseStatisticalEngine
from src.storage.zero_footprint_sync import ZeroFootprintStorage

SP_TZ = ZoneInfo("America/Sao_Paulo")

# Alias para compatibilidade semantica
ZeroFootprintStorageManager = ZeroFootprintStorage


def normalize_text_ascii(text: str) -> str:
    """Normaliza texto para comparacao de marcadores de posicionamento."""
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower()


class EphemeralDuckDBMedallionLake:
    """
    Gerenciador do Data Lake Analitico Efemero em DuckDB com limpeza Zero-Footprint garantida.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        memory_only: bool = False,
        hmac_secret_key: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.settings = settings_override or load_settings()
        self.storage = ZeroFootprintStorage()
        self.memory_only = memory_only
        self._ephemeral_files: List[Path] = []

        if self.memory_only:
            self.db_path = ":memory:"
            self._local_db_file: Optional[Path] = None
        elif db_path is not None:
            self.db_path = str(db_path)
            self._local_db_file = Path(db_path)
            self._ephemeral_files.append(self._local_db_file)
        else:
            ts_str = datetime.now().strftime('%H%M%S%f')
            self._local_db_file = self.storage.get_temp_path(f"duckdb_medallion_lake_{os.getpid()}_{ts_str}.duckdb")
            self.db_path = str(self._local_db_file)
            self._ephemeral_files.append(self._local_db_file)

        # Conecta ao DuckDB com limites estritos para o MacBook
        self.conn = duckdb.connect(self.db_path)
        self.conn.execute("SET memory_limit = '512MB';")
        self.conn.execute("SET threads = 2;")

        # Motores da Fase 01 reutilizados
        self.cleaner = LGPDCleanerAndCIBGraphEngine(
            hmac_secret_key=hmac_secret_key,
            settings_override=self.settings,
        )
        self.sampler = ObservedUniverseStratifiedSampler()
        self.stat_engine = DigitalDiscourseStatisticalEngine(settings_override=self.settings)

        self._init_medallion_tables()

    def __enter__(self) -> "EphemeralDuckDBMedallionLake":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close_and_purge()

    def _init_medallion_tables(self) -> None:
        """Cria as tabelas das 3 camadas colunares no DuckDB."""
        # 1. Camada Bronze: Ingestao sanitizada
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bronze_sanitized_ingest (
                comment_id VARCHAR PRIMARY KEY,
                theme_id VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                author_id_hash VARCHAR NOT NULL,
                hmac_key_id VARCHAR NOT NULL,
                created_at_utc TIMESTAMP NOT NULL,
                created_at_brt VARCHAR NOT NULL,
                shift_brt VARCHAR NOT NULL,
                day_brt VARCHAR NOT NULL,
                sanitized_text VARCHAR NOT NULL,
                shared_urls_json VARCHAR,
                hashtags_json VARCHAR,
                DDD_proxy VARCHAR,
                Macroregion_proxy VARCHAR,
                collection_query_used VARCHAR NOT NULL,
                collector_modality VARCHAR NOT NULL
            );
        """)

        # 2. Camada Silver: Comentarios classificados e Quadro de Contas
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS silver_comments_classified (
                comment_id VARCHAR PRIMARY KEY,
                theme_id VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                author_id_hash VARCHAR NOT NULL,
                created_at_utc TIMESTAMP NOT NULL,
                created_at_brt VARCHAR NOT NULL,
                shift_brt VARCHAR NOT NULL,
                day_brt VARCHAR NOT NULL,
                sanitized_text VARCHAR NOT NULL,
                stance_label VARCHAR NOT NULL,
                activity_class VARCHAR NOT NULL,
                is_commercial_spam BOOLEAN NOT NULL,
                spam_quarantine_reason VARCHAR,
                repetition_class VARCHAR,
                inauthenticity_index DOUBLE,
                account_suspected_cib BOOLEAN NOT NULL,
                cib_cluster_id VARCHAR
            );
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS silver_organic_accounts_frame (
                account_key VARCHAR PRIMARY KEY,
                theme_id VARCHAR NOT NULL,
                author_id_hash VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                modal_shift VARCHAR NOT NULL,
                modal_day VARCHAR NOT NULL,
                stratum_key VARCHAR NOT NULL,
                post_count INTEGER NOT NULL,
                Macroregion_proxy VARCHAR NOT NULL,
                inclusion_prob DOUBLE NOT NULL,
                design_weight DOUBLE NOT NULL,
                fpc_factor DOUBLE NOT NULL
            );
        """)

        # 3. Camada Gold: Amostra sorteada (sem texto) e Estimativas dos Cenarios
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_sampled_organic_accounts (
                account_key VARCHAR PRIMARY KEY,
                theme_id VARCHAR NOT NULL,
                platform VARCHAR NOT NULL,
                author_id_hash VARCHAR NOT NULL,
                stratum_key VARCHAR NOT NULL,
                created_at_hour_utc TIMESTAMP,
                stratum_pop_N INTEGER NOT NULL,
                stratum_sample_n INTEGER NOT NULL,
                inclusion_prob DOUBLE NOT NULL,
                design_weight DOUBLE NOT NULL,
                raking_weight DOUBLE NOT NULL,
                stance_label VARCHAR NOT NULL
            );
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS gold_scenario_estimates (
                metric_id VARCHAR PRIMARY KEY,
                theme_id VARCHAR NOT NULL,
                total_organic_accounts INTEGER NOT NULL,
                sampled_accounts INTEGER NOT NULL,
                c1_unweighted_fav DOUBLE,
                c1_unweighted_against DOUBLE,
                c1_unweighted_neutral DOUBLE,
                c2_equal_plat_fav DOUBLE,
                c2_equal_plat_against DOUBLE,
                c2_equal_plat_neutral DOUBLE,
                c3_raking_fav DOUBLE,
                c3_raking_against DOUBLE,
                c3_raking_neutral DOUBLE,
                c1_rogan_gladen_fav DOUBLE,
                c1_rogan_gladen_against DOUBLE,
                c1_rogan_gladen_neutral DOUBLE,
                kish_deff DOUBLE,
                effective_n DOUBLE,
                internal_uncertainty_pp DOUBLE,
                calibration_status VARCHAR,
                calculated_at TIMESTAMP NOT NULL
            );
        """)

    def ingest_to_bronze_and_sanitize(
        self,
        manifestations: Sequence[RawCollectedManifestation],
    ) -> int:
        """
        Ingere manifestacoes na Camada Bronze aplicando redacao de PII e HMAC-SHA256 em streaming.
        O raw_author_id e descartado imediatamente da memoria e NUNCA e persistido.
        """
        if not manifestations:
            return 0

        rows = []
        for m in manifestations:
            # 1. Pseudonimizacao HMAC-SHA256 irreversivel (LGPD Art. 13, §4o)
            author_hash = self.cleaner.anonymize_platform_account(m.platform, m.raw_author_id)
            hmac_key_id = self.cleaner.key_id

            # 2. Extracao de proxy geografico a partir de DDD (ANTES da redacao de telefone)
            phone_hint = m.phone_or_location_hint
            if not phone_hint and m.text:
                phone_match = PHONE_PATTERN.search(m.text)
                if phone_match:
                    phone_hint = phone_match.group(0)

            ddd_proxy, region_proxy = self.cleaner.extract_geographic_proxy_from_ddd(
                phone_hint or m.text
            )

            # 3. Redacao de PII no texto do comentario
            sanitized_txt = BaseLexicallyNeutralCollector.redact_pii_from_text(m.text)

            # 4. Normalizacao de data/hora para UTC e fuso horario de Brasilia
            dt_utc = BaseLexicallyNeutralCollector.normalize_timestamp_utc(m.created_at)
            dt_utc_naive = dt_utc.astimezone(timezone.utc).replace(tzinfo=None)
            dt_brt = to_brazil_timezone(dt_utc)
            shift_brt = get_time_slice_stratum(dt_brt)
            day_brt = dt_brt.strftime("%Y-%m-%d")
            created_at_brt_str = dt_brt.isoformat()

            rows.append((
                m.comment_id,
                m.theme_id,
                m.platform,
                author_hash,
                hmac_key_id,
                dt_utc_naive,
                created_at_brt_str,
                shift_brt,
                day_brt,
                sanitized_txt,
                json.dumps(m.shared_urls or [], ensure_ascii=False),
                json.dumps(m.hashtags or [], ensure_ascii=False),
                ddd_proxy,
                region_proxy,
                m.collection_query_used,
                m.collector_modality,
            ))

        self.conn.executemany("""
            INSERT OR REPLACE INTO bronze_sanitized_ingest VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

        return len(rows)

    def build_silver_layer(self, theme_id: str) -> Dict[str, int]:
        """
        Processa os dados da Bronze com o pipeline da Fase 01, gerando:
        - `silver_comments_classified` (todas as postagens com rotulos forenses)
        - `silver_organic_accounts_frame` (quadro U_Org com probabilidades pi_i e pesos d_i)
        """
        raw_rows = self.conn.execute("""
            SELECT comment_id, theme_id, platform, author_id_hash, hmac_key_id,
                   created_at_utc, created_at_brt, shift_brt, day_brt, sanitized_text,
                   shared_urls_json, hashtags_json, DDD_proxy, Macroregion_proxy,
                   collection_query_used, collector_modality
            FROM bronze_sanitized_ingest
            WHERE theme_id = ?
            ORDER BY created_at_utc ASC
        """, [theme_id]).fetchall()

        if not raw_rows:
            return {"silver_comments": 0, "organic_accounts": 0}

        # Carrega taxonomia de posicionamento especifica do tema em settings.yaml (C-04)
        themes_list = self.settings.get("pilot_themes", [])
        themes_map = {t["id"]: t for t in themes_list if isinstance(t, dict) and "id" in t}
        theme_cfg = themes_map.get(theme_id) or self.settings.get("legislative_themes", {}).get(theme_id, {})
        nlp_tax = theme_cfg.get("nlp_stance_taxonomy", {})
        favorable_markers = [normalize_text_ascii(m) for m in nlp_tax.get("favorable_markers", [])]
        against_markers = [normalize_text_ascii(m) for m in nlp_tax.get("against_markers", [])]

        gen_fav = ["vote sim", "apoio", "favor", "proteger direitos", "transparencia", "governanca algoritmica"]
        gen_against = ["vote nao", "vote não", "rejeitem", "contra", "derrubem", "censura"]
        all_fav = favorable_markers + [m for m in gen_fav if m not in favorable_markers]
        all_against = against_markers + [m for m in gen_against if m not in against_markers]

        posts_to_audit = []
        for r in raw_rows:
            txt_norm = normalize_text_ascii(r[9])
            fav_hits = sum(1 for m in all_fav if m in txt_norm)
            against_hits = sum(1 for m in all_against if m in txt_norm)
            if fav_hits > against_hits:
                stance = "Favoravel"
            elif against_hits > fav_hits:
                stance = "Contrario"
            else:
                stance = "Neutro"

            ts = r[5]
            if isinstance(ts, datetime) and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            # Deserializa shared_urls_json (r[10]) e hashtags_json (r[11])
            try:
                urls = json.loads(r[10]) if r[10] else []
            except Exception:
                urls = []
            try:
                tags = json.loads(r[11]) if r[11] else []
            except Exception:
                tags = []

            p = SocialPost(
                post_id=r[0],
                platform=r[2],
                raw_author_id="",
                timestamp=ts,
                text=r[9],
                shared_url=urls[0] if urls else None,
                hashtags=tags,
                stance=stance,
                phone_or_location_hint=r[12] if r[12] != "NI" else None,
                uf_proxy=r[12],
                region_proxy=r[13],
            )
            p.author_hash = r[3]
            p.hmac_key_id = r[4]
            posts_to_audit.append(p)

        # 1. Executa classificacao de Spam, LSH e Grafo CIB da Fase 01
        audited_posts = self.cleaner.process_and_audit_posts(posts_to_audit)

        # 2. Persiste em silver_comments_classified
        silver_comment_rows = []
        for p, r in zip(audited_posts, raw_rows):
            silver_comment_rows.append((
                p.post_id,
                theme_id,
                p.platform,
                p.author_hash,
                r[5],
                r[6],
                r[7],
                r[8],
                p.text,
                p.stance,
                p.activity_class,
                p.is_commercial_spam,
                p.spam_quarantine_reason or "",
                "LSH_NEAR_DUPLICATE" if getattr(p, "is_near_duplicate_lsh", False) else "UNIQUE_EXPRESSION",
                float(getattr(p, "coordination_signal_index", 0.0)),
                bool(p.account_suspected_cib),
                str(getattr(p, "leiden_community_id", "") or ""),
            ))

        if silver_comment_rows:
            self.conn.executemany("""
                INSERT OR REPLACE INTO silver_comments_classified VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, silver_comment_rows)

        # 3. Constroi o Quadro de Contas Organicas (U_Org)
        organic_frame = self.sampler.build_organic_account_frame(audited_posts)
        silver_account_rows = []
        for u in organic_frame:
            account_key = f"{theme_id}:{u.platform}:{u.author_hash}"
            silver_account_rows.append((
                account_key,
                theme_id,
                u.author_hash,
                u.platform,
                u.modal_time_stratum,
                u.modal_day_str,
                u.stratum_key,
                int(u.posts_count),
                u.region_proxy,
                float(u.inclusion_probability_pi),
                float(u.design_weight_d),
                float(getattr(u, "fpc_factor", 1.0)),
            ))

        if silver_account_rows:
            self.conn.executemany("""
                INSERT OR REPLACE INTO silver_organic_accounts_frame VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, silver_account_rows)

        return {
            "silver_comments": len(silver_comment_rows),
            "organic_accounts": len(silver_account_rows),
        }

    def get_silver_stratum_summary_sql(self, theme_id: str) -> List[Dict[str, Any]]:
        """
        Executa agregacao analitica SQL nativa no DuckDB para obter o perfil estratificado de U_Org.
        """
        query = """
            SELECT
                platform,
                modal_shift,
                stratum_key,
                COUNT(*) AS stratum_pop_N,
                ROUND(AVG(post_count), 2) AS avg_posts_per_account,
                ROUND(AVG(design_weight), 3) AS mean_design_weight,
                ROUND(MIN(inclusion_prob), 4) AS min_inclusion_prob
            FROM silver_organic_accounts_frame
            WHERE theme_id = ?
            GROUP BY platform, modal_shift, stratum_key
            ORDER BY platform, stratum_key;
        """
        res = self.conn.execute(query, [theme_id]).fetchall()
        cols = ["platform", "modal_shift", "stratum_key", "stratum_pop_N", "avg_posts_per_account", "mean_design_weight", "min_inclusion_prob"]
        return [dict(zip(cols, row)) for row in res]

    def build_gold_layer_and_export_parquet(
        self,
        theme_id: str,
        target_sample_size: Optional[int] = None,
        bootstrap_iterations: int = 300,
        output_parquet_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Executa a alocacao amostral de Hamilton, infere os 3 cenarios estatisticos e exporta
        a Camada Gold para Parquet ZSTD SEM a coluna de texto literal (protecao contra reidentificacao).
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", theme_id):
            raise ValueError(f"Identificador de tema legislativo invalido para exportacao SQL: '{theme_id}'")

        # 1. Recupera as contas organicas e comentarios limpos
        accounts_raw = self.conn.execute("""
            SELECT account_key, author_id_hash, platform, modal_shift, modal_day,
                   stratum_key, post_count, Macroregion_proxy, inclusion_prob, design_weight, fpc_factor
            FROM silver_organic_accounts_frame
            WHERE theme_id = ?
        """, [theme_id]).fetchall()

        if not accounts_raw:
            raise ValueError(f"Nenhuma conta organica encontrada na Camada Silver para o tema '{theme_id}'.")

        # Converte para lista de SocialPost auditados com Macroregion_proxy da Bronze
        comments_raw = self.conn.execute("""
            SELECT s.comment_id, s.platform, s.author_id_hash, s.created_at_utc, s.sanitized_text, s.stance_label,
                   s.activity_class, s.is_commercial_spam, s.account_suspected_cib, b.Macroregion_proxy
            FROM silver_comments_classified s
            LEFT JOIN bronze_sanitized_ingest b ON s.comment_id = b.comment_id
            WHERE s.theme_id = ?
        """, [theme_id]).fetchall()

        posts = []
        author_historical_timestamps: Dict[str, datetime] = {}
        for cr in comments_raw:
            ts = cr[3]
            if isinstance(ts, datetime) and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            auth_h = cr[2]
            if auth_h not in author_historical_timestamps or (isinstance(ts, datetime) and ts < author_historical_timestamps[auth_h]):
                author_historical_timestamps[auth_h] = ts

            sp = SocialPost(
                post_id=cr[0],
                platform=cr[1],
                raw_author_id="",
                timestamp=ts,
                text=cr[4],
                stance=cr[5],
                region_proxy=cr[9] or "Nao Identificado",
            )
            sp.author_hash = auth_h
            sp.activity_class = cr[6]
            sp.is_commercial_spam = cr[7]
            sp.account_suspected_cib = cr[8]
            sp.region_proxy = cr[9] or "Nao Identificado"
            posts.append(sp)

        # 2. Sorteio de Amostra Estratificada
        organic_frame = self.sampler.build_organic_account_frame(posts)
        pop_strata_sizes = Counter(u.stratum_key for u in organic_frame)
        n_req = target_sample_size or self.sampler.compute_required_sample_size(len(organic_frame))
        sampled_units, strata_counts = self.sampler.draw_stratified_account_sample(organic_frame, target_sample_size=n_req)
        sample_strata_sizes = Counter(u.stratum_key for u in sampled_units)

        # 3. Estimacao dos 3 Cenarios via DigitalDiscourseStatisticalEngine
        metrics = self.stat_engine.compute_verified_discourse_indicators(
            posts,
            sampled_account_units=sampled_units,
            bootstrap_iterations=bootstrap_iterations,
        )

        # 4. Raking e Insercao em gold_sampled_organic_accounts (SEM COLUNA DE TEXTO)
        sampled_plats = [u.platform for u in sampled_units]
        sampled_regs = [getattr(u, "region_proxy", "Nao Identificado") for u in sampled_units]
        calibrated_ipf_weights = self.stat_engine._compute_ipf_raking_weights(sampled_plats, sampled_regs)
        for idx, u in enumerate(sampled_units):
            w_factor = float(calibrated_ipf_weights[idx]) if idx < len(calibrated_ipf_weights) else 1.0
            u.raking_weight_w = float(u.design_weight_d * w_factor)

        gold_account_rows = []
        for u in sampled_units:
            # Timestamp real do autor truncado a hora
            raw_ts = author_historical_timestamps.get(u.author_hash)
            if raw_ts is not None:
                created_at_hour = raw_ts.replace(minute=0, second=0, microsecond=0, tzinfo=None)
            else:
                created_at_hour = datetime(2026, 10, 27, 14, 0, 0)

            n_h = int(sample_strata_sizes.get(u.stratum_key, 1))
            N_h = int(pop_strata_sizes.get(u.stratum_key, n_h))
            if N_h < n_h:
                N_h = n_h
            pi_i = float(n_h / max(1, N_h))
            d_i = float(N_h / max(1e-9, n_h))
            u.inclusion_probability_pi = pi_i
            u.design_weight_d = d_i

            w_rak = float(getattr(u, "raking_weight_w", d_i))

            gold_account_rows.append((
                f"gold_{theme_id}_{u.platform}_{u.author_hash[:16]}",
                theme_id,
                u.platform,
                u.author_hash,
                u.stratum_key,
                created_at_hour,
                N_h,
                n_h,
                pi_i,
                d_i,
                w_rak,
                Counter(u.stances).most_common(1)[0][0] if u.stances else "Neutro",
            ))

        self.conn.executemany("""
            INSERT OR REPLACE INTO gold_sampled_organic_accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, gold_account_rows)

        # 5. Persiste as estimativas resumidas
        calc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.conn.execute("""
            INSERT OR REPLACE INTO gold_scenario_estimates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"metric_{theme_id}_{calc_now.strftime('%Y%m%d_%H%M%S')}",
            theme_id,
            len(organic_frame),
            len(sampled_units),
            metrics.scenario_1_organic_unweighted_pct.get("Favoravel", 0.0),
            metrics.scenario_1_organic_unweighted_pct.get("Contrario", 0.0),
            metrics.scenario_1_organic_unweighted_pct.get("Neutro", 0.0),
            metrics.scenario_2_equal_platform_pct.get("Favoravel", 0.0),
            metrics.scenario_2_equal_platform_pct.get("Contrario", 0.0),
            metrics.scenario_2_equal_platform_pct.get("Neutro", 0.0),
            metrics.scenario_3_reweighted_sensitivity_pct.get("Favoravel", 0.0),
            metrics.scenario_3_reweighted_sensitivity_pct.get("Contrario", 0.0),
            metrics.scenario_3_reweighted_sensitivity_pct.get("Neutro", 0.0),
            metrics.rogan_gladen_corrected_c1_pct.get("Favoravel", 0.0),
            metrics.rogan_gladen_corrected_c1_pct.get("Contrario", 0.0),
            metrics.rogan_gladen_corrected_c1_pct.get("Neutro", 0.0),
            float(metrics.kish_design_effect_deff),
            float(metrics.effective_sample_size_n_eff),
            float(metrics.internal_statistical_uncertainty_pp),
            metrics.scenario_3_calibration_status,
            calc_now,
        ))

        # 6. Exportacao para Parquet ZSTD
        ts_str = datetime.now().strftime('%H%M%S%f')
        if output_parquet_path is not None:
            target_parquet = output_parquet_path
        else:
            target_parquet = self.storage.get_temp_path(f"gold_{theme_id}_{os.getpid()}_{ts_str}.parquet")
            self._ephemeral_files.append(target_parquet)

        export_sql = f"COPY (SELECT * FROM gold_sampled_organic_accounts WHERE theme_id = '{theme_id}') TO '{target_parquet}' (FORMAT PARQUET, COMPRESSION ZSTD);"
        self.conn.execute(export_sql)

        r_script = self.generate_r_survey_companion_script(str(target_parquet.name))

        return {
            "theme_id": theme_id,
            "parquet_path": str(target_parquet),
            "parquet_bytes": target_parquet.stat().st_size if target_parquet.exists() else 0,
            "sampled_accounts_n": len(sampled_units),
            "total_organic_N": len(organic_frame),
            "internal_uncertainty_pp": metrics.internal_statistical_uncertainty_pp,
            "calibration_status": metrics.scenario_3_calibration_status,
            "r_companion_script": r_script,
        }

    @staticmethod
    def generate_r_survey_companion_script(parquet_filename: str) -> str:
        """
        Gera script R canonico com o pacote `survey` para auditoria estatistica e inferencia.
        """
        return f"""# ==============================================================================
# Script Companheiro de Auditoria Estatistica e Inferencia em R (DataSenado / TCC)
# Leitura direta do Parquet ZSTD Gold gerado pelo DuckDB Medallion Lake
# ==============================================================================

library(arrow)
library(survey)

# 1. Carrega dados amostrais sem expor PII ou texto literal (Zero-Footprint)
df <- arrow::read_parquet("{parquet_filename}")

# 2. Instancia o objeto de desenho amostral complexo estratificado (C-01 / E-06)
#    - IDs = ~1 (amostragem de elementos/contas unicas)
#    - Estratos = ~stratum_key (Platform | Turno)
#    - Pesos = ~design_weight (d_i = 1 / pi_i)
#    - FPC = ~stratum_pop_N (Correcao de Populacao Finita de Cochran)
svy_design <- survey::svydesign(
  ids = ~1,
  strata = ~stratum_key,
  weights = ~design_weight,
  fpc = ~stratum_pop_N,
  data = df,
  nest = TRUE
)

# 3. Estimativa Pontual e Erros-Padrao com Correcao de FPC
c1_means <- survey::svymean(~stance_label, svy_design)
print("=== Proporcoes Estimadas Cenário 1 (U_Org com FPC) ===")
print(c1_means)
print(confint(c1_means))

# 4. Teste de Homogeneidade entre Plataformas (Rao-Scott F de 2a ordem)
rao_scott_test <- survey::svychisq(~stance_label + platform, svy_design, statistic = "F")
print("=== Teste de Homogeneidade Rao-Scott F ===")
print(rao_scott_test)
"""

    def close_and_purge(self) -> None:
        """Fecha a conexao e limpa apenas os arquivos efemeros criados por esta instancia garantindo 0 KB."""
        try:
            self.conn.close()
        except Exception:
            pass

        if self._local_db_file:
            wal_file = Path(f"{self._local_db_file}.wal")
            try:
                self._local_db_file.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                wal_file.unlink(missing_ok=True)
            except Exception:
                pass

        for p in self._ephemeral_files:
            try:
                if p.exists():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
