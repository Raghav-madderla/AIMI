/**
 * API service for communicating with the backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async uploadResume(file, jobRole = 'Data Scientist') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_role', jobRole);

    const token = this.getAuthToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/resumes/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload resume');
    }

    return await response.json();
  }

  async startInterview(resumeId, jobRole) {
    const response = await fetch(`${API_BASE_URL}/api/v1/interviews/start`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        resume_id: resumeId,
        job_role: jobRole,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start interview');
    }

    return await response.json();
  }

  async submitAnswer(sessionId, answer, question, domain, difficulty) {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/answer`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        answer,
        question,
        domain,
        difficulty,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit answer');
    }

    return await response.json();
  }

  async getSessionMessages(sessionId) {
    const token = this.getAuthToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/messages`, {
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get messages');
    }

    return await response.json();
  }

  async getSession(sessionId) {
    const token = this.getAuthToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get session');
    }

    return await response.json();
  }

  async getAllSessions() {
    const token = this.getAuthToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get sessions');
    }

    return await response.json();
  }

  async deleteSession(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete session');
    }

    return await response.json().catch(() => ({}));
  }

  async getInterviewReport(sessionId) {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/report`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get interview report');
    }

    return await response.json();
  }

  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      throw new Error('Backend is not reachable');
    }
  }

  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    return await response.json();
  }

  async register(email, password, name) {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        name,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return await response.json();
  }

  async logout() {
    const token = localStorage.getItem('authToken');
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        console.error('Logout failed');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
  }

  getAuthToken() {
    return localStorage.getItem('authToken');
  }

  getAuthHeaders() {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }
}

export const apiService = new ApiService();

