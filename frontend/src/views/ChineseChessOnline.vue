<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChineseChessBoard from '../components/ChineseChessBoard.vue'
import TitleBadge from '../components/TitleBadge.vue'
import EntranceBanner from '../components/EntranceBanner.vue'
import { createBoard, RED, BLACK, getPieceColor, getPieceName, getValidMoves, makeMove, cloneBoard, isInCheck } from '../services/chineseChessLogic.js'
import { getCcWsClient } from '../services/ccWsClient.js'
import { useAuthStore } from '../stores/auth.js'
import { audioManager } from '../services/audioManager.js'
import { useCcGameStore } from '../stores/ccGame.js'
import { useIsMobile } from '../composables/useIsMobile.js'
import { getTitleInfo } from '../utils/titles.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const gameStore = useCcGameStore()
const wsClient = getCcWsClient()
const { isMobile } = useIsMobile()
const mobileBoardWidth = computed(() => Math.min(window.innerWidth - 16, 560))

const roomId = route.params.roomId || gameStore.currentRoomId
const playerColor = ref(gameStore.playerColor)
const board = ref(createBoard())
const currentTurn = ref('red')
const myTurn = ref(false)
const gameOver = ref(false)
const winner = ref('')
const moveCount = ref(0)
const moveHistory = ref([])
const opponentName = ref(gameStore.opponentName || '等待对手加入...')
const waiting = ref(
  !opponentName.value || opponentName.value === '等待对手加入...'
)
const errorMsg = ref('')
const lastMove = ref(null)
const selectedPos = ref(null)
const validMoves = ref([])
const inCheck = ref('')
const drawOfferBy = ref('')
const undoOfferBy = ref('')
const pendingMove = ref(null)

const opponentTitle = ref(null)
const showEntryBanner = ref(false)
const entryPlayerName = ref('')
const entryTier = ref(1)

const turnLabel = computed(() => currentTurn.value === 'red' ? '红方' : '黑方')
const myColorLabel = computed(() => playerColor.value === 'red' ? '红方' : '黑方')

let unsubFns = []

function handleCellClick(pos) {
  if (gameOver.value || !myTurn.value || pendingMove.value) return
  const { row, col } = pos
  const piece = board.value[row][col]
  const pieceColor = getPieceColor(piece)
  const myColor = playerColor.value === 'red' ? RED : BLACK

  if (selectedPos.value) {
    const isOwnPiece = pieceColor === myColor
    const isValidTarget = validMoves.value.some(m => m.row === row && m.col === col)

    if (isValidTarget) {
      pendingMove.value = {
        from: { row: selectedPos.value.row, col: selectedPos.value.col },
        to: { row, col },
      }
      selectedPos.value = null
      validMoves.value = []
      return
    }

    if (isOwnPiece) {
      selectedPos.value = { row, col }
      validMoves.value = getValidMoves(board.value, row, col)
      return
    }

    selectedPos.value = null
    validMoves.value = []
    return
  }

  if (pieceColor === myColor) {
    selectedPos.value = { row, col }
    validMoves.value = getValidMoves(board.value, row, col)
  }
}

function confirmMove() {
  if (!pendingMove.value) return
  const { from, to } = pendingMove.value
  const captured = board.value[to.row][to.col]
  if (captured) {
    audioManager.playChessCapture()
    audioManager.playChessEat()
  }
  makeMove(board.value, from.row, from.col, to.row, to.col)
  audioManager.playChessMove()
  wsClient.send({
    type: 'move_piece',
    from_row: from.row,
    from_col: from.col,
    to_row: to.row,
    to_col: to.col,
  })
  pendingMove.value = null
}

function cancelMove() {
  pendingMove.value = null
}

function updateCheck() {
  const color = currentTurn.value === 'red' ? RED : BLACK
  const wasCheck = inCheck.value
  inCheck.value = isInCheck(board.value, color) ? currentTurn.value : ''
  if (inCheck.value && !wasCheck) audioManager.playChessCheck()
}

function unsubAll() {
  unsubFns.forEach(fn => fn())
  unsubFns = []
}

