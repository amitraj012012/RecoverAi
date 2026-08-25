import React from 'react';
import { Sparkles, ArrowUpRight, Cpu, CheckCircle2, AlertOctagon } from 'lucide-react';
import { Link } from 'react-router-dom';

interface AiRecoveryPanelProps {
  casesAnalyzed: number;
  actionsExecuted: number;
  recoveredToday: string;
  activeRate: number;
}

export const AiRecoveryPanel: React.FC<AiRecoveryPanelProps> = ({
  casesAnalyzed,
  actionsExecuted,
  recoveredToday,
  activeRate,
}) => {
  return (
    <div className="bg-[#0B1220] rounded-xl border border-slate-800 p-6 text-white shadow-sm relative overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-[#2563EB]/20 border border-[#2563EB]/40 flex items-center justify-center text-[#2563EB]">
            <Sparkles className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-white flex items-center">
              Autonomous Recovery Engine
            </h3>
            <p className="text-[11px] text-slate-400">Bounded AI Decision & Execution Layer</p>
          </div>
        </div>

        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
          Engine Online
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4">
        <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800">
          <div className="text-[11px] text-slate-400">Analyzed Cases</div>
          <div className="text-lg font-bold text-white mt-1 flex items-center">
            <Cpu className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            {casesAnalyzed.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800">
          <div className="text-[11px] text-slate-400">Actions Executed</div>
          <div className="text-lg font-bold text-white mt-1 flex items-center">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            {actionsExecuted.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800">
          <div className="text-[11px] text-slate-400">Recovered Today</div>
          <div className="text-lg font-bold text-emerald-400 mt-1">
            {recoveredToday}
          </div>
        </div>

        <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800">
          <div className="text-[11px] text-slate-400">Recovery Rate</div>
          <div className="text-lg font-bold text-white mt-1">
            {activeRate}%
          </div>
        </div>
      </div>

      <div className="pt-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-t border-slate-800/80">
        <div className="text-xs text-slate-300 flex items-center">
          <AlertOctagon className="w-3.5 h-3.5 text-blue-400 mr-1.5 shrink-0" />
          <span>Every recovery action is authorized, bounded, and verified before status change.</span>
        </div>

        <Link
          to="/app/ai-decisions"
          className="inline-flex items-center text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors"
        >
          View AI Decisions
          <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
        </Link>
      </div>
    </div>
  );
};
