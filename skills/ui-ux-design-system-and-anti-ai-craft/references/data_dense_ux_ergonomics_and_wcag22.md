# Ergonomia de Interfaces Data-Dense e Acessibilidade WCAG 2.2 AA/AAA

Este manual técnico aborda a fundamentação ergonômica de layouts de alta densidade informacional baseados na filosofia de Edward Tufte, a arquitetura espacial estilo Linear/Bloomberg/Tableau e a formulação matemática de contraste segundo a recomendação internacional W3C WCAG 2.2.

---

## 1. Princípios de Densidade de Dados (Edward Tufte)

Em interfaces voltadas para tomada de decisão legislativa de alta relevância, o espaço da tela deve priorizar a informação substantiva em vez de decorações vazias ou espaçamentos inflados que forçam rolagens desnecessárias.

### 1.1 Data-Ink Ratio
O conceito de razão dado-tinta (*Data-Ink Ratio*) postula que a proporção de pixels dedicados à apresentação direta de dados deve ser maximizada:
$$\text{Data-Ink Ratio} = \frac{\text{Tinta / Pixels dedicados aos dados}}{\text{Tinta / Pixels totais da visualização}} \ge 0.80$$
- **Eliminação de Gráficos Amadores:** Remover linhas de grade excessivas, fundos escuros desnecessários em gráficos claros, bordas grossas decorativas e elementos 3D.
- **Grades Espaciais de 4px / 8px:** Todo componente, preenchimento (*padding*) e margem deve alinhar-se à grade de múltiplos de 4px (`p-2`, `p-3`, `gap-2`, `gap-4`).
- **Cabeçalhos Compactos:** A barra superior de navegação deve ter altura fixa máxima de `48px` (`h-12`), liberando o plano vertical para os gráficos e matrizes estatísticas.

---

## 2. Padrões de Navegação e Ergonomia Operacional

Em vez de distribuir análises complexas em dezenas de páginas dispersas com cards gigantes:
1. **Barras de Ferramentas Funcionais (`Toolbar`):** Concentração de todos os controles de amostragem, seleção de tema e filtros cronológicos em uma barra compacta e persistente.
2. **Gavetas Laterais de Inspeção (*Slide-over Drawers*):** Ao clicar em um ponto do gráfico, um nó da bolha de polarização ou uma linha da tabela, uma gaveta lateral deslizante é aberta sem desmontar a visão analítica global.
3. **Menu de Comandos Rápido (`Cmd+K` / `Ctrl+K`):** Acesso instantâneo a qualquer tema, filtro ou exportação de relatório por busca semântica no teclado.

---

## 3. Matemática de Contraste e Acessibilidade WCAG 2.2

A norma W3C Web Content Accessibility Guidelines (WCAG) 2.2 estabelece critérios objetivos e verificáveis matematicamente para legibilidade e inclusão.

### 3.1 Luminância Relativa ($L$)
A luminância relativa de uma cor RGB no espaço sRGB é calculada linearizando os canais normalizados $c \in \{R/255, G/255, B/255\}$:

$$c_{\text{lin}} = \begin{cases} \frac{c}{12.92}, & \text{se } c \le 0.04045 \\ \left(\frac{c + 0.055}{1.055}\right)^{2.4}, & \text{se } c > 0.04045 \end{cases}$$

A luminância combinada pondera a sensibilidade do olho humano:
$$L = 0.2126 R_{\text{lin}} + 0.7152 G_{\text{lin}} + 0.0722 B_{\text{lin}} \in [0.0, 1.0]$$

### 3.2 Razão de Contraste ($\text{CR}$)
Dadas duas cores com luminâncias $L_1$ e $L_2$ (onde $L_{\max} = \max(L_1, L_2)$ e $L_{\min} = \min(L_1, L_2)$):

$$\text{CR} = \frac{L_{\max} + 0.05}{L_{\min} + 0.05} \in [1.0, 21.0]$$

### 3.3 Critérios de Conformidade Mandatórios
- **WCAG 2.2 Nível AA (Texto Normal $\le 18\text{pt}$):** $\text{CR} \ge 4.5:1$;
- **WCAG 2.2 Nível AA (Texto Grande $\ge 18\text{pt}$ ou Bold $\ge 14\text{pt}$):** $\text{CR} \ge 3.0:1$;
- **WCAG 2.2 Nível AA (Componentes de Interface e Gráficos):** $\text{CR} \ge 3.0:1$ entre a cor do elemento e as cores adjacentes;
- **WCAG 2.2 Nível AAA:** $\text{CR} \ge 7.0:1$ para texto normal.

---

## 4. Alvos de Toque e Navegação por Teclado
- **Área Mínima de Toque (WCAG 2.2 Critério 2.5.8):** Todo botão, aba e controle interativo deve ter dimensão mínima de $24 \times 24$ pixels com espaçamento adequado ou $40 \times 40$ pixels em alvos primários.
- **Anel de Foco Visível (Critério 2.4.13):** Proibido remover foco com `outline: none` sem fornecer substituto acessível. Empregar `focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2`.
