# Referência Matemática e Fórmulas Invariantes (Estatística & Amostragem)

Este documento consolida as formulações matemáticas rigorosas e contratos algorítmicos implementados nos módulos `src/sampling/stratified_sampler.py` e `src/stats/opinion_inference_engine.py`.

---

## 1. Dimensionamento e Alocação Amostral

### 1.1. Dimensionamento Operacional de Cochran com FPC e DEFF
Para um nível de confiança $1 - \alpha$ (com quantil normal $Z_{\alpha/2}$), proporção esperada $p = 0.50$, margem de erro operacional $e$, e fator de efeito de desenho antecipado $\text{DEFF}_{\text{esp}}$:
$$n_0 = \frac{Z_{\alpha/2}^2 \cdot p(1 - p) \cdot \text{DEFF}_{\text{esp}}}{e^2}$$

Com a Correção de População Finita (FPC) sobre o total de contas orgânicas $N_{\text{Org}}$:
$$n = \left\lceil \frac{n_0}{1 + \frac{n_0 - 1}{N_{\text{Org}}}} \right\rceil$$

### 1.2. Alocação Exata de Hamilton (Método do Maior Resto)
A alocação proporcional exata por estrato $h \in \{1, \dots, H\}$ evita distorções de arredondamento garantindo $\sum_{h=1}^H n_h = n$:
1. Cota contínua: $q_h = n \cdot \frac{N_h}{N_{\text{Org}}}$.
2. Parte inteira piso: $n_h^{(0)} = \lfloor q_h \rfloor$.
3. Resto fracionário: $r_h = q_h - n_h^{(0)}$.
4. Déficit de alocação: $R = n - \sum_{h=1}^H n_h^{(0)}$.
5. Ordenam-se os estratos decrescentemente por $r_h$ e adiciona-se $+1$ aos $R$ primeiros estratos:
   $$n_h = n_h^{(0)} + \mathbb{I}(h \in \text{Top-}R(r))$$

### 1.3. Probabilidade de Inclusão e Pesos de Desenho
Para cada conta $i$ pertencente ao estrato $h$:
$$\pi_i = \frac{n_h}{N_h}, \qquad d_i = \frac{1}{\pi_i} = \frac{N_h}{n_h}$$

---

## 2. Efeito de Desenho (DEFF) e Tamanho Efetivo de Amostra

### 2.1. DEFF de Kish (1965, 1992)
O aumento de variância devido à dispersão de pesos amostrais $w_i$:
$$\text{DEFF}_{\text{Kish}} = 1 + \text{CV}^2(w) = \frac{n \sum_{i=1}^n w_i^2}{\left( \sum_{i=1}^n w_i \right)^2}$$
$$n_{\text{eff}} = \frac{n}{\text{DEFF}_{\text{Kish}}}$$

---

## 3. Correção de Erro de Classificação (Rogan & Gladen, 1978)

Dado um classificador NLP automatizado com Sensibilidade ($\text{TPR}$) e Especificidade ($\text{TNR} = 1 - \text{FPR}$) estimadas via validação humana:
$$\tilde{\theta}_T = \text{clip}\left( \frac{\hat{\theta}_T + \text{TNR} - 1}{\text{TPR} + \text{TNR} - 1}, 0, 1 \right)$$
Onde $\hat{\theta}_T$ é a prevalência aparente ponderada da categoria favorável:
$$\hat{\theta}_T = \frac{\sum_{i \in s} w_i \cdot \mathbb{I}(\hat{y}_i = \text{Favorável})}{\sum_{i \in s} w_i}$$

---

## 4. Raking IPF com Truncamento no Simplex Limitado (Cenário 3)

No Cenário 3 (Reponderado), o algoritmo de Raking Bivariado (*Deming & Stephan, 1940*) calibra pesos para satisfazer as margens normativas de plataforma e macrorregião geográfica.

### 4.1. Projeção no Simplex Truncado Dentro do Laço
A cada ajuste de margem $m$:
1. Atualização multiplicativa: $w_i^{(t)} = w_i^{(t-1)} \cdot \frac{T_m}{\sum_{j \in m} w_j^{(t-1)}}$.
2. Truncamento pontual (*Kish, 1992; Valliant et al., 2018*):
   $$w_i^{\text{clip}} = \max\left(w_{\min}, \min\left(w_{\max}, w_i^{(t)}\right)\right), \quad \text{com } [w_{\min}, w_{\max}] = [0.25, 4.00]$$
3. Projeção iterativa no simplex para restaurar $\sum_{i=1}^n w_i = n$ mantendo os limites $[w_{\min}, w_{\max}]$.
4. **Critério de Convergência:** Discrepância percentual máxima entre margem obtida e alvo $\le 0.01$ (1 p.p.).
   - Se convergir: `calibration_status = "CALIBRADO_OK"`.
   - Se o truncamento impedir convergência estrita: `calibration_status = "NAO_ATINGIDA_LIMITADA_POR_TRIMMING"`.

---

## 5. Incerteza Amostral e Testes de Hipóteses

### 5.1. Bootstrap Estratificado de Contas em Chunks
- Para $b = 1, \dots, B$ (com $B \ge 1000$):
  - Em cada estrato $h$, sorteia-se com reposição $n_h$ contas da amostra estratificada $s_h$.
  - O cálculo é vetorizado em lotes de 500 réplicas (*chunks*) para garantir tempo de execução rápido e consumo mínimo de memória.
- O Intervalo de Confiança não paramétrico de 95% é extraído pelos percentis empíricos $[2.5\%, 97.5\%]$.

### 5.2. Teste $\chi^2$ de Homogeneidade Intraplataforma e V de Cramér
- Avalia independência entre posicionamento e plataforma sem utilizar pesos marginais externos de plataforma:
  $$\chi^2 = \sum_{k=1}^K \sum_{c=1}^C \frac{(O_{kc} - E_{kc})^2}{E_{kc}}$$
- Tamanho de efeito $V$ de Cramér:
  $$V = \sqrt{\frac{\chi^2}{n \cdot (\min(K, C) - 1)}}$$
- Correção de multiplicidade: Os $p$-valores das comparações categoria-a-categoria são ajustados via algoritmo de Holm-Bonferroni:
  $$p_{(i)}^{\text{adj}} = \min\left(1, \max_{j \le i} \left[ (m - j + 1) \cdot p_{(j)} \right]\right)$$
