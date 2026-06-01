from pydantic import BaseModel
from enum import Enum
from typing import Optional


class Stone(str, Enum):
    empty = "empty"
    black = "black"
    white = "white"


class GameStatus(str, Enum):
    playing = "playing"
    finished = "finished"


class AnalyzeRequest(BaseModel):
    board: list[list[int]]
    api_key: str = ""


class AnalysisResult(BaseModel):
    black_win_rate: float
    white_win_rate: float


class EvaluateRequest(BaseModel):
    moves: list[dict]
    result: str


class MoveReview(BaseModel):
    step: int
    label: str
    detail: str
    delta: Optional[float] = None


class EvaluateResult(BaseModel):
    reviews: list[MoveReview]


class AiMoveRequest(BaseModel):
    board: list[list[int]]
    player: int
    api_key: str = ""


class AiMoveResponse(BaseModel):
    row: int
    col: int
