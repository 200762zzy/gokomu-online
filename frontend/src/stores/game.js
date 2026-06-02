import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGameStore = defineStore('game', () => {
  const currentRoomId = ref(null)
  const playerColor = ref('')
  const opponentName = ref('')
  const opponentTitle = ref(null)
  const board = ref([])
  const currentTurn = ref('black')
  const myTurn = ref(false)
  const gameOver = ref(false)
  const winner = ref('')
  const gameResult = ref('')
  const moveHistory = ref([])
  const moveAnalysisHistory = ref([])
  const analysis = ref(null)
  const analyzing = ref(false)
  const blackMoveCount = ref(0)
  const whiteMoveCount = ref(0)
  const waiting = ref(false)
  const lastMove = ref(null)
  const isSpectator = ref(false)
  const pendingGameState = ref(null)

  const moveCount = computed(() => moveHistory.value.length)

  function reset() {
    currentRoomId.value = null
    playerColor.value = ''
    opponentName.value = ''
    opponentTitle.value = null
    board.value = []
    currentTurn.value = 'black'
    myTurn.value = false
    gameOver.value = false
    winner.value = ''
    gameResult.value = ''
    moveHistory.value = []
    moveAnalysisHistory.value = []
    analysis.value = null
    analyzing.value = false
    blackMoveCount.value = 0
    whiteMoveCount.value = 0
    waiting.value = false
    lastMove.value = null
    isSpectator.value = false
    pendingGameState.value = null
  }

  return {
    currentRoomId, playerColor, opponentName, opponentTitle,
    board, currentTurn, myTurn, gameOver,
    winner, gameResult, moveHistory, moveAnalysisHistory,
    analysis, analyzing, blackMoveCount, whiteMoveCount,
    waiting, lastMove, moveCount, isSpectator, pendingGameState,
    reset,
  }
})
