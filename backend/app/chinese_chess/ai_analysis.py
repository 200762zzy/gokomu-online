import os, json, logging, random
import httpx
from . import game

logger = logging.getLogger(__name__)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
TIMEOUT = httpx.Timeout(connect=5.0, read=8.0, write=10.0, pool=5.0)


def _board_to_prompt(board):
    lines = ["  0 1 2 3 4 5 6 7 8"]
    for r in range(game.ROWS):
        row = [str(r)]
        for c in range(game.COLS):
            val = board[r][c]
            if val == 0:
                row.append("．")
            else:
                name = game.PIECE_NAMES.get(game.get_piece_type(val), {}).get(
                    game.RED if val > 0 else game.BLACK, "?")
                row.append(name)
        lines.append(" ".join(row))
    return "\n".join(lines)


async def request_ai_move(board: list[list[int]], api_key: str | None, color: str) -> dict | None:
    if not api_key:
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return _fallback_move(board, color)

    player = game.RED if color == "red" else game.BLACK
    board_str = _board_to_prompt(board)
    turn_cn = "红方" if color == "red" else "黑方"

    prompt = f"""你是一个中国象棋AI专家。以下是当前棋盘状态（红方用汉字表示，黑方用汉字表示）：
{board_str}

当前轮到{turn_cn}走棋。

请分析局面，返回一个最佳走法。要求：
1. 分析双方子力、位置、攻防态势
2. 给出最佳走法的起止坐标
3. 只返回JSON，不要包含其他文字

返回格式：
```json
{{"from_row": 数字, "from_col": 数字, "to_row": 数字, "to_col": 数字, "reason": "简要分析"}}
```"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                json_str = content.strip()
                if json_str.startswith("```"):
                    json_str = json_str.split("\n", 1)[1]
                    json_str = json_str.rsplit("```", 1)[0]
                result = json.loads(json_str.strip())
                fr, fc = result.get("from_row"), result.get("from_col")
                tr, tc = result.get("to_row"), result.get("to_col")
                if all(v is not None for v in [fr, fc, tr, tc]):
                    piece_color = game.get_piece_color(board[fr][fc])
                    if piece_color != player:
                        logger.warning(f"AI returned move for opponent piece ({fr},{fc}), falling back")
                    else:
                        valid = game.get_valid_moves(board, fr, fc)
                        if (tr, tc) in valid:
                            return {"from_row": fr, "from_col": fc, "to_row": tr, "to_col": tc}
                        logger.warning(f"AI returned invalid move ({fr},{fc})->({tr},{tc}), falling back")
                else:
                    logger.warning(f"AI returned incomplete move, falling back")
            else:
                logger.warning(f"DeepSeek API error: {resp.status_code}")
    except Exception as e:
        logger.error(f"DeepSeek request failed: {e}")
    return _fallback_move(board, color)


def _fallback_move(board, color):
    player = game.RED if color == "red" else game.BLACK
    all_moves = []
    for r in range(game.ROWS):
        for c in range(game.COLS):
            if game.get_piece_color(board[r][c]) != player:
                continue
            valid = game.get_valid_moves(board, r, c)
            for tr, tc in valid:
                all_moves.append((r, c, tr, tc))
    if not all_moves:
        return None
    scored = []
    for fr, fc, tr, tc in all_moves:
        score = 0
        target = board[tr][tc]
        if target != 0:
            score += abs(target) * 10
        test = game.clone_board(board)
        game.make_move(test, fr, fc, tr, tc)
        enemy = game.BLACK if player == game.RED else game.RED
        if game.is_checkmate(test, enemy):
            score += 1000
        if game.is_in_check(test, enemy):
            score += 50
        scored.append((score, fr, fc, tr, tc))
    scored.sort(key=lambda x: -x[0])
    best = scored[0]
    return {"from_row": best[1], "from_col": best[2], "to_row": best[3], "to_col": best[4]}
