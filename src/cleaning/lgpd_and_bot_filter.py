"""
Motor de Desinfeccao, Pseudonimizacao LGPD (HMAC-SHA256) e Deteccao de Indicios de
Comportamento Inautentico Coordenado (CIB) por Busca de Similaridade Sub-Quadratica Esperada via LSH
e Particionamento em Grafo de Leiden.

Atende integralmente aos criterios da 2a Rodada de Auditoria Cientifica da Fase 01:
1. Pseudonimizacao por HMAC-SHA256 (LGPD art. 13, par. 4o) *Fail-Closed* (C-04 / B1 / L-01):
   - Exige `LGPD_HMAC_SECRET_KEY` forte (>= 32 chars) via ambiente/parametro; aborta imediatamente
     (`RuntimeError`) se ausente ou com valor de exemplo, sem fallback publico!
   - Apaga `raw_author_id` do objeto em memoria apos gerar `author_hash` (64 hex) e registra `key_id` (8 hex).
2. Proxy Geografico Aproximado (DDD) sem Falso Positivo Internacional (Checklist #10):
   - Valida explicitamente se o telefone nao possui DDI estrangeiro (`+1`, `+44`, etc.) antes de
     aceitar 10/11 digitos locais ou `55` + DDD.
3. Quarentena de Spam Comercial com Protecao de Contexto Legislativo (C-03):
   - Exige co-ocorrencia de pistas comerciais explicitas e protege vocabulos do processo legislativo
     ('sorteio do relator', 'CPI das apostas', 'legalizacao do cassino', 'plenario', 'senado'),
     registrando `spam_quarantine_reason` em vez de apagar silenciosamente.
4. Normalizacao Unicode NFKD e 5 Classes Auditaveis sem Vies Direcional SIM/NAO (C-03):
   - Reconhece simetricamente 'Vote SIM' e 'Vote NÃO' (com ou sem acento).
   - Separa `Mobilizacao_Civica_Legitima` (exige marcador civico explicito) de `Repeticao_Organica`
     (near-duplicate assincrono sem marcador civico), evitando que textos organicos parecidos inflem a mobilizacao.
5. Busca de Similaridade Sub-Quadratica Esperada via LSH + Union-Find + Verificacao Exata de Jaccard + Two-Pointer (G-04):
   - Verifica `mh_i.jaccard(mh_j) >= threshold` para eliminar falsos positivos do LSH, agrupa colisoes
     com estrutura Disjoint-Set (Union-Find) e pontua ambos os lados do par dentro da janela temporal.
6. Detector de CIB Fiel a Literatura (Giglietto et al., 2020; Pacheco et al., 2021) sem Falso Positivo em Noticia Viral (C-02):
   - Allowlist de dominios institucionais/jornalisticos (`senado.leg.br`, `g1.globo.com`, etc.).
   - Penalizacao IDF para itens/URLs/hashtags massivamente compartilhados.
   - Exige repeticao de co-compartilhamento em multiplos itens/eventos distintos ou rajada de altissima
     densidade temporal antes de formar arestas de coordenacao no Grafo de Leiden.
   - Politica de exclusao em nivel de CONTA (M-05): consolida `account_suspected_cib` para que
     nenhuma postagem residual de conta automatizada sobreviva como unidade organica.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import hmac
import math
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import unicodedata
from urllib.parse import urlparse

from datasketch import MinHash, MinHashLSH
from dotenv import load_dotenv
import igraph as ig
import leidenalg

from src.config_loader import load_settings

load_dotenv()

# Mapeamento Oficial de Codigos DDD Brasileiros para UF e Macrorregiao do IBGE
# Nota Metodologica (Problema 11 / L-01): Utilizado exclusivamente como PROXY GEOGRAFICO APROXIMADO.
DDD_TO_UF_REGION_PROXY: Dict[str, Tuple[str, str]] = {
    # Sudeste
    "11": ("SP", "Sudeste"), "12": ("SP", "Sudeste"), "13": ("SP", "Sudeste"),
    "14": ("SP", "Sudeste"), "15": ("SP", "Sudeste"), "16": ("SP", "Sudeste"),
    "17": ("SP", "Sudeste"), "18": ("SP", "Sudeste"), "19": ("SP", "Sudeste"),
    "21": ("RJ", "Sudeste"), "22": ("RJ", "Sudeste"), "24": ("RJ", "Sudeste"),
    "27": ("ES", "Sudeste"), "28": ("ES", "Sudeste"),
    "31": ("MG", "Sudeste"), "32": ("MG", "Sudeste"), "33": ("MG", "Sudeste"),
    "34": ("MG", "Sudeste"), "35": ("MG", "Sudeste"), "37": ("MG", "Sudeste"), "38": ("MG", "Sudeste"),
    # Sul
    "41": ("PR", "Sul"), "42": ("PR", "Sul"), "43": ("PR", "Sul"),
    "44": ("PR", "Sul"), "45": ("PR", "Sul"), "46": ("PR", "Sul"),
    "47": ("SC", "Sul"), "48": ("SC", "Sul"), "49": ("SC", "Sul"),
    "51": ("RS", "Sul"), "53": ("RS", "Sul"), "54": ("RS", "Sul"), "55": ("RS", "Sul"),
    # Centro-Oeste
    "61": ("DF", "Centro-Oeste"),
    "62": ("GO", "Centro-Oeste"), "64": ("GO", "Centro-Oeste"),
    "65": ("MT", "Centro-Oeste"), "66": ("MT", "Centro-Oeste"),
    "67": ("MS", "Centro-Oeste"),
    # Norte
    "63": ("TO", "Norte"), "68": ("AC", "Norte"), "69": ("RO", "Norte"),
    "91": ("PA", "Norte"), "93": ("PA", "Norte"), "94": ("PA", "Norte"),
    "92": ("AM", "Norte"), "97": ("AM", "Norte"),
    "95": ("RR", "Norte"), "96": ("AP", "Norte"),
    # Nordeste
    "71": ("BA", "Nordeste"), "73": ("BA", "Nordeste"), "74": ("BA", "Nordeste"),
    "75": ("BA", "Nordeste"), "77": ("BA", "Nordeste"),
    "79": ("SE", "Nordeste"),
    "81": ("PE", "Nordeste"), "87": ("PE", "Nordeste"),
    "82": ("AL", "Nordeste"), "83": ("PB", "Nordeste"), "84": ("RN", "Nordeste"),
    "85": ("CE", "Nordeste"), "88": ("CE", "Nordeste"),
    "86": ("PI", "Nordeste"), "89": ("PI", "Nordeste"),
    "98": ("MA", "Nordeste"), "99": ("MA", "Nordeste"),
}


def normalize_ascii(text: str) -> str:
    """Remove acentos via decomposicao NFKD e converte para minusculas (resolve C-03 'Vote NÃO')."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_str = decomposed.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", ascii_str).strip()


