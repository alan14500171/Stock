<template>
  <div class="login-container">
    <div class="login-box">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="text-center mb-4">欢迎登录</h4>
          
          <!-- 错误提示 -->
          <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
            {{ error }}
            <button type="button" class="btn-close" @click="error = ''"></button>
          </div>

          <form @submit.prevent="handleLogin">
            <!-- 用户名 -->
            <div class="form-floating mb-3">
              <input 
                type="text" 
                class="form-control" 
                id="username" 
                v-model="form.username"
                placeholder="用户名"
                required
                :disabled="loading"
              >
              <label for="username">用户名</label>
            </div>

            <!-- 密码 -->
            <div class="form-floating mb-4">
              <input 
                type="password" 
                class="form-control" 
                id="password" 
                v-model="form.password"
                placeholder="密码"
                required
                :disabled="loading"
              >
              <label for="password">密码</label>
            </div>

            <!-- 登录按钮 -->
            <div class="d-grid gap-2">
              <button 
                type="submit" 
                class="btn btn-primary btn-lg"
                :disabled="loading || !form.username || !form.password"
              >
                <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
                {{ loading ? '登录中...' : '登录' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '../utils/request'
import { useMessage } from '../composables/useMessage'
import { usePermissionStore } from '../stores/permission'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const emit = defineEmits(['login-success'])

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (loading.value) return
  error.value = ''
  loading.value = true
  
  try {
    console.log('开始登录请求...')
    const response = await request.post('/api/auth/login', {
      username: form.value.username,
      password: form.value.password
    })
    
    console.log('登录响应:', response)
    
    if (response.success) {
      // 后端API返回成功但没有token，使用cookie-based认证
      message.success('登录成功')
      console.log('登录成功，准备跳转到:', route.query.redirect || '/home')
      
      // 存储用户信息
      if (response.user) {
        console.log('存储用户信息:', response.user)
        localStorage.setItem('user', JSON.stringify(response.user))
      }
      
      // 设置登录状态
      localStorage.setItem('isLoggedIn', 'true')
      
      // 预加载权限
      const permissionStore = usePermissionStore()
      console.log('开始加载权限...')
      try {
        await permissionStore.loadPermissions()
        console.log('权限加载成功')
      } catch (permError) {
        console.error('权限加载失败:', permError)
        // 即使权限加载失败，也继续登录流程
      }
      
      // 检查是否为管理员用户
      const isAdmin = form.value.username === 'admin' || form.value.username === 'alan'
      if (isAdmin) {
        console.log('管理员用户登录，设置管理员权限')
        permissionStore.setAdminPermissions()
      }
      
      // 获取重定向路径
      const redirectPath = route.query.redirect || '/home'
      
      // 使用setTimeout确保DOM更新完成后再跳转
      setTimeout(() => {
        console.log('准备跳转到:', redirectPath)
        // 使用window.location.href进行完全刷新，确保导航栏正确显示
        window.location.href = redirectPath
      }, 500) // 增加延迟时间，确保DOM更新完成
    }
  } catch (error) {
    console.error('登录失败:', error)
    error.value = error.response?.data?.message || '登录失败，请检查用户名和密码'
    message.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 400px;
}

.card {
  border: none;
  border-radius: 10px;
}

.form-floating > label {
  color: #6c757d;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.btn-outline-secondary {
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover {
  color: #fff;
  background-color: #6c757d;
  border-color: #6c757d;
}

.alert {
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.spinner-border {
  width: 1rem;
  height: 1rem;
}
</style> 