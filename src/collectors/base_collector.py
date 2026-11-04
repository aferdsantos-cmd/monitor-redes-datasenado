"""
Classe Base e Contrato de Neutralidade Lexical para Conectores de Dados (Fase 02).

Implementa a Trava de Neutralidade Lexical Estrita (Achado M-04), garantindo que termos
valorativos ou enviesados jamais sejam utilizados como chave de busca nos coletores,
preservando a validade epistemologica e a ausencia de vieis de selecao no TCC e DataSenado.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import unicodedata
from zoneinfo import ZoneInfo

from src.config_loader import load_settings
from src.sampling.stratified_sampler import to_brazil_timezone

SP_TZ = ZoneInfo("America/Sao_Paulo")

# Expressoes regulares para redacao de Dados Pessoais (LGPD Art. 5o, I c/c Art. 13, §4o)
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}\s*)?(?:\(\d{2}\)|\b\d{2}\b)\s*\d{4,5}[-.\s]?\d{4}\b")
HANDLE_PATTERN = re.compile(r"(?<![/\w])@[\w_]+")
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+[^\s<>\"'.,;!?)]")
HASHTAG_PATTERN = re.compile(r"#[\wÀ-ÿ]+")


def _normalize_text_for_matching(text: str) -> str:
    """Normaliza texto removendo acentos e espacos excedentes para comparacao lexical."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", ascii_text).strip()


@dataclass
class RawCollectedManifestation:
    """Registro bruto estruturado de manifestacao coletada de rede social."""
    comment_id: str
    theme_id: str
    platform: str
    raw_author_id: str
    text: str
    created_at: datetime
    collection_query_used: str
    collector_modality: str  # "official_api_chronological" ou "passive_export_ingestion"
    shared_urls: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    phone_or_location_hint: Optional[str] = None
    stance_hint: Optional[str] = None


class BaseLexicallyNeutralCollector:
    """
    Classe base com verificacao rigorosa de neutralidade lexical e extratores de entidades.
    """

    def __init__(self, settings_override: Optional[Dict[str, Any]] = None) -> None:
        self.settings = settings_override or load_settings()
        self.themes_map = {t["id"]: t for t in self.settings.get("pilot_themes", [])}

    def validate_query_lexical_neutrality(self, theme_id: str, query: str) -> None:
        """
        Garante que a query pertence estritamente a lista neutra e nao contem termos valorativos.
        Lanca ValueError se violar a neutralidade lexical (M-04).
        """
        if theme_id not in self.themes_map:
            raise KeyError(f"Tema legislativo nao reconhecido: '{theme_id}'.")

        theme_cfg = self.themes_map[theme_id]
        allowed_queries = theme_cfg.get("collection_query_terms", [])
        taxonomy = theme_cfg.get("nlp_stance_taxonomy", {})
        favorable_markers = taxonomy.get("favorable_markers", [])
        against_markers = taxonomy.get("against_markers", [])

        norm_query = _normalize_text_for_matching(query)

        # 1. Trava contra termos valorativos/enviesados (positivos ou negativos)
        all_biased_markers = favorable_markers + against_markers
        for marker in all_biased_markers:
            norm_marker = _normalize_text_for_matching(marker)
            if norm_marker in norm_query or norm_query == norm_marker:
                raise ValueError(
                    f"VIOLAÇÃO DE NEUTRALIDADE LEXICAL (M-04): Termo valorativo proibido "
                    f"na etapa de coleta: '{marker}' encontrado na query '{query}'!"
                )

        # 2. Trava de aderencia estrita aos termos autorizados do tema
        norm_allowed = [_normalize_text_for_matching(q) for q in allowed_queries]
        if norm_query not in norm_allowed:
            raise ValueError(
                f"Termo '{query}' nao pertence a lista oficial de busca neutra do tema '{theme_id}'. "
                f"Termos permitidos: {allowed_queries}"
            )

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extrai todas as URLs do texto."""
        if not text:
            return []
        return URL_PATTERN.findall(text)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """Extrai todas as hashtags do texto."""
        if not text:
            return []
        return HASHTAG_PATTERN.findall(text)

    @staticmethod
    def redact_pii_from_text(text: str) -> str:
        """
        Aplica redacao de dados pessoais (CPF, e-mail, telefone, @handles) em streaming.
        Garante conformidade com o Art. 13, §4o da LGPD.
        """
        if not text:
            return ""
        s = CPF_PATTERN.sub("[CPF_REDACTED]", text)
        s = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", s)
        s = PHONE_PATTERN.sub("[PHONE_REDACTED]", s)
        s = HANDLE_PATTERN.sub("[HANDLE_REDACTED]", s)
        return s

    @staticmethod
    def normalize_timestamp_utc(dt: datetime) -> datetime:
        """Converte datetime para UTC com timezone explicito."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
