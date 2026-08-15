import os
import tempfile

def update_monitor():
    target = "monitor_jukebox.py"
    if not os.path.exists(target):
        print(f"Error: {target} not found.")
        return

    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    # Define the target function or snippet to handle random playback on tray click
    random_handler = """
def handle_shuffle_click(icon, item=None):
    import subprocess
    # Enable random mode and skip to a random track
    subprocess.run(["mpc", "random", "on"], check=False)
    subprocess.run(["mpc", "next"], check=False)
"""

    # Check if a custom click handler already exists, or inject/replace it
    if "handle_shuffle_click" not in content:
        # Append the helper function
        content += random_handler

    # Replace existing menu item or click actions pointing to sequential play with our random handler
    updated = content.replace("mpd_play_next.sh", "mpd_play_random.sh")
    updated = updated.replace("mpc next", "mpc random on && mpc next")

    dir_name = os.path.dirname(os.path.abspath(target))
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            tf.write(updated)
            temp_name = tf.name
        os.replace(temp_name, target)
        print("Successfully updated monitor_jukebox.py for random shuffle click!")
    except Exception as e:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        print(f"Failed to update file: {e}")

if __name__ == "__main__":
    update_monitor()
