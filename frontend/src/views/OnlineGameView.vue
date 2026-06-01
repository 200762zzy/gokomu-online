<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import GameBoard from '../components/GameBoard.vue'
import GameInfo from '../components/GameInfo.vue'
import WinRatePanel from '../components/WinRatePanel.vue'
import { createBoard, BLACK, WHITE, getStoneName } from '../services/gameLogic.js'
import { getWsClient } from '../services/wsClient.js'
import { requestReview } from '../services/apiClient.js'
import { audioManager } from '../services/audioManager.js'
import ReplayMoveList from '../components/ReplayMoveList.vue'

const props = defineProps({
  roomId: String,
  playerColor: String,
  playerName: String,
  opponentName: String,
})

const emit = defineEmits(['backLobby'])

const wsClient = getWsClient()

const board = ref(createBoard())
const currentTurn = ref('black')
const myTurn = ref(false)
const gameOver = ref(false)
const winner = ref('')
const gameResult = ref('')
const moveCount = ref(0)
const blackMoveCount = ref(0)
const whiteMoveCount = ref(0)
const moveHistory = ref([])
const opponentName = ref('等待对手加入...')
const analysis = ref(null)
const analyzing = ref(false)
const drawOfferBy = ref('')
const undoOfferBy = ref('')
const errorMsg = ref('')
const waiting = ref(true)
const lastMove = ref(null)
const moveAnalysisHistory = ref([])
const reviews = ref([])
const reviewsLoading = ref(false)
const replayMode = ref(false)
const replayStep = ref(-1)

const myColorLabel = computed(() => props.playerColor === 'black' ? '黑方' : '白方')

const currentMoveLabel = computed(() => {
  const len = moveAnalysisHistory.value.length
  if (len === 0) return null
  const cur = moveAnalysisHistory.value[len - 1]
  if (!cur) return null
  const prev = len >= 2 ? moveAnalysisHistory.value[len - 2] : null
  if (!prev) return { text: '开局', color: '#aaa', desc: '', delta: null }
  const last = moveHistory.value[len - 1]
  if (!last) return null
  let delta, playerRate
  if (last.player === BLACK) {
    delta = cur.black_win_rate - prev.black_win_rate
    playerRate = cur.black_win_rate
  } else {
    delta = cur.white_win_rate - prev.white_win_rate
    playerRate = cur.white_win_rate
  }
  if (playerRate >= 0.95) return { text: '绝杀手', color: '#ff2d55', desc: '必胜之着', delta }
  if (playerRate >= 0.85) return { text: '决胜手', color: '#ff6b6b', desc: '胜势确立', delta }
  if (delta >= 0.20) return { text: '妙手', color: '#ffd700', desc: '精妙着法', delta }
  if (delta >= 0.08) return { text: '好手', color: '#4ecdc4', desc: '取得优势', delta }
  if (delta >= -0.08) return { text: '正常', color: '#aaa', desc: '平稳进行', delta }
  if (delta >= -0.20) return { text: '疑问手', color: '#e6a817', desc: '略有亏损', delta }
  return { text: '昏招', color: '#dc3545', desc: '严重失误', delta }
})

const replayMoves = computed(() => {
  return moveHistory.value.map((m, i) => ({
    ...m,
    analysis: moveAnalysisHistory.value[i] || null,
  }))
})

const displayBoard = computed(() => {
  if (!replayMode.value) return board.value
  const b = createBoard()
  for (let i = 0; i <= replayStep.value; i++) {
    const m = moveHistory.value[i]
    if (m) b[m.row][m.col] = m.player
  }
  return b
})

const unsubFns = []

