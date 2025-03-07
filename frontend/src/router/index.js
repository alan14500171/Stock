import { createRouter, createWebHistory } from 'vue-router'
import { usePermissionStore } from '../stores/permission'
import Welcome from '../views/Welcome.vue'
import Login from '../views/Login.vue'
import Home from '../views/Home.vue'
import StockManager from '../views/StockManager.vue'
import TransactionList from '../views/TransactionList.vue'
import ProfitStats from '../views/ProfitStats.vue'
import ExchangeRateManager from '../views/ExchangeRateManager.vue'
import NotFound from '../views/NotFound.vue'

// 系统管理页面
import User from '../views/system/User.vue'
import Role from '../views/system/Role.vue'
import Permission from '../views/system/Permission.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome,
    meta: {
      title: '欢迎',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { 
      title: '登录',
      requiresAuth: false 
    }
  },
  {
    path: '/auth/change-password',
    name: 'ChangePassword',
    redirect: '/home',  // 重定向到首页
    meta: {
      title: '修改密码',
      requiresAuth: true
    }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {
      requiresAuth: true,
      title: '首页'
    }
  },
  {
    path: '/profit/stats',
    component: () => import('../views/ProfitStats.vue'),
    meta: { 
      title: '收益统计',
      requiresAuth: true,
      permission: 'profit:stats:view'
    }
  },
  {
    path: '/transaction/list',
    component: TransactionList,
    meta: { 
      title: '交易记录',
      requiresAuth: true,
      permission: 'transaction:records:view'
    }
  },
  {
    path: '/transactions/add',
    component: () => import('../views/TransactionAdd.vue'),
    meta: { 
      title: '添加交易',
      requiresAuth: true,
      permission: 'transaction:records:add'
    }
  },
  {
    path: '/transactions/edit/:id',
    component: () => import('../views/TransactionEdit.vue'),
    meta: { 
      title: '编辑交易',
      requiresAuth: true,
      permission: 'transaction:records:edit'
    }
  },
  {
    path: '/exchange/rate',
    component: ExchangeRateManager,
    meta: { 
      title: '汇率管理',
      requiresAuth: true,
      permission: 'exchange:rates:view'
    }
  },
  {
    path: '/stock',
    component: StockManager,
    meta: {
      title: '股票管理',
      requiresAuth: true,
      permission: 'stock:list:view'
    }
  },
  // 系统管理路由
  {
    path: '/system/user',
    component: User,
    meta: { 
      requiresAuth: true,
      permission: 'system:user:view'
    }
  },
  {
    path: '/system/role',
    component: Role,
    meta: { 
      requiresAuth: true,
      permission: 'system:role:view'
    }
  },
  {
    path: '/system/permission',
    component: Permission,
    meta: { 
      requiresAuth: true,
      permission: 'system:permission:view'
    }
  },
  {
    path: '/system/holder',
    component: () => import('../views/system/Holder.vue'),
    meta: { 
      requiresAuth: true,
      permission: 'system:holder:view'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到',
      requiresAuth: false
    }
  }
]

const router = createRouter({
  history: createWebHistory('/'),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '股票交易系统'
  
  // 检查路由是否需要认证
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (!requiresAuth) {
    // 不需要认证的路由直接放行
    return next()
  }
  
  // 检查认证状态 - 使用localStorage中的isLoggedIn标志
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  
  // 检查用户信息是否存在
  let userExists = false
  try {
    const userStr = localStorage.getItem('user')
    userExists = userStr && userStr !== 'undefined' && userStr !== 'null'
    if (userExists) {
      const user = JSON.parse(userStr)
      userExists = user && user.username
    }
  } catch (e) {
    console.error('解析用户信息失败:', e)
    userExists = false
    // 清除可能损坏的用户数据
    localStorage.removeItem('user')
    localStorage.removeItem('isLoggedIn')
  }
  
  // 只有当登录状态为true且用户信息存在时，才认为用户已认证
  const authenticated = isLoggedIn && userExists
  
  if (!authenticated) {
    // 未认证，重定向到登录页
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }
  
  // 检查是否是管理员用户
  let isAdmin = false
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    isAdmin = user.username === 'alan' || user.username === 'admin'
  } catch (e) {
    console.error('解析用户信息失败:', e)
  }
  
  // 如果是管理员用户，直接放行系统管理页面
  if (isAdmin && to.path.startsWith('/system')) {
    console.log('管理员用户访问系统管理页面，直接放行')
    return next()
  }
  
  // 检查权限
  const permissionStore = usePermissionStore()
  
  // 如果权限尚未加载，则加载权限
  if (!permissionStore.loaded) {
    try {
      await permissionStore.loadPermissions()
    } catch (error) {
      console.error('加载权限失败:', error)
      // 权限加载失败，但仍然允许用户访问不需要特定权限的页面
      if (!to.meta.permission) {
        return next()
      }
      // 如果需要特定权限，则重定向到首页
      return next({ name: 'Home' })
    }
  }
  
  // 检查路由是否需要特定权限
  const requiredPermission = to.meta.permission
  if (requiredPermission && !permissionStore.hasPermission(requiredPermission)) {
    // 没有所需权限，重定向到首页
    console.warn(`用户缺少访问 ${to.path} 所需的权限: ${requiredPermission}`)
    return next({ name: 'Home' })
  }
  
  // 通过所有检查，放行
  next()
})

// 全局后置钩子
router.afterEach(() => {
  // 路由切换完成后的处理
  // 可以在这里添加一些全局的处理逻辑
})

export default router 