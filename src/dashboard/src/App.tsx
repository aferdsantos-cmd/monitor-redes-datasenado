import React, { useState, useEffect, useMemo } from 'react';
import { ToastProvider, useToast } from './components/Toast';
import { Header } from './components/Header';
import { OperationalToolbar } from './components/OperationalToolbar';
import { NavigationSidebar, ActiveModuleId } from './components/NavigationSidebar';
import { Module1Inference } from './components/modules/Module1Inference';
import { Module2Bubbles } from './components/modules/Module2Bubbles';
import { Module3LegislativeRadar } from './components/modules/Module3LegislativeRadar';
import { Module4ReportsEcosystem } from './components/modules/Module4ReportsEcosystem';
import { Module5HumanValidationAndLayers } from './components/modules/Module5HumanValidationAndLayers';
import { Module6MethodologyAndScience } from './components/modules/Module6MethodologyAndScience';
import { SkeletonCard } from './components/SkeletonCard';
import { NewThemeModal } from './components/modals/NewThemeModal';
import { XaiInspectionDrawer } from './components/modals/XaiInspectionDrawer';
import { EcosystemHomePage, EcosystemSection } from './components/pages/EcosystemHomePage';
import { DebateHubPage } from './components/pages/DebateHubPage';
import { EcosystemOtherModules } from './components/pages/EcosystemOtherModules';
import { TimeWindow, PlatformId, ThemeDataset, AuditRecord, normalizeHumanGates } from './types';
import { THEMES_DATA, BOILING_TOPICS_LIST } from './data/mockData';

