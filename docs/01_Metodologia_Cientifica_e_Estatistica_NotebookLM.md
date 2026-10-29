# Fundamentação Metodológica e Científica: Monitoramento do Debate Público Digital com Validade Estatística (TCC & DataSenado)

> **Propósito deste Documento (Revisão `v1.2-fase01`):** Consolida a fundamentação teórica, estatística e computacional do projeto para servir como **fonte primária no Gemini NotebookLM** (*caderno "Pós-graduação - Ciências de Dados"*) e como base metodológica do TCC e de aplicações futuras no **Instituto de Pesquisa DataSenado**.

---

## 1. Delimitação do Objeto Científico e Formalização do Estimando

O ponto de partida deste projeto é a distinção rigorosa entre **pesquisas amostrais probabilísticas da população geral** e **inferência sobre o debate público digital observado** (*Bethlehem, 2010; Baker et al., 2013; Elliott & Valliant, 2017; Meng, 2018*):

1. **Pesquisa de Opinião Pública Populacional ($\mathcal{U}_{\text{Pop}}$ — Padrão CATI DataSenado):**
   - Mede a população de cidadãos brasileiros ($\ge 16$ anos) mediante sorteio probabilístico ativo com probabilidades de inclusão conhecidas na população demográfica.
2. **Monitoramento Estatístico do Debate Público Digital ($\mathcal{U}_{\text{Org}, T}$ — Objeto deste Projeto):**
   - Mede o **Universo Finito Observado de Contas Digitais Orgânicas ($\mathcal{U}_{\text{Org}, T}$)** que emitiram manifestações públicas sobre o tema legislativo $T$ nas plataformas monitoradas após a remoção de spam comercial e de contas com indício de coordenação inautêntica (CIB).
   - **Unidade Observacional:** **`1 Autor Digital Orgânico por Plataforma = 1 Unidade Observacional`**.

### Declaração Formal do Estimando Primário ($\theta_T$)
Seja $\mathcal{U}_{\text{Org}, T}$ o conjunto de $N_{\text{Org}} = |\mathcal{U}_{\text{Org}, T}|$ contas orgânicas observadas na janela. Quando uma sub-amostra estratificada $s \subset \mathcal{U}_{\text{Org}, T}$ de tamanho $n$ é sorteada internamente pelo pesquisador com probabilidades de inclusão conhecidas $\pi_i = n_h / N_h > 0$ (para classificação via LLM), o estimando primário e seu estimador de Hájek baseado no desenho são:

$$\theta_T = \frac{1}{N_{\text{Org}}} \sum_{i \in \mathcal{U}_{\text{Org}, T}} y_i, \qquad \hat{\theta}_T = \frac{\sum_{i \in s} d_i \hat{y}_i}{\sum_{i \in s} d_i}, \quad \text{com } d_i = \frac{1}{\pi_i}$$

Para corrigir o viés decorrente da taxa de sensibilidade ($\text{TPR}$) e falsos positivos ($\text{FPR} = 1 - \text{TNR}$) do classificador automatizado medida na amostra de validação humana, aplica-se a correção clássica de **Rogan & Gladen (1978)**:

$$\tilde{\theta}_T = \frac{\hat{\theta}_T - \text{FPR}}{\text{TPR} - \text{FPR}}$$

> **Cláusula de Escopo Inferencial:** Os intervalos de confiança reportados pelo sistema quantificam **(a) a incerteza estatística interna do sorteio estratificado de contas / reamostragem bootstrap** e **(b) o erro de classificação**. Não constituem margem de erro demográfica populacional e não quantificam viés de autosseleção da coleta, viés algorítmico das plataformas ou o silêncio de não usuários.

---

## 2. Coleta com Neutralidade Lexical e Amostragem de Contas

