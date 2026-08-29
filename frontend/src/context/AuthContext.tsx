import React, { createContext, useContext, useEffect, useState } from 'react';
import { Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../services/supabase';

const LOCAL_SESSION_KEY = 'recoverai_auth_session';

export interface MerchantUser {
  id: string;
  email: string;
  role: string;
  created_at?: string;
}

export interface AuthContextType {
  user: MerchantUser | null;
  session: Session | { access_token: string } | null;
  loading: boolean;
  isMockMode: boolean;
  signIn: (email: string, password: string) => Promise<{ error: string | null }>;
  signUp: (email: string, password: string) => Promise<{ error: string | null; message?: string }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: string | null; message?: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to create mock JWT strictly for offline local development / testing
function generateMockJwt(userId: string, email: string): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = btoa(
    JSON.stringify({
      sub: userId,
      email: email,
      role: "authenticated",
      exp: Math.floor(Date.now() / 1000) + 7 * 24 * 3600,
    })
  );
  const signature = btoa("mock_signature_for_dev_mode");
  return `${header}.${payload}.${signature}`;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<MerchantUser | null>(null);
  const [session, setSession] = useState<Session | { access_token: string } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      if (isSupabaseConfigured) {
        try {
          const { data: { session: initialSession } } = await supabase.auth.getSession();
          if (mounted) {
            if (initialSession?.user) {
              setSession(initialSession);
              const currentUser: MerchantUser = {
                id: initialSession.user.id,
                email: initialSession.user.email || '',
                role: initialSession.user.role || 'authenticated',
                created_at: initialSession.user.created_at,
              };
              setUser(currentUser);
              // Store real Supabase access token for API requests
              localStorage.setItem(
                LOCAL_SESSION_KEY,
                JSON.stringify({ user: currentUser, token: initialSession.access_token })
              );
            }
          }

          const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, currentSession) => {
            if (mounted) {
              if (currentSession?.user) {
                setSession(currentSession);
                const currentUser: MerchantUser = {
                  id: currentSession.user.id,
                  email: currentSession.user.email || '',
                  role: currentSession.user.role || 'authenticated',
                  created_at: currentSession.user.created_at,
                };
                setUser(currentUser);
                // Synchronize active Supabase access token on session change / refresh
                localStorage.setItem(
                  LOCAL_SESSION_KEY,
                  JSON.stringify({ user: currentUser, token: currentSession.access_token })
                );
              } else {
                setSession(null);
                setUser(null);
                localStorage.removeItem(LOCAL_SESSION_KEY);
              }
              setLoading(false);
            }
          });

          return () => {
            subscription.unsubscribe();
          };
        } catch (err) {
          console.warn('Supabase auth initialization error, falling back to local session check:', err);
        }
      }

      // Check local storage for persistent session
      const saved = localStorage.getItem(LOCAL_SESSION_KEY);
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.user && parsed.token) {
            setUser(parsed.user);
            setSession({ access_token: parsed.token });
          }
        } catch {
          localStorage.removeItem(LOCAL_SESSION_KEY);
        }
      }

      if (mounted) {
        setLoading(false);
      }
    }

    initAuth();

    return () => {
      mounted = false;
    };
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error: string | null }> => {
    if (!email || !password) {
      return { error: 'Please enter both email and password.' };
    }

    // Path A: Real Supabase Authentication
    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          return { error: error.message };
        }
        if (data.user && data.session) {
          const loggedInUser: MerchantUser = {
            id: data.user.id,
            email: data.user.email || '',
            role: data.user.role || 'authenticated',
            created_at: data.user.created_at,
          };
          setUser(loggedInUser);
          setSession(data.session);
          // Persist real Supabase access token for API requests
          localStorage.setItem(
            LOCAL_SESSION_KEY,
            JSON.stringify({ user: loggedInUser, token: data.session.access_token })
          );
          return { error: null };
        }
      } catch (err: any) {
        return { error: err.message || 'Authentication service error.' };
      }
    }

    // In Production: NEVER silently generate mock JWT
    if (import.meta.env.PROD) {
      return {
        error: 'Production authentication configuration error: Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your deployment environment.',
      };
    }

    // Path B: Local Development / Testing Mock Auth
    if (password.length < 6) {
      return { error: 'Password must be at least 6 characters.' };
    }

    const userId = `merchant_${btoa(email).replace(/[^a-zA-Z0-9]/g, '').slice(0, 16)}`;
    const token = generateMockJwt(userId, email);
    const mockUser: MerchantUser = {
      id: userId,
      email: email,
      role: 'authenticated',
      created_at: new Date().toISOString(),
    };

    localStorage.setItem(LOCAL_SESSION_KEY, JSON.stringify({ user: mockUser, token }));
    setUser(mockUser);
    setSession({ access_token: token });

    return { error: null };
  };

  const signUp = async (
    email: string,
    password: string
  ): Promise<{ error: string | null; message?: string }> => {
    if (!email || !password) {
      return { error: 'Please enter all required fields.' };
    }
    if (password.length < 6) {
      return { error: 'Password must be at least 6 characters.' };
    }

    if (isSupabaseConfigured) {
      try {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) {
          return { error: error.message };
        }
        if (data.session && data.user) {
          const newUser: MerchantUser = {
            id: data.user.id,
            email: data.user.email || '',
            role: data.user.role || 'authenticated',
            created_at: data.user.created_at,
          };
          setUser(newUser);
          setSession(data.session);
          localStorage.setItem(
            LOCAL_SESSION_KEY,
            JSON.stringify({ user: newUser, token: data.session.access_token })
          );
          return { error: null, message: 'Account created successfully.' };
        }
        return {
          error: null,
          message: 'Account created. Please check your email inbox to confirm your registration.',
        };
      } catch (err: any) {
        return { error: err.message || 'Signup service error.' };
      }
    }

    if (import.meta.env.PROD) {
      return {
        error: 'Production authentication configuration error: Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your deployment environment.',
      };
    }

    // Local development mode signup
    const userId = `merchant_${btoa(email).replace(/[^a-zA-Z0-9]/g, '').slice(0, 16)}`;
    const token = generateMockJwt(userId, email);
    const mockUser: MerchantUser = {
      id: userId,
      email: email,
      role: 'authenticated',
      created_at: new Date().toISOString(),
    };

    localStorage.setItem(LOCAL_SESSION_KEY, JSON.stringify({ user: mockUser, token }));
    setUser(mockUser);
    setSession({ access_token: token });

    return { error: null, message: 'Merchant account registered successfully.' };
  };

  const signOut = async (): Promise<void> => {
    if (isSupabaseConfigured) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error('Supabase sign out error:', err);
      }
    }
    localStorage.removeItem(LOCAL_SESSION_KEY);
    setUser(null);
    setSession(null);
  };

  const resetPassword = async (
    email: string
  ): Promise<{ error: string | null; message?: string }> => {
    if (!email) {
      return { error: 'Please enter your account email address.' };
    }

    if (isSupabaseConfigured) {
      try {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/reset-password`,
        });
        if (error) {
          return { error: error.message };
        }
        return {
          error: null,
          message: 'Password reset instructions have been sent to your email address.',
        };
      } catch (err: any) {
        return { error: err.message || 'Password reset request failed.' };
      }
    }

    if (import.meta.env.PROD) {
      return {
        error: 'Production authentication configuration error: Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.',
      };
    }

    return {
      error: null,
      message: `Password reset link simulated for ${email}. (Development mode)`,
    };
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        isMockMode: !isSupabaseConfigured,
        signIn,
        signUp,
        signOut,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
