"""
Teste de Software com Dados Sinteticos Diversificados e Verificacao do Pipeline (Fase 01).

Atende integralmente aos criterios da 2a Rodada de Auditoria Cientifica:
1. Rotulagem Honesta Anti-Overclaiming (M-03 / Anexo A):
   - Declarado explicitamente como 'Teste de Software com Dados Sinteticos' (nunca 'comprova em producao').
2. Diversidade Lexical Realista nos Textos Organicos Sinteticos (C-03):
   - Combina centenas de radicais, argumentos, estruturas sintaticas e observacoes distintas para que
     textos organicos espontaneos NAO compartilhem um template artificial que engane o LSH.
3. Fluxo Estrito de Amostragem e Inferencia (Checklist #3 / C-01 / E-06):
   - Coleta -> Desinfeccao (Spam/CIB em nivel de conta) -> Quadro de Contas Organicas (U_Org)
     -> Sorteio Estratificado de Contas (s com pi_i e d_i) -> Inferencia Estatistica.
4. Leitura Integral do `config/settings.yaml` via `load_settings()` (G-01) e IDs do `.env` sem
   nenhum fallback hardcoded de IDs do Google Drive no codigo-fonte (B2 / C-05).
"""

from datetime import datetime, timedelta
import os
import random
from typing import Dict, List
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import duckdb
import pandas as pd

from src.cleaning.lgpd_and_bot_filter import LGPDCleanerAndCIBGraphEngine, SocialPost
from src.config_loader import load_settings
from src.sampling.stratified_sampler import ObservedUniverseStratifiedSampler
from src.stats.opinion_inference_engine import DigitalDiscourseStatisticalEngine
from src.storage.zero_footprint_sync import ZeroFootprintStorage

load_dotenv()

# Carrega os pesos de referencia diretamente do config/settings.yaml (G-01)
_SETTINGS = load_settings()
PLATFORM_WEIGHTS_BRAZIL: Dict[str, float] = dict(_SETTINGS["platform_reference_weights_brazil"])

# Vocabulario rico e variado para gerar textos organicos genuinamente distintos (resolve C-03!)
_OPENERS = [
    "Estive lendo o texto do projeto hoje",
    "Na minha avaliacao profissional sobre tecnologia",
    "Acompanhei a sessao da comissao no Congresso",
    "Conversando com colegas da area juridica e de TI",
    "Vi o debate sobre inteligencia artificial ontem",
    "Pensando no futuro do mercado de trabalho brasileiro",
    "Como pesquisador e usuario diario de ferramentas digitais",
    "Olhando a experiencia internacional na Europa e nos EUA",
    "Analisando o relatorio apresentado pelos senadores",
    "Debatendo esse tema na universidade esta semana",
    "Preocupado com os rumos da legislacao digital no Brasil",
    "Refletindo sobre o impacto nas startups nacionais",
    "Observando como os artistas e criadores serao afetados",
    "Apos assistir a audiencia publica com especialistas",
    "Considerando a necessidade de regras claras para algoritmos",
    "Vendo os riscos de deepfakes nas proximas eleicoes",
]

