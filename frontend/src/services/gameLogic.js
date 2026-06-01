export const BOARD_SIZE = 15
export const EMPTY = 0
export const BLACK = 1
export const WHITE = 2

const DIRECTIONS = [[1, 0], [0, 1], [1, 1], [1, -1]]

export function createBoard() {
  return Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill(EMPTY))
}

export function isValidMove(board, row, col) {
  if (row < 0 || row >= BOARD_SIZE || col < 0 || col >= BOARD_SIZE) return false
  return board[row][col] === EMPTY
}

export function placeStone(board, row, col, player) {
  if (!isValidMove(board, row, col)) return false
  board[row][col] = player
  return true
}

export function checkWin(board, row, col) {
  const player = board[row][col]
  if (player === EMPTY) return null

  for (const [dr, dc] of DIRECTIONS) {
    let count = 1
    for (let step = 1; step < 5; step++) {
      const r = row + dr * step, c = col + dc * step
      if (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] === player) count++
      else break
    }
    for (let step = 1; step < 5; step++) {
      const r = row - dr * step, c = col - dc * step
      if (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] === player) count++
      else break
    }
    if (count >= 5) return player
  }
  return null
}

function _countDir(board, row, col, dr, dc, player) {
  let count = 0
  for (let step = 1; step < 6; step++) {
    const r = row + dr * step, c = col + dc * step
    if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE) break
    if (board[r][c] !== player) break
    count++
  }
  return count
}

export function checkForbiddenMove(board, row, col, player) {
  if (player !== BLACK) return null
  if (board[row][col] !== EMPTY) return null

  board[row][col] = BLACK

  for (const [dr, dc] of DIRECTIONS) {
    const fwd = _countDir(board, row, col, dr, dc, BLACK)
    const bwd = _countDir(board, row, col, -dr, -dc, BLACK)
    if (1 + fwd + bwd >= 6) {
      board[row][col] = EMPTY
      return '长连禁手'
    }
  }

  let fourCount = 0
  for (const [dr, dc] of DIRECTIONS) {
    const total = 1 + _countDir(board, row, col, dr, dc, BLACK) + _countDir(board, row, col, -dr, -dc, BLACK)
    if (total === 4) fourCount++
  }
  if (fourCount >= 2) {
    board[row][col] = EMPTY
    return '双四禁手'
  }

  let openThreeCount = 0
  for (const [dr, dc] of DIRECTIONS) {
    const fwd = _countDir(board, row, col, dr, dc, BLACK)
    const bwd = _countDir(board, row, col, -dr, -dc, BLACK)
    if (1 + fwd + bwd !== 3) continue
    const fr = row + dr * (fwd + 1), fc = col + dc * (fwd + 1)
    const br = row - dr * (bwd + 1), bc = col - dc * (bwd + 1)
    const e1 = fr >= 0 && fr < BOARD_SIZE && fc >= 0 && fc < BOARD_SIZE && board[fr][fc] === EMPTY
    const e2 = br >= 0 && br < BOARD_SIZE && bc >= 0 && bc < BOARD_SIZE && board[br][bc] === EMPTY
    if (e1 && e2) openThreeCount++
  }
  if (openThreeCount >= 2) {
    board[row][col] = EMPTY
    return '双三禁手'
  }

  board[row][col] = EMPTY
  return null
}

export function cloneBoard(board) {
  return board.map(row => [...row])
}

export function countForcedWins(board, player) {
  let count = 0
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (board[r][c] !== EMPTY) continue
      if (player === BLACK && checkForbiddenMove(board, r, c, BLACK)) continue
      board[r][c] = player
      if (checkWin(board, r, c)) count++
      board[r][c] = EMPTY
      if (count >= 2) return count
    }
  }
  return count
}

export function getStoneName(stone) {
  return stone === BLACK ? 'black' : 'white'
}
