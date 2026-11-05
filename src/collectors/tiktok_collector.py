"""
Conector Oficial e Auditável para TikTok via Research API e Ingestão Passiva.

Atende às exigências da Fase 03, ADR-006, ADR-008 e ADR-010:
1. Suporte à TikTok Research API (/v2/research/video/comment/list/) com ordenação estritamente cronológica ('create_time' / 'time');
2. Bloqueio com ValueError para qualquer ordenação algorítmica por popularidade ou likes ('relevance', 'likes', 'popular');
3. Mascaramento automático de tokens de cliente em logs e exceções HTTP;
4. Injeção de transporte HTTP para testes herméticos com pegada zero;
5. Suporte a metadados de co-engajamento, bolhas e espectros (ADR-010).
"""

from datetime import datetime, timedelta, timezone
import json
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import urllib.error
import urllib.parse
import urllib.request

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
    get_dynamic_theme_samples,
)

TIKTOK_RESEARCH_API_URL = "https://open.tiktokapis.com/v2/research/video/comment/list/"


class TikTokResearchCollector(BaseLexicallyNeutralCollector):
    """
    Coletor para TikTok via Research API oficial para pesquisadores e Ingestão Passiva.
    """

    platform = "tiktok"

    def __init__(
        self,
        client_token: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
        http_get_json: Optional[Callable[[str, Dict[str, Any], Dict[str, str]], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(settings_override=settings_override)
        self.client_token = (
            client_token
            or os.environ.get("TIKTOK_CLIENT_TOKEN")
            or os.environ.get("TIKTOK_BEARER_TOKEN")
        )
        self.http_get_json = http_get_json

    def enforce_chronological_order(self, order: Optional[str] = "create_time") -> str:
        """
        Valida que a ordenação na TikTok Research API é estritamente cronológica ('create_time' ou 'time').
        Lança ValueError para qualquer ordenação vazia, None ou algorítmica por likes ou relevância.
        """
        if order is None or not isinstance(order, str) or not order.strip():
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO NO TIKTOK: order não pode ser vazio ou None. "
                "Use exclusivamente 'create_time' ou 'time'!"
            )
        norm = order.strip().lower()
        if norm not in ("create_time", "time"):
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO NO TIKTOK: Coleta observacional na Research API "
                f"deve usar exclusivamente 'create_time' ou 'time', nunca '{order}'!"
            )
        return norm

    def _execute_api_post(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Executa requisição com proteção contra exposição de token de cliente."""
        if self.http_get_json is not None:
            # Reutiliza o mock injetado mesmo que seja post
            return self.http_get_json(url, payload, headers)

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            safe_err = err_body
            if self.client_token:
                safe_err = safe_err.replace(self.client_token, "[REDACTED_TIKTOK_TOKEN]")
            raise RuntimeError(f"Erro na TikTok Research API (HTTP {e.code}): {safe_err}")

    def collect_video_comments_research_api(
        self,
        theme_id: str,
        query: str,
        video_id: str,
        max_count: int = 25,
        order: str = "create_time",
        client_token: Optional[str] = None,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade A: Coleta comentários de vídeo via Research API oficial.
        """
        self.validate_query_lexical_neutrality(theme_id, query)
        enforced_order = self.enforce_chronological_order(order)

        token = client_token or self.client_token
        if not token and self.http_get_json is None:
            raise RuntimeError("TIKTOK_CLIENT_TOKEN ausente e nenhum http_get_json injetado.")

        headers = {
            "Authorization": f"Bearer {token or 'mock_token'}",
            "Content-Type": "application/json",
            "User-Agent": "DataSenado-TikTok-Monitor/3.0",
        }
        payload: Dict[str, Any] = {
            "video_id": int(video_id) if video_id.isdigit() else video_id,
            "max_count": min(100, max(1, max_count)),
            "order": enforced_order,
        }

        resp = self._execute_api_post(TIKTOK_RESEARCH_API_URL, payload, headers)
        data = resp.get("data", {})
        comments = data.get("comments", [])

        collected: List[RawCollectedManifestation] = []
        for c in comments:
            text = c.get("text", "")
            c_id = str(c.get("id", f"tt_c_{len(collected)}"))
            user_id = str(c.get("parent_comment_id") or c.get("user_id") or f"tt_user_{c_id}")

            # Converte epoch timestamp para datetime UTC
            create_time = c.get("create_time")
            if isinstance(create_time, (int, float)) and create_time > 0:
                dt = datetime.fromtimestamp(create_time, tz=timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            urls = self.extract_urls(text)
            tags = self.extract_hashtags(text)
            news_domains = []
            for u in urls:
                try:
                    dom = urllib.parse.urlparse(u).netloc.lower()
                    if dom.startswith("www."):
                        dom = dom[4:]
                    if dom and dom not in news_domains:
                        news_domains.append(dom)
                except Exception:
                    pass

            collected.append(
                RawCollectedManifestation(
                    comment_id=f"tt_{c_id}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"tt_{user_id}",
                    text=text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=query,
                    collector_modality="official_api_chronological",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=c.get("phone_or_location_hint"),
                    metadata={
                        "comment_id": c_id,
                        "video_id": video_id,
                        "like_count": c.get("like_count", 0),
                        "reply_count": c.get("reply_count", 0),
                        "exponent_seed_id": f"tt_vid_{video_id}",
                        "spectrum_seed_hint": c.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    def collect_from_tiktok_json_export(
        self,
        export_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        theme_id: str,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade B: Ingestão de exportações JSON passivas de vídeos e comentários do TikTok.
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        if isinstance(export_data, dict):
            raw_items = export_data.get("comments") or export_data.get("data", {}).get("comments", []) or [export_data]
            video_id = export_data.get("video_id", "tt_export_vid")
        else:
            raw_items = export_data
            video_id = "tt_export_vid"

        collected: List[RawCollectedManifestation] = []
        for item in raw_items:
            text = item.get("text") or item.get("comment", "")
            if not text:
                continue

            norm_text = _normalize_text_for_matching(text)
            matched_query: Optional[str] = None
            for orig_q, n_q in zip(allowed_queries, norm_queries):
                if n_q in norm_text:
                    matched_query = orig_q
                    break

            if not matched_query:
                continue

            c_id = str(item.get("id", f"tt_exp_{len(collected) + 1}"))
            user_id = str(item.get("user_id") or item.get("username") or f"tt_user_{c_id}")

            create_time = item.get("create_time")
            if isinstance(create_time, (int, float)) and create_time > 0:
                dt = datetime.fromtimestamp(create_time, tz=timezone.utc)
            elif item.get("date"):
                try:
                    dt = datetime.fromisoformat(item["date"]).replace(tzinfo=timezone.utc)
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            urls = self.extract_urls(text)
            tags = self.extract_hashtags(text)
            news_domains = []
            for u in urls:
                try:
                    dom = urllib.parse.urlparse(u).netloc.lower()
                    if dom.startswith("www."):
                        dom = dom[4:]
                    if dom and dom not in news_domains:
                        news_domains.append(dom)
                except Exception:
                    pass

            collected.append(
                RawCollectedManifestation(
                    comment_id=f"tt_{c_id}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"tt_{user_id}",
                    text=text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=item.get("phone_or_location_hint"),
                    metadata={
                        "comment_id": c_id,
                        "video_id": video_id,
                        "exponent_seed_id": item.get("exponent_seed_id", f"tt_seed_{video_id}"),
                        "spectrum_seed_hint": item.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    @staticmethod
    def generate_mock_tiktok_response(
        theme_id: str = "pl_ia_2338",
        video_id: str = "7298374928374",
        count: int = 25,
        span_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Gera payload no formato oficial da TikTok Research API distribuído em span_days.
        """
        base_dt = datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)
        samples = get_dynamic_theme_samples(theme_id)

        spectra = ["espectro_progressista", "espectro_conservador", "espectro_centro_institucional", "espectro_tecnico_setorial"]
        exponents = ["exp_senado_tiktok", "exp_criador_trabalhista", "exp_canal_empreender", "exp_tech_creator"]
        sample_ddds = ["+55 (11) 98765-4321", "+55 (21) 99888-7766", "+55 (71) 98111-2233", "+55 (41) 99222-3344", "+55 (61) 98333-4455", "+55 (92) 99444-5566"]

        comments = []
        for i in range(count):
            day_offset = i % max(1, span_days)
            dt = base_dt - timedelta(days=day_offset, hours=(i * 2) % 24, minutes=(i * 13) % 60)
            epoch_sec = int(dt.timestamp())
            text = samples[i % len(samples)]
            spec = spectra[i % len(spectra)]
            exp = exponents[i % len(exponents)]
            geo_hint = sample_ddds[i % len(sample_ddds)]

            comments.append({
                "id": 8392819280 + i,
                "video_id": int(video_id) if video_id.isdigit() else 7298374928374,
                "text": text,
                "like_count": i * 15,
                "reply_count": i % 4,
                "parent_comment_id": 0,
                "create_time": epoch_sec,
                "phone_or_location_hint": geo_hint,
                "exponent_seed_id": exp,
                "spectrum_seed_hint": spec,
            })

        return {
            "data": {
                "comments": comments,
                "cursor": 25,
                "has_more": False,
            },
            "error": {"code": "OK", "message": ""},
        }
