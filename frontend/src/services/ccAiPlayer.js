import {
  ROWS, COLS, RED, BLACK,
  getPieceColor, getValidMoves, cloneBoard, makeMove,
} from './chineseChessLogic.js'

const PIECE_VALUES = { 1: 10000, 2: 200, 3: 200, 4: 400, 5: 900, 6: 450, 7: 100 }

let apiKey = ''
export function setCcApiKey(key) {
  apiKey = key
}

function getAllMoves(board, color) {
  const moves = []
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (getPieceColor(board[r][c]) !== color) continue
      const valid = getValidMoves(board, r, c)
      for (const m of valid) {
        moves.push({ fromR: r, fromC: c, toR: m.row, toC: m.col })
      }
    }
  }
  return moves
}

function evaluate(board, color) {
  let score = 0
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const val = board[r][c]
      if (val === 0) continue
      const type = Math.abs(val)
      const pc = getPieceColor(val)
      let value = PIECE_VALUES[type]
      if (type === 7) {
        const crossed = pc === RED ? r < 5 : r > 4
        value += crossed ? 40 + (4 - Math.abs(c - 4)) * 5 : -10
      } else if (type === 4) {
        const dr = Math.abs(r - (pc === RED ? 0 : 9))
        const dc = Math.abs(c - 4)
        value += Math.max(0, 6 - dr - dc) * 8
      } else if (type === 5) {
        value += (pc === RED ? (9 - r) : r) * 3
      } else if (type === 6) {
        value += (4 - Math.abs(c - 4)) * 3
      }
      if (pc === color) score += value
      else score -= value
    }
  }
  return score
}

function negamax(board, depth, alpha, beta, color) {
  const moves = getAllMoves(board, color)
  if (depth === 0 || moves.length === 0) {
    return evaluate(board, color)
  }

  moves.sort((a, b) => Math.abs(board[b.toR][b.toC]) - Math.abs(board[a.toR][a.toC]))

  let bestScore = -Infinity
  for (const m of moves) {
    const nb = cloneBoard(board)
    makeMove(nb, m.fromR, m.fromC, m.toR, m.toC)
    const enemy = color === RED ? BLACK : RED
    const score = -negamax(nb, depth - 1, -beta, -alpha, enemy)
    if (score > bestScore) bestScore = score
    if (score > alpha) alpha = score
    if (alpha >= beta) break
  }
  return bestScore
}

function negamaxRoot(board, depth, color) {
  const moves = getAllMoves(board, color)
  if (moves.length === 0) return null

  moves.sort((a, b) => Math.abs(board[b.toR][b.toC]) - Math.abs(board[a.toR][a.toC]))

  const INF = 10000000
  let bestMove = moves[0]
  let alpha = -INF
  const beta = INF

  for (const m of moves) {
    const nb = cloneBoard(board)
    makeMove(nb, m.fromR, m.fromC, m.toR, m.toC)
    const enemy = color === RED ? BLACK : RED
    const score = -negamax(nb, depth - 1, -beta, -alpha, enemy)
    if (score > alpha) {
      alpha = score
      bestMove = m
    }
  }
  return bestMove
}

export async function getCcAiMove(board, color, difficulty) {
  if (difficulty === 'hard' && apiKey) {
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 8000)
      const resp = await fetch('/api/cc/ai-move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          board,
          color: color === RED ? 'red' : 'black',
          api_key: apiKey,
        }),
        signal: controller.signal,
      })
      clearTimeout(timer)
      if (resp.ok) {
        const data = await resp.json()
        if (data.from_row >= 0) {
          return { row: data.from_row, col: data.from_col, toRow: data.to_row, toCol: data.to_col }
        }
      }
    } catch {}
  }

  const depth = { easy: 2, medium: 3, hard: 4 }[difficulty] || 3
  const result = negamaxRoot(board, depth, color)

  if (!result) return null

  return {
    row: result.fromR,
    col: result.fromC,
    toRow: result.toR,
    toCol: result.toC,
  }
}
