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

// 导入 Toast 插件
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

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
const axiosInstance = axios.create({
  baseURL: window.APP_CONFIG?.API_BASE_URL || window.location.origin + '/api',
  timeout: 15000,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
axiosInstance.interceptors.request.use(config => {
  console.log('发送请求 (main.js):', {
    method: config.method,
    baseURL: config.baseURL,
    url: config.url,
    fullPath: `${config.baseURL}${config.url}`,
    headers: config.headers
  })
  
  // 从localStorage获取token
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  return config
}, error => {
  console.error('请求错误 (main.js):', error)
  return Promise.reject(error)
})

// 响应拦截器
axiosInstance.interceptors.response.use(
  response => {
    console.log('响应成功 (main.js):', response)
    return response
  },
  error => {
    console.error('响应错误 (main.js):', error)
    if (error.response) {
      console.error('错误状态码:', error.response.status)
      console.error('错误数据:', error.response.data)
    }
    return Promise.reject(error)
  }
)

// 创建应用实例
const app = createApp(App)

// 注册Element Plus
app.use(ElementPlus, {
  locale: zhCn,
})

// 注册 Toast 插件
app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: true,
  closeButton: 'button',
  icon: true,
  rtl: false
})

// 注册全局属性
app.config.globalProperties.$axios = axiosInstance
app.config.globalProperties.$bootstrap = bootstrap

// 注册Pinia
app.use(createPinia())

// 注册路由
app.use(router)

// 注册权限指令
app.use(permissionDirective)

// 挂载应用
app.mount('#app') 