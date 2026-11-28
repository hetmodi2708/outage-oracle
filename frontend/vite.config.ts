import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  devtools: {
    // Remove this `apply` property to enable devtools for build as well
    apply: 'serve',
  },
  plugins: [react()],
  server: {
    // During development, forward /api/* to the FastAPI backend on port 8000.
    // The browser only ever talks to localhost:5173, so no CORS issues and no hardcoded backend URL.
    // e.g. fetch('/api/search') -> http://localhost:8000/search
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
