import React, { useState, useEffect } from 'react';
import {
  Clock,
  Layers,
  Plus,
  SlidersHorizontal,
  Share2,
  Check,
  ChevronDown,
  ChevronUp,
  ArrowLeft,
  Activity,
  Play,
  AlertTriangle,
  ShieldCheck,
} from 'lucide-react';
import { PlatformId, TimeWindow, LifecycleStatus, RateLimitAlertInfo } from '../types';
import { PLATFORM_INFO } from '../data/mockData';
import { useToast } from './Toast';

interface OperationalToolbarProps {
  currentThemeId: string;
  onThemeChange: (themeId: string) => void;
  availableThemes: Array<{ id: string; title: string; committee: string }>;
  onOpenNewThemeModal: () => void;
  onBackToHub?: () => void;
  timeWindow: TimeWindow;
  onTimeWindowChange: (window: TimeWindow) => void;
  activePlatforms: Set<PlatformId>;
  onTogglePlatform: (platformId: PlatformId) => void;
  onSelectAllPlatforms: () => void;
  goldSampleSize: number;
  onGoldSampleSizeChange: (size: number) => void;
  platformCounts: Record<PlatformId, number>;
  lifecycleStatus?: LifecycleStatus;
  lifecycleProgressPercent?: number;
  onAdvanceLifecycle?: () => void;
  rateLimitAlert?: RateLimitAlertInfo | null;
  subrepresentationAlert?: { region: string; n: number; message: string } | null;
}

const TIME_WINDOW_LABELS: Record<TimeWindow, string> = {
  '24h': 'Últimas 24h',
  '7d': '7 dias',
  '15d': '15 dias',
  '30d': '30 dias',
  custom: 'Customizado',
};

