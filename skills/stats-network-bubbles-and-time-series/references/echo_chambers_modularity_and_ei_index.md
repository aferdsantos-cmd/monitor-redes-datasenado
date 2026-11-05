# Câmaras de Eco, Modularidade de Redes e o Índice E-I de Krackhardt & Stern

Este documento técnico formaliza os fundamentos matemáticos e estatísticos para identificação objetiva de bolhas de polarização digital e nós-ponte no debate público digital, em conformidade com a decisão arquitetural ADR-010.

---

## 1. Modularidade de Newman e Teste contra Modelo Nulo

A detecção de comunidades em redes de interação (retweets, respostas, compartilhamento conjunto de links) baseia-se na comparação entre a densidade observada de arestas internas e a densidade esperada sob um modelo aleatório.

### 1.1 Formulação da Modularidade ($Q$)
Dada uma matriz de adjacência $\mathbf{A}$ com pesos $A_{ij}$, o grau ponderado do nó $i$ é $k_i = \sum_j A_{ij}$, e o total de arestas da rede é $m = \frac{1}{2}\sum_i k_i$. Para uma partição de nós em comunidades $\mathcal{C} = \{c_1, \dots, c_N\}$:

$$Q = \frac{1}{2m} \sum_{i,j} \left( A_{ij} - \gamma \frac{k_i k_j}{2m} \right) \delta(c_i, c_j)$$

onde $\gamma$ é o parâmetro de resolução (padrão $\gamma = 1.0$) e $\delta(c_i, c_j) = 1$ se os nós $i$ e $j$ pertencem à mesma comunidade, e 0 caso contrário.

### 1.2 Teste de Significância contra o Modelo Nulo de Configuração
Valores positivos de $Q$ podem surgir espontaneamente em grafos aleatórios esparsos sem significar a existência de bolhas reais. Por isso, é obrigatório contrastar a modularidade observada $Q_{\text{obs}}$ contra uma distribuição empírica nula:
1. Geram-se $B \ge 200$ permutações aleatórias que preservam exatamente a sequência de graus da rede original (stub matching / switching model).
2. Computa-se a modularidade $Q_b$ para cada grafo nulo sob a mesma partição comunitária.
3. Calcula-se o $z$-score e o $p$-valor bicaudal:
   $$z_Q = \frac{Q_{\text{obs}} - \mu_{Q_{\text{nulo}}}}{\sigma_{Q_{\text{nulo}}}}, \quad p_Q = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(Q_b \ge Q_{\text{obs}})$$
Se $p_Q < 0.01$ e $z_Q > 3.0$, a estrutura comunitária é estatisticamente validada como não-aleatória.

---

## 2. Índice de Homofilia e Isolamento $E\text{-}I$ de Krackhardt & Stern (1988)

Enquanto a modularidade $Q$ quantifica a segregação global da rede, o Índice $E\text{-}I$ mensura o isolamento relativo de cada comunidade/bolha específica:

$$\text{EI}_c = \frac{E_c - I_c}{E_c + I_c} \in [-1, +1]$$

onde:
- $I_c = \sum_{i, j \in c} A_{ij}$ representa o volume total de conexões internas da comunidade $c$;
- $E_c = \sum_{i \in c, j \notin c} A_{ij}$ representa o volume de conexões da comunidade $c$ com o restante da rede.

### 2.1 Taxonomia Epistêmica de Câmaras de Eco
- $\text{EI}_c \le -0.40$: **Câmara de Eco Fechada (Hiper-polarizada).** Mais de 70% das interações ocorrem exclusivamente entre membros da própria bolha.
- $-0.40 < \text{EI}_c < 0.00$: **Bolha Moderada.** Há predomínio interno, mas com canais residuais de contato externo.
- $\text{EI}_c \ge 0.00$: **Comunidade Transversal / Debate Aberto.** Predomínio de conexões com outras correntes e espectros discursivos.

---

## 3. Coeficiente de Participação de Pontes de Guimerà & Amaral

Para identificar parlamentares, jornalistas, veículos ou influenciadores que atuam como "pontes" entre bolhas segregadas, calcula-se o Coeficiente de Participação ($P_i$):

$$P_i = 1 - \sum_{s=1}^{N_M} \left( \frac{k_{is}}{k_i} \right)^2 \in [0, 1]$$

onde $k_i$ é o grau total do nó $i$ e $k_{is}$ é o número de conexões do nó $i$ com a comunidade $s$:
- $P_i \to 0$: O nó é um **Hub Provincial**, cujas conexões concentram-se quase exclusivamente dentro da sua bolha.
- $P_i \to 1$: O nó é um **Conector Global (Ponte)**, distribuindo suas interações uniformemente entre múltiplas comunidades.
Identificar os nós com maior $P_i$ e alta centralidade é de valor crítico para o Senado, pois são os agentes capazes de furar bolhas e promover consenso transversal.
