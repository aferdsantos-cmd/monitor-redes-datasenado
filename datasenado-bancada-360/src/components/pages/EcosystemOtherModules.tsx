import React, { useState } from 'react';
import {
  ArrowLeft,
  Search,
  TrendingUp,
  Newspaper,
  Database,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  EyeOff,
  Sparkles,
} from 'lucide-react';

interface OtherModulesProps {
  moduleType: 'trends_module' | 'editorial_module' | 'datasenado_surveys_module';
  onBackToEcosystem: () => void;
  onOpenDebateTheme: (themeId: string) => void;
}

const TRENDS_ITEMS = [
  {
    term: 'Escala 6x1 o que muda no salário',
    searchGrowth: '+420%',
    volumeIndex: 98,
    topRegion: 'Sudeste e Sul',
    relatedThemeId: 'pec_escala_6x1',
    citizenIntent: 'Dúvida trabalhista: trabalhadores buscando se a redução para 36h ou 40h semanais reduzirá o piso salarial mensal.',
  },
  {
    term: 'Quais setores entram na PEC 6x1',
    searchGrowth: '+315%',
    volumeIndex: 86,
    topRegion: 'Nordeste e Sudeste',
    relatedThemeId: 'pec_escala_6x1',
    citizenIntent: 'Comerciários, profissionais de saúde e logística verificando regras de transição por convenção coletiva.',
  },
  {
    term: 'Eleição presidente do Senado funções CCJ',
    searchGrowth: '+180%',
    volumeIndex: 74,
    topRegion: 'Centro-Oeste (DF) e Sudeste',
    relatedThemeId: 'eleicao_presidencia_senado',
    citizenIntent: 'Cidadãos pesquisando o papel regimental do Presidente do Senado e da Comissão de Constituição e Justiça.',
  },
  {
    term: 'PL 2338 Inteligência Artificial direitos autorais',
    searchGrowth: '+210%',
    volumeIndex: 79,
    topRegion: 'Sul e Sudeste',
    relatedThemeId: 'pl_ia_2338',
    citizenIntent: 'Criadores de conteúdo, jornalistas e desenvolvedores pesquisando remuneração de obras usadas em treino de IA.',
  },
];

const EDITORIAL_COMPARISON = [
  {
    themeId: 'pec_escala_6x1',
    themeLabel: 'PEC da Escala 6x1 e Redução da Jornada',
    convergences:
      'Todos os grandes portais convergem ao destacar o forte apelo popular da pauta nas redes sociais e o impacto direto sobre o setor de comércio e serviços.',
    divergences:
      'Veículos econômicos (Valor, Estadão) enfatizam o risco de inflação de serviços e custo de contratação; veículos de foco social e trabalhista (CartaCapital, Brasil de Fato, Folha) destacam indicadores de saúde mental, exaustão e produtividade.',
    highlightsAndOmissions:
      'Destaque amplo para o embate político entre parlamentares; baixa cobertura detalhada sobre experiências internacionais de transição gradual com desoneração da folha para microempresas.',
    outletsTable: [
      { outlet: 'Valor Econômico / Estadão', mainAngle: 'Custo produtivo, competitividade e impacto em PMEs', tone: 'Cauteloso / Econômico' },
      { outlet: 'Folha de S.Paulo / O Globo', mainAngle: 'Viabilidade política no Congresso e negociação de transição', tone: 'Analítico / Institucional' },
      { outlet: 'Portal G1 / UOL', mainAngle: 'Repercussão nacional, dúvidas do trabalhador e tramitação', tone: 'Informativo / Serviço' },
    ],
  },
  {
    themeId: 'eleicao_presidencia_senado',
    themeLabel: 'Eleição para a Presidência e Mesa Diretora do Senado',
    convergences:
      'Consenso editorial sobre a ampla favoritismo da candidatura de construção institucional e foco na distribuição das comissões permanentes (CCJ e CAE).',
    divergences:
      'Colunistas políticos divergem sobre o grau de independência da futura Mesa Diretora em relação às pautas prioritárias do Executivo versus demandas da oposição.',
    highlightsAndOmissions:
      'Grande destaque para articulações de bastidores partidários; menor espaço dedicado à agenda técnica de modernização legislativa e regimental.',
    outletsTable: [
      { outlet: 'JOTA / ConJur', mainAngle: 'Segurança jurídica, comando da CCJ e relação com o STF', tone: 'Técnico-Jurídico' },
      { outlet: 'O Globo / Estadão', mainAngle: 'Governabilidade, pauta econômica e proporcionalidade de blocos', tone: 'Político / Institucional' },
      { outlet: 'Poder360 / Metrópoles', mainAngle: 'Contagem de votos nas bancadas e disputa por espaços na Mesa', tone: 'Cobertura de Bastidores' },
    ],
  },
  {
    themeId: 'pl_ia_2338',
    themeLabel: 'PL 2338/2023 — Marco Legal da Inteligência Artificial',
    convergences:
      'Reconhecimento unânime da importância estratégica do texto aprovado no Senado como referência regulatória na América Latina.',
    divergences:
      'Portais de tecnologia e inovação alertam para custos de conformidade sobre startups; cadernos de cultura e jornalismo cobram regras estritas de remuneração de direitos autorais.',
    highlightsAndOmissions:
      'Destaque para o conceito de alto risco e direitos autorais; omissão frequente sobre as diretrizes de fomento a sandboxes regulatórios previstas no substitutivo.',
    outletsTable: [
      { outlet: 'Convergência Digital / TI Inside', mainAngle: 'Competitividade de startups brasileiras e infraestrutura de IA', tone: 'Setorial / Inovação' },
      { outlet: 'Folha / O Globo', mainAngle: 'Proteção de direitos autorais do jornalismo e criadores', tone: 'Editorial / Direitos' },
      { outlet: 'Agência Senado / EBC', mainAngle: 'Detalhamento das garantias aos cidadãos e classificação de risco', tone: 'Institucional / Explicativo' },
    ],
  },
];

