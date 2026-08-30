import React from 'react';
import { PriorityLevel } from '../../types/application';
import { Flame, AlertCircle, Minus, ArrowDown } from 'lucide-react';

interface PriorityBadgeProps {
  priority: PriorityLevel | string;
  size?: 'sm' | 'md';
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, size = 'md' }) => {
  const getPriorityConfig = (p: string) => {
    switch (p.toUpperCase()) {
      case 'URGENT':
        return {
          bg: 'bg-red-100 text-red-800 border-red-300 font-bold',
          icon: Flame,
          label: 'URGENT',
        };
      case 'HIGH':
        return {
          bg: 'bg-rose-50 text-rose-800 border-rose-200 font-semibold',
          icon: AlertCircle,
          label: 'HIGH',
        };
      case 'NORMAL':
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200 font-medium',
          icon: Minus,
          label: 'NORMAL',
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-slate-50 text-slate-500 border-slate-200 font-normal',
          icon: ArrowDown,
          label: 'LOW',
        };
    }
  };

  const config = getPriorityConfig(priority);
  const Icon = config.icon;

  const sizeClasses = size === 'sm' ? 'text-[10px] px-1.5 py-0.5 gap-1' : 'text-xs px-2 py-0.5 gap-1.5';

  return (
    <span className={`inline-flex items-center rounded border ${config.bg} ${sizeClasses}`}>
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};
