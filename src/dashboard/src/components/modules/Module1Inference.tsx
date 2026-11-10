import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  Users,
  CheckCircle2,
  Database,
  Sliders,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Compass,
  Scale,
  BarChart2,
  Newspaper,
  Megaphone,
  Eye,
} from 'lucide-react';
import { ThemeDataset, PlatformId, AuditRecord } from '../../types';
import { PLATFORM_INFO } from '../../data/mockData';

interface Module1InferenceProps {
  dataset: ThemeDataset;
  activePlatforms: Set<PlatformId>;
  goldSampleSize: number;
  onInspectRecord: (record: AuditRecord) => void;
  onNavigateToReport?: () => void;
}

export const Module1Inference: React.FC<Module1InferenceProps> = ({
  dataset,
  activePlatforms,
  goldSampleSize,
  onInspectRecord,
  onNavigateToReport,
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('rogan_gladen');
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const [termsViewMode, setTermsViewMode] = useState<'bars' | 'cloud' | 'table'>('bars');
  const [searchAuditTerm, setSearchAuditTerm] = useState<string>('');
  const [filterStance, setFilterStance] = useState<string>('TODOS');
  const [filterPlatform, setFilterPlatform] = useState<string>('TODAS');

  const {
    title,
    committee,
    legislativeContext,
    narrativeInsights,
    medallion,
    scenarios,
    platforms,
    homogeneityTest,
    rakingDiagnostics,
    auditRecords,
    topTerms = [],
    pressHighlights = [],
    influentialProfiles = [],
    watchpoints = [],
  } = dataset;

  const officialScenario = useMemo(
    () => scenarios.find((s) => s.scenarioId === 'rogan_gladen') || scenarios[0],
    [scenarios]
  );

  const selectedScenario = useMemo(
    () => scenarios.find((s) => s.scenarioId === selectedScenarioId) || officialScenario,
    [scenarios, selectedScenarioId, officialScenario]
  );

  const filteredPlatforms = useMemo(() => {
    return platforms.filter((p) => activePlatforms.has(p.platformId));
  }, [platforms, activePlatforms]);

  const activeNOrg = useMemo(() => {
    return filteredPlatforms.reduce((acc, p) => acc + p.nOrg, 0);
  }, [filteredPlatforms]);

  const filteredAuditRecords = useMemo(() => {
    return auditRecords.filter((rec) => {
      if (filterStance !== 'TODOS' && rec.stance !== filterStance) {
        return false;
      }
      if (filterPlatform !== 'TODAS' && rec.platform !== filterPlatform) {
        return false;
      }
      if (searchAuditTerm.trim()) {
        const query = searchAuditTerm.toLowerCase();
        const matchesText = rec.sanitizedText.toLowerCase().includes(query);
        const matchesId = rec.id.toLowerCase().includes(query);
        const matchesSpectrum = rec.spectrumName.toLowerCase().includes(query);
        return matchesText || matchesId || matchesSpectrum;
      }
      return true;
    });
  }, [auditRecords, filterStance, filterPlatform, searchAuditTerm]);

  const maxTermMentions = useMemo(() => {
    return Math.max(...topTerms.map((t) => t.mentions), 1);
  }, [topTerms]);

  const getStanceColorHex = (stance: 'FAVORAVEL' | 'CONTRARIO' | 'NEUTRO') => {
    if (stance === 'FAVORAVEL') return '#0072B2';
    if (stance === 'CONTRARIO') return '#D55E00';
    return '#64748B';
  };

  const getStanceLabel = (stance: 'FAVORAVEL' | 'CONTRARIO' | 'NEUTRO') => {
    if (stance === 'FAVORAVEL') return 'Favorável';
    if (stance === 'CONTRARIO') return 'Contrário';
    return 'Neutro / Técnico';
  };

  return (
    <div className="max-w-[1360px] mx-auto space-y-8 pb-12">
      {/* 1. Executive Synthesis Banner (Focal Anchor) */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-100 dark:border-slate-800">
          <div className="space-y-1 flex-1 min-w-[280px]">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
              <span>Comissão: {committee}</span>
              <span className="mx-2">·</span>
              <span>Universo Orgânico: {activeNOrg.toLocaleString('pt-BR')} cidadãos únicos</span>
              <span className="mx-2">·</span>
              <span>Margem de incerteza: ±{medallion.marginOfError} p.p.</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight prose-justified">
              {title}
            </h2>
          </div>

          {onNavigateToReport && (
            <button
              onClick={onNavigateToReport}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#0B1F3A] hover:bg-blue-950 text-white text-xs font-semibold transition-colors whitespace-nowrap shrink-0"
            >
              <FileText className="w-4 h-4 text-[#DFBA4E]" />
              <span>Ler Relatório Descritivo Completo</span>
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6 items-center">
          {/* Left 7 cols: Justified plain-language narrative explanation */}
          <div className="lg:col-span-7 space-y-3">
            <div className="text-xs font-semibold text-blue-800 dark:text-blue-300 prose-justified">
              Síntese Interpretativa do Debate Público
            </div>
            <p className="text-sm sm:text-[15px] text-slate-700 dark:text-slate-200 leading-relaxed font-serif-editorial prose-justified">
              {narrativeInsights.executiveLead}
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed pt-1 prose-justified">
              Contexto Legislativo: {legislativeContext}
            </p>
          </div>

          {/* Right 5 cols: Official Estimate Summary Bar */}
          <div className="lg:col-span-5 p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-900 dark:text-white">
                Estimativa Oficial (Pós-Expurgo de Robôs)
              </span>
              <span className="text-slate-500 dark:text-slate-400 font-mono tabular-nums">
                IC 95%
              </span>
            </div>

            {/* Big Segmented Visual Bar */}
            <div className="h-4 w-full rounded-md overflow-hidden flex bg-slate-200 dark:bg-slate-700">
              <div
                style={{ width: `${officialScenario.favoravel}%` }}
                className="bg-[#0072B2] h-full transition-all duration-300"
                title={`Favorável: ${officialScenario.favoravel}%`}
              />
              <div
                style={{ width: `${officialScenario.contrario}%` }}
                className="bg-[#D55E00] h-full transition-all duration-300"
                title={`Contrário: ${officialScenario.contrario}%`}
              />
              <div
                style={{ width: `${officialScenario.neutro}%` }}
                className="bg-[#64748B] h-full transition-all duration-300"
                title={`Neutro: ${officialScenario.neutro}%`}
              />
            </div>

            {/* 3 Clear Pillars */}
            <div className="grid grid-cols-3 gap-3 pt-1">
              <div>
                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#0072B2]" />
                  <span>Favorável</span>
                </div>
                <div className="text-xl font-bold font-mono tabular-nums text-slate-900 dark:text-white mt-0.5">
                  {officialScenario.favoravel.toFixed(1)}%
                </div>
                <div className="text-[11px] font-mono tabular-nums text-slate-400">
                  [{officialScenario.favoravelCi[0]}% – {officialScenario.favoravelCi[1]}%]
                </div>
              </div>

              <div>
                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#D55E00]" />
                  <span>Contrário</span>
                </div>
                <div className="text-xl font-bold font-mono tabular-nums text-slate-900 dark:text-white mt-0.5">
                  {officialScenario.contrario.toFixed(1)}%
                </div>
                <div className="text-[11px] font-mono tabular-nums text-slate-400">
                  [{officialScenario.contrarioCi[0]}% – {officialScenario.contrarioCi[1]}%]
                </div>
              </div>

              <div>
                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-600 dark:text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#64748B]" />
                  <span>Neutro</span>
                </div>
                <div className="text-xl font-bold font-mono tabular-nums text-slate-900 dark:text-white mt-0.5">
                  {officialScenario.neutro.toFixed(1)}%
                </div>
                <div className="text-[11px] font-mono tabular-nums text-slate-400">
                  [{officialScenario.neutroCi[0]}% – {officialScenario.neutroCi[1]}%]
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Instituto DX Inspired Section: Eixos Temáticos & Disputa de Narrativas */}
      {narrativeInsights.thematicAxes && narrativeInsights.thematicAxes.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          {/* Left 7 cols: Eixos Temáticos do Debate (% Publicações vs % Interações) */}
          <section className="lg:col-span-7 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                  <Compass className="w-4 h-4" />
                  <span>Dinâmica da Conversa Pública</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                  Eixos Temáticos Predominantes (Publicações vs. Interações)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                  Divisão do debate segundo os subtemas que mais geraram postagens e engajamento na janela analisada.
                </p>
              </div>

              <div className="space-y-5 pt-1">
                {narrativeInsights.thematicAxes.map((axis, idx) => (
                  <div
                    key={axis.id}
                    className="p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 space-y-3"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white prose-justified">
                        0{idx + 1}. {axis.name}
                      </h4>
                      <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                        Predominância: <strong className="text-slate-800 dark:text-slate-200">{axis.dominantField}</strong>
                      </span>
                    </div>

                    {/* Dual Progress Bar: Posts vs Interactions */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-500 dark:text-slate-400">Volume de Publicações</span>
                          <span className="font-mono font-bold tabular-nums text-slate-900 dark:text-white">
                            {axis.sharePostsPercent}%
                          </span>
                        </div>
                        <div className="h-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            style={{ width: `${axis.sharePostsPercent}%` }}
                            className="bg-[#0B1F3A] dark:bg-blue-500 h-full rounded-full"
                          />
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-500 dark:text-slate-400">Volume de Interações</span>
                          <span className="font-mono font-bold tabular-nums text-amber-700 dark:text-amber-400">
                            {axis.shareInteractionsPercent}%
                          </span>
                        </div>
                        <div className="h-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                          <div
                            style={{ width: `${axis.shareInteractionsPercent}%` }}
                            className="bg-[#C59B27] h-full rounded-full"
                          />
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified pt-1">
                      {axis.summary}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Right 5 cols: Disputa de Narrativas por Campo Político-Discursivo */}
          <section className="lg:col-span-5 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                  <Scale className="w-4 h-4" />
                  <span>Análise Qualitativa de Enquadramento</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                  A Disputa de Narrativas em Circulação
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                  Como os principais campos de opinião estruturam seus discursos e palavras-chave.
                </p>
              </div>

              <div className="space-y-5 pt-1">
                {narrativeInsights.fieldDisputes.map((disp) => (
                  <div
                    key={disp.fieldId}
                    className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30 space-y-3"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: disp.colorHex }} />
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white prose-justified">
                          {disp.fieldName}
                        </h4>
                      </div>
                      <span className="text-xs font-mono font-bold tabular-nums text-slate-600 dark:text-slate-300 shrink-0">
                        {disp.shareWithinTheme.toFixed(1)}% do debate
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 prose-justified">
                      Enquadramento: {disp.centralFrame}
                    </div>

                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                      {disp.detailedNarrative}
                    </p>

                    <div className="pt-2 border-t border-slate-200/70 dark:border-slate-800 flex items-center gap-2 flex-wrap text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      <span>Termos-chave:</span>
                      {disp.keyHashtagsOrTerms.map((tag, i) => (
                        <React.Fragment key={tag}>
                          {i > 0 && <span>·</span>}
                          <span className="text-slate-700 dark:text-slate-300">#{tag}</span>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      )}

      {/* 3. Multi-Format Data Visualization: Termos Mais Falados (Colunas Horizontais | Nuvem de Palavras | Tabela) */}
      {topTerms.length > 0 && (
        <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
            <div className="space-y-1 max-w-2xl">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                <BarChart2 className="w-4 h-4" />
                <span>Ferramenta de Visualização de Vocabulário</span>
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Termos e Expressões Mais Falados no Debate
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                Explore os conceitos de maior recorrência nas manifestações orgânicas alternando entre Gráfico de Colunas Horizontais, Nuvem de Palavras Ponderada e Tabela Comparativa.
              </p>
            </div>

            {/* Interactive View Switcher */}
            <div className="inline-flex rounded-lg p-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shrink-0">
              <button
                onClick={() => setTermsViewMode('bars')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                  termsViewMode === 'bars'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Colunas Horizontais
              </button>
              <button
                onClick={() => setTermsViewMode('cloud')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                  termsViewMode === 'cloud'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Nuvem de Palavras
              </button>
              <button
                onClick={() => setTermsViewMode('table')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                  termsViewMode === 'table'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Tabela de Dados
              </button>
            </div>
          </div>

          {/* View 1: Horizontal Column Bars */}
          {termsViewMode === 'bars' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 pt-1">
              {topTerms.map((item, idx) => {
                const barWidth = Math.max(12, Math.round((item.mentions / maxTermMentions) * 100));
                const colorHex = getStanceColorHex(item.predominantStance);

                return (
                  <div key={item.term} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-800 dark:text-slate-200">
                        {idx + 1}. {item.term}
                      </span>
                      <span className="font-mono tabular-nums text-slate-500">
                        <strong className="text-slate-900 dark:text-white">{item.mentions.toLocaleString('pt-BR')}</strong> menções ({item.sharePercent.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-3.5 w-full bg-slate-100 dark:bg-slate-800 rounded-md overflow-hidden flex items-center">
                      <div
                        style={{ width: `${barWidth}%`, backgroundColor: colorHex }}
                        className="h-full rounded-md transition-all duration-300"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* View 2: Weighted Word Cloud */}
          {termsViewMode === 'cloud' && (
            <div className="p-8 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200/80 dark:border-slate-800 flex flex-wrap items-center justify-center gap-x-7 gap-y-5 min-h-[220px]">
              {topTerms.map((item) => {
                const ratio = item.mentions / maxTermMentions;
                const fontSizeRem = 0.85 + ratio * 1.15; // 0.85rem to 2.0rem
                const colorHex = getStanceColorHex(item.predominantStance);

                return (
                  <div
                    key={item.term}
                    style={{ fontSize: `${fontSizeRem}rem`, color: colorHex }}
                    className="font-bold tracking-tight transition-transform hover:scale-105 cursor-default flex items-baseline gap-1.5"
                    title={`${item.mentions.toLocaleString('pt-BR')} menções (${item.sharePercent}% do debate) · Predominância: ${getStanceLabel(item.predominantStance)}`}
                  >
                    <span>{item.term}</span>
                    <span className="text-[11px] font-mono font-normal opacity-75 tabular-nums">
                      ({item.sharePercent.toFixed(1)}%)
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* View 3: Structured Data Table */}
          {termsViewMode === 'table' && (
            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-lg">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-2.5 px-4">Posição & Termo</th>
                    <th className="py-2.5 px-4 text-right">Volume de Menções</th>
                    <th className="py-2.5 px-4 text-right">Participação (%)</th>
                    <th className="py-2.5 px-4">Posicionamento Predominante Associado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {topTerms.map((item, idx) => (
                    <tr key={item.term}>
                      <td className="py-2.5 px-4 font-semibold text-slate-800 dark:text-slate-200">
                        {idx + 1}. {item.term}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono tabular-nums font-bold text-slate-900 dark:text-white">
                        {item.mentions.toLocaleString('pt-BR')}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono tabular-nums text-slate-600 dark:text-slate-400">
                        {item.sharePercent.toFixed(1)}%
                      </td>
                      <td className="py-2.5 px-4 font-semibold" style={{ color: getStanceColorHex(item.predominantStance) }}>
                        {getStanceLabel(item.predominantStance)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>Cores indicam a postura onde o termo é mais acionado:</span>
            <div className="flex items-center gap-4 font-medium">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#0072B2]" /> Favorável
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#D55E00]" /> Contrário
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-xs bg-[#64748B]" /> Neutro / Técnico
              </span>
            </div>
          </div>
        </section>
      )}

      {/* 4. Perfis e Atores que Pautam o Debate (Positivo, Negativo e Neutro) & Destaques da Imprensa */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Left 7 cols: Perfis Influentes por Postura */}
        {influentialProfiles.length > 0 && (
          <section className="lg:col-span-7 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                  <Megaphone className="w-4 h-4" />
                  <span>Lideranças de Opinião nas Redes</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                  Perfis e Atores que Pautam o Debate (Favorável, Contrário e Neutro)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                  Agrupamento dos perfis públicos e hubs de influência que concentraram a tração de cada corrente de opinião.
                </p>
              </div>

              <div className="space-y-4">
                {influentialProfiles.map((prof, i) => {
                  const colorHex = getStanceColorHex(prof.stance);
                  const stanceLabel = getStanceLabel(prof.stance);

                  return (
                    <div
                      key={i}
                      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30 space-y-2"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: colorHex }} />
                          <h4 className="text-sm font-bold text-slate-900 dark:text-white prose-justified">
                            {prof.name}
                          </h4>
                        </div>
                        <span className="text-xs font-semibold" style={{ color: colorHex }}>
                          Pauta {stanceLabel} · {prof.engagementShare}
                        </span>
                      </div>

                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        <span>Redes principais: <strong className="text-slate-700 dark:text-slate-300">{prof.platform}</strong></span>
                        <span className="mx-2">·</span>
                        <span>Segmento: {prof.category}</span>
                      </div>

                      <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified pt-1">
                        {prof.coreMessage}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* Right 5 cols: Destaques da Imprensa */}
        {pressHighlights.length > 0 && (
          <section className="lg:col-span-5 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                  <Newspaper className="w-4 h-4" />
                  <span>Repercussão Editorial</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                  Destaques da Imprensa Compartilhados nas Redes
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
                  Manchetes e coberturas jornalísticas que mais alimentaram os argumentos das comunidades digitais.
                </p>
              </div>

              <div className="space-y-4">
                {pressHighlights.map((press, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                      <span className="font-bold text-slate-800 dark:text-slate-200">{press.outlet}</span>
                      <span>{press.dateStr} · {press.framing}</span>
                    </div>
                    <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white leading-snug prose-justified">
                      “{press.headline}”
                    </h4>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                      {press.repercussionSummary}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </div>

      {/* 5. Pontos de Atenção para Continuar Observando no Monitoramento */}
      {watchpoints.length > 0 && (
        <section className="p-7 rounded-xl border border-amber-200/90 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10 space-y-5">
          <div className="border-b border-amber-200/60 dark:border-amber-900/40 pb-4 space-y-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 dark:text-amber-400">
              <Eye className="w-4 h-4" />
              <span>Radar Prospectivo DataSenado</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
              Pontos de Atenção para Continuar Observando no Monitoramento
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 prose-justified">
              Fatores críticos, possíveis desdobramentos legislativos e movimentos de rede que exigem acompanhamento contínuo nos próximos dias.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {watchpoints.map((wp, i) => (
              <div
                key={i}
                className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-amber-800 dark:text-amber-400">
                      {wp.riskOrOpportunity === 'ALERTA'
                        ? 'Alerta de Curto Prazo'
                        : wp.riskOrOpportunity === 'AGENDA_LEGISLATIVA'
                        ? 'Janela Legislativa'
                        : 'Tendência em Formação'}
                    </span>
                    <span className="font-mono text-[11px] text-slate-400">{wp.horizon}</span>
                  </div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug prose-justified">
                    {wp.title}
                  </h4>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                    {wp.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 6. Clean 5-Stage Data Quality & Medallion Strip */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white prose-justified">
            Funil de Qualidade e Higienização da Amostra (Bronze → Silver → Gold)
          </h3>
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="flex items-center gap-1.5 text-xs font-medium text-blue-700 dark:text-blue-400 hover:underline"
          >
            <span>
              {showTechnicalDetails
                ? 'Ocultar parâmetros matemáticos'
                : 'Ver parâmetros matemáticos (DEFF, PSI, Youden)'}
            </span>
            {showTechnicalDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>1. Coleta Bruta (Bronze)</span>
              <Database className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              {medallion.bronzeTotal.toLocaleString('pt-BR')}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Postagens capturadas nas 6 redes
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-red-700 dark:text-red-400 font-medium">
              <span>2. Expurgo de Robôs (Silver)</span>
              <ShieldAlert className="w-4 h-4 text-red-600 dark:text-red-400" />
            </div>
            <div className="text-2xl font-bold font-mono tabular-nums text-red-700 dark:text-red-400">
              {(medallion.silverSpam + medallion.silverCibBots).toLocaleString('pt-BR')}{' '}
              <span className="text-sm font-normal">({medallion.artificialityRate}%)</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Bloqueio de {medallion.silverBotAccounts} contas automatizadas e spam
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>3. Cidadãos Únicos (U_Org)</span>
              <Users className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-2xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              {activeNOrg.toLocaleString('pt-BR')}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Cada conta real equivale a 1 unidade
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>4. Amostra Auditada (Gold)</span>
              <Sliders className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              n = {goldSampleSize}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Sorteio estratificado · Margem ±{medallion.marginOfError} p.p.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>5. Precisão do Modelo</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              {(medallion.specificity * 100).toFixed(0)}% / {(medallion.sensitivity * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Especificidade e Sensibilidade (Kappa {medallion.cohenKappa})
            </p>
          </div>
        </div>

        {showTechnicalDetails && (
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100/70 dark:bg-slate-800/40 text-xs font-mono text-slate-600 dark:text-slate-300 flex flex-wrap items-center justify-between gap-4">
            <span>Kish DEFF = {medallion.kishDeff} (n_efetivo = {Math.round(goldSampleSize / medallion.kishDeff)})</span>
            <span>Índice de Youden J = {medallion.youdenJ} (&gt; 0.20 OK)</span>
            <span>Estabilidade MLOps Drift PSI = {medallion.psiDrift} ({medallion.psiStatus})</span>
            <span>Queries Bronze: {medallion.queriesUsed.join(', ')}</span>
          </div>
        )}
      </section>

      {/* 7. Scenarios Comparison + Descriptive Finding */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
          <div className="space-y-1 max-w-3xl">
            <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
              Comparação entre o Volume Bruto (com Robôs) e os Cenários Estatísticos Limpos
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
              {narrativeInsights.scenariosFinding}
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium shrink-0 pt-1">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-[#0072B2]" />
              <span className="text-slate-700 dark:text-slate-300">Favorável</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-[#D55E00]" />
              <span className="text-slate-700 dark:text-slate-300">Contrário</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-xs bg-[#64748B]" />
              <span className="text-slate-700 dark:text-slate-300">Neutro</span>
            </div>
          </div>
        </div>

        {/* Horizontal Comparison Rows */}
        <div className="space-y-4">
          {scenarios.map((scen) => {
            const isSelected = selectedScenarioId === scen.scenarioId;
            const isOfficial = scen.scenarioId === 'rogan_gladen';
            const isBruto = scen.scenarioId === 'bruto';

            return (
              <div
                key={scen.scenarioId}
                role="button"
                tabIndex={0}
                onClick={() => setSelectedScenarioId(scen.scenarioId)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedScenarioId(scen.scenarioId);
                  }
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-blue-600 dark:border-blue-500 bg-blue-50/30 dark:bg-blue-950/20'
                    : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                  <div className="lg:col-span-4 space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                        {scen.shortName}
                      </span>
                      {isOfficial && (
                        <span className="text-[11px] font-semibold text-blue-700 dark:text-blue-400">
                          · Referência Oficial
                        </span>
                      )}
                      {isBruto && (
                        <span className="text-[11px] font-semibold text-red-600 dark:text-red-400">
                          · Sem filtro de robôs
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-snug prose-justified">
                      {scen.description}
                    </p>
                  </div>

                  <div className="lg:col-span-5">
                    <div className="h-5 w-full bg-slate-100 dark:bg-slate-800 rounded-md overflow-hidden flex">
                      <div
                        style={{ width: `${scen.favoravel}%` }}
                        className="bg-[#0072B2] h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
                      >
                        {scen.favoravel >= 12 ? `${scen.favoravel.toFixed(1)}%` : ''}
                      </div>
                      <div
                        style={{ width: `${scen.contrario}%` }}
                        className="bg-[#D55E00] h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
                      >
                        {scen.contrario >= 12 ? `${scen.contrario.toFixed(1)}%` : ''}
                      </div>
                      <div
                        style={{ width: `${scen.neutro}%` }}
                        className="bg-[#64748B] h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
                      >
                        {scen.neutro >= 12 ? `${scen.neutro.toFixed(1)}%` : ''}
                      </div>
                    </div>
                  </div>

                  <div className="lg:col-span-3 flex items-center justify-end gap-4 font-mono text-xs tabular-nums">
                    <div className="text-right">
                      <span className="text-[#0072B2] font-bold block">{scen.favoravel.toFixed(1)}%</span>
                      <span className="text-[10px] text-slate-400">
                        [{scen.favoravelCi[0]}–{scen.favoravelCi[1]}]
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[#D55E00] font-bold block">{scen.contrario.toFixed(1)}%</span>
                      <span className="text-[10px] text-slate-400">
                        [{scen.contrarioCi[0]}–{scen.contrarioCi[1]}]
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[#64748B] font-bold block">{scen.neutro.toFixed(1)}%</span>
                      <span className="text-[10px] text-slate-400">
                        [{scen.neutroCi[0]}–{scen.neutroCi[1]}]
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {selectedScenario.biasNote && (
          <div className="pt-2 text-xs text-slate-500 dark:text-slate-400 flex items-center justify-between border-t border-slate-100 dark:border-slate-800">
            <span className="prose-justified">
              <strong>Nota sobre {selectedScenario.shortName}:</strong> {selectedScenario.biasNote}
            </span>
            {selectedScenario.formula && (
              <code className="font-mono text-[11px] text-slate-500 ml-4 shrink-0">{selectedScenario.formula}</code>
            )}
          </div>
        )}
      </section>

      {/* 8. Platform Breakdown & Regional Calibration (2 Spacious Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Left 7 cols: 6 Platforms */}
        <section className="lg:col-span-7 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Comportamento por Rede Social ({filteredPlatforms.length} Plataformas)
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                {narrativeInsights.platformsFinding}
              </p>
            </div>

            <div className="space-y-4 pt-1">
              {filteredPlatforms.map((plat) => {
                const info = PLATFORM_INFO[plat.platformId] || { label: plat.platformName };

                return (
                  <div key={plat.platformId} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="font-semibold text-slate-800 dark:text-slate-200">
                        <span>{info.label}</span>
                        <span className="text-slate-400 font-normal ml-2 font-mono tabular-nums">
                          {plat.nOrg.toLocaleString('pt-BR')} contas ({plat.sharePercent.toFixed(1)}% do total)
                        </span>
                      </div>

                      <div className="flex items-center gap-3 font-mono text-xs tabular-nums">
                        <span className="text-[#0072B2] font-semibold">{plat.favoravel.toFixed(1)}% Fav</span>
                        <span className="text-[#D55E00] font-semibold">{plat.contrario.toFixed(1)}% Cont</span>
                        <span className="text-[#64748B]">{plat.neutro.toFixed(1)}% Neu</span>
                      </div>
                    </div>

                    <div className="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-md flex overflow-hidden">
                      <div style={{ width: `${plat.favoravel}%` }} className="bg-[#0072B2] h-full" />
                      <div style={{ width: `${plat.contrario}%` }} className="bg-[#D55E00] h-full" />
                      <div style={{ width: `${plat.neutro}%` }} className="bg-[#64748B] h-full" />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 flex flex-wrap items-center justify-between gap-2">
            <span className="prose-justified">{homogeneityTest.interpretation}</span>
            <span className="font-mono text-[11px] tabular-nums text-slate-400">
              χ² = {homogeneityTest.chi2Adjusted} · V de Cramér = {homogeneityTest.cramerV}
            </span>
          </div>
        </section>

        {/* Right 5 cols: Regional Calibration IBGE */}
        <section className="lg:col-span-5 p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Representatividade Regional (IBGE)
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                {narrativeInsights.regionalFinding}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-medium">
                    <th className="py-2.5 pr-2">Macrorregião</th>
                    <th className="py-2.5 px-2 text-right">Meta IBGE</th>
                    <th className="py-2.5 px-2 text-right">Amostra</th>
                    <th className="py-2.5 pl-2 text-right">Diferença</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/70">
                  {rakingDiagnostics.map((reg) => (
                    <tr key={reg.region}>
                      <td className="py-3 pr-2">
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{reg.region}</div>
                        <div className="text-[11px] text-slate-400">{reg.ufs.slice(0, 4).join(', ')}</div>
                      </td>
                      <td className="py-3 px-2 text-right font-mono tabular-nums text-slate-600 dark:text-slate-400">
                        {reg.targetIbgePercent.toFixed(1)}%
                      </td>
                      <td className="py-3 px-2 text-right font-mono tabular-nums font-semibold text-slate-900 dark:text-white">
                        {reg.obtainedPercent.toFixed(1)}%
                      </td>
                      <td className="py-3 pl-2 text-right font-mono tabular-nums text-emerald-600 dark:text-emerald-400">
                        {reg.gapPp > 0 ? `+${reg.gapPp.toFixed(1)}` : reg.gapPp.toFixed(1)} p.p.
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 prose-justified">
            Calibragem Raking IPF convergente em todas as 27 Unidades da Federação (pesos limitados entre 0,25 e 4,0).
          </div>
        </section>
      </div>

      {/* 9. Audit Sample Table + XAI Inspection */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
              Amostras Reais Auditáveis e Explicabilidade da Classificação
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
              Clique em qualquer manifestação abaixo para inspecionar quais palavras determinaram a classificação (SHAP / LIME)
            </p>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar palavra ou grupo..."
                value={searchAuditTerm}
                onChange={(e) => setSearchAuditTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs w-56 focus:outline-none focus:ring-2 focus:ring-blue-600/30"
              />
            </div>

            <select
              value={filterStance}
              onChange={(e) => setFilterStance(e.target.value)}
              className="py-1.5 px-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium cursor-pointer"
            >
              <option value="TODOS">Todas as Posturas</option>
              <option value="FAVORAVEL">Favorável</option>
              <option value="CONTRARIO">Contrário</option>
              <option value="NEUTRO">Neutro</option>
              <option value="QUARENTENA_CIB">Bloqueado (Robô/Spam)</option>
            </select>

            <select
              value={filterPlatform}
              onChange={(e) => setFilterPlatform(e.target.value)}
              className="py-1.5 px-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium cursor-pointer"
            >
              <option value="TODAS">Todas as Redes</option>
              <option value="x_twitter">X (Twitter)</option>
              <option value="telegram">Telegram</option>
              <option value="youtube">YouTube</option>
              <option value="instagram_facebook">Instagram/FB</option>
              <option value="tiktok">TikTok</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-medium">
                <th className="py-3 px-3">Rede · UF</th>
                <th className="py-3 px-3">Manifestação Pública (Anonimizada LGPD)</th>
                <th className="py-3 px-3">Posicionamento</th>
                <th className="py-3 px-3">Palavras-Chave Decisivas</th>
                <th className="py-3 px-3">Comunidade</th>
                <th className="py-3 px-3 text-right">Auditoria</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/70">
              {filteredAuditRecords.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Nenhum registro encontrado para os filtros selecionados.
                  </td>
                </tr>
              ) : (
                filteredAuditRecords.map((rec) => {
                  const platInfo = PLATFORM_INFO[rec.platform] || { short: rec.platform };
                  const isFav = rec.stance === 'FAVORAVEL';
                  const isCont = rec.stance === 'CONTRARIO';
                  const isNeu = rec.stance === 'NEUTRO';
                  const isCib = rec.stance === 'QUARENTENA_CIB';

                  return (
                    <tr
                      key={rec.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => onInspectRecord(rec)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onInspectRecord(rec);
                        }
                      }}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors group"
                    >
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{platInfo.short}</span>
                        <span className="mx-1.5 text-slate-300">·</span>
                        <span className="text-slate-500">{rec.uf}</span>
                      </td>
                      <td className="py-3.5 px-3 text-slate-700 dark:text-slate-200 max-w-md leading-relaxed prose-justified">
                        {rec.sanitizedText}
                      </td>
                      <td className="py-3.5 px-3 whitespace-nowrap font-semibold">
                        {isFav && <span className="text-[#0072B2]">Favorável</span>}
                        {isCont && <span className="text-[#D55E00]">Contrário</span>}
                        {isNeu && <span className="text-[#64748B]">Neutro</span>}
                        {isCib && <span className="text-red-600 dark:text-red-400">Robô / Spam</span>}
                      </td>
                      <td className="py-3.5 px-3 font-mono text-[11px] text-slate-500 dark:text-slate-400 max-w-[200px] truncate">
                        {rec.decisiveTerms.join(', ')}
                      </td>
                      <td className="py-3.5 px-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                        {rec.spectrumName.split('/')[0]}
                      </td>
                      <td className="py-3.5 px-3 text-right whitespace-nowrap">
                        <span className="text-blue-600 dark:text-blue-400 group-hover:underline font-medium inline-flex items-center gap-1">
                          Explicar <ExternalLink className="w-3 h-3" />
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
