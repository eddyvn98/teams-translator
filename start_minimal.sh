#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ -f ".venv/bin/python" ]; then
    exec .venv/bin/python run_minimal.py "$@"
else
    exec python3 run_minimal.py "$@"
fi
