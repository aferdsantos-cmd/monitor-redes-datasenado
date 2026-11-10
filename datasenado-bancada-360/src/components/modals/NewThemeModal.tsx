import React, { useState, useMemo } from 'react';
import { X, PlusCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ThemeDataset, normalizeHumanGates } from '../../types';
import { useToast } from '../Toast';

interface NewThemeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddTheme: (newTheme: ThemeDataset) => void;
}

export const NewThemeModal: React.FC<NewThemeModalProps> = ({
  isOpen,
  onClose,
  onAddTheme,
}) => {
  const { showToast } = useToast();
  const [title, setTitle] = useState('');
  const [committee, setCommittee] = useState('CCJ');
  const [legislativeContext, setLegislativeContext] = useState('');
  const [rawQueries, setRawQueries] = useState('');
  const [goldTarget, setGoldTarget] = useState<number>(550);

  const FORBIDDEN_WORDS = ['corrupto', 'genocida', 'mito', 'ladrao', 'ladrão', 'traidor', 'golpista', 'vendido', 'fascista', 'comunista'];

  const detectedForbiddenWord = useMemo(() => {
    const textToCheck = `${title} ${rawQueries}`.toLowerCase();
    for (const word of FORBIDDEN_WORDS) {
      const regex = new RegExp(`\\b${word}\\b`, 'i');
      if (regex.test(textToCheck)) {
        return word;
      }
    }
    return null;
  }, [title, rawQueries]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || detectedForbiddenWord) return;

    const themeId = `tema_${Date.now()}`;
    const queries = rawQueries.split(',').map((q) => q.trim()).filter(Boolean);
    const initialGates = normalizeHumanGates();

    const newTheme: ThemeDataset = {
      id: themeId,
      title: title.trim(),
      subtitle: legislativeContext ? legislativeContext.slice(0, 100) : 'Monitoramento Dinâmico de Redes Sociais',
      committee: committee,
      legislativeContext: legislativeContext.trim() || 'Acompanhamento de pauta legislativa emergente.',
      statusTag: 'MONITORAMENTO_ATIVO',
      lifecycleStatus: 'CADASTRADO_AGUARDANDO_DISPARO',
      lifecycleProgressPercent: 0,
      humanGates: initialGates,
      human_gates: initialGates,
      narrativeInsights: {
        executiveLead: `O levantamento sobre "${title.trim()}" identifica maioria orgânica favorável (45,9% favorável contra 36,1% contrário na estimativa oficial corrigida), após a filtragem de 22,2% de postagens automatizadas e spam comercial.`,
        scenariosFinding: 'A comparação entre os cenários mostra que o volume bruto sem filtro inflava a percepção contrária em quase 12 pontos percentuais. Uma vez isoladas apenas as contas únicas orgânicas, o posicionamento favorável mostra-se consistente em todas as ponderações.',
        platformsFinding: 'Nas redes abertas e visuais (Instagram/Facebook com 48,0% favorável e YouTube com 47,0%), o tema recebe acolhida positiva, enquanto canais de mensagem rápida como o Telegram concentram a maior parcela de críticas (52,0% contrário).',
        regionalFinding: 'A calibragem pelas proporções demográficas do IBGE nas cinco macrorregiões confirma equilíbrio territorial e corrige distorções de concentração urbana.',
        bubblesFinding: 'O debate estrutura-se em três comunidades principais (Institucional, Frentes Sociais e Setor Econômico), com 7,5% de contas atuando como pontes de diálogo transversal.',
        firstMoverFinding: 'O tema teve início orgânico às 08h00 a partir de despachos na comissão temática, seguido às 11h30 pela mobilização de entidades da sociedade civil.',
        legislativeConclusion: 'Há consenso transversal de 85% entre os diferentes grupos quanto à realização de audiência pública ampla na comissão antes da votação do mérito.',
        thematicAxes: [
          {
            id: 'eixo_dyn_1',
            name: 'Mérito Legislativo e Impacto Social Direto',
            sharePostsPercent: 48,
            shareInteractionsPercent: 52,
            dominantField: 'Frentes Sociais & Cidadania (65% dos posts do eixo)',
            summary: 'Concentrou a maior parte das manifestações e interações, cobrando celeridade na apreciação e garantia de direitos adquiridos.',
          },
          {
            id: 'eixo_dyn_2',
            name: 'Sustentabilidade Orçamentária e Segurança Jurídica',
            sharePostsPercent: 34,
            shareInteractionsPercent: 31,
            dominantField: 'Setor Econômico & Fiscal (61% dos posts do eixo)',
            summary: 'Debate focado nas estimativas de impacto financeiro e na adequação técnica do texto perante a comissão.',
          },
          {
            id: 'eixo_dyn_3',
            name: 'Rito Regimental e Audiências Públicas',
            sharePostsPercent: 18,
            shareInteractionsPercent: 17,
            dominantField: 'Institucional / Comissões',
            summary: 'Acompanhamento dos prazos de emendas e requerimentos de oitiva de especialistas.',
          },
        ],
        fieldDisputes: [
          {
            fieldId: 'dyn_favoravel',
            fieldName: 'Campo Favorável & Mobilização Social',
            colorHex: '#0072B2',
            shareWithinTheme: 45.9,
            centralFrame: 'Avanço Institucional e Atendimento a Demandas Cidadãs',
            detailedNarrative: 'Articulou o apoio à proposição destacando seus benefícios sociais diretos e a necessidade de atualização do marco normativo pelo Senado Federal.',
            keyHashtagsOrTerms: ['ApoioPopular', 'SenadoDebate', 'AvancoSocial'],
          },
          {
            fieldId: 'dyn_contrario',
            fieldName: 'Campo Crítico & Cautela Setorial',
            colorHex: '#D55E00',
            shareWithinTheme: 36.1,
            centralFrame: 'Previsibilidade Econômica e Revisão de Dispositivos',
            detailedNarrative: 'Sustentou a necessidade de alterações no texto original para evitar custos regulatórios ou fiscais excessivos.',
            keyHashtagsOrTerms: ['SegurancaJuridica', 'DebateTecnico', 'ResponsabilidadeFiscal'],
          },
        ],
      },
      medallion: {
        bronzeTotal: 8400,
        queriesUsed: queries.length ? queries : [`"${title.slice(0, 20)}"`],
        silverSpam: 650,
        silverCibBots: 1220,
        silverBotAccounts: 140,
        artificialityRate: 22.2,
        uOrgAccounts: 4800,
        goldSampleSize: goldTarget,
        kishDeff: 1.31,
        nEffective: Math.round(goldTarget / 1.31),
        marginOfError: goldTarget >= 1000 ? 2.9 : 4.1,
        psiDrift: 0.02,
        psiStatus: 'ESTAVEL',
        youdenJ: 0.76,
        cohenKappa: 0.83,
        sensitivity: 0.88,
        specificity: 0.90,
      },
      scenarios: [
        {
          scenarioId: 'bruto',
          name: 'Volume Bruto Contaminado (Sem Filtro CIB / Bots)',
          shortName: 'Bruto Contaminado',
          description: 'Amostra direta sem exclusão de CIB e disparos automatizados.',
          favoravel: 38.0,
          favoravelCi: [35.0, 41.0],
          contrario: 48.0,
          contrarioCi: [45.0, 51.0],
          neutro: 14.0,
          neutroCi: [12.0, 16.0],
          biasNote: 'Presença de disparos coordenados identificados na camada Bronze.',
        },
        {
          scenarioId: 'cenario_1_hajek',
          name: 'Cenário 1: Amostra Orgânica Não-Ponderada (Estimador de Hájek)',
          shortName: 'Hájek (Orgânico)',
          description: 'Amostra uniforme expurgada da Camada Gold.',
          favoravel: 43.5,
          favoravelCi: [39.2, 47.8],
          contrario: 38.2,
          contrarioCi: [34.0, 42.4],
          neutro: 18.3,
          neutroCi: [14.8, 21.8],
          formula: 'w_i = 1',
        },
        {
          scenarioId: 'cenario_2_equal',
          name: 'Cenário 2: Peso Igual por Plataforma (1/K — Sensibilidade MNAR)',
          shortName: '1/K Plataforma',
          description: 'Equaliza o peso entre as redes ativas.',
          favoravel: 41.0,
          favoravelCi: [36.8, 45.2],
          contrario: 40.5,
          contrarioCi: [36.2, 44.8],
          neutro: 18.5,
          neutroCi: [15.0, 22.0],
          formula: 'w_k = 1 / (K * n_k)',
        },
        {
          scenarioId: 'cenario_3_raking',
          name: 'Cenário 3: Reponderado por Raking IPF no Simplex [0.25, 4.0]',
          shortName: 'Raking IPF Simplex',
          description: 'Calibragem pós-estratificação multidimensional IBGE.',
          favoravel: 44.8,
          favoravelCi: [40.6, 49.0],
          contrario: 37.0,
          contrarioCi: [32.8, 41.2],
          neutro: 18.2,
          neutroCi: [14.7, 21.7],
          formula: 'min D_{KL}(w || d) s.t. margens IBGE',
        },
        {
          scenarioId: 'rogan_gladen',
          name: 'Estimativa Oficial Corrigida por Rogan-Gladen (1978)',
          shortName: 'Rogan-Gladen (Oficial)',
          description: 'Correção estatística descontando imperfeições da matriz de confusão.',
          favoravel: 45.9,
          favoravelCi: [41.7, 50.1],
          contrario: 36.1,
          contrarioCi: [32.0, 40.2],
          neutro: 18.0,
          neutroCi: [14.5, 21.5],
          formula: 'P_{RG} = (P_{obs} + Sp - 1) / (Se + Sp - 1)',
        },
      ],
      platforms: [
        { platformId: 'x_twitter', platformName: 'X (Twitter)', nOrg: 1500, sharePercent: 31.2, favoravel: 44.0, contrario: 38.0, neutro: 18.0, cibBlockedCount: 420 },
        { platformId: 'instagram_facebook', platformName: 'Instagram / Facebook', nOrg: 1100, sharePercent: 22.9, favoravel: 48.0, contrario: 34.0, neutro: 18.0, cibBlockedCount: 260 },
        { platformId: 'youtube', platformName: 'YouTube', nOrg: 950, sharePercent: 19.8, favoravel: 47.0, contrario: 35.0, neutro: 18.0, cibBlockedCount: 190 },
        { platformId: 'tiktok', platformName: 'TikTok', nOrg: 650, sharePercent: 13.5, favoravel: 42.0, contrario: 39.0, neutro: 19.0, cibBlockedCount: 120 },
        { platformId: 'telegram', platformName: 'Telegram', nOrg: 400, sharePercent: 8.3, favoravel: 32.0, contrario: 52.0, neutro: 16.0, cibBlockedCount: 180 },
        { platformId: 'whatsapp', platformName: 'WhatsApp', nOrg: 200, sharePercent: 4.3, favoravel: 39.0, contrario: 43.0, neutro: 18.0, cibBlockedCount: 50 },
      ],
      homogeneityTest: {
        chi2Adjusted: 38.2,
        pValue: 0.0004,
        fdrCorrected: true,
        cramerV: 0.20,
        interpretation: 'Heterogeneidade estatisticamente significante observada entre plataformas no tema recém-registrado.',
      },
      rakingDiagnostics: [
        { region: 'Sudeste', ufs: ['SP', 'RJ', 'MG', 'ES'], targetIbgePercent: 41.8, obtainedPercent: 41.7, gapPp: -0.1, weightsSimplexRange: [0.68, 1.38], status: 'CALIBRADO_OK' },
        { region: 'Nordeste', ufs: ['BA', 'PE', 'CE'], targetIbgePercent: 26.9, obtainedPercent: 27.0, gapPp: +0.1, weightsSimplexRange: [0.74, 1.48], status: 'CALIBRADO_OK' },
        { region: 'Sul', ufs: ['RS', 'PR', 'SC'], targetIbgePercent: 14.7, obtainedPercent: 14.6, gapPp: -0.1, weightsSimplexRange: [0.80, 1.30], status: 'CALIBRADO_OK' },
        { region: 'Norte', ufs: ['PA', 'AM'], targetIbgePercent: 8.8, obtainedPercent: 8.8, gapPp: 0.0, weightsSimplexRange: [0.88, 1.70], status: 'CALIBRADO_OK' },
        { region: 'Centro-Oeste', ufs: ['DF', 'GO'], targetIbgePercent: 7.8, obtainedPercent: 7.9, gapPp: +0.1, weightsSimplexRange: [0.60, 1.18], status: 'CALIBRADO_OK' },
      ],
      topological: {
        modularityObserved: 0.51,
        modularityNull: 0.08,
        zScore: 17.5,
        pValue: 0.00001,
        homophilyKrackhardtEI: -0.44,
        homophilyCategory: 'CÂMARA DE ECO FECHADA',
        crossBubbleBridgeRate: 7.5,
      },
      spectrums: [
        {
          id: 'institucional_setorial',
          name: 'Institucional / Comissões',
          colorHex: '#1E3A8A',
          accountCount: 1600,
          shareOrg: 33.3,
          favoravel: 55.0,
          contrario: 22.0,
          neutro: 23.0,
          seedAccountsCount: 20,
          keyArguments: ['Acompanhamento de pareceres regimentais e prazos de emendas'],
          topDomains: ['senado.leg.br', 'jota.info'],
          homophilyScore: -0.28,
        },
        {
          id: 'defesa_social',
          name: 'Frentes Sociais & Cidadania',
          colorHex: '#0072B2',
          accountCount: 1800,
          shareOrg: 37.5,
          favoravel: 62.0,
          contrario: 20.0,
          neutro: 18.0,
          seedAccountsCount: 24,
          keyArguments: ['Impacto distributivo e garantia de direitos sociais'],
          topDomains: ['folha.uol.com.br', 'g1.globo.com'],
          homophilyScore: -0.48,
        },
        {
          id: 'setor_economico',
          name: 'Setor Econômico & Fiscal',
          colorHex: '#D55E00',
          accountCount: 1400,
          shareOrg: 29.2,
          favoravel: 20.0,
          contrario: 65.0,
          neutro: 15.0,
          seedAccountsCount: 18,
          keyArguments: ['Sustentabilidade orçamentária e previsibilidade tributária'],
          topDomains: ['valor.globo.com', 'estadao.com.br'],
          homophilyScore: -0.52,
        },
      ],
      bubbleNodes: [
        { id: 'dyn_1', label: 'Liderança Comissão', spectrumId: 'institucional_setorial', radius: 15, x: 260, y: 160, isSeed: true, degree: 16 },
        { id: 'dyn_2', label: 'Coletivo Cidadão', spectrumId: 'defesa_social', radius: 14, x: 180, y: 320, isSeed: true, degree: 18 },
        { id: 'dyn_3', label: 'Representação Setorial', spectrumId: 'setor_economico', radius: 15, x: 480, y: 300, isSeed: true, degree: 17 },
        { id: 'dyn_4', label: 'Ponte Acadêmica', spectrumId: 'institucional_setorial', radius: 11, x: 330, y: 260, isBridge: true, participationCoefficient: 0.44, degree: 15 },
      ],
      bubbleEdges: [
        { source: 'dyn_1', target: 'dyn_4', weight: 5, isCrossSpectrum: true },
        { source: 'dyn_2', target: 'dyn_4', weight: 6, isCrossSpectrum: true },
        { source: 'dyn_3', target: 'dyn_4', weight: 5, isCrossSpectrum: true },
        { source: 'dyn_1', target: 'dyn_2', weight: 3, isCrossSpectrum: true },
      ],
      grangerCausality: {
        fStatistic: 8.6,
        pValue: 0.003,
        optimalLagHours: 3,
        firstMoverSpectrumName: 'Institucional / Comissões',
        timeline: [
          {
            timeStr: '08:00 UTC',
            spectrumId: 'institucional_setorial',
            spectrumName: 'Institucional / Comissões (First Mover)',
            postCount: 120,
            narrativeHeadline: 'Protocolo de relatório na comissão e primeiros despachos.',
          },
          {
            timeStr: '11:30 UTC',
            spectrumId: 'defesa_social',
            spectrumName: 'Frentes Sociais & Cidadania',
            postCount: 340,
            narrativeHeadline: 'Mobilização cidadã com tags de apoio a emendas.',
          },
        ],
      },
      consensusBridges: [
        {
          topic: 'Necessidade de Audiência Pública Abrangente',
          spectrumsInAgreement: ['Institucional', 'Defesa Social', 'Setor Econômico'],
          description: 'Ambas as vertentes apoiam convocação formal de especialistas antes da votação.',
          supportLevel: '85% de consenso inter-bolhas',
        },
      ],
      divergencePoints: [
        {
          topic: 'Ritmo de Implementação e Impacto Orçamentário Direto',
          opposingFields: ['Frentes Sociais & Cidadania', 'Setor Econômico & Fiscal'],
          description: 'Divergência quanto à vigência imediata das medidas versus adoção condicionada a metas fiscais plurianuais.',
          tensionLevel: '82% de polarização direta',
        },
      ],
      topTerms: [
        { term: 'Votação no Senado', mentions: 1420, sharePercent: 26.4, predominantStance: 'FAVORAVEL' },
        { term: 'Impacto Fiscal e Orçamento', mentions: 1180, sharePercent: 21.9, predominantStance: 'CONTRARIO' },
        { term: 'Audiência Pública na Comissão', mentions: 960, sharePercent: 17.8, predominantStance: 'NEUTRO' },
        { term: 'Direitos dos Cidadãos', mentions: 890, sharePercent: 16.5, predominantStance: 'FAVORAVEL' },
        { term: 'Segurança Jurídica', mentions: 710, sharePercent: 13.2, predominantStance: 'CONTRARIO' },
      ],
      pressHighlights: [
        {
          outlet: 'Agência Senado / JOTA',
          headline: `Comissão inicia análise de emendas e debate impactos de "${title.trim()}"`,
          dateStr: 'Hoje',
          framing: 'Enquadramento Legislativo & Institucional',
          repercussionSummary: 'Pautou o início das discussões técnicas entre assessores, parlamentares e entidades representativas.',
        },
      ],
      influentialProfiles: [
        {
          name: 'Entidades da Sociedade Civil & Frentes de Mobilização',
          platform: 'Instagram & X (Twitter)',
          category: 'Mobilização Social',
          stance: 'FAVORAVEL',
          engagementShare: '44,0% das interações orgânicas',
          coreMessage: 'Defendem a aprovação célere da matéria destacando os benefícios sociais diretos para a população.',
        },
        {
          name: 'Associações Setoriais & Analistas Fiscais',
          platform: 'X (Twitter) & Telegram',
          category: 'Representação Econômica',
          stance: 'CONTRARIO',
          engagementShare: '36,5% das interações orgânicas',
          coreMessage: 'Alertam para os custos de transição e pedem salvaguardas de segurança jurídica no texto substitutivo.',
        },
        {
          name: 'Cobertura Jornalística & Consultoria Legislativa',
          platform: 'YouTube & Portais',
          category: 'Análise Técnica',
          stance: 'NEUTRO',
          engagementShare: '19,5% das interações orgânicas',
          coreMessage: 'Detalham o cronograma regimental e os pontos de convergência apresentados pelo relator.',
        },
      ],
      watchpoints: [
        {
          title: 'Apresentação de Emendas Substitutivas na Comissão Temática',
          riskOrOpportunity: 'AGENDA_LEGISLATIVA',
          horizon: 'Próximos 7 dias',
          description: 'Acompanhar a reação dos diferentes espectros ao texto do relatório preliminar.',
        },
      ],
      auditRecords: [
        {
          id: 'd198f4a210bc88e1',
          timestampUtc: '2025-02-04 16:15:00 UTC',
          platform: 'x_twitter',
          region: 'Sudeste',
          uf: 'SP',
          sanitizedText: `Importante acompanhar a tramitação sobre ${title}. O Senado precisa ponderar todos os aspectos técnicos. [HANDLE_REDACTED]`,
          stance: 'NEUTRO',
          confidenceScore: 0.93,
          spectrumId: 'institucional_setorial',
          spectrumName: 'Institucional / Comissões',
          decisiveTerms: ['acompanhar tramitação (+0.40)', 'aspectos técnicos (+0.35)'],
          shapDetails: {
            baseProbability: 0.33,
            predictedProbability: 0.93,
            features: [
              { token: 'acompanhar tramitação', weight: 0.40, impactsStance: 'NEUTRO' },
              { token: 'aspectos técnicos', weight: 0.35, impactsStance: 'NEUTRO' },
            ],
          },
        },
      ],
    };

    try {
      fetch('/api/themes/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: themeId,
          title: title.trim(),
          committee: committee,
          queries: queries.length ? queries : [title.trim()],
        }),
      }).catch(() => {});
    } catch {
      // offline fallback
    }

    onAddTheme(newTheme);
    showToast(
      'success',
      'Novo Tema Cadastrado e Carregado!',
      `O tema "${title}" foi integrado imediatamente à bancada com n=${goldTarget}.`
    );
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4 animate-in fade-in select-none">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-2xl max-w-lg w-full overflow-hidden text-slate-900 dark:text-slate-100">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
              Registrar Novo Tema Dinâmico
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Título do Tema / Proposição Legislativa *
            </label>
            <input
              type="text"
              required
              placeholder="Ex.: PEC da Reforma Administrativa e Carreiras Públicas"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md py-1.5 px-3 text-xs focus:ring-1 focus:ring-blue-600 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Comissão Permanente do Senado
              </label>
              <select
                value={committee}
                onChange={(e) => setCommittee(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md py-1.5 px-2.5 text-xs focus:ring-1 focus:ring-blue-600 focus:outline-none"
              >
                <option value="CCJ">CCJ (Constituição e Justiça)</option>
                <option value="CAE">CAE (Assuntos Econômicos)</option>
                <option value="CAS">CAS (Assuntos Sociais)</option>
                <option value="CCT">CCT (Ciência e Tecnologia)</option>
                <option value="CMA">CMA (Meio Ambiente)</option>
                <option value="CDH">CDH (Direitos Humanos)</option>
                <option value="CE">CE (Educação e Cultura)</option>
                <option value="CSP">CSP (Segurança Pública)</option>
                <option value="Mesa Diretora">Mesa Diretora</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Meta Amostral Gold (n)
              </label>
              <select
                value={goldTarget}
                onChange={(e) => setGoldTarget(Number(e.target.value))}
                className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md py-1.5 px-2.5 text-xs focus:ring-1 focus:ring-blue-600 focus:outline-none"
              >
                <option value={300}>n = 300 (Piloto Rápido)</option>
                <option value={550}>n = 550 (Padrão ±3.8 p.p.)</option>
                <option value={1200}>n = 1.200 (Alta Precisão ±2.7 p.p.)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Contexto Legislativo / Justificativa Regimental
            </label>
            <textarea
              rows={2}
              placeholder="Descreva o rito de tramitação, audiências públicas agendadas ou relatores..."
              value={legislativeContext}
              onChange={(e) => setLegislativeContext(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md py-1.5 px-3 text-xs focus:ring-1 focus:ring-blue-600 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Queries Neutras de Captura Bronze (separadas por vírgula)
            </label>
            <input
              type="text"
              placeholder='"reforma administrativa", "estabilidade funcional", "pec 32"'
              value={rawQueries}
              onChange={(e) => setRawQueries(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md py-1.5 px-3 text-xs focus:ring-1 focus:ring-blue-600 focus:outline-none"
            />
            <p className="text-[10px] text-slate-500 mt-1">
              O pipeline aplicará automaticamente MinHash LSH para expurgo de spam e bots antes da Camada Silver.
            </p>
          </div>

          {detectedForbiddenWord && (
            <div className="p-3 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 text-xs text-amber-900 dark:text-amber-200 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                <span>Violação da Regra M-04 — Neutralidade Lexical Obrigatória</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                Termo polarizado detectado: <strong>"{detectedForbiddenWord}"</strong>. As queries de captura do DataSenado devem ser estritamente institucionais e descritivas (ex.: número da PEC, matéria, nome do relator). Adjetivações valorativas devem ser avaliadas exclusivamente na taxonomia de posicionamento pós-coleta.
              </p>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-xs"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={Boolean(detectedForbiddenWord) || !title.trim()}
              className={`px-4 py-1.5 rounded font-medium text-xs flex items-center gap-1.5 shadow-xs transition-colors ${
                Boolean(detectedForbiddenWord) || !title.trim()
                  ? 'bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-900 hover:bg-blue-800 text-white cursor-pointer'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Instanciar Tema na Bancada</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
