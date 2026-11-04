# Referência Técnica: Zero-Footprint, Sincronização em Nuvem e Segurança LGPD

Este documento formaliza os contratos de implementação para persistência de dados, versionamento sem dependência de ferramentas locais do sistema e proteção de dados pessoais.

---

## 1. Módulo `ZeroFootprintStorage` (`src/storage/zero_footprint_sync.py`)

### 1.1. Contrato Operacional
1. **Diretório Efêmero:** Opera exclusivamente em `/tmp/monitor_datasenado_cache/`. É estritamente vedada a criação de diretórios de dados permanentes dentro de `data/` ou na raiz do projeto.
2. **Compressão Parquet:** Utiliza DuckDB para leitura e exportação com codec `ZSTD`:
   ```python
   con.execute(f"COPY (SELECT * FROM df) TO '{temp_path}' (FORMAT PARQUET, CODEC 'ZSTD')")
   ```
3. **Sincronização com Google Drive (`gdrive` CLI):**
   - Executa via binário standalone `/Users/anderson/.gemini/antigravity/bin/gdrive`.
   - Lê os IDs de pastas exclusivamente do `.env` (`DRIVE_PARQUET_FOLDER_ID`, `DRIVE_REPORT_FOLDER_ID`).
   - Sincronização in-place (`mutate update`): se o arquivo remoto já existir com o mesmo nome na pasta de destino, atualiza o conteúdo do arquivo existente sem criar arquivos duplicados.
4. **Verificação de Integridade Pós-Upload:**
   - Compara o tamanho em bytes do arquivo remoto retornado pelo `gdrive files list/info` com o arquivo local.
   - Em caso de divergência, levanta `IOError` e retém o arquivo para diagnóstico.
5. **Garantia de Purga:**
   - O arquivo temporário local é removido via `Path.unlink()` no bloco `finally`.
   - Limite rígido de cache: se o espaço total em `/tmp/monitor_datasenado_cache/` ultrapassar 250 MB, o sistema executa varredura de arquivos antigos (`mtime`) ou aborta a execução.

---

## 2. Módulo `GitHubZeroFootprintSync` (`src/storage/github_zero_footprint_sync.py`)

### 2.1. Arquitetura Git Data API (Sem Xcode CLT)
Devido à ausência e proibição do pacote Apple Xcode CLT no ambiente macOS, todas as operações com o repositório GitHub remoto operam através da GitHub REST API (Git Data API v3):

1. **Leitura e Filtragem via `pathspec`:**
   - Compila as regras do `.gitignore` usando a especificação Git WildMatch (`pathspec.PathSpec.from_lines("gitignore", ...)`).
   - Injeta regras compulsórias de segurança:
     - `.env`, `*.env` (exceto `.env.example`);
     - `Auditorias/` (mantida apenas localmente na máquina do desenvolvedor);
     - `.DS_Store`, `*.parquet`, `*.duckdb`, `*.csv`, `config/secrets.yaml`.
2. **Construção do Commit Atômico:**
   - Para cada arquivo rastreado, cria um `Blob` remoto via `POST /repos/{owner}/{repo}/git/blobs` com codificação base64.
   - Constrói uma nova `Tree` remota com a lista total de blobs rastreados (`POST /repos/{owner}/{repo}/git/trees`). A ausência de `base_tree` garante que arquivos excluídos localmente sejam excluídos da nova árvore.
   - Cria o objeto `Commit` (`POST /repos/{owner}/{repo}/git/commits`).
   - Atualiza a referência de branch (`PATCH /repos/{owner}/{repo}/git/refs/heads/main`).
   - Cria ou atualiza a tag correspondente (`POST/PATCH /repos/{owner}/{repo}/git/refs/tags/{tag_name}`).

---

## 3. Segurança e Higienização LGPD (`src/cleaning/lgpd_and_bot_filter.py`)

### 3.1. Pseudonimização por `HMAC-SHA256`
- **Fundamento Legal:** LGPD art. 13, §4º (dados pessoais pseudonimizados mantidos em regime controlado).
- **Modo Fail-Closed:** A chave secreta é lida de `os.environ["LGPD_HMAC_SECRET_KEY"]`. Se a variável não estiver definida, tiver comprimento inferior a 32 caracteres ou for um placeholder (`"defina-"`), o sistema lança `RuntimeError` imediato e aborta o processamento.
- **Esvaziamento de Memória:** Logo após o cálculo do hash hexadecimal (64 caracteres), o campo `raw_author_id` do objeto em memória é imediatamente redefinido para `""` (string vazia).
- **Identificador de Chave:** Registra `hmac_key_id = hashlib.sha256(key.encode()).hexdigest()[:8]` para permitir auditoria de rotação criptográfica sem expor o segredo.

