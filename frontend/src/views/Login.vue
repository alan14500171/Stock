<template>
  <div class="login-container">
    <div class="card">
      <div class="card-header">
        <h4 class="mb-0">登录</h4>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleLogin">
          <div class="mb-3">
            <label for="username" class="form-label">用户名</label>
            <input type="text" class="form-control" id="username" v-model="form.username" required>
          </div>
          <div class="mb-3">
            <label for="password" class="form-label">密码</label>
            <input type="password" class="form-control" id="password" v-model="form.password" required>
          </div>
          <div class="d-grid">
            <button type="submit" class="btn btn-primary" :disabled="loading">
              {{ loading ? '登录中...' : '登录' }}
            </button>
          </div>
        </form>
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
const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', form.username)
    formData.append('password', form.password)
    
    const response = await axios.post('/auth/login', formData)
    if (response.data.success) {
      // 登录成功，跳转到之前的页面或默认页面
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    } else {
      alert(response.data.message || '登录失败')
    }
  } catch (error) {
    console.error('登录失败:', error)
    alert('登录失败，请重试')
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
  padding: 20px;
}

.card {
  width: 100%;
  max-width: 400px;
}
</style> 