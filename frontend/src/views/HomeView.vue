<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { audioManager } from '../services/audioManager.js'
import ChangelogModal from '../components/ChangelogModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const savedGames = ref([])
const showAiDialog = ref(false)
const aiDifficulty = ref('easy')
const aiColor = ref('black')
const activeTab = ref('comp')
const showChangelog = ref(false)
const guestBannerHidden = ref(localStorage.getItem('hide_guest_banner') === '1')

function dismissBanner() {
  guestBannerHidden.value = true
  localStorage.setItem('hide_guest_banner', '1')
}

const networkUrl = computed(() => {
  const ip = window.LAN_IP
  const port = window.LAN_PORT || 8000
  if (!ip || ip === '127.0.0.1') return null
  return `http://${ip}:${port}`
})

function loadHistory() {
  try {
    const data = localStorage.getItem('gomoku_history')
    savedGames.value = data ? JSON.parse(data).reverse() : []
  } catch {
    savedGames.value = []
  }
}

function formatResult(entry) {
  if (entry.result === 'draw') return '平局'
  if (entry.result === 'resign_black') return '白方胜（黑方认负）'
  if (entry.result === 'resign_white') return '黑方胜（白方认负）'
  if (entry.result === 'black_win') return '黑方胜'
  if (entry.result === 'white_win') return '白方胜'
  return '-'
}

function clearHistory() {
  localStorage.removeItem('gomoku_history')
  savedGames.value = []
}

