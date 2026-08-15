#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

def read_now_playing(path: Path) -> dict:
    if not path.exists():
        return {"error": "now_playing.json not found", "path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": "failed to parse now_playing.json", "details": str(e)}

class Handler(BaseHTTPRequestHandler):
    server_version = "ez_jukebox_now_playing_api/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/now_playing.json":
            payload = self.server.read_func()  # type: ignore[attr-defined]
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        # Keep logs quiet; rely on systemd journal where needed.
        return

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("EZ_NP_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("EZ_NP_API_PORT", "8765")))
    parser.add_argument("--file", default=os.environ.get("EZ_NP_API_FILE", str(Path.home() / ".local/share/ez_jukebox/now_playing.json")))
    args = parser.parse_args()

    fp = Path(args.file)

    def read_func():
        return read_now_playing(fp)

    httpd = HTTPServer((args.host, args.port), Handler)
    httpd.read_func = read_func  # type: ignore[attr-defined]

    print(f"[ez_jukebox] Now-playing API listening on http://{args.host}:{args.port}/now_playing.json")
    print(f"[ez_jukebox] Serving file: {fp}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
