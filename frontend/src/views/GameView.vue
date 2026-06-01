<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import GameBoard from '../components/GameBoard.vue'
import GameInfo from '../components/GameInfo.vue'
import WinRatePanel from '../components/WinRatePanel.vue'
import ReplayMoveList from '../components/ReplayMoveList.vue'
import { createBoard, placeStone, checkWin, isValidMove, checkForbiddenMove, countForcedWins, BLACK, WHITE, getStoneName } from '../services/gameLogic.js'
import { requestAnalysis, requestReview } from '../services/apiClient.js'
import { audioManager } from '../services/audioManager.js'

function getMoveLabel(move, prevAnalysis) {
  if (!move.analysis || !prevAnalysis) {
    return { text: '开局', color: '#aaa', desc: '', delta: null }
  }
  let delta
  let playerRate
  if (move.player === BLACK) {
    delta = move.analysis.black_win_rate - prevAnalysis.black_win_rate
    playerRate = move.analysis.black_win_rate
  } else {
    delta = move.analysis.white_win_rate - prevAnalysis.white_win_rate
    playerRate = move.analysis.white_win_rate
  }
  if (playerRate >= 0.95) return { text: '绝杀手', color: '#ff2d55', desc: '必胜之着', delta }
  if (playerRate >= 0.85) return { text: '决胜手', color: '#ff6b6b', desc: '胜势确立', delta }
  if (delta >= 0.20)      return { text: '妙手', color: '#ffd700', desc: '精妙着法', delta }
  if (delta >= 0.08)      return { text: '好手', color: '#4ecdc4', desc: '取得优势', delta }
  if (delta >= -0.08)     return { text: '正常', color: '#aaa', desc: '平稳进行', delta }
  if (delta >= -0.20)     return { text: '疑问手', color: '#e6a817', desc: '略有亏损', delta }
  return { text: '昏招', color: '#dc3545', desc: '严重失误', delta }
}

const props = defineProps({
  replayGameData: Object,
})

const emit = defineEmits(['backHome'])

const board = ref(createBoard())
const currentTurn = ref(BLACK)
const gameOver = ref(false)
const winner = ref('')
const gameResult = ref('')
const moveCount = ref(0)
const moveHistory = ref([])
const blackMoveCount = ref(0)
const whiteMoveCount = ref(0)
const analysis = ref(null)
const analyzing = ref(false)
const drawOfferBy = ref('')
const reviews = ref([])
const reviewsLoading = ref(false)
const forbiddenMessage = ref('')

const replayMode = ref(false)
const replayStep = ref(-1)
const replayMoves = ref([])

const lastMove = computed(() => {
  if (replayMode.value) {
    if (replayStep.value < 0) return null
    const m = replayMoves.value[replayStep.value]
    return m ? { row: m.row, col: m.col } : null
  }
  if (moveCount.value === 0) return null
  const m = moveHistory.value[moveCount.value - 1]
  return m ? { row: m.row, col: m.col } : null
})

const replayTotal = computed(() => replayMoves.value.length)

const displayBoard = computed(() => {
  if (!replayMode.value) return board.value
  const b = createBoard()
  for (let i = 0; i <= replayStep.value; i++) {
    const m = replayMoves.value[i]
    if (m) b[m.row][m.col] = m.player
  }
  return b
})

const replayCurrentAnalysis = computed(() => {
  if (!replayMode.value || replayStep.value < 0) return null
  const move = replayMoves.value[replayStep.value]
  if (!move || !move.analysis) return null
  return { black_win_rate: move.analysis.black_win_rate, white_win_rate: move.analysis.white_win_rate }
})

const replayCurrentLabel = computed(() => {
  if (!replayMode.value) return null
  if (replayStep.value < 0 || !replayMoves.value[replayStep.value]) {
    return { text: '开局', color: '#aaa', desc: '', delta: null }
  }
  const move = replayMoves.value[replayStep.value]
  const prevMove = replayStep.value > 0 ? replayMoves.value[replayStep.value - 1] : null
  const prevAnalysis = prevMove && prevMove.analysis ? prevMove.analysis : null
  return getMoveLabel(move, prevAnalysis)
})

function resetGame() {
  board.value = createBoard()
  currentTurn.value = BLACK
  gameOver.value = false
  winner.value = ''
  gameResult.value = ''
  moveCount.value = 0
  moveHistory.value = []
  blackMoveCount.value = 0
  whiteMoveCount.value = 0
  analysis.value = null
  analyzing.value = false
  drawOfferBy.value = ''
  reviews.value = []
  reviewsLoading.value = false
  forbiddenMessage.value = ''
}

