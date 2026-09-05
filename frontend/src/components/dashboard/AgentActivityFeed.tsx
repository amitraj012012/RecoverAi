import React from 'react';
import { AgentActivity } from '../../types/dashboard';
import { Activity, CheckCircle2, AlertTriangle, ArrowRight, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

interface AgentActivityFeedProps {
  activities: AgentActivity[];
}

export const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({ activities }) => {
  const getIcon = (status: AgentActivity['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-[#10B981]" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-[#F59E0B]" />;
      default:
        return <Activity className="w-4 h-4 text-[#2563EB]" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-[#64748B]" />
          <h3 className="text-sm font-bold text-[#0F172A]">Recent Agent Activity</h3>
        </div>
        <Link
          to="/app/recovery-cases"
          className="text-xs font-semibold text-[#2563EB] hover:text-blue-700 flex items-center"
        >
          View All
          <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </div>

      <div className="flow-root">
        {activities.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#64748B]">
            No autonomous recovery activity yet. Run a simulation to see live actions.
          </div>
        ) : (
          <ul className="-mb-4 divide-y divide-slate-100">
            {activities.map((act) => (
              <li key={act.id} className="py-3 flex items-start space-x-3">
                <div className="mt-0.5 shrink-0">{getIcon(act.status)}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-[#0F172A] leading-relaxed">{act.description}</p>
                  <div className="mt-1 flex items-center space-x-2 text-[10px] text-[#64748B]">
                    <span className="font-mono">{act.timestamp}</span>
                    {act.caseId && (
                      <>
                        <span>•</span>
                        <span className="font-mono text-slate-500">{act.caseId}</span>
                      </>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
