import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase, supabaseConfigured } from '../lib/supabase';

export type WorkspaceMode = 'citizen' | 'control-room';

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  loading: boolean;
  configured: boolean;
  workspace: WorkspaceMode;
  setWorkspace: (mode: WorkspaceMode) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function friendlyAuthError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes('email not confirmed')) {
    return 'Email confirmation is bypassed. Please sign in directly with your email and password.';
  }
  if (lower.includes('invalid login')) {
    return 'Email or password is incorrect. If you are new, please click "Create account".';
  }
  if (lower.includes('already registered')) {
    return 'This email already has an account. Signing you in...';
  }
  return message;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [workspace, setWorkspace] = useState<WorkspaceMode>(() => {
    const saved = localStorage.getItem('urbanpulse-workspace');
    return saved === 'control-room' ? 'control-room' : 'citizen';
  });

  useEffect(() => {
    localStorage.setItem('urbanpulse-workspace', workspace);
  }, [workspace]);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    session,
    user: session?.user ?? null,
    loading,
    configured: supabaseConfigured,
    workspace,
    setWorkspace,
    signIn: async (email, password) => {
      if (!supabase) throw new Error('Supabase is not configured.');
      const { error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
      if (error) throw new Error(friendlyAuthError(error.message));
    },
    signUp: async (email, password) => {
      if (!supabase) throw new Error('Supabase is not configured.');
      const cleanEmail = email.trim();
      const { data, error } = await supabase.auth.signUp({
        email: cleanEmail,
        password,
        options: { emailRedirectTo: window.location.origin },
      });
      if (error) {
        // If already registered, attempt sign-in automatically
        if (error.message.toLowerCase().includes('already registered')) {
          const { error: signInErr } = await supabase.auth.signInWithPassword({ email: cleanEmail, password });
          if (signInErr) throw new Error(friendlyAuthError(signInErr.message));
          return;
        }
        throw new Error(friendlyAuthError(error.message));
      }
      if (data.session) return;
      // Auto-confirmed accounts can sign in immediately
      const { error: signInError } = await supabase.auth.signInWithPassword({ email: cleanEmail, password });
      if (signInError) throw new Error(friendlyAuthError(signInError.message));
    },
    signOut: async () => {
      if (!supabase) return;
      await supabase.auth.signOut();
      setWorkspace('citizen');
    },
  }), [session, loading, workspace]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
