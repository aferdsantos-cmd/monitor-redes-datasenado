---
name: ds-eda-and-vectorized-manipulation
description: Use this skill whenever performing Exploratory Data Analysis (EDA), vectorized tabular data cleaning, missing data diagnostics (MCAR/MAR/MNAR), multi-level aggregations, pivot tables, schema validation, or memory-optimized DuckDB/Pandas/Excel/Word transformations.
---

# Manipulação Tabular e Análise Exploratória Vetorizada (EDA)

Padrões de engenharia de dados tabular de alta performance para o Monitor de Redes DataSenado, operando com manipulação vetorizada em memória restrita, álgebra relacional em DuckDB SQL e diagnósticos estruturados de dados faltantes sob a política Zero-Footprint.

## 1. Hierarquia de Execução Vetorizada (Zero Loops)
- **Camada 1 — DuckDB SQL:** Filtros pesados, agregações multi-nível (`CUBE`/`ROLLUP`), joins relacionais e window functions executados diretamente sobre arquivos Parquet (`ZSTD`) em `/tmp/monitor_datasenado_cache`.
- **Camada 2 — NumPy / Pandas 2.x PyArrow:** Transformações em memória vetorizadas via `np.select`, `pd.Categorical` e expressões booleanas colunares.
- **Proibição Estrita de Loops:** Proibido o uso de `df.iterrows()`, `df.apply(axis=1)` para operações numéricas/lógicas e atribuição encadeada (*chained indexing* `df[a][b] = v`).

## 2. Diagnóstico de Dados Faltantes (Taxonomia de Rubin)
- **MCAR (Missing Completely at Random):** Perda aleatória e independente de qualquer variável observada ou latente.
- **MAR (Missing at Random):** Ausência sistemática explicável por variáveis observadas (ex.: ausência de DDD correlacionada com canal YouTube vs WhatsApp). Tratar com imputação por estrato ou reponderação.
- **MNAR (Missing Not at Random):** Ausência dependente do próprio valor omitido (ex.: autocensura de opiniões extremas no Cenário 2). Exige modelagem de seleção de Heckman ou declaração epistêmica.
- **Proibição:** Proibido aplicar `.dropna()` ou `.fillna(0)` cegamente sem documentar a perda por plataforma e estrato.

## 3. Integridade e Conservação em Joins e Pivots
- **Asserção de Cardinalidade:** Todo merge tabular deve especificar cardinalidade explícita (`validate="many_to_one"` ou `"one_to_one"`).
- **Invariante de Conservação de Pesos:** Em qualquer cruzamento de tabelas com pesos amostrais ($d_i, w_i$), verificar que $\left|\sum w_{\text{pre}} - \sum w_{\text{post}}\right| < 10^{-9}$ para garantir que nenhum registro foi multiplicado indevidamente.

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Validar esquemas de tipos na leitura; usar `validate=` em joins; computar estatísticas de nulos por grupo; respeitar teto de 250 MB em `/tmp`.
- **MUST NOT DO:** Não iterar com `for` linha a linha; não ignorar duplicações após merge; não alterar tipos de colunas silenciosamente; não gravar arquivos CSV soltos no repositório.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para criação de variáveis de séries temporais, embeddings ou encoding: use `ds-advanced-feature-engineering`.
- Para treinamento e calibração de modelos: use `ds-ml-modeling-and-validation`.
- Para amostragem complexa, Hájek, Raking IPF e Rogan-Gladen: use `stats-inference-datasenado`.
- Para automação de pipelines, AST e sincronização Drive/Git: use `eng-python-zero-footprint`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute a sonda de validação e perfilamento:
  ```bash
  ./skills/ds-eda-and-vectorized-manipulation/scripts/eda_vectorized_linter_and_profiler.py --demo
  ```
- **Manuais Técnicos:**
  - [vectorized_duckdb_pandas_patterns.md](./references/vectorized_duckdb_pandas_patterns.md)
  - [missing_data_and_join_integrity.md](./references/missing_data_and_join_integrity.md)
