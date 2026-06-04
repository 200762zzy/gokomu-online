<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import ChineseChessBoard from '../components/ChineseChessBoard.vue'
import {
  createBoard, cloneBoard, getPieceColor, getPieceName,
  getValidMoves, makeMove, isCheckmate, isStalemate, isInCheck,
  moveToNotation, RED, BLACK,
} from '../services/chineseChessLogic.js'
import { getCcAiMove, setCcApiKey } from '../services/ccAiPlayer.js'
import { audioManager } from '../services/audioManager.js'
import { useIsMobile } from '../composables/useIsMobile.js'

const { isMobile } = useIsMobile()
const mobileBoardWidth = computed(() => Math.min(window.innerWidth - 16, 560))

// AI mode
const aiMode = ref(false)
const aiDifficulty = ref('medium')
const aiColor = ref(BLACK)
const aiThinking = ref(false)
const showAiDialog = ref(false)

// URL query params for AI mode
import { useRoute } from 'vue-router'
const route = useRoute()
if (route.query.ai === 'true') {
  aiMode.value = true
  aiDifficulty.value = route.query.difficulty || 'medium'
  aiColor.value = route.query.color === 'red' ? RED : BLACK
}

const board = ref(createBoard())
const boardKey = ref(0)
const currentTurn = ref(RED)
const gameOver = ref(false)
const winner = ref('')
const gameResult = ref('')
const moveCount = ref(0)
const moveHistory = ref([])
const inCheck = ref('')
const drawOfferBy = ref('')
const forbiddenMessage = ref('')

const selectedPos = ref(null)
const validMoves = ref([])
const lastMove = ref(null)

const turnLabel = computed(() => currentTurn.value === RED ? '红方' : '黑方')
const winnerLabel = computed(() => {
  if (!winner.value) return ''
  return winner.value === 'red' ? '红方胜' : '黑方胜'
})

const isHumanTurn = computed(() => {
  if (!aiMode.value) return true
  return currentTurn.value !== aiColor.value
})

function resetGame() {
  board.value = createBoard()
  boardKey.value++
  currentTurn.value = RED
  gameOver.value = false
  winner.value = ''
  gameResult.value = ''
  moveCount.value = 0
  moveHistory.value = []
  inCheck.value = ''
  drawOfferBy.value = ''
  forbiddenMessage.value = ''
  selectedPos.value = null
  validMoves.value = []
  lastMove.value = null
  aiThinking.value = false
}

async function aiMove() {
  if (gameOver.value || !aiMode.value) return
  const result = await getCcAiMove(board.value, aiColor.value, aiDifficulty.value)
  if (!result || gameOver.value) return
  const apiKey = localStorage.getItem('deepseek_api_key') || ''
  setCcApiKey(apiKey)
  executeMove(result.row, result.col, result.toRow, result.toCol)
  aiThinking.value = false
}

watch(currentTurn, (val) => {
  if (aiMode.value && val === aiColor.value && !gameOver.value) {
    aiThinking.value = true
    setTimeout(() => aiMove(), 300)
  }
})

function handleCellClick(pos) {
  if (gameOver.value) return
  const { row, col } = pos
  const piece = board.value[row][col]
  const pieceColor = getPieceColor(piece)

  if (selectedPos.value) {
    const isOwnPiece = pieceColor === currentTurn.value
    const isValidTarget = validMoves.value.some(m => m.row === row && m.col === col)

    if (isValidTarget) {
      executeMove(selectedPos.value.row, selectedPos.value.col, row, col)
      return
    }

    if (isOwnPiece) {
      selectPiece(row, col)
      return
    }

    selectedPos.value = null
    validMoves.value = []
    return
  }

  if (pieceColor === currentTurn.value) {
    selectPiece(row, col)
  }
}

function selectPiece(row, col) {
  selectedPos.value = { row, col }
  validMoves.value = getValidMoves(board.value, row, col)
}

