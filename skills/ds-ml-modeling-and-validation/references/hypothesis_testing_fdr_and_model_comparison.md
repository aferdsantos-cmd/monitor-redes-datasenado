# Testes de Hipóteses, Controle de FDR e Comparação de Modelos

Este documento formaliza os procedimentos estatísticos rigorosos para seleção de preditores, auditoria de deriva (*drift*) e comparação pareada de classificadores no Monitor de Redes DataSenado.

---

## 1. Árvore de Decisão para Testes de Hipóteses

Antes de aplicar qualquer teste inferencial entre grupos (ex.: diferenças de engajamento por espectro político, comparação de tempos de resposta entre plataformas ou taxas de erro por canal), deve-se verificar formalmente os pressupostos distributivos:

```text
[Verificação de Pressupostos]
  ├── Teste de Normalidade (Shapiro-Wilk se n <= 5000, D'Agostino-Pearson se n > 5000)
  └── Teste de Homocedasticidade (Levene para variâncias iguais)
        │
        ├── Se Normal E Variâncias Iguais:
        │     └── 2 Grupos: Student's t-test
        │     └── >2 Grupos: ANOVA unidirecional
        │
        ├── Se Normal E Variâncias Heterogêneas:
        │     └── 2 Grupos: Welch's t-test
        │     └── >2 Grupos: Welch's ANOVA
        │
        └── Se Não-Normal:
              └── 2 Grupos: Mann-Whitney U test (amostras independentes) / Wilcoxon (pareadas)
              └── >2 Grupos: Kruskal-Wallis H test (não-paramétrico)
              └── Comparação de Distribuições Contínuas: Kolmogorov-Smirnov (KS test)
```

---

## 2. Controle da Taxa de Falsas Descobertas (FDR — Benjamini & Hochberg, 1995)

Quando dezenas de testes de significância são executados simultaneamente (ex.: comparar dezenas de termos de busca ou centenas de cruzamentos de plataformas e turnos), o nível de significância nominal $\alpha = 0.05$ gera um acúmulo severo de falsos positivos pelo problema da multiplicidade (P-hacking acidental).

O procedimento de Benjamini-Hochberg (BH) controla a proporção esperada de falsas descobertas entre os testes declarados significantes ($\text{FDR} \le \alpha$):

### 2.1 Algoritmo de Benjamini-Hochberg
1. Executam-se os $m$ testes de hipótese e obtêm-se os $p$-valores: $p_1, p_2, \dots, p_m$.
2. Ordenam-se os $p$-valores em ordem crescente:
   $$p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$$
3. Encontra-se o maior índice $k$ tal que:
   $$p_{(k)} \le \frac{k}{m} \alpha$$
4. Rejeitam-se todas as hipóteses nulas $H_{(1)}, \dots, H_{(k)}$.
5. Os valores $q$ ajustados são calculados cumulativamente como:
   $$q_{(i)} = \min_{j \ge i} \left( \frac{m}{j} p_{(j)}, 1 \right)$$

---

## 3. Comparação Estatística Pareada de Classificadores (Teste de McNemar)

Para verificar se um novo modelo supervisionado $M_B$ apresenta melhora estatisticamente significante sobre o modelo baseline $M_A$ na mesma partição de validação, a simples comparação pontual de acurácia é metodologicamente inválida.

Aplica-se a tabela de contingência de concordância e discordância $2 \times 2$:

| Classificação | $M_B$ Correto | $M_B$ Incorreto | Total |
| :--- | :---: | :---: | :---: |
| **$M_A$ Correto** | $a$ | $b$ | $a + b$ |
| **$M_A$ Incorreto** | $c$ | $d$ | $c + d$ |

onde $b$ é a contagem de casos onde $M_A$ acertou e $M_B$ errou, e $c$ é a contagem onde $M_B$ acertou e $M_A$ errou.

### 3.1 Estatística do Teste com Correção de Continuidade de Edwards
Se $b + c \ge 25$:
$$\chi_{\text{McNemar}}^2 = \frac{(|b - c| - 1)^2}{b + c} \sim \chi_1^2$$

Se $b + c < 25$, calcula-se a probabilidade binomial exata com $p = 0.5$. Se $p < 0.05$ (ou $q < 0.05$ pós-FDR), conclui-se que a diferença de desempenho entre os modelos é estatisticamente significante.

---

## 4. Métricas de Validação Robustas em Desbalanceamento Extremo
1. **Macro-F1:** Média não-ponderada do F1-Score entre todas as classes, tratando minoritárias com igual relevância.
2. **Matthews Correlation Coefficient (MCC):**
   $$\text{MCC} = \frac{TP \times TN - FP \times FN}{\sqrt{(TP + FP)(TP + FN)(TN + FP)(TN + FN)}} \in [-1, 1]$$
3. **Kappa ($\kappa$) de Cohen & Alfa ($\alpha$) de Krippendorff:** Medem a concordância inter-anotadores acima do acaso, essenciais para validar amostras de teste humano.
