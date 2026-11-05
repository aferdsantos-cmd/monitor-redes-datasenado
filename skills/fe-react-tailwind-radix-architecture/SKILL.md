---
name: fe-react-tailwind-radix-architecture
description: Use this skill whenever architecting or coding frontend components in React/Next.js and TypeScript, styling with Tailwind CSS, building accessible primitives with Radix UI and React Aria, adding Framer Motion micro-interactions, validating forms with React Hook Form and Zod, managing async state with TanStack Query and Sonner, or syncing toolbar filters with URL state via Nuqs.
---

# Arquitetura Front-End Reativa: React 19, Tailwind, Radix UI, Zod & Nuqs

Diretrizes arquiteturais para engenharia de interface da Bancada Analítica do DataSenado, contemplando tipagem estrita TypeScript (`no-any`), primitivos de acessibilidade Radix UI / React Aria, animações orgânicas Framer Motion, sincronização de URL state com Nuqs e contratos de validação Zod sob a política Zero-Footprint.

## 1. Arquitetura Core e Tipagem Estrita (TypeScript + Tailwind)
- **Modularidade por Domínio:** Organização orientada a features analíticas (`features/radar-diario`, `features/monitoramento-tematico`, `features/bolhas-espectros`, `features/exportacao-360`).
- **TypeScript Estrito (`no-any`):** Proibição absoluta do tipo `any`. Todo payload, estado de filtro e resposta da API deve possuir interface tipada espelhada em esquemas Zod/Pydantic.
- **Estilização Utilitária:** Funções auxiliares determinísticas `cn()` baseadas em `clsx` e `tailwind-merge`.

## 2. Acessibilidade Nativa (WAI-ARIA) com Radix UI e React Aria
- **Primitivos Acessíveis:** Todos os modais (`Dialog`), menus (`DropdownMenu`), abas (`Tabs`), seletores (`Select`) e barras de ferramentas (`Toolbar`) devem utilizar **Radix UI** ou **React Aria**.
- **Proibição de `div onClick`:** É terminantemente proibido criar elementos clicáveis com `<div onClick={...}>` sem atributos `role`, `tabIndex`, suporte completo a teclado (`Enter`, `Space`, `ArrowKeys`, `Escape`) e foco visível.
- **Posicionamento Anti-Colisão:** Utilizar **Floating UI** para posicionamento adaptativo de tooltips e popovers estatísticos.

## 3. Microinterações Fluidas e Feedback Não-Bloqueante
- **Framer Motion:** Animações sutis com física de mola (`type: "spring", stiffness: 320, damping: 28`) e respeito obrigatório à preferência do usuário via `useReducedMotion()`.
- **Toasts Empilháveis (Sonner):** Proibição estrita de `window.alert()`, `window.confirm()` e `window.prompt()`. Todo feedback operacional deve utilizar notificações assíncronas elegantes via **Sonner**.

## 4. Fluxo Reativo Flawless: Toolbar $\to$ Nuqs $\to$ Zod $\to$ TanStack Query
- **URL State com Nuqs (`useQueryState`):** Todos os filtros da Barra Operacional (`theme_id`, `window_days`, `platforms`, `sample_n`, `scenario`) sincronizam diretamente na URL sem recarregar a página (`CLS = 0`).
- **Validação Instantânea com Zod:** Esquemas Zod validam parâmetros antes do despacho, impedindo queries espúrias ou datas inválidas.
- **Gestão Assíncrona com TanStack Query:** Cache inteligente, deduplicação de requisições e exibição compulsória de **Skeleton Screens geométricos** durante o carregamento.
- **Zero-Footprint no Navegador:** Proibido salvar textos de posts, hashes de cidadãos ou chaves de API em `localStorage`, `sessionStorage` ou `IndexedDB`.

## 5. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Sincronizar filtros na URL via Nuqs; usar Radix UI / React Aria para modais e abas; tipar com Zod; manter Skeletons com mesma altura dos gráficos.
- **MUST NOT DO:** Não usar `window.location.reload()`; não usar `: any`; não usar `window.alert()`; não persistir PII em `localStorage`; não usar spinners no centro da tela sem layout reservado.

## 6. Matriz de Roteamento e Fronteiras de Competência
- Para tokens institucionais, regras de tipografia e paleta Okabe-Ito: use `ui-ux-design-system-and-anti-ai-craft`.
- Para gráficos interativos ECharts, TanStack Table virtualizada e `@media print`: use `fe-data-viz-grids-maps-and-export`.
- Para certificação dos 4 Portões de Qualidade Visual e auditoria WCAG: use `qa-visual-a11y-and-frontend-validator`.
- Para orquestração backend Python/DuckDB e conformidade Zero-Footprint: use `eng-python-zero-footprint`.

## 7. Sonda Executável e Referências Aprofundadas
- Execute o validador de arquitetura front-end e contratos Zod:
  ```bash
  ./skills/fe-react-tailwind-radix-architecture/scripts/frontend_architecture_and_zod_contract_validator.py --demo
  ```
- **Manuais Técnicos:**
  - [radix_react_aria_tailwind_and_framer_motion.md](./references/radix_react_aria_tailwind_and_framer_motion.md)
  - [tanstack_query_nuqs_zod_and_zero_footprint_api.md](./references/tanstack_query_nuqs_zod_and_zero_footprint_api.md)
