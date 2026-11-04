# Protocolo de Diálogo Sequencial entre Auditoras e Templates Oficiais

Este documento estabelece o protocolo formal de interação cronológica entre a **IA Auditora Sênior** (`skills/audit-iia-iso31000-datasenado`) e a **IA Auditora Operacional** (`skills/audit-operational-fieldwork-datasenado`) no âmbito das normas internacionais **IIA GIAS / IPPF (Standards 1130, 2310, 2320, 2330 e 2340)** e das **Normas de Auditoria do TCU (NAT)**.

---

## 1. Topologia de Diretório e Regras de Nomenclatura

Toda a comunicação bilateral pericial entre as auditoras ocorre na pasta de diálogo específica da fase auditada:
`Auditorias/Fase_XX/05_Dialogo_Auditoras/`

### 1.1. Fluxograma Sequencial de 5 Etapas

```text
Auditorias/Fase_XX/05_Dialogo_Auditoras/
├── 01_SENIOR_para_OPERACIONAL_Plano_de_Testes_Auditoria.md       # Passo 1: Sênior define testes de campo (PTA)
├── 02_OPERACIONAL_para_SENIOR_Execucao_e_Evidencias_Brutas.md    # Passo 2: Operacional reporta outputs da sonda (EET)
├── 03_SENIOR_para_OPERACIONAL_Validacao_dos_Testes_Executados.md # Passo 3: Sênior emite atestado de supervisão IIA 2340 (VTE)
├── 04_OPERACIONAL_para_SENIOR_Nota_de_Auditoria_Achados.md       # Passo 4: Operacional emite Nota com 7 elementos por achado (NA)
└── 05_SENIOR_Parecer_Final_Homologacao.md                        # Passo 5: Sênior homologa e consolida relatório final
```

### 1.2. Regras de Nomenclatura Estrita
- **Prefixo Numérico:** Sempre dois dígitos (`01_` a `05_`), garantindo ordenação cronológica e alfabética natural no Finder/VS Code/Terminal.
- **Sentido do Fluxo:** `SENIOR_para_OPERACIONAL` ou `OPERACIONAL_para_SENIOR`.
- **Tipo de Documento:** `Plano_de_Testes_Auditoria`, `Execucao_e_Evidencias_Brutas`, `Validacao_dos_Testes_Executados`, `Nota_de_Auditoria_Achados`, `Parecer_Final_Homologacao`.
- **Ciclos de Reteste (Iteração Complementar):** Se no Passo 3 a Auditora Sênior identificar que um teste precisa de complemento ou reteste focal, utilizam-se os sufixos alfanuméricos:
  - `02b_OPERACIONAL_para_SENIOR_Execucao_Reteste.md`
  - `03b_SENIOR_para_OPERACIONAL_Validacao_Reteste.md`
  Preservando o histórico sem sobrescrever evidências prévias.

---

## 2. Template 01: Plano de Testes de Auditoria (PTA)
`01_SENIOR_para_OPERACIONAL_Plano_de_Testes_Auditoria.md`

```markdown
# 01. Plano de Testes de Auditoria (PTA) — IA Auditora Sênior para IA Auditora Operacional

- **Fase Auditada:** [Ex: Fase_01_Pre_Processamento]
- **Data de Emissão:** [AAAA-MM-DD HH:MM]
- **Líder de Auditoria (Supervisora):** IA Auditora Sênior (IIA Standard 2340)
- **Destinatária:** IA Auditora Operacional de Campo
- **Âncora de Negócio:** [H1 TCC Zero-Footprint / H2 Transição DataSenado]

## 1. Diretrizes Estratégicas de Campo
- Não modifique arquivos em `src/`, `config/` ou `docs/` (Modo Somente-Leitura).
- Execute a sonda compactada `./skills/audit-operational-fieldwork-datasenado/scripts/run_audit_fieldwork_probe.py --phase Fase_XX`.
- Utilize leituras cirúrgicas (`StartLine`/`EndLine`) guiadas pelo mapa AST (`ast_repo_map.py`) respeitando o orçamento de tokens.

## 2. Matriz de Procedimentos Periciais de Auditoria

| Teste ID | Alvo (`WP-ID` + Arquivo + Linhas) | Procedimento Exato a Executar | Critério de Referência | Orçamento Máximo de Leitura |
| :---: | :--- | :--- | :--- | :---: |
| `TEST-01` | `WP-04` (`src/sampling/...`) L45-L98 | Inspecionar se o algoritmo de alocação de Hamilton preserva soma exata | ADR-003 / Fórmula Hamilton | 60 linhas |
| `TEST-02` | `WP-05` (`src/text_processing/...`) L110-L150 | Verificar se HMAC-SHA256 é fail-closed quando salt é ausente/curto | LGPD Art. 13 / Requisito OS | 50 linhas |
| `TEST-03` | `WP-06` (`config/settings.yaml`) L1-L80 | Verificar se bounds de raking [0.25, 4.0] vêm do YAML sem hardcode | ADR-004 | 40 linhas |
```

