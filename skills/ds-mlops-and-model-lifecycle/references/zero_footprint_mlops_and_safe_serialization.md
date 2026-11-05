# MLOps Zero-Footprint e Serialização Segura sem Pickle

Este manual técnico define os padrões de governança e engenharia de ciclo de vida de modelos para o Monitor de Redes DataSenado, assegurando rastreabilidade criptográfica integral sob a política Zero-Footprint e conformidade estrita com o Gate 3 SAST.

---

## 1. Riscos de Segurança do Formato Pickle e o Gate 3 SAST

O módulo `pickle` padrão de Python é uma das principais fontes de vulnerabilidade em sistemas de aprendizado de máquina. A sua desserialização (`pickle.load` / `pickle.loads`) executa instruções arbitrárias através do método `__reduce__`, permitindo ataques de Execução Remota de Código (RCE - Remote Code Execution).

No projeto DataSenado:
1. O scanner SAST (`skills/eng-python-zero-footprint/scripts/verify_gate.sh`) reprova compulsoriamente qualquer menção a `pickle.load`, `pickle.loads`, `eval()` ou `exec()` no código-fonte.
2. É expressamente proibido versionar artefatos binários `.pkl` ou `.joblib` na árvore do repositório.

### 1.1 Formatos de Serialização Segura Homologados
- **JSON Estruturado:** Para modelos lineares, árvores leves, parâmetros de calibração Platt e matrizes de confusão.
- **Safetensors (HuggingFace):** Formato seguro baseado em memória mapeada (*zero-copy mmap*) para tensores e pesos de redes neurais e transformadores, imune a execução de código.
- **ONNX (Open Neural Network Exchange):** Para interoperabilidade e execução de inferência otimizada com grafo estático.
- **Parquet ZSTD em DuckDB:** Para tabelas de coeficientes, históricos de predição e logs de validação armazenados efemeramente em `/tmp/monitor_datasenado_cache` e sincronizados via Drive.

---

## 2. Estrutura Canônica do Model Card (Mitchell et al., 2019)

Para garantir reprodutibilidade e conformidade com auditorias públicas do TCU e do Senado, cada modelo promovido para o ambiente de execução deve possuir um *Model Card* canônico em formato JSON/Markdown:

### 2.1 Esquema Obrigatório de Metadados
```json
{
  "model_id": "datasenado-stance-linear-v1.0",
  "task": "legislative_opinion_stance_classification",
  "architecture": "regularized_logistic_with_platt_scaling",
  "created_at_utc": "2026-11-05T12:00:00Z",
  "code_commit_sha": "7af3548b",
  "training_data": {
    "dataset_fingerprint_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "n_samples": 4200,
    "platforms_covered": ["youtube", "telegram", "x", "meta", "tiktok", "whatsapp"]
  },
  "validation_metrics_oof": {
    "macro_f1": 0.842,
    "mcc": 0.685,
    "cohen_kappa": 0.681,
    "brier_score": 0.112,
    "expected_calibration_error": 0.038
  },
  "rogan_gladen_matrix": {
    "sensitivity_per_class": [0.88, 0.82, 0.85],
    "specificity_per_class": [0.93, 0.91, 0.94],
    "youden_index_min": 0.73
  },
  "ethical_and_lgpd_considerations": {
    "pseudonymization": "HMAC-SHA256 with pepper key rotation",
    "pii_redaction_verified": true,
    "prohibited_use_cases": "Identificação nominal individual ou vigilância de cidadãos"
  }
}
```

---

## 3. Higiene do Ciclo de Vida e Política Zero-Footprint
- **Teto Efêmero:** O treinamento e a inferência devem respeitar o limite operacional de 250 MB em `/tmp/monitor_datasenado_cache`.
- **Limpeza Compulsória:** Ao término da execução ou ciclo de validação, qualquer arquivo temporário deve ser eliminado, assegurando **0 KB** de resíduo antes da verificação dos gates.
- **Rastreabilidade Git/Drive:** Model Cards e resumos executivos são sincronizados no repositório, enquanto dados Parquet pesados permanecem no Google Drive em mutação in-place.