onMounted(() => {
  console.log('[CC] mounted, ws connected:', wsClient.isConnected(), 'opponentName:', opponentName.value, 'gameStore.opponentName:', gameStore.opponentName)
  if (!wsClient.isConnected()) {
    wsClient.connect(authStore.accessToken)
  }

  const pending = gameStore.pendingGameState
  if (pending) {
    gameStore.pendingGameState = null
    board.value = _parseBoard(pending.board)
    currentTurn.value = pending.currentTurn
    myTurn.value = pending.myTurn
    moveHistory.value = (pending.moveHistory || []).map(m => ({ ...m }))
    moveCount.value = pending.moveHistory.length
    lastMove.value = moveCount.value > 0
      ? { row: moveHistory.value[moveCount.value - 1].to_r, col: moveHistory.value[moveCount.value - 1].to_c }
      : null
  }
  if (gameStore.opponentName) {
    opponentName.value = gameStore.opponentName
    waiting.value = false
  }
  if (gameStore.playerColor) {
    playerColor.value = gameStore.playerColor
  }
  if (gameStore.opponentTitle) {
    triggerEntry(gameStore.opponentName, gameStore.opponentTitle)
  }

  let wasDisconnected = false

  function triggerEntry(name, title) {
    entryPlayerName.value = name
    const t = title || getTitleInfo(1000)
    opponentTitle.value = t
    entryTier.value = t.tier || 1
    showEntryBanner.value = true
  }

  unsubFns = [
    wsClient.on('room_joined', (msg) => {
      console.log('[CC] room_joined:', msg)
      opponentName.value = msg.opponent_name
      waiting.value = false
      if (msg.player_color) playerColor.value = msg.player_color
      if (msg.opponent_title) {
        triggerEntry(msg.opponent_name, msg.opponent_title)
      }
    }),

    wsClient.on('opponent_joined', (msg) => {
      console.log('[CC] opponent_joined:', msg)
      opponentName.value = msg.player_name
      waiting.value = false
      if (msg.player_title) {
        triggerEntry(msg.player_name, msg.player_title)
      }
    }),

    wsClient.on('reconnected', (msg) => {
      console.log('[CC] reconnected:', msg)
      const oppColor = msg.player_color === 'red' ? 'black' : 'red'
      const oppName = msg[`${oppColor}_name`]
      if (oppName) {
        opponentName.value = oppName
        waiting.value = false
      }
      if (msg.opponent_title) {
        opponentTitle.value = msg.opponent_title
        triggerEntry(oppName || opponentName.value, msg.opponent_title)
      }
      if (msg.board) {
        board.value = _parseBoard(msg.board)
        currentTurn.value = msg.current_turn
        myTurn.value = msg.your_turn
        moveHistory.value = (msg.move_history || []).map(m => ({ ...m }))
        moveCount.value = msg.move_history.length
        lastMove.value = moveCount.value > 0
          ? { row: moveHistory.value[moveCount.value - 1].to_r, col: moveHistory.value[moveCount.value - 1].to_c }
          : null
      }
    }),

    wsClient.on('game_state', (msg) => {
      board.value = _parseBoard(msg.board)
      currentTurn.value = msg.current_turn
      if (msg.your_turn !== undefined) myTurn.value = msg.your_turn
      moveHistory.value = (msg.move_history || []).map(m => ({ ...m }))
      moveCount.value = msg.move_history.length
      lastMove.value = moveCount.value > 0
        ? { row: moveHistory.value[moveCount.value - 1].to_r, col: moveHistory.value[moveCount.value - 1].to_c }
        : null
      updateCheck()
    }),

    wsClient.on('piece_moved', (msg) => {
      const isOpponent = playerColor.value !== msg.player
      if (isOpponent) {
        const captured = board.value[msg.to_row][msg.to_col]
        if (captured) {
          audioManager.playChessCapture()
          audioManager.playChessEat()
        }
        makeMove(board.value, msg.from_row, msg.from_col, msg.to_row, msg.to_col)
        audioManager.playChessMove()
      }
      currentTurn.value = msg.current_turn
      myTurn.value = msg.current_turn === playerColor.value
      lastMove.value = { row: msg.to_row, col: msg.to_col }
      moveCount.value++
      moveHistory.value.push({
        from_r: msg.from_row, from_c: msg.from_col,
        to_r: msg.to_row, to_c: msg.to_col,
      })
      selectedPos.value = null
      validMoves.value = []
      updateCheck()
    }),

    wsClient.on('your_turn', (msg) => {
      myTurn.value = msg.your_turn
    }),

    wsClient.on('game_over', (msg) => {
      gameOver.value = true
      winner.value = msg.winner
      inCheck.value = ''
      if (msg.winner === playerColor.value) audioManager.playWin()
      else if (msg.winner) audioManager.playLose()
    }),

    wsClient.on('draw_offered', (msg) => {
      drawOfferBy.value = msg.by
    }),

    wsClient.on('draw_declined', () => {
      drawOfferBy.value = ''
    }),

    wsClient.on('opponent_disconnected', (msg) => {
      errorMsg.value = msg.message
      setTimeout(() => errorMsg.value = '', 5000)
    }),

    wsClient.on('opponent_left', (msg) => {
      opponentName.value = msg.message || '对手离开了'
      waiting.value = true
      errorMsg.value = msg.message
      setTimeout(() => {
        router.push('/chess/lobby')
      }, 2000)
    }),

    wsClient.on('error', (msg) => {
      errorMsg.value = msg.message
      setTimeout(() => errorMsg.value = '', 3000)
    }),

    wsClient.on('sync_room', (msg) => {
      console.log('[CC] sync_room:', msg)
      if (msg.player_color) playerColor.value = msg.player_color
      if (msg.opponent_name && msg.opponent_name !== '等待对手加入...') {
        opponentName.value = msg.opponent_name
        waiting.value = false
      }
      if (msg.opponent_title) opponentTitle.value = msg.opponent_title
      if (msg.board) board.value = _parseBoard(msg.board)
      if (msg.current_turn) currentTurn.value = msg.current_turn
      if (msg.your_turn !== undefined) myTurn.value = msg.your_turn
      const hist = msg.move_history || []
      moveHistory.value = hist.map(m => ({ ...m }))
      moveCount.value = hist.length
      lastMove.value = moveCount.value > 0
        ? { row: hist[moveCount.value - 1].to_r, col: hist[moveCount.value - 1].to_c }
        : null
      if (msg.game_over) {
        gameOver.value = true
        winner.value = msg.winner || ''
      }
      updateCheck()
      gameStore.currentRoomId = null
      gameStore.pendingGameState = null
    }),

    wsClient.on('close', () => {
      wasDisconnected = true
      errorMsg.value = '连接已断开，正在尝试重连...'
    }),

    wsClient.on('open', () => {
      if (wasDisconnected) {
        wasDisconnected = false
        errorMsg.value = '重连成功'
        setTimeout(() => errorMsg.value = '', 2000)
        if (roomId) {
          wsClient.send({ type: 'sync' })
        }
      }
    }),
  ]

  setTimeout(() => {
    if (wsClient.isConnected() && roomId) {
      wsClient.send({ type: 'sync' })
    }
  }, 300)
})

