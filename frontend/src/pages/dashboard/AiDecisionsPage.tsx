import React, { useEffect, useState } from 'react';
import { Sparkles, Play, Brain, History } from 'lucide-react';
import {
  fetchAiDecisions,
  fetchMemoryStatus,
  fetchRelevantMemory,
} from '../../services/dashboardService';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const AiDecisionsPage: React.FC = () => {
  const [decisions, setDecisions] = useState<any[]>([]);
  const [memoryStatus, setMemoryStatus] = useState<any | null>(null);
  const [selectedClusterReason, setSelectedClusterReason] = useState('Card Expired');
  const [relevantMemory, setRelevantMemory] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [memoryLoading, setMemoryLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    const [decisionItems, memStatus] = await Promise.all([
      fetchAiDecisions(50),
      fetchMemoryStatus(),
    ]);
    setDecisions(decisionItems);
    setMemoryStatus(memStatus);
    setLoading(false);
  };

  const handleQueryMemory = async (reason: string) => {
    setSelectedClusterReason(reason);
    setMemoryLoading(true);
    const data = await fetchRelevantMemory(reason, 0.85, 12);
    setRelevantMemory(data);
    setMemoryLoading(false);
  };

  useEffect(() => {
    loadData();
    handleQueryMemory('Card Expired');
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">AI Recovery Decisions & Adaptive Memory</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Transparent audit logs of bounded decisions and continuous learning memory (Demo / Synthetic Environment)
          </p>
        </div>
      </div>

      {/* Governance & Policy Bounds Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
            Allowed Strategies
          </div>
          <div className="text-2xl font-bold text-[#0F172A] mt-2">6 Bounded Actions</div>
          <div className="mt-2 text-xs text-[#64748B]">
            Smart Retry, Payment Link, Alternate Method, Reminder, Incentive, Escalation
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
            Deterministic Guardrails
          </div>
          <div className="text-2xl font-bold text-[#10B981] mt-2">Strictly Enforced</div>
          <div className="mt-2 text-xs text-[#64748B]">
            Max 3 attempts, financial ceilings, and allowlisted simulator tools
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
            Adaptive Memory Version
          </div>
          <div className="text-2xl font-bold text-[#2563EB] mt-2">
            {memoryStatus?.memory_version || 'agent-memory-v1'}
          </div>
          <div className="mt-2 text-xs text-[#64748B]">
            {memoryStatus?.total_memory_records || 0} experiences learned from outcomes
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#E2E8F0] shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#64748B]">
            Context Clusters
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-2">
            {memoryStatus?.context_clusters_tracked?.length || 0} Tracked
          </div>
          <div className="mt-2 text-xs text-[#64748B]">
            Empirical win-rates guide strategy reasoning
          </div>
        </div>
      </div>

      {/* Phase 8: Interactive Adaptive Memory Retrieval Explorer */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#0F172A]">Adaptive Memory Retrieval Inspector</h3>
          </div>
          <span className="text-[11px] px-2 py-0.5 bg-blue-50 text-blue-700 font-semibold rounded">
            Bounded Context Clustering
          </span>
        </div>

        <p className="text-xs text-[#64748B]">
          Demonstrates how the agent retrieves historical recovery experience before choosing a strategy.
          Click a failure pattern to inspect empirical win-rates learned from actual simulator outcomes:
        </p>

        <div className="flex flex-wrap gap-2 pt-1">
          {[
            'Card Expired',
            'UPI Network Timeout',
            'Bank Server Unavailable',
            'Card Declined (Insufficient Funds)',
            'Transaction Limit Exceeded',
          ].map((reason) => (
            <button
              key={reason}
              onClick={() => handleQueryMemory(reason)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                selectedClusterReason === reason
                  ? 'bg-[#2563EB] text-white border-[#2563EB]'
                  : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              {reason}
            </button>
          ))}
        </div>

        {memoryLoading ? (
          <div className="py-6 text-center text-xs text-slate-500">Querying agent memory...</div>
        ) : relevantMemory ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="text-xs font-bold text-[#0F172A] flex items-center justify-between">
                <span>Context Cluster: {relevantMemory.context_cluster}</span>
                <span className="text-[10px] text-slate-500 font-mono">Sample Size: {relevantMemory.sample_size} experiences</span>
              </div>
              <div className="text-xs text-slate-600">
                Empirical Strategy Win-Rates:
              </div>
              {Object.keys(relevantMemory.strategy_performance).length === 0 ? (
                <div className="text-xs text-slate-400 italic">No historical experiences recorded for this cluster yet. Run simulations to generate learning experiences.</div>
              ) : (
                <div className="space-y-1.5 pt-1">
                  {Object.entries(relevantMemory.strategy_performance).map(([strat, stats]: [string, any]) => (
                    <div key={strat} className="flex items-center justify-between text-xs p-2 bg-white rounded border border-slate-200">
                      <span className="font-mono text-[11px] text-slate-700">{strat}</span>
                      <span className="font-bold text-[#10B981]">{stats.win_rate_percentage}% ({stats.successes}/{stats.attempts} recovered)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="text-xs font-bold text-[#0F172A] flex items-center justify-between">
                <span>Recent Retrieved Memories (Top {relevantMemory.recent_experiences.length})</span>
                <History className="w-3.5 h-3.5 text-slate-400" />
              </div>
              {relevantMemory.recent_experiences.length === 0 ? (
                <div className="text-xs text-slate-400 italic">No recent memories retrieved.</div>
              ) : (
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {relevantMemory.recent_experiences.map((exp: any) => (
                    <div key={exp.id} className="text-[11px] p-2 bg-white rounded border border-slate-200 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-slate-800">{exp.customer_id}</span> • <span className="font-mono text-slate-600">{exp.strategy_used}</span>
                      </div>
                      <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${exp.is_recovered ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                        {exp.outcome_result}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>

      {/* Decisions Feed */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#0F172A]">Recent Autonomous Decision Events</h3>
          </div>
          <span className="text-xs text-[#64748B]">{decisions.length} recorded events</span>
        </div>

        {loading ? (
          <DashboardSkeleton />
        ) : decisions.length === 0 ? (
          <div className="py-12 text-center text-xs text-[#64748B]">
            <Play className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            No recovery decisions executed yet. Go to <a href="/app/simulator" className="text-[#2563EB] underline font-semibold">Simulator</a> or <a href="/app/recovery-cases" className="text-[#2563EB] underline font-semibold">Recovery Cases</a> to run the autonomous agent!
          </div>
        ) : (
          <div className="space-y-3">
            {decisions.map((d) => (
              <div
                key={d.id}
                className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition-colors space-y-2"
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-blue-100 text-blue-800">
                      {d.selected_strategy}
                    </span>
                    <span className="text-xs font-semibold text-[#0F172A]">
                      Case: {d.recovery_case_id}
                    </span>
                    <span className="text-xs text-[#64748B]">• Customer: {d.customer_id}</span>
                  </div>

                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-[#64748B]">ML Probability:</span>
                    <span className="font-bold text-[#2563EB]">
                      {d.ml_probability_percentage === '—' ? '—' : `${d.ml_probability_percentage}%`}
                    </span>
                    <span className="text-slate-300">|</span>
                    <span className="text-[#64748B]">Tool:</span>
                    <span className="font-mono text-slate-700">{d.tool_invoked}</span>
                  </div>
                </div>

                <div className="text-xs text-[#64748B] bg-white p-2.5 rounded-lg border border-slate-100">
                  <strong className="text-slate-700">Agent Rationale:</strong> {d.decision_reason}
                </div>

                <div className="flex items-center justify-between text-[11px] text-[#64748B] pt-1">
                  <div>
                    Status: <strong className="text-slate-700">{d.current_status}</strong> (Result: {d.tool_result})
                  </div>
                  <div className="font-mono text-[10px] text-slate-400">
                    Action ID: {d.recovery_action_id}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
