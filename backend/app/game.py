from typing import Optional

BOARD_SIZE = 15
EMPTY = 0
BLACK = 1
WHITE = 2

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]


def create_board() -> list[list[int]]:
    return [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def is_valid_move(board: list[list[int]], row: int, col: int) -> bool:
    if row < 0 or row >= BOARD_SIZE or col < 0 or col >= BOARD_SIZE:
        return False
    return board[row][col] == EMPTY


def place_stone(board: list[list[int]], row: int, col: int, player: int) -> bool:
    if not is_valid_move(board, row, col):
        return False
    board[row][col] = player
    return True


def check_win(board: list[list[int]], row: int, col: int) -> Optional[int]:
    player = board[row][col]
    if player == EMPTY:
        return None

    for dr, dc in DIRECTIONS:
        count = 1
        for step in range(1, 5):
            r, c = row + dr * step, col + dc * step
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                count += 1
            else:
                break
        for step in range(1, 5):
            r, c = row - dr * step, col - dc * step
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
                count += 1
            else:
                break
        if count >= 5:
            return player
    return None


def _count_dir(board, row, col, dr, dc, player):
    """Count consecutive stones in one direction (excluding the cell itself)."""
    count = 0
    for step in range(1, 6):
        r, c = row + dr * step, col + dc * step
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == player:
            count += 1
        else:
            break
    return count


def is_forbidden(board: list[list[int]], row: int, col: int, player: int) -> Optional[str]:
    """Check if placing a stone at (row, col) is a forbidden move.
    Only applies to BLACK. Returns reason string or None."""
    if player != BLACK:
        return None
    if board[row][col] != EMPTY:
        return None

    board[row][col] = BLACK

    # 1. 长连禁手 — any direction ≥ 6 in a row
    for dr, dc in DIRECTIONS:
        total = 1 + _count_dir(board, row, col, dr, dc, BLACK) + _count_dir(board, row, col, -dr, -dc, BLACK)
        if total >= 6:
            board[row][col] = EMPTY
            return "长连禁手"

    # 2. 双四禁手 — ≥ 2 directions with total = 4
    four_count = 0
    for dr, dc in DIRECTIONS:
        total = 1 + _count_dir(board, row, col, dr, dc, BLACK) + _count_dir(board, row, col, -dr, -dc, BLACK)
        if total == 4:
            four_count += 1
    if four_count >= 2:
        board[row][col] = EMPTY
        return "双四禁手"

    # 3. 双三禁手 — ≥ 2 directions with exact 3 and both ends open
    open_three_count = 0
    for dr, dc in DIRECTIONS:
        fwd = _count_dir(board, row, col, dr, dc, BLACK)
        bwd = _count_dir(board, row, col, -dr, -dc, BLACK)
        total = 1 + fwd + bwd
        if total != 3:
            continue
        fr = row + dr * (fwd + 1)
        fc = col + dc * (fwd + 1)
        br = row - dr * (bwd + 1)
        bc = col - dc * (bwd + 1)
        end1_open = 0 <= fr < BOARD_SIZE and 0 <= fc < BOARD_SIZE and board[fr][fc] == EMPTY
        end2_open = 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE and board[br][bc] == EMPTY
        if end1_open and end2_open:
            open_three_count += 1
    if open_three_count >= 2:
        board[row][col] = EMPTY
        return "双三禁手"

    board[row][col] = EMPTY
    return None


def count_forced_wins(board: list[list[int]], player: int) -> int:
    """统计该方有多少个落子即胜的空位（跳过黑棋禁手）。"""
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != EMPTY:
                continue
            if player == BLACK and is_forbidden(board, r, c, BLACK):
                continue
            board[r][c] = player
            if check_win(board, r, c):
                count += 1
            board[r][c] = EMPTY
            if count >= 2:
                return count
    return count


def board_to_api_payload(board: list[list[int]]) -> dict:
    grid = []
    for r in range(BOARD_SIZE):
        row_data = []
        for c in range(BOARD_SIZE):
            val = board[r][c]
            if val == BLACK:
                row_data.append("black")
            elif val == WHITE:
                row_data.append("white")
            else:
                row_data.append("empty")
        grid.append(row_data)
    return {"board": grid, "board_size": BOARD_SIZE}
