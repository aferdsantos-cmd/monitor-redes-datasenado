"""
Conector Oficial e Auditável para Meta Instagram e Facebook com Neutralidade Lexical.

Atende às exigências da Fase 03, ADR-006, ADR-008 e ADR-010:
1. Suporte à Graph API e Meta Content Library com ordenação cronológica estrita ('reverse_chronological' / 'chronological');
2. Bloqueio com ValueError para qualquer ordenação algorítmica ('ranked', 'toplevel', 'relevance');
3. Reparo automático de mojibake UTF-8 (codificação Latin-1 nativa de exportações da Meta);
4. Injeção de transporte HTTP para testes herméticos com pegada zero;
5. Suporte a metadados de co-engajamento, bolhas e espectros (ADR-010).
"""

from datetime import datetime, timedelta, timezone
import json
import os
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
import urllib.error
import urllib.parse
import urllib.request

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
)

GRAPH_API_BASE_URL = "https://graph.facebook.com/v19.0"


def fix_meta_mojibake_utf8(text: str) -> str:
    """
    Corrige o defeito sistemático de codificação de exportações da Meta (Facebook/Instagram),
    onde bytes UTF-8 são decodificados incorretamente como Latin-1 / Windows-1252.
    Exemplo: 'Intelig\\u00c3\\u00aancia' -> 'Inteligência'.
    """
    if not text:
        return ""
    try:
        # Tentativa canônica: converte os caracteres para bytes latin-1 e decodifica em utf-8
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback de reparo cirúrgico para sequências UTF-8 quebradas comuns
        replacements = {
            "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
            "Ã ": "à", "Ã¢": "â", "Ãª": "ê", "Ã´": "ô", "Ã£": "ã",
            "Ãµ": "õ", "Ã§": "ç", "Ã": "Á", "Ã‰": "É", "Ã": "Í",
            "Ã“": "Ó", "Ãš": "Ú", "Ã‚": "Â", "ÃŠ": "Ê", "Ã”": "Ô",
            "Ãƒ": "Ã", "Ã•": "Õ", "Ã‡": "Ç",
        }
        res = text
        for mojibake, char in replacements.items():
            res = res.replace(mojibake, char)
        return res


