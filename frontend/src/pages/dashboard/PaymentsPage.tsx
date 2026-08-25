import React, { useEffect, useState } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchPayments } from '../../services/dashboardService';
import { StatusBadge } from '../../components/common/StatusBadge';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const PaymentsPage: React.FC = () => {
  const [payments, setPayments] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const limit = 15;

  const loadPayments = async () => {
    setLoading(true);
    const data = await fetchPayments(page, limit, statusFilter, searchTerm);
    setPayments(data.items);
    setTotal(data.total);
    setLoading(false);
  };

  useEffect(() => {
    loadPayments();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadPayments();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">Payments Ingestion Monitor</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Real-time feed of synthetic payment transactions ({total.toLocaleString()} records stored)
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="text-xs border border-[#E2E8F0] rounded-lg px-3 py-2 bg-white text-[#0F172A] focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
          >
            <option value="">All Statuses</option>
            <option value="success">Successful</option>
            <option value="failed">Failed</option>
          </select>

          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search by customer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="text-xs pl-8 pr-3 py-2 border border-[#E2E8F0] rounded-lg bg-white text-[#0F172A] focus:outline-none focus:ring-2 focus:ring-[#2563EB] w-48 sm:w-60"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </form>
        </div>
      </div>

      {/* Table Container */}
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
                    <th className="px-5 py-3">Transaction ID</th>
                    <th className="px-5 py-3">Customer ID</th>
                    <th className="px-5 py-3">Amount</th>
                    <th className="px-5 py-3">Method</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Failure Reason</th>
                    <th className="px-5 py-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="px-5 py-8 text-center text-[#64748B]">
                        No payment transactions match the selected filter.
                      </td>
                    </tr>
                  ) : (
                    payments.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-5 py-3.5 font-mono text-[11px] font-semibold text-[#0F172A]">
                          {p.id}
                        </td>
                        <td className="px-5 py-3.5 font-mono text-[11px] text-[#2563EB]">
                          {p.customer_id}
                        </td>
                        <td className="px-5 py-3.5 font-semibold text-[#0F172A]">
                          ₹{(p.amount / 100).toLocaleString()}
                        </td>
                        <td className="px-5 py-3.5 uppercase text-[10px] font-medium text-slate-600">
                          {p.payment_method}
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={p.status === 'failed' ? 'AT_RISK' : 'RECOVERED'} />
                        </td>
                        <td className="px-5 py-3.5 text-[#64748B] max-w-xs truncate">
                          {p.failure_reason || '—'}
                        </td>
                        <td className="px-5 py-3.5 text-[#64748B] text-[11px] whitespace-nowrap">
                          {new Date(p.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-[#64748B]">
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of{' '}
                {total.toLocaleString()} transactions
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
    </div>
  );
};
