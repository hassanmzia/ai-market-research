import { create } from 'zustand';
import { authAPI } from '../services/api';
import type { User } from '../types';

function extractTokens(data: any): { accessToken: string; refreshToken: string } {
  // Django returns { tokens: { access, refresh } }
  if (data.tokens) {
    return { accessToken: data.tokens.access, refreshToken: data.tokens.refresh };
  }
  // Fallback flat format
  return {
    accessToken: data.access_token || data.access || '',
    refreshToken: data.refresh_token || data.refresh || '',
  };
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    company?: string;
  }) => Promise<void>;
  logout: () => void;
  refreshAuth: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  loadFromStorage: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.login(email, password);
      const { accessToken, refreshToken } = extractTokens(response.data);
      const user = (response.data as any).user;

      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);

      set({
        user,
        token: accessToken,
        refreshToken,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.response?.data?.message || 'Login failed';
      set({ loading: false, error: message });
      throw new Error(message);
    }
  },

  register: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.register(data);
      const { accessToken, refreshToken } = extractTokens(response.data);
      const user = (response.data as any).user;

      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);

      set({
        user,
        token: accessToken,
        refreshToken,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (err: any) {
      const errData = err.response?.data;
      let message = 'Registration failed';
      if (errData?.detail) {
        message = errData.detail;
      } else if (errData?.message) {
        message = errData.message;
      } else if (typeof errData === 'object' && errData !== null) {
        // DRF validation errors: { field: ["error1", ...] }
        const fieldErrors = Object.entries(errData)
          .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
          .join('; ');
        if (fieldErrors) message = fieldErrors;
      }
      set({ loading: false, error: message });
      throw new Error(message);
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    });
  },

  refreshAuth: async () => {
    const refreshToken = get().refreshToken;
    if (!refreshToken) {
      get().logout();
      return;
    }

    try {
      const response = await authAPI.refresh(refreshToken);
      const data = response.data as any;
      const accessToken = data.access || data.access_token || '';
      const newRefresh = data.refresh || data.refresh_token || refreshToken;

      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', newRefresh);

      set({
        token: accessToken,
        refreshToken: newRefresh,
        isAuthenticated: true,
      });
    } catch {
      get().logout();
    }
  },

  updateProfile: async (data: Partial<User>) => {
    set({ loading: true, error: null });
    try {
      const response = await authAPI.updateProfile(data);
      set({ user: response.data, loading: false });
    } catch (err: any) {
      const message =
        err.response?.data?.detail || err.response?.data?.message || 'Update failed';
      set({ loading: false, error: message });
      throw new Error(message);
    }
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (token) {
      set({ token, refreshToken, isAuthenticated: true });

      // Fetch user profile
      authAPI
        .getProfile()
        .then((response) => {
          set({ user: response.data });
        })
        .catch(() => {
          // Token may be expired, try refresh
          get().refreshAuth();
        });
    }
  },

  clearError: () => set({ error: null }),
}));
