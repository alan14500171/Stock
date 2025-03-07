import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { toast } from 'vue-toastification'

// 从window.APP_CONFIG中获取API地址
const apiBaseUrl = window.APP_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL
console.log('API Base URL (request.js):', apiBaseUrl)

// 创建axios实例
const service = axios.create({
    baseURL: apiBaseUrl,
    timeout: 15000,
    withCredentials: true,
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
    }
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        console.log('发送请求 (request.js):', config.url, config)
        
        // 添加CORS相关头
        config.headers['Access-Control-Allow-Origin'] = '*'
        config.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        config.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept, Authorization'
        
        const userStore = useUserStore()
        if (userStore.token) {
            config.headers['Authorization'] = `Bearer ${userStore.token}`
        }
        
        // 添加时间戳防止缓存
        if (config.method === 'get') {
            config.params = {
                ...config.params,
                _t: new Date().getTime()
            }
        }
        
        return config
    },
    error => {
        console.error('请求错误 (request.js):', error)
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        console.log('响应成功 (request.js):', response)
        const res = response.data
        if (res.code && res.code !== 200) {
            toast.error(res.message || '请求失败')
            return Promise.reject(new Error(res.message || '请求失败'))
        }
        return res
    },
    error => {
        console.error('响应错误 (request.js):', error)
        if (error.response) {
            console.error('错误状态码:', error.response.status)
            console.error('错误数据:', error.response.data)
            
            const router = useRouter()
            
            switch (error.response.status) {
                case 401:
                    toast.error('未登录或登录已过期')
                    router.push('/login')
                    break
                case 403:
                    toast.error('没有权限访问')
                    break
                case 404:
                    toast.error('请求的资源不存在')
                    break
                case 500:
                    toast.error('服务器错误')
                    break
                default:
                    toast.error(error.message || '请求失败')
            }
        } else if (error.code === 'ERR_NETWORK') {
            toast.error('网络连接失败，请检查网络设置')
        } else {
            toast.error('请求失败，请稍后重试')
        }
        
        return Promise.reject(error)
    }
)

export default service 