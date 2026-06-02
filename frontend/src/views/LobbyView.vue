<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useGameStore } from '../stores/game.js'
import { getWsClient } from '../services/wsClient.js'
import TitleBadge from '../components/TitleBadge.vue'

const router = useRouter()
const authStore = useAuthStore()
const gameStore = useGameStore()

const playerName = ref(authStore.nickname || authStore.username)
const roomIdInput = ref('')
const passwordInput = ref('')
const passwordRoomId = ref('')
const showPasswordModal = ref(false)
const openRooms = ref([])
const activeRooms = ref([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const tab = ref('open')
const pollingTimer = ref(null)
const wsClient = getWsClient()
const unsubFns = []

const filterRooms = (rooms) => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return rooms
  return rooms.filter(r =>
    r.room_id?.toLowerCase().includes(q) ||
    (r.black_name || '').toLowerCase().includes(q) ||
    (r.white_name || '').toLowerCase().includes(q)
  )
}

const filteredOpenRooms = computed(() => filterRooms(openRooms.value))
const filteredActiveRooms = computed(() => filterRooms(activeRooms.value))

function fetchRooms() {
  fetch('/api/rooms')
    .then(r => r.ok ? r.json() : [])
    .then(data => { openRooms.value = data })
    .catch(() => {})
  fetch('/api/rooms/active')
    .then(r => r.ok ? r.json() : [])
    .then(data => { activeRooms.value = data })
    .catch(() => {})
}

function _lastMoveFromHistory(history) {
  if (!history || history.length === 0) return null
  const m = history[history.length - 1]
  return { row: m.row, col: m.col }
}

function navigateToGame(roomId, playerColor, opponentName, opponentTitle, gameState) {
  gameStore.currentRoomId = roomId
  gameStore.playerColor = playerColor
  gameStore.opponentName = opponentName || '等待中...'
  gameStore.opponentTitle = opponentTitle || null
  if (gameState) {
    gameStore.pendingGameState = {
      board: gameState.board,
      currentTurn: gameState.current_turn,
      myTurn: gameState.your_turn,
      moveHistory: gameState.move_history,
    }
  }
  router.push(`/game/${roomId}`)
}

function connectAndSend(action) {
  if (!playerName.value.trim()) {
    error.value = '请输入玩家昵称'
    return
  }
  loading.value = true
  error.value = ''

  wsClient.disconnect()
  wsClient.clearListeners()

  unsubFns.push(wsClient.on('open', () => {
    wsClient.send(action)
  }))

  unsubFns.push(wsClient.on('room_created', (msg) => {
    navigateToGame(msg.room_id, msg.player_color)
  }))

  unsubFns.push(wsClient.on('room_joined', (msg) => {
    navigateToGame(msg.room_id, msg.player_color, msg.opponent_name, msg.opponent_title, msg)
  }))

  unsubFns.push(wsClient.on('match_found', (msg) => {
    loading.value = false
    navigateToGame(msg.room_id, msg.your_color, msg.opponent?.name, msg.opponent?.title, msg)
  }))

  unsubFns.push(wsClient.on('match_queued', () => {}))

  unsubFns.push(wsClient.on('cancel_match', () => {
    loading.value = false
  }))

  unsubFns.push(wsClient.on('error', (msg) => {
    error.value = msg.message || '操作失败'
    loading.value = false
  }))

  wsClient.connect(playerName.value.trim(), authStore.accessToken || undefined)
}

function promptPassword(room) {
  if (room.has_password) {
    passwordRoomId.value = room.room_id
    passwordInput.value = ''
    showPasswordModal.value = true
  } else {
    doJoinRoom(room.room_id)
  }
}

function doJoinRoom(roomId, password) {
  connectAndSend({
    type: 'join_room',
    room_id: roomId,
    player_name: playerName.value.trim(),
    password: password || '',
  })
}

function submitPasswordJoin() {
  showPasswordModal.value = false
  doJoinRoom(passwordRoomId.value, passwordInput.value)
}

function createRoom() {
  connectAndSend({ type: 'create_room', player_name: playerName.value.trim() })
}

function joinRoom(roomId) {
  const rid = roomId || roomIdInput.value.trim()
  if (!rid) { error.value = '请输入房间号'; return }
  const room = openRooms.value.find(r => r.room_id === rid)
  if (room?.has_password) {
    passwordRoomId.value = rid
    passwordInput.value = ''
    showPasswordModal.value = true
  } else {
    doJoinRoom(rid)
  }
}

function spectateRoom(roomId) {
  router.push(`/spectate/${roomId}`)
}

function startMatch() {
  connectAndSend({ type: 'start_match' })
}

function cancelMatch() {
  wsClient.send({ type: 'cancel_match' })
  loading.value = false
}

function goToAiGame() {
  const params = new URLSearchParams({ difficulty: 'easy', playerColor: 'black' })
  router.push(`/ai-game?${params}`)
}

onMounted(() => {
  fetchRooms()
  pollingTimer.value = setInterval(fetchRooms, 3000)
})

onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
  unsubFns.forEach(fn => fn())
  unsubFns.length = 0
})
</script>

