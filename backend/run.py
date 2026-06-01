"""Production server - serves both API and frontend static files."""
import sys
import socket
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(sys._MEIPASS) if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS") else Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")
sys.path.insert(0, str(backend_dir))

from app.main import app
from fastapi.staticfiles import StaticFiles

frontend_dist = backend_dir / "frontend_dist"
if not frontend_dist.exists():
    frontend_dist = backend_dir.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

import uvicorn


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class LANIPMiddleware:
    def __init__(self, app, lan_ip: str, port: int):
        self.app = app
        self.lan_ip = lan_ip
        self.port = port

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        script = f'<script>window.LAN_IP="{self.lan_ip}";window.LAN_PORT={self.port};</script>'.encode()
        script_len = len(script)

        async def send_with_injection(message):
            if message["type"] == "http.response.start":
                self._inject = False
                headers = []
                for name, value in message.get("headers", []):
                    if name.lower() == b"content-type" and b"text/html" in value:
                        self._inject = True
                    headers.append((name, value))
                if self._inject:
                    new_headers = []
                    for name, value in headers:
                        if name.lower() == b"content-length":
                            new_len = int(value) + script_len
                            new_headers.append((name, str(new_len).encode()))
                        else:
                            new_headers.append((name, value))
                    message = {
                        "type": "http.response.start",
                        "status": message["status"],
                        "headers": new_headers,
                    }
                await send(message)
            elif message["type"] == "http.response.body" and self._inject:
                body = message.get("body", b"")
                new_body = body.replace(b"</head>", script + b"</head>", 1)
                if new_body == body:
                    new_body = body + script
                await send({
                    "type": "http.response.body",
                    "body": new_body,
                    "more_body": message.get("more_body", False),
                })
                return
            else:
                await send(message)

        await self.app(scope, receive, send_with_injection)


if __name__ == "__main__":
    if sys.stderr is None:
        import os
        sys.stderr = open(os.devnull, 'w')
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    lan_ip = get_lan_ip()
    app.add_middleware(LANIPMiddleware, lan_ip=lan_ip, port=8000)
    print(f"=> Local:   http://localhost:8000")
    print(f"=> Network: http://{lan_ip}:8000")
    webbrowser.open("http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)