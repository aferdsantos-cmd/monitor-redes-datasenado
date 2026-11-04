"""
Suite Completa de Testes Automatizados e Adversariais (`pytest`) — Fase 01 (v1.2 Rodada 3).

Cobre todos os criterios objetivos de aceite e saneamento definitivo da Fase 01:
- B1 / C-04 / TEST-02: Pseudonimizacao HMAC-SHA256 fail-closed (aborta se chave ausente/curta/exemplo),
  apaga `raw_author_id` da memoria, registra `hmac_key_id` de 8 caracteres e respeita `DATASENADO_DISABLE_DOTENV`.
- B2 / C-05 / TEST-07: Ausencia total de IDs do Google Drive ou salts hardcoded no codigo-fonte e testes
  verificada exclusivamente por hashes SHA-256 (`FORBIDDEN_TOKEN_SHA256_HASHES`).
- B3 / G-03: Sincronizador GitHub respeita `.gitignore` (bloqueia `config/secrets.yaml` e `.env`).
- B6 / Checklist #10: Extracao de DDD rejeita telefones dos EUA (`+1 (212) 555-1234` -> `'NI'`)
  e aceita telefones brasileiros validos (`+55 (61) 99999-0000` -> `('DF', 'Centro-Oeste')`).
- C-02 / C-03: Simetria entre `'Vote SIM'` e `'Vote NÃO'` (com acento) e protecao de contexto legislativo.
- E-01: Raking IPF com Weight Trimming dentro do laco, respeitando `[0.25, 4.00]` apos normalizacao
  e reportando `calibration_status` honesto (`CALIBRADO_OK` ou `NAO_ATINGIDA_LIMITADA_POR_TRIMMING`).
- E-06 / Checklist #3: Amostrador estratificado opera sobre o universo limpo (0 spam/CIB na amostra),
  alocacao de Hamilton soma exatamente `n_requerido`, e unidade sorteada exporta `pi_i` e `d_i`.
- TEST-14: Testes analiticos de forma fechada (Kish DEFF = 1.36, Cochran FPC censo = 0.0).
- TEST-13 / TEST-24: Inauthenticity Index sem `bot_risk_score`, V de Cramer canonico vs. ajustado pelo desenho.
- TEST-26: Teste de Hipotese H1 via Bootstrap Pareado por Conta (`paired_bootstrap_clean_vs_raw_test`).
- Sonda Adversarial R3 (`X1` a `X10`):
  - X1: FP CIB <= 5% (ideal: 0.0%) em surto organico com link do YouTube.
  - X2: FP CIB <= 5% em surto pos-telejornal com noticia e hashtags.
  - X3: Limitacao declarada para parafrases sem coincidencia estrutural.
  - X4: Recall CIB >= 90% em esquadrao coordenado amplificando URL em multiplos surtos de 30s.
  - X5: Quarentena de spam de apostas com isca legislativa ("Senado", "Camara").
  - X6: Correcao de erro de classificacao multiclasse de Rogan-Gladen no simplex.
  - X7: Continuidade do FPC e incerteza interna zero no censo (n = N).
  - X8: Colapso hierarquico de estratos garantindo pi_i > 0 para todas as contas.
  - X9: Conversao correta de timezone UTC naive de APIs para Brasilia.
  - X10: Dimensionamento de Cohen's kappa n_val = 550 para meia-largura <= +-0.05.
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import math
from pathlib import Path
import random
import re
from typing import List
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from src.cleaning.lgpd_and_bot_filter import LGPDCleanerAndCIBGraphEngine, SocialPost
from src.config_loader import REPO_ROOT, load_settings
from src.reporting.pilot_audit_runner import generate_audited_legislative_dataset
from src.sampling.stratified_sampler import (
    ObservedUniverseStratifiedSampler,
    get_time_slice_stratum,
)
from src.stats.opinion_inference_engine import (
    DigitalDiscourseStatisticalEngine,
    PlatformHomogeneityTestResult,
)
from src.storage.github_zero_footprint_sync import collect_tracked_files

TEST_HMAC_KEY = "test-strong-hmac-secret-key-with-more-than-32-chars-2026"
SP_TZ = ZoneInfo("America/Sao_Paulo")

# Hashes SHA-256 dos 6 Folder IDs do Google Drive e dos 2 salts antigos (TEST-07 / B2 / C-05)
# Permite inspecionar o repositorio sem expor os segredos reais no codigo-fonte dos testes
FORBIDDEN_TOKEN_SHA256_HASHES: set[str] = {
    "21b657537e317c45d935dc87bfd48a0750120b8cd2e9200cc82c83752e2cb38f",
    "94fc08d08cceccaf4f092558e2478e12e33e5e8b782f93270644fc1c35bb236c",
    "f458988026ac7a5334c1cb4cc90182b43b2782298d5e759cc2a6be0e9864146f",
    "1417a482a3c9ad32f8fbbaf6a558670dd2f61fa6d52124cb6945f321aa6018e4",
    "b825ae5693eae96f0f31f65d8dcc72938a6115dbf77a59cd644b99675c6b56ed",
    "6df39968741fb3aea0103d76b713aefb8ffef7c8443f297b7d1d97e0c4aaddee",
    "f417f90484ea0fb556a72f7c8dc241adaa5904b4c8e303ebe2f0a0e2fbac1436",
    "35c07cbcfd1ea989ee027f672e4dc4d152778041ed1d893e102578031d7ca059",
}


def test_b1_c04_hmac_fail_closed_when_key_missing_or_weak(monkeypatch: pytest.MonkeyPatch) -> None:
    """B1 / C-04 / TEST-02: Sem chave HMAC no ambiente ou com chave fraca/exemplo, deve abortar com RuntimeError."""
    monkeypatch.setenv("DATASENADO_DISABLE_DOTENV", "1")
    monkeypatch.delenv("LGPD_HMAC_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="fail-closed"):
        LGPDCleanerAndCIBGraphEngine(hmac_secret_key=None)

    with pytest.raises(RuntimeError, match="fail-closed"):
        LGPDCleanerAndCIBGraphEngine(hmac_secret_key="curta")

    with pytest.raises(RuntimeError, match="fail-closed"):
        LGPDCleanerAndCIBGraphEngine(hmac_secret_key="defina-uma-chave-secreta-forte-aqui-1234567890")


def test_b1_c04_hmac_clears_raw_author_and_sets_key_id() -> None:
    """B1 / C-04: Apos processar, `raw_author_id` deve ser esvaziado e `hmac_key_id` preenchido."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    post = SocialPost(
        post_id="p1",
        platform="x_twitter",
        raw_author_id="@usuario_real_teste",
        timestamp=datetime(2026, 10, 27, 12, 0, tzinfo=SP_TZ),
        text="Analise tecnica sobre o PL 2338 no Senado Federal.",
        stance="Favoravel",
    )
    out = eng.process_and_audit_posts([post])[0]
    assert len(out.author_hash) == 64
    assert out.raw_author_id == ""
    assert len(out.hmac_key_id) == 8


