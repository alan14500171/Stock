import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 9009,
    proxy: {
      '/stock': {
        target: 'http://localhost:9099',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:9099',
        changeOrigin: true
      },
      '/stocks': {
        target: 'http://localhost:9099',
        changeOrigin: true
      }
    }
  }
}) 