#!/usr/bin/env python3
"""
Teams Translator Minimalist - Entry point
Chay: python run_minimal.py
"""
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Auto-switch to virtualenv if available
venv_py_win = os.path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
venv_py_posix = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
venv_py = venv_py_win if sys.platform == "win32" else venv_py_posix
if os.path.exists(venv_py) and os.path.realpath(sys.executable) != os.path.realpath(venv_py):
    import subprocess
    sys.exit(subprocess.call([venv_py, __file__] + sys.argv[1:]))

from src_minimal.main import main

if __name__ == "__main__":
    main()
