import React from 'react';
import {
  BarChart3,
  Network,
  Radio,
  FileText,
  ShieldCheck,
  BookOpen,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export type ActiveModuleId = 'module_1' | 'module_2' | 'module_3' | 'module_4' | 'module_5' | 'module_6';

interface NavigationSidebarProps {
  activeModule: ActiveModuleId;
  onSelectModule: (module: ActiveModuleId) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  radarAlertsCount: number;
}

export const NavigationSidebar: React.FC<NavigationSidebarProps> = ({
  activeModule,
  onSelectModule,
  isCollapsed,
  onToggleCollapse,
  radarAlertsCount,
}) => {
  const navItems = [
    {
      id: 'module_1' as ActiveModuleId,
      label: 'Panorama & Opinião',
      subtitle: 'Posicionamento e redes',
      icon: BarChart3,
    },
    {
      id: 'module_2' as ActiveModuleId,
      label: 'Bolhas & Narrativas',
      subtitle: 'Grupos e consensos',
      icon: Network,
    },
    {
      id: 'module_3' as ActiveModuleId,
      label: 'Radar Legislativo',
      subtitle: `${radarAlertsCount} pautas em alta hoje`,
      icon: Radio,
    },
    {
      id: 'module_4' as ActiveModuleId,
      label: 'Relatórios & Notas',
      subtitle: 'Síntese descritiva e PDF',
      icon: FileText,
    },
    {
      id: 'module_5' as ActiveModuleId,
      label: 'Validação Humana & Camadas',
      subtitle: 'Bronze, Silver, Gold & Sandbox',
      icon: ShieldCheck,
    },
    {
      id: 'module_6' as ActiveModuleId,
      label: 'Metodologia & Ciência',
      subtitle: 'Tratado bilíngue e estudos',
      icon: BookOpen,
    },
  ];

  return (
    <aside
      className={`bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-all duration-200 select-none z-20 no-print shrink-0 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-3 space-y-1.5">
        <div className="flex items-center justify-between px-2.5 py-2 text-xs font-medium text-slate-400 dark:text-slate-500">
          {!isCollapsed && <span>Módulos de Análise</span>}
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors ml-auto"
            title={isCollapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeModule === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectModule(item.id)}
              title={isCollapsed ? `${item.label} — ${item.subtitle}` : undefined}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-colors group ${
                isActive
                  ? 'bg-[#0B1F3A] text-white dark:bg-blue-950/90'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  isActive
                    ? 'text-[#DFBA4E]'
                    : 'text-slate-400 group-hover:text-slate-700 dark:text-slate-500 dark:group-hover:text-slate-200'
                }`}
                strokeWidth={1.75}
              />
              {!isCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold truncate">{item.label}</div>
                  <div
                    className={`text-[11px] truncate mt-0.5 ${
                      isActive ? 'text-slate-300' : 'text-slate-400 dark:text-slate-500'
                    }`}
                  >
                    {item.subtitle}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {!isCollapsed && (
        <div className="p-4 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-400 dark:text-slate-500 space-y-1">
          <div className="font-medium text-slate-600 dark:text-slate-400">
            Instituto de Pesquisa DataSenado
          </div>
          <div>Senado Federal · Brasília, DF</div>
        </div>
      )}
    </aside>
  );
};
