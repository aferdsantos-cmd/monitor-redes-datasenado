# Aceleração em Apple Silicon MPS e Visão Computacional Multimodal

Este manual técnico aborda a otimização de execução de modelos de Deep Learning na arquitetura Apple Silicon (Metal Performance Shaders - MPS) e técnicas de visão computacional para detecção de campanhas coordenadas de imagens (Visual CIB) sob a política Zero-Footprint.

---

## 1. Gestão de Memória Unificada em Apple Silicon (MPS / CPU)

O MacBook conta com memória unificada (Unified Memory Architecture - UMA) compartilhada entre CPU, GPU e Neural Engine. Para evitar esgotamento de memória (OOM) e travamentos do sistema operacional:

### 1.1 Diretrizes de Execução Otimizada
1. **Seleção de Dispositivo Resiliente:** Proibido codificar `.to("cuda")` fixo. O código deve selecionar automaticamente a melhor opção disponível:
   ```python
   import torch
   if hasattr(torch, "backends") and torch.backends.mps.is_available():
       device = torch.device("mps")
   elif torch.cuda.is_available():
       device = torch.device("cuda")
   else:
       device = torch.device("cpu")
   ```
2. **Inferência Sem Rastreamento de Gradientes:** O bloco `with torch.inference_mode():` deve encapsular toda rotina de avaliação ou extração de vetores, reduzindo em até 60% o consumo de memória em relação a `torch.no_grad()`.
3. **Limpeza Explícita de Cache MPS:** Após processar lotes volumosos de textos ou imagens:
   ```python
   import gc
   gc.collect()
   if device.type == "mps":
       torch.mps.empty_cache()
   ```

---

## 2. Visão Computacional e Hashes Perceptuais (Visual CIB)

A proliferação de campanhas coordenadas de desinformação frequentemente adota o compartilhamento massivo de memes políticos e infográficos manipulados em plataformas visuais (Instagram, Facebook, TikTok, Telegram e WhatsApp).

Diferente de hashes criptográficos (como SHA-256), que mudam completamente com a mínima alteração de um único bit, os **Hashes Perceptuais** geram assinaturas invariantes a pequenas compressões, redimensionamentos ou adições de ruído.

### 2.1 Algoritmo Difference Hash (dHash)
1. **Redimensionamento:** Reduz a imagem para uma matriz em escala de cinza de tamanho $(8 \times 9)$ pixels (para um hash de 64 bits).
2. **Gradiente Horizontal:** Compara pixels adjacentes na linha horizontal: $P_{x, y} > P_{x+1, y}$.
3. **Conversão Binária:** Gera um vetor booleano de 64 bits, compactado em uma string hexadecimal de 16 caracteres.
4. **Métrica de Similaridade (Distância de Hamming):**
   $$\text{Distância}(H_1, H_2) = \text{contagem de bits diferentes entre } H_1 \text{ e } H_2$$
   - Distância $\le 5$: Imagens praticamente idênticas (mesmo meme sob compressões distintas de WhatsApp/Telegram);
   - Distância $\in [6, 10]$: Imagens altamente similares (mesmo layout com pequenas alterações de texto ou corte);
   - Distância $> 10$: Imagens estruturalmente distintas.

---

## 3. Higiene Zero-Footprint no Processamento Multimodal
- Imagens e frames de vídeo extraídos de postagens são gravados estritamente em `/tmp/monitor_datasenado_cache`.
- Logo após o cálculo do hash perceptual (`dHash`) e a eventual extração de embeddings semânticos (`CLIP`/`SigLIP`), o arquivo binário da imagem é compulsoriamente excluído do disco (`os.remove()`).
- O pipeline armazena exclusivamente os hashes, vetores e metadados, assegurando conformidade com o limite de 250 MB e zero resíduo em disco.
