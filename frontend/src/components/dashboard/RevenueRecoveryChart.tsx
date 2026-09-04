import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { RevenueTrendPoint } from '../../types/dashboard';

interface RevenueRecoveryChartProps {
  data: RevenueTrendPoint[];
}

const formatCurrency = (val: number) => `₹${(val / 100000).toFixed(1)}L`;

export const RevenueRecoveryChart: React.FC<RevenueRecoveryChartProps> = ({ data }) => {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
        <div>
          <h3 className="text-sm font-bold text-[#0F172A]">Revenue Recovery Trajectory</h3>
          <p className="text-xs text-[#64748B]">
            Daily timeline of revenue at risk vs verified recovered revenue
          </p>
        </div>

        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
            <span className="text-[#64748B]">Revenue at Risk</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            <span className="text-[#64748B]">Recovered Revenue</span>
          </div>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorAtRisk" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#94A3B8"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#E2E8F0' }}
            />
            <YAxis
              stroke="#94A3B8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatCurrency}
            />
            <Tooltip
              formatter={(value: any, name: any) => [
                `₹${(Number(value) / 100000).toFixed(2)}L`,
                name === 'atRisk' ? 'Revenue at Risk' : name === 'recovered' ? 'Recovered Revenue' : name,
              ]}
              labelFormatter={(label: string) => `Date: ${label}`}
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderColor: '#E2E8F0',
                borderRadius: '8px',
                fontSize: '12px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
            />
            <Area
              type="monotone"
              dataKey="atRisk"
              name="Revenue at Risk"
              stroke="#F59E0B"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorAtRisk)"
            />
            <Area
              type="monotone"
              dataKey="recovered"
              name="Recovered Revenue"
              stroke="#10B981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRecovered)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
