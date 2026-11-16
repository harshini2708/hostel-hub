/**
 * HostelHub - Frontend API Client Layer
 * Handles communication with the FastAPI backend and JWT session management.
 * Automatically switches between localhost (during development) and cloud backend.
 */

const isLocal = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.protocol === 'file:'
);

// When deployed, you can customize the backend URL in localStorage, or use the default Render deployment URL
const DEFAULT_CLOUD_API = 'https://hostelhub-api.onrender.com/api';
const API_BASE_URL = isLocal 
  ? 'http://localhost:8000/api' 
  : (localStorage.getItem('hostelhub_api_url') || DEFAULT_CLOUD_API);

const api = {
  // Authentication token management
  getToken() {
    return localStorage.getItem('hostelhub_token');
  },
  setToken(token) {
    if (token) localStorage.setItem('hostelhub_token', token);
    else localStorage.removeItem('hostelhub_token');
  },
  getCurrentUser() {
    const raw = localStorage.getItem('hostelhub_user');
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  setCurrentUser(user) {
    if (user) localStorage.setItem('hostelhub_user', JSON.stringify(user));
    else localStorage.removeItem('hostelhub_user');
  },
  logout() {
    this.setToken(null);
    this.setCurrentUser(null);
  },

  // Base HTTP request handler
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.detail || (typeof data === 'string' ? data : 'An error occurred.');
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  auth: {
    async login(email, password) {
      const data = await api.request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      api.setToken(data.access_token);
      api.setCurrentUser(data.user);
      return data;
    },
    async register(userData) {
      const data = await api.request('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData)
      });
      api.setToken(data.access_token);
      api.setCurrentUser(data.user);
      return data;
    },
    async getMe() {
      return await api.request('/auth/me');
    }
  },

  // Module 1: Menu & Voting
  menu: {
    async get() {
      return await api.request('/menu');
    },
    async add(day, dish) {
      return await api.request('/menu', {
        method: 'POST',
        body: JSON.stringify({ day, dish })
      });
    },
    async vote(itemId) {
      return await api.request(`/menu/${itemId}/vote`, {
        method: 'POST'
      });
    },
    async lock() {
      return await api.request('/menu/lock', { method: 'POST' });
    },
    async unlock() {
      return await api.request('/menu/unlock', { method: 'POST' });
    }
  },

  // Module 2: Feedback & Ratings
  feedback: {
    async get() {
      return await api.request('/feedback');
    },
    async submit(meal, stars, comment) {
      return await api.request('/feedback', {
        method: 'POST',
        body: JSON.stringify({ meal, stars, comment })
      });
    }
  },

  // Module 3: Complaints & Status Tracking
  complaints: {
    async get() {
      return await api.request('/complaints');
    },
    async submit(category, description, priority) {
      return await api.request('/complaints', {
        method: 'POST',
        body: JSON.stringify({ category, description, priority })
      });
    },
    async markViewed(id) {
      return await api.request(`/complaints/${id}/view`, {
        method: 'PATCH'
      });
    },
    async markResolved(id) {
      return await api.request(`/complaints/${id}/resolve`, {
        method: 'PATCH'
      });
    }
  },

  // Module 4: Polls & Voting
  polls: {
    async get() {
      return await api.request('/polls');
    },
    async create(question, options) {
      return await api.request('/polls', {
        method: 'POST',
        body: JSON.stringify({ question, options })
      });
    },
    async vote(pollId, optionId) {
      return await api.request(`/polls/${pollId}/vote`, {
        method: 'POST',
        body: JSON.stringify({ option_id: optionId })
      });
    }
  },

  // Module 5: Suggestions
  suggestions: {
    async get() {
      return await api.request('/suggestions');
    },
    async submit(text) {
      return await api.request('/suggestions', {
        method: 'POST',
        body: JSON.stringify({ text })
      });
    }
  },

  // Module 6: Admin Dashboard
  dashboard: {
    async get() {
      return await api.request('/admin/dashboard');
    }
  }
};

window.api = api;
