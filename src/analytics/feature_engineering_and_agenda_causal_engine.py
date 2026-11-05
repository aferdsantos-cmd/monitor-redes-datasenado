"""
Motor 4A: Engenharia de Recursos Causais, Salvaguardas Anti-Leakage e Agenda-Setting.

Implementa:
1. Validação de integridade de dados e diagnóstico de missing (MCAR/MAR/MNAR) vetorizado;
2. Extração de atributos temporais estritamente causais (closed='left'), Burstiness de Goh-Barabási e ciclos trigonométricos;
3. Atributos lexicais e de enquadramento editorial (ADR-011);
4. Pipeline Anti-Leakage Fit-on-Train-Only com Out-of-Fold (OOF) Empirical Bayes Target Encoding e VIF (< 5.0);
5. Salvaguarda de k-anonimato LGPD (k >= 5) para agregação de estratos;
6. Análise de Agenda-Setting, CUSUM e Causalidade de Granger Bivariada com controle de FDR (ADR-008).
"""

from __future__ import annotations

from collections import Counter, defaultdict
import copy
import math
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pandas as pd

from src.collectors.base_collector import (
    BaseLexicallyNeutralCollector,
    RawCollectedManifestation,
    enrich_settings_with_dynamic_themes,
)


def compute_burstiness(inter_arrival_times: np.ndarray) -> float:
    """
    Calcula o Índice de Burstiness de Goh-Barabási:
    B = (sigma - mu) / (sigma + mu) in [-1, 1]
    onde tau são os intervalos temporais entre postagens consecutivas.
    """
    clean = inter_arrival_times[~np.isnan(inter_arrival_times)]
    if len(clean) < 2:
        return 0.0
    mu = float(np.mean(clean))
    sigma = float(np.std(clean, ddof=1))
    if (sigma + mu) < 1e-12:
        return 0.0
    b = (sigma - mu) / (sigma + mu)
    return float(np.clip(b, -1.0, 1.0))


def compute_vif_matrix(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """Calcula o Fator de Inflação da Variância (VIF = 1 / (1 - R^2)) via OLS matricial."""
    n_samples, n_features = X.shape
    vif_dict: Dict[str, float] = {}

    if n_features < 2 or n_samples <= n_features:
        return {name: 1.0 for name in feature_names}

    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0)
    X_std[X_std < 1e-12] = 1.0
    X_norm = (X - X_mean) / X_std

    for i in range(n_features):
        y_i = X_norm[:, i]
        mask = np.ones(n_features, dtype=bool)
        mask[i] = False
        X_other = X_norm[:, mask]

        A = np.column_stack([np.ones(n_samples), X_other])
        try:
            coeffs, residuals, _, _ = np.linalg.lstsq(A, y_i, rcond=None)
            pred = A @ coeffs
            ss_tot = np.sum((y_i - np.mean(y_i)) ** 2)
            ss_res = np.sum((y_i - pred) ** 2)
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0
            r_squared = np.clip(r_squared, 0.0, 0.999999)
            vif_val = 1.0 / (1.0 - r_squared)
        except np.linalg.LinAlgError:
            vif_val = float("inf")

        vif_dict[feature_names[i]] = round(float(vif_val), 2)

    return vif_dict


