import { BOARD_SIZE, EMPTY, BLACK, WHITE, cloneBoard, checkWin, isValidMove, checkForbiddenMove } from './gameLogic.js'

const DIRS = [[1, 0], [0, 1], [1, 1], [1, -1]]

function countDir(board, row, col, dr, dc, player) {
  let c = 0
  for (let s = 1; s < 6; s++) {
    const r = row + dr * s, cc = col + dc * s
    if (r < 0 || r >= BOARD_SIZE || cc < 0 || cc >= BOARD_SIZE) break
    if (board[r][cc] !== player) break
    c++
  }
  return c
}

function evaluateCell(board, row, col, player) {
  board[row][col] = player
  let score = 0
  for (const [dr, dc] of DIRS) {
    const fwd = countDir(board, row, col, dr, dc, player)
    const bwd = countDir(board, row, col, -dr, -dc, player)
    const total = 1 + fwd + bwd
    const fr = row + dr * (fwd + 1), fc = col + dc * (fwd + 1)
    const br = row - dr * (bwd + 1), bc = col - dc * (bwd + 1)
    const openF = fr >= 0 && fr < BOARD_SIZE && fc >= 0 && fc < BOARD_SIZE && board[fr][fc] === EMPTY
    const openB = br >= 0 && br < BOARD_SIZE && bc >= 0 && bc < BOARD_SIZE && board[br][bc] === EMPTY
    const openEnds = (openF ? 1 : 0) + (openB ? 1 : 0)

    if (total >= 5) score += 100000
    else if (total === 4) score += openEnds === 2 ? 10000 : openEnds === 1 ? 5000 : 0
    else if (total === 3) score += openEnds === 2 ? 1000 : openEnds === 1 ? 500 : 0
    else if (total === 2) score += openEnds === 2 ? 100 : openEnds === 1 ? 50 : 0
  }
  board[row][col] = EMPTY
  return score
}

function getScoredMoves(board, aiPlayer) {
  const opponent = aiPlayer === BLACK ? WHITE : BLACK
  const moves = []

  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (!isValidMove(board, r, c)) continue
      if (aiPlayer === BLACK && checkForbiddenMove(board, r, c, BLACK)) continue

      const attack = evaluateCell(board, r, c, aiPlayer)
      const defense = evaluateCell(board, r, c, opponent)
      const center = (7 - Math.abs(r - 7)) + (7 - Math.abs(c - 7))
      moves.push({ row: r, col: c, score: attack * 1.1 + defense + center * 2 })
    }
  }

  return moves
}

function getCandidates(board, player, count) {
  const opponent = player === BLACK ? WHITE : BLACK
  const scored = []

  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (!isValidMove(board, r, c)) continue
      if (player === BLACK && checkForbiddenMove(board, r, c, BLACK)) continue

      let near = false
      for (const [dr, dc] of DIRS) {
        for (let d = 1; d <= 2; d++) {
          const nr = r + dr * d, nc = c + dc * d
          if (nr >= 0 && nr < BOARD_SIZE && nc >= 0 && nc < BOARD_SIZE && board[nr][nc] !== EMPTY) {
            near = true
            break
          }
          const nr2 = r - dr * d, nc2 = c - dc * d
          if (nr2 >= 0 && nr2 < BOARD_SIZE && nc2 >= 0 && nc2 < BOARD_SIZE && board[nr2][nc2] !== EMPTY) {
            near = true
            break
          }
        }
        if (near) break
      }
      if (!near) continue

      const att = evaluateCell(board, r, c, player)
      const def = evaluateCell(board, r, c, opponent)
      scored.push({ row: r, col: c, score: Math.max(att, def) })
    }
  }

  if (scored.length === 0) return []

  const maxCandidates = count || 15
  scored.sort((a, b) => b.score - a.score)
  return scored.slice(0, maxCandidates)
}

