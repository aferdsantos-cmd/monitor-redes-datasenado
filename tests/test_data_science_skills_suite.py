"""
Suíte de Testes da Arquitetura e Portões das 7 Novas Skills de Ciência de Dados.

Valida:
1. Imutabilidade absoluta da Baseline da Fase 01 (16 arquivos WP-01 a WP-16);
2. Estrutura, frontmatter YAML, teto de linhas (<= 85 linhas) e resolução de links;
3. Manuais técnicos aprofundados em references/ (> 40 linhas por manual);
4. Execução das 7 sondas em modo --demo com verificação de saída e 0 KB em /tmp;
5. Testes unitários das travas anti-atalhos (AST linter, leakage, disjunção de contas,
   modularidade Q, propagação harmônica de espectros, PSI drift e bloqueio de pickle).
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
import pytest
import yaml

from src.config_loader import REPO_ROOT
from src.storage.phase_baseline_guard import Phase01BaselineGuard

NEW_DATA_SCIENCE_SKILLS = [
    "ds-eda-and-vectorized-manipulation",
    "ds-advanced-feature-engineering",
    "ds-ml-modeling-and-validation",
    "stats-network-bubbles-and-time-series",
    "ds-xai-and-model-explainability",
    "ds-mlops-and-model-lifecycle",
    "ds-deep-learning-nlp-and-vision",
]

EXPECTED_NEW_REFERENCES = {
    "ds-eda-and-vectorized-manipulation": [
        "vectorized_duckdb_pandas_patterns.md",
        "missing_data_and_join_integrity.md",
    ],
    "ds-advanced-feature-engineering": [
        "leakage_free_pipelines_and_oof_encoding.md",
        "timeseries_lexical_and_graph_features.md",
    ],
    "ds-ml-modeling-and-validation": [
        "anti_leakage_cv_and_calibration.md",
        "hypothesis_testing_fdr_and_model_comparison.md",
    ],
    "stats-network-bubbles-and-time-series": [
        "echo_chambers_modularity_and_ei_index.md",
        "seed_label_propagation_and_granger_agenda.md",
    ],
    "ds-xai-and-model-explainability": [
        "shap_lime_and_permutation_workflows.md",
        "public_sector_xai_and_subgroup_fairness.md",
    ],
    "ds-mlops-and-model-lifecycle": [
        "zero_footprint_mlops_and_safe_serialization.md",
        "drift_monitoring_psi_jsd_and_recalibration.md",
    ],
    "ds-deep-learning-nlp-and-vision": [
        "transformers_peft_lora_and_ptbr_nlp.md",
        "multimodal_vision_and_apple_silicon_mps.md",
    ],
}

EXPECTED_NEW_SCRIPTS = {
    "ds-eda-and-vectorized-manipulation": "eda_vectorized_linter_and_profiler.py",
    "ds-advanced-feature-engineering": "feature_leakage_and_collinearity_auditor.py",
    "ds-ml-modeling-and-validation": "ml_validation_and_calibration_probe.py",
    "stats-network-bubbles-and-time-series": "bubble_topology_and_spectrum_probe.py",
    "ds-xai-and-model-explainability": "xai_shap_and_subgroup_fairness_auditor.py",
    "ds-mlops-and-model-lifecycle": "drift_psi_and_model_card_validator.py",
    "ds-deep-learning-nlp-and-vision": "dl_hardware_and_embedding_sanity_probe.py",
}

EXPECTED_DEMO_OUTPUTS = {
    "ds-eda-and-vectorized-manipulation": "EDA Vectorized Linter & Profiler concluído com 100% de conformidade",
    "ds-advanced-feature-engineering": "Auditoria de Feature Engineering e Anti-Leakage concluída com sucesso",
    "ds-ml-modeling-and-validation": "Sonda de Modelagem ML, Calibração e Validação FDR concluída com sucesso",
    "stats-network-bubbles-and-time-series": "Sonda de Topologia de Bolhas Digitais e Espectros (ADR-010) concluída com sucesso",
    "ds-xai-and-model-explainability": "Auditoria XAI (SHAP, Permutation Importance e Equidade de Subgrupo) concluída com sucesso",
    "ds-mlops-and-model-lifecycle": "Validador MLOps de Drift (PSI/JSD) e Model Card concluído com sucesso",
    "ds-deep-learning-nlp-and-vision": "Sonda de Deep Learning, Embeddings NLP e Visão Perceptual concluída com sucesso",
}


def test_phase01_baseline_remains_100_percent_intact():
    """Valida que todos os 16 arquivos da Fase 01 (WP-01 a WP-16) permanecem 100% intocados."""
    guard = Phase01BaselineGuard()
    status = guard.verify_baseline_integrity()
    assert status.is_intact is True, (
        f"Violação da baseline Fase 01! Arquivos divergentes: {status.divergent_files}"
    )


def test_all_seven_new_data_science_skills_exist():
    """Valida a presença de todas as 7 novas pastas de skills em skills/."""
    skills_root = REPO_ROOT / "skills"
    assert skills_root.exists() and skills_root.is_dir()

    for skill_name in NEW_DATA_SCIENCE_SKILLS:
        skill_dir = skills_root / skill_name
        assert skill_dir.exists() and skill_dir.is_dir(), f"Pasta de skill ausente: {skill_dir}"
        assert (skill_dir / "SKILL.md").exists(), f"SKILL.md ausente em {skill_dir}"


def test_new_skills_frontmatter_and_line_limits():
    """Valida frontmatter YAML estrito (name, description > 30 chars) e teto de <= 85 linhas."""
    skills_root = REPO_ROOT / "skills"

    for skill_name in NEW_DATA_SCIENCE_SKILLS:
        skill_md = skills_root / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()

        assert len(lines) <= 85, (
            f"{skill_name}/SKILL.md excedeu 85 linhas ({len(lines)} linhas). Respeite o Progressive Disclosure!"
        )

        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert match is not None, f"{skill_name}/SKILL.md não possui delimitadores YAML ---"

        data = yaml.safe_load(match.group(1))
        assert isinstance(data, dict), f"Frontmatter de {skill_name} deve ser um dicionário YAML"
        assert data.get("name") == skill_name, f"Campo 'name' inválido no frontmatter de {skill_name}"
        assert "description" in data and len(str(data["description"]).strip()) > 30, (
            f"Campo 'description' ausente ou excessivamente curto (> 30 chars) em {skill_name}"
        )


def test_new_skills_relative_links_and_references_resolve():
    """Garante que todos os links relativos em SKILL.md resolvem para referências e scripts reais (> 40 linhas)."""
    skills_root = REPO_ROOT / "skills"
    link_pattern = re.compile(r"\[.*?\]\(((?:\./|\.\./)[^)]+)\)")

    for skill_name in NEW_DATA_SCIENCE_SKILLS:
        skill_dir = skills_root / skill_name
        skill_md = skill_dir / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        links = link_pattern.findall(content)
        assert len(links) >= 2, f"{skill_name}/SKILL.md deve conter links relativos"

        for link in links:
            target_path = (skill_dir / link.split("#")[0]).resolve()
            assert target_path.exists(), f"Link quebrado em {skill_name}: '{link}' -> {target_path} não existe!"

        # Verifica se as duas referências técnicas profundas esperadas possuem > 40 linhas
        refs = EXPECTED_NEW_REFERENCES[skill_name]
        for ref_filename in refs:
            ref_path = skill_dir / "references" / ref_filename
            assert ref_path.exists(), f"Referência ausente: {ref_path}"
            ref_lines = ref_path.read_text(encoding="utf-8").splitlines()
            assert len(ref_lines) > 40, (
                f"{ref_filename} possui apenas {len(ref_lines)} linhas. Requer > 40 linhas de rigor técnico!"
            )


def test_new_skills_anti_shortcut_guardrails_documented():
    """Valida se todas as novas skills possuem seção explícita de práticas anti-atalhos (MUST DO / MUST NOT DO)."""
    skills_root = REPO_ROOT / "skills"

    for skill_name in NEW_DATA_SCIENCE_SKILLS:
        skill_md = skills_root / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")

        assert "MUST DO" in content and "MUST NOT DO" in content, (
            f"{skill_name}/SKILL.md deve conter seção anti-atalhos 'MUST DO / MUST NOT DO'"
        )
        assert "Matriz de Roteamento" in content or "Roteamento" in content, (
            f"{skill_name}/SKILL.md deve conter seção de roteamento de competências"
        )


def test_existing_skills_routing_updated_without_breaking_wp16():
    """Valida que stats-inference-datasenado, eng-python e AGENTS.md foram atualizados respeitando os limites."""
    stats_md = REPO_ROOT / "skills" / "stats-inference-datasenado" / "SKILL.md"
    eng_md = REPO_ROOT / "skills" / "eng-python-zero-footprint" / "SKILL.md"
    agents_md = REPO_ROOT / "AGENTS.md"

    stats_lines = stats_md.read_text(encoding="utf-8").splitlines()
    eng_lines = eng_md.read_text(encoding="utf-8").splitlines()
    agents_lines = agents_md.read_text(encoding="utf-8").splitlines()

    assert len(stats_lines) <= 85, f"stats-inference-datasenado/SKILL.md excedeu 85 linhas ({len(stats_lines)})"
    assert len(eng_lines) <= 85, f"eng-python-zero-footprint/SKILL.md excedeu 85 linhas ({len(eng_lines)})"
    assert len(agents_lines) <= 45, f"AGENTS.md excedeu 45 linhas ({len(agents_lines)})"

    stats_content = "\n".join(stats_lines)
    eng_content = "\n".join(eng_lines)
    agents_content = "\n".join(agents_lines)

    assert "ds-ml-modeling-and-validation" in stats_content
    assert "stats-network-bubbles-and-time-series" in stats_content
    assert "ds-eda-and-vectorized-manipulation" in eng_content
    assert "ds-mlops-and-model-lifecycle" in eng_content
    assert "Suíte de Ciência de Dados & Estatística Avançada" in agents_content


@pytest.mark.parametrize("skill_name", NEW_DATA_SCIENCE_SKILLS)
def test_new_skills_script_execution_demo(skill_name: str):
    """Executa a sonda de cada uma das 7 novas skills com --demo e valida saída e 0 KB em /tmp."""
    script_file = EXPECTED_NEW_SCRIPTS[skill_name]
    script_path = REPO_ROOT / "skills" / skill_name / "scripts" / script_file

    assert script_path.exists(), f"Script ausente: {script_path}"
    assert os.access(script_path, os.X_OK), f"Script {script_file} não possui permissão executável (+x)"

    res = subprocess.run(
        [sys.executable, str(script_path), "--demo"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res.returncode == 0, f"{script_file} falhou com código {res.returncode}:\n{res.stdout}\n{res.stderr}"

    expected_msg = EXPECTED_DEMO_OUTPUTS[skill_name]
    assert expected_msg in res.stdout, f"Mensagem esperada '{expected_msg}' não encontrada na saída de {script_file}"

    # Verificação de 0 KB em /tmp
    cache_dir = Path("/tmp/monitor_datasenado_cache")
    if cache_dir.exists():
        files = list(cache_dir.iterdir())
        assert len(files) == 0, f"Resíduo em {cache_dir} detectado após execução de {script_file}: {files}"


def _load_module_from_path(module_name: str, file_path: Path) -> Any:
    """Carrega dinamicamente módulo python a partir de caminho absoluto."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Falha ao carregar especificação para {file_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ast_vectorization_linter_rejects_slow_loops_and_accepts_vectorized():
    """Valida que o linter AST de eda_vectorized reprova iterrows()/apply(axis=1) e aprova operações vetorizadas."""
    script_path = REPO_ROOT / "skills" / "ds-eda-and-vectorized-manipulation" / "scripts" / "eda_vectorized_linter_and_profiler.py"
    eda_mod = _load_module_from_path("eda_mod", script_path)

    bad_snippet = """
import pandas as pd
for i, r in df.iterrows():
    pass
df.apply(lambda row: row['val'] * 2, axis=1)
"""
    violations = eda_mod.find_ast_vectorization_violations(bad_snippet)
    assert len(violations) == 2, f"Esperadas 2 violações, obtidas {len(violations)}: {violations}"

    good_snippet = """
import numpy as np
df['res'] = np.select([df['val'] > 0], [df['val'] * 2], default=0)
"""
    clean_violations = eda_mod.find_ast_vectorization_violations(good_snippet)
    assert len(clean_violations) == 0, f"Código limpo não deveria gerar violações: {clean_violations}"


