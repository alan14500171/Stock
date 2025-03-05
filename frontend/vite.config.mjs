import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 直接使用同步方式创建随机值
if (typeof window === 'undefined') {
  const getRandomValues = function(arr) {
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.floor(Math.random() * 256);
    }
    return arr;
  };
  
  // NodeJS环境下全局定义
  if (typeof global !== 'undefined') {
    if (!global.crypto) {
      global.crypto = { getRandomValues };
      console.log('已为NodeJS环境添加全局crypto.getRandomValues polyfill');
    }
  }
  
  // 浏览器环境下全局定义
  if (typeof window !== 'undefined' && !window.crypto) {
    window.crypto = { getRandomValues };
    console.log('已为浏览器环境添加全局crypto.getRandomValues polyfill');
  }
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
          'vue': ['vue', 'vue-router']
        }
      }
    }
  },
  optimizeDeps: {
    include: [
      'crypto-browserify',
      'buffer',
      'stream-browserify'
    ],
    esbuildOptions: {
      define: {
        global: 'globalThis'
      }
    }
  },
  define: {
    'process.env': {},
    '__VUE_PROD_DEVTOOLS__': false,
    'global': 'globalThis',
    'process.env.NODE_DEBUG': false
  }
}) 