#!/usr/bin/env python3
# ==============================================================================
# ez_jukebox - Zero-Latency Resilient Audio Watchdog
# ==============================================================================
import sys
import subprocess

def ensure_deps():
    """Ensure pulsectl and python-mpd2 are installed."""
    try:
        import pulsectl
        from mpd import MPDClient
    except ImportError:
        print("[+] Installing pulsectl and python-mpd2...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pulsectl", "python3-mpd2"], check=True)

ensure_deps()

import pulsectl
from mpd import MPDClient

TARGET_KEYWORD = "bluez_sink"
AUDIO_PROFILE = "a2dp"

def trigger_audio_switch():
    """Scans sinks and redirects default audio + resumes MPD if Bluetooth is found."""
    try:
        with pulsectl.Pulse('ez-jukebox-watchdog') as pulse:
            sinks = pulse.sink_list()
            bt_sink = None

            for sink in sinks:
                if TARGET_KEYWORD in sink.name and AUDIO_PROFILE in sink.name.lower():
                    bt_sink = sink
                    break

            if bt_sink:
                print(f"[+] Bluetooth A2DP sink detected: {bt_sink.name}")
                pulse.default_set(bt_sink)
                print("[+] Default sink updated successfully.")

                # Resume MPD cleanly
                try:
                    client = MPDClient()
                    client.connect("127.0.0.1", 6600)
                    if client.status().get("state") != "play":
                        client.play()
                    client.disconnect()
                    print("[+] MPD playback resumed.")
                except Exception as mpd_err:
                    print(f"[-] MPD control warning: {mpd_err}")
            else:
                print("[i] Audio change detected, keeping current output.")
    except Exception as e:
        print(f"[-] Event handler warning: {e}", file=sys.stderr)

def pulse_event_callback(ev):
    if ev.facility in ('sink', 'card') and ev.t in ('new', 'change', 'remove'):
        print(f"[*] Audio event: {ev.facility} -> {ev.t}")
        trigger_audio_switch()

def main():
    print("[*] Resilient Audio Watchdog active. Waiting for audio events...")
    trigger_audio_switch()

    with pulsectl.Pulse('ez-jukebox-listener') as pulse:
        pulse.event_mask_set('sink', 'card')
        pulse.event_callback_set(pulse_event_callback)
        pulse.event_listen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[-] Watchdog deactivated.")
        sys.exit(0)
