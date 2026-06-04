<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LudoBoard from '../components/LudoBoard.vue'
import Dice3D from '../components/Dice3D.vue'
import { getLudoWsClient } from '../services/ludoWsClient.js'
import { useAuthStore } from '../stores/auth.js'
import { useLudoGameStore } from '../stores/ludoGame.js'
import { PLAYER_COLORS, getColorHex, getColorNameCN } from '../services/ludoLogic.js'
import { useIsMobile } from '../composables/useIsMobile.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const gameStore = useLudoGameStore()
const wsClient = getLudoWsClient()
const { isMobile } = useIsMobile()
const mobileBoardWidth = computed(() => Math.min(window.innerWidth - 16, 560))

const roomId = route.params.roomId || gameStore.currentRoomId
const playerColor = ref(gameStore.playerColor || '')
const playerIndex = ref(gameStore.playerIndex >= 0 ? gameStore.playerIndex : -1)
const players = ref(gameStore.players || [])
const boardState = ref(gameStore.boardState)
const currentTurn = ref(gameStore.currentTurn)
const myTurn = ref(false)
const gameOver = ref(false)
const winner = ref('')
const diceValue = ref(null)
const playablePieces = ref([])
const rolling = ref(false)
const timerRemaining = ref(60)
const errorMsg = ref('')

const currentColorName = computed(() => {
  if (currentTurn.value === undefined || currentTurn.value === null) return '-'
  return getColorNameCN(PLAYER_COLORS[currentTurn.value])
})

const currentColorHex = computed(() => {
  if (currentTurn.value === undefined || currentTurn.value === null) return '#888'
  return getColorHex(PLAYER_COLORS[currentTurn.value])
})

const myColorLabel = computed(() => getColorNameCN(playerColor.value))

let unsubFns = []
let timerInterval = null

function handleRoll() {
  if (!myTurn.value || gameOver.value || rolling.value) return
  rolling.value = true
  wsClient.send({ type: 'roll_dice' })
}

function handlePieceClick(pieceIndex) {
  if (!myTurn.value || gameOver.value) return
  if (!playablePieces.value.includes(pieceIndex)) return
  wsClient.send({ type: 'move_piece', piece_index: pieceIndex })
}

function handleLeave() {
  wsClient.send({ type: 'leave_room' })
  gameStore.reset()
  router.push('/ludo/lobby')
}

function unsubAll() {
  unsubFns.forEach(fn => fn())
  unsubFns = []
}