function executeMove(fromR, fromC, toR, toC) {
  const notation = moveToNotation(board.value, fromR, fromC, toR, toC)
  const captured = board.value[toR][toC]

  makeMove(board.value, fromR, fromC, toR, toC)

  lastMove.value = { row: toR, col: toC }
  moveCount.value++
  moveHistory.value.push({
    fromR, fromC, toR, toC,
    player: currentTurn.value,
    notation,
    captured: captured !== 0 ? getPieceName(captured) : null,
  })

  selectedPos.value = null
  validMoves.value = []

  if (captured) {
    audioManager.playChessCapture()
    audioManager.playChessEat()
  }
  audioManager.playChessMove()

  const enemy = currentTurn.value === RED ? BLACK : RED
  if (isCheckmate(board.value, enemy)) {
    gameOver.value = true
    winner.value = currentTurn.value === RED ? 'red' : 'black'
    gameResult.value = 'checkmate'
    inCheck.value = ''
    if (currentTurn.value === RED) audioManager.playWin()
    else audioManager.playLose()
    return
  }

  if (isStalemate(board.value, enemy)) {
    gameOver.value = true
    winner.value = currentTurn.value === RED ? 'red' : 'black'
    gameResult.value = 'stalemate'
    inCheck.value = ''
    if (currentTurn.value === RED) audioManager.playWin()
    else audioManager.playLose()
    return
  }

  currentTurn.value = enemy

  if (isInCheck(board.value, enemy)) {
    inCheck.value = enemy === RED ? 'red' : 'black'
    audioManager.playChessCheck()
  } else {
    inCheck.value = ''
  }
}

function handleUndo() {
  if (moveCount.value < 2 || gameOver.value) return
  const m2 = moveHistory.value.pop()
  const m1 = moveHistory.value.pop()
  if (!m2 || !m1) return
  board.value[m2.fromR][m2.fromC] = board.value[m2.toR][m2.toC]
  board.value[m2.toR][m2.toC] = 0
  board.value[m1.fromR][m1.fromC] = board.value[m1.toR][m1.toC]
  board.value[m1.toR][m1.toC] = 0
  moveCount.value -= 2
  currentTurn.value = m1.player
  lastMove.value = moveCount.value > 0
    ? { row: moveHistory.value[moveCount.value - 1].toR, col: moveHistory.value[moveCount.value - 1].toC }
    : null
  selectedPos.value = null
  validMoves.value = []
  inCheck.value = isInCheck(board.value, currentTurn.value) ? (currentTurn.value === RED ? 'red' : 'black') : ''
}

function handleResign() {
  if (gameOver.value) return
  gameOver.value = true
  winner.value = currentTurn.value === RED ? 'black' : 'red'
  gameResult.value = 'resign'
  if (currentTurn.value !== RED) audioManager.playWin()
  else audioManager.playLose()
}

function handleDrawRequest() {
  if (gameOver.value || drawOfferBy.value) return
  drawOfferBy.value = turnLabel.value
}

function handleDrawResponse(accept) {
  if (accept) {
    gameOver.value = true
    winner.value = ''
    gameResult.value = 'draw'
  }
  drawOfferBy.value = ''
}

function startAiGame() {
  aiMode.value = true
  showAiDialog.value = false
  resetGame()
  const apiKey = localStorage.getItem('deepseek_api_key') || ''
  setCcApiKey(apiKey)
}
</script>

