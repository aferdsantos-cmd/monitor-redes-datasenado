"""
Conector Oficial e Auditável para o X (antigo Twitter) com Neutralidade Lexical.

Atende às exigências da Fase 03, ADR-006, ADR-008 e ADR-010:
1. Coleta na API v2 (/2/tweets/search/recent) com ordenação cronológica estrita ('recency');
2. Bloqueio com ValueError para qualquer ordenação algorítmica/popularidade;
3. Mascaramento automático de credenciais (Bearer Token) em logs e exceções HTTP;
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

TWITTER_API_RECENT_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


class XTwitterCollector(BaseLexicallyNeutralCollector):
    """
    Coletor para X/Twitter via API v2 e Ingestão Passiva de Arquivos JSON.
    """

    platform = "x_twitter"

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
        http_get_json: Optional[Callable[[str, Dict[str, Any], Dict[str, str]], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(settings_override=settings_override)
        self.bearer_token = (
            bearer_token
            or os.environ.get("TWITTER_BEARER_TOKEN")
            or os.environ.get("X_BEARER_TOKEN")
        )
        self.http_get_json = http_get_json

    def enforce_chronological_sort_order(self, sort_order: Optional[str] = "recency") -> str:
        """
        Valida que a ordenação na API v2 do X é estritamente cronológica ('recency').
        Lança ValueError para qualquer ordenação vazia, None ou baseada em relevância, popularidade ou likes.
        """
        if sort_order is None or not isinstance(sort_order, str) or not sort_order.strip():
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO NO X/TWITTER: sort_order não pode ser vazio ou None. "
                "Use exclusivamente sort_order='recency'!"
            )
        norm = sort_order.strip().lower()
        if norm != "recency":
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO NO X/TWITTER: Coleta observacional na API v2 "
                f"deve usar exclusivamente sort_order='recency', nunca '{sort_order}'!"
            )
        return norm

    def _execute_api_get(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Executa chamada HTTP GET com proteção contra vazamento de credenciais."""
        try:
            if self.http_get_json is not None:
                return self.http_get_json(url, params, headers)

            full_url = f"{url}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            safe_err = err_body
            if self.bearer_token:
                safe_err = safe_err.replace(self.bearer_token, "[REDACTED_BEARER_TOKEN]")
            raise RuntimeError(f"Erro na X/Twitter API v2 (HTTP {e.code}): {safe_err}")

    def collect_recent_tweets_v2(
        self,
        theme_id: str,
        query: str,
        max_results: int = 10,
        max_pages: int = 1,
        sort_order: str = "recency",
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade A: Coleta tweets recentes via API v2 oficial do X/Twitter.
        """
        self.validate_query_lexical_neutrality(theme_id, query)
        enforced_sort = self.enforce_chronological_sort_order(sort_order)

        if not self.bearer_token and self.http_get_json is None:
            raise RuntimeError("TWITTER_BEARER_TOKEN ausente e nenhum http_get_json injetado.")

        headers = {
            "Authorization": f"Bearer {self.bearer_token or 'mock_token'}",
            "User-Agent": "DataSenado-X-Monitor/3.0",
        }

        collected: List[RawCollectedManifestation] = []
        next_token: Optional[str] = None
        pages_fetched = 0

        while pages_fetched < max_pages:
            params: Dict[str, Any] = {
                "query": query,
                "max_results": min(100, max(10, max_results)),
                "sort_order": enforced_sort,
                "tweet.fields": "created_at,author_id,entities,public_metrics,in_reply_to_user_id,referenced_tweets",
                "expansions": "author_id,referenced_tweets.id",
                "user.fields": "username,name",
            }
            if next_token:
                params["next_token"] = next_token

            data = self._execute_api_get(TWITTER_API_RECENT_SEARCH_URL, params, headers)
            pages_fetched += 1

            tweets = data.get("data", [])
            users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

            for tw in tweets:
                tw_id = tw.get("id", f"tw_anon_{len(collected)}")
                author_id = tw.get("author_id", "tw_unknown_author")
                author_user = users.get(author_id, {}).get("username") or author_id
                text = tw.get("text", "")

                # Extrai URLs expandidas das entidades da API v2
                urls: List[str] = []
                for u in tw.get("entities", {}).get("urls", []):
                    exp = u.get("expanded_url") or u.get("url")
                    if exp:
                        urls.append(exp)
                if not urls:
                    urls = self.extract_urls(text)

                # Extrai hashtags
                tags: List[str] = []
                for h in tw.get("entities", {}).get("hashtags", []):
                    t = h.get("tag")
                    if t:
                        tags.append(f"#{t}" if not t.startswith("#") else t)
                if not tags:
                    tags = self.extract_hashtags(text)

                # Extrai domínios jornalísticos das URLs compartilhadas
                news_domains: List[str] = []
                for u_str in urls:
                    try:
                        netloc = urllib.parse.urlparse(u_str).netloc.lower()
                        if netloc.startswith("www."):
                            netloc = netloc[4:]
                        if netloc and netloc not in news_domains:
                            news_domains.append(netloc)
                    except Exception:
                        pass

                # Parse de data/hora UTC
                dt_str = tw.get("created_at")
                if dt_str:
                    try:
                        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    except ValueError:
                        dt = datetime.now(timezone.utc)
                else:
                    dt = datetime.now(timezone.utc)

                pub_metrics = tw.get("public_metrics", {})
                ref_tweets = tw.get("referenced_tweets", [])
                root_ref = ref_tweets[0].get("id") if ref_tweets else None
                exponent_seed = tw.get("in_reply_to_user_id") or root_ref or f"x_seed_{author_user}"

                collected.append(
                    RawCollectedManifestation(
                        comment_id=f"x_{tw_id}",
                        theme_id=theme_id,
                        platform=self.platform,
                        raw_author_id=f"@{author_user}",
                        text=text,
                        created_at=self.normalize_timestamp_utc(dt),
                        collection_query_used=query,
                        collector_modality="official_api_chronological",
                        shared_urls=urls,
                        hashtags=tags,
                        phone_or_location_hint=tw.get("phone_or_location_hint"),
                        metadata={
                            "tweet_id": tw_id,
                            "like_count": pub_metrics.get("like_count", 0),
                            "retweet_count": pub_metrics.get("retweet_count", 0),
                            "reply_count": pub_metrics.get("reply_count", 0),
                            "quote_count": pub_metrics.get("quote_count", 0),
                            "exponent_seed_id": exponent_seed,
                            "spectrum_seed_hint": tw.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                            "shared_news_domains": news_domains,
                        },
                    )
                )

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

        return collected

    def collect_from_json_export(
        self,
        export_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        theme_id: str,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade B: Ingestão de exportações JSON passivas de tweets.
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        if isinstance(export_data, dict):
            raw_tweets = export_data.get("data") or export_data.get("tweets") or [export_data]
            users = {u["id"]: u for u in export_data.get("includes", {}).get("users", [])}
        else:
            raw_tweets = export_data
            users = {}

        collected: List[RawCollectedManifestation] = []
        for tw in raw_tweets:
            text = tw.get("text", "")
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

            tw_id = tw.get("id", f"x_exp_{len(collected) + 1}")
            author_id = tw.get("author_id") or tw.get("username") or f"x_user_{tw_id}"
            author_user = users.get(author_id, {}).get("username") or author_id

            dt_str = tw.get("created_at")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
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
                    comment_id=f"x_{tw_id}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"@{author_user}",
                    text=text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=tw.get("phone_or_location_hint"),
                    metadata={
                        "tweet_id": tw_id,
                        "exponent_seed_id": tw.get("exponent_seed_id", f"x_seed_{author_user}"),
                        "spectrum_seed_hint": tw.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    @staticmethod
    def generate_mock_x_v2_response(
        query: str = "PL 2338",
        count: int = 25,
        span_days: int = 7,
        theme_id: str = "pl_ia_2338",
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gera payload sintético com formato oficial da API v2 do X/Twitter distribuído em span_days.
        """
        base_dt = datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)
        samples = get_dynamic_theme_samples(theme_id)

        spectra = ["espectro_progressista", "espectro_conservador", "espectro_centro_institucional", "espectro_tecnico_setorial"]
        exponents = ["exp_senado_noticias", "exp_bancada_trabalhista", "exp_frente_empreendedora", "exp_instituto_tecnologia"]
        sample_ddds = ["+55 (11) 98765-4321", "+55 (21) 99888-7766", "+55 (71) 98111-2233", "+55 (41) 99222-3344", "+55 (61) 98333-4455", "+55 (92) 99444-5566"]

        data_items = []
        user_items = []

        for i in range(count):
            day_offset = i % max(1, span_days)
            dt = base_dt - timedelta(days=day_offset, hours=(i * 2) % 24, minutes=(i * 7) % 60)
            t_iso = dt.isoformat().replace("+00:00", "Z")
            text = samples[i % len(samples)]
            u_id = f"usr_{100 + (i % 15)}"
            tw_id = f"tw_{1000 + i}"
            spec = spectra[i % len(spectra)]
            exp = exponents[i % len(exponents)]
            geo_hint = sample_ddds[i % len(sample_ddds)]

            extracted_tags = [{"tag": h.lstrip("#")} for h in BaseLexicallyNeutralCollector.extract_hashtags(text)]
            data_items.append({
                "id": tw_id,
                "text": text,
                "author_id": u_id,
                "created_at": t_iso,
                "in_reply_to_user_id": exp,
                "phone_or_location_hint": geo_hint,
                "spectrum_seed_hint": spec,
                "public_metrics": {
                    "like_count": i * 5,
                    "retweet_count": i * 2,
                    "reply_count": i,
                    "quote_count": i % 3,
                },
                "entities": {
                    "urls": [{"expanded_url": "https://senado.leg.br/noticia"}] if "senado.leg.br" in text else [],
                    "hashtags": extracted_tags,
                },
            })

            user_items.append({
                "id": u_id,
                "username": f"cidadao_x_{u_id}",
                "name": f"Cidadao Brasil {u_id}",
            })

        meta: Dict[str, Any] = {"result_count": len(data_items)}
        if next_token:
            meta["next_token"] = next_token

        return {
            "data": data_items,
            "includes": {"users": user_items},
            "meta": meta,
        }