class MetaInstagramFacebookCollector(BaseLexicallyNeutralCollector):
    """
    Coletor para Meta (Instagram e Facebook) via Graph API / Content Library e Ingestão Passiva.
    """

    platform = "instagram_facebook"

    def __init__(
        self,
        access_token: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
        http_get_json: Optional[Callable[[str, Dict[str, Any], Dict[str, str]], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(settings_override=settings_override)
        self.access_token = (
            access_token
            or os.environ.get("META_ACCESS_TOKEN")
            or os.environ.get("INSTAGRAM_ACCESS_TOKEN")
        )
        self.http_get_json = http_get_json

    def enforce_chronological_order(self, order: Optional[str] = "reverse_chronological") -> str:
        """
        Valida que a ordenação na Graph API é cronológica ('chronological' ou 'reverse_chronological').
        Lança ValueError para qualquer ordenação algorítmica ('ranked', 'toplevel', 'relevance').
        """
        norm = (order or "reverse_chronological").strip().lower()
        if norm not in ("chronological", "reverse_chronological"):
            raise ValueError(
                "VIÉS ALGORÍTMICO BLOQUEADO NA META: Coleta observacional no Instagram/Facebook "
                f"deve usar exclusivamente 'chronological' ou 'reverse_chronological', nunca '{order}'!"
            )
        return norm

    def _execute_api_get(
        self,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Executa requisição com proteção contra exposição de token de acesso."""
        if self.http_get_json is not None:
            return self.http_get_json(url, params, headers)

        full_url = f"{url}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            safe_err = err_body
            if self.access_token:
                safe_err = safe_err.replace(self.access_token, "[REDACTED_META_TOKEN]")
            raise RuntimeError(f"Erro na Meta Graph API (HTTP {e.code}): {safe_err}")

    def collect_public_comments_graph_api(
        self,
        theme_id: str,
        query: str,
        object_id: str,
        limit: int = 25,
        order: str = "reverse_chronological",
        access_token: Optional[str] = None,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade A: Coleta comentários públicos de postagem/vídeo via Graph API oficial.
        """
        self.validate_query_lexical_neutrality(theme_id, query)
        enforced_order = self.enforce_chronological_order(order)

        token = access_token or self.access_token
        if not token and self.http_get_json is None:
            raise RuntimeError("META_ACCESS_TOKEN ausente e nenhum http_get_json injetado.")

        url = f"{GRAPH_API_BASE_URL}/{object_id}/comments"
        params: Dict[str, Any] = {
            "access_token": token or "mock_token",
            "limit": min(100, max(1, limit)),
            "order": enforced_order,
            "fields": "id,message,created_time,from,like_count",
        }
        headers = {"User-Agent": "DataSenado-Meta-Monitor/3.0"}

        data = self._execute_api_get(url, params, headers)
        comments = data.get("data", [])

        collected: List[RawCollectedManifestation] = []
        for c in comments:
            raw_text = c.get("message", "")
            fixed_text = fix_meta_mojibake_utf8(raw_text)
            c_id = c.get("id", f"meta_c_{len(collected)}")

            from_obj = c.get("from", {})
            author_id = from_obj.get("id") or from_obj.get("name") or f"meta_user_{c_id}"

            dt_str = c.get("created_time")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            urls = self.extract_urls(fixed_text)
            tags = self.extract_hashtags(fixed_text)
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
                    comment_id=f"meta_{c_id}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"meta_{author_id}",
                    text=fixed_text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=query,
                    collector_modality="official_api_chronological",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=c.get("phone_or_location_hint"),
                    metadata={
                        "comment_id": c_id,
                        "object_id": object_id,
                        "like_count": c.get("like_count", 0),
                        "exponent_seed_id": f"meta_obj_{object_id}",
                        "spectrum_seed_hint": c.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    def collect_from_meta_json_export(
        self,
        export_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        theme_id: str,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade B: Ingestão de exportações JSON oficiais de páginas/perfis do Instagram/Facebook.
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        if isinstance(export_data, dict):
            raw_items = export_data.get("comments") or export_data.get("data") or [export_data]
            feed_name = export_data.get("feed_name", "meta_feed")
        else:
            raw_items = export_data
            feed_name = "meta_feed"

        collected: List[RawCollectedManifestation] = []
        for item in raw_items:
            raw_text = item.get("text") or item.get("message") or item.get("comment", "")
            fixed_text = fix_meta_mojibake_utf8(raw_text)
            if not fixed_text:
                continue

            norm_text = _normalize_text_for_matching(fixed_text)
            matched_query: Optional[str] = None
            for orig_q, n_q in zip(allowed_queries, norm_queries):
                if n_q in norm_text:
                    matched_query = orig_q
                    break

            if not matched_query:
                continue

            c_id = item.get("id", f"meta_exp_{len(collected) + 1}")
            author = item.get("author") or item.get("from") or f"meta_author_{c_id}"
            if isinstance(author, dict):
                author = author.get("name") or author.get("id") or f"meta_author_{c_id}"
            author_clean = fix_meta_mojibake_utf8(str(author))

            dt_str = item.get("created_time") or item.get("date")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            urls = self.extract_urls(fixed_text)
            tags = self.extract_hashtags(fixed_text)
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
                    comment_id=f"meta_{c_id}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"meta_{author_clean}",
                    text=fixed_text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=item.get("phone_or_location_hint"),
                    metadata={
                        "comment_id": c_id,
                        "feed_name": feed_name,
                        "exponent_seed_id": item.get("exponent_seed_id", f"meta_seed_{feed_name}"),
                        "spectrum_seed_hint": item.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    @staticmethod
    def generate_mock_meta_export(
        theme_id: str = "pl_ia_2338",
        count: int = 25,
        span_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Gera lote de comentários com simulação de mojibake UTF-8 nativo da Meta.
        """
        base_dt = datetime(2026, 11, 4, 18, 0, tzinfo=timezone.utc)
        if theme_id == "pec_escala_6x1":
            samples = [
                "Excelente debate sobre a PEC da escala 6x1 e a reduÃ§Ã£o da jornada sem reduÃ§Ã£o salarial #Escala6x1 https://senado.leg.br/noticia",
                "O fim da escala 6x1 traz qualidade de vida trabalhador e saÃºde para todos os trabalhadores.",
                "Precisamos pensar no custo para pequenas empresas e no risco de desemprego 6x1.",
                "O impacto produtivo escala 6x1 precisa de estudo aprofundado antes da votaÃ§Ã£o.",
                "Apoio a proposta da jornada 4x3 para valorizar a dignidade trabalhador 6x1 no Brasil.",
            ]
        else:
            samples = [
                "Acompanhando o PL 2338 com atenÃ§Ã£o. A proteÃ§Ã£o de direitos autorais Ã© fundamental! #PL2338 https://senado.leg.br/noticia",
                "Marco Legal da IA precisa de seguranÃ§a jurÃ­dica IA e governanÃ§a algorÃ­tmica responsÃ¡vel.",
                "Sou contrÃ¡rio se houver atraso tecnolÃ³gico e excesso de burocracia estatal no PL 2338.",
                "VotaÃ§Ã£o da lei da inteligÃªncia artificial e regular a inteligÃªncia artificial com transparÃªncia.",
                "Excelente audiÃªncia pÃºblica no Senado Federal sobre plataformas digitais e IA.",
            ]

        spectra = ["espectro_progressista", "espectro_conservador", "espectro_centro_institucional", "espectro_tecnico_setorial"]
        exponents = ["exp_senado_meta", "exp_pagina_trabalhista", "exp_empreendedor_digital", "exp_observatorio_ia"]
        sample_ddds = ["+55 (11) 98765-4321", "+55 (21) 99888-7766", "+55 (71) 98111-2233", "+55 (41) 99222-3344", "+55 (61) 98333-4455", "+55 (92) 99444-5566"]

        comments = []
        for i in range(count):
            day_offset = i % max(1, span_days)
            dt = base_dt - timedelta(days=day_offset, hours=(i * 3) % 24, minutes=(i * 11) % 60)
            t_iso = dt.isoformat().replace("+00:00", "Z")
            raw_t = samples[i % len(samples)]
            spec = spectra[i % len(spectra)]
            exp = exponents[i % len(exponents)]
            geo_hint = sample_ddds[i % len(sample_ddds)]

            comments.append({
                "id": f"comment_{2000 + i}",
                "message": raw_t,
                "created_time": t_iso,
                "from": {"id": f"user_meta_{100 + (i % 12)}", "name": f"CidadÃ£o Brasil {i}"},
                "like_count": i * 4,
                "phone_or_location_hint": geo_hint,
                "exponent_seed_id": exp,
                "spectrum_seed_hint": spec,
            })

        return {
            "feed_name": "pagina_debate_publico_meta",
            "comments": comments,
        }