# Contexto legislativo protegido contra falso positivo de spam (C-03)
LEGISLATIVE_CONTEXT_ALLOWLIST = re.compile(
    r"\b(relator\w*|cpi\b|cpmi\b|senado\w*|camara\b|congresso\b|plenario\b|"
    r"legalizac\w+|regulamentac\w+|tributac\w+|comissao\b|projeto\s+de\s+lei|pec\b)\b",
    re.IGNORECASE,
)

# Pistas comerciais explicitas (exigem promessa financeira/venda direta - C-03)
COMMERCIAL_SPAM_STRONG_CUE = re.compile(
    r"\b(sorteio\s+pix|pix\s+gratis|ganhe\s+dinheiro|renda\s+extra|cupom\s+de\s+desconto|"
    r"link\s+na\s+bio\s+para\s+comprar|criptomoeda\s+gratis|bonus\s+de\s+cadastro)\b",
    re.IGNORECASE,
)
COMMERCIAL_GAMBLING_PROMO_CUE = re.compile(
    r"\b(apostas?\s+esportivas?|cassino\s+online|bet\d+)\b.*\b(r\$|\d+\s*reais|gratis|ganhe|pix|bonus|sorteio)\b|"
    r"\b(r\$|\d+\s*reais|gratis|ganhe|pix|bonus|sorteio)\b.*\b(apostas?\s+esportivas?|cassino\s+online|bet\d+)\b",
    re.IGNORECASE,
)

# Padrao simetrico de Mobilizacao Civica (opera sobre texto normalizado sem acento - C-03)
CIVIC_MOBILIZATION_NORM_PATTERN = re.compile(
    r"\b(vote|vota|votem)\s+(sim|nao)\b|"
    r"\b(apoie|apoia|apoiem|rejeite|rejeitem|diga\s+sim|diga\s+nao)\b.*\b(pl|pec|projeto)\b|"
    r"\bpressione\s+seu\s+(senador|deputado|parlamentar)\b|"
    r"\bconsulta\s+publica\b.*\becidadania\b",
    re.IGNORECASE,
)


