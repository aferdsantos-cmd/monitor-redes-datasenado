---
name: ds-ml-modeling-and-validation
description: Use this skill whenever training, tuning, calibrating, or validating supervised or unsupervised machine learning models, configuring anti-leakage cross-validation (StratifiedGroupKFold, PurgedGroupTimeSeriesSplit), running multiple hypothesis tests with FDR correction, or computing validation metrics (Macro-F1, MCC, Cohen's Kappa, Brier Score) for Rogan-Gladen integration.
---

# Modelagem Supervisionada, Validação Anti-Leakage e Testes de Hipóteses

Diretrizes analíticas e protocolos estatísticos para desenvolvimento, calibração de probabilidades e validação rigorosa de modelos de Machine Learning no Monitor de Redes DataSenado.

## 1. Esquemas Obrigatórios de Validação Cruzada Anti-Leakage
- **Isolamento Estrito de Contas (`StratifiedGroupKFold`):** Todas as publicações de um mesmo `author_id_hash` pertencem obrigatoriamente a um único fold ($\mathcal{A}_{\text{train}} \cap \mathcal{A}_{\text{val}} = \emptyset$), impedindo que o modelo decore o estilo de autores frequentes.
- **Isolamento Temporal com Embargo (`PurgedGroupTimeSeriesSplit`):** Validação em janelas cronológicas com zona de embargo ($\Delta_{\text{embargo}}$) entre treino e teste para neutralizar vazamentos decorrentes de cascatas virais.

## 2. Calibração de Probabilidades e Ponte Rogan-Gladen
- **Calibração Fora da Amostra:** Classificadores complexos (GBDT, redes neurais) geram escores não-calibrados. Exigir calibração out-of-fold via Regressão Isotônica ou Sigmoide de Platt, avaliada por **Brier Score** e **Expected Calibration Error (ECE)**.
- **Ponte Rogan-Gladen com `stats-inference-datasenado`:** A matriz de confusão $\hat{\mathbf{C}}$ e as taxas $(\hat{\text{Se}}_c, \hat{\text{Sp}}_c)$ devem ser extraídas exclusivamente de predições *out-of-fold* cegas da amostra piloto ($n_{\text{val}} = 550$) antes de alimentar a correção de prevalência.

## 3. Testes de Hipóteses e Controle de Falsas Descobertas
- **Árvore de Decisão de Testes:** Avaliar normalidade (Shapiro-Wilk) e homocedasticidade (Levene) $\to$ Welch $t$-test / ANOVA se paramétrico; Mann-Whitney $U$ / Kruskal-Wallis se não-paramétrico.
- **Controle de FDR (Benjamini & Hochberg, 1995):** Para $m > 1$ testes simultâneos, ordenar $p_{(1)} \le \dots \le p_{(m)}$ e aplicar:
  $$q_{(i)} = \min_{k \ge i} \left(\frac{m}{k} p_{(k)}, 1\right)$$
- **Comparação de Modelos:** Teste de McNemar com correção de Edwards e Bootstrap 95% para Macro-F1, MCC e $\kappa$ de Cohen.

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Agrupar validação por autor; reportar Macro-F1 e MCC além de acurácia; aplicar Benjamini-Hochberg em múltiplos testes; calibrar probabilidades antes de Rogan-Gladen.
- **MUST NOT DO:** Não usar KFold aleatório em comentários sociais; não reportar apenas acurácia simples em bases desbalanceadas; não fazer p-hacking sem correção FDR; não usar pickle para salvar modelos.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para engenharia de features, lags e OOF target encoding: use `ds-advanced-feature-engineering`.
- Para correção de prevalência Rogan-Gladen e Raking IPF: use `stats-inference-datasenado`.
- Para topologia de bolhas e Granger de séries temporais: use `stats-network-bubbles-and-time-series`.
- Para explicabilidade SHAP/LIME e equidade de subgrupos: use `ds-xai-and-model-explainability`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute a sonda de validação, calibração e teste FDR:
  ```bash
  ./skills/ds-ml-modeling-and-validation/scripts/ml_validation_and_calibration_probe.py --demo
  ```
- **Manuais Técnicos:**
  - [anti_leakage_cv_and_calibration.md](./references/anti_leakage_cv_and_calibration.md)
  - [hypothesis_testing_fdr_and_model_comparison.md](./references/hypothesis_testing_fdr_and_model_comparison.md)
