# Propagação Harmônica de Espectros via Sementes e Causalidade de Agenda

Este manual técnico estabelece a formulação da propagação semi-supervisionada de afinidade a espectros políticos a partir de expoentes institucionais (ADR-010) e a metodologia econométrica de séries temporais para detecção de pioneirismo discursivo (ADR-008) no Monitor de Redes DataSenado.

---

## 1. Modelagem Semi-Supervisionada de Espectros via Expoentes-Semente (ADR-010)

Classificar nominalmente a inclinação política de milhares de cidadãos é epistêmica e eticamente problemático. Para superar essa limitação sem incorrer em rotulagem arbitrária ou desrespeito à LGPD:
1. Define-se um conjunto auditável de **Expoentes-Semente Públicos** $\mathcal{S}$ com posicionamento notório e documentado (senadores, deputados relatores, bancadas partidárias registradas e veículos temáticos).
2. Propaga-se a probabilidade contínua de afinidade com os espectros $K \in \{\text{Progressista}, \text{Conservador}, \text{Centro/Institucional}, \text{Técnico/Setorial}\}$ através da estrutura relacional do grafo orgânico.

### 1.1 Algoritmo de Difusão Harmônica (Zhou et al., 2004)
Seja $\mathbf{W}$ a matriz de pesos de co-engajamento entre contas, $\mathbf{D}$ a matriz diagonal de graus ($D_{ii} = \sum_j W_{ij}$), e $\mathbf{S} = \mathbf{D}^{-1/2}\mathbf{W}\mathbf{D}^{-1/2}$ o operador Laplaciano normalizado simétrico.

A matriz de rótulos iniciais $\mathbf{Y} \in \mathbb{R}^{N \times K}$ possui $Y_{ik} = 1$ se o nó $i \in \mathcal{S}$ é semente do espectro $k$, e $Y_{ik} = 0$ caso contrário. A matriz de afinidade $\mathbf{F} \in \mathbb{R}^{N \times K}$ converge iterativamente sob a regra de atualização:

$$\mathbf{F}^{(t+1)} = \alpha \mathbf{S} \mathbf{F}^{(t)} + (1 - \alpha) \mathbf{Y}$$

onde $\alpha \in (0, 1)$ pondera a retenção dos rótulos-semente em relação à difusão relacional (típico $\alpha = 0.85$). Como $\rho(\mathbf{S}) \le 1$, a solução analítica de ponto fixo é garantida:
$$\mathbf{F}^* = (1 - \alpha)(\mathbf{I} - \alpha \mathbf{S})^{-1} \mathbf{Y}$$

Após a convergência, cada linha $i$ é normalizada no simplex ($\sum_k F_{ik}^* = 1$), representando a distribuição de proximidade topológica aos expoentes do debate.

---

## 2. Estatística de Séries Temporais e Dinâmica de Agenda (ADR-008)

O Monitor de Redes DataSenado investiga como temas legislativos emergem, ganham tração e se propagam entre diferentes comunidades e espectros digitais.

### 2.1 Lead-Lag Cross-Correlation
Dadas duas séries temporais discretizadas em janelas horárias de menções a um projeto de lei por dois espectros $A$ e $B$ ($X_t$ e $Y_t$), a função de correlação cruzada com defasagem $\tau \in [-L, +L]$ é:

$$r_{XY}(\tau) = \frac{\sum_{t} (X_t - \bar{X})(Y_{t+\tau} - \bar{Y})}{\sqrt{\sum (X_t - \bar{X})^2 \sum (Y_t - \bar{Y})^2}}$$

Se o pico máximo $\arg\max_\tau |r_{XY}(\tau)|$ ocorrer em $\tau^* > 0$, há forte evidência descritiva de que a atividade da série $X$ antecede sistematicamente a série $Y$ por $\tau^*$ horas.

### 2.2 Teste F de Causalidade de Granger Bivariada
Para comprovar se a série antecedente $X$ contém informação incremental estatisticamente significante para prever $Y$ além do próprio histórico de $Y$:
1. Ajusta-se o modelo autorregressivo restrito:
   $$Y_t = c_0 + \sum_{p=1}^P \beta_p Y_{t-p} + \epsilon_t$$
2. Ajusta-se o modelo irrestrito incluindo as defasagens de $X$:
   $$Y_t = c_0 + \sum_{p=1}^P \beta_p Y_{t-p} + \sum_{p=1}^P \gamma_p X_{t-p} + u_t$$
3. Avalia-se a hipótese nula $H_0: \gamma_1 = \dots = \gamma_P = 0$ via estatística $F$:
   $$F = \frac{(\text{SSR}_{\text{restrito}} - \text{SSR}_{\text{irrestrito}}) / P}{\text{SSR}_{\text{irrestrito}} / (T - 2P - 1)}$$
Se $p < 0.05$ (com teste de estacionariedade Augmented Dickey-Fuller prévio), confirma-se estatisticamente o papel de **First-Mover Spectrum** da comunidade $X$ sobre a comunidade $Y$.
