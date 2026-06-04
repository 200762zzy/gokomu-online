<script setup>
import { ref, computed, onMounted } from 'vue'
import GameBoard from '../components/GameBoard.vue'
import GameInfo from '../components/GameInfo.vue'
import WinRatePanel from '../components/WinRatePanel.vue'
import ReplayMoveList from '../components/ReplayMoveList.vue'
import { createBoard, placeStone, checkWin, isValidMove, checkForbiddenMove, countForcedWins, BLACK, WHITE, getStoneName } from '../services/gameLogic.js'
import { requestAnalysis, requestReview } from '../services/apiClient.js'
import { getAIMove } from '../services/aiPlayer.js'
import { audioManager } from '../services/audioManager.js'
import { useIsMobile } from '../composables/useIsMobile.js'

const { isMobile } = useIsMobile()
const mobileBoardWidth = computed(() => Math.min(window.innerWidth - 16, 560))

const props = defineProps({
  difficulty: String,
  playerColor: String,
})

const emit = defineEmits(['backHome'])

const player = ref(props.playerColor === 'white' ? WHITE : BLACK)
const aiPlayer = computed(() => player.value === BLACK ? WHITE : BLACK)

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
const reviews = ref([])
const reviewsLoading = ref(false)
const forbiddenMessage = ref('')
const aiThinking = ref(false)

const difficultyLabel = computed(() => {
  if (props.difficulty === 'easy') return '初级'
  if (props.difficulty === 'medium') return '中级'
  if (props.difficulty === 'hard') return '高级'
  return props.difficulty
})

const lastMove = computed(() => {
  if (moveCount.value === 0) return null
  const m = moveHistory.value[moveCount.value - 1]
  return m ? { row: m.row, col: m.col } : null
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
  reviews.value = []
  reviewsLoading.value = false
  forbiddenMessage.value = ''
  aiThinking.value = false
}

function handlePlaceStone({ row, col }) {
  if (gameOver.value || aiThinking.value) return
  if (currentTurn.value !== player.value) return
  if (!isValidMove(board.value, row, col)) return

  if (player.value === BLACK) {
    const reason = checkForbiddenMove(board.value, row, col, BLACK)
    if (reason) {
      forbiddenMessage.value = reason
      setTimeout(() => forbiddenMessage.value = '', 3000)
      return
    }
  }

  commitMove(row, col, player.value)
}

function commitMove(row, col, p) {
  placeStone(board.value, row, col, p)
  moveCount.value++
  moveHistory.value.push({ row, col, player: p })
  if (p === BLACK) blackMoveCount.value++
  else whiteMoveCount.value++

  audioManager.playGomokuStone()

  const win = checkWin(board.value, row, col)
  if (win !== null) {
    gameOver.value = true
    winner.value = getStoneName(win)
    gameResult.value = win === BLACK ? 'black_win' : 'white_win'
    if (win === player.value) audioManager.playWin()
    else audioManager.playLose()
    saveGameToHistory()
    requestGameReview()
    return
  }

  currentTurn.value = currentTurn.value === BLACK ? WHITE : BLACK
  handleRequestAnalysis()

  if (currentTurn.value === aiPlayer.value && !gameOver.value) {
    triggerAIMove()
  }
}

function triggerAIMove() {
  aiThinking.value = true

  setTimeout(async () => {
    const apiKey = localStorage.getItem('deepseek_api_key') || ''

    let move
    if (props.difficulty === 'hard' && apiKey) {
      try {
        const resp = await fetch('/api/ai-move', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            board: board.value,
            player: aiPlayer.value,
            api_key: apiKey,
          }),
        })
        if (resp.ok) {
          const data = await resp.json()
          if (data && typeof data.row === 'number' && typeof data.col === 'number') {
            move = data
          }
        }
      } catch { /* fallback */ }
    }

    if (!move) {
      move = getAIMove(board.value, aiPlayer.value, props.difficulty)
    }

    if (move && isValidMove(board.value, move.row, move.col)) {
      const p = aiPlayer.value
      if (p === BLACK) {
        const reason = checkForbiddenMove(board.value, move.row, move.col, BLACK)
        if (reason) {
          move = getAIMove(board.value, aiPlayer.value, 'easy')
        }
      }
      aiThinking.value = false
      commitMove(move.row, move.col, p)
    } else {
      aiThinking.value = false
    }
  }, 300)
}

