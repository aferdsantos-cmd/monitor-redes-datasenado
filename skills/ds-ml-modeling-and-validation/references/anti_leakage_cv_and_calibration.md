# Validação Cruzada Anti-Leakage, Calibração de Probabilidades e Rogan-Gladen

Este manual técnico aborda a formulação e implementação de esquemas de particionamento amostral sem vazamento para debates em mídias sociais, métodos de calibração de probabilidades e a integração formal com o estimador de Rogan-Gladen no Monitor de Redes DataSenado.

---

## 1. Esquemas de Validação Cruzada em Redes Sociais

A amostragem aleatória simples (como `KFold` tradicional) é inadequada para dados de redes sociais e debates públicos digitais, pois a hipótese de observações independentes e identicamente distribuídas (i.i.d.) é violada por:
1. Múltiplos comentários oriundos da mesma conta orgânica (`author_id_hash`);
2. Estrutura temporal de propagação viral com correlação serial e contágio discursivo.

### 1.1 StratifiedGroupKFold por Conta Orgânica
Para assegurar generalização genuína sobre a população de participantes:
- A variável de agrupamento é o identificador pseudonimizado da conta: `groups = author_id_hash`;
- A partição garante disjunção absoluta de autores entre conjuntos de treino e teste:
  $$\mathcal{A}_{\text{train}} \cap \mathcal{A}_{\text{val}} = \emptyset$$
- A distribuição da variável alvo (ex.: posicionamento `Favorável`, `Contrário`, `Neutro`) é estratificada globalmente nos $K$ folds para manter o balanceamento representativo.

### 1.2 PurgedGroupTimeSeriesSplit com Embargo
Quando a dimensão cronológica é preponderante (prevenção de vazamento de tendências futuras):
- **Purging:** Elimina observações de treino cujos rótulos ou janelas móveis causais se sobrepõem ao início do período de teste.
- **Embargo ($\Delta_{\text{embargo}}$):** Introduz uma zona morta de isolamento temporal imediatamente posterior ao conjunto de treino antes de iniciar a validação (típico 6h a 24h), mitigando os efeitos de cauda de cascatas virais.

---

## 2. Calibração de Probabilidades

Modelos de aprendizado de máquina frequentemente geram saídas de probabilidade com viés sistemático (ex.: árvores de decisão e Random Forest concentram probabilidades longe de 0 e 1, enquanto boosting e redes neurais profundas tendem a gerar predições superconfiantes).

### 2.1 Métricas de Calibração
- **Brier Score:** Erro quadrático médio das probabilidades preditas em relação aos rótulos binários/one-hot:
  $$\text{BS} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$$
- **Expected Calibration Error (ECE):** Agrupa as predições em $B$ intervalos de confiança (bins) e calcula a diferença ponderada entre confiança média e acurácia empírica:
  $$\text{ECE} = \sum_{b=1}^B \frac{|B_b|}{N} \left| \text{acc}(B_b) - \text{conf}(B_b) \right|$$

### 2.2 Métodos de Calibração
1. **Regressão Logística de Platt (Sigmoide):** Ajusta parâmetros $A$ e $B$ tal que $\hat{p}_i = \frac{1}{1 + \exp(A \cdot f(x_i) + B)}$, ideal quando o erro de calibração é aproximadamente monotônico e sigmoidal.
2. **Regressão Isotônica:** Ajusta uma função escada monotônica não-paramétrica que minimiza a soma dos quadrados dos desvios, recomendada para amostras maiores ($n \ge 500$).
- **Regra de Ouro:** A calibração deve ser ajustada estritamente fora da partição de treino (via *out-of-fold predictions*), nunca no mesmo conjunto usado para aprender os pesos do classificador.

---

## 3. Ponte Estatística com o Estimador de Rogan-Gladen

O classificador algorítmico atua como um teste diagnóstico imperfeito. De acordo com o Teorema de Rogan-Gladen (1978), a prevalência aparente $\hat{P}^*$ não reflete a prevalência real $\hat{P}$ sem correção pelos erros de classificação:

$$\hat{P} = \frac{\hat{P}^* + \hat{\text{Sp}} - 1}{\hat{\text{Se}} + \hat{\text{Sp}} - 1}$$

### 3.1 Requisitos de Entrada para a Skill `stats-inference-datasenado`
1. A matriz de confusão $\hat{\mathbf{C}} \in \mathbb{R}^{K \times K}$ e os vetores de sensibilidade $\hat{\text{Se}}$ e especificidade $\hat{\text{Sp}}$ devem ser derivados de uma partição de validação humana cega com $n_{\text{val}} = 550$ anotações independentes.
2. Condição de Ponto de Ruptura de Youden: $\hat{\text{Se}}_c + \hat{\text{Sp}}_c - 1 > 0.20$ para todas as classes $c$. Se o critério falhar, o modelo é epistemologicamente inválido para calibração de prevalência pública.