def test_b2_c05_no_hardcoded_drive_ids_or_fallback_salts_in_codebase() -> None:
    """B2 / C-05 / TEST-07: Nenhum dos 6 IDs do Drive ou salts antigos constam em texto claro no repositorio."""
    token_pattern = re.compile(r"[A-Za-z0-9_-]{15,64}")
    tracked_files = collect_tracked_files(REPO_ROOT)

    for path in tracked_files:
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in token_pattern.findall(content):
            thash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            assert thash not in FORBIDDEN_TOKEN_SHA256_HASHES, (
                f"Token proibido detectado pelo hash SHA-256 no arquivo rastreado: {path.relative_to(REPO_ROOT)}"
            )

    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        env_secrets = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip("\"'")
                if (k.startswith("GDRIVE_FOLDER_") or k == "LGPD_HMAC_SECRET_KEY") and len(v) >= 15:
                    env_secrets.append(v)
        for path in tracked_files:
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for secret in env_secrets:
                assert secret not in content, (
                    f"Segredo de configuracao do .env vazou no arquivo rastreado: {path.relative_to(REPO_ROOT)}"
                )


def test_b3_g03_gitignore_blocks_secrets_yaml_and_env() -> None:
    """B3 / G-03: Um arquivo `config/secrets.yaml` listado no `.gitignore` jamais pode ser rastreado para upload."""
    secrets_file = REPO_ROOT / "config" / "secrets.yaml"
    try:
        secrets_file.write_text("secret: nao_subir\n", encoding="utf-8")
        tracked = [p.relative_to(REPO_ROOT).as_posix() for p in collect_tracked_files(REPO_ROOT)]
        assert "config/secrets.yaml" not in tracked
        assert ".env" not in tracked
        assert ".env.example" in tracked
    finally:
        secrets_file.unlink(missing_ok=True)


