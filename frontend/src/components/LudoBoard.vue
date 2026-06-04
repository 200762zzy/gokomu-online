<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import {
  BOARD_SIZE, MAIN_PATH, HOME_STRETCH, START_ZONES,
  PLAYER_COLORS, TOTAL_MAIN_CELLS, HOME_STRETCH_LEN,
  absoluteToView, getPlayerViewIndex, getColorHex,
} from '../services/ludoLogic.js'

const props = defineProps({
  boardState: { type: Object, default: null },
  playerColor: { type: String, default: 'red' },
  playablePieces: { type: Array, default: () => [] },
  gameOver: { type: Boolean, default: false },
  parentWidth: { type: Number, default: null },
})

const emit = defineEmits(['pieceClick'])

const canvasRef = ref(null)
const CELL_SIZE = ref(36)
const MARGIN = 20
const BOARD_PX = computed(() => BOARD_SIZE * CELL_SIZE.value + MARGIN * 2)

const viewIndex = computed(() => getPlayerViewIndex(props.playerColor))
const boardImg = ref(null)
const pieceImgs = ref({})
const imagesReady = ref(false)

function updateCellSize() {
  const maxW = props.parentWidth || window.innerWidth - 32
  let size = Math.min(36, Math.floor((maxW - MARGIN * 2) / BOARD_SIZE))
  size = Math.max(20, Math.min(48, size))
  CELL_SIZE.value = size
}

function toCanvas(coord) {
  const [r, c] = absoluteToView(coord, viewIndex.value)
  return { x: MARGIN + c * CELL_SIZE.value, y: MARGIN + r * CELL_SIZE.value }
}

function canvasToBoard(cx, cy) {
  const r = Math.round((cy - MARGIN) / CELL_SIZE.value)
  const c = Math.round((cx - MARGIN) / CELL_SIZE.value)
  const vr = Math.max(0, Math.min(BOARD_SIZE - 1, r))
  const vc = Math.max(0, Math.min(BOARD_SIZE - 1, c))
  return { viewRow: vr, viewCol: vc }
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const w = BOARD_PX.value
  const h = BOARD_PX.value
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'
  canvas.width = w * dpr
  canvas.height = h * dpr
  ctx.scale(dpr, dpr)

  const cs = CELL_SIZE.value
  const mg = MARGIN

  ctx.fillStyle = '#c8a25c'
  ctx.fillRect(0, 0, w, h)

  // Board PNG image (rotated for player view)
  if (boardImg.value) {
    ctx.save()
    const cx = mg + BOARD_SIZE * cs / 2
    const cy = mg + BOARD_SIZE * cs / 2
    ctx.translate(cx, cy)
    ctx.rotate(viewIndex.value * Math.PI / 2)
    const boardSize = BOARD_SIZE * cs
    ctx.drawImage(boardImg.value, -boardSize / 2, -boardSize / 2, boardSize, boardSize)
    ctx.restore()
  }

  // Home stretches (colored overlay on board image)
  for (let p = 0; p < 4; p++) {
    const hex = getColorHex(PLAYER_COLORS[p])
    ctx.fillStyle = hex + '40'
    for (const pos of HOME_STRETCH[p]) {
      const { x, y } = toCanvas(pos)
      ctx.fillRect(x - cs / 2 + 2, y - cs / 2 + 2, cs - 4, cs - 4)
    }
  }

  if (!props.boardState) return

  const state = props.boardState
  const playableSet = new Set(props.playablePieces)

  for (let p = 0; p < 4; p++) {
    const pieces = state.pieces[p]
    if (!pieces) continue
    const color = PLAYER_COLORS[p]
    const pieceImg = pieceImgs.value[color]

    for (let pi = 0; pi < pieces.length; pi++) {
      const piece = pieces[pi]
      let drawPos = null

      if (piece.state === 'home') {
        const homePos = START_ZONES[p][pi]
        const vp = toCanvas(homePos)
        drawPos = { x: vp.x, y: vp.y }
      } else if (piece.state === 'active') {
        if (piece.pos) {
          const vp = toCanvas(piece.pos)
          drawPos = { x: vp.x, y: vp.y }
        }
      } else if (piece.state === 'finished') {
        if (HOME_STRETCH[p]) {
          const vp = toCanvas(HOME_STRETCH[p][HOME_STRETCH_LEN - 1])
          drawPos = { x: vp.x, y: vp.y }
        }
      }

      if (!drawPos) continue

      const isPlayable = p === getPlayerViewIndex(props.playerColor) && playableSet.has(pi)

      if (isPlayable) {
        ctx.shadowColor = '#fff'
        ctx.shadowBlur = 12
      }

      const pSize = cs * 0.38
      if (pieceImg) {
        ctx.drawImage(pieceImg, drawPos.x - pSize, drawPos.y - pSize, pSize * 2, pSize * 2)
      }

      ctx.shadowBlur = 0

      ctx.fillStyle = '#fff'
      ctx.font = `bold ${pSize * 0.7}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(pi + 1, drawPos.x, drawPos.y)
    }
  }
}

function handleClick(e) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const { viewRow, viewCol } = canvasToBoard(x, y)

  // Find clicked piece
  const state = props.boardState
  if (!state) return
  for (let pi = 0; pi < 4; pi++) {
    const pieces = state.pieces[props.playerColor]
    if (!pieces) continue
    for (let i = 0; i < pieces.length; i++) {
      const piece = pieces[i]
      let pos = null
      if (piece.state === 'home') pos = START_ZONES[getPlayerViewIndex(props.playerColor)][i]
      else if (piece.state === 'active' && piece.pos) pos = piece.pos
      else continue
      const [vr, vc] = absoluteToView(pos, viewIndex.value)
      if (Math.abs(vr - viewRow) <= 0.5 && Math.abs(vc - viewCol) <= 0.5) {
        emit('pieceClick', i)
        return
      }
    }
  }
}

let resizeHandler = null

function loadImages() {
  const board = new Image()
  board.onload = () => { boardImg.value = board; imagesReady.value = true; nextTick(draw) }
  board.src = '/assets/ludo/board.png'

  for (const color of ['red', 'blue', 'green', 'yellow']) {
    const img = new Image()
    img.onload = () => { pieceImgs.value[color] = img; nextTick(draw) }
    img.src = `/assets/ludo/piece-${color}.png`
  }
}

onMounted(() => {
  updateCellSize()
  loadImages()
  resizeHandler = () => updateCellSize()
  window.addEventListener('resize', resizeHandler)
  nextTick(draw)
})

onUnmounted(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})

watch(() => [props.boardState, props.playerColor, props.playablePieces, props.parentWidth], () => {
  if (props.parentWidth) updateCellSize()
  nextTick(draw)
})

watch(CELL_SIZE, draw)
</script>

<template>
  <canvas
    ref="canvasRef"
    class="ludo-board-canvas"
    @click="handleClick"
  />
</template>

<style scoped>
.ludo-board-canvas {
  border-radius: 8px;
  display: block;
  max-width: 100%;
}
</style>
