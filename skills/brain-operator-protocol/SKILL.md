---
name: brain-operator-protocol
description: Use this skill when planning Service Orders (Brain role), executing Service Orders and generating Delivery Reports (Operator role), or optimizing context window and token usage across turns.
---

# Protocolo Cérebro-Operador e Eficiência Cognitiva

Diretrizes para o fluxo de trabalho dual-agent (*Planner-Executor-Verifier*) com controle rígido de consumo de tokens e preservação de contexto.

## 1. Princípio da Revelação Progressiva (Progressive Disclosure)
- **Nível 0 (`AGENTS.md`):** Carregado por padrão; restrito a $< 45$ linhas com invariantes absolutas.
- **Nível 1 (Frontmatter de Skills):** O agente consulta apenas `name` e `description` ao planejar.
- **Nível 2 (`SKILL.md`):** Carregado sob demanda na tarefa específica; restrito a $< 100$ linhas.
- **Nível 3 (`references/` e `scripts/`):** Lido cirurgicamente apenas quando a sub-rotina exata for necessária.

## 2. Diretrizes para o Chat Cérebro (Planejador / Auditor)
- **Emissão de OS:** Redigir Ordens de Serviço objetivas, modulares e autocontidas em `Auditorias/Fase_XX/00_Ordens_de_Servico/OS_FaseXX.md`.
- **Delimitação Explícita de Escopo:** Indicar expressamente quais arquivos podem e quais NÃO podem ser alterados.
- **Auditoria Econômica:** Auditar as entregas inspecionando primeiramente o relatório em `Auditorias/Fase_XX/03_Entregas_Implementacao/Entrega_FaseXX.md` e os testes antes de abrir arquivos volumosos.

## 3. Diretrizes para o Chat Operador (Executor Técnico)
- **Leitura Cirúrgica:** Usar `read_file` com parâmetros de linha (`StartLine`/`EndLine`) e ler apenas o que for estritamente necessário.
- **Edição Pontual:** Preferir `edit_file` para blocos específicos em vez de sobrescrever arquivos extensos com `write_file`.
- **Higiene de Logs:** Proibido colar saídas volumosas de terminal ou dumps no chat. Resumir o status dos testes e gravar logs extensos em `/tmp/` quando necessário.
- **Verificação Contínua:** Executar `./skills/eng-python-zero-footprint/scripts/verify_gate.sh` antes de gerar a entrega.
- **Relatório Estruturado:** Preencher o relatório de entrega com evidências objetivas e a saída sintetizada do pytest.

## 4. Templates Padronizados
Para os modelos de Ordem de Serviço e Relatório de Entrega:
- [os_and_delivery_templates.md](./references/os_and_delivery_templates.md)
