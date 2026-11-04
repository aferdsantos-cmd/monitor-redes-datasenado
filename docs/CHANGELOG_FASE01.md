# Changelog e Histórico de Mudanças — Fase 01 (`monitor-redes-datasenado`)

Este documento registra formalmente todo o ciclo de vida, homologação e eventuais alterações futuras na **Fase 01** do projeto.

> [!IMPORTANT]
> **POLÍTICA DE GOVERNANÇA E CONTROLE DE MUDANÇAS DA FASE 01:**
> Os 16 arquivos da Baseline da Fase 01 (`WP-01` a `WP-16`) estão congelados sob a versão `v1.2.0-fase01` (commit `7af3548b`).
> **É estritamente proibido realizar commits ou pushes diretos na branch `main` que modifiquem qualquer um desses 16 arquivos.**
> Qualquer alteração posterior exige:
> 1. Criação de branch dedicada (`pr/fase01-v1.2.x`);
> 2. Incremento semântico de versão da Fase 01 (`v1.2.1-fase01`, etc.);
> 3. Registro detalhado nesta página (data, arquivos, hashes antigos, novos e justificativa técnica);
> 4. Abertura formal de Pull Request (`gh pr create`) para aprovação do Proprietário do Projeto antes de qualquer mesclagem.

---

## [v1.2.0-fase01] — 2026-11-04 (Baseline Oficial Homologada e Congelada)

- **Commit de Referência:** `7af3548bce908475b5fe480666c427b91733ca4a`
- **Tag Git:** `v1.2.0-fase01-baseline` (e retrocompatível `v1.2-fase01`)
- **Status Pericial:** **100% CONFORME (30/30 Testes de Campo Aprovados)**
- **Documento Homologador:** `Auditorias/Fase_01/04_Homologacao_Final/Termo_de_Homologacao_e_Congelamento_Baseline_Fase01_v1_2.md`
- **Arquivo de Trava Criptográfica:** `config/fase01_baseline_lock.json`

### Escopo Entregue e Congelado
1. **Governança Ética e LGPD (Lei 13.709/2018):**
   - Pseudonimização irreversível `HMAC-SHA256` em streaming com chave isolada em `.env` (`LGPDComplianceProcessor`).
   - Redação de PII (CPF, e-mail, telefone, `@handles`) antes de qualquer persistência.
   - Enquadramento ético sob Resolução CNS 510/2016 (dados públicos de acesso irrestrito).
2. **Engenharia de Qualidade e Zero-Footprint:**
   - Trava de $\le 250\text{ MB}$ temporários em `/tmp/monitor_datasenado_cache` e **0 KB** de resíduo pós-execução.
   - Varredura SAST limpa (0 primitivas inseguras `eval`, `exec`, `pickle.loads`, `shell=True`).
   - Sincronização atômica linear com o GitHub sem destruição de histórico (`orphan_clean_history=False`).
   - Verificação de segredos e IDs via hashes SHA-256 (`FORBIDDEN_TOKEN_SHA256_HASHES`).
3. **Detecção de Automação e Grafos CIB (Coordinated Inauthentic Behavior):**
   - Algoritmo LSH (MinHash) para quase-duplicatas e detecção de comunidades Leiden.
   - Regra estrita de $\ge 2$ eventos/itens coordenados distintos (Giglietto et al., 2020).
   - Quarentena de spam comercial com regras específicas para apostas mesmo sob isca legislativa.
   - 0,0% de falso positivo em notícias virais/telejornais e 100% de recall em redes coordenadas.
4. **Amostragem Probabilística e Inferência Estatística Multiclasse:**
   - Unidade observacional canônica: 1 Autor Digital Orgânico por Plataforma = 1 Voto.
   - Amostragem estratificada com probabilidades de inclusão estritamente positivas ($\pi_i > 0 \ \forall i$) via colapso hierárquico e alocação de Hamilton.
   - Motor inferencial nos 3 Cenários Metodológicos:
     - **Cenário 1:** Universo Observado Limpo $\mathcal{U}_{\text{Org}}$ (com FPC exato $= 0,0\text{ p.p.}$ no censo $n=N$);
     - **Cenário 2:** Indicador Equilibrado por Plataforma (peso $1/K$);
     - **Cenário 3:** Sensibilidade Reponderada via Raking IPF com Trimming $[0.25, 4.00]$ sobre margens normativas TIC Domicílios / Reuters.
   - Correção multiclasse de erro de classificação de Rogan-Gladen no simplex.
   - Teste de hipótese $H_1$ via Bootstrap Pareado por Conta (`paired_bootstrap_clean_vs_raw_test`).
   - Teste de homogeneidade entre plataformas via $\chi^2$ de Pearson com ajuste por DEFF e $V$ de Cramér canônico.

### Inventário Criptográfico dos 16 Arquivos Congelados (`WP-01` a `WP-16`)

| WP-ID | Caminho Relativo do Arquivo | SHA-256 (Prefixo 12) | Linhas | Bytes |
| :---: | :--- | :---: | :---: | :---: |
| `WP-01` | `config/settings.yaml` | `afb2d506fe9f` | 131 | 5.878 |
| `WP-02` | `docs/00_Plano_Implementacao_Historico_v1_0_SUPERSEDED.md` | `f93b3aed7968` | 28 | 2.827 |
| `WP-03` | `docs/01_Metodologia_Cientifica_e_Estatistica_NotebookLM.md` | `603f6fff5e16` | 102 | 13.402 |
| `WP-04` | `docs/02_Plano_Validacao_Estatistica.md` | `d75759ed57cf` | 67 | 8.384 |
| `WP-05` | `docs/03_Termo_de_Emenda_Plano_v1_1_e_ADR.md` | `d3e0e732b7fe` | 34 | 7.373 |
| `WP-06` | `docs/Relatorio_Correcoes_Fase01_v3.md` | `da9ecfba63db` | 118 | 16.034 |
| `WP-07` | `README.md` | `bd3f977dc2b0` | 45 | 6.278 |
| `WP-08` | `src/cleaning/lgpd_and_bot_filter.py` | `2944b0fdab38` | 709 | 36.038 |
| `WP-09` | `src/config_loader.py` | `c9ef1b9c78d5` | 48 | 1.802 |
| `WP-10` | `src/reporting/pilot_audit_runner.py` | `fd3f838393bc` | 382 | 22.398 |
| `WP-11` | `src/sampling/stratified_sampler.py` | `f7be7ffeed99` | 358 | 15.451 |
| `WP-12` | `src/stats/opinion_inference_engine.py` | `0052984d272b` | 887 | 41.538 |
| `WP-13` | `src/storage/github_zero_footprint_sync.py` | `25b43326d3fb` | 267 | 9.531 |
| `WP-14` | `src/storage/zero_footprint_sync.py` | `0f89eb695f6a` | 211 | 9.821 |
| `WP-15` | `tests/test_fase01_audit_compliance.py` | `b6243b1bd294` | 574 | 28.832 |
| `WP-16` | `tests/test_skills_architecture.py` | `1bedb09b89a5` | 367 | 16.878 |