---

## 3. Template 02: Execução de Testes e Evidências Brutas (EET)
`02_OPERACIONAL_para_SENIOR_Execucao_e_Evidencias_Brutas.md`

```markdown
# 02. Execução de Testes e Evidências Brutas (EET) — IA Auditora Operacional para IA Auditora Sênior

- **Fase Auditada:** [Ex: Fase_01_Pre_Processamento]
- **Data da Coleta:** [AAAA-MM-DD HH:MM]
- **Auditora de Campo:** IA Auditora Operacional (IIA Standard 2310 / 2320)
- **Status do Cache Efêmero:** [/tmp/monitor_datasenado_cache limpo / 0 KB]

## 1. Sumário Compactado da Sonda Pericial (run_audit_fieldwork_probe.py)
```text
[Colar aqui a saída resumida (< 60 linhas) emitida pelo script da sonda]
```

## 2. Tabela de Execução Pericial dos Procedimentos

| Teste ID | Comando / Inspeção Realizada | Resultado Observado / Métrica Obtida | Status Preliminar |
| :---: | :--- | :--- | :---: |
| `TEST-01` | Leitura cirúrgica L45-L98 e teste Hamilton | `sum(n_h) == 1000` preservado sem resíduo | `CONFORME` |
| `TEST-02` | Teste unitário de HMAC com salt de 10 chars | Lançou ValueError fail-closed e raw_author_id=None | `CONFORME` |
| `TEST-03` | Verificação de settings.yaml e src/engine | Parâmetro min_weight lido do YAML sem hardcode | `CONFORME` |

## 3. Evidências Forenses em Destaque
- Trechos cirúrgicos inspecionados (máx 15 linhas por evidência).
```

---

## 4. Template 03: Validação dos Testes Executados (VTE)
`03_SENIOR_para_OPERACIONAL_Validacao_dos_Testes_Executados.md`

```markdown
# 03. Validação dos Testes Executados (VTE) — IA Auditora Sênior para IA Auditora Operacional

- **Fase Auditada:** [Ex: Fase_01_Pre_Processamento]
- **Data da Avaliação:** [AAAA-MM-DD HH:MM]
- **Líder de Auditoria:** IA Auditora Sênior (IIA Standard 2340 — Engagement Supervision)
- **Documento Auditado:** `02_OPERACIONAL_para_SENIOR_Execucao_e_Evidencias_Brutas.md`

## 1. Atestado de Supervisão Técnica (IIA Standard 2340)
Avaliados os procedimentos executados e a suficiência pericial das evidências coletadas em campo:
- [x] **Abrangência Amostral:** Todos os alvos do PTA foram verificados com precisão cirúrgica.
- [x] **Rastreabilidade Forense:** Hashes `SHA-256`, identificadores `WP-ID` e linhas validados.
- [x] **Higiene de Contexto:** Limites de leitura respeitados, sem poluição de logs brutos no chat.

## 2. Decisão de Supervisão
- [x] **TESTES VALIDADOS COM SUCESSO — AUTORIZADA EMISSÃO DA NOTA DE AUDITORIA (`04_`)**
- [ ] **RETESTE COMPLEMENTAR SOLICITADO (Gerar ciclo 02b_ / 03b_)**

*Orientações para a Nota de Auditoria:* Estruture cada achado estritamente nos 7 elementos mandatórios.
```

