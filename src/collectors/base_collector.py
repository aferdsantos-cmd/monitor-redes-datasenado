"""
Classe Base e Contrato de Neutralidade Lexical para Conectores de Dados (Fase 02).

Implementa a Trava de Neutralidade Lexical Estrita (Achado M-04), garantindo que termos
valorativos ou enviesados jamais sejam utilizados como chave de busca nos coletores,
preservando a validade epistemologica e a ausencia de vieis de selecao no TCC e DataSenado.
"""

import copy
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


# Catálogo de temas contemporâneos embutidos (ADR-008 / QA-F03-08)
BUILTIN_EXTENDED_THEMES: List[Dict[str, Any]] = [
    {
        "id": "eleicao_presidencia_senado",
        "title": "Eleição para a Presidência e Mesa Diretora do Senado Federal (Fevereiro)",
        "senate_committee": "CCJ/Mesa Diretora",
        "collection_query_terms": [
            "eleicao presidencia do Senado",
            "presidente do Senado Federal",
            "Mesa Diretora do Senado",
            "sucessao no Senado",
            "candidatos presidencia do Senado",
            "votacao Mesa do Senado fevereiro",
        ],
        "nlp_stance_taxonomy": {
            "favorable_markers": [
                "independencia do Senado",
                "dialogo institucional",
                "autonomia do Legislativo",
                "equilibrio entre Poderes",
                "fortalecimento das comissoes",
                "transparencia na pauta",
            ],
            "against_markers": [
                "submissao do Senado",
                "engavetamento de pautas",
                "acordao de cupula",
                "falta de independencia",
                "controle politico da Mesa",
                "retrocesso institucional",
            ],
            "neutral_markers": [
                "regimento interno do Senado",
                "sessao preparatoria de fevereiro",
                "quorum de maioria absoluta",
                "votacao secreta em cedula",
                "composicao da Mesa Diretora",
            ],
        },
    }
]

_CUSTOM_THEMES_REGISTRY: List[Dict[str, Any]] = []


def register_custom_theme(theme_spec: Dict[str, Any]) -> None:
    """Registra um tema legislativo customizado em tempo de execução sem alterar arquivos em disco."""
    if not isinstance(theme_spec, dict) or "id" not in theme_spec:
        raise ValueError("theme_spec deve ser um dicionário contendo pelo menos a chave 'id'.")
    for i, t in enumerate(_CUSTOM_THEMES_REGISTRY):
        if t.get("id") == theme_spec["id"]:
            _CUSTOM_THEMES_REGISTRY[i] = copy.deepcopy(theme_spec)
            return
    _CUSTOM_THEMES_REGISTRY.append(copy.deepcopy(theme_spec))


