import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message,
  onRetry,
}) => {
  return (
    <div className="bg-red-50/50 rounded-xl border border-red-200 p-8 text-center shadow-sm">
      <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto text-[#EF4444] mb-4">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-bold text-[#0F172A]">{title}</h3>
      <p className="mt-1 text-sm text-red-700 max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-2" />
          Retry Request
        </button>
      )}
    </div>
  );
};
