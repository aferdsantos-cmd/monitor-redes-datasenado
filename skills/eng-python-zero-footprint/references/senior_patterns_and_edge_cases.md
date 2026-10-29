# Padrões Sênior Python 3.12, Big-O, Concorrência e Casos de Borda

Este guia de referência reúne exemplos práticos *Few-Shot* ("Antes vs. Depois"), análise de complexidade algorítmica e a matriz obrigatória de casos de borda para o desenvolvimento de pipelines do monitor-redes-datasenado.

---

## 1. Exemplos Few-Shot: Antipadrões vs. Padrões Sênior

### 1.1. Caso 1: Complexidade Temporal (Comparação Par-a-Par vs. Janela Two-Pointer)

#### ❌ Antes (Antipadrão $O(N^2)$ — Inviável para $N > 10.000$)
```python
# Ineficiente: loop aninhado quadrático sobre todas as combinações de posts
coordinated_pairs = []
for i in range(len(posts)):
    for j in range(i + 1, len(posts)):
        delta_t = abs((posts[i].timestamp - posts[j].timestamp).total_seconds())
        if delta_t <= 60 and posts[i].text == posts[j].text:
            coordinated_pairs.append((posts[i].author_hash, posts[j].author_hash))
```

#### ✅ Depois (Padrão Sênior $O(N \log N + N \cdot k)$ via Ordenação + Janela Deslizante)
```python
# Eficiente: ordena por timestamp e varre com janela deslizante two-pointer
sorted_posts = sorted(posts, key=lambda p: p.timestamp)
coordinated_pairs = []
left = 0
n = len(sorted_posts)

for right in range(n):
    # Avança a borda esquerda para manter a janela temporal
    while (sorted_posts[right].timestamp - sorted_posts[left].timestamp).total_seconds() > 60:
        left += 1
    # Compara apenas com o subconjunto restrito dentro da janela [left, right)
    for k in range(left, right):
        if sorted_posts[right].text_hash == sorted_posts[k].text_hash:
            coordinated_pairs.append((sorted_posts[right].author_hash, sorted_posts[k].author_hash))
```

---

### 1.2. Caso 2: DuckDB Parametrizado e Garantia de Limpeza de Cache

#### ❌ Antes (Interpolação Insegura de Strings e Risco de Vazamento de Disco)
```python
# Inseguro contra injeção e sem garantia de remoção do arquivo temporário
query = f"SELECT * FROM tbl WHERE platform = '{user_platform}'"
temp_file = "/tmp/monitor_datasenado_cache/data.parquet"
con.execute(f"COPY ({query}) TO '{temp_file}' (FORMAT PARQUET)")
upload_to_drive(temp_file)
# Se o upload falhar ou lançar exceção, o arquivo fica ocupando disco!
```

#### ✅ Depois (Query Parametrizada + Proteção por Bloco `try...finally`)
```python
import duckdb
from pathlib import Path

temp_file = Path("/tmp/monitor_datasenado_cache/data.parquet")
try:
    with duckdb.connect() as con:
        # Uso estrito de parâmetros para prevenir injeção
        con.execute(
            "COPY (SELECT * FROM tbl WHERE platform = ?) TO ? (FORMAT PARQUET, CODEC 'ZSTD')",
            [user_platform, str(temp_file)]
        )
    upload_to_drive_with_verification(temp_file)
finally:
    # Garantia inegociável de purga do cache local
    if temp_file.exists():
        temp_file.unlink()
```

---

### 1.3. Caso 3: Coleta Assíncrona com Concorrência Limitada e Jitter Backoff

#### ❌ Antes (Síncrono Bloqueante sem Retentativas nem Timeout)
```python
import requests

def fetch_platform_posts(accounts):
    results = []
    for acc in accounts:
        # Bloqueia a thread; se receber HTTP 429 ou cair a rede, o pipeline congela
        resp = requests.get(f"https://api.plataforma.com/posts?acc={acc}")
        results.extend(resp.json())
    return results
```

#### ✅ Depois (I/O Assíncrono com `asyncio.Semaphore`, Timeout e Exponential Backoff)
```python
import asyncio
import random
import aiohttp

async def fetch_account_posts_resilient(session: aiohttp.ClientSession, account_id: str, semaphore: asyncio.Semaphore) -> list[dict]:
    url = f"https://api.plataforma.com/posts?acc={account_id}"
    base_delay = 1.0
    max_retries = 4

    async with semaphore:  # Limita concorrência para respeitar o rate-limit
        for attempt in range(max_retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10.0)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status in (429, 500, 502, 503):
                        # Retry-After ou backoff exponencial com full jitter
                        retry_after = float(resp.headers.get("Retry-After", base_delay * (2 ** attempt)))
                        jitter = random.uniform(0, retry_after)
                        await asyncio.sleep(jitter)
                    else:
                        resp.raise_for_status()
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.5))
    return []
```

---

## 2. Matriz Obrigatória de Casos de Borda (Edge Cases Checklist)

Todo módulo analítico ou conector deve ser testado contra as seguintes condições extremas:

| Categoria de Borda | Condição Adversária | Comportamento Requerido do Código |
| :--- | :--- | :--- |
| **Volumes Nulos / Unitários** | `posts = []` ou `N_Org = 1` | Retornar métricas nulas (`n=0`, `deff=1.0`) ou levantar `ValueError` informativo antes de operações com divisão por zero. |
| **Monotonia de Stance** | 100% dos posts classificados como `"Favorável"` | Raking e Rogan-Gladen devem operar sem matrizes singulares ou probabilidades negativas. |
| **Unicode Extremo e Emojis** | Textos compostos exclusivamente por emojis (`"👍👍🚨"`) ou caracteres cirílicos/árabes | Decomposição NFKD não deve gerar string vazia que cause erro no Shingling; aplicar fallback gracioso (`"sem_texto"`). |
| **Datas e Fusos Anômalos** | Timestamps ingênuos (*naive*) ou com fusos internacionais (`UTC+9`) | Conversão determinística para `ZoneInfo("America/Sao_Paulo")` ou rejeição explícita. |
| **Payloads de API Quebrados** | JSON truncado, respostas HTML de proxy de erro (`502 Bad Gateway`) | Captura explícita de `json.JSONDecodeError` e retentativa com backoff. |
| **Degeneração de Pesos** | Somatório de pesos nulo ($\sum w_i = 0$) no Raking IPF | Detectar degeneração no simplex e retornar status `NAO_ATINGIDA_LIMITADA_POR_TRIMMING`. |

---

## 3. Tabela de Escolha de Estruturas de Dados e Complexidade Big-O

| Estrutura / Tecnologia | Operação Primária | Complexidade de Tempo | Uso Adequado no Projeto |
| :--- | :--- | :---: | :--- |
| `dict` / `set` (Hash Table) | Lookup de conta / Deduplicação | $O(1)$ médio | Mapeamento de `author_hash`, checagem de allowlist jornalística. |
| `collections.Counter` | Contagem de frequências de tags | $O(N)$ | Determinação de termos frequentes e cálculo de IDF. |
| `numpy.ndarray` | Reamostragem Bootstrap em lotes | Vetorizado C | Multiplicação de matrizes de pesos por réplicas de reamostragem em memória compacta. |
| `DuckDB` | Agregações SQL out-of-core | $O(N)$ em disco | Limpeza e junção de grandes bases Parquet sem estourar a RAM local. |
| `MinHashLSH` | Busca de vizinhos aproximados | $O(N \cdot \bar{b})$ | Deduplicação textual de mensagens semelhantes antes do grafo de Leiden. |
