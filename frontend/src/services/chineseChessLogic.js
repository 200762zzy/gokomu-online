export const EMPTY = 0
export const RED = 1
export const BLACK = -1

export const ROWS = 10
export const COLS = 9

export const KING = 1
export const ADVISOR = 2
export const ELEPHANT = 3
export const HORSE = 4
export const CHARIOT = 5
export const CANNON = 6
export const SOLDIER = 7

export const PIECE_NAMES = {
  1: { red: '帥', black: '將' },
  2: { red: '仕', black: '士' },
  3: { red: '相', black: '象' },
  4: { red: '馬', black: '馬' },
  5: { red: '車', black: '車' },
  6: { red: '砲', black: '炮' },
  7: { red: '兵', black: '卒' },
}

export function getPieceType(val) {
  return Math.abs(val)
}

export function getPieceColor(val) {
  if (val > 0) return RED
  if (val < 0) return BLACK
  return EMPTY
}

export function getPieceName(val) {
  if (val === 0) return ''
  const type = getPieceType(val)
  const color = getPieceColor(val)
  const nameMap = PIECE_NAMES[type]
  return nameMap ? nameMap[color === RED ? 'red' : 'black'] : '?'
}

export function createBoard() {
  const b = Array.from({ length: ROWS }, () => Array(COLS).fill(0))
  const R = RED, B = BLACK
  const p = (color, type) => color * type
  b[0] = [p(B,CHARIOT), p(B,HORSE), p(B,ELEPHANT), p(B,ADVISOR), p(B,KING), p(B,ADVISOR), p(B,ELEPHANT), p(B,HORSE), p(B,CHARIOT)]
  b[2] = [0, p(B,CANNON), 0, 0, 0, 0, 0, p(B,CANNON), 0]
  b[3] = [p(B,SOLDIER), 0, p(B,SOLDIER), 0, p(B,SOLDIER), 0, p(B,SOLDIER), 0, p(B,SOLDIER)]
  b[6] = [p(R,SOLDIER), 0, p(R,SOLDIER), 0, p(R,SOLDIER), 0, p(R,SOLDIER), 0, p(R,SOLDIER)]
  b[7] = [0, p(R,CANNON), 0, 0, 0, 0, 0, p(R,CANNON), 0]
  b[9] = [p(R,CHARIOT), p(R,HORSE), p(R,ELEPHANT), p(R,ADVISOR), p(R,KING), p(R,ADVISOR), p(R,ELEPHANT), p(R,HORSE), p(R,CHARIOT)]
  return b
}

export function cloneBoard(board) {
  return board.map(row => [...row])
}

function inBounds(r, c) {
  return r >= 0 && r < ROWS && c >= 0 && c < COLS
}

function inPalace(r, c, color) {
  if (c < 3 || c > 5) return false
  if (color === RED) return r >= 7 && r <= 9
  return r >= 0 && r <= 2
}

function inOwnHalf(r, color) {
  if (color === RED) return r >= 5 && r <= 9
  return r >= 0 && r <= 4
}

function kingMoves(board, r, c, color) {
  const moves = []
  const dirs = [[-1,0],[1,0],[0,-1],[0,1]]
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc
    if (!inPalace(nr, nc, color)) continue
    const target = board[nr][nc]
    if (getPieceColor(target) === color) continue
    moves.push({ row: nr, col: nc })
  }
  return moves
}

function advisorMoves(board, r, c, color) {
  const moves = []
  const dirs = [[-1,-1],[-1,1],[1,-1],[1,1]]
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc
    if (!inPalace(nr, nc, color)) continue
    const target = board[nr][nc]
    if (getPieceColor(target) === color) continue
    moves.push({ row: nr, col: nc })
  }
  return moves
}

function elephantMoves(board, r, c, color) {
  const moves = []
  const dirs = [[-2,-2],[-2,2],[2,-2],[2,2]]
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc
    if (!inBounds(nr, nc)) continue
    if (!inOwnHalf(nr, color)) continue
    const blockR = r + dr / 2, blockC = c + dc / 2
    if (board[blockR][blockC] !== 0) continue
    const target = board[nr][nc]
    if (getPieceColor(target) === color) continue
    moves.push({ row: nr, col: nc })
  }
  return moves
}

