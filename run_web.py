"""
Launcher script for Teams Translator Web Edition (Google AI Studio style)
Automatically launches FastAPI server and opens web interface in browser.
"""

import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure running with .venv python
venv_py_win = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
venv_py_posix = PROJECT_ROOT / ".venv" / "bin" / "python"
venv_py = venv_py_win if sys.platform == "win32" else venv_py_posix
if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
    import subprocess
    sys.exit(subprocess.call([str(venv_py), __file__] + sys.argv[1:]))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def open_browser(port: int):
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[INFO] Opening web interface at: {url}\n")
    # On macOS, Google Chrome supports tab audio capture while Firefox/Safari do not
    if sys.platform == "darwin" and os.path.exists("/Applications/Google Chrome.app"):
        import subprocess
        try:
            subprocess.run(["open", "-a", "Google Chrome", url], check=False)
            return
        except Exception:
            pass
    webbrowser.open(url)

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Teams Translator Web Edition")
    parser.add_argument("--port", type=int, default=None, help="Port to run server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser")
    args, _ = parser.parse_known_args()

    port = args.port
    if port is None:
        env_port = os.getenv("PORT")
        if env_port:
            port = int(env_port)
        elif is_port_in_use(8000):
            port = 8080
        else:
            port = 8000

    host = args.host

    print("=" * 60)
    print("  Teams Translator - Google AI Studio Live Translate Web")
    print("=" * 60)
    print(f"  * Server: http://{host}:{port}")
    print("  * Press Ctrl+C to stop server.")
    print("=" * 60)

    # Launch browser automatically in background thread
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Run FastAPI server
    uvicorn.run("src_web.server:app", host=host, port=port, reload=False)
