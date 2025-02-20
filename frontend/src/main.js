import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// 配置axios
axios.defaults.withCredentials = true
axios.defaults.headers.common['Content-Type'] = 'application/json'
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest'

// 添加请求拦截器
axios.interceptors.request.use(
  config => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config)
    return config
  },
  error => {
    // 对请求错误做些什么
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
axios.interceptors.response.use(
  response => {
    // 对响应数据做点什么
    console.log('响应成功:', response)
    return response
  },
  error => {
    // 对响应错误做点什么
    console.error('响应错误:', error)
    if (error.response) {
      if (error.response.status === 401) {
        // 未登录或登录过期，重定向到登录页
        router.push('/auth/login')
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

// 注册路由
app.use(router)

// 挂载应用
app.mount('#app') 