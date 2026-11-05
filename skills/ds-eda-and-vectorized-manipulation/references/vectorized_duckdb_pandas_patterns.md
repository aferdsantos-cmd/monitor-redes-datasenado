# Padrões de Manipulação Vetorizada com DuckDB SQL e Pandas 2.x PyArrow

Este documento detalha os padrões arquiteturais de alta eficiência para processamento tabular analítico no projeto Monitor de Redes DataSenado, garantindo execução vetorizada em memória restrita e conformidade estrita com a política Zero-Footprint.

---

## 1. Princípios de Execução Colunar e Vetorização

O ecossistema do Monitor de Redes opera com volumes expressivos de dados provenientes de múltiplas redes sociais (YouTube, Telegram, X/Twitter, Meta, TikTok e WhatsApp). O processamento linha a linha em Python nativo gera degradações severas de latência e consumo desnecessário de CPU por overhead de despacho dinâmico.

A vetorização transfere a execução analítica para bibliotecas compiladas C/C++ e Rust (DuckDB, Apache Arrow, NumPy), operando diretamente sobre blocos contíguos de memória com instruções SIMD (Single Instruction, Multiple Data).

### 1.1 Hierarquia de Decisão Analítica
1. **Filtros e Agregações Pesadas:** Execute diretamente no DuckDB SQL sobre tabelas Parquet comprimidas em ZSTD.
2. **Transformações Condicionais Complexas:** Utilize `np.select()` ou `pd.Series.mask()` em vez de funções aplicadas com `.apply(axis=1)`.
3. **Mapeamentos Categóricos:** Empregue tipos `pd.Categorical` ou Arrow `dictionary` para reduzir drasticamente a pegada de memória de colunas de texto repetitivo (plataformas, macrorregiões, espectros).

---

## 2. DuckDB como Mecanismo Analítico Central

DuckDB fornece um motor OLAP relacional embarcado que executa consultas SQL analíticas sem necessidade de servidor externo, operando de forma perfeita dentro de contextos de memória delimitados ($\le 250\text{ MB}$).

### 2.1 Padrão de Conexão com Limite de Memória e Zero-Footprint
```python
import duckdb
from pathlib import Path

def query_parquet_dataset(parquet_path: Path, query: str) -> list[dict]:
    """Executa query SQL sobre Parquet com teto de memória estrito."""
    with duckdb.connect(database=":memory:") as con:
        con.execute("SET max_memory = '200MB'")
        con.execute("SET threads = 4")
        con.execute("SET preserve_insertion_order = false")
        result = con.execute(query).df()
    return result.to_dict(orient="records")
```

### 2.2 Agregações Multi-Nível com CUBE e ROLLUP
Para gerar resumos executivos prontos para relatórios legislativos sem efetuar múltiplos passos lentos de agregação:
```sql
SELECT 
    coalesce(platform, 'TODAS') AS platform,
    coalesce(macroregion, 'BRASIL') AS macroregion,
    count(*) AS total_posts,
    round(avg(length(text_clean)), 2) AS avg_chars,
    sum(coalesce(weight_rake, 1.0)) AS sum_weights
FROM read_parquet('/tmp/monitor_datasenado_cache/silver_organic.parquet')
GROUP BY ROLLUP (platform, macroregion)
ORDER BY platform, macroregion;
```

---

## 3. Padrões Vetorizados em Pandas 2.x e NumPy

Quando os dados são carregados em memória para inspeção ou transformação fina, as operações devem obedecer aos padrões descritos abaixo.

### 3.1 Substituição de `.apply()` por `np.select()`
Anti-padrão reprovado em auditoria:
```python
# PROIBIDO: loop disfarçado linha a linha
df['volume_class'] = df.apply(lambda row: 'High' if row['eng_score'] > 100 else 'Low', axis=1)
```

Padrão vetorizado obrigatório:
```python
# RECOMENDADO: execução vetorizada em C
import numpy as np

conditions = [
    df['eng_score'] > 500,
    df['eng_score'] > 100,
    df['eng_score'] >= 0,
]
choices = ['Viral', 'Alto', 'Normal']
df['volume_class'] = np.select(conditions, choices, default='Indefinido')
```

### 3.2 Prevenção de Chained Indexing
Nunca utilize a sintaxe de indexação encadeada `df[a][b] = v`, pois ela causa o alerta `SettingWithCopyWarning` e gera ambiguidades sobre se a atribuição ocorreu em uma cópia ou na visão original. Em vez disso, utilize `.loc`:
```python
df.loc[df['platform'] == 'youtube', 'platform_normalized'] = 'YouTube'
```

---

## 4. Orçamento de Memória e Padrões de Exportação

1. **Efemeridade do Cache:** Arquivos intermediários são lidos de `/tmp/monitor_datasenado_cache` e limpos no bloco `finally`.
2. **Formato Parquet ZSTD:** Nunca exporte CSVs volumosos na árvore do repositório. O formato Parquet comprimido com ZSTD garante integridade de tipos e redução de até 85% no espaço em disco.
3. **Ponte de Relatórios:** Tabelas sumarizadas destinadas a relatórios executivos (`.docx` ou `.xlsx`) devem ser geradas em objetos `io.BytesIO` em memória ou manipuladas como estruturas leves de dicionários antes da serialização.
