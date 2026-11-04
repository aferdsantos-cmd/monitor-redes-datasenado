# Âncora de Negócio (Owner's Intent), Gestão de Riscos (ISO 31000) e Matriz de Severidade

Este documento formaliza as diretrizes institucionais e epistemológicas que regem as auditorias do projeto **Monitor do Debate Público Digital (TCC Ciência de Dados & DataSenado)**, fundamentadas no **IPPF/GIAS (IIA)**, **ISO 31000:2018 (Gestão de Riscos)** e **ISO 9001:2015 (Sistemas de Gestão da Qualidade)**.

---

## 1. Declaração da Intenção do Proprietário (*Owner's Intent* — Horizonte Duplo)

A premissa fundamental da Auditoria Sênior orientada ao negócio é a distinção clara entre o que é mandatório para a conclusão e defesa do **TCC Acadêmico (Horizonte H1)** e o que constitui requisito de produção para a **Futura Implantação Institucional no DataSenado (Horizonte H2)**. 

Auditores que não observam essa fronteira incorrem no vício metodológico de exigir infraestruturas corporativas de missão crítica em projetos de pesquisa individual em hardware pessoal, gerando "falsos achados" que paralisam o desenvolvimento.

### Tabela Comparativa: Horizonte H1 (TCC) vs. Horizonte H2 (DataSenado)

| Dimensão | Horizonte H1: TCC Acadêmico (Imediato) | Horizonte H2: DataSenado (Futuro Roadmap) | Classificação de Achados em H1 |
| :--- | :--- | :--- | :--- |
| **Escopo de Plataformas (`ADR-006`)** | 6 Plataformas obrigatórias: YouTube, Telegram, X, Instagram/Facebook, TikTok, WhatsApp. Demonstração de viabilidade técnica e multi-rede. | Plataformas selecionadas conforme convênios oficiais e termos de serviço institucionais. | **Invariante do H1:** Tentar cortar qualquer uma das 6 plataformas é **Fora de Escopo (Falso Achado)**. |
| **Infraestrutura de Armazenamento** | *Zero-Footprint* local (`/tmp` $\le 250\text{ MB}$) com persistência em nuvem pessoal (Google Drive via CLI standalone) com atualização in-place (`mutate update`). | Cluster corporativo on-premise no Senado Federal, buckets S3/MinIO dedicados e backups imutáveis WORM. | Exigir S3/MinIO ou servidores dedicados no H1 é **Recomendação H2**, jamais Determinação. |
| **Hardware & Ferramentas de Desenvolvimento** | macOS (MacBook Air/Pro) com 28 GB de disco livre, sem Xcode CLT (~2.5 GB), executando exclusivamente via `uv` standalone. | Ambientes Linux conteinerizados (Docker/Kubernetes), CI/CD corporativo e runners dedicados do Senado. | Exigir Xcode CLT ou orquestradores de contêineres é **Violação de Invariante H1**. |
| **Estimando & Validade Amostral** | Inferência circunscrita ao Universo Finito Observado de Contas Orgânicas Digitais ($\mathcal{U}_{\text{Org}, T}$) ativas sobre a matéria legislativa $T$. | Pesquisas de opinião representativas da população nacional brasileira (pesquisas CATI probabilísticas domiciliares/telefônicas). | Exigir que a amostra de redes reflita a população brasileira geral é **Falso Achado Epistemológico**. |
| **Tratamento de Dados & LGPD** | Anonimização/pseudonimização via `HMAC-SHA256` (*salt* efêmero), retenção zero de texto bruto não agregado pós-análise. | Termo de Ajustamento de Conduta e governança formal de Encarregado de Proteção de Dados (DPO/Senado). | Desrespeito ao `raw_author_id=None` é **🚨 Determinação Bloqueante**. Falta de DPO institucional é **⚠️ Recomendação H2**. |
| **Custos de Operação** | Custo financeiro zero (APIs públicas/gratuitas, planos acadêmicos, bibliotecas abertas). | Orçamento público licitado (APIs Enterprise, contratos de dados comerciais). | Propor contratação de serviços pagos no H1 é **Proibido (*Dead End*)**. |

### Restrições Imutáveis do Proprietário (`ADR-001` a `ADR-006`)
Qualquer achado de auditoria que viole diretamente as decisões registradas em ADRs será descartado de plano pelo Cérebro:
1. **`ADR-001` (Zero-Footprint):** Não armazenar dados brutos ou bancos persistentes na árvore do repositório local.
2. **`ADR-002` (DuckDB + Parquet ZSTD):** Processamento colunar analítico em memória/cache efêmero `/tmp/monitor_datasenado_cache`.
3. **`ADR-003` (HMAC-SHA256 Salt Efêmero):** Pseudonimização irreversível em trânsito com descarte de chaves em modo *fail-closed*.
4. **`ADR-004` (Amostragem Hamilton + Rogan-Gladen):** Alocação inteira exata e correção analítica de classificação ruidosa.
5. **`ADR-005` (Sincronização GitHub via Git Data API):** Sincronização atômica remota sem o binário pesado do Xcode CLT.
6. **`ADR-006` (Cobertura Multiplataforma Integrada):** Manutenção expressa das 6 plataformas de debate digital.

---

## 2. Matriz de Severidade e Risco (ISO 31000 & IIA IPPF)

Conforme a norma **ISO 31000:2018 (Cláusulas 5.4 e 6.4 — Avaliação de Riscos)**, todo achado deve ser classificado pelo cruzamento entre **Impacto no Negócio** e **Probabilidade/Materialidade**:

