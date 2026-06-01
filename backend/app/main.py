import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalyzeRequest, EvaluateRequest, AiMoveRequest, AiMoveResponse
from .ai_analysis import request_analysis, request_review, request_ai_move
from .room_manager import room_manager
from .ws_handler import handle_websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gomoku Online API", version="1.0.0")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await handle_websocket(ws, room_manager)


@app.get("/api/rooms")
async def list_rooms():
    return room_manager.list_open_rooms()


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    result = await request_analysis(req.board, req.api_key)
    return result or {}


@app.post("/api/evaluate")
async def evaluate(req: EvaluateRequest):
    reviews = await request_review(req.moves, req.result)
    return {"reviews": reviews or []}


@app.post("/api/ai-move", response_model=AiMoveResponse)
async def ai_move(req: AiMoveRequest):
    result = await request_ai_move(req.board, req.player, req.api_key)
    if result:
        return AiMoveResponse(row=result["row"], col=result["col"])
    return AiMoveResponse(row=-1, col=-1)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
