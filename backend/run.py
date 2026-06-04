"""Gomoku Online server — starts API + frontend, optionally with ngrok tunnel."""
import os
import sys
import json
import time
import urllib.request
import subprocess
import threading
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

backend_dir = (
    Path(sys._MEIPASS)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    else Path(__file__).resolve().parent
)
load_dotenv(backend_dir / ".env")
sys.path.insert(0, str(backend_dir))

from app.main import app
from fastapi.staticfiles import StaticFiles
import uvicorn

PORT = int(os.getenv("PORT", "8001"))

# --- Find frontend dist ---
frontend_dist = None
candidates = [
    backend_dir / "frontend_dist",
    backend_dir.parent / "frontend" / "dist",
    Path(sys.executable).parent / "frontend_dist",
    Path(sys.executable).parent / "frontend" / "dist",
    backend_dir.parent.parent / "frontend" / "dist",
]
for p in candidates:
    if p.exists():
        frontend_dist = p
        break

if frontend_dist:
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    print(f"[server] Frontend mounted from {frontend_dist}")
else:
    print("[server] WARNING: Frontend dist not found, API-only mode")


def wait_for_server(url: str, timeout: int = 20) -> bool:
    for i in range(timeout):
        try:
            r = urllib.request.urlopen(url, timeout=2)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def get_ngrok_url(timeout: int = 20) -> str | None:
    for i in range(timeout):
        try:
            r = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2)
            data = json.loads(r.read())
            tunnels = data.get("tunnels", [])
            if tunnels:
                return tunnels[0]["public_url"]
        except Exception:
            pass
        time.sleep(1)
    return None


def start_server():
    uvicorn.run(app, host="0.0.0.0", port=PORT, ws_ping_interval=20, ws_ping_timeout=20)


if __name__ == "__main__":
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")

    print("=" * 48)
    print("  Gomoku Online - 启动中...")
    print("=" * 48)
    print()

    print(f"[server] 启动后端 (端口 {PORT})...")
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    if not wait_for_server(f"http://127.0.0.1:{PORT}/api/health"):
        print("[server] 后端启动超时")
        time.sleep(5)
        sys.exit(1)
    print("[server] 后端就绪")

    # Optional ngrok
    ngrok_proc: subprocess.Popen | None = None
    ngrok_url: str | None = None
    print("[ngrok] 尝试启动隧道...")
    try:
        ngrok_proc = subprocess.Popen(
            ["ngrok", "http", str(PORT), "--log=stdout"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"[ngrok] 隧道就绪: {ngrok_url}")
        else:
            print("[ngrok] 隧道不可用（未安装 ngrok 或未配置 authtoken）")
            ngrok_proc.terminate()
            ngrok_proc = None
    except FileNotFoundError:
        print("[ngrok] 未找到 ngrok")

    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 48)
    print("  Gomoku Online 已上线!")
    print("=" * 48)
    print()
    if ngrok_url:
        print(f"  公网地址: {ngrok_url}")
        print(f"  ngrok管理: http://127.0.0.1:4040")
        print()
        print("  将此地址发给朋友即可加入对战")
        open_url = ngrok_url
    else:
        open_url = f"http://localhost:{PORT}"
        print(f"  本地地址: {open_url}")
        print()
        print("  公网隧道不可用，仅本机可访问")
        print("  如需公网访问，请安装 ngrok 并配置 authtoken")
    print()

    webbrowser.open(open_url)

    try:
        input("  按 Enter 键停止所有服务...")
    except (EOFError, RuntimeError):
        time.sleep(3600)

    if ngrok_proc:
        ngrok_proc.terminate()
        try:
            ngrok_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ngrok_proc.kill()
    print("已停止")
