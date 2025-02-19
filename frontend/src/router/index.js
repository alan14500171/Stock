import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/profit/stats'
  },
  {
    path: '/auth/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: {
      title: '登录',
      requiresAuth: false
    }
  },
  {
    path: '/profit/stats',
    name: 'ProfitStats',
    component: () => import('../views/ProfitStats.vue'),
    meta: {
      title: '盈利统计',
      requiresAuth: true
    }
  },
  {
    path: '/transactions',
    name: 'TransactionList',
    component: () => import('../views/TransactionList.vue'),
    meta: {
      title: '交易记录',
      requiresAuth: true
    }
  },
  {
    path: '/exchange-rates',
    name: 'ExchangeRateManager',
    component: () => import('../views/ExchangeRateManager.vue'),
    meta: {
      title: '汇率管理',
      requiresAuth: true
    }
  },
  {
    path: '/stocks',
    name: 'StockManager',
    component: () => import('../views/StockManager.vue'),
    meta: {
      title: '股票管理',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 股票交易系统` : '股票交易系统'

  // 检查路由是否需要认证
  if (to.meta.requiresAuth) {
    try {
      // 检查登录状态
      const response = await fetch('/auth/check_login', {
        credentials: 'include'  // 包含 cookies
      })
      const data = await response.json()
      
      if (!data.is_authenticated) {
        // 未登录，重定向到登录页
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    } catch (error) {
      console.error('检查登录状态失败:', error)
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  
  next()
})

export default router 