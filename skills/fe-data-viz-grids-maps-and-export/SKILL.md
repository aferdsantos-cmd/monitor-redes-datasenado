---
name: fe-data-viz-grids-maps-and-export
description: Use this skill whenever implementing interactive charts (Apache ECharts, Recharts, Visx), virtualized data grids (TanStack Table, AG Grid), Brazilian UF/IBGE geographic choropleth maps (Visx SVG, Mapbox GL, Leaflet), or multi-format report exports (@media print CSS, html2canvas/jspdf PDF, and ADR-009 Microsoft Word .docx integration).
---

# Visualização Analítica Data-Dense, Grids Virtualizados, Mapas e Exportação

Padrões de engenharia visual de alta densidade informacional (Tufte $\ge 0.80$) para o Monitor de Redes DataSenado, integrando gráficos acelerados por Canvas/SVG (Apache ECharts), tabelas virtualizadas com salvaguardas da LGPD (TanStack Table), mapas coropléticos das 27 UFs/IBGE e exportação documental com fidelidade tipográfica (`@media print` CSS, PDF e Word `.docx` editável).

## 1. Gráficos Estatísticos Acelerados (Apache ECharts / Visx)
- **Transições Fluidas:** Utilização de `universalTransition: true` no ECharts para transições de layout sem recarregamento ou piscamento de tela após mudanças de filtro.
- **Os 4 Gráficos Nucleares do DataSenado:**
  1. *Painel dos 3 Cenários (C1 Hájek, C2 1/K, C3 Raking) + Rogan-Gladen:* Barras com bandas de erro de **Intervalo de Confiança de 95% (`IC 95%`)** e paleta Okabe-Ito.
  2. *Topologia de Bolhas Digitais e Câmaras de Eco (`ADR-010`):* Grafo de força com modularidade $Q$, índice $E\text{-}I$, nós-ponte $P_i$ e diagrama *First-Mover*.
  3. *Séries Temporais com Quebra Estrutural (CUSUM) e Granger (`ADR-008`):* Zoom interativo (`dataZoom`).
  4. *Quarentena de Descontaminação Silver e Explicabilidade SHAP:* Decomposição de atributos.
- **Proibição Estrita:** Proibido gráficos de pizza/rosca com mais de 3 fatias, gráficos 3D (`bar3D`) e gráficos sem declaração explícita de incerteza estatística (`IC 95%`).

## 2. Tabelas Virtualizadas e Blindagem LGPD (TanStack Table)
- **Virtualização Headless:** Suporte a 50.000+ linhas a 60 FPS com `@tanstack/react-virtual`, fixação de colunas (*column pinning*), ordenação e paginação local.
- **Salvaguardas LGPD na Interface:** Truncamento de hashes `HMAC-SHA256` para 10 caracteres (ex.: `a1b2c3d4e5...`) e colapso automático de células com $k < 5$ contas em `"OUTROS_ANONIMIZADO_LGPD_K5"`.

## 3. Mapas Geográficos das 27 UFs e 5 Macrorregiões IBGE
- **Distribuição Territorial:** Mapa coroplético vetorial das 27 UFs (`AC` a `TO` + `DF`) e 5 Macrorregiões (`Norte`, `Nordeste`, `Sudeste`, `Sul`, `Centro-Oeste`) com dados de DDD e convergência de Raking IPF.

## 4. Fidelidade de Impressão e Relatórios Oficiais (`ADR-009`)
- **Folha de Estilo `@media print`:** Ocultação de menus e barras operacionais (`print:hidden`), quebras de página controladas (`break-inside: avoid`) e ajuste para formato A4.
- **Ponte Tripla de Exportação:** Geração de PDF via `html2canvas/jspdf`, dados brutos em Parquet `ZSTD` e disparo do **Relatório Oficial Editável em Word (`.docx`) do DataSenado (`ADR-009`)**.

## 5. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Incluir bandas de erro IC 95% em gráficos de prevalência; usar paleta Okabe-Ito; aplicar tabular-nums e $k \ge 5$ em tabelas; usar `@media print` para PDF.
- **MUST NOT DO:** Não usar gráficos de pizza com mais de 3 categorias; não usar gráficos 3D; não omitir tamanho amostral $n$; não quebrar gráficos na impressão.

## 6. Matriz de Roteamento e Fronteiras de Competência
- Para Design System, tokens de cor e tipografia: use `ui-ux-design-system-and-anti-ai-craft`.
- Para contratos Zod, estado de URL com Nuqs e Radix: use `fe-react-tailwind-radix-architecture`.
- Para validação dos 4 Portões Visuais e auditoria WCAG: use `qa-visual-a11y-and-frontend-validator`.
- Para template acadêmico IMRaD e normas ABNT: use `academic-tcc-datasenado`.

## 7. Sonda Executável e Referências Aprofundadas
- Execute o validador de ECharts, TanStack Table e impressão:
  ```bash
  ./skills/fe-data-viz-grids-maps-and-export/scripts/dataviz_echarts_grid_and_print_validator.py --demo
  ```
- **Manuais Técnicos:**
  - [echarts_visx_statistical_charts_and_bubbles.md](./references/echarts_visx_statistical_charts_and_bubbles.md)
  - [tanstack_table_maps_and_print_docx_export.md](./references/tanstack_table_maps_and_print_docx_export.md)
