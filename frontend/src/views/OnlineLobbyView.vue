<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getWsClient } from '../services/wsClient.js'

const emit = defineEmits(['enterGame'])

const playerName = ref('')
const roomIdInput = ref('')
const openRooms = ref([])
const loading = ref(false)
const error = ref('')
const pollingTimer = ref(null)

const wsClient = getWsClient()
const unsubFns = []

function fetchRooms() {
  fetch('/api/rooms')
    .then(r => r.ok ? r.json() : [])
    .then(data => { openRooms.value = data })
    .catch(() => {})
}

function createRoom() {
  if (!playerName.value.trim()) {
    error.value = '请输入玩家昵称'
    return
  }
  loading.value = true
  error.value = ''

  wsClient.disconnect()

  unsubFns.push(wsClient.on('open', () => {
    wsClient.send({
      type: 'create_room',
      player_name: playerName.value.trim(),
    })
  }))

  unsubFns.push(wsClient.on('room_created', (msg) => {
    emit('enterGame', {
      roomId: msg.room_id,
      playerColor: msg.player_color,
      playerName: playerName.value.trim(),
    })
  }))

  unsubFns.push(wsClient.on('error', (msg) => {
    error.value = msg.message || '创建房间失败'
    loading.value = false
  }))

  wsClient.connect(playerName.value.trim())
}

function joinRoom(roomId) {
  if (!playerName.value.trim()) {
    error.value = '请输入玩家昵称'
    return
  }
  const rid = roomId || roomIdInput.value.trim()
  if (!rid) {
    error.value = '请输入房间号'
    return
  }
  loading.value = true
  error.value = ''

  wsClient.disconnect()

  unsubFns.push(wsClient.on('open', () => {
    wsClient.send({
      type: 'join_room',
      room_id: rid,
      player_name: playerName.value.trim(),
    })
  }))

  unsubFns.push(wsClient.on('room_joined', (msg) => {
    emit('enterGame', {
      roomId: msg.room_id,
      playerColor: msg.player_color,
      playerName: playerName.value.trim(),
      opponentName: msg.opponent_name,
    })
  }))

  unsubFns.push(wsClient.on('error', (msg) => {
    error.value = msg.message || '加入房间失败'
    loading.value = false
  }))

  wsClient.connect(playerName.value.trim())
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
        <input
          v-model="playerName"
          type="text"
          placeholder="输入你的昵称"
          maxlength="12"
          class="input"
        />
      </div>
      <button
        class="btn-primary"
        :disabled="loading"
        @click="createRoom"
      >
        {{ loading ? '创建中...' : '创建房间' }}
      </button>
    </div>

    <div class="card">
      <h3>加入房间</h3>
      <div class="form-group">
        <label>房间号</label>
        <input
          v-model="roomIdInput"
          type="text"
          placeholder="输入4位房间号"
          maxlength="4"
          class="input"
        />
      </div>
      <button
        class="btn-secondary"
        :disabled="loading"
        @click="joinRoom('')"
      >
        {{ loading ? '加入中...' : '加入房间' }}
      </button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div class="card rooms-card">
      <h3>等待中的房间</h3>
      <div v-if="openRooms.length === 0" class="no-rooms">
        暂无等待中的房间
      </div>
      <div
        v-for="room in openRooms"
        :key="room.room_id"
        class="room-item"
        @click="joinRoom(room.room_id)"
      >
        <span class="room-id">#{{ room.room_id }}</span>
        <span class="room-host">{{ room.black_name }} 等待中...</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lobby-container {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.card {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
}

.card h2 {
  font-size: 1.3rem;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.card h3 {
  font-size: 1rem;
  margin-bottom: 14px;
  color: #ddd;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 4px;
}

.input {
  width: 100%;
  padding: 10px 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
}

.input:focus {
  border-color: #667eea;
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

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-secondary {
  width: 100%;
  padding: 12px;
  background: #0f3460;
  border: 1px solid #333;
  color: #eee;
  font-size: 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary:hover:not(:disabled) {
  background: #1a1a4e;
}

.error-msg {
  grid-column: 1 / -1;
  background: #dc3545;
  color: #fff;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  text-align: center;
}

.no-rooms {
  text-align: center;
  color: #666;
  padding: 20px 0;
  font-size: 0.85rem;
}

.rooms-card {
  grid-column: 1 / -1;
}

.room-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
}

.room-item:hover {
  background: #1a1a3e;
}

.room-item:last-child {
  border-bottom: none;
}

.room-id {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 700;
  color: #667eea;
  min-width: 50px;
}

.room-host {
  color: #aaa;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .lobby-container {
    grid-template-columns: 1fr;
  }
  .rooms-card {
    grid-column: 1;
  }
}
</style>
