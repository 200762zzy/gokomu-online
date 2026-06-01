<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { audioManager } from './services/audioManager.js'
import HomeView from './views/HomeView.vue'
import GameView from './views/GameView.vue'
import OnlineLobbyView from './views/OnlineLobbyView.vue'
import OnlineGameView from './views/OnlineGameView.vue'
import AiGameView from './views/AiGameView.vue'

const currentView = ref('home')
const replayGameData = ref(null)
const onlineGameData = ref(null)
const aiGameData = ref(null)
const showApiDialog = ref(false)
const apiKeyInput = ref(localStorage.getItem('deepseek_api_key') || '')
const bgmEnabled = ref(true)
const bgmVolume = ref(0.3)
const showVolumePanel = ref(false)

function toggleBGM() {
  bgmEnabled.value = !bgmEnabled.value
  audioManager.bgmEnabled = bgmEnabled.value
}

function setVolume(v) {
  bgmVolume.value = v
  audioManager.setBGMVolume(v)
}

function toggleVolumePanel(e) {
  e.stopPropagation()
  showVolumePanel.value = !showVolumePanel.value
}

function onStartGame() {
  replayGameData.value = null
  currentView.value = 'game'
}

function onStartOnline() {
  currentView.value = 'online_lobby'
}

function onEnterGame(data) {
  onlineGameData.value = data
  currentView.value = 'online_game'
}

function onBackToLobby() {
  onlineGameData.value = null
  currentView.value = 'online_lobby'
}

function onViewReplay(data) {
  replayGameData.value = data
  currentView.value = 'game'
}

function onStartAI(data) {
  aiGameData.value = data
  currentView.value = 'ai_game'
}

function onBack() {
  currentView.value = 'home'
  replayGameData.value = null
  onlineGameData.value = null
  aiGameData.value = null
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

function onDocumentClick() {
  showVolumePanel.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})

const viewComponent = computed(() => {
  if (currentView.value === 'home') return HomeView
  if (currentView.value === 'game') return GameView
  if (currentView.value === 'online_lobby') return OnlineLobbyView
  if (currentView.value === 'ai_game') return AiGameView
  return OnlineGameView
})
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>五子棋在线对战</h1>
      <nav>
        <div class="audio-controls">
          <button class="btn-audio" @click="toggleBGM" :title="bgmEnabled ? '关闭音乐' : '开启音乐'">
            {{ bgmEnabled ? '🔊' : '🔇' }}
          </button>
          <button class="btn-volume" @click="toggleVolumePanel" title="音量调节">🎚️</button>
          <div v-if="showVolumePanel" class="volume-panel" @click.stop>
            <label class="volume-label">BGM 音量</label>
            <input type="range" min="0" max="1" step="0.01" :value="bgmVolume" @input="setVolume(parseFloat($event.target.value))" class="volume-slider" />
          </div>
        </div>
        <button class="btn-api" @click="openApiDialog" title="配置 DeepSeek API Key">API</button>
        <button v-if="currentView !== 'home'" class="btn-back" @click="onBack">返回首页</button>
      </nav>
    </header>
    <main class="app-main">
      <HomeView
        v-if="currentView === 'home'"
        @start-game="onStartGame"
        @start-online="onStartOnline"
        @start-ai="onStartAI"
        @view-replay="onViewReplay"
      />
      <GameView
        v-else-if="currentView === 'game'"
        :replay-game-data="replayGameData"
        @back-home="onBack"
      />
      <OnlineLobbyView
        v-else-if="currentView === 'online_lobby'"
        @enter-game="onEnterGame"
      />
      <OnlineGameView
        v-else-if="currentView === 'online_game'"
        :room-id="onlineGameData?.roomId"
        :player-color="onlineGameData?.playerColor"
        :player-name="onlineGameData?.playerName"
        :opponent-name="onlineGameData?.opponentName"
        @back-lobby="onBackToLobby"
      />
      <AiGameView
        v-else-if="currentView === 'ai_game'"
        :difficulty="aiGameData?.difficulty"
        :player-color="aiGameData?.playerColor"
        @back-home="onBack"
      />
    </main>
  </div>

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
  background-image: url('/1.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  background-attachment: fixed;
  color: #eee;
  min-height: 100vh;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #333;
  margin-bottom: 24px;
}

.app-header h1 {
  font-size: 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.app-header nav {
  display: flex;
  gap: 8px;
  align-items: center;
}

.audio-controls {
  position: relative;
  display: flex;
  align-items: center;
  gap: 2px;
}

.btn-audio {
  background: transparent;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  line-height: 1;
}
.btn-audio:hover {
  opacity: 0.8;
}

.btn-volume {
  background: transparent;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  padding: 4px 4px;
  line-height: 1;
}
.btn-volume:hover {
  opacity: 0.8;
}

.volume-panel {
  position: absolute;
  top: 100%;
  right: 0;
  background: #16213e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 10px 14px;
  z-index: 50;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  margin-top: 4px;
}

.volume-label {
  display: block;
  font-size: 0.75rem;
  color: #aaa;
  margin-bottom: 6px;
}

.volume-slider {
  width: 100%;
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
.volume-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
}

.btn-api {
  background: #0f3460;
  border: 1px solid #667eea;
  color: #667eea;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}

.btn-api:hover {
  background: #1a1a4e;
}

.btn-back {
  background: #333;
  color: #eee;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-back:hover {
  background: #444;
}

.app-main {
  display: flex;
  flex-direction: column;
}

/* 毛玻璃卡片通用样式 */
.frosted {
  background: rgba(22, 33, 62, 0.85) !important;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
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
  z-index: 100;
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

.btn-accept:hover {
  opacity: 0.9;
}

.btn-reject {
  background: #6c757d;
}

.btn-reject:hover {
  opacity: 0.9;
}
</style>
