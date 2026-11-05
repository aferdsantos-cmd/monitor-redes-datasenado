"""
Conector Oficial e Auditável para WhatsApp via Ingestão Passiva de Grupos Públicos.

Atende às exigências da Fase 03, ADR-006, ADR-008 e ADR-010:
1. Opera estritamente por Ingestão Passiva de Arquivos de Exportação (.txt e .json);
2. Parser robusto para padrões Android e iOS, com suporte a mensagens multilinhas;
3. Filtro automático de mensagens de sistema do WhatsApp (criptografia, entrada/saída, mídia oculta);
4. Extração automática de DDD/Região (+55 DD) do remetente para a Camada Bronze antes do HMAC-SHA256;
5. Suporte a metadados de co-engajamento, bolhas e espectros (ADR-010).
"""

from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any, Dict, List, Optional, Sequence, Union
import urllib.parse

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
)

# Regex para cabeçalhos de mensagens de exportação do WhatsApp
ANDROID_MSG_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+-\s+([^:]+):\s*(.*)$"
)
IOS_MSG_PATTERN = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:]+):\s*(.*)$"
)
ANDROID_SYSTEM_LINE_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)\s+-\s+(.*)$"
)
IOS_SYSTEM_LINE_PATTERN = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]\s+(.*)$"
)

# Padrões de mensagens de sistema e ruídos operacionais do WhatsApp
SYSTEM_MSG_INDICATORS = [
    "mensagens e as chamadas sao protegidas",
    "mensagens e as chamadas são protegidas",
    "messages and calls are end-to-end encrypted",
    "entrou usando o link de convite",
    "joined using this group",
    "saiu do grupo",
    "left",
    "<midia oculta>",
    "<mídia oculta>",
    "<arquivo de midia oculto>",
    "<arquivo de mídia oculto>",
    "<media omitted>",
    "mudou a descricao do grupo",
    "mudou a descrição do grupo",
    "mudou o nome do grupo",
    "criou o grupo",
    "apagou esta mensagem",
]

PHONE_SENDER_PATTERN = re.compile(r"^\+?\d[\d\s().-]{8,20}\d$")


