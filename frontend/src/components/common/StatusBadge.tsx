import React from 'react';
import { RecoveryStatus } from '../../types/dashboard';

interface StatusBadgeProps {
  status: RecoveryStatus | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const normalized = status.toUpperCase();

  const getStyle = () => {
    switch (normalized) {
      case 'SUCCESS':
      case 'SUCCESSFUL':
      case 'SETTLED':
        return {
          bg: 'bg-emerald-50 text-[#10B981] border-emerald-200',
          dot: 'bg-[#10B981]',
          label: 'Successful',
        };
      case 'RECOVERED':
        return {
          bg: 'bg-emerald-50 text-[#10B981] border-emerald-200',
          dot: 'bg-[#10B981]',
          label: 'Recovered',
        };
      case 'AT_RISK':
        return {
          bg: 'bg-amber-50 text-[#F59E0B] border-amber-200',
          dot: 'bg-[#F59E0B]',
          label: 'At Risk',
        };
      case 'ANALYZING':
        return {
          bg: 'bg-blue-50 text-[#2563EB] border-blue-200',
          dot: 'bg-[#2563EB]',
          label: 'Analyzing',
        };
      case 'RECOVERY_ACTIVE':
        return {
          bg: 'bg-blue-50 text-[#2563EB] border-blue-200',
          dot: 'bg-[#2563EB] animate-pulse',
          label: 'Recovery Active',
        };
      case 'FAILED':
        return {
          bg: 'bg-red-50 text-[#EF4444] border-red-200',
          dot: 'bg-[#EF4444]',
          label: 'Failed',
        };
      case 'ESCALATED':
        return {
          bg: 'bg-purple-50 text-purple-700 border-purple-200',
          dot: 'bg-purple-600',
          label: 'Escalated',
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-700 border-slate-200',
          dot: 'bg-slate-500',
          label: status,
        };
    }
  };

  const config = getStyle();
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium border ${config.bg} ${padding}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${config.dot}`} />
      {config.label}
    </span>
  );
};
