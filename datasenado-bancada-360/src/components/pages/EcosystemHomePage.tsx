import React from 'react';
import {
  ArrowUpRight,
  ShieldCheck,
  Database,
  Layers,
} from 'lucide-react';

export type EcosystemSection =
  | 'home'
  | 'debate_hub'
  | 'debate_dashboard'
  | 'trends_module'
  | 'editorial_module'
  | 'datasenado_surveys_module';

interface EcosystemHomePageProps {
  onSelectSection: (section: EcosystemSection) => void;
  monitoredThemesCount: number;
}

export const EcosystemHomePage: React.FC<EcosystemHomePageProps> = ({
  onSelectSection,
  monitoredThemesCount,
}) => {
  const modules = [
    {
      id: 'debate_hub' as EcosystemSection,
      badge: `${monitoredThemesCount} Pautas Ativas`,
      title: 'Inteligência do Debate Público',
      subtitle: 'Monitor das Redes Sociais',
      description:
        'Monitoramento contínuo em 6 redes digitais com higienização de robôs, estimativa de posicionamento orgânico, mapeamento de bolhas e síntese de narrativas.',
      accentColor: '#0072B2',
      borderAccent: 'hover:border-[#0072B2] dark:hover:border-blue-500',
      logoSvg: (
        <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
          <rect width="48" height="48" rx="12" className="fill-[#0B1F3A] dark:fill-blue-950" />
          <circle cx="17" cy="24" r="5" stroke="#DFBA4E" strokeWidth="2.2" />
          <circle cx="32" cy="16" r="4" stroke="#38BDF8" strokeWidth="2.2" />
          <circle cx="32" cy="32" r="4" stroke="#34D399" strokeWidth="2.2" />
          <path d="M21.5 21.5L28.2 17.8M21.5 26.5L28.2 30.2" stroke="#94A3B8" strokeWidth="1.8" strokeLinecap="round" />
          <path d="M32 20V28" stroke="#94A3B8" strokeWidth="1.5" strokeDasharray="2 2" />
        </svg>
      ),
    },
    {
      id: 'trends_module' as EcosystemSection,
      badge: 'Buscas Espontâneas',
      title: 'Trends / Tendências',
      subtitle: 'Monitor de Termos Buscados',
      description:
        'Rastreamento dos termos, dúvidas e conceitos mais buscados de forma geral na internet brasileira, capturando o interesse da maioria silenciosa.',
      accentColor: '#009E73',
      borderAccent: 'hover:border-[#009E73] dark:hover:border-emerald-500',
      logoSvg: (
        <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
          <rect width="48" height="48" rx="12" className="fill-[#0B1F3A] dark:fill-blue-950" />
          <path
            d="M12 32L20 23L26 27L36 15"
            stroke="#34D399"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M30 15H36V21"
            stroke="#DFBA4E"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <line x1="12" y1="36" x2="36" y2="36" stroke="#64748B" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      ),
    },
    {
      id: 'editorial_module' as EcosystemSection,
      badge: 'Multi-Espectro',
      title: 'Inteligência Editorial',
      subtitle: 'Monitor da Imprensa',
      description:
        'Análise comparativa dos principais portais de notícias com foco em como abordam cada tema, mapeando convergências, divergências, omissões e destaques.',
      accentColor: '#D97706',
      borderAccent: 'hover:border-[#D97706] dark:hover:border-amber-500',
      logoSvg: (
        <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
          <rect width="48" height="48" rx="12" className="fill-[#0B1F3A] dark:fill-blue-950" />
          <rect x="13" y="13" width="22" height="22" rx="3" stroke="#DFBA4E" strokeWidth="2" />
          <line x1="17" y1="19" x2="25" y2="19" stroke="#38BDF8" strokeWidth="2.2" strokeLinecap="round" />
          <line x1="17" y1="24" x2="31" y2="24" stroke="#E2E8F0" strokeWidth="1.6" strokeLinecap="round" />
          <line x1="17" y1="29" x2="28" y2="29" stroke="#E2E8F0" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      ),
    },
    {
      id: 'datasenado_surveys_module' as EcosystemSection,
      badge: 'Acervo Oficial',
      title: 'Opinião Pública DataSenado',
      subtitle: 'Buscador nos Dados do Senado',
      description:
        'Busca direta nas pesquisas probabilísticas oficiais do Instituto de Pesquisa DataSenado sobre temas legislativos, percepção social e séries históricas.',
      accentColor: '#1E3A8A',
      borderAccent: 'hover:border-blue-800 dark:hover:border-blue-400',
      logoSvg: (
        <svg viewBox="0 0 48 48" className="w-12 h-12" fill="none">
          <rect width="48" height="48" rx="12" className="fill-[#0B1F3A] dark:fill-blue-950" />
          <circle cx="22" cy="22" r="7.5" stroke="#DFBA4E" strokeWidth="2.2" />
          <path d="M27.5 27.5L35 35" stroke="#38BDF8" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M19 23V20M22 23V18M25 23V21" stroke="#E2E8F0" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col justify-between py-10 px-6 sm:px-10 select-none">
      <div className="max-w-[1280px] w-full mx-auto my-auto space-y-10">
        {/* Institutional Hero Header */}
        <div className="max-w-3xl mx-auto text-center space-y-3">
          <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[#0B1F3A] dark:text-[#DFBA4E]">
            <Layers className="w-3.5 h-3.5" />
            <span>Senado Federal · Instituto de Pesquisa DataSenado</span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-bold text-slate-900 dark:text-white tracking-tight text-center">
            Ecossistema de Inteligência de Dados 360º
          </h1>
          <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
            Plataforma integrada de análise e subsídio técnico ao processo legislativo. Selecione abaixo um dos quatro módulos de inteligência para explorar o debate público nas redes sociais, as tendências de busca na web, a cobertura comparada da imprensa ou o acervo oficial de pesquisas probabilísticas do DataSenado.
          </p>
        </div>

        {/* 4 Medium/Large Square Cards Grid (Instituto DX Inspired) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-[1240px] mx-auto">
          {modules.map((mod) => (
            <button
              key={mod.id}
              onClick={() => onSelectSection(mod.id)}
              className={`group relative text-left rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-7 flex flex-col justify-between lg:aspect-square min-h-[295px] transition-all duration-200 hover:-translate-y-1 hover:shadow-xl ${mod.borderAccent} cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600`}
            >
              {/* Top Row: Custom Logo + Status Tag */}
              <div className="space-y-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="shrink-0 transition-transform duration-200 group-hover:scale-105">
                    {mod.logoSvg}
                  </div>
                  <span className="text-[11px] font-mono font-semibold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-md">
                    {mod.badge}
                  </span>
                </div>

                {/* Title & Subtitle */}
                <div className="space-y-1">
                  <div className="text-xs font-semibold uppercase tracking-wider text-blue-800 dark:text-blue-400">
                    {mod.subtitle}
                  </div>
                  <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white leading-snug text-left group-hover:text-[#0B1F3A] dark:group-hover:text-[#DFBA4E] transition-colors">
                    {mod.title}
                  </h2>
                </div>

                {/* Justified Description */}
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                  {mod.description}
                </p>
              </div>

              {/* Bottom Action Bar */}
              <div className="pt-4 mt-4 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs font-bold text-[#0B1F3A] dark:text-blue-300 group-hover:text-blue-700 dark:group-hover:text-white">
                <span>Acessar Módulo</span>
                <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
            </button>
          ))}
        </div>

        {/* Bottom Institutional Assurance Strip */}
        <div className="max-w-4xl mx-auto pt-4 border-t border-slate-200/80 dark:border-slate-800/80 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Conformidade LGPD (Anonimização Irreversível HMAC-SHA256)</span>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-700 dark:text-blue-400" />
            <span>Interoperabilidade por Chave Geográfica IBGE e Comissões Permanentes</span>
          </div>
        </div>
      </div>
    </div>
  );
};