const DATASENADO_SURVEYS = [
  {
    id: 'srv_01',
    title: 'Panorama Trabalhista: Percepção sobre Jornada de Trabalho, Qualidade de Vida e Produtividade',
    year: '2026',
    sample: 'n = 2.400 entrevistas telefônicas (Amostragem Probabilística Nacional · Margem ±2,0 p.p.)',
    relatedThemeId: 'pec_escala_6x1',
    keyFindings:
      '68% dos entrevistados consideram que jornadas com apenas 1 dia de descanso semanal prejudicam o convívio familiar e a saúde preventiva; 54% apoiam transição gradual negociada por setor econômico.',
  },
  {
    id: 'srv_02',
    title: 'Cidadania Digital: Inteligência Artificial, Privacidade de Dados e Confiança nas Instituições',
    year: '2026',
    sample: 'n = 3.100 entrevistas (Representatividade nas 5 Macrorregiões IBGE · Margem ±1,8 p.p.)',
    relatedThemeId: 'pl_ia_2338',
    keyFindings:
      '79% dos cidadãos brasileiros defendem que sistemas de Inteligência Artificial utilizados em saúde, crédito e serviço público passem por auditoria de transparência e supervisão humana obrigatória.',
  },
  {
    id: 'srv_03',
    title: 'Agenda Legislativa Prioritária e Avaliação da Atuação do Parlamento Federal',
    year: '2026',
    sample: 'n = 2.800 entrevistas (Série Histórica DataSenado · Margem ±1,9 p.p.)',
    relatedThemeId: 'eleicao_presidencia_senado',
    keyFindings:
      'Para 71% da população, o equilíbrio institucional entre os Poderes e o foco no custo de vida, emprego e segurança pública devem ser as prioridades da Mesa Diretora do Senado Federal.',
  },
];

