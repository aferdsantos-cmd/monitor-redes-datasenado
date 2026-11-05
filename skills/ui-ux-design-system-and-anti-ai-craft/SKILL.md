---
name: ui-ux-design-system-and-anti-ai-craft
description: Use this skill whenever designing UI/UX layouts, defining color/typography/spacing tokens, applying the DataSenado institutional identity and Okabe-Ito scientific palette, enforcing tabular numerals and high data density, or auditing interfaces to eliminate generic AI-generated design patterns (Anti-AI-Slop).
---

# Design System Institucional DataSenado, UX Data-Dense e Anti-AI-Slop

Padrões de design visual, ergonomia analítica e identidade institucional do Senado Federal para o Monitor de Redes DataSenado, erradicando clichês visuais de "IA genérica" (*AI-Slop*) e assegurando alta densidade informacional (Tufte) e conformidade estrita com as normas de acessibilidade WCAG 2.2 AA/AAA.

## 1. Tokens de Cor Institucionais e Paleta Científica Okabe-Ito
- **Superfícies e Bordas Capilares (`1px`):**
  - *Modo Claro Editorial:* Fundo `bg-slate-50` (`#F8FAFC`), superfície `#FFFFFF`, bordas `#E2E8F0`, texto `#0F172A`.
  - *Modo Escuro Bancada:* Fundo `bg-[#090D16]`, superfície `#0F172A`, bordas `#1E293B`, texto `#F8FAFC`.
- **Acentos Institucionais:** Azul Senado (`#0B1F3A` / `#1E3A8A`) e Dourado Sóbrio (`#B45309`).
- **Paleta Científica Okabe-Ito (100% Segura para Daltônicos):**
  - `FAVORAVEL`: `#0072B2` (Azul Okabe-Ito);
  - `CONTRARIO`: `#D55E00` (Vermelho-Terracota Okabe-Ito);
  - `NEUTRO_INFORMATIVO`: `#64748B` / `#7F7F7F` (Cinza Neutro);
  - `BOLHA_ESPECTRO_A`: `#009E73` (Verde-Azulado) | `BOLHA_ESPECTRO_B`: `#CC79A7` (Púrpura Sóbrio);
  - `QUARENTENA_CIB_SPAM`: `#DC2626` (Alerta Crítico) / `#D97706` (Aviso Moderado).

## 2. Tipografia de Precisão e Regra Compulsória `tabular-nums`
- **Pareamento Tipográfico:** `Inter` ou `Geist Sans` para navegação e texto analítico; `JetBrains Mono` ou `Geist Mono` para hashes `HMAC-SHA256`, fórmulas, intervalos de confiança (`IC 95%`) e estatísticas.
- **Invariante Numérico:** Todo dígito, percentual, totalizador ($N_{\text{org}}$) ou valor monetário deve obrigatoriamente conter a propriedade `font-variant-numeric: tabular-nums` (classe Tailwind `tabular-nums`), eliminando o desalinhamento horizontal em atualizações reativas.

## 3. Ergonomia Data-Dense e Protocolo Anti-"Cara de IA" (*Anti-AI-Slop*)
- **Densidade Informacional (Tufte):** Grid espacial de 4px/8px, *Data-Ink Ratio* $\ge 0.80$, cabeçalhos compactos (`h-12` / 48px), gavetas laterais de inspeção (*Slide-over Drawers*) e barras de comando (`Cmd+K`).
- **Lista Negra de IA Genérica (Bloqueio Mandatório):** Proibição estrita de gradientes neon roxo/índigo/rosa (`from-indigo-500 to-purple-600`), sombras coloridas neon (`shadow-indigo-500/50`), cantos excessivamente arredondados em cards (`rounded-3xl`, `rounded-full`) e emojis em títulos, botões e cabeçalhos. Empregar exclusivamente ícones vetoriais monocromáticos **Lucide React** (`w-4 h-4`, `strokeWidth={1.75}`).

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Aplicar `tabular-nums` em tabelas e KPIs; garantir contraste WCAG 2.2 $\ge 4.5:1$ para texto e $\ge 3.0:1$ para componentes; usar paleta Okabe-Ito; usar ícones Lucide React com `aria-hidden="true"`.
- **MUST NOT DO:** Não usar gradientes neon clichês de IA; não colocar emojis em headers operacionais; não usar cantos `rounded-3xl` em cards analíticos; não usar cores arbitrárias para polarização fora da escala Okabe-Ito.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para implementação de componentes React, Radix UI e estado via Nuqs: use `fe-react-tailwind-radix-architecture`.
- Para gráficos interativos ECharts, TanStack Table virtualizada e `@media print`: use `fe-data-viz-grids-maps-and-export`.
- Para auditoria visual determinística dos 4 Portões e testes de contraste: use `qa-visual-a11y-and-frontend-validator`.
- Para normas acadêmicas de publicação e boletins Word `.docx`: use `academic-tcc-datasenado`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute o linter de design tokens e detector de AI-Slop:
  ```bash
  ./skills/ui-ux-design-system-and-anti-ai-craft/scripts/anti_ai_slop_and_design_token_linter.py --demo
  ```
- **Manuais Técnicos:**
  - [institutional_design_tokens_and_anti_ai_slop.md](./references/institutional_design_tokens_and_anti_ai_slop.md)
  - [data_dense_ux_ergonomics_and_wcag22.md](./references/data_dense_ux_ergonomics_and_wcag22.md)
