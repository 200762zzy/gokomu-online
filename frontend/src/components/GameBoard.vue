<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  board: Array,
  currentTurn: String,
  gameOver: Boolean,
  readonly: Boolean,
  replayLabel: Object,
  lastMove: Object,
  boardImage: String,
  parentWidth: { type: Number, default: 0 },
})

const emit = defineEmits(['placeStone'])

const BOARD_SIZE = 15

const CELL_SIZE = computed(() => {
  const availableWidth = props.parentWidth > 0 ? props.parentWidth : (window.innerWidth - 48)
  const maxFit = Math.floor((availableWidth - MARGIN * 2) / (BOARD_SIZE - 1))
  const desktopMax = 36
  return Math.max(20, Math.min(desktopMax, maxFit))
})
const MARGIN = 24
const canvasSize = computed(() => CELL_SIZE.value * (BOARD_SIZE - 1) + MARGIN * 2)

const canvasRef = ref(null)
let boardImageCache = null

function loadBoardImage(url) {
  if (!url) { boardImageCache = null; return }
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => { boardImageCache = img; drawBoard() }
  img.onerror = () => { boardImageCache = null; drawBoard() }
  img.src = url
}

function drawBoard() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  canvas.width = canvasSize.value * dpr
  canvas.height = canvasSize.value * dpr
  ctx.scale(dpr, dpr)

  const cs = canvasSize.value
  ctx.clearRect(0, 0, cs, cs)

  if (boardImageCache) {
    ctx.drawImage(boardImageCache, 0, 0, cs, cs)
  } else {
    ctx.fillStyle = '#d4a853'
    ctx.fillRect(0, 0, cs, cs)
  }

  const cell = CELL_SIZE.value
  const margin = MARGIN

  ctx.strokeStyle = '#8b6914'
  ctx.lineWidth = 1
  for (let i = 0; i < BOARD_SIZE; i++) {
    const pos = margin + i * cell
    ctx.beginPath()
    ctx.moveTo(margin, pos)
    ctx.lineTo(margin + (BOARD_SIZE - 1) * cell, pos)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(pos, margin)
    ctx.lineTo(pos, margin + (BOARD_SIZE - 1) * cell)
    ctx.stroke()
  }

  const stars = [[3,3], [3,11], [7,7], [11,3], [11,11]]
  ctx.fillStyle = '#8b6914'
  for (const [sr, sc] of stars) {
    ctx.beginPath()
    ctx.arc(margin + sc * cell, margin + sr * cell, Math.max(3, cell * 0.12), 0, Math.PI * 2)
    ctx.fill()
  }

  const board = props.board || []
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const val = board[r]?.[c]
      if (val === 0 || val === undefined) continue
      const x = margin + c * cell
      const y = margin + r * cell
      const radius = cell / 2 - 2

      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)

      if (val === 1) {
        const grad = ctx.createRadialGradient(x - 4, y - 4, 2, x, y, radius)
        grad.addColorStop(0, '#555')
        grad.addColorStop(1, '#111')
        ctx.fillStyle = grad
      } else {
        const grad = ctx.createRadialGradient(x - 4, y - 4, 2, x, y, radius)
        grad.addColorStop(0, '#fff')
        grad.addColorStop(1, '#ccc')
        ctx.fillStyle = grad
      }
      ctx.fill()
      ctx.strokeStyle = val === 1 ? '#000' : '#999'
      ctx.lineWidth = 1
      ctx.stroke()
    }
  }

  ctx.fillStyle = '#6b4f1a'
  ctx.font = Math.max(9, cell * 0.3) + 'px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  for (let i = 0; i < BOARD_SIZE; i++) {
    const pos = margin + i * cell
    ctx.fillText(String(i), margin - 14, pos)
    ctx.fillText(String(i), pos, margin - 14)
  }

  if (props.lastMove) {
    const lx = margin + props.lastMove.col * cell
    const ly = margin + props.lastMove.row * cell
    ctx.save()
    ctx.strokeStyle = '#ff2d55'
    ctx.lineWidth = Math.max(2, cell * 0.08)
    ctx.shadowColor = '#ff2d55'
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(lx, ly, cell / 2 + 1, 0, Math.PI * 2)
    ctx.stroke()
    ctx.restore()
  }

  if (props.replayLabel && props.replayLabel.text) {
    let lastRow = -1, lastCol = -1
    for (let r = BOARD_SIZE - 1; r >= 0; r--) {
      for (let c = BOARD_SIZE - 1; c >= 0; c--) {
        const v = board[r]?.[c]
        if (v === 1 || v === 2) { lastRow = r; lastCol = c; break }
      }
      if (lastRow !== -1) break
    }

    if (lastRow !== -1) {
      const x = margin + lastCol * cell
      const y = margin + lastRow * cell - cell * 0.75
      const label = props.replayLabel

      ctx.save()
      ctx.font = 'bold ' + Math.max(11, cell * 0.36) + 'px sans-serif'
      const text = label.text
      const metrics = ctx.measureText(text)
      const pad = 6
      const bw = metrics.width + pad * 2
      const bh = 22
      const bx = x - bw / 2
      const by = y - bh
      const r2 = 4

      ctx.fillStyle = label.color || '#ffd700'
      ctx.beginPath()
      ctx.moveTo(bx + r2, by)
      ctx.lineTo(bx + bw - r2, by)
      ctx.arcTo(bx + bw, by, bx + bw, by + r2, r2)
      ctx.lineTo(bx + bw, by + bh - r2)
      ctx.arcTo(bx + bw, by + bh, bx + bw - r2, by + bh, r2)
      ctx.lineTo(bx + r2, by + bh)
      ctx.arcTo(bx, by + bh, bx, by + bh - r2, r2)
      ctx.lineTo(bx, by + r2)
      ctx.arcTo(bx, by, bx + r2, by, r2)
      ctx.closePath()
      ctx.fill()

      ctx.fillStyle = ['#ffd700', '#e6a817', '#aaa'].includes(label.color) ? '#111' : '#fff'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(text, x, by + bh / 2)

      ctx.restore()
    }
  }
}

