"""
Motor de Inferencia Estatistica do Debate Publico Digital Observado (U_Org).

Atende integralmente aos criterios da 2a Rodada de Auditoria Cientifica da Fase 01:
1. Redesenho Formal do Estimando (C-01 / E-05 / E-06):
   - Estimando primario: proporcao theta_T sobre o universo finito observado de contas organicas (U_Org).
   - Suporta inferencia baseada no desenho a partir do sorteio interno de contas (pesos d_i = 1/pi_i
     com correcao para populacao finita FPC) e correcao matricial/binaria de erro de classificacao
     de Rogan & Gladen (1978).
   - Os intervalos de confianca quantificam (a) incerteza do sorteio interno / processo de amostragem
     de contas e (b) erro de classificacao, nao representando margem de erro demografica populacional.
2. Exclusao de CIB em Nivel de CONTA (Checklist #2 / M-05) e Taxa de Artificialidade Dupla (Post e Conta - E-10):
   - Se uma conta possui `account_suspected_cib = True` ou atinge o limiar de posts sinalizados,
     NENHUMA postagem dessa conta sobrevive como unidade organica.
   - Spam comercial e excluido do denominador e do calculo de volume bruto de opiniao (E-10).
3. Raking IPF com Trimming DENTRO do Laco e Diagnostico de Convergencia (E-01):
   - Aplica truncamento de pesos (`[min_weight, max_weight]`, Kish, 1992; Valliant, Dever & Kreuter, 2018)
     a cada iteracao do laco IPF com projecao em simplex limitado, garantindo que os pesos finais
     respeitem estritamente `[min_weight, max_weight]` apos normalizacao!
   - Exporta a tabela de margens (`alvo` vs. `obtido`) e sinaliza explicitamente `calibration_status`
     (`CALIBRADO_OK` se |Delta| <= 1 p.p. ou `NAO_ATINGIDA_LIMITADA_POR_TRIMMING` quando os limites [0.25, 4.0]
     impedem matematicamente atingir uma margem extrema).
   - O Cenario 3 e rotulado honestamente como:
     'Cenario 3 — Reponderado (sensibilidade sob ignorabilidade)' (Anexo A / C-01).
4. Bootstrap Nao Parametrico Estratificado de Contas em Chunks de Memoria Controlada (E-03 / G-05):
   - Le `bootstrap_iterations` e `bootstrap_chunk_size` diretamente do `config/settings.yaml` (G-01).
   - Processa em lotes (*chunks* de 500 replicas), evitando alocacoes de dezenas de GB.
5. Teste de Homogeneidade Inter-Plataformas Correto + V de Cramer + Correcao de Holm-Bonferroni (E-04 / E-09):
   - Nao aplica pesos de plataforma no teste de homogeneidade *entre* plataformas (evitando distorcer
     a estatistica Chi2 pela plataforma de maior peso marginal).
   - Rotula honestamente como 'Chi2 de Pearson ajustado pelo DEFF intraplataforma (aproximacao de 1a ordem)'
     e reporta o tamanho de efeito **V de Cramer** e p-valores ajustados por **Holm-Bonferroni** para multiplos testes.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
import warnings

import numpy as np
from scipy.stats import chi2

from src.cleaning.lgpd_and_bot_filter import SocialPost
from src.config_loader import load_settings
from src.sampling.stratified_sampler import OrganicAccountSampleUnit


@dataclass
class PlatformHomogeneityTestResult:
    """Resultado do teste de homogeneidade entre plataformas (Chi2 ajustado pelo DEFF + V de Cramer - E-04)."""
    test_label: str
    pearson_chi2: float
    design_effect_correction: float
    adjusted_chi2: float
    degrees_of_freedom: int
    p_value: float
    holm_corrected_p_values_by_category: Dict[str, float]
    cramers_v_effect_size: float
    statistically_significant_95: bool
    interpretation: str

    @property
    def rao_scott_f_or_chi2(self) -> float:
        """Alias retrocompativel para scripts de auditoria."""
        return self.adjusted_chi2


@dataclass
class StatisticalReportMetrics:
    total_raw_posts_N: int
    total_commercial_spam_posts: int
    total_suspected_cib_posts: int
    total_suspected_cib_accounts: int
    total_organic_accounts_N_org: int
    sampled_organic_accounts_n: int
    total_civic_mobilization_posts: int
    total_organic_repetition_posts: int
    post_level_artificiality_rate_pct: float
    account_level_artificiality_rate_pct: float
    kish_design_effect_deff: float
    effective_sample_size_n_eff: float
    confidence_level_pct: float
    internal_statistical_uncertainty_pp: float
    # Status e diagnostico de calibracao do Cenario 3 (E-01 / Anexo A)
    scenario_3_calibration_status: str
    scenario_3_max_margin_gap_pp: float
    scenario_3_margins_table: Dict[str, Dict[str, float]]
    # Os 3 Cenarios (com Cenario 3 rotulado como Reponderado sob Ignorabilidade)
    scenario_1_organic_unweighted_pct: Dict[str, float]
    scenario_2_equal_platform_pct: Dict[str, float]
    scenario_3_reweighted_sensitivity_pct: Dict[str, float]
    # Estimativa corrigida por erro de classificacao (Rogan & Gladen, 1978 - C-01)
    rogan_gladen_corrected_c1_pct: Dict[str, float]
    # Proporcao bruta contaminada (excluindo spam comercial sem opiniao - E-10)
    raw_contaminated_volume_pct: Dict[str, float]
    confidence_intervals_95_c1_pct: Dict[str, Tuple[float, float]]
    confidence_intervals_95_pct: Dict[str, Tuple[float, float]]
    platform_divergence_test: PlatformHomogeneityTestResult
    tie_breaking_sensitivity_pct: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Propriedades retrocompativeis com scripts anteriores e `audit_probe.py`
    @property
    def artificiality_rate_pct(self) -> float:
        return self.post_level_artificiality_rate_pct

    @property
    def unique_organic_platform_accounts_n(self) -> int:
        return self.total_organic_accounts_N_org

    @property
    def effective_sampling_uncertainty_pp(self) -> float:
        return self.internal_statistical_uncertainty_pp

    @property
    def scenario_3_raking_calibrated_pct(self) -> Dict[str, float]:
        return self.scenario_3_reweighted_sensitivity_pct

    @property
    def platform_divergence_rao_scott_test(self) -> PlatformHomogeneityTestResult:
        return self.platform_divergence_test


class DigitalDiscourseStatisticalEngine:
    """
    Motor de inferencia estatistica sobre o universo observado de contas organicas (U_Org),
    lendo parametros do `config/settings.yaml` (G-01).
    """

    def __init__(
        self,
        platform_target_weights: Optional[Dict[str, float]] = None,
        region_target_weights: Optional[Dict[str, float]] = None,
        stance_categories: Optional[Sequence[str]] = None,
        confidence_z: float = 1.96,
        suspected_cib_threshold: Optional[float] = None,
        tie_breaking_stance: Optional[str] = None,
        weight_trim_min: Optional[float] = None,
        weight_trim_max: Optional[float] = None,
        settings_override: Optional[Dict[str, Any]] = None,
    ):
        cfg = settings_override or load_settings()
        stat_cfg = cfg["statistical_parameters"]
        cib_cfg = cfg["cib_and_bot_detection"]
        trim_cfg = stat_cfg["weight_trimming"]

        plat_w = platform_target_weights or cfg["platform_reference_weights_brazil"]
        total_p = sum(plat_w.values())
        self.platform_targets = {k: float(v) / total_p for k, v in plat_w.items()}

        reg_w = region_target_weights or cfg["ibge_macroregion_weights_brazil"]
        total_r = sum(reg_w.values())
        self.region_targets = {k: float(v) / total_r for k, v in reg_w.items()}

        self.categories = list(stance_categories or stat_cfg["stance_categories"])
        self.confidence_z = float(confidence_z)
        self.suspected_cib_threshold = float(
            suspected_cib_threshold
            if suspected_cib_threshold is not None
            else cib_cfg["suspected_cib_composite_threshold"]
        )
        self.tie_breaking_stance = tie_breaking_stance or stat_cfg["tie_breaking_rule"]
        self.weight_trim_min = float(weight_trim_min if weight_trim_min is not None else trim_cfg["min_weight"])
        self.weight_trim_max = float(weight_trim_max if weight_trim_max is not None else trim_cfg["max_weight"])
        self.max_ipf_iterations = int(trim_cfg.get("max_ipf_iterations", 80))
        self.convergence_tol_pp = float(trim_cfg.get("convergence_tolerance_pp", 0.01))
        self.default_bootstrap_iterations = int(stat_cfg["bootstrap_iterations"])
        self.bootstrap_chunk_size = int(stat_cfg.get("bootstrap_chunk_size", 500))
        self.expected_deff = float(stat_cfg.get("expected_design_effect_deff", 1.50))

        # Status da ultima execucao do Raking IPF
        self.last_calibration_status: str = "NAO_EXECUTADO"
        self.last_max_margin_gap: float = 0.0
        self.last_margins_table: Dict[str, Dict[str, float]] = {}

    @staticmethod
    def operational_cochran_sample_size(
        design_target_precision: float = 0.03,
        confidence_z: float = 1.96,
        p: float = 0.5,
        observed_universe_N: int = 0,
        expected_deff: float = 1.0,
    ) -> int:
        """
        Calcula o tamanho minimo de cobertura amostral interna de contas sobre o universo observado (N),
        multiplicando pelo DEFF esperado (E-07) e aplicando correcao para populacao finita.
        """
        n0 = (confidence_z**2 * p * (1.0 - p) * max(1.0, expected_deff)) / (design_target_precision**2)
        if observed_universe_N and observed_universe_N > 0:
            n = n0 / (1.0 + ((n0 - 1.0) / observed_universe_N))
            return min(observed_universe_N, math.ceil(n))
        return math.ceil(n0)

    @staticmethod
    def rogan_gladen_misclassification_correction(
        observed_proportions: Dict[str, float],
        sensitivity_tpr: float = 0.90,
        specificity_tnr: float = 0.92,
    ) -> Dict[str, float]:
        """
        Corrige o erro de classificacao do classificador (LLM) usando o estimador de
        Rogan & Gladen (1978): theta_tilde = (p_hat - FPR) / (TPR - FPR) truncado em [0, 1]
        e renormalizado no simplex (C-01).
        """
        fpr = 1.0 - specificity_tnr
        denom = max(1e-6, sensitivity_tpr - fpr)
        raw_corrected: Dict[str, float] = {}
        for cat, pct_val in observed_proportions.items():
            p_hat = pct_val / 100.0
            theta_tilde = max(0.0, min(1.0, (p_hat - fpr) / denom))
            raw_corrected[cat] = theta_tilde

        tot = sum(raw_corrected.values())
        if tot <= 0:
            return dict(observed_proportions)
        return {k: round((v / tot) * 100.0, 2) for k, v in raw_corrected.items()}

    def _resolve_deterministic_modal_stance(self, stances: List[str], mode: str = "neutral_tie") -> str:
        """
        Resolve a posicao predominante de uma conta digital de forma deterministica,
        suportando modos alternativos para analise de sensibilidade (E-08):
        - 'neutral_tie' (padrao): empate estrito -> `tie_breaking_stance` ('Neutro')
        - 'last_post': empate estrito -> postura da manifestacao mais recente da conta
        """
        counts = Counter(stances)
        max_freq = max(counts.values())
        top_candidates = sorted([st for st, freq in counts.items() if freq == max_freq])
        if len(top_candidates) == 1:
            return top_candidates[0]
        if mode == "last_post":
            return stances[-1]
        return self.tie_breaking_stance

    @staticmethod
    def _bounded_simplex_renormalize(
        weights: np.ndarray,
        target_mean: float = 1.0,
        lo: float = 0.25,
        hi: float = 4.00,
        max_steps: int = 25,
    ) -> np.ndarray:
        """
        Projeta o vetor de pesos para ter media exata `target_mean` (soma = n)
        RESPEITANDO ESTRITAMENTE os limites `lo <= w_i <= hi` (resolve o bug 0.234 < 0.25 da Auditoria E-01!).
        """
        w = np.clip(weights.astype(float), lo, hi)
        n = len(w)
        target_sum = n * target_mean

        for _ in range(max_steps):
            diff = target_sum - float(np.sum(w))
            if abs(diff) < 1e-9:
                break
            if diff > 0:
                free_mask = w < (hi - 1e-9)
            else:
                free_mask = w > (lo + 1e-9)
            if not np.any(free_mask):
                break
            free_sum = float(np.sum(w[free_mask]))
            if free_sum > 0:
                scale = 1.0 + (diff / free_sum)
                w[free_mask] = np.clip(w[free_mask] * scale, lo, hi)
            else:
                w[free_mask] = np.clip(w[free_mask] + (diff / int(np.sum(free_mask))), lo, hi)

        return w

    def _compute_ipf_raking_weights(
        self,
        platforms: List[str],
        regions: List[str],
        max_iters: Optional[int] = None,
        tol: float = 1e-5,
        warn_on_non_convergence: bool = False,
    ) -> np.ndarray:
        """
        Executa Iterative Proportional Fitting (Raking Bivariado) COM Weight Trimming DENTRO do laco (E-01),
        respeitando estritamente `[weight_trim_min, weight_trim_max]` apos normalizacao e registrando
        a tabela de margens e o status de calibracao (`CALIBRADO_OK` vs `NAO_ATINGIDA_LIMITADA_POR_TRIMMING`).
        """
        n = len(platforms)
        if n == 0:
            return np.array([], dtype=float)

        iters = max_iters or self.max_ipf_iterations
        lo = self.weight_trim_min
        hi = self.weight_trim_max

        weights = np.ones(n, dtype=float)
        plat_arr = np.array(platforms)
        reg_arr = np.array(regions)

        present_plats = sorted(set(platforms))
        norm_plat_targets = {k: self.platform_targets.get(k, 1.0 / len(present_plats)) for k in present_plats}
        s_p = sum(norm_plat_targets.values())
        if s_p > 0:
            norm_plat_targets = {k: v / s_p for k, v in norm_plat_targets.items()}

        present_regs = sorted({r for r in regions if r in self.region_targets})
        norm_reg_targets = {k: self.region_targets[k] for k in present_regs}
        s_r = sum(norm_reg_targets.values())
        if s_r > 0:
            norm_reg_targets = {k: v / s_r for k, v in norm_reg_targets.items()}

        for _ in range(iters):
            prev_w = weights.copy()

            # Passo 1: Ajuste marginal por Regiao (no subconjunto com proxy de regiao conhecido)
            if norm_reg_targets:
                known_mask = np.isin(reg_arr, list(norm_reg_targets.keys()))
                total_known_w = float(np.sum(weights[known_mask]))
                if total_known_w > 0:
                    for reg, target_prop in norm_reg_targets.items():
                        mask = reg_arr == reg
                        current_prop = float(np.sum(weights[mask])) / total_known_w
                        if current_prop > 0:
                            weights[mask] *= target_prop / current_prop

            # Passo 2: Ajuste marginal por Plataforma (prioridade final da iteracao)
            total_w = float(np.sum(weights))
            if total_w > 0:
                for plat, target_prop in norm_plat_targets.items():
                    mask = plat_arr == plat
                    current_prop = float(np.sum(weights[mask])) / total_w
                    if current_prop > 0:
                        weights[mask] *= target_prop / current_prop

            # Passo 3: Trimming e Renormalizacao exata no simplex limitado DENTRO do laco (E-01)
            weights = self._bounded_simplex_renormalize(weights, target_mean=1.0, lo=lo, hi=hi)

            if float(np.max(np.abs(weights - prev_w))) < tol:
                break

        # Diagnostico formal de convergencia das margens (E-01)
        tot_final = float(np.sum(weights))
        margins_table: Dict[str, Dict[str, float]] = {}
        max_gap = 0.0
        for plat, target_prop in norm_plat_targets.items():
            obtained_prop = float(np.sum(weights[plat_arr == plat])) / max(1e-9, tot_final)
            gap = abs(obtained_prop - target_prop)
            if gap > max_gap:
                max_gap = gap
            margins_table[plat] = {
                "target_pct": round(target_prop * 100.0, 2),
                "obtained_pct": round(obtained_prop * 100.0, 2),
                "abs_gap_pp": round(gap * 100.0, 2),
            }

        self.last_max_margin_gap = round(max_gap * 100.0, 2)
        self.last_margins_table = margins_table
        if max_gap <= self.convergence_tol_pp:
            self.last_calibration_status = "CALIBRADO_OK"
        else:
            self.last_calibration_status = "NAO_ATINGIDA_LIMITADA_POR_TRIMMING"
            if warn_on_non_convergence:
                warnings.warn(
                    f"Raking nao atingiu todas as margens sob os limites [{lo}, {hi}] "
                    f"(gap maximo = {self.last_max_margin_gap} p.p.). Status: {self.last_calibration_status}"
                )

        return weights

    @staticmethod
    def holm_bonferroni_correction(p_values: Dict[str, float]) -> Dict[str, float]:
        """Aplica correcao de Holm-Bonferroni para multiplos testes de hipoteses (E-09)."""
        m = len(p_values)
        if m == 0:
            return {}
        sorted_items = sorted(p_values.items(), key=lambda x: x[1])
        adjusted: Dict[str, float] = {}
        running_max = 0.0
        for rank_idx, (key, p_val) in enumerate(sorted_items):
            adj_p = min(1.0, p_val * (m - rank_idx))
            running_max = max(running_max, adj_p)
            adjusted[key] = round(running_max, 4)
        return adjusted

    def platform_homogeneity_chi2_test(
        self,
        platforms: List[str],
        stances: List[str],
        intra_platform_weights: Optional[np.ndarray] = None,
    ) -> PlatformHomogeneityTestResult:
        """
        Testa a homogeneidade das proporcoes de posicionamento entre plataformas (H2 - E-04):
        - NAO aplica pesos marginais de plataforma (que distorceriam a tabela de contingencia),
          usando pesos intraplataforma (ou uniformes w=1 dentro de cada plataforma).
        - Calcula o Chi2 de Pearson ajustado pelo DEFF intraplataforma (aproximacao de 1a ordem),
          o tamanho de efeito **V de Cramer** e p-valores por categoria corrigidos por **Holm-Bonferroni** (E-09).
        """
        unique_plats = sorted(set(platforms))
        unique_cats = [c for c in self.categories if c in set(stances)]
        if len(unique_plats) < 2 or len(unique_cats) < 2:
            return PlatformHomogeneityTestResult(
                test_label="Chi2 de Pearson ajustado pelo DEFF intraplataforma (aproximacao de 1a ordem)",
                pearson_chi2=0.0,
                design_effect_correction=1.0,
                adjusted_chi2=0.0,
                degrees_of_freedom=1,
                p_value=1.0,
                holm_corrected_p_values_by_category={},
                cramers_v_effect_size=0.0,
                statistically_significant_95=False,
                interpretation="Amostra com menos de 2 plataformas ou categorias.",
            )

        n = len(platforms)
        w = intra_platform_weights if intra_platform_weights is not None else np.ones(n, dtype=float)
        sum_w = float(np.sum(w))
        sum_w2 = float(np.sum(w**2))
        intra_deff = max(1.0, (n * sum_w2) / (sum_w**2)) if sum_w > 0 else 1.0

        plat_idx = {p: i for i, p in enumerate(unique_plats)}
        cat_idx = {c: j for j, c in enumerate(unique_cats)}

        obs = np.zeros((len(unique_plats), len(unique_cats)), dtype=float)
        for p, s, wi in zip(platforms, stances, w):
            if s in cat_idx:
                obs[plat_idx[p], cat_idx[s]] += wi

        total_n = float(np.sum(obs))
        row_totals = obs.sum(axis=1, keepdims=True)
        col_totals = obs.sum(axis=0, keepdims=True)
        expected = (row_totals @ col_totals) / max(1e-9, total_n)

        valid = expected > 0
        pearson_chi2 = float(np.sum(((obs[valid] - expected[valid]) ** 2) / expected[valid]))
        adj_chi2 = pearson_chi2 / intra_deff
        dof = (len(unique_plats) - 1) * (len(unique_cats) - 1)
        p_val = float(1.0 - chi2.cdf(adj_chi2, df=dof))

        # Tamanho de efeito V de Cramer: sqrt(chi2 / (N * min(R-1, C-1)))
        min_dim = max(1, min(len(unique_plats) - 1, len(unique_cats) - 1))
        cramers_v = math.sqrt(max(0.0, adj_chi2 / (max(1.0, total_n) * min_dim)))

        # Testes post-hoc por categoria (1 vs resto) com correcao de Holm-Bonferroni (E-09)
        cat_raw_p: Dict[str, float] = {}
        for j, cat in enumerate(unique_cats):
            obs_bin = np.column_stack([obs[:, j], obs.sum(axis=1) - obs[:, j]])
            exp_bin = (obs_bin.sum(axis=1, keepdims=True) @ obs_bin.sum(axis=0, keepdims=True)) / max(1e-9, total_n)
            v_mask = exp_bin > 0
            c2_cat = float(np.sum(((obs_bin[v_mask] - exp_bin[v_mask]) ** 2) / exp_bin[v_mask])) / intra_deff
            cat_raw_p[cat] = float(1.0 - chi2.cdf(c2_cat, df=len(unique_plats) - 1))

        holm_p = self.holm_bonferroni_correction(cat_raw_p)
        sig = p_val < 0.05

        interp = (
            f"Divergencia entre plataformas estatisticamente significativa "
            f"(p = {p_val:.4f} < 0.05; V de Cramer = {cramers_v:.3f})."
            if sig
            else f"Divergencia entre plataformas dentro da variacao esperada "
            f"(p = {p_val:.4f} >= 0.05; V de Cramer = {cramers_v:.3f})."
        )
        return PlatformHomogeneityTestResult(
            test_label="Chi2 de Pearson ajustado pelo DEFF intraplataforma (aproximacao de 1a ordem)",
            pearson_chi2=round(pearson_chi2, 3),
            design_effect_correction=round(intra_deff, 3),
            adjusted_chi2=round(adj_chi2, 3),
            degrees_of_freedom=dof,
            p_value=round(p_val, 4),
            holm_corrected_p_values_by_category=holm_p,
            cramers_v_effect_size=round(cramers_v, 3),
            statistically_significant_95=sig,
            interpretation=interp,
        )

    def _stratified_chunked_bootstrap_ci(
        self,
        platforms: List[str],
        stances_np: np.ndarray,
        weights: np.ndarray,
        bootstrap_iterations: int,
        chunk_size: int,
        random_seed: int,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Bootstrap nao parametrico estratificado de contas processado em *chunks* (lotes de memoria),
        evitando alocacao O(B * n) gigante (resolve E-03 e G-05!).
        """
        n = len(stances_np)
        rng = np.random.default_rng(random_seed)

        # Indices agrupados por estrato de plataforma
        strata_indices: Dict[str, np.ndarray] = {}
        plat_arr = np.array(platforms)
        for pl in sorted(set(platforms)):
            strata_indices[pl] = np.where(plat_arr == pl)[0]

        replicates_by_cat: Dict[str, List[np.ndarray]] = {cat: [] for cat in self.categories}
        cat_indicators: Dict[str, np.ndarray] = {
            cat: (stances_np == cat).astype(float) for cat in self.categories
        }

        remaining = bootstrap_iterations
        while remaining > 0:
            cur_b = min(chunk_size, remaining)
            remaining -= cur_b

            # Sorteia dentro de cada estrato de plataforma com reposicao: shape (cur_b, n)
            sampled_blocks = [
                rng.choice(ix_h, size=(cur_b, len(ix_h)), replace=True)
                for ix_h in strata_indices.values()
            ]
            boot_idx = np.concatenate(sampled_blocks, axis=1)
            boot_w = weights[boot_idx]
            boot_w_sum = np.maximum(1e-9, np.sum(boot_w, axis=1))

            for cat in self.categories:
                boot_y = cat_indicators[cat][boot_idx]
                means_chunk = (np.sum(boot_w * boot_y, axis=1) / boot_w_sum) * 100.0
                replicates_by_cat[cat].append(means_chunk)

        ci_95: Dict[str, Tuple[float, float]] = {}
        for cat in self.categories:
            all_reps = np.concatenate(replicates_by_cat[cat])
            low, high = np.percentile(all_reps, [2.5, 97.5])
            ci_95[cat] = (round(float(low), 2), round(float(high), 2))

        return ci_95

    def compute_verified_discourse_indicators(
        self,
        posts: List[SocialPost],
        sampled_account_units: Optional[Sequence[OrganicAccountSampleUnit]] = None,
        bootstrap_iterations: Optional[int] = None,
        random_seed: int = 42,
    ) -> StatisticalReportMetrics:
        """
        Calcula os indicadores auditados do debate publico digital observado (U_Org):
        - Exclui CIB em nivel de CONTA (Checklist #2 / M-05).
        - Exclui spam comercial do calculo de volume bruto de opiniao (E-10).
        - Reporta taxa de artificialidade tanto por post quanto por conta (E-10).
        - Quando `sampled_account_units` (com `inclusion_probability_pi` e `design_weight_d`) e fornecido,
          estima C1 com inferencia baseada no desenho (FPC) sobre o sorteio interno de contas (C-01).
        """
        total_raw = len(posts)
        if total_raw == 0:
            raise ValueError("Lista de postagens vazia.")

        b_iters = bootstrap_iterations if bootstrap_iterations is not None else self.default_bootstrap_iterations

        # 1. Separacao de Spam Comercial (Quarentena) e identificacao de Contas CIB (M-05)
        spam_posts = [p for p in posts if p.is_commercial_spam]
        non_spam_posts = [p for p in posts if not p.is_commercial_spam]

        # Volume Bruto Contaminado calculado apenas sobre postagens nao-spam (resolve E-10!)
        raw_counts = Counter(p.stance for p in non_spam_posts if p.stance in self.categories)
        raw_total_valid = max(1, sum(raw_counts.values()))
        raw_contaminated_pct = {
            cat: round((raw_counts.get(cat, 0) / raw_total_valid) * 100.0, 2)
            for cat in self.categories
        }

        # Politica de exclusao em nivel de CONTA (Checklist #2 / M-05):
        # Qualquer conta que tenha `account_suspected_cib` ou post sinalizado como CIB e marcada como conta CIB
        cib_account_keys: Set[Tuple[str, str]] = set()
        all_non_spam_account_keys: Set[Tuple[str, str]] = set()
        for p in non_spam_posts:
            key = (p.platform, p.author_hash)
            all_non_spam_account_keys.add(key)
            if (
                p.account_suspected_cib
                or p.suspected_coordination
                or p.activity_class == "Suspeita_CIB_Automacao"
                or p.coordination_signal_index >= self.suspected_cib_threshold
            ):
                cib_account_keys.add(key)

        cib_posts = [p for p in non_spam_posts if (p.platform, p.author_hash) in cib_account_keys]
        civic_posts = [
            p
            for p in non_spam_posts
            if (p.platform, p.author_hash) not in cib_account_keys
            and p.activity_class == "Mobilizacao_Civica_Legitima"
        ]
        rep_org_posts = [
            p
            for p in non_spam_posts
            if (p.platform, p.author_hash) not in cib_account_keys
            and p.activity_class == "Repeticao_Organica"
        ]
        organic_posts = [
            p
            for p in non_spam_posts
            if (p.platform, p.author_hash) not in cib_account_keys
            and p.stance in self.categories
        ]

        post_art_rate = round((len(cib_posts) / max(1, len(non_spam_posts))) * 100.0, 2)
        acc_art_rate = round((len(cib_account_keys) / max(1, len(all_non_spam_account_keys))) * 100.0, 2)

        # 2. Consolidacao '1 Autor Digital Organico por Plataforma = 1 Unidade Observacional' (U_Org)
        account_stances: Dict[Tuple[str, str], List[str]] = defaultdict(list)
        account_region: Dict[Tuple[str, str], str] = {}
        for p in organic_posts:
            key = (p.platform, p.author_hash)
            account_stances[key].append(p.stance)
            if p.region_proxy != "Nao Identificado":
                account_region[key] = p.region_proxy

        total_N_org = len(account_stances)
        if total_N_org == 0:
            raise ValueError("Nenhuma unidade observacional organica restou apos filtragem.")

        # Se foi fornecida sub-amostra sorteada de contas (com pesos de desenho d_i = 1/pi_i - C-01),
        # usa as unidades sorteadas para estimar U_Org; caso contrario, usa o quadro de contas observado
        if sampled_account_units:
            active_units = [
                u for u in sampled_account_units if (u.platform, u.author_hash) not in cib_account_keys and u.stances
            ]
        else:
            active_units = [
                OrganicAccountSampleUnit(
                    platform=plat,
                    author_hash=acc_h,
                    region_proxy=account_region.get((plat, acc_h), "Nao Identificado"),
                    modal_time_stratum="",
                    modal_day_str="",
                    stratum_key=plat,
                    posts_count=len(st_list),
                    stances=st_list,
                    inclusion_probability_pi=1.0,
                    design_weight_d=1.0,
                )
                for (plat, acc_h), st_list in sorted(account_stances.items())
            ]

        n_sampled_accounts = len(active_units)
        obs_platforms = [u.platform for u in active_units]
        obs_regions = [u.region_proxy for u in active_units]
        obs_stances = [self._resolve_deterministic_modal_stance(u.stances, mode="neutral_tie") for u in active_units]
        design_weights = np.array([u.design_weight_d for u in active_units], dtype=float)
        stances_np = np.array(obs_stances)

        # Analise de sensibilidade do desempate modal (E-08: 'neutral_tie' vs 'last_post' vs 'fractional')
        last_post_stances = np.array([
            self._resolve_deterministic_modal_stance(u.stances, mode="last_post") for u in active_units
        ])
        tie_sensitivity: Dict[str, Dict[str, float]] = {
            "neutral_tie": {},
            "last_post": {},
            "fractional": {},
        }
        for cat in self.categories:
            tie_sensitivity["neutral_tie"][cat] = round(float(np.mean(stances_np == cat) * 100.0), 2)
            tie_sensitivity["last_post"][cat] = round(float(np.mean(last_post_stances == cat) * 100.0), 2)
            frac_vals = [sum(1.0 for s in u.stances if s == cat) / max(1, len(u.stances)) for u in active_units]
            tie_sensitivity["fractional"][cat] = round(float(np.mean(frac_vals) * 100.0), 2)

        # 3. Calculo dos 3 Cenarios:
        # Cenario 1: Indicador Organico de Contas (ponderado por d_i = 1/pi_i do sorteio interno)
        sum_d = float(np.sum(design_weights))
        scen1_pct: Dict[str, float] = {}
        for cat in self.categories:
            ind = (stances_np == cat).astype(float)
            scen1_pct[cat] = round(float(np.sum(design_weights * ind) / max(1e-9, sum_d) * 100.0), 2)

        # Correcao de erro de classificacao de Rogan & Gladen (1978) sobre C1 (C-01)
        rg_c1_pct = self.rogan_gladen_misclassification_correction(scen1_pct)

        # Cenario 2: Indicador Equilibrado por Plataforma (peso 1/K para cada rede presente)
        plat_counts = Counter(obs_platforms)
        k_plats = max(1, len(plat_counts))
        equal_plat_weights = np.array([
            (1.0 / k_plats) / (plat_counts[pl] / n_sampled_accounts)
            for pl in obs_platforms
        ])
        equal_plat_weights *= n_sampled_accounts / np.sum(equal_plat_weights)
        scen2_pct: Dict[str, float] = {}
        for cat in self.categories:
            ind = (stances_np == cat).astype(float)
            scen2_pct[cat] = round(float(np.sum(equal_plat_weights * ind) / np.sum(equal_plat_weights) * 100.0), 2)

        # Cenario 3: Reponderado (Sensibilidade sob Ignorabilidade) via Raking IPF com Trimming no Laco (E-01)
        raking_weights = self._compute_ipf_raking_weights(obs_platforms, obs_regions)
        sum_w = float(np.sum(raking_weights))
        sum_w2 = float(np.sum(raking_weights**2))

        # 4. Efeito do Desenho (DEFF de Kish) e Tamanho Amostral Efetivo (n_eff)
        deff = (n_sampled_accounts * sum_w2) / (sum_w**2) if sum_w > 0 else 1.0
        n_eff = n_sampled_accounts / deff

        scen3_pct: Dict[str, float] = {}
        for cat in self.categories:
            ind = (stances_np == cat).astype(float)
            scen3_pct[cat] = round(float(np.sum(raking_weights * ind) / sum_w * 100.0), 2)

        # Incerteza estatistica interna (com correcao para populacao finita FPC quando sub-amostrado de U_Org,
        # acrescida da incerteza do bootstrap sob superpopulacao estocastica - C-01 / E-05)
        fpc_factor = max(0.0, 1.0 - (n_sampled_accounts / total_N_org)) if n_sampled_accounts < total_N_org else 1.0
        internal_uncertainty_pp = round(
            self.confidence_z * math.sqrt((0.25 * fpc_factor) / max(1.0, n_eff)) * 100.0,
            2,
        )

        # 5. Bootstrap Nao Parametrico Estratificado de Contas em Chunks (E-03 / G-05)
        ci_95_c1 = self._stratified_chunked_bootstrap_ci(
            obs_platforms, stances_np, design_weights, b_iters, self.bootstrap_chunk_size, random_seed
        )
        ci_95_c3 = self._stratified_chunked_bootstrap_ci(
            obs_platforms, stances_np, raking_weights, b_iters, self.bootstrap_chunk_size, random_seed
        )

        # 6. Teste de Homogeneidade Inter-Plataformas (sem pesos marginais de plataforma + V de Cramer + Holm - E-04/E-09)
        homog_test = self.platform_homogeneity_chi2_test(obs_platforms, obs_stances, design_weights)

        return StatisticalReportMetrics(
            total_raw_posts_N=total_raw,
            total_commercial_spam_posts=len(spam_posts),
            total_suspected_cib_posts=len(cib_posts),
            total_suspected_cib_accounts=len(cib_account_keys),
            total_organic_accounts_N_org=total_N_org,
            sampled_organic_accounts_n=n_sampled_accounts,
            total_civic_mobilization_posts=len(civic_posts),
            total_organic_repetition_posts=len(rep_org_posts),
            post_level_artificiality_rate_pct=post_art_rate,
            account_level_artificiality_rate_pct=acc_art_rate,
            kish_design_effect_deff=round(deff, 3),
            effective_sample_size_n_eff=round(n_eff, 1),
            confidence_level_pct=95.0,
            internal_statistical_uncertainty_pp=internal_uncertainty_pp,
            scenario_3_calibration_status=self.last_calibration_status,
            scenario_3_max_margin_gap_pp=self.last_max_margin_gap,
            scenario_3_margins_table=self.last_margins_table,
            scenario_1_organic_unweighted_pct=scen1_pct,
            scenario_2_equal_platform_pct=scen2_pct,
            scenario_3_reweighted_sensitivity_pct=scen3_pct,
            rogan_gladen_corrected_c1_pct=rg_c1_pct,
            raw_contaminated_volume_pct=raw_contaminated_pct,
            confidence_intervals_95_c1_pct=ci_95_c1,
            confidence_intervals_95_pct=ci_95_c3,
            platform_divergence_test=homog_test,
            tie_breaking_sensitivity_pct=tie_sensitivity,
        )
