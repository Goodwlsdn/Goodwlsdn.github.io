#!/bin/bash
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo 'Install Python 3 first: https://www.python.org/downloads/macos/'; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if ! command -v cloudflared >/dev/null; then
  if command -v brew >/dev/null; then brew install cloudflared
  else echo 'Install cloudflared first (with Homebrew: brew install cloudflared).'; exit 1
  fi
fi
echo 'Setup complete. Run: bash Run-Mac.command'