def test_feature_leakage_and_collinearity_auditor_detects_leakage_and_vif():
    """Valida detecção de variável vazada (look-ahead correlation) e cômputo de VIF."""
    script_path = REPO_ROOT / "skills" / "ds-advanced-feature-engineering" / "scripts" / "feature_leakage_and_collinearity_auditor.py"
    feat_mod = _load_module_from_path("feat_mod", script_path)

    import numpy as np
    rng = np.random.default_rng(123)
    y = rng.integers(0, 2, size=100)
    clean_col = rng.normal(0, 1, size=100)
    leaked_col = y.astype(float) * 0.99 + rng.normal(0, 0.01, size=100)

    X = np.column_stack([clean_col, leaked_col])
    names = ["clean_feature", "future_leak_feature"]

    leaks = feat_mod.audit_feature_leakage(X, y, names, threshold=0.85)
    assert "future_leak_feature" in leaks
    assert "clean_feature" not in leaks

    # Teste de Burstiness
    bot_series = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    b_val = feat_mod.compute_burstiness(bot_series)
    assert b_val < -0.90


def test_ml_validation_probe_guarantees_disjoint_accounts_and_fdr():
    """Valida disjunção de autores em StratifiedGroupKFold e ordenação de Benjamini-Hochberg FDR."""
    script_path = REPO_ROOT / "skills" / "ds-ml-modeling-and-validation" / "scripts" / "ml_validation_and_calibration_probe.py"
    ml_mod = _load_module_from_path("ml_mod", script_path)

    import numpy as np
    rng = np.random.default_rng(42)
    authors = np.repeat(np.arange(30), 5)  # 150 observações em 30 autores
    y = rng.integers(0, 2, size=len(authors))

    splits = ml_mod.stratified_group_kfold_split(authors, y, n_splits=5, seed=42)
    assert len(splits) == 5

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        train_authors = set(authors[train_idx])
        val_authors = set(authors[val_idx])
        assert len(train_authors.intersection(val_authors)) == 0, f"Vazamento de autor no fold {fold_idx}"

    # Teste de Benjamini-Hochberg FDR
    p_vals = np.array([0.005, 0.01, 0.04, 0.25, 0.80])
    rejected, q_vals = ml_mod.benjamini_hochberg_fdr(p_vals, alpha=0.05)
    assert bool(rejected[0]) and bool(rejected[1])
    assert np.all(np.diff(q_vals) >= -1e-12), "q-valores de FDR devem ser monotonicamente crescentes"


