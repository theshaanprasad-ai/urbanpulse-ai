import React, { useState } from 'react';
import { Activity, AlertCircle, Loader2, Lock, Mail } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

export const LoginScreen: React.FC = () => {
  const { signIn, signUp, configured } = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'signin') await signIn(email.trim(), password);
      else await signUp(email.trim(), password);
    } catch (err: any) {
      setError(err.message || 'Could not sign in.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7F5] text-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl bg-white shadow-xl border border-emerald-100 p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 text-white flex items-center justify-center">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold">UrbanPulse</h1>
            <p className="text-sm text-slate-500">Report city problems. Help your neighbourhood.</p>
          </div>
        </div>

        {!configured && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to your .env file, then restart the frontend.
          </div>
        )}

        <div className="grid grid-cols-2 gap-2 mb-5 bg-slate-100 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setMode('signin')}
            className={`py-2 rounded-lg text-sm font-semibold ${mode === 'signin' ? 'bg-white shadow text-emerald-700' : 'text-slate-500'}`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setMode('signup')}
            className={`py-2 rounded-lg text-sm font-semibold ${mode === 'signup' ? 'bg-white shadow text-emerald-700' : 'text-slate-500'}`}
          >
            Create account
          </button>
        </div>

        <form onSubmit={submit} className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium text-slate-600">Email</span>
            <div className="mt-1 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3">
              <Mail className="w-4 h-4 text-slate-400" />
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-transparent py-3 text-sm outline-none"
              />
            </div>
          </label>
          <label className="block">
            <span className="text-sm font-medium text-slate-600">Password</span>
            <div className="mt-1 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3">
              <Lock className="w-4 h-4 text-slate-400" />
              <input
                type="password"
                required
                minLength={6}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                className="w-full bg-transparent py-3 text-sm outline-none"
              />
            </div>
          </label>

          {error && (
            <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={busy || !configured}
            className="w-full rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {busy && <Loader2 className="w-4 h-4 animate-spin" />}
            {mode === 'signin' ? 'Enter' : 'Create account and enter'}
          </button>
        </form>

        <p className="mt-5 text-xs text-slate-500 leading-relaxed">
          No OTP or email verification. Use any email and password to report potholes, water blockades, garbage, and streetlight issues.
        </p>
      </div>
    </div>
  );
};
