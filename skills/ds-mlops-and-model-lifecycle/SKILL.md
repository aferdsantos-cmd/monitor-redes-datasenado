---
name: ds-mlops-and-model-lifecycle
description: Use this skill whenever tracking ML experiments, versioning model artifacts under Zero-Footprint and SAST constraints (no pickle), generating Model Cards, or monitoring Data Drift, Covariate Shift, and Concept Drift (PSI, Jensen-Shannon, Wasserstein, KS) across monitoring windows.
---

# Governança de MLOps Zero-Footprint, Drift de Modelos e Model Cards

Padrões de governança operacional de modelos de Machine Learning para o Monitor de Redes DataSenado, conciliando monitoramento estatístico contínuo de deriva de dados (*data drift*), versionamento seguro sem `pickle` e conformidade estrita com a política Zero-Footprint.

## 1. MLOps Zero-Footprint e Serialização Segura
- **Banimento Estrito de `pickle`:** Proibido salvar `.pkl`, `.joblib` inseguro ou invocar `pickle.loads` (violação do Gate 3 SAST). Pesos e modelos devem ser salvos em formatos auditáveis: `JSON`, `safetensors`, `ONNX` ou tabelas de coeficientes em Parquet `ZSTD` em `/tmp/monitor_datasenado_cache`.
- **Model Card Compulsório (Mitchell et al., 2019):** Todo modelo em produção deve possuir ficha técnica versionada contendo `model_id`, commit git, hash SHA-256 dos dados de treino, hiperparâmetros, métricas out-of-fold, matriz de confusão Rogan-Gladen e salvaguardas da LGPD.

## 2. Monitoramento Estatístico de Data Drift e Concept Drift
- **Population Stability Index (PSI):**
  $$\text{PSI}(P, Q) = \sum_{b=1}^B (p_b - q_b) \ln\left(\frac{p_b + \epsilon}{q_b + \epsilon}\right)$$
  - $\text{PSI} < 0.10$: Distribuição estável (**Semáforo Verde**);
  - $0.10 \le \text{PSI} < 0.25$: Deriva moderada (**Semáforo Amarelo** — alerta de monitoramento);
  - $\text{PSI} \ge 0.25$: Deriva crítica (**Semáforo Vermelho** — trava de produção e disparo compulsório de nova anotação humana).
- **Divergência de Jensen-Shannon ($D_{JS} \in [0, \ln 2]$):** Para deriva em variáveis categóricas e tópicos.
- **Teste Kolmogorov-Smirnov (KS):** Para divergência de distribuições contínuas de engajamento e escores.

## 3. Trava de Ponto de Ruptura de Rogan-Gladen em Produção
- **Índice de Youden:** Em produção, se a degradação temporal ou drift fizer com que $J_c = \hat{\text{Se}}_c + \hat{\text{Sp}}_c - 1 \le 0.20$, o pipeline bloqueia imediatamente a divulgação do relatório e aciona a recalibração em `stats-inference-datasenado`.

## 4. Práticas Anti-Atalhos (MUST DO / MUST NOT DO)
- **MUST DO:** Validar esquema do Model Card; computar PSI entre janelas de monitoramento; alertar recalibração se PSI >= 0.25; respeitar 0 KB residual em `/tmp`.
- **MUST NOT DO:** Nunca usar `pickle`; não ignorar semáforo vermelho de drift; não alterar hiperparâmetros em produção sem novo Model Card; não salvar checkpoints pesados no repositório.

## 5. Matriz de Roteamento e Fronteiras de Competência
- Para treinamento, calibração ECE e testes FDR: use `ds-ml-modeling-and-validation`.
- Para correção de prevalência de Rogan-Gladen e Raking IPF: use `stats-inference-datasenado`.
- Para pipelines de sincronização segura Drive/GitHub: use `eng-python-zero-footprint`.

## 6. Sonda Executável e Referências Aprofundadas
- Execute a sonda de MLOps, drift e validação de Model Cards:
  ```bash
  ./skills/ds-mlops-and-model-lifecycle/scripts/drift_psi_and_model_card_validator.py --demo
  ```
- **Manuais Técnicos:**
  - [zero_footprint_mlops_and_safe_serialization.md](./references/zero_footprint_mlops_and_safe_serialization.md)
  - [drift_monitoring_psi_jsd_and_recalibration.md](./references/drift_monitoring_psi_jsd_and_recalibration.md)