function handlePlaceStone({ row, col }) {
  if (gameOver.value || replayMode.value) return
  if (!isValidMove(board.value, row, col)) return
  if (currentTurn.value === BLACK) {
    const reason = checkForbiddenMove(board.value, row, col, BLACK)
    if (reason) {
      forbiddenMessage.value = reason
      setTimeout(() => forbiddenMessage.value = '', 3000)
      return
    }
  }
  placeStone(board.value, row, col, currentTurn.value)
  audioManager.playStone()

  moveCount.value++
  moveHistory.value.push({ row, col, player: currentTurn.value })
  if (currentTurn.value === BLACK) blackMoveCount.value++
  else whiteMoveCount.value++

  const win = checkWin(board.value, row, col)
  if (win !== null) {
    gameOver.value = true
    winner.value = getStoneName(win)
    gameResult.value = win === BLACK ? 'black_win' : 'white_win'
    if (win === BLACK) audioManager.playWin()
    else audioManager.playLose()
    saveGameToHistory()
    requestGameReview()
    return
  }

  currentTurn.value = currentTurn.value === BLACK ? WHITE : BLACK
  handleRequestAnalysis()
}

function handleUndo() {
  if (moveCount.value === 0 || gameOver.value || replayMode.value) return
  const last = moveHistory.value.pop()
  if (!last) return
  board.value[last.row][last.col] = 0
  moveCount.value--
  if (last.player === BLACK) blackMoveCount.value--
  else whiteMoveCount.value--
  currentTurn.value = last.player
  analysis.value = null
}

function handleResign() {
  if (gameOver.value || replayMode.value) return
  gameOver.value = true
  if (currentTurn.value === BLACK) {
    winner.value = 'white'
    gameResult.value = 'resign_black'
  } else {
    winner.value = 'black'
    gameResult.value = 'resign_white'
  }
  saveGameToHistory()
  requestGameReview()
}

function handleDrawRequest() {
  if (gameOver.value || replayMode.value || drawOfferBy.value) return
  drawOfferBy.value = getStoneName(currentTurn.value)
}

function handleDrawResponse(accept) {
  if (accept) {
    gameOver.value = true
    winner.value = ''
    gameResult.value = 'draw'
    saveGameToHistory()
    requestGameReview()
  }
  drawOfferBy.value = ''
}

async function handleRequestAnalysis() {
  if (analyzing.value || gameOver.value || replayMode.value) return
  analyzing.value = true
  let result = await requestAnalysis(board.value)
  if (!result) result = { black_win_rate: 0.5, white_win_rate: 0.5 }

  if (countForcedWins(board.value, BLACK) >= 2) {
    result = { black_win_rate: 1.0, white_win_rate: 0.0 }
  } else if (countForcedWins(board.value, WHITE) >= 2) {
    result = { black_win_rate: 0.0, white_win_rate: 1.0 }
  }

  analysis.value = result

  const lastMove = moveHistory.value[moveHistory.value.length - 1]
  if (lastMove) {
    lastMove.analysis = { ...result }
  }

  analyzing.value = false
}

async function requestGameReview() {
  reviewsLoading.value = true
  const data = await requestReview(
    moveHistory.value.map(m => ({ row: m.row, col: m.col, player: m.player })),
    gameResult.value,
  )
  if (data && data.reviews) {
    reviews.value = data.reviews
    updateLastHistoryEntryReviews(data.reviews)
  }
  reviewsLoading.value = false
}

function updateLastHistoryEntryReviews(reviewData) {
  try {
    const history = JSON.parse(localStorage.getItem('gomoku_history') || '[]')
    if (history.length === 0) return
    history[history.length - 1].reviews = reviewData
    localStorage.setItem('gomoku_history', JSON.stringify(history))
  } catch {}
}

function saveGameToHistory() {
  const entry = {
    id: Date.now(),
    timestamp: new Date().toLocaleString('zh-CN'),
    result: gameResult.value,
    winner: winner.value,
    moves: moveHistory.value.map(m => ({
      row: m.row,
      col: m.col,
      player: m.player,
      analysis: m.analysis || null,
    })),
    blackMoveCount: blackMoveCount.value,
    whiteMoveCount: whiteMoveCount.value,
    reviews: reviews.value,
  }
  const history = JSON.parse(localStorage.getItem('gomoku_history') || '[]')
  history.push(entry)
  localStorage.setItem('gomoku_history', JSON.stringify(history))
}

function enterReplay(data) {
  replayMode.value = true
  gameOver.value = true
  winner.value = data.winner || ''
  gameResult.value = data.result || ''
  blackMoveCount.value = data.blackMoveCount || 0
  whiteMoveCount.value = data.whiteMoveCount || 0
  replayMoves.value = data.moves || []
  reviews.value = data.reviews || []
  replayStep.value = -1
}

