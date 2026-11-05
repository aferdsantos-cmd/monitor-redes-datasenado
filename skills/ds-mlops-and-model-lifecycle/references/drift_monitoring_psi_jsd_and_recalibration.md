# Monitoramento de Deriva de Dados (PSI, JSD, KS) e Gatilhos de Recalibração

Este documento formaliza as métricas matemáticas de detecção de deriva temporal de variáveis (Data Drift), mudança de distribuição de covariáveis (Covariate Shift) e descolamento de conceitos (Concept Drift) no Monitor de Redes DataSenado.

---

## 1. Population Stability Index (PSI)

O PSI é o padrão de referência para mensurar o afastamento entre a distribuição de uma variável na base de referência (treinamento/validação piloto $P$) e a base atual de produção (janela corrente de monitoramento $Q$).

### 1.1 Formulação Matemática
Discretiza-se a distribuição de referência em $B$ intervalos de quantis (típico $B=10$, decis). Sejam $p_b$ e $q_b$ as proporções de observações no intervalo $b$ nas amostras de referência e atual, respectivamente:

$$\text{PSI}(P, Q) = \sum_{b=1}^B (p_b - q_b) \ln\left( \frac{p_b + \epsilon}{q_b + \epsilon} \right)$$

onde $\epsilon = 10^{-6}$ é um termo de suavização para evitar divisão por zero ou logaritmo indefinido.

### 1.2 Regras de Decisão do Semáforo Operacional
- $\text{PSI} < 0.10$: **Semáforo Verde (Estável).** A distribuição da variável não sofreu alteração significante. A operação prossegue normalmente.
- $0.10 \le \text{PSI} < 0.25$: **Semáforo Amarelo (Deriva Moderada).** Há evidência de deslocamento distribucional. Emite-se alerta de monitoramento no boletim técnico interno.
- $\text{PSI} \ge 0.25$: **Semáforo Vermelho (Deriva Crítica).** Deslocamento severo de vocabulário, engajamento ou tópicos. **Gatilho compulsório:** bloqueio de predições automatizadas, recomendação de re-amostragem humana e recalibração da matriz de Rogan-Gladen.

---

## 2. Divergência de Jensen-Shannon (JSD) para Variáveis Categóricas

Para distribuições discretas (ex.: distribuição percentual entre plataformas, macrorregiões ou tópicos de discussão), utiliza-se a Divergência de Jensen-Shannon, versão simétrica e limitada da Divergência de Kullback-Leibler:

$$D_{JS}(P \parallel Q) = \frac{1}{2} D_{KL}(P \parallel M) + \frac{1}{2} D_{KL}(Q \parallel M)$$

onde $M = \frac{1}{2}(P + Q)$ é a distribuição mista.
- Propriedades: $0 \le D_{JS} \le \ln(2) \approx 0.693$; $\sqrt{D_{JS}}$ constitui uma verdadeira métrica de distância matemática.

---

## 3. Teste Kolmogorov-Smirnov (KS) para Covariáveis Contínuas

Para variáveis contínuas (ex.: comprimento de texto, escores de confiança, taxas de compartilhamento):
- O teste KS bicaudal compara as funções de distribuição acumulada empíricas $F_P(x)$ e $F_Q(x)$:
  $$D_{KS} = \sup_{x} |F_P(x) - F_Q(x)|$$
- Se $p < 0.01$ e $D_{KS} > 0.15$, há evidência estatística de descolamento distributivo da covariável.

---

## 4. Trava do Ponto de Ruptura de Rogan-Gladen em Produção

Mesmo que o classificador tenha sido calibrado na fase inicial, o surgimento de novas gírias ou ironias legislativas pode degradar a sensibilidade e especificidade ao longo do tempo.

O Teorema de Rogan-Gladen exige que o Índice de Youden satisfaça:
$$J_c = \hat{\text{Se}}_c + \hat{\text{Sp}}_c - 1 > 0.20$$
Se o monitoramento contínuo em amostras de auditoria periódica revelar que $J_c \le 0.20$:
1. A correção de prevalência perde estabilidade numérica, amplificando o erro amostral exponencialmente;
2. O validador de MLOps interrompe o pipeline com código de erro não-nulo;
3. É convocado o Chat Operador para retraining com inclusão de dados da janela recente.
