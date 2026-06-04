<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GameBoard from '../components/GameBoard.vue'
import GameInfo from '../components/GameInfo.vue'
import WinRatePanel from '../components/WinRatePanel.vue'
import { createBoard, BLACK, WHITE, getStoneName } from '../services/gameLogic.js'
import { getWsClient } from '../services/wsClient.js'
import { useAuthStore } from '../stores/auth.js'
import { useIsMobile } from '../composables/useIsMobile.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const wsClient = getWsClient()
const roomId = route.params.roomId
const { isMobile } = useIsMobile()
const mobileBoardWidth = computed(() => Math.min(window.innerWidth - 16, 560))

const board = ref(createBoard())
const currentTurn = ref('black')
const gameOver = ref(false)
const winner = ref('')
const gameResult = ref('')
const blackName = ref('')
const whiteName = ref('')
const moveHistory = ref([])
const blackMoveCount = ref(0)
const whiteMoveCount = ref(0)
const analysis = ref(null)
const analyzing = ref(false)
const error = ref('')
const connected = ref(false)

onMounted(() => {
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.username || '观战者', authStore.accessToken)
  }

  const unsubs = []

  function doSpectate() {
    wsClient.send({ type: 'spectate_room', room_id: roomId })
    connected.value = true
  }

  if (wsClient.isAuthenticated()) {
    doSpectate()
  } else {
    unsubs.push(wsClient.on('auth_ok', doSpectate))
  }

  unsubs.push(wsClient.on('spectate_joined', (msg) => {
    board.value = _parseBoard(msg.board)
    currentTurn.value = msg.current_turn
    blackName.value = msg.black_name
    whiteName.value = msg.white_name
    moveHistory.value = msg.move_history.map(m => ({ ...m }))
    blackMoveCount.value = msg.move_history.filter(m => m.player === BLACK).length
    whiteMoveCount.value = msg.move_history.filter(m => m.player === WHITE).length
  }))

  unsubs.push(wsClient.on('stone_placed', (msg) => {
    const r = msg.row, c = msg.col
    const p = msg.player === 'black' ? BLACK : WHITE
    board.value = board.value.map((row, ri) =>
      row.map((cell, ci) => (ri === r && ci === c ? p : cell))
    )
    currentTurn.value = msg.current_turn
    if (msg.player === 'black') blackMoveCount.value++
    else whiteMoveCount.value++
    moveHistory.value.push({ row: r, col: c, player: p })
  }))

  unsubs.push(wsClient.on('game_over', (msg) => {
    gameOver.value = true
    winner.value = msg.winner || ''
    gameResult.value = msg.reason || ''
  }))

  unsubs.push(wsClient.on('analysis_result', (msg) => {
    if (msg.analysis) {
      analysis.value = msg.analysis
      analyzing.value = false
    }
  }))

  unsubs.push(wsClient.on('error', (msg) => {
    error.value = msg.message
  }))

  unsubs.push(wsClient.on('close', () => {
    error.value = '连接已断开'
  }))
})

function _parseBoard(apiBoard) {
  return apiBoard.map(row =>
    row.map(cell => {
      if (cell === 'black') return BLACK
      if (cell === 'white') return WHITE
      return 0
    })
  )
}

function goBack() {
  router.push('/lobby')
}
</script>

<template>
  <div v-if="error" class="error-toast">{{ error }}</div>

  <!-- DESKTOP -->
  <template v-if="!isMobile">
    <div class="spectate-header">
      <span class="spectate-badge">👁 观战模式</span>
      <span class="room-badge">#{{ roomId }}</span>
      <span class="player-names">{{ blackName }} vs {{ whiteName }}</span>
      <button class="btn-back" @click="goBack">返回大厅</button>
    </div>
    <div class="game-layout">
      <div class="left-column">
        <GameBoard
          :board="board"
          :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
          :game-over="gameOver"
          :readonly="true"
        />
      </div>
      <div class="right-column">
        <GameInfo
          :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
          :game-over="gameOver"
          :winner="winner"
          :game-result="gameResult"
          :black-move-count="blackMoveCount"
          :white-move-count="whiteMoveCount"
        />
        <WinRatePanel :analysis="analysis" :loading="analyzing" />
      </div>
    </div>
  </template>

  <!-- MOBILE -->
  <template v-else>
    <div class="mobile-spectate-layout">
      <div class="mobile-spectate-header">
        <span class="spectate-badge">👁 观战</span>
        <span class="room-badge-sm">#{{ roomId }}</span>
        <span class="player-names-sm">{{ blackName }} vs {{ whiteName }}</span>
        <button class="btn-back-sm" @click="goBack">返回</button>
      </div>
      <div class="mobile-spectate-board">
        <GameBoard
          :board="board"
          :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
          :game-over="gameOver"
          :readonly="true"
          :parent-width="mobileBoardWidth"
        />
      </div>
      <div class="mobile-spectate-info">
        <GameInfo
          :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
          :game-over="gameOver"
          :winner="winner"
          :game-result="gameResult"
          :black-move-count="blackMoveCount"
          :white-move-count="whiteMoveCount"
        />
        <WinRatePanel :analysis="analysis" :loading="analyzing" />
      </div>
    </div>
  </template>
</template>

<style scoped>
.spectate-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.spectate-badge {
  background: #e6a817;
  color: #111;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 700;
}

.room-badge {
  font-family: monospace;
  color: #667eea;
  font-weight: 700;
}

.player-names {
  flex: 1;
  color: #ccc;
  font-size: 0.9rem;
}

.btn-back {
  background: #333;
  color: #eee;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}

.game-layout {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: start;
}

.left-column { display: flex; flex-direction: column; align-items: center; }
.right-column { display: flex; flex-direction: column; gap: 14px; min-width: 220px; }

.error-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #dc3545;
  color: #fff;
  padding: 10px 24px;
  border-radius: 8px;
  z-index: 200;
  box-shadow: 0 4px 16px rgba(220,53,69,0.4);
}

/* Mobile styles */
.mobile-spectate-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}

.mobile-spectate-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
}

.room-badge-sm {
  font-family: monospace;
  color: #667eea;
  font-weight: 700;
  font-size: 0.85rem;
}

.player-names-sm {
  flex: 1;
  color: #ccc;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-back-sm {
  background: #333;
  color: #eee;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  min-height: 36px;
}

.mobile-spectate-board {
  display: flex;
  justify-content: center;
  width: 100%;
}

.mobile-spectate-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

</style>
