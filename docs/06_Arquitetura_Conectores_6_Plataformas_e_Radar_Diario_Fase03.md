# Arquitetura dos Conectores das 6 Plataformas, Radar Diário e Orquestração Parametrizada (Fase 03)

**Data de Emissão:** 05 de Novembro de 2026  
**Versão do Documento:** 1.0 (Fase 03 / Emenda Diretora v2.2)  
**Módulos de Referência:** `src/collectors/` e `src/storage/duckdb_medallion_lake.py`  
**Decisões Estratégicas:** `docs/05_Termo_de_Emenda_Diretora_v2_1_ADR007_a_ADR009.md` (`ADR-007` a `ADR-011`)  

---

## 1. Visão Geral e Princípios Arquiteturais

A Fase 03 consolida a expansão do **Monitor do Debate Público Digital** para uma cobertura holística e metodologicamente controlada de **6 plataformas digitais** (YouTube, Telegram, X/Twitter, Instagram/Facebook, TikTok e WhatsApp), respaldada pelas decisões da Emenda Diretora v2.2 (`ADR-007` a `ADR-011`).

### Princípios Cardeais da Arquitetura:
1. **Neutralidade Lexical Estrita (M-04):** Todas as coletas ativas utilizam exclusivamente os termos oficiais e descritivos pré-aprovados em `config/settings.yaml`, bloqueando compulsoriamente termos valorativos ou adjetivados;
2. **Antiviés Algorítmico Obrigatório (ADR-006):** Bloqueio sistemático via `ValueError` de qualquer ordenação baseada em relevância, engajamento ou popularidade (`sort_order="recency"`, `"time"`, `"date"`, `"reverse_chronological"`);
3. **Conformidade Ética e Resolução CNS 510/2016:** WhatsApp monitorado estritamente por ingestão passiva de exportações públicas;
4. **Extração Precoce de Proxy Geográfico e Pseudonimização Irreversível (LGPD Art. 13):** Telefones e identificadores brutos têm seus DDDs extraídos na ingestão e são imediatamente destruídos via `HMAC-SHA256` na Camada Bronze;
5. **Zero-Footprint em Disco:** Arquivos temporários e bancos analíticos locais operam em buffers isolados e são purgados com 0 KB residual.

---

## 2. Mapa dos Conectores das 6 Plataformas

```
                                 [ BaseLexicallyNeutralCollector ]
                                                 │
         ┌──────────────┬──────────────┬─────────┴────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼              ▼              ▼
   [ YouTube ]    [ Telegram ]    [ X/Twitter ]   [ Meta I/F ]   [ TikTok ]    [ WhatsApp ]
    Official       Channel /      API v2 Recency   Graph API /    Research      Passive Txt/
     API v3         Bot API        + JSON Exp.     Content Lib    API v2         JSON Parser
```

### 2.1. Conector X / Twitter (`XTwitterCollector`)
- **Módulo:** `src/collectors/x_twitter_collector.py`
- **Modalidade Oficial:** Endpoint `/2/tweets/search/recent` da API v2 do X.
- **Trava de Ordenação:** Exige estritamente `sort_order="recency"`. Qualquer outro valor lança `ValueError`.
- **Extração de Entidades:** Processa `entities.urls` (resolvendo `expanded_url`) e `entities.hashtags` (`tag`), associando a expansão `includes.users`.
- **Sinais de Bolhas/Espectros (`ADR-010`):** Mapeia `in_reply_to_user_id` e `referenced_tweets` para identificar o perfil expoente raiz (`exponent_seed_id`).

### 2.2. Conector Meta Instagram / Facebook (`MetaInstagramFacebookCollector`)
- **Módulo:** `src/collectors/instagram_facebook_collector.py`
- **Modalidade Oficial:** Meta Graph API v19.0 (`/{object_id}/comments`) e Meta Content Library.
- **Trava de Ordenação:** Exige `order in ("reverse_chronological", "chronological")`. Ordenações como `"ranked"` e `"toplevel"` são rejeitadas.
- **Reparo de Mojibake UTF-8 (`fix_meta_mojibake_utf8`):** Tratamento determinístico para o defeito de codificação nativo de exportações da Meta (onde bytes UTF-8 são lidos como Latin-1).

### 2.3. Conector TikTok (`TikTokResearchCollector`)
- **Módulo:** `src/collectors/tiktok_collector.py`
- **Modalidade Oficial:** TikTok Research API para pesquisadores acadêmicos e institucionais (`/v2/research/video/comment/list/`).
- **Trava de Ordenação:** Exige `order in ("create_time", "time")`, rejeitando ordenações por curtidas ou relevância algorítmica.
- **Tratamento Temporal:** Converte `create_time` (epoch seconds) diretamente para `datetime` com fuso horário UTC.

