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
              
              <router-link 
                :to="{ name: 'Register' }" 
                class="btn btn-outline-secondary"
                :disabled="loading"
              >
                注册新账号
              </router-link>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (loading.value) return
  
  error.value = ''
  loading.value = true
  
  try {
    const response = await axios.post('/api/auth/login', {
      username: form.username,
      password: form.password
    })
    
    if (response.data.success) {
      // 登录成功，跳转到之前的页面或默认页面
      const redirect = route.query.redirect || '/profit/stats'
      router.push(redirect)
    } else {
      error.value = response.data.message || '登录失败'
    }
  } catch (err) {
    console.error('登录失败:', err)
    error.value = err.response?.data?.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
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