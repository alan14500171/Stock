import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { toast } from 'vue-toastification'

// 创建axios实例
const service = axios.create({
    baseURL: window.APP_CONFIG?.API_BASE_URL || import.meta.env.VITE_API_BASE_URL,
    timeout: 15000,
    withCredentials: true
})

// 请求拦截器
service.interceptors.request.use(
    config => {
        const userStore = useUserStore()
        if (userStore.token) {
            config.headers['Authorization'] = `Bearer ${userStore.token}`
        }
        return config
    },
    error => {
        console.error('请求错误:', error)
        return Promise.reject(error)
    }
)

// 响应拦截器
service.interceptors.response.use(
    response => {
        const res = response.data
        if (res.code && res.code !== 200) {
            toast.error(res.message || '请求失败')
            return Promise.reject(new Error(res.message || '请求失败'))
        }
        return res
    },
    error => {
        console.error('响应错误:', error)
        const router = useRouter()
        
        if (error.response) {
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
        } else {
            toast.error('网络错误，请检查网络连接')
        }
        
        return Promise.reject(error)
    }
)

export default service 