export const EcosystemOtherModules: React.FC<OtherModulesProps> = ({
  moduleType,
  onBackToEcosystem,
  onOpenDebateTheme,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEditorialTheme, setSelectedEditorialTheme] = useState<string>('pec_escala_6x1');

  const currentEditorial =
    EDITORIAL_COMPARISON.find((e) => e.themeId === selectedEditorialTheme) || EDITORIAL_COMPARISON[0];

  const filteredTrends = TRENDS_ITEMS.filter(
    (t) =>
      t.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.citizenIntent.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredSurveys = DATASENADO_SURVEYS.filter(
    (s) =>
      s.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.keyFindings.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="max-w-[1360px] mx-auto px-6 py-8 sm:px-10 space-y-8 pb-16 select-none">
      {/* Top Navigation Return */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <button
            onClick={onBackToEcosystem}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-400 hover:underline mb-1 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Voltar ao Ecossistema de Inteligência 360º</span>
          </button>

          {moduleType === 'trends_module' && (
            <>
              <div className="flex items-center gap-2.5">
                <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white text-left">
                  Trends / Tendências — Monitor de Termos Buscados
                </h1>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 prose-justified max-w-3xl">
                Monitoramento das dúvidas reais e buscas espontâneas realizadas pela população na internet, permitindo identificar o interesse dos cidadãos que buscam informação fora das bolhas das redes sociais.
              </p>
            </>
          )}

          {moduleType === 'editorial_module' && (
            <>
              <div className="flex items-center gap-2.5">
                <Newspaper className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white text-left">
                  Inteligência Editorial — Monitor Comparativo da Imprensa
                </h1>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 prose-justified max-w-3xl">
                Análise comparativa de como os principais sites de notícias abordam os temas legislativos, mapeando pontos de convergência, divergência editorial, destaques e omissões.
              </p>
            </>
          )}

          {moduleType === 'datasenado_surveys_module' && (
            <>
              <div className="flex items-center gap-2.5">
                <Database className="w-5 h-5 text-blue-700 dark:text-blue-400" />
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white text-left">
                  Opinião Pública DataSenado — Buscador de Pesquisas Oficiais
                </h1>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 prose-justified max-w-3xl">
                Consulte o acervo de pesquisas por amostragem probabilística do Instituto de Pesquisa DataSenado e compare a percepção da população brasileira com o debate digital nas redes.
              </p>
            </>
          )}
        </div>
      </div>

      {/* MODULE 2: TRENDS / TENDÊNCIAS */}
      {moduleType === 'trends_module' && (
        <div className="space-y-6">
          <div className="relative max-w-xl">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Pesquisar termo buscado na web (ex.: escala 6x1, salário, inteligência artificial, CCJ)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs sm:text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredTrends.map((item, idx) => (
              <div
                key={idx}
                className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-emerald-700 dark:text-emerald-400 font-bold">
                      Crescimento de Busca: {item.searchGrowth}
                    </span>
                    <span className="text-slate-500">Índice de Interesse: {item.volumeIndex}/100</span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white text-left">
                    “{item.term}”
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                    {item.citizenIntent}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-500">Maior concentração: <strong>{item.topRegion}</strong></span>
                  <button
                    onClick={() => onOpenDebateTheme(item.relatedThemeId)}
                    className="inline-flex items-center gap-1.5 font-bold text-blue-700 dark:text-blue-400 hover:underline cursor-pointer"
                  >
                    <span>Cruzar com Debate nas Redes</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODULE 3: INTELIGÊNCIA EDITORIAL */}
      {moduleType === 'editorial_module' && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 mr-2">Selecione o Tema Analisado na Imprensa:</span>
            {EDITORIAL_COMPARISON.map((ed) => (
              <button
                key={ed.themeId}
                onClick={() => setSelectedEditorialTheme(ed.themeId)}
                className={`px-3.5 py-2 rounded-lg text-xs font-semibold border transition-colors cursor-pointer ${
                  selectedEditorialTheme === ed.themeId
                    ? 'bg-[#0B1F3A] text-white border-[#0B1F3A]'
                    : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800'
                }`}
              >
                {ed.themeLabel}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase text-emerald-800 dark:text-emerald-300">
                <CheckCircle2 className="w-4 h-4" />
                <span>Convergências Editoriais</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose-justified">
                {currentEditorial.convergences}
              </p>
            </div>

            <div className="p-6 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50/40 dark:bg-red-950/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase text-red-800 dark:text-red-300">
                <AlertTriangle className="w-4 h-4" />
                <span>Divergências de Enquadramento</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose-justified">
                {currentEditorial.divergences}
              </p>
            </div>

            <div className="p-6 rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/40 dark:bg-amber-950/20 space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase text-amber-800 dark:text-amber-300">
                <EyeOff className="w-4 h-4" />
                <span>Destaques vs. Omissões</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose-justified">
                {currentEditorial.highlightsAndOmissions}
              </p>
            </div>
          </div>

          <div className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white text-left">
                Matriz Comparativa por Grupo de Veículos
              </h3>
              <button
                onClick={() => onOpenDebateTheme(currentEditorial.themeId)}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-700 dark:text-blue-400 hover:underline cursor-pointer"
              >
                <span>Ver Repercussão deste Tema nas Redes</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Veículos / Portais</th>
                    <th className="py-3 px-4">Foco Principal da Cobertura</th>
                    <th className="py-3 px-4">Tom Editorial Predominante</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {currentEditorial.outletsTable.map((row, i) => (
                    <tr key={i}>
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">{row.outlet}</td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300">{row.mainAngle}</td>
                      <td className="py-3 px-4 font-mono text-blue-800 dark:text-blue-300">{row.tone}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MODULE 4: OPINIÃO PÚBLICA DATASENADO */}
      {moduleType === 'datasenado_surveys_module' && (
        <div className="space-y-6">
          <div className="relative max-w-xl">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar nos dados de pesquisas do DataSenado (ex.: jornada, inteligência artificial, prioridades)..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs sm:text-sm"
            />
          </div>

          <div className="space-y-4">
            {filteredSurveys.map((srv) => (
              <div
                key={srv.id}
                className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-bold text-blue-800 dark:text-blue-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    Pesquisa Oficial DataSenado ({srv.year})
                  </span>
                  <span className="font-mono text-slate-500">{srv.sample}</span>
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white text-left">
                  {srv.title}
                </h3>

                <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200 leading-relaxed prose-justified">
                  <strong>Achado Principal:</strong> {srv.keyFindings}
                </p>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => onOpenDebateTheme(srv.relatedThemeId)}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#0B1F3A] dark:text-blue-300 hover:underline cursor-pointer"
                  >
                    <span>Comparar com o Monitoramento das Redes Sociais</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
