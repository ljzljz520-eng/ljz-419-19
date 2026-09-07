<template>
  <div class="dashboard-page animate-fade-in">
    <div class="page-header">
      <h1>控制台</h1>
      <p>欢迎回来，{{ userStore.user?.nickname || userStore.user?.username }}</p>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-grid" v-loading="statsLoading">
      <div class="stat-card" v-for="stat in stats" :key="stat.title">
        <div class="stat-icon" :style="{ background: stat.gradient }">
          <el-icon :size="24"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-title">{{ stat.title }}</div>
        </div>
      </div>
    </div>
    
    <!-- 快捷操作 -->
    <div class="section">
      <h2 class="section-title">快捷操作</h2>
      <div class="quick-actions">
        <el-card 
          v-for="action in quickActions" 
          :key="action.title"
          shadow="hover"
          class="action-card"
          @click="handleAction(action)"
        >
          <div class="action-icon" :style="{ background: action.gradient }">
            <el-icon :size="28"><component :is="action.icon" /></el-icon>
          </div>
          <div class="action-title">{{ action.title }}</div>
          <div class="action-desc">{{ action.desc }}</div>
        </el-card>
      </div>
    </div>
    
    <!-- 系统信息 -->
    <div class="section">
      <h2 class="section-title">系统信息</h2>
      <el-card class="system-info-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
          <el-descriptions-item label="API 网关">Kong 3.5</el-descriptions-item>
          <el-descriptions-item label="后端框架">FastAPI</el-descriptions-item>
          <el-descriptions-item label="前端框架">Vue 3</el-descriptions-item>
          <el-descriptions-item label="数据库">PostgreSQL 15</el-descriptions-item>
          <el-descriptions-item label="当前用户角色">
            <el-tag :type="roleTagType">{{ roleLabel }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import api from '@/api'
import { User, UserFilled, Setting, DocumentCopy, DataLine, Monitor } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const statsLoading = ref(false)
const userStats = ref({
  total: 0,
  active: 0,
  inactive: 0,
  by_role: {}
})

const stats = computed(() => [
  {
    title: '用户总数',
    value: userStats.value.total,
    icon: 'User',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  },
  {
    title: '活跃用户',
    value: userStats.value.active,
    icon: 'UserFilled',
    gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)'
  },
  {
    title: '管理员',
    value: userStats.value.by_role?.admin || 0,
    icon: 'Setting',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
  },
  {
    title: '普通用户',
    value: userStats.value.by_role?.user || 0,
    icon: 'Monitor',
    gradient: 'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)'
  }
])

const quickActions = computed(() => {
  const actions = [
    {
      title: '个人中心',
      desc: '管理个人信息和密码',
      icon: 'UserFilled',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      path: '/profile'
    }
  ]
  
  if (userStore.isManager) {
    actions.unshift({
      title: '用户管理',
      desc: '管理系统用户',
      icon: 'User',
      gradient: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
      path: '/users'
    })
  }
  
  return actions
})

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

async function fetchStats() {
  if (!userStore.isAdmin) return
  
  statsLoading.value = true
  try {
    const response = await api.users.getStats()
    if (response.success) {
      userStats.value = response.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    statsLoading.value = false
  }
}

function handleAction(action) {
  if (action.path) {
    router.push(action.path)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text-secondary);
    font-size: 14px;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: var(--border-radius);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
  }
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.action-card {
  cursor: pointer;
  text-align: center;
  padding: 8px;
  transition: all var(--transition-normal);
  
  &:hover {
    transform: translateY(-4px);
    
    .action-icon {
      transform: scale(1.1);
    }
  }
}

.action-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 16px;
  transition: transform var(--transition-normal);
}

.action-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.action-desc {
  font-size: 13px;
  color: var(--text-secondary);
}

.system-info-card {
  :deep(.el-descriptions__label) {
    width: 120px;
    font-weight: 500;
  }
}
</style>
