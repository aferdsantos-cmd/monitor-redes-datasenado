"""
Suite Completa de Testes Automatizados e Adversariais (`pytest`) — Fase 01 (v1.2).

Cobre todos os criterios objetivos de aceite da 2a Rodada de Auditoria Cientifica:
- B1 / C-04: Pseudonimizacao HMAC-SHA256 *fail-closed* (aborta se chave ausente/curta/exemplo),
  apaga `raw_author_id` da memoria e registra `hmac_key_id` de 8 caracteres.
- B2 / C-05: Ausencia total de IDs do Google Drive ou salts hardcoded no codigo-fonte (`src/` e `config/`).
- B3 / G-03: Sincronizador GitHub respeita `.gitignore` (bloqueia `config/secrets.yaml` e `.env`).
- B6 / Checklist #10: Extracao de DDD rejeita telefones dos EUA (`+1 (212) 555-1234` -> `'NI'`)
  e aceita telefones brasileiros validos (`+55 (61) 99999-0000` -> `('DF', 'Centro-Oeste')`).
- C-02: Suite adversarial T2 (300 cidadaos compartilhando noticia viral do G1 ao longo de 6h -> FP <= 5%)
  e T1 (copypasta/URL sincronizada de CIB -> recall >= 90%).
- C-03: Simetria entre `'Vote SIM'` e `'Vote NÃO'` (com acento) e protecao de contexto legislativo
  (`'O sorteio do relator do PL 2338'`, `'CPI das apostas esportivas'`, `'legalização do cassino'` -> `is_commercial_spam == False`),
  alem de confusao `org -> Mobilizacao_Civica_Legitima <= 5%` no piloto.
- E-01: Raking IPF com *Weight Trimming* dentro do laco, respeitando `[0.25, 4.00]` apos normalizacao
  e reportando `calibration_status` honesto (`CALIBRADO_OK` quando factivel, `NAO_ATINGIDA_LIMITADA_POR_TRIMMING` quando limitado).
- E-06 / Checklist #3: Amostrador estratificado opera sobre o universo limpo (0 spam/CIB na amostra),
  alocacao de Hamilton soma exatamente `n_requerido`, e unidade sorteada exporta `pi_i` e `d_i`.
- G-01: Alterar parametros no `settings.yaml` altera efetivamente o comportamento dos motores.
"""

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import random
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from src.cleaning.lgpd_and_bot_filter import LGPDCleanerAndCIBGraphEngine, SocialPost
from src.config_loader import REPO_ROOT, load_settings
from src.reporting.pilot_audit_runner import generate_audited_legislative_dataset
from src.sampling.stratified_sampler import ObservedUniverseStratifiedSampler
from src.stats.opinion_inference_engine import DigitalDiscourseStatisticalEngine
from src.storage.github_zero_footprint_sync import collect_tracked_files

TEST_HMAC_KEY = "test-strong-hmac-secret-key-with-more-than-32-chars-2026"


def test_b1_c04_hmac_fail_closed_when_key_missing_or_weak(monkeypatch: pytest.MonkeyPatch) -> None:
    """B1 / C-04: Sem chave HMAC no ambiente ou com chave fraca/exemplo, deve abortar com RuntimeError."""
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
        timestamp=datetime(2026, 10, 27, 12, 0, tzinfo=ZoneInfo("America/Sao_Paulo")),
        text="Analise tecnica sobre o PL 2338 no Senado Federal.",
        stance="Favoravel",
    )
    out = eng.process_and_audit_posts([post])[0]
    assert len(out.author_hash) == 64
    assert out.raw_author_id == ""
    assert len(out.hmac_key_id) == 8


def test_b2_c05_no_hardcoded_drive_ids_or_fallback_salts_in_codebase() -> None:
    """B2 / C-05: Nenhum dos 6 IDs de pastas do Google Drive nem o salt antigo podem constar no codigo."""
    forbidden_strings = [
        "1htCbTOKPsyO6BLm1bhLCIKGuWvHJrlnN",
        "1vvgdof3KtMWCRh2EfViJS45Tto1GyEX4",
        "1EheWEcKtnWanMTjG1BRLyGIAQJHdkS_-",
        "1r4KYa94iHCwgHvLl9gaYS2d9iq6UEx33",
        "1jYfPQUHpHXOG5Oqj9ByoUjnS_GM1sw-L",
        "1Wx7IHFQA7enQrAOQEfJF2JNgDNCp2aIc",
        "default-fallback-dev-key-change-in-env",
        "datasenado-tcc-lgpd-2026",
    ]
    for folder in ("src", "config", "docs"):
        for path in (REPO_ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".yaml", ".md"}:
                content = path.read_text(encoding="utf-8")
                for forbidden in forbidden_strings:
                    assert forbidden not in content, f"String proibida '{forbidden}' encontrada em {path}"


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
    base_ts = datetime(2026, 10, 27, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

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
    base = datetime(2026, 10, 27, 8, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
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

    # Caso 1: Desbalanceamento extremo (X=60% da amostra para alvo de 4% -> matematicamente bloqueado pelo trimming 0.25)
    plats_extreme = ["whatsapp"] * 100 + ["telegram"] * 50 + ["x_twitter"] * 600 + ["youtube"] * 150 + ["instagram_facebook"] * 80 + ["tiktok"] * 20
    regs_extreme = [rng.choice(["Sudeste", "Nordeste", "Sul"]) if p in ("whatsapp", "telegram") else "Nao Identificado" for p in plats_extreme]
    w_ext = st._compute_ipf_raking_weights(plats_extreme, regs_extreme)

    assert float(np.min(w_ext)) >= 0.25 - 1e-9
    assert float(np.max(w_ext)) <= 4.00 + 1e-9
    assert abs(float(np.mean(w_ext)) - 1.0) < 1e-6
    assert st.last_calibration_status == "NAO_ATINGIDA_LIMITADA_POR_TRIMMING"

    # Caso 2: Desbalanceamento moderado factivel dentro dos limites [0.25, 4.00]
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

    # Verifica tambem o metodo retrocompativel `draw_stratified_sample`
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
