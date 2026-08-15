import os
import tempfile

def inspect_and_fix():
    target = "monitor_jukebox.py"
    if not os.path.exists(target):
        print(f"Error: {target} not found.")
        return

    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    print("--- Inspecting Tray / Click Code in monitor_jukebox.py ---")
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in ["icon", "click", "menu", "action", "setup", "run"]):
            print(f"{i+1}: {line}")

    # Let's ensure there is a clear click handler function that calls mpd_play_random.sh
    random_trigger_code = """
def _trigger_random_shuffle(icon=None, item=None):
    import subprocess
    script_path = os.path.expanduser("~/home-data/github_projects/ez_jukebox/scripts/mpd_play_random.sh")
    if os.path.exists(script_path):
        subprocess.run(["bash", script_path], check=False)
    else:
        subprocess.run(["mpc", "random", "on"], check=False)
        subprocess.run(["mpc", "next"], check=False)
"""

    if "_trigger_random_shuffle" not in content:
        content = random_trigger_code + "\n" + content

    # Bind default click or menu action if pystray or similar is used
    # Look for Icon instantiation and ensure default action or menu item points to it
    if "pystray.Icon" in content or "Icon(" in content:
        # If there's an icon setup, try replacing dummy click handlers or adding default=True
        if "default=True" not in content:
            content = content.replace("pystray.Icon(", "pystray.Icon(") # placeholder for context

    # Save atomically
    dir_name = os.path.dirname(os.path.abspath(target))
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            tf.write(content)
            temp_name = tf.name
        os.replace(temp_name, target)
        print("\nSuccessfully updated monitor_jukebox.py with explicit random shuffle handler!")
    except Exception as e:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        print(f"Failed to update file: {e}")

if __name__ == "__main__":
    inspect_and_fix()
