import React, { useState, useMemo } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Plus,
  Search,
  Clock,
  Users,
  TrendingUp,
  Layers,
  CheckCircle2,
  X,
} from 'lucide-react';
import { ThemeDataset } from '../../types';
import { BOILING_TOPICS_LIST } from '../../data/mockData';
import { useToast } from '../Toast';

interface DebateHubPageProps {
  themes: ThemeDataset[];
  onSelectTheme: (themeId: string) => void;
  onOpenNewThemeModal: () => void;
  onCreateThemeFromDiscovery: (topicTitle: string, committee: string, queryHint: string) => void;
  onBackToEcosystem: () => void;
}

const MONITORING_DURATION_MAP: Record<string, { durationLabel: string; startedAt: string }> = {
  eleicao_presidencia_senado: {
    durationLabel: 'Monitorando há 14 dias (336h)',
    startedAt: 'Iniciado em 22 Out · Coleta contínua',
  },
  pec_escala_6x1: {
    durationLabel: 'Monitorando há 21 dias (504h)',
    startedAt: 'Iniciado em 15 Out · Coleta contínua',
  },
  pl_ia_2338: {
    durationLabel: 'Monitorando há 30 dias (720h)',
    startedAt: 'Iniciado em 06 Out · Coleta contínua',
  },
};

const EXTRA_DISCOVERABLE_TOPICS = [
  {
    id: 'disc_isencao_ir_5mil',
    title: 'Isenção de Imposto de Renda até R$ 5.000 e Reforma da Renda',
    committee: 'CAE — Comissão de Assuntos Econômicos',
    volume24h: 68400,
    growth24h: 195,
    summary:
      'Intenso debate nas redes sobre o impacto orçamentário da faixa de isenção do IRPF e a tributação compensatória sobre dividendos e altas rendas.',
    dominantNetworks: 'X (Twitter), Instagram, YouTube e WhatsApp',
  },
  {
    id: 'disc_seguranca_publica_pec',
    title: 'PEC da Segurança Pública e Integração das Forças Policiais',
    committee: 'CCJ / CSP — Comissão de Segurança Pública',
    volume24h: 51900,
    growth24h: 162,
    summary:
      'Discussão polarizada entre governadores e parlamentares sobre a autonomia das polícias estaduais versus a coordenação constitucional da União.',
    dominantNetworks: 'YouTube, X (Twitter), Telegram e Facebook',
  },
  {
    id: 'disc_apostas_bets_regulacao',
    title: 'CPI das Apostas Online (Bets) e Endividamento Familiar',
    committee: 'CPI das Bets / CAE',
    volume24h: 89300,
    growth24h: 245,
    summary:
      'Forte mobilização cidadã e cobertura da imprensa sobre o impacto das apostas esportivas no orçamento doméstico e restrições à publicidade digital.',
    dominantNetworks: 'TikTok, Instagram, YouTube e WhatsApp',
  },
];

