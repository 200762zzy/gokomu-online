import logging
import os
import time
from collections import defaultdict

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .models import AnalyzeRequest, EvaluateRequest, AiMoveRequest, AiMoveResponse
from .ai_analysis import request_analysis, request_review, request_ai_move
from .routers import auth_router, users_router, games_router, friends_router, admin_router
from .chinese_chess.routers import router as cc_router
from .ws.handler import handle_websocket
from .chinese_chess.room_manager import handle_cc_websocket
from .ludo.routers import handle_ludo_websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .log_handler import log_buffer
logging.getLogger().addHandler(log_buffer)

_ws_recent_connects: dict[str, list[float]] = defaultdict(list)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(title="YiQi API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(games_router)
app.include_router(friends_router)
app.include_router(admin_router)
app.include_router(cc_router)


@app.websocket("/ws/cc")
async def websocket_cc(ws: WebSocket):
    await handle_cc_websocket(ws)


@app.websocket("/ws/ludo")
async def websocket_ludo(ws: WebSocket):
    await handle_ludo_websocket(ws)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    client_ip = ws.client.host
    now = time.time()
    _ws_recent_connects[client_ip] = [t for t in _ws_recent_connects[client_ip] if now - t < 30]
    if len(_ws_recent_connects[client_ip]) >= 5:
        await ws.close(code=1008, reason="连接过于频繁")
        return
    _ws_recent_connects[client_ip].append(now)
    await handle_websocket(ws)


@app.get("/api/rooms")
async def list_rooms():
    from .room_manager import room_manager
    return room_manager.list_open_rooms()

@app.get("/api/rooms/active")
async def list_active_rooms():
    from .room_manager import room_manager
    return room_manager.list_spectatable_rooms()


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


@app.get("/api/ngrok-url")
async def ngrok_url():
    import os
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    url_file = os.path.join(root, ".ngrok_url")
    if os.path.exists(url_file):
        with open(url_file) as f:
            url = f.read().strip()
            return {"url": url}
    return {"url": None}

@app.get("/api/ludo/rooms")
async def list_ludo_rooms():
    from .ludo.room_manager import manager as ludo_manager
    return ludo_manager.list_open_rooms()

@app.get("/api/my-active-room")
async def my_active_room(request: Request):
    from .services.auth_service import verify_token
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    uid = verify_token(token, "access")
    if not uid:
        return {"game_type": None, "room_id": None}

    # Check Gomoku
    from .room_manager import room_manager
    room, _ = room_manager.find_room_by_user_id(uid)
    if room:
        return {"game_type": "gomoku", "room_id": room.id}

    # Check Chinese Chess
    from .chinese_chess.room_manager import cc_room_manager
    room, _ = cc_room_manager.find_room_by_user_id(uid)
    if room:
        return {"game_type": "cc", "room_id": room.id}

    # Check Ludo
    from .ludo.room_manager import manager as ludo_manager
    room, _ = ludo_manager.find_room_by_user_id(uid)
    if room:
        return {"game_type": "ludo", "room_id": room.id}

    return {"game_type": None, "room_id": None}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Serve frontend static files (production mode)
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    # Assets subdirectories first (longer prefix wins)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    app.mount("/audio", StaticFiles(directory=os.path.join(frontend_dist, "audio")), name="audio")
    app.mount("/bg", StaticFiles(directory=os.path.join(frontend_dist, "bg")), name="bg")
    # Root: serve exact files, fallback to index.html for SPA routes
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_dist}")
else:
    logger.warning(f"Frontend dist not found at {frontend_dist}, run 'npm run build' in frontend/")


