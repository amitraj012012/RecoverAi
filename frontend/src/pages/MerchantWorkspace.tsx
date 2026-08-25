import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, LogOut, CheckCircle2, Server, KeyRound, UserCheck } from 'lucide-react';

interface BackendMerchantProfile {
  merchant_id: string;
  email: string;
  role?: string;
}

export const MerchantWorkspace: React.FC = () => {
  const { user, session, signOut, isMockMode } = useAuth();
  const [backendProfile, setBackendProfile] = useState<BackendMerchantProfile | null>(null);
  const [backendStatus, setBackendStatus] = useState<'loading' | 'verified' | 'error'>('loading');
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = (session as any)?.access_token;

    if (!token) {
      setBackendStatus('error');
      setBackendError('No access token available in active session.');
      return;
    }

    fetch(`${apiBase}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Backend verification returned HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data: BackendMerchantProfile) => {
        setBackendProfile(data);
        setBackendStatus('verified');
      })
      .catch((err) => {
        setBackendError(err.message || 'Could not verify token with backend.');
        setBackendStatus('error');
      });
  }, [session]);

  const handleLogout = async () => {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = (session as any)?.access_token;

    if (token) {
      try {
        await fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      } catch (e) {
        // Continue frontend logout regardless
      }
    }

    await signOut();
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-[#0B1220] border-b border-slate-800 text-white sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-[#2563EB] flex items-center justify-center font-bold text-white text-lg">
                R
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight">RecoverAI</span>
                <span className="ml-2.5 px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase bg-blue-900/60 text-blue-300 border border-blue-700/50 rounded">
                  Merchant Workspace
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="hidden sm:flex flex-col items-end text-xs">
                <span className="text-slate-200 font-medium">{user?.email}</span>
                <span className="text-slate-400 font-mono text-[10px]">ID: {user?.id}</span>
              </div>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-1.5 border border-slate-700 hover:border-slate-600 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 transition-colors shadow-sm"
              >
                <LogOut className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Banner */}
        <div className="mb-6 bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-[#10B981] border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] mr-1.5"></span>
                  Authenticated Session Active
                </span>
                {isMockMode && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-[#2563EB] border border-blue-200">
                    Local Dev Session
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-bold text-[#0F172A] mt-2">
                Welcome, {user?.email?.split('@')[0] || 'Merchant'}
              </h1>
              <p className="text-sm text-[#64748B] mt-1">
                Your merchant workspace foundation is active and authenticated.
              </p>
            </div>

            <div className="flex items-center space-x-3 bg-slate-50 p-3 rounded-lg border border-slate-200 self-start sm:self-center">
              <UserCheck className="w-5 h-5 text-[#2563EB]" />
              <div className="text-xs">
                <div className="font-semibold text-[#0F172A]">Merchant Identity</div>
                <div className="text-[#64748B] font-mono">{user?.id}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Phase 1 Verification Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Frontend Session Card */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm">
            <div className="flex items-center space-x-2 text-sm font-bold text-[#0F172A] mb-4">
              <KeyRound className="w-4 h-4 text-[#2563EB]" />
              <span>Frontend Auth Session</span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-[#64748B]">Merchant Email</span>
                <span className="font-medium text-[#0F172A]">{user?.email}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-[#64748B]">Merchant ID</span>
                <span className="font-mono text-[#0F172A]">{user?.id}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-100">
                <span className="text-[#64748B]">Role</span>
                <span className="font-medium text-[#0F172A]">{user?.role || 'authenticated'}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-[#64748B]">Auth Engine</span>
                <span className="font-medium text-[#10B981] flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  Supabase Auth Provider
                </span>
              </div>
            </div>
          </div>

          {/* Backend Verification Card */}
          <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm">
            <div className="flex items-center space-x-2 text-sm font-bold text-[#0F172A] mb-4">
              <Server className="w-4 h-4 text-[#2563EB]" />
              <span>Backend Auth Boundary Verification</span>
            </div>

            <div className="space-y-3 text-xs">
              {backendStatus === 'loading' && (
                <div className="py-4 text-center text-[#64748B]">
                  <div className="w-5 h-5 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  Validating token against backend /auth/me...
                </div>
              )}

              {backendStatus === 'verified' && backendProfile && (
                <>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-[#64748B]">Backend Verified ID</span>
                    <span className="font-mono text-[#0F172A]">{backendProfile.merchant_id}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-[#64748B]">Backend Verified Email</span>
                    <span className="font-medium text-[#0F172A]">{backendProfile.email}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-100">
                    <span className="text-[#64748B]">Authorization Header</span>
                    <span className="font-mono text-[#10B981] font-semibold">Bearer token verified</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-[#64748B]">Boundary Status</span>
                    <span className="font-semibold text-[#10B981] flex items-center">
                      <ShieldCheck className="w-3.5 h-3.5 mr-1 text-[#10B981]" />
                      Protected & Authorized
                    </span>
                  </div>
                </>
              )}

              {backendStatus === 'error' && (
                <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-amber-800">
                  <div className="font-semibold">Backend Verification Notice</div>
                  <p className="mt-1">{backendError}</p>
                  <p className="mt-1 text-[11px] text-amber-700">
                    Ensure the FastAPI backend is running at http://localhost:8000.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Phase Milestone Box */}
        <div className="mt-6 p-4 rounded-xl bg-blue-50/60 border border-blue-200 flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-[#2563EB] shrink-0 mt-0.5" />
          <div className="text-xs text-slate-700">
            <span className="font-bold text-[#0F172A]">Phase 1 Milestone Complete:</span> Secure merchant authentication and route protection are fully operational. Ready for Phase 2 Dashboard & Navigation.
          </div>
        </div>
      </main>
    </div>
  );
};
