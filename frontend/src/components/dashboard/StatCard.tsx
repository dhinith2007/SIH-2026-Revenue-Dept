import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  colorScheme: 'amber' | 'blue' | 'emerald' | 'orange' | 'rose' | 'slate';
  subtext?: string;
  badge?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  colorScheme,
  subtext,
  badge,
}) => {
  const styles = {
    amber: {
      border: 'border-l-4 border-l-amber-500',
      iconBg: 'bg-amber-50 text-amber-600',
      badgeBg: 'bg-amber-100 text-amber-800',
    },
    blue: {
      border: 'border-l-4 border-l-blue-500',
      iconBg: 'bg-blue-50 text-blue-600',
      badgeBg: 'bg-blue-100 text-blue-800',
    },
    emerald: {
      border: 'border-l-4 border-l-emerald-500',
      iconBg: 'bg-emerald-50 text-emerald-600',
      badgeBg: 'bg-emerald-100 text-emerald-800',
    },
    orange: {
      border: 'border-l-4 border-l-orange-500',
      iconBg: 'bg-orange-50 text-orange-600',
      badgeBg: 'bg-orange-100 text-orange-800',
    },
    rose: {
      border: 'border-l-4 border-l-rose-500',
      iconBg: 'bg-rose-50 text-rose-600',
      badgeBg: 'bg-rose-100 text-rose-800',
    },
    slate: {
      border: 'border-l-4 border-l-slate-500',
      iconBg: 'bg-slate-50 text-slate-600',
      badgeBg: 'bg-slate-100 text-slate-800',
    },
  }[colorScheme];

  return (
    <div className={`bg-white rounded-lg p-4 shadow-sm border border-slate-200 ${styles.border} flex flex-col justify-between hover:shadow-md transition-shadow`}>
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {title}
          </span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{value}</div>
        </div>
        <div className={`p-2 rounded-lg ${styles.iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-2">
        <span>{subtext || 'Simulated metric'}</span>
        {badge && (
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${styles.badgeBg}`}>
            {badge}
          </span>
        )}
      </div>
    </div>
  );
};