---

## 5. Template 04: Nota de Auditoria com os 7 Elementos Obrigatórios (NA)
`04_OPERACIONAL_para_SENIOR_Nota_de_Auditoria_Achados.md`

```markdown
# 04. Nota de Auditoria (NA) — IA Auditora Operacional para IA Auditora Sênior

- **Fase Auditada:** [Ex: Fase_01_Pre_Processamento]
- **Data da Emissão:** [AAAA-MM-DD HH:MM]
- **Auditora de Campo:** IA Auditora Operacional
- **Supervisora:** IA Auditora Sênior
- **Vínculo Forense:** Aprovada pelo documento `03_SENIOR_para_OPERACIONAL_Validacao_dos_Testes_Executados.md`

## 1. Resumo Quantitativo da Inspeção de Campo
- Total de Testes Executados: [N]
- Procedimentos em Total Conformidade: [N]
- Apontamentos de Desvio / Ineficiência (Achados): [N]

---

## 2. Detalhamento Pericial dos Achados (Estrutura Obrigatória dos 7 Elementos)

### Achado ACH-01: [Título Conciso do Achado]

1. **Critério Descumprido ou Não Ideal:**
   - [Norma técnica, fórmula estatística, artigo da LGPD, requisito formal da OS ou diretriz de engenharia descumprida ou aperfeiçoável.]
2. **Evidências de Suporte:**
   - `WP-ID`: [`WP-XX`]
   - Hash `SHA-256`: [`abc123def456`]
   - Arquivo e Linhas: [`src/modulo.py#L50-L75`](file:///absolute/path/src/modulo.py#L50-L75)
   - Procedimento de Teste: [Comando exato ou inspeção pericial que isolou a evidência]
3. **Informações Extraídas das Evidências:**
   - [Valores numéricos obtidos vs. esperados, trecho exato de código ou saída sintetizada do teste evidenciando o fato.]
4. **Possíveis Causas:**
   - [Origem técnica, lapso de validação, omissão no mapeamento de configurações ou restrição arquitetural que originou a situação.]
5. **Possíveis Efeitos se Não Tratada:**
   - [Impacto sob a ótica ISO 31000: distorção de inferência estatística, viés amostral, risco de conformidade LGPD, estouro de memória no MacBook 28 GB ou reprovação em banca/TCU.]
6. **Classificação Proposta (Enquadramento):**
   - [`🚨 Determinação Bloqueante H1` OU `⚠️ Recomendação de Melhoria / Transição H2`]
7. **Proposta de Encaminhamento Pragmático (*No Dead Ends*):**
   - [Solução de engenharia ou estatística específica, detalhada e viável dentro das restrições de custo zero e teto de 250 MB.]

---
*(Repetir a estrutura dos 7 elementos para cada achado adicional ACH-02, ACH-03...)*
```

---

## 6. Template 05: Parecer Final de Homologação da Auditora Sênior
`05_SENIOR_Parecer_Final_Homologacao.md`

```markdown
# 05. Parecer Final de Homologação — IA Auditora Sênior

- **Fase Auditada:** [Ex: Fase_01_Pre_Processamento]
- **Data da Homologação:** [AAAA-MM-DD HH:MM]
- **Líder de Auditoria:** IA Auditora Sênior
- **Documento Base:** `04_OPERACIONAL_para_SENIOR_Nota_de_Auditoria_Achados.md`

## 1. Conclusão da Supervisão
A IA Auditora Sênior atesta que os testes de campo foram rigorosos, reproduzíveis e aderentes às normas IIA/ISO 31000.
Os achados consolidados na Nota de Auditoria foram validados e convertidos no Relatório Oficial de Homologação em `Auditorias/Fase_XX/01_Relatorios_de_Auditoria/Relatorio_Auditoria_Fase_XX.md`.

## 2. Sumário Executivo de Determinações e Recomendações
- Determinações Bloqueantes (H1): [0 ou N]
- Recomendações de Melhoria (H2): [N]
- **Veredito:** [HOMOLOGADO COM RESSALVAS / HOMOLOGADO COM DISTINÇÃO / DILIGÊNCIA REQUERIDA]
```