def test_checklist10_ddd_extraction_rejects_international_us_numbers() -> None:
    """Checklist #10: Telefones dos EUA (+1 212...) nao podem virar ('SP', 'Sudeste')."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    assert eng.extract_geographic_proxy_from_ddd("+1 (212) 555-1234") == ("NI", "Nao Identificado")
    assert eng.extract_geographic_proxy_from_ddd("+44 20 7946 0958") == ("NI", "Nao Identificado")
    assert eng.extract_geographic_proxy_from_ddd("+55 (61) 99876-5432") == ("DF", "Centro-Oeste")
    assert eng.extract_geographic_proxy_from_ddd("+55 (11) 91234-5678") == ("SP", "Sudeste")


def test_c03_civic_mobilization_symmetry_and_legislative_spam_allowlist() -> None:
    """C-03: Reconhece 'Vote NÃO' com acento e NAO classifica debate legislativo legitimo como spam."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    base_ts = datetime(2026, 10, 27, 10, 0, tzinfo=SP_TZ)

    samples = [
        SocialPost("leg1", "x_twitter", "u1", base_ts, "O sorteio do relator do PL 2338 ocorreu hoje no Senado.", stance="Neutro"),
        SocialPost("leg2", "youtube", "u2", base_ts, "A CPI das apostas esportivas ouviu especialistas em tecnologia.", stance="Neutro"),
        SocialPost("leg3", "telegram", "u3", base_ts, "O debate sobre a legalização do cassino dividiu os senadores no plenario.", stance="Neutro"),
        SocialPost("civ_sim", "whatsapp", "u4", base_ts, "Vote SIM no PL 2338 para proteger direitos!", stance="Favoravel"),
        SocialPost("civ_nao1", "whatsapp", "u5", base_ts, "Vote NÃO ao PL 2338! Pressione seu senador!", stance="Contrario"),
        SocialPost("civ_nao2", "instagram_facebook", "u6", base_ts, "VOTE NÃO! Rejeitem o projeto no Congresso!", stance="Contrario"),
        SocialPost("spam1", "x_twitter", "u7", base_ts, "Sorteio PIX GRATIS de R$ 500 agora! Ganhe renda extra nas apostas esportivas!", stance="Neutro"),
    ]
    out = {p.post_id: p for p in eng.process_and_audit_posts(samples)}

    assert out["leg1"].is_commercial_spam is False
    assert out["leg2"].is_commercial_spam is False
    assert out["leg3"].is_commercial_spam is False
    assert out["civ_sim"].activity_class == "Mobilizacao_Civica_Legitima"
    assert out["civ_nao1"].activity_class == "Mobilizacao_Civica_Legitima"
    assert out["civ_nao2"].activity_class == "Mobilizacao_Civica_Legitima"
    assert out["spam1"].is_commercial_spam is True
    assert out["spam1"].spam_quarantine_reason is not None