async function copyAddress() {
  if (!networkUrl.value) return
  try {
    await navigator.clipboard.writeText(networkUrl.value)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = networkUrl.value
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
}

function startAi() {
  const params = new URLSearchParams({ difficulty: aiDifficulty.value, playerColor: aiColor.value })
  router.push(`/ai-game?${params}`)
}

function viewReplay(game) {
  const data = JSON.stringify(game)
  router.push(`/local-game?replay=${encodeURIComponent(data)}`)
}

onMounted(loadHistory)
</script>

<template>
  <div class="home-container">
    <div v-if="networkUrl" class="network-card" @click="copyAddress" title="点击复制">
      <span class="network-label">局域网地址</span>
      <span class="network-url">{{ networkUrl }}</span>
      <span class="network-copy">复制</span>
    </div>

    <div v-if="!authStore.isAuthenticated && !guestBannerHidden" class="guest-banner">
      <div class="banner-content">
        <span class="banner-icon">✨</span>
        <span class="banner-text">注册账号即可体验在线对战、排行榜、好友对战等完整功能</span>
        <button class="banner-btn" @click="router.push('/login')">去注册</button>
      </div>
      <button class="banner-close" @click="dismissBanner">✕</button>
    </div>

    <div class="welcome-section">
      <h1 class="welcome-title">
        {{ authStore.isAuthenticated ? `欢迎回来，${authStore.username}` : '欢迎来到 弈棋' }}
      </h1>
      <p class="welcome-sub">竞技 &amp; 娱乐 对战平台</p>
    </div>

    <div class="tab-bar">
      <button
        :class="['tab-btn', { active: activeTab === 'comp' }]"
        @click="audioManager.playClick(); activeTab = 'comp'"
      >
        <span class="tab-icon">🏆</span>
        <span class="tab-label">竞技</span>
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'fun' }]"
        @click="audioManager.playClick(); activeTab = 'fun'"
      >
        <span class="tab-icon">🎲</span>
        <span class="tab-label">娱乐</span>
      </button>
    </div>

    <template v-if="activeTab === 'comp'">
      <div class="section-label">五子棋</div>

      <div class="card game-card" @click="audioManager.playClick(); router.push('/local-game')">
        <h2>本地对战</h2>
        <p class="subtitle">双人同屏</p>
        <button class="btn-primary" @click.stop="audioManager.playClick(); router.push('/local-game')">
          开始游戏
        </button>
      </div>
      <div class="card online-card" @click="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/lobby' : '/login?redirect=/lobby')">
        <h2>在线对战</h2>
        <p class="subtitle">联网匹配</p>
        <button class="btn-online" @click.stop="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/lobby' : '/login?redirect=/lobby')">
          创建 / 加入
        </button>
      </div>
      <div class="card ai-card" @click="audioManager.playClick(); showAiDialog = true">
        <h2>人机对战</h2>
        <p class="subtitle">AI 陪练</p>
        <button class="btn-ai" @click.stop="audioManager.playClick(); showAiDialog = true">
          开始挑战
        </button>
      </div>

      <div class="rules-card">
        <h3>五子棋规则</h3>
        <ul>
          <li>15×15 标准棋盘，黑棋先手</li>
          <li>两名玩家轮流落子</li>
          <li>五子连珠（横/竖/斜）获胜</li>
          <li>支持悔棋、认输、和棋</li>
          <li>对局结束后可回放复盘</li>
          <li>每步落子后自动请求AI分析</li>
        </ul>
      </div>

      <div class="section-label">中国象棋</div>

      <div class="card chess-card" @click="audioManager.playClick(); router.push('/chess/local')">
        <h2>象棋·本地</h2>
        <p class="subtitle">双人同屏</p>
        <button class="btn-chess" @click.stop="audioManager.playClick(); router.push('/chess/local')">
          开始对弈
        </button>
      </div>
      <div class="card chess-card" @click="audioManager.playClick(); router.push('/chess/local?ai=true&difficulty=easy')">
        <h2>象棋·人机</h2>
        <p class="subtitle">AI 陪练</p>
        <button class="btn-chess" @click.stop="audioManager.playClick(); router.push('/chess/local?ai=true&difficulty=easy')">
          开始挑战
        </button>
      </div>
      <div class="card chess-online-card" @click="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/chess/lobby' : '/login?redirect=/chess/lobby')">
        <h2>象棋·在线</h2>
        <p class="subtitle">联网对战</p>
        <button class="btn-chess-online" @click.stop="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/chess/lobby' : '/login?redirect=/chess/lobby')">
          创建 / 加入
        </button>
      </div>
    </template>

    <template v-if="activeTab === 'fun'">
      <div class="card ludo-card" @click="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/ludo/lobby' : '/login?redirect=/ludo/lobby')">
        <h2>飞行棋·在线</h2>
        <p class="subtitle">四人欢乐对战</p>
        <button class="btn-ludo" @click.stop="audioManager.playClick(); router.push(authStore.isAuthenticated ? '/ludo/lobby' : '/login?redirect=/ludo/lobby')">
          创建 / 加入
        </button>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="showAiDialog" class="overlay" @click.self="showAiDialog = false">
        <div class="dialog">
          <h3>人机对战</h3>
          <div class="dialog-row">
            <label>难度</label>
            <div class="btn-group">
              <button
                :class="['btn-group-item', { active: aiDifficulty === 'easy' }]"
                @click="aiDifficulty = 'easy'"
              >初级</button>
              <button
                :class="['btn-group-item', { active: aiDifficulty === 'medium' }]"
                @click="aiDifficulty = 'medium'"
              >中级</button>
              <button
                :class="['btn-group-item', { active: aiDifficulty === 'hard' }]"
                @click="aiDifficulty = 'hard'"
              >高级</button>
            </div>
          </div>
          <div class="dialog-row">
            <label>执棋</label>
            <div class="btn-group">
              <button
                :class="['btn-group-item', { active: aiColor === 'black' }]"
                @click="aiColor = 'black'"
              >黑棋（先手）</button>
              <button
                :class="['btn-group-item', { active: aiColor === 'white' }]"
                @click="aiColor = 'white'"
              >白棋（后手）</button>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="btn-cancel" @click="showAiDialog = false">取消</button>
            <button class="btn-start" @click="audioManager.playClick(); showAiDialog = false; startAi()">开始</button>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="savedGames.length > 0" class="history-card">
      <div class="history-header">
        <h3>对局历史</h3>
        <button class="btn-clear" @click="clearHistory">清空</button>
      </div>
      <div
        v-for="game in savedGames"
        :key="game.id"
        class="history-item"
        @click="viewReplay(game)"
      >
        <span class="history-result">{{ formatResult(game) }}</span>
        <span class="history-moves">
          黑{{ game.blackMoveCount || 0 }}手 / 白{{ game.whiteMoveCount || 0 }}手
        </span>
        <span class="history-time">{{ game.timestamp }}</span>
      </div>
    </div>

    <div class="footer-links">
      <button class="changelog-link" @click="audioManager.playClick(); showChangelog = true">
        📋 查看更新日志
      </button>
    </div>
  </div>

  <ChangelogModal :show="showChangelog" @close="showChangelog = false" />