def enrich_settings_with_dynamic_themes(base_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Enriquece settings em memória (via copy.deepcopy) garantindo a presença dos temas
    estendidos embutidos (eleicao_presidencia_senado) e customizados registrados.
    Preserva a imutabilidade absoluta de config/settings.yaml (WP-01).
    """
    cfg = copy.deepcopy(base_settings if base_settings is not None else load_settings())
    pilot_themes = cfg.setdefault("pilot_themes", [])
    existing_ids = {t["id"] for t in pilot_themes if isinstance(t, dict) and "id" in t}

    for extended in BUILTIN_EXTENDED_THEMES + _CUSTOM_THEMES_REGISTRY:
        tid = extended["id"]
        if tid not in existing_ids:
            pilot_themes.append(copy.deepcopy(extended))
            existing_ids.add(tid)

    return cfg


def get_dynamic_theme_samples(theme_id: str) -> List[str]:
    """Retorna amostras realistas de texto para temas contemporâneos e customizados."""
    if theme_id == "pec_escala_6x1":
        return [
            "Acompanhando o debate sobre a PEC da escala 6x1 e a reducao da jornada sem reducao salarial #Escala6x1 https://senado.leg.br/noticia",
            "O fim da escala 6x1 e essencial para a dignidade trabalhador 6x1 e saude mental dos trabalhadores.",
            "Precisamos avaliar o custo para pequenas empresas ao discutir a jornada de trabalho 6x1.",
            "Alerta para o risco de desemprego 6x1 e o impacto produtivo escala 6x1 em microempresas.",
            "Excelente sessao na comissao do Senado sobre a jornada 4x3 e modernizacao trabalhista.",
        ]
    elif theme_id == "eleicao_presidencia_senado":
        return [
            "Excelente debate sobre a eleicao presidencia do Senado e a autonomia do Legislativo com dialogo institucional #PresidenciaSenado https://senado.leg.br/noticia",
            "Acompanhando a sucessao no Senado. Defendo a independencia do Senado e o fortalecimento das comissoes tematicas.",
            "Alerta contra a submissao do Senado e o acordao de cupula na composicao da Mesa Diretora do Senado.",
            "Sou contra o engavetamento de pautas e a falta de independencia decorrente do controle politico da Mesa.",
            "O regimento interno do Senado exige quorum de maioria absoluta e votacao secreta em cedula para a eleicao da Mesa Diretora.",
        ]
    elif theme_id == "pl_ia_2338":
        return [
            "Debate relevante no Senado sobre o PL 2338 e protecao de direitos autorais para artistas #PL2338 https://senado.leg.br/noticia",
            "O PL 2338 precisa equilibrar inovacao com seguranca juridica IA e governanca algoritmica responsavel.",
            "Alerta contra o atraso tecnologico e excesso de burocracia estatal no PL 2338/2023.",
            "Acompanhando a votacao da lei da inteligencia artificial no Congresso hoje #MarcoLegalIA",
            "A regulamentacao da IA deve prever transparencia algoritmica e governanca responsavel.",
        ]
    else:
        cfg = enrich_settings_with_dynamic_themes()
        t_map = {t["id"]: t for t in cfg.get("pilot_themes", []) if isinstance(t, dict) and "id" in t}
        t_cfg = t_map.get(theme_id, {})
        q_terms = t_cfg.get("collection_query_terms", [theme_id])
        main_q = q_terms[0] if q_terms else theme_id
        tax = t_cfg.get("nlp_stance_taxonomy", {})
        favs = tax.get("favorable_markers", ["apoio"])
        agains = tax.get("against_markers", ["rejeicao"])
        neus = tax.get("neutral_markers", ["regimento"])
        return [
            f"Excelente debate sobre {main_q} no Senado Federal defendendo {favs[0]} https://senado.leg.br/noticia",
            f"Acompanhando a discussao de {main_q} com foco em {favs[min(1, len(favs)-1)]}.",
            f"Alerta sobre {main_q} com preocupacao quanto a {agains[0]}.",
            f"Manifestacao contraria sobre {main_q} criticando {agains[min(1, len(agains)-1)]}.",
            f"Analise tecnica sobre {main_q} avaliando {neus[0]}.",
        ]


class BaseLexicallyNeutralCollector:
    """
    Classe base com verificacao rigorosa de neutralidade lexical e extratores de entidades.
    """

    def __init__(self, settings_override: Optional[Dict[str, Any]] = None) -> None:
        self.settings = enrich_settings_with_dynamic_themes(settings_override)
        self.themes_map = {t["id"]: t for t in self.settings.get("pilot_themes", []) if isinstance(t, dict) and "id" in t}

    def register_custom_theme(self, theme_spec: Dict[str, Any]) -> None:
        """Registra tema customizado nesta instância e atualiza o mapeamento de temas."""
        register_custom_theme(theme_spec)
        self.settings = enrich_settings_with_dynamic_themes(self.settings)
        self.themes_map = {t["id"]: t for t in self.settings.get("pilot_themes", []) if isinstance(t, dict) and "id" in t}

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