onUnmounted(() => {
  unsubAll()
})

function handleDrawResponse(accept) {
  wsClient.send({ type: 'draw_response', accept })
  drawOfferBy.value = ''
}

function handleResign() {
  wsClient.send({ type: 'resign' })
}

function handleDrawRequest() {
  wsClient.send({ type: 'draw_request' })
}

function handleLeaveRoom() {
  wsClient.send({ type: 'leave_room' })
  gameStore.reset()
  router.push('/chess/lobby')
}

function _parseBoard(data) {
  if (!data || !data.length) return createBoard()
  const b = createBoard()
  for (let r = 0; r < data.length && r < 10; r++) {
    for (let c = 0; c < data[r].length && c < 9; c++) {
      b[r][c] = data[r][c] || 0
    }
  }
  return b
}
</script>

<template>
  <div class="cc-online-container">
    <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>

    <div class="turn-indicator" :class="{ 'red-turn': currentTurn === 'red', 'black-turn': currentTurn === 'black' }">
      {{ turnLabel }}走棋
      <span v-if="myTurn && !gameOver" class="my-turn-badge">你的回合</span>
      <span v-if="inCheck" class="check-badge">{{ inCheck === 'red' ? '红方被将军!' : '黑方被将军!' }}</span>
    </div>

    <template v-if="!isMobile">
      <div class="game-layout">
        <div class="left-column">
          <ChineseChessBoard
            :board="board"
            :current-turn="currentTurn"
            :game-over="gameOver"
            :readonly="!myTurn || gameOver || !!pendingMove"
            :last-move="lastMove"
            :selected-pos="selectedPos"
            :valid-moves="validMoves"
            :in-check="inCheck"
            :flipped="playerColor === 'black'"
            :pending-move="pendingMove"
            @cell-click="handleCellClick"
            @confirm-move="confirmMove"
            @cancel-move="cancelMove"
          />
        </div>
        <div class="right-column">
          <div class="info-panel">
            <div class="info-row">
              <span class="info-label">房间</span>
              <span class="room-id-text">{{ roomId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">你</span>
              <span class="red-text">{{ myColorLabel }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">对手</span>
              <span>{{ opponentName }}</span>
              <TitleBadge v-if="opponentTitle" :title="opponentTitle" size="sm" />
            </div>
            <div v-if="gameOver" class="game-result">
              <template v-if="winner === playerColor">你赢了!</template>
              <template v-else-if="winner && winner !== playerColor">你输了</template>
              <template v-else>和棋</template>
            </div>
          </div>

          <template v-if="!gameOver">
            <div class="action-row">
              <button class="btn-action btn-draw" :disabled="drawOfferBy !== ''" @click="handleDrawRequest">求和</button>
              <button class="btn-action btn-resign" @click="handleResign">认输</button>
            </div>
          </template>

          <button class="btn-action btn-leave" @click="handleLeaveRoom">离开房间</button>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="mobile-layout">
        <ChineseChessBoard
          :board="board"
          :current-turn="currentTurn"
          :game-over="gameOver"
          :readonly="!myTurn || gameOver || !!pendingMove"
          :last-move="lastMove"
          :selected-pos="selectedPos"
          :valid-moves="validMoves"
          :in-check="inCheck"
          :flipped="playerColor === 'black'"
          :pending-move="pendingMove"
          :parent-width="mobileBoardWidth"
          @cell-click="handleCellClick"
          @confirm-move="confirmMove"
          @cancel-move="cancelMove"
        />
        <div class="mobile-info">
          <div class="info-panel">
            <div class="info-row"><span class="info-label">对手</span><span>{{ opponentName }}</span><TitleBadge v-if="opponentTitle" :title="opponentTitle" size="sm" /></div>
            <div v-if="gameOver" class="game-result">
              <template v-if="winner === playerColor">你赢了!</template>
              <template v-else-if="winner">你输了</template>
              <template v-else>和棋</template>
            </div>
          </div>
          <template v-if="!gameOver">
            <div class="action-row">
              <button class="btn-action btn-draw" @click="handleDrawRequest">求和</button>
              <button class="btn-action btn-resign" @click="handleResign">认输</button>
              <button class="btn-action btn-leave" @click="handleLeaveRoom">离开</button>
            </div>
          </template>
          <template v-else>
            <button class="btn-action btn-leave" @click="handleLeaveRoom">离开</button>
          </template>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="drawOfferBy" class="draw-overlay" @click.self="handleDrawResponse(false)">
        <div class="draw-dialog">
          <p>对手请求和棋，是否接受？</p>
          <div class="draw-buttons">
            <button class="btn-draw-accept" @click="handleDrawResponse(true)">接受</button>
            <button class="btn-draw-reject" @click="handleDrawResponse(false)">拒绝</button>
          </div>
        </div>
      </div>
    </Teleport>
    <EntranceBanner
      :show="showEntryBanner"
      :title="opponentTitle || {}"
      :player-name="entryPlayerName"
      :tier="entryTier"
      @done="showEntryBanner = false"
    />
  </div>
</template>

<style scoped>
.cc-online-container { width: 100%; }
.error-toast {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  background: #dc3545; color: #fff; padding: 10px 24px; border-radius: 8px; z-index: 200;
}
.turn-indicator {
  text-align: center; font-size: 1.1rem; font-weight: 700;
  padding: 8px 16px; border-radius: 8px; margin-bottom: 12px;
}
.turn-indicator.red-turn { background: rgba(192,57,43,0.15); color: #e74c3c; }
.turn-indicator.black-turn { background: rgba(44,62,80,0.15); color: #95a5a6; }
.my-turn-badge {
  display: inline-block;
  background: #28a745; color: #fff; padding: 2px 10px;
  border-radius: 12px; font-size: 0.8rem; margin-left: 8px;
  animation: pulse 0.8s ease infinite alternate;
}
.check-badge {
  display: inline-block; background: #ff2d55; color: #fff;
  padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;
  animation: pulse 0.8s ease infinite alternate;
}
@keyframes pulse {
  from { opacity: 0.7; transform: scale(1); }
  to { opacity: 1; transform: scale(1.05); }
}
.game-layout { display: grid; grid-template-columns: auto 1fr; gap: 20px; align-items: start; }
.left-column { display: flex; flex-direction: column; align-items: center; }
.right-column { display: flex; flex-direction: column; gap: 12px; min-width: 200px; }
.info-panel {
  background: rgba(22,33,62,0.85); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; padding: 12px 16px;
}
.info-row { display: flex; justify-content: space-between; font-size: 0.9rem; padding: 4px 0; }
.info-label { color: #888; }
.red-text { color: #e74c3c; }
.room-id-text { font-family: monospace; color: #ffd700; }
.game-result { text-align: center; font-size: 1.1rem; font-weight: 700; color: #ffd700; padding: 8px 0; }
.action-row { display: flex; gap: 8px; }
.btn-action {
  flex: 1; padding: 10px 14px; border: none; color: #fff;
  border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600;
}
.btn-action:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-action:hover:not(:disabled) { opacity: 0.9; }
.btn-draw { background: #17a2b8; }
.btn-resign { background: #dc3545; }
.btn-leave { background: #6c757d; }
.mobile-layout { display: flex; flex-direction: column; align-items: center; gap: 12px; padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px)); }
.mobile-info { width: 100%; display: flex; flex-direction: column; gap: 10px; }
</style>

<style>
.draw-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100;
}
.draw-dialog { background: #1a1a3e; border-radius: 12px; padding: 32px; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.5); max-width: 320px; }
.draw-dialog p { font-size: 1.1rem; margin-bottom: 24px; color: #eee; }
.draw-buttons { display: flex; gap: 12px; justify-content: center; }
.draw-buttons button { padding: 10px 28px; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; color: #fff; }
.btn-draw-accept { background: #28a745; }
.btn-draw-reject { background: #6c757d; }
</style>
