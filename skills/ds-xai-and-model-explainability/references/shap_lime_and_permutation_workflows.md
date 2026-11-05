# Valores de Shapley (SHAP), LIME e Permutation Importance em Hold-Out

Este manual técnico detalha o arcabouço matemático de métodos de inteligência artificial explicável (XAI), axiomas de jogos cooperativos e diretrizes práticas para modelos de linguagem e classificadores no Monitor de Redes DataSenado.

---

## 1. Fundamentos Teóricos dos Valores de Shapley

Os valores de Shapley (Shapley, 1953) oferecem o único método teoricamente consistente de distribuição do ganho total de um jogo cooperativo entre seus participantes sob quatro axiomas fundamentais:

1. **Eficiência (Aditividade Local):**
   $$\sum_{j=1}^M \phi_j(x) = f(x) - \mathbb{E}[f(x)]$$
   A soma das contribuições marginais de todas as features é exatamente igual à diferença entre a predição para a instância $x$ e o valor esperado base do modelo sobre a amostra de referência.
2. **Simetria:** Se duas variáveis $i$ e $j$ contribuem igualmente em todas as coalizões possíveis, então $\phi_i(x) = \phi_j(x)$.
3. **Jogador Nulo (Dummy):** Se uma variável $j$ não altera a predição quando adicionada a qualquer subconjunto de atributos, então $\phi_j(x) = 0$.
4. **Aditividade:** Se um modelo é a soma ponderada de dois submecanismos $f = g + h$, então $\phi_j(f) = \phi_j(g) + \phi_j(h)$.

### 1.1 Decomposição Exata para Modelos Lineares e Aditivos
Para modelos lineares com coeficientes $\mathbf{w}$ e preditores com média empírica $\boldsymbol{\mu}$:
$$\phi_0 = w_0 + \sum_{j=1}^M w_j \mu_j = \mathbb{E}[f(x)], \quad \phi_j(x) = w_j (x_j - \mu_j)$$
Verifica-se imediatamente a eficiência:
$$\phi_0 + \sum_{j=1}^M \phi_j(x) = w_0 + \sum_{j=1}^M w_j x_j = f(x)$$

---

## 2. Permutation Feature Importance Estritamente em Hold-Out

A importância intrínseca das variáveis calculada por árvores (como o decréscimo de impureza de Gini no treinamento) apresenta forte viés em favor de atributos contínuos ou de alta cardinalidade e sofre de sobreajuste severo.

A técnica de Permutation Feature Importance (Breiman, 2001; Fisher et al., 2019) deve ser calculada estritamente sobre a partição de teste/validação independente (*hold-out*):

### 2.1 Algoritmo de Permutação
1. Calcula-se a métrica de desempenho de referência $S_{\text{base}}$ (ex.: Macro-F1 ou MCC) sobre o conjunto de validação $(X_{\text{val}}, y_{\text{val}})$.
2. Para cada feature $j \in \{1, \dots, M\}$:
   - Realizam-se $R \ge 10$ repetições independentes com semente determinística;
   - Em cada repetição $r$, embaralham-se aleatoriamente os valores da coluna $j$ mantendo as demais colunas intactas, quebrando a relação entre $X_j$ e $y$;
   - Calcula-se o novo desempenho $S_{j, r}$;
   - A importância da feature $j$ é a perda média de desempenho:
     $$\Delta S_j = S_{\text{base}} - \frac{1}{R} \sum_{r=1}^R S_{j, r}$$
Variáveis com $\Delta S_j \approx 0$ ou negativo são irrelevantes ou ruidosas e podem ser eliminadas.

---

## 3. Interpretabilidade Textual com LIME e Atribuição de Tokens

Para classificadores neurais ou ensembles sobre textos legislativos e discursos de redes:
- **LIME (Local Interpretable Model-agnostic Explanations):** Amostra perturbações do texto ao redor da instância sob análise (removendo palavras aleatoriamente), obtém as probabilidades preditas pela caixa-preta e ajusta um modelo linear esparso localmente ponderado pela distância de Jaccard/cosseno.
- **Interpretação para o Senado:** Gera uma lista ordenada de termos com seus respectivos pesos locais:
  - Termos com peso positivo elevam a probabilidade da classe focal;
  - Termos com peso negativo amortecem ou desviam a classificação.
- **Ressalva Epistêmica:** Explicações locais refletem a mecânica interna do modelo treinado, não constituindo necessariamente comprovação de causalidade no mundo real.
