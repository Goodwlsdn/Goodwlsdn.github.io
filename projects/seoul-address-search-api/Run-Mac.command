#!/bin/bash
set -e
cd "$(dirname "$0")"
test -x .venv/bin/python || { echo 'Run bash Setup-Mac.command first.'; exit 1; }
command -v cloudflared >/dev/null || { echo 'Install cloudflared first.'; exit 1; }
test -f seoul.sqlite || { echo 'Copy seoul.sqlite into this folder first.'; exit 1; }
port=$(.venv/bin/python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
api_pid=''
tunnel_pid=''
cleanup() {
  if [ -n "$tunnel_pid" ]; then kill "$tunnel_pid" 2>/dev/null || true; wait "$tunnel_pid" 2>/dev/null || true; fi
  if [ -n "$api_pid" ]; then kill "$api_pid" 2>/dev/null || true; wait "$api_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 0' INT TERM
PYTHONPATH='' .venv/bin/python serve.py --port "$port" >api-mac.log 2>&1 &
api_pid=$!
ready=0
for ((i=0;i<60;i++)); do
  kill -0 "$api_pid" 2>/dev/null || { cat api-mac.log; exit 1; }
  if curl --noproxy '*' --fail --silent --max-time 2 "http://127.0.0.1:$port/health" >/dev/null; then ready=1; break; fi
  sleep 1
done
[ "$ready" = 1 ] || { echo 'API startup timed out. See api-mac.log'; exit 1; }
echo "API ready: http://127.0.0.1:$port/docs"
cloudflared tunnel --no-autoupdate --protocol http2 --url "http://127.0.0.1:$port" >tunnel-mac.log 2>&1 &
tunnel_pid=$!
url=''
for ((i=0;i<60;i++)); do
  kill -0 "$tunnel_pid" 2>/dev/null || { cat tunnel-mac.log; exit 1; }
  url=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' tunnel-mac.log | head -n 1 || true)
  [ -z "$url" ] || break
  sleep 1
done
[ -n "$url" ] || { echo 'Tunnel startup timed out. See tunnel-mac.log'; exit 1; }
printf '%s\n' "$url" >public-url.txt
echo "PUBLIC URL: $url"
echo 'Keep this Terminal open. Press Control+C to stop both API and tunnel.'
while kill -0 "$api_pid" 2>/dev/null && kill -0 "$tunnel_pid" 2>/dev/null; do sleep 2; done
