import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/profit/stats'
  },
  {
    path: '/profit/stats',
    name: 'ProfitStats',
    component: () => import('../views/ProfitStats.vue'),
    meta: {
      title: '盈利统计'
    }
  },
  {
    path: '/transactions',
    name: 'TransactionList',
    component: () => import('../views/TransactionList.vue'),
    meta: {
      title: '交易记录'
    }
  },
  {
    path: '/exchange-rates',
    name: 'ExchangeRateManager',
    component: () => import('../views/ExchangeRateManager.vue'),
    meta: {
      title: '汇率管理'
    }
  },
  {
    path: '/stocks',
    name: 'StockManager',
    component: () => import('../views/StockManager.vue'),
    meta: {
      title: '股票管理'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 股票交易系统` : '股票交易系统'
  next()
})

export default router 