# Métodos Mistos (Bardin + NLP) e Padrão de Visualização Científica Internacional

Este guia padroniza a integração quali-quanti em estudos do debate legislativo e estabelece os requisitos gráficos para submissão a periódicos internacionais de alto impacto (*Elsevier, Springer, Nature, IEEE*).

---

## 1. Triangulação de Métodos Mistos (Creswell & Creswell, 2018; Bardin, 2011)

A inferência sobre o debate digital combina o rigor da inferência estatística de probabilidade conhecida com a profundidade interpretativa da análise de conteúdo:

```
[Corpus de Posts Coletados]
           │
           ├─────────────────────────────────────────┐
           ▼ (Vertente Quantitativa)                 ▼ (Vertente Qualitativa - Bardin)
    Quadro Limpo U_Org                       Pré-Análise e Leitura Flutuante
           │                                         │
    Sorteio Estratificado (Hamilton)         Exploração e Codificação Categorial
           │                                 (Eixos temáticos favoráveis e contrários)
    Estimadores C1, C2, C3                   Extração de Trechos Paradigmáticos Parafraseados
           │                                         │
           └───────────────────┬─────────────────────┘
                               ▼
        Triangulação Analítica: Validação de Frames e Posicionamentos
```

### 1.1. As Três Fases da Análise de Conteúdo (Bardin, 2011)
1. **Pré-análise:** Seleção e leitura exploratória dos textos amostrados; formulação de hipóteses de enquadramento temático (*framing*) sobre o projeto de lei.
2. **Exploração do Material e Codificação:**
   - Unidades de Registro: Palavras-chave temáticas, argumentos centrais e expressões valorativas.
   - Categorização Temática: Estruturação dos marcadores de stance (`favorable_markers` e `against_markers`) alimentando a taxonomia do `config/settings.yaml`.
3. **Tratamento dos Resultados, Inferência e Interpretação:** Confronto das categorias temáticas com a distribuição estatística das contas, avaliando quais argumentos predominam nas diferentes plataformas e estratos temporais.

---

## 2. Padrão Editorial de Visualização Científica (Elsevier / Springer / IEEE)

### 2.1. Acessibilidade Cromática Obrigatória (Colorblind-Safe)
Gráficos e mapas devem utilizar paletas perceptualmente uniformes e acessíveis a daltônicos (deuteranopia, protanopia, tritanopia). Adota-se a paleta **Okabe & Ito (2008)**:

| Categoria Semântica | Cor Hexadecimal | Nome da Cor | Uso Específico no Sistema |
| :--- | :---: | :--- | :--- |
| **Favorável** | `#0072B2` | Azul Seguro | Proporção e IC de apoio à matéria |
| **Contrário** | `#D55E00` | Vermelho-Ocre | Proporção e IC de oposição |
| **Neutro / Indeterminado** | `#999999` | Cinza Médio | Manifestações informativas/neutras |
| **Indício CIB / Automação** | `#CC79A7` | Roxo Claro | Clusters e anomalias de coordenação |
| **Mobilização Cívica** | `#009E73` | Verde Azulado | Campanhas legítimas e participativas |

*Paletas contínuas alternativas:* `viridis` ou `cividis` (nunca utilizar escala `jet` ou arco-íris).

### 2.2. Representação Obrigatória de Incerteza Amostral
- **Proibição de Estimativas Pontuais Isoladas:** É expressamente vedado apresentar gráficos de barras simples contendo apenas médias ou proporções pontuais sem a representação visual da incerteza.
- **Gráficos Recomendados:**
  - *Cleveland Dot Plots* ou *Forest Plots:* Comparação dos 3 cenários (C1, C2, C3) lado a lado, com marcadores pontuais e barras de erro horizontais correspondentes ao IC 95% Bootstrap.
  - *Ridge Plots* ou *Violin Plots:* Para ilustrar a dispersão empírica das réplicas do bootstrap.

### 2.3. Proibições Gráficas Absolutas (*Chartjunk*, Tufte, 2001)
- ❌ **Gráficos de Pizza ou Rosca (*Pie / Donut Charts*):** Humanos têm baixa acuidade para comparar áreas angulares; substituir por gráficos de pontos ou barras ordenadas.
- ❌ **Efeitos Tridimensionais (3D):** Proibido qualquer gráfico com perspectiva 3D, sombras artificiais ou chanfros.
- ❌ **Eixos Duplos Enganosos (*Dual-Axis*):** Proibido combinar escalas de ordens de grandeza distintas no mesmo gráfico para sugerir correlação espúria.
- ❌ **Grades e Fundos Saturados:** Adotar fundo branco puro (`#FFFFFF`) e linhas de grade discretas em cinza muito claro (`#E5E5E5`).

### 2.4. Especificação Técnica para Exportação de Figuras
1. **Formatos Vetoriais Primários:** `PDF` (com fontes embutidas) ou `SVG` para diagramas e gráficos de linha/pontos.
2. **Formatos Raster:** `PNG` ou `TIFF` com resolução mínima estrita de **300 DPI** (600 DPI para figuras com linhas finas).
3. **Tipografia:** Fonte sem serifa padronizada (`Arial`, `Helvetica` ou `DejaVu Sans`), tamanho 8–10 pt nos eixos e legendas, garantindo legibilidade em redução para coluna única de periódico (85 mm de largura).
4. **Legenda Autoexplicativa:** Toda figura deve conter legenda inferior detalhada descrevendo a amostra ($n$), o tamanho efetivo ($n_{\text{eff}}$), as plataformas analisadas e o método de cálculo do intervalo de confiança.