async function handleRequestAnalysis() {
  if (analyzing.value || gameOver.value) return
  analyzing.value = true
  let result = await requestAnalysis(board.value)
  if (!result) result = { black_win_rate: 0.5, white_win_rate: 0.5 }

  if (countForcedWins(board.value, BLACK) >= 2) {
    result = { black_win_rate: 1.0, white_win_rate: 0.0 }
  } else if (countForcedWins(board.value, WHITE) >= 2) {
    result = { black_win_rate: 0.0, white_win_rate: 1.0 }
  }

  analysis.value = result
  const last = moveHistory.value[moveHistory.value.length - 1]
  if (last) last.analysis = { ...result }
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
      row: m.row, col: m.col, player: m.player,
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

function handleResign() {
  if (gameOver.value) return
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

const playerLabel = computed(() => player.value === BLACK ? '黑棋' : '白棋')

onMounted(() => {
  if (player.value === WHITE) {
    triggerAIMove()
  }
})
</script>

<template>
  <div v-if="forbiddenMessage" class="forbidden-toast">{{ forbiddenMessage }}</div>

  <!-- DESKTOP -->
  <template v-if="!isMobile">
    <div class="ai-header">
      <span class="ai-badge">人机对战 · {{ difficultyLabel }}</span>
      <span class="ai-color">你执{{ playerLabel }}</span>
    </div>
    <div class="game-layout">
      <div class="left-column">
        <GameBoard
          :board="board"
          :current-turn="getStoneName(currentTurn)"
          :game-over="gameOver"
          :readonly="aiThinking || currentTurn !== player || gameOver"
          :last-move="lastMove"
          @place-stone="handlePlaceStone"
        />
        <div v-if="aiThinking" class="thinking-indicator">
          <span class="thinking-dot"></span>
          AI 思考中...
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
        <WinRatePanel
          :analysis="analysis"
          :loading="analyzing"
        />
        <button
          class="btn-action btn-analysis"
          :disabled="analyzing || gameOver"
          @click="handleRequestAnalysis"
        >
          {{ analyzing ? '分析中（约10-30秒）' : '刷新分析' }}
        </button>
        <div v-if="!gameOver" class="action-row">
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
      </div>
    </div>
  </template>

  <!-- MOBILE -->
  <template v-else>
    <div class="mobile-ai-layout">
      <div class="mobile-ai-header">
        <span class="ai-badge">人机 · {{ difficultyLabel }}</span>
        <span class="ai-color">你执{{ playerLabel }}</span>
        <div v-if="aiThinking" class="thinking-indicator-sm">
          <span class="thinking-dot"></span>
          AI思考中...
        </div>
      </div>

      <div class="mobile-ai-board">
        <GameBoard
          :board="board"
          :current-turn="getStoneName(currentTurn)"
          :game-over="gameOver"
          :readonly="aiThinking || currentTurn !== player || gameOver"
          :last-move="lastMove"
          :parent-width="mobileBoardWidth"
          @place-stone="handlePlaceStone"
        />
      </div>

      <div v-if="!gameOver" class="mobile-ai-actions">
        <button
          class="btn-action btn-resign"
          @click="handleResign"
        >认输</button>
        <button
          class="btn-action btn-analysis"
          :disabled="analyzing || gameOver"
          @click="handleRequestAnalysis"
        >
          {{ analyzing ? 'AI分析中...' : 'AI分析' }}
        </button>
      </div>

      <div class="mobile-ai-info">
        <GameInfo
          :current-turn="getStoneName(currentTurn)"
          :game-over="gameOver"
          :winner="winner"
          :game-result="gameResult"
          :black-move-count="blackMoveCount"
          :white-move-count="whiteMoveCount"
        />
        <WinRatePanel
          :analysis="analysis"
          :loading="analyzing"
        />
        <button
          v-if="gameOver"
          class="btn-action btn-restart"
          @click="resetGame"
        >再来一局</button>
      </div>
    </div>
  </template>
</template>

<style scoped>
.ai-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  width: 100%;
}
.ai-badge {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}
.ai-color {
  color: #aaa;
  font-size: 0.85rem;
}
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
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  color: #4ecdc4;
  font-size: 0.9rem;
  font-weight: 600;
}
.thinking-dot {
  width: 10px;
  height: 10px;
  background: #4ecdc4;
  border-radius: 50%;
  animation: pulse 0.6s ease-in-out infinite alternate;
}
@keyframes pulse {
  from { opacity: 0.3; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1.2); }
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
.btn-action:hover:not(:disabled) { opacity: 0.9; }
.btn-analysis { background: linear-gradient(135deg, #667eea, #764ba2); }
.btn-resign { background: #dc3545; }
.btn-restart { background: #533483; }
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

/* Mobile layout */
.mobile-ai-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}

.mobile-ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: rgba(22, 33, 62, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  flex-wrap: wrap;
}

.thinking-indicator-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4ecdc4;
  font-size: 0.8rem;
  font-weight: 600;
  margin-left: auto;
}

.thinking-indicator-sm .thinking-dot {
  width: 8px;
  height: 8px;
  background: #4ecdc4;
  border-radius: 50%;
  animation: pulse 0.6s ease-in-out infinite alternate;
}

.mobile-ai-board {
  display: flex;
  justify-content: center;
  width: 100%;
}

.mobile-ai-actions {
  display: flex;
  gap: 8px;
  width: 100%;
  justify-content: center;
}

.mobile-ai-actions .btn-action {
  flex: 0 1 auto;
  min-width: 100px;
  min-height: 44px;
  padding: 10px 20px;
}

.mobile-ai-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mobile-ai-info .btn-action {
  min-height: 44px;
}

</style>
