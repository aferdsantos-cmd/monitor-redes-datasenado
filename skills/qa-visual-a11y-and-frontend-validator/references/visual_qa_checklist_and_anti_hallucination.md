# Checklist de Controle de Qualidade Visual, Anti-Alucinação e os 4 Portões

Este manual técnico define os critérios periciais de inspeção e auditoria para a interface gráfica da Bancada Analítica do DataSenado, assegurando conformidade estética, matemática, de acessibilidade e honestidade estatística.

---

## 1. Fundamentos da Auditoria Visual Independente

Em pesquisas legislativas de opinião pública digital, a interface gráfica é o ponto de contato entre a modelagem estatística complexa e a decisão parlamentar. Distorções visuais (como escalas enganosas, omissão de margens de erro ou contrastes ilegíveis) constituem falhas graves de governança analítica.

---

## 2. Os 4 Portões Visuais Inegociáveis (Visual QA Gates)

A certificação de qualquer tela ou componente da Bancada do DataSenado exige aprovação compulsória nos 4 portões:

### 2.1 Portão 1: `ANTI_AI_SLOP_AND_TYPOGRAPHY_GATE`
- **Critério 1.1:** Ausência absoluta de gradientes neon genéricos de IA (`from-indigo-`, `via-purple-`, `to-pink-`);
- **Critério 1.2:** Ausência de sombras neon coloridas (`shadow-indigo-`, `shadow-purple-`);
- **Critério 1.3:** Raios de curvatura de cards e painéis contidos em `rounded-md` / `rounded-lg` (reprovação imediata de `rounded-3xl` em dashboards);
- **Critério 1.4:** Ausência de emojis em títulos de seções, cabeçalhos de tabela, cards de KPI e botões operacionais;
- **Critério 1.5:** Presença obrigatória da propriedade `tabular-nums` em 100% dos elementos numéricos e tabelas analíticas.

### 2.2 Portão 2: `WCAG22_CONTRAST_AND_A11Y_GATE`
- **Critério 2.1:** Razão de contraste matemático $\text{CR} \ge 4.5:1$ para texto regular e $\ge 3.0:1$ para textos grandes e componentes visuais de gráficos;
- **Critério 2.2:** Navegação completa por teclado (sem dependência de mouse) utilizando primitivos Radix UI / React Aria, com anéis de foco visíveis (`focus-visible:ring-2`);
- **Critério 2.3:** Presença de `aria-label`, `aria-hidden="true"` em ícones puramente decorativos e estrutura semântica correta (`h1`-`h4`, `nav`, `main`, `toolbar`);
- **Critério 2.4:** Respeito integral à diretiva de acessibilidade de movimento (`prefers-reduced-motion: reduce`).

### 2.3 Portão 3: `ZERO_CLS_SKELETON_AND_FLUID_UX_GATE`
- **Critério 3.1:** Eliminação de saltos visuais durante o carregamento assíncrono: Cumulative Layout Shift medido com $\text{CLS} == 0.00$;
- **Critério 3.2:** Presença de *Skeleton Screens* estruturais para todo card, gráfico e tabela com altura mínima e geometria idênticas ao componente preenchido;
- **Critério 3.3:** Sincronização de filtros na query string da URL via Nuqs sem disparar `window.location.reload()`.

### 2.4 Portão 4: `STATISTICAL_AND_LGPD_UI_HONESTY_GATE`
- **Critério 4.1:** Todo gráfico ou tabela de estimativa de prevalência populacional deve declarar explicitamente o tamanho da amostra auditada ($n$) e a contagem do universo orgânico observado ($N_{\text{org}}$);
- **Critério 4.2:** Presença obrigatória de barras ou bandas de erro com **Intervalo de Confiança de 95% (`IC 95%`)**;
- **Critério 4.3:** Identificação honesta dos 3 cenários metodológicos, explicitando o rótulo: *"Cenário 3 — Reponderado via Raking IPF sob Hipótese de Ignorabilidade"*;
- **Critério 4.4:** Blindagem LGPD na tela: truncamento visual de hashes para 10 caracteres e colapso compulsório de células demográficas com $k < 5$ contas orgânicas.

---

## 3. Matriz de Decisão do Certificado Visual
| Situação da Auditoria | Classificação | Encaminhamento Operacional |
| :--- | :--- | :--- |
| Todos os 4 Portões Aprovados | **CERTIFICADO CONFORME (PASS)** | Liberação da tela para produção ou parecer de auditoria |
| Falha no Portão 1 ou 2 | **REPROVADO — ERGONOMIA/A11Y** | Bloqueio de release; ajuste mandatório de tokens e classes |
| Falha no Portão 3 | **REPROVADO — INSTABILIDADE CLS** | Bloqueio de release; adição de Skeletons dimensionados |
| Falha no Portão 4 | **REPROVADO — RISCO EPISTÊMICO/LGPD** | Bloqueio imediato; correção de honestidade estatística |
