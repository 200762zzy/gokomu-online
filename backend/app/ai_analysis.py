import os
import json
import logging
import httpx
from typing import Optional

from .game import board_to_api_payload, BOARD_SIZE, BLACK, WHITE, EMPTY, count_forced_wins

logger = logging.getLogger(__name__)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
TIMEOUT_CONFIG = httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0)


def _build_prompt(board: list[list[int]]) -> str:
    payload = board_to_api_payload(board)
    board_json = json.dumps(payload, ensure_ascii=False)

    prompt = f"""你是一个职业五子棋AI专家，精通所有开局定式和棋型评估。以下是当前15×15棋盘状态：
{board_json}

请从以下维度综合分析局面，然后给出胜率：

1. 棋型统计：双方各有几个活四、冲四、活三、眠三、活二
2. 子力分布：棋子控制区域和中腹影响力
3. 先手判断：谁掌握局面主动权
4. 定式识别：根据现有棋子分布匹配已知开局定式（浦月、花月、云月、寒星、恒星、溪月、峡月等），参考定式结论辅助判断
5. 攻防紧迫度：哪方距五子连珠更近，是否有必须防守的威胁
6. 推演：在脑海中推演后续3-5步最优变化后，综合评估双方胜率

请返回JSON（不要包含任何其他文字）：
{{
  "black_win_rate": 0.0-1.0,
  "white_win_rate": 0.0-1.0
}}

注意：胜率之和应为1.0。请基于深入的棋型分析和定式知识做出准确评估。

重要规则：本局采用标准五子棋禁手规则。黑棋禁止下出双三、双四、长连；白棋无禁手限制。评估胜率时请考虑此规则。"""
    return prompt


def _local_analysis(board: list[list[int]]) -> dict:
    """Heuristic local analysis as fallback when API is unavailable."""
    black_count = sum(1 for row in board for cell in row if cell == BLACK)
    white_count = sum(1 for row in board for cell in row if cell == WHITE)
    total = black_count + white_count
    if total == 0:
        return {"black_win_rate": 0.5, "white_win_rate": 0.5, "source": "local"}

    def score_player(player):
        s = 0
        visited = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != player:
                    continue
                for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
                    pr, pc = r - dr, c - dc
                    if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == player:
                        continue
                    consecutive = 1
                    open_ends = 0
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                        consecutive += 1
                        nr += dr
                        nc += dc
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == EMPTY:
                        open_ends += 1
                    pr2, pc2 = r - dr, c - dc
                    if 0 <= pr2 < BOARD_SIZE and 0 <= pc2 < BOARD_SIZE and board[pr2][pc2] == EMPTY:
                        open_ends += 1
                    if consecutive >= 5:
                        s += 100000
                    elif consecutive == 4 and open_ends == 2:
                        s += 10000
                    elif consecutive == 4 and open_ends == 1:
                        s += 5000
                    elif consecutive == 3 and open_ends == 2:
                        s += 1000
                    elif consecutive == 3 and open_ends == 1:
                        s += 200
                    elif consecutive == 2 and open_ends == 2:
                        s += 50
                    elif consecutive == 2 and open_ends == 1:
                        s += 10
        return s

    black_score = score_player(BLACK)
    white_score = score_player(WHITE)
    diff = black_score - white_score
    bwr = 1 / (1 + pow(2.71828, -diff / 2000))
    bwr = max(0.05, min(0.95, bwr))
    wwr = 1 - bwr
    return {"black_win_rate": round(bwr, 4), "white_win_rate": round(wwr, 4), "source": "local"}


