import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Request interceptor — attach JWT + session ID ──────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const sessionId = getSessionId();
  if (sessionId) {
    config.headers['X-Session-Id'] = sessionId;
  }
  return config;
});

// ── Response interceptor — handle 401 ─────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      import('@/store/authStore').then(({ useAuthStore }) => {
        useAuthStore.getState().logout();
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
      });
    }
    return Promise.reject(error);
  }
);

// ── Session ID management ─────────────────────────────────────────────────
export function getSessionId(): string {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}

export default api;
