# Arquitetura Técnica — Fase 04: Triplo Motor de Inteligência Analítica, PNL Calibrada, Bolhas e MLOps (`ADR-010` e `ADR-011`)

- **Documento:** `docs/07_Arquitetura_Triplo_Motor_Inteligencia_Fase04.md`
- **Fase:** 04 (`v1.0`)
- **Status:** Implementado e Verificado
- **Emissão:** IA Operadora de Código sob o protocolo `brain-operator-protocol` e as 11 Skills do Projeto
- **Diretrizes de Referência:** `ADR-001` a `ADR-011`, ISO 31000 / ISO 9001, LGPD (Art. 5º, II e Art. 13)

---

## 1. Visão Geral e Arquitetura do Sistema

A Fase 04 consolida o coração analítico e estatístico do **Monitor de Redes Sociais do DataSenado**, integrando os dados multilaterais da Fase 03 (`Bronze -> Silver -> Gold` nas 6 plataformas) ao **Triplo Motor de Inteligência Analítica (`src/analytics/`)** e à ponte de inferência probabilística da Fase 01 (`DigitalDiscourseStatisticalEngine`):

```
       [ Phase03SixPlatformsOrchestrator ]
           | (6 Plataformas: X, IG/FB, TikTok, YT, TG, WA)
           v
       [ Camada Medallion DuckDB Efêmera ]
           |
   +-------+-----------------------+-----------------------+
   |                               |                       |
   v                               v                       v
[ Motor 4A: Causais & Agenda ] [ Motor 4B: PNL, XAI & MLOps ] [ Motor 4C: Bolhas & Espectros ADR-010 ]
   - Burstiness Goh-Barabási (B)   - Embeddings L2 = 1.0 (mps/cpu) - Higiene Estrita (100% anti-Spam/CIB)
   - Causal Windows (closed='left')- StratifiedGroupKFold (Autor)  - Grafo Co-Engajamento Orgânico
   - OOF Target Encoding (Autores) - PurgedTimeSplit (Embargo)     - Newman Q + Modelo Nulo (z, p)
   - VIF Diagnóstico (< 5.0)       - Calibração OOF (Brier, ECE)   - Krackhardt E-I (< -0.40 Eco)
   - k-anonimato LGPD (k >= 5)     - SHAP Aditivo (Eficiência)     - Pontes Guimerà-Amaral (Pi > 0.30)
   - CUSUM Quebra Estrutural       - LIME & Hold-Out Permutation   - Propagação Harmônica (alpha=0.85)
   - Causalidade Granger (FDR)     - Drift PSI/JSD/KS + Trava Youden- First-Mover Spectrum & Pontes
   +-------------------------------+-------------------------------+-------------------------------+
                                   |
                                   v
             [ Ponte com Motor Estatístico Fase 01 ]
             - Injeção das Taxas Calibradas (Se, Sp)
             - Correção Matricial Rogan & Gladen (1978)
             - Cenários 1, 2 e 3 (Raking IPF / Hamilton)
                                   |
                                   v
             [ Contrato Interoperabilidade 360º ADR-011 ]
             - Pilar 1 (Monitor Redes) -> Pilares 2, 3 e 4
             - Zero-Footprint Audit (Zero Pickle, 0 bytes /tmp)
```

---

## 2. Motor 4A: Engenharia de Features Causais e Causalidade de Agenda

Arquivo: `src/analytics/feature_engineering_and_agenda_causal_engine.py`
Classe: `FeatureEngineeringAndAgendaCausalEngine`

### 2.1. Princípio Causal Estrito (*No Look-Ahead Bias*)
Para qualquer manifestação emitida no instante $t$, toda e qualquer agregação móvel ou estatística temporal considera estritamente os eventos ocorridos no intervalo semi-aberto à direita:
$$\mathcal{E}(t) = \{ e_i \mid t - W \le t_i < t \}$$
garantindo a propriedade `closed='left'` e impedindo a contaminação da informação futura.

