#!/bin/bash
# Qwen3-VL Captioner — macOS launcher
cd "$(dirname "$0")"

if [[ ! -x ".venv/bin/python" ]]; then
    echo "[ERROR] Virtual environment not found."
    echo "        Please run ./setup.sh first."
    exit 1
fi

echo "Starting Qwen3-VL Captioner..."
exec .venv/bin/python app.py
