---
name: stats-inference-datasenado
description: Use this skill whenever implementing, auditing, or modifying sampling designs, statistical inference engines, Raking/IPF calibration, Rogan-Gladen correction, Bootstrap intervals, hypothesis tests, or Coordinated Inauthentic Behavior (CIB) detection.
---

# Consultoria Estatística e Econométrica Sênior (Python & R)

Orquestrador dos 5 Pilares de Excelência em Estatística Amostral, Econometria Causal e Interoperabilidade Bilingue para o Instituto de Pesquisa DataSenado e TCC.

## 1. Contexto Estatístico Enxuto e Notação Simbólica (Token Economy)
- **Zero Dados Brutos no Prompt:** Proibido despejar tabelas completas no chat. Inspecione dados via sumário executivo de momentos, tipos, nulos e $E_{\min}$:
  ```bash
  ./skills/stats-inference-datasenado/scripts/dataset_metadata_profiler.py --input <arquivo.parquet>
  ```
- **Notação Simbólica de Wilkinson & Protocolo de 4 Linhas:** Especifique modelos via sintaxe compacta (`stance ~ theme + time_slice + (1 | platform)`) e estruture pareceres em:
  `Estimando` $\to$ `Fórmula Simbólica/LaTeX` $\to$ `Diagnóstico de Pressupostos` $\to$ `Estimador & Erros Padrão`.

## 2. Pipeline Amostral Complexo e Calibração (Invariantes Fase 01)
- **Sequência Estrita:** (1) Limpeza LGPD + CIB Leiden (`seed=42`) $\to$ (2) Quadro de Contas Orgânicas ($\mathcal{U}_{\text{Org}}$) $\to$ (3) Amostragem Estratificada (`Platform × Turno × Dia`) com Alocação de Hamilton ($\sum n_h = n$) $\to$ (4) Inferência nos 3 Cenários (C1 Hájek + Rogan-Gladen, C2 $1/K$, C3 Raking IPF com truncamento $[0.25, 4.00]$ no simplex dentro do laço).

## 3. Interoperabilidade Bilingue Python $\leftrightarrow$ R (Padrão DataSenado)
- **Bilinguismo Nativo:** Suporte total para gerar scripts de análise e auditoria cruzada em **Python** (`numpy`, `scipy`, `statsmodels`, `duckdb`) e **R** (`arrow`, `survey`, `srvyr`, `fixest`, `did`, `rdrobust`, `igraph`) sobre arquivos comuns Apache Parquet (`ZSTD`).
- Script canônico R de amostragem complexa e Rao-Scott:
  - [r_and_python_survey_econometrics.md](./references/r_and_python_survey_econometrics.md)

## 4. Modelagem Econométrica, Inferência Causal e Árvore de Pressupostos
- **Métodos Longitudinais e Causais:** Escolha Discreta (`Multinomial Logit`, `Ordered Probit`), Painel com Efeitos Fixos e Inferência Causal de choques legislativos (`DiD`, `RDiT`, `IV / 2SLS`).
- **Failsafe Obrigatório de Pressupostos:**
  - *Cochran em $\chi^2$ ($E_{ij} < 5$ em $>20\%$):* Usar Monte Carlo ($B=10000$) ou Teste Exato de Fisher;
  - *Heterocedasticidade (`Breusch-Pagan` $p < 0.05$):* Usar matriz robusta `HC3` ou clusterizada por plataforma;
  - *Autocorrelação serial (`Ljung-Box` / `Durbin-Watson`):* Erros padrão `Newey-West (HAC)`;
  - *Multicolinearidade (`VIF >= 5.0`):* Remover preditor redundante ou regularizar;
  - *Instrumento Fraco em 2SLS:* Exigir $F > 10$ no primeiro estágio (Stock-Yogo).

## 5. Reprodutibilidade Estrita (Seed Locking) e Referências
- Fixar determinismo sempre: `np.random.default_rng(42)` em Python e `set.seed(42)` + `RNGkind("L'Ecuyer-CMRG")` em R.
- **Referências Aprofundadas:**
  - [formulas_and_invariants.md](./references/formulas_and_invariants.md)
  - [cib_network_thresholds.md](./references/cib_network_thresholds.md)
  - [r_and_python_survey_econometrics.md](./references/r_and_python_survey_econometrics.md)
