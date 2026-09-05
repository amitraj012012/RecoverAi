import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, AlertCircle, ArrowRight, Lock, Mail, Sparkles } from 'lucide-react';

const DEMO_EMAIL = import.meta.env.VITE_DEMO_EMAIL || 'demo@recoverai.io';
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || '';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoSubmitting, setIsDemoSubmitting] = useState(false);
  const { signIn, isMockMode } = useAuth();
  const navigate = useNavigate();

  const handleExploreDemo = async () => {
    setError(null);
    setIsDemoSubmitting(true);
    try {
      if (!DEMO_PASSWORD) {
        setError('Demo access is not configured. Please set VITE_DEMO_PASSWORD in your environment.');
        setIsDemoSubmitting(false);
        return;
      }
      // Authenticate with dedicated demo account credentials via standard Supabase JWT
      const res = await signIn(DEMO_EMAIL, DEMO_PASSWORD);
      if (res.error) {
        setError(`Demo sign-in failed: ${res.error}`);
        setIsDemoSubmitting(false);
      } else {
        navigate('/app', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during demo sign in.');
      setIsDemoSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim()) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await signIn(email.trim(), password);
      if (res.error) {
        setError(res.error);
        setIsSubmitting(false);
      } else {
        navigate('/app', { replace: true });
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during sign in.');
      setIsSubmitting(false);
    }
  };

  const handleFillDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('password123');
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-[#F8FAFC]">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center items-center space-x-2.5">
          <div className="w-10 h-10 rounded-xl bg-[#0B1220] flex items-center justify-center text-white font-bold text-xl shadow-sm">
            R
          </div>
          <span className="text-2xl font-bold tracking-tight text-[#0F172A]">RecoverAI</span>
        </div>
        <h2 className="mt-6 text-center text-2xl font-bold tracking-tight text-[#0F172A]">
          Merchant Workspace Login
        </h2>
        <p className="mt-2 text-center text-sm text-[#64748B]">
          Autonomous AI Revenue Recovery Engine
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm border border-[#E2E8F0] sm:rounded-2xl sm:px-10">
          {error && (
            <div className="mb-5 rounded-lg bg-red-50 p-4 border border-red-100 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-[#EF4444] shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* Dedicated Instant 1-Click Demo Access for Judges/Reviewers */}
          <div className="mb-6">
            <button
              type="button"
              onClick={handleExploreDemo}
              disabled={isDemoSubmitting || isSubmitting}
              className="w-full relative group overflow-hidden rounded-xl p-[1px] focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 transition-all disabled:opacity-60 shadow-sm hover:shadow-md"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-[#2563EB] via-[#4F46E5] to-[#0EA5E9] rounded-xl" />
              <span className="relative flex items-center justify-center gap-2.5 px-4 py-3 bg-[#0B1220] hover:bg-[#111C30] rounded-[11px] text-white font-semibold text-sm transition-colors">
                {isDemoSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-[#38BDF8] animate-pulse" />
                    <span>Explore Demo Workspace</span>
                    <span className="ml-1.5 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#2563EB]/40 text-[#93C5FD] border border-[#3B82F6]/50">
                      1-CLICK ACCESS
                    </span>
                  </>
                )}
              </span>
            </button>
            <p className="mt-2 text-center text-[11px] text-[#64748B]">
              Instantly experience live AI decisioning, risk analytics & simulator with benchmark SaaS data.
            </p>
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#E2E8F0]" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-3 text-[#94A3B8] font-medium tracking-wider">
                Or sign in with credentials
              </span>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#0F172A]">
                Merchant Email
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@business.com"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent text-[#0F172A] placeholder-[#94A3B8]"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium text-[#0F172A]">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs font-semibold text-[#2563EB] hover:text-blue-700"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent text-[#0F172A] placeholder-[#94A3B8]"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting || isDemoSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#2563EB] hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2563EB] disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <>
                    <span>Sign In to Workspace</span>
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>

          {isMockMode && (
            <div className="mt-6 pt-5 border-t border-[#E2E8F0]">
              <div className="flex items-center space-x-1.5 text-xs text-[#64748B] mb-2 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" />
                <span>Demo Quick Fill:</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleFillDemo('merchant@saas.io')}
                  className="flex-1 py-1.5 px-2.5 text-xs bg-slate-100 hover:bg-slate-200 text-[#0F172A] rounded-md font-medium text-center transition-colors"
                >
                  merchant@saas.io
                </button>
                <button
                  type="button"
                  onClick={() => handleFillDemo('founder@subs.com')}
                  className="flex-1 py-1.5 px-2.5 text-xs bg-slate-100 hover:bg-slate-200 text-[#0F172A] rounded-md font-medium text-center transition-colors"
                >
                  founder@subs.com
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 text-center text-xs text-[#64748B]">
            Don't have a merchant account?{' '}
            <Link to="/signup" className="font-semibold text-[#2563EB] hover:text-blue-700">
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
