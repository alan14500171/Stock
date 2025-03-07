<template>
  <div>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary" v-if="isAuthenticated">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">股票交易系统</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link to="/home" class="nav-link">
                <i class="bi bi-house-door"></i> 首页
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('profit:stats:view')">
              <router-link to="/profit/stats" class="nav-link">
                <i class="bi bi-bar-chart"></i> 收益统计
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('transaction:records:view')">
              <router-link to="/transaction/list" class="nav-link">
                <i class="bi bi-list-ul"></i> 交易记录
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('exchange:rates:view')">
              <router-link to="/exchange/rate" class="nav-link">
                <i class="bi bi-currency-exchange"></i> 汇率管理
              </router-link>
            </li>
            <li class="nav-item" v-if="hasPermission('stock:list:view')">
              <router-link to="/stock" class="nav-link">
                <i class="bi bi-graph-up"></i> 股票管理
              </router-link>
            </li>
            
            <!-- 系统管理下拉菜单 -->
            <li class="nav-item dropdown" v-if="hasAnySystemPermission">
              <a class="nav-link dropdown-toggle" href="#" id="systemDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-gear"></i> 系统管理
              </a>
              <ul class="dropdown-menu" aria-labelledby="systemDropdown">
                <li v-if="hasPermission('system:user:view')">
                  <router-link to="/system/user" class="dropdown-item">
                    <i class="bi bi-people"></i> 用户管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:role:view')">
                  <router-link to="/system/role" class="dropdown-item">
                    <i class="bi bi-person-badge"></i> 角色管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:permission:view')">
                  <router-link to="/system/permission" class="dropdown-item">
                    <i class="bi bi-shield-lock"></i> 权限管理
                  </router-link>
                </li>
                <li v-if="hasPermission('system:holder:view')">
                  <router-link to="/system/holder" class="dropdown-item">
                    <i class="bi bi-person-vcard"></i> 持有人管理
                  </router-link>
                </li>
              </ul>
            </li>
          </ul>
          
          <!-- 用户菜单 -->
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-person-circle"></i> {{ currentUsername }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                <li>
                  <a href="#" class="dropdown-item" @click.prevent="openPasswordChangeModal">
                    <i class="bi bi-key"></i> 修改密码
                  </a>
                </li>
                <li>
                  <a href="#" class="dropdown-item" @click.prevent="logout">
                    <i class="bi bi-box-arrow-right"></i> 退出登录
                  </a>
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="container-fluid mt-3">
      <router-view></router-view>
    </div>

    <!-- 密码修改模态框 -->
    <PasswordChangeModal v-if="isAuthenticated" ref="passwordChangeModal" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { usePermissionStore } from './stores/permission'
import PasswordChangeModal from './components/PasswordChangeModal.vue'

const router = useRouter()
const permissionStore = usePermissionStore()
const passwordChangeModal = ref(null)

// 计算属性：是否已认证
const isAuthenticated = computed(() => {
  const loggedIn = localStorage.getItem('isLoggedIn') === 'true'
  console.log('认证状态检查:', loggedIn)
  
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
  
  console.log('用户信息存在:', userExists)
  
  // 只有当登录状态为true且用户信息存在时，才认为用户已认证
  const authenticated = loggedIn && userExists
  console.log('最终认证状态:', authenticated)
  
  return authenticated
})

// 权限检查函数
const hasPermission = (permissionCode) => {
  return permissionStore.hasPermission(permissionCode)
}

// 计算属性：当前用户名
const currentUsername = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    console.log('当前用户:', user.username || '未登录')
    return user.username || ''
  } catch (e) {
    console.error('解析用户信息失败:', e)
    return ''
  }
})

// 计算属性：是否是管理员用户
const isAdmin = computed(() => {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const admin = user.username === 'alan' || user.username === 'admin'
    console.log('是否管理员:', admin)
    return admin
  } catch (e) {
    console.error('解析用户信息失败:', e)
    return false
  }
})

// 计算属性：是否有任何系统管理权限
const hasAnySystemPermission = computed(() => {
  const hasPermission = permissionStore.hasPermission('system:user:view') || 
                        permissionStore.hasPermission('system:role:view') || 
                        permissionStore.hasPermission('system:permission:view')
  console.log('是否有系统管理权限:', hasPermission)
  return hasPermission
})

// 方法：退出登录
const logout = () => {
  console.log('执行退出登录')
  
  // 先移除登录状态和用户信息
  localStorage.removeItem('isLoggedIn')
  localStorage.removeItem('user')
  permissionStore.resetPermissions()
  
  // 确保在路由跳转前完成状态更新
  nextTick(() => {
    console.log('退出登录，准备跳转到登录页')
    // 强制刷新页面以确保导航栏完全关闭
    window.location.href = '/login'
  })
}

// 方法：打开修改密码模态框
const openPasswordChangeModal = () => {
  passwordChangeModal.value.openModal()
}

