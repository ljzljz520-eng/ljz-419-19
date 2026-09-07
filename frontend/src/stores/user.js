import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useUserStore = defineStore('user', () => {
    // 状态
    const user = ref(null)
    const accessToken = ref(localStorage.getItem('accessToken') || '')
    const refreshToken = ref(localStorage.getItem('refreshToken') || '')

    // 计算属性
    const isLoggedIn = computed(() => !!accessToken.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const isManager = computed(() => ['admin', 'manager'].includes(user.value?.role))

    // 登录
    async function login(credentials) {
        try {
            const response = await api.auth.login(credentials)
            if (response.success) {
                const { access_token, refresh_token, user: userData } = response.data

                accessToken.value = access_token
                refreshToken.value = refresh_token
                user.value = userData

                localStorage.setItem('accessToken', access_token)
                localStorage.setItem('refreshToken', refresh_token)

                return { success: true }
            }
            return { success: false, message: response.message }
        } catch (error) {
            return { success: false, message: error.message || '登录失败' }
        }
    }

    // 注册
    async function register(data) {
        try {
            const response = await api.auth.register(data)
            return { success: response.success, message: response.message }
        } catch (error) {
            return { success: false, message: error.message || '注册失败' }
        }
    }

    // 登出
    function logout() {
        user.value = null
        accessToken.value = ''
        refreshToken.value = ''
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
    }

    // 获取当前用户信息
    async function fetchCurrentUser() {
        if (!accessToken.value) return

        try {
            const response = await api.auth.getCurrentUser()
            if (response.success) {
                user.value = response.data
            }
        } catch (error) {
            console.error('获取用户信息失败:', error)
            logout()
        }
    }

    // 刷新 Token
    async function refreshAccessToken() {
        try {
            const response = await api.auth.refreshToken(refreshToken.value)
            if (response.success) {
                accessToken.value = response.data.access_token
                refreshToken.value = response.data.refresh_token

                localStorage.setItem('accessToken', response.data.access_token)
                localStorage.setItem('refreshToken', response.data.refresh_token)

                return true
            }
            return false
        } catch (error) {
            logout()
            return false
        }
    }

    // 初始化 - 如果有 token 则获取用户信息
    if (accessToken.value) {
        fetchCurrentUser()
    }

    return {
        user,
        accessToken,
        refreshToken,
        isLoggedIn,
        isAdmin,
        isManager,
        login,
        register,
        logout,
        fetchCurrentUser,
        refreshAccessToken
    }
})