### 2.2. Índice de Burstiness de Goh-Barabási ($B$)
Quantifica a intermitência temporal e rajadas discursivas com base nos intervalos inter-eventos $\tau_i = t_i - t_{i-1}$:
$$B = \frac{\sigma_\tau - \mu_\tau}{\sigma_\tau + \mu_\tau} \in [-1, +1]$$
- $B \to -1$: Processo perfeitamente periódico e determinístico (suspeita de automação agendada);
- $B \to 0$: Processo estocástico de Poisson (ruído independente de memória nula);
- $B \to +1$: Comportamento fortemente em rajadas (*heavy-tailed bursty dynamics*), característico de engajamento humano orgânico apaixonado ou ataques orquestrados de alta intensidade.

### 2.3. Out-of-Fold (OOF) Empirical Bayes Target Encoding Agrupado por Autor
Para evitar vazamento de rótulos (*target leakage*) e sobreajuste (*overfitting*), o Target Encoding de variáveis categóricas $c$ é executado exclusivamente dentro dos folds de treino de um agrupamento estrito por `author_id_hash` ($\mathcal{A}_{\text{train}} \cap \mathcal{A}_{\text{val}} = \emptyset$):
$$\hat{x}_c = \frac{n_c \bar{y}_c + m \, \bar{y}_{\text{prior}}}{n_c + m}$$
onde $n_c$ é a frequência da categoria, $\bar{y}_c$ é a taxa média observada no fold de treino, $\bar{y}_{\text{prior}}$ é a média global a priori e $m$ é o parâmetro de suavização empírica de Bayes (padrão $m = 10.0$).

### 2.4. Diagnóstico de Colinearidade Multivariada (VIF)
Calculado para cada feature $j$ através da regressão linear OLS contra todas as demais:
$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$
Features com $\text{VIF}_j \ge 5.0$ são sinalizadas para mitigação ou eliminação preventiva.

### 2.5. Detector Sequencial CUSUM e Teste F de Causalidade de Granger Bivariada (`ADR-008`)
- **CUSUM:**
  $$S_t^+ = \max(0, S_{t-1}^+ + z_t - k), \quad S_t^- = \max(0, S_{t-1}^- - z_t - k)$$
  detecta pontos de inflexão estrutural abruptos no volume de postagens do Senado Federal.
- **Granger Bivariado:**
  Compara o Modelo Restrito $\text{AR}(p)$:
  $$Y_t = \alpha_0 + \sum_{k=1}^p \alpha_k Y_{t-k} + \varepsilon_t$$
  contra o Modelo Irrestrito:
  $$Y_t = \alpha_0 + \sum_{k=1}^p \alpha_k Y_{t-k} + \sum_{k=1}^p \beta_k X_{t-k} + u_t$$
  através da estatística:
  $$F = \frac{(\text{SSR}_r - \text{SSR}_{ur})/p}{\text{SSR}_{ur}/(T - 2p - 1)}$$
  com controle de taxa de falsa descoberta via **Benjamini-Hochberg FDR ($q$-value)**.

---

## 3. Motor 4B: PNL Calibrada, Explicabilidade XAI e MLOps Zero-Footprint

Arquivo: `src/analytics/calibrated_stance_xai_and_mlops_engine.py`
Classe: `CalibratedStanceXAIAndMLOpsEngine`

### 3.1. Representação Semântica Normalizada e Visão Multimodal
- **Embeddings $L_2$ Normalizados:**
  Gera vetores densos em português e normaliza na hiperesfera unitária:
  $$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}, \quad \|\hat{\mathbf{v}}\|_2 = 1.0 \pm 10^{-6}$$
  Dispositivo selecionado dinamicamente (`mps` se Apple Silicon, senão `cpu`, **zero `.cuda()` fixo**).
- **dHash Multimodal de 64 bits:**
  Calcula gradientes de intensidade horizontal $8 \times 8$ para detectar memes replicados em campanhas coordenadas via distância de Hamming.

