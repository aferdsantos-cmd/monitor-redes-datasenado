---
name: stats-network-bubbles-and-time-series
description: Use this skill whenever analyzing digital bubbles, echo chambers, political/discursive spectrum propagation from seed exponents (ADR-010), graph community modularity, cross-bubble bridge nodes, or agenda-setting time-series dynamics and Granger causality across social media platforms (ADR-008).
---

# Topologia Estatística de Bolhas Digitais, Espectros e Séries Temporais

Sub-skill estatística avançada ancorada nas decisões arquiteturais ADR-008 e ADR-010 do Monitor de Redes DataSenado, dedicada à modelagem topológica de câmaras de eco, propagação harmônica de espectros políticos via sementes e causalidade temporal de agenda.

## 1. Fronteira Conceitual com `stats-inference-datasenado`
- **Camada Silver vs Universo Orgânico:** Enquanto `stats-inference-datasenado` utiliza grafos de co-ocorrência na Camada Silver para detectar e expurgar comportamentos inautênticos coordenados (CIB), esta skill atua **exclusivamente sobre o Universo Orgânico Limpo ($\mathcal{U}_{\text{Org}}$)** para quantificar a estrutura do debate político e identificar bolhas digitais.

## 2. Topologia de Bolhas Digitais e Câmaras de Eco (ADR-010)
- **Modularidade de Newman ($Q$):** Avaliação de partições comunitárias com teste de hipótese contra modelo nulo de configuração (permutação com conservação da sequência de graus), computando o $z$-score e $p$-valor de $Q$.
- **Índice de Homofilia $E\text{-}I$ de Krackhardt & Stern (1988):**
  $$\text{EI}_c = \frac{E_c - I_c}{E_c + I_c} \in [-1, +1]$$
  onde $\text{EI}_c < -0.40$ caracteriza uma **Câmara de Eco fechada** e $\text{EI}_c \ge 0$ caracteriza debate transversal e aberto.
- **Coeficiente de Participação de Pontes de Guimerà & Amaral:** $P_i = 1 - \sum (k_{is}/k_i)^2$ para identificar nós que conectam bolhas opostas.

## 3. Propagação Harmônica de Espectros via Expoentes-Semente (ADR-010)
- **Sementes Parlamentares e Institucionais Públicas ($\mathcal{S}$):** Difusão semi-supervisionada sobre o Laplaciano normalizado ($\mathbf{S} = \mathbf{D}^{-1/2}\mathbf{W}\mathbf{D}^{-1/2}$) com garantia de convergência:
  $$\mathbf{F}^{(t+1)} = \alpha \mathbf{S} \mathbf{F}^{(t)} + (1 - \alpha) \mathbf{Y}$$
- **Salvaguarda LGPD:** Cálculos individuais ocorrem apenas em memória efêmera sobre hashes pseudonimizados. Os relatórios expõem exclusivamente métricas agregadas por espectro.

## 4. Séries Temporais e Causalidade de Agenda (ADR-008)
- **First-Mover Spectrum:** Correlação cruzada defasada (*lead-lag*) e Teste F de Causalidade de Granger bivariada entre espectros para identificar quem pautou a narrativa primeiro.
- **Detecção de Mudança Estrutural:** Algoritmo CUSUM sobre volumes horários para o Radar Diário do Senado.

## 5. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Testar modularidade contra modelo nulo; calcular Índice E-I para classificar câmaras de eco; proteger a LGPD com dados agregados; verificar estacionariedade em Granger.
- **MUST NOT DO:** Não rotular bolhas sem testar significância estatística de Q; não atribuir viés político nominal a cidadãos individuais; não usar Granger em séries não-estacionárias.

## 6. Matriz de Roteamento e Fronteiras de Competência
- Para desenho amostral de população finita e Raking IPF: use `stats-inference-datasenado`.
- Para treinamento e calibração de classificadores: use `ds-ml-modeling-and-validation`.
- Para auditoria de equidade e valores SHAP: use `ds-xai-and-model-explainability`.

## 7. Sonda Executável e Referências Aprofundadas
- Execute a sonda de bolhas e espectros políticos:
  ```bash
  ./skills/stats-network-bubbles-and-time-series/scripts/bubble_topology_and_spectrum_probe.py --demo
  ```
- **Manuais Técnicos:**
  - [echo_chambers_modularity_and_ei_index.md](./references/echo_chambers_modularity_and_ei_index.md)
  - [seed_label_propagation_and_granger_agenda.md](./references/seed_label_propagation_and_granger_agenda.md)