### 2.1. Neutralidade Lexical e Trade-off de Cobertura (Recall)
Para mitigar o viés de captura ideológica sem incorrer em viés de elite (que ocorreria se buscássemos apenas o número formal do projeto), o bloco `collection_query_terms` do [`config/settings.yaml`](../config/settings.yaml) combina **designações formais** (`"PL 2338"`, `"PEC escala 6x1"`) e **expressões descritivas populares neutras** (`"lei da inteligência artificial"`, `"regular a IA"`, `"fim da escala 6x1"`), deixando marcadores valorativos (`nlp_stance_taxonomy`) estritamente para a pós-classificação.

### 2.2. Ordem Estrita do Fluxo Amostral e Alocação de Hamilton
O pipeline segue rigorosamente a sequência:
$$\text{Coleta Observacional} \longrightarrow \text{Desinfecção (Spam + CIB em nível de conta)} \longrightarrow \text{Quadro Limpo } \mathcal{U}_{\text{Org}} (N_{\text{Org}}) \longrightarrow \text{Sorteio Estratificado de Contas } s (n)$$

- **Estratos Completos com Fuso Horário (`America/Sao_Paulo`):** As contas são estratificadas por `Plataforma × Turno Horário Modal × Dia` convertendo todos os timestamps para `ZoneInfo("America/Sao_Paulo")`.
- **Dimensionamento Operacional de Cochran com $DEFF$ Esperado:** $n_0 = \frac{Z_{\alpha/2}^2 \cdot p(1-p) \cdot DEFF_{\text{esp}}}{e^2}$, ajustado por correção de população finita sobre $N_{\text{Org}}$.
- **Alocação Inteira Exata (Método do Maior Resto de Hamilton):** Garante matematicamente que $\sum_h n_h = n$, tanto na alocação proporcional quanto na alocação ótima de Neyman.

---

## 3. Pseudonimização LGPD, Quarentena de Spam e Detecção de Indícios de CIB

### 3.1. Pseudonimização por `HMAC-SHA256` (*Fail-Closed*) e Proxy DDD
- **Pseudonimização (LGPD art. 13, §4º):** Identificadores de contas são transformados via `HMAC-SHA256` (64 caracteres hexadecimais) com chave secreta carregada do `.env` ($\ge 32$ caracteres, abortando em modo *fail-closed* se ausente). O campo `raw_author_id` é imediatamente esvaziado em memória e registra-se o identificador auditável `hmac_key_id` (8 hex). Como o titular de uma conta pública permanece reidentificável por quem detém a chave ou por busca reversa de texto literal, tratam-se os registros como **dados pessoais pseudonimizados** (nunca publicando textos literais de cidadãos comuns nos boletins e truncando timestamps à hora nos arquivos derivados).
- **Proxy Geográfico Aproximado (DDD):** Rejeita explicitamente números com DDI estrangeiro (`+1`, `+44`, etc.) e extrai apenas códigos DDD brasileiros (`+55 DD`), documentados como aproximação ecológica sujeita a portabilidade interestadual.

### 3.2. Quarentena de Spam Comercial e Simetria Cívica (NFKD)
- **Proteção de Contexto Legislativo:** Textos contendo pistas comerciais são movidos para quarentena (`is_commercial_spam = True` com `spam_quarantine_reason` registrado, sem deleção silenciosa), mas **protegendo explicitamente** vocábulos do debate parlamentar (*"sorteio do relator"*, *"CPI das apostas esportivas"*, *"legalização do cassino"*, *"plenário"*).
- **Simetria Unicode NFKD e 5 Classes:** Após decomposição canônica NFKD (garantindo reconhecimento idêntico para `"Vote SIM"` e `"Vote NÃO"` com til), a classe `Mobilizacao_Civica_Legitima` exige marcador cívico explícito sem sincronia mecânica, enquanto *near-duplicates* assíncronos sem marcador cívico recebem a classe neutra `Repeticao_Organica`.

