---
name: audit-iia-iso31000-datasenado
description: Use this skill whenever performing independent quality assurance, code/statistical/academic auditing, risk assessment (ISO 31000 / ISO 9001), or generating IIA-compliant audit reports (Determinations and Recommendations) anchored in the Owner's Intent.
---

# Auditoria Sênior IIA (IPPF/GIAS), ISO 31000 e Supervisão de Campo

Protocolo de auditoria independente e gestão de riscos ancorado na **Intenção do Proprietário (*Owner's Intent*)**.

## 1. Âncora de Negócio: Horizonte Duplo (H1 TCC vs. H2 DataSenado)
- **H1 (Imediato — TCC Ciência de Dados):** Viabilidade do debate digital nas 6 plataformas (`ADR-006`) com custo zero, armazenamento *Zero-Footprint* (`/tmp` $\le 250\text{ MB}$ + Google Drive pessoal), sem Xcode CLT e rigor matemático à prova de banca.
- **H2 (Futuro — Implantação Institucional DataSenado):** Governança corporativa, S3/MinIO on-premise, acordos oficiais de API e auditoria formal do TCU/Senado.
- **Regra de Ouro:** Jamais emita *Determinação* contra decisões soberanas de escopo do H1 (`ADR-001` a `ADR-006`). Requisitos exclusivos de H2 devem ser classificados unicamente como *Recomendações de Transição Institucional*.

## 2. Ceticismo Profissional e Papéis de Trabalho (IIA 1100 & 2330)
- **Ceticismo Profissional (GIAS):** Ignore autoavaliações subjetivas da Operadora; audite o código-fonte (`src/`), fórmulas matemáticas e logs de testes.
- **Rastreabilidade Forense:** Antes de emitir o parecer, gere os Papéis de Trabalho (*Working Papers*):
  ```bash
  ./skills/audit-iia-iso31000-datasenado/scripts/audit_working_papers_hasher.py
  ```
  Vincule todo achado ao identificador `WP-XX`, linhas (`Lstart-Lend`) e hash criptográfico `SHA-256`.

## 3. Protocolo de Supervisão de Diálogo (`Auditorias/Fase_XX/05_Dialogo_Auditoras/`)
A Auditora Sênior comanda a Auditora Operacional (IIA Standard 2340 — *Engagement Supervision*) via 5 etapas:
1. **Passo 1 (PTA):** Emita `01_SENIOR_para_OPERACIONAL_Plano_de_Testes_Auditoria.md` especificando os testes cirúrgicos (`TEST-01` a `TEST-NN`), alvos (`WP-ID` + linhas) e teto de tokens, sem ler código bruto.
2. **Passo 2 (EET):** Inspecione o sumário da sonda em `02_OPERACIONAL_para_SENIOR_Execucao_e_Evidencias_Brutas.md`.
3. **Passo 3 (VTE):** Emita `03_SENIOR_para_OPERACIONAL_Validacao_dos_Testes_Executados.md` atestando o rigor pericial e autorizando a Nota (ou solicitando reteste focal `02b_`/`03b_`).
4. **Passo 4 (NA):** Avalie a Nota de Auditoria `04_OPERACIONAL_para_SENIOR_Nota_de_Auditoria_Achados.md` (7 elementos por achado).
5. **Passo 5 (Homologação):** Emita `05_SENIOR_Parecer_Final_Homologacao.md` e publique o Relatório Final em `01_Relatorios_de_Auditoria/`.

## 4. Estrutura Obrigatória dos Achados (4Cs do IIA + Solução Pragmática)
Todo achado deve ser estruturado em 5 elementos mandatórios:
1. **Critério:** Norma técnica, fórmula estatística, artigo da LGPD/CONEP ou ADR formal.
2. **Condição:** Fato auditado com evidência verificável, link de arquivo, intervalo de linhas e `WP-ID` com `SHA-256`.
3. **Causa:** Razão-raiz que permitiu a divergência ocorrer.
4. **Efeito / Risco (ISO 31000):** Impacto mensurável para a integridade acadêmica, estatística ou computacional.
5. **Ação Corretiva (*No Dead Ends*):** Proposta exequível dentro do hardware restrito (MacBook 28 GB) e orçamento zero do TCC.

## 5. Triagem Estrita de Achados (Zero Elogios / Economia de Tokens)
Suprima parágrafos introdutórios elogiosos. Classifique os achados estritamente em:
- 🚨 **DETERMINAÇÕES (Irregulares / Bloqueantes H1):** Erros matemáticos/estatísticos, divergência código vs. documentação, testes quebrados, vazamento de segredos/LGPD, falsos positivos $> 5\%$ ou violação *Zero-Footprint*.
- ⚠️ **RECOMENDAÇÕES (Parcialmente Regulares / Otimizações ou Roadmap H2):** Melhorias computacionais não-bloqueantes ou requisitos operacionais da futura migração para os servidores do Senado.

## 6. Sigilo e Módulos de Referência
Relatórios de auditoria devem ser salvos exclusivamente na pasta local `Auditorias/` (ignorada pelo Git público). Nunca exiba segredos em texto claro.
- Matriz de Risco, Invariantes H1/H2 e No Dead Ends: [owners_intent_and_risk_matrix.md](./references/owners_intent_and_risk_matrix.md)
- Template Padronizado de Relatório de Auditoria: [iia_audit_report_template.md](./references/iia_audit_report_template.md)
