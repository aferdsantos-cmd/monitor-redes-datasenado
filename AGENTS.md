# Diretrizes Operacionais — Monitor de Redes DataSenado (TCC)

## 1. Arquitetura Dual-Agent & Economia de Tokens
- **Chat Cérebro (Planejador/Auditor):** Emite Ordens de Serviço (`Auditorias/Fase_XX/00_Ordens_de_Servico/`) e audita entregas. Não edita `src/` diretamente.
- **Chat Operador (Executor):** Implementa código conforme a OS, valida testes (`100% green, 0 warnings`) e gera relatórios em `Auditorias/Fase_XX/03_Entregas_Implementacao/`.
- **Higiene de Contexto:** Use leitura cirúrgica (`StartLine`/`EndLine`). Carregue a skill específica da tarefa em `skills/<nome>/SKILL.md` antes de agir. Só leia `references/` quando estritamente necessário.

## 2. Binários e Ambiente (Sem Xcode CLT)
- Python/Testes: `/Users/anderson/.local/bin/uv run --extra dev pytest -v`
- Execução de Módulos: `/Users/anderson/.local/bin/uv run python -m <modulo>`
- Google Drive CLI: `/Users/anderson/.gemini/antigravity/bin/gdrive`
- GitHub CLI: `/Users/anderson/.local/bin/gh` (Sincronizar via `src.storage.github_zero_footprint_sync`)

## 3. Invariantes Inegociáveis (v1.2-fase01)
- **Zero-Footprint:** Proibido salvar datasets na árvore do projeto. Usar `/tmp/monitor_datasenado_cache` (teto 250 MB), comprimir em Parquet `ZSTD` via `DuckDB`, atualizar in-place no Drive (`mutate update`) e purgar `/tmp`.
- **Segurança & LGPD:** `.env` jamais versionado. `HMAC-SHA256` em modo *fail-closed* ($\ge 32$ chars, 64 hex, `raw_author_id=None`).
- **Escopo Inferencial:** Universo Alvo = Discurso Público Digital Observado ($\mathcal{U}_{\text{Org}, T}$), unidade = `1 Conta Orgânica por Plataforma`. Manter as 6 plataformas (YouTube, Telegram, X, Instagram/Facebook, TikTok, WhatsApp) conforme `ADR-006`.
