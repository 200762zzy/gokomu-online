<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const emit = defineEmits(['openMenu'])

const tabs = [
  { path: '/', label: '首页', icon: '🏠', auth: false },
  { path: '/lobby', label: '大厅', icon: '🎮', auth: true },
  { path: '/leaderboard', label: '排行', icon: '🏆', auth: false },
  { path: '/friends', label: '好友', icon: '👥', auth: true },
]

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function go(path) {
  router.push(path)
}
</script>

<template>
  <nav class="bottom-tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.path"
      class="tab-btn"
      :class="{ active: isActive(tab.path) }"
      v-show="!tab.auth || authStore.isAuthenticated"
      @click="go(tab.path)"
    >
      <span class="tab-icon">{{ tab.icon }}</span>
      <span class="tab-label">{{ tab.label }}</span>
    </button>
    <button class="tab-btn more-btn" :class="{ active: route.path === '/profile' || route.path === '/history' || route.path === '/admin' }" @click="emit('openMenu')">
      <span class="tab-icon">☰</span>
      <span class="tab-label">更多</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  padding-bottom: env(safe-area-inset-bottom, 0px);
  background: rgba(15, 15, 40, 0.97);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 100;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.tab-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px 0;
  min-height: 44px;
  transition: color 0.15s;
  -webkit-tap-highlight-color: transparent;
}

.tab-btn:active {
  opacity: 0.7;
}

.tab-btn.active {
  color: #667eea;
}

.tab-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.tab-label {
  font-size: 0.65rem;
  font-weight: 600;
}
</style>
