import React, { useState } from 'react';
import {
  Radio,
  ArrowRight,
  Flame,
  Trash2,
  Landmark,
} from 'lucide-react';
import { BoilingTopic } from '../../types';
import { BOILING_TOPICS_LIST } from '../../data/mockData';
import { useToast } from '../Toast';

interface Module3LegislativeRadarProps {
  onDrilldownTopic: (themeIdTarget: string) => void;
}

export const Module3LegislativeRadar: React.FC<Module3LegislativeRadarProps> = ({
  onDrilldownTopic,
}) => {
  const { showToast } = useToast();
  const [filterSenateOnly, setFilterSenateOnly] = useState<boolean>(true);
  const [topics] = useState<BoilingTopic[]>(BOILING_TOPICS_LIST);

  const displayedTopics = filterSenateOnly
    ? topics.filter((t) => t.isSenateInterest)
    : topics;

  const handleDrilldown = (topic: BoilingTopic) => {
    if (topic.themeIdTarget) {
      onDrilldownTopic(topic.themeIdTarget);
      showToast(
        'info',
        'Tema Carregado no Panorama Principal',
        `Exibindo a análise completa de: ${topic.title}`
      );
    } else {
      showToast(
        'warning',
        'Tema Sem Coleta Ativa',
        'Utilize o botão "Monitorar Novo Tema" na barra superior para iniciar o acompanhamento desta pauta.'
      );
    }
  };

  return (
    <div className="max-w-[1360px] mx-auto space-y-8 pb-12 select-none">
      {/* 1. Header & Explanation */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
          <div className="space-y-1 max-w-2xl">
            <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
              <Radio className="w-4 h-4" />
              <span>Expediente Matinal · Triagem de Pautas das Últimas 24 Horas</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Radar Diário de Pautas em Ebulição e Cruzamento com Comissões
            </h2>
          </div>

          {/* Segmented Control */}
          <div className="inline-flex rounded-lg p-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setFilterSenateOnly(true)}
              className={`px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                filterSenateOnly
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Pautas Legislativas ({topics.filter((t) => t.isSenateInterest).length})
            </button>
            <button
              onClick={() => setFilterSenateOnly(false)}
              className={`px-3.5 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                !filterSenateOnly
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Ver Ruído Descartado ({topics.length})
            </button>
          </div>
        </div>

        <p className="text-sm sm:text-[15px] text-slate-700 dark:text-slate-200 leading-relaxed font-serif-editorial prose-justified">
          Todas as manhãs, o Radar identifica quais assuntos apresentaram crescimento abrupto de menções nas redes sociais e separa automaticamente os temas que possuem vínculo com as Comissões Permanentes do Senado Federal de assuntos gerais de entretenimento ou esportes.
        </p>
      </section>

      {/* 2. Topic Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {displayedTopics.map((topic) => {
          const isSenate = topic.isSenateInterest;

          return (
            <div
              key={topic.id}
              className={`p-6 rounded-xl border flex flex-col justify-between space-y-5 transition-all ${
                isSenate
                  ? 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'
                  : 'border-slate-200/70 dark:border-slate-800/50 bg-slate-50 dark:bg-slate-900/40 opacity-75'
              }`}
            >
              <div className="space-y-3">
                {/* Metadata Line (Unboxed clean text) */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 font-medium">
                    <span className="text-blue-800 dark:text-blue-300 font-semibold">
                      Comissão: {topic.committee}
                    </span>
                    {topic.cusumTriggered && isSenate && (
                      <>
                        <span className="text-slate-300">·</span>
                        <span className="text-amber-700 dark:text-amber-400 flex items-center gap-1 font-semibold">
                          <Flame className="w-3.5 h-3.5" />
                          Alta aceleração (+{topic.growth24h}% em 24h)
                        </span>
                      </>
                    )}
                    {!isSenate && (
                      <>
                        <span className="text-slate-300">·</span>
                        <span className="text-slate-500 flex items-center gap-1">
                          <Trash2 className="w-3.5 h-3.5" />
                          Entretenimento / Descartado
                        </span>
                      </>
                    )}
                  </div>

                  <span className="font-mono text-xs tabular-nums text-slate-500">
                    Relevância: <strong className="text-slate-900 dark:text-white">{topic.relevanceScore}/100</strong>
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
                  {topic.title}
                </h3>

                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                  <strong className="text-slate-800 dark:text-slate-200">Encaminhamento sugerido:</strong>{' '}
                  {topic.suggestedAction}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-4">
                <div className="text-xs text-slate-500 font-mono tabular-nums">
                  <span>{topic.volume24h.toLocaleString('pt-BR')} menções</span>
                  <span className="mx-2">·</span>
                  <span>Índice B = {topic.burstinessGohBarabasi}</span>
                </div>

                {isSenate && (
                  <button
                    onClick={() => handleDrilldown(topic)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0B1F3A] hover:bg-blue-950 text-white font-semibold text-xs transition-colors whitespace-nowrap shrink-0"
                  >
                    <span>Analisar Pauta</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#DFBA4E]" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Footnote */}
      <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-start gap-3 text-xs text-slate-500 dark:text-slate-400">
        <Landmark className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed prose-justified">
          O detector de mudança brusca (CUSUM) e o índice de explosão temporal (Burstiness de Goh-Barabási) avaliam janelas de 5 minutos para diferenciar picos orgânicos de interesse legislativo das oscilações rotineiras de tráfego.
        </p>
      </div>
    </div>
  );
};