def test_bubble_topology_probe_quantifies_modularity_and_seed_propagation():
    """Valida Modularidade de Newman Q e propagação harmônica de expoentes-semente (ADR-010)."""
    script_path = REPO_ROOT / "skills" / "stats-network-bubbles-and-time-series" / "scripts" / "bubble_topology_and_spectrum_probe.py"
    bubble_mod = _load_module_from_path("bubble_mod", script_path)

    import numpy as np
    # Grafo 2 bolhas perfeitamente desconectadas (n=10 cada)
    A = np.zeros((20, 20), dtype=float)
    A[:10, :10] = 1.0 - np.eye(10)
    A[10:, 10:] = 1.0 - np.eye(10)
    communities = np.array([0] * 10 + [1] * 10)

    q_val = bubble_mod.compute_newman_modularity(A, communities)
    assert q_val > 0.45, f"Modularidade de bolhas perfeitas deve ser alta: {q_val}"

    ei_res = bubble_mod.compute_krackhardt_ei_index(A, communities)
    assert ei_res[0] == -1.0 and ei_res[1] == -1.0, "Câmara de eco pura deve ter E-I = -1.0"

    # Propagação harmônica a partir dos nós 0 e 10
    affinity = bubble_mod.harmonic_seed_label_propagation(A, [0, 10], [0, 1], n_classes=2)
    assert affinity[0, 0] > 0.95 and affinity[10, 1] > 0.95


