import subprocess
import time
import urllib.request
import json
import os
import sys
import webbrowser
import atexit

root = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    root = os.path.dirname(sys.executable)

ngrok_url_file = os.path.join(root, ".ngrok_url")
processes = []


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def cleanup():
    for p in processes:
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait(timeout=3)
            except:
                try:
                    p.kill()
                except:
                    pass
    if os.path.exists(ngrok_url_file):
        os.remove(ngrok_url_file)


def wait_for_health(url, timeout=20):
    for i in range(timeout):
        try:
            r = urllib.request.urlopen(url, timeout=2)
            if r.status == 200:
                return True
        except:
            pass
        log(f"等待后端就绪... ({i+1}/{timeout})")
        time.sleep(1)
    return False


def wait_for_ngrok_url(timeout=25):
    for i in range(timeout):
        try:
            r = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2)
            data = json.loads(r.read())
            if data.get("tunnels"):
                return data["tunnels"][0]["public_url"]
        except:
            pass
        log(f"等待 ngrok 隧道... ({i+1}/{timeout})")
        time.sleep(1)
    return None


def run_subprocess(cmd, cwd, name):
    try:
        p = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        processes.append(p)
        return p
    except Exception as e:
        log(f"启动 {name} 失败: {e}")
        log(f"命令: {' '.join(cmd)}")
        return None


def main():
    atexit.register(cleanup)

    print("=" * 48)
    print("  Gomoku Online - 启动中...")
    print("=" * 48)
    print()

    # --- 构建前端 ---
    log("构建前端...")
    p = run_subprocess(
        ["npm", "run", "build"] if os.name != "nt" else ["cmd", "/c", "npm", "run", "build"],
        os.path.join(root, "frontend"),
        "前端构建",
    )
    if p:
        p.wait()
    if p and p.returncode != 0:
        log("前端构建失败，确保frontend/dist存在后重试")
        input("\n按 Enter 退出...")
        sys.exit(1)
    log("前端构建完成")

    # --- 启动后端 ---
    log("启动后端 (端口 8001)...")
    p = run_subprocess(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        os.path.join(root, "backend"),
        "后端",
    )
    if not p:
        input("\n按 Enter 退出...")
        sys.exit(1)

    if not wait_for_health("http://127.0.0.1:8001/api/health"):
        log("后端启动超时")
        log("请确认已安装依赖: pip install -r requirements.txt")
        cleanup()
        input("\n按 Enter 退出...")
        sys.exit(1)
    log(f"后端就绪 (PID {p.pid})")

    # --- 启动 ngrok ---
    log("启动 ngrok 隧道 (指向 8001)...")
    p = run_subprocess(
        ["ngrok", "http", "8001", "--log=stdout"],
        root,
        "ngrok",
    )
    if not p:
        log("请确认已安装 ngrok")
        cleanup()
        input("\n按 Enter 退出...")
        sys.exit(1)
    time.sleep(5)

    ngrok_url = wait_for_ngrok_url()
    if not ngrok_url:
        log("ngrok 隧道获取失败")
        log("请确认 ngrok authtoken 已配置")
        cleanup()
        input("\n按 Enter 退出...")
        sys.exit(1)

    with open(ngrok_url_file, "w") as f:
        f.write(ngrok_url)

    log(f"公网地址: {ngrok_url}")
    log("正在打开浏览器...")
    webbrowser.open(ngrok_url)

    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 48)
    print("  Gomoku Online 已上线!")
    print("=" * 48)
    print()
    print(f"  公网地址: {ngrok_url}")
    print(f"  ngrok管理: http://127.0.0.1:4040")
    print()
    print("  将此地址发给朋友即可加入对战")
    print("  架构: 后端直出前端静态文件, 无 Vite 代理")
    print()
    input("  按 Enter 键停止所有服务...")

    cleanup()
    print("已停止")


if __name__ == "__main__":
    main()
