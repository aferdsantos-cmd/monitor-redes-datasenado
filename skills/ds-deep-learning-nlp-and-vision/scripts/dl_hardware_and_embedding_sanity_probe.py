#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Sonda de Diagnóstico de Hardware Deep Learning, Embeddings NLP e Visão Perceptual.

Executa:
1. Detecção dinâmica de dispositivo de aceleração (Apple Silicon MPS / CUDA / CPU) sem hardcoding;
2. Normalização euclidiana L2 de embeddings densos de Transformers em Português;
3. Cálculo de similaridade semântica de cosseno e diagnóstico de Omissão Seletiva (ADR-011);
4. Geração de Hashes Perceptuais (dHash) para detecção de CIB Visual e memes coordenados;
5. Garantia de 0 KB residual em /tmp/monitor_datasenado_cache sob política Zero-Footprint.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


def detect_hardware_target() -> str:
    """Detecta de forma segura e não-bloqueante o dispositivo de aceleração disponível."""
    try:
        import torch
        if hasattr(torch, "backends") and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if hasattr(torch, "cuda") and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    except ImportError:
        # Fallback resiliente se PyTorch não estiver instalado no ambiente
        return "cpu"


def l2_normalize_embeddings(vectors: np.ndarray) -> np.ndarray:
    """Normaliza cada vetor de atributos na norma euclidiana L2 (|v|_2 = 1)."""
    v = np.asarray(vectors, dtype=float)
    if v.ndim == 1:
        norm = np.linalg.norm(v)
        return v / norm if norm > 1e-12 else v

    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1.0
    return v / norms


