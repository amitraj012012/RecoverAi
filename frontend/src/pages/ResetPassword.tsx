import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase, isSupabaseConfigured } from '../services/supabase';
import { AlertCircle, CheckCircle, Lock } from 'lucide-react';

export const ResetPassword: React.FC = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (isSupabaseConfigured) {
        const { error } = await supabase.auth.updateUser({ password: newPassword });
        if (error) {
          setError(error.message);
          setIsSubmitting(false);
          return;
        }
      }

      setSuccess('Password updated successfully. Redirecting to workspace...');
      setTimeout(() => {
        navigate('/app', { replace: true });
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Failed to update password.');
      setIsSubmitting(false);
    }
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
          Set New Password
        </h2>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-sm border border-[#E2E8F0] sm:rounded-2xl sm:px-10">
          {error && (
            <div className="mb-5 rounded-lg bg-red-50 p-4 border border-red-100 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-[#EF4444] shrink-0 mt-0.5" />
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-5 rounded-lg bg-emerald-50 p-4 border border-emerald-100 flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-[#10B981] shrink-0 mt-0.5" />
              <div className="text-sm text-emerald-800">{success}</div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleUpdate}>
            <div>
              <label htmlFor="new-password" className="block text-sm font-medium text-[#0F172A]">
                New Password
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="new-password"
                  name="newPassword"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent text-[#0F172A]"
                />
              </div>
            </div>

            <div>
              <label htmlFor="confirm-new-password" className="block text-sm font-medium text-[#0F172A]">
                Confirm New Password
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="confirm-new-password"
                  name="confirmNewPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2.5 sm:text-sm border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent text-[#0F172A]"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#2563EB] hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2563EB] disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <span>Update Password</span>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center text-xs text-[#64748B]">
            <Link to="/login" className="font-semibold text-[#2563EB] hover:text-blue-700">
              Return to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
