# Plano de Validação Estatística, Estimando Formal e Hipóteses Falsificáveis (TCC & DataSenado)

> **Propósito deste Documento (Revisão `v1.2-fase01`):** Atender integralmente aos achados `C-01`, `E-01` a `E-10` e `M-01` a `M-06` da 2ª Rodada de Auditoria Científica da Fase 01, formalizando matematicamente o estimando, o desenho de sorteio de contas, as hipóteses científicas revisadas e os protocolos de validação empírica.

---

## 1. Formalização Matemática do Estimando e Fontes de Incerteza (`C-01`)

### 1.1. Definição dos Universos e do Estimando Primário ($\theta_T$)
Para eliminar qualquer ambiguidade entre o universo observado nas plataformas e a população demográfica brasileira (*Meng, 2018; Elliott & Valliant, 2017*):

```text
θ_T = (1 / |𝒰_Org,T|) Σ_{i ∈ 𝒰_Org,T} 1[stance_i = Favorável]
Estimador baseado no sorteio interno de contas (s ⊂ 𝒰_Org,T):
  θ̂_T = (Σ_{i ∈ s} d_i ŷ_i) / (Σ_{i ∈ s} d_i),   onde d_i = 1 / π_i  (π_i = n_h / N_h > 0)
Correção de erro de classificação (Rogan & Gladen, 1978):
  θ̃_T = (θ̂_T − FPR) / (TPR − FPR)   [truncado em [0,1] e normalizado no simplex multiclasse]
```

### 1.2. Declaração Obrigatória de Fontes de Incerteza
1. **O que os Intervalos de Confiança Quantificam:**
   - **(a)** A incerteza estatística interna decorrente do sorteio probabilístico estratificado de contas ($s \subset \mathcal{U}_{\text{Org}, T}$) com correção para população finita ($\text{FPC} = 1 - n/N_{\text{Org}}$) e da variabilidade de reamostragem bootstrap estratificada;
   - **(b)** O ajuste de erro de classificação automatizada medido contra anotação humana.
2. **O que os Intervalos NÃO Quantificam:**
   - Não quantificam viés de autosseleção da coleta (*quem decide publicar vs. quem apenas lê*), viés algorítmico das plataformas digitais nem o silêncio de cidadãos desconectados.
3. **Natureza do Cenário 3 (Reponderado — Sensibilidade sob Hipótese de Ignorabilidade):**
   - O Cenário 3 aplica *Iterative Proportional Fitting (Raking)* com *Weight Trimming* $[0,25; 4,00]$ usando pesos normativos de referência de uso de plataformas e macrorregiões do IBGE. Ele é reportado exclusivamente como **análise de sensibilidade sob a hipótese não testável de ignorabilidade condicional**, acompanhado sempre do seu `calibration_status` (`CALIBRADO_OK` ou `NAO_ATINGIDA_LIMITADA_POR_TRIMMING`).

---

## 2. Protocolo de Validação do Detector de Indícios de CIB (`C-02`, `C-03`, `M-03`, `M-06`)

### 2.1. Separação entre Teste de Software (Sintético) e Validação Científica (Corpus Anotado)
- **Teste de Software (`pytest` / `pilot_audit_runner.py`):** Verifica determinismo, ausência de regressões e comportamento sob cenários adversariais controlados:
  - *Cenário Adversarial T2 (Notícia Viral Orgânica):* 300 cidadãos compartilhando a mesma reportagem de portal jornalístico (*allowlist*) ao longo de 6 horas $\implies \text{Taxa de Falso Positivo CIB} \le 5\%$ (medido: $0,0\%$).
  - *Cenário Adversarial T1 (Rajada de Copypasta e URL Não-Jornalística):* 35 contas em rajada sincronizada $\le 45\text{s}$ $\implies \text{Recall CIB} \ge 90\%$ (medido: $100,0\%$) e $0$ contas automatizadas sobreviventes em $\mathcal{U}_{\text{Org}}$.
  - *Cenário Adversarial T3 (Paráfrase Pura Espaçada sem URL/Hashtags):* Reconhecido e documentado explicitamente como **limitação conhecida** da camada léxica/LSH (recall esperado $= 0\%$ na ausência de embeddings densos + ANN, previsto como extensão para a Fase 04).
- **Análise de Sensibilidade do Índice Heurístico (`coordination_signal_index`):**
  - Os pesos base $(0,30; 0,25; 0,20; 0,15; 0,10)$ e o limiar $0,50$ constituem um **índice heurístico experimental de sinal de coordenação** (e não probabilidade de robô), devendo ser avaliados com perturbação de $\pm 0,10$ nos pesos sobre amostra real anotada na Fase 04.

