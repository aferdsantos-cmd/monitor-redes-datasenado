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
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import duckdb
import numpy as np

from src.cleaning.lgpd_and_bot_filter import (
    LGPDCleanerAndCIBGraphEngine,
    SocialPost,
)
from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
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

        if self.memory_only:
            self.db_path = ":memory:"
            self._local_db_file: Optional[Path] = None
        elif db_path is not None:
            self.db_path = str(db_path)
            self._local_db_file = Path(db_path)
        else:
            ts_str = datetime.now().strftime('%H%M%S%f')
            self._local_db_file = self.storage.get_temp_path(f"duckdb_medallion_lake_{os.getpid()}_{ts_str}.duckdb")
            self.db_path = str(self._local_db_file)

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

            # 2. Redacao de PII no texto do comentario
            sanitized_txt = BaseLexicallyNeutralCollector.redact_pii_from_text(m.text)

            # 3. Normalizacao de data/hora para UTC e fuso horario de Brasilia
            dt_utc = BaseLexicallyNeutralCollector.normalize_timestamp_utc(m.created_at)
            dt_utc_naive = dt_utc.astimezone(timezone.utc).replace(tzinfo=None)
            dt_brt = to_brazil_timezone(dt_utc)
            shift_brt = get_time_slice_stratum(dt_brt)
            day_brt = dt_brt.strftime("%Y-%m-%d")
            created_at_brt_str = dt_brt.isoformat()

            # 4. Extracao de proxy geografico a partir de DDD
            ddd_proxy, region_proxy = self.cleaner.extract_geographic_proxy_from_ddd(
                m.phone_or_location_hint or sanitized_txt
            )

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

        posts_to_audit = []
        for r in raw_rows:
            # Reconhece stance preliminar por palavras-chave neutras ou padrão
            txt_lower = r[9].lower()
            if any(w in txt_lower for w in ("vote sim", "apoio", "favor", "proteger direitos", "transparência")):
                stance = "Favoravel"
            elif any(w in txt_lower for w in ("vote não", "vote nao", "rejeitem", "contra", "derrubem", "censura")):
                stance = "Contrario"
            else:
                stance = "Neutro"

            ts = r[5]
            if isinstance(ts, datetime) and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            p = SocialPost(
                post_id=r[0],
                platform=r[2],
                raw_author_id="",
                timestamp=ts,
                text=r[9],
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
        # 1. Recupera as contas organicas e comentarios limpos
        accounts_raw = self.conn.execute("""
            SELECT account_key, author_id_hash, platform, modal_shift, modal_day,
                   stratum_key, post_count, Macroregion_proxy, inclusion_prob, design_weight, fpc_factor
            FROM silver_organic_accounts_frame
            WHERE theme_id = ?
        """, [theme_id]).fetchall()

        if not accounts_raw:
            raise ValueError(f"Nenhuma conta organica encontrada na Camada Silver para o tema '{theme_id}'.")

        # Converte para lista de SocialPost auditados
        comments_raw = self.conn.execute("""
            SELECT comment_id, platform, author_id_hash, created_at_utc, sanitized_text, stance_label,
                   activity_class, is_commercial_spam, account_suspected_cib
            FROM silver_comments_classified
            WHERE theme_id = ?
        """, [theme_id]).fetchall()

        posts = []
        for cr in comments_raw:
            sp = SocialPost(
                post_id=cr[0],
                platform=cr[1],
                raw_author_id="",
                timestamp=cr[3],
                text=cr[4],
                stance=cr[5],
            )
            sp.author_hash = cr[2]
            sp.activity_class = cr[6]
            sp.is_commercial_spam = cr[7]
            sp.account_suspected_cib = cr[8]
            posts.append(sp)

        # 2. Sorteio de Amostra Estratificada
        organic_frame = self.sampler.build_organic_account_frame(posts)
        n_req = target_sample_size or self.sampler.compute_required_sample_size(len(organic_frame))
        sampled_units, strata_counts = self.sampler.draw_stratified_account_sample(organic_frame, target_sample_size=n_req)

        # 3. Estimacao dos 3 Cenarios via DigitalDiscourseStatisticalEngine
        metrics = self.stat_engine.compute_verified_discourse_indicators(
            posts,
            sampled_account_units=sampled_units,
            bootstrap_iterations=bootstrap_iterations,
        )

        # 4. Raking e Insercao em gold_sampled_organic_accounts (SEM COLUNA DE TEXTO)
        gold_account_rows = []
        for u in sampled_units:
            # Timestamp truncado a hora para maxima privacidade
            created_at_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0, tzinfo=None)
            gold_account_rows.append((
                f"gold_{theme_id}_{u.platform}_{u.author_hash[:16]}",
                theme_id,
                u.platform,
                u.author_hash,
                u.stratum_key,
                created_at_hour,
                strata_counts.get(u.stratum_key, len(organic_frame)),
                len(sampled_units),
                float(u.inclusion_probability_pi),
                float(u.design_weight_d),
                float(getattr(u, "raking_weight_w", u.design_weight_d)),
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
        target_parquet = output_parquet_path or self.storage.get_temp_path(f"gold_{theme_id}_{os.getpid()}_{ts_str}.parquet")
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
        """Fecha a conexao e limpa qualquer arquivo residual em /tmp garantindo 0 KB."""
        try:
            self.conn.close()
        except Exception:
            pass

        if self._local_db_file and self._local_db_file.exists():
            try:
                self._local_db_file.unlink(missing_ok=True)
            except Exception:
                pass

        # Limpeza de qualquer arquivo parquet ou wal orfao no cache temporario
        cache_dir = Path("/tmp/monitor_datasenado_cache")
        if cache_dir.exists():
            for f in cache_dir.glob("duckdb_medallion_lake*"):
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    pass
            for f in cache_dir.glob("gold_*.parquet"):
                try:
                    f.unlink(missing_ok=True)
                except Exception:
                    pass
