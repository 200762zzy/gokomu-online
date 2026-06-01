<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  board: Array,
  currentTurn: String,
  gameOver: Boolean,
  readonly: Boolean,
  replayLabel: Object,
  lastMove: Object,
})

const emit = defineEmits(['placeStone'])

const BOARD_SIZE = 15
const CELL_SIZE = 36
const MARGIN = 24
const canvasSize = CELL_SIZE * (BOARD_SIZE - 1) + MARGIN * 2

const canvasRef = ref(null)

function drawBoard() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  canvas.width = canvasSize * dpr
  canvas.height = canvasSize * dpr
  ctx.scale(dpr, dpr)

  ctx.clearRect(0, 0, canvasSize, canvasSize)

  ctx.fillStyle = '#d4a853'
  ctx.fillRect(0, 0, canvasSize, canvasSize)

  ctx.strokeStyle = '#8b6914'
  ctx.lineWidth = 1
  for (let i = 0; i < BOARD_SIZE; i++) {
    const pos = MARGIN + i * CELL_SIZE
    ctx.beginPath()
    ctx.moveTo(MARGIN, pos)
    ctx.lineTo(MARGIN + (BOARD_SIZE - 1) * CELL_SIZE, pos)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(pos, MARGIN)
    ctx.lineTo(pos, MARGIN + (BOARD_SIZE - 1) * CELL_SIZE)
    ctx.stroke()
  }

  const stars = [[3,3], [3,11], [7,7], [11,3], [11,11]]
  ctx.fillStyle = '#8b6914'
  for (const [sr, sc] of stars) {
    ctx.beginPath()
    ctx.arc(MARGIN + sc * CELL_SIZE, MARGIN + sr * CELL_SIZE, 4, 0, Math.PI * 2)
    ctx.fill()
  }

  const board = props.board || []
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const val = board[r]?.[c]
      if (val === 0 || val === undefined) continue
      const x = MARGIN + c * CELL_SIZE
      const y = MARGIN + r * CELL_SIZE
      const radius = CELL_SIZE / 2 - 2

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
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  for (let i = 0; i < BOARD_SIZE; i++) {
    const pos = MARGIN + i * CELL_SIZE
    ctx.fillText(String(i), MARGIN - 14, pos)
    ctx.fillText(String(i), pos, MARGIN - 14)
  }

  if (props.lastMove) {
    const lx = MARGIN + props.lastMove.col * CELL_SIZE
    const ly = MARGIN + props.lastMove.row * CELL_SIZE
    ctx.save()
    ctx.strokeStyle = '#ff2d55'
    ctx.lineWidth = 3
    ctx.shadowColor = '#ff2d55'
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(lx, ly, CELL_SIZE / 2 + 1, 0, Math.PI * 2)
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
      const x = MARGIN + lastCol * CELL_SIZE
      const y = MARGIN + lastRow * CELL_SIZE - CELL_SIZE * 0.75
      const label = props.replayLabel

      ctx.save()
      ctx.font = 'bold 13px sans-serif'
      const text = label.text
      const metrics = ctx.measureText(text)
      const pad = 6
      const bw = metrics.width + pad * 2
      const bh = 22
      const bx = x - bw / 2
      const by = y - bh
      const r = 4

      ctx.fillStyle = label.color || '#ffd700'
      ctx.beginPath()
      ctx.moveTo(bx + r, by)
      ctx.lineTo(bx + bw - r, by)
      ctx.arcTo(bx + bw, by, bx + bw, by + r, r)
      ctx.lineTo(bx + bw, by + bh - r)
      ctx.arcTo(bx + bw, by + bh, bx + bw - r, by + bh, r)
      ctx.lineTo(bx + r, by + bh)
      ctx.arcTo(bx, by + bh, bx, by + bh - r, r)
      ctx.lineTo(bx, by + r)
      ctx.arcTo(bx, by, bx + r, by, r)
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

function handleClick(event) {
  if (props.gameOver || props.readonly) return

  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const col = Math.round((x - MARGIN) / CELL_SIZE)
  const row = Math.round((y - MARGIN) / CELL_SIZE)

  if (row < 0 || row >= BOARD_SIZE || col < 0 || col >= BOARD_SIZE) return

  emit('placeStone', { row, col })
}

onMounted(drawBoard)
watch(() => props.board, drawBoard, { deep: true })
watch(() => props.replayLabel, drawBoard, { deep: true })
</script>

<template>
  <div class="board-wrapper">
    <canvas
      ref="canvasRef"
      :style="{ width: canvasSize + 'px', height: canvasSize + 'px', cursor: (gameOver || readonly) ? 'default' : 'pointer' }"
      @click="handleClick"
    ></canvas>
  </div>
</template>

<style scoped>
.board-wrapper {
  display: flex;
  justify-content: center;
}

canvas {
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
</style>
