<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ROWS, COLS, getPieceColor, getPieceName, RED, BLACK, getValidMoves } from '../services/chineseChessLogic.js'

const props = defineProps({
  board: Array,
  currentTurn: String,
  gameOver: Boolean,
  readonly: Boolean,
  lastMove: Object,
  selectedPos: Object,
  validMoves: Array,
  inCheck: String,
  parentWidth: { type: Number, default: 0 },
  flipped: Boolean,
  pendingMove: Object,
})

const emit = defineEmits(['cellClick', 'confirmMove', 'cancelMove'])

const MARGIN = 28
const CELL_SIZE = computed(() => {
  const availableWidth = props.parentWidth > 0 ? props.parentWidth : (window.innerWidth - 48)
  const maxFit = Math.floor((availableWidth - MARGIN * 2) / (COLS - 1))
  const desktopMax = 52
  return Math.max(24, Math.min(desktopMax, maxFit))
})
const canvasW = computed(() => CELL_SIZE.value * (COLS - 1) + MARGIN * 2)
const canvasH = computed(() => CELL_SIZE.value * (ROWS - 1) + MARGIN * 2)

const canvasRef = ref(null)
let _widgetBounds = null

function drawBoard() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  canvas.width = canvasW.value * dpr
  canvas.height = canvasH.value * dpr
  ctx.scale(dpr, dpr)

  const cw = canvasW.value
  const ch = canvasH.value
  const cell = CELL_SIZE.value
  const margin = MARGIN
  ctx.clearRect(0, 0, cw, ch)

  ctx.fillStyle = '#d4a853'
  ctx.fillRect(0, 0, cw, ch)

  ctx.strokeStyle = '#8b6914'
  ctx.lineWidth = 1

  for (let r = 0; r < ROWS; r++) {
    const y = margin + r * cell
    ctx.beginPath()
    ctx.moveTo(margin, y)
    ctx.lineTo(margin + (COLS - 1) * cell, y)
    ctx.stroke()
  }

  for (let c = 0; c < COLS; c++) {
    const x = margin + c * cell
    if (c === 0 || c === COLS - 1) {
      ctx.beginPath()
      ctx.moveTo(x, margin)
      ctx.lineTo(x, margin + (ROWS - 1) * cell)
      ctx.stroke()
    } else {
      ctx.beginPath()
      ctx.moveTo(x, margin)
      ctx.lineTo(x, margin + 4 * cell)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(x, margin + 5 * cell)
      ctx.lineTo(x, margin + (ROWS - 1) * cell)
      ctx.stroke()
    }
  }

  ctx.fillStyle = '#8b6914'
  ctx.font = 'bold ' + Math.max(11, cell * 0.45) + 'px serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  const riverY = margin + 4.5 * cell
  ctx.fillText('楚 河', margin + 2 * cell, riverY)
  ctx.fillText('漢 界', margin + 6 * cell, riverY)

  function drawPalace(r1, c1, r2, c2) {
    const x1 = margin + c1 * cell, y1 = margin + r1 * cell
    const x2 = margin + c2 * cell, y2 = margin + r2 * cell
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(x2, y1); ctx.lineTo(x1, y2); ctx.stroke()
  }
  drawPalace(0, 3, 2, 5)
  drawPalace(7, 3, 9, 5)

  const flipRow = (r) => props.flipped ? ROWS - 1 - r : r

  const board = props.board || []
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const val = board[r]?.[c]
      if (val === 0 || val === undefined) continue
      const x = margin + c * cell
      const y = margin + flipRow(r) * cell
      const radius = cell * 0.42
      const color = getPieceColor(val)
      const isSelected = props.selectedPos && props.selectedPos.row === r && props.selectedPos.col === c

      ctx.save()
      ctx.shadowColor = 'rgba(0,0,0,0.3)'
      ctx.shadowBlur = 4
      ctx.shadowOffsetY = 2

      const grad = ctx.createRadialGradient(x - radius * 0.2, y - radius * 0.2, 2, x, y, radius)
      if (color === RED) {
        grad.addColorStop(0, '#fff5e6')
        grad.addColorStop(0.7, '#f5deb3')
        grad.addColorStop(1, '#d4a853')
      } else {
        grad.addColorStop(0, '#e8e8e8')
        grad.addColorStop(0.7, '#aaa')
        grad.addColorStop(1, '#666')
      }
      ctx.beginPath()
      ctx.arc(x, y, radius, 0, Math.PI * 2)
      ctx.fillStyle = grad
      ctx.fill()

      ctx.shadowBlur = 0
      ctx.shadowOffsetY = 0
      ctx.strokeStyle = color === RED ? '#c0392b' : '#2c3e50'
      ctx.lineWidth = isSelected ? 3 : 1.5
      ctx.stroke()

      if (isSelected) {
        ctx.strokeStyle = '#ffd700'
        ctx.lineWidth = 3
        ctx.stroke()
        ctx.shadowColor = '#ffd700'
        ctx.shadowBlur = 10
        ctx.stroke()
        ctx.shadowBlur = 0
      }

      ctx.fillStyle = color === RED ? '#c0392b' : '#2c3e50'
      ctx.font = 'bold ' + Math.max(12, cell * 0.52) + 'px "KaiTi", "STKaiti", "SimSun", serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(getPieceName(val), x, y + 1)
      ctx.restore()
    }
  }

  const validMoves = props.validMoves || []
  for (const m of validMoves) {
    const x = margin + m.col * cell
    const y = margin + flipRow(m.row) * cell
    ctx.beginPath()
    ctx.arc(x, y, cell * 0.15, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(46, 204, 113, 0.7)'
    ctx.fill()
  }

  if (props.lastMove) {
    const lx = margin + props.lastMove.col * cell
    const ly = margin + flipRow(props.lastMove.row) * cell
    ctx.save()
    ctx.strokeStyle = '#ff2d55'
    ctx.lineWidth = Math.max(2, cell * 0.06)
    ctx.shadowColor = '#ff2d55'
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(lx, ly, cell * 0.44, 0, Math.PI * 2)
    ctx.stroke()
    ctx.restore()
  }

  if (props.inCheck === 'red') {
    const k = findKingPos(board, RED)
    if (k) drawCheckMarker(ctx, margin + k.col * cell, margin + flipRow(k.row) * cell, cell)
  } else if (props.inCheck === 'black') {
    const k = findKingPos(board, BLACK)
    if (k) drawCheckMarker(ctx, margin + k.col * cell, margin + flipRow(k.row) * cell, cell)
  }

  if (props.pendingMove) {
    const tr = props.pendingMove.to.row
    const tc = props.pendingMove.to.col
    const px = margin + tc * cell
    const py = margin + flipRow(tr) * cell
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
}

function findKingPos(board, color) {
  const target = color * 1
  for (let r = 0; r < ROWS; r++)
    for (let c = 0; c < COLS; c++)
      if (board[r]?.[c] === target) return { row: r, col: c }
  return null
}

function drawCheckMarker(ctx, x, y, cell) {
  ctx.save()
  ctx.strokeStyle = '#ff2d55'
  ctx.lineWidth = 3
  ctx.shadowColor = '#ff2d55'
  ctx.shadowBlur = 15
  ctx.beginPath()
  const r = cell * 0.48
  for (let i = 0; i < 8; i++) {
    const angle = (i * Math.PI * 2) / 8 - Math.PI / 2
    const radius = i % 2 === 0 ? r : r * 0.6
    const px = x + Math.cos(angle) * radius
    const py = y + Math.sin(angle) * radius
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)
  }
  ctx.closePath()
  ctx.stroke()
  ctx.restore()
}

