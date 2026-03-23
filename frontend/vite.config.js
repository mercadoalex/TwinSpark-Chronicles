import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
  server: {
    port: 3000,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/assets': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
