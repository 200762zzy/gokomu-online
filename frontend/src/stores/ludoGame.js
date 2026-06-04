import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLudoGameStore = defineStore('ludoGame', () => {
  const currentRoomId = ref(null)
  const playerColor = ref('')
  const playerIndex = ref(-1)
  const players = ref([])
  const boardState = ref(null)
  const currentTurn = ref(0)
  const myTurn = ref(false)
  const gameOver = ref(false)
  const winner = ref('')
  const diceValue = ref(null)
  const playablePieces = ref([])
  const timerRemaining = ref(60)

  function reset() {
    currentRoomId.value = null
    playerColor.value = ''
    playerIndex.value = -1
    players.value = []
    boardState.value = null
    currentTurn.value = 0
    myTurn.value = false
    gameOver.value = false
    winner.value = ''
    diceValue.value = null
    playablePieces.value = []
    timerRemaining.value = 60
  }

  return {
    currentRoomId, playerColor, playerIndex, players,
    boardState, currentTurn, myTurn, gameOver, winner,
    diceValue, playablePieces, timerRemaining,
    reset,
  }
})
