import os, tempfile

def update_monitor():
    target = "monitor_jukebox.py"
    if not os.path.exists(target):
        print(f"Error: {target} missing")
        return

    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    # Define a clean click handler calling mpd_play_random.sh directly
    handler_code = """
import subprocess

def trigger_random_playback(icon=None, item=None):
    script = os.path.expanduser("~/home-data/github_projects/ez_jukebox/scripts/mpd_play_random.sh")
    if os.path.exists(script):
        subprocess.Popen(["bash", script])
    else:
        subprocess.Popen(["mpc", "random", "on"])
        subprocess.Popen(["mpc", "next"])
"""

    if "trigger_random_playback" not in content:
        content = handler_code + "\n" + content

    # Replace existing click actions or default menu callbacks
    content = content.replace("mpd_play_next.sh", "mpd_play_random.sh")
    
    dir_name = os.path.dirname(os.path.abspath(target))
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        tf.write(content)
        temp_name = tf.name
    os.replace(temp_name, target)
    print("Updated monitor_jukebox.py handler.")

def update_launch_sh():
    target = "launch.sh"
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    launch_line = "python3 monitor_jukebox.py &\n"
    if "monitor_jukebox.py" not in content:
        content += f"\necho \"🚀 Starting tray monitor...\"\n{launch_line}"

    dir_name = os.path.dirname(os.path.abspath(target))
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        tf.write(content)
        temp_name = tf.name
    os.replace(temp_name, target)
    os.chmod(target, 0o755)
    print("Updated launch.sh execution script.")

if __name__ == "__main__":
    update_monitor()
    update_launch_sh()
