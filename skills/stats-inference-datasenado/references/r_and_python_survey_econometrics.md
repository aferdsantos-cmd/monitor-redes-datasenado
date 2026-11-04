# Interoperabilidade Estatística e Econométrica Bilingue: Python & R (DataSenado)

Este guia técnico formaliza os contratos de interoperabilidade entre o pipeline Python em Apache Parquet (`DuckDB`) e o ecossistema analítico em **R** padrão do **Instituto de Pesquisa DataSenado** (pacotes `survey`, `srvyr`, `fixest`, `did`, `rdrobust` e `arrow`).

---

## 1. Script Canônico em R: Amostragem Complexa e Rao-Scott (Padrão DataSenado)

O script abaixo audita e replica os cálculos de amostragem estratificada, calibração por Raking e teste Rao-Scott de segunda ordem diretamente a partir do arquivo Parquet exportado pelo motor Python:

```r
# ==============================================================================
# Script de Auditoria e Réplica Estatística Bilingue (R / DataSenado)
# Pacotes: arrow, survey, srvyr
# ==============================================================================

# 1. Reprodutibilidade Estrita e Seed Locking
set.seed(42)
RNGkind("L'Ecuyer-CMRG")

suppressPackageStartupMessages({
  library(arrow)
  library(survey)
  library(srvyr)
})

# 2. Leitura Direta de Apache Parquet (ZSTD) gerado pelo pipeline Python
parquet_path <- "/tmp/monitor_datasenado_cache/audited_pilot_dataset.parquet"
df <- arrow::read_parquet(parquet_path)

# 3. Declaração do Desenho Amostral Estratificado (com FPC)
# ids = ~1 (sorteio de contas sem conglomerado), strata = ~stratum_id, weights = ~design_weight_d
discourse_design <- survey::svydesign(
  ids = ~1,
  strata = ~stratum_id,
  weights = ~design_weight_d,
  fpc = ~stratum_total_accounts_N,
  data = df
)

# 4. Cenário 1: Indicador Orgânico com Efeito de Desenho (DEFF de Kish)
prop_c1 <- survey::svymean(~stance, discourse_design, deff = TRUE)
print("=== Cenário 1: Proporções Ponderadas e DEFF ===")
print(prop_c1)
print(survey::deff(prop_c1))

# 5. Cenário 3: Raking IPF com Truncamento de Pesos no Simplex [0.25, 4.00]
# Margens populacionais normativas de referência (exemplo: platform e macroregion)
pop_platform <- data.frame(
  platform = c("whatsapp", "youtube", "instagram_facebook", "tiktok", "telegram", "x_twitter"),
  Freq = c(0.30, 0.25, 0.25, 0.12, 0.04, 0.04) * nrow(df)
)
pop_region <- data.frame(
  macroregion = c("Sudeste", "Nordeste", "Sul", "Norte", "Centro-Oeste"),
  Freq = c(0.42, 0.27, 0.14, 0.09, 0.08) * nrow(df)
)

calibrated_design <- survey::calibrate(
  discourse_design,
  formula = list(~platform, ~macroregion),
  population = list(pop_platform, pop_region),
  calfun = "raking",
  bounds = c(0.25, 4.00),
  maxit = 80,
  epsilon = 0.01
)

prop_c3 <- survey::svymean(~stance, calibrated_design)
print("=== Cenário 3: Proporções Reponderadas via Raking ===")
print(prop_c3)

# 6. Teste de Homogeneidade Inter-Plataformas: Chi-Quadrado Ajustado de Rao-Scott
# Utiliza a aproximação de segunda ordem de Rao-Scott (statistic = "F")
rao_scott_test <- survey::svychisq(~stance + platform, discourse_design, statistic = "F")
print("=== Teste de Independência Rao-Scott (2ª Ordem) ===")
print(rao_scott_test)

# Ajuste de multiplicidade via Holm-Bonferroni
p_vals <- c(rao_scott_test$p.value)
p_adj <- stats::p.adjust(p_vals, method = "holm")
```

---

## 2. Tabela de Equivalência Direta: Python vs. R

