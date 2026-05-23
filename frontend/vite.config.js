import { defineConfig } from 'vite'   // Vite's config helper function
import react from '@vitejs/plugin-react'  // Vite plugin that enables React/JSX

export default defineConfig({
  plugins: [react()],           // enable React JSX transformation
  server: {
    port: 5173,                 // React dev server runs on port 5173
    proxy: {
      // Any request starting with /api gets forwarded to FastAPI
      '/api': {
        target: 'http://localhost:8000',  // FastAPI server address
        changeOrigin: true,               // fix the Host header
        rewrite: (path) => path.replace(/^\/api/, '')  // strip /api prefix
        // Example: /api/query → http://localhost:8000/query
      }
    }
  }
})