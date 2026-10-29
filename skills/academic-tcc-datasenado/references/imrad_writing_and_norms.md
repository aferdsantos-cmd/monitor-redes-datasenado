# Redação Científica de Alto Impacto: Arquitetura IMRaD, Normas de Citação e Estilo

Este guia estabelece as diretrizes para elaboração de manuscritos no padrão IMRaD (*Introduction, Methods, Results, and Discussion*), conformidade com as normas ABNT NBR 10520:2023 / NBR 6023:2018, estilo APA 7th e exportação BibTeX/LaTeX.

---

## 1. Estrutura Padrão Ouro IMRaD

### 1.1. Introdução (*Introduction*)
1. **Contexto Institucional e Relevância Social:** A importância da escuta social para subsidiar a atuação do Parlamento e do Instituto de Pesquisa DataSenado.
2. **Problema Científico (*The Problem*):** O risco do *Big Data Paradox* (Meng, 2018) e da amplificação inautêntica de redes coordenadas (CIB) em abordagens tradicionais de monitoramento.
3. **Lacuna da Literatura (*Research Gap*):** Ausência de pipelines que combinem desinfecção de redes coordenadas em grafos de Leiden com amostragem estratificada com pesos conhecidos e calibração por Raking sob restrição de cache efêmero.
4. **Pergunta de Pesquisa:** *"Como estimar com validade estatística e controle de incerteza a distribuição de posicionamentos no universo de contas orgânicas do debate digital legislativo?"*
5. **Objetivos e Contribuições:** Formulação dos objetivos gerais/específicos e sumário das inovações metodológicas.

### 1.2. Metodologia (*Materials and Methods*)
1. **População Alvo e Estimando:** Definição formal do Universo Finito Observado de Contas Orgânicas ($\mathcal{U}_{\text{Org}, T}$) e unidade observacional (`1 Conta Orgânica por Plataforma`).
2. **Higienização e Detecção de CIB:** MinHash LSH, verificação exata de Jaccard $\ge 0.85$, janela temporal deslizante e partição de Leiden com exclusão em nível de conta.
3. **Desenho Amostral Estratificado:** Estratos por `Plataforma × Turno Modal × Dia` em `America/Sao_Paulo` com Alocação de Hamilton ($\sum n_h = n$).
4. **Estimadores Inferenciais:**
   - Cenário 1: Hájek com pesos de desenho $d_i = 1/\pi_i$ e correção de Rogan-Gladen.
   - Cenário 2: Ponderação uniforme entre plataformas ($1/K$).
   - Cenário 3: Raking IPF bivariado com projeção no simplex limitado $[0.25, 4.00]$ aplicada iterativamente dentro do laço.
5. **Protocolo Zero-Footprint e Reprodutibilidade:** Processamento em `/tmp`, compressão Parquet ZSTD via DuckDB e sincronização atômica Git Data API com sementes pseudoaleatórias fixadas (`seed=42`).

### 1.3. Resultados (*Results*)
1. **Funil Quantitativo de Coleta:** Relato objetivo das etapas:
   $$N_{\text{bruto}} \longrightarrow N_{\text{spam\_quarentena}} \longrightarrow N_{\text{CIB\_excluído}} \longrightarrow N_{\text{Org}} \longrightarrow n \longrightarrow n_{\text{eff}}$$
2. **Tabelas Comparativas:** Apresentação simultânea dos 3 cenários com proporções, intervalos de confiança de 95% via Bootstrap Estratificado e estimativa corrigida por Rogan-Gladen.
3. **Testes de Hipóteses:** Relatório de independência intraplataforma via $\chi^2$, tamanho de efeito $V$ de Cramér e correção de Holm-Bonferroni para controle de erro familiar ($\text{FWER}$).
*Regra de Ouro:* Relatar dados empíricos com precisão numérica, sem adjetivações valorativas subjetivas.

