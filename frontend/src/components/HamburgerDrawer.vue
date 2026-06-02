<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { audioManager } from '../services/audioManager.js'

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['close'])

const router = useRouter()
const authStore = useAuthStore()

const apiKeyInput = ref(localStorage.getItem('deepseek_api_key') || '')
const bgmEnabled = ref(true)
const bgmVolume = ref(0.3)
const showApiDialog = ref(false)

function navigate(path) {
  emit('close')
  router.push(path)
}

function toggleBGM() {
  bgmEnabled.value = !bgmEnabled.value
  audioManager.bgmEnabled = bgmEnabled.value
}

function setVolume(v) {
  bgmVolume.value = v
  audioManager.setBGMVolume(v)
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
  emit('close')
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="drawer-overlay" @click.self="emit('close')">
      <div class="drawer-panel" @click.stop>
        <div class="drawer-header">
          <span class="drawer-title">更多</span>
          <button class="drawer-close" @click="emit('close')">✕</button>
        </div>

        <div class="drawer-body">
          <button class="menu-item" @click="navigate('/profile')" v-if="authStore.isAuthenticated">
            <span class="menu-icon">👤</span>
            <span class="menu-label">个人中心</span>
          </button>

          <button class="menu-item" @click="navigate('/history')" v-if="authStore.isAuthenticated">
            <span class="menu-icon">📋</span>
            <span class="menu-label">对局记录</span>
          </button>

          <button class="menu-item" @click="navigate('/local-game')">
            <span class="menu-icon">🎮</span>
            <span class="menu-label">本地对战</span>
          </button>

          <button class="menu-item" @click="navigate('/ai-game')">
            <span class="menu-icon">🤖</span>
            <span class="menu-label">人机对战</span>
          </button>

          <button class="menu-item" @click="navigate('/admin')" v-if="authStore.isAdmin">
            <span class="menu-icon">⚙️</span>
            <span class="menu-label">管理后台</span>
          </button>

          <div class="menu-divider"></div>

          <div class="menu-item audio-row">
            <button class="menu-btn-icon" @click="toggleBGM">
              {{ bgmEnabled ? '🔊' : '🔇' }}
            </button>
            <input
              type="range" min="0" max="1" step="0.01"
              :value="bgmVolume"
              @input="setVolume(parseFloat($event.target.value))"
              class="volume-slider"
            />
          </div>

          <button class="menu-item" @click="showApiDialog = true">
            <span class="menu-icon">🔑</span>
            <span class="menu-label">API Key 配置</span>
          </button>

          <div class="menu-divider"></div>

          <template v-if="authStore.isAuthenticated">
            <div class="menu-item user-info">
              <span class="menu-icon">👤</span>
              <span class="menu-label">{{ authStore.username }}</span>
            </div>
            <button class="menu-item logout-btn" @click="handleLogout">
              <span class="menu-icon">🚪</span>
              <span class="menu-label">退出登录</span>
            </button>
          </template>
          <button v-else class="menu-item login-btn" @click="navigate('/login')">
            <span class="menu-icon">🔑</span>
            <span class="menu-label">登录</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showApiDialog" class="overlay" @click.self="showApiDialog = false">
      <div class="dialog">
        <h3>配置 DeepSeek API Key</h3>
        <p class="dialog-desc">配置后启用 AI 胜率分析和对局复盘功能。</p>
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

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.drawer-panel {
  width: 280px;
  max-width: 80vw;
  height: 100%;
  background: rgba(15, 15, 40, 0.98);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.25s ease;
  padding-bottom: calc(56px + env(safe-area-inset-bottom, 0px));
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.drawer-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #eee;
}

.drawer-close {
  background: none;
  border: none;
  color: #888;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  min-height: 44px;
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  background: none;
  border: none;
  color: #ccc;
  font-size: 0.95rem;
  cursor: pointer;
  text-align: left;
  min-height: 48px;
  transition: background 0.15s;
}

.menu-item:active {
  background: rgba(255, 255, 255, 0.05);
}

.menu-icon {
  font-size: 1.1rem;
  width: 24px;
  text-align: center;
}

.menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 8px 16px;
}

.audio-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

.menu-btn-icon {
  background: none;
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
  padding: 8px;
  min-height: 44px;
}

.volume-slider {
  flex: 1;
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
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
}

.user-info {
  cursor: default;
  color: #667eea;
  font-weight: 600;
}

.logout-btn {
  color: #dc3545;
}

.login-btn {
  color: #667eea;
  font-weight: 600;
}

/* Dialog styles */
.overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
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
  box-sizing: border-box;
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

.btn-accept { background: #28a745; }
.btn-accept:hover { opacity: 0.9; }
.btn-reject { background: #6c757d; }
.btn-reject:hover { opacity: 0.9; }
</style>
