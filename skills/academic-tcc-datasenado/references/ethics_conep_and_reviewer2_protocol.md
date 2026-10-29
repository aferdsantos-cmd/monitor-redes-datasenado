# Ética em Pesquisa (CONEP/LGPD), Integridade Científica e Protocolo "Reviewer 2"

Este documento estabelece o enquadramento ético regulatório brasileiro, os protocolos de integridade textual e a rubrica de auditoria adversária (*Reviewer 2*) para blindagem do TCC e relatórios do DataSenado.

---

## 1. Enquadramento Regulatório Ético no Brasil: Resolução CNS nº 510/2016

### 1.1. Fundamentação da Dispensa de Submissão ao Sistema CEP/CONEP
O monitoramento do debate público digital observativo conduzido neste projeto está **formalmente dispensado de registro e avaliação pelo sistema CEP/CONEP (Comitês de Ética em Pesquisa / Comissão Nacional de Ética em Pesquisa)**, com base estrita no **Artigo 1º, Parágrafo Único da Resolução CNS nº 510/2016 do Conselho Nacional de Saúde**:

> *"Não serão registradas nem avaliadas pelo sistema CEP/CONEP:*
> - *II – pesquisa que utilize informações de acesso público, nos termos da Lei nº 12.527, de 18 de novembro de 2011;*
> - *III – pesquisa que utilize informações de domínio público;*
> - *V – pesquisa com bancos de dados, cujas informações são agregadas, sem possibilidade de identificação individual."*

### 1.2. Harmonização com a LGPD (Lei Geral de Proteção de Dados — Lei nº 13.709/2018)
O tratamento de dados pessoais no âmbito da pesquisa fundamenta-se nos seguintes dispositivos:
- **Base Legal (Art. 7º, IV):** Tratamento realizado por órgão de pesquisa para a realização de estudos, garantida, sempre que possível, a anonimização ou pseudonimização dos dados pessoais.
- **Pseudonimização Criptográfica Imediata (Art. 13, §4º):**
  - Aplicação compulsória de `HMAC-SHA256` fail-closed na ingestão;
  - Descarte definitivo do identificador original em memória (`raw_author_id = ""`);
  - Truncamento de timestamps à hora no dataset exportado;
  - Custódia estrita do segredo de HMAC em variável de ambiente `.env`, fora do controle de versão.

### 1.3. Gatilhos de Alerta Ético e Proteção contra Busca Reversa (Markham, 2012)
- **Vulnerabilidade de Busca Reversa (*Reverse Searchability*):** A publicação de citações textuais literais de cidadãos comuns permite que qualquer usuário localize o perfil pessoal do autor através de motores de busca das plataformas, violando sua privacidade.
- **Regra de Conduta:** É terminantemente proibido publicar textos literais de cidadãos comuns (usuários não verificados ou sem notoriedade pública). Exige-se o uso de **paráfrase ética (*ethical fabrication / bricolage*)**, consolidando argumentos sem reproduzir strings literais identificáveis.
- **Gatilho Bloqueante:** Caso o pesquisador decida aplicar questionários ativos, testes de intervenção comportamental ou coletar dados em grupos privados/fechados de mensageria, o projeto perde a dispensa da Resolução 510/2016 e exige submissão prévia via Plataforma Brasil.

---

## 2. Integridade Científica, Paráfrase e Prevenção de Plágio

1. **Proibição de *Patchwriting*:** Não basta substituir palavras esparsas por sinônimos mantendo a estrutura sintática original de artigos de terceiros. A escrita científica exige assimilação conceitual e redação com voz autoral autêntica, atribuindo explicitamente as ideias seminais aos autores originais.
2. **Atribuição Multifonte:** Toda afirmação de fato ou revisão de literatura deve sintetizar a convergência ou divergência entre múltiplos autores canônicos (ex.: contrastar os limites do Big Data em Meng, 2018 com as recomendações de amostragem não-probabilística em Baker et al., 2013).

---

## 3. Simulador Adversário: O Protocolo "Reviewer 2" (Banca Examinadora)

Antes de submeter qualquer capítulo do TCC ou boletim técnico à auditoria ou publicação, o texto deve ser submetido ao seguinte checklist de 10 perguntas implacáveis:

1. ⚖️ **Fronteira Populacional:** O texto escorregou em algum parágrafo para a expressão *"a opinião dos brasileiros"* em vez de *"o universo observado de contas digitais orgânicas"*?
2. 🎯 **Identificação do Estimando:** O estimando $\theta_T$ está claramente formalizado como proporção sobre $\mathcal{U}_{\text{Org}, T}$ e acompanhado de sua unidade observacional (`1 Conta Orgânica por Plataforma`)?
3. 📉 **Incerteza Amostral:** As proporções estão sempre acompanhadas de intervalos de confiança empíricos (Bootstrap 95%) e do tamanho efetivo de amostra $n_{\text{eff}}$?
4. 🤖 **Justificativa da Detecção de CIB:** O método de detecção de redes coordenadas demonstrou controle contra falsos positivos em notícias virais (allowlist jornalística e exigência de repetição de co-ocorrência)?
5. 🔄 **Tratamento do Cenário 3:** A discrepância entre o Cenário 1 e o Cenário 3 foi interpretada corretamente como análise de sensibilidade sob ignorabilidade condicional, e não como *"a verdade corrigida"*?
6. 🔬 **Correção do Classificador:** A taxa de sensibilidade e especificidade do classificador de linguagem natural foi reportada e ajustada pela fórmula de Rogan & Gladen?
7. 📚 **Rastreabilidade de Citações:** Todas as citações no texto constam na lista de referências bibliográficas com DOI válido e verificado?
8. 🏛️ **Normas ABNT:** As citações autor-data entre parênteses estão em minúsculas conforme a norma atualizada ABNT NBR 10520:2023 (ex.: `(Meng, 2018)`)?
9. 🛡️ **Privacidade LGPD:** Nenhuma string literal de postagem de cidadão comum ou dado pessoal identificável foi exposto sem agregação ou paráfrase?
10. 📊 **Higiene Visual:** Foram evitados gráficos de pizza, efeitos 3D ou eixos distorcidos, garantindo paleta acessível a daltônicos (Okabe-Ito)?