---

## 3. Hipóteses Científicas Falsificáveis Revisadas (`M-02`, `E-04`, `E-09`)

1. **Hipótese $H_1$ (Efeito de Desinfecção e Desduplicação por Conta com Amostras Dependentes):**
   *A diferença absoluta $\Delta = |\hat{p}_{\text{bruto}} - \hat{p}_{\text{C1, limpo}}|$ entre a proporção de posicionamento no volume bruto de postagens e a proporção consolidada por conta orgânica ($\mathcal{U}_{\text{Org}}$), estimada via **bootstrap pareado em nível de conta** (respeitando a dependência estrutural entre o conjunto bruto e seu subconjunto limpo), excede o limiar de relevância prática pré-especificado de $\delta = 5,0\text{ pontos percentuais}$ (isto é, o limite inferior do IC 95% bilateral de $|\Delta|$ supera $5,0\text{ p.p.}$).*

2. **Hipótese $H_2$ (Heterogeneidade Inter-Plataformas com Tamanho de Efeito e Correção de Holm):**
   *A distribuição de posicionamento legislativo ($\text{Favorável}, \text{Contrário}, \text{Neutro}$) nas contas orgânicas ($\mathcal{U}_{\text{Org}}$) difere significativamente entre as plataformas digitais ($\chi^2$ de Pearson intraplataforma ajustado pelo $DEFF$, com $p < 0,05$ após correção de **Holm-Bonferroni** para múltiplos testes) e apresenta tamanho de efeito não-trivial (**$V\text{ de Cramér} \ge 0,10$**).*

3. **Hipótese $H_3$ (Sensibilidade de Reponderação e Desempate Modal):**
   *O deslocamento absoluto $|\hat{\theta}_{\text{C3}} - \hat{\theta}_{\text{C1}}|$ produzido pela reponderação sob limites de trimming $[0,25; 4,00]$ é superior à variação interna induzida pela escolha da regra de desempate modal de contas (`neutral_tie` vs. `last_post` vs. `fractional`), demonstrando que a composição de plataformas domina a incerteza de agregação intra-conta.*

4. **Hipótese $H_4$ (Concordância Inter-Anotadores e Validação do Classificador NLP):**
   *Em uma amostra aleatória estratificada de no mínimo $n_{\text{val}} = 300$ contas orgânicas (dimensionada para garantir meia-largura do IC 95% de $\kappa$ inferior a $\pm 0,05$), o classificador de posicionamento legislativo atinge concordância **substancial** ($0,61 \le \kappa \text{ de Cohen} \le 0,80$, segundo a escala de Landis & Koch, 1977; meta operacional $\kappa \ge 0,70$ e $\alpha \text{ de Krippendorff} \ge 0,70$) em relação ao consenso de dois anotadores humanos independentes, sem ultrapassar o teto de concordância humano-humano ($\kappa_{\text{HH}}$).*

---

## 4. Pré-Registro Qualitativo de Benchmarks Externos (`M-02`)

Dado que o projeto piloto analisa um número reduzido de proposições legislativas ($K = 2$ temas iniciais), a comparação com fontes externas do Congresso Nacional possui natureza de **estudo de caso de validade convergente/divergente qualitativa** (sem poder estatístico para inferência assintótica sobre o MAE entre temas):

1. **Situação de Tramitação Verificada dos Temas Piloto:**
   - **Tema 1 (`pl_ia_2338`):** O **PL 2338/2023** (Marco Legal da Inteligência Artificial) foi aprovado pelo Plenário do Senado Federal em dezembro de 2024 e remetido à Câmara dos Deputados, mantendo histórico consolidado de consulta pública no Portal **e-Cidadania** do Senado e debates contínuos nas duas Casas.
   - **Tema 2 (`pec_escala_6x1`):** O debate sobre o fim da escala 6x1 ganhou tração na Câmara dos Deputados (PEC 8/2025) e em proposições correlatas e audiências da Comissão de Direitos Humanos (CDH) e Comissão de Assuntos Sociais (CAS) no Senado Federal.
2. **Critério Pré-Registrado de Comparação:**
   - Documentar descritivamente as diferenças entre (a) o placar da consulta pública aberta no **e-Cidadania**, (b) os levantamentos probabilísticos telefônicos do **DataSenado** (quando disponíveis para o tema) e (c) os nossos Cenários C1, C2 e C3, avaliando se picos temporais de `Suspeita_CIB_Automacao` coincidem com mutirões de votação digital sem jamais reivindicar que o Cenário 3 "reproduz" a pesquisa telefônica nacional.
