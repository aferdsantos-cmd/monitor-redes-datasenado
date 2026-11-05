# Inspeção Visual Ao Vivo com Chrome DevTools MCP e Core Web Vitals

Este manual técnico orienta a execução de inspeções visuais em tempo real utilizando as ferramentas do protocolo MCP (Model Context Protocol) do Chrome DevTools sobre a aplicação web da Bancada do DataSenado em execução.

---

## 1. Arquitetura de Inspeção Ao Vivo via Chrome DevTools MCP

Quando a interface do DataSenado estiver em execução em servidor de desenvolvimento local (`http://localhost:3000`), a IA Operadora pode interagir diretamente com a aba ativa do navegador através das ferramentas do plugin `chrome-devtools-plugin`.

### 1.1 Ferramentas e Competências das Skills Globais
- **`chrome-devtools`:** Captura de telas em alta fidelidade (`take_screenshot`), execução de código JavaScript no console do navegador (`evaluate_script`), inspeção de requisições de rede (`list_network_requests`) e navegação controlada;
- **`a11y-debugging`:** Captura e inspeção da árvore de acessibilidade WAI-ARIA (`take_snapshot`), verificação de alvos de clique e contraste;
- **`debug-optimize-lcp`:** Rastreamento de performance e métricas vitais (`performance_start_trace`, `performance_stop_trace`).

---

## 2. Protocolo de Inspeção de Performance (Core Web Vitals)

Para garantir experiência instantânea em estações de trabalho do Congresso Nacional:

### 2.1 Metas Oficiais de Performance
1. **Largest Contentful Paint (LCP):** $\text{LCP} < 2.5\text{ segundos}$ no carregamento da tela principal com gráficos e KPIs;
2. **Cumulative Layout Shift (CLS):** $\text{CLS} == 0.00$ em todas as interações e trocas de filtro de data/tema via Nuqs;
3. **Interaction to Next Paint (INP):** $\text{INP} < 200\text{ milissegundos}$ ao clicar em botões da Toolbar ou abas analíticas.

### 2.2 Script de Verificação de CLS no Console do Navegador
A IA Operadora pode injetar e executar o script abaixo via `evaluate_script`:
```javascript
() => {
  return new Promise((resolve) => {
    let clsValue = 0;
    const observer = new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
    });
    observer.observe({ type: 'layout-shift', buffered: true });
    setTimeout(() => {
      observer.disconnect();
      resolve({ cumulative_layout_shift: clsValue, is_zero: clsValue === 0 });
    }, 1500);
  });
}
```

---

## 3. Auditoria de Acessibilidade via Árvore A11y

Através de `take_snapshot` do `a11y-debugging`, inspeciona-se se:
- Todos os botões possuem nomes acessíveis computados (`accessible name`);
- Os gráficos ECharts possuem elemento `<div role="img" aria-label="...">` com descrição sumária do resultado estatístico;
- Modais e gavetas contêm `role="dialog"` e `aria-modal="true"`.

---

## 4. Captura de Evidências Visuais para Relatórios de Auditoria
- Utilizar `take_screenshot(format="png", fullPage=true)` para gerar evidências visuais das telas homologadas;
- Conforme as regras da política Zero-Footprint e do ambiente, as capturas temporárias são gravadas em `/tmp` ou no diretório de artefatos da conversa, nunca na árvore permanente do código-fonte.