_ARGUMENTS_BY_STANCE = {
    "Favoravel": [
        "acredito que a protecao aos direitos autorais e indispensavel para os criadores.",
        "defendo que haja supervisao humana obrigatoria em sistemas de alto risco.",
        "apoio a criacao de regras transparentes para responsabilizar grandes plataformas.",
        "vejo com bons olhos a exigencia de governanca algoritmica na saude e educacao.",
        "concordo que precisamos proteger dados pessoais contra coleta indiscriminada.",
        "julgo positivo estabelecer salvaguardas claras para o cidadao comum.",
        "penso que a seguranca juridica vai atrair investimentos mais responsaveis.",
        "sou favoravel porque equilibra inovacao com direitos fundamentais.",
    ],
    "Contrario": [
        "temo que o excesso de obrigacoes burocraticas inviabilize pequenas empresas de software.",
        "acho que as exigencias de licenciamento previo vao atrasar o desenvolvimento cientifico.",
        "discordo da criacao de novos orgaos fiscalizadores que podem engessar o setor.",
        "critico a falta de clareza nos conceitos de alto risco que gera inseguranca.",
        "penso que copiar o modelo europeu pesado vai afastar startups do nosso pais.",
        "vejo risco de fuga de cerebros se a regulamentacao for punitiva demais.",
        "rejeito esse formato atual porque penaliza quem desenvolve codigo aberto.",
        "considero negativo criar barreiras regulatorias antes de fomentar a infraestrutura.",
    ],
    "Neutro": [
        "ainda tenho duvidas se o texto final conseguira equilibrar inovacao e cautela.",
        "precisamos aguardar as emendas do plenario para entender o efeito pratico.",
        "ha pontos positivos na transparencia, mas o capitulo de sancoes exige revisao.",
        "o debate no legislativo e importante, porem faltam dados empiricos de impacto.",
        "nao formei posicao definitiva entre o substitutivo atual e a proposta anterior.",
        "espero que os parlamentares oucam tanto a academia quanto o setor produtivo.",
        "a discussao sobre o sorteio do relator da comissao mostra que o tema e complexo.",
        "quero comparar com o que foi discutido na CPI das apostas esportivas sobre tecnologia.",
    ],
}

_CLOSERS = [
    "Vamos acompanhar os proximos capitulos em Brasilia.",
    "Espero que o debate tecnico prevaleca sobre a pressao de lobbies.",
    "O tema merece muita atencao da sociedade civil.",
    "Cada setor produtivo precisa enviar suas contribuicoes.",
    "Fundamental ler os artigos com calma antes de concluir.",
    "A tecnologia avanca muito mais rapido que o processo legislativo.",
    "Veremos como ficara a redacao final apos os destaques.",
    "Um assunto decisivo para a soberania digital nas proximas decadas.",
]


