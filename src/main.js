import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 导入Bootstrap的CSS和JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// 配置axios
axios.defaults.baseURL = 'http://localhost:9099'

const app = createApp(App)

// 注册路由
app.use(router)

// 挂载应用
app.mount('#app') 