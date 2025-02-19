import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// 配置axios
axios.defaults.baseURL = 'http://localhost:9099'
axios.defaults.withCredentials = true // 允许跨域请求携带cookie

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    return config
  },
  error => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    return response
  },
  error => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未登录，重定向到登录页面
          router.push('/auth/login')
          break
        case 403:
          // 权限不足
          console.error('权限不足')
          break
        case 404:
          // 请求的资源不存在
          console.error('请求的资源不存在')
          break
        case 500:
          // 服务器错误
          console.error('服务器错误')
          break
        default:
          console.error(error.response.data.message || '请求失败')
      }
    } else if (error.request) {
      // 请求已经成功发起，但没有收到响应
      console.error('无法连接到服务器')
    } else {
      // 发送请求时出了点问题
      console.error('请求配置有误')
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册路由
app.use(router)

// 挂载应用
app.mount('#app') 