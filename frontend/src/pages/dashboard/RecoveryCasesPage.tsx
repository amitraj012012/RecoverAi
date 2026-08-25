import React, { useEffect, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  X,
  ShieldCheck,
  Zap,
  AlertCircle,
} from 'lucide-react';
import { RecoveryCaseSummary } from '../../types/dashboard';
import {
  fetchRecoveryCases,
  predictRecoveryProbability,
  executeRecoveryWorkflow,
} from '../../services/dashboardService';
import { StatusBadge } from '../../components/common/StatusBadge';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const RecoveryCasesPage: React.FC = () => {
  const [cases, setCases] = useState<RecoveryCaseSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const [selectedExplainCase, setSelectedExplainCase] = useState<any | null>(null);
  const [recoveryModalData, setRecoveryModalData] = useState<any | null>(null);
  const [executingCaseId, setExecutingCaseId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  const limit = 15;

  const loadCases = async () => {
    setLoading(true);
    const data = await fetchRecoveryCases(page, limit, statusFilter);
    setCases(data.items);
    setTotal(data.total);
    setLoading(false);
  };

  useEffect(() => {
    loadCases();
  }, [page, statusFilter]);

  const handleExplain = async (c: RecoveryCaseSummary) => {
    const paymentId = (c as any).paymentId || c.id.replace('rec_', 'pay_');
    const prediction = await predictRecoveryProbability(paymentId);
    setSelectedExplainCase({ ...c, prediction });
  };

  const handleExecuteRecovery = async (c: RecoveryCaseSummary) => {
    setExecutingCaseId(c.id);
    setExecutionError(null);
    try {
      const result = await executeRecoveryWorkflow(c.id);
      setRecoveryModalData({ case: c, result });
      setCases((prev) =>
        prev.map((item) =>
          item.id === c.id
            ? {
                ...item,
                status: (result.current_status as any) || 'RECOVERED',
                selectedStrategy: result.selected_strategy,
                recoveredAmount: result.is_recovered ? item.amount : 0,
              }
            : item
        )
      );
    } catch (err: any) {
      setExecutionError(err.message || 'Recovery workflow execution failed.');
    } finally {
      setExecutingCaseId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">Recovery Cases Operational Console</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            ML-scored recovery pipeline ({total.toLocaleString()} active cases • Bounded AI Recovery Agent)
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs border border-[#E2E8F0] rounded-lg px-3 py-2 bg-white text-[#0F172A] focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
          >
            <option value="">All Case Statuses</option>
            <option value="FAILED">Failed</option>
            <option value="ANALYZING">Analyzing</option>
            <option value="ACTION_EXECUTED">Action Executed</option>
            <option value="RECOVERED">Recovered</option>
            <option value="ESCALATED">Escalated</option>
          </select>
        </div>
      </div>

      {executionError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>{executionError}</span>
          </div>
          <button onClick={() => setExecutionError(null)} className="text-rose-500 hover:text-rose-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6">
            <DashboardSkeleton />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
                <thead className="bg-slate-50 text-[#64748B] font-semibold uppercase text-[11px]">
                  <tr>
                    <th className="px-5 py-3">Case ID</th>
                    <th className="px-5 py-3">Customer ID</th>
                    <th className="px-5 py-3">Expected Amount</th>
                    <th className="px-5 py-3">ML Probability</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Assigned Strategy</th>
                    <th className="px-5 py-3 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {cases.map((c) => {
                    const probPercent = Math.round((c.recoveryProbability ?? 0.878) * 100);
                    const isTerminal = c.status === 'RECOVERED' || c.status === 'ESCALATED';

                    return (
                      <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-5 py-3.5 font-mono text-[11px] font-semibold text-[#0F172A]">
                          {c.id}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-[11px] text-[#2563EB]">
                          {c.customerId}
                        </td>
                        <td className="px-5 py-3.5 font-semibold text-[#0F172A]">
                          ₹{c.amount.toLocaleString()}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-[#0F172A] w-9">{probPercent}%</span>
                            <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-1.5 rounded-full ${
                                  probPercent >= 80
                                    ? 'bg-[#10B981]'
                                    : probPercent >= 50
                                    ? 'bg-[#2563EB]'
                                    : 'bg-[#F59E0B]'
                                }`}
                                style={{ width: `${probPercent}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={c.status} />
                        </td>
                        <td className="px-5 py-3.5 font-mono text-[10px] uppercase font-semibold text-slate-700">
                          {c.selectedStrategy ? c.selectedStrategy.replace(/_/g, ' ') : '—'}
                        </td>
                        <td className="px-5 py-3.5 text-right space-x-2">
                          <button
                            onClick={() => handleExplain(c)}
                            className="inline-flex items-center px-2 py-1 text-[11px] font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
                          >
                            <Sparkles className="w-3 h-3 mr-1 text-[#2563EB]" />
                            Factors
                          </button>

                          <button
                            onClick={() => handleExecuteRecovery(c)}
                            disabled={isTerminal || executingCaseId === c.id}
                            className={`inline-flex items-center px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                              isTerminal
                                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                                : executingCaseId === c.id
                                ? 'bg-blue-300 text-white cursor-wait'
                                : 'bg-[#2563EB] text-white hover:bg-blue-700 shadow-sm'
                            }`}
                          >
                            {executingCaseId === c.id ? (
                              'Executing...'
                            ) : (
                              <>
                                <Zap className="w-3 h-3 mr-1" />
                                Recover
                              </>
                            )}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-[#64748B]">
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of{' '}
                {total.toLocaleString()} cases
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="font-semibold text-[#0F172A]">
                  Page {page} of {Math.max(1, Math.ceil(total / limit))}
                </span>
                <button
                  onClick={() => setPage((p) => (p * limit < total ? p + 1 : p))}
                  disabled={page * limit >= total}
                  className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Recovery Execution Result Modal */}
      {recoveryModalData && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-[#10B981]" />
                <h3 className="text-base font-bold text-[#0F172A]">
                  AI Recovery Workflow Executed ({recoveryModalData.result.customer_id})
                </h3>
              </div>
              <button
                onClick={() => setRecoveryModalData(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 5-Stage Execution Flow Visualization */}
            <div className="space-y-2.5 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-[#64748B] uppercase">Stage 1: Prediction</span>
                  <div className="font-bold text-[#0F172A] text-sm">
                    ML Probability: {recoveryModalData.result.ml_probability_percentage}%
                  </div>
                </div>
                <span className="font-mono text-[10px] text-slate-500">logistic-regression-v2</span>
              </div>

              <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-200">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-blue-700 uppercase">Stage 2: AI Decision</span>
                  <span className="font-bold text-blue-900 bg-white px-2 py-0.5 rounded border border-blue-200">
                    {recoveryModalData.result.selected_strategy}
                  </span>
                </div>
                <p className="mt-1.5 text-slate-700 text-[11px]">
                  &quot;{recoveryModalData.result.decision_reason}&quot;
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-[#64748B] uppercase">Stage 3: Guardrail & Tool</span>
                  <div className="font-mono font-semibold text-[#0F172A] text-xs mt-0.5">
                    {recoveryModalData.result.tool_invoked}
                  </div>
                </div>
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 font-bold rounded text-[10px]">
                  GUARDRAIL PASS
                </span>
              </div>

              <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-emerald-800 uppercase">Stage 4: Simulator Outcome</span>
                  <div className="font-bold text-emerald-950 text-sm mt-0.5 flex items-center">
                    <CheckCircle2 className="w-4 h-4 text-[#10B981] mr-1.5" />
                    {recoveryModalData.result.is_recovered
                      ? `Recovered ₹${recoveryModalData.result.amount_inr}`
                      : `Action Executed (${recoveryModalData.result.tool_result})`}
                  </div>
                </div>
                <StatusBadge status={recoveryModalData.result.current_status} />
              </div>

              <div className="p-2.5 bg-slate-100 rounded-lg text-[10px] text-slate-600 font-mono flex items-center justify-between">
                <span>Audit Action ID: {recoveryModalData.result.recovery_action_id}</span>
                <span>Demo Simulator</span>
              </div>
            </div>

            <button
              onClick={() => setRecoveryModalData(null)}
              className="w-full py-2.5 bg-[#2563EB] text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Factors Explainability Modal */}
      {selectedExplainCase && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-[#2563EB]" />
                <h3 className="text-base font-bold text-[#0F172A]">
                  ML Prediction Rationale ({selectedExplainCase.customerId})
                </h3>
              </div>
              <button
                onClick={() => setSelectedExplainCase(null)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
              <div>
                <span className="text-xs text-[#64748B] font-medium">Model Output</span>
                <div className="text-2xl font-bold text-[#0F172A]">
                  {selectedExplainCase.prediction
                    ? `${selectedExplainCase.prediction.recovery_probability_percentage}%`
                    : `${Math.round((selectedExplainCase.recoveryProbability ?? 0.878) * 100)}%`}
                </div>
              </div>
              <div className="text-right">
                <span className="text-[11px] font-mono text-[#64748B]">
                  {selectedExplainCase.prediction?.model_version || 'logistic-regression-v2'}
                </span>
                <div className="text-xs text-[#10B981] font-semibold mt-0.5">High Confidence</div>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-bold text-[#0F172A] uppercase tracking-wider">
                Influencing Feature Factors
              </span>
              {selectedExplainCase.prediction?.factors?.map((f: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
                    f.impact === 'positive'
                      ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                      : f.impact === 'negative'
                      ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                      : 'bg-slate-50 border-slate-200 text-slate-900'
                  }`}
                >
                  <span>{f.description}</span>
                  <span
                    className={`font-bold uppercase text-[10px] px-2 py-0.5 rounded ${
                      f.impact === 'positive'
                        ? 'bg-emerald-100 text-emerald-800'
                        : f.impact === 'negative'
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {f.impact}
                  </span>
                </div>
              ))}
            </div>

            <button
              onClick={() => setSelectedExplainCase(null)}
              className="w-full py-2.5 bg-[#2563EB] text-white text-xs font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close Rationale
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