function evaluateBoard(board, player) {
  const opponent = player === BLACK ? WHITE : BLACK
  let score = 0

  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (board[r][c] === player) {
        for (const [dr, dc] of DIRS) {
          const fwd = countDir(board, r, c, dr, dc, player)
          const bwd = countDir(board, r, c, -dr, -dc, player)
          const total = 1 + fwd + bwd
          if (total >= 5) score += 100000
          else if (total >= 4) score += 5000
          else if (total >= 3) score += 500
          else if (total >= 2) score += 50
        }
      } else if (board[r][c] === opponent) {
        for (const [dr, dc] of DIRS) {
          const fwd = countDir(board, r, c, dr, dc, opponent)
          const bwd = countDir(board, r, c, -dr, -dc, opponent)
          const total = 1 + fwd + bwd
          if (total >= 5) score -= 100000
          else if (total >= 4) score -= 5000
          else if (total >= 3) score -= 500
          else if (total >= 2) score -= 50
        }
      }
    }
  }
  return score
}

function minimax(board, depth, alpha, beta, isMaximizing, aiPlayer, maxDepth) {
  if (depth === 0) {
    return { score: evaluateBoard(board, aiPlayer) }
  }

  const player = isMaximizing ? aiPlayer : (aiPlayer === BLACK ? WHITE : BLACK)
  const candidates = getCandidates(board, player, maxDepth === 2 ? 12 : 10)

  if (candidates.length === 0) {
    return { score: evaluateBoard(board, aiPlayer) }
  }

  let bestMove = candidates[0]

  if (isMaximizing) {
    let bestScore = -Infinity
    for (const m of candidates) {
      board[m.row][m.col] = player
      if (checkWin(board, m.row, m.col)) {
        board[m.row][m.col] = EMPTY
        return { row: m.row, col: m.col, score: 100000 + depth }
      }
      const result = minimax(board, depth - 1, alpha, beta, false, aiPlayer, maxDepth)
      board[m.row][m.col] = EMPTY
      if (result.score > bestScore) {
        bestScore = result.score
        bestMove = { row: m.row, col: m.col, score: bestScore }
      }
      alpha = Math.max(alpha, bestScore)
      if (beta <= alpha) break
    }
    return bestMove
  } else {
    let bestScore = Infinity
    for (const m of candidates) {
      board[m.row][m.col] = player
      if (checkWin(board, m.row, m.col)) {
        board[m.row][m.col] = EMPTY
        return { row: m.row, col: m.col, score: -100000 - depth }
      }
      const result = minimax(board, depth - 1, alpha, beta, true, aiPlayer, maxDepth)
      board[m.row][m.col] = EMPTY
      if (result.score < bestScore) {
        bestScore = result.score
        bestMove = { row: m.row, col: m.col, score: bestScore }
      }
      beta = Math.min(beta, bestScore)
      if (beta <= alpha) break
    }
    return bestMove
  }
}

export function getEasyMove(board, aiPlayer) {
  const moves = getScoredMoves(board, aiPlayer)
  if (moves.length === 0) return { row: 7, col: 7 }

  moves.sort((a, b) => b.score - a.score)
  const topScore = moves[0].score
  const candidates = moves.filter(m => m.score >= topScore * 0.85)

  const pick = candidates[Math.floor(Math.random() * candidates.length)]
  return pick
}

export function getMediumMove(board, aiPlayer) {
  const opponent = aiPlayer === BLACK ? WHITE : BLACK
  const scored = getScoredMoves(board, aiPlayer)
  if (scored.length === 0) return { row: 7, col: 7 }

  for (const m of scored) {
    if (m.score >= 100000) return m
  }
  for (const m of scored) {
    const def = evaluateCell(board, m.row, m.col, opponent)
    if (def >= 100000) return m
  }

  const totalStones = scored.length
  const depth = totalStones > 100 ? 1 : totalStones > 50 ? 2 : 3

  const boardCopy = cloneBoard(board)
  const result = minimax(boardCopy, depth, -Infinity, Infinity, true, aiPlayer, depth)
  if (result && typeof result.row === 'number' && typeof result.col === 'number') return result
  return scored[0]
}

let getHardMove = getMediumMove

export function setHardMove(fn) {
  getHardMove = fn
}

export function getAIMove(board, aiPlayer, difficulty) {
  if (difficulty === 'easy') return getEasyMove(board, aiPlayer)
  if (difficulty === 'medium') return getMediumMove(board, aiPlayer)
  return getHardMove(board, aiPlayer)
}
