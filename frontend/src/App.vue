<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth.js'
import { audioManager } from './services/audioManager.js'
import { useIsMobile } from './composables/useIsMobile.js'
import { useActiveRoom } from './composables/useActiveRoom.js'
import BottomTabBar from './components/BottomTabBar.vue'
import HamburgerDrawer from './components/HamburgerDrawer.vue'
import ChangelogModal from './components/ChangelogModal.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const { isMobile } = useIsMobile()
const showDrawer = ref(false)
const { activeRoom } = useActiveRoom()
const roomDismissed = ref(sessionStorage.getItem('_room_dismissed') === '1')

const isOnGamePage = computed(() => {
  if (!activeRoom.value) return false
  const path = route.path
  const { game_type, room_id } = activeRoom.value
  if (game_type === 'gomoku' && path === `/game/${room_id}`) return true
  if (game_type === 'cc' && path === `/chess/game/${room_id}`) return true
  if (game_type === 'ludo' && path === `/ludo/game/${room_id}`) return true
  return false
})

const showBanner = computed(() => {
  return activeRoom.value && !isOnGamePage.value && !roomDismissed.value
})

const gameTypeLabel = computed(() => {
  const map = { gomoku: '五子棋', cc: '中国象棋', ludo: '飞行棋' }
  return map[activeRoom.value?.game_type] || ''
})

const gameTypeRoute = computed(() => {
  const map = { gomoku: '/game', cc: '/chess/game', ludo: '/ludo/game' }
  return map[activeRoom.value?.game_type] || ''
})

function dismissRoomBanner() {
  roomDismissed.value = true
  sessionStorage.setItem('_room_dismissed', '1')
}

function goToRoom() {
  if (!activeRoom.value) return
  router.push(`${gameTypeRoute.value}/${activeRoom.value.room_id}`)
}

watch(() => route.path, () => {
  if (isOnGamePage.value) {
    roomDismissed.value = false
    sessionStorage.removeItem('_room_dismissed')
  }
})

const showApiDialog = ref(false)
const showChangelog = ref(false)
const apiKeyInput = ref(localStorage.getItem('deepseek_api_key') || '')
const bgmEnabled = ref(true)
const bgmVolume = ref(0.3)
const sfxVolume = ref(0.5)
const showVolumePanel = ref(false)

onMounted(() => {
  audioManager.playBGM()
})

watch(() => route.path, (path) => {
  if (path.startsWith('/chess')) {
    audioManager.gameType = 'chess'
  } else if (path.startsWith('/game') || path.startsWith('/local') || path.startsWith('/ai')) {
    audioManager.gameType = 'gomoku'
  }
})
const navItems = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/lobby', label: '五子棋', icon: '⚫', auth: true },
  { path: '/chess/local', label: '象棋·本地', icon: '♜' },
  { path: '/chess/lobby', label: '象棋·在线', icon: '♞', auth: true },
  { path: '/friends', label: '好友', icon: '👥', auth: true },
  { path: '/leaderboard', label: '排行榜', icon: '🏆' },
  { path: '/history', label: '对局记录', icon: '📋', auth: true },
  { path: '/admin', label: '管理后台', icon: '⚙️', auth: true, admin: true },
  { path: '/profile', label: '个人', icon: '👤', auth: true },
]

function toggleBGM() {
  bgmEnabled.value = !bgmEnabled.value
  audioManager.bgmEnabled = bgmEnabled.value
}

function setVolume(v) {
  bgmVolume.value = v
  audioManager.setBGMVolume(v)
}

function setSFXVolume(v) {
  sfxVolume.value = v
  audioManager.setSFXVolume(v)
}

function toggleVolumePanel(e) {
  e.stopPropagation()
  showVolumePanel.value = !showVolumePanel.value
}

function openApiDialog() {
  apiKeyInput.value = localStorage.getItem('deepseek_api_key') || ''
  showApiDialog.value = true
}

function saveApiKey() {
  const key = apiKeyInput.value.trim()
  if (key) {
    localStorage.setItem('deepseek_api_key', key)
  } else {
    localStorage.removeItem('deepseek_api_key')
  }
  showApiDialog.value = false
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function onDocumentClick() {
  showVolumePanel.value = false
}

import { onUnmounted } from 'vue'
onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})

</script>

