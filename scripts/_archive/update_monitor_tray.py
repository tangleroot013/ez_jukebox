import os, tempfile

code = '''import os
import subprocess
from PIL import Image, ImageDraw
import pystray

def play_random_song(icon=None, item=None):
    subprocess.run(["mpc", "random", "on"], check=False)
    subprocess.run(["mpc", "next"], check=False)

def create_simple_icon():
    img = Image.new("RGBA", (64, 64), color=(30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill=(0, 200, 100, 255))
    return img

if __name__ == "__main__":
    icon = pystray.Icon(
        "ez_jukebox",
        create_simple_icon(),
        "ez_jukebox (Click to Shuffle)",
        menu=pystray.Menu(
            pystray.MenuItem("Shuffle & Play", play_random_song, default=True),
            pystray.MenuItem("Exit", lambda icon, item: icon.stop()),
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
print("Updated monitor_jukebox.py successfully.")
