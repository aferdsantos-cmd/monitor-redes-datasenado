# Pipelines Livres de Vazamento e Codificação de Alvo Out-of-Fold

Este documento detalha os princípios formais para prevenção de contaminação estatística (*data leakage*) na engenharia de variáveis preditivas para modelagem supervisionada no Monitor de Redes DataSenado.

---

## 1. Tipologia de Vazamento de Dados em Redes Sociais

O vazamento de dados ocorre quando informações que não estariam disponíveis no momento da predição em produção são incorporadas ao modelo durante a etapa de treinamento ou validação. Em dados de mídias sociais digitais, esse problema se manifesta principalmente em quatro modalidades:

1. **Vazamento Pré-Split (Pre-Split Leakage):** Ajuste de transformações em todo o conjunto de dados antes da separação entre treino e teste. Exemplos clássicos incluem normalização com z-score global, imputação pela média global ou extração de componentes principais (PCA) sobre o corpus total.
2. **Vazamento de Nível de Conta (Account-Level Leakage):** Amostragem aleatória simples de comentários onde publicações do mesmo autor (`author_id_hash`) estão presentes simultaneamente nas partições de treino e teste. O modelo aprende idiossincrasias lexicais de autores prolíficos em vez de padrões generalizáveis.
3. **Vazamento Temporal (Look-Ahead Bias):** Utilização de estatísticas agregadas de janelas móveis calculadas de forma centralizada ou incluindo instantes futuros $[t, t + k]$, distorcendo a causalidade.
4. **Vazamento por Target Encoding Direto:** Substituição de categorias pela média do alvo calculada sobre a amostra inteira, criando uma correlação artificial quase perfeita que colapsa quando o modelo é aplicado a dados novos.

---

## 2. Invariante Fit-on-Train-Only

Para qualquer transformador com estado dependente dos dados, o método `.fit()` deve ser invocado exclusivamente no subconjunto de treinamento. O pipeline de inferência em produção deve receber os estimadores congelados.

```python
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class RobustStrataScaler(BaseEstimator, TransformerMixin):
    """Escalonador robusto baseado em mediana e IQR ajustado estritamente no treino."""
    def __init__(self) -> None:
        self.medians_: dict[str, float] = {}
        self.iqrs_: dict[str, float] = {}

    def fit(self, X: np.ndarray, y: np.ndarray | None = None) -> "RobustStrataScaler":
        # Ajuste exclusivamente no conjunto de treino
        self.medians_ = float(np.median(X, axis=0))
        q75, q25 = np.percentile(X, 75, axis=0), np.percentile(X, 25, axis=0)
        self.iqrs_ = float(np.maximum(q75 - q25, 1e-6))
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        # Aplicação cega na validação ou produção
        return (X - self.medians_) / self.iqrs_
```

---

## 3. Out-of-Fold (OOF) Target Encoding com Suavização de Bayes Empírico

Ao lidar com variáveis categóricas de alta cardinalidade (como hashtags, comunidades de rede ou canais), a substituição de rótulos por médias do alvo exige proteção matemática contra sobreajuste (*overfitting*).

Adota-se a formulação de Micci-Barreca (2001) com suavização de Bayes empírico (*Empirical Bayes Shrinkage*):

$$\hat{x}_c = \lambda_c \bar{y}_c + (1 - \lambda_c) \bar{y}_{\text{prior}}, \quad \lambda_c = \frac{n_c}{n_c + m}$$

onde:
- $\bar{y}_c$ é a média observada da classe alvo para a categoria $c$;
- $n_c$ é a contagem de observações da categoria $c$;
- $\bar{y}_{\text{prior}}$ é a média global do alvo no treino;
- $m$ é o parâmetro de suavização (típico $m \in [10, 50]$), que puxa categorias raras em direção à média global.

### 3.1 Algoritmo Out-of-Fold com Agrupamento por Autor
Para impedir que posts do mesmo autor influenciem a sua própria codificação:
1. Divide-se o conjunto de treino em $K$ folds usando agrupamento estrito por `author_id_hash`.
2. Para cada fold $k \in \{1, \dots, K\}$:
   - Calcula-se $\bar{y}_c$ e $\bar{y}_{\text{prior}}$ utilizando exclusivamente os outros $K-1$ folds.
   - Aplica-se a fórmula de Micci-Barreca para preencher os valores das observações do fold $k$.
3. Para os dados de validação externa e teste final, utilizam-se as estatísticas computadas sobre a totalidade da partição de treino.

---

## 4. Diagnóstico de Multicolinearidade via Fator de Inflação da Variância (VIF)

Antes de submeter vetores de atributos a modelos lineares ou aditivos, deve-se auditar o Fator de Inflação da Variância:

$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$

onde $R_j^2$ é o coeficiente de determinação da regressão da feature $j$ sobre todas as demais features.
- $\text{VIF}_j < 5.0$: Aceitável (baixa colinearidade);
- $5.0 \le \text{VIF}_j < 10.0$: Moderada (requer monitoramento);
- $\text{VIF}_j \ge 10.0$: Crítica (eliminação mandatória da feature colinear ou aplicação de regularização Ridge).
