import { defineConfig } from "vite";

export default defineConfig({
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      // Proxy all /api requests to the backend (eliminates CORS/cookie issues)
      '/api': {
        target: 'http://localhost:4000',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