onMounted(() => {
  if (props.opponentName) {
    opponentName.value = props.opponentName
    waiting.value = false
  }

  unsubFns.push(wsClient.on('room_joined', (msg) => {
    opponentName.value = msg.opponent_name
  }))

  unsubFns.push(wsClient.on('opponent_joined', (msg) => {
    opponentName.value = msg.player_name
    waiting.value = false
  }))

  unsubFns.push(wsClient.on('game_state', (msg) => {
    board.value = _parseBoard(msg.board)
    currentTurn.value = msg.current_turn
    myTurn.value = msg.your_turn
    moveCount.value = msg.move_history.length
    moveHistory.value = msg.move_history.map(m => ({ ...m }))
    blackMoveCount.value = msg.move_history.filter(m => m.player === BLACK).length
    whiteMoveCount.value = msg.move_history.filter(m => m.player === WHITE).length
    lastMove.value = _lastFromHistory(msg.move_history)
    waiting.value = false
  }))

  unsubFns.push(wsClient.on('stone_placed', (msg) => {
    audioManager.playStone()
    const r = msg.row
    const c = msg.col
    const p = msg.player === 'black' ? BLACK : WHITE
    board.value = board.value.map((row, ri) =>
      row.map((cell, ci) => (ri === r && ci === c ? p : cell))
    )
    currentTurn.value = msg.current_turn
    if (msg.player === 'black') {
      blackMoveCount.value++
    } else {
      whiteMoveCount.value++
    }
    moveCount.value++
    moveHistory.value.push({ row: r, col: c, player: p })
    moveAnalysisHistory.value.push(null)
    lastMove.value = { row: r, col: c }
  }))

  unsubFns.push(wsClient.on('your_turn', (msg) => {
    myTurn.value = msg.your_turn
  }))

  unsubFns.push(wsClient.on('analysis_result', (msg) => {
    if (msg.analysis) {
      analysis.value = msg.analysis
      analyzing.value = false
      const idx = moveCount.value - 1
      if (idx >= 0) {
        moveAnalysisHistory.value[idx] = msg.analysis
      }
    }
  }))

  unsubFns.push(wsClient.on('game_over', (msg) => {
    gameOver.value = true
    winner.value = msg.winner || ''
    gameResult.value = msg.reason || ''
    myTurn.value = false
    const myColor = props.playerColor === 'black' ? BLACK : WHITE
    if (msg.winner === 'black') (myColor === BLACK ? audioManager.playWin() : audioManager.playLose())
    else if (msg.winner === 'white') (myColor === WHITE ? audioManager.playWin() : audioManager.playLose())
    saveGameToHistory()
    requestGameReview()
  }))

  unsubFns.push(wsClient.on('undo_success', (msg) => {
    board.value = _parseBoard(msg.board)
    currentTurn.value = msg.current_turn
    moveCount.value = msg.move_history.length
    moveHistory.value = msg.move_history.map(m => ({ ...m }))
    moveAnalysisHistory.value = moveAnalysisHistory.value.slice(0, moveCount.value)
    blackMoveCount.value = msg.move_history.filter(m => m.player === BLACK).length
    whiteMoveCount.value = msg.move_history.filter(m => m.player === WHITE).length
    myTurn.value = currentTurn.value === props.playerColor
    lastMove.value = _lastFromHistory(msg.move_history)
  }))

  unsubFns.push(wsClient.on('undo_offered', (msg) => {
    undoOfferBy.value = msg.by
  }))

  unsubFns.push(wsClient.on('undo_declined', () => {
    undoOfferBy.value = ''
  }))

  unsubFns.push(wsClient.on('draw_offered', (msg) => {
    drawOfferBy.value = msg.by
  }))

  unsubFns.push(wsClient.on('draw_declined', () => {
    drawOfferBy.value = ''
  }))

  unsubFns.push(wsClient.on('opponent_disconnected', (msg) => {
    opponentName.value = msg.message || '对手断线了'
  }))

  unsubFns.push(wsClient.on('opponent_left', (msg) => {
    opponentName.value = msg.message || '对手离开了'
    gameOver.value = true
  }))

  unsubFns.push(wsClient.on('error', (msg) => {
    errorMsg.value = msg.message
    setTimeout(() => errorMsg.value = '', 3000)
  }))

  unsubFns.push(wsClient.on('close', () => {
    errorMsg.value = '连接已断开'
  }))
})

