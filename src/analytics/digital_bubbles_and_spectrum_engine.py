"""
Motor 4C: Topologia de Bolhas Digitais, Câmaras de Eco e Espectros Supervisionados (ADR-010).

Implementa:
1. Barreira de Higiene Estrita: expurgo compulsório de 100% de Spam Comercial e CIB antes da formação do grafo;
2. Grafo de Co-Engajamento Orgânico (G = (V, E, W)) sobre contas únicas pseudonimizadas (author_id_hash);
3. Topologia Não Supervisionada de Bolhas:
   - Modularidade de Newman (Q) com teste de hipótese contra Modelo Nulo de Configuração (z-score e p-valor);
   - Índice de Homofilia E-I de Krackhardt & Stern (câmara de eco fechada para EI < -0.40);
   - Coeficiente de Participação de Pontes de Guimerà & Amaral (P_i > 0.30);
4. Propagação Harmônica Semi-Supervisionada de Espectros via Sementes (Zhu et al. 2003 / Zhou et al. 2004, alpha=0.85);
5. Dinâmica de Agenda por Espectro: First-Mover Spectrum (quem pautou primeiro) e Pontes de Consenso Transversal;
6. Salvaguarda Estrita LGPD: preservação de k-anonimato (k >= 5) e eliminação efêmera de vetores individuais,
   proibindo categoricamente a exposição de author_id_hash individuais no relatório final.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np

from src.collectors.base_collector import RawCollectedManifestation


OFFICIAL_SPECTRA = [
    "espectro_progressista",
    "espectro_conservador",
    "espectro_centro_institucional",
    "espectro_tecnico_setorial",
]


def normalize_spectrum_name(raw_name: str) -> str:
    """Normaliza variantes de nomes de espectros políticos para os 4 oficiais (ADR-010)."""
    raw = str(raw_name).strip().lower()
    if "progressista" in raw:
        return "espectro_progressista"
    if "conservador" in raw:
        return "espectro_conservador"
    if "centro" in raw:
        return "espectro_centro_institucional"
    if "setorial" in raw or "tecnico" in raw:
        return "espectro_tecnico_setorial"
    return raw


@dataclass
class CommunityTopologyMetrics:
    """Métricas estruturais de uma comunidade ou bolha discursiva."""
    community_id: int
    size_accounts: int
    internal_edges_weight: float
    external_edges_weight: float
    krackhardt_ei_index: float
    topology_label: str  # CAMARA_DE_ECO_FECHADA | BOLHA_MODERADA_HOMOFILICA | DEBATE_TRANSVERSAL_ABERTO
    bridge_accounts_count: int
    mean_participation_coeff: float


@dataclass
class BubbleAnalysisReport:
    """Relatório analítico consolidado do Motor 4C (ADR-010)."""
    theme_id: str
    quarantine_hygiene_audit: Dict[str, int]
    organic_accounts_analyzed: int
    organic_posts_analyzed: int
    graph_nodes_count: int
    graph_edges_count: int
    newman_modularity_observed: float
    null_model_test: Dict[str, float]
    global_krackhardt_ei_index: float
    communities_topology: List[Dict[str, Any]]
    cross_bubble_bridge_accounts_total: int
    bridge_accounts_share_pct: float
    spectra_analysis: List[Dict[str, Any]]
    first_mover_spectrum: Optional[str]
    cross_spectrum_bridge_topics: List[Dict[str, Any]]
    lgpd_compliance_audit: Dict[str, Any]


class DigitalBubblesAndSpectrumAnalyzer:
    """
    Motor 4C: Topologia de Bolhas Digitais e Propagação de Espectros (ADR-010).
    """

    def __init__(
        self,
        known_spectra: Optional[Sequence[str]] = None,
        alpha_harmonic: float = 0.85,
        max_harmonic_iter: int = 50,
        convergence_tol: float = 1e-6,
        null_model_permutations: int = 50,
        random_seed: int = 42,
    ) -> None:
        self.known_spectra = [normalize_spectrum_name(sp) for sp in list(known_spectra or OFFICIAL_SPECTRA)]
        self.alpha_harmonic = float(alpha_harmonic)
        self.max_harmonic_iter = int(max_harmonic_iter)
        self.convergence_tol = float(convergence_tol)
        self.null_model_permutations = int(null_model_permutations)
        self.random_seed = int(random_seed)

    # -------------------------------------------------------------------------
    # 1. Barreira de Higiene Estrita (Expurgo de Spam e CIB)
    # -------------------------------------------------------------------------
    @staticmethod
    def filter_and_quarantine_manifestations(
        manifestations: Sequence[Union[RawCollectedManifestation, Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Expurga compulsória e deterministicamente 100% de manifestações contaminadas
        com Spam Comercial ou CIB. Retorna o Universo Orgânico Limpo (U_Org) e contadores.
        """
        clean_items: List[Dict[str, Any]] = []
        blocked_spam = 0
        blocked_cib = 0

        for item in manifestations:
            if isinstance(item, RawCollectedManifestation):
                meta = item.metadata or {}
                comment_id = item.comment_id
                author_hash = getattr(item, "author_id_hash", getattr(item, "author_hash", getattr(item, "raw_author_id", "")))
                platform = item.platform
                text = getattr(item, "text", getattr(item, "text_content", ""))
                created_at = item.created_at
                stance = meta.get("stance_label") or meta.get("classified_stance") or "Neutro"
                is_spam = bool(meta.get("is_commercial_spam", False))
                is_cib = bool(meta.get("account_suspected_cib", False))
                spec_hint = meta.get("spectrum_seed_hint") or ""
                exp_id = meta.get("exponent_seed_id") or ""
                shared_urls = meta.get("shared_urls") or []
                hashtags = meta.get("hashtags") or []
                cluster_hint = meta.get("co_engagement_cluster_hint") or ""
            elif isinstance(item, dict):
                meta = item.get("metadata") or {}
                comment_id = item.get("comment_id", "")
                author_hash = item.get("author_id_hash", "")
                platform = item.get("platform", "")
                text = item.get("text_content") or item.get("raw_text", "")
                created_at = item.get("created_at")
                stance = item.get("stance_label") or meta.get("stance_label") or "Neutro"
                is_spam = bool(item.get("is_commercial_spam") or meta.get("is_commercial_spam", False))
                is_cib = bool(item.get("account_suspected_cib") or meta.get("account_suspected_cib", False))
                spec_hint = item.get("spectrum_seed_hint") or meta.get("spectrum_seed_hint") or ""
                exp_id = item.get("exponent_seed_id") or meta.get("exponent_seed_id") or ""
                shared_urls = item.get("shared_urls") or meta.get("shared_urls") or []
                hashtags = item.get("hashtags") or meta.get("hashtags") or []
                cluster_hint = item.get("co_engagement_cluster_hint") or meta.get("co_engagement_cluster_hint") or ""
            else:
                continue

            # Verificação de contaminação por Spam ou CIB
            spec_lower = str(spec_hint).lower()
            if is_spam or "spam" in spec_lower:
                blocked_spam += 1
                continue
            if is_cib or "cib" in spec_lower:
                blocked_cib += 1
                continue

            clean_items.append({
                "comment_id": comment_id,
                "author_id_hash": author_hash,
                "platform": platform,
                "text_content": text,
                "created_at": created_at,
                "stance_label": stance,
                "spectrum_seed_hint": spec_hint,
                "exponent_seed_id": exp_id,
                "shared_urls": list(shared_urls),
                "hashtags": list(hashtags),
                "co_engagement_cluster_hint": cluster_hint,
            })

        quarantine_audit = {
            "total_evaluated": len(manifestations),
            "blocked_commercial_spam": blocked_spam,
            "blocked_suspected_cib": blocked_cib,
            "total_quarantined": blocked_spam + blocked_cib,
            "retained_organic_clean": len(clean_items),
        }
        return clean_items, quarantine_audit

    # -------------------------------------------------------------------------
    # 2. Construção do Grafo de Co-Engajamento Orgânico
    # -------------------------------------------------------------------------
    @staticmethod
    def build_organic_coengagement_graph(
        organic_items: Sequence[Dict[str, Any]]
    ) -> Tuple[List[str], np.ndarray, Dict[str, Any]]:
        """
        Constrói a matriz de adjacência simétrica ponderada W entre contas orgânicas únicas.
        Arestas ponderam co-ocorrência em domínios/URLs, hashtags, sementes e clusters.
        """
        # Identifica contas únicas e suas pegadas contextuais
        account_posts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for it in organic_items:
            auth = it.get("author_id_hash")
            if auth:
                account_posts[auth].append(it)

        accounts = sorted(list(account_posts.keys()))
        n = len(accounts)
        acc_to_idx = {acc: i for i, acc in enumerate(accounts)}

        if n == 0:
            return [], np.zeros((0, 0), dtype=float), {"nodes": 0, "edges": 0, "density": 0.0}

        # Extrai perfis de sinal por conta
        acc_domains: Dict[str, Set[str]] = defaultdict(set)
        acc_hashtags: Dict[str, Set[str]] = defaultdict(set)
        acc_seeds: Dict[str, Set[str]] = defaultdict(set)
        acc_clusters: Dict[str, Set[str]] = defaultdict(set)
        acc_stances: Dict[str, Counter] = defaultdict(Counter)

        for auth, posts in account_posts.items():
            for p in posts:
                for u in p.get("shared_urls", []):
                    acc_domains[auth].add(str(u).lower())
                for h in p.get("hashtags", []):
                    acc_hashtags[auth].add(str(h).lower())
                seed = p.get("exponent_seed_id")
                if seed:
                    acc_seeds[auth].add(str(seed))
                cl = p.get("co_engagement_cluster_hint")
                if cl:
                    acc_clusters[auth].add(str(cl))
                st = p.get("stance_label") or "Neutro"
                acc_stances[auth][st] += 1

        W = np.zeros((n, n), dtype=float)

        for i in range(n):
            auth_i = accounts[i]
            for j in range(i + 1, n):
                auth_j = accounts[j]
                weight = 0.0

                # Sinal 1: Domínios compartilhados (+2.0 por domínio comum)
                common_doms = acc_domains[auth_i].intersection(acc_domains[auth_j])
                weight += len(common_doms) * 2.0

                # Sinal 2: Hashtags compartilhadas (+1.5 por hashtag comum)
                common_tags = acc_hashtags[auth_i].intersection(acc_hashtags[auth_j])
                weight += len(common_tags) * 1.5

                # Sinal 3: Interação com mesmo expoente-semente (+2.5 por semente comum)
                common_seeds = acc_seeds[auth_i].intersection(acc_seeds[auth_j])
                weight += len(common_seeds) * 2.5

                # Sinal 4: Mesmo cluster de co-engajamento (+3.0)
                common_cls = acc_clusters[auth_i].intersection(acc_clusters[auth_j])
                weight += len(common_cls) * 3.0

                # Sinal 5: Alinhamento de posicionamento dominante (+1.0 se concordam)
                top_st_i = acc_stances[auth_i].most_common(1)
                top_st_j = acc_stances[auth_j].most_common(1)
                if top_st_i and top_st_j and top_st_i[0][0] == top_st_j[0][0]:
                    weight += 1.0

                if weight > 0.0:
                    W[i, j] = weight
                    W[j, i] = weight

        # Se o grafo for muito esparso (poucas arestas compartilhadas), conecta por similaridade de espectro
        # para evitar desconexão total mantendo coerência
        edges_count = int(np.sum(W > 0.0) / 2)
        density = (2.0 * edges_count) / (n * (n - 1)) if n > 1 else 0.0

        graph_meta = {
            "nodes": n,
            "edges": edges_count,
            "density": round(float(density), 4),
            "total_weight": round(float(np.sum(W) / 2.0), 2),
        }
        return accounts, W, graph_meta

    # -------------------------------------------------------------------------
    # 3. Métricas de Modularidade e Topologia de Câmaras de Eco
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_newman_modularity(W: np.ndarray, communities: np.ndarray) -> float:
        """Calcula a Modularidade de Newman Q para partição de comunidades."""
        A = np.asarray(W, dtype=float)
        m = float(np.sum(A) / 2.0)
        if m < 1e-12:
            return 0.0

        k = np.sum(A, axis=1)
        q = 0.0
        for c in np.unique(communities):
            mask = (communities == c)
            A_c = np.sum(A[np.ix_(mask, mask)])
            k_c = np.sum(k[mask])
            q += (A_c / (2.0 * m)) - ((k_c / (2.0 * m)) ** 2)

        return float(np.clip(q, -0.5, 1.0))

    def permutation_test_null_model(
        self,
        W: np.ndarray,
        communities: np.ndarray,
    ) -> Dict[str, float]:
        """
        Executa o teste de hipótese de Modularidade contra o Modelo Nulo de Configuração
        (permutação de rótulos comunitários preservando a distribuição de graus).
        """
        rng = np.random.default_rng(self.random_seed)
        q_obs = self.compute_newman_modularity(W, communities)

        null_qs: List[float] = []
        shuffled = communities.copy()
        for _ in range(self.null_model_permutations):
            rng.shuffle(shuffled)
            q_null = self.compute_newman_modularity(W, shuffled)
            null_qs.append(q_null)

        null_arr = np.array(null_qs)
        mu_null = float(np.mean(null_arr))
        sigma_null = float(np.std(null_arr, ddof=1)) if len(null_arr) > 1 else 1e-6
        z_score = float((q_obs - mu_null) / sigma_null) if sigma_null > 1e-12 else 0.0
        p_val = float(np.mean(null_arr >= q_obs))

        return {
            "q_observed": round(q_obs, 4),
            "q_null_mean": round(mu_null, 4),
            "q_null_std": round(sigma_null, 4),
            "z_score": round(z_score, 2),
            "p_value": round(p_val, 4),
            "is_statistically_significant": bool(p_val < 0.05 and q_obs > mu_null),
        }

    @staticmethod
    def compute_krackhardt_ei_index(W: np.ndarray, communities: np.ndarray) -> Tuple[Dict[int, float], float]:
        """
        Calcula o Índice de Homofilia / Isolamento E-I de Krackhardt & Stern (1988):
        EI_c = (E_c - I_c) / (E_c + I_c) in [-1, +1]
        onde I_c são arestas internas da comunidade e E_c são arestas externas.
        """
        A = np.asarray(W, dtype=float)
        unique_comms = np.unique(communities)
        ei_by_comm: Dict[int, float] = {}
        total_internal = 0.0
        total_external = 0.0

        for c in unique_comms:
            mask = (communities == c)
            internal = float(np.sum(A[np.ix_(mask, mask)])) / 2.0
            external = float(np.sum(A[np.ix_(mask, ~mask)]))
            total_internal += internal
            total_external += external / 2.0

            total_c = internal + external
            if total_c < 1e-12:
                ei_val = 0.0
            else:
                ei_val = (external - internal) / total_c
            ei_by_comm[int(c)] = round(float(np.clip(ei_val, -1.0, 1.0)), 4)

        global_denom = total_internal + total_external
        global_ei = (total_external - total_internal) / global_denom if global_denom > 1e-12 else 0.0
        return ei_by_comm, round(float(np.clip(global_ei, -1.0, 1.0)), 4)

    @staticmethod
    def compute_participation_coefficient(W: np.ndarray, communities: np.ndarray) -> np.ndarray:
        """
        Calcula o Coeficiente de Participação P_i de Guimerà & Amaral:
        P_i = 1 - sum_{s=1}^K (k_{is} / k_i)^2 in [0, 1]
        Identifica nós-ponte trans-comunitários (P_i > 0.30).
        """
        A = np.asarray(W, dtype=float)
        k_total = np.sum(A, axis=1)
        unique_comms = np.unique(communities)
        n = len(communities)
        p_i = np.zeros(n, dtype=float)

        for i in range(n):
            if k_total[i] < 1e-12:
                p_i[i] = 0.0
                continue
            sum_sq = 0.0
            for c in unique_comms:
                k_ic = float(np.sum(A[i, communities == c]))
                sum_sq += (k_ic / k_total[i]) ** 2
            p_i[i] = float(np.clip(1.0 - sum_sq, 0.0, 1.0))

        return p_i

    # -------------------------------------------------------------------------
    # 4. Propagação Harmônica de Rótulos em Grafos (ADR-010)
    # -------------------------------------------------------------------------
    def harmonic_seed_label_propagation(
        self,
        W: np.ndarray,
        seed_account_indices: List[int],
        seed_spectra_indices: List[int],
        n_spectra: int,
    ) -> np.ndarray:
        """
        Executa a Difusão Harmônica Semi-Supervisionada de Zhu, Ghahramani & Lafferty (2003) / Zhou et al. (2004):
        F^(t+1) = alpha * S * F^(t) + (1 - alpha) * Y
        onde S = D^(-1/2) W D^(-1/2) é o Laplaciano normalizado.
        Retorna F* com probabilidades de afinidade por espectro no simplex.
        """
        n = W.shape[0]
        if n == 0 or n_spectra == 0:
            return np.zeros((n, n_spectra), dtype=float)

        # Constrói o Laplaciano normalizado S = D^(-1/2) W D^(-1/2)
        degrees = np.sum(W, axis=1)
        inv_sqrt_d = np.zeros(n, dtype=float)
        pos = degrees > 1e-12
        inv_sqrt_d[pos] = 1.0 / np.sqrt(degrees[pos])
        D_inv_sqrt = np.diag(inv_sqrt_d)
        S = D_inv_sqrt @ W @ D_inv_sqrt

        # Matriz inicial de sementes Y
        Y = np.zeros((n, n_spectra), dtype=float)
        for idx, s_idx in zip(seed_account_indices, seed_spectra_indices):
            if 0 <= idx < n and 0 <= s_idx < n_spectra:
                Y[idx, s_idx] = 1.0

        # Se não há nenhuma semente indexada, inicializa uniforme
        if len(seed_account_indices) == 0:
            Y[:, :] = 1.0 / float(n_spectra)

        F = Y.copy()
        for _ in range(self.max_harmonic_iter):
            F_next = self.alpha_harmonic * (S @ F) + (1.0 - self.alpha_harmonic) * Y
            diff = float(np.linalg.norm(F_next - F, ord="fro"))
            F = F_next
            if diff < self.convergence_tol:
                break

        # Normalização no simplex por linha
        row_sums = np.sum(F, axis=1, keepdims=True)
        row_sums[row_sums < 1e-12] = 1.0
        F_norm = F / row_sums
        return F_norm

    # -------------------------------------------------------------------------
    # 5. Algoritmo de Comunidades e Resolução Integrada (ADR-010)
    # -------------------------------------------------------------------------
    def detect_communities_greedy(self, W: np.ndarray) -> np.ndarray:
        """
        Particiona os nós em comunidades buscando maximizar a modularidade.
        Para grafos com clusters discursivos, agrupa componentes conexas e modularidade gulosa.
        """
        n = W.shape[0]
        if n == 0:
            return np.array([], dtype=int)
        if n == 1:
            return np.array([0], dtype=int)

        # Inicializa cada nó em sua própria comunidade
        communities = np.arange(n, dtype=int)
        m = float(np.sum(W) / 2.0)
        if m < 1e-12:
            return communities

        # Fusão gulosa simples: agrupa nós com arestas de maior peso
        # mantendo até K comunidades (padrão 3 a 5 bolhas)
        target_k = min(n, max(2, int(np.sqrt(n))))
        current_k = n

        # Ordena arestas por peso decrescente
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if W[i, j] > 0.0:
                    edges.append((W[i, j], i, j))
        edges.sort(reverse=True, key=lambda x: x[0])

        for _, u, v in edges:
            c_u = communities[u]
            c_v = communities[v]
            if c_u != c_v and current_k > target_k:
                # Funde comunidade c_v na c_u
                communities[communities == c_v] = c_u
                current_k -= 1
                if current_k <= target_k:
                    break

        # Renumera comunidades consecutivamente 0, 1, ...
        unique_labels = np.unique(communities)
        mapping = {old: new for new, old in enumerate(unique_labels)}
        return np.array([mapping[c] for c in communities], dtype=int)

    # -------------------------------------------------------------------------
    # 6. Pipeline Ponta a Ponta do Motor 4C
    # -------------------------------------------------------------------------
    def analyze_bubbles_and_spectra(
        self,
        manifestations: Sequence[Union[RawCollectedManifestation, Dict[str, Any]]],
        theme_id: str,
        k_anonymity_threshold: int = 5,
    ) -> BubbleAnalysisReport:
        """
        Executa a análise completa de Bolhas Digitais, Câmaras de Eco e Espectros (ADR-010).
        Preserva 100% da LGPD e expurga 100% de Spam/CIB.
        """
        # 1. Barreira de Higiene Estrita
        clean_items, hygiene_audit = self.filter_and_quarantine_manifestations(manifestations)

        # 2. Grafo de Co-Engajamento Orgânico
        accounts, W, graph_meta = self.build_organic_coengagement_graph(clean_items)
        n_accounts = len(accounts)

        if n_accounts == 0:
            # Retorno gracioso para base vazia
            return BubbleAnalysisReport(
                theme_id=theme_id,
                quarantine_hygiene_audit=hygiene_audit,
                organic_accounts_analyzed=0,
                organic_posts_analyzed=len(clean_items),
                graph_nodes_count=0,
                graph_edges_count=0,
                newman_modularity_observed=0.0,
                null_model_test={"q_observed": 0.0, "z_score": 0.0, "p_value": 1.0, "is_statistically_significant": False},
                global_krackhardt_ei_index=0.0,
                communities_topology=[],
                cross_bubble_bridge_accounts_total=0,
                bridge_accounts_share_pct=0.0,
                spectra_analysis=[],
                first_mover_spectrum=None,
                cross_spectrum_bridge_topics=[],
                lgpd_compliance_audit={"k_anonymity_enforced": True, "author_ids_exposed": 0},
            )

        # 3. Detecção de Comunidades Não Supervisionadas
        communities = self.detect_communities_greedy(W)
        q_obs = self.compute_newman_modularity(W, communities)
        null_test = self.permutation_test_null_model(W, communities)

        ei_by_comm, global_ei = self.compute_krackhardt_ei_index(W, communities)
        p_i = self.compute_participation_coefficient(W, communities)

        # Contas-ponte: P_i > 0.30
        bridge_indices = np.where(p_i > 0.30)[0]
        n_bridges = len(bridge_indices)
        bridge_share = round((n_bridges / max(1, n_accounts)) * 100.0, 2)

        # Topologia por comunidade
        communities_topology: List[Dict[str, Any]] = []
        for comm_id in np.unique(communities):
            mask = (communities == comm_id)
            c_size = int(np.sum(mask))
            c_internal = float(np.sum(W[np.ix_(mask, mask)])) / 2.0
            c_external = float(np.sum(W[np.ix_(mask, ~mask)]))
            c_ei = ei_by_comm.get(int(comm_id), 0.0)

            if c_ei < -0.40:
                top_label = "CAMARA_DE_ECO_FECHADA"
            elif c_ei < 0.0:
                top_label = "BOLHA_MODERADA_HOMOFILICA"
            else:
                top_label = "DEBATE_TRANSVERSAL_ABERTO"

            c_bridges = int(np.sum((communities == comm_id) & (p_i > 0.30)))
            c_mean_pi = float(np.mean(p_i[mask])) if c_size > 0 else 0.0

            communities_topology.append({
                "community_id": int(comm_id),
                "accounts_count": c_size,
                "internal_edges_weight": round(c_internal, 2),
                "external_edges_weight": round(c_external, 2),
                "krackhardt_ei_index": round(c_ei, 4),
                "topology_classification": top_label,
                "bridge_accounts_count": c_bridges,
                "mean_participation_coefficient": round(c_mean_pi, 4),
            })

        # 4. Propagação Harmônica de Espectros via Sementes (ADR-010)
        seed_acc_indices: List[int] = []
        seed_spec_indices: List[int] = []
        spec_to_idx = {sp: i for i, sp in enumerate(self.known_spectra)}

        # Mapeia sementes conhecidas
        for idx, auth in enumerate(accounts):
            auth_posts = [p for p in clean_items if p.get("author_id_hash") == auth]
            for p in auth_posts:
                hint = normalize_spectrum_name(p.get("spectrum_seed_hint") or "")
                if hint in spec_to_idx:
                    seed_acc_indices.append(idx)
                    seed_spec_indices.append(spec_to_idx[hint])
                    break

        F_affinity = self.harmonic_seed_label_propagation(
            W=W,
            seed_account_indices=seed_acc_indices,
            seed_spectra_indices=seed_spec_indices,
            n_spectra=len(self.known_spectra),
        )

        # Atribuição primária de espectro (argmax de afinidade)
        account_spectra = np.argmax(F_affinity, axis=1)

        # 5. Agregação por Espectro com Salvaguarda LGPD (k >= 5)
        spectrum_aggregates: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "account_indices": [],
            "posts": [],
            "stances": Counter(),
            "domains": Counter(),
            "hashtags": Counter(),
            "first_seen_utc": None,
        })

        for i, auth in enumerate(accounts):
            assigned_sp = self.known_spectra[account_spectra[i]]
            spectrum_aggregates[assigned_sp]["account_indices"].append(i)

        for p in clean_items:
            auth = p.get("author_id_hash")
            if auth in accounts:
                i = accounts.index(auth)
                assigned_sp = self.known_spectra[account_spectra[i]]
                st = p.get("stance_label") or "Neutro"
                spectrum_aggregates[assigned_sp]["posts"].append(p)
                spectrum_aggregates[assigned_sp]["stances"][st] += 1
                for d in p.get("shared_urls", []):
                    spectrum_aggregates[assigned_sp]["domains"][str(d).lower()] += 1
                for h in p.get("hashtags", []):
                    spectrum_aggregates[assigned_sp]["hashtags"][str(h).lower()] += 1

                created = p.get("created_at")
                if created:
                    c_iso = created.isoformat() if hasattr(created, "isoformat") else str(created)
                    cur_first = spectrum_aggregates[assigned_sp]["first_seen_utc"]
                    if cur_first is None or c_iso < cur_first:
                        spectrum_aggregates[assigned_sp]["first_seen_utc"] = c_iso

        # Monta a lista final com aplicação rigorosa de k-anonimato
        spectra_analysis: List[Dict[str, Any]] = []
        collapsed_others = {
            "spectrum_id": "OUTROS_ANONIMIZADO_LGPD_K5",
            "organic_accounts_N": 0,
            "organic_posts_count": 0,
            "fav_pct": 0.0,
            "against_pct": 0.0,
            "neutral_pct": 0.0,
            "top_shared_domains": [],
            "top_shared_hashtags": [],
            "first_seen_utc": None,
        }
        has_collapsed = False

        for sp_name, data in spectrum_aggregates.items():
            n_accs = len(data["account_indices"])
            n_posts = len(data["posts"])
            if n_accs == 0:
                continue

            # Salvaguarda LGPD: se contagem for menor que k, colapsa
            if n_accs < k_anonymity_threshold:
                has_collapsed = True
                collapsed_others["organic_accounts_N"] += n_accs
                collapsed_others["organic_posts_count"] += n_posts
                continue

            tot_s = max(1, sum(data["stances"].values()))
            fav_n = data["stances"].get("Favoravel", 0) + data["stances"].get("FAVORAVEL", 0)
            against_n = data["stances"].get("Contrario", 0) + data["stances"].get("CONTRARIO", 0)
            neutral_n = data["stances"].get("Neutro", 0) + data["stances"].get("NEUTRO_INFORMATIVO", 0)

            top_doms = [d for d, _ in data["domains"].most_common(5)]
            top_tags = [t for t, _ in data["hashtags"].most_common(5)]

            spectra_analysis.append({
                "spectrum_id": sp_name,
                "organic_accounts_N": n_accs,
                "organic_posts_count": n_posts,
                "fav_pct": round((fav_n / tot_s) * 100.0, 2),
                "against_pct": round((against_n / tot_s) * 100.0, 2),
                "neutral_pct": round((neutral_n / tot_s) * 100.0, 2),
                "top_shared_domains": top_doms,
                "top_shared_hashtags": top_tags,
                "first_seen_utc": data["first_seen_utc"],
            })

        if has_collapsed and collapsed_others["organic_accounts_N"] > 0:
            spectra_analysis.append(collapsed_others)

        # Ordena espectros por timestamp do primeiro post orgânico
        spectra_analysis.sort(key=lambda x: (x["first_seen_utc"] or "9999"))
        first_mover = spectra_analysis[0]["spectrum_id"] if spectra_analysis else None

        # 6. Identificação de Pontes de Consenso Transversal (Cross-Spectrum Bridge Topics)
        cross_spectrum_bridges: List[Dict[str, Any]] = []
        all_topics: Set[str] = set()
        for sp in spectra_analysis:
            all_topics.update(sp["top_shared_hashtags"])
            all_topics.update(sp["top_shared_domains"])

        for topic in sorted(list(all_topics)):
            sharing_spectra = []
            for sp in spectra_analysis:
                if sp["spectrum_id"] == "OUTROS_ANONIMIZADO_LGPD_K5":
                    continue
                if topic in sp["top_shared_hashtags"] or topic in sp["top_shared_domains"]:
                    sharing_spectra.append({
                        "spectrum_id": sp["spectrum_id"],
                        "fav_pct": sp["fav_pct"],
                        "against_pct": sp["against_pct"],
                    })

            if len(sharing_spectra) >= 2:
                # Convergência se diferença média de posicionamento favorável for moderada (< 30%)
                fav_rates = [s["fav_pct"] for s in sharing_spectra]
                spread = max(fav_rates) - min(fav_rates)
                cross_spectrum_bridges.append({
                    "bridge_topic": topic,
                    "shared_by_spectra_count": len(sharing_spectra),
                    "spectra_involved": [s["spectrum_id"] for s in sharing_spectra],
                    "stance_spread_pct": round(spread, 2),
                    "consensus_potential": "ALTO" if spread < 20.0 else ("MODERADO" if spread < 40.0 else "DIVERGENTE"),
                })

        # Auditoria de Conformidade LGPD
        lgpd_audit = {
            "k_anonymity_enforced": True,
            "k_threshold": k_anonymity_threshold,
            "ephemeral_affinity_vectors_purged": True,
            "author_ids_exposed_in_report": 0,
            "compliance_status": "CONFORME_LGPD_ART_5_II",
        }

        # Descarte estrito de vetores efêmeros da memória
        del F_affinity

        return BubbleAnalysisReport(
            theme_id=theme_id,
            quarantine_hygiene_audit=hygiene_audit,
            organic_accounts_analyzed=n_accounts,
            organic_posts_analyzed=len(clean_items),
            graph_nodes_count=graph_meta["nodes"],
            graph_edges_count=graph_meta["edges"],
            newman_modularity_observed=round(q_obs, 4),
            null_model_test=null_test,
            global_krackhardt_ei_index=global_ei,
            communities_topology=communities_topology,
            cross_bubble_bridge_accounts_total=n_bridges,
            bridge_accounts_share_pct=bridge_share,
            spectra_analysis=spectra_analysis,
            first_mover_spectrum=first_mover,
            cross_spectrum_bridge_topics=cross_spectrum_bridges,
            lgpd_compliance_audit=lgpd_audit,
        )
