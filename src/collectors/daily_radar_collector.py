"""
Coletor e Analisador de Panorama Diário Aberto — Radar de Pautas do Senado Federal (ADR-008 Modo 2).

Atende às exigências da Fase 03 e ADR-008:
1. Varredura exploratória cronológica de manifestações do dia das 6 plataformas;
2. Agrupamento por tópicos emergentes do debate público digital;
3. Triagem automática contra as competências e vocabulário das Comissões Permanentes do Senado;
4. Geração de escores de relevância legislativa e recomendação de termos de busca neutros.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    _normalize_text_for_matching,
)

# Catálogo oficial de vocabulário temático e competências das Comissões do Senado Federal
SENATE_COMMITTEES_LEXICON: Dict[str, Dict[str, Any]] = {
    "CAS": {
        "name": "Comissão de Assuntos Sociais",
        "keywords": [
            "jornada de trabalho", "escala 6x1", "clt", "previdencia", "sus",
            "saude publica", "salario minimo", "direitos trabalhistas",
            "trabalhador", "jornada 4x3", "aposentadoria", "seguridade social",
        ],
    },
    "CCT": {
        "name": "Comissão de Ciência, Tecnologia, Inovação e Informática",
        "keywords": [
            "inteligencia artificial", "pl 2338", "marco legal da ia",
            "protecao de dados", "plataformas digitais", "ciberseguranca",
            "5g", "inovacao tecnologica", "governanca algoritmica", "redes sociais",
        ],
    },
    "CAE": {
        "name": "Comissão de Assuntos Econômicos",
        "keywords": [
            "reforma tributaria", "imposto sobre consumo", "iva", "taxa de juros",
            "arcabouco fiscal", "orcamento publico", "divida publica", "inflacao",
            "banco central", "pequenas empresas", "tributacao",
        ],
    },
    "CCJ": {
        "name": "Comissão de Constituição, Justiça e Cidadania",
        "keywords": [
            "codigo penal", "pec", "stf", "sistema eleitoral",
            "seguranca juridica", "administracao publica", "processo penal",
            "constituicao federal", "prerrogativas parlamentares",
        ],
    },
    "CMA": {
        "name": "Comissão de Meio Ambiente",
        "keywords": [
            "transicao energetica", "mercado de carbono", "desmatamento",
            "mudancas climaticas", "queimadas", "licenciamento ambiental",
            "amazonia", "energias renovaveis", "sustentabilidade",
        ],
    },
    "CE": {
        "name": "Comissão de Educação e Cultura",
        "keywords": [
            "piso da educacao", "novo ensino medio", "enem",
            "universidades federais", "bolsas de pesquisa", "cultura nacional",
            "professores", "fundeb",
        ],
    },
    "CSP": {
        "name": "Comissão de Segurança Pública",
        "keywords": [
            "combate ao crime organizado", "sistema prisional",
            "seguranca nas fronteiras", "lavagem de dinheiro", "apostas ilegais",
            "policia federal", "armas", "narcotrafico",
        ],
    },
}

# Tópicos conhecidos de entretenimento/geral sem aderência ao Senado Federal
GENERAL_NON_LEGISLATIVE_TOPICS: Dict[str, Dict[str, Any]] = {
    "futebol_campeonato": {
        "label": "Futebol e Campeonatos Esportivos",
        "keywords": ["campeonato brasileiro", "futebol", "libertadores", "gol", "escalacao", "torcida", "arbitragem"],
    },
    "celebridades_reality": {
        "label": "Celebridades, Cultura Pop e Reality Shows",
        "keywords": ["reality show", "famosos", "celebridade", "fofoca", "novela", "ator", "cantor"],
    },
    "jogos_e_esports": {
        "label": "Jogos Eletrônicos e e-Sports",
        "keywords": ["videogame", "gameplay", "esports", "jogos online", "playstation", "xbox", "streamer"],
    },
}


@dataclass
class DailyTopicRadarItem:
    """Item estruturado do Radar Diário de Descoberta de Pautas do Senado Federal."""
    topic_id: str
    topic_label: str
    total_posts: int
    unique_accounts_estimate: int
    share_of_day_pct: float
    platforms_active: List[str]
    senate_interest_flag: bool
    matched_senate_committees: List[str]
    legislative_relevance_score: float
    recommended_collection_queries: List[str]
    sample_snippets: List[str] = field(default_factory=list)


class DailyLegislativeRadarCollector(BaseLexicallyNeutralCollector):
    """
    Coletor de Radar Diário de Pautas do Senado Federal (ADR-008 Modo 2).
    """

    def __init__(self, settings_override: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(settings_override=settings_override)
        self.committees_lexicon = SENATE_COMMITTEES_LEXICON

    def scan_daily_dominant_topics(
        self,
        manifestations: Sequence[RawCollectedManifestation],
        target_date: Optional[str] = None,
    ) -> List[DailyTopicRadarItem]:
        """
        Recebe um fluxo aberto de manifestações de um determinado dia e realiza:
        1. Agrupamento em tópicos temáticos emergentes;
        2. Triagem contra as Comissões Permanentes do Senado;
        3. Cálculo de dominância, relevância legislativa e recomendação de queries neutras.
        """
        # Filtra pelo dia alvo se especificado (formato 'YYYY-MM-DD')
        day_items: List[RawCollectedManifestation] = []
        for m in manifestations:
            m_date = m.created_at.strftime("%Y-%m-%d")
            if target_date is None or m_date == target_date:
                day_items.append(m)

        if not day_items:
            return []

        total_day_manifestations = len(day_items)

        # Mapeamento de tópicos
        # 1. Tópicos legislativos piloto pré-cadastrados
        topic_buckets: Dict[str, List[RawCollectedManifestation]] = defaultdict(list)
        topic_labels: Dict[str, str] = {}
        topic_committees: Dict[str, Set[str]] = defaultdict(set)
        topic_relevance: Dict[str, float] = defaultdict(float)
        topic_queries: Dict[str, List[str]] = defaultdict(list)

        # Inicializa com os temas piloto de settings.yaml
        for t_cfg in self.settings.get("pilot_themes", []):
            tid = t_cfg["id"]
            topic_labels[tid] = t_cfg.get("title", tid)
            topic_queries[tid] = t_cfg.get("collection_query_terms", [])
            # Mapeia comissões padrão
            if "2338" in tid or "ia" in tid:
                topic_committees[tid].update(["CCT", "CCJ"])
                topic_relevance[tid] = 0.95
            elif "6x1" in tid or "escala" in tid:
                topic_committees[tid].update(["CAS", "CCJ"])
                topic_relevance[tid] = 0.95

        # Classifica cada manifestação
        for m in day_items:
            txt_norm = _normalize_text_for_matching(m.text)
            assigned_topic: Optional[str] = None

            # A. Verifica se pertence aos temas piloto
            if m.theme_id in topic_labels:
                assigned_topic = m.theme_id
            else:
                for tid, q_list in topic_queries.items():
                    if any(_normalize_text_for_matching(q) in txt_norm for q in q_list):
                        assigned_topic = tid
                        break

            # B. Se ainda não alocado, verifica contra as Comissões do Senado
            if not assigned_topic:
                matched_comm = []
                for comm_id, comm_data in self.committees_lexicon.items():
                    for kw in comm_data["keywords"]:
                        if _normalize_text_for_matching(kw) in txt_norm:
                            matched_comm.append(comm_id)
                            break
                if matched_comm:
                    assigned_topic = f"senate_topic_{matched_comm[0].lower()}"
                    topic_labels[assigned_topic] = f"Matéria sob competência da {matched_comm[0]} ({self.committees_lexicon[matched_comm[0]]['name']})"
                    topic_committees[assigned_topic].update(matched_comm)
                    topic_relevance[assigned_topic] = 0.85
                    topic_queries[assigned_topic] = [kw for comm in matched_comm for kw in self.committees_lexicon[comm]["keywords"][:3]]

            # C. Se ainda não alocado, verifica tópicos gerais não-legislativos
            if not assigned_topic:
                for gen_id, gen_data in GENERAL_NON_LEGISLATIVE_TOPICS.items():
                    if any(_normalize_text_for_matching(kw) in txt_norm for kw in gen_data["keywords"]):
                        assigned_topic = gen_id
                        topic_labels[assigned_topic] = gen_data["label"]
                        topic_relevance[assigned_topic] = 0.10
                        topic_queries[assigned_topic] = gen_data["keywords"][:2]
                        break

            # D. Tópico residual aberto
            if not assigned_topic:
                assigned_topic = "debate_geral_outros"
                topic_labels[assigned_topic] = "Debate Público Digital e Cotidiano (Outros)"
                topic_relevance[assigned_topic] = 0.05
                topic_queries[assigned_topic] = ["debate público"]

            topic_buckets[assigned_topic].append(m)

        # Monta a lista de itens estruturados do Radar
        radar_items: List[DailyTopicRadarItem] = []
        for top_id, items in topic_buckets.items():
            tot_posts = len(items)
            uniq_authors = len({m.raw_author_id for m in items})
            platforms = sorted(list({m.platform for m in items}))
            share_pct = round((tot_posts / total_day_manifestations) * 100.0, 2)
            comm_list = sorted(list(topic_committees.get(top_id, set())))
            is_senate = len(comm_list) > 0 or topic_relevance.get(top_id, 0.0) >= 0.50
            snippets = [m.text[:120] for m in items[:3]]

            radar_items.append(
                DailyTopicRadarItem(
                    topic_id=top_id,
                    topic_label=topic_labels.get(top_id, top_id),
                    total_posts=tot_posts,
                    unique_accounts_estimate=uniq_authors,
                    share_of_day_pct=share_pct,
                    platforms_active=platforms,
                    senate_interest_flag=is_senate,
                    matched_senate_committees=comm_list,
                    legislative_relevance_score=topic_relevance.get(top_id, 0.5 if is_senate else 0.1),
                    recommended_collection_queries=topic_queries.get(top_id, [])[:4],
                    sample_snippets=snippets,
                )
            )

        # Ordena por dominância (estimativa de contas únicas decrescente, seguido de total de posts)
        radar_items.sort(key=lambda x: (x.unique_accounts_estimate, x.total_posts), reverse=True)
        return radar_items
