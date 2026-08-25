import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, CheckCircle, ArrowLeft, Mail } from 'lucide-react';

export const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { resetPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFeedback(null);

    if (!email.trim()) {
      setError('Please enter your account email address.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await resetPassword(email.trim());
      if (res.error) {
        setError(res.error);
      } else {
        setFeedback(res.message || 'Password reset link has been dispatched to your email.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch reset email.');
    } finally {
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
          Reset Password
        </h2>
        <p className="mt-2 text-center text-sm text-[#64748B]">
          Enter your email to receive recovery instructions
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

          {feedback && (
            <div className="mb-5 rounded-lg bg-emerald-50 p-4 border border-emerald-100 flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-[#10B981] shrink-0 mt-0.5" />
              <div className="text-sm text-emerald-800">{feedback}</div>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="reset-email" className="block text-sm font-medium text-[#0F172A]">
                Merchant Email Address
              </label>
              <div className="mt-1.5 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#64748B]">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="reset-email"
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
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-[#2563EB] hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2563EB] disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <span>Send Recovery Instructions</span>
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 text-center text-xs text-[#64748B]">
            <Link to="/login" className="inline-flex items-center font-semibold text-[#2563EB] hover:text-blue-700">
              <ArrowLeft className="mr-1 w-3.5 h-3.5" />
              Back to Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
