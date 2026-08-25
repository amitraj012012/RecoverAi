import React, { useEffect, useState } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchCustomers } from '../../services/dashboardService';
import { DashboardSkeleton } from '../../components/common/LoadingState';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const limit = 15;

  const loadCustomers = async () => {
    setLoading(true);
    const data = await fetchCustomers(page, limit, searchTerm);
    setCustomers(data.items);
    setTotal(data.total);
    setLoading(false);
  };

  useEffect(() => {
    loadCustomers();
  }, [page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadCustomers();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#0F172A]">Customer Risk Profiles</h2>
          <p className="text-xs text-[#64748B] mt-0.5">
            Customer payment histories, tenure, and activity scores ({total.toLocaleString()} profiles)
          </p>
        </div>

        <form onSubmit={handleSearchSubmit} className="relative">
          <input
            type="text"
            placeholder="Search company or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="text-xs pl-8 pr-3 py-2 border border-[#E2E8F0] rounded-lg bg-white text-[#0F172A] focus:outline-none focus:ring-2 focus:ring-[#2563EB] w-56 sm:w-64"
          />
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
        </form>
      </div>

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
                    <th className="px-5 py-3">Customer ID</th>
                    <th className="px-5 py-3">Company / Demo Name</th>
                    <th className="px-5 py-3">Subscription Value</th>
                    <th className="px-5 py-3">Tenure (Months)</th>
                    <th className="px-5 py-3">Activity Score</th>
                    <th className="px-5 py-3">Member Since</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {customers.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-5 py-3.5 font-mono font-semibold text-[#2563EB]">
                        {c.id}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-[#0F172A]">
                        {c.demo_name}
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-[#0F172A]">
                        ₹{(c.subscription_value / 100).toLocaleString()}/mo
                      </td>
                      <td className="px-5 py-3.5 text-slate-600">
                        {c.tenure} months
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-[#0F172A]">
                            {Math.round(c.activity_score * 100)}%
                          </span>
                          <div className="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-1.5 rounded-full ${
                                c.activity_score > 0.7
                                  ? 'bg-[#10B981]'
                                  : c.activity_score > 0.4
                                  ? 'bg-[#2563EB]'
                                  : 'bg-[#F59E0B]'
                              }`}
                              style={{ width: `${c.activity_score * 100}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-[#64748B] text-[11px] whitespace-nowrap">
                        {new Date(c.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-[#64748B]">
              <div>
                Showing {(page - 1) * limit + 1} to {Math.min(page * limit, total)} of{' '}
                {total.toLocaleString()} customers
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
