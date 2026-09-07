import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const instance = axios.create({
    baseURL: '/api/v1',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
instance.interceptors.request.use(
    config => {
        const token = localStorage.getItem('accessToken')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 是否正在刷新 Token
let isRefreshing = false

// 响应拦截器
instance.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        const { response, config } = error

        if (response) {
            // 获取错误消息（优先使用后端返回的 message 或 detail）
            const errorMessage = response.data?.detail || response.data?.message || '请求失败'

            switch (response.status) {
                case 401:
                    // 如果是登录接口的 401，只显示一次错误提示
                    if (config.url?.includes('/auth/login')) {
                        ElMessage.error(errorMessage)
                    } else {
                        // 非登录接口的 401，清除 token 并跳转登录页
                        localStorage.removeItem('accessToken')
                        localStorage.removeItem('refreshToken')
                        if (!isRefreshing) {
                            isRefreshing = true
                            ElMessage.error('登录已过期，请重新登录')
                            router.push({ name: 'Login' })
                            setTimeout(() => { isRefreshing = false }, 2000)
                        }
                    }
                    break
                case 400:
                    ElMessage.error(errorMessage)
                    break
                case 403:
                    ElMessage.error('没有权限访问')
                    break
                case 404:
                    ElMessage.error('请求的资源不存在')
                    break
                case 422:
                    // 验证错误，统一提取第一个错误信息显示
                    if (response.data?.detail && Array.isArray(response.data.detail)) {
                        const firstError = response.data.detail[0]
                        ElMessage.error(firstError?.msg || '输入数据验证失败')
                    } else {
                        ElMessage.error(errorMessage)
                    }
                    break
                case 500:
                    ElMessage.error('服务器内部错误')
                    break
                default:
                    ElMessage.error(errorMessage)
            }
        } else {
            ElMessage.error('网络连接失败，请检查网络')
        }

        return Promise.reject(error)
    }
)

// API 接口定义
const api = {
    // 认证相关
    auth: {
        login: (data) => instance.post('/auth/login', data),
        register: (data) => instance.post('/auth/register', data),
        logout: () => instance.post('/auth/logout'),
        getCurrentUser: () => instance.get('/auth/me'),
        refreshToken: (refreshToken) => instance.post('/auth/refresh', { refresh_token: refreshToken })
    },

    // 用户管理
    users: {
        getList: (params) => instance.get('/users', { params }),
        getById: (id) => instance.get(`/users/${id}`),
        create: (data) => instance.post('/users', data),
        update: (id, data) => instance.put(`/users/${id}`, data),
        delete: (id) => instance.delete(`/users/${id}`),
        activate: (id) => instance.post(`/users/${id}/activate`),
        deactivate: (id) => instance.post(`/users/${id}/deactivate`),
        getStats: () => instance.get('/users/stats'),
        updateProfile: (data) => instance.put('/users/me', data),
        updatePassword: (data) => instance.put('/users/me/password', data)
    }
}

export default api
