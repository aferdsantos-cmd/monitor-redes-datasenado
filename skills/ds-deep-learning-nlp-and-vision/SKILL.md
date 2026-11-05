---
name: ds-deep-learning-nlp-and-vision
description: Use this skill whenever working with Deep Learning, HuggingFace Transformers for Portuguese NLP (BERTimbau, DeBERTa, multilingual embeddings), Parameter-Efficient Fine-Tuning (LoRA/QLoRA), Apple Silicon MPS/CPU optimization, or Computer Vision and multimodal meme/video frame analysis.
---

# Deep Learning, NLP em Português e Visão Computacional em Apple Silicon

Diretrizes arquiteturais para modelos neurais profundos, Transformers em Português e análise multimodal no Monitor de Redes DataSenado, com otimização para hardware Apple Silicon (MacBook 28 GB RAM) e conformidade Zero-Footprint.

## 1. Otimização Nativa para Apple Silicon (Zero `.cuda()` Fixo)
- **Seleção Dinâmica de Dispositivo:**
  ```python
  import torch
  device = "mps" if hasattr(torch, "backends") and torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
  ```
- **Inferência Otimizada:** Empregar compulsoriamente `torch.inference_mode()`, lotes controlados ($\le 64$ textos/imagens por batch) e liberação de memória unificada (`torch.mps.empty_cache()` e `gc.collect()`). Proibido `.to("cuda")` fixo!

## 2. Transformers para NLP Legislativo em Português (ADR-011)
- **Modelos de Referência:** BERTimbau (`neuralmind/bert-base-portuguese-cased`), DeBERTa-v3 e `BGE-M3` para representações densas multilíngues.
- **Normalização de Embeddings ($L_2 = 1$):** Vetores semânticos devem ser normalizados na norma euclidiana para permitir similaridade rápida por produto escalar:
  - Agrupamento de narrativas emergentes no Radar Diário (`ADR-008`);
  - Alinhamento de parágrafos entre portais para detecção de **Omissão Seletiva** e **Enquadramento** (`ADR-011`).
- **PEFT (LoRA / QLoRA):** Congelamento do backbone com adaptadores de posto baixo $\Delta W = B A$ ($r \in \{8, 16\}$, $\alpha = 2r$) injetados em `q_proj` e `v_proj`, serializados em `safetensors`.

## 3. Visão Computacional e CIB Visual (Memes e Imagens)
- **Hashes Perceptuais (dHash / pHash via DCT):** Geração de impressões digitais compactas de 64 bits para imagens e frames de vídeo sobre `/tmp/monitor_datasenado_cache`.
- **Detecção de Campanhas Coordenadas:** Identificação de imagens idênticas ou levemente alteradas (distância de Hamming $\le 5$) disseminadas entre contas distintas, com descarte imediato da mídia bruta (`Zero-Footprint`).

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Usar seleção de dispositivo MPS/CPU; normalizar embeddings em $L_2$; liberar cache; purgar imagens temporárias após hashing.
- **MUST NOT DO:** Nunca usar `.to("cuda")` estático; não executar inferência sem `torch.inference_mode()`; não salvar pesos brutos em `.pkl`; não reter mídia bruta em disco.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para extração tabular de features e VIF: use `ds-advanced-feature-engineering`.
- Para calibração de classificadores e testes de McNemar: use `ds-ml-modeling-and-validation`.
- Para monitoramento de drift de embeddings (PSI/KS): use `ds-mlops-and-model-lifecycle`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute a sonda de aceleração de hardware, embeddings e visão:
  ```bash
  ./skills/ds-deep-learning-nlp-and-vision/scripts/dl_hardware_and_embedding_sanity_probe.py --demo
  ```
- **Manuais Técnicos:**
  - [transformers_peft_lora_and_ptbr_nlp.md](./references/transformers_peft_lora_and_ptbr_nlp.md)
  - [multimodal_vision_and_apple_silicon_mps.md](./references/multimodal_vision_and_apple_silicon_mps.md)
