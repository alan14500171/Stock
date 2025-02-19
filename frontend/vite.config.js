import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    port: 9009,
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true
      },
      '/api': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true
      },
      '/stock': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true
      }
    }
  }
}) 