import React, { useState } from 'react';
import {
  BookOpen,
  CheckCircle2,
  AlertOctagon,
  Scale,
  GraduationCap,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Binary,
  Microscope,
} from 'lucide-react';
import { ThemeDataset } from '../../types';

interface Module6Props {
  dataset?: ThemeDataset;
}

export const Module6MethodologyAndScience: React.FC<Module6Props> = ({ dataset }) => {
  const [activeSection, setActiveSection] = useState<'pipeline' | 'criteria' | 'bibliography' | 'boundaries'>('pipeline');
  const [expandedStep, setExpandedStep] = useState<number | null>(1);

  const pipelineSteps = [
    {
      step: 1,
      title: 'Coleta Neutra e Interoperável (Regra M-04)',
      layman: 'Para não enviesar a pesquisa desde o início, buscamos nas 6 redes sociais usando apenas termos neutros (como o número oficial da lei e o assunto), proibindo qualquer palavra que induza apoio ou rejeição (como "mito", "golpista" ou "corrupto"). Assim, garantimos que todos os lados do debate tenham a mesma chance de serem coletados.',
      math: 'A amostragem observacional opera sob o Universo Alvo U_Org restrito à taxonomia neutra T_leg. O operador de busca B(Q) satisfaz a invariante: interseção(Q, W_biased) = vazio, garantindo que a probabilidade inicial de captura não seja função do vetor de postura Y_i.',
      formula: 'Pr(Captura | Y_i = k) = Pr(Captura | Y_i = l),  ∀ k, l ∈ {Fav, Contr, Neut}',
    },
    {
      step: 2,
      title: 'Pseudonimização Criptográfica LGPD (Fail-Closed)',
      layman: 'Antes de qualquer análise, o sistema apaga nomes de usuários, telefones e links pessoais, substituindo-os por um código criptográfico único e anônimo. Os dados pessoais brutos nunca são salvos em disco nem expostos a terceiros, cumprindo com rigor a Lei Geral de Proteção de Dados.',
      math: 'O autor bruto a_i é mapeado deterministicamente via HMAC-SHA256 com chave K de entropia >= 256 bits mantida exclusivamente em memória volátil RAM. O registro resultante descarta o identificador original do autor e proíbe persistência em disco (Zero-Footprint).',
      formula: 'h_i = HMAC_{SHA256}(K, a_i),  com K ∈ {0,1}^{256} e a_i := None',
    },
    {
      step: 3,
      title: 'Expurgo de Robôs e Spam Comercial (Camada Silver)',
      layman: 'Identificamos e separamos robôs, contas falsas e mensagens que tentam vender produtos ou dar golpes usando a hashtag do projeto de lei como isca. Disparos repetidos em poucos segundos com o mesmo texto são enviados para quarentena.',
      math: 'Detecção de Comportamento Inautêntico Coordenado (CIB) via MinHash LSH (Jaccard >= 0.85 em janela delta t <= 10s) e coeficiente de Burstiness de Goh-Barabási B > 0.60. Quarentena preventiva de links comerciais via regex supervisionada.',
      formula: 'J(A, B) = |A ∩ B| / |A ∪ B| ≥ 0.85  e  B = (σ_τ - m_τ) / (σ_τ + m_τ) > 0.60',
    },
    {
      step: 4,
      title: 'Colapso por Conta Única: Princípio "1 Cidadão = 1 Voz"',
      layman: 'Se uma pessoa ou militante postar 500 vezes a mesma opinião, nós não contamos 500 votos. Todas as mensagens da mesma conta são consolidadas em uma única unidade. Isso impede que pequenos grupos ruidosos pareçam ser a maioria do debate.',
      math: 'Definição formal da unidade amostral elementar u_i = 1 correspondente a 1 conta orgânica única em U_Org. Se a conta produziu m_i postagens no período T, o peso base de Hájek é atribuído proporcionalmente a 1/m_i, anulando a inflação por hiperatividade.',
      formula: 'u_i = 1  e  d_i^{Hajek} = 1 / m_i,  com  ∑_{j=1}^{m_i} d_{ij} = 1',
    },
    {
      step: 5,
      title: 'Amostragem Estratificada de Neyman (27 UFs × 6 Redes)',
      layman: 'Sorteamos uma amostra representativa de 550 a 1.200 contas distribuídas entre as 6 plataformas e as regiões do país, garantindo precisão matemática e permitindo auditar os textos um a um.',
      math: 'Alocação ótima de Neyman n_h = n * (N_h * S_h) / ∑(N_k * S_k) sobre H = 30 estratos (6 plataformas × 5 macrorregiões IBGE). Cada unidade possui probabilidade de inclusão estritamente positiva π_i > 0.',
      formula: 'n_h = n · \\frac{N_h σ_h}{\\sum_{k=1}^H N_k σ_k},  com  π_i = n_h / N_h > 0',
    },
    {
      step: 6,
      title: 'Os Três Cenários de Ponderação e Calibração Raking IPF',
      layman: 'Apresentamos 3 cenários transparentes: o Cenário 1 reflete as contas que realmente falaram nas redes; o Cenário 2 equilibra o peso de cada rede; e o Cenário 3 ajusta a proporção regional para refletir o peso populacional do Censo IBGE em cada região do Brasil.',
      math: 'Algoritmo Iterative Proportional Fitting (IPF / Deming & Stephan, 1940) calibrando os pesos amostrais w_i para convergir aos totais marginais populacionais do IBGE/PNAD sob a restrição de simplex e truncamento de pesos de Kish w_i ∈ [0.25, 4.00].',
      formula: 'w_i^{(t+1)} = w_i^{(t)} · \\frac{T_m}{\\sum_{j ∈ S_m} w_j^{(t)}},  com  w_i ∈ [0.25, 4.00]',
    },
    {
      step: 7,
      title: 'Classificação PNL e Correção Oficial de Rogan-Gladen',
      layman: 'Nenhuma inteligência artificial acerta 100% das vezes. Por isso, medimos cientificamente a taxa de acerto da IA contra analistas humanos e aplicamos a fórmula clássica de Rogan-Gladen, que desconta matematicamente os erros da máquina antes de publicar o resultado oficial.',
      math: 'Estimador de prevalência corrigida de Rogan-Gladen (1978). Converte a prevalência aparente p_obs observada pelo classificador na prevalência verdadeira corrigida pelas taxas de Sensibilidade (Se) e Especificidade (Sp) obtidas em auditoria às cegas.',
      formula: '\\hat{p}_{RG} = \\frac{p_{obs} + Sp - 1}{Se + Sp - 1},  com  J = Se + Sp - 1 > 0.15',
    },
    {
      step: 8,
      title: 'Topologia de Bolhas (Newman), Espectros e Causalidade de Granger',
      layman: 'Mapeamos como os grupos conversam entre si, se existem câmaras de eco fechadas e quem começou primeiro a pauta nas redes (quem pautou quem ao longo do tempo).',
      math: 'Maximização da Modularidade de Newman Q em grafos bipartidos e cálculo do Índice E-I de Krackhardt. Teste F de Causalidade de Granger sobre séries temporais para detectar precedência temporal estatística de primeira movimentação.',
      formula: 'Q = \\frac{1}{2m} \\sum_{vw} \\left[ A_{vw} - \\frac{k_v k_w}{2m} \\right] δ(c_v, c_w)  e  E\\text{-}I = \\frac{E - I}{E + I}',
    },
  ];

  const mathematicalCriteria = [
    {
      threshold: 'n = 550 (faixas 300 a 1.200)',
      name: 'Tamanho Amostral Auditado',
      whyLayman: 'Garante margem de erro segura de até ±4,9 pontos percentuais a 95% de confiança, mesmo com as variações naturais entre redes sociais.',
      whyMath: 'Com Efeito de Desenho de Kish médio DEFF ≈ 1.38, o tamanho efetivo n_eff = 550 / 1.38 ≈ 398 unidades independentes. Sob z = 1.96 e p = 0.50, a margem de erro teórica máxima é ME = 1.96 * sqrt(0.25 / 398) ≈ 4.90 p.p., estabilizando a variância assintótica do estimador de Rogan-Gladen.',
    },
    {
      threshold: 'k ≥ 5',
      name: 'Limiar de k-Anonimato (LGPD)',
      whyLayman: 'Impede que alguém descubra a identidade de um cidadão combinando informações raras, como a cidade, a rede e a opinião dele.',
      whyMath: 'Critério matemático formal de Sweeney (2002) adotado por agências estatísticas oficiais (IBGE/Eurostat). Garante que qualquer partição de atributos quase-identificadores (plataforma × UF × postura) contenha no mínimo 5 contas distintas, eliminando risco de reidentificação por exclusão.',
    },
    {
      threshold: '[0.25, 4.00]',
      name: 'Truncamento de Pesos de Raking IPF',
      whyLayman: 'Evita que a opinião de uma única pessoa em uma região pequena ganhe um peso gigantesco (como valer por 20 pessoas), distorcendo a pesquisa.',
      whyMath: 'Técnica de weight trimming (Potter, 1990; Valliant et al., 2018). Limitar w_i no intervalo [0.25, 4.00] controla a inflação do erro quadrático médio (MSE) e impede que o DEFF de Kish exploda (1 + CV^2(w) > 3.0), preservando a estabilidade dos intervalos de confiança.',
    },
    {
      threshold: 'J = Se + Sp - 1 > 0.15',
      name: 'Índice J de Youden (Fail-Closed)',
      whyLayman: 'Exige que a inteligência artificial seja muito melhor do que um sorteio de cara ou coroa antes de os resultados serem aceitos pelo sistema.',
      whyMath: 'Na fórmula de Rogan-Gladen p_RG = (p_obs + Sp - 1) / (Se + Sp - 1), o denominador é exatamente o índice J de Youden. Se J se aproxima de zero, o denominador divide por quase zero, fazendo a variância tender ao infinito. O sistema bloqueia a execução se J <= 0.15.',
    },
    {
      threshold: 'κ ≥ 0.70',
      name: 'Concordância Kappa de Cohen',
      whyLayman: 'Comprova que analistas humanos experientes e a máquina concordam em quase todas as classificações difíceis.',
      whyMath: 'Escala psicométrica de Landis & Koch (1977). O coeficiente Kappa de Cohen compensa a concordância observada pelo acaso P_e. Valores >= 0.70 indicam concordância substancial a quase perfeita, atendendo ao rigor exigido para boletins legislativos oficiais.',
    },
    {
      threshold: 'Jaccard ≥ 0.85 & Δt ≤ 10s',
      name: 'Detecção de Robôs e CIB',
      whyLayman: 'Flagra campanhas coordenadas em que robôs copiam o mesmo texto e disparam dezenas de vezes quase no mesmo segundo.',
      whyMath: 'MinHash Locality Sensitive Hashing capturando quase-duplicatas com pequenas mutações ortográficas ou troca de emojis disparadas em sincronia temporal de rajada (burst).',
    },
    {
      threshold: 'E-I < -0.40 & Q (z > 1.96)',
      name: 'Câmaras de Eco Fechadas',
      whyLayman: 'Mostra quando mais de 70% das conversas acontecem apenas entre pessoas que já pensam igual, caracterizando uma bolha fechada.',
      whyMath: 'Como E-I = (E - I) / (E + I) ∈ [-1, +1] mede as conexões externas contra internas, E-I < -0.40 comprova segregação discursiva extrema com significância estatística confirmada pelo z-score contra modelo nulo de Erdős-Rényi.',
    },
    {
      threshold: 'PSI < 0.25 & VIF < 5.0',
      name: 'Estabilidade e Não-Colinearidade',
      whyLayman: 'Garante que o comportamento do modelo estatístico permaneça estável ao longo das semanas sem perder a calibração.',
      whyMath: 'Population Stability Index (PSI) abaixo de 0.25 assegura ausência de deriva conceitual severa (Concept Drift), enquanto o Variance Inflation Factor (VIF) abaixo de 5.0 atesta ausência de multicolinearidade prejudicial nas variáveis explicativas.',
    },
  ];

  const scientificBibliography = [
    {
      authors: 'Meng, Xiao-Li',
      year: '2018',
      title: 'Statistical paradises and paradoxes in big data: Law of large populations, big data paradox, and small-sample sizes',
      journal: 'Annals of Applied Statistics, 12(2), 685-726',
      doi: '10.1214/18-AOAS1185BR',
      application: 'Fundamenta por que milhões de postagens brutas sem desenho amostral geram erros maiores do que amostras de 550 contas (Paradoxo do Big Data).',
    },
    {
      authors: 'Rogan, Walter J. & Gladen, Beth',
      year: '1978',
      title: 'Estimating prevalence from the results of a screening test',
      journal: 'American Journal of Epidemiology, 107(1), 71-76',
      doi: '10.1093/oxfordjournals.aje.a112510',
      application: 'Fornece a base matemática da correção oficial de prevalência quando a classificação de IA possui sensibilidade e especificidade imperfeitas.',
    },
    {
      authors: 'Deming, W. Edwards & Stephan, Frederick F.',
      year: '1940',
      title: 'On a least squares adjustment of a sampled frequency table when the expected marginal totals are known',
      journal: 'Annals of Mathematical Statistics, 11(4), 427-444',
      doi: '10.1214/aoms/1177731829',
      application: 'Algoritmo Raking IPF utilizado no Cenário 3 para convergir a distribuição regional às margens demográficas do Censo/PNAD do IBGE.',
    },
    {
      authors: 'Kish, Leslie',
      year: '1965',
      title: 'Survey Sampling',
      journal: 'John Wiley & Sons, New York',
      doi: '10.1002/bimj.19680100122',
      application: 'Formulação clássica do Efeito do Desenho amostral (DEFF = 1 + CV^2(w)) e cálculo do tamanho efetivo de amostras ponderadas.',
    },
    {
      authors: 'Newman, Mark E. J.',
      year: '2006',
      title: 'Modularity and community structure in networks',
      journal: 'Proceedings of the National Academy of Sciences (PNAS), 103(23), 8577-8582',
      doi: '10.1073/pnas.0601602103',
      application: 'Métrica de modularidade Q aplicada para identificar topologicamente se os 4 espectros formam bolhas isoladas ou debate transversal.',
    },
    {
      authors: 'Krackhardt, David & Stern, Robert N.',
      year: '1988',
      title: 'Informal networks and organizational crises: An experimental simulation',
      journal: 'Social Psychology Quarterly, 51(2), 123-140',
      doi: '10.2307/2786835',
      application: 'Índice E-I (External-Internal) que quantifica se o debate digital ocorre dentro das próprias bolhas ou entre grupos opostos.',
    },
    {
      authors: 'Guimerà, Roger & Amaral, Luís A. Nunes',
      year: '2005',
      title: 'Functional cartography of complex metabolic networks',
      journal: 'Nature, 433, 895-900',
      doi: '10.1038/nature03288',
      application: 'Coeficiente de participação P_i para identificar contas-ponte que transitam entre diferentes espectros políticos com P_i > 0.30.',
    },
    {
      authors: 'Goh, Kwang-Il & Barabási, Albert-László',
      year: '2008',
      title: 'Burstiness and memory in complex systems',
      journal: 'Europhysics Letters (EPL), 81(4), 48002',
      doi: '10.1209/0295-5075/81/48002',
      application: 'Coeficiente de rajada temporal B utilizado no filtro Silver para distinguir atividade humana orgânica de disparos robóticos em bloco.',
    },
    {
      authors: 'Granger, Clive W. J.',
      year: '1969',
      title: 'Investigating causal relations by econometric models and cross-spectral methods',
      journal: 'Econometrica, 37(3), 424-438',
      doi: '10.2307/1912791',
      application: 'Teste de precedência temporal que identifica qual espectro ou rede começou a pautar os demais ao longo das horas do dia.',
    },
    {
      authors: 'Sweeney, Latanya',
      year: '2002',
      title: 'k-Anonymity: A model for protecting privacy',
      journal: 'International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), 557-570',
      doi: '10.1142/S0218488502001648',
      application: 'Garante o princípio de privacidade diferencial k >= 5 em todas as tabelas e recortes do sistema em estrito cumprimento da LGPD.',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Cabeçalho do Módulo 6 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 rounded-xl">
              <BookOpen className="w-6 h-6 text-blue-700 dark:text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Tratado Metodológico & Rigor Científico
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 font-semibold font-mono">
                  DataSenado / Senado Federal
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Fundamentação teórica bilíngue (linguagem acessível para parlamentares + rigor estatístico avançado), justificativa de limiares e fronteiras éticas.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
            <span>Versão: v5.1.0 (Fase 05)</span>
          </div>
        </div>

        {/* Abas de Navegação */}
        <div className="flex items-center gap-2 mt-5 overflow-x-auto pb-1">
          {[
            { id: 'pipeline', label: '1. O Pipeline em 8 Etapas (Leigo vs. Matemático)' },
            { id: 'criteria', label: '2. Por Que Usamos Estes Números? (Critérios)' },
            { id: 'bibliography', label: '3. Biblioteca Científica & DOIs' },
            { id: 'boundaries', label: '4. O Que PODE vs. NÃO PODE Afirmar' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap cursor-pointer ${
                activeSection === tab.id
                  ? 'bg-blue-700 text-white shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* SEÇÃO 1: PIPELINE EM 8 ETAPAS */}
      {activeSection === 'pipeline' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 flex items-center gap-2">
            <Microscope className="w-4 h-4 text-blue-700 shrink-0" />
            <span>
              Cada uma das 8 etapas é apresentada em dupla camada: à esquerda, uma explicação intuitiva e direta sem jargões; à direita, a formulação matemática e algorítmica exata.
            </span>
          </div>

          <div className="space-y-4">
            {pipelineSteps.map((step) => {
              const isExpanded = expandedStep === step.step;
              return (
                <div
                  key={step.step}
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-2xs transition-all"
                >
                  <button
                    onClick={() => setExpandedStep(isExpanded ? null : step.step)}
                    className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/60 text-blue-800 dark:text-blue-200 text-xs font-bold font-mono flex items-center justify-center">
                        {step.step}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        {step.title}
                      </h3>
                    </div>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </button>

                  {isExpanded && (
                    <div className="p-6 pt-2 border-t border-slate-100 dark:border-slate-800/60 grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in">
                      {/* Lado Leigo */}
                      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
                        <div className="text-xs font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                          🗣️ Para Leigos & Parlamentares (Analogia Prática)
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                          {step.layman}
                        </p>
                      </div>

                      {/* Lado Matemático */}
                      <div className="p-4 rounded-xl bg-slate-900 text-slate-100 border border-slate-800 space-y-3 font-sans">
                        <div className="text-xs font-bold text-[#DFBA4E] uppercase tracking-wider flex items-center gap-1.5">
                          📐 Fundamentação Matemática & Algorítmica
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans">
                          {step.math}
                        </p>
                        <div className="p-2.5 rounded-lg bg-slate-950 font-mono text-[11px] text-emerald-400 overflow-x-auto border border-slate-800/80">
                          {step.formula}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SEÇÃO 2: POR QUE USAMOS ESTES NÚMEROS? */}
      {activeSection === 'criteria' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Tabela Auditável dos Limiares Matemáticos e Critérios Numéricos
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Justificativa didática e científica para cada número de corte, margem de segurança e tolerância estatística adotados na Bancada 360º.
              </p>
            </div>

            <div className="space-y-4">
              {mathematicalCriteria.map((crit, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 space-y-2"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-700/60 pb-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <Binary className="w-4 h-4 text-blue-600" />
                      {crit.name}
                    </span>
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-800 dark:text-blue-200 tabular-nums self-start sm:self-auto">
                      {crit.threshold}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 text-xs">
                    <div>
                      <strong className="text-slate-600 dark:text-slate-400 block mb-1">Por que esse número para o usuário:</strong>
                      <p className="text-slate-700 dark:text-slate-300 leading-relaxed">{crit.whyLayman}</p>
                    </div>
                    <div>
                      <strong className="text-slate-600 dark:text-slate-400 block mb-1">Demonstração estatística:</strong>
                      <p className="text-slate-700 dark:text-slate-300 leading-relaxed font-sans">{crit.whyMath}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SEÇÃO 3: BIBLIOTECA CIENTÍFICA & DOIS */}
      {activeSection === 'bibliography' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-blue-700" />
                Biblioteca de Estudos Científicos de Referência
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Trabalhos seminais e artigos revisados por pares que fundamentam as equações, algoritmos e salvaguardas da Bancada DataSenado.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {scientificBibliography.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 space-y-2 flex flex-col justify-between"
                >
                  <div className="space-y-1.5">
                    <div className="text-xs font-bold text-slate-900 dark:text-white">
                      {item.title}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      {item.authors} ({item.year}) · <em>{item.journal}</em>
                    </div>
                    <div className="text-xs text-slate-700 dark:text-slate-300 pt-1">
                      <strong>Como usamos:</strong> {item.application}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-[11px]">
                    <span className="font-mono text-slate-500 truncate mr-2">DOI: {item.doi}</span>
                    <a
                      href={`https://doi.org/${item.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-semibold whitespace-nowrap"
                    >
                      Acessar Estudo <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SEÇÃO 4: O QUE PODE VS. NÃO PODE AFIRMAR */}
      {activeSection === 'boundaries' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Scale className="w-5 h-5 text-blue-700" />
                Guia de Honestidade Institucional & Limitações Metodológicas
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Para proteger a credibilidade do DataSenado e orientar Senadores e consultores legislativos sobre as fronteiras epistemológicas dos dados.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* O QUE PODE AFIRMAR */}
              <div className="p-5 rounded-2xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-300 dark:border-emerald-800 space-y-4">
                <div className="flex items-center gap-2 text-emerald-900 dark:text-emerald-200 font-bold text-sm border-b border-emerald-200 dark:border-emerald-800 pb-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  O Que VOCÊ PODE Afirmar com Rigor Científico
                </div>

                <ul className="space-y-3 text-xs text-emerald-950 dark:text-emerald-200 leading-relaxed list-disc pl-4 font-sans">
                  <li>
                    <strong>No debate público digital observado (U_Org):</strong> Após expurgo auditável de robôs/spam e correção de erro por Rogan-Gladen, a proporção de contas orgânicas favoráveis, contrárias e neutras é de X% (IC 95%: [L, U]).
                  </li>
                  <li>
                    <strong>Estrutura topológica de bolhas:</strong> O debate apresenta segregação comunitária (Q de Newman significativo e Krackhardt E-I &lt; -0.40), com formação de câmaras de eco e consenso restrito a subtemas técnicos.
                  </li>
                  <li>
                    <strong>Dinâmica temporal de pauta (Granger):</strong> Um determinado campo discursivo ou rede social apresentou precedência temporal preditiva na circulação dos argumentos em relação aos demais.
                  </li>
                  <li>
                    <strong>Cenário 3 (Simulação Demográfica):</strong> Projeta qual seria o equilíbrio do discurso digital caso a participação regional das contas seguisse as proporções do Censo/PNAD do IBGE.
                  </li>
                </ul>
              </div>

              {/* O QUE NÃO PODE AFIRMAR */}
              <div className="p-5 rounded-2xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-300 dark:border-rose-800 space-y-4">
                <div className="flex items-center gap-2 text-rose-900 dark:text-rose-200 font-bold text-sm border-b border-rose-200 dark:border-rose-800 pb-2">
                  <AlertOctagon className="w-5 h-5 text-rose-600" />
                  O Que VOCÊ JAMAIS PODE Afirmar (Limitações Inegociáveis)
                </div>

                <ul className="space-y-3 text-xs text-rose-950 dark:text-rose-200 leading-relaxed list-disc pl-4 font-sans">
                  <li>
                    <strong>NÃO É PESQUISA DA POPULAÇÃO BRASILEIRA (Nem Intenção de Voto):</strong> Proibido afirmar que "X% dos brasileiros apoiam o projeto". Redes sociais capturam apenas cidadãos autoselecionados e vocais. A população geral só é mensurável pelas pesquisas probabilísticas telefônicas/domiciliares do DataSenado.
                  </li>
                  <li>
                    <strong>Raking não elimina viés não-ignorável (MNAR):</strong> Ponderar por região corrige o volume entre estados, mas se quem posta no Norte for mais polarizado do que quem não posta no Norte, nenhum peso estatístico elimina esse viés interno.
                  </li>
                  <li>
                    <strong>Precedência de Granger não é causa física direta:</strong> Dizer que a Rede A precede a Rede B indica padrão temporal nas séries históricas, e não prova isolada de que as mesmas pessoas migraram de uma rede para a outra.
                  </li>
                  <li>
                    <strong>Inferência regional é ecológica e protegida:</strong> A localização das contas é inferida a partir de sinais públicos sob k-anonimato (k ≥ 5), não equivalendo a comprovante de domicílio eleitoral.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
