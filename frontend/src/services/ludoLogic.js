export const PLAYER_COLORS = ["red", "blue", "green", "yellow"]

export const BOARD_SIZE = 15

export const MAIN_PATH = [
  [13, 6], [12, 6], [11, 6], [10, 6], [9, 6],
  [8, 6], [8, 5], [8, 4], [8, 3], [8, 2], [8, 1], [8, 0],
  [7, 0], [6, 0],
  [6, 1], [6, 2], [6, 3], [6, 4], [6, 5],
  [5, 6], [4, 6], [3, 6], [2, 6], [1, 6], [0, 6],
  [0, 7], [0, 8],
  [1, 8], [2, 8], [3, 8], [4, 8], [5, 8],
  [6, 9], [6, 10], [6, 11], [6, 12], [6, 13], [6, 14],
  [7, 14], [8, 14],
  [8, 13], [8, 12], [8, 11], [8, 10], [8, 9],
  [9, 8], [10, 8], [11, 8], [12, 8], [13, 8],
  [13, 7],
]

export const TOTAL_MAIN_CELLS = 51

export const PLAYER_ENTRY = [0, 13, 26, 39]

export const HOME_STRETCH = {
  0: [[13, 7], [12, 7], [11, 7], [10, 7], [9, 7], [8, 7]],
  1: [[7, 1], [7, 2], [7, 3], [7, 4], [7, 5], [7, 6]],
  2: [[1, 7], [2, 7], [3, 7], [4, 7], [5, 7], [6, 7]],
  3: [[7, 13], [7, 12], [7, 11], [7, 10], [7, 9], [7, 8]],
}

export const START_ZONES = {
  0: [[9, 11], [9, 12], [10, 11], [10, 12]],
  1: [[2, 11], [2, 12], [3, 11], [3, 12]],
  2: [[2, 2], [2, 3], [3, 2], [3, 3]],
  3: [[9, 2], [9, 3], [10, 2], [10, 3]],
}

export const PIECES_PER_PLAYER = 4
export const HOME_STRETCH_LEN = 6
export const STEPS_TO_FINISH = 56

export function absoluteToView(coord, playerView) {
  const [r, c] = coord
  if (playerView === 1) return [c, 14 - r]
  if (playerView === 2) return [14 - r, 14 - c]
  if (playerView === 3) return [14 - c, r]
  return [r, c]
}

export function getPlayerViewIndex(color) {
  return PLAYER_COLORS.indexOf(color)
}

export function getPathIndex(pos) {
  for (let i = 0; i < MAIN_PATH.length; i++) {
    if (MAIN_PATH[i][0] === pos[0] && MAIN_PATH[i][1] === pos[1]) return i
  }
  return -1
}

export function getColorHex(color) {
  const map = { red: '#e74c3c', blue: '#3498db', green: '#2ecc71', yellow: '#f1c40f' }
  return map[color] || '#888'
}

export function getColorNameCN(color) {
  const map = { red: '红方', blue: '蓝方', green: '绿方', yellow: '黄方' }
  return map[color] || color
}
