# Diagnóstico de Dados Faltantes e Integridade Amostral em Joins

Este manual técnico estabelece as diretrizes para auditoria de completude de dados, taxonomia de dados faltantes segundo Rubin (1976) e salvaguardas de conservação de cardinalidade e pesos amostrais em junções tabulares no âmbito do Monitor de Redes DataSenado.

---

## 1. Taxonomia de Dados Faltantes (Rubin, 1976)

Em pesquisas de opinião pública digital, os dados faltantes nunca devem ser tratados de forma uniforme. A causa subjacente da ausência dita o procedimento metodológico correto.

### 1.1 MCAR (Missing Completely at Random)
- **Definição:** A probabilidade de um dado estar ausente independe tanto das variáveis observadas quanto dos valores não observados.
  $$\mathbb{P}(M | Y_{\text{obs}}, Y_{\text{mis}}) = \mathbb{P}(M)$$
- **Exemplo Prático:** Falha aleatória transitória de conectividade com a API do YouTube em uma requisição específica de metadados.
- **Tratamento:** A exclusão dos casos faltantes (*complete-case analysis*) não introduz viés na estimativa pontual, embora reduza a eficiência estatística ($n_{\text{efetivo}} < n$).

### 1.2 MAR (Missing at Random)
- **Definição:** A probabilidade de ausência depende das variáveis observadas no conjunto de dados, mas é condicionalmente independente dos valores não observados da própria variável em questão.
  $$\mathbb{P}(M | Y_{\text{obs}}, Y_{\text{mis}}) = \mathbb{P}(M | Y_{\text{obs}})$$
- **Exemplo Prático:** A ausência de DDD ou indicação geográfica é substancialmente mais alta no canal Telegram ou YouTube do que no WhatsApp (onde o DDD é inerente ao número telefônico).
- **Tratamento:** A análise por casos completos é viciada. É obrigatório estratificar o diagnóstico por plataforma e utilizar métodos de pós-estratificação (como Raking IPF) para reponderar as categorias sub-representadas.

### 1.3 MNAR (Missing Not at Random)
- **Definição:** A probabilidade de ausência depende do próprio valor não observado.
  $$\mathbb{P}(M | Y_{\text{obs}}, Y_{\text{mis}}) \neq \mathbb{P}(M | Y_{\text{obs}})$$
- **Exemplo Prático:** No Cenário 2 (Discurso Público Espontâneo), usuários com opiniões impopulares ou temerosos de repercussão legal podem optar pela autocensura (*espiral do silêncio* de Noelle-Neumann), não emitindo opinião.
- **Tratamento:** Modelos de correção de seleção amostral (Heckman selection model) ou declaração explícita de limite epistêmico no relatório de auditoria e TCC.

---

## 2. Teste Heurístico de Padrões de Ausência

Para diferenciar analiticamente entre MCAR e MAR sem dependências pesadas de bibliotecas externas, aplica-se a heurística de teste bivariado entre o indicador binário de ausência $R_i \in \{0, 1\}$ e as variáveis auxiliares observadas (plataforma, turno de coleta):
```python
import numpy as np

def test_missing_at_random_heuristic(is_missing: np.ndarray, strata: np.ndarray) -> dict[str, float]:
    """Testa se a ausência varia significativamente entre estratos observados (MAR)."""
    unique_strata = np.unique(strata)
    rates = {}
    for s in unique_strata:
        mask = (strata == s)
        rates[str(s)] = float(np.mean(is_missing[mask]))
    
    max_rate = max(rates.values())
    min_rate = min(rates.values())
    disparity = max_rate - min_rate
    
    return {
        "strata_missing_rates": rates,
        "max_disparity": round(disparity, 4),
        "pattern": "MAR" if disparity > 0.05 else "MCAR_candidate",
    }
```

---

## 3. Integridade e Conservação de Cardinalidade em Joins

Em bases de dados analíticas com pesos amostrais (Raking IPF ou Alocação de Hamilton), junções impróprias podem duplicar registros silenciosamente (produto cartesiano involuntário), corrompendo a representatividade demográfica.

### 3.1 Padrão de Asserção de Integridade (`assert_join_integrity`)
Toda junção relacional deve verificar preventivamente a cardinalidade da chave primária/estrangeira e comprovar a conservação dos pesos antes e após a operação:

```python
import pandas as pd

def assert_join_integrity(
    df_left: pd.DataFrame,
    df_right: pd.DataFrame,
    on: str,
    how: str = "left",
    weight_col: str | None = "weight_rake"
) -> pd.DataFrame:
    """Executa merge com verificação rigorosa de integridade relacional e conservação de pesos."""
    # 1. Verifica duplicidade na tabela de busca (right table)
    if df_right[on].duplicated().any():
        raise ValueError(f"Chave '{on}' não é única na tabela de busca: risco de produto cartesiano!")
    
    pre_len = len(df_left)
    pre_weight = df_left[weight_col].sum() if weight_col and weight_col in df_left else None
    
    # 2. Executa junção validada
    merged = pd.merge(df_left, df_right, on=on, how=how, validate="many_to_one")
    
    # 3. Asserção de conservação de linhas
    if how == "left" and len(merged) != pre_len:
        raise AssertionError(f"Inflação de linhas detectada: {pre_len} -> {len(merged)}")
        
    # 4. Asserção de conservação de pesos
    if pre_weight is not None:
        post_weight = merged[weight_col].sum()
        if abs(pre_weight - post_weight) > 1e-9:
            raise AssertionError(f"Divergência na soma de pesos: {pre_weight} vs {post_weight}")
            
    return merged
```

---

## 4. Checklist de Validação em Auditorias Tabulares
1. Todas as colunas possuem tipos de dados fixos e coerentes (evitar tipo `object` genérico quando for `category` ou `string`).
2. Nenhum `.fillna(0)` foi aplicado a variáveis sensíveis sem justificativa prévia.
3. As taxas de dados faltantes estão categorizadas explicitamente em MCAR, MAR ou MNAR.
4. Nenhuma operação de merge gerou inflação não controlada de linhas ou alteração de pesos amostrais.