<template>
  <div class="app-layout">
    <aside v-if="!isMobile" class="sidebar">
      <div class="sidebar-header">
        <h1 class="logo" @click="router.push('/')">弈棋</h1>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
          v-show="!item.auth || (authStore.isAuthenticated && (!item.admin || authStore.user?.is_admin))"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="audio-controls">
          <button class="btn-icon" @click="toggleBGM" :title="bgmEnabled ? '关闭音乐' : '开启音乐'">
            {{ bgmEnabled ? '🔊' : '🔇' }}
          </button>
          <button class="btn-icon" @click="toggleVolumePanel" title="音量">🎚️</button>
          <div v-if="showVolumePanel" class="volume-panel" @click.stop>
            <div class="volume-row">
              <span class="volume-label">🎵 音乐</span>
              <input type="range" min="0" max="1" step="0.01" :value="bgmVolume" @input="setVolume(parseFloat($event.target.value))" class="volume-slider" />
            </div>
            <div class="volume-row">
              <span class="volume-label">🔊 音效</span>
              <input type="range" min="0" max="1" step="0.01" :value="sfxVolume" @input="setSFXVolume(parseFloat($event.target.value))" class="volume-slider" />
            </div>
          </div>
        </div>
        <button class="btn-icon" @click="showChangelog = true" title="更新日志">📋</button>
        <button class="btn-icon" @click="openApiDialog" title="API Key">🔑</button>
        <template v-if="authStore.isAuthenticated">
          <span class="user-badge" @click="router.push('/profile')">
            {{ authStore.username }}
          </span>
          <button class="btn-icon" @click="handleLogout" title="退出">🚪</button>
        </template>
        <button v-else class="btn-login" @click="router.push('/login')">登录</button>
      </div>
    </aside>

    <div v-if="showBanner" class="room-banner" @click="goToRoom">
      <span class="room-banner-icon">⏳</span>
      <span class="room-banner-text">你有一个进行中的 <strong>{{ gameTypeLabel }}</strong> 房间 <strong>#{{ activeRoom.room_id }}</strong></span>
      <span class="room-banner-action">返回继续</span>
      <button class="room-banner-close" @click.stop="dismissRoomBanner">✕</button>
    </div>
    <main class="main-content" :class="{ 'is-mobile': isMobile }">
      <router-view />
    </main>
  </div>

  <BottomTabBar v-if="isMobile" @open-menu="showDrawer = true" />
  <HamburgerDrawer :show="isMobile && showDrawer" @close="showDrawer = false" />

  <ChangelogModal :show="showChangelog" @close="showChangelog = false" />

  <Teleport to="body">
    <div v-if="showApiDialog" class="overlay" @click.self="showApiDialog = false">
      <div class="dialog">
        <h3>配置 DeepSeek API Key</h3>
        <p class="dialog-desc">配置后启用 AI 胜率分析和对局复盘功能，不配置不影响正常对局。</p>
        <input
          v-model="apiKeyInput"
          type="text"
          placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
          class="dialog-input"
          @keyup.enter="saveApiKey"
        />
        <div class="dialog-buttons">
          <button class="btn-reject" @click="showApiDialog = false">取消</button>
          <button class="btn-accept" @click="saveApiKey">保存</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #1a1a2e;
  color: #eee;
  min-height: 100vh;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 200px;
  min-width: 200px;
  background: rgba(15, 15, 40, 0.95);
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  padding: 16px;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-header {
  margin-bottom: 24px;
}

.logo {
  font-size: 1.4rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  cursor: pointer;
  text-align: center;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: #aaa;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
}

.nav-item:hover {
  background: rgba(255,255,255,0.05);
  color: #eee;
}

.nav-item.active {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.nav-icon {
  font-size: 1.1rem;
  width: 24px;
  text-align: center;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
  flex-wrap: wrap;
}

.audio-controls {
  position: relative;
  display: flex;
  gap: 2px;
}

.btn-icon {
  background: transparent;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  line-height: 1;
}

.btn-icon:hover {
  background: rgba(255,255,255,0.1);
}

.volume-panel {
  position: absolute;
  bottom: 100%;
  left: 0;
  background: #16213e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 8px 12px;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  margin-bottom: 4px;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}
.volume-row + .volume-row {
  margin-top: 6px;
}
.volume-label {
  font-size: 0.75rem;
  color: #aaa;
  min-width: 3em;
}

.volume-slider {
  width: 100px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: #333;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
}

.user-badge {
  font-size: 0.8rem;
  color: #667eea;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.user-badge:hover {
  background: rgba(102,126,234,0.1);
}

.btn-login {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  margin-left: auto;
}

.btn-login:hover {
  opacity: 0.9;
}

.main-content {
  flex: 1;
  padding: 24px;
  max-width: calc(100vw - 200px);
  overflow-y: auto;
}

.main-content.is-mobile {
  max-width: 100vw;
  padding: 12px;
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.dialog {
  background: #1a1a3e;
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  max-width: 400px;
  width: 90%;
}

.dialog h3 {
  font-size: 1.1rem;
  margin-bottom: 10px;
  color: #eee;
}

.dialog-desc {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 16px;
  line-height: 1.4;
}

.dialog-input {
  width: 100%;
  padding: 10px 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 6px;
  font-size: 0.9rem;
  font-family: monospace;
  outline: none;
  margin-bottom: 16px;
}

.dialog-input:focus {
  border-color: #667eea;
}

.dialog-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.dialog-buttons button {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
}

.btn-accept {
  background: #28a745;
}
.btn-accept:hover { opacity: 0.9; }
.btn-reject {
  background: #6c757d;
}
.btn-reject:hover { opacity: 0.9; }

.room-banner {
  position: fixed;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  background: linear-gradient(135deg, rgba(230,126,34,0.92), rgba(243,156,18,0.88));
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #fff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  white-space: nowrap;
  transition: opacity 0.2s;
  backdrop-filter: blur(4px);
}
.room-banner:hover {
  opacity: 0.95;
}
.room-banner-icon {
  font-size: 1rem;
  flex-shrink: 0;
}
.room-banner-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.room-banner-text strong {
  font-weight: 700;
}
.room-banner-action {
  padding: 4px 14px;
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.4);
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  flex-shrink: 0;
}
.room-banner-close {
  background: none;
  border: none;
  color: rgba(255,255,255,0.6);
  font-size: 0.9rem;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}
.room-banner-close:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

/* Background ambient animation */
body::before {
  content: '';
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(102, 126, 234, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(118, 75, 162, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(231, 76, 60, 0.04) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
  animation: ambientShift 12s ease-in-out infinite alternate;
}

@keyframes ambientShift {
  0%   { transform: translate(0, 0) scale(1); }
  50%  { transform: translate(-10px, 8px) scale(1.02); }
  100% { transform: translate(10px, -8px) scale(0.98); }
}

</style>
