'use client'

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  // Get token from Supabase session
  const { createClient } = await import('@supabase/supabase-js');
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://your-project.supabase.co';
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'your-anon-key';
  const supabase = createClient(supabaseUrl, supabaseKey);
  
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

// Questions/Logs API
export const questionsAPI = {
  getQuestions: () => api.get('/questions/questions/'),
  createQuestion: (question) => api.post('/questions/questions/', { question }),
  getFeedback: () => api.get('/questions/feedback/'),
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
    params: { start_date: startDate, end_date: endDate } 
  }),
};

export default api;
