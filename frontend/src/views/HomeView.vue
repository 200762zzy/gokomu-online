<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { audioManager } from '../services/audioManager.js'

const router = useRouter()
const authStore = useAuthStore()

const savedGames = ref([])
const showAiDialog = ref(false)
const aiDifficulty = ref('easy')
const aiColor = ref('black')

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
      <h3>游戏规则</h3>
      <ul>
        <li>15×15 标准棋盘，黑棋先手</li>
        <li>两名玩家轮流在同一台电脑落子</li>
        <li>五子连珠（横/竖/斜）获胜</li>
        <li>支持悔棋、认输、和棋</li>
        <li>对局结束后可回放复盘</li>
        <li>每步落子后自动请求AI分析</li>
      </ul>
    </div>

    <div class="tutorial-card">
      <h3>联机教程</h3>
      <ol>
        <li>启动服务者双击 <code>GomokuOnline.exe</code> 或 <code>start.bat</code></li>
        <li>将上方显示的 <b>局域网地址</b> 发给同一局域网的朋友</li>
        <li>朋友在浏览器中打开该地址</li>
        <li>双方都点击「在线对战」→ 一人创建房间，一人输入房间号加入</li>
      </ol>
    </div>

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
  </div>
</template>

<style scoped>
.home-container {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .home-container {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

.network-card {
  grid-column: 1 / -1;
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
  transform: translateY(-2px);
  border-color: rgba(102, 126, 234, 0.3);
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
  grid-column: 1 / -1;
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

.tutorial-card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
}

.tutorial-card h3 {
  font-size: 1rem;
  margin-bottom: 12px;
  color: #4ecdc4;
}

.tutorial-card ol {
  list-style: decimal;
  padding-left: 20px;
}

.tutorial-card li {
  margin-bottom: 8px;
  font-size: 0.85rem;
  color: #ccc;
  line-height: 1.5;
}

.tutorial-card code {
  background: #0f3460;
  padding: 2px 6px;
  border-radius: 4px;
  color: #667eea;
  font-family: monospace;
}

</style>
