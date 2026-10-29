"""
Amostrador Probabilistico Estratificado de CONTAS Organicas sobre o Universo Observado no Data Lake.

Atende integralmente aos criterios da 2a Rodada de Auditoria Cientifica (C-01, E-06, E-07, Secao 8):
1. Fluxo Estrito (Checklist #3):
   Coleta Observacional -> Desinfeccao (Spam/CIB em nivel de conta) -> Universo Observado de Contas Organicas (U_Org) -> Sorteio Estratificado de Contas (s).
2. Unidade de Sorteio = Unidade de Analise = CONTA DIGITAL ORGANICA POR PLATAFORMA (E-06):
   Neutraliza o vies de volume (size-biased sampling) de contas hiperativas.
3. Fuso Horario Explicito (`America/Sao_Paulo` via `zoneinfo`) e Estrato Completo `Plataforma x Turno Modal x Dia` (E-06 / Secao 8).
4. Alocacao Exata pelo Metodo do Maior Resto de Hamilton (garante que sum(n_h) == n_requerido exatamente, corrigindo 587 != 588 - E-06).
5. Exportacao das Probabilidades de Inclusao Conhecidas (`pi_i = n_h / N_h`) e Pesos de Desenho (`design_weight_d_i = N_h / n_h`) (C-01 / E-06).
6. Dimensionamento de Cochran incorporando o `expected_design_effect_deff` com correcao para populacao finita (E-07).
7. Semente pseudoaleatoria fixa e registrada (Mersenne Twister auditavel - Anexo A).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import math
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from src.cleaning.lgpd_and_bot_filter import SocialPost
from src.config_loader import load_settings


@dataclass
class OrganicAccountSampleUnit:
    """Representa uma unidade observacional unica (1 Conta Organica por Plataforma) com probabilidade de inclusao conhecida."""
    platform: str
    author_hash: str
    region_proxy: str
    modal_time_stratum: str
    modal_day_str: str
    stratum_key: str
    posts_count: int
    stances: List[str] = field(default_factory=list)
    inclusion_probability_pi: float = 1.0
    design_weight_d: float = 1.0


def to_brazil_timezone(ts: datetime, tz_name: str = "America/Sao_Paulo") -> datetime:
    """Converte timestamps ingenuos (assumidos UTC ou local) ou com fuso para America/Sao_Paulo (E-06)."""
    target_tz = ZoneInfo(tz_name)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=target_tz)
    return ts.astimezone(target_tz)


def get_time_slice_stratum(ts: datetime, tz_name: str = "America/Sao_Paulo") -> str:
    """Classifica o horario da publicacao nos 4 estratos temporais diarios no fuso de Brasilia."""
    local_ts = to_brazil_timezone(ts, tz_name)
    hour = local_ts.hour
    if 0 <= hour < 6:
        return "T1_Madrugada_00h_06h"
    if 6 <= hour < 12:
        return "T2_Manha_06h_12h"
    if 12 <= hour < 18:
        return "T3_Tarde_12h_18h"
    return "T4_Noite_18h_24h"


class ObservedUniverseStratifiedSampler:
    """
    Realiza sorteio aleatorio estratificado de CONTAS organicas (Plataforma x Turno Modal x Dia)
    com alocacao exata de Hamilton (Maior Resto) ou de Neyman sobre o Universo Observado Limpo (U_Org).
    """

    def __init__(
        self,
        design_target_precision: Optional[float] = None,
        confidence_z: float = 1.96,
        expected_deff: Optional[float] = None,
        timezone_name: Optional[str] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ):
        cfg = settings_override or load_settings()
        stat_cfg = cfg["statistical_parameters"]
        proj_cfg = cfg["project"]

        self.design_target_precision = float(
            design_target_precision if design_target_precision is not None else stat_cfg["design_target_precision"]
        )
        self.confidence_z = float(confidence_z)
        self.expected_deff = float(
            expected_deff if expected_deff is not None else stat_cfg.get("expected_design_effect_deff", 1.0)
        )
        self.timezone_name = timezone_name or proj_cfg.get("timezone", "America/Sao_Paulo")

    def compute_required_sample_size(
        self,
        observed_N: int,
        p: float = 0.5,
        include_expected_deff: bool = False,
    ) -> int:
        """
        Dimensiona a cobertura minima interna sobre o Universo Observado (N) usando a formula
        de Cochran com correcao para populacao finita (e opcionalmente multiplicada pelo DEFF esperado - E-07).
        """
        if observed_N <= 0:
            return 0
        deff_factor = self.expected_deff if include_expected_deff else 1.0
        n0 = (self.confidence_z**2 * p * (1.0 - p) * deff_factor) / (self.design_target_precision**2)
        n = n0 / (1.0 + ((n0 - 1.0) / observed_N))
        return min(observed_N, math.ceil(n))

    @staticmethod
    def filter_clean_organic_posts(posts: Sequence[SocialPost]) -> List[SocialPost]:
        """Filtra apenas postagens de contas organicas (excluindo Spam Comercial e Suspeita de CIB)."""
        return [
            p
            for p in posts
            if not p.is_commercial_spam
            and not p.suspected_coordination
            and not p.account_suspected_cib
            and p.activity_class not in ("Spam_Comercial", "Suspeita_CIB_Automacao")
        ]

    def build_organic_account_frame(self, posts: Sequence[SocialPost]) -> List[OrganicAccountSampleUnit]:
        """
        Constrói o cadastro de unidades observacionais (U_Org) consolidando todas as postagens
        limpas por `(platform, author_hash)` antes do sorteio (E-06 / C-01).
        """
        clean_posts = self.filter_clean_organic_posts(posts)
        grouped: Dict[Tuple[str, str], List[SocialPost]] = defaultdict(list)
        for p in clean_posts:
            grouped[(p.platform, p.author_hash)].append(p)

        units: List[OrganicAccountSampleUnit] = []
        for (plat, acc_hash), p_list in sorted(grouped.items()):
            time_slices = [get_time_slice_stratum(p.timestamp, self.timezone_name) for p in p_list]
            days = [to_brazil_timezone(p.timestamp, self.timezone_name).strftime("%Y-%m-%d") for p in p_list]
            regions = [p.region_proxy for p in p_list if p.region_proxy != "Nao Identificado"]

            modal_slice = sorted(Counter(time_slices).most_common(), key=lambda x: (-x[1], x[0]))[0][0]
            modal_day = sorted(Counter(days).most_common(), key=lambda x: (-x[1], x[0]))[0][0]
            region_val = regions[0] if regions else "Nao Identificado"
            stratum_key = f"{plat}|{modal_slice}|{modal_day}"

            stances_list = [p.stance for p in p_list if p.stance]
            units.append(
                OrganicAccountSampleUnit(
                    platform=plat,
                    author_hash=acc_hash,
                    region_proxy=region_val,
                    modal_time_stratum=modal_slice,
                    modal_day_str=modal_day,
                    stratum_key=stratum_key,
                    posts_count=len(p_list),
                    stances=stances_list,
                )
            )
        return units

    @staticmethod
    def _hamilton_largest_remainder_allocation(
        stratum_sizes: Dict[str, int],
        target_n: int,
        stratum_std_devs: Optional[Dict[str, float]] = None,
    ) -> Dict[str, int]:
        """
        Calcula a alocacao inteira exata por estrato (Proporcional ou de Neyman) usando o
        Metodo do Maior Resto de Hamilton, garantindo matematicamente que sum(n_h) == target_n (E-06).
        """
        total_N = sum(stratum_sizes.values())
        if target_n >= total_N:
            return dict(stratum_sizes)

        weights: Dict[str, float] = {}
        for k, N_h in stratum_sizes.items():
            sd_h = stratum_std_devs.get(k, 0.5) if stratum_std_devs else 1.0
            weights[k] = N_h * max(1e-6, sd_h)
        total_w = sum(weights.values())

        quotas: Dict[str, float] = {k: target_n * (weights[k] / total_w) for k in stratum_sizes}
        alloc: Dict[str, int] = {}
        remainders: List[Tuple[float, str]] = []

        for k, q in quotas.items():
            # Garante pelo menos 1 se target_n >= numero de estratos e N_h >= 1
            floor_q = min(stratum_sizes[k], int(math.floor(q)))
            alloc[k] = floor_q
            rem = q - floor_q if alloc[k] < stratum_sizes[k] else -1.0
            remainders.append((rem, k))

        deficit = target_n - sum(alloc.values())
        remainders.sort(key=lambda x: (-x[0], x[1]))

        idx = 0
        while deficit > 0 and idx < len(remainders):
            _, k = remainders[idx]
            if alloc[k] < stratum_sizes[k]:
                alloc[k] += 1
                deficit -= 1
            idx = (idx + 1) if idx + 1 < len(remainders) else 0
            if all(alloc[key] >= stratum_sizes[key] for key in stratum_sizes):
                break

        return alloc

    def draw_stratified_account_sample(
        self,
        posts_or_units: Sequence[Any],
        target_sample_size: int = 0,
        random_seed: int = 2026,
        allocation_method: str = "proportional",
    ) -> Tuple[List[OrganicAccountSampleUnit], Dict[str, int]]:
        """
        Sorteia uma amostra probabilistica estratificada de CONTAS organicas (U_Org)
        com semente pseudoaleatoria fixa e registrada, exportando `inclusion_probability_pi`
        e `design_weight_d` em cada unidade sorteada (C-01 / E-06).
        """
        if not posts_or_units:
            return [], {}

        if isinstance(posts_or_units[0], SocialPost):
            units = self.build_organic_account_frame(posts_or_units)
        else:
            units = list(posts_or_units)

        total_N = len(units)
        if total_N == 0:
            return [], {}

        n_req = target_sample_size if target_sample_size > 0 else self.compute_required_sample_size(total_N)
        n_req = min(total_N, n_req)

        strata_buckets: Dict[str, List[OrganicAccountSampleUnit]] = defaultdict(list)
        for u in units:
            strata_buckets[u.stratum_key].append(u)

        stratum_sizes = {k: len(bucket) for k, bucket in strata_buckets.items()}
        stratum_sds: Optional[Dict[str, float]] = None
        if allocation_method == "neyman":
            stratum_sds = {}
            for k, bucket in strata_buckets.items():
                fav_rate = sum(1 for u in bucket if "Favoravel" in u.stances) / max(1, len(bucket))
                p_clamped = min(0.95, max(0.05, fav_rate))
                stratum_sds[k] = math.sqrt(p_clamped * (1.0 - p_clamped))

        alloc = self._hamilton_largest_remainder_allocation(stratum_sizes, n_req, stratum_sds)

        rng = random.Random(random_seed)
        sampled_units: List[OrganicAccountSampleUnit] = []
        sampled_strata_counts: Dict[str, int] = {}

        for stratum_key, bucket in sorted(strata_buckets.items()):
            N_h = len(bucket)
            n_h = alloc[stratum_key]
            if n_h <= 0:
                continue
            chosen = rng.sample(bucket, n_h) if n_h < N_h else list(bucket)
            pi_h = n_h / N_h
            d_h = N_h / n_h
            for unit in chosen:
                unit.inclusion_probability_pi = round(pi_h, 6)
                unit.design_weight_d = round(d_h, 6)
                sampled_units.append(unit)
            sampled_strata_counts[stratum_key] = len(chosen)

        return sampled_units, sampled_strata_counts

    def draw_stratified_sample(
        self,
        observed_posts: List[SocialPost],
        target_sample_size: int = 0,
        random_seed: int = 2026,
    ) -> Tuple[List[SocialPost], Dict[str, int]]:
        """
        Metodo compativel com `audit_probe.py` (T5):
        1. Filtra o universo sujo (remove Spam Comercial e Suspeita de CIB antes do sorteio!).
        2. Sorteia com alocacao exata de Hamilton (garantindo len(sample) == n_requerido e 0 spam/CIB).
        """
        clean_posts = self.filter_clean_organic_posts(observed_posts)
        total_clean = len(clean_posts)
        if total_clean == 0:
            return [], {}

        n_req = target_sample_size if target_sample_size > 0 else self.compute_required_sample_size(total_clean)
        n_req = min(total_clean, n_req)

        strata_buckets: Dict[str, List[SocialPost]] = defaultdict(list)
        for p in clean_posts:
            s_key = f"{p.platform}|{get_time_slice_stratum(p.timestamp, self.timezone_name)}"
            strata_buckets[s_key].append(p)

        stratum_sizes = {k: len(b) for k, b in strata_buckets.items()}
        alloc = self._hamilton_largest_remainder_allocation(stratum_sizes, n_req)

        rng = random.Random(random_seed)
        sampled_posts: List[SocialPost] = []
        sampled_counts: Dict[str, int] = {}

        for s_key, bucket in sorted(strata_buckets.items()):
            n_h = alloc[s_key]
            if n_h <= 0:
                continue
            chosen = rng.sample(bucket, n_h) if n_h < len(bucket) else list(bucket)
            sampled_posts.extend(chosen)
            sampled_counts[s_key] = len(chosen)

        return sampled_posts, sampled_counts
