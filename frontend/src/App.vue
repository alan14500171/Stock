<template>
  <div class="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" :to="isAuthenticated ? '/home' : '/'">股票交易记录系统</router-link>
        
        <!-- 未登录状态显示登录注册按钮 -->
        <div v-if="!isAuthenticated" class="navbar-nav ms-auto">
          <router-link to="/auth/login" class="nav-link">登录</router-link>
          <router-link to="/auth/register" class="nav-link">注册</router-link>
        </div>

        <!-- 登录状态显示完整导航菜单 -->
        <template v-else>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'ProfitStats'}">盈利统计</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'TransactionList'}">交易记录</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'ExchangeRateManager'}">汇率管理</router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link" :to="{name: 'StockManager'}">股票管理</router-link>
              </li>
            </ul>
            <ul class="navbar-nav ms-auto">
              <li class="nav-item">
                <a href="#" class="nav-link" @click.prevent="handleLogout">
                  <i class="bi bi-box-arrow-right"></i> 退出登录
                </a>
              </li>
            </ul>
          </div>
        </template>
      </div>
    </nav>

    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import useMessage from './composables/useMessage'

const router = useRouter()
const message = useMessage()
const isAuthenticated = ref(false)

// 检查登录状态
const checkAuth = async () => {
  try {
    const response = await axios.get('/api/auth/check_login')
    isAuthenticated.value = response.data.is_authenticated
    
    // 如果已登录但在登录页面或注册页面，重定向到首页
    if (isAuthenticated.value && 
        (router.currentRoute.value.name === 'Login' || 
         router.currentRoute.value.name === 'Register')) {
      const redirectPath = router.currentRoute.value.query.redirect || '/home'
      router.push(redirectPath)
    }
    
    // 如果未登录且需要认证，重定向到登录页
    if (!isAuthenticated.value && router.currentRoute.value.meta.requiresAuth) {
      router.push({
        name: 'Login',
        query: { redirect: router.currentRoute.value.fullPath }
      })
    }
  } catch (error) {
    console.error('检查登录状态失败:', error)
    isAuthenticated.value = false
  }
}

// 处理登录成功
const handleLoginSuccess = async () => {
  isAuthenticated.value = true
  const redirectPath = router.currentRoute.value.query.redirect || '/home'
  await router.push(redirectPath)
}

// 处理退出登录
const handleLogout = async () => {
  try {
    const response = await axios.get('/api/auth/logout')
    if (response.data.success) {
      isAuthenticated.value = false
      message.success('退出登录成功')
      router.push('/')
    }
  } catch (error) {
    console.error('退出登录失败:', error)
    message.error('退出登录失败，请稍后重试')
  }
}

// 组件挂载时添加事件监听
onMounted(() => {
  checkAuth()
  window.addEventListener('login-success', handleLoginSuccess)
})

// 组件卸载前移除事件监听
onBeforeUnmount(() => {
  window.removeEventListener('login-success', handleLoginSuccess)
})
</script>

<style>
.app-container {
  min-height: 100vh;
  background-color: #f8f9fa;
}

.navbar {
  margin-bottom: 0;
  padding: 0.5rem 1rem;
  background-color: #343a40 !important;
}

/* 导航栏样式优化 */
.navbar-brand {
  font-weight: 500;
  font-size: 1.1rem;
  color: #fff !important;
}

.navbar-nav .nav-link {
  color: rgba(255, 255, 255, 0.85) !important;
  padding: 0.5rem 1rem;
  font-weight: 400;
  font-size: 0.9rem;
}

.navbar-nav .nav-link:hover {
  color: #fff !important;
}

.navbar-nav .nav-link.active {
  color: #fff !important;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 0.25rem;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式调整 */
@media (max-width: 991.98px) {
  .navbar-nav {
    padding: 0.5rem 0;
  }
  
  .navbar-nav .nav-link {
    padding: 0.5rem 0;
  }
  
  .navbar-nav .nav-item {
    margin: 0.25rem 0;
  }
}
</style> 