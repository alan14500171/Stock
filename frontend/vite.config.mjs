import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

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
      '@': path.resolve(__dirname, './src'),
      'crypto': 'crypto-browserify',
      'stream': 'stream-browserify',
      'assert': 'assert',
      'buffer': 'buffer',
      'util': 'util'
    }
  },
  build: {
    chunkSizeWarningLimit: 1000,
    cssCodeSplit: false,
    target: 'es2015',
    reportCompressedSize: false,
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue': ['vue', 'vue-router', 'vuex']
        }
      }
    }
  },
  optimizeDeps: {
    esbuildOptions: {
      define: {
        global: 'globalThis'
      }
    },
    include: ['crypto-browserify']
  },
  define: {
    'process.env': {},
    __VUE_PROD_DEVTOOLS__: false,
    'process.env.NODE_DEBUG': false,
    'global': 'window',
    'process': {
      'env': {}
    }
  }
}) 