### 1.4. Discussão e Limitações (*Discussion & Limitations*)
1. **Confronto Teórico:** Interpretação da discrepância entre Cenários 1, 2 e 3 à luz do viés de seleção e da hipótese de ignorabilidade condicional.
2. **Implicações Parlamentares:** Como os achados informam o processo legislativo sem induzir parlamentares ao erro de confundir debate em rede com opinião pública geral.
3. **Limitações Metodológicas Obrigatórias:** Transparência sobre:
   - Autosseleção dos usuários das redes digitais;
   - Proxy geográfico imperfeito por DDD (sujeito a portabilidade);
   - Dependência da acurácia do classificador de linguagem natural.

---

## 2. Normas de Citação Atualizadas

### 2.1. ABNT NBR 10520:2023 (Atualização Crucial)
> [!IMPORTANT]
> A norma ABNT NBR 10520:2023 aboliu a exigência de CAIXA ALTA para autores entre parênteses. Agora, utiliza-se **apenas a letra inicial maiúscula**:
> - **No corpo do texto:** Segundo Meng (2018), o aumento do volume de dados...
> - **Entre parênteses:** O viés de seleção pode dominar o erro amostral (Meng, 2018).
> - **Múltiplos autores:** (Traag; Waltman; Van Eck, 2019) ou (Baker et al., 2013).

### 2.2. ABNT NBR 6023:2018 (Referências com DOI)
Formato padronizado:
- MENG, Xiao-Li. Statistical Paradises and Paradoxes in Big Data (I). **The Annals of Applied Statistics**, v. 12, n. 2, p. 685–726, 2018. DOI: `https://doi.org/10.1214/18-AOAS1161SF`.

### 2.3. APA 7th Edition e IEEE
- **APA 7th:** (Meng, 2018) ou Meng (2018); referências com recuo francês de 0,5 polegada e DOI no formato `https://doi.org/10.1214/18-AOAS1161SF`.
- **IEEE:** Citações numéricas sequenciais entre colchetes: `[1]`, `[2]–[4]`.

### 2.4. Template Canônico BibTeX para LaTeX
```bibtex
@article{meng2018statistical,
  author    = {Xiao-Li Meng},
  title     = {Statistical Paradises and Paradoxes in Big Data (I): Law of Large Populations, Big Data Paradox, and the 2016 US Presidential Election},
  journal   = {The Annals of Applied Statistics},
  volume    = {12},
  number    = {2},
  pages     = {685--726},
  year      = {2018},
  doi       = {10.1214/18-AOAS1161SF}
}

@article{traag2019louvain,
  author    = {V. A. Traag and L. Waltman and N. J. van Eck},
  title     = {From Louvain to Leiden: guaranteeing well-connected communities},
  journal   = {Scientific Reports},
  volume    = {9},
  number    = {1},
  pages     = {5233},
  year      = {2019},
  doi       = {10.1038/s41598-019-41695-z}
}
```

---

## 3. Diretrizes de Estilo Linguístico e Gramática Científica

| Aspecto | Diretriz para Português Científico | Diretriz para Academic English |
| :--- | :--- | :--- |
| **Voz Verbal** | Impessoalidade na terceira pessoa (*"Observou-se"*, *"Coletaram-se"*) ou primeira pessoa do plural reflexiva em discussões conceituais (*"Propomos uma abordagem..."*). | Voz ativa concisa (*"We estimate"*, *"The algorithm partitions"*) com voz passiva nos Métodos (*"Data were pre-processed"*). |
| **Tempos Verbais** | - Passado para *Metodologia* e *Resultados* (*"Amostrou-se"*, *"Verificou-se"*).<br>- Presente para *Introdução*, *Discussão* e propriedades matemáticas universais (*"O estimador Hájek converge"*). | - Past tense for *Methods* and *Results* (*"We sampled"*, *"The test revealed"*).<br>- Present tense for *General Truths* and *Conclusions* (*"The theorem proves"*). |
| **Precisão Léxica** | Evitar advérbios vagos (*"claramente"*, *"obviamente"*, *"muito grande"*). Substituir por métricas numéricas concretas e limites de confiança. | Avoid colloquial hedges (*"kind of"*, *"basically"*, *"huge difference"*). Quantify via effect size and precision intervals. |
