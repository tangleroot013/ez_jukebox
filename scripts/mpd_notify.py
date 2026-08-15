#!/usr/bin/env python3
import os
import json
import time
import datetime
from pathlib import Path
from mpd import MPDClient

OUT_FILE = Path.home() / ".local/share/ez_jukebox" / "now_playing.json"
HOST = os.environ.get("MPD_HOST", "127.0.0.1")
PORT = int(os.environ.get("MPD_PORT", 6600))

def update_now_playing(client):
    try:
        status = client.status()
        song = client.currentsong()
        
        state = status.get("state", "stopped")
        title = song.get("title", song.get("name", "Unknown Title")) if state != "stopped" else "Stopped"
        artist = song.get("artist", "Unknown Artist") if state != "stopped" else "Unknown Artist"
        album = song.get("album", "Unknown Album") if state != "stopped" else "Unknown Album"
        file_path = song.get("file", "") if state != "stopped" else ""
        shuffle = "ON" if status.get("random") == "1" else "OFF"
        
        data = {
            "state": state,
            "title": title,
            "artist": artist,
            "album": album,
            "file": file_path,
            "shuffle": shuffle,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        
        tmp_file = OUT_FILE.with_suffix(".tmp")
        with open(tmp_file, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, OUT_FILE)
    except Exception as e:
        print(f"Error updating now_playing.json: {e}")

def main():
    while True:
        try:
            client = MPDClient()
            client.connect(HOST, PORT)
            update_now_playing(client)
            
            while True:
                # Wait for player or options change events
                events = client.idle("player", "options")
                if events:
                    update_now_playing(client)
        except Exception as e:
            print(f"MPD connection error ({e}), retrying in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    main()