function exitReplay() {
  replayMode.value = false
  replayMoves.value = []
  replayStep.value = -1
  resetGame()
}

function replayGoTo(step) {
  replayStep.value = Math.max(-1, Math.min(step, replayMoves.value.length - 1))
}

function replayNext() {
  if (replayStep.value < replayMoves.value.length - 1) replayStep.value++
}

function replayPrev() {
  if (replayStep.value >= 0) replayStep.value--
}

onMounted(() => {
  if (props.replayGameData) {
    enterReplay(props.replayGameData)
  }
})

watch(() => props.replayGameData, (val) => {
  if (val) {
    resetGame()
    enterReplay(val)
  }
})
</script>

<template>
  <div v-if="forbiddenMessage" class="forbidden-toast">{{ forbiddenMessage }}</div>
  <div class="game-layout">
    <div class="left-column">
      <GameBoard
        :board="displayBoard"
        :current-turn="getStoneName(currentTurn)"
        :game-over="gameOver"
        :readonly="replayMode"
        :replay-label="replayCurrentLabel"
        :last-move="lastMove"
        @place-stone="handlePlaceStone"
      />
      <div v-if="replayMode" class="replay-controls">
        <button class="replay-btn" @click="replayGoTo(-1)" title="开局">|◁</button>
        <button class="replay-btn" @click="replayPrev" title="上一步">◁</button>
        <span class="replay-step">
          <template v-if="replayStep === -1">开局</template>
          <template v-else>第 {{ replayStep + 1 }} / {{ replayTotal }} 手</template>
        </span>
        <button class="replay-btn" @click="replayNext" title="下一步">▷</button>
        <button class="replay-btn" @click="replayGoTo(replayTotal - 1)" title="终局">▷|</button>
      </div>
    </div>
    <div class="right-column">
      <GameInfo
        :current-turn="getStoneName(currentTurn)"
        :game-over="gameOver"
        :winner="winner"
        :game-result="gameResult"
        :black-move-count="blackMoveCount"
        :white-move-count="whiteMoveCount"
      />
      <template v-if="replayMode">
        <WinRatePanel
          :analysis="replayCurrentAnalysis || { black_win_rate: 0.5, white_win_rate: 0.5 }"
          :loading="false"
          :move-label="replayCurrentLabel"
        />
        <ReplayMoveList
          :moves="replayMoves"
          :current-step="replayStep"
          :reviews="reviews"
          :reviews-loading="reviewsLoading"
          @go-to-step="replayGoTo"
        />
      </template>
      <template v-else>
        <WinRatePanel
          :analysis="analysis"
          :loading="analyzing"
        />
      </template>
      <template v-if="!replayMode">
        <button
          class="btn-action btn-analysis"
          :disabled="analyzing || gameOver"
          @click="handleRequestAnalysis"
        >
          {{ analyzing ? '分析中（约10-30秒）' : '刷新分析' }}
        </button>
        <div v-if="!gameOver" class="action-row">
          <button
            class="btn-action btn-undo"
            :disabled="moveCount === 0"
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
        <button
          v-if="gameOver"
          class="btn-action btn-restart"
          @click="resetGame"
        >再来一局</button>
      </template>
      <template v-else>
        <button class="btn-action btn-restart" @click="exitReplay">退出回放</button>
      </template>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="drawOfferBy" class="draw-overlay" @click.self="handleDrawResponse(false)">
      <div class="draw-dialog">
        <p>{{ drawOfferBy === 'black' ? '黑方' : '白方' }}请求和棋，是否接受？</p>
        <div class="draw-buttons">
          <button class="btn-draw-accept" @click="handleDrawResponse(true)">接受</button>
          <button class="btn-draw-reject" @click="handleDrawResponse(false)">拒绝</button>
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

.replay-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
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

.replay-step {
  font-size: 0.85rem;
  color: #aaa;
  min-width: 80px;
  text-align: center;
  font-family: monospace;
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

.forbidden-toast {
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
.draw-overlay {
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

.draw-dialog {
  background: #1a1a3e;
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  max-width: 320px;
}

.draw-dialog p {
  font-size: 1.1rem;
  margin-bottom: 24px;
  color: #eee;
}

.draw-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.draw-buttons button {
  padding: 10px 28px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
  transition: opacity 0.2s;
}

.draw-buttons button:hover {
  opacity: 0.9;
}

.btn-draw-accept {
  background: #28a745;
}

.btn-draw-reject {
  background: #6c757d;
}
</style>
