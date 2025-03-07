import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import * as bootstrap from 'bootstrap'
// 导入Bootstrap Icons
import 'bootstrap-icons/font/bootstrap-icons.css'
import './assets/main.css'
import permissionDirective from './directives/permission'

// 将Bootstrap挂载到window对象
window.bootstrap = bootstrap

// 确保Bootstrap正确初始化
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM加载完成，初始化Bootstrap组件')
  
  // 确保Bootstrap已加载
  if (!window.bootstrap) {
    console.log('从全局变量设置window.bootstrap')
    window.bootstrap = bootstrap
  }
  
  // 初始化所有下拉菜单
  setTimeout(() => {
    const dropdownElementList = document.querySelectorAll('.dropdown-toggle')
    console.log('找到下拉菜单元素数量:', dropdownElementList.length)
    
    if (dropdownElementList.length > 0) {
      dropdownElementList.forEach((dropdownToggleEl, index) => {
        console.log(`初始化第${index+1}个下拉菜单`)
        new bootstrap.Dropdown(dropdownToggleEl)
      })
    }
    
    // 初始化所有模态框
    const modalElements = document.querySelectorAll('.modal')
    console.log('找到模态框元素数量:', modalElements.length)
    
    if (modalElements.length > 0) {
      modalElements.forEach((modalEl, index) => {
        console.log(`初始化第${index+1}个模态框`)
        new bootstrap.Modal(modalEl)
      })
    }
  }, 500)
})

// 配置axios
axios.defaults.baseURL = window.APP_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL
axios.defaults.withCredentials = true
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest'

// 添加请求拦截器
axios.interceptors.request.use(config => {
  // 从localStorage获取token
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  // 添加CSRF token
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
  if (csrfToken) {
    config.headers['X-CSRF-TOKEN'] = csrfToken
  }
  
  return config
})

// 创建应用实例
const app = createApp(App)

// 注册Element Plus
app.use(ElementPlus, {
  locale: zhCn,
})

// 注册全局属性
app.config.globalProperties.$axios = axios
app.config.globalProperties.$bootstrap = bootstrap

// 注册Pinia
app.use(createPinia())

// 注册路由
app.use(router)

// 注册权限指令
app.use(permissionDirective)

// 挂载应用
app.mount('#app') 