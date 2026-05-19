import axios from "axios";

export const api = axios.create({
  // Use relative URL so Vite proxy handles routing to backend
  // This eliminates CORS and session cookie issues
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  withCredentials: true,
  timeout: 10000,
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
