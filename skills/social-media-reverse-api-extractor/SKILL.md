---
name: social-media-reverse-api-extractor
description: Use this skill when extracting social media data (posts, metrics, profiles, search results) from platforms without official/free APIs (e.g. X/Twitter, LinkedIn, Threads, Instagram, TikTok) via reverse-engineered internal endpoints, HAR logs, or DevTools network traffic.
---

# Extração de Dados de Redes Sociais via APIs Reversas

Protocolo operacional para interceptar, higienizar e automatizar a coleta de dados de redes sociais a partir de suas APIs internas (Fetch/XHR/GraphQL), contornando paywalls de APIs oficiais com segurança de sessão e zero overhead.

<objective>
Capacitar o agente a mapear endpoints internos de plataformas sociais, isolar parâmetros e headers essenciais, reproduzir requisições autenticadas de forma leve (cURL/Python) e estruturar os payloads JSON resultantes para os pipelines de dados do projeto.
</objective>

<instructions>
1. **Fase de Mapeamento e Captura**:
   - Abrir a rede social alvo em navegador autenticado com a conta de monitoramento.
   - Acessar o DevTools (F12) -> aba "Network" (Rede) -> filtrar por "Fetch/XHR".
   - Executar a ação desejada na interface (ex: carregar feed, pesquisar palavra-chave, rolar perfil).
   - Identificar a requisição principal que retorna a lista ou métricas em JSON puro (frequentemente graphql, timeline, feed ou search).
   - Clicar com botão direito na requisição -> "Copy as cURL" ou exportar o tráfego como arquivo .har.

2. **Fase de Higienização de Cabeçalhos (Strip Noise)**:
   - Eliminar headers supérfluos de telemetria, anúncios e navegador (ex: sec-ch-ua, referer, accept-language).
   - Reter estritamente:
     * Endpoint URL e Método (GET ou POST).
     * Cabeçalho de Autorização / Bearer (se estático da aplicação).
     * Cookies de Sessão essenciais (ex: auth_token, ct0, li_at, sessionid).
     * Tokens anti-CSRF exigidos pela plataforma (ex: x-csrf-token).
     * Query Parameters e Payload JSON (especialmente paginação: cursor, count, offset).

3. **Fase de Teste e Validação da Resposta**:
   - Executar uma chamada de teste controlada usando curl isolado.
   - Confirmar se o status HTTP retornado é 200 e se o corpo contém a árvore de dados esperada.
   - Mapear o schema JSON (campos de autor, texto, timestamp, engajamento e métricas).

4. **Fase de Automação e Integração**:
   - Encapsular a requisição em um script leve (shell/curl ou módulo do projeto).
   - Implementar paginação incremental consumindo o token/cursor do último post coletado.
   - Normalizar os dados para o schema de ingestão do banco de dados/Data Lake do projeto.
</instructions>

<constraints>
- NUNCA realizar requisições em rajada (high-frequency burst). Respeitar intervalo mínimo com jitter aleatório (3 a 10 segundos entre requisições; 5 a 15 minutos entre varreduras de monitoramento) para evitar bloqueio de IP ou rate limit.
- NUNCA expor credenciais, cookies de sessão ou tokens de autenticação em código versionado no repositório. Utilizar variáveis de ambiente (.env).
- NUNCA armazenar dados brutos de telemetria ou cookies pessoais em logs de auditoria ou no chat do agente.
- Proibido simular ações de escrita (postar, curtir, seguir) através deste protocolo. O escopo é estritamente LEITURA e MONITORAMENTO de dados públicos ou autorizados.
</constraints>

<output_format>
Ao documentar ou entregar a extração de uma nova rede, apresente:
1. Endpoint Canônico: URL base, método e propósito da chamada.
2. Headers Mínimos Necessários: Lista restrita dos cabeçalhos obrigatórios.
3. Payload / Parâmetros: Mapeamento dos filtros e cursor de paginação.
4. Schema Resumido: Dicionário com os campos extraídos (ID, autor, data, texto, métricas).
5. Script de Teste cURL: Comando pronto para teste de conectividade.
</output_format>

<error_handling>
- HTTP 401 / 403 (Unauthorized / Forbidden): Sessão ou cookie expirado. Notificar a necessidade de renovação do cookie ou verificar se o header anti-CSRF mudou.
- HTTP 429 (Too Many Requests): Rate limit atingido. Interromper imediatamente o coletor, acionar backoff exponencial (espera mínima de 15 a 30 minutos) e registrar o alerta.
- HTTP 200 com Payload Vazio ou Erro de Schema: Mudança estrutural no frontend da plataforma. Reabrir o DevTools para inspecionar a nova nomenclatura do endpoint ou hash de query.
</error_handling>
