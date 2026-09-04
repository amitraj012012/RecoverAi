import React, { useEffect, useState } from 'react';
import {
  DashboardMetrics,
  RecoveryCaseSummary,
  AgentActivity,
  RevenueTrendPoint,
} from '../../types/dashboard';
import {
  fetchDashboardMetrics,
  fetchRecoveryCasesPreview,
  fetchRecentActivities,
  fetchRevenueTrends,
  fetchFailureReasons,
} from '../../services/dashboardService';
import { MetricCard } from '../../components/common/MetricCard';
import { AiRecoveryPanel } from '../../components/dashboard/AiRecoveryPanel';
import { AgentActivityFeed } from '../../components/dashboard/AgentActivityFeed';
import { RevenueRecoveryChart } from '../../components/dashboard/RevenueRecoveryChart';
import { ActiveCasesTable } from '../../components/dashboard/ActiveCasesTable';
import { DashboardSkeleton } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { AlertOctagon, TrendingUp, Percent, ShieldCheck, PieChart, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Overview: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [cases, setCases] = useState<RecoveryCaseSummary[]>([]);
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [trends, setTrends] = useState<RevenueTrendPoint[]>([]);
  const [failureReasons, setFailureReasons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [m, c, a, t, fr] = await Promise.all([
        fetchDashboardMetrics(),
        fetchRecoveryCasesPreview(),
        fetchRecentActivities(),
        fetchRevenueTrends(),
        fetchFailureReasons(),
      ]);
      setMetrics(m);
      setCases(c);
      setActivities(a);
      setTrends(t);
      setFailureReasons(fr);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard overview data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error || !metrics) {
    return (
      <ErrorState
        title="Dashboard Data Unavailable"
        message={error || 'Could not load metrics.'}
        onRetry={loadData}
      />
    );
  }

  const formatLakh = (amount: number) => `₹${(amount / 100000).toFixed(1)}L`;

  return (
    <div className="space-y-6">
      {/* 1. Top Impact Welcome Banner */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-[#64748B] flex items-center">
            <span className="w-2 h-2 rounded-full bg-[#10B981] mr-2"></span>
            Autonomous Recovery Intelligence Active
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-[#0F172A] mt-1">
            Good morning, {user?.email?.split('@')[0] || 'Merchant'}
          </h2>
          <p className="text-sm text-[#64748B] mt-0.5">
            RecoverAI detected{' '}
            <span className="font-bold text-[#F59E0B]">{formatLakh(metrics.revenueAtRisk)}</span>{' '}
            revenue at risk across {metrics.activeCases.toLocaleString()} failed transactions.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs bg-slate-50 p-3 rounded-lg border border-slate-200 shrink-0">
          <ShieldCheck className="w-5 h-5 text-[#2563EB]" />
          <div>
            <div className="font-semibold text-[#0F172A]">Demo / Synthetic Data</div>
            <div className="text-[#64748B]">Database Computed Exposure</div>
          </div>
        </div>
      </div>

      {/* 2. Primary Financial Metric Cards (Revenue Impact Hierarchy) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Revenue at Risk */}
        <MetricCard
          title="Revenue at Risk"
          value={formatLakh(metrics.revenueAtRisk)}
          subValue={`${metrics.activeCases.toLocaleString()} failed transactions`}
          icon={AlertOctagon}
          variant="atRisk"
          pillText="At Risk"
          pillVariant="warning"
        />

        {/* Estimated Recoverable Revenue (Phase 4 Heuristic) */}
        <MetricCard
          title="Estimated Recoverable"
          value={formatLakh(metrics.estimatedRecoverable)}
          subValue="Heuristic Baseline (~70%)"
          icon={TrendingUp}
          variant="recoverable"
          pillText="Target"
          pillVariant="info"
        />

        {/* Total Ingested Transactions */}
        <MetricCard
          title="Simulated Recovered"
          value={`₹${(metrics.revenueRecovered / 100000).toFixed(2)}L`}
          subValue="Actual Autonomous Settlements"
          icon={CheckCircle2}
          variant="recovered"
          pillText="Recovered"
          pillVariant="success"
        />

        {/* Failure Rate */}
        <MetricCard
          title="Failure Rate"
          value={`${metrics.recoveryRate}%`}
          subValue="Transaction Failure Frequency"
          icon={Percent}
          variant="atRisk"
          pillText="Calculated"
          pillVariant="warning"
        />
      </div>

      {/* 3. AI Recovery Engine Status & Overview Panel */}
      <AiRecoveryPanel
        casesAnalyzed={metrics.casesAnalyzed}
        actionsExecuted={metrics.successfulActions}
        recoveredToday={`₹${(metrics.revenueRecovered / 100000).toFixed(2)}L`}
        activeRate={metrics.recoveryRate}
      />

      {/* 4. Failure Reason Breakdown (Phase 4 Database Analysis) */}
      {failureReasons.length > 0 && (
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <PieChart className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#0F172A]">Failure Reason Breakdown</h3>
            <span className="text-xs text-[#64748B]">• Database Aggregated Exposure</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {failureReasons.map((fr) => (
              <div key={fr.failure_reason} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-xs font-semibold text-[#0F172A] truncate">
                  {fr.failure_reason}
                </div>
                <div className="mt-1 flex items-baseline justify-between">
                  <span className="text-base font-bold text-[#F59E0B]">
                    ₹{(fr.revenue_at_risk_paise / 10000000).toFixed(3)}L
                  </span>
                  <span className="text-xs text-[#64748B] font-medium">
                    {fr.count.toLocaleString()} cases · {fr.percentage_of_risk}% exposure
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Trajectory Chart + Recent Agent Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RevenueRecoveryChart data={trends} />
        </div>
        <div>
          <AgentActivityFeed activities={activities} />
        </div>
      </div>

      {/* 6. Active Recovery Cases Table */}
      <ActiveCasesTable cases={cases} />
    </div>
  );
};