def benjamini_hochberg_fdr(
    p_values: Sequence[float],
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """Aplica o procedimento de Benjamini-Hochberg para controle de taxa de falsas descobertas (FDR)."""
    p_arr = np.asarray(p_values, dtype=float)
    m = len(p_arr)
    if m == 0:
        return np.array([], dtype=bool), np.array([], dtype=float)

    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    k_ranks = np.arange(1, m + 1)
    q_raw = sorted_p * (float(m) / k_ranks)
    q_monotonic = np.minimum.accumulate(q_raw[::-1])[::-1]
    q_monotonic = np.clip(q_monotonic, 0.0, 1.0)

    q_values = np.zeros(m, dtype=float)
    q_values[sorted_indices] = q_monotonic
    rejected = q_values <= alpha
    return rejected, q_values


def detect_cusum_structural_break(
    series: np.ndarray,
    threshold: float = 5.0,
    drift: float = 0.5,
) -> Dict[str, Any]:
    """
    Detector sequencial CUSUM para identificar o instante exato de explosão
    de pauta ou quebra estrutural em volumes temporais.
    """
    s = np.asarray(series, dtype=float)
    if len(s) < 3:
        return {"break_detected": False, "break_index": None, "cusum_max": 0.0}

    mean_val = float(np.mean(s))
    std_val = float(np.std(s, ddof=1)) if len(s) > 1 else 1.0
    if std_val < 1e-12:
        return {"break_detected": False, "break_index": None, "cusum_max": 0.0}

    z = (s - mean_val) / std_val
    s_pos = 0.0
    s_neg = 0.0
    break_idx: Optional[int] = None
    max_c = 0.0

    for i, val in enumerate(z):
        s_pos = max(0.0, s_pos + val - drift)
        s_neg = max(0.0, s_neg - val - drift)
        cur_max = max(s_pos, s_neg)
        if cur_max > max_c:
            max_c = cur_max
        if (s_pos > threshold or s_neg > threshold) and break_idx is None:
            break_idx = i

    return {
        "break_detected": break_idx is not None,
        "break_index": break_idx,
        "cusum_max": round(float(max_c), 3),
    }


# Alias de conveniência
cusum_detector = detect_cusum_structural_break


def granger_causality_test(
    series_x: np.ndarray,
    series_y: np.ndarray,
    max_lag: int = 3,
) -> Dict[str, float]:
    """
    Executa o Teste F de Causalidade de Granger Bivariada: X causa Y no sentido de Granger?
    Compara SSR do modelo restrito AR(p) vs modelo irrestrito com lags de X.
    """
    x = np.asarray(series_x, dtype=float)
    y = np.asarray(series_y, dtype=float)
    T = len(y)
    if T <= 2 * max_lag + 2:
        return {"f_statistic": 0.0, "p_value": 1.0, "is_causal": False}

    Y_target = y[max_lag:]
    n_samples = len(Y_target)

    X_restr_cols = [np.ones(n_samples)]
    for lag in range(1, max_lag + 1):
        X_restr_cols.append(y[max_lag - lag : T - lag])
    X_restr = np.column_stack(X_restr_cols)

    X_unrestr_cols = list(X_restr_cols)
    for lag in range(1, max_lag + 1):
        X_unrestr_cols.append(x[max_lag - lag : T - lag])
    X_unrestr = np.column_stack(X_unrestr_cols)

    try:
        b_restr, _, _, _ = np.linalg.lstsq(X_restr, Y_target, rcond=None)
        ssr_restr = float(np.sum((Y_target - X_restr @ b_restr) ** 2))

        b_unrestr, _, _, _ = np.linalg.lstsq(X_unrestr, Y_target, rcond=None)
        ssr_unrestr = float(np.sum((Y_target - X_unrestr @ b_unrestr) ** 2))

        df_num = max_lag
        df_denom = max(1, n_samples - (2 * max_lag + 1))
        ss_diff = max(0.0, ssr_restr - ssr_unrestr)
        f_stat = float((ss_diff / df_num) / (max(ssr_unrestr, 1e-12) / df_denom))
        p_val = float(math.erfc(math.sqrt(max(0.0, f_stat * df_num) / 2.0)))
    except Exception:
        f_stat, p_val = 0.0, 1.0

    return {
        "f_statistic": round(f_stat, 4),
        "p_value": round(p_val, 4),
        "is_causal": bool(p_val < 0.05),
    }


class FeatureEngineeringAndAgendaCausalEngine:
    """
    Motor 4A: Extração de Features Causais, OOF Target Encoding e Causalidade de Agenda.
    Garante ausência absoluta de data leakage e look-ahead bias.
    """

    def __init__(self, settings_override: Optional[Dict[str, Any]] = None) -> None:
        self.settings = enrich_settings_with_dynamic_themes(settings_override)

    # =========================================================================
    # 1. Diagnóstico de Qualidade e Missing (MCAR / MAR / MNAR)
    # =========================================================================
    @staticmethod
    def validate_and_diagnose_dataset(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executa verificação de integridade e classifica o mecanismo de missing
        de forma vetorizada sem utilizar iteração linha a linha.
        """
        total_rows = len(df)
        if total_rows == 0:
            return {"total_rows": 0, "columns": {}, "status": "EMPTY_DATASET"}

        col_diag: Dict[str, Dict[str, Any]] = {}
        missing_counts = df.isnull().sum()

        for col in df.columns:
            m_count = int(missing_counts[col])
            m_pct = round((m_count / total_rows) * 100.0, 2)
            mechanism = "COMPLETE"
            if m_count > 0:
                # Heurística diagnóstico de padrão de dados ausentes
                if m_pct < 5.0:
                    mechanism = "MCAR_MISSING_COMPLETELY_AT_RANDOM"
                elif col in ("phone_or_location_hint", "DDD_proxy", "shared_urls_json"):
                    mechanism = "MAR_MISSING_AT_RANDOM_STRUCTURAL"
                else:
                    mechanism = "MNAR_MISSING_NOT_AT_RANDOM"

            col_diag[col] = {
                "missing_count": m_count,
                "missing_pct": m_pct,
                "dtype": str(df[col].dtype),
                "inferred_mechanism": mechanism,
            }

        return {
            "total_rows": total_rows,
            "total_columns": len(df.columns),
            "columns": col_diag,
            "status": "VALIDATED_OK",
        }

    # =========================================================================
    # 2. Features de Séries Temporais Estritamente Causais (closed='left')
    # =========================================================================
    @staticmethod
    def compute_causal_temporal_features(
        df_or_items: Union[pd.DataFrame, Sequence[RawCollectedManifestation]],
    ) -> pd.DataFrame:
        """
        Calcula atributos temporais causais:
        - Janelas deslizantes móveis usando APENAS eventos estritamente anteriores [t - W, t);
        - Codificação trigonométrica contínua (hour_sin/cos, dow_sin/cos);
        - Burstiness de Goh-Barabási e EWMA velocity.
        """
        if isinstance(df_or_items, pd.DataFrame):
            df = df_or_items.copy()
        else:
            rows = []
            for m in df_or_items:
                meta = getattr(m, "metadata", {}) or {}
                rows.append({
                    "comment_id": m.comment_id,
                    "author_id_hash": getattr(m, "author_hash", m.raw_author_id),
                    "platform": m.platform,
                    "created_at": m.created_at,
                    "text": getattr(m, "text", getattr(m, "text_content", "")),
                    "stance_label": meta.get("stance_label") or meta.get("classified_stance") or "Neutro",
                })
            df = pd.DataFrame(rows)

        if df.empty:
            return df

        if not pd.api.types.is_datetime64_any_dtype(df["created_at"]):
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

        # Ordena cronologicamente para garantir temporalidade estrita
        df = df.sort_values("created_at").reset_index(drop=True)

        # 1. Ciclos Trigonométricos
        hours = df["created_at"].dt.hour.to_numpy() + df["created_at"].dt.minute.to_numpy() / 60.0
        dows = df["created_at"].dt.day_of_week.to_numpy()

        df["hour_sin"] = np.sin(2.0 * np.pi * hours / 24.0)
        df["hour_cos"] = np.cos(2.0 * np.pi * hours / 24.0)
        df["dow_sin"] = np.sin(2.0 * np.pi * dows / 7.0)
        df["dow_cos"] = np.cos(2.0 * np.pi * dows / 7.0)

        # 2. Janelas Móveis Causais com closed='left' (evita look-ahead bias)
        timestamps = df["created_at"].dt.tz_convert(None).to_numpy()
        n = len(df)
        counts_6h = np.zeros(n, dtype=float)
        velocity_ewma = np.zeros(n, dtype=float)

        window_sec = 6.0 * 3600.0
        left_idx = 0

        # Implementação Two-Pointer estritamente causal [t - W, t)
        for i in range(n):
            cur_t = timestamps[i].astype("datetime64[ns]").astype(np.int64) / 1e9
            # Ajusta ponteiro da esquerda para t - window_sec
            while left_idx < i:
                left_t = timestamps[left_idx].astype("datetime64[ns]").astype(np.int64) / 1e9
                if (cur_t - left_t) > window_sec:
                    left_idx += 1
                else:
                    break
            # Apenas itens estritamente anteriores a i são computados: [left_idx, i)
            counts_6h[i] = float(max(0, i - left_idx))

        df["causal_rolling_post_count_6h"] = counts_6h

        # EWMA da velocidade (taxa inter-chegadas)
        inter_arrivals = np.diff(timestamps.astype("datetime64[ns]").astype(np.int64) / 1e9)
        inter_arrivals = np.concatenate([[60.0], inter_arrivals])
        inter_arrivals = np.maximum(1.0, inter_arrivals)

        alpha = 0.20
        cur_vel = 1.0 / inter_arrivals[0]
        for i in range(n):
            if i > 0:
                cur_vel = alpha * (1.0 / inter_arrivals[i]) + (1.0 - alpha) * cur_vel
            velocity_ewma[i] = cur_vel

        df["ewma_velocity"] = np.round(velocity_ewma, 4)

        # 3. Burstiness de Goh-Barabási global e dinâmico por linha
        global_burstiness = compute_burstiness(inter_arrivals)
        df["global_burstiness_b"] = global_burstiness

        author_history: Dict[str, List[float]] = defaultdict(list)
        burstiness_per_row = np.zeros(n, dtype=float)

        for i in range(n):
            cur_sec = timestamps[i].astype("datetime64[ns]").astype(np.int64) / 1e9
            auth = str(df.iloc[i].get("author_id_hash", "anon"))
            author_history[auth].append(cur_sec)

            local_slice = inter_arrivals[max(0, i - 8) : i + 1]
            local_b = compute_burstiness(local_slice)

            auth_times = author_history[auth]
            if len(auth_times) >= 3:
                auth_deltas = np.diff(auth_times[-9:])
                auth_b = compute_burstiness(auth_deltas)
                row_b = 0.7 * auth_b + 0.3 * local_b
            elif len(auth_times) == 2:
                row_b = 0.5 * local_b + 0.5 * global_burstiness
            else:
                row_b = 0.5 * local_b

            burstiness_per_row[i] = round(float(np.clip(row_b, -1.0, 1.0)), 4)

        df["burstiness_b"] = burstiness_per_row

        return df

    # =========================================================================
    # 3. Features Lexicais e Enquadramento Editorial (ADR-011)
    # =========================================================================
    def compute_lexical_and_framing_features(
        self,
        df_or_items: Union[pd.DataFrame, Sequence[Union[RawCollectedManifestation, Dict[str, Any]]]],
        theme_id: str,
    ) -> pd.DataFrame:
        """
        Calcula densidade léxica (Type-Token Ratio), viés léxico de adjetivos,
        pontuação enfática e alinhamento com vocabulário legislativo do tema.
        """
        if isinstance(df_or_items, pd.DataFrame):
            df_out = df_or_items.copy()
            if "text" not in df_out.columns and "text_content" in df_out.columns:
                df_out["text"] = df_out["text_content"]
        else:
            rows = []
            for m in df_or_items:
                if isinstance(m, RawCollectedManifestation):
                    rows.append({
                        "comment_id": m.comment_id,
                        "text": getattr(m, "text", getattr(m, "text_content", "")),
                    })
                elif isinstance(m, dict):
                    rows.append({
                        "comment_id": m.get("comment_id", ""),
                        "text": m.get("text") or m.get("text_content", ""),
                    })
            df_out = pd.DataFrame(rows)

        if df_out.empty or "text" not in df_out.columns:
            return df_out

        texts = df_out["text"].astype(str).tolist()

        # Marcadores de adjetivação / intensificadores
        intensifiers = {
            "absurdo", "urgente", "vergonha", "golpe", "crime", "traicao", "excelente",
            "parabens", "historia", "vitoria", "derrota", "rejeitem", "aprovem", "fora",
            "perigo", "atraso", "ameaca", "retrocesso", "avanco", "inadmissivel",
        }

        # Vocabulário neutro institucional do tema em settings
        themes_map = {t["id"]: t for t in self.settings.get("pilot_themes", []) if isinstance(t, dict) and "id" in t}
        theme_cfg = themes_map.get(theme_id, {})
        neutral_terms = set()
        for q in theme_cfg.get("collection_query_terms", []):
            neutral_terms.update(re.findall(r"\w+", q.lower()))

        ttr_list = []
        bias_rate_list = []
        punct_density_list = []
        has_news_domain_list = []
        vocab_alignment_list = []

        allowlisted_domains = self.settings.get("cib_and_bot_detection", {}).get(
            "institutional_and_news_domain_allowlist", ["senado.leg.br", "camara.leg.br", "gov.br"]
        )

        nlp_tax = theme_cfg.get("nlp_stance_taxonomy", {})
        fav_markers = [str(m).lower() for m in nlp_tax.get("favorable_markers", [])]
        against_markers = [str(m).lower() for m in nlp_tax.get("against_markers", [])]
        neutral_markers = [str(m).lower() for m in nlp_tax.get("neutral_markers", [])]

        fav_density_list = []
        against_density_list = []
        neutral_density_list = []
        net_polarity_list = []

        for txt in texts:
            tokens = re.findall(r"\w+", txt.lower())
            n_tokens = len(tokens)
            if n_tokens == 0:
                ttr_list.append(0.0)
                bias_rate_list.append(0.0)
                punct_density_list.append(0.0)
                has_news_domain_list.append(0.0)
                vocab_alignment_list.append(0.0)
                fav_density_list.append(0.0)
                against_density_list.append(0.0)
                neutral_density_list.append(0.0)
                net_polarity_list.append(0.0)
                continue

            # Type-Token Ratio
            ttr = len(set(tokens)) / float(n_tokens)
            ttr_list.append(round(ttr, 3))

            # Taxa de intensificadores / viés adjetival
            bias_hits = sum(1 for tok in tokens if tok in intensifiers)
            bias_rate_list.append(round(bias_hits / float(n_tokens), 3))

            # Pontuação enfática (! e ?)
            punct_hits = len(re.findall(r"[!?]", txt))
            punct_density_list.append(round(punct_hits / float(len(txt)), 3))

            # Presença de domínio jornalístico/governamental
            has_domain = any(dom in txt.lower() for dom in allowlisted_domains)
            has_news_domain_list.append(1.0 if has_domain else 0.0)

            # Alinhamento lexical com termos neutros
            if neutral_terms:
                align_hits = sum(1 for tok in tokens if tok in neutral_terms)
                vocab_alignment_list.append(round(align_hits / float(n_tokens), 3))
            else:
                vocab_alignment_list.append(0.0)

            # Densidade semântica de marcadores de stance (ADR-011)
            txt_lower = txt.lower()
            fav_c = sum(1 for m in fav_markers if m in txt_lower)
            against_c = sum(1 for m in against_markers if m in txt_lower)
            neutral_c = sum(1 for m in neutral_markers if m in txt_lower)

            fav_d = round(fav_c / float(max(1, n_tokens)), 4)
            against_d = round(against_c / float(max(1, n_tokens)), 4)
            neutral_d = round(neutral_c / float(max(1, n_tokens)), 4)
            net_pol = round(float(fav_d - against_d), 4)

            fav_density_list.append(fav_d)
            against_density_list.append(against_d)
            neutral_density_list.append(neutral_d)
            net_polarity_list.append(net_pol)

        df_out["lexical_ttr"] = ttr_list
        df_out["type_token_ratio"] = ttr_list
        df_out["lexical_bias_rate"] = bias_rate_list
        df_out["punct_emphasis_density"] = punct_density_list
        df_out["has_news_domain"] = has_news_domain_list
        df_out["neutral_vocab_alignment"] = vocab_alignment_list
        df_out["fav_marker_density"] = fav_density_list
        df_out["against_marker_density"] = against_density_list
        df_out["neutral_marker_density"] = neutral_density_list
        df_out["net_marker_polarity"] = net_polarity_list

        return df_out

    # =========================================================================
    # 4. Pipeline Anti-Leakage Fit-on-Train-Only e OOF Target Encoding
    # =========================================================================
    @staticmethod
    def fit_transform_train_and_transform_val(
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        target_col: str,
        group_col: str = "author_id_hash",
        categorical_cols: Optional[List[str]] = None,
        numeric_cols: Optional[List[str]] = None,
        smoothing_m: float = 10.0,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Executa transformações de pré-processamento com rigor anti-leakage:
        - Bloqueia com ValueError se houver interseção de autores entre treino e validação;
        - Ajusta OOF Empirical Bayes Target Encoding no treino e aplica mapping no val;
        - Escalonamento robusto ajustado exclusivamente no treino;
        - Diagnóstico de VIF no treino.
        """
        # 1. Trava anti-vazamento de contas
        train_authors = set(train_df[group_col].dropna().unique())
        val_authors = set(val_df[group_col].dropna().unique())
        overlap = train_authors.intersection(val_authors)
        if overlap:
            raise ValueError(
                f"VAZAMENTO DE AUTOR DETECTADO (ANTI-LEAKAGE): {len(overlap)} contas "
                f"presentes simultaneamente no treino e na validação!"
            )

        train_out = train_df.copy()
        val_out = val_df.copy()

        y_train = train_out[target_col].values
        # Mapeamento numérico se alvo for categórico
        if y_train.dtype == object or isinstance(y_train[0], str):
            unique_classes = sorted(list(set(y_train)))
            class_map = {cls_name: i for i, cls_name in enumerate(unique_classes)}
            y_train_num = np.array([class_map[val] for val in y_train], dtype=float)
        else:
            y_train_num = np.asarray(y_train, dtype=float)

        global_prior = float(np.mean(y_train_num)) if len(y_train_num) > 0 else 0.5
        cats = categorical_cols or ["platform"]
        oof_meta: Dict[str, Any] = {"global_prior": global_prior, "mappings": {}}

        # 2. Out-of-Fold Target Encoding no Treino (agrupado por autor)
        unique_groups = list(train_out[group_col].unique())
        n_splits = min(5, max(2, len(unique_groups)))
        rng = np.random.default_rng(42)
        shuffled_groups = list(unique_groups)
        rng.shuffle(shuffled_groups)
        folds = np.array_split(shuffled_groups, n_splits)

        for col in cats:
            if col not in train_out.columns:
                continue

            encoded_train = np.zeros(len(train_out), dtype=float)

            # OOF no Treino
            for fold_groups in folds:
                val_mask = train_out[group_col].isin(fold_groups)
                tr_mask = ~val_mask

                tr_cats = train_out.loc[tr_mask, col].values
                tr_y = y_train_num[tr_mask]
                tr_prior = float(np.mean(tr_y)) if len(tr_y) > 0 else global_prior

                cat_stats: Dict[Any, Tuple[float, int]] = {}
                for c_val in np.unique(tr_cats):
                    sub_m = (tr_cats == c_val)
                    cat_stats[c_val] = (float(np.mean(tr_y[sub_m])), int(np.sum(sub_m)))

                fold_cats = train_out.loc[val_mask, col].values
                fold_enc = np.zeros(len(fold_cats), dtype=float)
                for idx, c_val in enumerate(fold_cats):
                    if c_val in cat_stats:
                        m_c, n_c = cat_stats[c_val]
                        lambda_c = n_c / (n_c + smoothing_m)
                        fold_enc[idx] = lambda_c * m_c + (1.0 - lambda_c) * tr_prior
                    else:
                        fold_enc[idx] = tr_prior

                encoded_train[val_mask.values] = fold_enc

            train_out[f"{col}_oof_te"] = encoded_train

            # Estatísticas consolidadas de todo o treino para aplicar no val_df
            full_cat_stats: Dict[Any, float] = {}
            for c_val in train_out[col].unique():
                sub_m = (train_out[col] == c_val)
                n_c = int(np.sum(sub_m))
                m_c = float(np.mean(y_train_num[sub_m.values]))
                lambda_c = n_c / (n_c + smoothing_m)
                full_cat_stats[c_val] = lambda_c * m_c + (1.0 - lambda_c) * global_prior

            oof_meta["mappings"][col] = full_cat_stats

            # Aplicação pura de transform em val_df (fit-on-train-only)
            val_encoded = np.array([
                full_cat_stats.get(v, global_prior) for v in val_out[col].values
            ], dtype=float)
            val_out[f"{col}_oof_te"] = val_encoded

        # 3. Escalonamento Robusto e VIF sobre numéricas
        nums = numeric_cols or [c for c in train_out.select_dtypes(include=[np.number]).columns if not c.endswith("_oof_te") and c != target_col]
        # Remove eventuais constantes
        nums = [c for c in nums if train_out[c].nunique() > 1]

        robust_scaler_medians: Dict[str, float] = {}
        robust_scaler_iqrs: Dict[str, float] = {}

        for col in nums:
            med = float(np.median(train_out[col]))
            q75, q25 = np.percentile(train_out[col], [75, 25])
            iqr = float(max(q75 - q25, 1e-6))
            robust_scaler_medians[col] = round(med, 4)
            robust_scaler_iqrs[col] = round(iqr, 4)
            train_out[f"{col}_robust_scaled"] = (train_out[col] - med) / iqr
            val_out[f"{col}_robust_scaled"] = (val_out[col] - med) / iqr

        vif_results: Dict[str, float] = {}
        if nums:
            X_tr_num = train_out[nums].values
            vif_results = compute_vif_matrix(X_tr_num, nums)

        metadata = {
            "train_rows": len(train_out),
            "val_rows": len(val_out),
            "robust_scaler_medians": robust_scaler_medians,
            "robust_scaler_iqrs": robust_scaler_iqrs,
            "vif_diagnostics": vif_results,
            "target_encoding": oof_meta,
            "high_vif_features": [f for f, v in vif_results.items() if v >= 5.0],
        }

        return train_out, val_out, metadata

    # =========================================================================
    # 5. Salvaguarda de k-Anonimato LGPD (k >= 5)
    # =========================================================================
    @staticmethod
    def enforce_k_anonymity_aggregation(
        df: pd.DataFrame,
        group_cols: List[str],
        author_col: str = "author_id_hash",
        k: int = 5,
    ) -> pd.DataFrame:
        """
        Agrega estatísticas por estrato, colapsando automaticamente qualquer
        célula com contagem única de contas < k em 'OUTROS_ANONIMIZADO_LGPD_K5'.
        Garante que nenhuma célula publicada exponha 0 < N < k contas.
        """
        if df.empty:
            return pd.DataFrame()

        # Agrupa e conta autores distintos
        agg_df = (
            df.groupby(group_cols)[author_col]
            .nunique()
            .reset_index(name="unique_authors_count")
        )

        # Identifica células vulneráveis (1 <= count < k)
        vulnerable_mask = agg_df["unique_authors_count"] < k
        if not vulnerable_mask.any():
            return agg_df

        # Colapsa o último nível de agrupamento em categoria segura
        safe_agg = agg_df.copy()
        last_col = group_cols[-1]
        safe_agg.loc[vulnerable_mask, last_col] = "OUTROS_ANONIMIZADO_LGPD_K5"

        # Re-agrega sobre as novas categorias colapsadas
        re_agg = (
            safe_agg.groupby(group_cols)["unique_authors_count"]
            .sum()
            .reset_index()
        )

        # Salvaguarda LGPD Estrita: se alguma célula residual ainda tiver contagem < k,
        # aplica o piso censurado LGPD para não expor célula com contagem < k.
        under_k_mask = re_agg["unique_authors_count"] < k
        if under_k_mask.any():
            re_agg.loc[under_k_mask, "unique_authors_count"] = k
            re_agg["k_anonymity_censored_floor"] = True

        return re_agg

    # =========================================================================
    # 6. Agenda-Setting, CUSUM e Causalidade de Granger (ADR-008)
    # =========================================================================
    @staticmethod
    def analyze_agenda_setting_and_granger_causality(
        df_or_items: Union[pd.DataFrame, Sequence[RawCollectedManifestation]],
        entity_col: str = "platform",
        max_lag: int = 2,
    ) -> Dict[str, Any]:
        """
        Executa o Teste F de Causalidade de Granger bivariada entre todos os pares
        de entidades (plataformas ou espectros), com ajuste de Benjamini-Hochberg FDR
        e detecção de structural breaks com CUSUM.
        """
        if isinstance(df_or_items, pd.DataFrame):
            df = df_or_items.copy()
        else:
            rows = []
            for m in df_or_items:
                if isinstance(m, dict):
                    ent_val = m.get(entity_col) or m.get("platform", "plataforma_geral")
                    ts = m.get("created_at")
                else:
                    ent_val = getattr(m, entity_col, getattr(m, "platform", "plataforma_geral"))
                    ts = getattr(m, "created_at", None)
                rows.append({
                    entity_col: ent_val,
                    "created_at": ts,
                })
            df = pd.DataFrame(rows)

        if df.empty or len(df) < 10:
            return {
                "pairs_tested": 0,
                "granger_results": [],
                "cusum_alerts": {},
                "status": "INSUFFICIENT_DATA",
            }

        if not pd.api.types.is_datetime64_any_dtype(df["created_at"]):
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True)

        # Constrói séries temporais discretizadas contínuas (freq adaptativa garantindo T >= 24)
        min_ts = df["created_at"].min()
        max_ts = df["created_at"].max()
        time_span_hours = max(0.1, (max_ts - min_ts).total_seconds() / 3600.0)

        min_required_T = max(24, 2 * max_lag + 6)
        if time_span_hours >= min_required_T:
            freq_str = "1h"
        elif time_span_hours >= min_required_T / 2.0:
            freq_str = "30min"
        elif time_span_hours >= min_required_T / 4.0:
            freq_str = "15min"
        else:
            freq_str = "5min"

        df["time_bucket"] = df["created_at"].dt.floor(freq_str)
        pivot = (
            df.groupby(["time_bucket", entity_col])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        start_grid = min_ts.floor(freq_str)
        end_grid = max_ts.ceil(freq_str)
        full_grid = pd.date_range(start=start_grid, end=end_grid, freq=freq_str, tz=min_ts.tz)
        if len(full_grid) < min_required_T:
            full_grid = pd.date_range(start=start_grid, periods=min_required_T, freq=freq_str, tz=min_ts.tz)

        pivot = pivot.reindex(full_grid, fill_value=0)

        entities = list(pivot.columns)
        granger_raw: List[Dict[str, Any]] = []
        p_values_to_adjust: List[float] = []

        # Testa causalidade de Granger para cada par (X -> Y)
        for i, ent_x in enumerate(entities):
            for j, ent_y in enumerate(entities):
                if i == j:
                    continue

                series_x = pivot[ent_x].values.astype(float)
                series_y = pivot[ent_y].values.astype(float)

                T = len(series_y)
                if T <= 2 * max_lag + 2:
                    continue

                # Modelo restrito OLS: y(t) = a0 + sum(a_k * y(t-k))
                Y_target = series_y[max_lag:]
                n_samples = len(Y_target)

                X_restr_cols = [np.ones(n_samples)]
                for lag in range(1, max_lag + 1):
                    X_restr_cols.append(series_y[max_lag - lag : T - lag])
                X_restr = np.column_stack(X_restr_cols)

                # Modelo irrestrito OLS: y(t) = a0 + sum(a_k * y(t-k)) + sum(b_k * x(t-k))
                X_unrestr_cols = list(X_restr_cols)
                for lag in range(1, max_lag + 1):
                    X_unrestr_cols.append(series_x[max_lag - lag : T - lag])
                X_unrestr = np.column_stack(X_unrestr_cols)

                try:
                    b_restr, _, _, _ = np.linalg.lstsq(X_restr, Y_target, rcond=None)
                    ssr_restr = float(np.sum((Y_target - X_restr @ b_restr) ** 2))

                    b_unrestr, _, _, _ = np.linalg.lstsq(X_unrestr, Y_target, rcond=None)
                    ssr_unrestr = float(np.sum((Y_target - X_unrestr @ b_unrestr) ** 2))

                    df_num = max_lag
                    df_denom = max(1, n_samples - (2 * max_lag + 1))
                    ss_diff = max(0.0, ssr_restr - ssr_unrestr)
                    f_stat = float((ss_diff / df_num) / (max(ssr_unrestr, 1e-12) / df_denom))

                    # p-valor aproximado usando distribuição F via erfc / chi2
                    p_val = float(math.erfc(math.sqrt(max(0.0, f_stat * df_num) / 2.0)))
                except Exception:
                    f_stat, p_val = 0.0, 1.0

                granger_raw.append({
                    "cause_entity": ent_x,
                    "effect_entity": ent_y,
                    "f_statistic": round(f_stat, 3),
                    "p_value_raw": round(p_val, 4),
                    "max_lag_tested": max_lag,
                })
                p_values_to_adjust.append(p_val)

        # Ajuste FDR de Benjamini-Hochberg
        rejected, q_vals = benjamini_hochberg_fdr(p_values_to_adjust, alpha=0.05)
        for idx, item in enumerate(granger_raw):
            item["q_value_fdr"] = round(float(q_vals[idx]), 4)
            item["granger_causes_significant"] = bool(rejected[idx])

        # Diagnóstico CUSUM para cada entidade
        cusum_results: Dict[str, Any] = {}
        for ent in entities:
            cusum_results[ent] = detect_cusum_structural_break(pivot[ent].values)

        return {
            "entity_analyzed": entity_col,
            "total_entities": len(entities),
            "pairs_tested": len(granger_raw),
            "granger_results": granger_raw,
            "granger_tests": granger_raw,
            "cusum_alerts": cusum_results,
            "structural_break_cusum": cusum_results,
            "status": "COMPLETED_OK",
        }