### 3.2. Sanitização de PII e Filtros Geográficos
- **Truncamento Temporal:** Timestamps em artefatos derivados devem ser truncados no nível da hora (`timestamp_hour_trunc = ts.replace(minute=0, second=0, microsecond=0)`).
- **Remoção de PII:** Expressões regulares sanitizam menções a números de CPF (`\d{3}\.\d{3}\.\d{3}-\d{2}`), endereços de e-mail e números de telefone celular.
- **Extração Segura de DDD:** Números internacionais iniciados com `+1` (EUA), `+44` (Reino Unido), etc., são explicitamente rejeitados pelo extrator e classificados como `('NI', 'Nao Identificado')`. Apenas códigos com formato `+55 (DD)` mapeados para a tabela DDD da Anatel são aceitos como proxy geográfico aproximado.

### 3.3. Normalização Unicode e Proteção de Contexto Legislativo
- **Decomposição NFKD:** O texto de posts é normalizado via `unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()`. Garante que expressões valorativas cívicas como `"Vote SIM"` e `"Vote NÃO"` recebam tratamento simétrico independentemente de acentuação gráfica.
- **Proteção de Vocábulos Parlamentares:** A quarentena de spam comercial possui lista de exceções que protege termos legislativos essenciais contra falso positivo, tais como:
  - `"sorteio do relator"`;
  - `"CPI das apostas esportivas"`;
  - `"legalização do cassino"`;
  - `"votação em plenário"`.

---

## 4. Security-by-Design, Prevenção de Vulnerabilidades e Licenciamento

### 4.1. Prevenção de SQL Injection em DuckDB
- É terminantemente vedada a interpolação direta de variáveis de usuário em queries SQL (`f"SELECT * FROM tbl WHERE platform = '{user_input}'"`).
- Todas as consultas dinâmicas devem utilizar passagem segura de parâmetros posicionais:
  ```python
  con.execute("SELECT * FROM tbl WHERE platform = ? AND created_at >= ?", [platform, min_date])
  ```
- Operações de exportação `COPY ... TO` devem validar o caminho de destino assegurando que pertença ao diretório efêmero permitido.

### 4.2. Prevenção de Path Traversal
- Qualquer caminho de arquivo gerado a partir de identificadores externos (como nomes de arquivos derivados de IDs de temas legislativos) deve ser sanitizado e validado:
  ```python
  target_path = (base_dir / filename).resolve()
  if not target_path.is_relative_to(base_dir.resolve()):
      raise SecurityError(f"Tentativa de Path Traversal detectada: {filename}")
  ```

### 4.3. Proibição de Primitivas Inseguras (SAST)
O código do projeto é auditado automaticamente pelo Quality Gate contra primitivas de execução arbitrária:
- ❌ **`eval()` e `exec()`:** Proibidos. Toda lógica dinâmica deve ser mapeada via dicionários ou despacho determinístico.
- ❌ **`pickle.loads()` e `pickle.load()`:** Proibidos para serialização de dados externos (vulnerabilidade de execução remota de código). Utilizar Apache Parquet ou JSON.
- ❌ **`subprocess.run(..., shell=True)`:** Proibido. Toda execução externa deve receber a lista de argumentos explícita (`shell=False`).
- ❌ **`yaml.load()` sem Loader Seguro:** Proibido. Sempre utilizar `yaml.safe_load()`.

### 4.4. Compliance de Licenciamento Open-Source
Para garantir a viabilidade jurídica de transferência do código para o **Instituto de Pesquisa DataSenado** e uso pelo Senado Federal:
- Todas as dependências externas em `pyproject.toml` devem possuir licenças estritamente permissivas:
  - `MIT`;
  - `BSD-2-Clause` / `BSD-3-Clause`;
  - `Apache-2.0`;
  - `PSF-2.0` (Python Software Foundation);
  - `MPL-2.0` ou `LGPL-3.0` (como dependência dinâmica).
- Dependências sob licenças copyleft recíprocas fortes (`GPLv3`, `AGPLv3`) ou proprietárias restritivas são vedadas no núcleo analítico da aplicação.

