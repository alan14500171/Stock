import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 9009,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:9099',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    },
    cors: true
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'crypto': 'crypto-browserify',
      'stream': 'stream-browserify',
      'assert': 'assert',
      'buffer': 'buffer'
    }
  },
  optimizeDeps: {
    include: ['crypto-browserify', 'buffer', 'stream-browserify']
  },
  build: {
    chunkSizeWarningLimit: 1000,
    cssCodeSplit: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    target: 'es2015',
    reportCompressedSize: false,
    outDir: 'dist'
  },
  define: {
    'process.env': {},
    '__VUE_PROD_DEVTOOLS__': false,
    'global': 'globalThis'
  }
}) 