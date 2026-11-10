import React, { useState } from 'react';
import { Sun, Moon, BookOpen, ShieldCheck, X, LayoutGrid, Layers } from 'lucide-react';
import { useToast } from './Toast';
import { ActiveModuleId } from './NavigationSidebar';
import { EcosystemSection } from './pages/EcosystemHomePage';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  activeModule: ActiveModuleId;
  onSelectModule: (module: ActiveModuleId) => void;
  ecosystemSection: EcosystemSection;
  onSelectEcosystemSection: (section: EcosystemSection) => void;
}

export const Header: React.FC<HeaderProps> = ({
  darkMode,
  setDarkMode,
  activeModule,
  onSelectModule,
  ecosystemSection,
  onSelectEcosystemSection,
}) => {
  const { showToast } = useToast();
  const [showMethodologyModal, setShowMethodologyModal] = useState(false);

  const navItems: { id: ActiveModuleId; label: string }[] = [
    { id: 'module_1', label: 'Panorama & Opinião' },
    { id: 'module_2', label: 'Bolhas & Narrativas' },
    { id: 'module_3', label: 'Radar Legislativo' },
    { id: 'module_4', label: 'Relatórios & Notas' },
  ];

  return (
    <>
      <header className="relative bg-[#0B1F3A] text-white border-b border-[#C59B27]/40 z-30 select-none no-print">
        <div className="h-[2px] w-full bg-[#C59B27]" />

        <div className="max-w-[1440px] mx-auto px-6 py-3.5 flex items-center justify-between gap-6">
          {/* Zone 1: Brand Title & Hierarchical Navigation Breadcrumb */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onSelectEcosystemSection('home')}
              className="flex items-center gap-2 text-base font-bold tracking-tight text-white whitespace-nowrap shrink-0 text-left hover:text-[#DFBA4E] transition-colors cursor-pointer focus-visible:outline-none"
              title="Ir para a Página Inicial do Ecossistema de Inteligência de Dados 360º"
            >
              <span>DataSenado · Ecossistema 360º</span>
            </button>

            {ecosystemSection !== 'home' && (
              <>
                <span className="text-slate-500">/</span>
                <button
                  onClick={() => onSelectEcosystemSection('debate_hub')}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                    ecosystemSection === 'debate_hub'
                      ? 'bg-white/15 text-[#DFBA4E]'
                      : 'bg-white/5 hover:bg-white/15 text-slate-200'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5 text-[#DFBA4E]" />
                  <span>Temas Monitorados</span>
                </button>
              </>
            )}
          </div>

          {/* Zone 2: Clean single-line navigation links (visible when inside a theme dashboard) */}
          {ecosystemSection === 'debate_dashboard' ? (
            <nav className="hidden xl:flex items-center gap-6 text-sm font-medium">
              {navItems.map((item) => {
                const isActive = activeModule === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectModule(item.id)}
                    className={`whitespace-nowrap shrink-0 py-1 transition-colors border-b-2 cursor-pointer ${
                      isActive
                        ? 'text-white border-[#C59B27] font-semibold'
                        : 'text-slate-300 border-transparent hover:text-white'
                    }`}
                  >
                    {item.label}
                  </button>
                );
              })}
            </nav>
          ) : (
            <div className="hidden lg:flex items-center gap-5 text-xs text-slate-300">
              <button
                onClick={() => onSelectEcosystemSection('home')}
                className={`hover:text-white transition-colors cursor-pointer ${
                  ecosystemSection === 'home' ? 'text-[#DFBA4E] font-semibold' : ''
                }`}
              >
                Início (4 Módulos)
              </button>
              <button
                onClick={() => onSelectEcosystemSection('debate_hub')}
                className={`hover:text-white transition-colors cursor-pointer ${
                  ecosystemSection === 'debate_hub' ? 'text-[#DFBA4E] font-semibold' : ''
                }`}
              >
                Inteligência do Debate Público
              </button>
              <button
                onClick={() => onSelectEcosystemSection('trends_module')}
                className={`hover:text-white transition-colors cursor-pointer ${
                  ecosystemSection === 'trends_module' ? 'text-[#DFBA4E] font-semibold' : ''
                }`}
              >
                Trends / Tendências
              </button>
              <button
                onClick={() => onSelectEcosystemSection('editorial_module')}
                className={`hover:text-white transition-colors cursor-pointer ${
                  ecosystemSection === 'editorial_module' ? 'text-[#DFBA4E] font-semibold' : ''
                }`}
              >
                Inteligência Editorial
              </button>
              <button
                onClick={() => onSelectEcosystemSection('datasenado_surveys_module')}
                className={`hover:text-white transition-colors cursor-pointer ${
                  ecosystemSection === 'datasenado_surveys_module' ? 'text-[#DFBA4E] font-semibold' : ''
                }`}
              >
                Opinião Pública DataSenado
              </button>
            </div>
          )}

          {/* Zone 3: Actions */}
          <div className="flex items-center gap-2.5 shrink-0">
            {ecosystemSection !== 'home' && (
              <button
                onClick={() => onSelectEcosystemSection('home')}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white/10 hover:bg-white/15 text-xs font-medium text-white transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                title="Voltar aos 4 Cards do Ecossistema 360º"
              >
                <LayoutGrid className="w-3.5 h-3.5 text-[#DFBA4E]" />
                <span>Ecossistema 360º</span>
              </button>
            )}

            <button
              onClick={() => setShowMethodologyModal(true)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-white/10 hover:bg-white/15 text-xs font-medium text-white transition-colors whitespace-nowrap shrink-0 cursor-pointer"
            >
              <BookOpen className="w-3.5 h-3.5 text-[#DFBA4E]" />
              <span>Guia Metodológico</span>
            </button>

            <button
              onClick={() => {
                setDarkMode(!darkMode);
                showToast(
                  'info',
                  !darkMode ? 'Modo Escuro Ativado' : 'Modo Claro Editorial Ativado',
                  !darkMode
                    ? 'Superfície de alto contraste ativada.'
                    : 'Superfície editorial clara ativada.'
                );
              }}
              title={darkMode ? 'Alternar para Modo Claro Editorial' : 'Alternar para Modo Escuro'}
              className="p-2 rounded-md bg-white/10 hover:bg-white/15 text-slate-200 hover:text-white transition-colors cursor-pointer"
            >
              {darkMode ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4 text-blue-200" />}
            </button>
          </div>
        </div>
      </header>

      {/* Methodology Modal */}
      {showMethodologyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-6 animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden text-slate-900 dark:text-slate-100">
            <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Como Ler os Dados do DataSenado Digital
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Tradução simples dos critérios científicos e estatísticos utilizados na bancada
                </p>
              </div>
              <button
                onClick={() => setShowMethodologyModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1.5 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-5 text-sm leading-relaxed">
              <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <h4 className="font-semibold text-slate-900 dark:text-white mb-1 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-blue-700 dark:text-blue-400" />
                  O que estes números representam?
                </h4>
                <p className="text-slate-600 dark:text-slate-300 text-xs leading-relaxed prose-justified">
                  As análises retratam a opinião das <strong>contas reais e orgânicas</strong> que se manifestaram publicamente nas 6 redes monitoradas. Elas servem como termômetro ágil do debate público digital, complementando (mas não substituindo) as pesquisas telefônicas e domiciliares por amostragem probabilística do DataSenado.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <h5 className="font-bold text-slate-900 dark:text-white mb-1.5">
                    1. Limpeza de Robôs e Spam (Filtro Silver)
                  </h5>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed prose-justified">
                    Antes de calcular qualquer percentual, o sistema identifica postagens repetidas em rajada e redes coordenadas de robôs (via algoritmos MinHash LSH e Leiden). Assim, <strong>1 conta cidadã real vale 1 voto</strong> na amostra.
                  </p>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <h5 className="font-bold text-slate-900 dark:text-white mb-1.5">
                    2. Estimativa Oficial (Rogan-Gladen)
                  </h5>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed prose-justified">
                    Todo modelo classificador tem uma pequena margem de erro ao ler ironias ou textos ambíguos. A correção matemática de Rogan-Gladen desconta exatamente a sensibilidade e especificidade medidas do modelo.
                  </p>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <h5 className="font-bold text-slate-900 dark:text-white mb-1.5">
                    3. Calibragem Regional (Raking IBGE)
                  </h5>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed prose-justified">
                    Se uma rede social tem excesso de usuários de uma única capital, o modelo reequilibra os pesos de acordo com as macrorregiões do IBGE para evitar distorções geográficas.
                  </p>
                </div>

                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800">
                  <h5 className="font-bold text-slate-900 dark:text-white mb-1.5">
                    4. Privacidade e Proteção LGPD
                  </h5>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed prose-justified">
                    Nenhum nome pessoal ou telefone é salvo. Os identificadores são convertidos em código irreversível (HMAC-SHA256) e os grupos só são exibidos quando reúnem ao menos 5 contas ($k \ge 5$).
                  </p>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setShowMethodologyModal(false)}
                className="px-4 py-2 rounded-lg bg-[#0B1F3A] text-white text-xs font-semibold hover:bg-blue-950 transition-colors"
              >
                Fechar Guia
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