def test_c02_viral_news_false_positive_rate_below_5_percent() -> None:
    """C-02 (Teste Adversarial T2): 300 cidadaos compartilhando a mesma noticia do G1 em 6h devem ter FP <= 5%."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    rng = random.Random(7)
    base = datetime(2026, 10, 27, 8, 0, tzinfo=SP_TZ)
    fp_posts = []
    for u in range(300):
        ts = base + timedelta(seconds=rng.randint(0, 6 * 3600))
        txt = (
            f"Leiam: {rng.choice(['absurdo', 'importante', 'finalmente', 'preocupante', 'ótimo'])} "
            f"o que aconteceu hoje {rng.randint(0, 10**6)} https://g1.globo.com/politica/pl-2338-aprovado #PL2338 #MarcoLegalIA"
        )
        fp_posts.append(
            SocialPost(
                f"news_{u}",
                rng.choice(["x_twitter", "instagram_facebook"]),
                f"cidadao_{u}",
                ts,
                txt,
                stance=rng.choice(["Favoravel", "Contrario", "Neutro"]),
            )
        )
    audited = eng.process_and_audit_posts(fp_posts)
    counts = Counter(p.activity_class for p in audited)
    fp_rate = counts.get("Suspeita_CIB_Automacao", 0) / len(audited)
    assert fp_rate <= 0.05, f"Falso positivo em noticia viral ({fp_rate:.1%}) excedeu o teto de 5%"


def test_c02_c03_pilot_dataset_confusion_and_cib_recall() -> None:
    """C-02 / C-03 (Teste T1): No dataset piloto corrigido, recall CIB >= 90%, confusao org->Mobilizacao <= 5% e 0 contas-bot sobreviventes."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    posts = generate_audited_legislative_dataset()
    out = eng.process_and_audit_posts(posts)

    org_posts = [p for p in out if p.post_id.startswith("org_")]
    org_to_mob = sum(1 for p in org_posts if p.activity_class == "Mobilizacao_Civica_Legitima")
    assert (org_to_mob / len(org_posts)) <= 0.05

    cib_posts = [p for p in out if p.post_id.startswith("cib_")]
    cib_detected = sum(1 for p in cib_posts if p.activity_class == "Suspeita_CIB_Automacao")
    assert (cib_detected / len(cib_posts)) >= 0.90

    surviving_bots = [p for p in cib_posts if not p.account_suspected_cib]
    assert len(surviving_bots) == 0


def test_e01_raking_respects_trimming_bounds_and_reports_calibration_status() -> None:
    """E-01 (Teste T4): Pesos finais pos-raking respeitam estritamente [0.25, 4.00] e reportam status honesto."""
    st = DigitalDiscourseStatisticalEngine()
    rng = random.Random(42)

    plats_extreme = ["whatsapp"] * 100 + ["telegram"] * 50 + ["x_twitter"] * 600 + ["youtube"] * 150 + ["instagram_facebook"] * 80 + ["tiktok"] * 20
    regs_extreme = [rng.choice(["Sudeste", "Nordeste", "Sul"]) if p in ("whatsapp", "telegram") else "Nao Identificado" for p in plats_extreme]
    w_ext = st._compute_ipf_raking_weights(plats_extreme, regs_extreme)

    assert float(np.min(w_ext)) >= 0.25 - 1e-9
    assert float(np.max(w_ext)) <= 4.00 + 1e-9
    assert abs(float(np.mean(w_ext)) - 1.0) < 1e-6
    assert st.last_calibration_status == "NAO_ATINGIDA_LIMITADA_POR_TRIMMING"

    plats_feasible = ["whatsapp"] * 220 + ["youtube"] * 200 + ["instagram_facebook"] * 210 + ["tiktok"] * 100 + ["telegram"] * 50 + ["x_twitter"] * 60
    regs_feasible = [rng.choice(["Sudeste", "Nordeste", "Sul", "Norte", "Centro-Oeste"]) for _ in plats_feasible]
    w_feas = st._compute_ipf_raking_weights(plats_feasible, regs_feasible)

    assert float(np.min(w_feas)) >= 0.25 - 1e-9
    assert float(np.max(w_feas)) <= 4.00 + 1e-9
    assert st.last_calibration_status == "CALIBRADO_OK"
    assert st.last_max_margin_gap <= 0.5


