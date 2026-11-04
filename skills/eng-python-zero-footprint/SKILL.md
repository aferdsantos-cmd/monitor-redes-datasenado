---
name: eng-python-zero-footprint
description: Use this skill whenever writing, refactoring, testing, or syncing Python code, DuckDB/Parquet pipelines, LGPD pseudonymization, or Google Drive/GitHub integrations in the monitor-redes-datasenado project.
---

# Engenharia de Software Sênior, Padrões Python 3.12 e Zero-Footprint

Guia e checklist dos 5 Pilares de Excelência em Engenharia Sênior para desenvolvimento, otimização e integração do monitor-redes-datasenado.

## 1. Contexto Inteligente, Mapeamento AST e Edição Cirúrgica
- **Descoberta AST (Zero Leitura Integral Desnecessária):** Antes de ler arquivos de `src/`, execute o mapa sintático para localizar assinaturas e linhas exatas (`Lxx-Lyy`):
  ```bash
  ./skills/eng-python-zero-footprint/scripts/ast_repo_map.py
  ```
- **Edição Cirúrgica (`edit_file`):** Use blocos pontuais de `Target`/`Replacement`. **PROIBIDO** usar comentários destrutivos como `# ... código existente ...` dentro de ferramentas de edição.
- **Higiene de Saída:** Nunca reimprima blocos de código inteiros no chat; utilize links clicáveis com números de linhas (`[modulo.py](file:///...#L10-L30)`).

## 2. Engenharia Python 3.12 Sênior, Big-O e Concorrência
- **Tipagem Estrita:** `from __future__ import annotations`, `dataclass(slots=True)` e tipos explícitos.
- **Complexidade Sub-Quadrática:** Proibido loops $O(N^2)$ sobre posts/contas. Empregar `set`/`dict` ($O(1)$), janelas *two-pointer* ($O(N \log N)$), LSH ou vetorização NumPy/DuckDB.
- **I/O Assíncrono Resiliente:** Para coleta de APIs, utilizar `asyncio` com `Semaphore` de concorrência, timeouts explícitos e *exponential backoff com full jitter* para `HTTP 429 / 5xx`.

## 3. Abordagem TDD Invertida e Matriz de Casos de Borda (Edge Cases)
- **Test-First Obrigatório:** Escrever ou estender testes unitários (`pytest`) antes ou simultaneamente à implementação de novas rotinas.
- **Blindagem de Casos de Borda:** Validar obrigatoriamente: entrada vazia (`posts = []`), singleton (`N=1`), payloads com emojis/Unicode extremo, timestamps sem fuso horário e rate-limit.

## 4. Security-by-Design, LGPD e Política Zero-Footprint
- **Zero-Footprint:** Cache efêmero em `/tmp/monitor_datasenado_cache` ($\le 250\text{ MB}$), compressão Parquet `ZSTD` via DuckDB, `mutate update` no Drive e purga em `try...finally`.
- **Prevenção de Injeção & SAST:** Queries DuckDB parametrizadas (`con.execute("SELECT ... WHERE id = ?", [val])`), prevenção de Path Traversal (`is_relative_to`), e proibição estrita de `eval()`, `exec()`, `pickle.loads()`, `shell=True` e `yaml.load()` inseguro.
- **Conformidade de Licenças:** Aceitar apenas dependências permissivas (`MIT`, `BSD`, `Apache-2.0`, `PSF`, `MPL-2.0`).

## 5. Portão de Verificação (Quality Gate) e Referências
- Execute a validação compulsória antes de finalizar qualquer entrega:
  ```bash
  ./skills/eng-python-zero-footprint/scripts/verify_gate.sh
  ```
- **Referências Aprofundadas:**
  - [zero_footprint_and_security.md](./references/zero_footprint_and_security.md)
  - [senior_patterns_and_edge_cases.md](./references/senior_patterns_and_edge_cases.md)
