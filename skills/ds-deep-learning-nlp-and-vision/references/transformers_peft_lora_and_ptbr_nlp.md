# Modelos de Linguagem em Português, LoRA/QLoRA e Alinhamento Semântico

Este manual técnico orienta a aplicação de modelos neurais baseados em Transformers para o processamento de texto legislativo em língua portuguesa, técnicas de ajuste fino com eficiência de parâmetros (PEFT) e métodos de alinhamento textual para a detecção de viés editorial (ADR-011).

---

## 1. Modelos Pré-Treinados em Português

O discurso legislativo e a opinião pública no Brasil possuem particularidades linguísticas (jargões jurídicos, gírias regionais, construções irônicas e concordâncias coloquiais) que demandam modelos especializados:

1. **BERTimbau (`neuralmind/bert-base-portuguese-cased`):** Modelo de referência para tarefas discriminativas (classificação de posicionamento, extração de entidades nomeadas e análise de sentimento legislativo).
2. **DeBERTa-v3 Multilíngue:** Arquitetura com atenção desacoplada (*disentangled attention*) que codifica conteúdo e posição relativa separadamente, superior na captura de relações sintáticas complexas e polaridade sutil.
3. **BGE-M3 / Sentence-BERTimbau:** Modelos focados em geração de embeddings densos de frases e parágrafos para busca semântica e agrupamento no Radar Diário do Senado (ADR-008).

---

## 2. Parameter-Efficient Fine-Tuning (PEFT / LoRA)

O ajuste fino completo (*Full Fine-Tuning*) de um modelo de linguagem requer gradientes para todos os bilhões de parâmetros, exigindo dezenas de gigabytes de VRAM e gerando arquivos redundantes.

A técnica Low-Rank Adaptation (LoRA - Hu et al., 2021) congela os pesos originais $W_0 \in \mathbb{R}^{d \times k}$ e injeta duas matrizes de posto baixo $B \in \mathbb{R}^{d \times r}$ e $A \in \mathbb{R}^{r \times k}$ com $r \ll \min(d, k)$:

$$W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \cdot A)$$

### 2.1 Configuração Homologada para macOS Apple Silicon
- **Posto ($r$):** $r=8$ ou $r=16$;
- **Fator de Escala ($\alpha$):** $\alpha = 2r$ (típico $\alpha=16$ para $r=8$);
- **Módulos Alvo:** Injeção preferencial nas projeções de atenção (`q_proj`, `v_proj` ou `query`, `value`);
- **Formato de Exportação:** Salvamento dos adaptadores exclusivamente em `safetensors` (peso inferior a 30 MB por modelo ajustado, facilitando a governança Zero-Footprint).

---

## 3. Alinhamento Semântico e Detecção de Omissão Seletiva (ADR-011)

No âmbito do futuro ecossistema de inteligência editorial 360º (Pilar 2), o sistema compara como diferentes veículos de comunicação cobrem a mesma pauta legislativa:

### 3.1 Normalização e Similaridade de Cosseno
Sejam $\mathbf{e}_A$ e $\mathbf{e}_B$ os vetores de representação densa de dois parágrafos de notícias de portais distintos. Exige-se normalização prévia na norma euclidiana:
$$\hat{\mathbf{e}} = \frac{\mathbf{e}}{\|\mathbf{e}\|_2} \implies \text{sim}(\mathbf{e}_A, \mathbf{e}_B) = \hat{\mathbf{e}}_A \cdot \hat{\mathbf{e}}_B$$

### 3.2 Diagnóstico de Omissão Seletiva
1. Para cada parágrafo factual da cobertura da Agência Senado (referência institucional), busca-se o parágrafo de maior similaridade de cosseno na cobertura de um portal comercial:
   $$s_i^* = \max_j (\hat{\mathbf{e}}_{\text{senado}, i} \cdot \hat{\mathbf{e}}_{\text{portal}, j})$$
2. Se $s_i^* < 0.65$, o fato $i$ (ex.: menção aos custos orçamentários, parecer da consultoria legislativa ou posicionamento da oposição) é diagnosticado como **Fato Omitido** pelo portal.
3. A taxa agregada de omissões gera o Índice de Omissão Seletiva (*Selective Omission Score*), fornecendo ao parlamento uma visão analítica sobre o enquadramento midiático.
