import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCcGameStore = defineStore('ccGame', () => {
  const currentRoomId = ref(null)
  const playerColor = ref('')
  const opponentName = ref('')
  const board = ref([])
  const currentTurn = ref('red')
  const myTurn = ref(false)
  const gameOver = ref(false)
  const winner = ref('')
  const moveHistory = ref([])
  const inCheck = ref('')
  const pendingGameState = ref(null)
  const isSpectator = ref(false)
  const opponentTitle = ref(null)
  const showOpponentEntry = ref(false)

  function reset() {
    currentRoomId.value = null
    playerColor.value = ''
    opponentName.value = ''
    board.value = []
    currentTurn.value = 'red'
    myTurn.value = false
    gameOver.value = false
    winner.value = ''
    moveHistory.value = []
    inCheck.value = ''
    pendingGameState.value = null
    isSpectator.value = false
    opponentTitle.value = null
    showOpponentEntry.value = false
  }

  return {
    currentRoomId, playerColor, opponentName,
    board, currentTurn, myTurn, gameOver, winner,
    moveHistory, inCheck, pendingGameState, isSpectator,
    opponentTitle, showOpponentEntry,
    reset,
  }
})