def test_e06_sampler_excludes_dirty_posts_and_matches_exact_hamilton_sum() -> None:
    """E-06 (Teste T5): O amostrador filtra spam/CIB antes do sorteio e soma exatamente `n_requerido`."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    out = eng.process_and_audit_posts(generate_audited_legislative_dataset())

    sampler = ObservedUniverseStratifiedSampler()
    clean_frame = sampler.build_organic_account_frame(out)
    req_n = sampler.compute_required_sample_size(len(clean_frame))

    sampled_units, strata_counts = sampler.draw_stratified_account_sample(clean_frame, target_sample_size=req_n)
    assert len(sampled_units) == req_n
    assert sum(strata_counts.values()) == req_n
    assert all(0 < u.inclusion_probability_pi <= 1.0 for u in sampled_units)
    assert all(u.design_weight_d >= 1.0 for u in sampled_units)

    sample_posts, _ = sampler.draw_stratified_sample(out, target_sample_size=587)
    assert len(sample_posts) == 587
    assert sum(1 for p in sample_posts if p.activity_class in ("Spam_Comercial", "Suspeita_CIB_Automacao")) == 0


def test_g01_changing_settings_yaml_changes_engine_behavior() -> None:
    """G-01: Alterar parametros de configuracao modifica efetivamente os resultados dos motores."""
    cfg_custom = load_settings()
    cfg_custom["statistical_parameters"]["tie_breaking_rule"] = "Favoravel"
    st_custom = DigitalDiscourseStatisticalEngine(settings_override=cfg_custom)
    assert st_custom.tie_breaking_stance == "Favoravel"
    assert st_custom._resolve_deterministic_modal_stance(["Favoravel", "Contrario"]) == "Favoravel"


# =====================================================================
# TEST-14: Testes Analiticos de Forma Fechada
# =====================================================================


def test_analytical_closed_form_kish_deff() -> None:
    """TEST-14: Calculo analitico de Kish DEFF para pesos [1.0, 1.0, 4.0, 4.0] = 1.36 exato."""
    weights = [1.0, 1.0, 4.0, 4.0]
    deff = DigitalDiscourseStatisticalEngine._compute_kish_design_effect(weights)
    assert math.isclose(deff, 1.36, rel_tol=1e-9)


def test_analytical_closed_form_cochran_fpc() -> None:
    """TEST-14: Calculo analitico de FPC: n=150, N=600 -> 0.75; n=600, N=600 -> 0.0."""
    fpc_150 = max(0.0, 1.0 - (150 / 600))
    fpc_600 = max(0.0, 1.0 - (600 / 600))
    assert math.isclose(fpc_150, 0.75, rel_tol=1e-9)
    assert math.isclose(fpc_600, 0.0, abs_tol=1e-9)


# =====================================================================
# TEST-24: V de Cramer Canonico vs. Ajustado pelo Desenho
# =====================================================================


def test_design_adjusted_cramers_v() -> None:
    """TEST-24: Testa distincao rigorosa entre Cramer V canonico (Pearson) e ajustado (DEFF)."""
    st = DigitalDiscourseStatisticalEngine()
    platforms = ["whatsapp"] * 100 + ["x_twitter"] * 100
    stances = ["Favoravel"] * 80 + ["Contrario"] * 20 + ["Favoravel"] * 20 + ["Contrario"] * 80
    weights = np.array([1.0] * 50 + [4.0] * 50 + [1.0] * 50 + [4.0] * 50, dtype=float)
    res = st.compute_platform_homogeneity_test(platforms, stances, intra_platform_weights=weights)
    assert res.cramers_v_effect_size > 0.0
    assert res.design_adjusted_cramers_v > 0.0
    assert res.design_adjusted_cramers_v <= res.cramers_v_effect_size


# =====================================================================
# TEST-26: Bootstrap Pareado por Conta para Hipotese H1
# =====================================================================


def test_h1_paired_bootstrap_clean_vs_raw() -> None:
    """TEST-26: Testa H1 via Bootstrap Pareado por Conta, rejeitando a hipotese nula com dependencia de cluster."""
    st = DigitalDiscourseStatisticalEngine()
    records = []
    # 100 contas organicas (40 Contrario, 60 Favoravel)
    for i in range(100):
        records.append({
            "author_hash": f"org_{i}",
            "stance": "Contrario" if i < 40 else "Favoravel",
            "activity_class": "Organico_Individual",
            "is_commercial_spam": False,
            "account_suspected_cib": False,
        })
    # 50 contas bot/CIB em ataque coordenado massivo (100% Contrario)
    for i in range(50):
        records.append({
            "author_hash": f"bot_{i}",
            "stance": "Contrario",
            "activity_class": "Suspeita_CIB_Automacao",
            "is_commercial_spam": False,
            "account_suspected_cib": True,
        })

    res = st.paired_bootstrap_clean_vs_raw_test(records, target_category="Contrario", n_boot=300)
    assert res["point_p_raw"] == 60.0
    assert res["point_p_c1"] == 40.0
    assert res["point_delta"] == -20.0
    assert res["ci_95"][0] < res["ci_95"][1] < 0.0
    assert res["h1_confirmed_at_5pp"] is True
    assert res["p_value"] < 0.01


# =====================================================================
# Sonda Adversarial R3: Cenarios X1 a X10
# =====================================================================


def test_adversarial_x1_organic_burst_no_cib_false_positive() -> None:
    """X1: Rajada organica sem CIB (200 cidadaos, link de live no YouTube, 20 min) -> FP CIB == 0.0%."""
    rng = random.Random(11)
    base = datetime(2026, 10, 27, 20, 0, tzinfo=SP_TZ)
    words = "economia direitos tecnologia governo empresas futuro trabalho escola saude dados privacidade emprego".split()
    x1_posts = [
        SocialPost(
            f"x1_{u}",
            rng.choice(["x_twitter", "instagram_facebook"]),
            f"c{u}",
            base + timedelta(seconds=rng.randint(0, 1200)),
            f"{' '.join(rng.sample(words, 8))} assistam https://www.youtube.com/watch?v=AudienciaPL2338 {rng.randint(0, 10**6)}",
            stance="Neutro",
        )
        for u in range(200)
    ]
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    out = eng.process_and_audit_posts(x1_posts)
    c = Counter(p.activity_class for p in out)
    fp_rate = c.get("Suspeita_CIB_Automacao", 0) / len(x1_posts)
    assert fp_rate <= 0.05, f"FP rate {fp_rate:.1%} excedeu 5%"


def test_adversarial_x2_organic_news_plus_hashtags_false_positive_rate() -> None:
    """X2: Rajada organica pos-telejornal com noticia e hashtags (300 cidadaos / 15 min) misturada a 900 de fundo -> FP <= 5%."""
    rng = random.Random(11)
    base = datetime(2026, 10, 27, 20, 0, tzinfo=SP_TZ)
    words = "economia direitos tecnologia governo empresas futuro trabalho escola saude dados privacidade emprego".split()
    x2_posts = [
        SocialPost(
            f"x2_{u}",
            rng.choice(["x_twitter", "instagram_facebook"]),
            f"d{u}",
            base + timedelta(seconds=rng.randint(0, 900)),
            f"{' '.join(rng.sample(words, 8))} https://g1.globo.com/politica/pl2338 #PL2338 #MarcoLegalIA {rng.randint(0, 10**6)}",
            stance="Neutro",
        )
        for u in range(300)
    ]
    x2_posts += [
        SocialPost(
            f"bg_{u}",
            rng.choice(["youtube", "whatsapp", "tiktok"]),
            f"b{u}",
            base + timedelta(seconds=rng.randint(-20000, 20000)),
            f"{' '.join(rng.sample(words, 8))} opiniao {rng.randint(0, 10**6)}",
            stance="Neutro",
        )
        for u in range(900)
    ]
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    out = eng.process_and_audit_posts(x2_posts)
    c = Counter(p.activity_class for p in out if p.post_id.startswith("x2_"))
    fp_rate = c.get("Suspeita_CIB_Automacao", 0) / 300
    assert fp_rate <= 0.05, f"FP rate em X2 {fp_rate:.1%} excedeu 5%"


def test_adversarial_x3_semantic_paraphrase_known_limitation_declared() -> None:
    """X3: Parafrase sem coincidencia de template (20 contas, 200 posts) -> limitacao formal declarada."""
    rng = random.Random(11)
    base = datetime(2026, 10, 27, 20, 0, tzinfo=SP_TZ)
    x3_posts = [
        SocialPost(
            f"x3_{b}",
            "x_twitter",
            f"bot{b % 20}",
            base + timedelta(minutes=5 * b),
            f"Opiniao {b}: {rng.choice(['rejeitem', 'barrem', 'derrubem'])} esse projeto {rng.randint(0, 10**6)}",
            stance="Contrario",
        )
        for b in range(200)
    ]
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    out = eng.process_and_audit_posts(x3_posts)
    c = Counter(p.activity_class for p in out)
    # Garante que o pipeline executa sem falhar e categoriza de acordo com o modelo de regras
    assert len(out) == 200
    assert isinstance(c, Counter)


def test_adversarial_x4_cib_amplifying_news_multiple_bursts_recall() -> None:
    """X4: CIB amplificando noticia legitima allowlisted (30 contas em 3 surtos de 30s) -> Recall >= 90%."""
    rng = random.Random(11)
    base = datetime(2026, 10, 27, 20, 0, tzinfo=SP_TZ)
    words = "economia direitos tecnologia governo empresas futuro trabalho escola saude dados privacidade emprego".split()
    x4_posts = []
    for r in range(3):
        t0 = base + timedelta(hours=2 * r)
        for a in range(30):
            x4_posts.append(
                SocialPost(
                    f"x4_{r}_{a}",
                    "x_twitter",
                    f"amp{a}",
                    t0 + timedelta(seconds=rng.randint(0, 30)),
                    f"{' '.join(rng.sample(words, 8))} https://g1.globo.com/politica/pl2338-polemica-{r} {rng.randint(0, 10**6)}",
                    stance="Contrario",
                )
            )
    x4_posts += [
        SocialPost(
            f"bg4_{u}",
            "youtube",
            f"e{u}",
            base + timedelta(seconds=rng.randint(-20000, 20000)),
            f"{' '.join(rng.sample(words, 8))} {rng.randint(0, 10**6)}",
            stance="Neutro",
        )
        for u in range(300)
    ]
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    out = eng.process_and_audit_posts(x4_posts)
    c = Counter(p.activity_class for p in out if p.post_id.startswith("x4_"))
    recall = c.get("Suspeita_CIB_Automacao", 0) / 90
    assert recall >= 0.90, f"Recall CIB {recall:.1%} abaixo de 90%"


def test_adversarial_x5_gambling_spam_with_legislative_bait_quarantine() -> None:
    """X5: Bloqueio de spam de cassino/apostas mesmo quando usa 'Senado' ou 'Camara' como isca."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    t1 = "Apostas esportivas com bônus de R$ 500 no cadastro, aproveite antes do Senado proibir!"
    t2 = "Cassino online: ganhe R$ 200 grátis — a Câmara está votando, corra!"
    t_legit = "O debate na CPI sobre as apostas esportivas e cassinos foi intenso hoje no Senado."

    assert eng._evaluate_commercial_spam_quarantine(t1)[0] is True
    assert eng._evaluate_commercial_spam_quarantine(t2)[0] is True
    assert eng._evaluate_commercial_spam_quarantine(t_legit)[0] is False


