# Termo de Emenda Diretora v2.2 — Registros de Decisão de Arquitetura (ADR-007 a ADR-011)

**Data de Emissão:** 05 de Novembro de 2026  
**Status:** Aprovado pela Gestão / Homologado pelo Proprietário  
**Referência Metodológica:** `docs/01_Metodologia_Cientifica_e_Estatistica_NotebookLM.md` c/c `docs/03_Termo_de_Emenda_Plano_v1_1_e_ADR.md`  
**Destinatários:** Equipe de Ciência de Dados, Consultoria Legislativa e Auditoria DataSenado  

---

## 1. Contexto e Motivação da Emenda Diretora

A evolução do Monitor do Debate Público Digital para a **Fase 03** consolidou a necessidade de formalizar as diretrizes estratégicas e metodológicas emanadas da Gestão do Projeto e do Proprietário institucional (DataSenado).

O presente termo estende o arcabouço de governança já estabelecido pelos ADRs 001 a 006, registrando as decisões arquiteturais **`ADR-007` a `ADR-011`**, que balizam a expansão para **6 plataformas digitais**, a introdução da **Dupla Modalidade Operacional (Monitoramento Temático vs. Radar Diário do Senado)**, a inteligência mista de **Bolhas e Espectros Políticos**, e a interoperabilidade futura com o **Ecossistema 360º de Dados**.

---

## 2. Registro de Decisões de Arquitetura (ADR-007 a ADR-011)

### ADR-007: Produto Interno de Bancada Analítica para Servidores do DataSenado

- **Status:** Aprovado / Inegociável
- **Contexto:** Havia incerteza sobre se o sistema deveria prover uma interface web pública de autoatendimento para cidadãos em tempo real ou se deveria ser uma ferramenta interna de bancada.
- **Decisão:**
  1. O sistema é concebido estritamente como um **software de bancada analítica de uso interno e restrito aos servidores e pesquisadores do DataSenado**;
  2. O produto externo entregue à sociedade brasileira, aos parlamentares e à imprensa consiste exclusivamente nos **Boletins Técnicos, Relatórios Metodológicos e Notas Analíticas** emitidos pelo Instituto após o encerramento, auditoria e validação de cada ciclo amostral;
  3. Não haverá painel web aberto ou endpoint de consulta pública desprovido de rigor amostral ou sem o processo de calibração estatística (Raking IPF e FPC).
- **Consequências:** Foco máximo na robustez metodológica, no isolamento de dados locais (política Zero-Footprint) e na segurança jurídica e ética (LGPD Art. 13 e Resolução CNS 510/2016).

---

### ADR-008: Dupla Modalidade Operacional Parametrizável (Monitoramento Temático vs. Radar Diário de Pautas)

- **Status:** Aprovado / Implementado na Fase 03
- **Contexto:** As demandas legislativas do Senado Federal dividem-se em dois tipos fundamentais: (a) o acompanhamento longitudinal e amostralmente representativo de uma matéria pré-definida em tramitação (ex.: PL 2338 ou PEC 6x1); e (b) a identificação ágil e exploratória das pautas que ganharam tração nas redes sociais no dia a dia.
- **Decisão:** O sistema deve operar nativamente sob **duas modalidades operacionais**:
  1. **Modalidade 1 — Monitoramento Temático Parametrizável (Contrato `MonitoringWindowSpec`):**
     - Permite parametrizar a coleta por recorte temporal flexível (dias específicos, semanas inteiras, meses ou datas absolutas de tramitação legislativa);
     - Permite selecionar plataformas específicas (todas as 6 redes ou qualquer subconjunto, como YouTube + WhatsApp);
     - Permite fixar tetos de volume bruto e limites do tamanho da amostra representativa sorteada na Camada Gold ($n$).
  2. **Modalidade 2 — Radar Diário de Pautas do Senado Federal (`DailyLegislativeRadarCollector`):**
     - Varredura exploratória cronológica do dia em curso para mapear os temas dominantes nas redes;
     - Triagem e cruzamento automático com o vocabulário temático e competências das **Comissões Permanentes do Senado Federal** (`CAS`, `CCT`, `CAE`, `CCJ`, `CMA`, `CE`, `CSP`);
     - Geração de escores de relevância legislativa e recomendação automática de termos de busca neutros caso o DataSenado decida abrir um Monitoramento Temático (Modalidade 1) sobre a matéria.
- **Consequências:** Flexibilidade operacional total para a equipe analítica do Senado sem comprometer o rigor inferencial.

---

### ADR-009: Emissão de Relatórios Analíticos em Formato Microsoft Word (.docx) na Fase 06