<template>
  <div class="cc-local-container">
    <div class="turn-indicator" :class="{ 'red-turn': currentTurn === RED, 'black-turn': currentTurn === BLACK }">
      <template v-if="aiThinking">AI 思考中<span class="thinking-dots"></span></template>
      <template v-else>{{ turnLabel }}走棋</template>
      <span v-if="inCheck" class="check-badge">将军!</span>
      <span v-if="aiMode && !gameOver" class="ai-badge">AI</span>
    </div>

    <div v-if="forbiddenMessage" class="forbidden-toast">{{ forbiddenMessage }}</div>

    <template v-if="!isMobile">
      <div class="game-layout">
        <div class="left-column">
          <ChineseChessBoard
            :key="boardKey"
            :board="board"
            :current-turn="currentTurn === RED ? 'red' : 'black'"
            :game-over="gameOver"
            :readonly="aiThinking || (!isHumanTurn)"
            :last-move="lastMove"
            :selected-pos="selectedPos"
            :valid-moves="validMoves"
            :in-check="inCheck"
            @cell-click="handleCellClick"
          />
        </div>
        <div class="right-column">
          <div class="info-panel">
            <div class="info-row"><span class="info-label">回合</span><span>{{ Math.floor(moveCount / 2) + 1 }}</span></div>
            <div class="info-row"><span class="info-label">走法数</span><span>{{ moveCount }}</span></div>
            <div v-if="gameOver" class="game-result">{{ winnerLabel }}{{ gameResult === 'draw' ? '和棋' : '' }}</div>
          </div>

          <div class="move-list">
            <div class="move-list-title">走法记录</div>
            <div class="move-scroll">
              <div v-for="(m, i) in moveHistory" :key="i" class="move-item">
                <span class="move-num">{{ Math.floor(i / 2) + 1 }}{{ i % 2 === 0 ? '.' : '...' }}</span>
                <span :class="['move-text', m.player === RED ? 'red-text' : 'black-text']">{{ m.notation }}</span>
                <span v-if="m.captured" class="capture-badge">吃{{ m.captured }}</span>
              </div>
            </div>
          </div>

          <template v-if="!gameOver">
            <div class="action-row">
            <button class="btn-action btn-undo" :disabled="moveCount < 2 || aiMode" @click="handleUndo">悔棋</button>
              <button class="btn-action btn-draw" :disabled="drawOfferBy !== '' || aiMode" @click="handleDrawRequest">求和</button>
              <button class="btn-action btn-resign" @click="handleResign">认输</button>
            </div>
          </template>
          <template v-else>
            <button class="btn-action btn-restart" @click="resetGame">再来一局</button>
          </template>
          <button class="btn-action btn-ai" @click="showAiDialog = true">
            {{ aiMode ? `AI 对战 (${aiDifficulty === 'easy' ? '初级' : aiDifficulty === 'medium' ? '中级' : '高级'})` : 'AI 对手' }}
          </button>

          <div class="move-list">
            <div class="move-list-title">走法记录</div>
            <div class="move-scroll">
              <div v-for="(m, i) in moveHistory" :key="i" class="move-item">
                <span class="move-num">{{ Math.floor(i / 2) + 1 }}{{ i % 2 === 0 ? '.' : '...' }}</span>
                <span :class="['move-text', m.player === RED ? 'red-text' : 'black-text']">{{ m.notation }}</span>
                <span v-if="m.captured" class="capture-badge">吃{{ m.captured }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="mobile-layout">
        <ChineseChessBoard
          :key="boardKey"
          :board="board"
          :current-turn="currentTurn === RED ? 'red' : 'black'"
          :game-over="gameOver"
          :readonly="aiThinking || (!isHumanTurn)"
          :last-move="lastMove"
          :selected-pos="selectedPos"
          :valid-moves="validMoves"
          :in-check="inCheck"
          :parent-width="mobileBoardWidth"
          @cell-click="handleCellClick"
        />

        <div class="mobile-info">
          <div class="info-panel">
            <div class="info-row"><span class="info-label">回合</span><span>{{ Math.floor(moveCount / 2) + 1 }}</span></div>
            <div v-if="gameOver" class="game-result">{{ winnerLabel || '和棋' }}</div>
          </div>

          <template v-if="!gameOver">
            <div class="action-row">
              <button class="btn-action btn-undo" :disabled="moveCount < 2 || aiMode" @click="handleUndo">悔棋</button>
              <button class="btn-action btn-draw" :disabled="drawOfferBy !== '' || aiMode" @click="handleDrawRequest">求和</button>
              <button class="btn-action btn-resign" @click="handleResign">认输</button>
            </div>
          </template>
          <template v-else>
            <button class="btn-action btn-restart" @click="resetGame">再来一局</button>
          </template>
          <button class="btn-action btn-ai" @click="showAiDialog = true">
            {{ aiMode ? `AI ${aiDifficulty === 'easy' ? '初级' : aiDifficulty === 'medium' ? '中级' : '高级'}` : 'AI 对手' }}
          </button>

          <div class="move-list">
            <div class="move-list-title">走法记录</div>
            <div class="move-scroll">
              <div v-for="(m, i) in moveHistory" :key="i" class="move-item">
                <span class="move-num">{{ Math.floor(i / 2) + 1 }}{{ i % 2 === 0 ? '.' : '...' }}</span>
                <span :class="['move-text', m.player === RED ? 'red-text' : 'black-text']">{{ m.notation }}</span>
                <span v-if="m.captured" class="capture-badge">吃{{ m.captured }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="showAiDialog" class="overlay" @click.self="showAiDialog = false">
        <div class="dialog">
          <h3>AI 对战设置</h3>
          <div class="dialog-row">
            <label>难度</label>
            <div class="btn-group">
              <button :class="['btn-group-item', { active: aiDifficulty === 'easy' }]" @click="aiDifficulty = 'easy'">初级</button>
              <button :class="['btn-group-item', { active: aiDifficulty === 'medium' }]" @click="aiDifficulty = 'medium'">中级</button>
              <button :class="['btn-group-item', { active: aiDifficulty === 'hard' }]" @click="aiDifficulty = 'hard'">高级</button>
            </div>
          </div>
          <div class="dialog-row">
            <label>执棋</label>
            <div class="btn-group">
              <button :class="['btn-group-item', { active: aiColor === RED }]" @click="aiColor = RED">红方（先手）</button>
              <button :class="['btn-group-item', { active: aiColor === BLACK }]" @click="aiColor = BLACK">黑方（后手）</button>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="btn-cancel" @click="showAiDialog = false">取消</button>
            <button class="btn-start" @click="startAiGame">开始</button>
          </div>
        </div>
      </div>
      <div v-if="drawOfferBy" class="draw-overlay" @click.self="handleDrawResponse(false)">
        <div class="draw-dialog">
          <p>{{ drawOfferBy }}请求和棋，是否接受？</p>
          <div class="draw-buttons">
            <button class="btn-draw-accept" @click="handleDrawResponse(true)">接受</button>
            <button class="btn-draw-reject" @click="handleDrawResponse(false)">拒绝</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.cc-local-container {
  width: 100%;
}

.turn-indicator {
  text-align: center;
  font-size: 1.1rem;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: background 0.2s;
}
.turn-indicator.red-turn {
  background: rgba(192, 57, 43, 0.15);
  color: #e74c3c;
}
.turn-indicator.black-turn {
  background: rgba(44, 62, 80, 0.15);
  color: #95a5a6;
}
.check-badge {
  display: inline-block;
  background: #ff2d55;
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-left: 8px;
  animation: pulse 0.8s ease infinite alternate;
}
@keyframes pulse {
  from { opacity: 0.7; transform: scale(1); }
  to { opacity: 1; transform: scale(1.05); }
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
  gap: 12px;
  min-width: 220px;
}

.info-panel {
  background: rgba(22, 33, 62, 0.85);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 12px 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  padding: 4px 0;
}
.info-label { color: #888; }
.game-result {
  text-align: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffd700;
  padding: 8px 0;
}

.move-list {
  background: rgba(22, 33, 62, 0.85);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 12px;
  flex: 1;
  min-height: 200px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
}
.move-list-title {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 8px;
}
.move-scroll {
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-content: flex-start;
}
.move-item {
  font-size: 0.85rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255,255,255,0.03);
  white-space: nowrap;
}
.move-num {
  color: #666;
}
.move-text.red-text { color: #e74c3c; }
.move-text.black-text { color: #95a5a6; }
.capture-badge {
  font-size: 0.7rem;
  color: #ffd700;
  margin-left: 2px;
}

.action-row {
  display: flex;
  gap: 8px;
}
.btn-action {
  flex: 1;
  padding: 10px 14px;
  border: none;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
}
.btn-action:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-action:hover:not(:disabled) { opacity: 0.9; }
.btn-undo { background: #e6a817; }
.btn-draw { background: #17a2b8; }
.btn-resign { background: #dc3545; }
.btn-restart { background: #533483; }
.btn-ai { background: linear-gradient(135deg, #667eea, #764ba2); }

.ai-badge {
  display: inline-block;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-left: 8px;
}

.thinking-dots::after {
  content: '...';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { content: '.'; }
  40% { content: '..'; }
  60%, 100% { content: '...'; }
}

.overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.dialog {
  background: rgba(26,26,62,0.95);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 28px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.5);
  max-width: 380px;
  width: 90%;
}
.dialog h3 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  color: #eee;
  text-align: center;
}
.dialog-row {
  margin-bottom: 16px;
}
.dialog-row label {
  display: block;
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 8px;
}
.btn-group {
  display: flex;
  gap: 8px;
}
.btn-group-item {
  flex: 1;
  padding: 8px 6px;
  border: 1px solid #444;
  background: #0f3460;
  color: #aaa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.15s;
}
.btn-group-item.active {
  border-color: #667eea;
  background: #1a1a4e;
  color: #667eea;
}
.dialog-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}
.btn-cancel, .btn-start {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  color: #fff;
}
.btn-cancel { background: #6c757d; }
.btn-start { background: #28a745; }

.mobile-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}
.mobile-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
}
</style>

<style>
.draw-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6);
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
  box-shadow: 0 8px 30px rgba(0,0,0,0.5);
  max-width: 320px;
}
.draw-dialog p { font-size: 1.1rem; margin-bottom: 24px; color: #eee; }
.draw-buttons { display: flex; gap: 12px; justify-content: center; }
.draw-buttons button {
  padding: 10px 28px; border: none; border-radius: 8px;
  font-size: 1rem; font-weight: 600; cursor: pointer; color: #fff;
}
.btn-draw-accept { background: #28a745; }
.btn-draw-reject { background: #6c757d; }
</style>
