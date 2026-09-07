<template>
  <div class="not-found-page">
    <div class="content">
      <div class="error-code text-gradient">404</div>
      <h1>页面未找到</h1>
      <p>抱歉，您访问的页面不存在或已被移除</p>
      <div class="actions">
        <el-button type="primary" size="large" @click="goHome">
          返回首页
        </el-button>
        <el-button size="large" @click="goBack">
          返回上一页
        </el-button>
      </div>
    </div>
    
    <div class="decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}

function goBack() {
  router.back()
}
</script>

<style lang="scss" scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
  overflow: hidden;
}

.content {
  text-align: center;
  z-index: 1;
}

.error-code {
  font-size: 160px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 16px;
}

h1 {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

p {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  
  &.circle-1 {
    width: 400px;
    height: 400px;
    background: #667eea;
    top: -150px;
    right: -150px;
  }
  
  &.circle-2 {
    width: 300px;
    height: 300px;
    background: #764ba2;
    bottom: -100px;
    left: -100px;
  }
  
  &.circle-3 {
    width: 200px;
    height: 200px;
    background: #f093fb;
    top: 50%;
    left: 10%;
  }
}
</style>
