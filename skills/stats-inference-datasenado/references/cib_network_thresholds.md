# Detecção de Comportamento Inautêntico Coordenado (CIB): Arquitetura e Limiares

Este documento estabelece as especificações algorítmicas do pipeline de detecção de indícios de coordenação inautêntica e automação implementado em `src/cleaning/lgpd_and_bot_filter.py`.

---

## 1. Arquitetura em Duas Etapas

Para conciliar eficiência computacional sub-quadrática com rigor contra falsos positivos (*Rauchfleisch & Kaiser, 2020; Giglietto et al., 2020*), a detecção opera em duas camadas sequenciais:

```
[Posts Brutos] 
       │
       ▼ (Etapa 1: Filtro de Similaridade Textual & Sincronia Rápida)
   Shingling 3-gramas ──► MinHashLSH (128 perm) ──► Jaccard Exato >= 0.85
       │                                                    │
       ▼                                                    ▼
   Allowlist de Imprensa/Gov                     Janela Two-Pointer (Delta t <= Janela)
       │                                                    │
       └────────────────────────┬───────────────────────────┘
                                ▼
(Etapa 2: Grafo de Co-Compartilhamento Repetido & Comunidades)
       │
       ├─► Ponderação IDF de Hashtags: log(1 + N_posts / df(h))
       ├─► Eliminação de tags ubíquas (frequência documental > 35%)
       ├─► Aresta exige co-compartilhamento repetido de itens/eventos distintos (>= 2)
       │
       ▼
   Algoritmo de Leiden (igraph + leidenalg, seed=42)
       │
       ▼
[Índice de Coordenação & Exclusão em Nível de Conta]
```

---

## 2. Etapa 1: Similaridade Sub-Quadrática via MinHash LSH

1. **Tokenização e Shingles:** Extração de n-gramas de caracteres (3-shingles) normalizados via NFKD.
2. **MinHash:** Geração de assinatura compacta com 128 permutações pseudoaleatórias (`minhash_num_perm: 128`).
3. **Indexação LSH & Validação de Jaccard:**
   - O `MinHashLSH` recupera pares candidatos com threshold de projeto.
   - Todo par candidato é submetido à conferência determinística exata:
     $$J(A, B) = \frac{|A \cap B|}{|A \cup B|} \ge 0.85$$
4. **Agrupamento Union-Find com Varredura Temporal:**
   - Varredura em janela deslizante *two-pointer* com complexidade $O(N \cdot \bar{b})$ sobre registros ordenados no tempo.
   - Aplicação de janelas de sincronia temporal por dinâmica de plataforma:
     - Telegram, WhatsApp, X (Twitter): $\Delta t \le 60\text{s}$;
     - Instagram / Facebook: $\Delta t \le 120\text{s}$;
     - YouTube, TikTok: $\Delta t \le 180\text{s}$.
5. **Proteção contra Falso Positivo em Notícia Viral (Allowlist):**
   - URLs pertencentes à *allowlist* jornalística e governamental (`senado.leg.br`, `camara.leg.br`, `gov.br`, `g1.globo.com`, `uol.com.br`, etc.) são isentas de penalização de coordenação quando compartilhadas de forma orgânica ao longo do tempo.

---

## 3. Etapa 2: Grafo de Co-Compartilhamento e Comunidades de Leiden

1. **Ponderação e Filtragem de Hashtags:**
   - Hashtags temáticas ubíquas (presentes em $> 35\%$ das contas) são desconsideradas para geração de arestas entre contas para evitar agrupamento espúrio em torno de palavras-chave oficiais do debate.
   - Para as demais hashtags, calcula-se o peso por Frequência Inversa do Documento:
     $$\text{IDF}(h) = \ln\left(1 + \frac{N_{\text{posts}}}{\text{df}(h)}\right)$$
2. **Consolidação de Arestas no Grafo:**
   - Uma aresta não direcionada entre duas contas só é adicionada se houver repetição de co-ocorrência em eventos/itens distintos (`min_distinct_co_shared_items_for_edge: 2`).
   - O peso da aresta $w_{uv}$ acumula a intensidade temporal e o IDF dos itens co-compartilhados.
3. **Detecção de Comunidades Coordenadas via Leiden:**
   - Execução via `igraph` + `leidenalg` utilizando a partição de modularidade ou Reichardt & Bornholdt (`RBConfigurationVertexPartition`) com semente reprodutível fixa `seed = 42`.
   - Limiares para cluster suspeito:
     - Tamanho mínimo do cluster: $|C| \ge 3$ contas;
     - Taxa mínima de sincronia temporal interna: $\ge 0.35$;
     - Peso médio das arestas do cluster: $\ge 2.5$.

---

## 4. Índice Composto e Exclusão em Nível de Conta

### 4.1. Índice Heurístico Experimental (`coordination_signal_index`)
Para cada conta analisada, calcula-se um score linear ponderado em $[0, 1]$:
$$I_{\text{Coord}} = 0.30 \cdot S_{\text{LSH}} + 0.25 \cdot S_{\text{Sync}} + 0.20 \cdot S_{\text{URL/Tag}} + 0.15 \cdot S_{\text{Leiden}} + 0.10 \cdot S_{\text{FreqZ}}$$
Onde:
- $S_{\text{LSH}}$: similaridade textual máxima com mensagens idênticas de terceiros;
- $S_{\text{Sync}}$: razão de publicações dentro de janelas de sincronia de alta densidade;
- $S_{\text{URL/Tag}}$: índice de compartilhamento de URLs curtas e hashtags idênticas;
- $S_{\text{Leiden}}$: centralidade ou pertencimento a cluster coordenado no grafo de Leiden;
- $S_{\text{FreqZ}}$: anomalia de frequência comportamental (Z-score de hiperatividade horária $\ge 3.0$ ou teto $> 50$ posts/hora).

### 4.2. Exclusão em Nível de Conta (Quadro $\mathcal{U}_{\text{Org}}$)
Uma conta inteira é marcada como `account_suspected_cib = True` e excluída do universo $\mathcal{U}_{\text{Org}}$ se:
- Possuir $\ge 2$ publicações sinalizadas por indício de CIB; **OU**
- Possuir $\ge 30\%$ do total de suas publicações sinalizadas.
Isso impede que postagens residuais de uma conta operada por automação passem despercebidas e contaminem o sorteio amostral.