export const OperationalToolbar: React.FC<OperationalToolbarProps> = ({
  currentThemeId,
  onThemeChange,
  availableThemes,
  onOpenNewThemeModal,
  onBackToHub,
  timeWindow,
  onTimeWindowChange,
  activePlatforms,
  onTogglePlatform,
  onSelectAllPlatforms,
  goldSampleSize,
  onGoldSampleSizeChange,
  platformCounts,
  lifecycleStatus,
  lifecycleProgressPercent,
  onAdvanceLifecycle,
  rateLimitAlert,
  subrepresentationAlert,
}) => {
  const { showToast } = useToast();
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const platformsList: PlatformId[] = [
    'youtube',
    'telegram',
    'x_twitter',
    'instagram_facebook',
    'tiktok',
    'whatsapp',
  ];

  const queryStateStr = `?theme=${currentThemeId}&window=${timeWindow}&platforms=${activePlatforms.size}&n=${goldSampleSize}`;

  useEffect(() => {
    if (typeof window !== 'undefined' && window.history && window.history.replaceState) {
      window.history.replaceState(null, '', queryStateStr);
    }
  }, [currentThemeId, timeWindow, activePlatforms, goldSampleSize, queryStateStr]);

  const handleCopyUrl = () => {
    const fullUrl = `${window.location.origin}${window.location.pathname}${queryStateStr}`;
    navigator.clipboard.writeText(fullUrl).then(() => {
      setCopiedUrl(true);
      showToast('success', 'Link do Filtro Copiado', `Estado compartilhável (${queryStateStr}) copiado.`);
      setTimeout(() => setCopiedUrl(false), 2000);
    });
  };

  return (
    <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 select-none no-print">
      <div className="max-w-[1440px] mx-auto px-6 py-3.5">
        {/* Primary Row: Theme Selector on Left (plenty of room) + Filter Drawer Toggle on Right */}
        <div className="flex items-center justify-between gap-4">
          {/* Left: Pauta em Análise */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {onBackToHub && (
              <button
                onClick={onBackToHub}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold text-xs transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                title="Voltar à Vitrine de Cards dos Temas Monitorados"
              >
                <ArrowLeft className="w-3.5 h-3.5 text-blue-700 dark:text-blue-400" />
                <span>Cards de Temas</span>
              </button>
            )}

            <div className="hidden sm:flex items-center gap-2 text-slate-500 dark:text-slate-400 shrink-0">
              <Layers className="w-4 h-4 text-blue-700 dark:text-blue-400" />
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap">
                Pauta em Análise:
              </span>
            </div>

            <select
              value={currentThemeId}
              onChange={(e) => onThemeChange(e.target.value)}
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg py-2 px-3.5 text-sm font-semibold text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-600/30 w-full max-w-2xl truncate cursor-pointer transition-colors"
            >
              {availableThemes.map((theme) => (
                <option key={theme.id} value={theme.id}>
                  {theme.title} ({theme.committee})
                </option>
              ))}
            </select>

            <button
              onClick={onOpenNewThemeModal}
              className="hidden md:flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs transition-colors whitespace-nowrap shrink-0 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>Nova Pauta</span>
            </button>

            {lifecycleStatus && (
              <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-mono">
                <Activity className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 animate-pulse" />
                <span className="text-slate-700 dark:text-slate-300">
                  {lifecycleStatus.replace(/_/g, ' ')} ({lifecycleProgressPercent ?? 100}%)
                </span>
                {onAdvanceLifecycle && lifecycleStatus !== 'PRONTO_PARA_ANALISE_E_BOLETIM' && (
                  <button
                    onClick={onAdvanceLifecycle}
                    title="Avançar etapa do ciclo de vida"
                    className="ml-1 p-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-blue-600 dark:text-blue-400 cursor-pointer"
                  >
                    <Play className="w-3 h-3" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Right: Consolidated Filter Drawer Button (Período · Redes · Amostra) */}
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg border text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                showAdvancedFilters || activePlatforms.size < 6 || timeWindow !== '7d'
                  ? 'bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>
                Filtros: {TIME_WINDOW_LABELS[timeWindow]} · {activePlatforms.size}/6 Redes · n={goldSampleSize}
              </span>
              {showAdvancedFilters ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>

            <button
              onClick={handleCopyUrl}
              title={`Copiar link com parâmetros: ${queryStateStr}`}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              {copiedUrl ? <Check className="w-4 h-4 text-emerald-600" /> : <Share2 className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Operational Alert Banners (Lacuna 4) */}
        {rateLimitAlert && (
          <div className="mt-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 flex items-center justify-between text-xs text-amber-900 dark:text-amber-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>
                <strong>Pausa Preventiva por Rate Limit (HTTP 429) em {rateLimitAlert.platformName}:</strong> Backoff ativo com {rateLimitAlert.backoffSecondsRemaining}s restantes. O pipeline aguardará o jitter programado antes de novas consultas.
              </span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-amber-700 dark:text-amber-300 tabular-nums">
              {rateLimitAlert.backoffSecondsRemaining}s
            </span>
          </div>
        )}

        {subrepresentationAlert && (
          <div className="mt-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-300 dark:border-blue-800 flex items-center gap-2 text-xs text-blue-950 dark:text-blue-200">
            <ShieldCheck className="w-4 h-4 text-blue-700 dark:text-blue-400 shrink-0" />
            <span>
              <strong>Alerta Metodológico de Sub-representação Amostral:</strong> Estrato {subrepresentationAlert.region} com n={subrepresentationAlert.n} (&lt; 15 contas orgânicas). O estimador de Raking IPF aplicará truncamento de pesos de Kish no intervalo [0.25, 4.00].
            </span>
          </div>
        )}

        {/* Collapsible Filter Panel: Temporalidade + 6 Plataformas + Amostra Gold */}
        {showAdvancedFilters && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4 animate-in fade-in duration-150">
            {/* Row 1 inside filter panel: Temporalidade & Amostra Gold */}
            <div className="flex flex-wrap items-center justify-between gap-4">
              {/* Temporalidade (24h, 7 dias, 15 dias, 30 dias) */}
              <div className="flex items-center gap-2.5 flex-wrap">
                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
                  <Clock className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                  <span>Recorte Temporal:</span>
                </div>
                <div className="inline-flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200/70 dark:border-slate-700">
                  {(
                    [
                      { id: '24h', label: 'Últimas 24h' },
                      { id: '7d', label: '7 dias (Semanal)' },
                      { id: '15d', label: '15 dias' },
                      { id: '30d', label: '30 dias (Mensal)' },
                    ] as const
                  ).map((w) => (
                    <button
                      key={w.id}
                      onClick={() => onTimeWindowChange(w.id)}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                        timeWindow === w.id
                          ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs font-semibold'
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                      }`}
                    >
                      {w.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sample Size */}
              <div className="flex items-center gap-2.5">
                <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  Amostra Auditada (Gold):
                </span>
                <div className="inline-flex rounded-lg p-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                  {[300, 550, 1200].map((size) => (
                    <button
                      key={size}
                      onClick={() => onGoldSampleSizeChange(size)}
                      className={`px-2.5 py-1 rounded-md text-xs font-mono tabular-nums transition-colors ${
                        goldSampleSize === size
                          ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-semibold shadow-2xs'
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                      }`}
                    >
                      n={size}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Row 2 inside filter panel: 6 Platforms */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-100 dark:border-slate-800/60">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 mr-1">
                  Redes Monitoradas ({activePlatforms.size}/6):
                </span>
                {platformsList.map((pId) => {
                  const active = activePlatforms.has(pId);
                  const count = platformCounts[pId] || 0;
                  const info = PLATFORM_INFO[pId];

                  return (
                    <button
                      key={pId}
                      onClick={() => onTogglePlatform(pId)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs transition-all whitespace-nowrap shrink-0 ${
                        active
                          ? 'bg-slate-900 dark:bg-slate-100 border-slate-900 dark:border-slate-100 text-white dark:text-slate-900 font-medium'
                          : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 hover:border-slate-300'
                      }`}
                    >
                      <span>{info.label.split(' ')[0]}</span>
                      <span
                        className={`font-mono text-[11px] tabular-nums ${
                          active ? 'text-slate-300 dark:text-slate-600' : 'text-slate-400'
                        }`}
                      >
                        {count.toLocaleString('pt-BR')}
                      </span>
                    </button>
                  );
                })}

                {activePlatforms.size < 6 && (
                  <button
                    onClick={onSelectAllPlatforms}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline px-2 font-medium"
                  >
                    Selecionar todas
                  </button>
                )}
              </div>

              <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                Anonimização HMAC-SHA256 · k-Anonimato ≥ 5
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
