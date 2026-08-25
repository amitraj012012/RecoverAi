import React from 'react';
import { ShieldCheck, KeyRound } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#0F172A]">Workspace Settings</h2>
        <p className="text-xs text-[#64748B] mt-0.5">
          Merchant account preferences and automated recovery thresholds
        </p>
      </div>

      <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm space-y-6">
        <div>
          <h3 className="text-sm font-bold text-[#0F172A] flex items-center">
            <KeyRound className="w-4 h-4 mr-2 text-[#2563EB]" />
            Merchant Profile
          </h3>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-medium text-[#64748B]">Merchant Email</label>
              <div className="mt-1 font-semibold text-[#0F172A] p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                {user?.email}
              </div>
            </div>
            <div>
              <label className="block font-medium text-[#64748B]">Merchant Workspace ID</label>
              <div className="mt-1 font-mono text-[#0F172A] p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                {user?.id}
              </div>
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-100">
          <h3 className="text-sm font-bold text-[#0F172A] flex items-center">
            <ShieldCheck className="w-4 h-4 mr-2 text-[#10B981]" />
            Recovery Policy Configuration
          </h3>
          <div className="mt-4 space-y-3 text-xs text-[#64748B]">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="font-semibold text-[#0F172A]">Max Recovery Attempts</span>
                <p className="text-[11px] text-[#64748B]">Automatic human escalation threshold</p>
              </div>
              <span className="font-bold text-[#0F172A] px-3 py-1 bg-white rounded border border-slate-200">3 Attempts</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="font-semibold text-[#0F172A]">Strict Verification Mode</span>
                <p className="text-[11px] text-[#64748B]">Require payment gateway verification before marking revenue recovered</p>
              </div>
              <span className="font-semibold text-[#10B981] px-3 py-1 bg-emerald-50 rounded border border-emerald-200">Enforced</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
