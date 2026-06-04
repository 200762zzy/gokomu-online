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
  previewPos: Object,
})

const emit = defineEmits(['placeStone', 'confirmPlace', 'cancelPlace'])

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
let _widgetBounds = null

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

  if (props.previewPos) {
    const px = margin + props.previewPos.col * cell
    const py = margin + props.previewPos.row * cell
    const radius = cell / 2 - 2
    ctx.save()
    ctx.globalAlpha = 0.4
    ctx.beginPath()
    ctx.arc(px, py, radius, 0, Math.PI * 2)
    const grad = ctx.createRadialGradient(px - 4, py - 4, 2, px, py, radius)
    grad.addColorStop(0, '#888')
    grad.addColorStop(1, '#444')
    ctx.fillStyle = grad
    ctx.fill()
    ctx.restore()

    const isMobile = props.parentWidth > 0
    const bw = isMobile ? 80 : 56
    const bh = isMobile ? 40 : 28
    const btnW = isMobile ? 30 : 20
    const gap = isMobile ? 5 : 4
    const wx = px - bw / 2
    let wy = py - cell / 2 - bh - 4
    if (wy < margin) {
      wy = py + cell / 2 + 4
    }

    ctx.save()
    ctx.fillStyle = 'rgba(22, 33, 62, 0.95)'
    ctx.beginPath()
    const r2 = 6
    ctx.moveTo(wx + r2, wy)
    ctx.lineTo(wx + bw - r2, wy)
    ctx.arcTo(wx + bw, wy, wx + bw, wy + r2, r2)
    ctx.lineTo(wx + bw, wy + bh - r2)
    ctx.arcTo(wx + bw, wy + bh, wx + bw - r2, wy + bh, r2)
    ctx.lineTo(wx + r2, wy + bh)
    ctx.arcTo(wx, wy + bh, wx, wy + bh - r2, r2)
    ctx.lineTo(wx, wy + r2)
    ctx.arcTo(wx, wy, wx + r2, wy, r2)
    ctx.closePath()
    ctx.fill()

    const confirmX = wx + gap
    const confirmY = wy + gap
    const confirmW = btnW
    const confirmH = bh - gap * 2
    ctx.fillStyle = '#28a745'
    ctx.beginPath()
    const b1r = 4
    ctx.moveTo(confirmX + b1r, confirmY)
    ctx.lineTo(confirmX + confirmW - b1r, confirmY)
    ctx.arcTo(confirmX + confirmW, confirmY, confirmX + confirmW, confirmY + b1r, b1r)
    ctx.lineTo(confirmX + confirmW, confirmY + confirmH - b1r)
    ctx.arcTo(confirmX + confirmW, confirmY + confirmH, confirmX + confirmW - b1r, confirmY + confirmH, b1r)
    ctx.lineTo(confirmX + b1r, confirmY + confirmH)
    ctx.arcTo(confirmX, confirmY + confirmH, confirmX, confirmY + confirmH - b1r, b1r)
    ctx.lineTo(confirmX, confirmY + b1r)
    ctx.arcTo(confirmX, confirmY, confirmX + b1r, confirmY, b1r)
    ctx.closePath()
    ctx.fill()
    ctx.fillStyle = '#fff'
    ctx.font = 'bold ' + (isMobile ? 20 : 14) + 'px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('✓', confirmX + confirmW / 2, confirmY + confirmH / 2)

    const cancelX = wx + gap * 2 + btnW
    const cancelY = wy + gap
    const cancelW = btnW
    const cancelH = bh - gap * 2
    ctx.fillStyle = '#dc3545'
    ctx.beginPath()
    ctx.moveTo(cancelX + b1r, cancelY)
    ctx.lineTo(cancelX + cancelW - b1r, cancelY)
    ctx.arcTo(cancelX + cancelW, cancelY, cancelX + cancelW, cancelY + b1r, b1r)
    ctx.lineTo(cancelX + cancelW, cancelY + cancelH - b1r)
    ctx.arcTo(cancelX + cancelW, cancelY + cancelH, cancelX + cancelW - b1r, cancelY + cancelH, b1r)
    ctx.lineTo(cancelX + b1r, cancelY + cancelH)
    ctx.arcTo(cancelX, cancelY + cancelH, cancelX, cancelY + cancelH - b1r, b1r)
    ctx.lineTo(cancelX, cancelY + b1r)
    ctx.arcTo(cancelX, cancelY, cancelX + b1r, cancelY, b1r)
    ctx.closePath()
    ctx.fill()
    ctx.fillStyle = '#fff'
    ctx.fillText('✗', cancelX + cancelW / 2, cancelY + cancelH / 2)
    ctx.restore()

    _widgetBounds = { x: wx, y: wy, w: bw, h: bh, confirmX, confirmY, confirmW, confirmH }
  } else {
    _widgetBounds = null
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

function clientToCanvas(clientX, clientY) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasSize.value / rect.width
  const scaleY = canvasSize.value / rect.height
  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY,
  }
}

function getBoardPos(clientX, clientY) {
  const { x, y } = clientToCanvas(clientX, clientY)
  const col = Math.round((x - MARGIN) / CELL_SIZE.value)
  const row = Math.round((y - MARGIN) / CELL_SIZE.value)
  if (row < 0 || row >= BOARD_SIZE || col < 0 || col >= BOARD_SIZE) return null
  return { row, col }
}

function hitTestWidget(clientX, clientY) {
  if (!_widgetBounds) return null
  const { x, y } = clientToCanvas(clientX, clientY)
  const b = _widgetBounds
  if (x < b.x || x > b.x + b.w || y < b.y || y > b.y + b.h) return null
  if (x >= b.confirmX && x <= b.confirmX + b.confirmW &&
      y >= b.confirmY && y <= b.confirmY + b.confirmH) return 'confirm'
  return 'cancel'
}

function handleClick(event) {
  const widget = hitTestWidget(event.clientX, event.clientY)
  if (widget === 'confirm') { emit('confirmPlace'); return }
  if (widget === 'cancel') { emit('cancelPlace'); return }
  if (props.gameOver || props.readonly) return
  const pos = getBoardPos(event.clientX, event.clientY)
  if (pos) emit('placeStone', pos)
}

function handleTouch(event) {
  const touch = event.touches[0]
  if (!touch) return
  const widget = hitTestWidget(touch.clientX, touch.clientY)
  if (widget === 'confirm') { emit('confirmPlace'); return }
  if (widget === 'cancel') { emit('cancelPlace'); return }
  if (props.gameOver || props.readonly) return
  event.preventDefault()
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
watch(() => props.previewPos, drawBoard)
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
