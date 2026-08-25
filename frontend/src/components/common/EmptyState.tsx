import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Inbox,
  actionText,
  onAction,
}) => {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] p-12 text-center shadow-sm">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-[#64748B] mb-4">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-[#0F172A]">{title}</h3>
      <p className="mt-1 text-sm text-[#64748B] max-w-sm mx-auto">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="mt-5 inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-xs font-semibold text-white bg-[#2563EB] hover:bg-blue-700 transition-colors"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
