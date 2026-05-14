#!/usr/bin/env python3
"""
Teams Translator — Entry point
Chạy: python run.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use Qwen STT by default for realtime translation flow.
os.environ.setdefault("STT_BACKEND", "qwen")

from src.main import main

if __name__ == "__main__":
    main()
