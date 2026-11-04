# Plano de Implementação Histórico (v1.0 — SUPERSEDED)

> [!WARNING]
> **DOCUMENTO HISTÓRICO SUPERADO (SUPERSEDED BY v1.1 / v1.2):**  
> Este plano original v1.0 foi formalmente emendado por [`docs/03_Termo_de_Emenda_Plano_v1_1_e_ADR.md`](03_Termo_de_Emenda_Plano_v1_1_e_ADR.md), [`docs/01_Metodologia_Cientifica_e_Estatistica_NotebookLM.md`](01_Metodologia_Cientifica_e_Estatistica_NotebookLM.md) e [`docs/02_Plano_Validacao_Estatistica.md`](02_Plano_Validacao_Estatistica.md).  
> Qualquer referência a termos obsoletos deste plano original (como "MRP", "inferência sobre população brasileira", "bot_risk_score" ou unidades observacionais baseadas em postagens) foi expressamente revogada pelos `ADR-001` a `ADR-006`.

---

## 1. Resumo Estrutural do Plano Original (v1.0)

O plano inicial concebido para o projeto previa:
1. **Pipeline de Coleta:** Ingestão de postagens em 6 plataformas sociais utilizando consultas textuais com termos de busca e termos valorativos em conjunto.
2. **Camada de Limpeza e Anonimização:** Limpeza de identificadores de autoria e cálculo de índice composto experimental de robôs (`bot_risk_score`).
3. **Pós-Estratificação:** Intenção inicial de aplicar técnicas de *Multilevel Regression and Post-Stratification (MRP)* com base em variáveis sociodemográficas inferidas.
4. **Infraestrutura:** Planejamento de uso de armazenamento em nuvem e bibliotecas analíticas convencionais.

---

## 2. Motivação da Revisão e Emendas Formais (Fase 01)

Durante a 1ª e a 2ª rodadas de Auditoria Científica e Metodológica da Fase 01, foram identificados os seguintes limites e aprimoramentos epistemológicos:
- **Revogação do MRP (ADR-001):** Redes sociais não fornecem dados censitários individuais auditáveis. O estimando foi formalizado estritamente sobre o **Universo Finito Observado de Contas Orgânicas ($\mathcal{U}_{\text{Org}, T}$)**, adotando-se o estimador de Hájek e calibração por Raking IPF (Cenário 3) sob hipótese de ignorabilidade condicional.
- **Unidade Observacional (ADR-002):** Transição de "postagens" para **`1 Autor Digital Orgânico por Plataforma = 1 Unidade Observacional`**, eliminando a distorção gerada por hiperatividade individual.
- **Desinfecção CIB e LGPD (ADR-003, ADR-005):** Proteção de dados via `HMAC-SHA256` *fail-closed*, detecção de coordenação temporal via LSH e partição de Leiden com isolamento de redes coordenadas em nível de conta.
- **Portabilidade Zero-Footprint (ADR-004):** Operação sob cache estrito de 250 MB em `/tmp` com `uv` standalone no macOS, sem necessidade do pesado Xcode CLT.

Para todos os efeitos analíticos, de auditoria e de conformidade pericial, prevalecem as diretrizes registradas no **Termo de Emenda Formal v1.1/v1.2** (`docs/03_Termo_de_Emenda_Plano_v1_1_e_ADR.md`).
