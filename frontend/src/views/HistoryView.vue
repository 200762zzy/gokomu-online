<script setup>
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const authStore = useAuthStore()
const API_BASE = '/api'

const games = ref([])
const loading = ref(true)
const page = ref(1)
const total = ref(0)
const limit = 20
const gameType = ref('')

const tabs = [
  { label: '全部', value: '' },
  { label: '五子棋', value: 'gomoku' },
  { label: '象棋', value: 'chinese_chess' },
]

function gameTypeLabel(type) {
  if (type === 'chinese_chess') return '象棋'
  if (type === 'gomoku') return '五子棋'
  return ''
}

async function fetchHistory() {
  loading.value = true
  try {
    let url = `${API_BASE}/games/?page=${page.value}&limit=${limit}`
    if (gameType.value) url += `&game_type=${gameType.value}`
    const resp = await fetch(url, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` },
    })
    if (resp.ok) {
      const data = await resp.json()
      games.value = data.games || []
      total.value = data.total || 0
    }
  } catch { /* ignore */ }
  loading.value = false
}

function resultText(game) {
  if (game.game_type === 'chinese_chess') {
    if (game.winner === null) return '和棋'
    if (game.winner === 'red') return '红胜'
    if (game.winner === 'black') return '黑胜'
  }
  if (game.winner === null) return '和棋'
  if (game.winner === 'black') return '黑胜'
  if (game.winner === 'white') return '白胜'
  return '-'
}

function eloChangeText(change) {
  if (change === 0) return '-'
  return (change > 0 ? '+' : '') + change
}

onMounted(fetchHistory)
watch(gameType, () => { page.value = 1; fetchHistory() })
</script>

<template>
  <div class="history-container">
    <h2 class="page-title">对局记录</h2>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-btn', { active: gameType === tab.value }]"
        @click="gameType = tab.value"
      >{{ tab.label }}</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="games.length === 0" class="empty">暂无对局记录</div>
    <div v-else class="list">
      <div v-for="game in games" :key="game.id" class="game-row">
        <div class="game-info">
          <span class="game-type-label" v-if="game.game_type === 'chinese_chess'">象</span>
          <span class="game-type-label gomoku" v-else>五</span>
          <span class="game-result" :class="game.winner">{{ resultText(game) }}</span>
          <span class="game-reason" v-if="game.reason">{{ game.reason }}</span>
        </div>
        <div class="elo-changes">
          <span class="elo-change black">
            {{ eloChangeText(game.black_elo_change) }}
          </span>
          <span class="elo-change white">
            {{ eloChangeText(game.white_elo_change) }}
          </span>
        </div>
        <span class="game-time">{{ game.ended_at?.slice(0, 10) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-container { max-width: 700px; margin: 0 auto; }
.page-title { font-size: 1.3rem; margin-bottom: 16px; }

.tab-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  background: rgba(22,33,62,0.85);
  border-radius: 10px;
  padding: 4px;
}
.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #888;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.tab-btn.active {
  background: rgba(102,126,234,0.2);
  color: #667eea;
}
.tab-btn:hover:not(.active) {
  color: #aaa;
}

.list { display: flex; flex-direction: column; gap: 6px; }

.game-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.game-info { display: flex; align-items: center; gap: 8px; flex: 1; }

.game-type-label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(231,76,60,0.2);
  color: #e74c3c;
}
.game-type-label.gomoku {
  background: rgba(102,126,234,0.2);
  color: #667eea;
}

.game-result { font-weight: 700; font-size: 0.95rem; }
.game-result.black { color: #ddd; }
.game-result.white { color: #aaa; }
.game-result.red { color: #e74c3c; }
.game-reason { font-size: 0.8rem; color: #888; }

.elo-changes { display: flex; gap: 8px; }
.elo-change { font-family: monospace; font-size: 0.85rem; font-weight: 600; }
.elo-change.black { color: #ccc; }
.elo-change.white { color: #999; }

.game-time { color: #666; font-size: 0.8rem; min-width: 80px; text-align: right; }

.loading, .empty { text-align: center; padding: 40px; color: #888; }

@media (max-width: 768px) {
  .history-container { max-width: 100%; }
  .game-row { padding: 12px; min-height: 48px; }
  .page-title { font-size: 1.1rem; }
}
</style>
