import React from 'react';
import { RecoveryCaseSummary } from '../../types/dashboard';
import { StatusBadge } from '../common/StatusBadge';
import { ArrowRight, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ActiveCasesTableProps {
  cases: RecoveryCaseSummary[];
}

export const ActiveCasesTable: React.FC<ActiveCasesTableProps> = ({ cases }) => {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
      <div className="p-5 flex items-center justify-between border-b border-slate-100">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-[#2563EB]" />
          <h3 className="text-sm font-bold text-[#0F172A]">Active Recovery Cases</h3>
        </div>
        <Link
          to="/app/recovery-cases"
          className="text-xs font-semibold text-[#2563EB] hover:text-blue-700 flex items-center"
        >
          View All Cases
          <ArrowRight className="w-3 h-3 ml-1" />
        </Link>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
          <thead className="bg-slate-50 text-[#64748B] font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th className="px-5 py-3">Customer</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Failure Reason</th>
              <th className="px-5 py-3">Recovery Prob.</th>
              <th className="px-5 py-3">Strategy</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {cases.map((c) => (
              <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="px-5 py-3.5 whitespace-nowrap">
                  <div className="font-semibold text-[#0F172A]">{c.customerName}</div>
                  <div className="text-[#64748B] font-mono text-[10px]">{c.customerId}</div>
                </td>
                <td className="px-5 py-3.5 whitespace-nowrap font-semibold text-[#0F172A]">
                  ₹{c.amount.toLocaleString()}
                </td>
                <td className="px-5 py-3.5 text-[#64748B] max-w-xs truncate">
                  {c.failureReason}
                </td>
                <td className="px-5 py-3.5 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-[#0F172A]">
                      {Math.round(c.recoveryProbability ?? 70)}%
                    </span>
                    <div className="w-12 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-[#2563EB] h-1.5 rounded-full"
                        style={{ width: `${Math.round(c.recoveryProbability ?? 70)}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3.5 whitespace-nowrap">
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium font-mono text-[10px] border border-slate-200">
                    {c.selectedStrategy.replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-5 py-3.5 whitespace-nowrap">
                  <StatusBadge status={c.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
