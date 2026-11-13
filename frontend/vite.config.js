import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The RAG backend runs on :8000. Proxying /api means the backend needs no CORS setup.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': process.env.API_URL || 'http://localhost:8000' },
  },
})
