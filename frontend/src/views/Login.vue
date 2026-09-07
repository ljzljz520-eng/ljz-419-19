<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧装饰 -->
      <div class="login-left">
        <div class="decoration">
          <div class="circle circle-1"></div>
          <div class="circle circle-2"></div>
          <div class="circle circle-3"></div>
        </div>
        <div class="welcome-text">
          <h1>欢迎回来</h1>
          <p>企业级微服务管理平台</p>
          <div class="features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>安全可靠的用户认证</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>强大的权限管理系统</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>微服务架构设计</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧表单 -->
      <div class="login-right">
        <div class="form-container">
          <div class="form-header">
            <h2>用户登录</h2>
            <p>请输入您的账号和密码</p>
          </div>
          
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名或邮箱"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                class="login-btn"
                @click="handleLogin"
              >
                {{ loading ? '登录中...' : '登 录' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="form-footer">
            <span>还没有账号？</span>
            <router-link to="/register">立即注册</router-link>
          </div>
          
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Check } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

async function handleLogin() {
  if (!formRef.value) return
  
  try {
    // 先做表单验证
    await formRef.value.validate()
  } catch {
    // 表单验证失败，不需要额外提示
    return
  }

  loading.value = true
  
  try {
    const result = await userStore.login(form)
    
    if (result.success) {
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || '/'
      router.push(redirect)
    }
    // 登录失败时不在此处弹提示，由 axios 响应拦截器统一处理错误提示
    // 避免出现两个弹窗的问题
  } catch {
    // 网络异常等已由拦截器处理
  } finally {
    loading.value = false
  }
}

function fillDemo(type) {
  if (type === 'admin') {
    form.username = 'admin'
    form.password = '123456'
  } else {
    form.username = 'user'
    form.password = '123456'
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  display: flex;
  max-width: 1000px;
  width: 100%;
  min-height: 600px;
  background: white;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 60px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  
  @media (max-width: 768px) {
    display: none;
  }
}

.decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  
  &.circle-1 {
    width: 300px;
    height: 300px;
    background: #667eea;
    top: -100px;
    right: -100px;
  }
  
  &.circle-2 {
    width: 200px;
    height: 200px;
    background: #764ba2;
    bottom: 50px;
    left: -50px;
  }
  
  &.circle-3 {
    width: 150px;
    height: 150px;
    background: #f093fb;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
  }
}

.welcome-text {
  position: relative;
  z-index: 1;
  color: white;
  
  h1 {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 12px;
  }
  
  p {
    font-size: 16px;
    opacity: 0.8;
    margin-bottom: 40px;
  }
}

.features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.9;
  
  .el-icon {
    width: 24px;
    height: 24px;
    background: rgba(102, 126, 234, 0.3);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #667eea;
  }
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #f8f9fc;
}

.form-container {
  width: 100%;
  max-width: 400px;
  padding: 48px 40px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

.form-header {
  text-align: center;
  margin-bottom: 36px;
  
  h2 {
    font-size: 26px;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 8px;
  }
  
  p {
    color: #8c8c9a;
    font-size: 14px;
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 24px;
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  letter-spacing: 2px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  color: #8c8c9a;
  font-size: 14px;
  
  a {
    color: #667eea;
    font-weight: 600;
    margin-left: 8px;
    text-decoration: none;
    transition: color 0.3s;
    
    &:hover {
      color: #764ba2;
    }
  }
}

.demo-accounts {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px dashed #e8e8ee;
  
  p {
    font-size: 12px;
    color: #b0b0bc;
    margin-bottom: 12px;
    text-align: center;
  }
}

.account-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  
  .el-tag {
    cursor: pointer;
    transition: all 0.3s;
    border-radius: 8px;
    padding: 4px 12px;
    
    &:hover {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
  }
}
</style>
