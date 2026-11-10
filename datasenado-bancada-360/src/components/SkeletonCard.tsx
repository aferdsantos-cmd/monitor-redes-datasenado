import React from 'react';

interface SkeletonCardProps {
  className?: string;
  minHeightClassName?: string;
  lines?: number;
  title?: string;
}

export const SkeletonCard: React.FC<SkeletonCardProps> = ({
  className = '',
  minHeightClassName = 'min-h-[240px]',
  lines = 3,
  title = 'Carregando indicadores...',
}) => {
  return (
    <div
      role="status"
      aria-label={title}
      aria-busy="true"
      className={`rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs animate-pulse ${minHeightClassName} ${className}`}
    >
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="h-4 w-36 bg-slate-200 dark:bg-slate-800 rounded-md" />
        <div className="h-3 w-16 bg-slate-200 dark:bg-slate-800 rounded-md" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`bg-slate-100 dark:bg-slate-800/60 rounded-md ${
              i === 0 ? 'h-5 w-3/4' : i === 1 ? 'h-4 w-full' : 'h-4 w-2/3'
            }`}
          />
        ))}
      </div>
      <span className="sr-only">{title}</span>
    </div>
  );
};

export default SkeletonCard;
