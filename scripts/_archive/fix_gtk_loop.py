import os, tempfile

code = '''import os
import sys
import threading
import subprocess
from PIL import Image, ImageDraw

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import pystray

def play_random_song(icon=None, item=None):
    subprocess.run(["mpc", "random", "on"], check=False)
    subprocess.run(["mpc", "next"], check=False)

def create_simple_icon():
    img = Image.new("RGBA", (64, 64), color=(30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill=(0, 200, 100, 255))
    return img

def start_gtk_loop():
    Gtk.main()

if __name__ == "__main__":
    # Start GTK main loop in a background thread to satisfy AppIndicator
    gtk_thread = threading.Thread(target=start_gtk_loop, daemon=True)
    gtk_thread.start()

    icon = pystray.Icon(
        "ez_jukebox",
        create_simple_icon(),
        "ez_jukebox (Click to Shuffle)",
        menu=pystray.Menu(
            pystray.MenuItem("Shuffle & Play", play_random_song, default=True),
            pystray.MenuItem("Exit", lambda icon, item: (icon.stop(), Gtk.main_quit())),
        ),
    )
    icon.run()
'''

target = "monitor_jukebox.py"
dir_name = os.path.dirname(os.path.abspath(target))
with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
    tf.write(code)
    temp_name = tf.name
os.replace(temp_name, target)
print("Updated monitor_jukebox.py with explicit GTK loop.")