// 方法：初始化Bootstrap下拉菜单
const initBootstrapDropdowns = () => {
  console.log('初始化Bootstrap下拉菜单')
  if (typeof window !== 'undefined') {
    // 确保Bootstrap已加载
    if (!window.bootstrap && typeof bootstrap !== 'undefined') {
      console.log('从导入的bootstrap设置window.bootstrap')
      window.bootstrap = bootstrap
    }
    
    if (window.bootstrap) {
      try {
        // 检查导航栏是否显示
        const navbar = document.querySelector('.navbar')
        if (!navbar) {
          console.log('导航栏元素不存在，跳过初始化下拉菜单')
          return
        }
        
        if (getComputedStyle(navbar).display === 'none') {
          console.log('导航栏不可见，跳过初始化下拉菜单')
          return
        }
        
        // 销毁现有的下拉菜单实例
        const dropdownElementList = document.querySelectorAll('.dropdown-toggle')
        console.log('找到下拉菜单元素数量:', dropdownElementList.length)
        
        if (dropdownElementList.length === 0) {
          console.log('未找到下拉菜单元素，可能导航栏尚未渲染')
          return
        }
        
        dropdownElementList.forEach((dropdownToggleEl, index) => {
          console.log(`初始化第${index+1}个下拉菜单:`, dropdownToggleEl.id || '无ID')
          
          // 尝试获取现有实例并销毁
          const instance = window.bootstrap.Dropdown.getInstance(dropdownToggleEl)
          if (instance) {
            console.log(`销毁第${index+1}个下拉菜单的现有实例`)
            instance.dispose()
          }
          
          // 创建新实例
          new window.bootstrap.Dropdown(dropdownToggleEl)
        })
        console.log('Bootstrap下拉菜单初始化完成')
      } catch (error) {
        console.error('初始化下拉菜单时出错:', error)
      }
    } else {
      console.warn('Bootstrap未加载，无法初始化下拉菜单')
      console.log('window对象上可用的属性:', Object.keys(window).filter(key => key.startsWith('b')))
      
      // 尝试从CDN加载Bootstrap
      console.log('尝试从全局变量获取Bootstrap')
      setTimeout(() => {
        if (window.bootstrap) {
          console.log('成功从全局变量获取Bootstrap，重新尝试初始化')
          initBootstrapDropdowns()
        }
      }, 500)
    }
  }
}

// 监听认证状态变化
watch(isAuthenticated, (newValue) => {
  console.log('认证状态变化:', newValue)
  if (newValue) {
    if (!permissionStore.loaded) {
      console.log('认证状态变化，加载权限')
      permissionStore.loadPermissions()
    }
    
    // 在DOM更新后初始化下拉菜单
    nextTick(() => {
      console.log('DOM更新后初始化下拉菜单')
      setTimeout(initBootstrapDropdowns, 300)
    })
  }
})

// 生命周期钩子：组件挂载后
onMounted(() => {
  console.log('App组件挂载')
  
  // 导入Bootstrap
  import('bootstrap').then(module => {
    console.log('动态导入Bootstrap成功')
    window.bootstrap = module
    
    // 如果已登录，预加载权限
    if (isAuthenticated.value && !permissionStore.loaded) {
      console.log('组件挂载，加载权限')
      permissionStore.loadPermissions()
    }
    
    // 确保Bootstrap的下拉菜单正常工作
    nextTick(() => {
      console.log('组件挂载后初始化下拉菜单(第一次)')
      setTimeout(initBootstrapDropdowns, 300)
    })
    
    // 再次尝试初始化下拉菜单（以防第一次尝试失败）
    setTimeout(() => {
      console.log('组件挂载后初始化下拉菜单(第二次)')
      initBootstrapDropdowns()
    }, 1000)
    
    // 第三次尝试初始化下拉菜单
    setTimeout(() => {
      console.log('组件挂载后初始化下拉菜单(第三次)')
      initBootstrapDropdowns()
    }, 2000)
  }).catch(error => {
    console.error('动态导入Bootstrap失败:', error)
  })
  
  // 监听路由变化，在路由变化后重新初始化下拉菜单
  router.beforeEach((to, from, next) => {
    console.log('路由变化前:', from.path, '->', to.path)
    next()
  })
  
  router.afterEach((to, from) => {
    console.log('路由变化后:', from.path, '->', to.path)
    console.log('当前认证状态:', isAuthenticated.value)
    
    // 检查是否是登录或退出相关的路由变化
    const isAuthRoute = to.path.includes('/login') || from.path.includes('/login')
    
    if (isAuthRoute) {
      console.log('检测到登录/退出相关的路由变化，将在页面加载后重新检查认证状态')
      // 在页面完全加载后重新检查认证状态
      setTimeout(() => {
        const currentAuth = localStorage.getItem('isLoggedIn') === 'true'
        console.log('页面加载后的认证状态:', currentAuth)
        
        if (currentAuth && to.path !== '/login') {
          console.log('用户已登录，确保导航栏显示')
          nextTick(() => {
            setTimeout(initBootstrapDropdowns, 300)
          })
        }
      }, 500)
    } else if (isAuthenticated.value) {
      console.log('路由变化后初始化下拉菜单')
      nextTick(() => {
        setTimeout(initBootstrapDropdowns, 300)
      })
    }
  })
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