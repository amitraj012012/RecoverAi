import React from 'react';

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Metric Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-[#E2E8F0] p-5 h-32 space-y-3">
            <div className="h-4 bg-slate-200 rounded w-1/2"></div>
            <div className="h-8 bg-slate-200 rounded w-3/4"></div>
            <div className="h-3 bg-slate-100 rounded w-full"></div>
          </div>
        ))}
      </div>

      {/* Main Grid Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl border border-[#E2E8F0] p-6 h-80 space-y-4">
          <div className="h-5 bg-slate-200 rounded w-1/3"></div>
          <div className="h-60 bg-slate-100 rounded w-full"></div>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 h-80 space-y-4">
          <div className="h-5 bg-slate-200 rounded w-1/2"></div>
          <div className="h-60 bg-slate-100 rounded w-full"></div>
        </div>
      </div>
    </div>
  );
};