</template>

<style scoped>
.home-container {
  width: 100%;
  max-width: 680px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: relative;
}

.welcome-section {
  text-align: center;
  padding: 20px 0 4px;
}

.welcome-title {
  font-size: 1.6rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea, #764ba2, #e74c3c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 6px;
}

.welcome-sub {
  font-size: 0.9rem;
  color: #888;
}

.guest-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 10px;
  padding: 12px 16px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from { transform: translateY(-12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.banner-icon {
  font-size: 1.2rem;
}

.banner-text {
  font-size: 0.85rem;
  color: #ccc;
  flex: 1;
}

.banner-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.banner-btn:hover {
  opacity: 0.9;
}

.banner-close {
  background: none;
  border: none;
  color: #888;
  font-size: 1rem;
  cursor: pointer;
  padding: 4px 8px;
  margin-left: 8px;
  border-radius: 4px;
}

.banner-close:hover {
  background: rgba(255,255,255,0.1);
  color: #eee;
}

.network-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(15, 52, 96, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid #4ecdc4;
  border-radius: 8px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
}
.network-card:hover {
  background: rgba(26, 74, 122, 0.9);
}
.network-label {
  font-size: 0.8rem;
  color: #4ecdc4;
  white-space: nowrap;
}
.network-url {
  flex: 1;
  font-family: monospace;
  font-size: 0.9rem;
  color: #fff;
}
.network-copy {
  font-size: 0.75rem;
  color: #888;
  border: 1px solid #555;
  border-radius: 4px;
  padding: 2px 8px;
}
.network-card:hover .network-copy {
  border-color: #4ecdc4;
  color: #4ecdc4;
}

.card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}
.card:hover {
  transform: translateY(-4px) scale(1.01);
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
}

.game-card:hover {
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
}

.online-card:hover {
  box-shadow: 0 8px 30px rgba(78, 205, 196, 0.15);
}

.ai-card:hover {
  box-shadow: 0 8px 30px rgba(118, 75, 162, 0.2);
}

.chess-card:hover {
  box-shadow: 0 8px 30px rgba(231, 76, 60, 0.2);
}

.chess-online-card:hover {
  box-shadow: 0 8px 30px rgba(142, 68, 173, 0.2);
}

.card h2 {
  font-size: 1.3rem;
  margin-bottom: 6px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #888;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.btn-primary {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-online {
  width: 100%;
  padding: 12px;
  background: rgba(15, 52, 96, 0.85);
  border: 1px solid #667eea;
  color: #667eea;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 10px;
}

.btn-online:hover {
  background: rgba(26, 26, 78, 0.9);
}

.btn-ai {
  width: 100%;
  padding: 12px;
  background: rgba(83, 52, 131, 0.85);
  border: 1px solid #764ba2;
  color: #c9a0f0;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 10px;
}
.btn-ai:hover {
  background: rgba(106, 63, 158, 0.9);
}

.overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.dialog {
  background: rgba(26, 26, 62, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.5);
  max-width: 380px;
  width: 90%;
}
.dialog h3 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  color: #eee;
  text-align: center;
}
.dialog-row {
  margin-bottom: 16px;
}
.dialog-row label {
  display: block;
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 8px;
}
.btn-group {
  display: flex;
  gap: 8px;
}
.btn-group-item {
  flex: 1;
  padding: 8px 6px;
  border: 1px solid #444;
  background: #0f3460;
  color: #aaa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.15s;
}
.btn-group-item.active {
  border-color: #667eea;
  background: #1a1a4e;
  color: #667eea;
}
.btn-group-item:hover:not(.active) {
  border-color: #666;
}
.dialog-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}
.btn-cancel, .btn-start {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
}
.btn-cancel { background: #6c757d; }
.btn-start { background: #28a745; }
.btn-cancel:hover, .btn-start:hover { opacity: 0.9; }

.rules-card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
}

.rules-card h3 {
  margin-bottom: 12px;
  font-size: 1rem;
}

.rules-card ul {
  list-style: none;
}

.rules-card li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: #ccc;
}

