import React from 'react';
import { ApplicationStatus } from '../../types/application';
import {
  Clock,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  CheckCheck,
  AlertOctagon,
  Layers,
} from 'lucide-react';

interface StatusBadgeProps {
  status: ApplicationStatus | string;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getStatusConfig = (st: string) => {
    switch (st.toUpperCase()) {
      case 'PENDING':
        return {
          bg: 'bg-amber-50 text-amber-800 border-amber-300',
          icon: Clock,
          label: 'PENDING REVIEW',
        };
      case 'PROCESSING':
        return {
          bg: 'bg-blue-50 text-blue-800 border-blue-300',
          icon: RotateCw,
          label: 'IN PROCESSING',
        };
      case 'VERIFIED':
        return {
          bg: 'bg-emerald-50 text-emerald-800 border-emerald-300',
          icon: CheckCircle2,
          label: 'VERIFIED',
        };
      case 'COMPLETED':
        return {
          bg: 'bg-teal-50 text-teal-800 border-teal-300',
          icon: CheckCheck,
          label: 'COMPLETED',
        };
      case 'ACTION_REQUIRED':
        return {
          bg: 'bg-orange-50 text-orange-800 border-orange-300',
          icon: AlertTriangle,
          label: 'ACTION REQUIRED',
        };
      case 'REJECTED':
        return {
          bg: 'bg-rose-50 text-rose-800 border-rose-300',
          icon: XCircle,
          label: 'REJECTED',
        };
      case 'FAILED':
        return {
          bg: 'bg-red-50 text-red-800 border-red-300',
          icon: AlertOctagon,
          label: 'FAILED',
        };
      case 'QUEUED':
        return {
          bg: 'bg-purple-50 text-purple-800 border-purple-300',
          icon: Layers,
          label: 'QUEUED',
        };
      default:
        return {
          bg: 'bg-slate-50 text-slate-700 border-slate-300',
          icon: Clock,
          label: st,
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5 gap-1 font-medium',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-semibold',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-bold',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-2xs tracking-wider uppercase ${config.bg} ${sizeClasses}`}
    >
      <Icon className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{config.label}</span>
    </span>
  );
};
