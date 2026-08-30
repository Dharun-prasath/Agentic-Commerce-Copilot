import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import api from '@/services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User, prevSessionId?: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (token, user) => {
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
        set({ user, token, isAuthenticated: true });
      },

      logout: async () => {
        const oldSessionId = localStorage.getItem('session_id');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('session_id');
        
        if (oldSessionId) {
            try {
                await fetch(`http://localhost:8000/api/v1/integration/events/terminate/${oldSessionId}`, {
                    method: 'POST'
                });
            } catch (err) {
                // Ignore
            }
        }
        set({ user: null, token: null, isAuthenticated: false });
      },

      setUser: (user) => {
        localStorage.setItem('user', JSON.stringify(user));
        set({ user });
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
    }
  )
);
