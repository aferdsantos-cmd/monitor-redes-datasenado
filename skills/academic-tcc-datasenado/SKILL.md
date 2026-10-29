---
name: academic-tcc-datasenado
description: Use this skill whenever structuring research designs, writing or reviewing TCC chapters, scientific articles (IMRaD), methodology sections, literature reviews with DOI verification, mixed-methods analysis, publication-grade visualizations, CONEP/LGPD research ethics, Reviewer 2 peer-review simulations, or DataSenado technical bulletins.
---

# Excelência Científica, Epistemologia e Padrão DataSenado / TCC

Orquestrador dos 5 Pilares de integridade acadêmica para redação de artigos (IMRaD), capítulos de TCC em Ciência de Dados e boletins técnicos do DataSenado.

## 1. Pilar 1 — Raciocínio Epistemológico, Desenho e Validade
- **População e Estimando:** Delimitação estrita sobre o Universo Finito Observado de Contas Orgânicas ($\mathcal{U}_{\text{Org}, T}$). Unidade observacional = `1 Conta Orgânica por Plataforma` nas 6 redes (`ADR-006`).
- **Ameaças à Validade (Shadish et al., 2002):** Mitigação estruturada de ameaças à Validade de Conclusão Estatística (DEFF, Hamilton, Bootstrap), Interna (LSH, Leiden, Allowlist), Construto (Rogan-Gladen) e Externa (fronteira entre debate digital e população geral).
- **Referência:** [epistemic_boundaries.md](./references/epistemic_boundaries.md)

## 2. Pilar 2 — Métodos Mistos (Quali-Quanti) e Visualização Científica
- **Triangulação Quali-Quanti:** Integração entre inferência amostral estratificada (C1, C2, C3) e análise de conteúdo categorial (*Bardin, 2011*) para exploração de enquadramentos (*frames*).
- **Padrão Gráfico Internacional (Elsevier/Springer/IEEE):** Paleta acessível Okabe-Ito (`#0072B2` favorável, `#D55E00` contrário, `#999999` neutro), barras de erro de IC 95% obrigatórias, 300+ DPI. Proibição de gráficos de pizza ou 3D.
- **Referência:** [scientific_viz_and_mixed_methods.md](./references/scientific_viz_and_mixed_methods.md)

## 3. Pilar 3 — Bibliometria e Rastreabilidade Anti-Alucinação (DOI)
- **Protocolo Zero-Hallucination:** Proibição de citações sem correspondência canônica estruturada e DOI oficial verificável (ISO 26324).
- **Auditoria de Citações:** Executar o script verificador determinístico antes de submeter textos:
  ```bash
  ./skills/academic-tcc-datasenado/scripts/verify_citations_doi.py
  ```

## 4. Pilar 4 — Escrita Científica de Alto Impacto (IMRaD, ABNT, APA, LaTeX)
- **Arquitetura IMRaD:** Estrutura modular (Introduction $\to$ Methods $\to$ Results $\to$ Discussion) para relatórios parlamentares, papers e capítulos de TCC.
- **Normas Atualizadas:** Citação autor-data com iniciais maiúsculas conforme **ABNT NBR 10520:2023** `(Meng, 2018)`, referências **NBR 6023:2018**, e compatibilidade APA 7th / BibTeX.
- **Referências:**
  - [imrad_writing_and_norms.md](./references/imrad_writing_and_norms.md)
  - [datasenado_report_template.md](./references/datasenado_report_template.md)

## 5. Pilar 5 — Ética em Pesquisa (CONEP/LGPD) e Simulação "Reviewer 2"
- **Resolução CNS/CONEP nº 510/2016:** Dispensa de submissão a CEP/CONEP fundamentada no Art. 1º, Parágrafo Único, incisos II, III e V (dados públicos e agregados sem reidentificação individual).
- **LGPD:** Base legal de órgão de pesquisa (Art. 7º, IV e Art. 13) com pseudonimização HMAC-SHA256 e proibição de citação literal de cidadãos sem paráfrase ética (*bricolage*).
- **Simulador "Reviewer 2":** Rubrica de 10 perguntas adversárias de banca examinadora para blindagem de textos.
- **Referência:** [ethics_conep_and_reviewer2_protocol.md](./references/ethics_conep_and_reviewer2_protocol.md)
