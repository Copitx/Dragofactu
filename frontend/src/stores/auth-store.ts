import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
  setTokens: (accessToken: string) => void;
  setAccessToken: (accessToken: string) => void;
  setUser: (user: UserResponse) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      isAuthenticated: false,

      setTokens: (accessToken) =>
        set({ accessToken, isAuthenticated: true }),

      setAccessToken: (accessToken) =>
        set({ accessToken }),

      setUser: (user) =>
        set({ user }),

      logout: () =>
        set({
          accessToken: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "dragofactu-auth",
      partialize: (state) => ({
        // Keep access token in-memory only; refresh token lives in HttpOnly cookie.
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
