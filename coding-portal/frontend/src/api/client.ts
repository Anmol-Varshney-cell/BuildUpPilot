import axios from "axios";

const getBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  if (typeof window !== 'undefined' && (window.location.port === '5173' || window.location.port === '5174')) {
    return 'http://localhost:4000/api';
  }
  return '/api';
};

export const api = axios.create({
  baseURL: getBaseUrl(),
  withCredentials: true,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    if (error.code === 'NETWORK_ERROR') {
      console.error('Network connection failed - check if backend is running');
    }
    return Promise.reject(error);
  }
);