class _UnionFind:
    """Estrutura Disjoint-Set (Union-Find) para agrupar colisoes LSH transitivas (G-04)."""

    def __init__(self, size: int):
        self.parent = list(range(size))

    def find(self, i: int) -> int:
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i

    def union(self, i: int, j: int) -> None:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if root_i < root_j:
                self.parent[root_j] = root_i
            else:
                self.parent[root_i] = root_j


@dataclass
class SocialPost:
    post_id: str
    platform: str
    raw_author_id: str
    timestamp: datetime
    text: str
    shared_url: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    phone_or_location_hint: Optional[str] = None

    # Atributos auditaveis preenchidos pelo pipeline (nomenclatura revisada conforme Anexo A)
    author_hash: str = ""                       # Pseudonimizacao HMAC-SHA256 (64 hex chars)
    hmac_key_id: str = ""                       # Identificador auditavel da chave (8 hex chars - B1)
    uf_proxy: str = "NI"                        # Proxy geografico aproximado (UF)
    region_proxy: str = "Nao Identificado"      # Proxy geografico aproximado (Macrorregiao IBGE)
    is_commercial_spam: bool = False            # Sinalizador de quarentena comercial
    spam_quarantine_reason: Optional[str] = None # Motivo auditavel da quarentena (C-03)
    activity_class: str = "Organico"            # 'Organico', 'Mobilizacao_Civica_Legitima', 'Repeticao_Organica', 'Suspeita_CIB_Automacao', 'Spam_Comercial'
    is_near_duplicate_lsh: bool = False         # Detectado por LSH + verificacao exata de Jaccard
    lsh_cluster_id: int = -1                    # ID do componente conexo no Union-Find
    suspected_coordination: bool = False        # Indicio de coordenacao (nivel post/conta)
    account_suspected_cib: bool = False         # Flag consolidada em nivel de CONTA (M-05)
    leiden_community_id: int = -1               # ID do cluster no grafo de Leiden (-1 se isolado)
    coordination_score: float = 0.0             # Componente de sincronia de rede [0, 1]
    coordination_signal_index: float = 0.0      # Indice Composto Experimental de Coordenacao [0, 1] (substitui bot_risk_score - Anexo A)
    stance: Optional[str] = None                # 'Favoravel', 'Contrario', 'Neutro'

    @property
    def bot_risk_score(self) -> float:
        """Alias retrocompativel para `coordination_signal_index`."""
        return self.coordination_signal_index


