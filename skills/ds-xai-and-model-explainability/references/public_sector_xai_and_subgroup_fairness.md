# Transparência Algorítmica no Setor Público e Equidade por Subgrupo

Este manual técnico orienta a conformidade do Monitor de Redes DataSenado com as diretrizes do Tribunal de Contas da União (TCU) e da literatura de equidade algorítmica (*algorithmic fairness*) aplicada à opinião pública.

---

## 1. Padrões de Transparência Algorítmica para o Setor Público (TCU / DataSenado)

No contexto do Poder Legislativo e da administração pública, o emprego de sistemas de Inteligência Artificial para aferição do sentimento popular sobre projetos de lei exige padrões reforçados de governança e prestação de contas (*accountability*):

1. **Explicabilidade por Desenho:** Nenhum índice ou gráfico apresentado a senadores e comissões parlamentares pode decorrer de caixas-pretas inescrutáveis.
2. **Registro de Racionalidade Decisória:** Para cada relatório executivo ou boletim temático, devem constar os 10 termos e atributos mais influentes no cômputo da polarização.
3. **Auditabilidade Independente:** Especialistas externos ou órgãos de controle devem poder reexecutar os cálculos sobre os dados pseudonimizados com sementes fixas e verificar as atribuições locais.

---

## 2. Métricas Formais de Equidade Algorítmica (*Fairness*)

Em pesquisas multi-plataforma e multi-regional, os classificadores automáticos não podem apresentar disparidades sistemáticas de acurácia contra determinados estratos sociais, regionais ou canais comunicacionais.

### 2.1 Critérios de Avaliação
- **Paridade Demográfica (Demographic Parity):** A taxa de predição positiva é idêntica entre grupos: $\mathbb{P}(\hat{Y}=1 | G=g) = \mathbb{P}(\hat{Y}=1 | G=g')$. Nota: nem sempre desejável se as prevalências reais de fato diferirem.
- **Igualdade de Oportunidades (Equal Opportunity / Equalized Odds):** A sensibilidade e a especificidade do classificador são uniformes entre os subgrupos:
  $$\mathbb{P}(\hat{Y}=1 | Y=1, G=g) = \mathbb{P}(\hat{Y}=1 | Y=1, G=g') \quad (\text{Igualdade de Sensibilidade})$$
  $$\mathbb{P}(\hat{Y}=0 | Y=0, G=g) = \mathbb{P}(\hat{Y}=0 | Y=0, G=g') \quad (\text{Igualdade de Especificidade})$$

---

## 3. Protocolo de Auditoria de Disparidade de Erro

Para auditar a estabilidade do classificador nas 6 plataformas (YouTube, Telegram, X, Meta, TikTok, WhatsApp) e nas 5 macrorregiões do país:

### 3.1 Procedimento de Teste
1. Na partição de validação humana cega ($n_{\text{val}} = 550$), estratificam-se as predições por subgrupo $g$.
2. Para cada subgrupo $g$, calculam-se a sensibilidade $\hat{\text{Se}}_g$ e a especificidade $\hat{\text{Sp}}_g$.
3. Calcula-se a amplitude máxima de disparidade:
   $$\Delta_{\text{Se}} = \max_g \hat{\text{Se}}_g - \min_g \hat{\text{Se}}_g, \quad \Delta_{\text{Sp}} = \max_g \hat{\text{Sp}}_g - \min_g \hat{\text{Sp}}_g$$

### 3.2 Critérios de Ação Corretiva
- **Se $\Delta_{\text{Se}} \le 0.08$ e $\Delta_{\text{Sp}} \le 0.08$:** O modelo é considerado equitativo entre subgrupos. Aplica-se a matriz de Rogan-Gladen global.
- **Se $\Delta_{\text{Se}} > 0.08$ ou $\Delta_{\text{Sp}} > 0.08$:** Disparidade substancial detectada (ex.: o classificador é menos sensível a gírias regionais do Norte/Nordeste ou mensagens curtas do TikTok). É **mandatório** particionar a matriz de calibração e aplicar o estimador de **Rogan-Gladen Estratificado por Subgrupo**:
  $$\hat{P}_g = \frac{\hat{P}^*_g + \hat{\text{Sp}}_g - 1}{\hat{\text{Se}}_g + \hat{\text{Sp}}_g - 1}$$
garantindo que o viés do classificador em uma plataforma específica não contamine a estimativa nacional consolidada.
