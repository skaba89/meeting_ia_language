/**
 * Zustand store for authentication state management.
 * Handles token persistence in localStorage and user session.
 */

import { create } from "zustand";
import type { UserOut } from "./api-client";

interface AuthState {
  token: string | null;
  user: UserOut | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: UserOut) => void;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  setAuth: (token: string, user: UserOut) => {
    localStorage.setItem("meetingai_token", token);
    localStorage.setItem("meetingai_user", JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("meetingai_token");
    localStorage.removeItem("meetingai_user");
    set({ token: null, user: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("meetingai_token");
    const userStr = localStorage.getItem("meetingai_user");
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as UserOut;
        set({ token, user, isAuthenticated: true });
      } catch {
        localStorage.removeItem("meetingai_token");
        localStorage.removeItem("meetingai_user");
      }
    }
  },
}));