.rules-card li::before {
  content: '\2022';
  position: absolute;
  left: 0;
  color: #667eea;
}

.history-card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.history-header h3 {
  font-size: 1rem;
}

.btn-clear {
  background: transparent;
  border: 1px solid #555;
  color: #aaa;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-clear:hover {
  background: #333;
  color: #eee;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 4px;
}

.history-item:hover {
  background: rgba(26, 26, 62, 0.5);
}

.history-item:last-child {
  border-bottom: none;
}

.history-result {
  font-weight: 600;
  color: #ffd700;
  font-size: 0.85rem;
  min-width: 80px;
}

.history-moves {
  color: #aaa;
  font-size: 0.8rem;
  font-family: monospace;
}

.history-time {
  color: #666;
  font-size: 0.75rem;
}

.tab-bar {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.tab-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  background: rgba(22,33,62,0.7);
  color: #888;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 600;
  transition: all 0.2s;
}
.tab-btn.active {
  background: rgba(102,126,234,0.15);
  border-color: #667eea;
  color: #fff;
}
.tab-btn:hover:not(.active) {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.15);
}
.tab-icon { font-size: 1.3rem; }
.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #667eea;
  text-transform: uppercase;
  letter-spacing: 2px;
  padding: 4px 0 0;
  border-bottom: 1px solid rgba(102,126,234,0.15);
}

.chess-card {
  border-color: rgba(231, 76, 60, 0.2);
}
.chess-card:hover {
  border-color: rgba(231, 76, 60, 0.5);
}
.chess-card h2 {
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.btn-chess {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  border: none;
  color: #fff;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}
.btn-chess:hover { opacity: 0.9; }

.chess-online-card {
  border-color: rgba(142, 68, 173, 0.2);
}
.chess-online-card:hover {
  border-color: rgba(142, 68, 173, 0.5);
}
.chess-online-card h2 {
  background: linear-gradient(135deg, #8e44ad, #9b59b6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.btn-chess-online {
  width: 100%;
  padding: 12px;
  background: rgba(142, 68, 173, 0.2);
  border: 1px solid #8e44ad;
  color: #c9a0f0;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 10px;
}
.btn-chess-online:hover {
  opacity: 0.9;
}

.ludo-divider {
  background: linear-gradient(90deg, transparent, #e67e22, transparent) !important;
  color: #e67e22 !important;
  margin-top: 20px !important;
}

.ludo-card {
  background: linear-gradient(135deg, rgba(230,126,34,0.12), rgba(243,156,18,0.08)) !important;
  border-color: rgba(230,126,34,0.3) !important;
}
.ludo-card:hover {
  border-color: rgba(230,126,34,0.6) !important;
  box-shadow: 0 4px 20px rgba(230,126,34,0.15);
}
.ludo-card h2 {
  background: linear-gradient(135deg, #e67e22, #f39c12);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.btn-ludo {
  width: 100%; padding: 10px; border: none; border-radius: 8px;
  background: linear-gradient(135deg, #e67e22, #f39c12);
  color: #fff; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.btn-ludo:hover { opacity: 0.9; }

.footer-links {
  text-align: center;
  padding: 12px 0 4px;
}

.changelog-link {
  background: none;
  border: 1px solid rgba(255,255,255,0.1);
  color: #888;
  padding: 6px 18px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.changelog-link:hover {
  border-color: #667eea;
  color: #667eea;
  background: rgba(102, 126, 234, 0.08);
}

</style>