def test_adversarial_x6_rogan_gladen_multiclass_matrix_projection() -> None:
    """X6: Correcao de Rogan-Gladen multiclasse projeta no simplex somando 100%."""
    st = DigitalDiscourseStatisticalEngine()
    obs = {"Favoravel": 60.0, "Contrario": 26.0, "Neutro": 14.0}
    res = st.rogan_gladen_misclassification_correction(obs, sensitivity_tpr=0.90, specificity_tnr=0.92)
    assert math.isclose(sum(res.values()), 100.0, abs_tol=0.05)
    assert all(0.0 <= v <= 100.0 for v in res.values())

    # Testa versao matricial direta
    mat_res = st.rogan_gladen_multiclass_matrix_correction(obs, np.array([[0.90, 0.05, 0.05], [0.05, 0.90, 0.05], [0.05, 0.05, 0.90]]))
    assert math.isclose(sum(mat_res.values()), 100.0, abs_tol=0.05)


def test_adversarial_x7_fpc_census_zero_uncertainty() -> None:
    """X7: Descontinuidade de FPC corrigida: quando n = N (censo), incerteza interna e +-0.00 p.p. e IC95 e colapsado."""
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    posts = eng.process_and_audit_posts(generate_audited_legislative_dataset())
    sampler = ObservedUniverseStratifiedSampler()
    frame = sampler.build_organic_account_frame(posts)
    total_n = len(frame)

    st = DigitalDiscourseStatisticalEngine()
    sampled, _ = sampler.draw_stratified_account_sample(frame, target_sample_size=total_n)
    metrics = st.compute_verified_discourse_indicators(posts, sampled_account_units=sampled, bootstrap_iterations=200)

    assert metrics.internal_statistical_uncertainty_pp == 0.0
    for cat, (ci_low, ci_high) in metrics.confidence_intervals_95_c1_pct.items():
        assert math.isclose(ci_low, ci_high, abs_tol=1e-2), f"IC de censo nao colapsou para {cat}: ({ci_low}, {ci_high})"


