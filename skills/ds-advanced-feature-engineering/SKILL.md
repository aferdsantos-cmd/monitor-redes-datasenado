---
name: ds-advanced-feature-engineering
description: Use this skill whenever designing, transforming, encoding, or auditing features for machine learning or statistical models, including time-series lags/rolling windows, out-of-fold target encoding, text/framing embeddings, graph centrality features, or LGPD-compliant k-anonymity transformations.
---

# Engenharia de Recursos Avançada e Salvaguardas Anti-Leakage

Diretrizes arquiteturais para engenharia de features analíticas no Monitor de Redes DataSenado, contemplando séries temporais causais, codificação out-of-fold, métricas lexicais e de rede, com prevenção absoluta de vazamento de dados (*data leakage*) e salvaguardas da LGPD.

## 1. Invariante Fit-on-Train-Only (Prevenção de Vazamento Pré-Split)
- **Bloqueio Absoluto:** Toda transformação dependente da distribuição dos dados (escalonamento robusto, imputação estatística, quantis, vocabulário TF-IDF/BM25 e Target Encoding) deve ser ajustada (`fit`) exclusivamente sobre a partição de treino de cada fold.
- **Partição de Teste/Validação Intocada:** Na avaliação, apenas o método `transform` pode ser aplicado. Nunca execute `.fit()` ou `.fit_transform()` sobre a base inteira antes do split!

## 2. Features de Séries Temporais Estritamente Causais
- **Janelas Deslizantes Causais:** Utilizar parâmetros `closed='left'` em janelas móveis temporais, assegurando que o instante $t$ receba dados apenas do intervalo $[t - W, t)$, eliminando *look-ahead bias*.
- **Métricas Temporais:** Médias móveis exponenciais (EWMA), taxa de aceleração de postagens e **Índice de Burstiness de Goh-Barabási**:
  $$B = \frac{\sigma_\tau - \mu_\tau}{\sigma_\tau + \mu_\tau} \in [-1, 1]$$
  onde $\tau$ representa os intervalos de tempo entre postagens sucessivas da mesma conta.
- **Ciclos Temporais:** Codificação trigonométrica contínua para horas e dias: $\sin(2\pi h / 24)$ e $\cos(2\pi h / 24)$.

## 3. Codificação de Alta Cardinalidade e Métricas Avançadas
- **Out-of-Fold (OOF) Empirical Bayes Target Encoding:**
  $$\hat{x}_c = \frac{n_c \bar{y}_c + m \bar{y}_{\text{prior}}}{n_c + m}$$
  com suavização de Bayes empírico ($m=10$) e particionamento agrupado por autor (`author_id_hash`).
- **Features Editoriais e Lexicais (ADR-011):** Taxa de adjetivação, densidade léxica e divergência de Kullback-Leibler textual.
- **Features de Grafos (ADR-010):** Grau ponderado, PageRank e centralidade local.

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Agrupar validação cruzada por autor; usar `closed='left'` em séries temporais; auditar colinearidade ($VIF < 5.0$); garantir $k \ge 5$ contas no $k$-anonimato LGPD.
- **MUST NOT DO:** Nunca usar a variável-alvo para criar features sem esquema OOF; não calcular normalização antes do split; não ignorar a dependência temporal; não aplicar SMOTE na validação.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para limpeza básica, diagnósticos MCAR/MAR e merges relacionais: use `ds-eda-and-vectorized-manipulation`.
- Para treinamento, calibração Platt/Isotônica e validação cruzada: use `ds-ml-modeling-and-validation`.
- Para topologia de bolhas em redes orgânicas e Granger causal: use `stats-network-bubbles-and-time-series`.
- Para interpretabilidade e valores SHAP: use `ds-xai-and-model-explainability`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute a sonda de auditoria anti-leakage e colinearidade:
  ```bash
  ./skills/ds-advanced-feature-engineering/scripts/feature_leakage_and_collinearity_auditor.py --demo
  ```
- **Manuais Técnicos:**
  - [leakage_free_pipelines_and_oof_encoding.md](./references/leakage_free_pipelines_and_oof_encoding.md)
  - [timeseries_lexical_and_graph_features.md](./references/timeseries_lexical_and_graph_features.md)