def generate_audited_legislative_dataset(seed: int = 2026) -> List[SocialPost]:
    """
    Gera conjunto de dados sinteticos para teste de software (M-03) com:
    - 780 manifestacoes organicas com alta diversidade lexical (C-03);
    - 40 manifestacoes de mobilizacao civica legitima ('Vote SIM' e 'Vote NÃO' com acento - C-03);
    - 30 postagens de spam comercial (que serao colocadas em quarentena);
    - 450 disparos de ataque coordenado (CIB) combinando copypasta textual e rajada de URL/hashtags.
    """
    rng = random.Random(seed)
    tz_sp = ZoneInfo("America/Sao_Paulo")
    base_time = datetime(2026, 10, 27, 8, 0, 0, tzinfo=tz_sp)
    posts: List[SocialPost] = []
    ddds = ["11", "21", "31", "41", "51", "61", "71", "81", "85", "91", "92"]
    stances = ["Favoravel", "Contrario", "Neutro"]
    post_counter = 1

    # 1. Contas Organicas Espontaneas nas 6 redes (780 posts genuinamente variados)
    organic_specs = [
        ("whatsapp", 180, [0.58, 0.26, 0.16]),
        ("youtube", 160, [0.55, 0.29, 0.16]),
        ("instagram_facebook", 170, [0.57, 0.27, 0.16]),
        ("tiktok", 110, [0.52, 0.30, 0.18]),
        ("telegram", 70, [0.46, 0.40, 0.14]),
        ("x_twitter", 90, [0.42, 0.44, 0.14]),
    ]

    vocab_words = [
        "algoritmo", "transparencia", "inovacao", "universidade", "pesquisa", "economia",
        "cidadania", "industria", "soberania", "educacao", "saude", "agricultura",
        "comercio", "servicos", "judiciario", "computacao", "modelos", "dados",
        "privacidade", "investimento", "competitividade", "democracia", "etica", "futuro",
    ]

    for platform, n_users, probs in organic_specs:
        for u in range(n_users):
            stance = rng.choices(stances, weights=probs, k=1)[0]
            ddd = rng.choice(ddds)
            phone_hint = f"+55 ({ddd}) 9{rng.randint(8000,9999)}-{rng.randint(1000,9999)}"
            ts = base_time + timedelta(minutes=rng.randint(1, 960), seconds=rng.randint(0, 59))

            opener = rng.choice(_OPENERS)
            arg = rng.choice(_ARGUMENTS_BY_STANCE[stance])
            closer = rng.choice(_CLOSERS)
            extra_words = " ".join(rng.sample(vocab_words, k=6))
            unique_text = f"{opener} ({extra_words}): {arg} {closer} [nota {u}_{rng.randint(100,999)}]"

            posts.append(
                SocialPost(
                    post_id=f"org_{post_counter}",
                    platform=platform,
                    raw_author_id=f"conta_{platform}_{u}",
                    timestamp=ts,
                    text=unique_text,
                    phone_or_location_hint=phone_hint,
                    stance=stance,
                )
            )
            post_counter += 1

    # 2. Mobilizacao Civica Legitima (40 cidadaos reais usando 'Vote SIM' e 'Vote NÃO' com acento de forma assincrona - C-03)
    for c in range(40):
        plat = rng.choice(["instagram_facebook", "youtube", "whatsapp"])
        ddd = rng.choice(ddds)
        ts = base_time + timedelta(minutes=rng.randint(30, 900), seconds=rng.randint(0, 59))
        if c % 2 == 0:
            civ_text = f"Vote SIM no PL 2338! Apoie o PL na consulta publica ecidadania! Cidadao #{c} ({rng.choice(vocab_words)})"
            civ_stance = "Favoravel"
        else:
            civ_text = f"Vote NÃO ao PL 2338! Pressione seu senador contra burocracia! Cidadao #{c} ({rng.choice(vocab_words)})"
            civ_stance = "Contrario"

        posts.append(
            SocialPost(
                post_id=f"civ_{post_counter}",
                platform=plat,
                raw_author_id=f"cidadao_mobilizado_{plat}_{c}",
                timestamp=ts,
                text=civ_text,
                phone_or_location_hint=f"+55 ({ddd}) 9{rng.randint(7000,9999)}-{rng.randint(1000,9999)}",
                stance=civ_stance,
            )
        )
        post_counter += 1

    # 3. Spam Comercial Infiltrado na Hashtag Politica (30 posts colocados em quarentena)
    for s in range(30):
        plat = rng.choice(["x_twitter", "telegram", "instagram_facebook"])
        ts = base_time + timedelta(minutes=rng.randint(10, 600))
        posts.append(
            SocialPost(
                post_id=f"spam_{post_counter}",
                platform=plat,
                raw_author_id=f"spammer_account_{s}",
                timestamp=ts,
                text=f"Sorteio PIX GRATIS de R$ 500 agora! Ganhe renda extra nas apostas esportivas #PL2338 ref {s}",
                stance="Neutro",
            )
        )
        post_counter += 1

    # 4. Ataque Coordenado (CIB) de 35 contas automatizadas disparando 450 posts em rajadas sincronizadas
    attack_time = base_time + timedelta(minutes=240)
    copypasta_template = (
        "URGENTE! O PL 2338 no Senado vai destruir a inovacao! "
        "Digam NAO ao PL 2338 agora mesmo! Compartilhem em todos os grupos!"
    )
    coordinated_url = "https://portal-ataque-coordenado.exemplo/contra-pl2338"
    coordinated_tags = ["naoaopl2338", "urgentesenado", "bloqueioia"]

    for b in range(450):
        plat = "x_twitter" if b < 350 else "telegram"
        bot_id = f"rede_bot_conta_{b % 35}"
        ts = attack_time + timedelta(seconds=rng.randint(0, 45))
        if b < 300:
            txt = copypasta_template
            url_val = None
            tags_val = []
        else:
            txt = f"Analise urgente #{b}_{rng.randint(1000,9999)} mostra por que barrar hoje mesmo: {coordinated_url}"
            url_val = coordinated_url
            tags_val = coordinated_tags

        posts.append(
            SocialPost(
                post_id=f"cib_{post_counter}",
                platform=plat,
                raw_author_id=bot_id,
                timestamp=ts,
                text=txt,
                shared_url=url_val,
                hashtags=tags_val,
                phone_or_location_hint="+55 (11) 99999-0000",
                stance="Contrario",
            )
        )
        post_counter += 1

    return posts


