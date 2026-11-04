"""
Conector Oficial da YouTube Data API v3 com Ordenacao Cronologica Antivies (Fase 02).

Implementa a trava estrita de ordenacao cronologica (order='time' e order='date'),
bloqueando qualquer tentativa de captura por relevancia (order='relevance') que introduziria
vieses de engajamento algoritmico da plataforma (Achado E-02 / ADR-006).
"""

from datetime import datetime, timezone
import json
import os
import re
from typing import Any, Callable, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
)

YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeOfficialCollector(BaseLexicallyNeutralCollector):
    """
    Coletor oficial do YouTube com garantia de neutralidade lexical e ordenacao cronologica.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        http_get_json: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(settings_override=settings_override)
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
        self.http_get_json = http_get_json

    def _execute_api_get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa chamada GET na YouTube API v3 via transporte injetado ou urllib padrao."""
        if self.http_get_json is not None:
            return self.http_get_json(endpoint, params)

        if not self.api_key:
            raise RuntimeError(
                "YOUTUBE_API_KEY ausente no ambiente e nenhuma funcao http_get_json injetada."
            )

        query_params = dict(params)
        query_params["key"] = self.api_key
        url = f"{YOUTUBE_API_BASE_URL}/{endpoint}?" + urllib.parse.urlencode(query_params)

        req = urllib.request.Request(url, headers={"User-Agent": "DataSenado-Research-Monitor/2.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Erro na YouTube Data API v3 (HTTP {e.code}): {err_body}")

    def enforce_chronological_order(self, order: str, context: str = "commentThreads") -> str:
        """
        Valida que a ordenacao e estritamente cronologica (date ou time), rejeitando 'relevance'.
        """
        norm_order = (order or "").strip().lower()
        if norm_order == "relevance":
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO: Coleta observacional no YouTube deve usar "
                f"exclusivamente order='time' ou order='date', nunca 'relevance'! (Contexto: {context})"
            )
        if context == "search" and norm_order not in ("date", "time"):
            return "date"
        if context == "commentThreads" and norm_order not in ("time", "date"):
            return "time"
        return norm_order

    def search_videos_by_query(
        self,
        theme_id: str,
        query: str,
        max_results: int = 10,
        order: str = "date",
    ) -> List[str]:
        """
        Busca IDs de videos relevantes aplicando a trava de neutralidade lexical e order='date'.
        """
        self.validate_query_lexical_neutrality(theme_id, query)
        enforced_order = self.enforce_chronological_order(order, context="search")

        params = {
            "part": "id,snippet",
            "q": query,
            "type": "video",
            "maxResults": min(50, max_results),
            "order": enforced_order,
        }
        data = self._execute_api_get("search", params)
        video_ids = []
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid:
                video_ids.append(vid)
        return video_ids

    def parse_comment_thread_item(
        self,
        item: Dict[str, Any],
        theme_id: str,
        query_used: str,
    ) -> RawCollectedManifestation:
        """Parseia um item de commentThreads da API v3 para RawCollectedManifestation."""
        snippet = item.get("snippet", {})
        top = snippet.get("topLevelComment", {})
        top_snippet = top.get("snippet", {})

        comment_id = top.get("id") or item.get("id", "yt_unknown")
        raw_author = (
            top_snippet.get("authorChannelId", {}).get("value")
            or top_snippet.get("authorDisplayName")
            or f"yt_user_{comment_id}"
        )
        text = top_snippet.get("textOriginal") or top_snippet.get("textDisplay") or ""

        # Parse de publishedAt ISO-8601 (ex.: 2026-10-27T18:30:00Z)
        pub_raw = top_snippet.get("publishedAt")
        if pub_raw:
            try:
                dt = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        shared_urls = self.extract_urls(text)
        hashtags = self.extract_hashtags(text)

        return RawCollectedManifestation(
            comment_id=f"yt_{comment_id}",
            theme_id=theme_id,
            platform="youtube",
            raw_author_id=raw_author,
            text=text,
            created_at=self.normalize_timestamp_utc(dt),
            collection_query_used=query_used,
            collector_modality="official_api_chronological",
            shared_urls=shared_urls,
            hashtags=hashtags,
            metadata={
                "like_count": top_snippet.get("likeCount", 0),
                "total_reply_count": snippet.get("totalReplyCount", 0),
                "video_id": snippet.get("videoId", ""),
            },
        )

    def collect_comments_for_video(
        self,
        video_id: str,
        theme_id: str,
        query_used: str,
        max_comments: int = 100,
        order: str = "time",
    ) -> List[RawCollectedManifestation]:
        """
        Coleta comentarios de um video via `commentThreads.list` com paginacao e order='time'.
        """
        enforced_order = self.enforce_chronological_order(order, context="commentThreads")
        collected: List[RawCollectedManifestation] = []
        page_token: Optional[str] = None

        while len(collected) < max_comments:
            params: Dict[str, Any] = {
                "part": "snippet",
                "videoId": video_id,
                "textFormat": "plainText",
                "maxResults": min(100, max_comments - len(collected)),
                "order": enforced_order,
            }
            if page_token:
                params["pageToken"] = page_token

            data = self._execute_api_get("commentThreads", params)
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                manifestation = self.parse_comment_thread_item(item, theme_id, query_used)
                collected.append(manifestation)
                if len(collected) >= max_comments:
                    break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return collected

    @staticmethod
    def generate_mock_api_v3_response(
        video_id: str,
        count: int = 15,
        theme_id: str = "pl_ia_2338",
        next_page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gera uma fixture realista no formato da YouTube Data API v3 para testes determinísticos.
        """
        items = []
        base_dt = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)
        if theme_id == "pec_escala_6x1":
            sample_texts = [
                "Excelente debate sobre a PEC da escala 6x1 no Senado Federal #Escala6x1 https://senado.leg.br/noticia",
                "Acompanhando a votacao da proposta sobre a jornada de trabalho e fim da escala 6x1 hoje #FimDaEscala6x1",
                "Sou a favor da reducao da jornada na escala 6x1 para garantir mais qualidade de vida aos trabalhadores.",
                "O debate da PEC da escala 6x1 precisa considerar a sustentabilidade economica dos setores produtivos.",
                "Transmissao ao vivo muito esclarecedora sobre a escala 6x1 e os direitos dos trabalhadores no Brasil.",
            ]
        else:
            sample_texts = [
                "Excelente debate sobre o PL 2338 no Senado Federal. Protecao de direitos e essencial! https://senado.leg.br/noticia #PL2338",
                "Acompanhando a votacao da lei da inteligencia artificial hoje. Precisamos de regras claras #MarcoLegalIA",
                "Sou contra o PL 2338/2023 se houver burocracia excessiva, mas apoio a transparencia algoritmica.",
                "O sorteio do relator do PL 2338 foi muito relevante. Assistindo a transmissao ao vivo.",
                "Regulamentacao da IA e urgente no Brasil para evitar fraudes digitais e proteger dados pessoais.",
            ]

        for i in range(count):
            t_iso = (base_dt.replace(minute=i % 60)).isoformat().replace("+00:00", "Z")
            items.append({
                "kind": "youtube#commentThread",
                "id": f"ct_{video_id}_{i}",
                "snippet": {
                    "videoId": video_id,
                    "totalReplyCount": i % 3,
                    "topLevelComment": {
                        "kind": "youtube#comment",
                        "id": f"c_{video_id}_{i}",
                        "snippet": {
                            "authorDisplayName": f"Cidadao Brasil {i}",
                            "authorChannelId": {"value": f"UC_yt_author_{i}_{video_id}"},
                            "textDisplay": sample_texts[i % len(sample_texts)],
                            "textOriginal": sample_texts[i % len(sample_texts)],
                            "likeCount": i * 2,
                            "publishedAt": t_iso,
                        },
                    },
                },
            })

        return {
            "kind": "youtube#commentThreadListResponse",
            "nextPageToken": next_page_token,
            "pageInfo": {"totalResults": count, "resultsPerPage": count},
            "items": items,
        }