function clientToCanvas(clientX, clientY) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvasW.value / rect.width
  const scaleY = canvasH.value / rect.height
  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY,
  }
}

function getBoardPos(clientX, clientY) {
  const { x, y } = clientToCanvas(clientX, clientY)
  const col = Math.round((x - MARGIN) / CELL_SIZE.value)
  let row = Math.round((y - MARGIN) / CELL_SIZE.value)
  if (props.flipped) row = ROWS - 1 - row
  if (row < 0 || row >= ROWS || col < 0 || col >= COLS) return null
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
  if (widget === 'confirm') { emit('confirmMove'); return }
  if (widget === 'cancel') { emit('cancelMove'); return }
  if (props.gameOver || props.readonly) return
  const pos = getBoardPos(event.clientX, event.clientY)
  if (pos) emit('cellClick', pos)
}

function handleTouch(event) {
  const touch = event.touches[0]
  if (!touch) return
  const widget = hitTestWidget(touch.clientX, touch.clientY)
  if (widget === 'confirm') { emit('confirmMove'); return }
  if (widget === 'cancel') { emit('cancelMove'); return }
  if (props.gameOver || props.readonly) return
  event.preventDefault()
  const pos = getBoardPos(touch.clientX, touch.clientY)
  if (pos) emit('cellClick', pos)
}

onMounted(drawBoard)
watch(() => props.board, drawBoard, { deep: true })
watch(() => props.selectedPos, drawBoard, { deep: true })
watch(() => props.validMoves, drawBoard, { deep: true })
watch(() => props.lastMove, drawBoard, { deep: true })
watch(() => props.inCheck, drawBoard)
watch(() => props.pendingMove, drawBoard, { deep: true })
watch([canvasW, canvasH], drawBoard)
</script>

<template>
  <div class="cc-board-wrapper">
    <div class="cc-board-container">
      <canvas
        ref="canvasRef"
        :style="{
          width: canvasW + 'px',
          height: canvasH + 'px',
          maxWidth: '100%',
          cursor: (gameOver || readonly) ? 'default' : 'pointer',
        }"
        @click="handleClick"
        @touchstart="handleTouch"
      ></canvas>
    </div>
  </div>
</template>

<style scoped>
.cc-board-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}
.cc-board-container {
  max-width: 100%;
  overflow: hidden;
}
canvas {
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  touch-action: none;
}
</style>
