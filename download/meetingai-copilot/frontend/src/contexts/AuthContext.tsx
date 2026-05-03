'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, User } from '@/lib/api';
import { getToken, removeToken, saveToken } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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

  const login = async (email: string, password: string) => {
    const response = await apiClient.login({ email, password });
    saveToken(response.access_token);
    apiClient.setToken(response.access_token);
    const userData = await apiClient.getMe();
    setUser(userData);
  };

  const register = async (email: string, password: string, full_name: string) => {
    // Register returns the user, then we need to login to get a token
    await apiClient.register({ email, password, full_name });
    // Now login to get the token
    const loginResponse = await apiClient.login({ email, password });
    saveToken(loginResponse.access_token);
    apiClient.setToken(loginResponse.access_token);
    const userData = await apiClient.getMe();
    setUser(userData);
  };

  const logout = () => {
    apiClient.clearToken();
    removeToken();
    setUser(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
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