| Capacidade Estatística | Implementação em Python | Implementação Padrão em R |
| :--- | :--- | :--- |
| **Leitura Parquet ZSTD** | `duckdb.connect().execute("...")` / `pyarrow` | `arrow::read_parquet()` |
| **Desenho Amostral / FPC** | `ObservedUniverseStratifiedSampler` | `survey::svydesign(..., fpc = ~N)` |
| **DEFF de Kish** | `1.0 + (np.std(w)/np.mean(w))**2` | `survey::deff(svymean(..., deff=TRUE))` |
| **Raking IPF Truncado** | `_bounded_simplex_renormalize()` em laço | `survey::calibrate(..., calfun="raking", bounds=c(0.25, 4.00))` |
| **Teste Rao-Scott $\chi^2$** | `platform_homogeneity_chi2_test()` (1ª ordem) | `survey::svychisq(..., statistic="F")` (2ª ordem) |
| **Correção de Multiplicidade** | `holm_bonferroni_correction()` | `stats::p.adjust(..., method="holm")` |
| **Escolha Discreta / Multinomial** | `statsmodels.discrete.discrete_model.MNLogit` | `nnet::multinom()` |
| **Painel com Efeitos Fixos** | `linearmodels.panel.PanelOLS` | `fixest::feols(stance ~ x | platform + date)` |
| **Diferenças em Diferenças (DiD)** | `diff-in-diff` / regressão TWFE | `did::att_gt()` / `fixest::feols()` |
| **Regressão Descontínua (RDD)** | `rdrobust` (Python wrapper) | `rdrobust::rdrobust()` |
| **Variáveis Instrumentais (2SLS)** | `linearmodels.iv.IV2SLS` | `fixest::feols(y ~ 1 | x ~ z)` |

---

## 3. Modelagem Econométrica e Inferência Causal de Choques Legislativos

Em análises longitudinais de debate legislativo (ex.: efeito de uma votação de urgência, audiência pública ou vazamento de relatório), utilizam-se técnicas causais quase-experimentais:

### 3.1. Diferenças em Diferenças (DiD) e Event-Study
- **Notação de Wilkinson:** `stance_favoravel ~ treat * post | platform + author_hash`
- **Estimador:** Callaway & Sant'Anna (2021) para adoção escalonada (*staggered treatment*), prevenindo vieses de pesos negativos do TWFE canônico.
- **Validação de Tendências Paralelas:** Teste de Wald sobre os coeficientes antecedentes (*leads/pre-trends*). Se $p < 0.05$, a hipótese de tendências paralelas é rejeitada e deve-se empregar *Synthetic Difference-in-Differences (SDID)*.

### 3.2. Regressão Descontínua no Tempo (RDiT / Interrupted Time Series)
- **Notação:** `stance ~ time_centered + post_event + post_event:time_centered`
- Utiliza janelas de largura de banda ótima de Imbens-Kalyanaraman (*IK bandwidth*) e polinômios locais lineares com erros robustos clusterizados.

### 3.3. Variáveis Instrumentais (2SLS)
- Utilizado quando a exposição a determinado discurso na rede é endógena ao comportamento do autor:
  - 1º Estágio: `exposure ~ instrument + controls`
  - 2º Estágio: `stance ~ exposure_hat + controls`
- **Failsafe de Instrumento Fraco:** Exige estatística $F > 10$ no primeiro estágio (*Stock & Yogo, 2005*). Se $F \le 10$, a inferência pontual é inválida e devem-se reportar intervalos de Anderson-Rubin.

---

## 4. Árvore de Decisão de Pressupostos (Failsafe Diagnostics)

| Pressuposto / Teste | Procedimento de Diagnóstico | Limiar de Alerta / Rejeição | Ação Corretiva Failsafe Obrigatória |
| :--- | :--- | :---: | :--- |
| **Célula Mínima no $\chi^2$ (Cochran)** | Tabela de frequências esperadas $E_{ij}$ | $> 20\%$ das células com $E_{ij} < 5$ ou qualquer $E_{ij} < 1$ | Substituir $\chi^2$ assintótico por Teste Exato de Fisher ou simulação de Monte Carlo ($B \ge 10.000$). |
| **Multicolinearidade** | Fator de Inflação de Variância (`VIF`) | $\text{VIF} \ge 5.0$ em qualquer covariável | Remover preditor colinear, ortogonalizar ou aplicar penalização Ridge/Lasso. |
| **Heterocedasticidade** | Teste de Breusch-Pagan / White | $p < 0.05$ | Aplicar matriz de variância covariância robusta `HC3` (MacKinnon & White) ou clusterizada no nível da plataforma. |
| **Autocorrelação Serial** | Teste de Ljung-Box / Durbin-Watson | $p < 0.05$ ou $\text{DW} \notin [1.5, 2.5]$ | Aplicar erros padrão consistentes com heterocedasticidade e autocorrelação de Newey-West (`HAC`). |
| **Normalidade de Resíduos** | Teste Shapiro-Wilk / Gráfico Q-Q | $p < 0.01$ em amostras $N < 300$ | Empregar inferência não paramétrica ou reamostragem Bootstrap em vez de aproximação gaussiana. |
| **Instrumento Fraco em 2SLS** | Teste $F$ do primeiro estágio | $F < 10.0$ (Stock-Yogo) | Abortar estimativa pontual de Wald e calcular Intervalo de Confiança Robusto de Anderson-Rubin. |
