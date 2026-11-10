import React from 'react';
import { X, ShieldCheck, Cpu, ArrowRight, Activity, Terminal } from 'lucide-react';
import { AuditRecord } from '../../types';
import { PLATFORM_INFO } from '../../data/mockData';

interface XaiInspectionDrawerProps {
  record: AuditRecord | null;
  onClose: () => void;
}

export const XaiInspectionDrawer: React.FC<XaiInspectionDrawerProps> = ({ record, onClose }) => {
  if (!record) return null;

  const platformInfo = PLATFORM_INFO[record.platform] || { label: record.platform, color: '#64748B' };

  const getStanceBadge = () => {
    switch (record.stance) {
      case 'FAVORAVEL':
        return {
          label: 'Favorável',
          bg: 'bg-[#0072B2]/15 text-[#0072B2] border-[#0072B2]/40',
        };
      case 'CONTRARIO':
        return {
          label: 'Contrário',
          bg: 'bg-[#D55E00]/15 text-[#D55E00] border-[#D55E00]/40',
        };
      case 'NEUTRO':
        return {
          label: 'Neutro / Informativo',
          bg: 'bg-[#64748B]/15 text-[#64748B] border-[#64748B]/40',
        };
      case 'QUARENTENA_CIB':
        return {
          label: 'Quarentena Silver (CIB/Spam)',
          bg: 'bg-red-500/15 text-red-600 border-red-500/40',
        };
    }
  };

  const badge = getStanceBadge();
  const shap = record.shapDetails;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-2xs animate-in fade-in select-none">
      <div
        className="w-full max-w-lg bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200 text-slate-900 dark:text-slate-100"
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-850">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                Inspeção Explicável XAI (SHAP / LIME)
              </h3>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                Hash: {record.id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Metadata Card */}
          <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Origem & Espectro
              </span>
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${badge.bg}`}>
                {badge.label}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div>
                <span className="text-slate-400">Plataforma:</span>{' '}
                <span className="font-semibold text-slate-800 dark:text-slate-200">{platformInfo.label}</span>
              </div>
              <div>
                <span className="text-slate-400">UF / Região:</span>{' '}
                <span className="font-semibold text-slate-800 dark:text-slate-200">{record.uf} ({record.region})</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400">Timestamp:</span>{' '}
                <span className="text-slate-700 dark:text-slate-300">{record.timestampUtc}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400">Espectro:</span>{' '}
                <span className="text-slate-700 dark:text-slate-300 font-sans font-medium">{record.spectrumName}</span>
              </div>
            </div>
          </div>

          {/* Sanitized Text */}
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <div className="flex items-center gap-1.5 text-slate-400 mb-1.5">
              <Terminal className="w-3.5 h-3.5" />
              <span className="text-[10px] font-semibold uppercase tracking-wider">
                Texto Sanitizado LGPD
              </span>
            </div>
            <p className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-mono bg-slate-50 dark:bg-slate-850 p-2.5 rounded border border-slate-100 dark:border-slate-800">
              {record.sanitizedText}
            </p>
          </div>

          {/* Model Confidence & Waterfall */}
          <div className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                <span className="text-xs font-bold text-slate-900 dark:text-white">
                  Decomposição de Valores de Shapley (Waterfall)
                </span>
              </div>
              <span className="text-xs font-mono font-bold text-slate-900 dark:text-white tabular-nums">
                p = {(shap.predictedProbability * 100).toFixed(1)}%
              </span>
            </div>

            <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
              <div className="flex items-center justify-between text-slate-500 font-mono text-[10px]">
                <span>Probabilidade Base a Priori E[f(x)]:</span>
                <span className="tabular-nums font-semibold">{(shap.baseProbability * 100).toFixed(1)}%</span>
              </div>

              {/* Waterfall Bars */}
              <div className="pt-2 space-y-2">
                {shap.features.map((feat, idx) => {
                  const isPositive = feat.weight >= 0;
                  const weightPercent = Math.abs(feat.weight * 100).toFixed(1);

                  return (
                    <div key={idx} className="space-y-0.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                          "{feat.token}"
                        </span>
                        <span
                          className={`font-mono text-[10px] tabular-nums font-semibold ${
                            isPositive ? 'text-[#0072B2]' : 'text-[#D55E00]'
                          }`}
                        >
                          {isPositive ? `+${weightPercent}%` : `-${weightPercent}%`}
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex">
                        {isPositive ? (
                          <div
                            className="h-full bg-[#0072B2] rounded-full"
                            style={{ width: `${Math.min(100, Math.abs(feat.weight) * 200)}%` }}
                          />
                        ) : (
                          <div
                            className="h-full bg-[#D55E00] rounded-full"
                            style={{ width: `${Math.min(100, Math.abs(feat.weight) * 200)}%` }}
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between font-mono text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  Probabilidade Predita Final f(x):
                </span>
                <span className="font-bold text-blue-700 dark:text-blue-400 tabular-nums">
                  {(shap.predictedProbability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Mathematical Guarantee Note */}
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 text-[10px] text-slate-500 dark:text-slate-400 space-y-1">
            <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              Axioma de Eficiência de Shapley (Lloyd Shapley, 1953)
            </div>
            <p className="leading-relaxed">
              A soma das contribuições marginais dos tokens é estritamente igual à diferença entre
              o valor esperado a priori e a probabilidade de predição do modelo:
              <br />
              <code className="text-slate-700 dark:text-slate-300 font-mono">
                ∑ φ_i(x) = f(x) - E[f(x)]
              </code>
              . Esta garantia matemática elimina arbitrariedades e assegura auditabilidade jurídica perante os órgãos de controle.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex justify-end">
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded bg-slate-800 dark:bg-slate-700 text-white text-xs font-medium hover:bg-slate-700 dark:hover:bg-slate-600 transition-colors"
          >
            Fechar Inspeção
          </button>
        </div>
      </div>
    </div>
  );
};