export function DataSenadoApp() {
  const { showToast } = useToast();
  const [darkMode, setDarkMode] = useState<boolean>(false);
  const [ecosystemSection, setEcosystemSection] = useState<EcosystemSection>('home');
  const [activeModule, setActiveModule] = useState<ActiveModuleId>('module_1');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);
  const [isNewThemeModalOpen, setIsNewThemeModalOpen] = useState<boolean>(false);
  const [selectedAuditRecord, setSelectedAuditRecord] = useState<AuditRecord | null>(null);

  const [themesMap, setThemesMap] = useState<Record<string, ThemeDataset>>(THEMES_DATA);
  const [currentThemeId, setCurrentThemeId] = useState<string>('eleicao_presidencia_senado');

  const [timeWindow, setTimeWindow] = useState<TimeWindow>('7d');
  const [activePlatforms, setActivePlatforms] = useState<Set<PlatformId>>(
    new Set<PlatformId>(['youtube', 'telegram', 'x_twitter', 'instagram_facebook', 'tiktok', 'whatsapp'])
  );
  const [goldSampleSize, setGoldSampleSize] = useState<number>(550);

  const [isLoadingTransition, setIsLoadingTransition] = useState<boolean>(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.location.search) {
      const params = new URLSearchParams(window.location.search);
      const themeParam = params.get('theme');
      const windowParam = params.get('window') as TimeWindow | null;
      const nParam = params.get('n');
      if (themeParam && themesMap[themeParam]) {
        setCurrentThemeId(themeParam);
        setEcosystemSection('debate_dashboard');
      }
      if (windowParam && ['24h', '7d', '15d', '30d', 'custom'].includes(windowParam)) {
        setTimeWindow(windowParam);
      }
      if (nParam && [300, 550, 1200].includes(Number(nParam))) {
        setGoldSampleSize(Number(nParam));
      }
    }
  }, []);

  useEffect(() => {
    // Sincronização automática reativa com o Servidor Local Python REST se ativo
    const fetchBackendTheme = async () => {
      try {
        const res = await fetch(`/api/themes/${currentThemeId}?window=${timeWindow}&n=${goldSampleSize}`);
        if (res.ok) {
          const liveData = await res.json();
          if (liveData && liveData.id) {
            setThemesMap((prev) => ({
              ...prev,
              [currentThemeId]: {
                ...prev[currentThemeId],
                ...liveData,
              },
            }));
          }
        }
      } catch {
        // Fallback transparente em memória RAM
      }
    };
    fetchBackendTheme();
  }, [currentThemeId, timeWindow, goldSampleSize]);

  const handleDatasetUpdated = (updatedPartial: Partial<ThemeDataset>) => {
    setThemesMap((prev) => {
      const current = prev[currentThemeId];
      if (!current) return prev;
      const normalizedGates = updatedPartial.humanGates
        ? normalizeHumanGates(updatedPartial.humanGates)
        : (updatedPartial.human_gates ? normalizeHumanGates(updatedPartial.human_gates) : current.humanGates);
      return {
        ...prev,
        [currentThemeId]: {
          ...current,
          ...updatedPartial,
          humanGates: normalizedGates,
          human_gates: normalizedGates,
        },
      };
    });
  };

  const handleAdvanceLifecycle = async () => {
    const currentStatus = currentDataset?.lifecycleStatus || 'PRONTO_PARA_ANALISE_E_BOLETIM';
    const gates = normalizeHumanGates(currentDataset?.humanGates);

    // Trava Estrita Anti-Atalho de Portões Humanos (Pilares 1 e 2)
    if (currentStatus === 'COLETA_EM_ANDAMENTO_6_REDES' && gates.bronzeGate.status !== 'APROVADO_PELO_ANALISTA') {
      showToast(
        'error',
        'Portão Humano 1 Pendente',
        'A Camada Bronze requer homologação formal do analista no Módulo 5 antes de avançar para a Descontaminação Silver.'
      );
      setActiveModule('module_5');
      return;
    }

    if (currentStatus === 'DESCONTAMINACAO_SILVER_CIB_SPAM' && gates.silverGate.status !== 'APROVADO_PELO_ANALISTA') {
      showToast(
        'error',
        'Portão Humano 2 Pendente',
        'A Camada Silver (Descontaminação CIB/Spam) requer aprovação formal no Módulo 5 antes da Calibração Gold.'
      );
      setActiveModule('module_5');
      return;
    }

    if (currentStatus === 'CALIBRACAO_RAKING_IPF_ROGAN_GLADEN' && gates.goldGate.status !== 'APROVADO_PELO_ANALISTA') {
      showToast(
        'error',
        'Portão Humano 3 Pendente',
        'A Camada Gold (Amostragem Ponderada e Calibração) requer aprovação formal no Módulo 5 antes do Boletim Final.'
      );
      setActiveModule('module_5');
      return;
    }

    const order = [
      { status: 'CADASTRADO_AGUARDANDO_DISPARO', pct: 0, label: 'Cadastrado / Aguardando Disparo' },
      { status: 'VALIDANDO_SESSOES_CONECTORES', pct: 15, label: 'Validando Sessões dos Conectores' },
      { status: 'COLETA_EM_ANDAMENTO_6_REDES', pct: 45, label: 'Coleta em Andamento nas 6 Redes' },
      { status: 'DESCONTAMINACAO_SILVER_CIB_SPAM', pct: 70, label: 'Descontaminação Silver CIB & Spam' },
      { status: 'CALIBRACAO_RAKING_IPF_ROGAN_GLADEN', pct: 90, label: 'Calibração Raking IPF & Rogan-Gladen' },
      { status: 'PRONTO_PARA_ANALISE_E_BOLETIM', pct: 100, label: 'Pronto para Análise e Boletim' },
    ] as const;
    const idx = order.findIndex((s) => s.status === currentStatus);
    const nextIdx = idx >= 0 && idx < order.length - 1 ? idx + 1 : 0;
    const nextStep = order[nextIdx];

    try {
      await fetch(`/api/themes/${currentThemeId}/lifecycle/advance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
    } catch {
      // offline fallback
    }

    setThemesMap((prev) => ({
      ...prev,
      [currentThemeId]: {
        ...prev[currentThemeId],
        lifecycleStatus: nextStep.status,
        lifecycleProgressPercent: nextStep.pct,
      },
    }));

    showToast('info', `Ciclo de Vida: ${nextStep.pct}%`, `Etapa transacionada para: ${nextStep.label}`);
  };

  const currentDataset = useMemo(() => {
    return themesMap[currentThemeId] || themesMap['eleicao_presidencia_senado'];
  }, [themesMap, currentThemeId]);

  const platformCounts = useMemo(() => {
    const res: Record<PlatformId, number> = {
      youtube: 0,
      telegram: 0,
      x_twitter: 0,
      instagram_facebook: 0,
      tiktok: 0,
      whatsapp: 0,
    };
    if (currentDataset?.platforms) {
      currentDataset.platforms.forEach((p) => {
        res[p.platformId] = p.nOrg;
      });
    }
    return res;
  }, [currentDataset]);

  const handleThemeChange = (themeId: string) => {
    setIsLoadingTransition(true);
    setCurrentThemeId(themeId);
    setEcosystemSection('debate_dashboard');
    setTimeout(() => {
      setIsLoadingTransition(false);
    }, 150);
  };

  const handleTogglePlatform = (pId: PlatformId) => {
    setActivePlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(pId)) {
        if (next.size > 1) {
          next.delete(pId);
        }
      } else {
        next.add(pId);
      }
      return next;
    });
  };

  const handleSelectAllPlatforms = () => {
    setActivePlatforms(
      new Set<PlatformId>(['youtube', 'telegram', 'x_twitter', 'instagram_facebook', 'tiktok', 'whatsapp'])
    );
  };

  const handleAddTheme = (newTheme: ThemeDataset) => {
    setThemesMap((prev) => ({
      ...prev,
      [newTheme.id]: newTheme,
    }));
    handleThemeChange(newTheme.id);
    setActiveModule('module_1');
  };

  const handleCreateThemeFromDiscovery = (topicTitle: string, committee: string, queryHint: string) => {
    const baseTemplate = THEMES_DATA['pec_escala_6x1'];
    const slugId = `tema_${Date.now()}`;
    const initialGates = normalizeHumanGates();
    const newTheme: ThemeDataset = {
      ...baseTemplate,
      id: slugId,
      title: topicTitle,
      subtitle: `Monitoramento iniciado via Descoberta de Temas em Debate nas Redes`,
      committee,
      legislativeContext: `Acompanhamento de repercussão pública, posicionamento orgânico e disputa de narrativas sobre "${topicTitle}" para subsídio técnico à ${committee}.`,
      statusTag: 'RECÉM-INICIADO · COLETA ATIVA',
      lifecycleStatus: 'CADASTRADO_AGUARDANDO_DISPARO',
      lifecycleProgressPercent: 0,
      humanGates: initialGates,
      human_gates: initialGates,
      medallion: {
        ...baseTemplate.medallion,
        queriesUsed: [queryHint],
      },
    };

    try {
      fetch('/api/themes/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: slugId,
          title: topicTitle,
          committee,
          queries: [queryHint],
        }),
      }).catch(() => {});
    } catch {
      // offline fallback
    }

    setThemesMap((prev) => ({
      ...prev,
      [slugId]: newTheme,
    }));
    showToast(
      'success',
      'Monitoramento Iniciado a partir da Pesquisa',
      `O tema "${topicTitle}" foi adicionado aos cards ativos e aberto na bancada.`
    );
    handleThemeChange(slugId);
    setActiveModule('module_1');
  };

  const themesArray = useMemo(() => {
    return Object.values(themesMap);
  }, [themesMap]);

  const availableThemesList = useMemo(() => {
    return themesArray.map((t) => ({
      id: t.id,
      title: t.title,
      committee: t.committee,
    }));
  }, [themesArray]);

  const radarAlertsCount = useMemo(() => {
    return BOILING_TOPICS_LIST.filter((t) => t.isSenateInterest && t.cusumTriggered).length;
  }, []);

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-200 ${
        darkMode ? 'dark bg-[#090D16] text-slate-100' : 'bg-[#F8FAFC] text-slate-900'
      }`}
    >
      {/* 1. Institutional Top Bar */}
      <Header
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        activeModule={activeModule}
        onSelectModule={setActiveModule}
        ecosystemSection={ecosystemSection}
        onSelectEcosystemSection={setEcosystemSection}
      />

      {/* PAGE LEVEL 1: ECOSYSTEM 360º HOME (4 SQUARE CARDS) */}
      {ecosystemSection === 'home' && (
        <main className="flex-1 overflow-y-auto">
          <EcosystemHomePage
            onSelectSection={(sec) => setEcosystemSection(sec)}
            monitoredThemesCount={themesArray.length}
          />
        </main>
      )}

      {/* PAGE LEVEL 2: DEBATE PÚBLICO HUB (MONITORED THEME CARDS + "+ NOVO" + "PESQUISAR") */}
      {ecosystemSection === 'debate_hub' && (
        <main className="flex-1 overflow-y-auto">
          <DebateHubPage
            themes={themesArray}
            onSelectTheme={(themeId) => {
              handleThemeChange(themeId);
              setActiveModule('module_1');
            }}
            onOpenNewThemeModal={() => setIsNewThemeModalOpen(true)}
            onCreateThemeFromDiscovery={handleCreateThemeFromDiscovery}
            onBackToEcosystem={() => setEcosystemSection('home')}
          />
        </main>
      )}

      {/* OTHER ECOSYSTEM MODULES (TRENDS, EDITORIAL, DATASENADO SURVEYS) */}
      {(ecosystemSection === 'trends_module' ||
        ecosystemSection === 'editorial_module' ||
        ecosystemSection === 'datasenado_surveys_module') && (
        <main className="flex-1 overflow-y-auto">
          <EcosystemOtherModules
            moduleType={ecosystemSection}
            onBackToEcosystem={() => setEcosystemSection('home')}
            onOpenDebateTheme={(themeId) => {
              handleThemeChange(themeId);
              setActiveModule('module_1');
            }}
          />
        </main>
      )}

      {/* PAGE LEVEL 3: ANALYTICAL DASHBOARD FOR SELECTED MONITORED THEME */}
      {ecosystemSection === 'debate_dashboard' && (
        <>
          <OperationalToolbar
            currentThemeId={currentThemeId}
            onThemeChange={handleThemeChange}
            availableThemes={availableThemesList}
            onOpenNewThemeModal={() => setIsNewThemeModalOpen(true)}
            onBackToHub={() => setEcosystemSection('debate_hub')}
            timeWindow={timeWindow}
            onTimeWindowChange={setTimeWindow}
            activePlatforms={activePlatforms}
            onTogglePlatform={handleTogglePlatform}
            onSelectAllPlatforms={handleSelectAllPlatforms}
            goldSampleSize={goldSampleSize}
            onGoldSampleSizeChange={setGoldSampleSize}
            platformCounts={platformCounts}
            lifecycleStatus={currentDataset?.lifecycleStatus || 'PRONTO_PARA_ANALISE_E_BOLETIM'}
            lifecycleProgressPercent={currentDataset?.lifecycleProgressPercent ?? 100}
            onAdvanceLifecycle={handleAdvanceLifecycle}
            rateLimitAlert={currentDataset?.rateLimitAlert || null}
            subrepresentationAlert={currentDataset?.subrepresentationAlert || null}
            humanGates={currentDataset?.humanGates}
            onNavigateToHumanGates={() => setActiveModule('module_5')}
          />

          <div className="flex-1 flex overflow-hidden">
            <NavigationSidebar
              activeModule={activeModule}
              onSelectModule={setActiveModule}
              isCollapsed={isSidebarCollapsed}
              onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              radarAlertsCount={radarAlertsCount}
            />

            <main className="flex-1 overflow-y-auto px-6 py-8 sm:px-10">
              {isLoadingTransition ? (
                <div className="max-w-[1360px] mx-auto space-y-6">
                  <SkeletonCard minHeightClassName="min-h-[180px]" lines={3} title="Carregando cabeçalho executivo..." />
                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <SkeletonCard key={i} minHeightClassName="min-h-[110px]" lines={2} title="Carregando métricas..." />
                    ))}
                  </div>
                  <SkeletonCard minHeightClassName="min-h-[360px]" lines={5} title="Carregando estimadores oficiais e intervalos de confiança..." />
                </div>
              ) : (
                <>
                  {activeModule === 'module_1' && (
                    <Module1Inference
                      dataset={currentDataset}
                      activePlatforms={activePlatforms}
                      goldSampleSize={goldSampleSize}
                      onInspectRecord={(rec) => setSelectedAuditRecord(rec)}
                      onNavigateToReport={() => setActiveModule('module_4')}
                    />
                  )}

                  {activeModule === 'module_2' && (
                    <Module2Bubbles dataset={currentDataset} />
                  )}

                  {activeModule === 'module_3' && (
                    <Module3LegislativeRadar
                      onDrilldownTopic={(targetThemeId) => {
                        handleThemeChange(targetThemeId);
                        setActiveModule('module_1');
                      }}
                    />
                  )}

                  {activeModule === 'module_4' && (
                    <Module4ReportsEcosystem dataset={currentDataset} />
                  )}

                  {activeModule === 'module_5' && (
                    <Module5HumanValidationAndLayers
                      dataset={currentDataset}
                      onDatasetUpdated={handleDatasetUpdated}
                    />
                  )}

                  {activeModule === 'module_6' && (
                    <Module6MethodologyAndScience dataset={currentDataset} />
                  )}
                </>
              )}
            </main>
          </div>
        </>
      )}

      {/* Modals & Drawers */}
      <NewThemeModal
        isOpen={isNewThemeModalOpen}
        onClose={() => setIsNewThemeModalOpen(false)}
        onAddTheme={handleAddTheme}
      />

      <XaiInspectionDrawer
        record={selectedAuditRecord}
        onClose={() => setSelectedAuditRecord(null)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <DataSenadoApp />
    </ToastProvider>
  );
}
