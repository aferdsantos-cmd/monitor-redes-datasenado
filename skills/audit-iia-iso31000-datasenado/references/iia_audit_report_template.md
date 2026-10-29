# Template Oficial de Relatório de Auditoria Sênior (IIA / ISO 31000)

Use este template rigoroso para elaborar relatórios de auditoria e pareceres de homologação. O documento é estruturado para garantir rastreabilidade pericial total, supressão de prolixidade (*zero fluff*) e respeito intransigente à Intenção do Proprietário (*Owner's Intent*).

---

```markdown
# Relatório de Auditoria Independente de Qualidade e Conformidade
## Avaliação Pericial: Normas IIA (IPPF/GIAS), ISO 31000:2018 e Acórdãos TCU/Senado

- **Ordem de Serviço Auditada:** `OS_FaseXX_Nome`
- **Data da Auditoria:** YYYY-MM-DD HH:MM BRT
- **Auditor Responsável:** IA Auditora Independente (Skill `audit-iia-iso31000-datasenado`)
- **Auditado:** IA Operadora / Executora Técnica
- **Destinatário:** IA Cérebro (Planejador e Autoridade Metodológica)

---

### 🎯 1. OBJETIVO DO NEGÓCIO ANCORADO (OWNER'S INTENT)
- **Horizonte H1 (TCC Ciência de Dados):** [Síntese da entrega auditada, confirmando alinhamento com ADR-001 a ADR-006, viabilidade em MacBook de 28 GB e custo zero].
- **Horizonte H2 (Roadmap DataSenado):** [Mapeamento de aspectos institucionais futuros sem interferência bloqueante em H1].
- **Status Geral da Auditoria:** 
  - `[ ] HOMOLOGADO INTEGRALMENTE (Sem ressalvas)`
  - `[ ] HOMOLOGADO COM RECOMENDAÇÕES (Regular com melhorias para H2)`
  - `[ ] RETIDO POR DETERMINAÇÕES BLOQUEANTES (Irregular no escopo H1)`

---

### 📂 2. INVENTÁRIO DE PAPÉIS DE TRABALHO AUDITADOS (WORKING PAPERS — IIA 2330)
> *Tabela gerada automaticamente pelo script `audit_working_papers_hasher.py` garantindo integridade forense via SHA-256.*

| WP-ID | Arquivo | Linhas | Bytes | SHA-256 (12 hex) | Status de Auditoria |
| :---: | :--- | :---: | :---: | :---: | :---: |
| `WP-01` | `src/core/sampler.py` | 142 | 4.821 | `a1b2c3d4e5f6` | Conforme |
| `WP-02` | `src/nlp/classifier.py` | 98 | 3.200 | `f6e5d4c3b2a1` | Conforme |
| `WP-03` | `tests/test_sampler.py` | 65 | 2.100 | `0123456789ab` | Conforme |
| `...` | `...` | `...` | `...` | `...` | `...` |

---

### 🚨 3. DETERMINAÇÕES (SITUAÇÕES GRAVES / IRREGULARES NO ESCOPO H1)
*Situações de inconformidade matemática, quebra de testes, violação da LGPD/CONEP ou falhas no código que invalidam a entrega do TCC.*

#### Determinação DET-01: [Título Descritivo e Objetivo]
1. **Critério:** [Artigo da lei, norma ABNT/IIA/ISO, teorema estatístico ou cláusula da OS violada].
2. **Condição (Evidência Pericial):** [Descrição exata do fato encontrado, referenciando `WP-ID`, arquivo, linhas exatas e trecho de código/fórmula].
3. **Causa:** [Fator que permitiu o erro acontecer, ex.: falta de asserção de limite no código].
4. **Efeito / Risco para o Negócio (ISO 31000):** [Impacto mensurável, ex.: distorção da estimativa pontual em até 15%, risco de reprovação em banca ou quebra de pipeline].
5. **Ação Corretiva Exigida (*No Dead Ends*):** [Solução técnica pragmática, viável no hardware do proprietário e no orçamento zero do TCC].

*(Caso não existam determinações, registrar explicitamente: "Nenhuma determinação bloqueante identificada.")*

---

### ⚠️ 4. RECOMENDAÇÕES (PARCIALMENTE REGULARES / OTIMIZAÇÕES & ROADMAP H2)
*Oportunidades de melhoria técnica não-bloqueantes para o TCC ou requisitos da futura implantação corporativa no Senado Federal.*

#### Recomendação REC-01: [Título da Otimização ou Requisito H2]
1. **Critério:** [Boa prática de engenharia, recomendação de governança do Senado ou padrão ISO 9001].
2. **Condição (Evidência):** [Situação atual que funciona no H1 mas pode ser aperfeiçoada para o H2, citando `WP-ID`].
3. **Causa:** [Priorização do escopo enxuto do TCC em relação a sistemas corporativos de larga escala].
4. **Oportunidade / Benefício (ISO 31000):** [Ganho de robustez institucional, facilidade de manutenção por terceiros ou auditoria pelo TCU].
5. **Ação Recomendada (*Roadmap H2*):** [Sugestão técnica para implementação futura sem impacto no cronograma do TCC].

---

### 📊 5. MATRIZ DE RASTREABILIDADE E HISTÓRICO DE CORREÇÕES
*Acompanhamento de deliberações anteriores para assegurar que falhas sanadas permaneçam resolvidas (IIA 2500).*

| Código | Descrição Resumida | Situação Anterior | Situação Atual | Evidência de Resolução (`WP-ID`) |
| :---: | :--- | :---: | :---: | :--- |
| `DET-00` | Exemplo de correção anterior | Aberto | Resolvido | `WP-01` (Linha 45, teste verde) |
| `REC-00` | Exemplo de melhoria sugerida | Em análise | Implementado | `WP-02` (Linha 80) |

---
```
