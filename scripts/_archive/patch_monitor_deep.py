import os
import tempfile

def inspect_and_patch_monitor():
    target_file = "monitor_jukebox.py"
    if not os.path.exists(target_file):
        print(f"Error: {target_file} not found.")
        return

    with open(target_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print("--- Scanning monitor_jukebox.py for click/action handlers ---")
    for idx, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in ['click', 'shuffle', 'next', 'menu', 'item', 'action', 'callback']):
            print(f"Line {idx + 1}: {line.strip()}")

    updated_lines = []
    modified = False
    
    for line in lines:
        if "mpd_play_next" in line:
            new_line = line.replace("mpd_play_next", "mpd_play_random")
            updated_lines.append(new_line)
            modified = True
            print(f"Patched line: {line.strip()} -> {new_line.strip()}")
        elif "mpc next" in line:
            new_line = line.replace("mpc next", "mpc random on && mpc next")
            updated_lines.append(new_line)
            modified = True
            print(f"Patched line: {line.strip()} -> {new_line.strip()}")
        else:
            updated_lines.append(line)

    if not modified:
        print("\nInjecting random playback fallback hook into monitor_jukebox.py...")
        patch_snippet = "\n# Injected random shuffle click handler\ndef handle_tray_click(icon, item=None):\n    import subprocess\n    subprocess.run(['mpc', 'random', 'on'], check=False)\n    subprocess.run(['mpc', 'next'], check=False)\n"
        updated_lines.append(patch_snippet)
        modified = True

    if modified:
        dir_name = os.path.dirname(os.path.abspath(target_file))
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                tf.writelines(updated_lines)
                temp_name = tf.name
            os.replace(temp_name, target_file)
            print(f"\nSuccessfully applied patch to {target_file} atomically!")
        except Exception as e:
            if temp_name and os.path.exists(temp_name):
                os.remove(temp_name)
            print(f"Failed to write file atomically: {e}")

if __name__ == "__main__":
    inspect_and_patch_monitor()
