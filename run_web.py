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

# Ensure running with .venv python (matching start_minimal.bat)
venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
    import subprocess
    sys.exit(subprocess.call([str(venv_py), __file__] + sys.argv[1:]))

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n[INFO] Đang mở giao diện web tại: {url}\n")
    webbrowser.open(url)

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  Teams Translator - Google AI Studio Live Translate Web")
    print("=" * 60)
    print("  * Server: http://127.0.0.1:8000")
    print("  * Bấm Ctrl+C để dừng server.")
    print("=" * 60)

    # Launch browser automatically in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run FastAPI server
    uvicorn.run("src_web.server:app", host="127.0.0.1", port=8000, reload=False)
