import os
import tempfile

def patch_monitor_jukebox():
    target_file = "monitor_jukebox.py"
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found in the current directory.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    old_patterns = [
        ('mpd_play_next.sh', 'mpd_play_random.sh'),
        ('mpc next', 'mpc random on && mpc next'),
    ]

    updated_content = content
    replaced = False

    for old, new in old_patterns:
        if old in updated_content:
            updated_content = updated_content.replace(old, new)
            replaced = True
            print(f"Replaced '{old}' with '{new}' in {target_file}")

    if not replaced:
        print("Note: Exact default next/shuffle command strings weren't matched automatically.")
        print("Please check monitor_jukebox.py manually or specify your click handler function.")
        return

    dir_name = os.path.dirname(os.path.abspath(target_file))
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            tf.write(updated_content)
            temp_name = tf.name

        os.replace(temp_name, target_file)
        print(f"Successfully updated {target_file} atomically!")
    except Exception as e:
        if temp_name and os.path.exists(temp_name):
            os.remove(temp_name)
        print(f"Failed to update file: {e}")

if __name__ == "__main__":
    patch_monitor_jukebox()
