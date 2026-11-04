# Templates Padronizados: Ordem de Serviço (OS) e Relatório de Entrega

Modelos estruturados para a comunicação inter-agentes no protocolo dual-agent (*Planner-Executor-Verifier*).

---

## 1. Template: Ordem de Serviço (`Auditorias/Fase_XX/00_Ordens_de_Servico/OS_FaseXX.md`)

```markdown
# Ordem de Serviço: OS_FaseXX_{NOME_CURTO}

- **Código da OS:** `OS_FaseXX`
- **Emitente:** Chat Cérebro (Planejador e Auditor Metodológico)
- **Destinatário:** Chat Operador (IA Executora Técnica)
- **Escopo:** {DESCRICAO_OBJETIVA_DO_ESCOPO}
- **Restrição de Escopo:** NÃO modifique {ARQUIVOS_PROTEGIDOS} sem instrução explícita.

---

## 1. Contexto e Motivação
{SUMARIO_BREVE_DO_PORQUE_DA_TAREFA}

---

## 2. Requisitos Técnicos e Arquiteturais
1. **Requisito 1:** {DESCRICAO_TECNICA_E_CONTRATO}
2. **Requisito 2:** {DESCRICAO_TECNICA_E_CONTRATO}

---

## 3. Arquivos Envolvidos
- **Criar/Modificar:**
  - `caminho/para/arquivo.py`: {OBJETIVO_DA_ALTERACAO}
- **Testes:**
  - `tests/test_faseXX_....py`: {CASOS_DE_TESTE_OBRIGATORIOS}

---

## 4. Critérios de Aceite e Homologação
1. Todos os novos testes e suíte regressiva aprovados (`100% green, 0 warnings`).
2. Script `./skills/eng-python-zero-footprint/scripts/verify_gate.sh` aprovado.
3. Sincronização atômica GitHub via `src.storage.github_zero_footprint_sync` realizada.
4. Relatório em `Auditorias/Fase_XX/03_Entregas_Implementacao/Entrega_FaseXX.md` gerado.
```

---

## 2. Template: Relatório de Entrega (`Auditorias/Fase_XX/03_Entregas_Implementacao/Entrega_FaseXX.md`)

```markdown
# Relatório de Entrega de Implementação — Fase XX

- **Ordem de Serviço Referenciada:** `OS_FaseXX_{NOME_CURTO}`
- **Executor:** Chat Operador (IA Executora Técnica)
- **Data da Entrega:** {DATA_HORA}
- **Status Geral:** Concluído com Sucesso (100% de Conformidade)

---

## 1. Resumo das Alterações Realizadas
- **Arquivos Criados:**
  - [`caminho/arquivo`](file:///Users/...): {DESCRICAO_SINTETICA}
- **Arquivos Modificados:**
  - [`caminho/arquivo`](file:///Users/...): {DESCRICAO_SINTETICA}

---

## 2. Evidência dos Testes Automatizados (`pytest`)
Saída literal da execução do `pytest -v`:
```text
{COLAR_SAIDA_CONCISA_DO_PYTEST}
```

---

## 3. Matriz de Rastreabilidade e Conformidade com a OS
| Requisito da OS | Arquivo / Módulo Implementado | Status de Conformidade |
| :--- | :--- | :---: |
| Requisito 1 | `caminho/arquivo.py` | ✅ Conforme |
| Requisito 2 | `caminho/outro.py` | ✅ Conforme |

---

## 4. Status de Verificação e Sincronização
- **Portão de Verificação (`verify_gate.sh`):** Aprovado (sem vazamento de `/tmp`, sem arquivos proibidos).
- **Sincronização GitHub:** Realizada via Git Data API (Commit `{COMMIT_SHA[:8]}`, Tag `{TAG_NAME}`).
```