export const DebateHubPage: React.FC<DebateHubPageProps> = ({
  themes,
  onSelectTheme,
  onOpenNewThemeModal,
  onCreateThemeFromDiscovery,
  onBackToEcosystem,
}) => {
  const { showToast } = useToast();
  const [isSearchExplorerOpen, setIsSearchExplorerOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<'TODOS' | 'SENADO' | 'GERAL'>('TODOS');

  const allDiscoverableTopics = useMemo(() => {
    const fromBoiling = BOILING_TOPICS_LIST.map((b) => ({
      id: b.id,
      title: b.title,
      committee: b.committee,
      volume24h: b.volume24h,
      growth24h: b.growth24h,
      isSenateInterest: b.isSenateInterest,
      themeIdTarget: b.themeIdTarget,
      summary: b.suggestedAction,
      dominantNetworks: b.isSenateInterest
        ? 'X (Twitter), YouTube, Instagram e Telegram'
        : 'TikTok, Instagram e X (Twitter)',
    }));

    const fromExtra = EXTRA_DISCOVERABLE_TOPICS.map((e) => ({
      ...e,
      isSenateInterest: true,
      themeIdTarget: undefined,
    }));

    return [...fromBoiling, ...fromExtra];
  }, []);

  const filteredDiscoveryTopics = useMemo(() => {
    return allDiscoverableTopics.filter((item) => {
      if (filterCategory === 'SENADO' && !item.isSenateInterest) return false;
      if (filterCategory === 'GERAL' && item.isSenateInterest) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          item.title.toLowerCase().includes(q) ||
          item.committee.toLowerCase().includes(q) ||
          item.summary.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [allDiscoverableTopics, searchQuery, filterCategory]);

  const handleSelectDiscoveryTopic = (topic: (typeof allDiscoverableTopics)[0]) => {
    if (topic.themeIdTarget) {
      showToast(
        'info',
        'Abrindo Tema Monitorado',
        `Direcionando para o painel de "${topic.title}".`
      );
      onSelectTheme(topic.themeIdTarget);
    } else {
      onCreateThemeFromDiscovery(topic.title, topic.committee, topic.title);
    }
  };

  return (
    <div className="max-w-[1360px] mx-auto px-6 py-8 sm:px-10 space-y-8 pb-16 select-none">
      {/* Top Breadcrumb & Return Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <button
            onClick={onBackToEcosystem}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-400 hover:underline mb-1 cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Voltar ao Ecossistema de Inteligência 360º</span>
          </button>
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-[#0B1F3A] dark:text-[#DFBA4E]" />
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight text-left">
              Inteligência do Debate Público — Pautas Monitoradas
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 prose-justified max-w-3xl">
            Selecione um dos temas com monitoramento ativo abaixo para abrir sua bancada completa de análise, cadastre um novo tema legislativo (<strong>+ Novo</strong>) ou explore os principais assuntos em ebulição nas redes sociais (<strong>Pesquisar</strong>).
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
          <span>{themes.length} monitoramentos ativos em tempo real (6 redes)</span>
        </div>
      </div>

      {/* Main Cards Grid: Existing Monitored Themes + "+ Novo" Card + "Pesquisar" Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
        {/* 1. Cards for Each Monitored Theme */}
        {themes.map((theme) => {
          const durationInfo = MONITORING_DURATION_MAP[theme.id] || {
            durationLabel: 'Monitorando há 1 hora (Recém-criado)',
            startedAt: 'Iniciado hoje · Coleta contínua',
          };
          const officialScenario =
            theme.scenarios.find((s) => s.scenarioId === 'rogan_gladen') || theme.scenarios[0];

          return (
            <div
              key={theme.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectTheme(theme.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectTheme(theme.id);
                }
              }}
              className="group rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 flex flex-col justify-between space-y-5 transition-all duration-200 hover:-translate-y-1 hover:border-blue-600 dark:hover:border-blue-500 hover:shadow-lg cursor-pointer"
            >
              <div className="space-y-4">
                {/* Status Indicator Row: Green Dot + Active Duration + Lifecycle State */}
                <div className="flex items-center justify-between gap-2 pb-3 border-b border-slate-100 dark:border-slate-800 flex-wrap">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-900/60">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
                      <span className="text-[11px] font-bold text-emerald-800 dark:text-emerald-300">
                        Ativo
                      </span>
                    </div>
                    {theme.lifecycleStatus && (
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                        <span>{theme.lifecycleStatus.replace(/_/g, ' ')}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5 text-xs font-mono text-slate-500 dark:text-slate-400 tabular-nums">
                    <Clock className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                    <span>{durationInfo.durationLabel}</span>
                  </div>
                </div>

                {/* Commission & Title */}
                <div className="space-y-1.5">
                  <div className="text-xs font-semibold text-blue-800 dark:text-blue-300">
                    Comissão: {theme.committee}
                  </div>
                  <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white leading-snug text-left group-hover:text-blue-800 dark:group-hover:text-blue-300 transition-colors">
                    {theme.title}
                  </h2>
                </div>

                {/* Context Summary */}
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified line-clamp-3">
                  {theme.legislativeContext}
                </p>

                {/* Mini Stance Distribution Bar */}
                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono tabular-nums">
                    <span className="text-[#0072B2] font-bold">
                      {officialScenario.favoravel.toFixed(1)}% Fav
                    </span>
                    <span className="text-[#D55E00] font-bold">
                      {officialScenario.contrario.toFixed(1)}% Cont
                    </span>
                    <span className="text-[#64748B]">
                      {officialScenario.neutro.toFixed(1)}% Neu
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden flex">
                    <div
                      style={{ width: `${officialScenario.favoravel}%` }}
                      className="bg-[#0072B2] h-full"
                    />
                    <div
                      style={{ width: `${officialScenario.contrario}%` }}
                      className="bg-[#D55E00] h-full"
                    />
                    <div
                      style={{ width: `${officialScenario.neutro}%` }}
                      className="bg-[#64748B] h-full"
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-0.5">
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      {theme.medallion.uOrgAccounts.toLocaleString('pt-BR')} contas orgânicas
                    </span>
                    <span className="font-mono tabular-nums">n = {theme.medallion.goldSampleSize}</span>
                  </div>
                </div>
              </div>

              {/* Card Footer CTA */}
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-[#0B1F3A] dark:text-blue-300 group-hover:text-blue-700">
                <span>Abrir Painel de Monitoramento</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          );
        })}

        {/* 2. Card "+ Novo" (Cadastrar Novo Tema Monitorado) */}
        <button
          onClick={onOpenNewThemeModal}
          className="group rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-blue-600 dark:hover:border-blue-400 bg-white/70 dark:bg-slate-900/60 hover:bg-white dark:hover:bg-slate-900 p-7 flex flex-col justify-between text-left space-y-6 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg cursor-pointer min-h-[320px]"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-700 dark:text-blue-400 group-hover:scale-105 transition-transform">
                <Plus className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono font-semibold text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-950/50 px-2.5 py-1 rounded-md">
                + Novo Monitoramento
              </span>
            </div>

            <div className="space-y-1.5 pt-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Cadastro de Pauta Específica
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white text-left">
                + Novo Tema Monitorado
              </h2>
            </div>

            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
              Já sabe qual Projeto de Lei, PEC, Medida Provisória ou assunto deseja acompanhar? Configure um novo monitoramento definindo a comissão do Senado e as palavras-chave de busca nas 6 redes sociais.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-200/70 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-blue-700 dark:text-blue-400">
            <span>Cadastrar Novo Tema Agora</span>
            <Plus className="w-4 h-4" />
          </div>
        </button>

        {/* 3. Card "Pesquisar" (Descobrir Temas em Debate nas Redes) */}
        <button
          onClick={() => setIsSearchExplorerOpen(true)}
          className={`group rounded-2xl border-2 text-left p-7 flex flex-col justify-between space-y-6 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg cursor-pointer min-h-[320px] ${
            isSearchExplorerOpen
              ? 'border-amber-500 bg-amber-50/20 dark:bg-amber-950/20'
              : 'border-slate-200 dark:border-slate-800 hover:border-amber-500 dark:hover:border-amber-500 bg-white dark:bg-slate-900'
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 flex items-center justify-center text-amber-700 dark:text-amber-400 group-hover:scale-105 transition-transform">
                <Search className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono font-semibold text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 px-2.5 py-1 rounded-md">
                Descoberta nas Redes
              </span>
            </div>

            <div className="space-y-1.5 pt-2">
              <div className="text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                Sem Tema Pré-Definido?
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white text-left">
                Pesquisar Temas em Debate
              </h2>
            </div>

            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
              Explore os principais temas que estão mobilizando as redes sociais no Brasil neste momento. Verifique o volume de menções, a aceleração de crescimento e escolha uma pauta a partir dali para monitorar.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs font-bold text-amber-700 dark:text-amber-400">
            <span>Explorar Temas em Ebulição nas Redes</span>
            <Search className="w-4 h-4" />
          </div>
        </button>
      </div>

      {/* Interactive Search & Discovery Section (Opened when clicking the "Pesquisar" Card) */}
      {isSearchExplorerOpen && (
        <section className="p-7 rounded-2xl border-2 border-amber-300 dark:border-amber-800/80 bg-white dark:bg-slate-900 space-y-6 shadow-lg animate-in fade-in duration-200">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
            <div className="space-y-1 max-w-2xl">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                <TrendingUp className="w-4 h-4" />
                <span>Buscador de Pautas & Assuntos em Ebulição nas Redes</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white text-left">
                Escolha um Tema em Debate nas Redes para Iniciar ou Abrir a Análise
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                Pesquise por palavra-chave ou filtre abaixo os assuntos de maior repercussão orgânica nas últimas 24 horas. Ao selecionar qualquer tema, o painel analítico é aberto automaticamente.
              </p>
            </div>

            <button
              onClick={() => setIsSearchExplorerOpen(false)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Fechar buscador de temas"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Search Input & Category Filter */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="relative flex-1 min-w-[260px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Pesquisar assunto em debate (ex.: Escala 6x1, Imposto de Renda, Inteligência Artificial, Bets, Segurança)..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-amber-500/40"
              />
            </div>

            <div className="inline-flex rounded-lg p-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setFilterCategory('TODOS')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  filterCategory === 'TODOS'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                Todos em Alta ({allDiscoverableTopics.length})
              </button>
              <button
                onClick={() => setFilterCategory('SENADO')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  filterCategory === 'SENADO'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                Pautas Legislativas / Senado
              </button>
              <button
                onClick={() => setFilterCategory('GERAL')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
                  filterCategory === 'GERAL'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400'
                }`}
              >
                Assuntos Gerais (Ruído)
              </button>
            </div>
          </div>

          {/* Results List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredDiscoveryTopics.map((topic) => (
              <div
                key={topic.id}
                className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex flex-col justify-between space-y-4 hover:border-amber-500/60 transition-colors"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2 text-xs">
                    <span className="font-semibold text-blue-800 dark:text-blue-300">
                      {topic.committee}
                    </span>
                    <span className="font-mono font-bold text-emerald-700 dark:text-emerald-400 tabular-nums">
                      +{topic.growth24h}% em 24h · {topic.volume24h.toLocaleString('pt-BR')} posts
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-slate-900 dark:text-white text-left">
                    {topic.title}
                  </h4>

                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                    {topic.summary}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-200/70 dark:border-slate-800 flex items-center justify-between gap-3">
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                    Redes: <strong>{topic.dominantNetworks}</strong>
                  </span>

                  <button
                    onClick={() => handleSelectDiscoveryTopic(topic)}
                    className="px-3.5 py-1.5 rounded-lg bg-[#0B1F3A] hover:bg-blue-950 text-white text-xs font-semibold transition-colors whitespace-nowrap shrink-0 cursor-pointer flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#DFBA4E]" />
                    <span>{topic.themeIdTarget ? 'Abrir Monitoramento' : 'Escolher e Monitorar'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};