function horseMoves(board, r, c, color) {
  const moves = []
  const steps = [
    { leg: [-1,0], targets: [[-2,-1],[-2,1]] },
    { leg: [1,0], targets: [[2,-1],[2,1]] },
    { leg: [0,-1], targets: [[-1,-2],[1,-2]] },
    { leg: [0,1], targets: [[-1,2],[1,2]] },
  ]
  for (const { leg, targets } of steps) {
    const lr = r + leg[0], lc = c + leg[1]
    if (!inBounds(lr, lc) || board[lr][lc] !== 0) continue
    for (const [dr, dc] of targets) {
      const nr = r + dr, nc = c + dc
      if (!inBounds(nr, nc)) continue
      const target = board[nr][nc]
      if (getPieceColor(target) === color) continue
      moves.push({ row: nr, col: nc })
    }
  }
  return moves
}

function chariotMoves(board, r, c, color) {
  const moves = []
  const dirs = [[-1,0],[1,0],[0,-1],[0,1]]
  for (const [dr, dc] of dirs) {
    let nr = r + dr, nc = c + dc
    while (inBounds(nr, nc)) {
      const target = board[nr][nc]
      if (target === 0) {
        moves.push({ row: nr, col: nc })
      } else {
        if (getPieceColor(target) !== color) {
          moves.push({ row: nr, col: nc })
        }
        break
      }
      nr += dr; nc += dc
    }
  }
  return moves
}

function cannonMoves(board, r, c, color) {
  const moves = []
  const dirs = [[-1,0],[1,0],[0,-1],[0,1]]
  for (const [dr, dc] of dirs) {
    let nr = r + dr, nc = c + dc
    let jumped = false
    while (inBounds(nr, nc)) {
      const target = board[nr][nc]
      if (!jumped) {
        if (target === 0) {
          moves.push({ row: nr, col: nc })
        } else {
          jumped = true
        }
      } else {
        if (target !== 0) {
          if (getPieceColor(target) !== color) {
            moves.push({ row: nr, col: nc })
          }
          break
        }
      }
      nr += dr; nc += dc
    }
  }
  return moves
}

function soldierMoves(board, r, c, color) {
  const moves = []
  const forward = color === RED ? -1 : 1
  const crossed = !inOwnHalf(r, color)
  const dirs = [[forward, 0]]
  if (crossed) {
    dirs.push([0, -1], [0, 1])
  }
  for (const [dr, dc] of dirs) {
    const nr = r + dr, nc = c + dc
    if (!inBounds(nr, nc)) continue
    const target = board[nr][nc]
    if (getPieceColor(target) === color) continue
    moves.push({ row: nr, col: nc })
  }
  return moves
}

const PIECE_MOVE_FNS = {
  [KING]: kingMoves,
  [ADVISOR]: advisorMoves,
  [ELEPHANT]: elephantMoves,
  [HORSE]: horseMoves,
  [CHARIOT]: chariotMoves,
  [CANNON]: cannonMoves,
  [SOLDIER]: soldierMoves,
}

export function getRawMoves(board, r, c) {
  const piece = board[r][c]
  if (piece === 0) return []
  const type = getPieceType(piece)
  const color = getPieceColor(piece)
  const fn = PIECE_MOVE_FNS[type]
  if (!fn) return []
  return fn(board, r, c, color)
}

function findKing(board, color) {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (board[r][c] === color * KING) return { row: r, col: c }
    }
  }
  return null
}

function kingsAreFacing(board) {
  const redKing = findKing(board, RED)
  const blackKing = findKing(board, BLACK)
  if (!redKing || !blackKing) return false
  if (redKing.col !== blackKing.col) return false
  for (let r = Math.min(redKing.row, blackKing.row) + 1; r < Math.max(redKing.row, blackKing.row); r++) {
    if (board[r][redKing.col] !== 0) return false
  }
  return true
}

