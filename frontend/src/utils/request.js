import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

// 创建axios实例
const service = axios.create({
    baseURL: window.APP_CONFIG?.API_BASE_URL || window.location.protocol + '//' + window.location.hostname + (window.location.port ? ':9099' : '/api'),
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
        console.log('发送请求 (request.js):', {
            method: config.method,
            baseURL: config.baseURL,
            url: config.url,
            fullPath: `${config.baseURL}${config.url}`,
            headers: config.headers
        })
        
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
        return response.data
    },
    error => {
        console.error('响应错误 (request.js):', error)
        const toast = useToast()
        
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