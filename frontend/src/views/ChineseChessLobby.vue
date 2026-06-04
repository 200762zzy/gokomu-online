<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useCcGameStore } from '../stores/ccGame.js'
import { getCcWsClient } from '../services/ccWsClient.js'
import TitleBadge from '../components/TitleBadge.vue'
import { getTitleInfo } from '../utils/titles.js'

const router = useRouter()
const authStore = useAuthStore()
const gameStore = useCcGameStore()
const wsClient = getCcWsClient()

const playerName = ref(authStore.nickname || authStore.username)
const roomIdInput = ref('')
const passwordInput = ref('')
const createPassword = ref('')
const errorMsg = ref('')
const waiting = ref(false)
const openRooms = ref([])
let pollTimer = null
let unsubFns = []

function showError(msg) {
  errorMsg.value = msg
  setTimeout(() => errorMsg.value = '', 3000)
}

async function createRoom() {
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
    await new Promise(resolve => {
      const unsub = wsClient.on('open', () => { unsub(); resolve() })
      setTimeout(resolve, 5000)
    })
  }
  wsClient.send({
    type: 'create_room',
    player_name: playerName.value,
    password: createPassword.value,
  })
}

async function joinRoom() {
  if (!roomIdInput.value) return
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
    await new Promise(resolve => {
      const unsub = wsClient.on('open', () => { unsub(); resolve() })
      setTimeout(resolve, 5000)
    })
  }
  doJoinRoom(roomIdInput.value, passwordInput.value)
}

async function joinRoomById(roomId, password) {
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
    await new Promise(resolve => {
      const unsub = wsClient.on('open', () => { unsub(); resolve() })
      setTimeout(resolve, 5000)
    })
  }
  doJoinRoom(roomId, password || '')
}

function doJoinRoom(roomId, password) {
  wsClient.send({
    type: 'join_room',
    room_id: roomId,
    player_name: playerName.value,
    password: password || '',
  })
}

function handleMessage(msg) {
  switch (msg.type) {
    case 'room_created':
      gameStore.currentRoomId = msg.room_id
      gameStore.playerColor = msg.player_color
      router.push(`/chess/game/${msg.room_id}`)
      break
    case 'room_joined':
      gameStore.currentRoomId = msg.room_id
      gameStore.playerColor = msg.player_color
      gameStore.opponentName = msg.opponent_name
      gameStore.opponentTitle = msg.opponent_title || null
      gameStore.pendingGameState = {
        board: msg.board,
        currentTurn: msg.current_turn,
        myTurn: msg.your_turn,
        moveHistory: msg.move_history || [],
      }
      router.push(`/chess/game/${msg.room_id}`)
      break
    case 'error':
      showError(msg.message)
      break
  }
}

async function fetchRooms() {
  try {
    const res = await fetch('/api/cc/rooms')
    if (res.ok) openRooms.value = await res.json()
  } catch { /* ignore */ }
}

onMounted(() => {
  if (authStore.isAuthenticated && !wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
  }
  unsubFns = [
    wsClient.on('room_created', handleMessage),
    wsClient.on('room_joined', handleMessage),
    wsClient.on('error', handleMessage),
  ]
  fetchRooms()
  pollTimer = setInterval(fetchRooms, 3000)
})

onUnmounted(() => {
  unsubFns.forEach(fn => fn())
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="cc-lobby">
    <h2 class="lobby-title">中国象棋 · 在线对战</h2>

    <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>

    <div class="lobby-grid">
      <div class="lobby-card">
        <h3>创建房间</h3>
        <input v-model="playerName" placeholder="昵称" class="lobby-input" />
        <input v-model="createPassword" type="password" placeholder="房间密码（可选）" class="lobby-input" />
        <button class="btn-primary" @click="createRoom">创建房间</button>
      </div>

      <div class="lobby-card">
        <h3>加入房间</h3>
        <input v-model="roomIdInput" placeholder="房间号（4位数字）" class="lobby-input" maxlength="4" />
        <input v-model="passwordInput" type="password" placeholder="密码（有密码时）" class="lobby-input" />
        <button class="btn-primary" @click="joinRoom">加入房间</button>
      </div>
    </div>

    <div class="room-list">
      <h3>等待中的房间</h3>
      <div v-if="openRooms.length === 0" class="empty-hint">暂无开放房间</div>
      <div v-for="room in openRooms" :key="room.room_id" class="room-item" @click="room.has_password ? (roomIdInput = room.room_id, passwordInput = '') : joinRoomById(room.room_id)">
        <span class="room-id">{{ room.room_id }}</span>
        <span class="room-host">{{ room.red_name }}{{ room.has_password ? ' 🔒' : '' }}</span>
        <TitleBadge v-if="room.red_title" :title="room.red_title" size="sm" />
        <span class="room-status">点击加入</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cc-lobby {
  max-width: 600px;
  margin: 0 auto;
}
.lobby-title {
  text-align: center;
  margin-bottom: 20px;
  font-size: 1.3rem;
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.error-toast {
  position: fixed;
  top: 20px; left: 50%;
  transform: translateX(-50%);
  background: #dc3545; color: #fff;
  padding: 10px 24px; border-radius: 8px;
  z-index: 200;
}
.lobby-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
@media (max-width: 600px) {
  .lobby-grid { grid-template-columns: 1fr; }
}
.lobby-card {
  background: rgba(22,33,62,0.85);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.lobby-card h3 {
  font-size: 1rem;
  margin-bottom: 4px;
}
.lobby-input {
  width: 100%;
  padding: 10px 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 6px;
  font-size: 0.9rem;
  outline: none;
}
.lobby-input:focus {
  border-color: #667eea;
}
.btn-primary {
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover { opacity: 0.9; }
.room-list {
  background: rgba(22,33,62,0.85);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px;
  padding: 16px;
}
.room-list h3 {
  font-size: 1rem;
  margin-bottom: 12px;
}
.empty-hint {
  text-align: center;
  color: #666;
  padding: 20px;
}
.room-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.room-item:hover { background: rgba(255,255,255,0.05); }
.room-id {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffd700;
  min-width: 50px;
}
.room-host { flex: 1; color: #ccc; font-size: 0.9rem; }
.room-status { color: #888; font-size: 0.8rem; }
</style>