- **Status:** Aprovado / Previsto para a Fase 06
- **Contexto:** Os fluxos de trabalho da Consultoria Legislativa e do DataSenado exigem a edição, revisão textual colaborativa e diagramação institucional dos relatórios finais antes de sua publicação oficial em PDF.
- **Decisão:**
  1. Na **Fase 06**, o sistema incluirá um motor de exportação de relatórios finais no formato nativo **Microsoft Word (`.docx`)**;
  2. O arquivo `.docx` conterá o template visual do DataSenado, tabelas de estatísticas descritivas pré-formatadas, sumários do funil de integridade e gráficos analíticos em alta resolução embutidos;
  3. Fica assegurada cláusula de flexibilidade metodológica para que a estrutura das seções do documento Word seja ajustada com a equipe do DataSenado durante a execução da Fase 06.
- **Consequências:** Perfeita aderência ao fluxo editorial dos servidores públicos, eliminando retrabalho de formatação manual.

---

### ADR-010: Inteligência Mista de Bolhas Digitais (Não Supervisionada) e Espectros Políticos (Supervisionada por Expoentes-Semente)

- **Status:** Aprovado / Em vigor a partir da Fase 03
- **Contexto:** O debate público nas redes sociais é caracterizado pela polarização e pela formação de câmaras de eco. O DataSenado necessita compreender não apenas a opinião média geral, mas também a dinâmica discursiva entre os diferentes espectros e bolhas digitais.
- **Decisão:** O monitoramento adotará uma abordagem híbrida de inteligência de redes:
  1. **Componente Não Supervisionado (Detecção de Bolhas Orgânicas):** Algoritmos de grafos baseados em co-engajamento, LSH e particionamento comunitário (Leiden com modularidade $Q$) para revelar aglomerados orgânicos e ecossistemas isolados de opinião;
  2. **Componente Supervisionado / Semi-Supervisionado (Espectros e Expoentes-Semente):**
     - Monitoramento e indexação de **Expoentes-Semente Públicos** representativos dos diferentes polos político-discursivos (ex.: espectro progressista, conservador, centro institucional, técnico-setorial);
     - Análise de reação de cada espectro à matéria em tramitação;
     - Identificação de **qual espectro pautou a matéria primeiro** (`first_seen_utc`);
     - Medição de convergências e **pontes de consenso inter-espectros** em matérias de interesse nacional;
  3. **Conformidade Ética e LGPD:** Todas as contas de cidadãos que interagem nas publicações dos expoentes são imediatamente pseudonimizadas via `HMAC-SHA256` na Camada Bronze, preservando o anonimato individual e analisando estritamente os padrões agregados de rede.
- **Consequências:** Capacidade de gerar análises aprofundadas com alto valor agregado para o processo legislativo.

---

### ADR-011: Arquitetura Plugável para o Futuro "Ecossistema de Inteligência de Dados e Informações 360º"

- **Status:** Aprovado / Contrato de Interoperabilidade Ativo
- **Contexto:** O monitoramento de redes sociais constitui o primeiro pilar de uma visão institucional integrada de inteligência de dados idealizada pelo DataSenado.
- **Decisão:**
  1. A arquitetura dos dados da Fase 03 deve expor um contrato explícito de interoperabilidade (`ecosystem_360_interop_contract`);
  2. O sistema fornecerá chaves e dimensões universais de acoplamento:
     - `theme_id` e `senate_committee` (tema legislativo e comissão competente);
     - `date_window_brt` (janela temporal harmonizada);
     - `shared_news_domains_ranking` (domínios de mídia mais compartilhados nas redes);
     - `active_spectra` (espectros ativos no debate);
  3. Esse contrato permitirá integrar futuramente:
     - **Pilar 2 — Inteligência Editorial e de Mídia:** Fatos noticiados, convergências, divergências, omissão seletiva, ordem dos fatos, enquadramento (*framing*), uso de adjetivação e pluralidade de fontes ouvidas;
     - **Pilar 3 — Medição de Buscas e Intenções:** Tendências de interesse ativo dos cidadãos em ferramentas de busca;
     - **Pilar 4 — Pesquisas de Opinião DataSenado:** Pesquisas probabilísticas por telefone com o método padrão-ouro do DataSenado.
- **Consequências:** O sistema nasce preparado para integrar uma plataforma unificada de inteligência informacional de 360 graus.

---

## 3. Conclusão e Vigência

As diretrizes dos ADRs 007 a 011 passam a ter força normativa imediata no repositório, regendo os conectores, o orquestrador, os esquemas de dados e a suíte de testes da Fase 03 em diante.
