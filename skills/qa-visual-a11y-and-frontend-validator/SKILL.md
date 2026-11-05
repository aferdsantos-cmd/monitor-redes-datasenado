---
name: qa-visual-a11y-and-frontend-validator
description: Use this skill whenever performing visual quality control, UI/UX auditing, WCAG 2.2 accessibility verification, layout stability (CLS=0) and Core Web Vitals checks, statistical/LGPD UI honesty validation, or orchestrating live browser inspections with Chrome DevTools MCP.
---

# Validador de Qualidade Visual, Acessibilidade WCAG 2.2 e Honestidade Estatística

Portão de controle de qualidade visual, acessibilidade universal e integridade estatística na interface da Bancada Analítica do DataSenado, operando em modo offline determinístico e em orquestração ao vivo com Chrome DevTools MCP.

## 1. Arquitetura de Dupla Verificação Visual
- **Modo 1 — Sonda Offline Determinística (`visual_ui_and_a11y_quality_gate.py`):** Execução sem necessidade de navegador externo, inspecionando código JSX/TSX, CSS, DOM sintético e configurações ECharts, gerando certificado auditável com resultado binário (`PASS`/`FAIL`).
- **Modo 2 — Inspeção Ao Vivo via Chrome DevTools MCP:** Quando o servidor estiver ativo, orquestra inspeções com `chrome-devtools` (`take_screenshot`, `evaluate_script`), `a11y-debugging` (`take_snapshot` da árvore de acessibilidade) e `debug-optimize-lcp` (`performance_start_trace` para medir `LCP < 2.5s` e `CLS == 0.00`).

## 2. Os 4 Portões do Visual QA (Critérios Inegociáveis)
- **Portão 1 — Anti-AI-Slop & Tipografia:** Zero gradientes neon clichês de IA, zero emojis operacionais, 100% de `tabular-nums` em dados e uso exclusivo da paleta institucional e Okabe-Ito.
- **Portão 2 — Contraste WCAG 2.2 & A11y:** Razão de contraste matemático $\ge 4.5:1$ para texto e $\ge 3.0:1$ para elementos gráficos, navegação por teclado sem armadilhas de foco e `prefers-reduced-motion`.
- **Portão 3 — Zero CLS & UX Fluida:** Todo container assíncrono TanStack Query possui `Skeleton` com mesma geometria (`CLS = 0`), filtros via URL state (Nuqs) sem recarregar a página e transições Framer Motion não-bloqueantes.
- **Portão 4 — Honestidade Estatística & LGPD:** Exibição obrigatória de $n$, $N_{\text{org}}$, barras de erro de IC 95%, Kish DEFF, rótulo honesto do Cenário 3 e mascaramento LGPD ($k \ge 5$ e hashes truncados).

## 3. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Validar os 4 Portões antes de qualquer release; garantir Skeletons idênticos ao layout final; exibir IC 95% em gráficos de opinião; verificar contraste em ambos os temas.
- **MUST NOT DO:** Não liberar tela com CLS > 0; não omitir incerteza estatística em gráficos de opinião; não ignorar avisos de contraste WCAG; não exibir células com $k < 5$ sem mascaramento.

## 4. Matriz de Roteamento e Fronteiras de Competência
- Para tokens visuais, paleta Okabe-Ito e linter de design: use `ui-ux-design-system-and-anti-ai-craft`.
- Para arquitetura de componentes React, Radix e Nuqs: use `fe-react-tailwind-radix-architecture`.
- Para gráficos interativos ECharts e exportação `@media print`: use `fe-data-viz-grids-maps-and-export`.
- Para auditoria sênior IIA/ISO 31000 e pareceres finais: use `audit-iia-iso31000-datasenado`.

## 5. Sonda Executável e Referências Aprofundadas
- Execute o portão de qualidade visual e acessibilidade:
  ```bash
  ./skills/qa-visual-a11y-and-frontend-validator/scripts/visual_ui_and_a11y_quality_gate.py --demo
  ```
- **Manuais Técnicos:**
  - [visual_qa_checklist_and_anti_hallucination.md](./references/visual_qa_checklist_and_anti_hallucination.md)
  - [chrome_devtools_mcp_and_live_ui_inspection.md](./references/chrome_devtools_mcp_and_live_ui_inspection.md)
