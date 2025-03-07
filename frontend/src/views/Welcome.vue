<template>
  <div class="welcome-container">
    <div class="welcome-content text-center">
      <h1 class="display-4 mb-3">欢迎使用股票交易记录系统</h1>
      <p class="lead mb-4">这是一个简单的股票交易记录管理系统，帮助您追踪港股和美股的交易记录。</p>
      
      <div class="d-grid gap-3 d-sm-flex justify-content-sm-center">
        <router-link to="/login" class="btn btn-primary btn-lg px-4">
          登录
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'

const router = useRouter()

// 检查登录状态
onMounted(async () => {
  console.log('Welcome组件挂载，开始检查登录状态')
  
  // 获取API基础URL
  const apiBaseUrl = window.APP_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL
  console.log('当前API基础地址:', apiBaseUrl)
  
  // 检查本地存储中的登录状态
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  console.log('本地存储登录状态:', isLoggedIn)
  
  if (isLoggedIn) {
    console.log('用户已登录，准备跳转到首页')
    router.push('/home')
    return
  }
  
  // 如果本地存储没有登录状态，尝试从API检查
  try {
    console.log('尝试从API检查登录状态')
    // 使用完整的URL路径
    const checkLoginUrl = `${apiBaseUrl}/api/auth/check_login`
    console.log('检查登录URL:', checkLoginUrl)
    const response = await request({
      url: checkLoginUrl,
      method: 'get',
      withCredentials: true,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    console.log('API登录状态检查响应:', response)
    
    if (response.is_authenticated) {
      console.log('API确认用户已登录')
      localStorage.setItem('isLoggedIn', 'true')
      if (response.user) {
        console.log('存储用户信息:', response.user)
        localStorage.setItem('user', JSON.stringify(response.user))
      }
      router.push('/home')
    } else {
      console.log('API确认用户未登录')
    }
  } catch (error) {
    console.error('检查登录状态失败:', error)
    if (error.code === 'ERR_NETWORK') {
      console.error('网络连接失败，可能是后端服务未启动或网络问题')
      console.error('尝试访问的地址:', apiBaseUrl)
    }
  }
})
</script>

<style scoped>
.welcome-container {
  min-height: calc(100vh - 56px);  /* 减去导航栏的高度 */
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  padding: 20px;
}

.welcome-content {
  max-width: 600px;
  margin: 0 auto;
  background-color: #fff;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.display-4 {
  font-size: 2.5rem;
  font-weight: 300;
  line-height: 1.2;
}

.lead {
  font-size: 1.25rem;
  font-weight: 300;
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
  border-radius: 0.5rem;
}

@media (max-width: 576px) {
  .display-4 {
    font-size: 2rem;
  }
  
  .lead {
    font-size: 1.1rem;
  }
  
  .btn-lg {
    width: 100%;
  }
  
  .welcome-content {
    padding: 1.5rem;
  }
}
</style> 