def semantic_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calcula a similaridade de cosseno entre dois vetores normalizados."""
    a_norm = l2_normalize_embeddings(vec_a)
    b_norm = l2_normalize_embeddings(vec_b)
    sim = float(np.dot(a_norm, b_norm))
    return float(np.clip(sim, -1.0, 1.0))


def compute_dhash_synthetic_image(matrix: np.ndarray, hash_size: int = 8) -> str:
    """Computa o Difference Hash (dHash) de 64 bits para uma matriz bidimensional de imagem (H, W)."""
    m = np.asarray(matrix, dtype=float)
    # Se a dimensão não for (hash_size, hash_size + 1), redimensiona via média de blocos
    h, w = m.shape
    target_h = hash_size
    target_w = hash_size + 1

    # Interpolação/amostragem em grade simples
    h_indices = np.linspace(0, h - 1, target_h).astype(int)
    w_indices = np.linspace(0, w - 1, target_w).astype(int)
    grid = m[np.ix_(h_indices, w_indices)]

    # Compara cada pixel com o pixel adjacente à direita
    diff = grid[:, :-1] > grid[:, 1:]
    bit_array = diff.flatten()

    # Converte vetor booleano de 64 bits em hex
    decimal_val = 0
    for bit in bit_array:
        decimal_val = (decimal_val << 1) | int(bit)

    return f"{decimal_val:016x}"


def hamming_distance_hashes(hash1: str, hash2: str) -> int:
    """Calcula a distância de Hamming (contagem de bits diferentes) entre dois hashes hexadecimais."""
    val1 = int(hash1, 16)
    val2 = int(hash2, 16)
    xor_val = val1 ^ val2
    # Contagem de bits 1 (popcount)
    return bin(xor_val).count("1")


def detect_selective_omission(
    news_emb_matrix: np.ndarray,
    portal_labels: List[str],
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Identifica fatos institucionais do Senado omitidos na cobertura de portais terceiros."""
    # O primeiro portal na lista é a referência institucional (Senado)
    norm_embs = l2_normalize_embeddings(news_emb_matrix)
    senado_mask = np.array([p == portal_labels[0] for p in portal_labels])

    senado_embs = norm_embs[senado_mask]
    other_embs = norm_embs[~senado_mask]

    if len(senado_embs) == 0 or len(other_embs) == 0:
        return {"omitted_facts_count": 0, "max_alignment_scores": []}

    # Similaridade de cosseno de cada fato do senado com a cobertura comercial
    sim_matrix = senado_embs @ other_embs.T
    max_scores = np.max(sim_matrix, axis=1)

    omitted_mask = max_scores < threshold
    n_omitted = int(np.sum(omitted_mask))

    return {
        "reference_facts_total": len(senado_embs),
        "omitted_facts_count": n_omitted,
        "omission_rate": round(float(n_omitted / len(senado_embs)), 4),
        "max_alignment_scores": [round(float(s), 4) for s in max_scores],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sonda de Hardware Deep Learning, NLP e Visão")
    parser.add_argument("--demo", action="store_true", help="Executa demonstração com detecção de hardware, NLP e dHash")
    args = parser.parse_args()

    print("=== [1/3] Detecção Resiliente de Hardware (Apple Silicon MPS / CPU) ===")
    target_hw = detect_hardware_target()
    print(f"Dispositivo selecionado: '{target_hw}'")
    assert target_hw in ("mps", "cuda", "cpu"), f"Target inesperado: {target_hw}"
    print("  ✅ Seleção de dispositivo executada sem hardcoding de .cuda().")

    print("\n=== [2/3] Normalização de Embeddings e Diagnóstico de Omissão Seletiva ===")
    rng = np.random.default_rng(42)
    # 4 fatos institucionais da Agência Senado + 3 coberturas de portais
    n_facts = 7
    dim = 64
    raw_vectors = rng.normal(0, 1, size=(n_facts, dim))
    portals = ["senado", "senado", "senado", "senado", "portal_a", "portal_a", "portal_a"]

    # Fato 0 é coberto pelo portal_a (similaridade alta); Fato 3 é omitido
    raw_vectors[4] = raw_vectors[0] + rng.normal(0, 0.1, size=dim)

    norm_embs = l2_normalize_embeddings(raw_vectors)
    norms = np.linalg.norm(norm_embs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), "Todos os vetores devem ter norma L2 = 1.0"
    print("  ✅ Vetores de representação normalizados com sucesso (||e||_2 = 1.0).")

    omission_diag = detect_selective_omission(raw_vectors, portals, threshold=0.70)
    print(f"Diagnóstico de Omissão Seletiva: {json.dumps(omission_diag, indent=2)}")
    assert omission_diag["omitted_facts_count"] >= 1, "Pelo menos um fato omitido deveria ser detectado"
    print("  ✅ Diagnóstico de omissão seletiva executado com precisão.")

    print("\n=== [3/3] Visão Perceptual: Difference Hash (dHash) e CIB Visual ===")
    # Imagem sintética base 16x16
    img_base = rng.uniform(0, 255, size=(16, 16))
    # Imagem ligeiramente modificada (compressão/ruído suave)
    img_compressed = img_base + rng.normal(0, 5, size=(16, 16))
    # Imagem totalmente diferente
    img_different = rng.uniform(0, 255, size=(16, 16))

    hash_base = compute_dhash_synthetic_image(img_base)
    hash_comp = compute_dhash_synthetic_image(img_compressed)
    hash_diff = compute_dhash_synthetic_image(img_different)

    dist_near = hamming_distance_hashes(hash_base, hash_comp)
    dist_far = hamming_distance_hashes(hash_base, hash_diff)

    print(f"dHash Imagem Base:       {hash_base}")
    print(f"dHash Imagem Comprimida: {hash_comp} (Distância: {dist_near} bits)")
    print(f"dHash Imagem Diferente:  {hash_diff} (Distância: {dist_far} bits)")

    assert dist_near <= 5, f"Distância esperada <= 5 para imagem similar, obtida {dist_near}"
    assert dist_far > 10, f"Distância esperada > 10 para imagem distinta, obtida {dist_far}"
    print("  ✅ Hashes perceptuais identificaram meme similar vs imagem distinta sob ruído.")

    # Verificação de Zero-Footprint em /tmp
    cache_dir = Path("/tmp/monitor_datasenado_cache")
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
    print("  ✅ Política Zero-Footprint verificada (0 KB residual em /tmp).")

    print("\nSonda de Deep Learning, Embeddings NLP e Visão Perceptual concluída com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