onUnmounted(() => {
  wsClient.send({ type: 'leave_room' })
  wsClient.disconnect()
  unsubFns.forEach(fn => fn())
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

function _lastFromHistory(history) {
  if (!history || history.length === 0) return null
  const m = history[history.length - 1]
  return { row: m.row, col: m.col }
}

function handlePlaceStone({ row, col }) {
  if (gameOver.value || !myTurn.value || waiting.value) return
  wsClient.send({ type: 'place_stone', row, col })
}

function handleUndo() {
  if (gameOver.value || waiting.value || moveCount.value === 0) return
  wsClient.send({ type: 'undo_request' })
}

function handleUndoResponse(accept) {
  wsClient.send({ type: 'undo_response', accept })
  undoOfferBy.value = ''
}

function handleResign() {
  if (gameOver.value || waiting.value) return
  wsClient.send({ type: 'resign' })
}

function handleDrawRequest() {
  if (gameOver.value || waiting.value || drawOfferBy.value) return
  wsClient.send({ type: 'draw_request' })
}

function handleDrawResponse(accept) {
  wsClient.send({ type: 'draw_response', accept })
  drawOfferBy.value = ''
}

function leaveRoom() {
  emit('backLobby')
}

function formatResult(reason) {
  if (reason === '和棋') return 'draw'
  if (reason === '黑方认负' || reason === 'black认负') return 'resign_black'
  if (reason === '白方认负' || reason === 'white认负') return 'resign_white'
  if (winner.value === 'black') return 'black_win'
  if (winner.value === 'white') return 'white_win'
  return ''
}

function saveGameToHistory() {
  const entry = {
    id: Date.now(),
    timestamp: new Date().toLocaleString('zh-CN'),
    result: formatResult(gameResult.value) || gameResult.value,
    winner: winner.value,
    moves: moveHistory.value.map((m, i) => ({
      row: m.row,
      col: m.col,
      player: m.player,
      analysis: moveAnalysisHistory.value[i] || null,
    })),
    blackMoveCount: blackMoveCount.value,
    whiteMoveCount: whiteMoveCount.value,
    reviews: reviews.value,
  }
  try {
    const history = JSON.parse(localStorage.getItem('gomoku_history') || '[]')
    history.push(entry)
    localStorage.setItem('gomoku_history', JSON.stringify(history))
  } catch {}
}

async function requestGameReview() {
  if (moveHistory.value.length === 0) return
  reviewsLoading.value = true
  const data = await requestReview(
    moveHistory.value.map(m => ({ row: m.row, col: m.col, player: m.player })),
    formatResult(gameResult.value),
  )
  if (data && data.reviews) {
    reviews.value = data.reviews
  }
  reviewsLoading.value = false
}

function enterReplay() {
  replayMode.value = true
  replayStep.value = moveCount.value - 1
}

function exitReplay() {
  replayMode.value = false
  replayStep.value = -1
}

function replayGoTo(step) {
  replayStep.value = Math.max(-1, Math.min(step, moveCount.value - 1))
}

function replayNext() {
  if (replayStep.value < moveCount.value - 1) replayStep.value++
}

function replayPrev() {
  if (replayStep.value >= 0) replayStep.value--
}
</script>

<template>
  <div v-if="errorMsg" class="error-toast">{{ errorMsg }}</div>
  <div class="game-layout">
    <div class="left-column">
      <GameBoard
        :board="displayBoard"
        :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
        :game-over="gameOver"
        :readonly="!myTurn || gameOver || replayMode"
        :last-move="replayMode ? (replayStep >= 0 ? { row: moveHistory[replayStep]?.row, col: moveHistory[replayStep]?.col } : null) : lastMove"
        @place-stone="handlePlaceStone"
      />
    </div>
    <div class="right-column">
      <div class="room-info">
        <span class="room-badge">#{{ roomId }}</span>
        <span class="my-color">{{ myColorLabel }}</span>
      </div>

      <GameInfo
        :current-turn="getStoneName(currentTurn === 'black' ? BLACK : WHITE)"
        :game-over="gameOver"
        :winner="winner"
        :game-result="gameResult"
        :black-move-count="blackMoveCount"
        :white-move-count="whiteMoveCount"
      />

      <div class="player-info">
        <div class="player-row">
          <span class="player-label">你</span>
          <span class="player-name">{{ playerName }}</span>
          <span class="player-dot" :class="playerColor"></span>
        </div>
        <div class="player-row">
          <span class="player-label">对手</span>
          <span class="player-name">{{ opponentName }}</span>
          <span class="player-dot" :class="playerColor === 'black' ? 'white' : 'black'"></span>
        </div>
      </div>

      <template v-if="waiting">
        <div class="waiting-msg">等待对手加入...</div>
      </template>
      <template v-else>
        <WinRatePanel
          :analysis="analysis"
          :loading="analyzing"
          :move-label="currentMoveLabel"
        />

        <button
          class="btn-action btn-analysis"
          :disabled="analyzing"
          @click="wsClient.send({ type: 'request_analysis' })"
        >
          {{ analyzing ? '分析中...' : '刷新分析' }}
        </button>

        <template v-if="!replayMode">
          <div v-if="!gameOver" class="action-row">
            <button
              class="btn-action btn-undo"
              :disabled="!myTurn || moveCount === 0 || undoOfferBy !== ''"
              @click="handleUndo"
            >悔棋</button>
            <button
              class="btn-action btn-draw"
              :disabled="drawOfferBy !== ''"
              @click="handleDrawRequest"
            >求和</button>
            <button
              class="btn-action btn-resign"
              @click="handleResign"
            >认输</button>
          </div>
          <div v-else class="game-over-actions">
            <button class="btn-action btn-restart" @click="leaveRoom">返回大厅</button>
            <button
              v-if="reviewsLoading || reviews.length > 0"
              class="btn-action btn-review"
              @click="enterReplay"
            >{{ reviewsLoading ? '评价加载中...' : '查看复盘' }}</button>
          </div>
        </template>
        <template v-else>
          <ReplayMoveList
            :moves="replayMoves"
            :current-step="replayStep"
            :reviews="reviews"
            :reviews-loading="reviewsLoading"
            @go-to-step="replayGoTo"
          />
          <div class="replay-controls">
            <button class="replay-btn" @click="replayPrev" title="上一步">◁</button>
            <span class="replay-step-info">
              <template v-if="replayStep === -1">开局</template>
              <template v-else>第 {{ replayStep + 1 }} / {{ moveCount }} 手</template>
            </span>
            <button class="replay-btn" @click="replayNext" title="下一步">▷</button>
          </div>
          <button class="btn-action btn-restart" @click="exitReplay">退出复盘</button>
        </template>
      </template>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="drawOfferBy" class="overlay" @click.self="handleDrawResponse(false)">
      <div class="dialog">
        <p>对手请求和棋，是否接受？</p>
        <div class="dialog-buttons">
          <button class="btn-accept" @click="handleDrawResponse(true)">接受</button>
          <button class="btn-reject" @click="handleDrawResponse(false)">拒绝</button>
        </div>
      </div>
    </div>
    <div v-if="undoOfferBy" class="overlay">
      <div class="dialog">
        <p>对手请求悔棋，是否接受？</p>
        <div class="dialog-buttons">
          <button class="btn-accept" @click="handleUndoResponse(true)">接受</button>
          <button class="btn-reject" @click="handleUndoResponse(false)">拒绝</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.game-layout {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  width: 100%;
  align-items: start;
}

.left-column {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 220px;
}

.room-info {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px 16px;
}

.room-badge {
  font-family: monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #667eea;
  background: #0f3460;
  padding: 4px 10px;
  border-radius: 6px;
}

.my-color {
  font-size: 0.9rem;
  color: #aaa;
}

.player-info {
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px 16px;
}

.player-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.player-label {
  color: #888;
  font-size: 0.85rem;
  min-width: 30px;
}

.player-name {
  flex: 1;
  font-size: 0.9rem;
}

.player-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.player-dot.black {
  background: #222;
}

.player-dot.white {
  background: #ddd;
  border: 1px solid #888;
}

.waiting-msg {
  text-align: center;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 32px;
  color: #888;
  font-size: 0.95rem;
}

.action-row {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 10px 14px;
  border: none;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: opacity 0.2s;
  flex: 1;
}

.btn-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-action:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-analysis {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.btn-undo {
  background: #e6a817;
}

.btn-draw {
  background: #17a2b8;
}

.btn-resign {
  background: #dc3545;
}

.btn-restart {
  background: #533483;
}

.game-over-actions {
  display: flex;
  gap: 8px;
}

.btn-review {
  background: #533483;
}

.replay-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 10px 16px;
  border-radius: 10px;
}

.replay-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #0f3460;
  color: #eee;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 700;
  transition: background 0.2s;
}

.replay-btn:hover {
  background: #533483;
}

.replay-step-info {
  font-size: 0.85rem;
  color: #aaa;
  min-width: 80px;
  text-align: center;
  font-family: monospace;
}

.error-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #dc3545;
  color: #fff;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  z-index: 200;
  box-shadow: 0 4px 16px rgba(220, 53, 69, 0.4);
  animation: fadeInOut 3s ease forwards;
}

@keyframes fadeInOut {
  0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
  10% { opacity: 1; transform: translateX(-50%) translateY(0); }
  80% { opacity: 1; }
  100% { opacity: 0; }
}

@media (max-width: 820px) {
  .game-layout {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
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
  padding: 32px;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  max-width: 320px;
}

.dialog p {
  font-size: 1.1rem;
  margin-bottom: 24px;
  color: #eee;
}

.dialog-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.dialog-buttons button {
  padding: 10px 28px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
  transition: opacity 0.2s;
}

.dialog-buttons button:hover {
  opacity: 0.9;
}

.btn-accept {
  background: #28a745;
}

.btn-reject {
  background: #6c757d;
}
</style>
