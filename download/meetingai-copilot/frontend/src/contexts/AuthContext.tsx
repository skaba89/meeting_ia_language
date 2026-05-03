'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { apiClient, User } from '@/lib/api';
import {
  getToken,
  removeToken,
  saveToken,
  getRefreshToken,
  saveRefreshToken,
  isTokenExpiringSoon,
} from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const REFRESH_INTERVAL = 4 * 60 * 1000; // Check every 4 minutes
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes before expiry

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      apiClient.setToken(token);
      const userData = await apiClient.getMe();
      setUser(userData);
    } catch {
      removeToken();
      apiClient.clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!user) return;

    const checkTokenExpiry = () => {
      if (isTokenExpiringSoon(TOKEN_REFRESH_THRESHOLD)) {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          // Attempt silent refresh — if backend supports it
          apiClient.getMe().catch(() => {
            // If refresh fails, logout
            logout();
          });
        }
      }
    };

    refreshTimerRef.current = setInterval(checkTokenExpiry, REFRESH_INTERVAL);

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const login = async (email: string, password: string) => {
    const response = await apiClient.login({ email, password });
    saveToken(response.access_token);
    apiClient.setToken(response.access_token);
    const userData = await apiClient.getMe();
    setUser(userData);
  };

  const register = async (email: string, password: string, full_name: string) => {
    await apiClient.register({ email, password, full_name });
    const loginResponse = await apiClient.login({ email, password });
    saveToken(loginResponse.access_token);
    apiClient.setToken(loginResponse.access_token);
    const userData = await apiClient.getMe();
    setUser(userData);
  };

  const logout = useCallback(() => {
    apiClient.clearToken();
    removeToken();
    setUser(null);
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
    }
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    try {
      apiClient.setToken(token);
      const userData = await apiClient.getMe();
      setUser(userData);
    } catch {
      // Silently fail — user state remains unchanged
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