function getBoardPos(clientX, clientY) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasSize.value / rect.width
  const scaleY = canvasSize.value / rect.height
  const x = (clientX - rect.left) * scaleX
  const y = (clientY - rect.top) * scaleY
  const col = Math.round((x - MARGIN) / CELL_SIZE.value)
  const row = Math.round((y - MARGIN) / CELL_SIZE.value)
  if (row < 0 || row >= BOARD_SIZE || col < 0 || col >= BOARD_SIZE) return null
  return { row, col }
}

function handleClick(event) {
  if (props.gameOver || props.readonly) return
  const pos = getBoardPos(event.clientX, event.clientY)
  if (pos) emit('placeStone', pos)
}

function handleTouch(event) {
  if (props.gameOver || props.readonly) return
  event.preventDefault()
  const touch = event.touches[0]
  if (!touch) return
  const pos = getBoardPos(touch.clientX, touch.clientY)
  if (pos) emit('placeStone', pos)
}

onMounted(() => {
  loadBoardImage(props.boardImage)
  drawBoard()
})
watch(() => props.board, drawBoard, { deep: true })
watch(() => props.replayLabel, drawBoard, { deep: true })
watch(() => props.boardImage, (url) => { loadBoardImage(url); drawBoard() })
watch(canvasSize, drawBoard)
</script>

<template>
  <div class="board-wrapper">
    <div class="board-container">
      <canvas
        ref="canvasRef"
        :style="{
          width: canvasSize + 'px',
          height: canvasSize + 'px',
          cursor: (gameOver || readonly) ? 'default' : 'pointer',
          maxWidth: '100%',
          maxHeight: '100%',
        }"
        @click="handleClick"
        @touchstart="handleTouch"
      ></canvas>
    </div>
  </div>
</template>

<style scoped>
.board-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}

.board-container {
  max-width: 100%;
  overflow: hidden;
}

canvas {
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  touch-action: none;
}
</style>
