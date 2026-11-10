import React, { useState } from 'react';
import {
  Network,
  Share2,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { ThemeDataset, BubbleGraphNode } from '../../types';

interface Module2BubblesProps {
  dataset: ThemeDataset;
}

export const Module2Bubbles: React.FC<Module2BubblesProps> = ({ dataset }) => {
  const {
    narrativeInsights,
    topological,
    spectrums,
    bubbleNodes,
    bubbleEdges,
    grangerCausality,
    consensusBridges = [],
    divergencePoints = [],
  } = dataset;

  const [selectedNode, setSelectedNode] = useState<BubbleGraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<BubbleGraphNode | null>(null);
  const [showTopologicalMath, setShowTopologicalMath] = useState<boolean>(false);

  const getSpectrumColor = (spectrumId: string) => {
    const s = spectrums.find((sp) => sp.id === spectrumId);
    return s?.colorHex || '#64748B';
  };

  return (
    <div className="max-w-[1360px] mx-auto space-y-8 pb-12 select-none">
      {/* 1. Executive Narrative Lead on Bubbles & Polarization */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="space-y-1 max-w-3xl">
            <div className="text-xs font-semibold text-blue-800 dark:text-blue-300 prose-justified">
              Mapeamento de Comunidades & Diálogo Transversal
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white prose-justified">
              Como as Comunidades Digitais se Organizam neste Debate
            </h2>
          </div>

          <button
            onClick={() => setShowTopologicalMath(!showTopologicalMath)}
            className="flex items-center gap-1.5 text-xs font-medium text-blue-700 dark:text-blue-400 hover:underline"
          >
            <span>
              {showTopologicalMath
                ? 'Ocultar métricas topológicas'
                : 'Ver índices matemáticos (Modularidade Q, E-I, Granger)'}
            </span>
            {showTopologicalMath ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        <p className="text-sm sm:text-[15px] text-slate-700 dark:text-slate-200 leading-relaxed font-serif-editorial prose-justified">
          {narrativeInsights.bubblesFinding}
        </p>

        {/* 3 Clear Indicators in Plain Language */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-2">
          <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Nível de Isolamento entre Grupos</span>
              <Layers className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">
              {topological.homophilyCategory === 'CÂMARA DE ECO FECHADA'
                ? 'Alto (Bolhas Fechadas)'
                : 'Moderado (Com Diálogo)'}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
              Índice E-I de {topological.homophilyKrackhardtEI} (quanto mais negativo, mais fechado o grupo)
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Contas-Ponte (Mediadores)</span>
              <Share2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div className="text-xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              {topological.crossBubbleBridgeRate}% das contas
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
              Perfis orgânicos que conversam e são compartilhados por lados opostos
            </p>
          </div>

          <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Separação Estrutural de Comunidades</span>
              <Network className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="text-xl font-bold font-mono tabular-nums text-slate-900 dark:text-white">
              Q = {topological.modularityObserved.toFixed(2)}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
              {spectrums.length} comunidades nítidas identificadas no universo limpo
            </p>
          </div>
        </div>

        {showTopologicalMath && (
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-100/70 dark:bg-slate-800/40 text-xs font-mono text-slate-600 dark:text-slate-300 flex flex-wrap items-center justify-between gap-4">
            <span>Newman Q_obs = {topological.modularityObserved} vs Q_null = {topological.modularityNull} (z = {topological.zScore}, p &lt; 0.0001)</span>
            <span>Propagação Harmônica: F^(t+1) = αSF^(t) + (1-α)Y</span>
            <span>Critério Ponte Guimerà-Amaral: P_i &gt; 0.30</span>
          </div>
        )}
      </section>

      {/* 2. Interactive Topological Map */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-5">
        <div className="space-y-1.5">
          <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
            Mapa de Conexões entre as Comunidades e Pontes de Diálogo
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
            Passe o mouse ou clique nos círculos para inspecionar os perfis de referência de cada comunidade e as pontes de diálogo transversal (linhas tracejadas que conectam campos distintos).
          </p>
        </div>

        <div className="relative bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200/80 dark:border-slate-800 overflow-hidden h-[380px] flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 680 480">
            <defs>
              <pattern id="gridPatternClean" width="40" height="40" patternUnits="userSpaceOnUse">
                <path
                  d="M 40 0 L 0 0 0 40"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="0.5"
                  className="text-slate-200/60 dark:text-slate-800/50"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#gridPatternClean)" />

            {/* Edges */}
            {bubbleEdges.map((edge, idx) => {
              const src = bubbleNodes.find((n) => n.id === edge.source);
              const tgt = bubbleNodes.find((n) => n.id === edge.target);
              if (!src || !tgt) return null;

              const isCross = edge.isCrossSpectrum;
              return (
                <line
                  key={idx}
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={isCross ? '#CC79A7' : '#94A3B8'}
                  strokeWidth={isCross ? 2 : Math.max(1.2, edge.weight * 0.35)}
                  strokeDasharray={isCross ? '5,5' : undefined}
                  strokeOpacity={isCross ? 0.85 : 0.4}
                />
              );
            })}

            {/* Nodes */}
            {bubbleNodes.map((node) => {
              const color = getSpectrumColor(node.spectrumId);
              const isHovered = hoveredNode?.id === node.id;
              const isSelected = selectedNode?.id === node.id;

              return (
                <g
                  key={node.id}
                  className="cursor-pointer"
                  onMouseEnter={() => setHoveredNode(node)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => setSelectedNode(node)}
                >
                  {node.isBridge && (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={node.radius + 6}
                      fill="none"
                      stroke="#CC79A7"
                      strokeWidth="1.75"
                      strokeDasharray="3,3"
                    />
                  )}

                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={isHovered || isSelected ? node.radius + 3 : node.radius}
                    fill={color}
                    fillOpacity={0.9}
                    stroke="#FFFFFF"
                    strokeWidth={isSelected ? 3 : 1.5}
                    className="transition-all duration-150"
                  />

                  <text
                    x={node.x}
                    y={node.y + node.radius + 14}
                    textAnchor="middle"
                    className="text-[10px] font-sans font-medium fill-slate-700 dark:fill-slate-300 pointer-events-none"
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {(hoveredNode || selectedNode) && (
            <div className="absolute bottom-4 left-4 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border border-slate-200 dark:border-slate-800 rounded-lg p-3.5 text-xs shadow-md max-w-xs space-y-1">
              <div className="flex items-center justify-between gap-3">
                <span className="font-bold text-slate-900 dark:text-white">
                  {(hoveredNode || selectedNode)?.label}
                </span>
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: getSpectrumColor((hoveredNode || selectedNode)!.spectrumId) }}
                />
              </div>
              <div className="text-slate-500 dark:text-slate-400 space-y-0.5">
                <div>Conexões ativas: {(hoveredNode || selectedNode)?.degree} interações</div>
                {(hoveredNode || selectedNode)?.isBridge && (
                  <div className="text-purple-700 dark:text-purple-300 font-medium">
                    Atua como Ponte de Diálogo entre grupos (P_i = {(hoveredNode || selectedNode)?.participationCoefficient})
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-5 flex-wrap text-xs text-slate-600 dark:text-slate-400">
          {spectrums.map((sp) => (
            <div key={sp.id} className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: sp.colorHex }} />
              <span className="font-medium text-slate-800 dark:text-slate-200">{sp.name}</span>
              <span className="font-mono text-slate-400 tabular-nums">({sp.shareOrg.toFixed(1)}%)</span>
            </div>
          ))}
        </div>
      </section>

      {/* 3. Pontos de Convergência (Verde) vs. Pontos de Divergência e Tensão (Vermelho) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
        {/* Left: Pontos de Convergência (Verde) */}
        <section className="p-7 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="border-b border-emerald-100 dark:border-emerald-900/40 pb-4 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="w-4 h-4" />
                <span>Pontos de Convergência (Consenso Transversal)</span>
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Onde os Diferentes Grupos Concordam
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                Mesmo em debates polarizados, a análise qualitativa de conteúdo identifica propostas e salvaguardas específicas que reúnem apoio simultâneo de correntes opostas.
              </p>
            </div>

            <div className="space-y-4">
              {consensusBridges.map((br, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-emerald-200/80 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-2"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm prose-justified">
                      {br.topic}
                    </h4>
                  </div>
                  <div className="text-xs font-semibold text-emerald-800 dark:text-emerald-300 prose-justified">
                    {br.supportLevel} · Une: {br.spectrumsInAgreement.join(' + ')}
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed prose-justified">
                    {br.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-emerald-100 dark:border-emerald-900/40 text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
            <strong>Síntese para Relatoria:</strong> {narrativeInsights.legislativeConclusion}
          </div>
        </section>

        {/* Right: Pontos de Divergência e Tensão (Vermelho) */}
        <section className="p-7 rounded-xl border border-red-200 dark:border-red-900/60 bg-white dark:bg-slate-900 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="border-b border-red-100 dark:border-red-900/40 pb-4 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-red-700 dark:text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span>Pontos de Divergência (Focos de Tensão e Disputa)</span>
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Onde os Diferentes Grupos Divergem Frontalmente
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                Mapeamento dos principais pontos de atrito e incompatibilidade argumentativa que concentram o embate direto e a rejeição mútua entre os polos do debate.
              </p>
            </div>

            <div className="space-y-4">
              {divergencePoints.map((dv, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-red-200/80 dark:border-red-900/50 bg-red-50/40 dark:bg-red-950/20 space-y-2"
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm prose-justified">
                      {dv.topic}
                    </h4>
                  </div>
                  <div className="text-xs font-semibold text-red-800 dark:text-red-300 prose-justified">
                    {dv.tensionLevel} · Em disputa: {dv.opposingFields.join(' vs. ')}
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed prose-justified">
                    {dv.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-red-100 dark:border-red-900/40 text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
            <strong>Alerta de Mediação Legislativa:</strong> Os pontos de divergência acima concentram o maior risco de obstrução e mobilização negativa caso não sejam endereçados por audiências públicas ou emendas de redação.
          </div>
        </section>
      </div>

      {/* 4. Narratives by Community (Spacious Cards Grid) */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-6">
        <div className="border-b border-slate-100 dark:border-slate-800 pb-4 space-y-1">
          <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
            Argumentos Centrais de Cada Comunidade
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 prose-justified">
            Resumo das principais teses defendidas por cada grupo orgânico (agrupados com mínimo de 5 contas para proteção de privacidade LGPD).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {spectrums.map((sp) => (
            <div
              key={sp.id}
              className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 border-b border-slate-200/70 dark:border-slate-800 pb-2.5">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="w-3.5 h-3.5 rounded-full shrink-0" style={{ backgroundColor: sp.colorHex }} />
                    <div className="font-bold text-slate-900 dark:text-white text-sm leading-snug text-left break-words">
                      {sp.name}
                    </div>
                  </div>
                  <span className="text-xs font-mono tabular-nums text-slate-500 dark:text-slate-400 shrink-0">
                    {sp.accountCount.toLocaleString('pt-BR')} contas ({sp.shareOrg.toFixed(1)}%)
                  </span>
                </div>

                {/* Mini stance bar inside community */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-mono tabular-nums">
                    <span className="text-[#0072B2] font-semibold">{sp.favoravel.toFixed(1)}% Favorável</span>
                    <span className="text-[#D55E00] font-semibold">{sp.contrario.toFixed(1)}% Contrário</span>
                    <span className="text-[#64748B]">{sp.neutro.toFixed(1)}% Neutro</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden flex">
                    <div style={{ width: `${sp.favoravel}%` }} className="bg-[#0072B2] h-full" />
                    <div style={{ width: `${sp.contrario}%` }} className="bg-[#D55E00] h-full" />
                    <div style={{ width: `${sp.neutro}%` }} className="bg-[#64748B] h-full" />
                  </div>
                </div>

                <div className="space-y-1.5 pt-1">
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Teses e Argumentos Predominantes:
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {sp.keyArguments.map((arg, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-slate-400 select-none">•</span>
                        <span className="prose-justified">{arg}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-200/70 dark:border-slate-800 text-xs text-slate-400 flex items-center justify-between gap-2">
                <span>Fontes mais citadas:</span>
                <span className="font-mono text-[11px] text-slate-600 dark:text-slate-300 truncate">
                  {sp.topDomains.join(' · ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Chronological Origin ("Quem Pautou Primeiro?") */}
      <section className="p-7 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="space-y-1 max-w-3xl">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-700 dark:text-blue-400" />
              <h3 className="text-base font-bold text-slate-900 dark:text-white prose-justified">
                Linha do Tempo: Quem Iniciou e Como Reagiu Cada Grupo
              </h3>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
              {narrativeInsights.firstMoverFinding}
            </p>
          </div>

          <div className="text-xs font-mono text-slate-500 dark:text-slate-400 pt-1">
            Causalidade Temporal (F = {grangerCausality.fStatistic} · Defasagem média: {grangerCausality.optimalLagHours}h)
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {grangerCausality.timeline.map((evt, idx) => {
            const isPurged = !!evt.isSpamPurgedNote;

            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col justify-between space-y-3 ${
                  isPurged
                    ? 'border-red-200 dark:border-red-900/50 bg-red-50/20 dark:bg-red-950/15'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/30'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-slate-900 dark:text-white">{evt.timeStr}</span>
                    <span className="text-slate-400 tabular-nums">{evt.postCount} posts</span>
                  </div>
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200 prose-justified">
                    {evt.spectrumName}
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed prose-justified">
                    {evt.narrativeHeadline}
                  </p>
                </div>

                {isPurged && (
                  <div className="text-[11px] font-semibold text-red-700 dark:text-red-400 pt-2 border-t border-red-200/60 dark:border-red-900/40">
                    Bloqueado antes da análise
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};