### 3.3. Busca Sub-Quadrática Esperada via LSH e Grafo de Co-Compartilhamento Repetido
Para evitar a alta taxa de falsos positivos de detectores ingênuos (*Rauchfleisch & Kaiser, 2020; Cresci, 2020*):
1. **LSH + Verificação Exata de Jaccard + Union-Find (*Broder, 1997; Leskovec, Rajaraman & Ullman*):** Pares candidatos retornados pelo `MinHashLSH` (128 permutações) têm sua similaridade de Jaccard verificada (`mh_i.jaccard(mh_j) >= 0.85`) e são agrupados via *Union-Find*, com varredura temporal *two-pointer* de complexidade sub-quadrática esperada $O(N \cdot \bar{b})$.
2. **Allowlist de Imprensa/Governo, IDF e Repetição de Co-Compartilhamento (*Giglietto et al., 2020; Pacheco et al., 2021*):**
   - Links de portais oficiais (`senado.leg.br`, `camara.leg.br`, `gov.br`) e grandes veículos de imprensa (`g1.globo.com`, `uol.com.br`, `folha.uol.com.br`, etc.) entram em *allowlist* para que o compartilhamento orgânico de notícias virais por cidadãos ao longo do dia **não gere falsos positivos de CIB**.
   - Pares de hashtags com frequência documental $> 35\%$ das contas (tags oficiais do tema, como `#PL2338`) são filtrados e as demais recebem ponderação IDF.
   - Uma aresta no grafo para o **Algoritmo de Leiden** (`igraph` + `leidenalg`, *Traag et al., 2019*) só é consolidada quando o par de contas co-compartilha repetidamente sinais/eventos ou atua em rajada de alta densidade.
3. **Política de Exclusão em Nível de Conta e Índice de Sinal de Coordenação:**
   Calcula-se o índice heurístico experimental `coordination_signal_index` ($\in [0, 1]$). Se uma conta possui $\ge 2$ postagens sinalizadas ou $\ge 30\%$ de suas publicações sinalizadas, **toda a conta** recebe `account_suspected_cib = True`, impedindo que postagens residuais de uma conta automatizada entrem em $\mathcal{U}_{\text{Org}}$.

---

## 4. Os 3 Cenários, Raking IPF com *Trimming* no Laço e Homogeneidade Inter-Plataformas

1. **Cenário 1 — Indicador Orgânico de Contas ($\mathcal{U}_{\text{Org}}$):** Proporção estimada sobre as contas orgânicas (com pesos de desenho $d_i = 1/\pi_i$ e versão corrigida por Rogan-Gladen).
2. **Cenário 2 — Indicador Equilibrado por Plataforma ($w_k = 1/K$):** Dá peso igual a cada plataforma monitorada.
3. **Cenário 3 — Reponderado (Sensibilidade sob Hipótese de Ignorabilidade):**
   - Aplica *Iterative Proportional Fitting (Raking)* (*Deming & Stephan, 1940; Kalton & Flores-Cervantes, 2003*) com **Truncamento de Pesos (*Weight Trimming* em $[0,25; 4,00]$, *Kish, 1992; Valliant, Dever & Kreuter, 2018*) dentro de cada iteração do laço** via projeção no simplex limitado.
   - Exporta a tabela completa de margens (`target_pct`, `obtained_pct`, `abs_gap_pp`) e o `calibration_status` (`CALIBRADO_OK` quando o gap máximo $\le 1\text{ p.p.}$, ou `NAO_ATINGIDA_LIMITADA_POR_TRIMMING` quando os limites $[0,25; 4,00]$ impedem matematicamente atingir uma margem extrema).
4. **Bootstrap Não Paramétrico Estratificado de Contas (em *Chunks*) e Teste de Homogeneidade:**
   - Reamostragem estratificada por plataforma processada em lotes de 500 réplicas (*chunks* de memória controlada).
   - Teste de homogeneidade entre plataformas calculado **sem pesos marginais de plataforma** via **$\chi^2$ de Pearson ajustado pelo $DEFF$ intraplataforma (aproximação de 1ª ordem)**, reportando o **Tamanho de Efeito $V$ de Cramér** e $p$-valores por categoria corrigidos pelo método de **Holm-Bonferroni**.

