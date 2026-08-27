import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Route-level lazy loading (see App.jsx) already keeps page code out of
    // the initial bundle. This groups third-party libraries into their own
    // vendor chunk, separate from app code: app code changes on every
    // deploy and would otherwise force the browser to re-download the
    // (much larger, rarely-changing) vendor code too. Splitting them lets
    // the vendor chunk stay cached across deploys where only app code changed.
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['framer-motion', 'lucide-react'],
          'vendor-charts': ['recharts'],
        },
      },
    },
  },
})
