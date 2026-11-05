---
name: ds-xai-and-model-explainability
description: Use this skill whenever generating global or local model explanations (SHAP, LIME, Permutation Importance, Partial Dependence), auditing black-box NLP/ML classifiers for legislative transparency, or testing subgroup fairness and sensitivity/specificity stability across platforms, regions, and political spectra.
---

# Explicabilidade de Modelos (XAI), SHAP/LIME e Equidade por Subgrupo

Diretrizes de transparência algorítmica, interpretabilidade local/global e auditoria de viés por subgrupo para o Monitor de Redes DataSenado, em total alinhamento com os padrões de auditoria pública do TCU e rigor epistêmico do TCC.

## 1. Proibição de Modelos Caixa-Preta em Relatórios Públicos
- **Transparência Compulsória:** Nenhuma classificação automatizada de opinião, polarização ou tema legislativo pode ser apresentada sem a devida decomposição de fatores determinantes (*Feature Importance* global e atribuição local de termos/atributos).
- **Auditabilidade TCU:** Decisões algorítmicas de interesse público devem ser rastreáveis e justificáveis sob escrutínio de órgãos de controle e da sociedade civil.

## 2. Rigor Matemático em Valores SHAP e Permutation Importance
- **Axioma da Eficiência de Shapley (Aditividade Local):**
  $$\left| \left( \phi_0 + \sum_{j=1}^M \phi_{ij} \right) - f(x_i) \right| < 10^{-5}$$
  onde $\phi_0 = \mathbb{E}[f(x)]$ é o valor base esperado e $\phi_{ij}$ é a contribuição marginal do atributo $j$ para a observação $i$.
- **Permutation Importance Estritamente em Hold-Out:** A avaliação da queda de desempenho ($\Delta\text{Macro-F1}$ ou $\Delta\text{MCC}$) por permutação de variáveis deve ser executada exclusivamente na partição de validação/teste congelada. É proibido computá-la sobre a partição de treino!

## 3. Explicabilidade Textual e Racionalidade Editorial (LIME / Atribuição)
- **Atribuição Lexical Local:** Decomposição dos termos e expressões que deslocaram a probabilidade predita para `Favorável`, `Contrário` ou `Neutro`.
- **Inteligência 360º (ADR-011):** Diagnóstico de adjetivos, verbos modalizadores e omissões textuais que justificam o enquadramento editorial.

## 4. Auditoria de Equidade Algorítmica por Subgrupo
- **Estabilidade de Sensibilidade e Especificidade:** Avaliar se $\text{Se}_{c,g}$ e $\text{Sp}_{c,g}$ variam substancialmente entre subgrupos $g \in \{\text{Plataformas}, \text{Macrorregiões}, \text{Espectros}\}$.
- **Gatilho de Reparação:** Se a disparidade $|\text{Se}_{c,g} - \text{Se}_{c,g'}| > 0.08$, deve-se acionar a correção de Rogan-Gladen estratificada por subgrupo em `stats-inference-datasenado`.

## 5. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Verificar aditividade SHAP; computar permutation importance em hold-out; auditar paridade de erro entre canais; documentar top features.
- **MUST NOT DO:** Não publicar predições sem explicabilidade local; não avaliar importância de variáveis no treino; não assumir que SHAP implica causalidade; não usar pickle.

## 6. Matriz de Roteamento e Fronteiras de Competência
- Para treinamento e validação cruzada anti-leakage: use `ds-ml-modeling-and-validation`.
- Para correção de prevalência de Rogan-Gladen estratificada: use `stats-inference-datasenado`.
- Para monitoramento de drift de produção (PSI): use `ds-mlops-and-model-lifecycle`.

## 7. Sonda Executável e Referências Aprofundadas
- Execute a sonda de explicabilidade SHAP e equidade de subgrupos:
  ```bash
  ./skills/ds-xai-and-model-explainability/scripts/xai_shap_and_subgroup_fairness_auditor.py --demo
  ```
- **Manuais Técnicos:**
  - [shap_lime_and_permutation_workflows.md](./references/shap_lime_and_permutation_workflows.md)
  - [public_sector_xai_and_subgroup_fairness.md](./references/public_sector_xai_and_subgroup_fairness.md)
