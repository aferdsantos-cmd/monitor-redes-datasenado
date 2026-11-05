# Gráficos Analíticos com Apache ECharts e Visx, Incerteza IC 95% e Bolhas ADR-010

Este manual técnico aborda a configuração avançada do Apache ECharts e Visx para visualizações estatísticas rigorosas no Monitor de Redes DataSenado, incluindo representação de intervalos de confiança, grafos de força para câmaras de eco e séries temporais de agenda com detecção de quebra estrutural.

---

## 1. Configuração do Apache ECharts e Transições Fluidas

O Apache ECharts oferece aceleração via Canvas e WebGL, permitindo renderização estável a 60 FPS com dezenas de milhares de pontos. Para evitar piscamentos de tela (*flash of unstyled content*) ao receber dados atualizados do `TanStack Query`:

```ts
export const BASE_ECHARTS_OPTIONS: echarts.EChartsOption = {
  animationDuration: 400,
  animationEasing: "cubicOut",
  // Habilita transição universal suave entre estados
  universalTransition: {
    enabled: true,
    divideShape: "clone",
  },
  textStyle: {
    fontFamily: "Inter, Geist Sans, sans-serif",
  },
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(15, 23, 42, 0.95)",
    borderColor: "#334155",
    textStyle: { color: "#F8FAFC", fontSize: 12 },
  },
};
```

---

## 2. Gráfico Nuclear 1: Os 3 Cenários Estatísticos + Rogan-Gladen com Bandas IC 95%

A estimativa de proporção de posicionamento público (`Favorável`, `Contrário`, `Neutro`) nunca deve ser reportada como um número pontual isolado. O gráfico combina barras com bandas de erro geradas por renderizador customizado:

```ts
export function buildStanceComparisonOption(data: StanceComparisonData): echarts.EChartsOption {
  return {
    ...BASE_ECHARTS_OPTIONS,
    color: ["#0072B2", "#D55E00", "#64748B"], // Paleta Okabe-Ito
    legend: { data: ["Favorável", "Contrário", "Neutro"], bottom: 0 },
    xAxis: {
      type: "category",
      data: [
        "Cenário 1: Hájek + Rogan-Gladen",
        "Cenário 2: Inverso 1/K",
        "Cenário 3: Raking IPF Simplex",
      ],
    },
    yAxis: {
      type: "value",
      axisLabel: { formatter: "{value}%" },
      max: 100,
    },
    series: [
      {
        name: "Favorável",
        type: "bar",
        data: data.favoravel_estimates,
      },
      {
        name: "IC 95%",
        type: "custom",
        renderItem: renderErrorBarItem, // Desenha os bigodes do IC 95%
        data: data.favoravel_confidence_intervals,
        z: 3,
      },
      // ... Séries correspondentes para Contrário e Neutro
    ],
  };
}
```

---

## 3. Gráfico Nuclear 2: Topologia de Bolhas Digitais e Espectros (ADR-010)

Visualiza a segregação discursiva de contas orgânicas ($\mathcal{U}_{\text{Org}}$) através de um grafo de força:
- **Nós:** Contas orgânicas, coloridas pelo espectro político propagado via expoentes-semente (Progressista `#009E73`, Conservador `#D55E00`, Centro `#0072B2`, Técnico `#CC79A7`);
- **Tamanho do Nó:** Proporcional ao grau ponderado ou engajamento orgânico;
- **Arestas:** Relações de co-engajamento, menções mútuas ou compartilhamento de links;
- **Métricas Anotadas:** Modularidade $Q$, Índice $E\text{-}I$ de Krackhardt & Stern e destaque visual para os **Nós-Ponte** (com Coeficiente de Participação $P_i > 0.40$).

---

## 4. Gráfico Nuclear 3: Séries Temporais de Agenda e Causalidade de Granger (ADR-008)

- **Linhas Suavizadas:** Volume horário/diário de menções por espectro;
- **Componente `dataZoom`:** Slider horizontal compacto no rodapé permitindo zoom milimétrico em períodos de votação parlamentar;
- **Marcadores de Quebra Estrutural (CUSUM):** Linhas verticais pontilhadas vermelhas (`markLine`) indicando choques legislativos onde a variância ou média sofreu descontinuidade estatística significante ($p < 0.01$).
- **Anotação de First-Mover:** Seta direcional destacando qual espectro ou plataforma antecipou a curva de debate conforme comprovado pelo Teste F de Granger.

---

## 5. Proibições Rígidas em Visualização de Dados
1. **Gráficos de Pizza/Rosca:** Proibidos para mais de 3 categorias. O olho humano tem dificuldade em comparar ângulos e áreas;
2. **Gráficos Tridimensionais (3D):** Proibidos compulsoriamente (perspectiva distorce a proporcionalidade dos dados);
3. **Ausência de Erro Amostral:** Proibido plotar gráficos de estimativa de opinião sem barras de erro de IC 95%.
