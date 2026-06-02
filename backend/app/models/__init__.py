from pydantic import BaseModel
from enum import Enum
from typing import Optional

# ===== ORM models =====
from .user import User
from .game import GameRecord
from .friend import Friendship, FriendRequest

__all__ = ["User", "GameRecord", "Friendship", "FriendRequest"]

# ===== Legacy Pydantic schemas =====
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


# ===== Title / Rank =====
class TitleInfo(BaseModel):
    name: str
    tier: int
    icon: str


# ===== Auth =====
class AuthRegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthRefreshRequest(BaseModel):
    refresh_token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: int
    username: str
    nickname: str
    elo: int
    is_admin: bool = False
    title: TitleInfo | None = None


# ===== User Profile =====
class UserProfileResponse(BaseModel):
    id: int
    username: str
    nickname: str
    avatar_url: str = ""
    board_image: str = ""
    background_image: str = ""
    elo: int
    is_admin: bool = False
    created_at: str = ""
    title: TitleInfo | None = None


class LeaderboardEntry(BaseModel):
    id: int
    username: str
    nickname: str
    elo: int
    rank: int
    title: TitleInfo | None = None


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total: int
    page: int


# ===== Game Records =====
class GameRecordResponse(BaseModel):
    id: int
    black_id: int
    white_id: int
    winner: str | None = None
    reason: str | None = None
    moves_json: str = "[]"
    black_elo_change: int = 0
    white_elo_change: int = 0
    started_at: str = ""
    ended_at: str | None = None


class GameHistoryResponse(BaseModel):
    games: list[GameRecordResponse]
    total: int
    page: int


# ===== Friends =====
class FriendEntry(BaseModel):
    id: int
    username: str
    nickname: str
    elo: int
    title: TitleInfo | None = None


class FriendListResponse(BaseModel):
    friends: list[FriendEntry]


# ===== WebSocket Messages =====
class WsAuthMessage(BaseModel):
    type: str = "auth"
    token: str


class WsCreateRoom(BaseModel):
    type: str = "create_room"
    player_name: str = ""


class WsJoinRoom(BaseModel):
    type: str = "join_room"
    room_id: str
    player_name: str = ""


class WsPlaceStone(BaseModel):
    type: str = "place_stone"
    row: int
    col: int


class WsChat(BaseModel):
    type: str = "chat"
    message: str
    room_id: str = ""


class WsGlobalChat(BaseModel):
    type: str = "global_chat"
    message: str


class WsPrivateChat(BaseModel):
    type: str = "private_chat"
    to: str
    message: str