### 3.2. Validação Anti-Leakage e Calibração Probabilística
- `StratifiedGroupKFold` garantindo $\mathcal{A}_{\text{train}} \cap \mathcal{A}_{\text{val}} = \emptyset$;
- `PurgedGroupTimeSeriesSplit` com zona de embargo temporal $\Delta_{\text{embargo}} = 6\text{h}$;
- **Métricas de Calibração Out-of-Fold:**
  $$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$$
  $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} |\text{acc}(B_b) - \text{conf}(B_b)|$$
- **Auditoria Cega ($n_{\text{val}} = 550$):**
  Produz a matriz de confusão $\hat{\mathbf{C}}_{3 \times 3}$, $\kappa$ de Cohen, Macro-F1, MCC e Teste de McNemar comparativo.

### 3.3. Explicabilidade Algorítmica Compulsória (XAI)
1. **Decomposição SHAP Aditiva:**
   Calcula $\phi_0 = \mathbb{E}[f(x)]$ e $\phi_{ij} = w_j (x_{ij} - \mu_j)$, verificando compulsoriamente o **Axioma da Eficiência de Shapley**:
   $$\left| \left( \phi_0 + \sum_{j=1}^M \phi_{ij} \right) - f(x_i) \right| < 10^{-5}$$
2. **Permutation Importance em Hold-Out Estrito:**
   Calcula a queda de performance ($\Delta \text{Macro-F1}$) permutando cada feature **exclusivamente na partição de validação congelada**. Lança `ValueError` caso invocada no treino.
3. **Auditoria de Equidade por Subgrupo (*Subgroup Fairness*):**
   Calcula $(\hat{\text{Se}}_{c,g}, \hat{\text{Sp}}_{c,g})$ entre plataformas, regiões e espectros. Se $\max |\Delta \text{Se}| > 0.08$, aciona `requires_stratified_rogan_gladen = True`.

### 3.4. Governança MLOps Zero-Footprint e Trava de Ruptura de Youden
- **Monitoramento de Drift:**
  Calcula o **Population Stability Index (PSI)**, **Divergência de Jensen-Shannon ($D_{JS}$)** e teste **KS**:
  - $\text{PSI} < 0.10 \to \text{VERDE\_ESTAVEL}$
  - $0.10 \le \text{PSI} < 0.25 \to \text{AMARELO\_ALERTA}$
  - $\text{PSI} \ge 0.25 \to \text{VERMELHO\_DRIFT\_CRITICO}$
- **Trava de Youden ($J_c \le 0.20$):**
  Se $J_c = \hat{\text{Se}}_c + \hat{\text{Sp}}_c - 1 \le 0.20$, o classificador é considerado degradado além do limite teórico de confiabilidade, bloqueando a publicação (`BLOQUEADO_PONTO_RUPTURA_YOUDEN`).
- **Model Card SHA-256:**
  Emite artefato estruturado em JSON/Parquet ZSTD contendo linhagem completa, dados de treino SHA-256 e **proibição estrita de arquivos `.pkl` ou `.joblib`**.

---

## 4. Motor 4C: Topologia de Bolhas Digitais, Câmaras de Eco e Espectros (`ADR-010`)

Arquivo: `src/analytics/digital_bubbles_and_spectrum_engine.py`
Classe: `DigitalBubblesAndSpectrumAnalyzer`

### 4.1. Barreira de Higiene Estrita do Universo Orgânico ($\mathcal{U}_{\text{Org}}$)
Antes da construção do grafo, o motor aplica filtro que descarta **100%** de itens marcados com `is_commercial_spam = True`, `account_suspected_cib = True` ou metadados hostis, contabilizando as quarentenas.

### 4.2. Grafo de Co-Engajamento Orgânico ($G = (V, E, W)$)
- Vértices $V$: contas únicas orgânicas pseudonimizadas (`author_id_hash`);
- Arestas ponderadas $w_{uv}$:
  $$w_{uv} = 2.0 \cdot |D_u \cap D_v| + 1.5 \cdot |H_u \cap H_v| + 2.5 \cdot |S_u \cap S_v| + 3.0 \cdot \mathbb{I}(C_u = C_v) + 1.0 \cdot \mathbb{I}(\text{Stance}_u = \text{Stance}_v)$$