class WhatsAppPublicGroupsExportCollector(BaseLexicallyNeutralCollector):
    """
    Coletor para WhatsApp via Ingestão Passiva de Grupos Públicos Temáticos (.txt ou .json).
    """

    platform = "whatsapp"

    def __init__(self, settings_override: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(settings_override=settings_override)

    def _parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Converte data e hora de exportação do WhatsApp para datetime UTC (fuso de Brasília)."""
        parts = date_str.split("/")
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        if year < 100:
            year += 2000

        time_parts = time_str.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2]) if len(time_parts) > 2 else 0

        # Assumindo exportação nativa em horário de Brasília (UTC-3)
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone(timedelta(hours=-3)))
        return dt.astimezone(timezone.utc)

    def parse_whatsapp_txt_export(
        self,
        content: str,
        theme_id: str,
        channel_name: str = "grupo_whatsapp",
    ) -> List[RawCollectedManifestation]:
        """
        Realiza o parsing de arquivo .txt de exportação do WhatsApp (Android ou iOS).
        Suporta mensagens multilinhas e extrai o DDD do remetente antes da redação PII.
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        lines = content.splitlines()
        parsed_entries: List[Dict[str, Any]] = []
        current_entry: Optional[Dict[str, Any]] = None

        for line in lines:
            line_strip = line.strip()
            if not line_strip:
                continue

            # Testa formato Android
            match_android = ANDROID_MSG_PATTERN.match(line)
            # Testa formato iOS
            match_ios = IOS_MSG_PATTERN.match(line)

            match = match_android or match_ios
            if match:
                if current_entry:
                    parsed_entries.append(current_entry)
                date_s, time_s, sender, msg_text = match.groups()
                current_entry = {
                    "date_str": date_s,
                    "time_str": time_s,
                    "sender": sender.strip(),
                    "text": msg_text,
                }
            elif ANDROID_SYSTEM_LINE_PATTERN.match(line) or IOS_SYSTEM_LINE_PATTERN.match(line):
                # Linha de notificação de sistema sem remetente com dois-pontos
                # Encerra a mensagem anterior e não a contamina como linha de continuação
                if current_entry:
                    parsed_entries.append(current_entry)
                    current_entry = None
            else:
                # Linha de continuação (mensagem multilinha)
                if current_entry:
                    current_entry["text"] += "\n" + line

        if current_entry:
            parsed_entries.append(current_entry)

        collected: List[RawCollectedManifestation] = []
        for i, entry in enumerate(parsed_entries):
            raw_text = entry["text"].strip()
            norm_raw = _normalize_text_for_matching(raw_text)

            # 1. Filtra avisos de sistema e mídias
            if any(ind in norm_raw for ind in SYSTEM_MSG_INDICATORS):
                continue

            # 2. Filtra por termos de busca neutros da matéria
            matched_query: Optional[str] = None
            for orig_q, n_q in zip(allowed_queries, norm_queries):
                if n_q in norm_raw:
                    matched_query = orig_q
                    break

            if not matched_query:
                continue

            # 3. Extrai data/hora
            dt = self._parse_timestamp(entry["date_str"], entry["time_str"])

            # 4. Extrai telefone do remetente para proxy geográfico
            sender_str = entry["sender"]
            phone_hint: Optional[str] = None
            if PHONE_SENDER_PATTERN.match(sender_str):
                phone_hint = sender_str

            urls = self.extract_urls(raw_text)
            tags = self.extract_hashtags(raw_text)
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
                    comment_id=f"wa_{channel_name}_{i + 1}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"wa_{sender_str}",
                    text=raw_text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=phone_hint,
                    metadata={
                        "message_index": i + 1,
                        "channel_name": channel_name,
                        "exponent_seed_id": f"wa_{channel_name}",
                        "spectrum_seed_hint": "nao_rotulado_unsupervised",
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    def collect_from_whatsapp_json_export(
        self,
        export_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        theme_id: str,
    ) -> List[RawCollectedManifestation]:
        """
        Modalidade alternativa: Ingestão de exportações em formato JSON estruturado.
        """
        theme_cfg = self.themes_map.get(theme_id, {})
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        norm_queries = [_normalize_text_for_matching(q) for q in allowed_queries]

        if isinstance(export_data, dict):
            messages = export_data.get("messages") or export_data.get("data") or [export_data]
            channel_name = export_data.get("group_name") or export_data.get("channel_name", "grupo_whatsapp")
        else:
            messages = export_data
            channel_name = "grupo_whatsapp"

        collected: List[RawCollectedManifestation] = []
        for i, msg in enumerate(messages):
            raw_text = msg.get("text") or msg.get("message", "")
            if not raw_text:
                continue

            norm_text = _normalize_text_for_matching(raw_text)
            if any(ind in norm_text for ind in SYSTEM_MSG_INDICATORS):
                continue

            matched_query: Optional[str] = None
            for orig_q, n_q in zip(allowed_queries, norm_queries):
                if n_q in norm_text:
                    matched_query = orig_q
                    break

            if not matched_query:
                continue

            dt_str = msg.get("date") or msg.get("timestamp")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    dt = datetime.now(timezone.utc)
            else:
                dt = datetime.now(timezone.utc)

            sender = str(msg.get("from") or msg.get("sender") or f"wa_user_{i}")
            phone_hint = msg.get("phone_or_location_hint") or (sender if PHONE_SENDER_PATTERN.match(sender) else None)

            urls = self.extract_urls(raw_text)
            tags = self.extract_hashtags(raw_text)
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
                    comment_id=f"wa_{channel_name}_{i + 1}",
                    theme_id=theme_id,
                    platform=self.platform,
                    raw_author_id=f"wa_{sender}",
                    text=raw_text,
                    created_at=self.normalize_timestamp_utc(dt),
                    collection_query_used=matched_query,
                    collector_modality="passive_export_ingestion",
                    shared_urls=urls,
                    hashtags=tags,
                    phone_or_location_hint=phone_hint,
                    metadata={
                        "message_index": i + 1,
                        "channel_name": channel_name,
                        "exponent_seed_id": f"wa_{channel_name}",
                        "spectrum_seed_hint": msg.get("spectrum_seed_hint", "nao_rotulado_unsupervised"),
                        "shared_news_domains": news_domains,
                    },
                )
            )

        return collected

    @staticmethod
    def generate_mock_whatsapp_txt_export(
        theme_id: str = "pl_ia_2338",
        count: int = 25,
        span_days: int = 7,
        channel_name: str = "debate_publico_brasil",
    ) -> str:
        """
        Gera um arquivo de texto realista de exportação do WhatsApp contendo formatos Android e iOS,
        mensagens multilinhas, avisos de sistema e remetentes com DDDs reais do Brasil.
        """
        base_dt = datetime(2026, 11, 4, 18, 0)
        lines: List[str] = [
            "27/10/2026 09:00 - As mensagens e as chamadas são protegidas com a criptografia de ponta a ponta.",
            "27/10/2026 09:05 - +55 61 99888-7766 entrou usando o link de convite deste grupo",
        ]

        if theme_id == "pec_escala_6x1":
            samples = [
                "Bom dia pessoal. Compartilhando a discussão da PEC da escala 6x1 e a reducao da jornada sem reducao salarial.\nhttps://senado.leg.br/noticia\nPrecisamos acompanhar #Escala6x1",
                "O fim da escala 6x1 vai garantir dignidade trabalhador 6x1 para os trabalhadores do comércio.",
                "Temos que avaliar com prudência o custo para pequenas empresas e o risco de desemprego 6x1 que isso pode causar.",
                "Sobre a jornada de trabalho 6x1:\nO impacto produtivo escala 6x1 precisa ser debatido com o setor produtivo.",
                "Excelente iniciativa do Senado em abrir debate sobre a jornada 4x3.",
            ]
        else:
            samples = [
                "Bom dia a todos. Saiu nova matéria sobre o PL 2338 no Senado.\nProtecao de direitos autorais para autores!\nhttps://senado.leg.br/noticia #PL2338",
                "O Marco Legal da IA precisa dar seguranca juridica IA e governanca algoritmica responsavel.",
                "Atenção para o atraso tecnologico e excesso de burocracia estatal no PL 2338/2023 se passar como está.",
                "Acompanhando a votação da lei da inteligencia artificial hoje pelo canal do Senado.",
                "Precisamos regular a inteligencia artificial garantindo inovação e soberania digital para o Brasil.",
            ]

        sample_senders = [
            "+55 11 98765-4321",
            "+55 21 99888-7766",
            "+55 71 98111-2233",
            "+55 41 99222-3344",
            "+55 61 98333-4455",
            "+55 92 99444-5566",
            "+55 51 99555-6677",
        ]

        for i in range(count):
            day_offset = i % max(1, span_days)
            dt = base_dt - timedelta(days=day_offset, hours=(i * 2) % 24, minutes=(i * 9) % 60)
            sender = sample_senders[i % len(sample_senders)]
            msg = samples[i % len(samples)]

            # Alterna entre padrão Android e padrão iOS
            if i % 2 == 0:
                # Android: 27/10/2026 14:32 - +55 61 ...: Texto
                d_str = dt.strftime("%d/%m/%Y")
                t_str = dt.strftime("%H:%M")
                lines.append(f"{d_str} {t_str} - {sender}: {msg}")
            else:
                # iOS: [27/10/2026, 14:32:10] +55 (11) ...: Texto
                d_str = dt.strftime("%d/%m/%Y")
                t_str = dt.strftime("%H:%M:%S")
                lines.append(f"[{d_str}, {t_str}] {sender}: {msg}")

            if i == 5:
                lines.append(f"{dt.strftime('%d/%m/%Y %H:%M')} - +55 31 99111-0000 saiu do grupo")
            if i == 10:
                lines.append(f"{dt.strftime('%d/%m/%Y %H:%M')} - +55 11 98765-4321: <Mídia oculta>")

        return "\n".join(lines)
