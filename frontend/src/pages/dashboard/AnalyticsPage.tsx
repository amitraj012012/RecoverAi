import React, { useEffect, useState } from 'react';
import { PieChart, CreditCard } from 'lucide-react';
import { RevenueTrendPoint } from '../../types/dashboard';
import {
  fetchRevenueTrends,
  fetchFailureReasons,
  fetchPaymentMethods,
} from '../../services/dashboardService';
import { RevenueRecoveryChart } from '../../components/dashboard/RevenueRecoveryChart';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const AnalyticsPage: React.FC = () => {
  const [trends, setTrends] = useState<RevenueTrendPoint[]>([]);
  const [failureReasons, setFailureReasons] = useState<any[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchRevenueTrends(),
      fetchFailureReasons(),
      fetchPaymentMethods(),
    ]).then(([t, fr, pm]) => {
      setTrends(t);
      setFailureReasons(fr);
      setPaymentMethods(pm);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">Revenue Risk & Failure Analytics</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Database-derived metrics on transaction failure exposure and payment methods (Demo / Synthetic Data)
          </p>
        </div>
      </div>

      <RevenueRecoveryChart data={trends} />

      {/* Grid: Failure Reasons & Payment Methods Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Failure Reasons Table */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <PieChart className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#0F172A]">Failure Reason Exposure</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 text-[#64748B] font-semibold uppercase text-[11px]">
                <tr>
                  <th className="px-4 py-2.5">Failure Reason</th>
                  <th className="px-4 py-2.5">Failed Count</th>
                  <th className="px-4 py-2.5">Revenue at Risk</th>
                  <th className="px-4 py-2.5">% of Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {failureReasons.map((fr) => (
                  <tr key={fr.failure_reason} className="hover:bg-slate-50/80">
                    <td className="px-4 py-3 font-semibold text-[#0F172A]">{fr.failure_reason}</td>
                    <td className="px-4 py-3 text-[#64748B]">{fr.count.toLocaleString()}</td>
                    <td className="px-4 py-3 font-semibold text-[#F59E0B]">
                      ₹{(fr.revenue_at_risk_paise / 10000000).toFixed(2)}L
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-700">{fr.percentage_of_risk}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Payment Methods Table */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center space-x-2 mb-4">
            <CreditCard className="w-4 h-4 text-[#2563EB]" />
            <h3 className="text-sm font-bold text-[#0F172A]">Payment Method Reliability</h3>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-left text-xs">
              <thead className="bg-slate-50 text-[#64748B] font-semibold uppercase text-[11px]">
                <tr>
                  <th className="px-4 py-2.5">Method</th>
                  <th className="px-4 py-2.5">Total Volume</th>
                  <th className="px-4 py-2.5">Failed</th>
                  <th className="px-4 py-2.5">Failure Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {paymentMethods.map((pm) => (
                  <tr key={pm.payment_method} className="hover:bg-slate-50/80">
                    <td className="px-4 py-3 font-semibold text-[#0F172A] uppercase">
                      {pm.payment_method}
                    </td>
                    <td className="px-4 py-3 text-[#64748B]">
                      ₹{(pm.total_volume_paise / 10000000).toFixed(1)}L ({pm.total_count})
                    </td>
                    <td className="px-4 py-3 font-semibold text-[#F59E0B]">
                      {pm.failed_count}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-700">
                      <div className="flex items-center space-x-2">
                        <span>{pm.failure_rate}%</span>
                        <div className="w-12 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${
                              pm.failure_rate > 10 ? 'bg-[#EF4444]' : 'bg-[#10B981]'
                            }`}
                            style={{ width: `${Math.min(pm.failure_rate * 5, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
