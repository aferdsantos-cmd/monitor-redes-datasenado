"""
Orquestrador Ponta a Ponta do Pipeline Medallion da Fase 02.

Integra Conectores (YouTube e Telegram) -> DuckDB (Bronze -> Silver -> Gold)
-> Estimacao dos 3 Cenarios -> Exportacao Parquet ZSTD -> Limpeza Zero-Footprint (0 KB).
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.collectors.base_collector import RawCollectedManifestation
from src.collectors.telegram_collector import TelegramPublicChannelCollector
from src.collectors.youtube_collector import YouTubeOfficialCollector
from src.config_loader import load_settings
from src.storage.duckdb_medallion_lake import EphemeralDuckDBMedallionLake


class Phase02MedallionOrchestrator:
    """
    Orquestrador unificado da Fase 02 para ingestao, saneamento, inferencia e exportacao analitica.
    """

    def __init__(
        self,
        theme_id: str = "pl_ia_2338",
        hmac_secret_key: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.theme_id = theme_id
        self.settings = settings_override or load_settings()
        self.hmac_secret_key = hmac_secret_key

        self.yt_collector = YouTubeOfficialCollector(settings_override=self.settings)
        self.tg_collector = TelegramPublicChannelCollector(settings_override=self.settings)

    def generate_pilot_synthetic_manifestations(
        self,
        theme_id: Optional[str] = None,
        youtube_count: int = 50,
        telegram_count: int = 50,
    ) -> List[RawCollectedManifestation]:
        """
        Gera lote representativo para o tema legislativo utilizando as fixtures oficiais dos conectores.
        """
        tid = theme_id or self.theme_id
        manifestations: List[RawCollectedManifestation] = []

        # 1. YouTube via fixture de API v3
        q_term = "PL 2338" if tid == "pl_ia_2338" else "escala 6x1"
        yt_mock = YouTubeOfficialCollector.generate_mock_api_v3_response(
            video_id=f"video_{tid}_senado",
            count=youtube_count,
            theme_id=tid,
        )
        for item in yt_mock.get("items", []):
            m = self.yt_collector.parse_comment_thread_item(item, tid, q_term)
            manifestations.append(m)

        # 2. Telegram via fixture de exportacao Desktop JSON
        tg_mock = TelegramPublicChannelCollector.generate_mock_telegram_export(
            theme_id=tid,
            count=telegram_count,
        )
        tg_items = self.tg_collector.collect_from_telegram_json_export(tg_mock, tid)
        manifestations.extend(tg_items)

        return manifestations

    def run_medallion_pipeline(
        self,
        manifestations: Optional[List[RawCollectedManifestation]] = None,
        target_sample_size: Optional[int] = None,
        cleanup_after_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa o pipeline completo:
        1. Ingestao Bronze (redacao PII + HMAC-SHA256);
        2. Processamento Silver (LSH, CIB, U_Org frame, SQL summaries);
        3. Geracao Gold (Hamilton sampling, 3 cenarios, Parquet ZSTD, R script);
        4. Limpeza Zero-Footprint.
        """
        items = manifestations or self.generate_pilot_synthetic_manifestations()

        with EphemeralDuckDBMedallionLake(
            hmac_secret_key=self.hmac_secret_key,
            settings_override=self.settings,
        ) as lake:
            # 1. Ingestao na Camada Bronze
            n_bronze = lake.ingest_to_bronze_and_sanitize(items)

            # 2. Processamento da Camada Silver
            silver_metrics = lake.build_silver_layer(self.theme_id)
            strata_summary = lake.get_silver_stratum_summary_sql(self.theme_id)

            # Contabiliza quarentena de spam e CIB via SQL
            spam_count = lake.conn.execute("""
                SELECT COUNT(*) FROM silver_comments_classified
                WHERE theme_id = ? AND is_commercial_spam = TRUE
            """, [self.theme_id]).fetchone()[0]

            cib_accounts_count = lake.conn.execute("""
                SELECT COUNT(DISTINCT author_id_hash) FROM silver_comments_classified
                WHERE theme_id = ? AND account_suspected_cib = TRUE
            """, [self.theme_id]).fetchone()[0]

            # 3. Processamento e Exportacao da Camada Gold
            gold_metrics = lake.build_gold_layer_and_export_parquet(
                self.theme_id,
                target_sample_size=target_sample_size,
            )

            # 4. Verificacao de tabelas DuckDB ativas
            tables = [t[0] for t in lake.conn.execute("SHOW TABLES;").fetchall()]

            parquet_file = Path(gold_metrics["parquet_path"])
            parquet_size = parquet_file.stat().st_size if parquet_file.exists() else 0

            result = {
                "theme_id": self.theme_id,
                "total_collected_bronze": n_bronze,
                "silver_comments_count": silver_metrics["silver_comments"],
                "organic_accounts_N": silver_metrics["organic_accounts"],
                "quarantined_spam_count": spam_count,
                "quarantined_cib_accounts": cib_accounts_count,
                "sampled_accounts_n": gold_metrics["sampled_accounts_n"],
                "duckdb_tables_verified": tables,
                "parquet_zstd_bytes": parquet_size,
                "strata_count": len(strata_summary),
                "internal_uncertainty_pp": gold_metrics["internal_uncertainty_pp"],
                "calibration_status": gold_metrics["calibration_status"],
                "r_companion_script_lines": len(gold_metrics["r_companion_script"].splitlines()),
            }

            if cleanup_after_run:
                # Remove o parquet temporario para Zero-Footprint
                parquet_file.unlink(missing_ok=True)

        # 5. Medicao do residuo em /tmp
        tmp_cache = Path("/tmp/monitor_datasenado_cache")
        residual_bytes = 0
        if tmp_cache.exists():
            for f in tmp_cache.iterdir():
                if f.is_file():
                    residual_bytes += f.stat().st_size
        result["tmp_residual_bytes"] = residual_bytes

        return result


if __name__ == "__main__":
    orchestrator = Phase02MedallionOrchestrator()
    res = orchestrator.run_medallion_pipeline()
    print("Resultado da Execucao da Fase 02 (Pipeline Medallion):")
    for k, v in res.items():
        print(f"  {k}: {v}")