onMounted(() => {
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
  }

  if (gameStore.currentRoomId) {
    roomId = gameStore.currentRoomId
    playerColor.value = gameStore.playerColor
    playerIndex.value = gameStore.playerIndex
    players.value = gameStore.players
  }

  unsubFns = [
    wsClient.on('room_created', (msg) => {
      gameStore.playerColor = playerColor.value = msg.player_color
      gameStore.playerIndex = playerIndex.value = msg.player_index
      gameStore.currentRoomId = roomId
      players.value = [{ name: authStore.nickname || authStore.username, color: msg.player_color, online: true }]
      gameStore.players = players.value
    }),

    wsClient.on('room_joined', (msg) => {
      gameStore.playerColor = playerColor.value = msg.player_color
      gameStore.playerIndex = playerIndex.value = msg.player_index
      gameStore.currentRoomId = roomId
      players.value = msg.players || []
      gameStore.players = players.value
    }),

    wsClient.on('player_joined', (msg) => {
      players.value = msg.players || []
      gameStore.players = players.value
      errorMsg.value = `${msg.player_name} 加入了房间`
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('game_start', (msg) => {
      players.value = msg.players || []
      gameStore.players = players.value
      errorMsg.value = '游戏开始！'
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('your_turn', (msg) => {
      currentTurn.value = msg.player_index !== undefined ? msg.player_index : PLAYER_COLORS.indexOf(msg.player)
      myTurn.value = currentTurn.value === playerIndex.value
      playablePieces.value = []
      diceValue.value = null
      rolling.value = false
      timerRemaining.value = 60
    }),

    wsClient.on('dice_rolled', (msg) => {
      diceValue.value = msg.value
      rolling.value = false
      const turnIdx = PLAYER_COLORS.indexOf(msg.player)
      currentTurn.value = turnIdx
    }),

    wsClient.on('your_move', (msg) => {
      playablePieces.value = msg.playable_pieces || []
      diceValue.value = msg.dice_value
    }),

    wsClient.on('piece_moved', (msg) => {
      if (boardState.value) {
        const pIdx = PLAYER_COLORS.indexOf(msg.player)
        if (boardState.value.pieces[pIdx]) {
          const piece = boardState.value.pieces[pIdx][msg.piece_index]
          if (piece) {
            piece.state = msg.state || piece.state
            piece.pos = msg.new_pos
            if (msg.entered) {
              piece.state = 'active'
              piece.steps = 0
            }
            if (msg.finished) piece.state = 'finished'
          }
        }
      }
      playablePieces.value = []
    }),

    wsClient.on('piece_captured', (msg) => {
      const pIdx = PLAYER_COLORS.indexOf(msg.target_player)
      if (boardState.value && boardState.value.pieces[pIdx]) {
        const piece = boardState.value.pieces[pIdx][msg.target_piece]
        if (piece) {
          piece.state = 'home'
          piece.pos = -1
          piece.steps = 0
        }
      }
      errorMsg.value = `${getColorNameCN(msg.target_player)} 的棋子被 ${getColorNameCN(msg.by_player)} 吃掉了！`
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('extra_turn', () => {
      myTurn.value = true
      errorMsg.value = '掷出 6，获得额外回合！'
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('three_sixes_penalty', (msg) => {
      errorMsg.value = `${getColorNameCN(msg.player)} 连续三次掷出 6，所有棋子返回起点！`
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('timer', (msg) => {
      timerRemaining.value = msg.remaining
    }),

    wsClient.on('game_over', (msg) => {
      gameOver.value = true
      winner.value = msg.winner
      errorMsg.value = msg.reason ? `${getColorNameCN(msg.winner)} 获胜（${msg.reason}）` : `${getColorNameCN(msg.winner)} 获胜！`
      rolling.value = false
    }),

    wsClient.on('player_disconnected', (msg) => {
      errorMsg.value = `${msg.player_name} 断开了连接`
    }),

    wsClient.on('player_reconnected', (msg) => {
      errorMsg.value = `${msg.player_name} 重新连接`
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('reconnected', (msg) => {
      playerColor.value = msg.player_color
      gameStore.playerColor = msg.player_color
      playerIndex.value = msg.player_index
      gameStore.playerIndex = msg.player_index
      if (msg.state) {
        boardState.value = msg.state.board_state
        gameStore.boardState = msg.state.board_state
        players.value = msg.state.players || []
        gameStore.players = msg.state.players
        currentTurn.value = msg.state.board_state.current_turn
        myTurn.value = currentTurn.value === playerIndex.value
        if (msg.state.board_state.game_over) {
          gameOver.value = true
          winner.value = msg.state.board_state.winner
        }
      }
      errorMsg.value = '重新连接成功'
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('player_left', (msg) => {
      errorMsg.value = `${msg.player_name} 离开了房间`
      setTimeout(() => {
        router.push('/ludo/lobby')
      }, 2000)
    }),

    wsClient.on('error', (msg) => {
      errorMsg.value = msg.message
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('close', () => {
      errorMsg.value = '连接已断开，正在重连...'
    }),

    wsClient.on('open', () => {
      errorMsg.value = ''
    }),
  ]

  setTimeout(() => {
    if (wsClient.isConnected()) {
      wsClient.send({ type: 'sync' })
    }
  }, 300)
})

onUnmounted(() => {
  unsubAll()
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<template>
  <div class="ludo-game-container">
    <div v-if="errorMsg" class="error-toast" :class="{ 'success': errorMsg.includes('成功') || errorMsg.includes('开始') }">{{ errorMsg }}</div>

    <div class="turn-indicator" :style="{ borderColor: currentColorHex, color: currentColorHex }">
      {{ gameOver ? '游戏结束' : currentColorName + '走棋' }}
      <span v-if="myTurn && !gameOver" class="my-turn-badge">你的回合</span>
      <span v-if="gameOver && winner === playerColor" class="win-badge">你赢了!</span>
      <span v-if="gameOver && winner && winner !== playerColor" class="lose-badge">你输了</span>
    </div>

    <div class="players-bar">
      <div
        v-for="(p, i) in players"
        :key="i"
        class="player-chip"
        :class="{ active: currentTurn === i, me: i === playerIndex }"
        :style="{ '--player-color': getColorHex(p.color) }"
      >
        <span class="player-dot" :style="{ background: getColorHex(p.color) }"></span>
        <span class="player-name">{{ p.name }} {{ i === playerIndex ? '(你)' : '' }}</span>
        <span v-if="!p.online" class="offline-tag">离线</span>
      </div>
    </div>

    <template v-if="!isMobile">
      <div class="game-layout">
        <div class="board-area">
          <LudoBoard
            :board-state="boardState"
            :player-color="playerColor"
            :playable-pieces="myTurn ? playablePieces : []"
            :game-over="gameOver"
            @piece-click="handlePieceClick"
          />
        </div>
        <div class="sidebar">
          <div class="dice-area">
            <Dice3D
              :value="diceValue"
              :rolling="rolling"
              :disabled="!myTurn || gameOver"
              @roll="handleRoll"
            />
          </div>
          <div class="timer-display" v-if="!gameOver">
            <div class="timer-label">剩余时间</div>
            <div class="timer-value" :class="{ urgent: timerRemaining <= 10 }">{{ timerRemaining }}s</div>
          </div>
          <div class="info-panel">
            <div class="info-row">
              <span class="info-label">房间</span>
              <span class="room-id-text">{{ roomId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">你的颜色</span>
              <span class="color-label" :style="{ color: getColorHex(playerColor) }">{{ myColorLabel }}</span>
            </div>
            <div v-if="diceValue && !gameOver" class="dice-result">
              掷出：<strong>{{ diceValue }}</strong>
            </div>
          </div>
          <button class="btn-leave" @click="handleLeave">离开房间</button>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="mobile-layout">
        <LudoBoard
          :board-state="boardState"
          :player-color="playerColor"
          :playable-pieces="myTurn ? playablePieces : []"
          :game-over="gameOver"
          :parent-width="mobileBoardWidth"
          @piece-click="handlePieceClick"
        />
        <div class="mobile-bottom">
          <Dice3D
            :value="diceValue"
            :rolling="rolling"
            :disabled="!myTurn || gameOver"
            @roll="handleRoll"
          />
          <div class="timer-display" v-if="!gameOver">
            <div class="timer-value" :class="{ urgent: timerRemaining <= 10 }">{{ timerRemaining }}s</div>
          </div>
          <button class="btn-leave" @click="handleLeave">离开</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ludo-game-container { width: 100%; }
.error-toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  background: #dc3545; color: #fff; padding: 10px 24px; border-radius: 8px; z-index: 200;
  font-size: 0.9rem;
}
.error-toast.success { background: #28a745; }
.turn-indicator {
  text-align: center; font-size: 1.1rem; font-weight: 700;
  padding: 8px 16px; border-radius: 8px; margin-bottom: 12px;
  border: 1px solid;
}
.my-turn-badge {
  display: inline-block; background: #28a745; color: #fff;
  padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;
  animation: pulse 0.8s ease infinite alternate;
}
.win-badge {
  display: inline-block; background: #ffd700; color: #222;
  padding: 2px 12px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;
}
.lose-badge {
  display: inline-block; background: #666; color: #fff;
  padding: 2px 12px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;
}
@keyframes pulse {
  from { opacity: 0.7; transform: scale(1); }
  to { opacity: 1; transform: scale(1.05); }
}
.players-bar {
  display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; justify-content: center;
}
.player-chip {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 12px 4px 8px; border-radius: 20px;
  background: rgba(22,33,62,0.85); border: 1px solid transparent;
  font-size: 0.8rem;
}
.player-chip.active { border-color: var(--player-color); }
.player-chip.me { background: rgba(255,255,255,0.08); }
.player-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.player-name { color: #ccc; }
.offline-tag { font-size: 0.7rem; color: #888; }
.game-layout { display: grid; grid-template-columns: auto 1fr; gap: 20px; align-items: start; }
.board-area { display: flex; flex-direction: column; align-items: center; }
.sidebar {
  display: flex; flex-direction: column; gap: 12px; min-width: 180px; align-items: center;
}
.dice-area { text-align: center; }
.timer-display {
  background: rgba(22,33,62,0.85); border-radius: 10px; padding: 10px 16px; text-align: center;
  border: 1px solid rgba(255,255,255,0.06);
}
.timer-label { font-size: 0.75rem; color: #888; }
.timer-value { font-size: 1.5rem; font-weight: 700; font-family: monospace; color: #eee; }
.timer-value.urgent { color: #dc3545; animation: pulse 0.5s ease infinite alternate; }
.info-panel {
  background: rgba(22,33,62,0.85); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 12px 16px; width: 100%;
}
.info-row { display: flex; justify-content: space-between; font-size: 0.9rem; padding: 4px 0; }
.info-label { color: #888; }
.room-id-text { font-family: monospace; color: #ffd700; }
.color-label { font-weight: 700; }
.dice-result { text-align: center; font-size: 0.9rem; color: #ccc; margin-top: 4px; }
.btn-leave {
  width: 100%; padding: 10px; border: none; border-radius: 8px;
  background: #6c757d; color: #fff; cursor: pointer; font-size: 0.85rem; font-weight: 600;
}
.btn-leave:hover { opacity: 0.9; }
.mobile-layout { display: flex; flex-direction: column; align-items: center; gap: 12px; padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px)); }
.mobile-bottom { display: flex; align-items: center; gap: 16px; width: 100%; justify-content: center; }
</style>
