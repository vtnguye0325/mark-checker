import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    // macOS + Docker volume mounts drop inotify events; poll so HMR actually fires.
    watch: { usePolling: true, interval: 300 },
    proxy: {
      '/ml-predict': apiTarget,
      '/llm-explain': apiTarget,
      '/llm-assess': apiTarget,
      '/health': apiTarget,
    },
  },
})
