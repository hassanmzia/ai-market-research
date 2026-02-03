import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  User,
  ResearchProject,
  ResearchTask,
  ResearchResult,
  Notification,
  SavedReport,
  AgentCard,
  WatchlistItem,
  DashboardStats,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://172.168.1.95:4063';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 and refresh token
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        });
        const { access: access_token, refresh: refresh_token } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        processQueue(null, access_token);
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ===================== Auth API =====================
export const authAPI = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string; user: User }>('/api/auth/login/', {
      email,
      password,
    }),

  register: (data: {
    email: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    company?: string;
  }) =>
    api.post<{ access_token: string; refresh_token: string; user: User }>('/api/auth/register/', data),

  refresh: (refreshToken: string) =>
    api.post<{ access_token: string; refresh_token: string }>('/api/auth/token/refresh/', {
      refresh: refreshToken,
    }),

  getProfile: () => api.get<User>('/api/auth/profile/'),

  updateProfile: (data: Partial<User>) => api.put<User>('/api/auth/profile/', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post('/api/auth/change-password/', data),
};

// ===================== Research API =====================
export const researchAPI = {
  getProjects: () => api.get<ResearchProject[]>('/api/research/projects/'),

  createProject: (data: { name: string; description?: string }) =>
    api.post<ResearchProject>('/api/research/projects/', data),

  getProject: (id: number) => api.get<ResearchProject>(`/api/research/projects/${id}/`),

  startResearch: (data: { company_name: string; project_id?: number }) =>
    api.post<{ task_id: string; task: ResearchTask }>('/api/research/tasks/start_research/', data),

  getTasks: (params?: { status?: string; search?: string }) =>
    api.get<ResearchTask[]>('/api/research/tasks/', { params }),

  getTask: (taskId: string) => api.get<ResearchTask>(`/api/research/tasks/${taskId}/`),

  getTaskResult: (taskId: string) =>
    api.get<ResearchResult>(`/api/research/tasks/${taskId}/result/`),

  cancelTask: (taskId: string) => api.post(`/api/research/tasks/${taskId}/cancel/`),
};

// ===================== Reports API =====================
export const reportsAPI = {
  getReports: (params?: { search?: string; format?: string }) =>
    api.get<SavedReport[]>('/api/reports/', { params }),

  getReport: (id: number) => api.get<SavedReport>(`/api/reports/${id}/`),

  saveReport: (data: {
    task_id: string;
    title: string;
    description?: string;
    format?: string;
  }) => api.post<SavedReport>('/api/reports/', data),

  deleteReport: (id: number) => api.delete(`/api/reports/${id}/`),

  shareReport: (id: number) =>
    api.post<{ share_token: string; share_url: string }>(`/api/reports/${id}/share/`),

  downloadReport: (id: number, format: string) =>
    api.get(`/api/reports/${id}/download/`, {
      params: { format },
      responseType: 'blob',
    }),
};

// ===================== Watchlist API =====================
export const watchlistAPI = {
  getWatchlist: () => api.get<WatchlistItem[]>('/api/watchlist'),

  addToWatchlist: (data: {
    company_name: string;
    alert_on_news?: boolean;
    alert_on_competitor_change?: boolean;
    notes?: string;
  }) => api.post<WatchlistItem>('/api/watchlist', data),

  updateWatchlistItem: (id: number, data: Partial<WatchlistItem>) =>
    api.put<WatchlistItem>(`/api/watchlist/${id}`, data),

  removeFromWatchlist: (id: number) => api.delete(`/api/watchlist/${id}`),
};

// ===================== Notifications API =====================
export const notificationsAPI = {
  getNotifications: () => api.get<Notification[]>('/api/notifications/'),

  markRead: (id: number) => api.put(`/api/notifications/${id}/read/`),

  markAllRead: () => api.put('/api/notifications/read-all/'),
};

// ===================== Dashboard API =====================
export const dashboardAPI = {
  getStats: () => api.get<DashboardStats>('/api/dashboard/'),
};

// ===================== Agents API =====================
export const agentsAPI = {
  getAgents: () => api.get<AgentCard[]>('/api/agents'),

  getAgentStatus: (name: string) => api.get<AgentCard>(`/api/agents/${name}`),
};

export default api;
