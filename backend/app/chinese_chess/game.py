EMPTY = 0
RED = 1
BLACK = -1

ROWS = 10
COLS = 9

KING = 1
ADVISOR = 2
ELEPHANT = 3
HORSE = 4
CHARIOT = 5
CANNON = 6
SOLDIER = 7

PIECE_NAMES = {
    KING: {RED: "帥", BLACK: "將"},
    ADVISOR: {RED: "仕", BLACK: "士"},
    ELEPHANT: {RED: "相", BLACK: "象"},
    HORSE: {RED: "馬", BLACK: "馬"},
    CHARIOT: {RED: "車", BLACK: "車"},
    CANNON: {RED: "砲", BLACK: "炮"},
    SOLDIER: {RED: "兵", BLACK: "卒"},
}


def get_piece_type(val: int) -> int:
    return abs(val)


def get_piece_color(val: int) -> int:
    if val > 0:
        return RED
    if val < 0:
        return BLACK
    return EMPTY


def create_board() -> list[list[int]]:
    b = [[EMPTY] * COLS for _ in range(ROWS)]
    R, B = RED, BLACK
    p = lambda c, t: c * t
    b[0] = [p(B,CHARIOT), p(B,HORSE), p(B,ELEPHANT), p(B,ADVISOR), p(B,KING), p(B,ADVISOR), p(B,ELEPHANT), p(B,HORSE), p(B,CHARIOT)]
    b[2] = [EMPTY, p(B,CANNON), EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, p(B,CANNON), EMPTY]
    b[3] = [p(B,SOLDIER), EMPTY, p(B,SOLDIER), EMPTY, p(B,SOLDIER), EMPTY, p(B,SOLDIER), EMPTY, p(B,SOLDIER)]
    b[6] = [p(R,SOLDIER), EMPTY, p(R,SOLDIER), EMPTY, p(R,SOLDIER), EMPTY, p(R,SOLDIER), EMPTY, p(R,SOLDIER)]
    b[7] = [EMPTY, p(R,CANNON), EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, p(R,CANNON), EMPTY]
    b[9] = [p(R,CHARIOT), p(R,HORSE), p(R,ELEPHANT), p(R,ADVISOR), p(R,KING), p(R,ADVISOR), p(R,ELEPHANT), p(R,HORSE), p(R,CHARIOT)]
    return b


def clone_board(board: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in board]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < ROWS and 0 <= c < COLS


def _in_palace(r: int, c: int, color: int) -> bool:
    if c < 3 or c > 5:
        return False
    if color == RED:
        return 7 <= r <= 9
    return 0 <= r <= 2


def _in_own_half(r: int, color: int) -> bool:
    if color == RED:
        return 5 <= r <= 9
    return 0 <= r <= 4


def _king_moves(board, r, c, color):
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if not _in_palace(nr, nc, color):
            continue
        target = board[nr][nc]
        if get_piece_color(target) == color:
            continue
        moves.append((nr, nc))
    return moves


def _advisor_moves(board, r, c, color):
    moves = []
    for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr, nc = r + dr, c + dc
        if not _in_palace(nr, nc, color):
            continue
        target = board[nr][nc]
        if get_piece_color(target) == color:
            continue
        moves.append((nr, nc))
    return moves


def _elephant_moves(board, r, c, color):
    moves = []
    for dr, dc in [(-2,-2),(-2,2),(2,-2),(2,2)]:
        nr, nc = r + dr, c + dc
        if not _in_bounds(nr, nc):
            continue
        if not _in_own_half(nr, color):
            continue
        br, bc = r + dr // 2, c + dc // 2
        if board[br][bc] != EMPTY:
            continue
        target = board[nr][nc]
        if get_piece_color(target) == color:
            continue
        moves.append((nr, nc))
    return moves


def _horse_moves(board, r, c, color):
    moves = []
    legs_targets = [
        ((-1, 0), [(-2,-1), (-2, 1)]),
        (( 1, 0), [( 2,-1), ( 2, 1)]),
        (( 0,-1), [(-1,-2), ( 1,-2)]),
        (( 0, 1), [(-1, 2), ( 1, 2)]),
    ]
    for (lr, lc), targets in legs_targets:
        leg_r, leg_c = r + lr, c + lc
        if not _in_bounds(leg_r, leg_c) or board[leg_r][leg_c] != EMPTY:
            continue
        for dr, dc in targets:
            nr, nc = r + dr, c + dc
            if not _in_bounds(nr, nc):
                continue
            target = board[nr][nc]
            if get_piece_color(target) == color:
                continue
            moves.append((nr, nc))
    return moves