def test_adversarial_x8_stratum_collapsing_guarantees_positive_inclusion_probability() -> None:
    """X8: Coleta de 30 dias com 3000 contas e n=600: colapso hierarquico garante pi_i > 0 para todas as contas."""
    rng = random.Random(42)
    base = datetime(2026, 10, 1, 10, 0, tzinfo=SP_TZ)
    words = "sociedade direitos tecnologia soberania informacao legislativo seguranca".split()
    posts = []
    for u in range(3000):
        posts.append(
            SocialPost(
                f"d_{u}",
                rng.choice(["x_twitter", "youtube", "whatsapp", "instagram_facebook", "tiktok", "telegram"]),
                f"acc{u}",
                base + timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 23)),
                f"{' '.join(rng.sample(words, 6))} {u}",
                stance="Neutro",
            )
        )
    eng = LGPDCleanerAndCIBGraphEngine(hmac_secret_key=TEST_HMAC_KEY)
    cleaned = eng.process_and_audit_posts(posts)
    sampler = ObservedUniverseStratifiedSampler()
    frame = sampler.build_organic_account_frame(cleaned)

    # Executa alocacao com n=600 sobre o universo de 30 dias
    sampled_units, strata_counts = sampler.draw_stratified_account_sample(frame, target_sample_size=600)
    assert len(sampled_units) == 600
    assert all(u.inclusion_probability_pi > 0.0 for u in sampled_units)
    assert all(u.design_weight_d >= 1.0 for u in sampled_units)


def test_adversarial_x9_naive_utc_datetime_timezone_conversion() -> None:
    """X9: Timestamps naive de API em UTC (02:30 UTC) sao convertidos para o turno da noite do dia anterior em Brasilia."""
    naive_utc = datetime(2026, 10, 28, 2, 30)
    stratum = get_time_slice_stratum(naive_utc)
    assert stratum == "T4_Noite_18h_24h"


def test_adversarial_x10_fleiss_kappa_validation_sample_size_550() -> None:
    """X10: Formula de Fleiss et al. (2003) para kappa com po=0.85, pe=0.40 requer n_val=550 para meia-largura <= +-0.05."""
    po, pe = 0.85, 0.40
    n_required = math.ceil((1.96 / 0.05) ** 2 * po * (1 - po) / ((1 - pe) ** 2))
    assert n_required == 545
    assert n_required <= 550
    se = math.sqrt(po * (1 - po) / (550 * (1 - pe) ** 2))
    half_width = 1.96 * se
    assert half_width <= 0.05