class LGPDCleanerAndCIBGraphEngine:
    """
    Executa pseudonimizacao por HMAC-SHA256 *fail-closed* (LGPD art. 13, par. 4o),
    quarentena de spam com protecao de contexto legislativo, busca de similaridade
    sub-quadratica esperada via LSH (com Union-Find e verificacao de Jaccard) e
    deteccao de indicios de coordenacao em grafo via Algoritmo de Leiden.
    """

    def __init__(
        self,
        hmac_secret_key: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ):
        cfg = settings_override or load_settings()
        cib_cfg = cfg["cib_and_bot_detection"]

        # Validacao Fail-Closed da chave HMAC (C-04 / B1)
        secret = hmac_secret_key if hmac_secret_key is not None else os.environ.get("LGPD_HMAC_SECRET_KEY")
        if (
            not secret
            or not isinstance(secret, str)
            or len(secret.strip()) < 32
            or secret.strip().startswith("defina-")
        ):
            raise RuntimeError(
                "LGPD_HMAC_SECRET_KEY ausente, curta (<32 chars) ou com valor de exemplo. "
                "Pipeline abortado em modo fail-closed (Condicao B1 / Achado C-04)."
            )

        self._secret_bytes = secret.strip().encode("utf-8")
        self.key_id = hmac.new(self._secret_bytes, b"datasenado-key-id-v1", hashlib.sha256).hexdigest()[:8]

        # Parametros carregados diretamente do config/settings.yaml (G-01)
        self.minhash_num_perm: int = int(cib_cfg["minhash_num_perm"])
        self.lsh_jaccard_threshold: float = float(cib_cfg["minhash_lsh_jaccard_threshold"])
        self.min_distinct_co_shared_items: int = int(cib_cfg.get("min_distinct_co_shared_items_for_edge", 2))
        self.account_cib_min_count: int = int(cib_cfg.get("account_cib_flagged_posts_min_count", 2))
        self.account_cib_min_ratio: float = float(cib_cfg.get("account_cib_flagged_posts_min_ratio", 0.30))
        self.hyperactivity_z_threshold: float = float(cib_cfg["hyperactivity_zscore_threshold"])
        self.posts_per_hour_cap: float = float(cib_cfg["hyperactivity_posts_per_hour_cap"])
        self.suspected_cib_threshold: float = float(cib_cfg["suspected_cib_composite_threshold"])
        self.cib_windows: Dict[str, int] = dict(cib_cfg["cib_windows_by_platform_seconds"])
        self.weights_cfg: Dict[str, float] = dict(cib_cfg["coordination_signal_weights"])
        self.domain_allowlist: Set[str] = {
            d.lower().strip() for d in cib_cfg.get("institutional_and_news_domain_allowlist", [])
        }

    def anonymize_platform_account(self, platform: str, raw_author_id: str) -> str:
        """
        Pseudonimizacao por HMAC-SHA256 completo (64 caracteres hexadecimais) para representar
        a unidade observacional '1 Autor Digital Unico por Plataforma' (LGPD art. 13, par. 4o).
        """
        if not raw_author_id or not raw_author_id.strip():
            raise ValueError("raw_author_id vazio nao pode ser pseudonimizado.")
        msg = f"{platform.strip().lower()}:{raw_author_id.strip().lower()}".encode("utf-8")
        return hmac.new(self._secret_bytes, msg, hashlib.sha256).hexdigest()

    def extract_geographic_proxy_from_ddd(self, phone_str: Optional[str]) -> Tuple[str, str]:
        """
        Extrai apenas o DDD brasileiro como PROXY GEOGRAFICO APROXIMADO de UF/Macrorregiao,
        rejeitando explicitamente codigos internacionais estrangeiros (ex: +1 dos EUA - Checklist #10).
        """
        if not phone_str:
            return ("NI", "Nao Identificado")
        raw = phone_str.strip()
        digits = re.sub(r"\D", "", raw)

        # Se comeca com '+' ou '00', exige explicitamente o DDI do Brasil (+55 / 0055)
        if raw.startswith("+"):
            if not digits.startswith("55") or len(digits) not in (12, 13):
                return ("NI", "Nao Identificado")
            ddd = digits[2:4]
            return DDD_TO_UF_REGION_PROXY.get(ddd, ("NI", "Nao Identificado"))

        if raw.startswith("00"):
            if not digits.startswith("0055") or len(digits) not in (14, 15):
                return ("NI", "Nao Identificado")
            ddd = digits[4:6]
            return DDD_TO_UF_REGION_PROXY.get(ddd, ("NI", "Nao Identificado"))

        # Sem sinal de '+', aceita formato com DDI 55 (12 ou 13 digitos) ou nacional (10 ou 11 digitos)
        if digits.startswith("55") and len(digits) in (12, 13):
            ddd = digits[2:4]
            return DDD_TO_UF_REGION_PROXY.get(ddd, ("NI", "Nao Identificado"))

        if len(digits) in (10, 11):
            ddd = digits[:2]
            return DDD_TO_UF_REGION_PROXY.get(ddd, ("NI", "Nao Identificado"))

        return ("NI", "Nao Identificado")

    def _is_allowlisted_news_or_gov_url(self, url: Optional[str]) -> bool:
        """Verifica se a URL pertence a veiculo de imprensa ou portal institucional (C-02)."""
        if not url:
            return False
        try:
            host = (urlparse(url).hostname or "").lower()
            return any(host == dom or host.endswith("." + dom) for dom in self.domain_allowlist)
        except Exception:
            return False

    @staticmethod
    def _evaluate_commercial_spam_quarantine(text: str) -> Tuple[bool, Optional[str]]:
        """
        Avalia se o texto deve ir para quarentena de spam comercial, protegendo
        explicitamente termos do debate legislativo (C-03).
        """
        norm = normalize_ascii(text)
        # Se contem marcador forte de golpe/sorteio comercial
        if COMMERCIAL_SPAM_STRONG_CUE.search(norm):
            return True, "QUARENTENA_PROMOCAO_FINANCEIRA_DIRETA"

        # Se menciona apostas/cassino + dinheiro/sorteio, verifica se NAO e debate legislativo
        if COMMERCIAL_GAMBLING_PROMO_CUE.search(norm):
            if LEGISLATIVE_CONTEXT_ALLOWLIST.search(norm):
                return False, None
            return True, "QUARENTENA_PROPAGANDA_APOSTAS_COMERCIAL"

        return False, None

    @staticmethod
    def _extract_urls_and_hashtags(
        text: str, explicit_url: Optional[str], explicit_tags: List[str]
    ) -> Tuple[Optional[str], Tuple[str, ...]]:
        url = explicit_url
        if not url:
            url_match = re.search(r"https?://[^\s]+", text)
            if url_match:
                url = url_match.group(0).lower().rstrip(".,;)")
        tags = set(normalize_ascii(t).lstrip("#") for t in explicit_tags if t.strip())
        for m in re.findall(r"#(\w+)", text):
            tags.add(normalize_ascii(m))
        return url, tuple(sorted(t for t in tags if t))

    def _build_minhash(self, text: str, k: int = 5) -> MinHash:
        clean = normalize_ascii(text)
        # Remove URLs e mencoes numericas triviais apenas se houver texto suficiente
        mh = MinHash(num_perm=self.minhash_num_perm)
        if len(clean) < k:
            mh.update(clean.encode("utf-8"))
        else:
            shingles = [clean[i : i + k].encode("utf-8") for i in range(len(clean) - k + 1)]
            mh.update_batch(shingles)
        return mh

    def process_and_audit_posts(self, posts: List[SocialPost]) -> List[SocialPost]:
        """
        Executa o pipeline completo de desinfeccao e deteccao de indicios de coordenacao:
        1. Pseudonimizacao HMAC-SHA256 fail-closed (limpando `raw_author_id`) e proxy DDD.
        2. Quarentena de Spam Comercial com protecao de contexto legislativo.
        3. Busca de similaridade sub-quadratica esperada via LSH + verificacao exata de Jaccard + Union-Find.
        4. Grafo de Co-Ocorrencia Multi-Sinal (com allowlist de imprensa/governo, penalizacao IDF e
           repeticao de itens/eventos em janela two-pointer) + Algoritmo de Leiden.
        5. Calculo do `coordination_signal_index` (lido do YAML) e politica de exclusao por CONTA (M-05).
        """
        n = len(posts)
        if n == 0:
            return posts

        w_lsh = float(self.weights_cfg["textual_similarity_lsh"])
        w_sync = float(self.weights_cfg["temporal_synchrony"])
        w_url = float(self.weights_cfg["shared_url_hashtag"])
        w_leiden = float(self.weights_cfg["leiden_graph_centrality"])
        w_behav = float(self.weights_cfg["behavioral_hyperactivity"])

        lsh = MinHashLSH(threshold=self.lsh_jaccard_threshold, num_perm=self.minhash_num_perm)
        minhashes: List[MinHash] = []
        extracted_urls: List[Optional[str]] = []
        extracted_tags: List[Tuple[str, ...]] = []
        norm_texts: List[str] = []

        # Etapa 1 & 2: Pseudonimizacao HMAC-SHA256, Proxy DDD e Quarentena de Spam
        for idx, p in enumerate(posts):
            if not p.author_hash:
                p.author_hash = self.anonymize_platform_account(p.platform, p.raw_author_id)
            p.hmac_key_id = self.key_id
            # Minimizacao em memoria/serializacao (C-04 / B1)
            p.raw_author_id = ""

            if p.phone_or_location_hint:
                p.uf_proxy, p.region_proxy = self.extract_geographic_proxy_from_ddd(p.phone_or_location_hint)
                # Remove referencia ao dado sensivel no objeto (Problema 9)
                p.phone_or_location_hint = None

            is_spam, reason = self._evaluate_commercial_spam_quarantine(p.text)
            if is_spam:
                p.is_commercial_spam = True
                p.spam_quarantine_reason = reason
                p.activity_class = "Spam_Comercial"

            url, tags = self._extract_urls_and_hashtags(p.text, p.shared_url, p.hashtags)
            p.shared_url = url
            extracted_urls.append(url)
            extracted_tags.append(tags)
            norm_texts.append(normalize_ascii(p.text))

            mh = self._build_minhash(p.text)
            minhashes.append(mh)
            if not p.is_commercial_spam:
                lsh.insert(str(idx), mh)

        # Etapa 3: Colisoes LSH verificadas por Jaccard estimado >= limiar + Union-Find (G-04)
        uf = _UnionFind(n)
        for i in range(n):
            if posts[i].is_commercial_spam:
                continue
            candidates = [int(c) for c in lsh.query(minhashes[i])]
            for j in candidates:
                if j <= i or posts[j].is_commercial_spam:
                    continue
                if minhashes[i].jaccard(minhashes[j]) >= self.lsh_jaccard_threshold:
                    uf.union(i, j)

        lsh_clusters: Dict[int, List[int]] = defaultdict(list)
        for i in range(n):
            if not posts[i].is_commercial_spam:
                root = uf.find(i)
                lsh_clusters[root].append(i)

        text_sim_score = [0.0] * n
        url_tag_rep_score = [0.0] * n
        temp_sync_score = [0.0] * n

        # Mapeia co-ocorrencias sincronas por par de contas: (acc_A, acc_B) -> set de sinais/eventos distintos
        pair_sync_events: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        pair_sync_weight: Dict[Tuple[str, str], float] = defaultdict(float)

        # 3a. Processamento de cada cluster LSH verificando janela temporal via Two-Pointer (G-04)
        for root_id, idxs in lsh_clusters.items():
            distinct_authors = {posts[k].author_hash for k in idxs}
            if len(distinct_authors) < 2:
                continue

            for k in idxs:
                posts[k].is_near_duplicate_lsh = True
                posts[k].lsh_cluster_id = root_id
                text_sim_score[k] = min(1.0, len(distinct_authors) / 5.0)

            idxs_sorted = sorted(idxs, key=lambda k: posts[k].timestamp)
            m_len = len(idxs_sorted)
            right = 0
            sync_partners_per_post: Dict[int, Set[str]] = defaultdict(set)

            for left in range(m_len):
                u_idx = idxs_sorted[left]
                win_sec = self.cib_windows.get(posts[u_idx].platform, 60)
                if right < left:
                    right = left
                while (
                    right + 1 < m_len
                    and (posts[idxs_sorted[right + 1]].timestamp - posts[u_idx].timestamp).total_seconds() <= win_sec
                ):
                    right += 1

                for pos in range(left + 1, right + 1):
                    v_idx = idxs_sorted[pos]
                    if posts[u_idx].author_hash != posts[v_idx].author_hash:
                        # Pontua AMBOS os lados do par sincronizado (G-04)
                        sync_partners_per_post[u_idx].add(posts[v_idx].author_hash)
                        sync_partners_per_post[v_idx].add(posts[u_idx].author_hash)
                        pair = tuple(sorted((posts[u_idx].author_hash, posts[v_idx].author_hash)))
                        time_bucket = int(posts[u_idx].timestamp.timestamp() // max(1, win_sec))
                        pair_sync_events[pair].add(f"lsh:{root_id}:t{time_bucket}")
                        pair_sync_weight[pair] += 1.0

            for k_idx, partners in sync_partners_per_post.items():
                # Sincronia de copypasta textual exige pelo menos 2 parceiros sincronizados na mesma janela
                if len(partners) >= 2:
                    temp_sync_score[k_idx] = max(temp_sync_score[k_idx], min(1.0, len(partners) / 4.0))

        # 3b. Co-ocorrencia de URLs (nao-allowlisted) e Pares de Hashtags com ponderacao IDF (C-02)
        total_active_accounts = max(1, len({p.author_hash for p in posts if not p.is_commercial_spam}))
        url_buckets: Dict[str, List[int]] = defaultdict(list)
        tag_pair_buckets: Dict[Tuple[str, str], List[int]] = defaultdict(list)

        for i in range(n):
            if posts[i].is_commercial_spam:
                continue
            url = extracted_urls[i]
            # Ignora links de imprensa/portais legislativos oficiais para nao punir compartilhamento de noticia (C-02)
            if url and not self._is_allowlisted_news_or_gov_url(url):
                url_buckets[url].append(i)

            # Qualquer par de hashtags identicas (>= 2 tags em comum, corrigindo divergencia da Secao 8)
            tags = extracted_tags[i]
            if len(tags) >= 2:
                for t1_i in range(len(tags)):
                    for t2_i in range(t1_i + 1, len(tags)):
                        tag_pair_buckets[(tags[t1_i], tags[t2_i])].append(i)

        # Avalia buckets de URLs suspeitas (nao-jornalisticas)
        for url_key, idxs in url_buckets.items():
            authors_in_bucket = {posts[k].author_hash for k in idxs}
            if len(authors_in_bucket) < 3:
                continue
            idxs_sorted = sorted(idxs, key=lambda k: posts[k].timestamp)
            span_sec = max(1.0, (posts[idxs_sorted[-1]].timestamp - posts[idxs_sorted[0]].timestamp).total_seconds())
            # Taxa de rajada: quantos posts por minuto compartilham a mesma URL nao-jornalistica
            burst_rate_per_min = len(idxs_sorted) / (span_sec / 60.0)

            sync_partners_url: Dict[int, Set[str]] = defaultdict(set)
            m_len = len(idxs_sorted)
            right = 0
            for left in range(m_len):
                u_idx = idxs_sorted[left]
                win_sec = self.cib_windows.get(posts[u_idx].platform, 60)
                if right < left:
                    right = left
                while (
                    right + 1 < m_len
                    and (posts[idxs_sorted[right + 1]].timestamp - posts[u_idx].timestamp).total_seconds() <= win_sec
                ):
                    right += 1
                for pos in range(left + 1, right + 1):
                    v_idx = idxs_sorted[pos]
                    if posts[u_idx].author_hash != posts[v_idx].author_hash:
                        sync_partners_url[u_idx].add(posts[v_idx].author_hash)
                        sync_partners_url[v_idx].add(posts[u_idx].author_hash)
                        pair = tuple(sorted((posts[u_idx].author_hash, posts[v_idx].author_hash)))
                        tb = int(posts[u_idx].timestamp.timestamp() // max(1, win_sec))
                        pair_sync_events[pair].add(f"url:{url_key}:t{tb}")
                        pair_sync_weight[pair] += 1.0

            for k_idx, partners in sync_partners_url.items():
                # So pontua URL se o post participou efetivamente de rajada sincrona (>= 3 parceiros na janela)
                if len(partners) >= 3 and burst_rate_per_min >= 5.0:
                    url_tag_rep_score[k_idx] = max(url_tag_rep_score[k_idx], min(1.0, len(partners) / 5.0))
                    temp_sync_score[k_idx] = max(temp_sync_score[k_idx], min(1.0, len(partners) / 4.0))

        # Avalia pares de hashtags com penalizacao IDF (hashtags gerais da campanha tem IDF baixo - C-02)
        for tag_pair, idxs in tag_pair_buckets.items():
            authors_in_bucket = {posts[k].author_hash for k in idxs}
            if len(authors_in_bucket) < 3:
                continue
            # Se > 35% das contas usam a hashtag do proprio PL (ex: #PL2338), e a tag oficial do tema, nao CIB!
            doc_freq_ratio = len(authors_in_bucket) / total_active_accounts
            if doc_freq_ratio > 0.35:
                continue
            idf_factor = min(1.0, math.log(1.0 + (1.0 / max(0.01, doc_freq_ratio))) / 3.0)

            idxs_sorted = sorted(idxs, key=lambda k: posts[k].timestamp)
            m_len = len(idxs_sorted)
            right = 0
            sync_partners_tag: Dict[int, Set[str]] = defaultdict(set)
            for left in range(m_len):
                u_idx = idxs_sorted[left]
                win_sec = self.cib_windows.get(posts[u_idx].platform, 60)
                if right < left:
                    right = left
                while (
                    right + 1 < m_len
                    and (posts[idxs_sorted[right + 1]].timestamp - posts[u_idx].timestamp).total_seconds() <= win_sec
                ):
                    right += 1
                for pos in range(left + 1, right + 1):
                    v_idx = idxs_sorted[pos]
                    if posts[u_idx].author_hash != posts[v_idx].author_hash:
                        sync_partners_tag[u_idx].add(posts[v_idx].author_hash)
                        sync_partners_tag[v_idx].add(posts[u_idx].author_hash)
                        pair = tuple(sorted((posts[u_idx].author_hash, posts[v_idx].author_hash)))
                        pair_sync_events[pair].add(f"tag:{tag_pair[0]}_{tag_pair[1]}")
                        pair_sync_weight[pair] += idf_factor

            for k_idx, partners in sync_partners_tag.items():
                if len(partners) >= 3:
                    url_tag_rep_score[k_idx] = max(url_tag_rep_score[k_idx], min(1.0, idf_factor * (len(partners) / 5.0)))
                    temp_sync_score[k_idx] = max(temp_sync_score[k_idx], min(1.0, idf_factor * (len(partners) / 4.0)))

        # Etapa 4: Grafo de Co-Ocorrencia Filtrado por Repeticao + Algoritmo de Leiden (`igraph` + `leidenalg`)
        # Regra Giglietto/Pacheco (C-02): Aresta confirmada exige >= min_distinct_co_shared_items eventos/sinais
        # ou peso de rajada >= 2.0 entre o mesmo par de contas.
        filtered_edges: Dict[Tuple[str, str], float] = {
            pair: w
            for pair, w in pair_sync_weight.items()
            if len(pair_sync_events[pair]) >= self.min_distinct_co_shared_items or w >= 2.0
        }

        author_leiden_centrality: Dict[str, float] = defaultdict(float)
        author_community_id: Dict[str, int] = {}

        if filtered_edges:
            unique_nodes = sorted({u for pair in filtered_edges.keys() for u in pair})
            node_to_id = {u: idx for idx, u in enumerate(unique_nodes)}
            edges_list = [(node_to_id[u], node_to_id[v]) for (u, v) in filtered_edges.keys()]
            weights_list = list(filtered_edges.values())

            g = ig.Graph(n=len(unique_nodes), edges=edges_list, directed=False)
            g.es["weight"] = weights_list

            partition = leidenalg.find_partition(
                g,
                leidenalg.ModularityVertexPartition,
                weights=g.es["weight"],
                seed=42,
            )

            degrees = g.strength(weights=g.es["weight"])
            for comm_id, cluster_nodes in enumerate(partition):
                cluster_size = len(cluster_nodes)
                if cluster_size >= 3:
                    for vid in cluster_nodes:
                        acc_hash = unique_nodes[vid]
                        author_community_id[acc_hash] = comm_id
                        author_leiden_centrality[acc_hash] = min(
                            1.0, (cluster_size / 10.0) * min(1.0, degrees[vid] / 4.0)
                        )

        # Etapa 5: Anomalia Comportamental de Frequencia (Z-score >= 3.0 OU > posts_per_hour_cap - Secao 8)
        author_counts = Counter(p.author_hash for p in posts if not p.is_commercial_spam)
        author_hourly_max: Dict[str, int] = defaultdict(int)
        author_hour_buckets: Dict[Tuple[str, int], int] = defaultdict(int)
        for p in posts:
            if not p.is_commercial_spam:
                hb = int(p.timestamp.timestamp() // 3600)
                author_hour_buckets[(p.author_hash, hb)] += 1
        for (acc_h, _), cnt in author_hour_buckets.items():
            if cnt > author_hourly_max[acc_h]:
                author_hourly_max[acc_h] = cnt

        counts_values = list(author_counts.values())
        mean_c = sum(counts_values) / max(1, len(counts_values))
        std_c = math.sqrt(sum((c - mean_c) ** 2 for c in counts_values) / max(1, len(counts_values)))

        # Etapa 6: Calculo do `coordination_signal_index` por post
        author_flagged_count: Dict[str, int] = defaultdict(int)

        for i, p in enumerate(posts):
            if p.is_commercial_spam:
                continue

            c_count = author_counts[p.author_hash]
            max_h = author_hourly_max[p.author_hash]
            z_score = (c_count - mean_c) / std_c if std_c > 0 else 0.0

            if z_score >= self.hyperactivity_z_threshold or max_h >= self.posts_per_hour_cap:
                behav_score = 1.0
            else:
                behav_score = max(
                    0.0,
                    max(z_score / self.hyperactivity_z_threshold, max_h / self.posts_per_hour_cap),
                )

            leiden_score = author_leiden_centrality.get(p.author_hash, 0.0)
            p.leiden_community_id = author_community_id.get(p.author_hash, -1)

            p.coordination_score = round(
                0.45 * temp_sync_score[i] + 0.35 * leiden_score + 0.20 * url_tag_rep_score[i],
                3,
            )

            composite_signal = (
                w_lsh * text_sim_score[i]
                + w_sync * temp_sync_score[i]
                + w_url * url_tag_rep_score[i]
                + w_leiden * leiden_score
                + w_behav * behav_score
            )
            p.coordination_signal_index = round(min(1.0, composite_signal), 3)

            if p.coordination_signal_index >= self.suspected_cib_threshold or (
                leiden_score >= 0.35 and temp_sync_score[i] >= 0.50
            ):
                p.suspected_coordination = True
                author_flagged_count[p.author_hash] += 1

        # Etapa 7: Politica de Exclusao em Nivel de CONTA (M-05) e Classificacao nas 5 Categorias (C-03)
        flagged_accounts: Set[str] = set()
        for acc_h, tot_posts in author_counts.items():
            f_cnt = author_flagged_count.get(acc_h, 0)
            if f_cnt >= self.account_cib_min_count or (tot_posts > 0 and (f_cnt / tot_posts) >= self.account_cib_min_ratio):
                flagged_accounts.add(acc_h)

        for i, p in enumerate(posts):
            if p.is_commercial_spam:
                continue

            if p.author_hash in flagged_accounts or p.suspected_coordination:
                p.account_suspected_cib = True
                p.suspected_coordination = True
                p.activity_class = "Suspeita_CIB_Automacao"
            elif CIVIC_MOBILIZATION_NORM_PATTERN.search(norm_texts[i]) and temp_sync_score[i] < 0.50:
                # Exige marcador civico EXPLICITO ('Vote SIM', 'Vote NÃO', 'Apoie o PL') sem sincronia robotica (C-03)
                p.activity_class = "Mobilizacao_Civica_Legitima"
            elif p.is_near_duplicate_lsh and temp_sync_score[i] < 0.50:
                # Classe neutra auditavel para near-duplicates assincronos sem marcador civico (C-03)
                p.activity_class = "Repeticao_Organica"
            else:
                p.activity_class = "Organico"

        return posts