def _chariot_moves(board, r, c, color):
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        while _in_bounds(nr, nc):
            target = board[nr][nc]
            if target == EMPTY:
                moves.append((nr, nc))
            else:
                if get_piece_color(target) != color:
                    moves.append((nr, nc))
                break
            nr += dr
            nc += dc
    return moves


def _cannon_moves(board, r, c, color):
    moves = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        jumped = False
        while _in_bounds(nr, nc):
            target = board[nr][nc]
            if not jumped:
                if target == EMPTY:
                    moves.append((nr, nc))
                else:
                    jumped = True
            else:
                if target != EMPTY:
                    if get_piece_color(target) != color:
                        moves.append((nr, nc))
                    break
            nr += dr
            nc += dc
    return moves


def _soldier_moves(board, r, c, color):
    moves = []
    forward = -1 if color == RED else 1
    crossed = not _in_own_half(r, color)
    dirs = [(forward, 0)]
    if crossed:
        dirs.extend([(0, -1), (0, 1)])
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if not _in_bounds(nr, nc):
            continue
        target = board[nr][nc]
        if get_piece_color(target) == color:
            continue
        moves.append((nr, nc))
    return moves


_PIECE_MOVE_FNS = {
    KING: _king_moves,
    ADVISOR: _advisor_moves,
    ELEPHANT: _elephant_moves,
    HORSE: _horse_moves,
    CHARIOT: _chariot_moves,
    CANNON: _cannon_moves,
    SOLDIER: _soldier_moves,
}


def get_raw_moves(board, r, c):
    piece = board[r][c]
    if piece == EMPTY:
        return []
    ptype = get_piece_type(piece)
    color = get_piece_color(piece)
    fn = _PIECE_MOVE_FNS.get(ptype)
    if not fn:
        return []
    return fn(board, r, c, color)


def _find_king(board, color):
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == color * KING:
                return (r, c)
    return None


def _kings_are_facing(board):
    rk = _find_king(board, RED)
    bk = _find_king(board, BLACK)
    if not rk or not bk:
        return False
    if rk[1] != bk[1]:
        return False
    for r in range(min(rk[0], bk[0]) + 1, max(rk[0], bk[0])):
        if board[r][rk[1]] != EMPTY:
            return False
    return True


def is_in_check(board, color):
    king = _find_king(board, color)
    if not king:
        return True
    enemy = BLACK if color == RED else RED
    for r in range(ROWS):
        for c in range(COLS):
            if get_piece_color(board[r][c]) != enemy:
                continue
            moves = get_raw_moves(board, r, c)
            for mr, mc in moves:
                if mr == king[0] and mc == king[1]:
                    return True
    return False


def is_in_check_after_move(board, from_r, from_c, to_r, to_c, color):
    test = clone_board(board)
    test[to_r][to_c] = test[from_r][from_c]
    test[from_r][from_c] = EMPTY
    if _kings_are_facing(test):
        return True
    return is_in_check(test, color)


def get_valid_moves(board, r, c):
    piece = board[r][c]
    if piece == EMPTY:
        return []
    color = get_piece_color(piece)
    raw = get_raw_moves(board, r, c)
    return [(mr, mc) for mr, mc in raw if not is_in_check_after_move(board, r, c, mr, mc, color)]


def make_move(board, from_r, from_c, to_r, to_c):
    board[to_r][to_c] = board[from_r][from_c]
    board[from_r][from_c] = EMPTY


def has_legal_moves(board, color):
    for r in range(ROWS):
        for c in range(COLS):
            if get_piece_color(board[r][c]) != color:
                continue
            if get_valid_moves(board, r, c):
                return True
    return False


def is_checkmate(board, color):
    return is_in_check(board, color) and not has_legal_moves(board, color)


def is_stalemate(board, color):
    return not is_in_check(board, color) and not has_legal_moves(board, color)


def board_to_api(board):
    result = []
    for r in range(ROWS):
        row_data = []
        for c in range(COLS):
            val = board[r][c]
            if val == EMPTY:
                row_data.append(None)
            else:
                row_data.append(val)
        result.append(row_data)
    return result


def api_to_board(data):
    board = [[EMPTY] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            val = data[r][c]
            board[r][c] = val if val is not None else EMPTY
    return board


def position_hash(board):
    pieces = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != EMPTY:
                pieces.append((r, c, board[r][c]))
    return tuple(pieces)