async def request_analysis(board: list[list[int]], api_key: str = "") -> Optional[dict]:
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return _local_analysis(board)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": _build_prompt(board)}
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            resp = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                content = content.rsplit("```", 1)[0] if "```" in content else content
            result = json.loads(content)
            result = _validate_result(result)
            result["source"] = "deepseek"
            return _apply_forced_win(board, result)
    except httpx.TimeoutException:
        logger.error("DeepSeek API timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API HTTP error: {e.response.status_code} - {e.response.text[:500]}")
    except httpx.RequestError as e:
        logger.error(f"DeepSeek API connection error: {e}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"DeepSeek response parse error: {e}")

    return _local_analysis(board)


def _validate_result(result: dict) -> dict:
    bwr = float(result.get("black_win_rate", 0.5))
    wwr = float(result.get("white_win_rate", 0.5))
    total = bwr + wwr
    if total > 0:
        bwr /= total
        wwr /= total
    else:
        bwr = wwr = 0.5

    return {
        "black_win_rate": round(bwr, 4),
        "white_win_rate": round(wwr, 4),
    }


def _apply_forced_win(board: list[list[int]], result: dict) -> dict:
    bwr = result.get("black_win_rate", 0.5)
    wwr = result.get("white_win_rate", 0.5)
    src = result.get("source", "deepseek")

    black_wins = count_forced_wins(board, BLACK)
    white_wins = count_forced_wins(board, WHITE)

    if black_wins >= 2:
        return {"black_win_rate": 1.0, "white_win_rate": 0.0, "source": src}
    if white_wins >= 2:
        return {"black_win_rate": 0.0, "white_win_rate": 1.0, "source": src}

    return result


def _build_ai_move_prompt(board: list[list[int]], player: int) -> str:
    payload = board_to_api_payload(board)
    board_json = json.dumps(payload, ensure_ascii=False)
    player_name = "黑棋" if player == BLACK else "白棋"

    prompt = f"""你是一个职业五子棋AI选手。以下是当前15×15棋盘状态（1=黑棋，2=白棋，0=空）：
{board_json}

你是{player_name}，请分析局面并给出最佳落子位置。

请严格按照以下步骤思考：
1. 检查是否有活四或双三/双四的必胜手
2. 检查对手是否有活三或冲四需要防守
3. 评估棋盘上的关键位置（眠三、活二等）
4. 选择能最大提升己方胜率或降低对方胜率的位置

重要规则：本局采用标准五子棋禁手规则。黑棋禁止下出双三、双四、长连。

请返回JSON（不要包含任何其他文字）：
{{"row": 0-14, "col": 0-14}}"""
    return prompt


async def request_ai_move(board: list[list[int]], player: int, api_key: str = "") -> Optional[dict]:
    api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        logger.warning("DEEPSEEK_API_KEY not set, cannot request AI move")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": _build_ai_move_prompt(board, player)}
        ],
        "temperature": 0.3,
        "max_tokens": 256,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            resp = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                content = content.rsplit("```", 1)[0] if "```" in content else content
            result = json.loads(content)
            row = int(result["row"])
            col = int(result["col"])
            if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                return {"row": row, "col": col}
    except Exception as e:
        logger.error(f"AI move API error: {e}")

    return None


def _build_review_prompt(moves: list[dict], result: str) -> str:
    lines = []
    for i, m in enumerate(moves):
        side = "黑" if m["player"] == 1 else "白"
        lines.append(f"{i + 1}: {side}({m['row']},{m['col']})")
    board_txt = "\n".join(lines)

    result_cn = {"black_win": "黑", "white_win": "白", "draw": "平局"}.get(result, "未知")

    prompt = f"""你是一个职业五子棋AI复盘专家。
以下是一局完整的五子棋对局，{"黑方" if result_cn == "黑" else "白方" if result_cn == "白" else "双方"}获胜{'' if result_cn != '平局' else '，和棋'}。
请基于整局结果分析每一手棋的质量，而非仅看当时局面。

棋谱：
{board_txt}

评价标准（必须说明每手棋在整局中起到了什么作用）：
- 绝杀手：直接形成必胜局面或连杀
- 决胜手：奠定胜势的关键转折点
- 妙手：取得显著优势的精妙着法
- 好手：巩固优势或扭转局面的正确选择
- 正常：平稳合理但无重大影响的着法
- 疑问手：错过机会或造成小幅亏损
- 昏招：导致形势逆转或直接输棋的严重失误

对每一手棋做出评价，并说明这手棋在整局胜负中起到了什么作用。
详解示例：
「开局定式选择，形成浦月必胜型」「关键防守，化解活三威胁」
「战略扩张压制白方空间」「失误导致白方反先，从此被动」
每手详解 15-35 字，必须结合当前局面和整局结果来说明。

返回JSON（不要包含任何其他文字）：
{{
  "reviews": [
    {{"step": 0, "label": "正常", "detail": "开局占中，平稳", "delta": 0}},
    ...
  ]
}}"""
    return prompt


async def request_review(moves: list[dict], result: str) -> Optional[list[dict]]:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        logger.warning("DEEPSEEK_API_KEY not set, skipping review")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": _build_review_prompt(moves, result)}
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
            resp = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                content = content.rsplit("```", 1)[0] if "```" in content else content
            result_data = json.loads(content)
            reviews = result_data.get("reviews", [])
            for r in reviews:
                r["delta"] = float(r.get("delta", 0))
            return reviews
    except Exception as e:
        logger.error(f"Review API error: {e}")
        return None
