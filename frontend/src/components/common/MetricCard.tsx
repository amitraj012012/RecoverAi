import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  subValue?: string;
  icon?: LucideIcon;
  variant?: 'recovered' | 'atRisk' | 'recoverable' | 'default';
  pillText?: string;
  pillVariant?: 'success' | 'warning' | 'info' | 'neutral';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subValue,
  icon: Icon,
  variant = 'default',
  pillText,
  pillVariant = 'neutral',
}) => {
  const getBorderTop = () => {
    switch (variant) {
      case 'recovered':
        return 'border-t-4 border-t-[#10B981]';
      case 'atRisk':
        return 'border-t-4 border-t-[#F59E0B]';
      case 'recoverable':
        return 'border-t-4 border-t-[#2563EB]';
      default:
        return 'border-t border-t-[#E2E8F0]';
    }
  };

  const getPillStyle = () => {
    switch (pillVariant) {
      case 'success':
        return 'bg-emerald-50 text-[#10B981] border-emerald-200';
      case 'warning':
        return 'bg-amber-50 text-[#F59E0B] border-amber-200';
      case 'info':
        return 'bg-blue-50 text-[#2563EB] border-blue-200';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  return (
    <div
      className={`bg-white rounded-xl border border-[#E2E8F0] ${getBorderTop()} p-5 shadow-sm transition-all hover:shadow-md`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
          {title}
        </span>
        {Icon && (
          <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-[#64748B] border border-slate-100">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0F172A]">
          {value}
        </div>
      </div>

      {(subValue || pillText) && (
        <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-slate-100">
          {subValue && <span className="text-[#64748B]">{subValue}</span>}
          {pillText && (
            <span className={`px-2 py-0.5 rounded-full font-medium border ${getPillStyle()}`}>
              {pillText}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
