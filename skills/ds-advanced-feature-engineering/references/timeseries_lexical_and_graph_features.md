# Engenharia de Recursos para Séries Temporais, Análise Lexical e Grafos

Este documento apresenta as metodologias matemáticas para extração de atributos derivados de fluxos temporais, características textuais de posicionamento editorial e métricas topológicas de redes no Monitor de Redes DataSenado.

---

## 1. Séries Temporais em Fluxos de Mídias Sociais

O comportamento de publicação em debates legislativos apresenta sazonalidade intradia acentuada, com picos durante sessões plenárias e comissões temáticas.

### 1.1 Codificação Cíclica Trigonométrica
Variáveis circulares (hora do dia $h \in [0, 23]$ e dia da semana $d \in [0, 6]$) não devem ser tratadas como ordinais contínuas lineares, pois isso introduziria uma descontinuidade artificial entre 23:59 e 00:00. Aplica-se a projeção no círculo unitário:

$$x_{\sin} = \sin\left(\frac{2\pi \cdot h}{24}\right), \quad x_{\cos} = \cos\left(\frac{2\pi \cdot h}{24}\right)$$

Dessa forma, a distância euclidiana entre as 23h e a 0h reflete a continuidade temporal natural.

### 1.2 Janelas Deslizantes Causais e EWMA
Toda variável baseada em janela móvel sobre a série temporal de publicações deve utilizar `closed='left'`, garantindo que o valor computado para o timestamp $t$ contenha apenas dados de $[t - W, t)$:
```python
# Correto: causal (não inclui o post atual)
rolling_causal = series.shift(1).rolling(window='2h', closed='left').mean()
```

Para dar maior relevância a eventos recentes sem descartar o histórico da janela, utiliza-se a Média Móvel Exponencialmente Ponderada (EWMA):
$$\text{EWMA}_t = \alpha Y_{t-1} + (1 - \alpha) \text{EWMA}_{t-1}, \quad \alpha = \frac{2}{S + 1}$$

### 1.3 Índice de Burstiness de Goh-Barabási
Para distinguir entre atividade orgânica com intervalos irregulares e campanhas automatizadas ou bots com intervalos estritamente periódicos ($\sigma_\tau \approx 0$), computa-se o índice de burstiness:

$$B = \frac{\sigma_\tau - \mu_\tau}{\sigma_\tau + \mu_\tau} \in [-1, 1]$$

onde $\mu_\tau$ e $\sigma_\tau$ são a média e o desvio padrão dos intervalos de tempo $\tau$ entre postagens consecutivas de uma mesma conta:
- $B \to -1$: Processo periódico determinístico (forte indicativo de bot agendado);
- $B \approx 0$: Processo de Poisson livre de memória (atividade aleatória padrão);
- $B \to +1$: Comportamento com explosão (*bursty*) e cauda longa (típico de engajamento orgânico humano em eventos de choque).

---

## 2. Atributos Lexicais e de Enquadramento Editorial (ADR-011)

No contexto da inteligência editorial e posicionamento legislativo, extraem-se indicadores sintáticos e de polarização:

1. **Taxa de Modulação Subjetiva:** Proporção de adjetivos e advérbios modalizadores em relação ao total de substantivos e verbos no texto.
2. **Divergência de Kullback-Leibler Lexical ($D_{KL}$):** Mede o afastamento entre a distribuição de unigramas e bigramas de uma fonte e o vocabulário de referência neutro:
   $$D_{KL}(P \parallel Q) = \sum_{w} P(w) \ln\left(\frac{P(w)}{Q(w)}\right)$$
3. **Projeções Semânticas Normalizadas:** Vetores de representação densa normalizados na norma euclidiana ($\|\mathbf{e}\|_2 = 1$).

---

## 3. Features Topológicas de Rede (ADR-010)

Para capturar a posição estrutural de contas e nós na rede de interações orgânicas:

1. **Grau Ponderado de Entrada/Saída:** Volume acumulado de menções e repostagens.
2. **PageRank com Teletransporte ($d=0.85$):** Centralidade global considerando a autoridade dos nós conectores.
3. **Coeficiente de Clusterização Local:** Proporção de triângulos fechados entre os vizinhos do nó:
   $$C_i = \frac{2 e_i}{k_i(k_i - 1)}$$
4. **Entropia de Domínios:** Diversidade de fontes e URLs compartilhadas pela conta, calculada via entropia de Shannon sobre a distribuição de domínios.

---

## 4. Salvaguardas LGPD na Engenharia de Features
- Todas as features agregadas operam exclusivamente sobre o identificador pseudonimizado `author_id_hash`.
- Em tabelas agregadas destinadas a relatórios analíticos, aplica-se o critério de $k$-anonimato: qualquer estrato com contagem inferior a $k=5$ contas distintas deve ser mascarado ou agrupado em categoria residual.
