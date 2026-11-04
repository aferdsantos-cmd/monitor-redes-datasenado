# Heurísticas de Testes Periciais de Campo (Fieldwork Testing Heuristics)

Guia de bolso da **IA Auditora Operacional** para execução pericial de testes de campo, inspeção de invariantes e coleta de evidências sem consumo excessivo de tokens.

---

## 1. Heurísticas de Campo — Pilar de Engenharia e Segurança

### 1.1. Aderência Estrita a `config/settings.yaml` (Sem Hardcoding)
- **O que inspecionar:** Todo limiar numérico, tolerância de convergência, bound de raking ou parâmetro de amostragem deve derivar de `src.config_loader.load_settings()`.
- **Como testar cirurgicamente:**
  1. Localize no mapa AST as classes de engine (`DigitalDiscourseStatisticalEngine`, `ObservedUniverseStratifiedSampler`).
  2. Leia as linhas de inicialização (`__init__`).
  3. Verifique se `self.cfg` é referenciado ou se constantes mágicas foram introduzidas no código.
- **Evidência típica:** Delta entre parâmetro injetado no YAML vs. valor lido na execução.

### 1.2. Higiene de Memória e Disco (*Zero-Footprint*)
- **O que inspecionar:** Arquivos temporários gerados em `/tmp/monitor_datasenado_cache/` não devem ultrapassar 250 MB durante o processamento e devem ser purgados após a mutação no Google Drive.
- **Como testar:**
  ```bash
  du -sk /tmp/monitor_datasenado_cache 2>/dev/null || echo "0 KB"
  ```
- **Arquivos Proibidos no Repositório:** Varra o repositório para assegurar que nenhum `.parquet`, `.duckdb` ou `secrets.yaml` foi commitado no Git.

### 1.3. Segurança LGPD e Pseudonimização Criptográfica
- **O que inspecionar:** A função de hashing de autores (`LGPDCleanerAndCIBGraphEngine.pseudonymize_author_id`) deve operar em modo **fail-closed**:
  - Salt ausente ou menor que 32 caracteres deve disparar `ValueError` imediato;
  - A saída deve ter exatamente 64 caracteres hexadecimais (SHA-256);
  - O campo de origem `raw_author_id` deve ser compulsoriamente nulo (`None`) no dataset final.

### 1.4. Scanner SAST de Primitivas Inseguras
- **O que inspecionar:** Código Python não deve conter `eval()`, `exec()`, `pickle.load()` ou `shell=True`.
- **Comando pericial:**
  ```bash
  grep -rnE '\b(eval\(|exec\(|pickle\.loads?|shell=True)\b' src/
  ```

---

## 2. Heurísticas de Campo — Pilar Estatístico e Amostral

### 2.1. Conservação da Soma na Alocação Estratificada de Hamilton
- **Invariante Matemática:** A soma dos tamanhos amostrais estratificados deve ser rigorosamente igual ao tamanho amostral total:
  $$\sum_{h=1}^L n_h = n$$
- **Como testar:** Verifique se o método de maiores restos de Hamilton foi utilizado para truncamento dos decimais e se `sum(allocations.values()) == target_n`.

### 2.2. Calibração Raking IPF (Iterative Proportional Fitting)
- **Limites de Peso (Trimming Bounds):** Os pesos finais calibrados $w_i$ devem obedecer estritamente aos limites do settings:
  $$w_i \in [w_{\min}, w_{\max}] = [0.25, 4.00]$$
- **Conservação de Massa:** A soma dos pesos deve reproduzir o tamanho total da população ou da amostra ($\sum w_i = n$).
- **Convergência:** O algoritmo deve reportar explicitamente o status de convergência (`converged: True` com tolerância $\le 10^{-4}$ em até 50 iterações).

### 2.3. Controle de Falsos Positivos e Correção de Rogan-Gladen
- **Taxa de Falsos Positivos ($FPR$):** Em detecção de anomalias/notícias virais, o FPR deve permanecer estritamente $\le 5.0\%$.
- **Rogan-Gladen:** Estimativas de prevalência de desinformação devem aplicar a correção epidemiológica de sensibilidade ($Se$) e especificidade ($Sp$):
  $$p_{\text{true}} = \frac{p_{\text{obs}} - (1 - Sp)}{Se + Sp - 1}$$

### 2.4. Detecção de Comportamento Inautêntico Coordenado (CIB)
- **Topologia de Rede:** Janela de sincronismo temporal $\Delta t \le 300\text{ s}$ e coeficiente de Jaccard de conteúdo $\ge 0.80$.
- **Momentos Distribucionais:** Assimetria (*skewness*), curtose (*kurtosis*), entropia de Shannon e contagem celular mínima esperada ($\ge 5$ para validade assintótica de $\chi^2$).

---

## 3. Heurísticas de Campo — Pilar Acadêmico e Documental

### 3.1. Alinhamento 1-para-1: Teoria vs. Código
- **O que inspecionar:** Cada equação numerada apresentada nos documentos de metodologia (`docs/01_Metodologia_Cientifica_Amostragem_Redes.md`) deve possuir uma implementação correspondente em `src/` com assinatura semântica idêntica.

### 3.2. Integridade de Citações e Verificação de DOIs
- **O que inspecionar:** Citações a artigos seminais (Deming, Cochran, Rogan-Gladen, etc.) devem referenciar DOIs válidos conforme a norma ISO 26324.
- **Comando pericial:**
  ```bash
  ./skills/academic-tcc-datasenado/scripts/verify_citations_doi.py
  ```

### 3.3. Limpeza Lexical e Moderação Epistêmica
- **O que inspecionar:** Nenhum documento acadêmico ou relatório de auditoria deve conter alegações generalistas sobre "toda a sociedade brasileira" ou termos epistemicamente inflacionados ("opinião pública nacional"). O objeto é exclusivamente o **Discurso Público Digital Observado** ($\mathcal{U}_{\text{Org}, T}$).
