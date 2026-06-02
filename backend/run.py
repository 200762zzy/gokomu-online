"""Gomoku Online server — starts API + frontend + ngrok tunnel for public access."""
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

frontend_dist = backend_dir / "frontend_dist"
if not frontend_dist.exists():
    frontend_dist = backend_dir.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    print(f"[server] Frontend mounted from {frontend_dist}")
else:
    print("[server] WARNING: Frontend dist not found, API-only mode")

PORT = int(os.getenv("PORT", "8001"))


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


def get_ngrok_url(timeout: int = 30) -> str | None:
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
    uvicorn.run(app, host="0.0.0.0", port=PORT)


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

    print("[ngrok] 启动隧道...")
    ngrok_proc = subprocess.Popen(
        ["ngrok", "http", str(PORT), "--log=stdout"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("[ngrok] 获取公网地址失败")
        print("[ngrok] 请确认已安装 ngrok 并配置 ngrok authtoken")
        ngrok_proc.terminate()
        time.sleep(5)
        sys.exit(1)

    with open(backend_dir / ".ngrok_url", "w") as f:
        f.write(ngrok_url)

    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 48)
    print("  Gomoku Online 已上线!")
    print("=" * 48)
    print()
    print(f"  公网地址: {ngrok_url}")
    print(f"  ngrok管理: http://127.0.0.1:4040")
    print()
    print("  将此地址发给朋友即可加入对战")
    print()
    try:
        input("  按 Enter 键停止所有服务...")
    except (EOFError, RuntimeError):
        time.sleep(3600)

    ngrok_proc.terminate()
    try:
        ngrok_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        ngrok_proc.kill()
    print("已停止")