```
+-----------------------------------------------------------------------------------------+
|                               MATRIZ DE RISCO ISO 31000                                 |
+---------------------+-------------------------------+-----------------------------------+
| IMPACTO NO NEGÓCIO  | ALTA PROBABILIDADE / EVIDÊNCIA| MÉDIA/BAIXA PROBABILIDADE         |
+---------------------+-------------------------------+-----------------------------------+
| CRÍTICO (Bloqueia   | 🚨 DETERMINAÇÃO BLOQUEANTE    | 🚨 DETERMINAÇÃO BLOQUEANTE        |
| H1: TCC / Matemática| (Correção imediata requerida; | (Correção preventiva mandatória;  |
| / LGPD / Segurança) | Retém aprovação da entrega)   | Retém aprovação da entrega)       |
+---------------------+-------------------------------+-----------------------------------+
| MODERADO (Melhoria  | ⚠️ RECOMENDAÇÃO H1/H2         | ⚠️ RECOMENDAÇÃO H2                |
| de Performance /    | (Otimização técnica para      | (Item do roadmap de migração      |
| Arquitetura Futura) | execuções futuras)            | para o Senado Federal)            |
+---------------------+-------------------------------+-----------------------------------+
| INEXISTENTE (Contra | ⛔ FORA DE ESCOPO / DESCARTADO| ⛔ FORA DE ESCOPO / DESCARTADO    |
| a Intenção do Dono) | (Falso achado desconsiderado) | (Falso achado desconsiderado)     |
+---------------------+-------------------------------+-----------------------------------+
```

### Critérios Objetivos de Triagem por Pilar

#### A. Pilar Acadêmico e Metodológico
- **🚨 Determinação:** Estimando formal ausente ou em contradição matemática com o código; alegação de generalização populacional brasileira (violação de Bethlehem, 2010); violação da Resolução CNS nº 510/2016 (ausência de enquadramento de dispensa ética); DOIs inexistentes ou incorretos em citações canônicas.
- **⚠️ Recomendação:** Adição de comparações com novas publicações recentes; ampliação de seções de discussão; refinamento de paleta de cores para daltonismo (Okabe-Ito).
- **⛔ Descartado:** Exigir aprovação de CEP/CONEP para dados agregados públicos de rede social sem identificação pessoal.

#### B. Pilar Estatístico e Econométrico
- **🚨 Determinação:** Alocação de Hamilton com soma diferente de $n$ ($\sum n_h \neq n$); fórmula de Rogan-Gladen com viés em valores extremos de prevalência aparente ($AP$ fora de limites); falha no seed locking impedindo reprodutibilidade exata; pesos de calibração Raking fora do intervalo simplex viável $[0.25, 4.00]$ gerando variância descontrolada.
- **⚠️ Recomendação:** Inclusão de testes adicionais de robustez em R (`svychisq` Rao-Scott de 2ª ordem); modelagem causal com *staggered rollouts* (Callaway & Sant'Anna) para análises de longo prazo.
- **⛔ Descartado:** Exigir amostragem probabilística domiciliar aleatória para dados nativamente observacionais de redes digitais.

#### C. Pilar de Engenharia de Software e Segurança
- **🚨 Determinação:** Primitivas inseguras detectadas por SAST (`eval`, `exec`, `pickle.loads`, `shell=True`); vazamento de segredos, tokens ou dados pessoais em logs ou no GitHub; estouro de cache efêmero acima de 250 MB; teste unitário quebrado no `pytest`.
- **⚠️ Recomendação:** Otimização de tempos de deserialização DuckDB; paralelização de chamadas assíncronas I/O; redução de overhead de strings.
- **⛔ Descartado:** Exigir instalação de Xcode CLT, Kubernetes, Docker Desktop, Apache Spark ou serviços de nuvem paga incompatíveis com o MacBook de 28 GB.

---

## 3. Diretriz "No Dead Ends" (Orientação a Soluções Pragmáticas)

Em conformidade com as melhores práticas de auditoria operacional do **TCU (Tribunal de Contas da União)** e do **IIA**, nenhum achado pode consistir em mera crítica ou apontamento de gargalo sem que o auditor forneça uma **contraproposta tecnicamente viável e implementável** dentro do ecossistema real do auditado.

### Matriz de Contrapropostas: O que é Proibido (*Dead End*) vs. O que é Exigido

| Categoria | ❌ Contraproposta Proibida (*Dead End*) | ✅ Contraproposta Pragmática Exigida pela Skill |
| :--- | :--- | :--- |
| **Detecção de Redes Coordenadas** | *"O cálculo de similaridade $O(N^2)$ é pesado demais, contrate um cluster Spark na nuvem."* | *"Implemente agrupamento temporal em janela deslizante two-pointer combinado com MinHash LSH ($O(N \log N + N \cdot k)$) no DuckDB local."* |
| **Limitação de Memória / Disco** | *"250 MB é insuficiente para Big Data; compre um HD externo ou máquina de 64 GB de RAM."* | *"Comprima os lotes em Parquet com codec ZSTD level 3 e faça descarregamento atômico streaming no Google Drive via mutate update."* |
| **Coleta de Redes Sociais** | *"APIs oficiais são caras ou fecharam; abandone a coleta do X e Telegram no TCC."* | *"Utilize endpoints acadêmicos, webhooks controlados e exportações legítimas de dados conforme especificado no ADR-006."* |
| **Validação Estatística em R** | *"Instale um servidor RStudio Server corporativo com pacotes de inferência causal."* | *"Gere scripts canônicos autônomos em R usando bibliotecas survey e arrow para execução via Rscript local ou Google Colab gratuito."* |
| **Auditoria e Qualidade** | *"Instale o SonarQube Enterprise e dependências pesadas de Java/Node."* | *"Execute a varredura SAST nativa e o gerador de Working Papers audit_working_papers_hasher.py em Python leve via uv."* |
