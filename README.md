# 📊 Monitor do Debate Público Digital com Validade Estatística (TCC Ciência de Dados & DataSenado)

Plataforma modular e open-source de **Escuta Social Multi-Plataforma, Detecção de Indícios de Comportamento Inautêntico Coordenado (CIB) e Inferência Estatística sobre o Debate Público Digital Observado**, desenvolvida como Trabalho de Conclusão de Curso (TCC) em Ciência de Dados com foco em aplicação complementar no **Instituto de Pesquisa DataSenado (Senado Federal)**.

---

## 🎯 Escopo Científico, Estimando Primário e Limites Inferenciais

> [!IMPORTANT]
> **Distinção Metodológica Fundamental (Debate Digital Observado vs. Censo Populacional):**
> Em estrita conformidade com a literatura estatística sobre amostras não-probabilísticas e rastros digitais (*Bethlehem, 2010; Baker et al., 2013; Elliott & Valliant, 2017; Meng, 2018*), este sistema **não substitui nem se equipara a uma pesquisa de opinião pública por amostragem probabilística da população brasileira** (como os *surveys* telefônicos realizados pelo DataSenado).
>
> - **População-Alvo e Estimando Primário ($\theta_T$):** A proporção de posicionamento sobre o **Universo Observado de Contas Digitais Orgânicas ($\mathcal{U}_{\text{Org}, T}$)** que se manifestam sobre o tema legislativo $T$:
>   $$\theta_T = \frac{1}{|\mathcal{U}_{\text{Org}, T}|} \sum_{i \in \mathcal{U}_{\text{Org}, T}} \mathbb{I}(\text{stance}_i = \text{Favorável})$$
> - **Unidade Observacional:** **`1 Autor Digital Orgânico por Plataforma = 1 Unidade Observacional`** (`total_organic_accounts_N_org`), submetida a **pseudonimização por `HMAC-SHA256`** (64 caracteres hexadecimais, dado pessoal nos termos da LGPD art. 13, §4º, com chave secreta em `.env` e modo *fail-closed*).
> - **Significado dos Intervalos de Confiança:** Os intervalos quantificam **(a) a incerteza estatística interna do sorteio estratificado de contas ($\pi_i$) / reamostragem bootstrap** e **(b) a correção do erro de classificação (Rogan & Gladen, 1978)**; **não são margem de erro demográfica populacional** e não quantificam viés de autosseleção ou silêncio de não usuários.

---

## 🔬 Diferenciais Técnicos e Estatísticos Implementados (Versão `v1.2-fase01`)

1. **Coleta com Neutralidade Lexical e Amostragem Estratificada de Contas ([`src/sampling/stratified_sampler.py`](src/sampling/stratified_sampler.py)):**
   - Separação no [`config/settings.yaml`](config/settings.yaml) (carregado centralmente por [`src/config_loader.py`](src/config_loader.py)) entre **termos descritivos/institucionais de coleta** (`collection_query_terms`) e **taxonomia semântica de pós-classificação** (`nlp_stance_taxonomy`).
   - Fluxo estrito: **Coleta Observacional $\rightarrow$ Desinfecção (Spam/CIB em nível de conta) $\rightarrow$ Quadro de Contas Orgânicas ($\mathcal{U}_{\text{Org}}$) $\rightarrow$ Sorteio Estratificado de Contas ($s$)** por `Plataforma × Turno Modal × Dia` (no fuso `America/Sao_Paulo`), com alocação exata de Hamilton (Maior Resto), semente pseudoaleatória fixa e registrada e exportação de $\pi_i$ e $d_i = 1/\pi_i$.

2. **Busca de Similaridade Sub-Quadrática Esperada via LSH e Grafo de Co-Compartilhamento Repetido ([`src/cleaning/lgpd_and_bot_filter.py`](src/cleaning/lgpd_and_bot_filter.py)):**
   - **LSH + Union-Find + Verificação de Jaccard:** Gera assinaturas `MinHash` (128 permutações) indexadas em `MinHashLSH`, valida `jaccard >= 0.85` e agrupa componentes conexos via *Union-Find* com janela temporal *two-pointer* (complexidade sub-quadrática esperada $O(N \cdot \bar{b})$).
   - **Proteção contra Falso Positivo em Notícia Viral (Rauchfleisch & Kaiser, 2020; Giglietto et al., 2020; Pacheco et al., 2021):** Possui *allowlist* de domínios jornalísticos e institucionais (`senado.leg.br`, `camara.leg.br`, `g1.globo.com`, etc.), penalização IDF para hashtags do próprio tema e exigência de repetição de co-compartilhamento antes de formar arestas para o **Algoritmo de Leiden** (`igraph` + `leidenalg`).
   - **Classificação Simétrica em 5 Classes e Quarentena de Spam:** Normalização Unicode NFKD (tratando simetricamente *"Vote SIM"* e *"Vote NÃO"* com acento), separando `Organico`, `Mobilizacao_Civica_Legitima` (marcador cívico explícito), `Repeticao_Organica` (near-duplicate assíncrono neutro), `Suspeita_CIB_Automacao` (aplicada em **nível de conta**) e `Spam_Comercial` (colocado em quarentena com motivo auditável e proteção de vocábulos legislativos como *"sorteio do relator"* e *"CPI das apostas"*).
   - **Índice Heurístico Experimental de Sinal de Coordenação (`coordination_signal_index` $\in [0,1]$):**
     $$I_{\text{Coord}} = 0,30 \cdot S_{\text{LSH}} + 0,25 \cdot S_{\text{Sync}} + 0,20 \cdot S_{\text{URL/Tag}} + 0,15 \cdot S_{\text{Leiden}} + 0,10 \cdot S_{\text{FreqZ}}$$

3. **Motor Estatístico em 3 Cenários, Raking IPF com *Trimming* no Laço e Testes com Correção de Holm ([`src/stats/opinion_inference_engine.py`](src/stats/opinion_inference_engine.py)):**
   - **Cenário 1 — Indicador Orgânico de Contas ($\mathcal{U}_{\text{Org}}$):** Estimado com pesos de desenho $d_i = 1/\pi_i$ e acompanhado da estimativa corrigida por erro de classificação de **Rogan & Gladen (1978)**.
   - **Cenário 2 — Indicador Equilibrado por Plataforma ($w_k = 1/K$):** Atribui peso igual a cada plataforma monitorada.
   - **Cenário 3 — Reponderado (Sensibilidade sob Hipótese de Ignorabilidade):** Raking Bivariado IPF (*Deming & Stephan, 1940; Kalton & Flores-Cervantes, 2003*) com **Truncamento de Pesos (*Weight Trimming* $[0,25; 4,00]$, *Kish, 1992; Valliant, Dever & Kreuter, 2018*) aplicado dentro do laço** e projeção no simplex limitado, reportando tabela de margens e `calibration_status` (`CALIBRADO_OK` ou `NAO_ATINGIDA_LIMITADA_POR_TRIMMING`).
   - **Bootstrap Não Paramétrico Estratificado de Contas (em *chunks* de memória controlada)** e **$\chi^2$ de Pearson Ajustado pelo $DEFF$ Intraplataforma (Aproximação de 1ª Ordem)** acompanhado de **Tamanho de Efeito $V$ de Cramér** e correção de **Holm-Bonferroni** para múltiplos testes.

---

## 🧪 Como Executar a Suíte de Testes Automatizados (`pytest`)

```bash
uv run --extra dev pytest -v
```
