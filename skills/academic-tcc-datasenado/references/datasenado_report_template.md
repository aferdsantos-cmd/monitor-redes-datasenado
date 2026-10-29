# [MODELO] Boletim Técnico Parlamentar — Instituto de Pesquisa DataSenado

**Tema Legislativo:** {ID_TEMA} — {TITULO_TEMA}  
**Período de Monitoramento:** {DATA_INICIO} a {DATA_FIM}  
**Versão do Motor Analítico:** `v1.2-fase01`  
**Data de Emissão:** {DATA_EMISSAO}  

---

## 1. Sumário Executivo para Tomada de Decisão Parlamentar

- **Síntese Geral:** No período analisado, o debate público digital observado registrou um volume total de `{N_POSTS_BRUTOS}` postagens distribuídas entre as plataformas monitoradas. Após os filtros de desinfecção, identificou-se um universo de `{N_ORG_CONTAS}` contas orgânicas ativas sobre a matéria.
- **Predominância de Posicionamento:**
  - **Cenário 1 (Orgânico Ponderado pelo Desenho):** {PCT_FAVORAVEL_C1}% Favorável, {PCT_CONTRARIO_C1}% Contrário, {PCT_NEUTRO_C1}% Neutro/Indefinido.
  - **Cenário 2 (Equilíbrio entre Plataformas 1/K):** {PCT_FAVORAVEL_C2}% Favorável, {PCT_CONTRARIO_C2}% Contrário, {PCT_NEUTRO_C2}% Neutro/Indefinido.
  - **Cenário 3 (Reponderação / Análise de Sensibilidade):** {PCT_FAVORAVEL_C3}% Favorável, {PCT_CONTRARIO_C3}% Contrário, {PCT_NEUTRO_C3}% Neutro/Indefinido.
- **Sinal de Coordenação e Automação:** A taxa de artificialidade observada foi de `{TAXA_ARTIF_POST}%` no nível de postagens e `{TAXA_ARTIF_CONTA}%` no nível de contas.

---

## 2. Ficha Técnica e Indicadores Amostrais

| Indicador Metodológico | Valor Mensurado |
| :--- | :--- |
| **Universo de Contas Orgânicas ($N_{\text{Org}}$)** | `{N_ORG_CONTAS}` contas |
| **Amostra Estratificada Sorteada ($n$)** | `{N_AMOSTRA}` contas (Alocação Exata de Hamilton) |
| **Tamanho Efetivo de Amostra ($n_{\text{eff}}$)** | `{N_EFF}` contas |
| **Efeito de Desenho de Kish ($\text{DEFF}$)** | `{DEFF_VALOR}` |
| **Incerteza Amostral Interna (IC 95% Bootstrap)** | ±`{MARGEM_ERRO_PP}` p.p. |
| **Status da Calibração IPF (Cenário 3)** | `{CALIBRATION_STATUS}` (Limites $[0.25, 4.00]$) |

---

## 3. Tabela Comparativa de Cenários Inferenciais

| Posicionamento | Cenário 1: Orgânico ($\mathcal{U}_{\text{Org}}$) | Cenário 1 (Rogan-Gladen Corrigido) | Cenário 2: Equilibrado ($1/K$) | Cenário 3: Reponderado (Raking IPF) |
| :--- | :---: | :---: | :---: | :---: |
| **Favorável** | {C1_FAV}% [IC: {C1_FAV_INF}% – {C1_FAV_SUP}%] | {C1_RG_FAV}% | {C2_FAV}% [IC: {C2_FAV_INF}% – {C2_FAV_SUP}%] | {C3_FAV}% [IC: {C3_FAV_INF}% – {C3_FAV_SUP}%] |
| **Contrário** | {C1_CON}% [IC: {C1_CON_INF}% – {C1_CON_SUP}%] | {C1_RG_CON}% | {C2_CON}% [IC: {C2_CON_INF}% – {C2_CON_SUP}%] | {C3_CON}% [IC: {C3_CON_INF}% – {C3_CON_SUP}%] |
| **Neutro / Indeterminado** | {C1_NEU}% [IC: {C1_NEU_INF}% – {C1_NEU_SUP}%] | {C1_RG_NEU}% | {C2_NEU}% [IC: {C2_NEU_INF}% – {C2_NEU_SUP}%] | {C3_NEU}% [IC: {C3_NEU_INF}% – {C3_NEU_SUP}%] |

---

## 4. Diagnóstico de Comportamento Inautêntico Coordenado (CIB) e Spam

- **Total de Postagens em Quarentena de Spam Comercial:** `{N_SPAM}` posts.
- **Contas Excluídas por Indício de Coordenação / Automação:** `{N_CONTAS_CIB}` contas.
- **Top Comunidades de Coordenação Identificadas:**
  - Cluster #1: {TAMANHO_C1} contas, densidade temporal={DENS_C1}, hashtag predominante=`{TAG_C1}`.
- **Padrão de Disseminação em Notícias Virais:** Veículos de imprensa e órgãos oficiais na *allowlist* registraram `{N_NOTICIAS_VIRAL}` compartilhamentos sem falso positivo de coordenação.

---

## 5. Homogeneidade Intra-Plataforma

- **Estatística do Teste:** $\chi^2 = {CHI2_VALOR}$ (gl={GL_VALOR}, $p$-valor corrigido por Holm = `{P_VALOR_HOLM}`).
- **Tamanho de Efeito:** $V$ de Cramér = `{V_CRAMER}` ({CLASSIFICACAO_EFEITO}: pequeno / moderado / substancial).
- **Interpretação:** As plataformas {APRESENTAM / NAO APRESENTAM} divergência estatisticamente significante na proporção de posicionamentos observados.

---

## 6. Nota Metodológica e Limites de Interpretação

> **Aviso Institucional Obrigatório:**
> As estimativas apresentadas neste boletim referem-se estritamente ao **Universo Observado de Contas Digitais Orgânicas ($\mathcal{U}_{\text{Org}, T}$)** ativas durante a janela de coleta e **não se equiparam nem substituem as pesquisas de opinião pública por amostragem probabilística da população brasileira** conduzidas pelo DataSenado via CATI.
> Os intervalos de confiança refletem exclusivamente a incerteza estatística interna do sorteio estratificado de contas e reamostragem bootstrap, não incorporando possíveis vieses de autosseleção ou silêncio de cidadãos não usuários das plataformas.