def test_drift_validator_triggers_red_alert_and_blocks_pickle_model_card():
    """Valida semáforo vermelho de PSI (>= 0.25) e bloqueio de serialização pickle no Model Card."""
    script_path = REPO_ROOT / "skills" / "ds-mlops-and-model-lifecycle" / "scripts" / "drift_psi_and_model_card_validator.py"
    mlops_mod = _load_module_from_path("mlops_mod", script_path)

    import numpy as np
    rng = np.random.default_rng(999)
    ref = rng.normal(0, 1, size=500)
    drifted = rng.normal(1.5, 1.5, size=500)

    psi_val = mlops_mod.calculate_psi(ref, drifted)
    assert psi_val >= 0.25, f"Esperado PSI crítico (>= 0.25), obtido {psi_val}"

    bad_card = {
        "model_id": "test_model",
        "task": "stance",
        "architecture": "net",
        "code_commit_sha": "abc",
        "training_data": {},
        "validation_metrics_oof": {},
        "rogan_gladen_matrix": {},
        "format": "pickle.dump",
    }
    is_valid, errors = mlops_mod.validate_model_card_json(bad_card)
    assert is_valid is False
    assert any("pickle" in err for err in errors)


def test_dl_hardware_probe_normalizes_embeddings_and_detects_dhash():
    """Valida normalização de embeddings L2 e computação de diferença perceptual dHash."""
    script_path = REPO_ROOT / "skills" / "ds-deep-learning-nlp-and-vision" / "scripts" / "dl_hardware_and_embedding_sanity_probe.py"
    dl_mod = _load_module_from_path("dl_mod", script_path)

    import numpy as np
    rng = np.random.default_rng(42)
    vectors = rng.normal(0, 1, size=(5, 32))
    norm_v = dl_mod.l2_normalize_embeddings(vectors)
    norms = np.linalg.norm(norm_v, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)

    img_a = rng.uniform(0, 255, size=(16, 16))
    img_b = img_a.copy()
    img_b[0, 0] += 1.0  # Quase imperceptível

    hash_a = dl_mod.compute_dhash_synthetic_image(img_a)
    hash_b = dl_mod.compute_dhash_synthetic_image(img_b)
    dist = dl_mod.hamming_distance_hashes(hash_a, hash_b)
    assert dist <= 2, f"Imagens idênticas com ruído mínimo devem ter distância de Hamming baixa: {dist}"
