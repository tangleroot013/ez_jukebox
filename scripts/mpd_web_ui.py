#!/usr/bin/env python3
# ==============================================================================
# ez_jukebox - Lightweight Flask Web UI Server
# ==============================================================================
import os
import sys
import subprocess

try:
    from flask import Flask, render_template_string, request
    from mpd import MPDClient
except ImportError:
    print("[+] Installing required packages: flask, python3-mpd2...")
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "python3-mpd2"], check=True)
    from flask import Flask, render_template_string, request
    from mpd import MPDClient

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ez_jukebox Web UI</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; background: #f4f6f8; color: #333; }
        .card { background: white; max-width: 480px; margin: auto; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        h1 { font-size: 1.5rem; margin-top: 0; color: #111; }
        .status-box { background: #eef2f5; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
        .controls button { padding: 0.6rem 1rem; margin: 0.2rem; font-size: 1rem; border: none; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }
        .controls button:hover { background: #1d4ed8; }
        .slider-box { margin-top: 1rem; }
        input[type=range] { width: 100%; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎵 ez_jukebox Control</h1>
        <div class="status-box">
            <div><strong>State:</strong> {{ status.get("state", "unknown") }}</div>
            <div><strong>Volume:</strong> {{ status.get("volume", "0") }}%</div>
            <div><strong>Current Track:</strong> {{ song.get("title", song.get("file", "No track playing")) }}</div>
            {% if song.get("artist") %}
            <div><strong>Artist:</strong> {{ song.get("artist") }}</div>
            {% endif %}
        </div>
        <div class="controls">
            <button onclick="sendCmd('play')">▶ Play</button>
            <button onclick="sendCmd('pause')">⏸ Pause</button>
            <button onclick="sendCmd('stop')">⏹ Stop</button>
            <button onclick="sendCmd('prev')">⏮ Prev</button>
            <button onclick="sendCmd('next')">⏭ Next</button>
        </div>
        <div class="slider-box">
            <label><strong>Volume:</strong></label>
            <input type="range" min="0" max="100" value="{{ status.get('volume', 50) }}" onchange="sendCmd('volume/' + this.value)">
        </div>
    </div>
    <script>
        function sendCmd(path) {
            fetch('/cmd/' + path).then(() => location.reload());
        }
    </script>
</body>
</html>
"""

def get_mpd_client():
    client = MPDClient()
    client.timeout = 5
    client.connect("127.0.0.1", 6600)
    return client

@app.route("/")
def index():
    try:
        client = get_mpd_client()
        status = client.status()
        song = client.currentsong() or {}
        client.disconnect()
        return render_template_string(HTML_TEMPLATE, status=status, song=song)
    except Exception as err:
        return f"<h3>MPD Connection Error: {err}</h3><p>Make sure MPD is running on port 6600.</p>"

@app.route("/cmd/<action>")
@app.route("/cmd/<action>/<value>")
def handle_cmd(action, value=None):
    try:
        client = get_mpd_client()
        if action == "play":
            client.play()
        elif action == "pause":
            client.pause()
        elif action == "stop":
            client.stop()
        elif action == "next":
            client.next()
        elif action == "prev":
            client.previous()
        elif action == "volume" and value is not None:
            client.setvol(int(value))
        client.disconnect()
        return "OK"
    except Exception as err:
        return f"Error: {err}", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[*] Starting MPD Web UI at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
