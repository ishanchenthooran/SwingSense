'use client'

import axios from 'axios';
import { supabase } from '@/utils/supabase';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Questions / Logs API
export const questionsAPI = {
  getQuestions: () => api.get('/questions/'),
  createQuestion: (question) => api.post('/questions/', { question }),
  getFeedback: () => api.get('/questions/feedback'),
};

// Plans API
export const plansAPI = {
  generatePlan: (planData) => api.post('/plans/generate', planData),
  getCurrentPlan: () => api.get('/plans/current'),
};

// Resources API
export const resourcesAPI = {
  getResources: (issue) => api.get('/resources/', { params: { issue } }),
};

// Progress API
export const progressAPI = {
  createProgress: (progressData) => api.post('/progress/', progressData),
  getProgress: (startDate, endDate) => api.get('/progress/', {
    params: { start_date: startDate, end_date: endDate },
  }),
};

export default api;