### 4.3. Modularidade de Newman e Teste contra Modelo Nulo
$$Q = \frac{1}{2m} \sum_{i,j} \left( A_{ij} - \frac{k_i k_j}{2m} \right) \delta(c_i, c_j)$$
O teste de permutação (50 permutações preservando sequência de graus) avalia:
$$z = \frac{Q_{\text{obs}} - \mu_{Q_{\text{null}}}}{\sigma_{Q_{\text{null}}}}, \quad p = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(Q_{\text{null}}^{(b)} \ge Q_{\text{obs}})$$
classificando se a segregação em bolhas é estatisticamente significativa ($p < 0.05$).

### 4.4. Índice de Homofilia $E\text{-}I$ de Krackhardt & Stern (1988)
$$\text{EI}_c = \frac{E_c - I_c}{E_c + I_c} \in [-1, +1]$$
- $\text{EI}_c < -0.40 \to \text{CAMARA\_DE\_ECO\_FECHADA}$
- $-0.40 \le \text{EI}_c < 0.0 \to \text{BOLHA\_MODERADA\_HOMOFILICA}$
- $\text{EI}_c \ge 0.0 \to \text{DEBATE\_TRANSVERSAL\_ABERTO}$

### 4.5. Coeficiente de Participação de Pontes de Guimerà & Amaral
$$P_i = 1 - \sum_{s=1}^K \left( \frac{k_{is}}{k_i} \right)^2 \in [0, 1]$$
Contas com $P_i > 0.30$ são classificadas como Contas-Ponte Transversais (*Cross-Bubble Bridges*).

### 4.6. Propagação Harmônica Semi-Supervisionada de Espectros via Sementes
A partir de expoentes-semente parlamentares e institucionais com rótulos iniciais $\mathbf{Y}$, computa-se o Laplaciano normalizado $\mathbf{S} = \mathbf{D}^{-1/2} \mathbf{W} \mathbf{D}^{-1/2}$ e itera-se a difusão harmônica de Zhou et al. (2004) / Zhu et al. (2003):
$$\mathbf{F}^{(t+1)} = \alpha \mathbf{S} \mathbf{F}^{(t)} + (1 - \alpha) \mathbf{Y} \quad (\alpha = 0.85)$$
até convergência matricial $\|\mathbf{F}^{(t+1)} - \mathbf{F}^{(t)}\|_F < 10^{-6}$.
- **Salvaguarda Compulsória LGPD (Art. 5º, II):**
  Os vetores de afinidade individuais $\mathbf{F}^*_i$ residem exclusivamente na memória volátil durante a propagação e são descartados imediatamente após a sumarização.
  O relatório final opera sob piso de $k$-anonimato ($k \ge 5$) e **jamais expõe a lista de `author_id_hash` de cidadãos comuns por espectro**.

---

## 5. Orquestrador Unificado e Contrato de Interoperabilidade 360º (`ADR-011`)

Arquivo: `src/analytics/phase04_intelligence_orchestrator.py`
Classe: `Phase04IntelligenceOrchestrator`

O Orquestrador conecta o lago DuckDB da Fase 03, os Motores 4A, 4B e 4C e o motor estatístico da Fase 01, gerando o **Dossiê Analítico Consolidado da Fase 04** e atualizando o Contrato 360º com:
- `lexical_bias_rate_mean` (Motor 4A);
- `structural_break_cusum` (Motor 4A);
- `rogan_gladen_calibrated_favourability_pct` (Motor 4B + Fase 01);
- `newman_modularity_q` e significância estatística (Motor 4C);
- `first_mover_spectrum` (Motor 4C);
- `cross_spectrum_bridge_topics` (Motor 4C);
- `ready_for_phase05_multimodal_audio_video = True`.
