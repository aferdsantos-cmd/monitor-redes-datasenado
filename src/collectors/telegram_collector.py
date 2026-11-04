"""
Conector de Canais Publicos do Telegram (Fase 02).

Suporta as duas modalidades eticas e oficiais de coleta previstas no ADR-006:
1. Modalidade A: Ingestao passiva de arquivos JSON oficiais de exportacao do Telegram Desktop
   (doacao voluntaria de dados / preservacao documental sob Resolucao CNS 510/2016);
2. Modalidade B: Consumo de atualizacoes de canais publicos via Telegram Bot API oficial (getUpdates).
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import urllib.parse
import urllib.request

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
)

TELEGRAM_API_BASE_URL = "https://api.telegram.org"


class TelegramPublicChannelCollector(BaseLexicallyNeutralCollector):
    """
    Coletor de canais publicos do Telegram com suporte a exportacao JSON polimorfica e Bot API.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        http_get_json: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(settings_override=settings_override)
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.http_get_json = http_get_json

    @staticmethod
    def _extract_text_and_entities_from_telegram_message(
        raw_text: Union[str, List[Any]],
    ) -> Tuple[str, List[str], List[str]]:
        """
        Trata o formato polimorfico do Telegram Desktop Export:
        - String pura: "Exemplo de mensagem"
        - Lista de entidades: [{"type": "plain", "text": "Leiam "}, {"type": "link", "text": "https://..."}]
        """
        if isinstance(raw_text, str):
            urls = BaseLexicallyNeutralCollector.extract_urls(raw_text)
            tags = BaseLexicallyNeutralCollector.extract_hashtags(raw_text)
            return raw_text, urls, tags

        if isinstance(raw_text, list):
            parts: List[str] = []
            urls: List[str] = []
            tags: List[str] = []

            for item in raw_text:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    t = item.get("text", "")
                    parts.append(t)
                    item_type = item.get("type", "")
                    href = item.get("href")
                    if href and href not in urls:
                        urls.append(href)
                    if item_type in ("link", "url") or t.startswith("http"):
                        if t not in urls:
                            urls.append(t)
                    elif item_type == "text_link":
                        if href and href not in urls:
                            urls.append(href)
                    elif item_type == "hashtag" or t.startswith("#"):
                        if t not in tags:
                            tags.append(t)

            full_text = "".join(parts)
            # Complementa com extratores regex caso haja entidades nao marcadas
            urls.extend([u for u in BaseLexicallyNeutralCollector.extract_urls(full_text) if u not in urls])
            tags.extend([h for h in BaseLexicallyNeutralCollector.extract_hashtags(full_text) if h not in tags])
            return full_text, urls, tags

        return "", [], []

    def collect_from_telegram_json_export(
        self,
        json_data_or_path: Union[Dict[str, Any], str, Path],
        theme_id: str,
        channel_name_override: Optional[str] = None,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade A: Processa a exportacao oficial do Telegram Desktop (JSON).
        Filtra apenas mensagens pertinentes aos termos neutros de busca do tema legislativo.
        """
        if isinstance(json_data_or_path, (str, Path)):
            p = Path(json_data_or_path)
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = dict(json_data_or_path)

        channel_name = channel_name_override or data.get("name") or "telegram_public_channel"
        messages = data.get("messages", [])

        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        collected: List[RawCollectedManifestation] = []

        for msg in messages:
            if msg.get("type") != "message":
                continue

            raw_text = msg.get("text")
            full_text, urls, tags = self._extract_text_and_entities_from_telegram_message(raw_text)
            if not full_text.strip():
                continue

            norm_full = _normalize_text_for_matching(full_text)

            # Verifica se o texto contem algum dos termos neutros do tema
            matched_query: Optional[str] = None
            for orig_q, n_q in zip(allowed_queries, norm_queries):
                if n_q in norm_full:
                    matched_query = orig_q
                    break

            if not matched_query:
                continue

            # Parse de timestamp
            date_unix = msg.get("date_unixtime")
            if date_unix:
                dt = datetime.fromtimestamp(int(date_unix), tz=timezone.utc)
            elif msg.get("date"):
                try:
                    dt = datetime.fromisoformat(msg["date"]).replace(tzinfo=timezone.utc)
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            msg_id = msg.get("id", len(collected) + 1)
            from_author = msg.get("from") or msg.get("from_id") or f"tg_author_{msg_id}"

            collected.append(
                RawCollectedManifestation(
                    comment_id=f"tg_{channel_name}_{msg_id}",
                    theme_id=theme_id,
                    platform="telegram",
                    raw_author_id=str(from_author),
                    text=full_text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    metadata={
                        "channel_name": channel_name,
                        "forwarded_from": msg.get("forwarded_from"),
                        "reply_to_message_id": msg.get("reply_to_message_id"),
                    },
                )
            )

        return collected

    def collect_from_bot_api_updates(
        self,
        theme_id: str,
        offset: Optional[int] = None,
        limit: int = 100,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade B: Coleta atualizacoes de canais publicos via Bot API oficial (`getUpdates`).
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        params: Dict[str, Any] = {"limit": min(100, limit)}
        if offset is not None:
            params["offset"] = offset

        if self.http_get_json is not None:
            data = self.http_get_json("getUpdates", params)
        else:
            if not self.bot_token:
                raise RuntimeError("TELEGRAM_BOT_TOKEN ausente e nenhum http_get_json injetado.")
            url = f"{TELEGRAM_API_BASE_URL}/bot{self.bot_token}/getUpdates?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "DataSenado-Telegram-Monitor/2.0"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="ignore")
                safe_err = err_body.replace(self.bot_token, "[REDACTED_BOT_TOKEN]") if self.bot_token else err_body
                raise RuntimeError(f"Erro na Telegram Bot API (HTTP {e.code}): {safe_err}")

        collected: List[RawCollectedManifestation] = []
        updates = data.get("result", [])

        for upd in updates:
            msg = upd.get("channel_post") or upd.get("message")
            if not msg:
                continue

            text = msg.get("text") or msg.get("caption") or ""
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

            date_unix = msg.get("date", 0)
            dt = datetime.fromtimestamp(int(date_unix), tz=timezone.utc) if date_unix else datetime.now(timezone.utc)
            chat = msg.get("chat", {})
            sender = msg.get("from", {})
            raw_author = sender.get("username") or sender.get("id") or chat.get("username") or chat.get("id") or "tg_anon"

            # Entidades anexas da Bot API
            entities = msg.get("entities") or msg.get("caption_entities") or []
            entity_urls = []
            entity_tags = []
            for ent in entities:
                ent_type = ent.get("type")
                if ent_type == "text_link" and ent.get("url"):
                    entity_urls.append(ent.get("url"))
                elif ent_type == "url":
                    offset = ent.get("offset", 0)
                    length = ent.get("length", 0)
                    entity_urls.append(text[offset:offset + length])
                elif ent_type == "hashtag":
                    offset = ent.get("offset", 0)
                    length = ent.get("length", 0)
                    entity_tags.append(text[offset:offset + length])

            combined_urls = list(dict.fromkeys(self.extract_urls(text) + entity_urls))
            combined_tags = list(dict.fromkeys(self.extract_hashtags(text) + entity_tags))

            collected.append(
                RawCollectedManifestation(
                    comment_id=f"tg_api_{upd.get('update_id', 0)}_{msg.get('message_id', 0)}",
                    theme_id=theme_id,
                    platform="telegram",
                    raw_author_id=str(raw_author),
                    text=text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="official_api_chronological",
                    shared_urls=combined_urls,
                    hashtags=combined_tags,
                    metadata={"chat_title": chat.get("title", ""), "chat_id": chat.get("id")},
                )
            )

        return collected

    @staticmethod
    def generate_mock_telegram_export(
        theme_id: str = "pl_ia_2338",
        count: int = 15,
        channel_name: str = "Canal_Politica_DF_Publico",
    ) -> Dict[str, Any]:
        """Gera uma fixture realista de exportacao JSON do Telegram Desktop."""
        base_dt = datetime(2026, 10, 27, 10, 0, tzinfo=timezone.utc)
        messages = []

        if theme_id == "pec_escala_6x1":
            sample_entities = [
                [
                    {"type": "plain", "text": "Novo parecer sobre a "},
                    {"type": "bold", "text": "PEC escala 6x1"},
                    {"type": "plain", "text": " publicado. Leiam a integra: "},
                    {"type": "link", "text": "https://camara.leg.br/escala6x1"},
                    {"type": "plain", "text": " "},
                    {"type": "hashtag", "text": "#Escala6x1"},
                ],
                [
                    {"type": "plain", "text": "Debate aberto sobre o fim da escala 6x1 na Câmara. Concordam com o texto? "},
                    {"type": "hashtag", "text": "#FimDaEscala6x1"},
                ],
                "Discussão sobre a jornada de trabalho 6x1 avançou no plenário hoje.",
                [
                    {"type": "plain", "text": "Alerta importante sobre a "},
                    {"type": "link", "text": "https://g1.globo.com/economia/escala6x1"},
                    {"type": "plain", "text": " na escala 6x1. Vote NÃO se houver risco de desemprego!"},
                ],
                "VOTE SIM ao fim da escala 6x1 para garantir dignidade e descanso semanal remunerado.",
            ]
        else:
            sample_entities = [
                [
                    {"type": "plain", "text": "Novo parecer do relator sobre o "},
                    {"type": "bold", "text": "PL 2338/2023"},
                    {"type": "plain", "text": " publicado. Leiam a integra: "},
                    {"type": "link", "text": "https://senado.leg.br/pl2338"},
                    {"type": "plain", "text": " "},
                    {"type": "hashtag", "text": "#MarcoLegalIA"},
                ],
                [
                    {"type": "plain", "text": "Debate aberto sobre a regulamentação da IA no Senado. Concordam com o texto? "},
                    {"type": "hashtag", "text": "#PL2338"},
                ],
                "Discussão sobre a lei da inteligência artificial avançou na Câmara hoje.",
                [
                    {"type": "plain", "text": "Alerta importante sobre o "},
                    {"type": "link", "text": "https://g1.globo.com/politica/ia-senado"},
                    {"type": "plain", "text": " no PL 2338. Vote NÃO se houver restrições excessivas!"},
                ],
                "VOTE SIM ao PL 2338 para garantir transparência nas redes sociais e evitar deepfakes.",
            ]

        sample_ddds = [" (11) 98765-4321", " (21) 99888-7766", " (71) 98111-2233", " (41) 99222-3344", " (61) 98333-4455", " (92) 99444-5566"]

        for i in range(count):
            msg_dt = base_dt.replace(minute=(i * 3) % 60)
            base_ent = sample_entities[i % len(sample_entities)]
            ddd_suffix = sample_ddds[i % len(sample_ddds)]
            if isinstance(base_ent, str):
                msg_text = base_ent + ddd_suffix
            elif isinstance(base_ent, list):
                msg_text = list(base_ent) + [{"type": "plain", "text": ddd_suffix}]
            else:
                msg_text = base_ent

            messages.append({
                "id": 1000 + i,
                "type": "message",
                "date": msg_dt.isoformat(),
                "date_unixtime": int(msg_dt.timestamp()),
                "from": f"Membro_Canal_{i}",
                "from_id": f"user{20000 + i}",
                "text": msg_text,
            })

        return {
            "name": channel_name,
            "type": "public_channel",
            "id": 99887766,
            "messages": messages,
        }
