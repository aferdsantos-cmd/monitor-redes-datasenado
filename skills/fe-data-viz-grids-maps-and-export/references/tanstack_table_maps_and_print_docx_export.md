# Tabelas Virtualizadas com TanStack Table, Mapas Coropléticos IBGE e Exportação `@media print` / Word

Este manual técnico aborda a arquitetura de tabelas de alta densidade virtualizadas, a integração de mapas geográficos das 27 UFs do Brasil e o pipeline de exportação documental multipadrão (`@media print` CSS, PDF e Microsoft Word `.docx` editável) conforme as decisões ADR-009 e ADR-012.

---

## 1. Tabelas de Dados com TanStack Table e Salvaguardas LGPD

O volume de postagens e contas orgânicas auditadas exige virtualização de linhas para garantir taxa estável de 60 quadros por segundo em monitores de alta frequência.

### 1.1 Configuração Virtualizada
- **Headless:** TanStack Table gerencia estado, paginação, fixação de colunas (*column pinning*) e ordenação multi-coluna, enquanto a estilização é controlada via Tailwind com classe compulsória `tabular-nums`.
- **Virtualização:** `@tanstack/react-virtual` renderiza apenas as ~25 linhas visíveis no viewport da tabela, reciclando nós do DOM.

### 1.2 Regras Mandatórias de Privacidade LGPD na Tela
1. **Truncamento de Hash:** Identificadores pseudonimizados de contas (`author_id_hash`) jamais são exibidos em formato completo de 64 caracteres hexadecimais. A UI deve truncá-los visualmente para os primeiros 10 caracteres (`hash.slice(0, 10) + "..."`).
2. **Máscara de $k$-Anonimato ($k \ge 5$):** Qualquer agregação de tabela ou cruzamento demográfico que apresente menos de 5 contas únicas deve ter seu rótulo colapsado em `"OUTROS_ANONIMIZADO_LGPD_K5"`, impossibilitando a reidentificação de cidadãos em cidades ou estratos pequenos.

---

## 2. Mapas Coropléticos das 27 UFs e 5 Macrorregiões do IBGE

A distribuição regional do debate é um dos eixos primordiais do DataSenado. A interface deve fornecer um mapa vetorial coroplético interativo do território nacional:

### 2.1 Especificação Cartográfica
- **27 Unidades Federativas:** `AC`, `AL`, `AP`, `AM`, `BA`, `CE`, `DF`, `ES`, `GO`, `MA`, `MT`, `MS`, `MG`, `PA`, `PB`, `PR`, `PE`, `PI`, `RJ`, `RN`, `RS`, `RO`, `RR`, `SC`, `SP`, `SE`, `TO`.
- **5 Macrorregiões IBGE:** `Norte`, `Nordeste`, `Sudeste`, `Sul`, `Centro-Oeste`.
- **Camadas Analíticas:**
  - *Volume de Contas Observadas ($N_{\text{org}}$);*
  - *Distribuição Inferida via DDD de WhatsApp e Geolocalização de YouTube;*
  - *Tabela de Convergência de Raking IPF:* Exibe o alvo populacional IBGE (Censo 2022) contrastado com a proporção da amostra antes e depois da calibração no simplex.

---

## 3. Emissão de Relatórios com `@media print` CSS e Word `.docx` (ADR-009)

O consultor do Senado frequentemente precisa imprimir o relatório executivo da bancada ou anexá-lo em pareceres legislativos.

### 3.1 Folha de Estilo `@media print` Dedicada
```css
@media print {
  @page {
    size: A4 portrait;
    margin: 15mm 15mm 20mm 15mm;
  }
  
  /* Oculta barras operacionais, menus de navegação e filtros */
  .no-print, [data-no-print], header, nav, .toolbar-root {
    display: none !important;
  }

  /* Impede quebras de página desastradas no meio de gráficos ou tabelas */
  .card-analytics, table, .echarts-container {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }

  /* Força renderização de cores e fundos contrastantes */
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
  }
}
```

### 3.2 Ponte com o Boletim em Microsoft Word (`.docx` — ADR-009)
Além da impressão direta pelo navegador e da geração de PDF com `html2canvas / jspdf`, a bancada disponibiliza um botão de comando rápido que aciona o gerador oficial de documentos Word do DataSenado (`src/reporting/`), exportando tabelas e pareceres técnicos prontos para edição em Word pelas comissões do Senado.