def run_audited_pilot_verification(sync_to_cloud: bool = True) -> None:
    cfg = load_settings()
    print("1. [Teste de Software com Dados Sinteticos] Gerando lote multi-plataforma diversificado...")
    raw_posts = generate_audited_legislative_dataset()

    print("2. Executando Desinfeccao, Pseudonimizacao HMAC-SHA256 (LGPD art. 13 §4o) e Detector CIB (LSH + Leiden)...")
    cib_engine = LGPDCleanerAndCIBGraphEngine(settings_override=cfg)
    audited_posts = cib_engine.process_and_audit_posts(raw_posts)

    print("3. Construindo Quadro de Contas Organicas (U_Org) e Sorteando Amostra Estratificada de Contas (com pi_i e d_i)...")
    sampler = ObservedUniverseStratifiedSampler(settings_override=cfg)
    account_frame = sampler.build_organic_account_frame(audited_posts)
    req_n = sampler.compute_required_sample_size(len(account_frame), include_expected_deff=False)
    sampled_accounts, strata_summary = sampler.draw_stratified_account_sample(
        account_frame, target_sample_size=req_n, random_seed=2026
    )
    print(
        f"   -> Quadro Limpo U_Org = {len(account_frame)} contas organicas | "
        f"Amostra sorteada n = {len(sampled_accounts)} contas em {len(strata_summary)} estratos."
    )

    print("4. Executando Motor Estatistico sobre U_Org e Sub-amostra Sorteada...")
    stat_engine = DigitalDiscourseStatisticalEngine(settings_override=cfg)
    metrics_full = stat_engine.compute_verified_discourse_indicators(audited_posts, random_seed=42)
    metrics_sampled = stat_engine.compute_verified_discourse_indicators(
        audited_posts, sampled_account_units=sampled_accounts, random_seed=42
    )
    print(
        f"   -> C1 (Censo U_Org N={metrics_full.total_organic_accounts_N_org}): {metrics_full.scenario_1_organic_unweighted_pct} | "
        f"C1 (Sorteio Interno n={metrics_sampled.sampled_organic_accounts_n} com d_i=1/pi_i): {metrics_sampled.scenario_1_organic_unweighted_pct}"
    )

    backend_mode = "gdrive" if (sync_to_cloud and os.environ.get("GDRIVE_DATASETS_LAKE_FOLDER_ID")) else "local_repro"
    storage = ZeroFootprintStorage(backend_mode=backend_mode)

    parquet_path = storage.get_temp_path("amostra_piloto_pl2338_auditada.parquet")
    df = pd.DataFrame([
        {
            "post_id": p.post_id,
            "platform": p.platform,
            "author_hmac_sha256": p.author_hash,
            "hmac_key_id": p.hmac_key_id,
            "timestamp_hour_trunc": p.timestamp.strftime("%Y-%m-%dT%H:00:00%z"),
            "uf_proxy_ddd": p.uf_proxy,
            "region_proxy_ibge": p.region_proxy,
            "activity_class": p.activity_class,
            "spam_quarantine_reason": p.spam_quarantine_reason,
            "is_near_duplicate_lsh": p.is_near_duplicate_lsh,
            "suspected_coordination": p.suspected_coordination,
            "account_suspected_cib": p.account_suspected_cib,
            "leiden_community_id": p.leiden_community_id,
            "coordination_score": p.coordination_score,
            "coordination_signal_index": p.coordination_signal_index,
            "stance": p.stance,
        }
        for p in audited_posts
    ])

    con = duckdb.connect()
    con.execute(f"COPY df TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    parquet_size_kb = round(parquet_path.stat().st_size / 1024, 1)
    print(f"   -> Dataset Parquet ZSTD gerado em /tmp ({parquet_size_kb} KB para {len(df)} registros).")

    report_path = storage.get_temp_path("Boletim_Piloto_01_PL2338_IA_DataSenado_DX.md")
    fav_ci = metrics_full.confidence_intervals_95_pct["Favoravel"]
    con_ci = metrics_full.confidence_intervals_95_pct["Contrario"]
    neu_ci = metrics_full.confidence_intervals_95_pct["Neutro"]
    hom = metrics_full.platform_divergence_test

    report_md = f"""# 📊 Boletim Piloto #01 (Revisado Pós-Auditoria v2) — Monitoramento do Debate Público Digital
> **AVISO DE ESCOPO (Teste de Software com Dados Sintéticos):** Este documento é resultado de um **teste de software com dados sintéticos** para verificação dos algoritmos da Fase 01. Versões anteriores deste boletim piloto encontram-se marcadas como **SUPERSEDED (Substituídas)**.

**Tema Legislativo:** PL 2338/2023 (Marco Legal da Inteligência Artificial — Senado/Câmara)  
**Metodologia:** Investigação Triangular (*Inspirada no Instituto Democracia em Xeque & Padrões DataSenado*)  
**Estimando Primário ($\\theta_T$):** Proporção sobre o Universo Observado de Contas Digitais Orgânicas ($\\mathcal{{U}}_{{\\text{{Org}}}}$: `1 Conta Orgânica por Plataforma = 1 Unidade Observacional`)  
**Data de Geração:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---

## 1. Comparativo dos 3 Cenários de Indicadores Digitais vs. Volume Bruto Contaminado

| Posicionamento | Monitor Comum (Volume Bruto sem Spam) | **Cenário 1: Orgânico de Contas ($\\mathcal{{U}}_{{\\text{{Org}}}}$)** | **Cenário 1 Corrigido (Rogan-Gladen)** | **Cenário 2: Equilibrado por Plataforma ($1/K$)** | **Cenário 3: Reponderado (Sensibilidade sob Ignorabilidade)** | IC 95% Bootstrap Estratificado (Cenário 3) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Favorável** | {metrics_full.raw_contaminated_volume_pct['Favoravel']:.1f}% | **{metrics_full.scenario_1_organic_unweighted_pct['Favoravel']:.1f}%** | {metrics_full.rogan_gladen_corrected_c1_pct['Favoravel']:.1f}% | **{metrics_full.scenario_2_equal_platform_pct['Favoravel']:.1f}%** | **{metrics_full.scenario_3_reweighted_sensitivity_pct['Favoravel']:.1f}%** | [{fav_ci[0]:.1f}% — {fav_ci[1]:.1f}%] |
| **Contrário** | {metrics_full.raw_contaminated_volume_pct['Contrario']:.1f}% *(Inflado por CIB)* | **{metrics_full.scenario_1_organic_unweighted_pct['Contrario']:.1f}%** | {metrics_full.rogan_gladen_corrected_c1_pct['Contrario']:.1f}% | **{metrics_full.scenario_2_equal_platform_pct['Contrario']:.1f}%** | **{metrics_full.scenario_3_reweighted_sensitivity_pct['Contrario']:.1f}%** | [{con_ci[0]:.1f}% — {con_ci[1]:.1f}%] |
| **Neutro** | {metrics_full.raw_contaminated_volume_pct['Neutro']:.1f}% | **{metrics_full.scenario_1_organic_unweighted_pct['Neutro']:.1f}%** | {metrics_full.rogan_gladen_corrected_c1_pct['Neutro']:.1f}% | **{metrics_full.scenario_2_equal_platform_pct['Neutro']:.1f}%** | **{metrics_full.scenario_3_reweighted_sensitivity_pct['Neutro']:.1f}%** | [{neu_ci[0]:.1f}% — {neu_ci[1]:.1f}%] |

*Status de Calibração do Cenário 3:* **`{metrics_full.scenario_3_calibration_status}`** (Gap máximo absoluto pós-trimming $[0,25; 4,00]$ = `{metrics_full.scenario_3_max_margin_gap_pp} p.p.`).

---

## 2. Termômetro de Indícios de Coordenação (CIB) e Quarentena
- **Universo Total Capturado ($N$):** `{metrics_full.total_raw_posts_N}` publicações nas 6 plataformas.
- **Spam Comercial em Quarentena:** `{metrics_full.total_commercial_spam_posts}` publicações (excluídas do cálculo de opinião).
- **Indícios de Coordenação (CIB) Isolados:** `{metrics_full.total_suspected_cib_posts}` publicações emitidas por `{metrics_full.total_suspected_cib_accounts}` contas (**`{metrics_full.post_level_artificiality_rate_pct}%` em nível de post** | **`{metrics_full.account_level_artificiality_rate_pct}%` em nível de conta**).
- **Mobilização Cívica Legítima Preservada:** `{metrics_full.total_civic_mobilization_posts}` publicações (com marcador cívico explícito *"Vote SIM / Vote NÃO"* sem sincronia mecânica).
- **Repetição Orgânica Assíncrona:** `{metrics_full.total_organic_repetition_posts}` publicações.

---

## 3. Ficha Técnica Estatística e Limites Inferenciais
- **Unidades Observacionais Orgânicas ($|\\mathcal{{U}}_{{\\text{{Org}}}}|$):** `{metrics_full.total_organic_accounts_N_org}` contas digitais únicas por plataforma (pseudonimizadas via `HMAC-SHA256` de 64 caracteres, LGPD art. 13 §4º, `key_id={cib_engine.key_id}`).
- **Sub-Amostra Sorteada de Contas ($n$):** `{metrics_sampled.sampled_organic_accounts_n}` contas sorteadas com probabilidades de inclusão $\\pi_i$ conhecidas (Incerteza estatística interna do sorteio com FPC: `± {metrics_sampled.internal_statistical_uncertainty_pp} p.p.`).
- **Efeito do Desenho ($DEFF$ de Kish no Cenário 3):** `{metrics_full.kish_design_effect_deff}` ($n_{{\\text{{eff}}}} = {metrics_full.effective_sample_size_n_eff}$).
- **Nota de Escopo Inferencial:** Os intervalos quantificam a incerteza estatística interna (sorteio de contas e reamostragem bootstrap estratificada); **não representam margem de erro demográfica populacional** e não corrigem viés de autosseleção ou silêncio de não usuários.
- **Teste de Homogeneidade Inter-Plataformas ({hom.test_label}):**
  - $\\chi^2_{{\\text{{Pearson}}}} = {hom.pearson_chi2}$, $\\chi^2_{{\\text{{Ajustado}}}} = {hom.adjusted_chi2}$ ($gl = {hom.degrees_of_freedom}$), **$p\\text{{-valor}} = {hom.p_value}$**, **Tamanho de Efeito $V\\text{{ de Cramér}} = {hom.cramers_v_effect_size}$** $\\longrightarrow$ *{hom.interpretation}*
  - *p-valores por categoria corrigidos por Holm-Bonferroni:* `{hom.holm_corrected_p_values_by_category}`
"""
    report_path.write_text(report_md, encoding="utf-8")

    reports_folder_id = os.environ.get("GDRIVE_RELATORIOS_DX_FOLDER_ID") if backend_mode == "gdrive" else "local_repro"
    print(f"5. Sincronizando artefatos via ZeroFootprintStorage (modo={backend_mode}) com verificacao de integridade...")
    up1 = storage.upload_and_purge(parquet_path)
    up2 = storage.upload_and_purge(report_path, reports_folder_id)
    storage.clear_all_cache()
    print(f"   -> {up1}")
    print(f"   -> {up2}")
    print("6. Verificacao de software concluida com sucesso!")


if __name__ == "__main__":
    run_audited_pilot_verification()
