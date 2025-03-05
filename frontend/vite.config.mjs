import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 自定义crypto polyfill
if (typeof global !== 'undefined' && !global.crypto) {
  global.crypto = {
    getRandomValues: function(buffer) {
      for (let i = 0; i < buffer.length; i++) {
        buffer[i] = Math.floor(Math.random() * 256);
      }
      return buffer;
    }
  };
  console.log('已添加自定义crypto polyfill');
}

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
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
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
    include: ['crypto-browserify'],
    esbuildOptions: {
      define: {
        global: "window"
      }
    }
  },
  define: {
    'process.env': {},
    '__VUE_PROD_DEVTOOLS__': false,
    'global': 'window',
    'process.env.NODE_DEBUG': false
  }
}) 