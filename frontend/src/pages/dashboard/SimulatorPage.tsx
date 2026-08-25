import React, { useEffect, useState } from 'react';
import {
  Play,
  RotateCcw,
  Zap,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Sliders,
  DollarSign,
  TrendingUp,
} from 'lucide-react';
import {
  fetchSimulatorStatus,
  runBatchSimulation,
  simulateSingleCase,
  resetSimulator,
} from '../../services/dashboardService';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const SimulatorPage: React.FC = () => {
  const [metrics, setMetrics] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [batchRunning, setBatchRunning] = useState(false);
  const [singleRunning, setSingleRunning] = useState(false);
  const [batchSize, setBatchSize] = useState(25);
  const [c1024Scenario, setC1024Scenario] = useState('auto');
  const [lastBatchResult, setLastBatchResult] = useState<any | null>(null);
  const [lastSingleResult, setLastSingleResult] = useState<any | null>(null);
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  const loadStatus = async () => {
    setLoading(true);
    const data = await fetchSimulatorStatus();
    setMetrics(data);
    setLoading(false);
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleRunBatch = async () => {
    setBatchRunning(true);
    setNotification(null);
    try {
      const res = await runBatchSimulation(batchSize, 'auto');
      setLastBatchResult(res);
      setNotification({
        text: `Simulation complete: Processed ${res.cases_processed} cases. Recovered ₹${res.total_recovered_inr.toLocaleString()} across ${res.recovered_count} transactions.`,
        type: 'success',
      });
      await loadStatus();
    } catch (err: any) {
      setNotification({ text: err.message || 'Batch simulation failed.', type: 'error' });
    } finally {
      setBatchRunning(false);
    }
  };

  const handleSimulateC1024 = async () => {
    setSingleRunning(true);
    setNotification(null);
    try {
      const res = await simulateSingleCase('rec_c1024_fail', c1024Scenario);
      setLastSingleResult(res);
      setNotification({
        text: `C1024 Scenario Executed (${c1024Scenario}): Status is ${res.current_status} • ${res.is_recovered ? `Recovered ₹${res.recovered_amount_inr}` : 'Action Dispatched'}.`,
        type: 'success',
      });
      await loadStatus();
    } catch (err: any) {
      setNotification({ text: err.message || 'Simulation on C1024 failed.', type: 'error' });
    } finally {
      setSingleRunning(false);
    }
  };

  const handleResetDemo = async () => {
    if (!window.confirm('Reset all recovery cases and simulation records back to baseline FAILED state?')) {
      return;
    }
    setLoading(true);
    await resetSimulator();
    setLastBatchResult(null);
    setLastSingleResult(null);
    setNotification({ text: 'Simulator and demo cases cleanly reset to initial state.', type: 'info' });
    await loadStatus();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">Autonomous Payment & Recovery Simulator</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Interactive demo control center • Synthetic / Demo Simulation Environment
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleResetDemo}
            className="inline-flex items-center px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-sm transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            Reset Demo State
          </button>
        </div>
      </div>

      {notification && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : notification.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-900'
              : 'bg-blue-50 border-blue-200 text-blue-900'
          }`}
        >
          <span>{notification.text}</span>
          <button onClick={() => setNotification(null)} className="font-bold ml-2">
            ×
          </button>
        </div>
      )}

      {/* Simulator Metrics Dashboard Cards */}
      {loading && !metrics ? (
        <DashboardSkeleton />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Total Simulated Recovered</span>
              <DollarSign className="w-4 h-4 text-[#10B981]" />
            </div>
            <div className="text-2xl font-bold text-[#10B981] mt-2">
              ₹{(metrics?.total_revenue_recovered_inr || 0).toLocaleString()}
            </div>
            <div className="text-[11px] text-[#64748B] mt-1">
              {metrics?.recovered_cases || 0} cases successfully resolved
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Revenue Still At Risk</span>
              <TrendingUp className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl font-bold text-[#0F172A] mt-2">
              ₹{(metrics?.revenue_still_at_risk_inr || 0).toLocaleString()}
            </div>
            <div className="text-[11px] text-[#64748B] mt-1">
              {metrics?.failed_cases || 0} failed transactions pending
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Simulation Recovery Rate</span>
              <Zap className="w-4 h-4 text-[#2563EB]" />
            </div>
            <div className="text-2xl font-bold text-[#2563EB] mt-2">
              {metrics?.recovery_rate_percentage || 0}%
            </div>
            <div className="text-[11px] text-[#64748B] mt-1">
              Based on executed simulator attempts
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Escalated to Ops</span>
              <AlertTriangle className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl font-bold text-slate-700 mt-2">
              {metrics?.escalated_cases || 0}
            </div>
            <div className="text-[11px] text-[#64748B] mt-1">
              Max attempts reached or manual review
            </div>
          </div>
        </div>
      )}

      {/* Control Panels: Batch Simulator & C1024 Lab */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: Batch Autonomous Simulation */}
        <div className="bg-white p-6 rounded-xl border border-[#E2E8F0] shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-sm font-bold text-[#0F172A]">Batch Recovery Runner</h3>
            </div>
            <span className="text-[11px] px-2 py-0.5 bg-blue-50 text-blue-700 font-semibold rounded">
              Autonomous Loop
            </span>
          </div>

          <p className="text-xs text-[#64748B]">
            Simulates the full autonomous agent loop across a cohort of unrecovered failed payments:
            ML scoring $\rightarrow$ Strategy selection $\rightarrow$ Guardrail check $\rightarrow$ Simulator execution.
          </p>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-[#0F172A]">Batch Size:</label>
            <div className="flex items-center space-x-3">
              {[10, 25, 50, 100].map((size) => (
                <button
                  key={size}
                  onClick={() => setBatchSize(size)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                    batchSize === size
                      ? 'bg-[#2563EB] text-white border-[#2563EB]'
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {size} Cases
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleRunBatch}
            disabled={batchRunning}
            className={`w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 shadow-sm transition-colors ${
              batchRunning
                ? 'bg-blue-300 text-white cursor-wait'
                : 'bg-[#2563EB] hover:bg-blue-700 text-white'
            }`}
          >
            {batchRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                Simulating Autonomous Cohort...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white mr-2" />
                Run Autonomous Batch ({batchSize} Cases)
              </>
            )}
          </button>

          {lastBatchResult && (
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
              <div className="font-bold text-[#0F172A] flex items-center justify-between">
                <span>Latest Batch Execution Summary</span>
                <span className="text-[#10B981]">
                  +{lastBatchResult.recovered_count} Recovered (₹{lastBatchResult.total_recovered_inr.toLocaleString()})
                </span>
              </div>
              <div className="text-[11px] text-[#64748B]">
                Processed {lastBatchResult.cases_processed} cases • {lastBatchResult.escalated_count} escalated • {lastBatchResult.still_active_count} pending next attempt.
              </div>
            </div>
          )}
        </div>

        {/* Panel 2: Demo Case C1024 Sandbox */}
        <div className="bg-white p-6 rounded-xl border border-[#E2E8F0] shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-bold text-[#0F172A]">Demo Case Sandbox (C1024)</h3>
            </div>
            <span className="text-[11px] px-2 py-0.5 bg-amber-50 text-amber-800 font-semibold rounded">
              ₹1,999 Card Decline
            </span>
          </div>

          <p className="text-xs text-[#64748B]">
            Execute controlled scenario testing on judge demo customer <strong>C1024</strong> (18mo tenure, 88% activity, 17/17 historical payments).
          </p>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-[#0F172A]">Scenario Preset:</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'auto', label: 'Auto (Stochastic ML)' },
                { id: 'force_success', label: 'Forced Success' },
                { id: 'force_fail', label: 'Forced Failure' },
                { id: 'force_escalate', label: 'Force Escalate' },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => setC1024Scenario(s.id)}
                  className={`p-2 text-xs font-semibold rounded-lg border text-left transition-colors ${
                    c1024Scenario === s.id
                      ? 'bg-amber-50 border-amber-300 text-amber-950 font-bold'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleSimulateC1024}
            disabled={singleRunning}
            className={`w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 shadow-sm transition-colors ${
              singleRunning
                ? 'bg-amber-300 text-white cursor-wait'
                : 'bg-amber-600 hover:bg-amber-700 text-white'
            }`}
          >
            {singleRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                Executing C1024 Simulation...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 fill-white mr-2" />
                Execute C1024 Simulation ({c1024Scenario})
              </>
            )}
          </button>

          {lastSingleResult && (
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
              <div className="font-bold text-[#0F172A] flex items-center justify-between">
                <span>Result: {lastSingleResult.current_status}</span>
                <span className="font-mono text-[10px] text-[#2563EB]">{lastSingleResult.selected_strategy}</span>
              </div>
              <div className="text-[11px] text-[#64748B]">
                Tool: <strong className="font-mono text-slate-700">{lastSingleResult.tool_invoked}</strong> ({lastSingleResult.tool_result}) • Recovered: ₹{lastSingleResult.recovered_amount_inr}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Honesty & Governance Card */}
      <div className="p-4 bg-slate-100 rounded-xl border border-slate-200 text-xs text-slate-700 flex items-start space-x-2.5">
        <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#0F172A]">Prototype Simulation Protocol:</span> All payment links, retries, and gateway responses are executed within controlled synthetic test harnesses. No live banking connections or real customer accounts are accessed.
        </div>
      </div>
    </div>
  );
};