---

## 5. Referências Bibliográficas Incorporadas
1. **Baker, R., Brick, J. M., Bates, N. A., et al. (2013).** *Summary Report of the AAPOR Task Force on Non-probability Sampling*. Journal of Survey Statistics and Methodology, 1(2), 90–143.
2. **Bethlehem, J. (2010).** *Selection Bias in Web Surveys*. International Statistical Review, 78(2), 161–188.
3. **Broder, A. Z. (1997).** *On the Resemblance and Containment of Documents*. Compression and Complexity of Sequences, IEEE, 21–29.
4. **Cresci, S. (2020).** *A Decade of Social Bot Detection*. Communications of the ACM, 63(10), 72–83.
5. **Deming, W. E., & Stephan, F. F. (1940).** *On a Least Squares Adjustment of a Sampled Frequency Table When the Expected Marginal Totals are Known*. Annals of Mathematical Statistics, 11(4), 427–444.
6. **Elliott, M. R., & Valliant, R. (2017).** *Inference for Nonprobability Samples*. Statistical Science, 32(2), 249–264.
7. **Giglietto, F., Righetti, N., Rossi, L., & Marino, G. (2020).** *It takes a village to manipulate the media: coordinated link sharing behavior*. Information, Communication & Society.
8. **Kalton, G., & Flores-Cervantes, I. (2003).** *Weighting Methods*. Journal of Official Statistics, 19(2), 81–97.
9. **Kish, L. (1965).** *Survey Sampling*. New York: John Wiley & Sons.
10. **Kish, L. (1992).** *Weighting for Unequal $P_i$*. Journal of Official Statistics, 8(2), 183–200.
11. **Landis, J. R., & Koch, G. G. (1977).** *The Measurement of Observer Agreement for Categorical Data*. Biometrics, 33(1), 159–174.
12. **Leskovec, J., Rajaraman, A., & Ullman, J. D. (2020).** *Mining of Massive Datasets* (3rd ed., Cap. 3: Locality-Sensitive Hashing). Cambridge University Press.
13. **Lumley, T. (2010).** *Complex Surveys: A Guide to Analysis Using R*. John Wiley & Sons.
14. **Meng, X.-L. (2018).** *Statistical Paradises and Paradoxes in Big Data (I): Law of Large Populations, Big Data Paradox, and the 2016 US Presidential Election*. The Annals of Applied Statistics, 12(2), 685–726.
15. **Pacheco, D., Hui, P. M., Torres-Lugo, C., Truong, B. T., Flammini, A., & Menczer, F. (2021).** *Uncovering Coordinated Networks on Social Media: Methods and Case Studies*. ICWSM, 15, 455–466.
16. **Rao, J. N. K., & Scott, A. J. (1981).** *The Analysis of Categorical Data From Complex Sample Surveys*. JASA, 76(374), 221–230.
17. **Rao, J. N. K., & Scott, A. J. (1984).** *On Chi-Squared Tests for Multiway Contingency Tables with Cell Proportions Estimated from Survey Data*. Annals of Statistics, 12(1), 46–60.
18. **Rao, J. N. K., & Wu, C. F. J. (1988).** *Resampling Inference with Complex Survey Data*. JASA, 83(401), 231–241.
19. **Rauchfleisch, A., & Kaiser, J. (2020).** *The False Positive Problem of Automatic Bot Detection in Social Science Research*. PLoS ONE, 15(10), e0241045.
20. **Rogan, W. J., & Gladen, B. (1978).** *Estimating Prevalence from the Results of a Screening Test*. American Journal of Epidemiology, 107(1), 71–76.
21. **Traag, V. A., Waltman, L., & van Eck, N. J. (2019).** *From Louvain to Leiden: guaranteeing well-connected communities*. Scientific Reports, 9(1), 5233.
22. **Valliant, R., Dever, J. A., & Kreuter, F. (2018).** *Practical Tools for Designing and Weighting Survey Samples* (2nd ed.). Springer.