### 2.4. Conector WhatsApp de Grupos Públicos (`WhatsAppPublicGroupsExportCollector`)
- **Módulo:** `src/collectors/whatsapp_collector.py`
- **Modalidade Ética:** Ingestão passiva de arquivos de exportação `.txt` e `.json` de grupos públicos temáticos (sem automação de sessão pessoal).
- **Parser Multi-Plataforma:** Suporta nativamente exportações Android (`DD/MM/YYYY HH:MM - Remetente: Texto`) e iOS (`[DD/MM/YYYY, HH:MM:SS] Remetente: Texto`), com suporte a mensagens multilinhas.
- **Filtragem de Sistema:** Descarta automaticamente mensagens de criptografia ponta a ponta, entradas e saídas de membros e avisos de mídia oculta.
- **Extração Precoce de DDD (`phone_or_location_hint`):** Quando o remetente é um número de telefone (`+55 61 ...`), o DDD é extraído para metadados geográficos antes que o texto passe pela redação PII e o autor seja convertido em hash HMAC-SHA256.

### 2.5. Conectores YouTube e Telegram (Consolidados na Fase 02)
- Mantidos em plena operação: `YouTubeOfficialCollector` (`src/collectors/youtube_collector.py`) com trava `date`/`time` e resiliência a comentários desativados; e `TelegramPublicChannelCollector` (`src/collectors/telegram_collector.py`) com parsing polimórfico de exportações desktop e Bot API.

---

## 3. Coletor de Panorama Diário Aberto (Radar do Senado — ADR-008 Modo 2)

O módulo `src/collectors/daily_radar_collector.py` implementa a classe `DailyLegislativeRadarCollector`:
- **Catálogo Temático das Comissões (`SENATE_COMMITTEES_LEXICON`):** Mapeia o vocabulário e matérias de competência da `CAS`, `CCT`, `CAE`, `CCJ`, `CMA`, `CE` e `CSP`;
- **Varredura Cronológica (`scan_daily_dominant_topics`):** Analisa o lote diário misto de manifestações das 6 plataformas, agrupa por tópicos emergentes e calcula:
  - `total_posts` e `unique_accounts_estimate`;
  - `share_of_day_pct` (% de dominância no dia);
  - `senate_interest_flag` (`True` quando aderente a competências do Senado Federal);
  - `matched_senate_committees` (comissões competentes para apreciar o tema);
  - `legislative_relevance_score` e `recommended_collection_queries` (termos neutros sugeridos para abertura de monitoramento amostral).

---

## 4. Orquestrador Parametrizado (`MonitoringWindowSpec`) e Dossiê Descritivo SQL

O orquestrador `Phase03SixPlatformsOrchestrator` (`src/collectors/phase03_six_platforms_orchestrator.py`) introduz o contrato formal de parametrização:

### 4.1. Estrutura do `MonitoringWindowSpec`
```python
@dataclass
class MonitoringWindowSpec:
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    window_days: Optional[int] = None
    window_weeks: Optional[int] = None
    window_months: Optional[int] = None
    selected_platforms: List[str] = field(default_factory=lambda: ["youtube", "telegram", "x_twitter", "instagram_facebook", "tiktok", "whatsapp"])
    max_manifestations_per_platform: Optional[int] = None
    max_total_manifestations: Optional[int] = None
    target_sample_size_n: Optional[int] = None
```

### 4.2. Dossiê de Estatísticas Descritivas SQL
Consultas analíticas executadas diretamente sobre o DuckDB:
1. `funnel_summary`: Funil contábil da ingestão à amostra representativa final;
2. `by_platform_breakdown`: Volume bruto, spam, CIB e divisão de posicionamento por rede social;
3. `by_day_timeseries`: Linha do tempo diária com contagem de manifestações, ataques CIB interceptados e saldo de posicionamento;
4. `by_shift_breakdown` e `by_macroregion_breakdown`: Distribuição temporal por turnos e geográfica por macrorregiões do IBGE;
5. `by_digital_spectrum_and_bubbles_summary` (`ADR-010`): Análise comportamental por espectro político-discursivo com identificação de `first_seen_utc` (qual espectro pautou o debate primeiro);
6. `ecosystem_360_interop_contract` (`ADR-011`): Contrato padronizado com chaves universais para integração com inteligência editorial, buscas e pesquisas do DataSenado.

---

## 5. Garantias de Segurança e Zero-Footprint

- **Zero Resíduos em Disco:** O pipeline orquestrado limpa e purga todos os bancos temporários no fechamento dos blocos `with`, garantindo rigorosamente **0 KB** de resíduos em `/tmp/monitor_datasenado_cache`;
- **Imutabilidade da Fase 01:** A integridade dos 16 arquivos da Fase 01 permanece validada criptograficamente via `Phase01BaselineGuard`.