<template>
  <div class="lobby-container">
    <div class="card">
      <h2>在线对战</h2>
      <div class="form-group">
        <label>玩家昵称</label>
        <input v-model="playerName" type="text" placeholder="输入你的昵称" maxlength="12" class="input" />
      </div>
      <button class="btn-primary" :disabled="loading" @click="createRoom">
        {{ loading ? '创建中...' : '创建房间' }}
      </button>
    </div>

    <div class="card">
      <h3>加入房间</h3>
      <div class="form-group">
        <label>房间号</label>
        <input v-model="roomIdInput" type="text" placeholder="输入4位房间号" maxlength="4" class="input" />
      </div>
      <button class="btn-secondary" :disabled="loading" @click="joinRoom('')">
        {{ loading ? '加入中...' : '加入房间' }}
      </button>
    </div>

    <div class="card match-card">
      <h3>快速匹配</h3>
      <p class="match-desc">系统自动匹配实力相近的对手</p>
      <button v-if="!loading" class="btn-match" @click="startMatch">开始匹配</button>
      <button v-else class="btn-match cancel" @click="cancelMatch">取消匹配</button>
    </div>

    <div class="card rooms-card">
      <div class="search-bar">
        <input v-model="searchQuery" type="text" placeholder="搜索房间号或玩家名..." class="input" />
      </div>
      <div class="sub-tabs">
        <button :class="['sub-tab', { active: tab === 'open' }]" @click="tab = 'open'">
          等待中 ({{ openRooms.length }})
        </button>
        <button :class="['sub-tab', { active: tab === 'active' }]" @click="tab = 'active'">
          对局中 ({{ activeRooms.length }})
        </button>
      </div>

      <div v-if="tab === 'open'">
        <div v-if="filteredOpenRooms.length === 0" class="no-rooms">
          {{ searchQuery ? '无匹配结果' : '暂无等待中的房间' }}
        </div>
        <div v-for="room in filteredOpenRooms" :key="room.room_id" class="room-item" @click="promptPassword(room)">
          <span class="room-id">#{{ room.room_id }}</span>
          <span class="room-host">{{ room.black_name }}</span>
          <TitleBadge v-if="room.black_title" :title="room.black_title" size="sm" />
          <span class="room-host-status">等待中...</span>
          <span v-if="room.has_password" class="spec-count">🔒 加密</span>
          <span v-if="room.spectator_count > 0" class="spec-count">{{ room.spectator_count }} 观战</span>
        </div>
      </div>

      <div v-if="tab === 'active'">
        <div v-if="filteredActiveRooms.length === 0" class="no-rooms">
          {{ searchQuery ? '无匹配结果' : '暂无进行中的对局' }}
        </div>
        <div v-for="room in filteredActiveRooms" :key="room.room_id" class="room-item">
          <span class="room-id">#{{ room.room_id }}</span>
          <span class="room-host">{{ room.black_name }}</span>
          <TitleBadge v-if="room.black_title" :title="room.black_title" size="sm" />
          <span class="room-vs">vs</span>
          <span class="room-host">{{ room.white_name }}</span>
          <TitleBadge v-if="room.white_title" :title="room.white_title" size="sm" />
          <button class="btn-spectate" @click.stop="spectateRoom(room.room_id)">观战</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
      <div class="modal-card">
        <h3>房间需密码</h3>
        <p>房间 #{{ passwordRoomId }} 需要密码才能加入</p>
        <input v-model="passwordInput" type="password" placeholder="输入房间密码" class="input" @keyup.enter="submitPasswordJoin" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showPasswordModal = false">取消</button>
          <button class="btn-primary" @click="submitPasswordJoin">加入</button>
        </div>
      </div>
    </div>
  </div>


  <!-- Password modal (shared) -->
  <div v-if="showPasswordModal" class="modal-overlay" @click.self="showPasswordModal = false">
    <div class="modal-card">
      <h3>房间需密码</h3>
      <p>房间 #{{ passwordRoomId }} 需要密码才能加入</p>
      <input v-model="passwordInput" type="password" placeholder="输入房间密码" class="input" @keyup.enter="submitPasswordJoin" />
      <div class="modal-actions">
        <button class="btn-secondary" @click="showPasswordModal = false">取消</button>
        <button class="btn-primary" @click="submitPasswordJoin">加入</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lobby-container { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

@media (max-width: 768px) {
  .lobby-container { grid-template-columns: 1fr; gap: 12px; }
}

.card {
  background: rgba(22, 33, 62, 0.85); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 20px;
}

.card h2 { font-size: 1.3rem; margin-bottom: 16px; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.card h3 { font-size: 1rem; margin-bottom: 14px; color: #ddd; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 0.85rem; color: #888; margin-bottom: 4px; }

.input {
  width: 100%; padding: 10px 12px; background: #0f3460; border: 1px solid #333;
  color: #eee; border-radius: 6px; font-size: 1rem; outline: none; box-sizing: border-box;
}
.input:focus { border-color: #667eea; }

.btn-primary {
  width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea, #764ba2);
  border: none; color: #fff; font-size: 1rem; border-radius: 8px; cursor: pointer; font-weight: 600;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { opacity: 0.9; }

.btn-secondary {
  width: 100%; padding: 12px; background: #0f3460; border: 1px solid #333;
  color: #eee; font-size: 1rem; border-radius: 8px; cursor: pointer; font-weight: 600;
}
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary:hover:not(:disabled) { background: #1a1a4e; }

.match-card { text-align: center; }
.match-desc { font-size: 0.85rem; color: #888; margin-bottom: 16px; }

.btn-match {
  width: 100%; padding: 14px; background: linear-gradient(135deg, #4ecdc4, #44a08d);
  border: none; color: #fff; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 700; transition: opacity 0.2s;
}
.btn-match:hover:not(:disabled) { opacity: 0.9; }
.btn-match.cancel { background: #dc3545; }

.error-msg {
  grid-column: 1 / -1; background: #dc3545; color: #fff;
  padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; text-align: center;
}

.no-rooms { text-align: center; color: #666; padding: 20px 0; font-size: 0.85rem; }

@media (max-width: 768px) {
  .room-item { min-height: 48px; padding: 14px 12px; }
  .input { font-size: 16px; }
  .btn-primary, .btn-secondary, .btn-match { min-height: 48px; }
}

.rooms-card { grid-column: 1 / -1; }

.search-bar { margin-bottom: 12px; }

.sub-tabs { display: flex; gap: 4px; margin-bottom: 12px; }
.sub-tab {
  flex: 1; padding: 8px; border: none; background: #0f3460; color: #888;
  border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: all 0.15s;
}
.sub-tab.active { background: #667eea; color: #fff; }

.room-item {
  display: flex; align-items: center; gap: 12px; padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06); cursor: pointer; border-radius: 6px; transition: background 0.2s;
}
.room-item:hover { background: #1a1a3e; }
.room-item:last-child { border-bottom: none; }

.room-id { font-family: monospace; font-size: 1.1rem; font-weight: 700; color: #667eea; min-width: 50px; }
.room-host { color: #aaa; font-size: 0.9rem; }
.room-host-status { color: #888; font-size: 0.8rem; flex: 1; }
.spec-count { color: #888; font-size: 0.8rem; }

.btn-spectate {
  padding: 4px 12px; background: #4ecdc4; border: none; color: #fff;
  border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600;
}
.btn-spectate:hover { opacity: 0.85; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal-card {
  background: #16213e; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px; padding: 24px; width: 320px;
}
.modal-card h3 { margin-bottom: 8px; }
.modal-card p { font-size: 0.85rem; color: #888; margin-bottom: 16px; }
.modal-card .input { margin-bottom: 16px; }
.modal-actions { display: flex; gap: 8px; }
.modal-actions .btn-secondary { flex: 1; }
.modal-actions .btn-primary { flex: 1; }

</style>
