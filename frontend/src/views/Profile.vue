<template>
  <div class="profile-page animate-fade-in">
    <div class="page-header">
      <h1>个人中心</h1>
      <p>管理您的个人信息和账户设置</p>
    </div>
    
    <div class="profile-content">
      <!-- 用户信息卡片 -->
      <el-card class="profile-card">
        <div class="profile-header">
          <div class="avatar-section">
            <el-avatar :size="100" :src="userStore.user?.avatar">
              {{ userStore.user?.nickname?.charAt(0) || userStore.user?.username?.charAt(0) }}
            </el-avatar>
            <div class="user-meta">
              <h2>{{ userStore.user?.nickname || userStore.user?.username }}</h2>
              <el-tag :type="roleTagType">{{ roleLabel }}</el-tag>
            </div>
          </div>
        </div>
        
        <el-divider />
        
        <el-descriptions :column="1" border>
          <el-descriptions-item label="用户名">
            {{ userStore.user?.username }}
          </el-descriptions-item>
          <el-descriptions-item label="邮箱">
            {{ userStore.user?.email }}
          </el-descriptions-item>
          <el-descriptions-item label="手机号">
            {{ userStore.user?.phone || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="简介">
            {{ userStore.user?.bio || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">
            {{ formatDate(userStore.user?.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后登录">
            {{ userStore.user?.last_login_at ? formatDate(userStore.user?.last_login_at) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
      
      <!-- 编辑个人信息 -->
      <el-card class="edit-card">
        <template #header>
          <div class="card-header">
            <span>编辑个人信息</span>
          </div>
        </template>
        
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          :rules="profileRules"
          label-width="80px"
        >
          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
          </el-form-item>
          
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="profileForm.phone" placeholder="请输入手机号" />
          </el-form-item>
          
          <el-form-item label="头像URL">
            <el-input v-model="profileForm.avatar" placeholder="请输入头像图片URL" />
          </el-form-item>
          
          <el-form-item label="个人简介">
            <el-input
              v-model="profileForm.bio"
              type="textarea"
              :rows="3"
              placeholder="介绍一下自己吧"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" :loading="profileLoading" @click="updateProfile">
              保存修改
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <!-- 修改密码 -->
      <el-card class="password-card">
        <template #header>
          <div class="card-header">
            <span>修改密码</span>
          </div>
        </template>
        
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="80px"
        >
          <el-form-item label="当前密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" :loading="passwordLoading" @click="updatePassword">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import api from '@/api'

const userStore = useUserStore()

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

const profileForm = reactive({
  nickname: '',
  phone: '',
  avatar: '',
  bio: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const profileRules = {
  nickname: [
    { max: 100, message: '昵称最多 100 个字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ]
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const roleLabel = computed(() => {
  const roleMap = {
    admin: '管理员',
    manager: '管理者',
    user: '普通用户',
    guest: '访客'
  }
  return roleMap[userStore.user?.role] || '未知'
})

const roleTagType = computed(() => {
  const typeMap = {
    admin: 'danger',
    manager: 'warning',
    user: 'success',
    guest: 'info'
  }
  return typeMap[userStore.user?.role] || 'info'
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function initProfileForm() {
  profileForm.nickname = userStore.user?.nickname || ''
  profileForm.phone = userStore.user?.phone || ''
  profileForm.avatar = userStore.user?.avatar || ''
  profileForm.bio = userStore.user?.bio || ''
}

async function updateProfile() {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    profileLoading.value = true
    try {
      const response = await api.users.updateProfile(profileForm)
      if (response.success) {
        ElMessage.success('个人信息更新成功')
        // 重新获取用户信息
        await userStore.fetchCurrentUser()
      }
    } catch (error) {
      console.error('更新失败:', error)
    } finally {
      profileLoading.value = false
    }
  })
}

async function updatePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      const response = await api.users.updatePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      })
      
      if (response.success) {
        ElMessage.success('密码修改成功')
        // 清空表单
        passwordForm.old_password = ''
        passwordForm.new_password = ''
        passwordForm.confirm_password = ''
        passwordFormRef.value.resetFields()
      }
    } catch (error) {
      console.error('修改密码失败:', error)
    } finally {
      passwordLoading.value = false
    }
  })
}

onMounted(() => {
  initProfileForm()
})
</script>

<style lang="scss" scoped>
.profile-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 14px;
  }
}

.profile-content {
  display: grid;
  gap: 20px;
}

.profile-card {
  .profile-header {
    display: flex;
    justify-content: center;
    padding: 20px 0;
  }
  
  .avatar-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }
  
  .user-meta {
    text-align: center;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
  }
}

.card-header {
  font-size: 16px;
  font-weight: 600;
}

.edit-card,
.password-card {
  :deep(.el-form) {
    max-width: 500px;
  }
}
</style>