export function isInCheck(board, color) {
  const king = findKing(board, color)
  if (!king) return true
  const enemy = color === RED ? BLACK : RED
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (getPieceColor(board[r][c]) !== enemy) continue
      const moves = getRawMoves(board, r, c)
      if (moves.some(m => m.row === king.row && m.col === king.col)) return true
    }
  }
  return false
}

export function isInCheckAfterMove(board, fromR, fromC, toR, toC, color) {
  const test = cloneBoard(board)
  test[toR][toC] = test[fromR][fromC]
  test[fromR][fromC] = 0
  if (kingsAreFacing(test)) return true
  return isInCheck(test, color)
}

export function getValidMoves(board, r, c) {
  const piece = board[r][c]
  if (piece === 0) return []
  const color = getPieceColor(piece)
  const raw = getRawMoves(board, r, c)
  return raw.filter(m => !isInCheckAfterMove(board, r, c, m.row, m.col, color))
}

export function makeMove(board, fromR, fromC, toR, toC) {
  board[toR][toC] = board[fromR][fromC]
  board[fromR][fromC] = 0
}

export function hasLegalMoves(board, color) {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      if (getPieceColor(board[r][c]) !== color) continue
      if (getValidMoves(board, r, c).length > 0) return true
    }
  }
  return false
}

export function isCheckmate(board, color) {
  return isInCheck(board, color) && !hasLegalMoves(board, color)
}

export function isStalemate(board, color) {
  return !isInCheck(board, color) && !hasLegalMoves(board, color)
}

export function getResultAfterMove(board, fromR, fromC, toR, toC, color) {
  const test = cloneBoard(board)
  makeMove(test, fromR, fromC, toR, toC)
  const enemy = color === RED ? BLACK : RED
  if (isCheckmate(test, enemy)) return { winner: color, reason: '将杀' }
  if (isStalemate(test, enemy)) return { winner: color, reason: '困毙' }
  return null
}

function colLabel(c) {
  return '九八七六五四三二一' [c]
}

function colLabelRed(c) {
  return '１２３４５６７８９' [c]
}

function rowLabel(r) {
  return String(ROWS - r)
}

export function moveToNotation(board, fromR, fromC, toR, toC) {
  const piece = board[fromR][fromC]
  const color = getPieceColor(piece)
  const name = getPieceName(piece)
  const type = getPieceType(piece)

  if (type === HORSE || type === ELEPHANT || type === ADVISOR || type === KING) {
    const fromCol = color === RED ? colLabelRed(fromC) : colLabel(fromC)
    const dr = toR - fromR
    const dc = toC - fromC
    let direction, steps
    if (dr < 0) { direction = '進'; steps = Math.abs(dc) || Math.abs(dr) }
    else if (dr > 0) { direction = '退'; steps = Math.abs(dc) || Math.abs(dr) }
    else if (dc < 0) { direction = '進'; steps = Math.abs(dc) }
    else { direction = '進'; steps = Math.abs(dc) }
    const stepsStr = color === RED ? colLabelRed(steps - 1) : colLabel(steps - 1)
    return name + fromCol + direction + stepsStr
  }
  if (type === CHARIOT || type === CANNON || type === SOLDIER) {
    const fromCol = color === RED ? colLabelRed(fromC) : colLabel(fromC)
    const dr = toR - fromR
    const dc = toC - fromC
    let direction, steps
    if (dr < 0) { direction = '進'; steps = Math.abs(dr) }
    else if (dr > 0) { direction = '退'; steps = Math.abs(dr) }
    else {
      if (dc > 0) { direction = '進'; steps = Math.abs(dc) }
      else { direction = '退'; steps = Math.abs(dc) }
    }
    const stepsStr = color === RED ? colLabelRed(steps - 1) : colLabel(steps - 1)
    return name + fromCol + direction + stepsStr
  }
  return `${name}(${fromR},${fromC})→(${toR},${toC})`
}
